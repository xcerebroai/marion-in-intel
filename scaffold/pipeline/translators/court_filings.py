"""
tyler_odyssey_court translator (built-in, v5.5.0+).

Converts court-case records (produced by a county-side court scraper,
e.g. scrapers/court_filings.py) into framework signals + placeholder
parcels.

This translator is COUNTY-AGNOSTIC. All county-specific data (case-type
synonym maps, parcel-ID prefix, state rule family) comes from the county
config and source config passed at call time.

Canonical RAW RECORD shape consumed (§4.32):

    {
        "raw_record_id": "<cf_...>",
        "source_id":     "<source id>",
        "source_url":    "<portal case URL>",
        "source_fetched_at": "<ISO timestamp>",
        "parser_confidence": 90,
        "raw_payload": {
            "case_number":    "<court case number>",
            "case_type_code": "MF",
            "case_type_raw":  "<human-readable type label>",
            "filing_date":    "YYYY-MM-DD",
            "case_status":    "Pending",
            "plaintiff":      "<plaintiff / lender>",
            "defendant":      "<defendant / borrower>",
            ...
        }
    }

Expected source_config structure:

    {
        "translator": "tyler_odyssey_court",
        "translator_config": {
            "case_type_doc_type_map": {   # optional — overrides defaults
                "MF": "LIS_PENDENS",
                "EV": "EVICTION_FILING"
            },
            "state_rule_family": "IN_judicial_foreclosure"  # optional override;
                                  # read from county_config.state_rule_family if absent
        },
        "parcel_id_prefix": "CT-",
        "field_map": {}    # optional — identity mapping when absent
    }

Default case_type_code → canonical_doc_type map (overridable per source):

    MF → LIS_PENDENS         (judicial foreclosure suit = lis pendens event)
    EV → EVICTION_FILING
    DN → DIVORCE_FILING
    CP → JUDGMENT_LIEN
    CC → JUDGMENT_LIEN

Under a judicial-foreclosure state_rule_family, MF (→ LIS_PENDENS) records
are tagged FORECLOSURE_LIS_PENDENS in per_signal_meta. The signal's doc_type
stays LIS_PENDENS so the pipeline's normalize → registry chain routes it; the
run_staged_pipeline lis_pendens_mode applies the judicial-foreclosure
classification at scoring time.

Cross-source dedup note: the signal carries `case_number` explicitly so
build_leads._cross_source_dedup_lp_mf() can match it against a recorder LP's
reference_number field and unify placeholder parcel_ids when both sources
capture the same filing event.

Returns: (signals, parcels, per_signal_meta_by_url)
"""

from __future__ import annotations

import hashlib

from scaffold.pipeline.translators import register

_DEFAULT_CASE_TYPE_MAP: dict[str, str] = {
    "MF": "LIS_PENDENS",
    "EV": "EVICTION_FILING",
    "DN": "DIVORCE_FILING",
    "CP": "JUDGMENT_LIEN",
    "CC": "JUDGMENT_LIEN",
}


def _make_parcel_id(prefix: str, case_number: str) -> str:
    """Stable placeholder parcel ID from prefix + case number hash."""
    h = hashlib.sha1(case_number.upper().strip().encode("utf-8")).hexdigest()[:12].upper()
    sep = "" if prefix.endswith("-") else "-"
    return f"{prefix}{sep}{h}"


def _foreclosure_subtype(canonical: str, state_rule_family: str) -> str | None:
    """Return FORECLOSURE_LIS_PENDENS when canonical is LIS_PENDENS in a
    judicial-foreclosure state — stored in per_signal_meta for reference only."""
    if (
        canonical == "LIS_PENDENS"
        and "judicial_foreclosure" in (state_rule_family or "").lower()
    ):
        return "FORECLOSURE_LIS_PENDENS"
    return None


@register("tyler_odyssey_court")
def translate_tyler_odyssey_court(
    raw_records: list[dict],
    county_config: dict,
    source_config: dict,
) -> tuple[list[dict], list[dict], dict[str, dict]]:
    """
    Translate court-case raw records into pipeline signals.

    Args:
        raw_records:   List in canonical §4.32 wrapped shape.
        county_config: Full county config dict.
        source_config: This source's config block.

    Returns:
        (signals, parcels, per_signal_meta_by_url)
    """
    tc = source_config.get("translator_config", {}) or {}
    parcel_id_prefix: str = source_config.get("parcel_id_prefix", "CT-")

    # Merge defaults with any per-county overrides.
    case_type_map: dict = dict(_DEFAULT_CASE_TYPE_MAP)
    if tc.get("case_type_doc_type_map"):
        case_type_map.update(tc["case_type_doc_type_map"])

    # State rule family: translator_config overrides county_config top-level.
    state_rule_family: str = (
        tc.get("state_rule_family")
        or county_config.get("state_rule_family", "")
    )

    source_id = source_config.get("_source_id") or "court_filings"

    signals: list[dict] = []
    parcels: list[dict] = []
    per_signal_meta: dict[str, dict] = {}
    seen_parcel_ids: set[str] = set()

    for raw in raw_records:
        payload = raw.get("raw_payload", {}) or {}

        case_number    = (payload.get("case_number") or "").strip()
        case_type_code = (payload.get("case_type_code") or "").strip().upper()
        filing_date    = (payload.get("filing_date") or "").strip()
        plaintiff      = (payload.get("plaintiff") or "").strip()
        defendant      = (payload.get("defendant") or "").strip()
        case_status    = (payload.get("case_status") or "").strip()

        if not case_number:
            continue

        canonical = case_type_map.get(case_type_code, "UNKNOWN").upper()
        fc_subtype = _foreclosure_subtype(canonical, state_rule_family)

        parcel_id = _make_parcel_id(parcel_id_prefix, case_number)

        if parcel_id not in seen_parcel_ids:
            parcels.append({
                "parcel_id":            parcel_id,
                "address":              "",
                "city":                 "",
                "zip":                  "",
                "owner_name":           defendant or None,
                "legal_description":    None,
                "parcel_master_status": "placeholder_pending_enrichment",
            })
            seen_parcel_ids.add(parcel_id)

        signal_id = "sig_" + hashlib.sha1(
            f"{source_id}|{case_number}|{filing_date}".encode("utf-8")
        ).hexdigest()[:16]

        source_url = (
            raw.get("source_url")
            or f"about:blank/{source_id}/{case_number}"
        )

        signal = {
            "signal_id":              signal_id,
            "raw_record_id":          raw.get("raw_record_id"),
            "source_id":              source_id,
            "source_url":             source_url,
            "doc_type":               canonical,
            "doc_type_subtype_label": case_type_code,
            "doc_number":             case_number,
            "primary_parcel_id":      parcel_id,
            "filing_date":            filing_date or None,
            "defendant":              defendant or None,   # borrower / debtor (DF role for §17 debtor engine)
            "plaintiff":              plaintiff or None,   # lender / creditor (PL role)
            "grantor":                defendant or None,   # legacy alias — keep for downstream compat
            "grantee":                plaintiff or None,   # legacy alias
            "case_number":            case_number,         # explicit; used for cross-source dedup
            "case_type_code":         case_type_code,
            "case_status":            case_status or None,
            "parser_confidence":      raw.get("parser_confidence", 90),
        }
        signals.append(signal)

        meta_entry: dict = {
            "preset_review_flags": [],
            "match_confidence":    0,
            "match_method":        "placeholder",
            "case_number":         case_number,
            "filing_date":         filing_date,
            "canonical_doc_type":  canonical,
            "primary_parcel_id":   parcel_id,
        }
        if fc_subtype:
            meta_entry["foreclosure_subtype"] = fc_subtype
        per_signal_meta[source_url] = meta_entry

    return signals, parcels, per_signal_meta

"""
recorder_recordings translator (built-in, v5.2.0+).

Converts NORMALIZED recorded-instrument records (produced by a county-side
recorder scraper, e.g. scrapers/recorder_recordings.py) into framework
signals + placeholder parcels.

This translator is COUNTY-AGNOSTIC. All county-specific data (doc-type
synonym maps, parcel-ID prefix, accepted municipalities, state rule family)
comes from the county config and source config passed at call time.

Canonical RAW RECORD shape consumed (MASTER_PROMPT §4.32):

    {
        "raw_record_id": "<unique id>",
        "source_id": "<source id>",
        "source_url": "<portal URL>",
        "source_fetched_at": "<ISO timestamp>",
        "parser_confidence": <0..100>,
        "raw_payload": {
            "doc_number":    "<instrument number, canonical>",
            "doc_type_raw":  "<raw document type label from source>",
            "recording_date": "<YYYY-MM-DD>",
            "party1":        "<first party (grantor/debtor/grantor/borrower)>",
            "party2":        "<second party (grantee/lender/trustee/beneficiary)>",
            "legal_desc":    "<legal description / subdivision / lot>",
            "book":          "<book number if applicable>",
            "page":          "<page number if applicable>",
            ... (other source-specific fields, ignored by translator)
        }
    }

Expected source_config structure:

    {
        "translator": "recorder_recordings",
        "translator_config": {
            "state_rule_family": "IN_judicial_foreclosure"  # optional; read
                                 # from county_config.state_rule_family if absent
        },
        "doc_type_synonyms": {
            "LP":          "LIS_PENDENS",
            "MORTGAGE":    "MORTGAGE",
            "DEED":        "WARRANTY_DEED",
            ...
        },
        "parcel_id_prefix": "MARIN-REC-",
        "field_map": {}   # optional — identity mapping when absent
    }

`doc_type_synonyms` maps the raw label (as returned by the source) to a
canonical type name from knowledge_base/domain/canonical_doc_types.json.
The mapping is applied BEFORE the normalize_doc_type fallback, giving counties
explicit control over instrument-type classification.

Returns: (signals, parcels, per_signal_meta_by_url)
"""

from __future__ import annotations

import hashlib
from typing import Any

from scaffold.pipeline.translators import register
from scaffold.pipeline.normalize import normalize_doc_type


def _make_parcel_id(prefix: str, doc_number: str) -> str:
    """Stable placeholder parcel ID from prefix + instrument number hash."""
    h = hashlib.sha1(doc_number.upper().strip().encode("utf-8")).hexdigest()[:12].upper()
    sep = "" if prefix.endswith("-") else "-"
    return f"{prefix}{sep}{h}"


def _resolve_doc_type(
    doc_type_raw: str,
    synonyms: dict[str, str],
) -> tuple[str, str]:
    """
    Resolve raw doc type label to (canonical_doc_type, subtype_label).

    Resolution order:
      1. Exact match in synonyms (case-insensitive, stripped).
      2. normalize_doc_type() framework fallback.
      3. Unknown — return (UNKNOWN, raw label) → routes to review queue.
    """
    if not doc_type_raw:
        return "UNKNOWN", "Unknown"

    key = doc_type_raw.strip().upper()

    # Build case-insensitive synonym lookup.
    for raw_label, canonical in synonyms.items():
        if raw_label.strip().upper() == key:
            return canonical.upper(), doc_type_raw.strip()

    # Framework fallback normalization.
    norm = normalize_doc_type(doc_type_raw)
    normalized = norm.get("normalized_doc_type") or ""
    if normalized and normalized != "UNKNOWN":
        return normalized.upper(), doc_type_raw.strip()

    return "UNKNOWN", doc_type_raw.strip()


def _foreclosure_subtype(
    canonical: str,
    state_rule_family: str,
) -> str | None:
    """
    Return FORECLOSURE_LIS_PENDENS when canonical is LIS_PENDENS in a judicial-
    foreclosure state — stored in per_signal_meta for reference only.

    The signal's doc_type stays LIS_PENDENS so the pipeline's normalize_doc_type
    → registry_to_lead_type chain can route it. The state_rule_family is passed
    to run_staged_pipeline as lis_pendens_mode="foreclosure" (via
    state_profile.mode_from_rule_family), which is where the IN judicial-
    foreclosure classification is applied.
    """
    if (
        canonical == "LIS_PENDENS"
        and "judicial_foreclosure" in (state_rule_family or "").lower()
    ):
        return "FORECLOSURE_LIS_PENDENS"
    return None


@register("recorder_recordings")
def translate_recorder_recordings(
    raw_records: list[dict],
    county_config: dict,
    source_config: dict,
) -> tuple[list[dict], list[dict], dict[str, dict]]:
    """
    Translate normalized recorded-instrument raw records into pipeline signals.

    Args:
        raw_records:   List in canonical §4.32 wrapped shape.
        county_config: Full county config dict.
        source_config: This source's config block.

    Returns:
        (signals, parcels, per_signal_meta_by_url)
    """
    tc = source_config.get("translator_config", {}) or {}
    doc_type_synonyms: dict = source_config.get("doc_type_synonyms", {}) or {}
    parcel_id_prefix: str = source_config.get("parcel_id_prefix", "REC-")
    field_map: dict = source_config.get("field_map", {}) or {}

    # State rule family comes from county config; translator_config can override.
    state_rule_family: str = (
        tc.get("state_rule_family")
        or county_config.get("state_rule_family", "")
    )

    geography = county_config.get("geography", {}) or {}
    accepted_municipalities = geography.get("accepted_municipalities", []) or []
    accepted_names = {m["name"].upper() for m in accepted_municipalities}
    cross_county_policy = geography.get("cross_county_policy", {}) or {}
    unknown_city_action = cross_county_policy.get("unknown_city_action", "flag_for_review")

    source_id = source_config.get("_source_id") or "recorder_recordings"

    def _resolve_field(payload: dict, canonical_name: str) -> str:
        actual = field_map.get(canonical_name, canonical_name)
        return (payload.get(actual) or "").strip()

    signals: list[dict] = []
    parcels: list[dict] = []
    per_signal_meta: dict[str, dict] = {}
    seen_parcel_ids: set[str] = set()

    for raw in raw_records:
        payload = raw.get("raw_payload", {}) or {}

        doc_number   = _resolve_field(payload, "doc_number")
        doc_type_raw = _resolve_field(payload, "doc_type_raw")
        rec_date     = _resolve_field(payload, "recording_date")
        party1       = _resolve_field(payload, "party1")
        party2       = _resolve_field(payload, "party2")
        legal_desc   = _resolve_field(payload, "legal_desc")

        if not doc_number:
            continue

        # Doc-type resolution.
        canonical, subtype_label = _resolve_doc_type(doc_type_raw, doc_type_synonyms)
        fc_subtype = _foreclosure_subtype(canonical, state_rule_family)

        # Parcel placeholder (instrument-number-keyed; no address in recorder index).
        parcel_id = _make_parcel_id(parcel_id_prefix, doc_number)

        if parcel_id not in seen_parcel_ids:
            parcels.append({
                "parcel_id":             parcel_id,
                "address":               "",
                "city":                  "",
                "zip":                   "",
                "owner_name":            party1 or None,
                "legal_description":     legal_desc or None,
                "parcel_master_status":  "placeholder_pending_enrichment",
            })
            seen_parcel_ids.add(parcel_id)

        # Signal.
        signal_id = "sig_" + hashlib.sha1(
            f"{source_id}|{doc_number}|{rec_date}".encode("utf-8")
        ).hexdigest()[:16]

        source_url = raw.get("source_url") or f"about:blank/{source_id}/{doc_number}"

        signal = {
            "signal_id":              signal_id,
            "raw_record_id":          raw.get("raw_record_id"),
            "source_id":              source_id,
            "source_url":             source_url,
            "doc_type":               canonical,
            "doc_type_subtype_label": subtype_label,
            "doc_number":             doc_number,
            "primary_parcel_id":      parcel_id,
            "filing_date":            rec_date or None,
            "grantor":                party1 or None,
            "grantee":                party2 or None,
            "parser_confidence":      raw.get("parser_confidence", 90),
        }
        signals.append(signal)

        meta_entry: dict = {
            "preset_review_flags":  [],
            "match_confidence":     0,
            "match_method":         "placeholder",
            "doc_number":           doc_number,
            "recording_date":       rec_date,
            "canonical_doc_type":   canonical,
            "primary_parcel_id":    parcel_id,
        }
        if fc_subtype:
            meta_entry["foreclosure_subtype"] = fc_subtype
        per_signal_meta[source_url] = meta_entry

    return signals, parcels, per_signal_meta

"""
County-side translator adapters for the Marion (IN) build.

Registers the `owner_notice_records` translator: a thin, config-driven
adapter for lead sources whose raw records already carry a situs address,
an owner/grantor name, and a stable parcel key (code enforcement cases,
estate/probate owner-name sweeps). Unlike `foreclosure_notices` (which
derives an expected sale date from a recording year/month and drops the
owner name), this translator preserves the owner name as both the signal
`grantor` and the placeholder parcel `owner_name`, and carries the exact
parcel_id the scraper assigned (task §4.32 parcel-id formulas).

It is registered here (county-side) rather than in scaffold/ because it is
wired in only for this county's `code_enforcement` and `probate_estates`
sources. The module is imported by scrapers/__init__.py so its @register
runs when build_leads.py executes `import scrapers`.

Consumed raw-record shape (framework-canonical §4.32 wrapped):

    {
        "raw_record_id": "...",
        "source_id": "...",
        "source_url": "...",
        "source_fetched_at": "...",
        "parser_confidence": <int>,
        "raw_payload": {
            "parcel_id":      "<scraper-assigned placeholder parcel id>",
            "doc_number":     "<case/instrument number; may be empty>",
            "address":        "<situs address>",
            "city":           "<situs city>",
            "zip":            "<5-digit zip>",
            "grantor":        "<owner / estate / responsible-party name>",
            "recording_date": "<YYYY-MM-DD or null>",
            ... (other source-specific fields, ignored)
        }
    }

Expected source_config:

    {
        "translator": "owner_notice_records",
        "translator_config": {
            "canonical": "CODE_VIOLATION_NOTICE",      # required
            "subtype_label": "Code Violation Notice"   # optional
        },
        "field_map": { ... }                            # optional (identity)
    }

`canonical` must be a registry-aligned canonical doc type
(knowledge_base/domain/canonical_doc_types.json) so the orchestrator's
normalize -> bridge chain routes the resulting signal to a lead type.

Returns: (signals, parcels, per_signal_meta_by_url)
"""

from __future__ import annotations

import hashlib

from scaffold.pipeline.translators import register


def _city_action(city: str, county_config: dict) -> tuple[list[str], str]:
    """Mirror the foreclosure_notices cross-county-leak policy.

    Returns (preset_review_flags, action) where action is 'keep' or 'drop'.
    """
    geography = county_config.get("geography", {}) or {}
    accepted = geography.get("accepted_municipalities", []) or []
    policy = geography.get("cross_county_policy", {}) or {}
    if not city or not accepted:
        return [], "keep"
    accepted_names = {m["name"].upper() for m in accepted}
    if city.upper().strip() in accepted_names:
        return [], "keep"
    action = policy.get("unknown_city_action", "flag_for_review")
    if action == "drop":
        return [], "drop"
    return ["potential_cross_county_leak"], "keep"


@register("owner_notice_records")
def translate_owner_notice_records(
    raw_records: list[dict],
    county_config: dict,
    source_config: dict,
) -> tuple[list[dict], list[dict], dict[str, dict]]:
    """Translate owner/notice raw records into pipeline signals + parcels."""
    tc = source_config.get("translator_config", {}) or {}
    canonical = (tc.get("canonical") or "").strip().upper()
    subtype_label = tc.get("subtype_label") or (
        canonical.replace("_", " ").title() if canonical else "Notice"
    )
    field_map = source_config.get("field_map", {}) or {}
    source_id = source_config.get("_source_id") or "owner_notice_records"

    def _f(payload: dict, name: str) -> str:
        actual = field_map.get(name, name)
        value = payload.get(actual)
        return ("" if value is None else str(value)).strip()

    signals: list[dict] = []
    parcels: list[dict] = []
    per_signal_meta: dict[str, dict] = {}
    seen_parcel_ids: set[str] = set()

    for raw in raw_records:
        payload = raw.get("raw_payload", {}) or {}

        parcel_id = _f(payload, "parcel_id")
        if not parcel_id:
            continue

        address = _f(payload, "address")
        city = _f(payload, "city")
        zip_code = _f(payload, "zip")
        grantor = _f(payload, "grantor")
        doc_number = _f(payload, "doc_number") or parcel_id
        recording_date = _f(payload, "recording_date") or None

        # Cross-county-leak detection (same policy foreclosure_notices honors).
        preset_flags, action = _city_action(city, county_config)
        if action == "drop":
            continue

        if parcel_id not in seen_parcel_ids:
            parcels.append({
                "parcel_id":            parcel_id,
                "address":              address,
                "city":                 city,
                "zip":                  zip_code,
                "owner_name":           grantor or None,
                "parcel_master_status": "placeholder_pending_enrichment",
            })
            seen_parcel_ids.add(parcel_id)

        signal_id = "sig_" + hashlib.sha1(
            f"{source_id}|{doc_number}|{recording_date}".encode("utf-8")
        ).hexdigest()[:16]
        source_url = raw.get("source_url") or f"about:blank/{source_id}/{doc_number}"

        signals.append({
            "signal_id":              signal_id,
            "raw_record_id":          raw.get("raw_record_id"),
            "source_id":              source_id,
            "source_url":             source_url,
            "doc_type":               canonical,
            "doc_type_subtype_label": subtype_label,
            "doc_number":             doc_number,
            "primary_parcel_id":      parcel_id,
            "filing_date":            recording_date,
            "grantor":                grantor or None,
            "grantee":                None,
            "address":                address,
            "city":                   city,
            "zip":                    zip_code,
            "parser_confidence":      raw.get("parser_confidence", 90),
        })

        per_signal_meta[source_url] = {
            "preset_review_flags": preset_flags,
            "match_confidence":    0,
            "match_method":        "placeholder",
            "canonical_doc_type":  canonical,
            "primary_parcel_id":   parcel_id,
            "address":             address,
            "city":                city,
            "zip":                 zip_code,
        }

    return signals, parcels, per_signal_meta

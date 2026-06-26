"""
scoring_seam — pipeline seam (post-scoring-removal refactor).

The seam between the staged engine's `matched_leads.json` and the retained
classification / review / dashboard stages (classify.py, review.py,
dashboard.py). Scoring has been removed — clients build their own ranking
logic on top of the signal data.

What the seam does — in order, per matched_lead:

  1. Build a stack-shaped input for `classify.classify_deal_paths` from
     `matched_lead.signals[]`. The matched_lead carries §18 aggregated
     SignalGroups (lowercased registry `canonical_doc_type`, plus a `count`
     and dated range). The seam:
       - lowercased canonical_doc_type → UPPERCASE registry key;
       - lookup of `lead_pattern` from canonical_doc_types.json's CANONICAL;
       - one stack entry per signal group `count` occurrence.
  2. Optionally attach parcel-master enrichment (R3(iii)). When the caller
     supplies an `enrichment_provider(parcel_id)` that returns a parcel-master
     dict, attributes are derived via `normalize.derive_attributes` and the
     parcel-display snapshot is stamped on the processed lead. When no
     enrichment is provided, attributes is empty, `parcel_display` is None,
     and `enrichment_status = "UNENRICHED"`. A lead is never dropped for
     missing enrichment.
  3. Call `classify.classify_deal_paths`.
  4. Run `review.evaluate_review_queue` for review_flags / lead_status.
  5. Emit a `processed_lead_record` dict (schema-validated).

This module is universal framework code: no county / state / vendor literal
appears here. The county-agnostic regression scanner enforces that.
"""

from __future__ import annotations

import functools
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Optional

from jsonschema import Draft202012Validator

from scaffold.pipeline.classify import classify_deal_paths
from scaffold.pipeline.contracts import schema_path
from scaffold.pipeline.debtor_party_engine import BROAD_KEY_REGISTRY_ALIASES
from scaffold.pipeline.doc_type_bridge import (
    REGISTRY_LOWER_KEYS,
    REGISTRY_UPPER_KEYS,
)
from scaffold.pipeline.normalize import CANONICAL, derive_attributes
from scaffold.pipeline.review import evaluate_review_queue
from scaffold.pipeline.state_profile import resolve_lis_pendens_pattern


# ---------------------------------------------------------------------------
# Bridge helpers — canonical_doc_type (lowercased) <-> normalized_doc_type
# (UPPERCASE registry key). The Session-8 doc_type_bridge defines the rule
# (monolith UPPERCASE -> lowercased registry); the seam's inverse is a
# straight uppercase, validated against REGISTRY_UPPER_KEYS so an unknown
# canonical_doc_type fails loud rather than silently scoring as zero.
# ---------------------------------------------------------------------------

def canonical_doc_type_to_normalized(canonical_doc_type: str) -> Optional[str]:
    """Return the UPPERCASE registry key matching a lowercased canonical_doc_type.

    The staged engine's lowercased canonical_doc_type is one of
    REGISTRY_LOWER_KEYS (Session 8 bridge guarantees this for normalize.py's
    output); the seam uppercases it to align with score.BASE_SCORE and
    normalize.CANONICAL. An unknown canonical_doc_type returns None — the
    caller routes it to the F-5-style review reason rather than fabricating
    a score.

    Session 8 broad-key fan-out: a Session-2 broad §17 key
    (foreclosure_notice / code_lien / probate / trustee_sale /
    abstract_of_judgment / civil_judgment / administrative_lien) is NOT
    itself a registry entry. When the canonical_doc_type is a broad key with
    a non-empty fan-out, the seam picks the first fan-out alias (every alias
    in a single broad-key fan-out shares the same §17 rule by construction —
    Session 8 — and they share base-score / pattern semantics within their
    family). When the broad key has an empty fan-out (administrative_lien /
    civil_judgment — broad buckets whose children carry their own rules),
    None is returned.
    """
    if not isinstance(canonical_doc_type, str) or not canonical_doc_type:
        return None
    lowered = canonical_doc_type.lower()
    if lowered in REGISTRY_LOWER_KEYS:
        upper = lowered.upper()
        assert upper in REGISTRY_UPPER_KEYS, (  # noqa: S101 — invariant
            "doc_type_bridge invariant violated: lowercased key in "
            "REGISTRY_LOWER_KEYS but UPPERCASE not in REGISTRY_UPPER_KEYS"
        )
        return upper
    # Broad-key fan-out — Session-2 §17 broad keys (foreclosure_notice etc.)
    # are not registry entries but fan out to one or more registry aliases.
    aliases = BROAD_KEY_REGISTRY_ALIASES.get(lowered) or ()
    for alias in aliases:
        if alias in REGISTRY_LOWER_KEYS:
            return alias.upper()
    return None


def pattern_for_canonical_doc_type(
    canonical_doc_type: str, *, lis_pendens_mode: Optional[str] = None
) -> Optional[str]:
    """Return the `lead_pattern` (foreclosure / tax / lien / estate / code / ...)
    for a lowercased canonical_doc_type, via canonical_doc_types.json's CANONICAL
    table. Returns None when no pattern is associated (enrichment-only types).

    When the canonical entry's lead_pattern is the sentinel "by_state_profile",
    the actual pattern is resolved at runtime from the county's foreclosure
    regime mode (state_profile.resolve_lis_pendens_pattern). The mode is a
    per-county config fact (derived from `state_rule_family`), so the same
    canonical_doc_types.json stays universal across judicial, non-judicial,
    and hybrid regimes."""
    upper = canonical_doc_type_to_normalized(canonical_doc_type)
    if upper is None:
        return None
    entry = CANONICAL.get(upper, {})
    lead_pattern = entry.get("lead_pattern")
    if lead_pattern == "by_state_profile":
        return resolve_lis_pendens_pattern(lis_pendens_mode)
    return lead_pattern


# ---------------------------------------------------------------------------
# matched_lead → stack adapter (G3 — aggregated groups vs raw signals).
# ---------------------------------------------------------------------------


def _parse_iso_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def adapt_matched_lead_to_stack(
    matched_lead: dict, *, as_of: date, lis_pendens_mode: Optional[str] = None
) -> dict:
    """Convert a matched_lead into a stack-shaped dict the retained
    classify.classify_deal_paths helper consumes.

    Each `matched_lead.signals[]` entry is one §18 aggregated SignalGroup
    (canonical_doc_type lowercased, plus a `count` and dated range). The
    monolith stack contract is "one active_signal dict per stack-contributing
    instrument" (§09 / domain/03_scoring_and_stacking.md). The seam
    synthesizes `count` stack entries per signal group so the §18.E
    legitimate-stacking bonus the monolith would have computed survives
    (per docs/v5.4.0_session6_seam_design.md G3).

    Empty / unknown patterns are dropped from `pattern_set` and don't
    contribute to `stack_depth`, matching the monolith's behavior.
    """
    parcel_id = matched_lead.get("primary_parcel_id")
    signals = matched_lead.get("signals") or []
    active_signals: list[dict] = []
    pattern_seq: list[str] = []

    for group in signals:
        canonical = group.get("canonical_doc_type") or ""
        normalized = canonical_doc_type_to_normalized(canonical)
        pattern = pattern_for_canonical_doc_type(
            canonical, lis_pendens_mode=lis_pendens_mode
        )
        canonical_entry = CANONICAL.get(normalized or "", {})
        document_priority = canonical_entry.get("document_priority", 0)
        event_date = (group.get("latest_recorded_date")
                      or group.get("earliest_recorded_date"))
        count = int(group.get("count") or 1)
        if count < 1:
            count = 1
        for _ in range(count):
            sig = {
                "signal_id": (
                    f"seam_{(group.get('instrument_numbers') or [None])[0]}"
                    f"_{len(active_signals)}"
                ),
                "source_id": (group.get("source_ids") or [None])[0],
                "source_url": (group.get("source_urls") or [None])[0],
                "raw_doc_type": canonical,
                "normalized_doc_type": normalized,
                "canonical_doc_type": canonical,
                "pattern": pattern,
                "event_date": event_date,
                "document_priority": document_priority,
                "lifecycle_status": "ACTIVE",
                "counts_in_stack": True,
                "signal_type": group.get("signal_type"),
                "evidence_ids": list(group.get("evidence_ids") or []),
                "_aggregation_count": count,
                "_aggregated_from_group": True,
            }
            active_signals.append(sig)
            if pattern:
                pattern_seq.append(pattern)

    seen = set()
    pattern_set: list[str] = []
    for p in pattern_seq:
        if p and p not in seen:
            seen.add(p)
            pattern_set.append(p)

    return {
        "parcel_id": parcel_id,
        "active_signals": active_signals,
        "suppressed_signals": [],
        "patterns": list(pattern_seq),
        "stack_contrib_patterns": list(pattern_seq),
        "pattern_set": pattern_set,
        "stack_depth": len(pattern_seq),
        "amounts": [],
        "eviction_collapsed": False,
    }


# ---------------------------------------------------------------------------
# Enrichment — R3(iii). The seam accepts an OPTIONAL provider; absent ⇒
# attributes is empty, parcel_display is None, enrichment_status=UNENRICHED.
# ---------------------------------------------------------------------------

EnrichmentProvider = Callable[[Optional[str]], Optional[dict]]
"""Callable: parcel_id -> parcel dict (or None). Provided by the caller when
parcel-master enrichment is available. The seam invokes it once per scored
lead; a None return means the parcel has no enrichment row available, which
is fine — the lead is still scored without it."""


def _parcel_display_from(parcel: dict) -> Optional[dict]:
    """Project the parcel-master fields the dashboard renders. Returns None
    when `parcel` is None — the UNENRICHED path."""
    if not parcel:
        return None
    return {
        "situs_address": parcel.get("situs_address") or parcel.get("address"),
        "situs_city": parcel.get("situs_city") or parcel.get("city"),
        "situs_state": parcel.get("situs_state"),
        "owner_mailing_address": parcel.get("owner_mailing_address"),
        "owner_mailing_city": parcel.get("owner_mailing_city"),
        "owner_mailing_state": parcel.get("owner_mailing_state"),
        "owner_mailing_zip": parcel.get("owner_mailing_zip"),
        "assessed_value": parcel.get("assessed_value"),
        "last_sale_price": parcel.get("last_sale_price"),
        "last_sale_date": parcel.get("last_sale_date"),
        "year_built": parcel.get("year_built"),
        "property_class": parcel.get("property_class") or parcel.get("property_use"),
    }


# ---------------------------------------------------------------------------
# Seam — matched_lead -> scored_lead.
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _output_validator() -> Draft202012Validator:
    schema = json.loads(
        schema_path("scored_lead_record").read_text(encoding="utf-8")
    )
    return Draft202012Validator(schema)


def _validate(record: dict) -> dict:
    """Validate a scored_lead against scored_lead_record.schema.json. Raises
    ValueError on a non-conforming record — the seam fails loud rather than
    write a malformed scored_lead."""
    errors = sorted(
        _output_validator().iter_errors(record), key=lambda e: list(e.path)
    )
    if errors:
        detail = "; ".join(
            f"{list(e.path) or '<root>'}: {e.message}" for e in errors
        )
        raise ValueError(
            "scoring_seam produced a record that violates "
            f"scored_lead_record.schema.json: {detail}"
        )
    return record


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _processed_lead_id(matched_lead: dict, enrichment_status: str) -> str:
    """Deterministic id from matched_lead.lead_id + enrichment_status."""
    digest = hashlib.sha1(
        f"{matched_lead.get('lead_id')}|{enrichment_status}".encode("utf-8")
    ).hexdigest()
    return f"processed_{digest[:16]}"


def process_matched_lead(
    matched_lead: dict,
    *,
    as_of: Optional[date] = None,
    enrichment_provider: Optional[EnrichmentProvider] = None,
    scoring_overrides: Optional[dict] = None,
    multi_property_ids: Optional[set] = None,
    lis_pendens_mode: Optional[str] = None,
) -> dict:
    """Seam — process one matched_lead and emit a processed_lead record.

    Scoring has been removed. The seam attaches enrichment, derives
    attributes, classifies deal paths, and evaluates review queue.

    The contract (R3(iii) enrichment-optional):
      - When `enrichment_provider` is None, OR the provider returns None for
        this matched_lead's parcel_id, the lead is UNENRICHED:
        `attributes = []`, `parcel_display = None`. The lead is NOT dropped.
      - When the provider returns a parcel dict, attributes are derived via
        `normalize.derive_attributes` and `parcel_display` is populated.

    The output is schema-validated; a non-conforming record raises ValueError.
    """
    as_of = as_of or date.today()
    stack = adapt_matched_lead_to_stack(
        matched_lead, as_of=as_of, lis_pendens_mode=lis_pendens_mode
    )

    parcel: Optional[dict] = None
    if enrichment_provider is not None:
        try:
            parcel = enrichment_provider(matched_lead.get("primary_parcel_id"))
        except Exception:  # noqa: BLE001
            parcel = None

    if parcel:
        attributes = derive_attributes(
            parcel,
            stack["active_signals"],
            as_of=as_of,
            multi_property_ids=multi_property_ids,
            scoring_overrides=scoring_overrides,
        )
        enrichment_status = "ENRICHED"
        parcel_display = _parcel_display_from(parcel)
    else:
        attributes = []
        enrichment_status = "UNENRICHED"
        parcel_display = None

    deal_paths = classify_deal_paths(stack, attributes)

    _has_unresolved_lp = any(
        s.get("normalized_doc_type") == "LIS_PENDENS" and s.get("pattern") is None
        for s in stack["active_signals"]
    )

    primary_event = max(
        (s.get("event_date") for s in stack["active_signals"] if s.get("event_date")),
        default=None,
    )
    _seed_flags = list(_seed_review_flags(matched_lead))
    if _has_unresolved_lp:
        _seed_flags.append("lis_pendens_unconfirmed_regime")
    transient = {
        "lead_id": matched_lead.get("lead_id"),
        "primary_parcel_id": matched_lead.get("primary_parcel_id"),
        "patterns": stack["patterns"],
        "match_confidence": 100,
        "title_complexity_score": 0,
        "doc_type_normalization": {
            "doc_type_review_required": False,
        },
        "review_flags": _seed_flags,
        "parcel_display": parcel_display,
        "owner_name": matched_lead.get("owner_name", ""),
        "owner_type": matched_lead.get("owner_type", "UNKNOWN"),
    }
    transient = evaluate_review_queue(transient, now=_now_iso())

    record = {
        "scored_lead_id": _processed_lead_id(matched_lead, enrichment_status),
        "lead_id": matched_lead.get("lead_id"),
        "primary_parcel_id": matched_lead.get("primary_parcel_id"),
        "owner_name": matched_lead.get("owner_name"),
        "owner_type": matched_lead.get("owner_type"),
        "deal_paths": list(deal_paths),
        "pattern_set": list(stack["pattern_set"]),
        "patterns": list(stack["patterns"]),
        "display_patterns": list(stack["patterns"]),
        "stack_depth": stack["stack_depth"],
        "attributes": list(attributes),
        "review_flags": list(transient.get("review_flags", [])),
        "lead_status": transient.get("lead_status"),
        "enrichment_status": enrichment_status,
        "evidence_ids": list(matched_lead.get("evidence_ids") or []),
        "source_ids": list(matched_lead.get("source_ids") or []),
        "source_urls": sorted(
            {
                u
                for g in matched_lead.get("signals") or []
                for u in (g.get("source_urls") or [])
                if u
            }
        ),
        "primary_event_date": primary_event,
        "match_confidence": None,  # populated by a matcher-aware caller
        "doc_type_normalization": {
            "canonical_doc_types": [
                (g.get("canonical_doc_type") or "")
                for g in matched_lead.get("signals") or []
            ],
            "normalized_doc_types": [
                (canonical_doc_type_to_normalized(g.get("canonical_doc_type") or "")
                 or "")
                for g in matched_lead.get("signals") or []
            ],
            "doc_type_review_required": any(
                canonical_doc_type_to_normalized(g.get("canonical_doc_type") or "")
                is None
                for g in matched_lead.get("signals") or []
            ),
        },
        "parcel_display": parcel_display,
        "lead_status_history": list(transient.get("lead_status_history") or []),
    }
    return _validate(record)


def _seed_review_flags(matched_lead: dict) -> list:
    """Carry §17 / parcel REVIEW_REQUIRED context into the scored_lead's
    initial review_flags, so the retained review-queue evaluator routes
    REVIEW_REQUIRED matched leads to REVIEW_REQUIRED scored leads."""
    flags: list = []
    if matched_lead.get("parcel_resolution_status") == "REVIEW_REQUIRED":
        flags.append("parcel_resolution_review_required")
    if matched_lead.get("review_reason"):
        flags.append(f"matched_lead_review_reason:{matched_lead['review_reason']}")
    return flags


# ---------------------------------------------------------------------------
# §20 gate — scoring proceeds only when the §20 verdict permits.
# ---------------------------------------------------------------------------

class SemanticGateBlocked(RuntimeError):
    """Raised when §20 returns DEPLOY_BLOCKED. Scoring / dashboard MUST NOT
    proceed; the operator triages the §20 report."""


class SemanticGateNeedsReview(RuntimeError):
    """Raised when §20 returns NEEDS_OPERATOR_REVIEW and the caller did not
    pass approve_needs_review=True. The cutover sequence's intended behavior
    (per docs/v5.4.0_session6_seam_design.md §4): proceed only on explicit
    operator approval."""


def gate_on_semantic_verdict(
    semantic_report: dict, *, approve_needs_review: bool = False
) -> str:
    """Return the §20 verdict, raising when scoring must NOT proceed.

    - DEPLOY_OK             — return verdict; caller proceeds.
    - DEPLOY_BLOCKED        — raise SemanticGateBlocked.
    - NEEDS_OPERATOR_REVIEW — raise SemanticGateNeedsReview unless
      `approve_needs_review=True`, in which case return the verdict so the
      caller can proceed with the operator's explicit override.
    """
    verdict = semantic_report.get("verdict")
    if verdict == "DEPLOY_BLOCKED":
        raise SemanticGateBlocked(
            "§20 returned DEPLOY_BLOCKED — scoring / dashboard MUST NOT "
            "proceed. Triage the §20 report."
        )
    if verdict == "NEEDS_OPERATOR_REVIEW" and not approve_needs_review:
        raise SemanticGateNeedsReview(
            "§20 returned NEEDS_OPERATOR_REVIEW — proceed only on explicit "
            "operator approval (pass approve_needs_review=True)."
        )
    return verdict


def process_matched_leads(
    matched_leads: list,
    *,
    as_of: Optional[date] = None,
    enrichment_provider: Optional[EnrichmentProvider] = None,
    scoring_overrides: Optional[dict] = None,
    multi_property_ids: Optional[set] = None,
    lis_pendens_mode: Optional[str] = None,
) -> list:
    """Batch helper — call process_matched_lead over every matched_lead in
    deterministic order (sorted by lead_id), returning the processed lead list."""
    ordered = sorted(matched_leads, key=lambda m: m.get("lead_id") or "")
    return [
        process_matched_lead(
            m,
            as_of=as_of,
            enrichment_provider=enrichment_provider,
            scoring_overrides=scoring_overrides,
            multi_property_ids=multi_property_ids,
            lis_pendens_mode=lis_pendens_mode,
        )
        for m in ordered
    ]


# Keep backwards-compatible alias so existing call sites don't break immediately.
score_matched_leads = process_matched_leads
score_matched_lead = process_matched_lead

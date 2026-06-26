"""
scrapers/open_indy_parcels.py

Marion County Assessor ArcGIS enrichment join adapter.

Reads data/raw/marion_recorder.jsonl and data/raw/court_filings.jsonl,
reconstructs the exact placeholder parcel_ids assigned by the pipeline
translators, then queries the Marion County Assessor ArcGIS layer by owner
name and writes data/raw/parcel_master.jsonl in framework canonical shape.

Parcel-id reconstruction mirrors the translator _make_parcel_id logic exactly:
  recorder  -> prefix "MARIN-REC-" + SHA1(doc_number.upper().strip())[:12].upper()
  court     -> prefix "MARIN-CT-"  + SHA1(case_number.upper().strip())[:12].upper()

ArcGIS endpoint (confirmed real):
  https://gis.indy.gov/server/rest/services/MapIndy/MapIndyProperty/MapServer/10/query
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

RECORDER_JSONL = RAW_DIR / "marion_recorder.jsonl"
COURT_JSONL    = RAW_DIR / "court_filings.jsonl"
OUTPUT_JSONL   = RAW_DIR / "parcel_master.jsonl"

ARCGIS_URL = (
    "https://gis.indy.gov/server/rest/services/"
    "MapIndy/MapIndyProperty/MapServer/10/query"
)
OUT_FIELDS = (
    "PARCEL_I,PARCEL_C,STATEPARCELNUMBER,"
    "STNUMBER,PRE_DIR,STREET_NAME,SUFFIX,FULL_STNAME,"
    "CITY,ZIPCODE,FULLOWNERNAME,"
    "OWNERADDRESS,OWNERCITY,OWNERSTATE,OWNERZIP,"
    "ASSESSORYEAR_TOTALAV,ASSESSORYEAR_LANDTOTAL,ASSESSORYEAR_IMPTOTAL,"
    "PROPERTY_CLASS,PROPERTY_SUB_CLASS_DESCRIPTION,ACREAGE"
)

REC_PREFIX = "MARIN-REC-"
CT_PREFIX  = "MARIN-CT-"


# ---------------------------------------------------------------------------
# Parcel-id reconstruction — must be byte-for-byte identical to translator
# ---------------------------------------------------------------------------

def _make_parcel_id(prefix: str, key: str) -> str:
    h   = hashlib.sha1(key.upper().strip().encode("utf-8")).hexdigest()[:12].upper()
    sep = "" if prefix.endswith("-") else "-"
    return f"{prefix}{sep}{h}"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _first_defendant(defendant: str) -> str:
    """Extract first named party before the first comma or ' AND ' (case-insensitive)."""
    import re
    parts = re.split(r",|\bAND\b", defendant, maxsplit=1, flags=re.IGNORECASE)
    return parts[0].strip() if parts else defendant.strip()


# ---------------------------------------------------------------------------
# ArcGIS query
# ---------------------------------------------------------------------------

def _arcgis_query(owner_name: str) -> list[dict]:
    escaped = owner_name.upper().replace("'", "''")
    where   = f"UPPER(FULLOWNERNAME) LIKE '%{escaped}%'"
    params  = urllib.parse.urlencode({
        "where":             where,
        "outFields":         OUT_FIELDS,
        "f":                 "json",
        "returnGeometry":    "false",
        "resultRecordCount": "101",
    })
    url = f"{ARCGIS_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if "error" in body:
            print(
                f"  [WARN] ArcGIS error for {owner_name!r}: {body['error']}",
                file=sys.stderr,
            )
            return []
        return [f["attributes"] for f in body.get("features", [])]
    except Exception as exc:
        print(f"  [WARN] ArcGIS request failed for {owner_name!r}: {exc}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Record assembly
# ---------------------------------------------------------------------------

def _assemble_address(attrs: dict) -> str:
    stnumber    = str(attrs.get("STNUMBER")    or "").strip()
    full_stname = str(attrs.get("FULL_STNAME") or "").strip()
    if full_stname:
        return f"{stnumber} {full_stname}".strip()
    # Fallback: assemble from components when FULL_STNAME is absent
    parts = [
        stnumber,
        str(attrs.get("PRE_DIR")     or "").strip(),
        str(attrs.get("STREET_NAME") or "").strip(),
        str(attrs.get("SUFFIX")      or "").strip(),
    ]
    return " ".join(p for p in parts if p)


def _safe_int(val) -> int | None:
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _safe_float(val) -> float | None:
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _build_pm_record(parcel_id: str, attrs: dict, fetched_at: str) -> dict:
    rid_hash = hashlib.sha1(
        f"{parcel_id}|{attrs.get('FULLOWNERNAME', '')}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "raw_record_id":     f"pm_{rid_hash}",
        "source_id":         "parcel_master",
        "source_fetched_at": fetched_at,
        "parser_confidence": 85,
        "raw_payload": {
            "parcel_id":             parcel_id,
            "address":               _assemble_address(attrs),
            "owner_name":            str(attrs.get("FULLOWNERNAME")  or "").strip() or None,
            "owner_mailing_address": str(attrs.get("OWNERADDRESS")   or "").strip() or None,
            "owner_mailing_city":    str(attrs.get("OWNERCITY")      or "").strip() or None,
            "owner_mailing_state":   str(attrs.get("OWNERSTATE")     or "").strip() or None,
            "owner_mailing_zip":     str(attrs.get("OWNERZIP")       or "").strip() or None,
            "city":                  str(attrs.get("CITY")           or "").strip() or None,
            "zip":                   str(attrs.get("ZIPCODE")        or "").strip() or None,
            "assessed_value":        _safe_int(attrs.get("ASSESSORYEAR_TOTALAV")),
            "land_value":            _safe_int(attrs.get("ASSESSORYEAR_LANDTOTAL")),
            "improvement_value":     _safe_int(attrs.get("ASSESSORYEAR_IMPTOTAL")),
            "year_built":            None,
            "exempt_homestead":      False,
            "exempt_over_65":        False,
            "exempt_disabled":       False,
            "exempt_veteran":        False,
            "property_use":          str(attrs.get("PROPERTY_CLASS") or "").strip() or None,
            "acres":                 _safe_float(attrs.get("ACREAGE")),
            "legal_description":     str(attrs.get("PROPERTY_SUB_CLASS_DESCRIPTION") or "").strip() or None,
        },
    }


# ---------------------------------------------------------------------------
# Main enrichment join
# ---------------------------------------------------------------------------

def run(dry_run: bool = False) -> None:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    recorder_recs = _load_jsonl(RECORDER_JSONL)
    court_recs    = _load_jsonl(COURT_JSONL)

    # Build (parcel_id, owner_name_for_query) list — one entry per raw signal
    items: list[tuple[str, str]] = []

    for raw in recorder_recs:
        payload    = raw.get("raw_payload", {}) or {}
        doc_number = (payload.get("doc_number") or "").strip()
        party1     = (payload.get("party1")     or "").strip()
        if doc_number and party1:
            items.append((_make_parcel_id(REC_PREFIX, doc_number), party1))

    for raw in court_recs:
        payload     = raw.get("raw_payload", {}) or {}
        case_number = (payload.get("case_number") or "").strip()
        defendant   = (payload.get("defendant")   or "").strip()
        if case_number and defendant:
            items.append((_make_parcel_id(CT_PREFIX, case_number), _first_defendant(defendant)))

    # Deduplicate by parcel_id — each placeholder parcel_id is queried once.
    seen_ids: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for pid, oname in items:
        if pid not in seen_ids:
            seen_ids.add(pid)
            deduped.append((pid, oname))
    items = deduped

    total = len(items)
    print(
        f"Signals loaded: {len(recorder_recs)} recorder + {len(court_recs)} court "
        f"= {total} unique parcel-ids to enrich"
    )

    out_records: list[dict] = []
    matched  = 0
    skipped  = 0
    sample_shown = False

    for idx, (parcel_id, owner_name) in enumerate(items):
        if idx > 0:
            time.sleep(0.5)

        features = _arcgis_query(owner_name)

        if not features:
            skipped += 1
        elif len(features) >= 100:
            # Too many hits — name is too generic or matches a corporate portfolio;
            # skip rather than emit a random parcel.
            skipped += 1
        else:
            attrs = features[0]  # first result; assessor returns in parcel_id order
            out_records.append(_build_pm_record(parcel_id, attrs, fetched_at))
            matched += 1
            if not sample_shown:
                print(f"  Sample match:")
                print(f"    parcel_id    : {parcel_id}")
                print(f"    query owner  : {owner_name!r}")
                print(f"    assessor name: {attrs.get('FULLOWNERNAME')!r}")
                sample_shown = True

        if (idx + 1) % 20 == 0 or (idx + 1) == total:
            pct = round((idx + 1) / total * 100)
            print(f"  [{pct:3d}%] {idx + 1}/{total} processed — {matched} matched, {skipped} skipped")

    print(f"\nResults: {total} processed | {matched} matched | {skipped} skipped")

    if dry_run:
        print(f"[dry-run] Would write {len(out_records)} records to {OUTPUT_JSONL}")
        return

    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSONL.open("w", encoding="utf-8") as f:
        for rec in out_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out_records)} records to {OUTPUT_JSONL}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run(dry_run=dry_run)

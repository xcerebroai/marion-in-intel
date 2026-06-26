"""
scrapers/code_enforcement.py

Marion County / City of Indianapolis Department of Code Enforcement (DCE)
adapter. Pulls open code-enforcement cases from the OpenIndy non-spatial
ArcGIS REST dataset and writes framework-canonical (§4.32 wrapped) raw
records to data/raw/code_enforcement.jsonl.

source_id: code_enforcement
endpoint:  https://gis.indy.gov/server/rest/services/
           OpenData/OpenData_NonSpatial/MapServer/1/query

Confirmed fields (live probe 2026-06-26):
  CASE_NUMBER, CASE_TYPE, CASE_STATUS, OPEN_DATE, STREET_ADDRESS,
  CITY, STATE, ZIP, OWNER, TOWNSHIP, LINK

Query strategy:
  - WHERE  CASE_STATUS IN ('Open','Overdue','In Violation')
           AND OPEN_DATE >= DATE '<N days ago>'
    (ArcGIS rejects raw epoch-ms comparison on the date field with HTTP 400;
     the `DATE 'YYYY-MM-DD'` literal is the confirmed working syntax.)
  - High-value case types (Unsafe Buildings, Vacant Board Order, Vacant -
    Board Up Order, Zoning Violation) are NOT filtered out — all Open /
    Overdue / In Violation cases are pulled; the high-value list is recorded
    on each record as `high_value` for downstream prioritization.
  - Pagination: resultOffset + resultRecordCount=1000; 0.5s between requests.

OPEN_DATE comes back as Unix epoch milliseconds and is converted to
YYYY-MM-DD (UTC) for recording_date.

parcel_id: "MARIN-DCE-" + SHA1(CASE_NUMBER.upper().strip())[:12].upper()

All real owner names / addresses stay in data/raw/ (gitignored).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_ID = "code_enforcement"
DOC_TYPE = "CODE_VIOLATION_NOTICE"
PARCEL_PREFIX = "MARIN-DCE-"

ARCGIS_URL = (
    "https://gis.indy.gov/server/rest/services/"
    "OpenData/OpenData_NonSpatial/MapServer/1/query"
)
TARGET_STATUSES = ("Open", "Overdue", "In Violation")
HIGH_VALUE_CASE_TYPES = {
    "UNSAFE BUILDINGS",
    "VACANT BOARD ORDER",
    "VACANT - BOARD UP ORDER",
    "ZONING VIOLATION",
}
OUT_FIELDS = (
    "CASE_NUMBER,CASE_TYPE,CASE_STATUS,OPEN_DATE,STREET_ADDRESS,"
    "CITY,STATE,ZIP,OWNER,TOWNSHIP,LINK"
)
PAGE_SIZE = 1000
RATE_LIMIT_SECONDS = 0.5
DEFAULT_SOURCE_URL = "https://data.indy.gov/datasets/5d08eba2e9034bc88986af25afe12f5e_1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _epoch_ms_to_date(value) -> str | None:
    """Convert an ArcGIS epoch-millisecond timestamp to YYYY-MM-DD (UTC)."""
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _parcel_id(case_number: str) -> str:
    h = hashlib.sha1(case_number.upper().strip().encode("utf-8")).hexdigest()[:12].upper()
    return f"{PARCEL_PREFIX}{h}"


def _build_where(days_back: int) -> str:
    cutoff = (date.today() - timedelta(days=days_back)).isoformat()
    statuses = ", ".join(f"'{s}'" for s in TARGET_STATUSES)
    return f"CASE_STATUS IN ({statuses}) AND OPEN_DATE >= DATE '{cutoff}'"


def _query(where: str, offset: int) -> dict:
    params = urllib.parse.urlencode({
        "where":             where,
        "outFields":         OUT_FIELDS,
        "f":                 "json",
        "returnGeometry":    "false",
        "orderByFields":     "OPEN_DATE DESC",
        "resultOffset":      str(offset),
        "resultRecordCount": str(PAGE_SIZE),
    })
    url = f"{ARCGIS_URL}?{params}"
    with urllib.request.urlopen(url, timeout=40) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    if "error" in body:
        raise RuntimeError(f"ArcGIS error: {body['error']}")
    return body


def _wrap(attrs: dict, fetched_at: str) -> dict:
    case_number = str(attrs.get("CASE_NUMBER") or "").strip()
    case_type = str(attrs.get("CASE_TYPE") or "").strip()
    case_status = str(attrs.get("CASE_STATUS") or "").strip()
    link = str(attrs.get("LINK") or "").strip() or DEFAULT_SOURCE_URL
    parcel_id = _parcel_id(case_number)

    payload = {
        "parcel_id":          parcel_id,
        "doc_type":           DOC_TYPE,
        "doc_number":         case_number,
        "instrument_number":  case_number,
        "recording_date":     _epoch_ms_to_date(attrs.get("OPEN_DATE")),
        "grantor":            str(attrs.get("OWNER") or "").strip() or None,
        "grantee":            None,
        "address":            str(attrs.get("STREET_ADDRESS") or "").strip(),
        "city":               str(attrs.get("CITY") or "").strip(),
        "state":              str(attrs.get("STATE") or "IN").strip() or "IN",
        "zip":                str(attrs.get("ZIP") or "").strip(),
        "case_type":          case_type,
        "case_status":        case_status,
        "township":           str(attrs.get("TOWNSHIP") or "").strip() or None,
        "high_value":         case_type.upper() in HIGH_VALUE_CASE_TYPES,
        "source_url":         link,
    }
    return {
        "raw_record_id":     f"dce_{hashlib.sha1(case_number.upper().strip().encode()).hexdigest()[:16]}",
        "source_id":         SOURCE_ID,
        "source_url":        link,
        "source_fetched_at": fetched_at,
        "parser_confidence": 90,
        "raw_payload":       payload,
    }


def run(days_back: int = 30, output_path: Path | None = None) -> dict:
    if output_path is None:
        output_path = REPO_ROOT / "data" / "raw" / f"{SOURCE_ID}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    where = _build_where(days_back)
    fetched_at = _now_iso()
    stats: dict = {
        "source_id":       SOURCE_ID,
        "where":           where,
        "pages_fetched":   0,
        "records_written": 0,
        "high_value":      0,
        "sample_cases":    [],
        "error":           None,
    }

    records: list[dict] = []
    offset = 0
    try:
        while True:
            body = _query(where, offset)
            feats = body.get("features", []) or []
            stats["pages_fetched"] += 1
            for f in feats:
                rec = _wrap(f.get("attributes", {}) or {}, fetched_at)
                records.append(rec)
                if rec["raw_payload"]["high_value"]:
                    stats["high_value"] += 1
                if len(stats["sample_cases"]) < 5:
                    stats["sample_cases"].append(rec["raw_payload"]["doc_number"])
            # Continue only while the server signals more rows remain.
            if not feats or not body.get("exceededTransferLimit", False):
                break
            offset += PAGE_SIZE
            time.sleep(RATE_LIMIT_SECONDS)
    except Exception as exc:  # noqa: BLE001 — surface any pull error in stats
        stats["error"] = str(exc)

    tmp = output_path.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tmp.replace(output_path)

    stats["records_written"] = len(records)
    stats["output_path"] = str(output_path)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pull Marion County code-enforcement cases (OpenIndy ArcGIS)."
    )
    parser.add_argument(
        "--days-back", type=int, default=30,
        help="Pull cases with OPEN_DATE within the last N days. Default 30.",
    )
    parser.add_argument(
        "--out", default=None,
        help=f"Output JSONL path. Default: data/raw/{SOURCE_ID}.jsonl",
    )
    args = parser.parse_args()

    out = Path(args.out) if args.out else None
    stats = run(days_back=args.days_back, output_path=out)
    print(json.dumps(stats, indent=2))
    if stats.get("error"):
        print(f"\nERROR: {stats['error']}", file=sys.stderr)
        return 1
    print(
        f"\nPulled {stats['records_written']} code-enforcement records "
        f"({stats['high_value']} high-value) -> {stats['output_path']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

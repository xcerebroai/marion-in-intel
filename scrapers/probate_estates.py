"""
scrapers/probate_estates.py

Probate / estate lead generator via a Marion County Assessor ArcGIS owner-name
sweep. Queries the assessor parcel layer for owners whose FULLOWNERNAME matches
estate / decedent / heirship patterns, filters out corporate false positives,
and writes framework-canonical (§4.32 wrapped) raw records to
data/raw/probate_estates.jsonl.

No recorder filing is needed: a parcel still titled to "ESTATE OF ..." /
"HEIRS OF ..." / a testamentary trust is itself the probate signal.

source_id: probate_estates
endpoint:  https://gis.indy.gov/server/rest/services/
           MapIndy/MapIndyProperty/MapServer/10/query

Estate owner-name patterns pulled (server-side LIKE):
  %ESTATE OF%, % EST OF %, % EST %, %HEIRS OF%, %HEIR OF%,
  %DECEASED%, %TESTAMENTARY%, %DEVISEES%

False-positive exclusion (client-side): a name is dropped when it carries a
corporate / institutional designator (LLC, INC, CORP, PROPERTIES, REALTY,
BANK, ...). Designators are matched on WORD BOUNDARIES so legitimate personal
names that merely contain the letters (e.g. "VINCENT" containing "INC",
"PHILP" containing "LP") are NOT wrongly excluded — only standalone corporate
tokens trigger the drop.

  "ESTATE OF MARY ANN LOPEZ"          -> KEEP
  "EST OF MARY ANN LOPEZ"             -> KEEP
  "PROPERTY ESTATE BUYERS LLC"        -> EXCLUDE (LLC, BUYERS)
  "HERITAGE ESTATE PROPERTIES INC"    -> EXCLUDE (INC, PROPERTIES)

parcel_id: "MARIN-PRO-" + SHA1(STATEPARCELNUMBER.upper().strip())[:12].upper()

Owner names from assessor data are public record (they appear on the
dashboard) so printing owner-name samples to stdout is permitted; addresses
are NOT printed. All records stay in data/raw/ (gitignored).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_ID = "probate_estates"
DOC_TYPE = "AFFIDAVIT_OF_HEIRSHIP"
PARCEL_PREFIX = "MARIN-PRO-"
SOURCE_URL = "https://www.indy.gov/activity/property-search"

ARCGIS_URL = (
    "https://gis.indy.gov/server/rest/services/"
    "MapIndy/MapIndyProperty/MapServer/10/query"
)
OUT_FIELDS = (
    "PARCEL_I,STATEPARCELNUMBER,"
    "STNUMBER,PRE_DIR,STREET_NAME,SUFFIX,FULL_STNAME,"
    "CITY,ZIPCODE,FULLOWNERNAME,ASSESSORYEAR_TOTALAV"
)
ESTATE_WHERE = (
    "UPPER(FULLOWNERNAME) LIKE '%ESTATE OF%' "
    "OR UPPER(FULLOWNERNAME) LIKE '% EST OF %' "
    "OR UPPER(FULLOWNERNAME) LIKE '% EST %' "
    "OR UPPER(FULLOWNERNAME) LIKE '%HEIRS OF%' "
    "OR UPPER(FULLOWNERNAME) LIKE '%HEIR OF%' "
    "OR UPPER(FULLOWNERNAME) LIKE '%DECEASED%' "
    "OR UPPER(FULLOWNERNAME) LIKE '%TESTAMENTARY%' "
    "OR UPPER(FULLOWNERNAME) LIKE '%DEVISEES%'"
)
PAGE_SIZE = 1000
RATE_LIMIT_SECONDS = 0.5

# Corporate / institutional designators. A name carrying any of these (on a
# word boundary) is a company, not an estate, and is excluded. Multi-word and
# punctuated forms ("TRUST CO", "L.L.C", "CO.") are matched as-is.
_EXCLUDE_TOKENS = [
    r"LLC", r"L\.L\.C", r"INC", r"CORP", r"CO\.", r"LTD", r"LP", r"LLP",
    r"PARTNERSHIP", r"ASSOCIATES", r"GROUP", r"HOLDINGS", r"PROPERTIES",
    r"REALTY", r"INVESTMENTS", r"MANAGEMENT", r"ENTERPRISES", r"SERVICES",
    r"SOLUTIONS", r"BUYERS", r"CAPITAL", r"FUND", r"TRUST CO", r"BANK",
    r"FINANCIAL",
]
_EXCLUDE_RE = re.compile(
    r"(?<![A-Z])(?:" + "|".join(_EXCLUDE_TOKENS) + r")(?![A-Z])",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _is_company(owner_name: str) -> bool:
    """True when the owner name carries a corporate/institutional designator."""
    return bool(_EXCLUDE_RE.search(owner_name or ""))


def _parcel_id(state_parcel: str) -> str:
    h = hashlib.sha1(state_parcel.upper().strip().encode("utf-8")).hexdigest()[:12].upper()
    return f"{PARCEL_PREFIX}{h}"


def _assemble_address(attrs: dict) -> str:
    full_stname = str(attrs.get("FULL_STNAME") or "").strip()
    stnumber = str(attrs.get("STNUMBER") or "").strip()
    if full_stname:
        return f"{stnumber} {full_stname}".strip()
    parts = [
        stnumber,
        str(attrs.get("PRE_DIR") or "").strip(),
        str(attrs.get("STREET_NAME") or "").strip(),
        str(attrs.get("SUFFIX") or "").strip(),
    ]
    return " ".join(p for p in parts if p)


def _query(offset: int) -> dict:
    params = urllib.parse.urlencode({
        "where":             ESTATE_WHERE,
        "outFields":         OUT_FIELDS,
        "f":                 "json",
        "returnGeometry":    "false",
        "orderByFields":     "STATEPARCELNUMBER ASC",
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
    state_parcel = str(attrs.get("STATEPARCELNUMBER") or "").strip()
    raw_id = state_parcel or str(attrs.get("PARCEL_I") or "").strip()
    owner = str(attrs.get("FULLOWNERNAME") or "").strip()
    av = attrs.get("ASSESSORYEAR_TOTALAV")
    payload = {
        "parcel_id":          _parcel_id(raw_id),
        "doc_type":           DOC_TYPE,
        "doc_number":         state_parcel or None,
        "instrument_number":  None,
        "recording_date":     None,
        "grantor":            owner or None,
        "grantee":            None,
        "address":            _assemble_address(attrs),
        "city":               str(attrs.get("CITY") or "").strip(),
        "state":              "IN",
        "zip":                str(attrs.get("ZIPCODE") or "").strip(),
        "assessed_value":     str(int(av)) if isinstance(av, (int, float)) else None,
        "source_url":         SOURCE_URL,
    }
    return {
        "raw_record_id":     f"pro_{hashlib.sha1(raw_id.upper().strip().encode()).hexdigest()[:16]}",
        "source_id":         SOURCE_ID,
        "source_url":        SOURCE_URL,
        "source_fetched_at": fetched_at,
        "parser_confidence": 80,
        "raw_payload":       payload,
    }


def run(output_path: Path | None = None) -> dict:
    if output_path is None:
        output_path = REPO_ROOT / "data" / "raw" / f"{SOURCE_ID}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fetched_at = _now_iso()
    stats: dict = {
        "source_id":         SOURCE_ID,
        "raw_results":       0,
        "excluded_company":  0,
        "estate_leads":      0,
        "sample_owners":     [],
        "error":             None,
    }

    records: list[dict] = []
    offset = 0
    try:
        while True:
            body = _query(offset)
            feats = body.get("features", []) or []
            stats["raw_results"] += len(feats)
            for f in feats:
                attrs = f.get("attributes", {}) or {}
                owner = str(attrs.get("FULLOWNERNAME") or "").strip()
                if _is_company(owner):
                    stats["excluded_company"] += 1
                    continue
                records.append(_wrap(attrs, fetched_at))
                if len(stats["sample_owners"]) < 3 and owner:
                    stats["sample_owners"].append(owner)
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

    stats["estate_leads"] = len(records)
    stats["output_path"] = str(output_path)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sweep Marion County Assessor ArcGIS for estate/probate owner names."
    )
    parser.add_argument(
        "--out", default=None,
        help=f"Output JSONL path. Default: data/raw/{SOURCE_ID}.jsonl",
    )
    args = parser.parse_args()

    out = Path(args.out) if args.out else None
    stats = run(output_path=out)
    # Owner names are public record (they appear on the dashboard) — safe to
    # print. Addresses are NOT printed.
    print(json.dumps(stats, indent=2))
    if stats.get("error"):
        print(f"\nERROR: {stats['error']}", file=sys.stderr)
        return 1
    print(
        f"\nRaw ArcGIS results: {stats['raw_results']} | "
        f"excluded as companies: {stats['excluded_company']} | "
        f"genuine estate leads: {stats['estate_leads']} -> {stats['output_path']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

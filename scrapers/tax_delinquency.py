"""
scrapers/tax_delinquency.py

Marion County (IN) annual tax-sale delinquency list adapter.

The Marion County Treasurer publishes the annual tax-sale reports through the
indy.gov CMS, which is a JS SPA backed by a public GraphCMS (Hygraph) read API.
The "Tax Sale Reports" activity exposes, per year, a set of report PDFs:

  - Sold List           (sold parcels; HAS situs address)
  - County Lien List    (parcels struck to the county; HAS situs address)
  - Status List         (every tax-sale parcel; NO address)
  - Combination List    (parent/child parcel groupings; NO address)

Only the Sold List and County Lien List carry situs addresses, and the
downstream pipeline translators require an address per record, so those two
reports are the lead-bearing sources. Both share the same column layout:

  # | Bidder ID | Parcel # | Primary Owner | Parcel Location | Face Value | Overbid | Purchase Amount

Face Value is the delinquent tax amount that put the parcel into the sale.

This adapter:
  1. Resolves the latest published year's report PDF URLs via the GraphCMS API
     (robust across annual republication — no hard-coded asset ids).
  2. Downloads the address-bearing report PDFs and extracts their tables with
     pdfplumber.
  3. Writes data/raw/tax_delinquency.jsonl in the flat shape consumed by the
     csv_static_list translator.

GraphCMS endpoint (confirmed real, public read):
  https://api-us-east-1-indy.graphcms.com/v2/ckp3xrh1i657g01xp53az2mv4/master
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_JSONL = RAW_DIR / "tax_delinquency.jsonl"
COUNTY_CONFIG = ROOT / "config" / "counties" / "marion_in.json"

GRAPHCMS_ENDPOINT = (
    "https://api-us-east-1-indy.graphcms.com/v2/"
    "ckp3xrh1i657g01xp53az2mv4/master"
)
ACTIVITY_SLUG = "tax-sale-reports"
PUBLIC_PAGE = "https://www.indy.gov/activity/tax-sale-reports"

PARCEL_ID_PREFIX = "MARIN-TX-"
SOURCE_ID = "tax_delinquency"
DOC_TYPE = "TAX_FORECLOSURE_NOTICE"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) marion-in-intel/1.0"

# Report labels whose PDFs include a situs address ("Parcel Location" column).
ADDRESS_BEARING_LABELS = ("sold list", "county lien list")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _http(url: str, *, data: bytes | None = None, headers: dict | None = None,
          timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, data=data, headers=headers or {})
    req.add_header("User-Agent", UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _graphql(query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    raw = _http(
        GRAPHCMS_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Resolve the latest-year report PDF URLs from the CMS
# ---------------------------------------------------------------------------

_ACTIVITY_QUERY = (
    "query($slug:String){ activities(where:{slug:$slug}){ "
    "accordions{ items{ title description{ html } } } } }"
)
_YEAR_ITEM_RE = re.compile(r"^\s*(\d{4})\s+Tax Sale Reports", re.I)
_ANCHOR_RE = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)


def resolve_report_urls(year: int | None = None) -> tuple[int, list[tuple[str, str]]]:
    """Return (resolved_year, [(label, href), ...]) for address-bearing reports.

    If ``year`` is None, the most recent published year is selected.
    """
    data = _graphql(_ACTIVITY_QUERY, {"slug": ACTIVITY_SLUG})
    activities = (data.get("data", {}) or {}).get("activities") or []
    if not activities:
        raise RuntimeError("CMS returned no tax-sale-reports activity")

    # Collect (year -> {label: href}) across every accordion item.
    by_year: dict[int, list[tuple[str, str]]] = {}
    for accordion in activities[0].get("accordions", []) or []:
        for item in accordion.get("items", []) or []:
            m = _YEAR_ITEM_RE.match(item.get("title") or "")
            if not m:
                continue
            yr = int(m.group(1))
            html = (item.get("description") or {}).get("html") or ""
            links = [
                (re.sub(r"<[^>]+>", "", label).strip(), href)
                for href, label in (
                    (mt.group(1), mt.group(2)) for mt in _ANCHOR_RE.finditer(html)
                )
            ]
            by_year.setdefault(yr, []).extend(links)

    if not by_year:
        raise RuntimeError("No year-tagged tax sale report items found")

    target = year if year is not None else max(by_year)
    if target not in by_year:
        raise RuntimeError(f"No reports published for year {target}")

    wanted = [
        (label, href)
        for (label, href) in by_year[target]
        if any(k in label.lower() for k in ADDRESS_BEARING_LABELS)
    ]
    return target, wanted


# ---------------------------------------------------------------------------
# Address parsing
# ---------------------------------------------------------------------------

def _load_accepted_cities() -> list[str]:
    cfg = json.loads(COUNTY_CONFIG.read_text(encoding="utf-8"))
    muni = cfg.get("geography", {}).get("accepted_municipalities", []) or []
    names = [m["name"].upper().strip() for m in muni if m.get("name")]
    # Longest first so multi-word cities ("BEECH GROVE") match before substrings.
    return sorted(set(names), key=len, reverse=True)


_LOC_RE = re.compile(r"^(.*?)\s*,?\s+IN\s+(\d{5})(?:-\d{4})?\s*$", re.I)


def parse_location(location: str, cities: list[str]) -> tuple[str, str, str]:
    """Split 'STREET CITY, IN ZIP' into (street, city, zip).

    Falls back gracefully: if the city can't be isolated, the whole
    pre-state remainder is returned as the street and city is "".
    """
    loc = re.sub(r"\s+", " ", (location or "").strip().upper())
    m = _LOC_RE.match(loc)
    if not m:
        return loc, "", ""
    pre, zip_code = m.group(1).strip(), m.group(2)
    for city in cities:
        if pre.endswith(" " + city) or pre == city:
            street = pre[: len(pre) - len(city)].strip()
            return street, city, zip_code
    return pre, "", zip_code


def _clean_amount(value: str) -> str:
    """Normalize Face Value cells like '6 ,441.79' -> '6,441.79'."""
    if not value:
        return ""
    cleaned = re.sub(r"\s+", "", value.strip())
    return "" if cleaned in {"-", ""} else cleaned


# ---------------------------------------------------------------------------
# PDF table parsing
# ---------------------------------------------------------------------------

_HEADER_TOKENS = ("parcel #", "primary owner", "parcel location")
_PARCEL_RE = re.compile(r"^\d{6,}$")


def _find_columns(row: list) -> dict | None:
    """Given a header row, map canonical column names to indices."""
    norm = [(c or "").strip().lower() for c in row]
    if not all(any(tok in cell for cell in norm) for tok in _HEADER_TOKENS):
        return None
    cols = {}
    for idx, cell in enumerate(norm):
        if cell == "parcel #":
            cols["parcel"] = idx
        elif cell == "primary owner":
            cols["owner"] = idx
        elif cell == "parcel location":
            cols["location"] = idx
        elif cell == "face value":
            cols["face"] = idx
    return cols if {"parcel", "owner", "location", "face"} <= cols.keys() else None


def parse_report_pdf(pdf_bytes: bytes) -> list[dict]:
    """Extract (parcel, owner, location, face_value) rows from a report PDF."""
    rows: list[dict] = []
    tmp = RAW_DIR / f".tax_dl_tmp_{hashlib.sha1(pdf_bytes[:64]).hexdigest()[:8]}.pdf"
    tmp.write_bytes(pdf_bytes)
    try:
        with pdfplumber.open(str(tmp)) as pdf:
            cols: dict | None = None
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue
                for row in table:
                    if not row:
                        continue
                    header = _find_columns(row)
                    if header:
                        cols = header
                        continue
                    if not cols or len(row) <= max(cols.values()):
                        continue
                    parcel = (row[cols["parcel"]] or "").strip()
                    if not _PARCEL_RE.match(parcel):
                        continue
                    rows.append({
                        "parcel": parcel,
                        "owner": (row[cols["owner"]] or "").strip(),
                        "location": (row[cols["location"]] or "").strip(),
                        "face": _clean_amount(row[cols["face"]] or ""),
                    })
    finally:
        tmp.unlink(missing_ok=True)
    return rows


# ---------------------------------------------------------------------------
# Record building
# ---------------------------------------------------------------------------

def build_record(entry: dict, cities: list[str], recorded_date: str) -> dict:
    parcel = entry["parcel"]
    street, city, zip_code = parse_location(entry["location"], cities)
    parcel_hash = hashlib.sha1(parcel.upper().strip().encode("utf-8")).hexdigest()[:12].upper()
    return {
        "source_id": SOURCE_ID,
        "raw_record_id": f"tax_{parcel}",
        "doc_type": DOC_TYPE,
        "recorded_date": recorded_date,
        "grantor": entry["owner"] or None,
        "grantee": None,
        "instrument_number": parcel,
        "address": street,
        "city": city,
        "state": "IN",
        "zip": zip_code,
        "source_url": f"{PUBLIC_PAGE}#parcel={parcel}",
        "delinquent_amount": entry["face"],
        "parcel_id": f"{PARCEL_ID_PREFIX}{parcel_hash}",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Marion County IN tax delinquency scraper")
    ap.add_argument("--year", type=int, default=None,
                    help="Tax sale year to pull (default: latest published)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap number of output records (debug)")
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cities = _load_accepted_cities()
    recorded_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    year, reports = resolve_report_urls(args.year)
    if not reports:
        print(f"[tax_delinquency] no address-bearing reports for {year}", file=sys.stderr)
        return 1
    print(f"[tax_delinquency] year={year} reports={[lbl for lbl, _ in reports]}",
          file=sys.stderr)

    merged: dict[str, dict] = {}  # parcel -> entry (dedupe across reports)
    for label, href in reports:
        try:
            pdf_bytes = _http(href, timeout=120)
        except Exception as exc:  # noqa: BLE001
            print(f"[tax_delinquency] download failed for {label}: {exc}", file=sys.stderr)
            continue
        entries = parse_report_pdf(pdf_bytes)
        print(f"[tax_delinquency]   {label}: {len(entries)} rows", file=sys.stderr)
        for e in entries:
            merged.setdefault(e["parcel"], e)

    records = [build_record(e, cities, recorded_date) for e in merged.values()]
    if args.limit:
        records = records[: args.limit]

    with OUTPUT_JSONL.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with_addr = sum(1 for r in records if r["address"])
    print(f"[tax_delinquency] wrote {len(records)} records "
          f"({with_addr} with street address) -> {OUTPUT_JSONL}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

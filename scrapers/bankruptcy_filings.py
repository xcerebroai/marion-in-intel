"""
Marion County bankruptcy-filings adapter — CourtListener RECAP (Indiana Southern
District / court code `insb`).

source_id: bankruptcy_filings
output:    data/raw/bankruptcy_filings.jsonl
lead type: Bankruptcy Petition  ·  regime: IN_judicial_foreclosure (distress signal)

Marion County sits in the U.S. Bankruptcy Court, Southern District of Indiana
(`insb`). A Chapter 7 (liquidation) or Chapter 13 (wage-earner reorganization)
petition is a strong financial-distress signal for the property owner.

API recon (live, 2026-06-26):
  - The documented v3/v4 *dockets* endpoint now returns HTTP 401 for anonymous
      callers ("Authentication credentials were not provided"). v3 *search* is
      403 ("Anonymous users don't have permission"). The ONLY no-auth path that
      still works is the **v4 search** endpoint with `type=r` (RECAP):

          https://www.courtlistener.com/api/rest/v4/search/?type=r&court=insb&filed_after=<date>

      Confirmed free, no token. Returns the metadata we need:
          docketNumber, chapter ("7"/"13"), caseName, party[] (debtor names),
          dateFiled, dateTerminated, docket_absolute_url, court_id, suitNature.
  - NO debtor street address / city / zip is exposed in the free metadata
      (consistent with PACER free-tier limits). Coverage is therefore the whole
      Southern District of Indiana, not Marion-only — flagged `partial_recap`.
  - Pagination is cursor-based via the response `next` URL.
  - Free tier: rate-limit to ~1 request/second.

Output contract: framework-canonical WRAPPED raw record (MASTER_PROMPT §4.32),
same shape every other adapter in this repo writes (see scrapers/court_filings.py).
The downstream `foreclosure_notices` translator reads `raw_payload` and needs a
non-empty `address` + `doc_number`; the free API has no street address, so the
docket number doubles as the parcel KEY. That makes the translator's placeholder
parcel_id resolve to exactly:

    MARIN-BK- + SHA1(docket_number.upper().strip())[:12].upper()

Every descriptive field the operator cares about (debtor name, chapter, the
absolute case URL, the precomputed parcel_id) is also carried in raw_payload for
traceability. Debtor names stay in data/raw/ (gitignored); only docket numbers,
chapters and counts ever reach stdout.
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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SOURCE_ID = "bankruptcy_filings"
COURT_CODE = "insb"
PARCEL_ID_PREFIX = "MARIN-BK-"

_API_BASE = "https://www.courtlistener.com/api/rest/v4/search/"
_SITE_BASE = "https://www.courtlistener.com"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 marion-in-intel/1.0"
)

_DEFAULT_CHAPTERS = ("7", "13")     # most distress-relevant petitions
_RATE_LIMIT_SECONDS = 1.5           # polite base pace between requests
_MAX_PAGES = 400                    # safety backstop onn cursor pagination
_REQUEST_TIMEOUT = 45


# ---------------------------------------------------------------------------
# Small helpers — time, ids, dates.
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _parcel_id(docket_number: str) -> str:
    """Placeholder parcel id — matches foreclosure_notices._make_parcel_id with
    address == docket_number. Prefix ends with '-', so no extra separator."""
    h = hashlib.sha1(docket_number.upper().strip().encode("utf-8")).hexdigest()[:12].upper()
    return f"{PARCEL_ID_PREFIX}{h}"


def _record_id(docket_number: str) -> str:
    """Deterministic raw_record_id from the docket number."""
    h = hashlib.sha1(f"{SOURCE_ID}|{docket_number}".encode("utf-8")).hexdigest()[:20]
    return f"bk_{h}"


def _normalize_date(raw: str) -> str:
    """CourtListener dates are already ISO YYYY-MM-DD; pass through defensively."""
    if not raw:
        return ""
    raw = raw.strip()
    if "T" in raw:
        return raw.split("T")[0]
    if len(raw) >= 10 and raw[4] == "-":
        return raw[:10]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def _year_month(iso_date: str) -> tuple[int | None, int | None]:
    if not iso_date or len(iso_date) < 7 or iso_date[4] != "-":
        return None, None
    try:
        return int(iso_date[:4]), int(iso_date[5:7])
    except ValueError:
        return None, None


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _get_json(url: str) -> dict:
    for attempt in range(4):
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                retry_after = int(exc.headers.get("Retry-After", 60))
                print(f"  429 rate-limited — backing off {retry_after}s (attempt {attempt+1}/4)", file=sys.stderr)
                time.sleep(retry_after)
                continue
            raise
    raise RuntimeError("Exceeded 429 retry limit on CourtListener")


def _build_url(filed_after: str) -> str:
    params = {
        "type": "r",                  # RECAP (federal court dockets)
        "court": COURT_CODE,
        "filed_after": filed_after,   # MM/DD/YYYY or YYYY-MM-DD both accepted
        "order_by": "dateFiled desc",
    }
    return _API_BASE + "?" + urllib.parse.urlencode(params)


# ---------------------------------------------------------------------------
# Record normalization + §4.32 wrapping
# ---------------------------------------------------------------------------

def _first_debtor(result: dict) -> str:
    """First debtor name — prefer the structured party[] list, fall back to
    caseName. Returns '' when neither is present."""
    party = result.get("party")
    if isinstance(party, list):
        for p in party:
            if isinstance(p, str) and p.strip():
                return p.strip()
    case_name = result.get("caseName")
    return case_name.strip() if isinstance(case_name, str) else ""


def _absolute_url(result: dict) -> str:
    rel = result.get("docket_absolute_url") or ""
    if rel.startswith("http"):
        return rel
    if rel:
        return _SITE_BASE + rel
    return _SITE_BASE


def _wrap(result: dict, fetched_at: str) -> dict | None:
    """Map one v4 search RECAP hit to a §4.32 wrapped raw record. Returns None
    when the docket number is missing (cannot key a parcel)."""
    docket_number = (result.get("docketNumber") or "").strip()
    if not docket_number:
        return None

    chapter = str(result.get("chapter") or "").strip()
    recorded_date = _normalize_date(result.get("dateFiled") or "")
    rec_year, rec_month = _year_month(recorded_date)
    debtor = _first_debtor(result)
    source_url = _absolute_url(result)
    parcel_id = _parcel_id(docket_number)

    # raw_payload carries BOTH the fields the foreclosure_notices translator
    # consumes (address, doc_number, recording_year/month, city, zip) AND the
    # operator-facing descriptive fields enumerated in the task contract.
    raw_payload = {
        # --- translator-consumed (canonical names) ---
        "address": docket_number,        # parcel KEY → MARIN-BK-+SHA1(docket)
        "doc_number": docket_number,
        "recording_year": rec_year,
        "recording_month": rec_month,
        "city": "",                      # no situs city in free RECAP metadata
        "zip": "",
        # --- descriptive / task-contract fields ---
        "doc_type": "BANKRUPTCY_PETITION",
        "recorded_date": recorded_date,
        "grantor": debtor,               # first debtor (party[0])
        "grantee": None,
        "instrument_number": docket_number,
        "parcel_id": parcel_id,
        "state": "IN",
        "chapter": chapter,
        "case_name": (result.get("caseName") or "").strip(),
        "date_terminated": _normalize_date(result.get("dateTerminated") or ""),
        "court_id": result.get("court_id") or COURT_CODE,
        "pacer_case_id": result.get("pacer_case_id") or "",
        "coverage": "partial_recap",
    }

    return {
        "raw_record_id": _record_id(docket_number),
        "source_id": SOURCE_ID,
        "source_url": source_url,
        "source_fetched_at": fetched_at,
        "parser_confidence": 85,
        "raw_payload": raw_payload,
    }


# ---------------------------------------------------------------------------
# Fetch loop
# ---------------------------------------------------------------------------

def _fetch_all(filed_after: str, chapters: tuple[str, ...], stats: dict) -> list[dict]:
    """Walk the cursor-paginated v4 search results, keeping Ch7/13 insb dockets.
    Dedup by docket number."""
    keep_chapters = set(chapters)
    by_docket: dict[str, dict] = {}
    url = _build_url(filed_after)
    fetched_at = _now_iso()
    pages = 0

    while url and pages < _MAX_PAGES:
        try:
            data = _get_json(url)
        except Exception as exc:  # noqa: BLE001 — record + stop politely
            stats["error"] = f"{type(exc).__name__}: {exc}"
            break

        pages += 1
        stats["requests"] += 1
        if stats.get("total_count") is None:
            stats["total_count"] = data.get("count")

        for result in (data.get("results") or []):
            stats["results_seen"] += 1
            if (result.get("court_id") or "") != COURT_CODE:
                continue
            chapter = str(result.get("chapter") or "").strip()
            if keep_chapters and chapter not in keep_chapters:
                stats["skipped_other_chapter"] += 1
                continue
            wrapped = _wrap(result, fetched_at)
            if wrapped is None:
                stats["skipped_no_docket"] += 1
                continue
            docket = wrapped["raw_payload"]["doc_number"]
            if docket not in by_docket:
                by_docket[docket] = wrapped
                stats["chapter_counts"][chapter] = (
                    stats["chapter_counts"].get(chapter, 0) + 1
                )

        url = data.get("next") or ""
        if url:
            time.sleep(_RATE_LIMIT_SECONDS)

    stats["pages"] = pages
    if pages >= _MAX_PAGES and url:
        stats["page_cap_hit"] = True
    return list(by_docket.values())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(
    days_back: int = 30,
    chapters: tuple[str, ...] = _DEFAULT_CHAPTERS,
    output_path: Path | None = None,
    filed_after: str | None = None,
) -> dict:
    """Pull Ch7/13 insb bankruptcy petitions filed in the last `days_back` days
    and write §4.32 wrapped raw records to data/raw/bankruptcy_filings.jsonl."""
    if output_path is None:
        output_path = REPO_ROOT / "data" / "raw" / f"{SOURCE_ID}.jsonl"
    if filed_after is None:
        filed_after = (date.today() - timedelta(days=days_back)).isoformat()

    stats: dict = {
        "source_id": SOURCE_ID,
        "court": COURT_CODE,
        "filed_after": filed_after,
        "chapters": list(chapters),
        "requests": 0,
        "pages": 0,
        "total_count": None,
        "results_seen": 0,
        "skipped_other_chapter": 0,
        "skipped_no_docket": 0,
        "chapter_counts": {},
        "records_written": 0,
        "error": None,
    }

    records = _fetch_all(filed_after, chapters, stats)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".jsonl.tmp")
    count = 0
    with open(tmp, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1
    tmp.replace(output_path)

    stats["records_written"] = count
    stats["output_path"] = str(output_path)
    return stats


def discover(days_back: int = 30) -> dict:
    """Discovery mode: one request, report the response shape (field names only,
    no party values) so the live API contract can be inspected."""
    filed_after = (date.today() - timedelta(days=days_back)).isoformat()
    out: dict = {
        "mode": "discover",
        "url": _build_url(filed_after),
        "status": "pending",
    }
    try:
        data = _get_json(_build_url(filed_after))
        results = data.get("results") or []
        out["status"] = "ok"
        out["top_level_keys"] = sorted(data.keys())
        out["count"] = data.get("count")
        out["results_in_page"] = len(results)
        out["has_next"] = bool(data.get("next"))
        if results:
            out["result_item_keys"] = sorted(results[0].keys())
            tally: dict = {}
            for r in results:
                ch = str(r.get("chapter") or "")
                tally[ch] = tally.get(ch, 0) + 1
            out["chapter_tally_in_page"] = tally
    except Exception as exc:  # noqa: BLE001
        out["status"] = f"error: {type(exc).__name__}: {exc}"
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Marion County bankruptcy-filings adapter — pulls Chapter 7/13 "
            "petitions from the U.S. Bankruptcy Court, Southern District of "
            "Indiana (insb) via the CourtListener v4 RECAP search API."
        )
    )
    parser.add_argument("--days-back", type=int, default=30,
                        help="Look back N days from today. Default 30.")
    parser.add_argument("--filed-after", default=None,
                        help="Explicit ISO date (YYYY-MM-DD); overrides --days-back.")
    parser.add_argument("--chapters", default="7,13",
                        help="Comma-separated chapters to keep. Default '7,13'.")
    parser.add_argument("--out", default=None,
                        help=f"Output JSONL path. Default: data/raw/{SOURCE_ID}.jsonl")
    parser.add_argument("--discover", action="store_true",
                        help="Discovery mode: one request, print response shape.")
    args = parser.parse_args()

    if args.discover:
        info = discover(days_back=args.days_back)
        print(json.dumps(info, indent=2))
        return 0 if info.get("status") == "ok" else 1

    chapters = tuple(c.strip() for c in args.chapters.split(",") if c.strip())
    out = Path(args.out) if args.out else None
    stats = run(
        days_back=args.days_back,
        chapters=chapters,
        output_path=out,
        filed_after=args.filed_after,
    )
    print(json.dumps(stats, indent=2))
    if stats.get("error"):
        print(f"\nERROR: {stats['error']}", file=sys.stderr)
        return 1
    print(f"\nPulled {stats['records_written']} records → {stats['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

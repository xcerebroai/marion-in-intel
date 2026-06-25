"""
Marion County Recorder adapter — Fidlar Breeze Angular SPA.

source_id: marion_recorder
output:    data/raw/recorder_recordings.jsonl

Architecture (confirmed via live bypass probe, 2026-06-25):
  - Angular SPA + Google reCAPTCHA v3 at:
      https://inmarion.fidlar.com/INMarion/DirectSearch/
  - Backing API (Breeze JS data layer):
      POST https://inmarion.fidlar.com/INMarion/
           Scrap.WebService.DirectSearch/breeze/Search
  - Auth: SPA auto-fetches /breeze/token on page load → stores JWT in
      localStorage.authorizationData.access_token
    Every search POST sends:
      Authorization: Bearer <JWT>
      FidlarCaptchaSolution: <reCAPTCHA-v3-token>
  - reCAPTCHA site key: 6LckDLwaAAAAAFdkFeW-dkX0IMirFhqiB_tXcRZE
  - Query strategy: date-range sweep only (StartDate / EndDate, ISO YYYY-MM-DD).
    NO wildcard / NO parcel search per site constraints and IC 36-1-8.5.
  - Response envelope: DocResults (list), TotalResults (int), ViewableResults (int),
    ResultAccessCode (str — used for subsequent-page requests).
  - ViewableResults caps at 200 per request. If TotalResults > 200 the adapter
    sends further requests with the same ResultAccessCode to page through.

Wrapped raw-record shape follows MASTER_PROMPT §4.32.
All real owner / party names stay in data/raw/ (gitignored).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SOURCE_ID = "marion_recorder"
_SPA_URL = "https://inmarion.fidlar.com/INMarion/DirectSearch/"
_BREEZE_URL = (
    "https://inmarion.fidlar.com/INMarion/"
    "Scrap.WebService.DirectSearch/breeze/Search"
)
_RECAPTCHA_SITE_KEY = "6LckDLwaAAAAAFdkFeW-dkX0IMirFhqiB_tXcRZE"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
_RATE_LIMIT_SECONDS = 2.0   # polite pause between paginated requests


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _normalize_date(raw: str) -> str:
    """Normalise recording_date to ISO YYYY-MM-DD.

    Breeze returns 'M/D/YYYY H:MM:SS AM/PM' (e.g. '6/16/2026 4:30:12 PM').
    """
    if not raw:
        return ""
    raw = raw.strip()
    # Already ISO with optional time component.
    if "T" in raw:
        return raw.split("T")[0]
    if len(raw) >= 10 and raw[4] == "-":
        return raw[:10]
    # M/D/YYYY HH:MM:SS AM/PM or M/D/YYYY
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw[:10] if len(raw) >= 10 else raw


# ---------------------------------------------------------------------------
# Record ID + normalization
# ---------------------------------------------------------------------------

def _record_id(doc_number: str, recording_date: str) -> str:
    """Deterministic raw_record_id from instrument number + date."""
    key = f"{SOURCE_ID}|{doc_number}|{recording_date}"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]
    return f"rr_{h}"


def _normalize_record(raw: dict) -> dict:
    """
    Map a single confirmed Fidlar Breeze DocResults object to framework-canonical
    field names. All output values are strings, numbers, or None.
    """
    doc_number      = (raw.get("DocumentName") or "").strip()
    recording_date  = _normalize_date(raw.get("RecordedDateTime") or "")
    tapestry        = (raw.get("TapestryLink") or "").strip()

    return {
        "doc_number":           doc_number,
        "doc_type_raw":         (raw.get("DocumentType") or "").strip(),
        "recording_date":       recording_date,
        "party1":               (raw.get("Party1") or "").strip(),
        "party2":               (raw.get("Party2") or "").strip(),
        "legal_desc":           (raw.get("LegalSummary") or "").strip(),
        "book":                 (raw.get("Book") or "").strip(),
        "page":                 (raw.get("Page") or "").strip(),
        "reference_number":     (raw.get("ReferenceNumber") or "").strip(),
        "consideration_amount": raw.get("ConsiderationAmount"),
        "doc_date":             (raw.get("DocumentDate") or "").strip(),
        "image_page_count":     raw.get("ImagePageCount"),
        "tapestry_link":        tapestry,
        "breeze_id":            raw.get("Id"),
    }


def _wrap(normalized: dict, fetched_at: str) -> dict:
    """Produce a §4.32 canonical wrapped raw record."""
    doc_number     = normalized.get("doc_number") or ""
    recording_date = normalized.get("recording_date") or ""
    tapestry       = normalized.get("tapestry_link") or ""
    return {
        "raw_record_id":     _record_id(doc_number, recording_date),
        "source_id":         SOURCE_ID,
        "source_url":        tapestry or _SPA_URL,
        "source_fetched_at": fetched_at,
        "parser_confidence": 90,
        "raw_payload":       normalized,
    }


# ---------------------------------------------------------------------------
# Request body builder
# ---------------------------------------------------------------------------

def _build_search_body(
    start_date: str,
    end_date: str,
    result_access_code: str = "",
) -> dict:
    """
    Build the Breeze POST body for a recording-date-range sweep.
    Dates must be ISO YYYY-MM-DD (confirmed from live Angular intercept).
    result_access_code is only sent for subsequent-page requests.
    """
    body: dict = {
        "FirstName": "",
        "LastBusinessName": "",
        "StartDate": start_date,
        "EndDate": end_date,
        "DocumentName": "",
        "DocumentType": "",
        "SubdivisionName": "",
        "SubdivisionLot": "",
        "SubdivisionBlock": "",
        "MunicipalityName": "",
        "TractSection": "",
        "TractTownship": "",
        "TractRange": "",
        "TractQuarter": "",
        "TractQuarterQuarter": "",
        "AddressHouseNo": "",
        "AddressStreet": "",
        "AddressCity": "",
        "AddressZip": "",
        "ParcelNumber": "",
        "Book": "",
        "Page": "",
        "ReferenceNumber": "",
    }
    if result_access_code:
        body["ResultAccessCode"] = result_access_code
    return body


# ---------------------------------------------------------------------------
# JS snippets — executed inside the Playwright browser context.
# Strings are templates; real values are injected as evaluate() arguments.
# ---------------------------------------------------------------------------

_JS_MINT_CAPTCHA = (
    "(siteKey) => new Promise((resolve, reject) => {"
    "  grecaptcha.ready(() => {"
    "    grecaptcha.execute(siteKey, {action: 'search'}).then(resolve).catch(reject);"
    "  });"
    "})"
)

_JS_POST_BREEZE = """
async (args) => {
    const { url, body, jwt, captcha } = args;
    const resp = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + jwt,
            'FidlarCaptchaSolution': captcha,
        },
        body: JSON.stringify(body),
    });
    const text = await resp.text();
    return { status: resp.status, text: text };
}
"""


# ---------------------------------------------------------------------------
# Playwright async core
# ---------------------------------------------------------------------------

async def _boot_spa(pw) -> tuple:
    """
    Launch headless browser, load Fidlar SPA, wait for Angular + JWT auto-login.
    The SPA automatically POSTs to /breeze/token on load and stores the JWT in
    localStorage.authorizationData.access_token.
    Returns (browser, page, jwt).
    """
    browser = await pw.chromium.launch(headless=True)
    ctx = await browser.new_context(
        user_agent=_USER_AGENT,
        locale="en-US",
        timezone_id="America/Indiana/Indianapolis",
    )
    page = await ctx.new_page()
    await page.goto(_SPA_URL, wait_until="networkidle", timeout=60_000)
    await page.wait_for_timeout(4_000)

    auth_raw = await page.evaluate("() => localStorage.getItem('authorizationData')")
    jwt = json.loads(auth_raw)["access_token"]
    return browser, page, jwt


async def _mint_captcha(page) -> str:
    return await page.evaluate(_JS_MINT_CAPTCHA, _RECAPTCHA_SITE_KEY)


async def _post_search(page, jwt: str, captcha: str, body: dict) -> dict:
    """POST to Breeze search endpoint; raise on non-200."""
    result = await page.evaluate(
        _JS_POST_BREEZE,
        {"url": _BREEZE_URL, "body": body, "jwt": jwt, "captcha": captcha},
    )
    if result["status"] != 200:
        snippet = result["text"][:400]
        raise RuntimeError(f"Breeze API HTTP {result['status']}: {snippet}")
    return json.loads(result["text"])


async def _search_date_range_async(start: date, end: date) -> tuple[list[dict], dict]:
    """
    Pull all recorder recordings for [start, end] (ISO YYYY-MM-DD).
    Pages through all results using ResultAccessCode.
    Returns (normalized_records, stats).
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError(
            "playwright not available in this Python. "
            "Run with: C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe"
        )

    start_str = start.isoformat()
    end_str   = end.isoformat()
    fetched_at = _now_iso()
    records: list[dict] = []
    stats: dict = {
        "source_id":        SOURCE_ID,
        "start_date":       start_str,
        "end_date":         end_str,
        "pages_fetched":    0,
        "total_results":    0,
        "viewable_results": 0,
        "records_returned": 0,
        "error":            None,
    }

    async with async_playwright() as pw:
        browser, page, jwt = await _boot_spa(pw)
        try:
            rac = ""           # ResultAccessCode — empty on first request
            seen_doc_ids: set[str] = set()   # detect pagination returning same records

            while True:
                captcha = await _mint_captcha(page)
                body = _build_search_body(start_str, end_str, rac)
                data = await _post_search(page, jwt, captcha, body)

                total    = data.get("TotalResults", 0)
                viewable = data.get("ViewableResults", 0)
                docs     = data.get("DocResults") or []
                new_rac  = data.get("ResultAccessCode") or ""

                if stats["pages_fetched"] == 0:
                    stats["total_results"]    = total
                    stats["viewable_results"] = viewable

                if not docs:
                    break

                # Count how many of this page are genuinely new.
                new_this_page = 0
                for doc in docs:
                    key = str(doc.get("DocumentName") or doc.get("Id") or "")
                    if key and key not in seen_doc_ids:
                        seen_doc_ids.add(key)
                        records.append(_normalize_record(doc))
                        new_this_page += 1

                stats["pages_fetched"] += 1

                # Breeze re-returns the same ViewableResults on subsequent RAC
                # requests when no additional records are available.
                if new_this_page == 0:
                    break
                if len(records) >= total:
                    break
                if not new_rac:
                    break

                rac = new_rac
                await asyncio.sleep(_RATE_LIMIT_SECONDS)

        except Exception as exc:
            stats["error"] = str(exc)
        finally:
            await browser.close()

    stats["records_returned"] = len(records)
    return records, stats


# ---------------------------------------------------------------------------
# Discovery mode
# ---------------------------------------------------------------------------

async def _discover_async(start: date, end: date, out_path: Path) -> dict:
    """Pull one request from Breeze and save the schema-only JSON to out_path."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError(
            "playwright not available. "
            "Run with: C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe"
        )

    stats: dict = {
        "mode": "discover",
        "start_date": str(start),
        "end_date": str(end),
        "status": "pending",
        "response_keys": [],
        "first_record_keys": [],
        "total_results": 0,
        "viewable_results": 0,
        "records_in_page": 0,
    }

    async with async_playwright() as pw:
        browser, page, jwt = await _boot_spa(pw)
        try:
            captcha = await _mint_captcha(page)
            body = _build_search_body(start.isoformat(), end.isoformat())
            data = await _post_search(page, jwt, captcha, body)

            docs = data.get("DocResults") or []
            stats["response_keys"]    = sorted(data.keys())
            stats["total_results"]    = data.get("TotalResults", 0)
            stats["viewable_results"] = data.get("ViewableResults", 0)
            stats["records_in_page"]  = len(docs)

            if docs:
                stats["first_record_keys"] = sorted(docs[0].keys())

            # Save schema-only (no DocResults PII) to committed recon file.
            meta = {k: v for k, v in data.items() if k != "DocResults"}
            meta["DocResults_count"]       = len(docs)
            meta["DocResults_sample_keys"] = list(docs[0].keys()) if docs else []
            meta["DocResults_sample_first"] = (
                {k: type(v).__name__ for k, v in docs[0].items()} if docs else {}
            )

            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            stats["status"]   = "ok"
            stats["saved_to"] = str(out_path)

        except Exception as exc:
            stats["status"] = f"error: {exc}"
        finally:
            await browser.close()

    return stats


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def discover(
    start: date | None = None,
    end: date | None = None,
    out_path: Path | None = None,
) -> dict:
    if start is None:
        start = date.today() - timedelta(days=9)
    if end is None:
        end = date.today() - timedelta(days=5)
    if out_path is None:
        out_path = (
            REPO_ROOT / "runs" / "marion_in" / "recon"
            / "breeze_response_sample.json"
        )
    return asyncio.run(_discover_async(start, end, out_path))


def run(
    start: date | None = None,
    end: date | None = None,
    output_path: Path | None = None,
    days_back: int = 1,
) -> dict:
    """
    Production mode: pull all recorder recordings for a date window and write
    to data/raw/marion_recorder.jsonl (gitignored — never committed).
    """
    if end is None:
        end = date.today() - timedelta(days=5)  # available 5 days after recording
    if start is None:
        start = end - timedelta(days=days_back - 1)
    if output_path is None:
        output_path = REPO_ROOT / "data" / "raw" / f"{SOURCE_ID}.jsonl"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fetched_at = _now_iso()

    records, stats = asyncio.run(_search_date_range_async(start, end))

    tmp = output_path.with_suffix(".jsonl.tmp")
    count = 0
    with open(tmp, "w", encoding="utf-8") as fh:
        for rec in records:
            wrapped = _wrap(rec, fetched_at)
            fh.write(json.dumps(wrapped, ensure_ascii=False) + "\n")
            count += 1
    tmp.replace(output_path)

    stats["output_path"]     = str(output_path)
    stats["records_written"] = count
    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Marion County Recorder adapter — pulls recorded instruments "
            "from Fidlar Breeze API by recording-date range."
        )
    )
    parser.add_argument(
        "--start-date", default=None,
        help="Recording start date YYYY-MM-DD.",
    )
    parser.add_argument(
        "--end-date", default=None,
        help="Recording end date YYYY-MM-DD.",
    )
    parser.add_argument(
        "--days-back", type=int, default=1,
        help="Days before today when end-date not supplied. Default 1.",
    )
    parser.add_argument(
        "--out", default=None,
        help=f"Output JSONL path. Default: data/raw/{SOURCE_ID}.jsonl",
    )
    parser.add_argument(
        "--discover", action="store_true",
        help=(
            "Discovery mode: pull one page and print response field names. "
            "Saves schema JSON to runs/marion_in/recon/breeze_response_sample.json."
        ),
    )
    args = parser.parse_args()

    start = date.fromisoformat(args.start_date) if args.start_date else None
    end   = date.fromisoformat(args.end_date)   if args.end_date   else None

    if args.discover:
        stats = discover(start=start, end=end)
        print(json.dumps(stats, indent=2))
        if stats.get("status") == "ok":
            print("\nTop-level response keys:", stats["response_keys"])
            print("First record field names:", stats["first_record_keys"])
            return 0
        print(f"\nDiscovery failed: {stats.get('status')}", file=sys.stderr)
        return 1

    out   = Path(args.out) if args.out else None
    stats = run(start=start, end=end, output_path=out, days_back=args.days_back)
    print(json.dumps(stats, indent=2))
    if stats.get("error"):
        print(f"\nERROR: {stats['error']}", file=sys.stderr)
        return 1
    print(f"\nPulled {stats['records_written']} records → {stats['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

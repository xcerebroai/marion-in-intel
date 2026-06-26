"""
Marion County court-filings adapter — Indiana MyCase (lis pendens / foreclosure).

source_id: court_filings
output:    data/raw/court_filings.jsonl
lead type: Lis Pendens  ·  regime: IN_judicial_foreclosure

Indiana is a judicial-foreclosure state: a mortgage foreclosure SUIT (case type
**MF — Mortgage Foreclosure**) is the court event that precedes — and triggers —
the recording of a lis pendens. Court filing date leads recording date, so MyCase
is the early LP signal and a backstop for the recorder free-tier 200-record cap.

Architecture (confirmed via live recon 2026-06-26 — see
runs/marion_in/recon/mycase_recon.md):
  - Portal is a custom Knockout.js MVVM SPA ("PublicAccessV3", Indiana JTAC) at
      https://public.courts.in.gov/mycase/   (NOT Tyler Odyssey, despite config).
  - Search API:  POST /mycase/Search/SearchCases  (JSON in, JSON out).
      Raw fetch is bounced to a portal redirect (anti-forgery token required), so
      the adapter calls the SPA's OWN service layer from inside the page:
          od.services.Search.SearchCases(body).success(...).failure(...)
      which reuses the app's $http (token + headers + cookies). Same doctrine as
      the Phase 2 recorder adapter (Playwright runs the page's own JS).
  - No keyless/date-only search exists: ByParty requires a name. Filing date,
      court and category are FILTERS, not query keys. Access path = wildcard
      surname sweep A*..Z* with CourtItemID=146 (Marion, all divisions),
      Categories=["CV"] (Civil), the target FileStart/FileEnd window; paginate
      each prefix (Skip/Take, hard cap 1000 ⇒ subdivide), filter client-side to
      CaseType MF, dedup by CaseNumber.
  - Conditional image CAPTCHA: a response with CaptchaKey means the portal wants
      a CAPTCHA. We do NOT solve it — we stop politely and record it in stats.

Wrapped raw-record shape follows MASTER_PROMPT §4.32.
All party names / captions stay in data/raw/ (gitignored); only case numbers,
types and counts ever reach stdout.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import string
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SOURCE_ID = "court_filings"
_SPA_URL = "https://public.courts.in.gov/mycase/"
_CASE_SUMMARY_BASE = "https://public.courts.in.gov/mycase/#/vw/CaseSummary/"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

# Live-confirmed query constants (recon 2026-06-26).
_MARION_COURT_ITEM_ID = 146        # "Marion County" — all Marion divisions
_CIVIL_CATEGORY = ["CV"]           # Mortgage Foreclosure lives under Civil
_DEFAULT_CASE_TYPE_PREFIXES = ("MF",)   # MF — Mortgage Foreclosure (LP signal)

_RESULT_CAP = 1000                 # server caps any single query at 1000 results
_PAGE_TAKE = 100                   # rows per page (honored by server)
_MAX_PREFIX_LEN = 2                # subdivide a maxxed prefix down to 2 chars
_RATE_LIMIT_SECONDS = 1.5          # polite pause between requests (public courts)
_SWEEP_PREFIXES = tuple(string.ascii_uppercase)   # A..Z surname sweep


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _to_mdY(d: date) -> str:
    """MyCase FileStart/FileEnd format: MM/DD/YYYY."""
    return d.strftime("%m/%d/%Y")


def _normalize_date(raw: str) -> str:
    """Normalise a MyCase date (M/D/YYYY) to ISO YYYY-MM-DD."""
    if not raw:
        return ""
    raw = raw.strip()
    if "T" in raw:
        return raw.split("T")[0]
    if len(raw) >= 10 and raw[4] == "-":
        return raw[:10]
    for fmt in ("%m/%d/%Y", "%m/%d/%Y %I:%M:%S %p"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


# ---------------------------------------------------------------------------
# Record ID + normalization
# ---------------------------------------------------------------------------

def _record_id(case_number: str) -> str:
    """Deterministic raw_record_id from the case number (globally unique)."""
    key = f"{SOURCE_ID}|{case_number}"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:20]
    return f"cf_{h}"


def _case_type_code(case_type_raw: str) -> str:
    """'MF - Mortgage Foreclosure' -> 'MF'. Also handles a bare 'MF'."""
    if not case_type_raw:
        return ""
    head = case_type_raw.split("-", 1)[0].strip()
    return head.upper()


def _split_caption(style: str) -> tuple[str, str]:
    """
    Split a case caption ('Plaintiff v. Defendant') into (plaintiff, defendant).
    Handles ' v. ', ' vs. ', ' vs ' separators (case-insensitive). If no
    separator is found, the whole caption is treated as the plaintiff side.
    """
    if not style:
        return "", ""
    s = style.strip()
    low = s.lower()
    for sep in (" v. ", " vs. ", " vs ", " v ", " -vs- "):
        idx = low.find(sep)
        if idx != -1:
            return s[:idx].strip(), s[idx + len(sep):].strip()
    return s, ""


def _case_detail_url(case_token: str) -> str:
    """
    Reconstruct the public case deep link the SPA builds:
      #/vw/CaseSummary/<b64( JSON.stringify({"v":{"CaseToken": token}}) )>
    """
    if not case_token:
        return _SPA_URL
    payload = json.dumps({"v": {"CaseToken": case_token}}, separators=(",", ":"))
    b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    return _CASE_SUMMARY_BASE + b64


def _normalize_record(raw: dict) -> dict:
    """
    Map one MyCase SearchCases result object to framework-canonical fields.
    All output values are strings, numbers, bools or None.
    """
    case_number   = (raw.get("CaseNumber") or "").strip()
    case_type_raw = (raw.get("CaseType") or "").strip()
    style         = (raw.get("Style") or "").strip()
    case_token    = (raw.get("CaseToken") or "").strip()
    plaintiff, defendant = _split_caption(style)

    return {
        "case_number":      case_number,
        "case_type_raw":    case_type_raw,
        "case_type_code":   _case_type_code(case_type_raw),
        "case_subtype":     (raw.get("CaseSubType") or "").strip(),
        "filing_date":      _normalize_date(raw.get("FileDate") or ""),
        "case_status":      (raw.get("CaseStatus") or "").strip(),
        "case_status_date": _normalize_date(raw.get("CaseStatusDate") or ""),
        "court":            (raw.get("Court") or "").strip(),
        "court_code":       (raw.get("CourtCode") or "").strip(),
        "county_code":      (raw.get("CountyCode") or "").strip(),
        "plaintiff":        plaintiff,
        "defendant":        defendant,
        "caption":          style,
        "parties_raw":      (raw.get("Parties") or "").strip(),
        "attorneys_raw":    (raw.get("Attorneys") or "").strip(),
        "case_token":       case_token,
        "case_id":          raw.get("CaseID"),
        "is_active":        raw.get("IsActive"),
        "is_public":        raw.get("IsPublic"),
        "case_detail_url":  _case_detail_url(case_token),
    }


def _wrap(normalized: dict, fetched_at: str) -> dict:
    """Produce a §4.32 canonical wrapped raw record."""
    case_number = normalized.get("case_number") or ""
    detail_url  = normalized.get("case_detail_url") or _SPA_URL
    return {
        "raw_record_id":     _record_id(case_number),
        "source_id":         SOURCE_ID,
        "source_url":        detail_url,
        "source_fetched_at": fetched_at,
        "parser_confidence": 90,
        "raw_payload":       normalized,
    }


# ---------------------------------------------------------------------------
# Request body builder
# ---------------------------------------------------------------------------

def _build_search_body(
    last_wildcard: str,
    start_str: str,
    end_str: str,
    active_flag: str = "All",
    skip: int = 0,
    take: int = _PAGE_TAKE,
) -> dict:
    """
    Build the /Search/SearchCases POST body for a wildcard surname sweep,
    filtered to Marion (146) + Civil + a filing-date window. Confirmed schema
    from a live Knockout-form intercept.
    """
    return {
        "Mode":         "ByParty",
        "CaseNum":      None,
        "CiteNum":      None,
        "CrossRefNum":  None,
        "First":        None,
        "Middle":       None,
        "Last":         last_wildcard,
        "Business":     None,
        "DoBStart":     None,
        "DoBEnd":       None,
        "OANum":        None,
        "BarNum":       None,
        "SoundEx":      False,
        "CourtItemID":  _MARION_COURT_ITEM_ID,
        "Categories":   list(_CIVIL_CATEGORY),
        "Limits":       None,
        "Advanced":     True,
        "ActiveFlag":   active_flag,
        "FileStart":    start_str,
        "FileEnd":      end_str,
        "CountyCode":   None,
        "NewSearch":    True,
        "CaptchaAnswer": None,
        "Skip":         skip,
        "Take":         take,
        "Sort":         "FileDate DESC",
    }


# ---------------------------------------------------------------------------
# JS snippet — runs inside the Playwright page, using the SPA's own service.
# ---------------------------------------------------------------------------

_JS_SEARCH = """
async (body) => await new Promise((resolve) => {
    try {
        if (!(window.od && od.services && od.services.Search)) {
            resolve({ ok: false, err: 'od.services.Search unavailable' });
            return;
        }
        od.services.Search.SearchCases(body)
            .success(r => resolve({ ok: true, r: r }))
            .failure(e => resolve({
                ok: false,
                err: (e && e.ErrorThrown) ? String(e.ErrorThrown) : 'search failure',
                raw: JSON.stringify(e || {}).slice(0, 300)
            }));
    } catch (ex) { resolve({ ok: false, err: String(ex) }); }
})
"""


class _CaptchaRequired(RuntimeError):
    """Raised when MyCase returns a CaptchaKey (we do not solve CAPTCHAs)."""


# ---------------------------------------------------------------------------
# Playwright async core
# ---------------------------------------------------------------------------

async def _boot_spa(pw):
    """Launch headless Chromium, load MyCase, wait for the Knockout app + od.services."""
    browser = await pw.chromium.launch(headless=True)
    ctx = await browser.new_context(
        user_agent=_USER_AGENT,
        locale="en-US",
        timezone_id="America/Indiana/Indianapolis",
    )
    page = await ctx.new_page()
    await page.goto(_SPA_URL, wait_until="networkidle", timeout=60_000)
    # Wait for the app service layer to be ready.
    try:
        await page.wait_for_function(
            "() => !!(window.od && od.services && od.services.Search)",
            timeout=30_000,
        )
    except Exception:
        await page.wait_for_timeout(4_000)
    return browser, page


async def _post_search(page, body: dict) -> dict:
    """Call the SPA service; return the unwrapped Result dict. Raises on error/captcha."""
    out = await page.evaluate(_JS_SEARCH, body)
    if not out.get("ok"):
        raise RuntimeError(f"SearchCases failed: {out.get('err')} {out.get('raw', '')}")
    payload = out["r"]
    result = payload.get("Result", payload) if isinstance(payload, dict) else {}
    if result.get("CaptchaKey"):
        raise _CaptchaRequired("MyCase returned a CaptchaKey — search paused.")
    return result


async def _sweep_prefix(
    page,
    prefix: str,
    start_str: str,
    end_str: str,
    active_flag: str,
    type_prefixes: tuple[str, ...],
    by_case: dict,
    stats: dict,
) -> None:
    """
    Pull every page for one surname prefix (e.g. 'A' -> 'A*'), keeping records
    whose CaseType matches `type_prefixes`. If a prefix exceeds the 1000 cap,
    subdivide it (append A..Z) down to _MAX_PREFIX_LEN rather than truncate.
    """
    wildcard = f"{prefix}*"
    skip = 0
    first = True
    while True:
        body = _build_search_body(wildcard, start_str, end_str, active_flag, skip, _PAGE_TAKE)
        result = await _post_search(page, body)
        stats["requests"] += 1
        total = max(int(result.get("TotalResults") or 0), 0)
        rows = result.get("Results") or []

        if first:
            first = False
            if total >= _RESULT_CAP and len(prefix) < _MAX_PREFIX_LEN:
                stats["subdivided_prefixes"].append(wildcard)
                for c in _SWEEP_PREFIXES:
                    await _sweep_prefix(page, prefix + c, start_str, end_str,
                                        active_flag, type_prefixes, by_case, stats)
                    await asyncio.sleep(_RATE_LIMIT_SECONDS)
                return
            if total >= _RESULT_CAP:
                # Cannot subdivide further — record that this slice is maxxed.
                stats["maxxed_prefixes"].append(wildcard)

        for raw in rows:
            ctype = _case_type_code(raw.get("CaseType") or "")
            if type_prefixes and not any(ctype.startswith(tp) for tp in type_prefixes):
                continue
            norm = _normalize_record(raw)
            cn = norm["case_number"]
            if cn and cn not in by_case:
                by_case[cn] = norm

        if not rows or skip + _PAGE_TAKE >= total:
            break
        skip += _PAGE_TAKE
        await asyncio.sleep(_RATE_LIMIT_SECONDS)


async def _search_window_async(
    start: date,
    end: date,
    active_flag: str = "All",
    type_prefixes: tuple[str, ...] = _DEFAULT_CASE_TYPE_PREFIXES,
    prefixes: tuple[str, ...] = _SWEEP_PREFIXES,
) -> tuple[list[dict], dict]:
    """
    Sweep surname prefixes over [start, end] and return (normalized MF records,
    stats). Records are deduped by case number across prefixes.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError(
            "playwright not available in this Python. Run with: "
            "C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe"
        )

    start_str, end_str = _to_mdY(start), _to_mdY(end)
    by_case: dict[str, dict] = {}
    stats: dict = {
        "source_id":            SOURCE_ID,
        "start_date":           start.isoformat(),
        "end_date":             end.isoformat(),
        "active_flag":          active_flag,
        "case_type_prefixes":   list(type_prefixes),
        "prefixes_swept":       0,
        "requests":             0,
        "subdivided_prefixes":  [],
        "maxxed_prefixes":      [],
        "records_returned":     0,
        "error":                None,
    }

    async with async_playwright() as pw:
        browser, page = await _boot_spa(pw)
        try:
            for prefix in prefixes:
                await _sweep_prefix(page, prefix, start_str, end_str, active_flag,
                                    type_prefixes, by_case, stats)
                stats["prefixes_swept"] += 1
                await asyncio.sleep(_RATE_LIMIT_SECONDS)
        except _CaptchaRequired as exc:
            stats["error"] = str(exc)
            stats["captcha_required"] = True
        except Exception as exc:
            stats["error"] = str(exc)
        finally:
            await browser.close()

    records = list(by_case.values())
    stats["records_returned"] = len(records)
    return records, stats


# ---------------------------------------------------------------------------
# Discovery mode
# ---------------------------------------------------------------------------

async def _discover_async(start: date, end: date, out_path: Path) -> dict:
    """Run ONE surname-prefix search and save the schema-only JSON (no PII)."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise ImportError(
            "playwright not available. Run with: "
            "C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe"
        )

    stats: dict = {
        "mode": "discover",
        "start_date": str(start),
        "end_date": str(end),
        "status": "pending",
        "response_keys": [],
        "result_item_keys": [],
        "total_results": 0,
        "records_in_page": 0,
    }

    async with async_playwright() as pw:
        browser, page = await _boot_spa(pw)
        try:
            body = _build_search_body("A*", _to_mdY(start), _to_mdY(end))
            result = await _post_search(page, body)
            rows = result.get("Results") or []
            stats["response_keys"]  = sorted(result.keys())
            stats["total_results"]  = result.get("TotalResults", 0)
            stats["records_in_page"] = len(rows)
            if rows:
                stats["result_item_keys"] = sorted(rows[0].keys())

            # Schema-only artifact: field-name -> type, plus type tally. No values.
            meta = {k: v for k, v in result.items() if k != "Results"}
            meta["Results_count"] = len(rows)
            meta["Results_item_types"] = (
                {k: type(v).__name__ for k, v in rows[0].items()} if rows else {}
            )
            type_tally: dict = {}
            for r in rows:
                ct = _case_type_code(r.get("CaseType") or "")
                type_tally[ct] = type_tally.get(ct, 0) + 1
            meta["CaseType_tally"] = type_tally

            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            stats["status"] = "ok"
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
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=13)
    if out_path is None:
        out_path = (
            REPO_ROOT / "runs" / "marion_in" / "recon"
            / "mycase_response_sample.json"
        )
    return asyncio.run(_discover_async(start, end, out_path))


def run(
    start: date | None = None,
    end: date | None = None,
    output_path: Path | None = None,
    days_back: int = 14,
    active_flag: str = "All",
    case_type_prefixes: tuple[str, ...] = _DEFAULT_CASE_TYPE_PREFIXES,
) -> dict:
    """
    Production mode: sweep MyCase for foreclosure (MF) filings over a date window
    and write §4.32 wrapped raw records to data/raw/court_filings.jsonl
    (gitignored — never committed).
    """
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=days_back - 1)
    if output_path is None:
        output_path = REPO_ROOT / "data" / "raw" / f"{SOURCE_ID}.jsonl"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fetched_at = _now_iso()

    records, stats = asyncio.run(
        _search_window_async(start, end, active_flag, case_type_prefixes)
    )

    tmp = output_path.with_suffix(".jsonl.tmp")
    count = 0
    with open(tmp, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(_wrap(rec, fetched_at), ensure_ascii=False) + "\n")
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
            "Marion County court-filings adapter — pulls MF (mortgage "
            "foreclosure / lis pendens) cases from Indiana MyCase by filing-date "
            "range via a wildcard surname sweep."
        )
    )
    parser.add_argument("--start-date", default=None, help="Filing start date YYYY-MM-DD.")
    parser.add_argument("--end-date", default=None, help="Filing end date YYYY-MM-DD.")
    parser.add_argument("--days-back", type=int, default=14,
                        help="Window length when start-date not supplied. Default 14.")
    parser.add_argument("--active-flag", default="All", choices=["All", "Open", "Closed"],
                        help="Case status filter. Default All.")
    parser.add_argument("--case-types", default="MF",
                        help="Comma-separated case-type code prefixes to keep. Default MF.")
    parser.add_argument("--out", default=None,
                        help=f"Output JSONL path. Default: data/raw/{SOURCE_ID}.jsonl")
    parser.add_argument("--discover", action="store_true",
                        help=("Discovery mode: one search; print response field names + "
                              "case-type tally. Saves schema JSON to "
                              "runs/marion_in/recon/mycase_response_sample.json."))
    args = parser.parse_args()

    start = date.fromisoformat(args.start_date) if args.start_date else None
    end   = date.fromisoformat(args.end_date)   if args.end_date   else None

    if args.discover:
        stats = discover(start=start, end=end)
        print(json.dumps(stats, indent=2))
        if stats.get("status") == "ok":
            print("\nTop-level response keys:", stats["response_keys"])
            print("Result item field names:", stats["result_item_keys"])
            return 0
        print(f"\nDiscovery failed: {stats.get('status')}", file=sys.stderr)
        return 1

    type_prefixes = tuple(
        t.strip().upper() for t in args.case_types.split(",") if t.strip()
    )
    out = Path(args.out) if args.out else None
    stats = run(start=start, end=end, output_path=out, days_back=args.days_back,
                active_flag=args.active_flag, case_type_prefixes=type_prefixes)
    print(json.dumps(stats, indent=2))
    if stats.get("error"):
        print(f"\nERROR: {stats['error']}", file=sys.stderr)
        return 1
    print(f"\nPulled {stats['records_written']} records → {stats['output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

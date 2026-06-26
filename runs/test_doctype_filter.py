"""
Probe: does the Fidlar Breeze API honour DocumentType as a server-side filter?

Self-contained — replicates the Playwright boot/captcha/POST pattern from
scrapers/recorder_recordings.py (_boot_spa, _mint_captcha, _JS_POST_BREEZE,
_JS_MINT_CAPTCHA) without importing or modifying that module.

Fires exactly two Breeze search requests over the SAME single-day window
(2026-06-16 → 2026-06-16):
  1. DocumentType = 'LIS PENDENS'  (exact raw doc type confirmed in Phase 2)
  2. DocumentType = ''             (baseline — no type filter)

Then prints a verdict:
  FILTER_WORKS   — LIS PENDENS count < baseline count AND every returned
                   DocResults record has DocumentType == 'LIS PENDENS'
  FILTER_IGNORED — the two TotalResults counts are identical
  PARTIAL        — anything else (fewer results but mixed types, or zero rows, etc.)

Run with the Python that has Playwright installed:
  C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe \
      runs/test_doctype_filter.py

Prints stats only (doc_type_raw, doc_number, party1) — no full PII to stdout.
"""

from __future__ import annotations

import asyncio
import json
import sys

# ---------------------------------------------------------------------------
# Constants — mirrored from scrapers/recorder_recordings.py
# ---------------------------------------------------------------------------

_PY312 = "C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe"

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

_TEST_DATE = "2026-06-16"          # single-day window, start == end
_LIS_PENDENS = "LIS PENDENS"        # exact raw doc type confirmed in Phase 2

# ---------------------------------------------------------------------------
# JS snippets — identical to recorder_recordings.py
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
# Request body builder — same shape as the scraper, but DocumentType is a param
# ---------------------------------------------------------------------------

def _build_search_body(start_date: str, end_date: str, document_type: str = "") -> dict:
    """Breeze POST body for a recording-date-range sweep with optional DocumentType."""
    return {
        "FirstName": "",
        "LastBusinessName": "",
        "StartDate": start_date,
        "EndDate": end_date,
        "DocumentName": "",
        "DocumentType": document_type,
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


# ---------------------------------------------------------------------------
# Playwright core — mirrors _boot_spa / _mint_captcha / _post_search
# ---------------------------------------------------------------------------

async def _boot_spa(pw) -> tuple:
    """Launch headless browser, load Fidlar SPA, return (browser, page, jwt)."""
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


# ---------------------------------------------------------------------------
# One search → compact stats (no full PII)
# ---------------------------------------------------------------------------

def _summarize(label: str, data: dict) -> dict:
    docs = data.get("DocResults") or []
    summary = {
        "label":            label,
        "total_results":    data.get("TotalResults", 0),
        "viewable_results": data.get("ViewableResults", 0),
        "doc_results_len":  len(docs),
        "first_three": [
            {
                "doc_type_raw": (d.get("DocumentType") or "").strip(),
                "doc_number":   (d.get("DocumentName") or "").strip(),
                "party1":       (d.get("Party1") or "").strip(),
            }
            for d in docs[:3]
        ],
        "doc_types_seen": sorted(
            {(d.get("DocumentType") or "").strip() for d in docs}
        ),
    }
    return summary


def _print_summary(s: dict) -> None:
    print(f"\n=== {s['label']} ===")
    print(f"  TotalResults    : {s['total_results']}")
    print(f"  ViewableResults : {s['viewable_results']}")
    print(f"  len(DocResults) : {s['doc_results_len']}")
    print("  First 3 records (doc_type_raw | doc_number | party1):")
    if not s["first_three"]:
        print("    (none)")
    for r in s["first_three"]:
        print(f"    - {r['doc_type_raw']!r} | {r['doc_number']!r} | {r['party1']!r}")


# ---------------------------------------------------------------------------
# Main async flow — two requests, one boot
# ---------------------------------------------------------------------------

async def _run_async() -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print(
            "playwright not available in this Python.\n"
            f"Run with: {_PY312} runs/test_doctype_filter.py",
            file=sys.stderr,
        )
        return 2

    async with async_playwright() as pw:
        browser, page, jwt = await _boot_spa(pw)
        try:
            # 1. Baseline query — DocumentType = ''
            captcha = await _mint_captcha(page)
            base_body = _build_search_body(_TEST_DATE, _TEST_DATE, "")
            base_data = await _post_search(page, jwt, captcha, base_body)
            base = _summarize(f"BASELINE  DocumentType=''  {_TEST_DATE}", base_data)

            # 2. Known doc type — MORTGAGE (confirmed from Phase 2 pull)
            captcha = await _mint_captcha(page)
            mtg_body = _build_search_body(_TEST_DATE, _TEST_DATE, "MORTGAGE")
            mtg_data = await _post_search(page, jwt, captcha, mtg_body)
            mtg = _summarize("FILTERED  DocumentType='MORTGAGE'", mtg_data)

            # 3. Filtered query — DocumentType = 'LIS PENDENS'
            captcha = await _mint_captcha(page)
            lp_body = _build_search_body(_TEST_DATE, _TEST_DATE, _LIS_PENDENS)
            lp_data = await _post_search(page, jwt, captcha, lp_body)
            lp = _summarize(f"FILTERED  DocumentType={_LIS_PENDENS!r}  {_TEST_DATE}", lp_data)
        finally:
            await browser.close()

    _print_summary(base)
    _print_summary(mtg)
    _print_summary(lp)

    # -------------------------------------------------------------------
    # Verdict
    # -------------------------------------------------------------------
    lp_total   = lp["total_results"]
    base_total = base["total_results"]
    lp_types   = lp["doc_types_seen"]            # distinct types in filtered DocResults
    all_lis    = bool(lp_types) and lp_types == [_LIS_PENDENS]

    if lp_total == base_total:
        verdict = "FILTER_IGNORED"
        reason = (
            f"identical TotalResults ({lp_total} == {base_total}); "
            "DocumentType appears to have no server-side effect"
        )
    elif lp_total < base_total and all_lis:
        verdict = "FILTER_WORKS"
        reason = (
            f"filtered TotalResults {lp_total} < baseline {base_total} AND "
            f"every returned record is {_LIS_PENDENS!r}"
        )
    else:
        verdict = "PARTIAL"
        reason = (
            f"filtered TotalResults {lp_total} vs baseline {base_total}; "
            f"doc types in filtered DocResults = {lp_types or '[]'}"
        )

    print("\n" + "=" * 60)
    print(f"VERDICT: {verdict}")
    print(f"  reason: {reason}")
    print("=" * 60)
    return 0


def main() -> int:
    return asyncio.run(_run_async())


if __name__ == "__main__":
    raise SystemExit(main())

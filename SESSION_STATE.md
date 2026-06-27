# Marion County IN — Session State (2026-06-26)

## Repo
`C:/Users/Owner/projects/marion-in-intel`
GitHub: `https://github.com/xcerebroai/marion-in-intel`
Dashboard: `https://xcerebroai.github.io/marion-in-intel/dashboard/`

---

## What Was Built This Session

### Pipeline changes
- Scoring system removed entirely (`score.py` deleted, `scoring_seam.py` gutted)
- `scaffold/pipeline/lead_registry.py` added — tracks `is_new` / `first_seen_date` across runs
- `scaffold/pipeline/run_pipeline_staged.py` — added `owner_type`, `mailing_address`, `mailing_city`, `mailing_state`, `mailing_zip`, `property_class`, `year_built` to dashboard projection
- `scaffold/pipeline/dashboard.py` — removed `score_tier_distribution`, added `new_lead_count`

### New scrapers added
- `scrapers/bankruptcy_filings.py` — CourtListener RECAP, Indiana Southern District, Ch7/Ch13, 429 backoff wired
- `scrapers/tax_delinquency.py` — indy.gov GraphCMS API → PDF parse via pdfplumber, 766 records
- `scrapers/code_enforcement.py` — OpenIndy ArcGIS DCE endpoint (stale mirror, last updated Feb 2024 — scraper works, data is stale)
- `scrapers/probate_estates.py` — ArcGIS owner name sweep for ESTATE OF / EST OF patterns with LLC/INC false-positive filter
- `scrapers/county_lead_translators.py` — custom translator for code enforcement + probate

### Dashboard rebuilt
- Full dark-theme card UI matching El Paso County dashboard style
- Files: `dashboard/index.html`, `dashboard/styles.css`, `dashboard/dashboard.js`
- Old `dashboard/dashboard.css` deleted, replaced by `styles.css`

### Lead counts
- Started: 143 leads
- After bankruptcy: 501
- After all sources: ~1,508 leads
- Patterns: foreclosure 402, tax 766, estate 155, transfer 137, lien 1

---

## ACTIVE BUG — Tax leads have no address or owner on dashboard

### Root cause (traced and confirmed)
`csv_static_list` translator emits the owner as `taxpayer` field in the signal, but the `_NAME_TYPE_FROM_FIELD` dict in `build_leads.py` maps `taxpayer → TP`. The §17 debtor engine receives the TP party but `TAX_FORECLOSURE_NOTICE` rule still returns `owner_not_on_document`.

### What was tried
1. Added `situs_address`, `situs_city`, `owner_name` to parcel output in `csv_static_list.py` ✓
2. Added `grantor`/`taxpayer`/`address` to signal output in `csv_static_list.py` ✓
3. Cleared `.pyc` cache ✓
4. Confirmed `_NAME_TYPE_FROM_FIELD` has `"taxpayer": "TP"` in `build_leads.py` ✓

### Still failing
The debtor engine returns `review_reason: "owner_not_on_document"` even with TP party present.

### Next debug step
Check `scaffold/pipeline/debtor_party_engine.py` — specifically the `tax_foreclosure_notice` rule. It may require a `TP` party from `document_body` not just from the parties list, OR the `UNIVERSAL_DEBTOR_PARTY_RULES` for `tax_foreclosure_notice` may use `document-body` resolution path which requires the party to come from a specific source.

Run this to diagnose:
```python
import sys, json
sys.path.insert(0, '.')
from scaffold.pipeline.debtor_party_engine import resolve_debtor_party, UNIVERSAL_DEBTOR_PARTY_RULES

# Check what rule applies to tax_foreclosure_notice
rule = UNIVERSAL_DEBTOR_PARTY_RULES.get('tax_foreclosure_notice')
print('rule:', rule)

# Then test resolution with a real TP party
raw_event = {
    'canonical_doc_type': 'tax_foreclosure_notice',
    'parties': [{'name': 'VGM CAPITAL HOLDINGS LLC', 'name_type': 'TP', 'raw_role': 'taxpayer'}],
    'property_refs': {'parcel_id': 'MARIN-TX-TEST', 'situs_address': '2615 WHITE AV'},
    'document_body_text': None,
}
drr = resolve_debtor_party(raw_event)
print('owner_name:', drr.get('owner_name'))
print('review_reason:', drr.get('review_reason'))
print('debtor_resolution_status:', drr.get('debtor_resolution_status'))
```

### Likely fix
If `tax_foreclosure_notice` uses `document-body` resolution path, the workaround is to write the owner name into `document_body_text` on the raw event, OR patch the debtor engine rule for `tax_foreclosure_notice` to accept TP from the parties list directly (same as how `court_filings` was fixed for DF).

---

## ACTIVE BUG — "New Today" always shows 0

### Root cause
`data/seen_leads.json` was seeded with all leads on first run, so every subsequent run shows 0 new.

### Fix attempt
Cleared `seen_leads.json` to `{}` during this session. On next pipeline run all 1,508 leads will stamp as new (expected). After that, only genuinely new leads will show the NEW pill.

### How it works going forward
Daily GitHub Actions cron runs pipeline → `lead_registry.stamp_leads()` compares against `data/seen_leads.json` → new lead_ids get `is_new: True` → cron commits `data/seen_leads.json` back to repo. The registry persists between runs because it's now tracked in git (removed from `.gitignore`).

---

## Current git state
Last commit: `a5f9629` — dashboard rebuild
Dirty files (uncommitted): `scaffold/pipeline/translators/csv_static_list.py` (translator fix in progress)

---

## Gate status
`C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe scaffold/tests/run_all.py` — **PASS (28/28)**

---

## Config: active sources in `config/counties/marion_in.json`
- `marion_recorder` — Fidlar Breeze, 200 rec/day cap
- `court_filings` — MyCase LP/MF, 44 records/run
- `parcel_master` — ArcGIS assessor enrichment join
- `bankruptcy_filings` — CourtListener RECAP (Ch7/Ch13)
- `tax_delinquency` — PDF via GraphCMS API (annual batch, 766 records)
- `code_enforcement` — OpenIndy ArcGIS DCE (stale, last updated Feb 2024)
- `probate_estates` — ArcGIS owner name sweep

---

## Daily cron
`.github/workflows/daily_refresh.yml` — runs 07:00 UTC daily
Steps: recorder → court filings → parcel enrichment → tax delinquency (with pdfplumber) → pipeline → commit dashboard.json + seen_leads.json + push

---

## Next tasks (in priority order)
1. **Fix tax lead address/owner** — debug `tax_foreclosure_notice` debtor engine rule (see above)
2. **Probate leads** — verify estate leads on dashboard have real owner names (same translator fix may be needed)
3. **Code enforcement** — source mirror is stale; build scraper against `permitsandcases.indy.gov` for real-time violations
4. **Sheriff sales** — indy.gov pages 500 error; check `sri-taxsale.com` or MyCase scheduling orders
5. **Tapestry** — client needs to create account at `tapestry.fidlar.com` to lift Fidlar 200-record cap
6. **Sync changes to framework master** — `xcerebroai/xcerebro-county-intel` needs these pipeline fixes

---

## Environment
- Python 3.12: `C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe`
- All `claude -p` build calls use `--model claude-opus-4-8`
- Hermes agent stays on `claude-sonnet-4-6`
- Billing: Claude Max ($200/mo) at claude.ai

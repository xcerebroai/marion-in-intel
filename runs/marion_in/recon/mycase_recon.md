# MyCase Court-Filings Recon — Marion County, IN (Phase 3)

**Lead type:** Lis Pendens / Foreclosure · **Regime:** `IN_judicial_foreclosure`
**Source:** Indiana MyCase — https://public.courts.in.gov/mycase/
**Recon performed:** 2026-06-26 (live browser probe, headless Chromium / Playwright)
**Adapter built:** `scrapers/court_filings.py` → `data/raw/court_filings.jsonl`

This document records what the **real** MyCase interface is, established by live
inspection before any adapter code was written (recon-before-code hard rule).

---

## 0. Headline finding — portal is NOT Tyler Odyssey

`config/counties/marion_in.json` (read-only for this phase) fingerprints
`court_filings` as **Tyler Odyssey Public Access (React SPA)** with module
`scrapers.tyler_odyssey_mycase` / translator `tyler_odyssey_court`. **Live recon
contradicts this.** The actual portal is a custom **Knockout.js MVVM** single-page
app — the **"PublicAccessV3"** framework served from the Indiana JTAC CDN
(`foundations.jtac.in.gov/CDN/PublicAccessV3/v3_5_2/...`), built by the Indiana
Office of Judicial Administration / JTAC. There is no React, no Angular.

- `window.angular` → false, `[ng-version]` → none, React root → none.
- Scripts: `libs.min.js`, `framework.min.js` (JTAC CDN) + `Scripts/All`,
  `ODScripts/All` (app bundles). MVVM view templates fetched as
  `MVVM/ViewModels/Search/Search.tmpl.html` etc.

**Config impact (NOT changed this phase):** the `scraper_module`,
`translator`, `portal_family: "Tyler"`, and `portal_version` fields in the config
are inaccurate. The built adapter is `scrapers.court_filings`. Flag for an
operator config-sync follow-up; out of scope here (config is read-only).

---

## 1. Search interface

Default route `#/vw/Search`. Three search **modes** (tabs):

| Tab        | Mode key  | Primary key required (see §4) |
|------------|-----------|-------------------------------|
| Case       | `ByCase`  | Case **or** Citation **or** Cross-Ref number (exactly one) |
| Name       | `ByParty` | Last / First / Middle / Business / DoB (Last is the anchor) |
| Attorney   | `ByAtty`  | Attorney name or bar number |

Shared **filters** (apply across modes, revealed by "Advanced Search Options"):

- **Court** dropdown — `CourtItemID`. **`146` = "Marion County"** (all Marion
  divisions; confirmed from a live request). The dropdown exposes only the
  county-wide option plus township/small-claims courts — **there is no
  per-superior-court-division entry** (no way to select the D33 foreclosure
  docket directly; see §4/§5).
- **Categories** checkboxes — coarse case-category filter. Keys (from
  `CategoriesModel`): **`CR`** Criminal & Citation, **`CV`** Civil,
  **`FAM`** Family, **`PR`** Probate. (Mortgage foreclosure lives under **`CV`**.)
  There is **no finer case-type filter** in the request — you cannot ask the
  server for "MF only"; you filter `CaseType` client-side.
- **Status** radios — `ActiveFlag`: `All` / `Open` / `Closed`.
- **File Date** range — `FileStart` / `FileEnd`, mask `mm/dd/yyyy`.
- Sort — `Sort: "FileDate DESC"` (default).

---

## 2. Backing API

| Purpose            | Endpoint (POST, JSON)                                   |
|--------------------|--------------------------------------------------------|
| **Case search**    | `POST /mycase/Search/SearchCases`                      |
| Term formatting    | `POST /mycase/Search/FormatTerms`                      |
| Case detail/docket | `POST /mycase/Case/CaseSummary` (body `{CaseToken,…}`) |
| Court dropdown     | `POST /mycase/Dropdown/GetByKey`                       |
| Current user       | `GET  /mycase/User/Current`                            |

### Request body — `/Search/SearchCases` (captured verbatim from a live search)

```json
{
  "Mode": "ByParty", "CaseNum": null, "CiteNum": null, "CrossRefNum": null,
  "First": null, "Middle": null, "Last": "A*", "Business": null,
  "DoBStart": null, "DoBEnd": null, "OANum": null, "BarNum": null,
  "SoundEx": false, "CourtItemID": 146, "Categories": ["CV"], "Limits": null,
  "Advanced": true, "ActiveFlag": "All", "FileStart": "06/12/2026",
  "FileEnd": "06/26/2026", "CountyCode": null, "NewSearch": true,
  "CaptchaAnswer": null, "Skip": 0, "Take": 25, "Sort": "FileDate DESC"
}
```

### Response envelope

```
{ "Result": { "TotalResults": int, "Skip": int, "Take": int,
              "Sort": str, "Results": [ {caseobj}, ... ],
              "CaptchaKey": null|str, "Url": null|str } }
```

- **Pagination:** `Skip` / `Take`. `TotalResults` is the full count; page until
  `Skip + Take >= TotalResults`. `Take = 100` is honored (verified live).
- **Hard cap:** results are capped at **1000** per query (`ResultsMaxxed` in the
  app). A query whose `TotalResults` ≥ 1000 must be subdivided (narrower surname
  prefix / shorter date window) to avoid silent truncation — the adapter does
  this automatically down to 2-char prefixes.
- **CAPTCHA:** conditional, and it is the **binding constraint on bulk access**.
  A response carries `CaptchaKey` + `Url` once the portal decides a CAPTCHA is
  due; the answer would be replayed as `CaptchaAnswer`. Empirically (live run
  2026-06-26):
    - It is **request-count triggered, not rate triggered** — it fired at
      **request ~47** of a sweep (after 18 surname prefixes), regardless of the
      1.5 s spacing. Slowing down does **not** avoid it; only *fewer requests*
      per session do.
    - It is **IP / session-persistent** — opening a brand-new browser context
      after the trip still returns `CaptchaKey` immediately. A fresh session does
      **not** reset it; the cooldown must elapse.
  The adapter **does not solve CAPTCHAs**: it detects `CaptchaKey`, stops
  politely, persists whatever it has gathered, and sets `captcha_required: true`
  in stats. ⇒ A full A–Z Civil sweep (~80–100 requests for a 14-day window)
  **cannot complete in a single session**. See §5 for the coverage implication.

### Result item shape (keys)

```
CaseID, CaseToken, CaseNumber, CountyCode, CourtCode, Court, FileDate,
CaseStatus, CaseStatusDate, CaseType, CaseSubType, Style, IsActive, IsPublic,
Parties, Attorneys, ShowWarrantIcon, CommCourtFlag, ExpungedCaseFlag,
CiteNumbers, Charges, Flags
```

Field notes:
- `CaseNumber` — e.g. **`49D33-2606-MF-032396`** = `49` (Marion) · `D33`
  (court/division) · `2606` (YYMM filed) · `MF` (case-type code) · `032396` (seq).
- `CaseType` — human label with embedded code, e.g. `"MF - Mortgage Foreclosure"`,
  `"CC - Civil Collection"`, `"CT - Civil Tort"`, `"EV - Evictions (Civil Docket)"`.
- `Style` — the case **caption** (`"Plaintiff v. Defendant"`); the only field that
  encodes plaintiff-vs-defendant role. **Contains party names (PII).**
- `Parties` — flat **comma-separated string** of all party names (PII). Not an
  array; no embedded role labels.
- `Attorneys` — comma-separated counsel surnames string.
- `FileDate` / `CaseStatusDate` — `MM/DD/YYYY`.
- `CaseToken` — opaque per-case key; used for the detail/docket call and the
  public deep link.

### Public case deep link (document access point)

The app builds it as
`#/vw/CaseSummary/<b64>` where
`b64 = base64( JSON.stringify( {"v": {"CaseToken": "<token>"}} ) )`:

```
https://public.courts.in.gov/mycase/#/vw/CaseSummary/<b64>
```

The structured docket + document list is then loaded via
`POST /mycase/Case/CaseSummary` with `{CaseToken}`. The adapter stores the
`CaseToken` and this constructed URL as the case/document link; full document
enumeration is a later phase.

---

## 3. Anti-bot: why we call the SPA's own service layer

A **raw** `fetch`/`POST` to `/Search/SearchCases` (correct body, browser
context, cookies) returns an **HTML portal redirect**, not JSON:

```html
<script>window.location = 'https://public.courts.in.gov/portal/';</script>
```

The endpoint requires the framework's anti-forgery token (`__RequestVerification`,
referenced in `Scripts.js`) and AJAX headers that the app's `$http` wrapper adds.
Rather than reverse-engineer the token, the adapter invokes the app's **own**
service from inside the page:

```js
od.services.Search.SearchCases(body).success(...).failure(...)
```

This reuses the SPA's `$http` (token + headers + cookies) and returns clean JSON.
Mirrors the established Phase 2 pattern (Playwright executing the page's own JS;
see `scrapers/recorder_recordings.py`).

---

## 4. No keyless / date-only search — access strategy

`validateCriteria` (in `ODScripts.js`) **rejects** a search that has only
court + date range + category:

- **ByCase** → requires exactly one of Case / Citation / Cross-Ref number.
- **ByParty** → requires Last / First / Middle / Business / DoB (with Last as the
  anchor for First/Middle/DoB). `Last="*"` alone is rejected — a wildcard must be
  a **trailing** `*` on a value that starts with a letter/number (`"SMITH*"` ok,
  `"*"` / `"*SMITH"` rejected).
- **ByAtty** → requires attorney name or bar number.
- The only keyless exception is a Commercial-court selection (not foreclosures).

⇒ There is **no bulk "all foreclosures filed in date range X"** query. Filing
date is a *filter*, not a query key.

**Adopted strategy — wildcard surname sweep:**
sweep `Last` over `A*`…`Z*`, holding `CourtItemID=146`, `Categories=["CV"]`,
`ActiveFlag` (configurable), `FileStart`/`FileEnd` = the target window; paginate
each prefix; **filter client-side to `CaseType` starting `MF`** (Mortgage
Foreclosure = the Indiana judicial-foreclosure / lis-pendens court signal);
**dedup by `CaseNumber`**. The homeowner **defendant** of essentially every
residential foreclosure is a natural person, so a surname sweep catches them
(the homeowner is exactly the lead target). If a prefix's `TotalResults` ≥ 1000,
the adapter subdivides it (two-letter prefixes) — logged, never silently
truncated.

**Known limitations:**
- Foreclosures with **only** business/LLC parties (no natural person) are not
  caught by a surname sweep — they would require a parallel `Business` wildcard
  sweep. Out of scope for the residential-lead Phase 3; noted for later.
- The CAPTCHA caps a single session's sweep (see §2 / §5).

---

## 5. Live measurements + coverage implication

### CaseType distribution (5 prefixes `A,S,J,M,W`, Marion, Civil, 06/12–06/26)

| CaseType                              | count |
|---------------------------------------|------:|
| CC - Civil Collection                 | 1005  |
| CT - Civil Tort                       |  126  |
| MI - Miscellaneous Civil              |  110  |
| EV - Evictions (Civil Docket)         |   93  |
| **MF - Mortgage Foreclosure**         | **45** |
| XP - Expungement                      |   24  |
| PL - Civil Plenary                    |   24  |
| MC - Reinstatement Waiver             |   11  |
| CE - Commercial Court Eligible        |    7  |
| PC - Post Conviction Relief Petition  |    2  |
| TP - Tax Deed Petition                |    1  |

- The Civil sweep is dominated by CC (collections); MF filters out cleanly
  client-side.
- **Every MF case observed was filed in court `D33`** (`49D33-…-MF-…`) — Marion
  Superior Court 33 is the dedicated mortgage-foreclosure docket. The adapter
  stays Marion-wide (`146`) and filters by type rather than pinning `D33`, both
  because `D33` is **not individually selectable** in the court dropdown and for
  resilience if routing changes.
- Pagination (`Skip`/`Take`) verified across multi-page prefixes;
  `IsPublic: true` on returned cases.

### Coverage implication of the CAPTCHA (production run, `--days-back 14`)

A full-window production run (all-Marion, Civil, MF filter) swept prefixes
**A–R (18 of 26)** and made **47 requests** before the portal returned a
`CaptchaKey`. The adapter paused and persisted **44 unique MF cases**
(43 Pending, 1 Decided; **all in court D33**; filing dates 2026-06-13 → 06-25).
Prefixes S–Z were not reached that session.

Because the CAPTCHA is **count-based (~47 req) and IP-persistent**, and there is
**no way to narrow the search to the D33 foreclosure docket** to cut request
volume, a complete single-session A–Z sweep is not achievable against this
portal. Operator paths to full coverage:

1. **Batched windows across the cooldown** — run narrower date windows (e.g. 3–4
   days) so each A–Z pass stays under ~47 requests, spaced so the CAPTCHA
   cooldown elapses between sessions; accumulate + dedup by `CaseNumber`.
2. **Treat MyCase as the early-signal / backstop source** (its intended role):
   court filing date leads recording date, so even a partial daily pull surfaces
   foreclosures days before the recorder LP appears. The Fidlar recorder remains
   the bulk source of record.
3. CAPTCHA-solving is explicitly **out of scope** (we do not defeat a public
   court system's anti-bot control).

The 44-record partial pull is a **valid, deduped, real result**; the adapter
fails safe (partial save + `captcha_required: true`) rather than truncating
silently.

---

## 6. Field mapping → wrapped raw record (MASTER_PROMPT §4.32)

`raw_record_id = "cf_" + sha1(source_id | CaseNumber)[:20]`. `source_id =
court_filings`. `parser_confidence = 90`. Normalized `raw_payload`:

| canonical field    | from MyCase           |
|--------------------|-----------------------|
| `case_number`      | `CaseNumber`          |
| `case_type_raw`    | `CaseType`            |
| `case_type_code`   | parsed prefix (`MF`)  |
| `case_subtype`     | `CaseSubType`         |
| `filing_date`      | `FileDate` → ISO      |
| `case_status`      | `CaseStatus`          |
| `case_status_date` | `CaseStatusDate` → ISO|
| `court`            | `Court`               |
| `court_code`       | `CourtCode`           |
| `county_code`      | `CountyCode`          |
| `plaintiff`        | `Style` (before ` v. `) |
| `defendant`        | `Style` (after ` v. `)  |
| `caption`          | `Style`               |
| `parties_raw`      | `Parties`             |
| `attorneys_raw`    | `Attorneys`           |
| `case_token`       | `CaseToken`           |
| `case_id`          | `CaseID`              |
| `is_active`        | `IsActive`            |
| `case_detail_url`  | constructed (§2)      |

All party names / captions stay in `data/raw/` (gitignored); only case numbers,
types and counts go to stdout.

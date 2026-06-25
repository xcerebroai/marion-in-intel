# Build Eligibility Report — Marion County, Indiana
# Phase 0 v5.3.0 Amendment — Recon artifact
# Generated: 2026-06-25

Formal build eligibility report per Build Mode Protocol §02.1.
Companion to build_eligibility_handoff.md.

---

## County

    County: Marion County, Indiana
    Slug: marion_in
    FIPS: 18097
    Government structure: Consolidated City-County (Indianapolis / Marion County
                          Consolidated Government "Unigov", established 1970)
    State foreclosure type: JUDICIAL (Indiana uses judicial foreclosure via
                            Circuit/Superior Court)

---

## Build Mode Entry Precondition Check (§02.1)

    [ PASS ] Source-of-Record Matrix exists (source_of_record_matrix.json)
    [ PASS ] Matrix validates (per county config schema sourceOfRecordMatrix $def)
    [ PASS ] Matrix county_build_status: READY_TO_BUILD
    [ PASS ] At least one lead_type has status LIVE_SOURCE_FOUND (20 of 27)
    [ PASS ] Primary event sources have completed PDF/sample inspection (per
             document_type_discovery.md — index metadata confirmed; doc images
             N/A for lead generation at index metadata level)
    [ PASS ] Primary event sources have bulk-availability classification (per
             build_eligibility_handoff.md)
    [ PASS ] All sources have documented-API discovery report (api_discovery_report.md)

    All Build Mode entry preconditions: SATISFIED

---

## Build Mode Classification

    county_build_status: READY_TO_BUILD
    build_mode_classification: FULL_BUILD

    Rationale: All 6 primary event sources are LIVE_SOURCE_FOUND or
    LIVE_SOURCE_FOUND_LIMITED_COVERAGE. No required primary source is blocked.
    The one blocked source (PACER/Bankruptcy) is not a county source, is low
    priority for initial build, and does not block the other 24 accessible lead
    types. Full build authorized across all primary source categories.

---

## Primary Event Sources — Status Summary

    Source                          Access              Status
    ---------------------------------------------------------------------------
    Marion County Recorder (Fidlar) SEARCH_ONLY_PUBLIC  LIVE_SOURCE_FOUND
    Indiana MyCase (courts)         OPEN_PUBLIC         LIVE_SOURCE_FOUND
    GovEase (Sheriff Sales)         OPEN_PUBLIC         LIVE_SOURCE_FOUND
    Marion County Treasurer (Tax)   OPEN_PUBLIC         LIVE_SOURCE_FOUND
    Accela (Code Enforcement)       OPEN_PUBLIC         LIVE_SOURCE_FOUND
    Open Indy Portal (CE bulk)      OPEN_PUBLIC/API     LIVE_SOURCE_FOUND

---

## Lead Type Coverage Summary

    Total lead types in sweep:           27
    LIVE_SOURCE_FOUND:                   20 (74%)
    LIVE_SOURCE_FOUND_LIMITED_COVERAGE:  2 (7%)
    NOT_APPLICABLE_IN_STATE:             3 (11%)
    SOURCE_FOUND_BLOCKED:                1 (4%) — Bankruptcy/PACER
    SOURCE_NOT_FOUND:                    0

---

## Verdict

    Build Eligibility Gate: READY_TO_BUILD
    Build Mode Classification: FULL_BUILD

    This county is authorized to proceed to Build Mode (Phase 1+) upon
    operator approval. No operator credentials, payments, CAPTCHA solvers,
    or proxies are required to begin the build.

    Phase 0.5 (Auto-Resolve Blockers): SKIPPED — NO BLOCKERS
    (All primary sources are accessible. The only blocker is PACER which
    requires a payment decision from the operator — not an auto-resolvable
    technical blocker.)

# Build Eligibility Handoff — Marion County, Indiana
# Phase 0.G / §01.15 — Recon artifact
# Generated: 2026-06-25

This document records the blocker classification (Phase 0.G) and the Build
Eligibility Gate verdict with justification trail (§01.15 / §4.10).

---

## Counts

    VERIFIED_OFFICIAL sources:              8
    Sources by role:
        PRIMARY_LEAD_SOURCE:                6 (Recorder, MyCase, GovEase, Treasurer,
                                              Accela, Open Indy Data Portal CE bulk)
        ENRICHMENT_SOURCE:                  4 (Open Indy Parcels, Assessor/IndyGIS,
                                              GIS Open Data, Indiana Gateway DLGF)
        REFERENCE_ONLY:                     1 (IARA Historical)
        BLOCKED_SOURCE:                     1 (PACER — federal bankruptcy)
        NOT_FOUND:                          0

    Sources by access classification:
        OPEN_PUBLIC:                        7 (MyCase, GovEase, Treasurer, Accela,
                                              Open Indy Portal, Assessor/IndyGIS,
                                              GIS Open Data)
        SEARCH_ONLY_PUBLIC:                 1 (Recorder/Fidlar Direct Search)
        BLOCKED:                            0
        PAID_SUBSCRIPTION_REQUIRED:         0 (among verified primary sources)

---

## Accessible Primary Sources

    PRIMARY_LEAD_SOURCE sources intersected with OPEN_PUBLIC or SEARCH_ONLY_PUBLIC:

    1. Marion County Recorder (Fidlar) — SEARCH_ONLY_PUBLIC
       Document images: paid, but index metadata is FREE and sufficient for
       lead generation. SEARCH_ONLY_PUBLIC is ACCEPTABLE per §01.16.
       Accessible primary document types: LP, ML, AJ, FTL, State Tax Warrant,
       AH, ED, AD, TD (see document_type_discovery.md)

    2. Indiana MyCase — OPEN_PUBLIC
       Fully accessible. All case types (MF, EV, EM/ES/EU, CP, CC) publicly
       searchable and docket metadata viewable. Document images publicly
       viewable for most case types per Indiana access matrix.
       Accessible primary case types: MF (foreclosure), EV (eviction),
       EM/ES/EU (probate/estate), CP/CC (civil judgment)

    3. GovEase (Sheriff Sales) — OPEN_PUBLIC
       Fully accessible. Listing browse public without registration. Property
       address, case #, plaintiff/defendant, sale date, opening bid all public.
       Accessible signals: active judicial foreclosure sales pipeline.

    4. Marion County Treasurer (Tax Delinquency) — OPEN_PUBLIC
       Accessible via downloadable annual lists + tax sale reports page.
       Accessible primary signals: annual tax delinquency list, tax sale
       certificates, sold property records.
       Caveat: annual publication cycle (not real-time); mid-July availability.

    5. Accela (Code Enforcement) — OPEN_PUBLIC
       Fully accessible for case search. Code enforcement violation cases,
       demolition orders, condemnation cases searchable by address.

    6. Open Indy Data Portal (CE bulk) — OPEN_PUBLIC / API
       Documented ArcGIS API. Bulk CSV + API access. Same code enforcement data
       as Accela but in bulk form. Preferred for pipeline automation.

    Accessible primary sources count: 6 of 6 verified primary sources
    Accessible primary document types confirmed: YES (per document_type_discovery.md)

---

## Blockers by Type

    Technical blockers (auto-resolvable):    0
        (All primary sources accessible without technical bypass)

    Permission blockers (require operator):  1
        PACER (federal bankruptcy): PAID_ACCESS_REQUIRED
        next_access_strategy: use_paid_subscription_if_operator_provides
        This is a federal court source, not county. Low priority for initial build.

    Hard blockers:                           0
        (No Cloudflare/IP-block issues identified)

    Not found:                               0
        (All standard primary source categories found)

    State-specific N/A:                      3
        Trustee Sale, Notice of Trustee Sale, Notice of Substitute Trustee Sale
        are NOT APPLICABLE in Indiana (judicial foreclosure state). These lead
        types do not exist in Indiana public records.

---

## 27 Lead Type Sweep — Complete

Per §01.21 (v5.3.0 amendment):

    1.  Foreclosure           — LIVE_SOURCE_FOUND  — Indiana MyCase (MF)
    2.  Trustee Sale          — NOT_APPLICABLE_IN_STATE (Indiana: judicial only)
    3.  Notice Trustee Sale   — NOT_APPLICABLE_IN_STATE
    4.  Notice Sub. Trustee   — NOT_APPLICABLE_IN_STATE
    5.  Sheriff Sale          — LIVE_SOURCE_FOUND  — GovEase
    6.  Tax Lien Foreclosure  — LIVE_SOURCE_FOUND  — Treasurer + GovEase Tax
    7.  Tax Sale              — LIVE_SOURCE_FOUND  — GovEase Tax / indy.gov
    8.  Tax Sale Certificate  — LIVE_SOURCE_FOUND  — Recorder (Fidlar) + Treasurer
    9.  Tax Delinquency       — LIVE_SOURCE_FOUND  — Treasurer / indy.gov
    10. Lis Pendens           — LIVE_SOURCE_FOUND  — Recorder (Fidlar)
    11. Civil Judgment        — LIVE_SOURCE_FOUND  — MyCase (CP/CC)
    12. Abstract of Judgment  — LIVE_SOURCE_FOUND  — Recorder (Fidlar)
    13. Mechanic Lien         — LIVE_SOURCE_FOUND  — Recorder (Fidlar)
    14. Construction Lien     — LIVE_SOURCE_FOUND  — Recorder (Fidlar)
    15. Federal Tax Lien      — LIVE_SOURCE_FOUND  — Recorder (Fidlar)
    16. State Tax Lien        — LIVE_SOURCE_FOUND  — Recorder (Fidlar) [IN DOR warrants]
    17. Probate               — LIVE_SOURCE_FOUND  — MyCase (EM/ES/EU)
    18. Affidavit of Heirship — LIVE_SOURCE_FOUND  — Recorder (Fidlar)
    19. Executor Deed         — LIVE_SOURCE_FOUND  — Recorder (Fidlar)
    20. Administrator Deed    — LIVE_SOURCE_FOUND  — Recorder (Fidlar)
    21. Code Lien             — LIVE_SOURCE_FOUND  — Accela + Open Indy Portal
    22. Demolition            — LIVE_SOURCE_FOUND  — Accela + Open Indy Portal
    23. Condemnation          — LIVE_SOURCE_FOUND  — Accela + Open Indy Portal
    24. Eviction              — LIVE_SOURCE_FOUND  — MyCase (EV)
    25. Divorce               — LIVE_SOURCE_FOUND_LIMITED_COVERAGE — MyCase (DN);
                                low lead value without property intersection
    26. Bankruptcy            — SOURCE_FOUND_BLOCKED — PACER (federal);
                                requires paid subscription
    27. Surplus               — LIVE_SOURCE_FOUND_LIMITED_COVERAGE — GovEase
                                (post-sale surplus tracking); limited data

    LIVE_SOURCE_FOUND:                      20 lead types
    LIVE_SOURCE_FOUND_LIMITED_COVERAGE:     2 lead types
    NOT_APPLICABLE_IN_STATE:                3 lead types
    SOURCE_FOUND_BLOCKED:                   1 lead type (Bankruptcy / PACER)

---

## Bulk Data Availability Classification (§01.24)

    Marion County Recorder (Fidlar):
        bulk_availability: PER_RECORD_ONLY (Direct Search tier is per-query,
                           not bulk export). Laredo subscription may provide
                           bulk access — to confirm in Phase 1.
        coverage_implication: Records accessible by name/date/doc-type search.
                              Initial pipeline fetch may require iterative date-
                              range queries. Full historical backfill feasible
                              via date-range iteration.

    Indiana MyCase:
        bulk_availability: BATCH_QUERY (search by case type + county + date
                           range returns multiple results; Playwright required
                           for SPA; no bulk download confirmed)
        coverage_implication: Date-range filtered searches by case type (MF, EV,
                              EM) allow systematic population of lead backlog.

    GovEase (Sheriff Sales):
        bulk_availability: FULL_COUNTY_BULK (browse-all-active-listings page
                           returns all current Marion County sheriff sale listings)
        coverage_implication: Full current sale schedule accessible in one browse.

    Marion County Treasurer (Tax Delinquency):
        bulk_availability: FULL_COUNTY_BULK (annual downloadable list)
        coverage_implication: Full annual delinquency list downloadable once
                              per year. Not real-time.

    Accela (Code Enforcement):
        bulk_availability: PER_RECORD_ONLY (address-based search only)
        coverage_implication: Prefer Open Indy Data Portal bulk API.

    Open Indy Data Portal (Code Enforcement + Parcels):
        bulk_availability: FULL_COUNTY_BULK (complete dataset downloadable)
        coverage_implication: Full code enforcement and parcel datasets accessible
                              via ArcGIS API or bulk CSV download. No coverage gap.

---

## Recommended Provisional Verdict

    READY_TO_BUILD

    Justification:
        Condition 1 — At least one verified primary lead source is fully
        accessible without operator escalation: TRUE.
        Six verified primary lead sources all accessible at OPEN_PUBLIC or
        SEARCH_ONLY_PUBLIC tier. No login, no payment, no operator credentials
        required for any primary source.

        Condition 2 — At least one accessible primary document type: TRUE.
        20 of 27 lead types have LIVE_SOURCE_FOUND status. Primary document
        types confirmed across all key categories (foreclosure, probate,
        recorder instruments, code enforcement, sheriff sales, tax delinquency).

        Condition 3 — No critical blocker prevents Phase 1+ work: TRUE.
        The only blocker is PACER (federal bankruptcy) which is low-priority,
        not a county source, and not required for an initial build. All county-
        level primary sources are accessible.

        Condition 4 — Enrichment available: TRUE.
        Four verified enrichment sources available, including bulk parcel dataset
        with owner info and assessed values updated nightly via ArcGIS API.

        Condition 5 — County config will pass schema validation: LIKELY (to be
        confirmed after Step 4 config write).

    No Do Not Proceed Matrix conditions (§4.11) fire.

---

## Recommended Operator Next Actions

    1. Approve Build Mode to proceed to Phase 1 (portal fingerprinting + scraper
       adapter selection) for the following sources in priority order:
           a. Indiana MyCase — foreclosure (MF) scraper via Playwright/Odyssey API
           b. Marion County Recorder (Fidlar) — lis pendens + recorder instruments
           c. Open Indy Data Portal — code enforcement bulk via ArcGIS API
           d. GovEase — sheriff sale listings via HTML scraper
           e. Marion County Treasurer — tax delinquency annual list download

    2. Open question: confirm exact Fidlar Direct Search document type dropdown
       labels in Phase 1 portal fingerprinting.

    3. Open question: confirm exact format (PDF vs. CSV) and URL of Marion County
       Treasurer annual delinquency list download in Phase 1.

    4. Optional — evaluate PACER paid access for bankruptcy leads if operator
       wants that lead type.

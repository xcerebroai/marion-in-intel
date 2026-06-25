# Recon Summary — Marion County, Indiana
# Phase 0 Final Artifact — §01.15 / §01.18
# Generated: 2026-06-25

This is the operator-facing executive summary of the Phase 0 recon for
Marion County, Indiana. Full justification trail in build_eligibility_handoff.md.

---

## County Overview

Marion County, Indiana is one of the most buildable counties in the Midwest.
It is home to Indianapolis — the state capital and a major metro area with
one of the highest eviction filing rates in the nation. Marion County operates
under a consolidated city-county government structure (Unigov since 1970).
Indiana uses judicial foreclosure exclusively; all foreclosures go through the
Marion County Superior Court and are trackable via the statewide MyCase portal.

---

## Build Eligibility Gate Verdict

    BUILD VERDICT:    READY_TO_BUILD
    BUILD LABEL:      FULL_BUILD
    PHASE 0.5:        SKIPPED — NO BLOCKERS

---

## Source Snapshot (6 Primary Lead Sources — All Accessible)

    1. Marion County Recorder (Fidlar/Laredo)
       URL: inmarion.fidlar.com/INMarion/DirectSearch/
       Access: Free index search; doc images have per-copy fee (not needed for leads)
       Signal types: Lis pendens, judgment liens, mechanic liens, FTL/state tax
                     warrants, affidavits of heirship, executor/administrator deeds

    2. Indiana Courts Case Search (MyCase)
       URL: public.courts.in.gov/mycase/
       Access: Fully public, free, no login required
       Signal types: Foreclosure filings (MF), eviction cases (EV), probate/
                     estate (EM/ES/EU), civil judgments (CP/CC)

    3. GovEase — Sheriff Foreclosure Sales
       URL: liveauctions.govease.com/in/inmarion/
       Access: Fully public, free listing browse; third Friday of each month
       Signal types: Active sheriff sale listings (judicial foreclosure pipeline)

    4. Marion County Treasurer — Tax Sale Hub
       URL: indy.gov/activity/tax-sale-reports (+ GovEase for auction)
       Access: Annual downloadable delinquency list; publicly accessible
       Signal types: Tax delinquency, tax sale certificates, sold tax sale properties

    5. Accela — Code Enforcement
       URL: aca-prod.accela.com/INDY/Cap/CapHome.aspx?module=Enforcement
       Access: Fully public search, no login required
       Signal types: Code violations, demolition orders, condemnation cases

    6. Open Indy Data Portal — Code Enforcement Bulk + Parcels
       URL: data.indy.gov (ArcGIS Hub; documented REST API)
       Access: Fully public API; bulk CSV download; nightly updates
       Signal types: Code enforcement (same as Accela, bulk form — preferred for pipeline)
       Enrichment: 348,272+ parcel records with owner info + assessed values

---

## Enrichment Summary

    Three robust, publicly available enrichment sources:
        - Open Indy Data Portal parcels (bulk CSV / ArcGIS API — nightly update)
        - Marion County Assessor / IndyGIS (per-record query)
        - Marion County GIS Open Data Portal (ArcGIS Hub, spatial layers)

    Enrichment is fully accessible without credentials. Entity resolution key:
    Marion County parcel ID format confirmed. The Open Indy bulk parcel dataset
    is the highest-quality enrichment source — 348k+ parcels, updated nightly.

---

## Blocked Sources

    Bankruptcy (PACER): Federal court, paid access required ($0.10/page).
    Not a county source. Low priority for initial build. One operator decision
    needed to add this lead type: subscribe to PACER and declare credentials.

---

## Lead Type Coverage

    20/27 lead types fully accessible (LIVE_SOURCE_FOUND)
    2/27 limited coverage (Divorce, Surplus)
    3/27 not applicable in Indiana (Trustee Sale variants — judicial state)
    1/27 blocked (Bankruptcy — PACER/federal)
    0/27 not found

---

## Indiana-Specific Notes

    - Indiana is a JUDICIAL FORECLOSURE state. All foreclosures go through
      Marion County Superior Court. No trustee sale, no notice of substitute
      trustee sale. Lis pendens is the primary pre-foreclosure public notice.

    - Marion County has one of the highest eviction filing rates in the United
      States. Eviction cases on MyCase are a high-volume lead source for
      landlord-distress and tenant-occupied property leads.

    - The consolidated Unigov structure means the City of Indianapolis and
      Marion County share a single government. All city code enforcement,
      treasurer, and assessor records serve the entire county.

    - Marion County has several "excluded cities" (Beech Grove, Lawrence,
      Southport, Speedway, and several small towns) that have their own
      local government but are still within Marion County's jurisdiction for
      recorder, court, and state-level records.

---

## Phase 0 Artifact Checklist

    [x] runs/marion_in/recon/source_discovery.md
    [x] runs/marion_in/recon/source_verification.md
    [x] runs/marion_in/recon/portal_fingerprints.md
    [x] runs/marion_in/recon/access_classification.md
    [x] runs/marion_in/recon/source_role_classification.md
    [x] runs/marion_in/recon/document_type_discovery.md
    [x] runs/marion_in/recon/build_eligibility_handoff.md
    [x] runs/marion_in/recon/recon_summary.md (this file)
    [x] runs/marion_in/recon/source_of_record_matrix.json (v5.3.0)
    [x] runs/marion_in/recon/source_of_record_matrix.md (v5.3.0)
    [x] runs/marion_in/recon/source_coverage_map.md (v5.3.0)
    [x] runs/marion_in/recon/api_discovery_report.md (v5.3.0)
    [x] runs/marion_in/recon/operator_verified_sources.yml (v5.3.0)
    [x] runs/marion_in/recon/build_eligibility_report.md (v5.3.0)

---

## No Framework Files Modified

No files outside runs/marion_in/ and config/counties/marion_in.json were
modified during this Phase 0 run. No scraper code, translator code, or dashboard
code was created. No commits were made.

---

## Recommended Next Action

Operator authorization to proceed to Build Mode (Phase 1). All preconditions
are met for a FULL_BUILD.

# Source Role Classification — Marion County, Indiana
# Phase 0.E — Recon artifact
# Generated: 2026-06-25

Role classification per §4.9 source hierarchy and §01.10 / §01.11 rules.
PRIMARY_LEAD_SOURCE entries can create leads. ENRICHMENT_SOURCE entries cannot.

---

## Marion County Recorder — Fidlar/Laredo

    name:                Marion County Recorder (Fidlar/Laredo)
    source_role:         PRIMARY_LEAD_SOURCE
    rationale:           County clerk/recorder is Tier 1 per §4.9. Recorded
                         instruments include: lis pendens (LP — foreclosure
                         notice), mechanic/construction liens (ML, CL), judgment
                         liens (AJ, abstract of judgment), federal tax liens
                         (IRS filed with county recorder), Indiana state tax
                         warrants (DOR files with county recorder), affidavits
                         of heirship (estate/inheritance indicator), executor/
                         administrator deeds (post-probate property transfer),
                         sheriff's deeds (post-foreclosure transfer), treasurer's
                         deeds (post-tax-sale transfer), quitclaim deeds (possible
                         distress indicator in combination with other signals).
                         All are Tier 1 primary lead events.
    section_13_reference: §4.9 Tier 1 — Clerk records / recorder records, liens,
                          lis pendens, judgments, recorded notices.

---

## Indiana MyCase (Court Filings — Foreclosure, Civil, Eviction, Probate)

    name:                Indiana Courts Case Search (MyCase)
    source_role:         PRIMARY_LEAD_SOURCE
    rationale:           Court filings are Tier 1 per §4.9. Specifically:
                         Mortgage Foreclosure (MF cases) — direct foreclosure
                         distress signal; Eviction (EV cases) — landlord/tenant
                         distress; Civil Plenary/Collections (CP/CC cases) —
                         judgment source (judgment liens recorded with recorder
                         after entry); Probate/Estate (EM/ES/EU cases) — estate
                         leads for inherited/heir-owned properties. MyCase is
                         the statewide portal for ALL Indiana court records
                         including Marion County.
    section_13_reference: §4.9 Tier 1 — Court filings (foreclosure cases,
                          probate cases, civil judgments, evictions).

---

## GovEase (Marion County Sheriff Foreclosure Sales)

    name:                GovEase — Sheriff Sales
    source_role:         PRIMARY_LEAD_SOURCE
    rationale:           Sheriff sale records are Tier 1 per §4.9. Active sale
                         listings represent properties at the end of the judicial
                         foreclosure pipeline — highest distress signal category.
                         Also signals: defendant/borrower identity, property
                         address, pending loss of title. Sale dates provide
                         timing for investor outreach window.
    section_13_reference: §4.9 Tier 1 — Sheriff sales / auction results.

---

## Marion County Treasurer (Tax Delinquency / Tax Sale)

    name:                Marion County Treasurer — Tax Sale Hub
    source_role:         PRIMARY_LEAD_SOURCE
    rationale:           Tax delinquency events and tax sale events are Tier 1
                         per §4.9. The annual delinquent parcel list (eligible
                         for tax sale) identifies properties where owners have
                         failed to pay property taxes — high distress signal.
                         Tax sale certificates are primary recorded events.
                         Post-sale surplus funds and redemption periods are
                         supporting signals.
    section_13_reference: §4.9 Tier 1 — Tax collector delinquency lists, tax
                          sale events.

---

## Accela (Code Enforcement)

    name:                Accela Citizen Access — Code Enforcement Module
    source_role:         PRIMARY_LEAD_SOURCE
    rationale:           Code enforcement events (when they expose violations
                         with liens, demolition orders, or condemnation notices)
                         are Tier 1 per §4.9. Marion County/Indianapolis has
                         active code enforcement via the Department of Code
                         Enforcement (DCE). Demolition and condemnation cases
                         in particular are high-distress signals indicating
                         property in severe disrepair — owner may be motivated
                         to sell quickly to avoid further city action.
    section_13_reference: §4.9 Tier 1 — Code enforcement events (violations /
                          liens / demolition / condemnation / nuisance).

---

## Open Indy Data Portal — Code Enforcement Bulk Dataset

    name:                Open Indy Data Portal — Code Enforcement Violations
    source_role:         PRIMARY_LEAD_SOURCE
    rationale:           Same data as Accela but in bulk downloadable form
                         (CSV/API via ArcGIS Hub). Preferred for pipeline
                         automation — bulk download is faster and more reliable
                         than per-record Accela scraping. Bulk form of a
                         PRIMARY_LEAD_SOURCE.
    section_13_reference: §4.9 Tier 1 — Code enforcement events (bulk channel).

---

## Open Indy Data Portal — Parcels Dataset

    name:                Open Indy Data Portal — Parcels w/ Owner Info + AV
    source_role:         ENRICHMENT_SOURCE
    rationale:           Parcel data with owner information and assessed values
                         is Tier 3 per §4.9 — ENRICHMENT ONLY. Cannot create
                         leads. Used to enrich lead rows with: situs address,
                         owner name (mailing), assessed value, property
                         characteristics, parcel ID for entity resolution.
                         A parcel record alone is NOT a lead.
    section_13_reference: §4.9 Tier 3 — Parcel data, assessor data, owner
                          mailing data, valuation data.

---

## Marion County Assessor / IndyGIS

    name:                Marion County Assessor — Property Report Cards
    source_role:         ENRICHMENT_SOURCE
    rationale:           Assessor property record data is Tier 3 — enrichment
                         only. Provides assessed values, sales history, property
                         characteristics. Cannot create leads. Same underlying
                         data as Open Indy Data Portal parcels.
    section_13_reference: §4.9 Tier 3 — Assessor / appraisal district parcel
                          master.

---

## Marion County GIS Open Data Portal

    name:                Marion County GIS Open Data Portal
    source_role:         ENRICHMENT_SOURCE
    rationale:           GIS parcel layers are Tier 3 — enrichment only.
                         Provides spatial parcel polygons for geocoding and
                         boundary validation. Cannot create leads.
    section_13_reference: §4.9 Tier 3 — GIS parcel layers.

---

## Indiana Gateway / DLGF

    name:                Indiana Gateway — Tax Bill Look Up
    source_role:         ENRICHMENT_SOURCE
    rationale:           Per-parcel tax bill lookup returns current assessed
                         value and tax amount. Enrichment-only; does not expose
                         delinquency events directly. Redundant with Open Indy
                         Data Portal for most use cases.
    section_13_reference: §4.9 Tier 3 — Enrichment sources.

---

## IARA Historical Records

    name:                Indiana Archives and Records Administration (IARA)
    source_role:         REFERENCE_ONLY
    rationale:           Historical archival records only. No current lead
                         generation value. Not included in pipeline build.
    section_13_reference: Reference — out of scope for lead pipeline.

---

## PACER / Federal Bankruptcy Court

    name:                PACER — Federal Bankruptcy Court
    source_role:         BLOCKED_SOURCE
    rationale:           Bankruptcy filings are filed in the U.S. Bankruptcy
                         Court for the Southern District of Indiana — a federal
                         court, not a county court. PACER (Public Access to
                         Court Electronic Records) requires paid subscription
                         ($0.10/page, minimum quarterly spend). No free public
                         portal equivalent to MyCase exists for federal
                         bankruptcy records. Blocker: PAID_ACCESS_REQUIRED.
                         next_access_strategy: use_paid_subscription_if_operator_provides.
                         Not a county-level source — framework primary intent
                         is county public records.
    section_13_reference: §4.9 — Blocked source; federal (not county) jurisdiction.

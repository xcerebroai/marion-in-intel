# Source Coverage Map — Marion County, Indiana
# Phase 0 v5.3.0 Amendment — Recon artifact
# Generated: 2026-06-25

Summary of live, blocked, limited, and not-found sources / lead types.
Companion to source_of_record_matrix.json.

---

## Live Sources (PRIMARY_LEAD_SOURCE, fully accessible)

    1. Marion County Recorder — Fidlar/Laredo Direct Search
       URL: https://inmarion.fidlar.com/INMarion/DirectSearch/
       Access: SEARCH_ONLY_PUBLIC (metadata free; doc images paid)
       Covers lead types: Lis Pendens, Mechanic Lien, Construction Lien,
                          Abstract of Judgment, Federal Tax Lien, State Tax Lien,
                          Affidavit of Heirship, Executor Deed, Administrator Deed,
                          Tax Sale Certificate (Treasurer's Deed)

    2. Indiana Courts Case Search (MyCase)
       URL: https://public.courts.in.gov/mycase/
       Access: OPEN_PUBLIC
       Covers lead types: Foreclosure (MF), Eviction (EV), Probate/Estate
                          (EM/ES/EU), Civil Judgment (CP/CC)

    3. GovEase — Marion County Sheriff Sales
       URL: https://liveauctions.govease.com/in/inmarion/
       Access: OPEN_PUBLIC
       Covers lead types: Sheriff Sale (active foreclosure sales pipeline)

    4. Marion County Treasurer / indy.gov
       URL: https://www.indy.gov/activity/tax-sale-reports
       Access: OPEN_PUBLIC (annual downloadable files)
       Covers lead types: Tax Delinquency, Tax Sale, Tax Lien Foreclosure

    5. Accela Citizen Access — Code Enforcement
       URL: https://aca-prod.accela.com/INDY/Cap/CapHome.aspx?module=Enforcement
       Access: OPEN_PUBLIC
       Covers lead types: Code Lien, Demolition, Condemnation, Code Violation

    6. Open Indy Data Portal — Code Enforcement Bulk (ArcGIS)
       URL: https://data.indy.gov/datasets/5d08eba2e9034bc88986af25afe12f5e_1
       Access: OPEN_PUBLIC / API_ENDPOINT
       Covers lead types: Code Lien, Demolition, Condemnation (bulk form; same
                          coverage as Accela, preferred for pipeline)

---

## Blocked Sources

    1. PACER — Federal Bankruptcy Court
       Access: PAID_SUBSCRIPTION_REQUIRED
       Covers lead types: Bankruptcy
       Blocker reason: Federal court (U.S. Bankruptcy Court, S.D. Indiana);
                       requires PACER account at $0.10/page or quarterly minimum.
       Next access strategy: use_paid_subscription_if_operator_provides

---

## Limited Coverage Sources

    1. Divorce (MyCase DN case type)
       Access: OPEN_PUBLIC (same MyCase portal)
       Coverage limitation: Available but low lead value without property
                            intersection data in the case record. Divorce cases
                            do not expose property address in case caption.
                            Limited use without manual cross-referencing to
                            recorder data.

    2. Surplus (GovEase post-sale)
       Access: OPEN_PUBLIC (GovEase lists closed sales with surplus info)
       Coverage limitation: Surplus tracking available post-sale; limited
                            data on surplus amounts in browsable listing.

---

## Not-Found Lead Types

    None — all 27 lead types either found, not applicable, blocked (one), or
    limited coverage (two).

---

## Not Applicable in State

    1. Trustee Sale — Indiana is judicial foreclosure only
    2. Notice of Trustee Sale — same
    3. Notice of Substitute Trustee Sale — same

---

## Enrichment Sources (Verified)

    1. Open Indy Data Portal — Parcels w/ Owner Info + AV
       URL: https://data.indy.gov/datasets/parcels
       Access: OPEN_PUBLIC / API — bulk CSV download, nightly update
       Coverage: 348,272+ Marion County parcels with owner name, address,
                 assessed value, parcel number

    2. Marion County Assessor — Property Report Cards (IndyGIS)
       URL: https://maps.indy.gov/AssessorPropertyCards/
       Access: OPEN_PUBLIC (per-record search)
       Coverage: All Marion County parcels; redundant with Open Indy Data Portal

    3. Marion County GIS Open Data Portal
       URL: https://gis-marioncounty.opendata.arcgis.com/
       Access: OPEN_PUBLIC / API (ArcGIS Hub)
       Coverage: Full Marion County GIS layers (parcel polygons, zoning, etc.)

    4. Indiana Gateway — Tax Bill Look Up (DLGF)
       URL: https://gateway.ifionline.org/TaxBillLookUp/Default.aspx
       Access: OPEN_PUBLIC (per-record query)
       Coverage: Statewide per-parcel assessed value + tax bill

---

## Operator Review Required

    None — all sources classified with HIGH or MEDIUM confidence.
    Open questions captured in build_eligibility_handoff.md but do not
    block build authorization.

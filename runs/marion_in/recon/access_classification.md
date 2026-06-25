# Access Classification — Marion County, Indiana
# Phase 0.D — Recon artifact
# Generated: 2026-06-25

Classification per §01.9 canonical access taxonomy. Evidence recorded for each.

---

## Marion County Recorder — Fidlar/Laredo (Direct Search)

    name:                Marion County Recorder (Fidlar/Laredo)
    access_classification: SEARCH_ONLY_PUBLIC
    evidence:            Direct Search at inmarion.fidlar.com/INMarion/DirectSearch/
                         is publicly accessible without login. Basic grantor/grantee
                         name search and instrument number lookup returns index
                         metadata (document type, recording date, book/page,
                         instrument number, grantor, grantee) without payment.
                         Document image copies (PDF/TIFF) require a Laredo
                         account with per-copy fee or a Laredo subscription.
                         Classification: search and result metadata are free;
                         document images are behind payment.
    notes:               SEARCH_ONLY_PUBLIC is acceptable for the framework.
                         Document images are NOT required to produce matched
                         leads from search metadata. All primary lead-type
                         signals (lis pendens, judgment liens, tax warrants,
                         mechanic liens, affidavits of heirship) are identifiable
                         from the index metadata alone (doc type + parties +
                         recording date + instrument number).

---

## Indiana MyCase (Tyler Odyssey)

    name:                Indiana Courts Case Search (MyCase)
    access_classification: OPEN_PUBLIC
    evidence:            Case search confirmed fully public at
                         public.courts.in.gov/mycase/. No login or registration
                         required. Search by party name or case number returns
                         full docket for any public case. Non-confidential
                         orders, judgment entries, and foreclosure documents
                         viewable online per Indiana Judicial Branch public
                         access matrix. Some case-specific documents restricted
                         to in-person clerk access (noted in framework as
                         DOCUMENTS_PUBLIC for the lead-relevant document types).
    notes:               Best primary lead source for all court-originated
                         distress signals. Foreclosure (MF), eviction (EV),
                         civil judgment (CP/CC), and probate (EM/ES/EU) are
                         all fully accessible. No access barrier.

---

## GovEase (Sheriff Sales)

    name:                GovEase — Marion County Sheriff Foreclosure Sales
    access_classification: OPEN_PUBLIC
    evidence:            Property listing browse at liveauctions.govease.com/in/inmarion/
                         confirmed publicly accessible without registration.
                         Property cards showing address, case #, defendant name,
                         plaintiff name, sale date, and opening bid are all
                         publicly viewable. Registration to GovEase.com required
                         only to submit bids. Lead extraction (property address,
                         case #, party names, sale date) requires no account.
    notes:               Third Friday of each month (except December). Properties
                         listed ~30 days before sale; removed from active listings
                         at/after sale. Important for lifecycle tracking —
                         configure expire_if_not_seen_runs accordingly.

---

## Marion County Treasurer (Tax Delinquency/Sale)

    name:                Marion County Treasurer — Tax Sale Hub
    access_classification: OPEN_PUBLIC
    evidence:            Tax sale information pages at indy.gov confirmed publicly
                         accessible. Annual delinquent parcel lists published as
                         downloadable files (PDF or CSV) before each fall tax sale.
                         Sold tax sale property lookup available online without
                         login. GovEase auction platform for bidding requires
                         registration, but listing browse is public.
    notes:               Annual publication cycle for delinquency lists (mid-July
                         before fall sale). Real-time delinquency data is NOT
                         available — the delinquency list is a point-in-time
                         annual snapshot. Build pipeline must account for this
                         refresh cadence (expected_refresh_cadence: MANUAL /
                         ANNUALLY). For live tax-delinquent-parcel data, the
                         recorder's tax warrant recording is the real-time signal.

---

## Accela Citizen Access (Code Enforcement)

    name:                Accela — Code Enforcement Module
    access_classification: OPEN_PUBLIC
    evidence:            Code enforcement case search at aca-prod.accela.com/INDY/
                         confirmed publicly accessible without login or fee.
                         Address search and case number search return enforcement
                         case records with status (open, closed), case type
                         (violation, demolition, condemnation), and inspection
                         history. Login required only for applicant functions.
    notes:               Accela ViewState/session tokens add MEDIUM scrape
                         difficulty but do not block public access. Playwright
                         recommended for automation. Open Indy Data Portal
                         bulk code enforcement dataset is preferred for pipeline
                         use (CSV/API; same underlying data, no ViewState
                         complexity).

---

## Open Indy Data Portal (Bulk Datasets)

    name:                Open Indy Data Portal — ArcGIS Hub
    access_classification: OPEN_PUBLIC
    evidence:            data.indy.gov confirmed publicly accessible. Code
                         enforcement violations dataset and parcels dataset
                         both confirmed publicly downloadable without login.
                         ArcGIS REST API available with no authentication.
                         Download links directly accessible as CSV/GeoJSON/
                         Shapefile.
    notes:               ArcGIS Hub query API limits 2000 records per call;
                         use bulk CSV download for initial full dataset.
                         Nightly update cadence for parcel data confirmed.
                         Code enforcement update cadence not confirmed —
                         assumed daily/near-real-time based on Accela feed.

---

## Marion County Assessor / IndyGIS (Enrichment)

    name:                Marion County Assessor — Property Report Cards
    access_classification: OPEN_PUBLIC
    evidence:            maps.indy.gov/AssessorPropertyCards/ confirmed publicly
                         accessible without login. Per-parcel search by parcel
                         number, owner name, or address returns property record
                         card. Enrichment only.
    notes:               Prefer Open Indy Data Portal parcels dataset for
                         pipeline use (bulk download, same data, no per-record
                         query complexity).

---

## Marion County GIS Open Data (Enrichment)

    name:                Marion County GIS Open Data Portal
    access_classification: OPEN_PUBLIC
    evidence:            gis-marioncounty.opendata.arcgis.com confirmed publicly
                         accessible. ArcGIS Hub portal with downloadable GIS
                         layers. No authentication required. Enrichment only.
    notes:               Provides spatial parcel data. Most useful for address
                         geocoding and boundary validation during pipeline.

---

## Indiana Gateway / DLGF (Enrichment — State level)

    name:                Indiana Gateway — Tax Bill Look Up
    access_classification: OPEN_PUBLIC
    evidence:            gateway.ifionline.org/TaxBillLookUp/ confirmed publicly
                         accessible. Per-parcel tax bill lookup returns assessed
                         value and tax amount. No login required.
    notes:               Per-record query only; no bulk download. Enrichment
                         source; cannot generate leads. Use Open Indy Data
                         Portal parcel dataset for bulk assessed values.

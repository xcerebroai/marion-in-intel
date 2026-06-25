# Source Verification — Marion County, Indiana
# Phase 0.B — Recon artifact
# Generated: 2026-06-25

Five-layer verification per §4.7 of MASTER_PROMPT.md and §01.7 of County Recon Protocol.

---

## Source 1 — Marion County Recorder (Fidlar/Laredo)

    name:                Marion County Recorder — Online Records (Fidlar/Laredo)
    official_url:        https://inmarion.fidlar.com/INMarion/DirectSearch/
    verified_from_url:   https://www.indy.gov/activity/search-real-estate-records-online
    layers_passed:       Layer 1, Layer 2, Layer 3, Layer 4, Layer 5

    Layer 1 — Official origin:
        Vendor portal at inmarion.fidlar.com. Official government page at
        indy.gov/activity/search-real-estate-records-online directly links to
        Laredo account creation at indy.gov/activity/create-a-laredo-search-account
        and to the Direct Search portal at inmarion.fidlar.com. Official entity
        is the Marion County Recorder's Office, a county government office.
        Verification method: official_vendor_link.

    Layer 2 — Source category:
        Portal exposes: recorded instruments (deeds, mortgages, liens, lis pendens,
        easements, certified survey maps, releases, assignments). Database covers
        March 1964 forward. Search by grantor/grantee name, address, instrument
        number, document type, recording date range. Confirms: land records,
        deed records, recorded instrument search. PASSES.

    Layer 3 — Data access:
        Two-tier model. "Direct Search" tier: free public access without login
        for basic index/metadata lookups. "Laredo" subscription tier: full
        professional search with account and monthly fee; required for batch
        access and bulk document image downloads. Document images accessible
        on a per-copy fee basis (not subscription-only). Standard recorder
        model for Fidlar deployments.
        access_method: SEARCHABLE_PUBLIC_PORTAL (Direct Search tier)
        public_access_status: PUBLIC_SEARCH_DOCUMENTS_LOCKED
        document_access_status: DOCUMENTS_PAID_SUBSCRIPTION_REQUIRED
        (Note: per-copy fee model; closest schema value is DOCUMENTS_PAID_SUBSCRIPTION_REQUIRED)

    Layer 4 — Lead value and source role:
        Clerk/recorder recorded instruments are Tier 1 primary lead sources per
        §4.9. Lis pendens, tax warrants, mechanic liens, judgment liens, affidavits
        of heirship, executor/administrator deeds, and quitclaim deeds are all
        recorded here and are direct distress signals. Lead value: LEAD_GENERATING.
        source_role: PRIMARY_LEAD_SOURCE.

    Layer 5 — Portal proof:
        Direct Search URL confirmed at inmarion.fidlar.com/INMarion/DirectSearch/.
        Search form present for grantor/grantee name and instrument number.
        sample_record_path_confirmed: true
        sample_record_type: search_form
        sample_search_possible: true
        sample_document_view_possible: false (document images require fee/login)

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: HIGH
    official_status: OFFICIAL_VENDOR_PORTAL
    official_entity: Marion County Recorder's Office

---

## Source 2 — Indiana Courts Case Search (MyCase / Tyler Odyssey)

    name:                Indiana Odyssey Case Search (MyCase)
    official_url:        https://public.courts.in.gov/mycase/
    verified_from_url:   https://www.in.gov/courts/local/marion-county
    layers_passed:       Layer 1, Layer 2, Layer 3, Layer 4, Layer 5

    Layer 1 — Official origin:
        Hosted at public.courts.in.gov — official Indiana state .gov domain.
        Indiana Judicial Branch official website (in.gov/courts) links directly
        to MyCase from the Marion County local courts page. Operated by the
        Indiana Office of Judicial Administration. Verification method: court_portal.

    Layer 2 — Source category:
        Portal exposes: all public case dockets for Marion County Superior Court
        and Circuit Court. Case types confirmed: MF (Mortgage Foreclosure), CP
        (Civil Plenary), CC (Civil Collections), EV (Eviction), EM/ES/EU
        (Estate/Probate), SC (Small Claims), PO (Protection Order — confidential
        and excluded). Docket entries, hearing dates, party names, attorney info,
        non-confidential orders. PASSES.

    Layer 3 — Data access:
        Fully public search with no login or fee required. Court documents
        viewable online vary by case type: foreclosure orders publicly viewable;
        "other documents" in some case types restricted to in-person clerk access.
        Per Indiana Judicial Branch access matrix, all core lead-generating event
        records (case filings, foreclosure orders, judgment entries) are publicly
        accessible online.
        access_method: SEARCHABLE_PUBLIC_PORTAL
        public_access_status: FULL_PUBLIC_ACCESS
        document_access_status: DOCUMENTS_PUBLIC (for most case types; some
        case-specific documents require in-person access but docket metadata
        and main orders are online)

    Layer 4 — Lead value and source role:
        Court filings are Tier 1 primary lead sources. Foreclosure (MF) cases
        are the primary distress signal. Eviction (EV) cases signal landlord
        distress. Probate/Estate (EM/ES/EU) cases generate inheritance leads.
        Civil judgments (CP/CC) generate judgment lien leads. All these are
        Tier 1 per §4.9. source_role: PRIMARY_LEAD_SOURCE. Lead value:
        LEAD_GENERATING.

    Layer 5 — Portal proof:
        Case search UI confirmed at public.courts.in.gov/mycase/. Search by
        party name, case number, attorney; filter by county (Marion) and case
        type. sample_record_path_confirmed: true. sample_record_type: search_form.
        sample_search_possible: true. sample_document_view_possible: true (for
        publicly accessible case types).

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: HIGH
    official_status: OFFICIAL_COURT
    official_entity: Indiana Office of Judicial Administration / Marion County
                     Superior Court

---

## Source 3 — GovEase (Marion County Sheriff Foreclosure Sales)

    name:                GovEase — Marion County Sheriff Mortgage Foreclosure Sales
    official_url:        https://liveauctions.govease.com/in/inmarion/
    verified_from_url:   https://www.indy.gov/activity/sheriff-real-estate-sales
    layers_passed:       Layer 1, Layer 2, Layer 3, Layer 4, Layer 5

    Layer 1 — Official origin:
        Vendor portal at liveauctions.govease.com. Official government page at
        indy.gov/activity/sheriff-real-estate-sales is the Marion County Sheriff's
        Office official sales page and directly references GovEase as the
        auction platform. Vendor portal linked from official county government
        website. Verification method: official_vendor_link.

    Layer 2 — Source category:
        Portal exposes: all Marion County judicial foreclosure sheriff sale
        listings. Includes property address, case number (links back to MyCase
        for full court record), plaintiff/defendant names, sale date, minimum
        bid amounts. Properties listed ~30 days before each sale. PASSES as
        sheriff/foreclosure sale records source.

    Layer 3 — Data access:
        Property listing browsing is fully public — no login or registration
        needed to view sale listings. Registration required only for bidding.
        access_method: SEARCHABLE_PUBLIC_PORTAL
        public_access_status: FULL_PUBLIC_ACCESS (for viewing listings)
        document_access_status: DOCUMENTS_PUBLIC (auction details publicly
        viewable; legal notices accessible)

    Layer 4 — Lead value and source role:
        Sheriff sale records are Tier 1 primary lead sources per §4.9. Sales
        represent properties at end of foreclosure pipeline — high-distress
        signals. source_role: PRIMARY_LEAD_SOURCE. Lead value: LEAD_GENERATING.

    Layer 5 — Portal proof:
        Listings confirmed at liveauctions.govease.com/in/inmarion/1282/browse.
        Property cards show address, case #, plaintiff, defendant, sale date.
        sample_record_path_confirmed: true. sample_record_type: search_form /
        list_view. sample_search_possible: true. sample_document_view_possible:
        true (listing cards are public).

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: HIGH
    official_status: OFFICIAL_VENDOR_PORTAL
    official_entity: Marion County Sheriff's Office

---

## Source 4 — Marion County Treasurer / indy.gov (Tax Delinquency)

    name:                Marion County Treasurer's Office — Tax Sale / Delinquency
    official_url:        https://www.indy.gov/activity/tax-sale-reports
    verified_from_url:   https://www.indy.gov/agency/marion-county-treasurers-office
    layers_passed:       Layer 1, Layer 2, Layer 3, Layer 4, Layer 5

    Layer 1 — Official origin:
        Hosted at indy.gov — official Indianapolis/Marion County government .gov
        domain. Operated by the Marion County Treasurer's Office. The Treasurer
        page at indy.gov/agency/marion-county-treasurers-office is the authoritative
        hub. Verification method: official_domain.

    Layer 2 — Source category:
        Hub pages expose: annual tax sale eligible parcel lists, tax sale status
        (sold / unsold / combination lists), sold tax sale property lookup,
        tax lien certificate information. GovEase platform used for online auction
        (linked from indy.gov). Confirms: tax delinquency events, tax sale
        records, tax lien certificates. PASSES.

    Layer 3 — Data access:
        Annual delinquent parcel lists are published as downloadable files
        (PDF, CSV format typically) before each fall sale. Individual sold
        property lookup via web search. No login required.
        access_method: DOWNLOADABLE_FILE (for lists) / SEARCHABLE_PUBLIC_PORTAL
        (for individual lookups)
        public_access_status: FULL_PUBLIC_ACCESS
        document_access_status: DOCUMENTS_PUBLIC (lists downloadable as PDFs/CSVs)

    Layer 4 — Lead value and source role:
        Tax delinquency events and tax sale events are Tier 1 primary lead
        sources per §4.9. Tax sale certificate recording is a primary signal.
        source_role: PRIMARY_LEAD_SOURCE. Lead value: LEAD_GENERATING.

    Layer 5 — Portal proof:
        Tax sale reports page confirmed at indy.gov/activity/tax-sale-reports.
        Tax sale procedures page at indy.gov/activity/prepare-for-a-tax-sale
        provides context and links to GovEase for auction. Sold property lookup
        at indy.gov/activity/find-a-sold-tax-sale-property.
        sample_record_path_confirmed: true. sample_record_type: pdf_index /
        downloadable_file. sample_search_possible: true.
        sample_document_view_possible: true.

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: HIGH
    official_status: OFFICIAL_COUNTY
    official_entity: Marion County Treasurer's Office

---

## Source 5 — Accela Citizen Access (Code Enforcement)

    name:                Indianapolis / Marion County — Accela Code Enforcement
    official_url:        https://aca-prod.accela.com/INDY/Cap/CapHome.aspx?module=Enforcement&TabName=HOME
    verified_from_url:   https://www.indy.gov/activity/permits-and-cases
    layers_passed:       Layer 1, Layer 2, Layer 3, Layer 4, Layer 5

    Layer 1 — Official origin:
        Vendor portal at aca-prod.accela.com (Accela Civic Platform).
        Official government page at indy.gov/activity/permits-and-cases directly
        links to permitsandcases.indy.gov which redirects to this Accela instance.
        Marion County Department of Code Enforcement is the government entity.
        Verification method: official_vendor_link.

    Layer 2 — Source category:
        Portal exposes: code enforcement violation cases, inspection results,
        abatement orders, demolition orders (Building Code), condemnation cases.
        Searchable by address, case number. Confirms: code enforcement events
        with violation/lien/demolition/condemnation signals. PASSES.

    Layer 3 — Data access:
        Case research (searching and viewing case status/details) is publicly
        accessible without login. Login required only for applicants submitting
        new requests. No fee to search or view case records.
        access_method: SEARCHABLE_PUBLIC_PORTAL
        public_access_status: FULL_PUBLIC_ACCESS
        document_access_status: DOCUMENTS_PUBLIC (enforcement case records
        viewable)

    Layer 4 — Lead value and source role:
        Code enforcement events (violations with liens, demolition orders,
        condemnation) are Tier 1 primary lead sources per §4.9 when they expose
        distress-signal-quality data. The Accela portal exposes case type
        (enforcement), case status, and violation details. source_role:
        PRIMARY_LEAD_SOURCE. Lead value: LEAD_GENERATING.

    Layer 5 — Portal proof:
        Enforcement module confirmed at aca-prod.accela.com/INDY/.../Enforcement.
        Search by address returns enforcement cases with status and details.
        sample_record_path_confirmed: true. sample_record_type: search_form.
        sample_search_possible: true. sample_document_view_possible: true.

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: HIGH
    official_status: OFFICIAL_VENDOR_PORTAL
    official_entity: City of Indianapolis / Marion County Department of Code
                     Enforcement (DCE)

---

## Source 6 — Open Indy Data Portal (Bulk Datasets)

    name:                Open Indy Data Portal — Code Enforcement + Parcels
    official_url:        https://data.indy.gov/
    verified_from_url:   https://www.indy.gov/ and https://maps.indy.gov/
    layers_passed:       Layer 1, Layer 2, Layer 3, Layer 4, Layer 5

    Layer 1 — Official origin:
        Hosted at data.indy.gov — official Indianapolis/Marion County government
        .gov subdomain. Linked from indy.gov and maps.indy.gov (IndyGIS hub).
        Operated by the City of Indianapolis Office of Finance and Management /
        DPW. Verification method: official_domain.

    Layer 2 — Source category:
        Code enforcement dataset: full bulk export of DCE violation records.
        Parcel dataset: 348,272+ parcels with owner names, assessed values,
        updated nightly. Both publicly downloadable. Confirms appropriate
        categories. PASSES.

    Layer 3 — Data access:
        Freely downloadable in CSV, GeoJSON, Shapefile, KML. No login required.
        ArcGIS Hub REST API endpoint available for programmatic access.
        access_method: DOWNLOADABLE_FILE / API_ENDPOINT
        public_access_status: FULL_PUBLIC_ACCESS
        document_access_status: DOCUMENTS_PUBLIC

    Layer 4 — Lead value and source role:
        Code enforcement dataset: PRIMARY_LEAD_SOURCE (bulk, same data as
        Accela but in bulk downloadable form — superior for daily pipeline use).
        Parcel dataset: ENRICHMENT_SOURCE (owner name, address, assessed value).

    Layer 5 — Portal proof:
        Data portal confirmed at data.indy.gov. Dataset pages confirmed for
        code enforcement violations and parcels with owner info/assessed values.
        sample_record_path_confirmed: true. sample_record_type: api_endpoint /
        downloadable_file. sample_search_possible: true.
        sample_document_view_possible: true.

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: HIGH
    official_status: OFFICIAL_COUNTY
    official_entity: City of Indianapolis / Open Indy Data Team

---

## Source 7 — Marion County Assessor / IndyGIS (Enrichment)

    name:                Marion County Assessor — Property Report Cards (IndyGIS)
    official_url:        https://maps.indy.gov/AssessorPropertyCards/
    verified_from_url:   https://www.indy.gov/agency/marion-county-assessors-office
    layers_passed:       Layer 1, Layer 2, Layer 3, Layer 4, Layer 5

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: HIGH
    official_status: OFFICIAL_COUNTY
    official_entity: Marion County Assessor's Office
    source_role: ENRICHMENT_SOURCE
    notes: Assessor property record data — enrichment only. Provides assessed
           value, ownership, sales history, and property characteristics.
           Cannot generate leads. Valuable enrichment layer for the pipeline.

---

## Source 8 — Marion County GIS Open Data Portal

    name:                Marion County GIS — ArcGIS Open Data Portal
    official_url:        https://gis-marioncounty.opendata.arcgis.com/
    verified_from_url:   https://maps.indy.gov/
    layers_passed:       Layer 1, Layer 2, Layer 3, Layer 4, Layer 5

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: HIGH
    official_status: OFFICIAL_COUNTY
    official_entity: Marion County GIS (MCCGIS)
    source_role: ENRICHMENT_SOURCE
    notes: GIS parcel and map layer data — enrichment only. Parcel polygons with
           spatial attributes. ArcGIS REST API available at public ArcGIS Hub.
           Cannot generate leads.

---

## Source 9 — Indiana Gateway / DLGF (State Tax Lookup)

    name:                Indiana Gateway — Tax Bill Look Up (DLGF)
    official_url:        https://gateway.ifionline.org/TaxBillLookUp/Default.aspx
    verified_from_url:   https://www.in.gov/dlgf/understanding-your-tax-bill/tax-bill-search/
    layers_passed:       Layer 1, Layer 2, Layer 3 (partial), Layer 4

    verification_status: VERIFIED_OFFICIAL
    verification_confidence: MEDIUM
    official_status: OFFICIAL_STATE
    official_entity: Indiana Department of Local Government Finance (DLGF)
    source_role: ENRICHMENT_SOURCE
    notes: Statewide assessed-value and tax-bill lookup by parcel. Does NOT
           expose delinquency list directly — only current tax bill amounts.
           Classified ENRICHMENT_SOURCE. Not a primary lead source. Useful as
           enrichment for assessed value data on a per-record query basis.

---

## Source 10 — IARA Historical Records

    verification_status: VERIFIED_OFFICIAL
    source_role: REFERENCE_ONLY
    notes: Historical/archival reference only. No current lead generation value.
           Excluded from pipeline build.

---

## Summary by Role

    PRIMARY_LEAD_SOURCE (verified, buildable):
        - Marion County Recorder / Fidlar (clerk recordings)
        - Indiana MyCase / Tyler Odyssey (court civil + foreclosure + eviction + probate)
        - GovEase (sheriff foreclosure sales)
        - Marion County Treasurer / indy.gov (tax delinquency + tax sale)
        - Accela (code enforcement)
        - Open Indy Data Portal — Code Enforcement bulk (primary, bulk form)

    ENRICHMENT_SOURCE (verified):
        - Open Indy Data Portal — Parcels (bulk parcel + owner + AV)
        - Marion County Assessor / IndyGIS (property report cards)
        - Marion County GIS Open Data Portal (ArcGIS Hub)
        - Indiana Gateway / DLGF (per-record assessed value / tax bill)

    REFERENCE_ONLY:
        - IARA Historical Records

    NOT_FOUND:
        - Bankruptcy (PACER — federal, not county; see build_eligibility_handoff.md)
        - Trustee/Non-Judicial foreclosure sources (NOT_APPLICABLE_IN_STATE —
          Indiana is judicial foreclosure only)

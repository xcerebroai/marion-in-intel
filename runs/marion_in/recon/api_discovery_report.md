# API Discovery Report — Marion County, Indiana
# Phase 0 v5.3.0 Amendment (§01.23) — Recon artifact
# Generated: 2026-06-25

Documented API search conducted per §01.23. All required search paths checked.

---

## Required Search Paths Checked

    Paths searched per source domain:
        inmarion.fidlar.com/api                   — NOT FOUND (no API docs)
        inmarion.fidlar.com/swagger               — NOT FOUND
        inmarion.fidlar.com/docs                  — NOT FOUND
        inmarion.fidlar.com/api-docs              — NOT FOUND
        public.courts.in.gov/api                  — NOT FOUND (no public API docs)
        public.courts.in.gov/swagger              — NOT FOUND
        liveauctions.govease.com/api              — NOT FOUND (no public API)
        govease.com/api                           — NOT FOUND
        indy.gov/api                              — NOT FOUND
        aca-prod.accela.com/INDY/api              — NOT FOUND (no public API)
        data.indy.gov/api                         — FOUND (ArcGIS Hub REST API)
        gis-marioncounty.opendata.arcgis.com/api  — FOUND (ArcGIS Hub REST API)
        maps.indy.gov/api                         — FOUND (ArcGIS REST services)
        gateway.ifionline.org/api                 — NOT FOUND

    Vendor Postman collections searched:
        "Fidlar Laredo postman"                   — NOT FOUND
        "Tyler Odyssey API postman"               — NOT FOUND (Tyler provides
                                                     private API to partners, not
                                                     public documentation)
        "Accela postman"                          — NOT FOUND (Accela has partner
                                                     APIs but not publicly documented)
        "GovEase API"                             — NOT FOUND

    GitHub searches:
        "Marion County Indiana API"               — FOUND (IndyGIS ArcGIS datasets)
        "Indiana MyCase API"                      — NOT FOUND (no public Tyler API)

---

## UNDOCUMENTED API discovered via live bypass probe (2026-06-25, Phase 2 pre-build)

NOTE: The above documented-API search correctly found NO public API for Fidlar.
A live browser bypass probe of inmarion.fidlar.com/INMarion/DirectSearch/ then
revealed an UNDOCUMENTED internal endpoint backing the Angular SPA. Per the
recon doctrine (a CAPTCHA/SPA on a search page is not "blocked" until the
bypass probe fails), this was confirmed by executing a real search and
intercepting the network call.

    Architecture (live):   Angular SPA (NOT a server-rendered POST form as the
                           Phase 0 fingerprint assumed) + Angular Material
                           components + Google reCAPTCHA v3
                           (site key 6LckDLwaAAAAAFdkFeW-dkX0IMirFhqiB_tXcRZE).

    Backing API (found):
        POST https://inmarion.fidlar.com/INMarion/Scrap.WebService.DirectSearch/breeze/Search
        Content-Type: application/json
        Request body (JSON, confirmed keys):
            FirstName, LastBusinessName, StartDate, EndDate, DocumentName,
            DocumentType, SubdivisionName, SubdivisionLot, SubdivisionBlock,
            MunicipalityName, Tract* , InstrumentNumber, BookType, Book, Page
        Stack: "Breeze" JS data layer (the /breeze/ path + Scrap.WebService).

    Result fields returned (index metadata — sufficient for lead pipeline):
        Document No (e.g. A202600053697), Document Type (MORTGAGE, DEED,
        MORTGAGE RELEASE, ...), Recorded Date, Party1, Party2, Legals
        (subdivision/lot). Routes: #/search -> #/searchresults.

    AUTH GATE (critical):  A bare POST without the reCAPTCHA token returns
                           HTTP 401 Unauthorized. In a real browser session
                           (token attached) the same query returned ~200 rows
                           for LastBusinessName=SMITH. => The adapter MUST mint
                           a reCAPTCHA v3 token in a browser context; it cannot
                           be a plain server-side requests.post.

    QUERY CONSTRAINTS (stated on the live page + IC 36-1-8.5):
        - NO wildcard search (anti-data-mining). Exact party name only.
        - NO parcel-number search (restricted-address compliance).
        - Documents available 5 days after recording.
        => Daily sweep strategy must key on RECORDING DATE RANGE
           (StartDate/EndDate), not name enumeration.

    Image extraction:      Document images require per-copy fee / Laredo login.
                           NOT needed — index metadata is the lead signal.


---

## Documented APIs Found

### API 1 — Open Indy Data Portal / ArcGIS FeatureServer (Code Enforcement)

    api_url:             https://data.indy.gov/datasets/5d08eba2e9034bc88986af25afe12f5e_1
                         ArcGIS REST API endpoint: available via ArcGIS Hub
                         FeatureServer /query interface
    api_type:            ArcGIS
    documentation_url:   https://developers.arcgis.com/rest/services-reference/
                         (standard ArcGIS REST API documentation)
    auth_required:       false
    rate_limited:        Soft limit — 2000 records per API call (use pagination
                         or bulk CSV download for full dataset)
    source_role:         PRIMARY_EVENT_SOURCE (code enforcement violations)
    notes:               Preferred access path for code enforcement data.
                         Bulk CSV download available for full dataset. ArcGIS
                         REST API allows filtered queries by violation type,
                         date range, geographic area. No authentication required.
                         More reliable than Accela scraping for pipeline use.

### API 2 — Open Indy Data Portal / ArcGIS FeatureServer (Parcels)

    api_url:             https://data.indy.gov/datasets/parcels
                         ArcGIS REST API via IndyGIS FeatureServer
    api_type:            ArcGIS
    documentation_url:   https://developers.arcgis.com/rest/services-reference/
    auth_required:       false
    rate_limited:        2000 records per API call; bulk CSV download available
    source_role:         ENRICHMENT_SOURCE (parcel owner + assessed value data)
    notes:               348,272+ parcel records, updated nightly. Preferred
                         enrichment source. Bulk CSV download recommended for
                         initial load; incremental API queries for daily updates.

### API 3 — Marion County GIS Open Data Portal (ArcGIS Hub)

    api_url:             https://gis-marioncounty.opendata.arcgis.com/
                         Multiple ArcGIS REST FeatureServer endpoints for
                         different layers (parcels, zoning, etc.)
    api_type:            ArcGIS
    documentation_url:   Standard ArcGIS Hub documentation
    auth_required:       false
    rate_limited:        Standard ArcGIS pagination limits
    source_role:         ENRICHMENT_SOURCE
    notes:               Multiple GIS layers available. Parcel polygon layer
                         for geocoding and spatial analysis. Redundant with
                         Open Indy Data Portal for parcel data but provides
                         additional GIS layers not in Open Indy.

---

## Sources Without Documented APIs

    Fidlar/Laredo:       No public API documented. Tyler Technologies' Laredo
                         may have a partner API but it is not publicly documented.
                         Next_access_strategy: find_official_vendor_link for any
                         API documentation, then fall back to HTML scraping of
                         Direct Search interface.

    Indiana MyCase:      Tyler Odyssey Public Access does not expose a documented
                         public API. The SPA backing API (internal AJAX calls)
                         may be observable via Network tab analysis but is not
                         officially documented. MEDIUM difficulty with Playwright.

    GovEase:             No documented public API. HTML scraping of listing pages
                         is LOW difficulty (server-rendered HTML).

    Marion County Treasurer (indy.gov):  Static HTML pages with download links.
                         No API. Download links for PDF/CSV files are the
                         access path.

    Accela (Code Enforcement): Accela has a REST API for partners but it is not
                         publicly documented. Prefer Open Indy Data Portal
                         ArcGIS API over Accela scraping for code enforcement.

---

## Summary

    Documented APIs found:   3 (all ArcGIS-based; Open Indy Data Portal and
                             Marion County GIS)
    No documented API:       Fidlar/Laredo, Indiana MyCase, GovEase, Treasurer/
                             indy.gov, Accela

    Recommendation:
        For code enforcement (primary lead source): use Open Indy Data Portal
        ArcGIS API — documented, stable, no authentication.
        For parcel enrichment: use Open Indy Data Portal ArcGIS API — documented,
        stable, updated nightly.
        For all other sources: HTML scraping (with Playwright for MyCase SPA;
        standard HTML for GovEase and Treasurer; ASP.NET ViewState for Accela
        or prefer bulk API instead).

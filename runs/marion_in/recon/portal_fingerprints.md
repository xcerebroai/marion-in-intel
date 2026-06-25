# Portal Fingerprints — Marion County, Indiana
# Phase 0.C — Recon artifact
# Generated: 2026-06-25

Fingerprint results for all VERIFIED_OFFICIAL sources. Vendor library consulted
per §4.24 / §01.8 for recognized vendor patterns.

---

## Fingerprint 1 — Marion County Recorder (Fidlar/Laredo)

    name:                Marion County Recorder — Online Records
    vendor:              Fidlar Technologies (Laredo product)
    detection_heuristics: URL subdomain inmarion.fidlar.com matches Fidlar
                         domain pattern. Laredo account creation linked from
                         official indy.gov page. "INMarion" path component
                         is the county identifier used by Fidlar deployments.
                         Footer vendor branding on search portal pages.
    architecture:        Server-rendered HTML with some JS for session handling.
                         Direct Search is a simpler HTML interface; full Laredo
                         is a more complex authenticated web app.
    search_interface:    Form-based POST search with grantor/grantee name,
                         instrument number, document type, recording date range.
                         Direct Search is form-based; Laredo uses a more
                         complex search API.
    result_url_pattern:  /INMarion/DirectSearch/Results or similar (exact
                         result URL not confirmed without executing a search)
    detail_url_pattern:  /INMarion/DirectSearch/DocDetail?... (instrument-level
                         detail page)
    scrape_difficulty:   MEDIUM — Direct Search tier: server-rendered HTML, no
                         authentication barrier for index. Document image
                         extraction: HIGH (requires fee/login). For lead pipeline
                         purposes (index metadata only), difficulty is MEDIUM.
    portal_family:       Fidlar
    recommended_adapter: fidlar_direct_search_recordings
    known_blockers:      Session timeout on inactivity; document images require
                         fee/login; batch queries may trigger rate limiting.
    fingerprinted_at:    2026-06-25
    fingerprint_confidence: MEDIUM (Direct Search tier confirmed; full Laredo
                            behavior not confirmed without account)

---

## Fingerprint 2 — Indiana MyCase (Tyler Odyssey)

    name:                Indiana Courts Case Search (MyCase)
    vendor:              Tyler Technologies (Odyssey case management system)
    detection_heuristics: URL public.courts.in.gov — official Indiana state
                         court domain. Indiana is a statewide Tyler Odyssey
                         deployment. "MyCase" brand name consistent with Tyler
                         Odyssey Public Access branding. mycase.in.gov redirects
                         to public.courts.in.gov/mycase/. React SPA with
                         Odyssey-typical URL hash routing (#/).
    architecture:        Single-page application (React). Odyssey Public Access
                         web front-end. Search results load via AJAX to a
                         /mycase/ endpoint.
    search_interface:    REST/JSON API backing a React SPA. Requests observable
                         via Network tab: POST to /mycase/api/... or similar
                         Odyssey API endpoint. Public API, no authentication
                         token required for case search.
    result_url_pattern:  /mycase/#/case/{caseId}/overview (case detail SPA route)
    detail_url_pattern:  /mycase/#/case/{caseId}/caseInformation
    scrape_difficulty:   MEDIUM — SPA requires JS rendering (Playwright) to
                         execute searches. However, the Odyssey API backing
                         the SPA may be directly queryable with proper headers.
                         No authentication barrier. Rate limiting possible on
                         heavy queries.
    portal_family:       Tyler Technologies (Odyssey)
    recommended_adapter: tyler_odyssey_court
    known_blockers:      JS rendering required for search execution; rate
                         limiting on bulk queries; some document types restricted.
    fingerprinted_at:    2026-06-25
    fingerprint_confidence: HIGH (Tyler Odyssey statewide Indiana deployment;
                            well-documented public access interface)

---

## Fingerprint 3 — GovEase (Sheriff Sales)

    name:                GovEase — Marion County Sheriff Foreclosure Sales
    vendor:              GovEase (SRI Tax Sale Services)
    detection_heuristics: URL liveauctions.govease.com confirms GovEase platform.
                         /in/inmarion/ path structure: state abbreviation /
                         county slug. GovEase is the contracted platform for
                         Marion County Sheriff sales per official indy.gov page.
    architecture:        Server-rendered HTML with some JavaScript for filtering.
                         Auction listing pages are directly browsable without
                         account creation.
    search_interface:    Browsable list with filter controls. URL path-based
                         navigation (browse/openrefresh, browse/closed, etc.).
                         No search form — browse-only interface for public users.
    result_url_pattern:  /in/inmarion/1282/browse/{status} (status = openrefresh,
                         closed, etc.)
    detail_url_pattern:  /in/inmarion/1282/detail/{lotId} (property detail card)
    scrape_difficulty:   LOW — Server-rendered HTML, fully public, no
                         authentication for browsing. Pagination manageable.
    portal_family:       GovEase
    recommended_adapter: govease_sheriff_sales
    known_blockers:      Registration required for bidding (not needed for lead
                         extraction). List resets monthly (properties removed
                         up to day-of sale — important for lifecycle tracking).
    fingerprinted_at:    2026-06-25
    fingerprint_confidence: HIGH (GovEase Indiana sheriff sales deployment;
                            Marion County confirmed on official indy.gov)

---

## Fingerprint 4 — Marion County Treasurer / indy.gov (Tax Delinquency)

    name:                Marion County Treasurer — Tax Sale Hub (indy.gov)
    vendor:              Custom (indy.gov CMS; linked to GovEase for auction)
    detection_heuristics: indy.gov is the official consolidated city/county
                         government CMS. Tax sale lists are published as static
                         PDF/CSV download links on indy.gov activity pages.
                         GovEase handles the live auction platform.
    architecture:        Static HTML page (indy.gov CMS) with downloadable
                         file links (PDF, CSV). No dynamic search interface
                         for the delinquency lists — they are bulk-download
                         publications.
    search_interface:    Static download links on indy.gov activity pages.
                         Annual publication (lists released mid-July before
                         fall sale). GovEase platform handles interactive
                         bidder registration and auction listing.
    result_url_pattern:  indy.gov activity pages with embedded file download
                         links. File formats: PDF, possibly CSV.
    detail_url_pattern:  N/A — static file downloads
    scrape_difficulty:   LOW — Static HTML pages on indy.gov with direct
                         download links. File parsing needed for delinquency
                         list (PDF or CSV).
    portal_family:       Custom (indy.gov) + GovEase (auction)
    recommended_adapter: static_html_table (for list pages) / csv_static_list
                         (for downloaded CSV files)
    known_blockers:      Annual publication cycle (not real-time); lists
                         available only before fall tax sale season. GovEase
                         auction listings for tax sale not confirmed to be
                         identical platform to sheriff sales.
    fingerprinted_at:    2026-06-25
    fingerprint_confidence: MEDIUM (indy.gov structure confirmed; exact file
                            format and URL patterns for downloadable lists
                            require Phase 1 investigation)

---

## Fingerprint 5 — Accela Citizen Access (Code Enforcement)

    name:                Indianapolis / Marion County — Accela Code Enforcement
    vendor:              Accela (Civic Platform, cloud SaaS)
    detection_heuristics: URL aca-prod.accela.com/INDY/ confirms Accela Civic
                         Platform. "INDY" is the agency code for Indianapolis/
                         Marion County. permitsandcases.indy.gov is the official
                         branded redirect to the same Accela instance.
                         module=Enforcement path parameter confirms enforcement
                         module.
    architecture:        Server-rendered HTML with JavaScript enhancements.
                         Accela Civic Platform uses ASP.NET Web Forms architecture.
                         URL contains module and tab parameters for navigation.
    search_interface:    Form-based search with address and case number fields.
                         POST-based form submission. Results paginated in HTML
                         table format.
    result_url_pattern:  /INDY/Cap/CapList.aspx?... (search results list)
    detail_url_pattern:  /INDY/Cap/CapDetail.aspx?altId=... (case detail page)
    scrape_difficulty:   MEDIUM — ASP.NET Web Forms with ViewState tokens;
                         session management required; pagination is standard
                         but ViewState must be maintained across requests.
                         Playwright recommended.
    portal_family:       Accela
    recommended_adapter: accela_citizen_access (enforcement module)
    known_blockers:      ASP.NET ViewState tokens must be maintained; session
                         state required; rate limiting on heavy address searches.
                         CAPTCHA not observed on public search.
    fingerprinted_at:    2026-06-25
    fingerprint_confidence: HIGH (Accela INDY instance confirmed; enforcement
                            module URL confirmed)

---

## Fingerprint 6 — Open Indy Data Portal (ArcGIS Hub)

    name:                Open Indy Data Portal — ArcGIS Hub
    vendor:              Esri ArcGIS Hub
    detection_heuristics: data.indy.gov is the official open data portal,
                         powered by ArcGIS Hub. Dataset URLs contain ArcGIS
                         Hub pattern. ArcGIS REST API endpoints available
                         for programmatic access to both code enforcement
                         and parcel datasets.
    architecture:        ArcGIS Hub (cloud SaaS). REST API at ArcGIS FeatureServer
                         endpoints. Data also available as bulk CSV/GeoJSON/Shapefile
                         downloads.
    search_interface:    REST API (ArcGIS FeatureServer /query endpoint) with
                         standard ArcGIS query parameters (where, outFields,
                         f=json). Bulk CSV download also available directly
                         without API calls.
    result_url_pattern:  ArcGIS Hub dataset page + direct download link or
                         FeatureServer /query API endpoint
    detail_url_pattern:  N/A — bulk data, no individual record URL
    scrape_difficulty:   LOW — documented public ArcGIS REST API; no
                         authentication required; well-understood query
                         syntax.
    portal_family:       ArcGIS (Esri)
    recommended_adapter: arcgis_feature_server (for API queries) /
                         csv_static_list (for bulk CSV downloads)
    known_blockers:      ArcGIS Hub query results limited to 2000 records
                         per API call by default (pagination required for
                         full dataset). Bulk CSV download recommended for
                         initial full-dataset pull.
    fingerprinted_at:    2026-06-25
    fingerprint_confidence: HIGH (ArcGIS Hub confirmed; REST API pattern
                            standard and well-documented)

---

## Fingerprint 7 — Marion County Assessor / IndyGIS

    name:                Marion County Assessor — Property Report Cards
    vendor:              Esri ArcGIS (custom IndyGIS application)
    detection_heuristics: Hosted at maps.indy.gov/AssessorPropertyCards/ —
                         official IndyGIS subdomain. Esri-powered web mapping
                         application with property card generation.
    architecture:        Custom Esri web mapping application. May have API
                         backend for per-parcel property card generation.
    scrape_difficulty:   MEDIUM — Per-record query interface; may require
                         Playwright for map/search interaction. Best accessed
                         via ArcGIS REST API or Open Indy Data Portal bulk
                         download (preferred for pipeline use).
    portal_family:       ArcGIS (Esri)
    recommended_adapter: arcgis_feature_server (via Open Indy Data Portal —
                         same underlying data, easier API access)
    known_blockers:      Per-record query only through this interface;
                         prefer bulk download from Open Indy Data Portal for
                         pipeline enrichment.
    fingerprinted_at:    2026-06-25
    fingerprint_confidence: MEDIUM (IndyGIS application confirmed; underlying
                            ArcGIS data confirmed via Open Indy Data Portal)

# Source Discovery — Marion County, Indiana
# Phase 0.A — Recon artifact
# Generated: 2026-06-25

Queries executed per §01.6 protocol. All sources checked for official government
origin. Third-party aggregators and paid data vendors excluded.

---

## Source 1 — Marion County Recorder (Fidlar/Laredo)

    name:               Marion County Recorder's Office — Online Records Search (Laredo/Fidlar)
    official_url:       https://inmarion.fidlar.com/INMarion/DirectSearch/
    page_title:         Marion County Indiana — Recorder Online Records
    gov_or_aggregator:  OFFICIAL_VENDOR_PORTAL
    records_covered:    Deeds, mortgages, liens, lis pendens, easements, survey maps,
                        all recorded instruments. Database from March 1964 forward.
                        Searchable by owner name, address, instrument number.
    discovered_via_query: "Marion County Indiana recorder of deeds land records";
                          confirmed via indy.gov at /activity/search-real-estate-records-online
                          and /activity/create-a-laredo-search-account

---

## Source 2 — Indiana Courts Case Search (MyCase / Tyler Odyssey)

    name:               Indiana Odyssey Case Search — MyCase (Indiana Office of
                        Judicial Administration)
    official_url:       https://public.courts.in.gov/mycase/
    page_title:         Indiana Courts Case Search — MyCase
    gov_or_aggregator:  OFFICIAL_COURT
    records_covered:    All public Marion County Superior Court and Circuit Court cases:
                        Mortgage Foreclosure (MF), Civil Plenary (CP), Civil Collections
                        (CC), Evictions (EV), Probate/Estate (EM, ES, EU), Small Claims
                        (SC), and all other case types. Docket entries, hearing dates,
                        party names, non-confidential orders/documents.
    discovered_via_query: "Indiana MyCase court records portal Marion County foreclosure
                          civil probate official URL"; confirmed via in.gov/courts/local/
                          marion-county

---

## Source 3 — GovEase (Marion County Sheriff Foreclosure Sales)

    name:               Marion County Sheriff Mortgage Foreclosure Sale — GovEase
                        Online Auction Platform
    official_url:       https://liveauctions.govease.com/in/inmarion/
    page_title:         GovEase — Marion County IN Mortgage Foreclosure Sheriff Sales
    gov_or_aggregator:  OFFICIAL_VENDOR_PORTAL
    records_covered:    All Marion County judicial foreclosure sheriff sale listings.
                        Properties listed ~30 days before sale. Includes property address,
                        case number, plaintiff/defendant names, sale date, opening bid.
                        Sales held third Friday of each month (except December) via
                        online auction only.
    discovered_via_query: "Marion County Indiana sheriff sales foreclosure auction
                          official website"; confirmed via indy.gov at
                          /activity/sheriff-real-estate-sales

---

## Source 4 — Marion County Treasurer / indy.gov (Tax Delinquency)

    name:               Marion County Treasurer's Office — Tax Sale Hub (indy.gov)
    official_url:       https://www.indy.gov/activity/prepare-for-a-tax-sale
                        https://www.indy.gov/activity/tax-sale-reports
                        https://www.indy.gov/activity/find-a-sold-tax-sale-property
    page_title:         Marion County Treasurer — Tax Sale Information
    gov_or_aggregator:  OFFICIAL_COUNTY
    records_covered:    Annual tax sale procedures, eligible delinquent parcel lists,
                        tax sale status lists, sold and unsold property lists, tax lien
                        certificate records. Also: GovEase platform for annual online
                        tax sale auction. Lists published mid-July each year before
                        fall sale.
    discovered_via_query: "Marion County Indiana treasurer tax delinquency tax sale
                          official URL indy.gov"

---

## Source 5 — Accela Citizen Access — Indianapolis Code Enforcement

    name:               City of Indianapolis / Marion County — Accela Citizen Access
                        Portal (Code Enforcement Module)
    official_url:       https://aca-prod.accela.com/INDY/Cap/CapHome.aspx?module=Enforcement&TabName=HOME
    alternate_url:      https://permitsandcases.indy.gov/
    page_title:         Indianapolis — Citizen Access — Enforcement
    gov_or_aggregator:  OFFICIAL_VENDOR_PORTAL
    records_covered:    Code enforcement violation cases, inspection results, abatement
                        orders, demolition orders, condemnation cases. Searchable by
                        address or case number. Covers all of Marion County /
                        Indianapolis. Current and historical enforcement actions.
    discovered_via_query: "Marion County Indiana code enforcement violations search
                          portal indy.gov"; confirmed via indy.gov at
                          /activity/permits-and-cases and permitsandcases.indy.gov

---

## Source 6 — Open Indy Data Portal (ArcGIS Hub) — Code Enforcement Bulk + Parcels

    name:               Open Indy Data Portal — Indianapolis Code Enforcement
                        Violations Dataset + Parcels with Owner Information
    official_url:       https://data.indy.gov/datasets/5d08eba2e9034bc88986af25afe12f5e_1
                        (code enforcement violations)
                        https://data.indy.gov/datasets/parcels
                        (parcels with owner info and assessed values)
    page_title:         Open Indy Data Portal
    gov_or_aggregator:  OFFICIAL_COUNTY
    records_covered:    Code enforcement: full bulk dataset of all DCE violation and
                        investigation records. Parcels: 348,272+ parcel polygons with
                        owner names, assessed values, parcel numbers, updated nightly.
                        Multiple download formats (CSV, GeoJSON, Shapefile).
    discovered_via_query: "Marion County Indiana code enforcement open indy data portal
                          violations dataset ArcGIS download parcels"

---

## Source 7 — Marion County Assessor / IndyGIS (Property Report Cards)

    name:               Marion County Assessor — Assessor Property Report Cards
                        (IndyGIS)
    official_url:       https://maps.indy.gov/AssessorPropertyCards/
    page_title:         Marion County Assessor — Property Record Cards
    gov_or_aggregator:  OFFICIAL_COUNTY
    records_covered:    Full assessor property record cards for all parcels in Marion
                        County. Searchable by parcel number, state parcel number,
                        owner name, or property address. Returns ownership, legal
                        description, assessed value, property characteristics,
                        sales history.
    discovered_via_query: "Marion County Indiana assessor property records IndyGIS
                          parcel search maps.indy.gov"

---

## Source 8 — Marion County GIS Open Data Portal (ArcGIS Hub)

    name:               Marion County GIS — ArcGIS Open Data Portal
    official_url:       https://gis-marioncounty.opendata.arcgis.com/
    page_title:         Marion County GIS — Open Data
    gov_or_aggregator:  OFFICIAL_COUNTY
    records_covered:    Full suite of GIS layers: parcels, zoning, streets, flood
                        zones, land use, jurisdictions, utilities. Downloadable in
                        multiple formats. Powered by Esri ArcGIS Hub.
    discovered_via_query: "Marion County Indiana GIS open data ArcGIS parcel layers"

---

## Source 9 — Indiana Gateway / DLGF (Statewide Tax Bill Lookup — State level)

    name:               Indiana Gateway for Government Units — Tax Bill Look Up
                        (Indiana DLGF)
    official_url:       https://gateway.ifionline.org/TaxBillLookUp/Default.aspx
    page_title:         Indiana Gateway — Tax Bill Look Up
    gov_or_aggregator:  OFFICIAL_STATE
    records_covered:    Statewide property tax bill lookup (all 92 Indiana counties
                        including Marion). Taxpayer name, address, parcel number.
                        Returns total tax bill amounts and assessed values.
                        Enrichment/reference source — does not expose delinquency
                        list directly.
    discovered_via_query: "Indiana statewide property tax portal DLGF parcel
                          assessment"

---

## Source 10 — IARA Historical Records (Reference Only)

    name:               Indiana Archives and Records Administration (IARA) —
                        Marion County Recorder Research Page
    official_url:       https://researchindiana.iara.in.gov/
    page_title:         Research Indiana — IARA
    gov_or_aggregator:  OFFICIAL_STATE
    records_covered:    Historical/archival recorder records for Marion County.
                        Pre-digital records. Useful for historical research only;
                        not a real-time lead source.
    discovered_via_query: "Marion County Indiana recorder land records official"
                          (appeared in results as historical context)

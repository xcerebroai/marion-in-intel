# Source of Record Matrix — Marion County, Indiana
# Phase 0 v5.3.0 Amendment — Recon artifact
# Generated: 2026-06-25

Companion markdown to source_of_record_matrix.json. Summary table of all 27
lead types, their source-of-record assignments, and status in Marion County.

---

## Summary

    County:             Marion County, Indiana (marion_in)
    FIPS:               18097
    Framework:          v5.1.2-beta-r3
    Build Status:       READY_TO_BUILD
    Lead Types Swept:   27 of 27

    LIVE_SOURCE_FOUND:                      21
    LIVE_SOURCE_FOUND_LIMITED_COVERAGE:      2
    NOT_APPLICABLE_IN_STATE:                 3
    SOURCE_FOUND_BLOCKED:                    1

---

## Source of Record Table

| # | Lead Type                 | Status                            | Source of Record                  | Access          |
|---|---------------------------|-----------------------------------|-----------------------------------|-----------------|
| 1 | Foreclosure               | LIVE_SOURCE_FOUND                 | Indiana MyCase (MF)               | OPEN_PUBLIC     |
| 2 | Trustee Sale              | NOT_APPLICABLE_IN_STATE           | —                                 | —               |
| 3 | Notice of Trustee Sale    | NOT_APPLICABLE_IN_STATE           | —                                 | —               |
| 4 | Ntc of Sub. Trustee Sale  | NOT_APPLICABLE_IN_STATE           | —                                 | —               |
| 5 | Sheriff Sale              | LIVE_SOURCE_FOUND                 | GovEase (Marion Co Sheriff)       | OPEN_PUBLIC     |
| 6 | Tax Lien Foreclosure      | LIVE_SOURCE_FOUND                 | Marion Co Treasurer               | OPEN_PUBLIC     |
| 7 | Tax Sale                  | LIVE_SOURCE_FOUND                 | Marion Co Treasurer               | OPEN_PUBLIC     |
| 8 | Tax Sale Certificate      | LIVE_SOURCE_FOUND                 | Recorder (Fidlar) + Treasurer     | SEARCH_PUBLIC   |
| 9 | Tax Delinquency           | LIVE_SOURCE_FOUND                 | Marion Co Treasurer               | OPEN_PUBLIC     |
|10 | Lis Pendens               | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|11 | Civil Judgment            | LIVE_SOURCE_FOUND                 | Indiana MyCase (CP/CC)            | OPEN_PUBLIC     |
|12 | Abstract of Judgment      | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|13 | Mechanic Lien             | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|14 | Construction Lien         | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|15 | Federal Tax Lien          | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|16 | State Tax Lien            | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|17 | Probate                   | LIVE_SOURCE_FOUND                 | Indiana MyCase (EM/ES/EU)         | OPEN_PUBLIC     |
|18 | Affidavit of Heirship     | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|19 | Executor Deed             | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|20 | Administrator Deed        | LIVE_SOURCE_FOUND                 | Marion Co Recorder (Fidlar)       | SEARCH_PUBLIC   |
|21 | Code Lien                 | LIVE_SOURCE_FOUND                 | Open Indy Portal / Accela (DCE)   | OPEN_PUBLIC     |
|22 | Demolition                | LIVE_SOURCE_FOUND                 | Open Indy Portal / Accela (DCE)   | OPEN_PUBLIC     |
|23 | Condemnation              | LIVE_SOURCE_FOUND                 | Open Indy Portal / Accela (DCE)   | OPEN_PUBLIC     |
|24 | Eviction                  | LIVE_SOURCE_FOUND                 | Indiana MyCase (EV)               | OPEN_PUBLIC     |
|25 | Divorce                   | LIVE_SOURCE_FOUND_LIMITED_COVERAGE| Indiana MyCase (DN)               | OPEN_PUBLIC     |
|26 | Bankruptcy                | SOURCE_FOUND_BLOCKED              | PACER (federal)                   | PAID_BLOCKED    |
|27 | Surplus                   | LIVE_SOURCE_FOUND_LIMITED_COVERAGE| GovEase (post-sale)               | OPEN_PUBLIC     |

---

## Source Registry

### recorder_fidlar
    Name:      Marion County Recorder
    Vendor:    Fidlar Technologies (Laredo)
    URL:       https://inmarion.fidlar.com/INMarion/DirectSearch/
    Access:    SEARCH_ONLY_PUBLIC (index metadata free; document images paid)
    Bulk:      PER_RECORD_ONLY
    Covers:    Lis Pendens, Mechanic Lien, Construction Lien, Abstract of Judgment,
               Federal Tax Lien, State Tax Lien, Affidavit of Heirship,
               Executor Deed, Administrator Deed, Tax Sale Certificate

### indiana_mycase_court
    Name:      Indiana Courts Case Search (MyCase)
    Vendor:    Tyler Technologies (Odyssey)
    URL:       https://public.courts.in.gov/mycase/
    Access:    OPEN_PUBLIC
    Bulk:      BATCH_QUERY (by case type + date range; no bulk download)
    Covers:    Foreclosure (MF), Eviction (EV), Probate (EM/ES/EU),
               Civil Judgment (CP/CC), Divorce (DN)

### govease_sheriff_sales
    Name:      GovEase — Marion County Sheriff Sales
    Vendor:    GovEase (SRI Tax Sale Services)
    URL:       https://liveauctions.govease.com/in/inmarion/
    Access:    OPEN_PUBLIC
    Bulk:      FULL_COUNTY_BULK (browse all active listings)
    Covers:    Sheriff Sale, Surplus (limited)

### treasurer_tax_sale
    Name:      Marion County Treasurer / indy.gov Tax Sale Hub
    Vendor:    Custom (indy.gov CMS)
    URL:       https://www.indy.gov/activity/tax-sale-reports
    Access:    OPEN_PUBLIC (annual downloadable files)
    Bulk:      FULL_COUNTY_BULK (annual list)
    Covers:    Tax Delinquency, Tax Sale, Tax Lien Foreclosure, Tax Sale Certificate

### open_indy_code_enforcement
    Name:      Open Indy Data Portal — Code Enforcement Bulk (ArcGIS)
    Vendor:    Esri ArcGIS Hub
    URL:       https://data.indy.gov/datasets/5d08eba2e9034bc88986af25afe12f5e_1
    Access:    OPEN_PUBLIC / API
    Bulk:      FULL_COUNTY_BULK (documented ArcGIS REST API; nightly update)
    Covers:    Code Lien, Demolition, Condemnation (preferred over Accela for pipeline)

### accela_code_enforcement
    Name:      Accela Citizen Access — Code Enforcement
    Vendor:    Accela (Civic Platform)
    URL:       https://aca-prod.accela.com/INDY/Cap/CapHome.aspx?module=Enforcement
    Access:    OPEN_PUBLIC
    Bulk:      PER_RECORD_ONLY (address-based; ViewState)
    Covers:    Code Lien, Demolition, Condemnation (secondary; same data as Open Indy)

### pacer_federal_bankruptcy
    Name:      PACER — U.S. Bankruptcy Court, Southern District of Indiana
    Vendor:    U.S. Courts
    URL:       https://www.pacer.gov/
    Access:    PAID_SUBSCRIPTION_REQUIRED — BLOCKED
    Bulk:      UNKNOWN
    Covers:    Bankruptcy (BLOCKED)

---

## Indiana-Specific Notes

    1. Indiana is a judicial foreclosure state. Trustee Sale lead types
       (items 2–4 above) are NOT APPLICABLE.

    2. The "State Tax Lien" source of record for Indiana is the Indiana DOR
       tax warrant, recorded with the county recorder. These are classified
       as "State Tax Warrant" in Fidlar's document type library.

    3. Lis Pendens is the primary pre-foreclosure public notice in Indiana.
       Filed with the county recorder at time of foreclosure suit.

    4. Marion County's MyCase data covers the entire Unigov consolidated
       city-county area. No sub-jurisdiction split required.

    5. Tax sale cycle: Annual fall sale (August–September auction on GovEase).
       Delinquency list published mid-July.

---

## Machine-Readable File

See: source_of_record_matrix.json (same directory)

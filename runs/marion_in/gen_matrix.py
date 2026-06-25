"""
Generates source_of_record_matrix.json for Marion County, Indiana.
Run from repo root: python runs/marion_in/gen_matrix.py
"""
import json
import os

RECORDER = {
    "source_id": "recorder_fidlar",
    "official_url": "https://inmarion.fidlar.com/INMarion/DirectSearch/",
    "authority_type": "County Recorder",
    "vendor_name": "Fidlar Technologies (Laredo)",
    "source_role": "PRIMARY_EVENT_SOURCE",
    "access_status": "SEARCH_ONLY_PUBLIC",
    "bulk_availability": "PER_RECORD_ONLY",
    "verification_layers": {
        "authority": "Vendor portal linked from indy.gov at /activity/search-real-estate-records-online; official_vendor_link",
        "lead_type_relevance": "All recorded instruments including lis pendens, liens, judgments, heirship affidavits, deeds",
        "access": "Free index search; document images require per-copy fee (not needed for lead metadata)",
        "extractability": "Server-rendered HTML Direct Search; MEDIUM difficulty for index; HIGH for doc images",
        "refresh_provenance": "Real-time recording; instruments indexed same business day as recording"
    },
    "sample_record_path_confirmed": True,
    "sample_document_view_possible": False,
    "minimum_lead_fields_available": ["grantor", "grantee", "doc_type", "recording_date", "instrument_number", "book_page"],
    "notes": "Direct Search tier is free for index metadata. Laredo subscription required for bulk/doc images."
}

MYCASE = {
    "source_id": "indiana_mycase_court",
    "official_url": "https://public.courts.in.gov/mycase/",
    "authority_type": "Court",
    "vendor_name": "Tyler Technologies (Odyssey Public Access)",
    "source_role": "PRIMARY_EVENT_SOURCE",
    "access_status": "OPEN_PUBLIC",
    "bulk_availability": "BATCH_QUERY",
    "verification_layers": {
        "authority": "Indiana Office of Judicial Administration; public.courts.in.gov (.gov domain); linked from in.gov/courts",
        "lead_type_relevance": "All Marion County court case types: MF (foreclosure), EV (eviction), EM/ES/EU (probate), CP/CC (civil judgment)",
        "access": "Fully public; no login; no fee; case dockets and most orders viewable online",
        "extractability": "React SPA (Odyssey); Playwright required; docket metadata and party info extractable",
        "refresh_provenance": "Real-time case filing; docket updated same day as court events"
    },
    "sample_record_path_confirmed": True,
    "sample_document_view_possible": True,
    "minimum_lead_fields_available": ["case_number", "case_type", "plaintiff", "defendant", "filing_date", "case_status", "address_in_caption"],
    "notes": "Single statewide portal covers all Indiana counties including Marion. Filter by county and case type."
}

GOVEASE_SHERIFF = {
    "source_id": "govease_sheriff_sales",
    "official_url": "https://liveauctions.govease.com/in/inmarion/",
    "authority_type": "Sheriff",
    "vendor_name": "GovEase (SRI Tax Sale Services)",
    "source_role": "PRIMARY_EVENT_SOURCE",
    "access_status": "OPEN_PUBLIC",
    "bulk_availability": "FULL_COUNTY_BULK",
    "verification_layers": {
        "authority": "Vendor portal linked from indy.gov at /activity/sheriff-real-estate-sales; Marion County Sheriff official platform",
        "lead_type_relevance": "All active Marion County judicial foreclosure sheriff sale listings",
        "access": "Fully public listing browse; registration required to bid only (not for lead extraction)",
        "extractability": "Server-rendered HTML; LOW difficulty; property cards include all lead fields",
        "refresh_provenance": "Updated daily; sales removed at/after sale date; third Friday of month (except December)"
    },
    "sample_record_path_confirmed": True,
    "sample_document_view_possible": True,
    "minimum_lead_fields_available": ["property_address", "case_number", "plaintiff", "defendant", "sale_date", "opening_bid"],
    "notes": "Third Friday of each month except December. Properties listed ~30 days before sale."
}

TREASURER = {
    "source_id": "treasurer_tax_sale",
    "official_url": "https://www.indy.gov/activity/tax-sale-reports",
    "authority_type": "County Treasurer",
    "vendor_name": "Custom (indy.gov CMS); GovEase for auction",
    "source_role": "PRIMARY_EVENT_SOURCE",
    "access_status": "OPEN_PUBLIC",
    "bulk_availability": "FULL_COUNTY_BULK",
    "verification_layers": {
        "authority": "Marion County Treasurer's Office; indy.gov official .gov domain",
        "lead_type_relevance": "Annual tax delinquency list, tax sale eligible parcels, sold/unsold lists, tax certificates",
        "access": "Downloadable annual lists; publicly accessible without login",
        "extractability": "Static file download (PDF/CSV); LOW difficulty",
        "refresh_provenance": "Annual publication cycle (mid-July before fall sale); not real-time delinquency"
    },
    "sample_record_path_confirmed": True,
    "sample_document_view_possible": True,
    "minimum_lead_fields_available": ["parcel_number", "owner_name", "property_address", "delinquent_amount", "tax_years"],
    "notes": "Annual publication cycle. Real-time tax delinquency signals come from recorder (tax warrant recording)."
}

ACCELA = {
    "source_id": "accela_code_enforcement",
    "official_url": "https://aca-prod.accela.com/INDY/Cap/CapHome.aspx?module=Enforcement&TabName=HOME",
    "authority_type": "Code Enforcement",
    "vendor_name": "Accela (Civic Platform)",
    "source_role": "PRIMARY_EVENT_SOURCE",
    "access_status": "OPEN_PUBLIC",
    "bulk_availability": "PER_RECORD_ONLY",
    "verification_layers": {
        "authority": "City of Indianapolis / Marion County DCE; linked from indy.gov at /activity/permits-and-cases",
        "lead_type_relevance": "Code violations, demolition orders, condemnation cases with distress signals",
        "access": "Fully public case search; no login required",
        "extractability": "ASP.NET Web Forms with ViewState; MEDIUM difficulty; Playwright recommended",
        "refresh_provenance": "Real-time case updates; violations recorded as opened"
    },
    "sample_record_path_confirmed": True,
    "sample_document_view_possible": True,
    "minimum_lead_fields_available": ["case_number", "address", "case_type", "status", "open_date"],
    "notes": "Prefer Open Indy Data Portal bulk API for pipeline use (same data, no ViewState complexity)."
}

OPEN_INDY_CE = {
    "source_id": "open_indy_code_enforcement",
    "official_url": "https://data.indy.gov/datasets/5d08eba2e9034bc88986af25afe12f5e_1",
    "authority_type": "Code Enforcement (Bulk)",
    "vendor_name": "Esri ArcGIS Hub",
    "source_role": "PRIMARY_EVENT_SOURCE",
    "access_status": "OPEN_PUBLIC",
    "bulk_availability": "FULL_COUNTY_BULK",
    "verification_layers": {
        "authority": "data.indy.gov (.gov domain); official City of Indianapolis open data portal",
        "lead_type_relevance": "Full bulk DCE violation and enforcement dataset; same records as Accela",
        "access": "Fully public ArcGIS REST API; bulk CSV download; no authentication",
        "extractability": "ArcGIS REST API; LOW difficulty; documented API; no auth required",
        "refresh_provenance": "Updated daily (near-real-time from Accela feed)"
    },
    "sample_record_path_confirmed": True,
    "sample_document_view_possible": True,
    "minimum_lead_fields_available": ["case_number", "address", "violation_type", "status", "open_date"],
    "notes": "Preferred over Accela for pipeline use. Documented ArcGIS REST API available."
}

PACER = {
    "source_id": "pacer_federal_bankruptcy",
    "official_url": "https://www.pacer.gov/",
    "authority_type": "Federal Court",
    "vendor_name": "PACER (U.S. Courts)",
    "source_role": "BLOCKED_SOURCE",
    "access_status": "PAID_SUBSCRIPTION_REQUIRED",
    "bulk_availability": "UNKNOWN",
    "verification_layers": {
        "authority": "U.S. Bankruptcy Court, Southern District of Indiana; federal court system",
        "lead_type_relevance": "Bankruptcy filings for Marion County debtors",
        "access": "PACER account required; $0.10/page or quarterly minimum fee",
        "extractability": "BLOCKED — requires paid account; no public alternative",
        "refresh_provenance": "Real-time case filings if access obtained"
    },
    "sample_record_path_confirmed": False,
    "sample_document_view_possible": False,
    "minimum_lead_fields_available": [],
    "notes": "Federal court, not county. Requires PACER paid account. Low priority for initial build."
}

MYCASE_DN = {
    "source_id": "indiana_mycase_divorce",
    "official_url": "https://public.courts.in.gov/mycase/",
    "authority_type": "Court",
    "vendor_name": "Tyler Technologies (Odyssey)",
    "source_role": "PRIMARY_EVENT_SOURCE",
    "access_status": "OPEN_PUBLIC",
    "bulk_availability": "BATCH_QUERY",
    "verification_layers": {
        "authority": "Same as indiana_mycase_court (IN OJA; .gov domain)",
        "lead_type_relevance": "DN (Dissolution of Marriage) case type; property address rarely in caption",
        "access": "Fully public",
        "extractability": "Same as MyCase; party names and filing date accessible",
        "refresh_provenance": "Real-time case filing"
    },
    "sample_record_path_confirmed": True,
    "sample_document_view_possible": True,
    "minimum_lead_fields_available": ["case_number", "petitioner", "respondent", "filing_date"],
    "notes": "Limited lead value without property address in case record. Low priority."
}

lead_types = [
    {
        "lead_type": "Foreclosure",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Superior Court"],
        "candidate_sources": [MYCASE],
        "selected_source_id": "indiana_mycase_court",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "MF (Mortgage Foreclosure) case type. Indiana judicial foreclosure. Lis pendens recorded with county recorder is the pre-filing signal; MF case filing is the primary event."
    },
    {
        "lead_type": "Trustee Sale",
        "state_applicability": "NOT_APPLICABLE_IN_STATE",
        "expected_authorities": [],
        "candidate_sources": [],
        "selected_source_id": "",
        "status": "NOT_APPLICABLE_IN_STATE",
        "coverage_notes": "Indiana is a judicial foreclosure state. Non-judicial trustee sales do not exist in Indiana."
    },
    {
        "lead_type": "Notice of Trustee Sale",
        "state_applicability": "NOT_APPLICABLE_IN_STATE",
        "expected_authorities": [],
        "candidate_sources": [],
        "selected_source_id": "",
        "status": "NOT_APPLICABLE_IN_STATE",
        "coverage_notes": "Not applicable in Indiana (judicial foreclosure state)."
    },
    {
        "lead_type": "Notice of Substitute Trustee Sale",
        "state_applicability": "NOT_APPLICABLE_IN_STATE",
        "expected_authorities": [],
        "candidate_sources": [],
        "selected_source_id": "",
        "status": "NOT_APPLICABLE_IN_STATE",
        "coverage_notes": "Not applicable in Indiana (judicial foreclosure state)."
    },
    {
        "lead_type": "Sheriff Sale",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Sheriff's Office"],
        "candidate_sources": [GOVEASE_SHERIFF],
        "selected_source_id": "govease_sheriff_sales",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Judicial foreclosure sheriff sales conducted on GovEase platform. Third Friday of each month except December."
    },
    {
        "lead_type": "Tax Lien Foreclosure",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Treasurer's Office"],
        "candidate_sources": [TREASURER],
        "selected_source_id": "treasurer_tax_sale",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Indiana tax lien sale process managed by county treasurer. Annual fall sale via GovEase. Tax certificates issued to buyers; properties subject to redemption period."
    },
    {
        "lead_type": "Tax Sale",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Treasurer's Office"],
        "candidate_sources": [TREASURER],
        "selected_source_id": "treasurer_tax_sale",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Annual fall tax sale. Delinquent list published mid-July. Auction on GovEase."
    },
    {
        "lead_type": "Tax Sale Certificate",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder", "Marion County Treasurer's Office"],
        "candidate_sources": [RECORDER, TREASURER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Tax sale certificates recorded with county recorder after tax sale. Treasurer sold-property list is the secondary source."
    },
    {
        "lead_type": "Tax Delinquency",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Treasurer's Office"],
        "candidate_sources": [TREASURER],
        "selected_source_id": "treasurer_tax_sale",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Annual delinquency list published by Treasurer mid-July. Not real-time. Indiana DOR tax warrants recorded with county recorder are the real-time signal."
    },
    {
        "lead_type": "Lis Pendens",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Lis pendens is the primary pre-foreclosure notice in Indiana. Filed with county recorder by plaintiff (lender) at time of foreclosure suit. Also cross-referencing MyCase MF filings."
    },
    {
        "lead_type": "Civil Judgment",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Superior Court", "Marion County Recorder"],
        "candidate_sources": [MYCASE, RECORDER],
        "selected_source_id": "indiana_mycase_court",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Civil judgments entered in CP/CC cases on MyCase. Abstract of Judgment subsequently recorded with county recorder to create lien."
    },
    {
        "lead_type": "Abstract of Judgment",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Abstracts of judgment (AJ) recorded with county recorder after court judgment. Creates lien against all real property owned in the county."
    },
    {
        "lead_type": "Mechanic Lien",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Mechanic's liens filed with county recorder. Indiana statute requires filing within 90 days of last furnishing labor/materials."
    },
    {
        "lead_type": "Construction Lien",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Construction liens recorded with county recorder. Overlaps with mechanic liens."
    },
    {
        "lead_type": "Federal Tax Lien",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "IRS federal tax liens (FTL) filed with county recorder. High financial distress signal."
    },
    {
        "lead_type": "State Tax Lien",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Indiana Department of Revenue tax warrants recorded with county recorder. Also called 'State Tax Warrant' in Indiana. High financial distress signal."
    },
    {
        "lead_type": "Probate",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Superior Court (Probate Division)"],
        "candidate_sources": [MYCASE],
        "selected_source_id": "indiana_mycase_court",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Estate/Probate cases on MyCase: EM (Estate/Miscellaneous), ES (Estate/Small), EU (Estate/Unsupervised). High lead value — inherited properties often sold by heirs."
    },
    {
        "lead_type": "Affidavit of Heirship",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Affidavits of heirship (AH) recorded with county recorder. Indicates decedent's real property being transferred to heirs outside formal probate. High lead value."
    },
    {
        "lead_type": "Executor Deed",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Executor's deeds (ED) recorded after probate sale. Indicates post-estate property transfer."
    },
    {
        "lead_type": "Administrator Deed",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Recorder"],
        "candidate_sources": [RECORDER],
        "selected_source_id": "recorder_fidlar",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Administrator's deeds (AD) recorded after intestate estate administration. Indicates post-estate property transfer without a will."
    },
    {
        "lead_type": "Code Lien",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["City of Indianapolis / Marion County Department of Code Enforcement"],
        "candidate_sources": [OPEN_INDY_CE, ACCELA],
        "selected_source_id": "open_indy_code_enforcement",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Code enforcement liens recorded when violations are not remediated. Open Indy Data Portal bulk dataset preferred for pipeline use."
    },
    {
        "lead_type": "Demolition",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["City of Indianapolis / Marion County Department of Code Enforcement"],
        "candidate_sources": [OPEN_INDY_CE, ACCELA],
        "selected_source_id": "open_indy_code_enforcement",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Demolition orders issued by DCE for unsafe structures. High distress signal. Open Indy Data Portal preferred."
    },
    {
        "lead_type": "Condemnation",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["City of Indianapolis / Marion County Department of Code Enforcement"],
        "candidate_sources": [OPEN_INDY_CE, ACCELA],
        "selected_source_id": "open_indy_code_enforcement",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "Condemnation orders for properties declared unfit for habitation. Highest distress signal in code enforcement category."
    },
    {
        "lead_type": "Eviction",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Superior Court"],
        "candidate_sources": [MYCASE],
        "selected_source_id": "indiana_mycase_court",
        "status": "LIVE_SOURCE_FOUND",
        "coverage_notes": "EV (Eviction) case type on MyCase. Marion County has one of the highest eviction filing rates in the US. Landlord-distress lead source. Tenant-occupied-property signal."
    },
    {
        "lead_type": "Divorce",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Superior Court"],
        "candidate_sources": [MYCASE_DN],
        "selected_source_id": "indiana_mycase_divorce",
        "status": "LIVE_SOURCE_FOUND_LIMITED_COVERAGE",
        "coverage_notes": "DN (Dissolution of Marriage) case type on MyCase. Property address rarely in case caption. Limited lead value without cross-reference to recorder data. Low priority."
    },
    {
        "lead_type": "Bankruptcy",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["U.S. Bankruptcy Court, Southern District of Indiana"],
        "candidate_sources": [PACER],
        "selected_source_id": "pacer_federal_bankruptcy",
        "status": "SOURCE_FOUND_BLOCKED",
        "coverage_notes": "Federal court. PACER paid account required. Not a county-level source. Requires operator decision to subscribe. Low priority for initial build."
    },
    {
        "lead_type": "Surplus",
        "state_applicability": "APPLICABLE",
        "expected_authorities": ["Marion County Sheriff's Office", "Marion County Treasurer's Office"],
        "candidate_sources": [GOVEASE_SHERIFF],
        "selected_source_id": "govease_sheriff_sales",
        "status": "LIVE_SOURCE_FOUND_LIMITED_COVERAGE",
        "coverage_notes": "Post-sale surplus tracking available on GovEase (closed sales). Limited data on surplus amounts from listing alone. Surplus claim process managed by Marion County Clerk."
    }
]

matrix = {
    "county_slug": "marion_in",
    "county_name": "Marion County",
    "state": "IN",
    "framework_version": "v5.1.2-beta-r3",
    "generated_at": "2026-06-25T19:30:00Z",
    "county_build_status": "READY_TO_BUILD",
    "lead_types": lead_types
}

out_path = os.path.join(os.path.dirname(__file__), "recon", "source_of_record_matrix.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(matrix, f, indent=2, ensure_ascii=False)

print(f"Written: {out_path}")
print(f"Lead types: {len(lead_types)}")
live = sum(1 for lt in lead_types if lt["status"] == "LIVE_SOURCE_FOUND")
limited = sum(1 for lt in lead_types if lt["status"] == "LIVE_SOURCE_FOUND_LIMITED_COVERAGE")
na = sum(1 for lt in lead_types if lt["status"] == "NOT_APPLICABLE_IN_STATE")
blocked = sum(1 for lt in lead_types if lt["status"] == "SOURCE_FOUND_BLOCKED")
print(f"  LIVE_SOURCE_FOUND: {live}")
print(f"  LIVE_SOURCE_FOUND_LIMITED_COVERAGE: {limited}")
print(f"  NOT_APPLICABLE_IN_STATE: {na}")
print(f"  SOURCE_FOUND_BLOCKED: {blocked}")

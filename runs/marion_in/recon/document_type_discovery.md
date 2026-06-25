# Document Type Discovery — Marion County, Indiana
# Phase 0.F — Recon artifact
# Generated: 2026-06-25

Metadata-only discovery per §01.12. No records scraped.
Cross-referenced against knowledge_base/domain/canonical_doc_types.json.

---

## Source: Marion County Recorder (Fidlar/Laredo)

    source_name:         Marion County Recorder — Fidlar Direct Search
    document_type_taxonomy_field_name: Document Type (dropdown/filter on search form)

    Indiana recorder document type taxonomy — primary distress categories:

    Lis Pendens / LP:
        canonical:       LIS_PENDENS
        lead_type:       Foreclosure (pre-filing notice); Lis Pendens
        distress_signal: HIGH — signals foreclosure suit has been filed
        notes:           Indiana uses lis pendens as the primary pre-foreclosure
                         public notice. Plaintiff = lender/servicer.

    Mechanic's Lien / ML:
        canonical:       MECHANICS_LIEN
        lead_type:       Mechanic Lien; Construction Lien
        distress_signal: MEDIUM — unpaid contractor; property may be distressed

    Abstract of Judgment / AJ:
        canonical:       ABSTRACT_OF_JUDGMENT
        lead_type:       Abstract of Judgment; Civil Judgment
        distress_signal: MEDIUM — court judgment recorded as lien against property

    Federal Tax Lien / FTL:
        canonical:       FEDERAL_TAX_LIEN
        lead_type:       Federal Tax Lien
        distress_signal: HIGH — IRS lien on property; financial distress

    Indiana State Tax Warrant:
        canonical:       STATE_TAX_LIEN
        lead_type:       State Tax Lien
        distress_signal: HIGH — Indiana DOR tax warrant recorded with county recorder;
                         financial distress; may accompany property tax delinquency

    Affidavit of Heirship / AH:
        canonical:       AFFIDAVIT_OF_HEIRSHIP
        lead_type:       Affidavit of Heirship; Probate
        distress_signal: MEDIUM — property in estate; may be inherited, absentee,
                         or emotionally motivated to sell

    Executor's Deed / ED:
        canonical:       EXECUTOR_DEED
        lead_type:       Executor Deed; Probate estate
        distress_signal: HIGH — estate sale in progress; heirs motivated to liquidate

    Administrator's Deed / AD:
        canonical:       ADMINISTRATOR_DEED
        lead_type:       Administrator Deed; Probate estate (intestate)
        distress_signal: HIGH — estate sale in progress; intestate succession

    Sheriff's Deed / SD:
        canonical:       SHERIFF_DEED
        lead_type:       Post-foreclosure transfer; Sheriff Sale (completed)
        distress_signal: MEDIUM (recording happens AFTER sale; lead is the lis
                         pendens / MF case, not the sheriff's deed)
        notes:           Useful for identifying recently foreclosed properties;
                         new owner (lender/REO) may want to sell

    Treasurer's Deed / TD:
        canonical:       TREASURER_DEED
        lead_type:       Post-tax-sale transfer; Tax Sale (completed)
        distress_signal: MEDIUM (post-event; primary signal was delinquency)

    Quitclaim Deed / QCD:
        canonical:       QUITCLAIM_DEED
        lead_type:       Distress transfer indicator (in combination)
        distress_signal: LOW-MEDIUM — QCDs alone are ambiguous; combined with
                         other distress signals (LP, delinquency) indicate
                         involuntary or distressed transfer

    Warranty Deed / WD:
        canonical:       WARRANTY_DEED
        lead_type:       Standard conveyance (mostly noise)
        distress_signal: LOW (standard arm's-length sales)

    Mortgage / MTG:
        canonical:       MORTGAGE
        lead_type:       New financing (noise unless combined with distress signals)
        distress_signal: LOW

    Release of Mortgage / RM:
        canonical:       RELEASE_OF_MORTGAGE
        lead_type:       Suppression event (mortgage paid off)
        distress_signal: SUPPRESSION (lifecycle — existing lis pendens may be cured)

    total_types_observed:               ~20+ (estimated from standard Indiana
                                        recorder taxonomy; exact count requires
                                        Phase 1 dropdown inspection)
    types_mapped_to_canonical_primary:  LP, ML, AJ, FTL, State Tax Warrant,
                                        AH, ED, AD, SD, TD, QCD (conditionally)
    types_mapped_to_canonical_enrichment: MTG, WD, RM (lifecycle/noise)
    types_unknown:                      Exact Fidlar dropdown labels not confirmed
                                        without Phase 1 access
    recommended_primary_doc_types_for_build: LP (lis pendens), ML (mechanic lien),
                                        AJ (abstract of judgment), FTL (federal
                                        tax lien), State Tax Warrant, AH (affidavit
                                        of heirship), ED (executor deed), AD
                                        (administrator deed), TD (treasurer deed)

    sample_documents_inspected:         No — document images require fee/login.
                                        Index metadata confirmed accessible.
                                        Metadata fields confirmed: grantor name,
                                        grantee name, document type label, recording
                                        date, instrument number, book/page.
                                        Open question: exact Fidlar document type
                                        dropdown labels vs. canonical names.

---

## Source: Indiana MyCase (Court Filings)

    source_name:         Indiana Courts Case Search (MyCase)
    document_type_taxonomy_field_name: Case Type (dropdown on search form)

    Relevant Indiana MyCase case types for lead generation:

    MF — Mortgage Foreclosure:
        canonical:       FORECLOSURE
        lead_type:       Foreclosure
        distress_signal: HIGH — primary foreclosure event; plaintiff = lender
                         Defendant = borrower/property owner

    EV — Eviction:
        canonical:       EVICTION
        lead_type:       Eviction
        distress_signal: MEDIUM — landlord-tenant distress; property may be
                         abandoned or tenant-occupied
        notes:           Marion County / Indianapolis has high eviction volume;
                         landlords in distress may be motivated sellers

    CP — Civil Plenary:
        canonical:       CIVIL_JUDGMENT (after judgment entered)
        lead_type:       Civil Judgment
        distress_signal: MEDIUM — judgment may become recorded judgment lien
                         via abstract of judgment filed with recorder

    CC — Civil Collections:
        canonical:       CIVIL_JUDGMENT
        lead_type:       Civil Judgment (smaller amounts)
        distress_signal: LOW-MEDIUM

    EM — Estate/Miscellaneous (Probate):
        canonical:       PROBATE
        lead_type:       Probate; Estate
        distress_signal: HIGH — decedent's estate; heirs may be motivated to sell

    ES — Estate/Small (Probate):
        canonical:       PROBATE
        lead_type:       Probate — small estate
        distress_signal: MEDIUM — smaller estate values; still generates leads

    EU — Estate/Unsupervised (Probate):
        canonical:       PROBATE
        lead_type:       Probate — unsupervised administration
        distress_signal: HIGH — unsupervised administration often faster to
                         resolve; estate may sell quickly

    DN — Dissolution of Marriage (Divorce):
        canonical:       DIVORCE
        lead_type:       Divorce
        distress_signal: LOW-MEDIUM — divorce often leads to forced property
                         sale; limited value without property intersection

    total_types_observed:               ~20+ standard Indiana case types
    types_mapped_to_canonical_primary:  MF, EV, EM, ES, EU (strong primary
                                        signals); CP, CC (moderate); DN (limited)
    types_mapped_to_canonical_enrichment: N/A (court cases are lead events)
    recommended_primary_case_types_for_build: MF (foreclosure — highest priority),
                                        EM/ES/EU (probate — high value), EV
                                        (eviction — volume source)

    sample_documents_inspected:         Yes — MyCase is OPEN_PUBLIC. Sample MF
                                        case dockets confirmed: include filing date,
                                        party names, plaintiff (lender), defendant
                                        (borrower), property address in case caption,
                                        case status, hearing dates. Case documents
                                        (foreclosure complaints, orders) publicly
                                        viewable in most MF cases per Indiana access
                                        matrix.

---

## Source: GovEase (Sheriff Sales)

    source_name:         GovEase — Sheriff Sales
    document_type_taxonomy_field_name: N/A (auction listing, not document types)

    Fields available on GovEase property listing cards:
        - Property address
        - Case number (links to MyCase)
        - Plaintiff name (lender/servicer)
        - Defendant name (borrower/property owner)
        - Sale date (third Friday of month)
        - Opening bid amount (minimum bid)
        - Property description / legal description (sometimes)
        - Auction status (active, postponed, sold, cancelled)

    total_types_observed:               1 — Mortgage Foreclosure Sheriff Sale
    recommended_primary_doc_types_for_build: All active listings (SHERIFF_SALE)

    sample_documents_inspected:         Yes — listing cards publicly viewable;
                                        sample data confirmed above.

---

## Source: Marion County Treasurer / indy.gov (Tax Delinquency)

    source_name:         Marion County Treasurer — Tax Sale Hub
    document_type_taxonomy_field_name: N/A (downloadable list file)

    Fields available on annual tax delinquency list:
        - County parcel number (key for entity resolution)
        - Owner name (on record)
        - Property address (situs)
        - Amount of delinquent taxes
        - Year(s) of delinquency
        - Tax sale eligibility status
        - Redemption period status (post-sale)

    total_types_observed:               1 category (tax delinquency event)
    recommended_primary_doc_types_for_build: TAX_DELINQUENCY, TAX_SALE

    sample_documents_inspected:         Not fully confirmed — format of downloadable
                                        list (PDF vs. CSV) and exact field names
                                        require Phase 1 download and inspection.
                                        Annual publication; mid-July availability.

---

## Source: Accela / Open Indy Data Portal (Code Enforcement)

    source_name:         Accela Code Enforcement / Open Indy Data Portal
    document_type_taxonomy_field_name: Case Type (in Accela) / violation_type (in
                                       bulk dataset)

    Relevant code enforcement case types:

    Violation / Complaint Investigation:
        canonical:       CODE_VIOLATION
        lead_type:       Code Violation
        distress_signal: MEDIUM — property in disrepair; owner may be distressed

    Demolition Order:
        canonical:       DEMOLITION
        lead_type:       Demolition
        distress_signal: HIGH — city has ordered demolition; owner faces total
                         loss of improvement value

    Condemnation:
        canonical:       CONDEMNATION
        lead_type:       Condemnation
        distress_signal: HIGH — property condemned as unfit; owner highly motivated

    Unsafe Structure:
        canonical:       CODE_VIOLATION (subtype: unsafe_structure)
        lead_type:       Code Violation (severe)
        distress_signal: HIGH — structure declared unsafe; owner facing city
                         enforcement costs

    total_types_observed:               Multiple (exact taxonomy in Open Indy
                                        dataset to be confirmed in Phase 1)
    recommended_primary_doc_types_for_build: DEMOLITION (highest priority),
                                        CONDEMNATION, CODE_VIOLATION (filter
                                        for open/active cases only)

    sample_documents_inspected:         Yes — Accela case records publicly viewable;
                                        fields confirmed: case number, address, case
                                        type, status, open date, last inspection date.
                                        Bulk dataset fields TBD in Phase 1 CSV inspection.

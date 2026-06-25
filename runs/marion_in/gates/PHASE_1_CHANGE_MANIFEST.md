# Phase 1 Change Manifest — Marion County, IN
**Gate**: REVIEW_GATE_2  
**Status**: APPROVED  
**Date**: 2026-06-25

---

## Files Modified

### Pipeline

| File | Change |
|------|--------|
| `scaffold/pipeline/build_leads.py` | Added `registry_to_lead_type` import from `doc_type_bridge`; added filter in `_signal_to_raw_event` to skip no-§16-lead-type doc types (quitclaim_deed, hoa_lien, vacated_judgment → dropped before pipeline); output path for synthetic mode set to `data/synthetic/dashboard.json` |

### Synthetic Data

| File | Change |
|------|--------|
| `scaffold/data/synthetic_signals.jsonl` | Completely rewritten: 24 signals for 12 parcels covering all 9 pattern chips and 5 deal-path classifications. All 21 active signals now carry proper party fields (grantor/grantee/plaintiff/defendant/taxpayer) and `document_body_text` where required by debtor_party_engine (DOCUMENT_BODY rules). 3 signals annotated with `_note` and correctly filtered. |
| `scaffold/data/synthetic_parcels.jsonl` | Seeded with 12 parcel records (SYN-001–SYN-012) with realistic Marion County address strings and attribute fields. |
| `scaffold/data/synthetic_attribute_overrides.json` | Created: per-parcel attribute overrides for all 12 synthetic parcels to exercise all 4 attribute chips (free_and_clear, high_equity, long_term_owned, vacant). |
| `scaffold/data/synthetic_expectations.json` | Completely rewritten to match actual v5.4.0 staged pipeline output: lead_total=12, 21 active signals, 3 filtered, all pattern/attribute/tier/depth/deal-path distributions, per-parcel assertions including score_min and tier. |

### Dashboard

| File | Change |
|------|--------|
| `dashboard/dashboard.js` | Updated `DATA_PATHS_SYNTH` to check `./data/synthetic/dashboard.json` first (pipeline output path). Replaced Bexar TX `PRECANNED_VIEWS` with 6 Marion County views: Foreclosure Pipeline, Recorder Instruments, High-Volume Evictions, Probate / Estate, Code Enforcement, Tax Distress. |

### Gate / Run Artifacts

| File | Change |
|------|--------|
| `runs/marion_in/gates/REVIEW_GATE_2.signoff.json` | Created: gate signoff with pipeline_summary, approved_artifacts, phase_2_scope_directive, backlog_items. |
| `runs/marion_in/gates/PHASE_1_CHANGE_MANIFEST.md` | This file. |

---

## Files NOT Modified (verified unchanged)

- `scaffold/pipeline/debtor_party_engine.py` — §17 rule table; no changes needed, confirmed all 12 parcel doc types have rules
- `scaffold/pipeline/doc_type_bridge.py` — registry/lead-type bridge; no changes needed
- `scaffold/pipeline/normalize.py` — `_RAW_SUBTYPE_MAP` supports all synthetic subtypes
- `scaffold/pipeline/aggregation_key_engine.py` — §18 key engine; unchanged
- `scaffold/pipeline/aggregator.py` — §19 aggregator; unchanged
- `scaffold/pipeline/leads_base_writer.py` — §18 base writer; unchanged
- `scaffold/pipeline/semantic_verify.py` — §20 verifier; unchanged
- `scaffold/pipeline/scoring_seam.py` — Option-Y scoring seam; unchanged
- `scaffold/pipeline/run_pipeline_staged.py` — orchestrator; unchanged
- `config/counties/marion_in.json` — county config; unchanged (set in Phase 0)
- `dashboard/index.html` — HTML shell; unchanged
- `dashboard/dashboard.css` — styles; unchanged

---

## Pipeline Run Results

```
Synthetic mode: ON
Input:  scaffold/data/synthetic_signals.jsonl  (24 lines)
Output: data/synthetic/dashboard.json

Signals in dataset:     24
Signals filtered:        3  (quitclaim_deed, hoa_lien, vacated_judgment)
Signals processed:      21
Leads produced:         12  (all RESOLVED, all APPROVED_FOR_DASHBOARD)
Semantic verdict:       NEEDS_OPERATOR_REVIEW (legitimate — null instruments)

Tier distribution:      Hot=3, Strong=4, Workable=1, Low=4
Pattern chips:          bankruptcy, code, divorce, estate, eviction, foreclosure,
                        lien, surplus_owed, tax
Attribute chips:        free_and_clear, high_equity, long_term_owned, vacant
Deal-path chips:        messy_title, partial_interest, sub_to, surplus_recovery, wholesale
Stack depth:            1×5, 2×5, 3×2
```

---

## Test Results

```
Golden path (test_golden_path.py):  66/66 PASS
All tests (run_all.py):             ALL PASS
```

---

## What Phase 2 Will Add

First adapter: Fidlar/Laredo clerk recordings translator (`adapters/clerk_recordings/fidlar_laredo.py`).  
Covers: judgment_lien, mechanics_lien, construction_lien, lis_pendens, abstract_of_judgment — the highest-density §16 types in the Marion County recorder's system.  
GovEase sheriff sales adapter second.  
Parcel master enrichment (data.indy.gov ArcGIS) alongside first adapter.

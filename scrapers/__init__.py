"""
County-specific scraper adapters.

Each module drives one source declared in the active county config.
The split keeps framework code county-agnostic while county wiring
stays here.

Marion County, IN (Phase 2):
  recorder_recordings — Fidlar Breeze Angular SPA adapter for the
                        Marion County Recorder recorded instruments.
"""

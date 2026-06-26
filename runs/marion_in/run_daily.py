"""
Marion County, IN — Daily run commands.

Run from repo root.  Each source must be run before the pipeline.

CAPTCHA cap notes
-----------------
recorder (Fidlar Breeze reCAPTCHA v3):  ~200 requests/session safe zone.
                                         --days-back 1 (default) = 1 request.
court_filings (MyCase image CAPTCHA):    ~47 requests per session hard cap.
                                         Use --days-back 4 (4 surname sweeps
                                         × ~10 letters each ≈ 40 requests).
                                         Do NOT exceed --days-back 4 without
                                         verifying the cap hasn't tightened.

Scraper commands
----------------

    # Recorder (Fidlar Breeze) — requires Playwright + Python 3.12
    C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe \\
        scrapers/recorder_recordings.py --days-back 1

    # Court filings (MyCase) — requires Playwright + Python 3.12
    # --days-back 4 keeps requests under the ~47-request CAPTCHA cap
    C:/Users/Owner/AppData/Local/Programs/Python/Python312/python.exe \\
        scrapers/court_filings.py --days-back 4 --case-types MF

Pipeline command
----------------

    python scaffold/pipeline/build_leads.py \\
        --county-config config/counties/marion_in.json \\
        --approve-needs-review

Output files
------------
    data/matched_leads.json
    data/scored_leads.json
    data/evidence_ledger.json
    data/dashboard.json
    data/runs/latest.manifest.json
"""

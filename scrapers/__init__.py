"""
County-specific scraper adapters for the Bexar (TX) build.

Each module here drives one source declared in
`config/counties/bexar_tx.json`. The modules are intentionally thin
wrappers that delegate the heavy lifting to framework-shared adapters
under `scaffold/scrapers/`. The split keeps the framework code
county-agnostic while county wiring stays here.
"""

# Register county-side translator adapters at package import time. build_leads.py
# does `import scrapers` before dispatching translators, so importing the module
# here runs its @register decorators and makes the names resolvable via lookup().
from scrapers import county_lead_translators  # noqa: E402, F401

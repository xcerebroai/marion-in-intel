"""
Lead registry — tracks which leads have been seen across runs.

Persists a JSON file (data/seen_leads.json, gitignored) containing a dict of
{lead_id: first_seen_date}. On each run:
  - load the registry
  - for each processed lead, check if lead_id is in registry
  - if not: mark is_new=True, record first_seen_date=today, add to registry
  - if yes: mark is_new=False, first_seen_date=registry[lead_id]
  - save the updated registry

The registry file is gitignored — it persists locally across runs, reset if deleted.

This module is universal framework code: no county / state / vendor literal
appears here. The county-agnostic regression scanner enforces that.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

REGISTRY_FILENAME = "seen_leads.json"


def load_registry(workdir: Path) -> dict:
    """Load the seen-leads registry from workdir/seen_leads.json.
    Returns empty dict if the file does not exist."""
    path = Path(workdir) / REGISTRY_FILENAME
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_registry(workdir: Path, registry: dict) -> None:
    """Persist the registry to workdir/seen_leads.json."""
    path = Path(workdir) / REGISTRY_FILENAME
    path.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def stamp_leads(leads: list, workdir: Path, as_of: date | None = None) -> list:
    """Stamp each lead with is_new (bool) and first_seen_date (ISO date string).

    Updates and saves the registry. Mutates leads in place and returns the list.
    A lead whose lead_id is not yet in the registry gets is_new=True and is
    added. An already-known lead gets is_new=False and its original first_seen_date.
    """
    today = (as_of or date.today()).isoformat()
    registry = load_registry(workdir)
    for lead in leads:
        lead_id = lead.get("lead_id") or lead.get("scored_lead_id", "")
        if lead_id and lead_id not in registry:
            registry[lead_id] = today
            lead["is_new"] = True
            lead["first_seen_date"] = today
        else:
            lead["is_new"] = False
            lead["first_seen_date"] = registry.get(lead_id, today)
    save_registry(workdir, registry)
    return leads

"""Regenerate the offline triage fixture cache.

Single source of truth for cache keys: this builder calls
``asantico_cli.infra.llm.canonical_redaction`` (normalize, redact, hash), the
exact function ``triage_request`` uses at runtime. That guarantees the key
written here matches the key looked up by the real CLI path.

Run with: python scripts/build_triage_cache.py
"""

import json
from pathlib import Path

from asantico_cli.infra.llm import canonical_redaction

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKORDER_DIR = REPO_ROOT / "tests" / "fixtures" / "workorders"
CACHE_DIR = REPO_ROOT / "tests" / "fixtures" / "triage_cache"

# Recorded model responses keyed by work order id. PII fields reference redacted
# tokens; property_name is not PII. Confidence is deliberately low on ambiguous
# cases so they escalate to human review. No em dashes anywhere.
RESPONSES: dict[str, dict] = {
    "wo_01_emergency_plumbing": {
        "urgency": "emergency", "trade": "plumbing",
        "property_name": "The Meridian", "unit": "UNIT_1",
        "tenant_contact": "NAME_1, PHONE_1",
        "issue_summary": "Burst pipe under kitchen sink, water spreading to hallway",
        "confidence": {"urgency": 0.98, "trade": 0.95, "property_name": 0.97, "unit": 0.93, "tenant_contact": 0.9},
    },
    "wo_02_emergency_electrical": {
        "urgency": "emergency", "trade": "electrical",
        "property_name": "Portal", "unit": "UNIT_1", "tenant_contact": None,
        "issue_summary": "Outlet sparking with burning smell and smoke, breaker off",
        "confidence": {"urgency": 0.97, "trade": 0.94, "property_name": 0.95, "unit": 0.9},
    },
    "wo_03_routine_appliance": {
        "urgency": "routine", "trade": "appliance",
        "property_name": "Garden", "unit": "UNIT_1", "tenant_contact": None,
        "issue_summary": "Dishwasher not draining fully, standing water after cycle",
        "confidence": {"urgency": 0.92, "trade": 0.9, "property_name": 0.96, "unit": 0.94},
    },
    "wo_04_routine_general": {
        "urgency": "routine", "trade": "general",
        "property_name": "Canterbury Shores", "unit": None, "tenant_contact": None,
        "issue_summary": "Touch up paint and patch drywall nail pops in hallway",
        "confidence": {"urgency": 0.93, "trade": 0.82, "property_name": 0.95},
    },
    "wo_05_urgent_hvac": {
        "urgency": "urgent", "trade": "hvac",
        "property_name": "Koda Condominiums", "unit": "UNIT_1", "tenant_contact": None,
        "issue_summary": "Furnace stopped producing heat, unit very cold",
        "confidence": {"urgency": 0.88, "trade": 0.93, "property_name": 0.95, "unit": 0.9},
    },
    "wo_06_routine_plumbing": {
        "urgency": "routine", "trade": "plumbing",
        "property_name": "Aprea View", "unit": "UNIT_1", "tenant_contact": None,
        "issue_summary": "Bathroom sink draining slowly, likely trap clog",
        "confidence": {"urgency": 0.9, "trade": 0.88, "property_name": 0.94, "unit": 0.9},
    },
    "wo_07_ambiguous_noise": {
        "urgency": "routine", "trade": "general",
        "property_name": "Linden Avenue Condominiums", "unit": None, "tenant_contact": None,
        "issue_summary": "Intermittent humming noise of unknown source",
        "confidence": {"urgency": 0.6, "trade": 0.45, "property_name": 0.9},
    },
    "wo_08_ambiguous_water_electrical": {
        "urgency": "urgent", "trade": "plumbing",
        "property_name": "Gilman's Fairway", "unit": "UNIT_1", "tenant_contact": None,
        "issue_summary": "Water pooling near water heater with flickering hallway lights",
        "confidence": {"urgency": 0.66, "trade": 0.5, "property_name": 0.92, "unit": 0.88},
    },
    "wo_09_heavy_pii_appliance": {
        "urgency": "routine", "trade": "appliance",
        "property_name": "Clark Roadhouse", "unit": "UNIT_1",
        "tenant_contact": "NAME_1, PHONE_1, EMAIL_1",
        "issue_summary": "Clothes dryer will not heat, clothes damp after cycle",
        "confidence": {"urgency": 0.91, "trade": 0.92, "property_name": 0.95, "unit": 0.9, "tenant_contact": 0.85},
    },
    "wo_10_urgent_appliance": {
        "urgency": "urgent", "trade": "appliance",
        "property_name": "Garden", "unit": "UNIT_1", "tenant_contact": None,
        "issue_summary": "Refrigerator not cooling, freezer thawing and food spoiling",
        "confidence": {"urgency": 0.84, "trade": 0.9, "property_name": 0.95, "unit": 0.9},
    },
    "wo_11_routine_electrical": {
        "urgency": "routine", "trade": "electrical",
        "property_name": "The Meridian", "unit": "UNIT_1", "tenant_contact": None,
        "issue_summary": "Kitchen can light out, does not work with new bulb",
        "confidence": {"urgency": 0.92, "trade": 0.89, "property_name": 0.95, "unit": 0.9},
    },
}


def build() -> list[str]:
    """Write one cache file per work order fixture and return the filenames."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Start clean so stale keys cannot linger.
    for stale in CACHE_DIR.glob("*.json"):
        stale.unlink()

    filenames: list[str] = []
    for path in sorted(WORKORDER_DIR.glob("*.json")):
        workorder = json.loads(path.read_text(encoding="utf-8"))
        wid = workorder["id"]
        if wid not in RESPONSES:
            raise SystemExit(f"Missing recorded response for {wid}")
        _, _, digest = canonical_redaction(workorder["raw_text"])
        out = CACHE_DIR / f"{digest}.json"
        out.write_text(json.dumps(RESPONSES[wid], indent=2) + "\n", encoding="utf-8")
        filenames.append(out.name)
    return filenames


if __name__ == "__main__":
    written = build()
    print(f"Wrote {len(written)} cache files to {CACHE_DIR}:")
    for name in written:
        print(f"  {name}")

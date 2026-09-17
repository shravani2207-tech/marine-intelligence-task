import json
from datetime import datetime, timezone

from mmr_canonical_envelope import envelope, point_geom
from mmr_feasibility import load_json, get_mmr_jetties

# -----------------------------------------------------------------------
# NOTE: No real cost data exists anywhere in this data layer yet
# (waterways.json / ports.json / logistics.json / environmental.json all
# checked -- no cost, budget, price, or expenditure fields present).
# Every function below is a STRUCTURAL PLACEHOLDER: it defines the shape
# of the financial assessment so it can be populated once real cost
# benchmarks are sourced. No number is fabricated. This mirrors how
# decongestion_assessment() is handled in mmr_feasibility.py.
# -----------------------------------------------------------------------

def land_development_cost_estimate():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real per-hectare land acquisition and development rates for the MMR corridor (Thane/Bhiwandi/Kalyan land records or MMRDA benchmarks).",
        "methodology": "TBD"
    }

def water_channel_development_cost_estimate():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real dredging and channel-construction cost benchmarks for NW-53 (IWAI cost norms or comparable inland waterway projects).",
        "methodology": "TBD"
    }

def port_infra_setup_cost_estimate():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real port/jetty infrastructure capex benchmarks (berth construction, terminal equipment, land-side connectivity).",
        "methodology": "TBD"
    }

def logistics_cost_estimate():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real logistics and transport cost data (per-tonne-km road vs. waterway cost comparison for the MMR corridor).",
        "methodology": "TBD"
    }

def roi_assessment():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "ROI cannot be derived until land, water-channel, port, and logistics cost estimates above are populated with real figures, along with projected traffic/cargo volume from the Scenario Simulation module.",
        "methodology": "TBD",
        "depends_on": [
            "land_development_cost_estimate",
            "water_channel_development_cost_estimate",
            "port_infra_setup_cost_estimate",
            "logistics_cost_estimate",
            "scenario_simulation traffic/cargo volume projections"
        ]
    }

def build_financial_report(jetties):
    return {
        "study": "NW-53 Kalyan-Thane-Mumbai Financial Assessment (ROI / Budget Mapping)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jetty_count_covered": len(jetties),
        "land_development_cost": land_development_cost_estimate(),
        "water_channel_development_cost": water_channel_development_cost_estimate(),
        "port_infra_setup_cost": port_infra_setup_cost_estimate(),
        "logistics_cost": logistics_cost_estimate(),
        "roi_assessment": roi_assessment(),
        "known_gaps": [
            "No real cost data sourced yet for land, water channel, port infra, or logistics -- all fields are structural placeholders.",
            "ROI cannot be computed without both cost data and cargo/traffic volume projections (the latter depends on Scenario Simulation).",
            "Only 2 of ~9 known NW-53 jetties currently in the data layer, so any future budget scheme will be partial until Kaushlendra's remaining jetties are added.",
            "No official IWAI/MMRDA/state government cost benchmarks referenced yet -- pending confirmation from Akash Sir on data source access."
        ]
    }

def build_financial_assessment_entity(report, jetties):
    sorted_j = sorted(jetties, key=lambda j: j["latitude"])
    corridor_coords = [(j["longitude"], j["latitude"]) for j in sorted_j]
    if len(corridor_coords) >= 2:
        geom = {"type": "LineString", "coordinates": [[c[0], c[1]] for c in corridor_coords]}
    elif corridor_coords:
        geom = point_geom(corridor_coords[0][0], corridor_coords[0][1])
    else:
        geom = None
    return envelope(
        entity_id="FINANCIAL_ASSESSMENT_NW53_MMR",
        entity_type="financial_assessment",
        name="NW-53 Kalyan-Thane-Mumbai Financial Assessment (ROI / Budget Mapping)",
        geometry=geom,
        source="mmr_financial_assessment.py (generated, not an external source)",
        authority="marine-intelligence-task internal analysis -- not an official government assessment",
        properties={
            "land_development_cost": report["land_development_cost"],
            "water_channel_development_cost": report["water_channel_development_cost"],
            "port_infra_setup_cost": report["port_infra_setup_cost"],
            "logistics_cost": report["logistics_cost"],
            "roi_assessment": report["roi_assessment"],
        },
        confidence="LOW",
        known_unknowns=report["known_gaps"]
    )

if __name__ == "__main__":
    waterways = load_json("waterways.json")
    jetties = get_mmr_jetties(waterways)
    report = build_financial_report(jetties)
    with open("mmr_financial_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("MMR financial report generated: mmr_financial_report.json")
    assessment_entity = build_financial_assessment_entity(report, jetties)
    with open("mmr_financial_assessment.json", "w", encoding="utf-8") as f:
        json.dump(assessment_entity, f, indent=2)
    print("Canonical financial_assessment entity generated: mmr_financial_assessment.json")
    print(json.dumps(report, indent=2))

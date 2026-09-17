import json
from datetime import datetime, timezone

from mmr_canonical_envelope import envelope, point_geom
from mmr_feasibility import load_json, get_mmr_jetties

# -----------------------------------------------------------------------
# RATE_CONFIG: single place to plug in real cost benchmarks once sourced
# from Akash Sir / IWAI / MMRDA / land records. Every value is None until
# a real, cited figure is provided -- nothing here is guessed or invented.
# Units are documented next to each key so whoever fills these in knows
# exactly what to provide.
# -----------------------------------------------------------------------
RATE_CONFIG = {
    "land_dev_cost_per_hectare_inr": None,       # e.g. Maharashtra Ready Reckoner rate for the corridor
    "land_area_required_hectares": None,          # estimated land footprint for jetty/terminal sites
    "water_channel_dev_cost_per_km_inr": None,    # dredging/channel construction cost per km, NW-53
    "water_channel_length_km": None,              # length of NW-53 channel requiring development
    "port_infra_setup_cost_per_berth_inr": None,  # capex per berth (construction + equipment)
    "berth_count_planned": None,                  # number of berths planned across MMR jetties
    "logistics_cost_per_tonne_km_inr": None,      # road vs waterway per-tonne-km cost benchmark
    "projected_annual_cargo_tonnes": None,        # from Scenario Simulation cargo/traffic projections
    "projected_annual_revenue_or_savings_inr": None,  # from Scenario Simulation -- needed for ROI numerator
}

def _cost_or_placeholder(value, note, methodology):
    if value is None:
        return {"status": "NOT_YET_ASSESSED", "note": note, "methodology": methodology}
    return {"status": "COMPUTED", "value_inr": round(value, 2), "methodology": methodology}

def land_development_cost_estimate():
    rate = RATE_CONFIG["land_dev_cost_per_hectare_inr"]
    area = RATE_CONFIG["land_area_required_hectares"]
    methodology = "cost = land_dev_cost_per_hectare_inr * land_area_required_hectares"
    note = "Requires real per-hectare land acquisition and development rates for the MMR corridor (Thane/Bhiwandi/Kalyan land records or MMRDA benchmarks)."
    if rate is None or area is None:
        return _cost_or_placeholder(None, note, methodology)
    return _cost_or_placeholder(rate * area, note, methodology)

def water_channel_development_cost_estimate():
    rate = RATE_CONFIG["water_channel_dev_cost_per_km_inr"]
    length = RATE_CONFIG["water_channel_length_km"]
    methodology = "cost = water_channel_dev_cost_per_km_inr * water_channel_length_km"
    note = "Requires real dredging and channel-construction cost benchmarks for NW-53 (IWAI cost norms or comparable inland waterway projects)."
    if rate is None or length is None:
        return _cost_or_placeholder(None, note, methodology)
    return _cost_or_placeholder(rate * length, note, methodology)

def port_infra_setup_cost_estimate():
    rate = RATE_CONFIG["port_infra_setup_cost_per_berth_inr"]
    berths = RATE_CONFIG["berth_count_planned"]
    methodology = "cost = port_infra_setup_cost_per_berth_inr * berth_count_planned"
    note = "Requires real port/jetty infrastructure capex benchmarks (berth construction, terminal equipment, land-side connectivity)."
    if rate is None or berths is None:
        return _cost_or_placeholder(None, note, methodology)
    return _cost_or_placeholder(rate * berths, note, methodology)

def logistics_cost_estimate():
    rate = RATE_CONFIG["logistics_cost_per_tonne_km_inr"]
    cargo = RATE_CONFIG["projected_annual_cargo_tonnes"]
    methodology = "cost = logistics_cost_per_tonne_km_inr * projected_annual_cargo_tonnes (per year; distance factor TBD once route length is fixed)"
    note = "Requires real logistics and transport cost data (per-tonne-km road vs. waterway cost comparison for the MMR corridor) and cargo volume from Scenario Simulation."
    if rate is None or cargo is None:
        return _cost_or_placeholder(None, note, methodology)
    return _cost_or_placeholder(rate * cargo, note, methodology)

def roi_assessment(land, water, port, logistics):
    methodology = "ROI = (projected_annual_revenue_or_savings_inr - total_annual_operating_cost) / total_capex"
    depends_on = [
        "land_development_cost_estimate",
        "water_channel_development_cost_estimate",
        "port_infra_setup_cost_estimate",
        "logistics_cost_estimate",
        "scenario_simulation traffic/cargo volume and revenue/savings projections",
    ]
    cost_parts = [land, water, port, logistics]
    if any(c["status"] != "COMPUTED" for c in cost_parts):
        return {
            "status": "NOT_YET_ASSESSED",
            "note": "ROI cannot be derived until all four cost components above are COMPUTED with real figures, along with projected revenue/savings from the Scenario Simulation module.",
            "methodology": methodology,
            "depends_on": depends_on,
        }
    total_capex = land["value_inr"] + water["value_inr"] + port["value_inr"]
    annual_operating_cost = logistics["value_inr"]
    revenue = RATE_CONFIG["projected_annual_revenue_or_savings_inr"]
    if revenue is None:
        return {
            "status": "PARTIAL",
            "note": "All cost components computed, but ROI still requires projected_annual_revenue_or_savings_inr from the Scenario Simulation module.",
            "total_capex_inr": round(total_capex, 2),
            "annual_operating_cost_inr": round(annual_operating_cost, 2),
            "methodology": methodology,
            "depends_on": ["scenario_simulation traffic/cargo volume and revenue/savings projections"],
        }
    roi = (revenue - annual_operating_cost) / total_capex
    return {
        "status": "COMPUTED",
        "total_capex_inr": round(total_capex, 2),
        "annual_operating_cost_inr": round(annual_operating_cost, 2),
        "annual_revenue_or_savings_inr": round(revenue, 2),
        "roi": round(roi, 4),
        "methodology": methodology,
    }

def build_financial_report(jetties):
    land = land_development_cost_estimate()
    water = water_channel_development_cost_estimate()
    port = port_infra_setup_cost_estimate()
    logistics = logistics_cost_estimate()
    roi = roi_assessment(land, water, port, logistics)
    return {
        "study": "NW-53 Kalyan-Thane-Mumbai Financial Assessment (ROI / Budget Mapping)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jetty_count_covered": len(jetties),
        "land_development_cost": land,
        "water_channel_development_cost": water,
        "port_infra_setup_cost": port,
        "logistics_cost": logistics,
        "roi_assessment": roi,
        "known_gaps": [
            "RATE_CONFIG values are all None -- formula engine is ready but no real cost data has been sourced yet.",
            "ROI cannot be computed without both cost data and cargo/traffic volume + revenue/savings projections (the latter depends on Scenario Simulation).",
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

import json
from datetime import datetime, timezone

from mmr_canonical_envelope import envelope, point_geom
from mmr_feasibility import load_json, get_mmr_jetties

# -----------------------------------------------------------------------
# SCHEMA DESIGN NOTE: This module's data categories are modeled on the
# Rhine/Danube River Information Services (RIS) standard, as suggested
# by Akash Sir -- specifically its four core data domains: fairway
# information, traffic information (vessel/AIS tracking), notices to
# skippers, and cargo/fleet management, plus RIS reference data like
# water-level gauges and the RIS Index (waterway object codes).
#
# This file is a STRUCTURAL SKELETON ONLY. No live data feed exists yet
# for any of these categories (Map My India, NISAR satellite, tide/
# salinity/water-level feeds are all still pending access confirmation
# from Akash Sir). Every section below is NOT_YET_ASSESSED by design --
# nothing here is invented or estimated.
# -----------------------------------------------------------------------

# GROWTH_CONFIG: placeholders for the 50-100 year traffic growth
# simulation. growth_rate_annual_pct must come from a real transport/
# demand study -- it is not guessed here.
GROWTH_CONFIG = {
    "growth_rate_annual_pct": None,   # e.g. compound annual cargo/traffic growth rate
    "base_year_cargo_tonnes": None,   # current-year baseline cargo volume to project from
    "projection_horizon_years": [50, 100],  # per Akash Sir's spec
}

DPR_2024_TRAFFIC = [
    {"route": "Kolshet ↔ Kalher", "direction": "Kolshet → Kalher", "peak_hour_traffic": 235, "daily_15h_traffic": 2818},
    {"route": "Kolshet ↔ Kalher", "direction": "Kalher → Kolshet", "peak_hour_traffic": 224, "daily_15h_traffic": 3027},
    {"route": "Kolshet ↔ Anjur Dive", "direction": "Kolshet → Anjur Dive", "peak_hour_traffic": 234, "daily_15h_traffic": 2461},
    {"route": "Kolshet ↔ Anjur Dive", "direction": "Anjur Dive → Kolshet", "peak_hour_traffic": 224, "daily_15h_traffic": 2018},
    {"route": "Dombivli ↔ Vasai", "direction": "Dombivli → Vasai", "peak_hour_traffic": 151, "daily_15h_traffic": 175},
    {"route": "Dombivli ↔ Vasai", "direction": "Vasai → Dombivli", "peak_hour_traffic": 172, "daily_15h_traffic": 210},
    {"route": "Dombivli ↔ Nagla Bunder", "direction": "Dombivli → Nagla Bunder", "peak_hour_traffic": 151, "daily_15h_traffic": 197},
    {"route": "Dombivli ↔ Nagla Bunder", "direction": "Nagla Bunder → Dombivli", "peak_hour_traffic": 151, "daily_15h_traffic": 197},
    {"route": "Dombivli ↔ Parsik Bunder", "direction": "Parsik Bunder → Dombivli", "peak_hour_traffic": 293, "daily_15h_traffic": 309},
    {"route": "Dombivli ↔ Parsik Bunder", "direction": "Dombivli → Parsik Bunder", "peak_hour_traffic": 768, "daily_15h_traffic": 802},
    {"route": "Kalyan ↔ Dombivli", "direction": "Dombivli → Kalyan", "peak_hour_traffic": 304, "daily_15h_traffic": 406},
    {"route": "Kalyan ↔ Dombivli", "direction": "Kalyan → Dombivli", "peak_hour_traffic": 881, "daily_15h_traffic": 1194},
]


def fairway_information():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real fairway data for NW-53: channel depth, width, navigability restrictions. Modeled on RIS 'fairway information' domain (waterway-only data).",
        "data_source_needed": "Sea routes / river data (per Akash Sir's spec), NISAR satellite bathymetry"
    }


def traffic_information():
    return {
        "status": "DPR_2024_VERIFIED",
        "note": "Peak Hour Traffic and 15-Hour Operational Traffic per Day were taken from the official IWAI DPR tables for NW-53 (2024). The 15-hour daily value already accounts for seasonal variation.",
        "source": "IWAI DPR – IWT Vasai (Bassein) Creek / NW-53 (2024)",
        "traffic_by_route": DPR_2024_TRAFFIC,
        "routes_covered": len(DPR_2024_TRAFFIC),
        "terminal_coordinate_status": {
            "Kolshet": "verified",
            "Gaimukh": "verified",
            "Vasai": "UNVERIFIED",
            "Dombivli": "UNVERIFIED",
            "Nagla Bunder": "UNVERIFIED",
            "Parsik Bunder": "UNVERIFIED",
            "Kalher": "pending verification",
            "Anjur Dive": "pending verification"
        }
    }

def water_level_and_tide_data():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real tide, salinity, and water-level data for the MMR corridor. Modeled on RIS gauge-station ('Pegelstellen') data.",
        "data_source_needed": "Tide data, salinity and water level data, weather data"
    }

def locks_and_berths_index():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires a reference index of locks, berths, and waterway objects along NW-53, analogous to the RIS Index used on the Rhine/Danube (unique codes + restricting conditions per object).",
        "data_source_needed": "Land routes data, port/jetty infrastructure records"
    }

def notices_to_skippers():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires a live safety/navigability alert feed for NW-53 (hazards, closures, seasonal restrictions). Modeled on RIS 'Notices to Skippers'.",
        "data_source_needed": "Not yet identified -- no Indian inland-waterway equivalent confirmed"
    }

def cargo_fleet_management():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires vessel/fleet and cargo-volume data moving through NW-53 jetties. Modeled on RIS 'cargo and fleet management' information.",
        "data_source_needed": "Land traffic data, logistics cost/volume data"
    }

def traffic_growth_projection():
    rate = GROWTH_CONFIG["growth_rate_annual_pct"]
    base = GROWTH_CONFIG["base_year_cargo_tonnes"]
    methodology = "future_value = base_year_cargo_tonnes * (1 + growth_rate_annual_pct/100) ** years, for years in projection_horizon_years"
    note = "Requires a real annual growth-rate assumption and a base-year cargo/traffic figure before any 50-100 year projection can be produced."
    if rate is None or base is None:
        return {
            "status": "NOT_YET_ASSESSED",
            "note": note,
            "methodology": methodology,
            "projection_horizon_years": GROWTH_CONFIG["projection_horizon_years"]
        }
    projections = {
        f"{years}_year_projection_tonnes": round(base * (1 + rate / 100) ** years, 2)
        for years in GROWTH_CONFIG["projection_horizon_years"]
    }
    return {
        "status": "COMPUTED",
        "methodology": methodology,
        "base_year_cargo_tonnes": base,
        "growth_rate_annual_pct": rate,
        **projections
    }

def build_scenario_simulation_report(jetties):
    return {
        "study": "NW-53 Kalyan-Thane-Mumbai Scenario Simulation (Partial: DPR-Verified Traffic + Schema for Remaining Domains)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "jetty_count_covered": len(jetties),
        "schema_reference": "Modeled on Rhine/Danube River Information Services (RIS) data domains, per Akash Sir's spec",
        "fairway_information": fairway_information(),
        "traffic_information": traffic_information(),
        "water_level_and_tide_data": water_level_and_tide_data(),
        "locks_and_berths_index": locks_and_berths_index(),
        "notices_to_skippers": notices_to_skippers(),
        "cargo_fleet_management": cargo_fleet_management(),
        "traffic_growth_projection": traffic_growth_projection(),
        "known_gaps": [
            "This is a schema/structure design only -- no live data source is connected for any category.",
            "Blocked on Akash Sir confirming access to Map My India API, NISAR satellite data, and tide/salinity/water-level feeds.",
            "traffic_growth_projection() formula is ready but requires a real growth-rate assumption and base-year cargo figure.",
            "Notices to Skippers has no confirmed Indian inland-waterway data source equivalent yet -- needs research.",
            "Financial assessment's roi_assessment() depends on this module's cargo/revenue projections once computed."
        ]
    }

def build_scenario_simulation_entity(report, jetties):
    sorted_j = sorted(jetties, key=lambda j: j["latitude"])
    corridor_coords = [(j["longitude"], j["latitude"]) for j in sorted_j]
    if len(corridor_coords) >= 2:
        geom = {"type": "LineString", "coordinates": [[c[0], c[1]] for c in corridor_coords]}
    elif corridor_coords:
        geom = point_geom(corridor_coords[0][0], corridor_coords[0][1])
    else:
        geom = None
    return envelope(
        entity_id="SCENARIO_SIMULATION_NW53_MMR",
        entity_type="scenario_simulation",
        name="NW-53 Kalyan-Thane-Mumbai Scenario Simulation (Partial: DPR-Verified Traffic + Schema for Remaining Domains)",
        geometry=geom,
        source="mmr_scenario_simulation.py (generated, not an external source)",
        authority="marine-intelligence-task internal analysis -- not an official government assessment",
        properties={
            "fairway_information": report["fairway_information"],
            "traffic_information": report["traffic_information"],
            "water_level_and_tide_data": report["water_level_and_tide_data"],
            "locks_and_berths_index": report["locks_and_berths_index"],
            "notices_to_skippers": report["notices_to_skippers"],
            "cargo_fleet_management": report["cargo_fleet_management"],
            "traffic_growth_projection": report["traffic_growth_projection"],
        },
        confidence="LOW",
        known_unknowns=report["known_gaps"]
    )

if __name__ == "__main__":
    waterways = load_json("waterways.json")
    jetties = get_mmr_jetties(waterways)
    report = build_scenario_simulation_report(jetties)
    with open("mmr_scenario_simulation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("MMR scenario simulation report generated: mmr_scenario_simulation_report.json")
    entity = build_scenario_simulation_entity(report, jetties)
    with open("mmr_scenario_simulation_assessment.json", "w", encoding="utf-8") as f:
        json.dump(entity, f, indent=2)
    print("Canonical scenario_simulation entity generated: mmr_scenario_simulation_assessment.json")
    print(json.dumps(report, indent=2))



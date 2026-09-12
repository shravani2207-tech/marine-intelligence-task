import json
import math
from datetime import datetime, timezone

# =====================================================================
# MMR FEASIBILITY & CONGESTION ANALYSIS -- SKELETON (Objective 3)
# Consumes existing data layer (waterways.json, ports.json, environmental.json)
# Does NOT duplicate Scenario Simulation -- this is a feasibility scoring
# module meant to feed INTO that existing capability, not replace it.
# =====================================================================

def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, dict) and "value" in data and "Count" in data:
        return data["value"]
    return data

def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))

def get_mmr_jetties(waterways_data):
    terminals = waterways_data["iwt_terminals"] if isinstance(waterways_data, dict) else waterways_data
    return [t for t in terminals if "NW-53" in t.get("waterway_name", "")]

def get_mmr_ports(ports_data):
    target_names = {"Mumbai Port", "Jawaharlal Nehru Port", "Rewas Port"}
    ports = ports_data["value"] if isinstance(ports_data, dict) and "value" in ports_data else ports_data
    return [p for p in ports if p["port_name"] in target_names]

def get_environmental_constraints(env_data):
    entries = env_data["value"] if isinstance(env_data, dict) and "value" in env_data else env_data
    return [e for e in entries if "MMR" in e.get("coverage_area", "") or "Thane" in e.get("coverage_area", "")]

def waterway_feasibility(jetties, ports):
    """
    Computes real great-circle distances from each NW-53 jetty to each MMR port.
    This is straight-line distance, NOT actual navigable waterway distance --
    that distinction is called out explicitly in the output so it is never
    mistaken for a surveyed route length.
    """
    jetty_connectivity = []
    for j in jetties:
        distances = []
        for p in ports:
            d = haversine_km(j["latitude"], j["longitude"], p["latitude"], p["longitude"])
            distances.append({"port_name": p["port_name"], "straight_line_km": round(d, 2)})
        distances.sort(key=lambda x: x["straight_line_km"])
        jetty_connectivity.append({
            "jetty": j["terminal_name"],
            "nearest_port": distances[0]["port_name"],
            "nearest_port_distance_km": distances[0]["straight_line_km"],
            "all_port_distances": distances
        })

    return {
        "jetty_count": len(jetties),
        "jetties": [j["terminal_name"] for j in jetties],
        "connected_ports": [p["port_name"] for p in ports],
        "jetty_to_port_connectivity": jetty_connectivity,
        "distance_methodology": "Haversine great-circle distance (straight-line), NOT actual navigable waterway route length. Real feasibility scoring still requires navigability depth, seasonal variation, and dredging data.",
        "status": "DISTANCE_COMPUTED_NO_FEASIBILITY_SCORE_YET",
        "note": "Real feasibility score not yet computed -- needs methodology beyond distance (navigability, depth, seasonal data)."
    }

def decongestion_assessment():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real road-traffic baseline data (e.g. Maharashtra traffic dept, Google/TomTom congestion index) before any estimate can be produced.",
        "methodology": "TBD"
    }

def environmental_overlay(constraints, jetties):
    flags = []
    for c in constraints:
        if "Ramsar" in c.get("dataset_name", ""):
            for j in jetties:
                flags.append({
                    "jetty": j["terminal_name"],
                    "constraint": c["dataset_name"],
                    "note": "Within Thane Creek Ramsar corridor -- dredging/siting requires ecological clearance."
                })
    return flags

def build_report():
    waterways = load_json("waterways.json")
    ports = load_json("ports.json")
    environmental = load_json("environmental.json")

    jetties = get_mmr_jetties(waterways)
    mmr_ports = get_mmr_ports(ports)
    constraints = get_environmental_constraints(environmental)

    report = {
        "study": "NW53 Kalyan-Thane-Mumbai Waterway Feasibility",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "waterway_feasibility": waterway_feasibility(jetties, mmr_ports),
        "decongestion_assessment": decongestion_assessment(),
        "environmental_flags": environmental_overlay(constraints, jetties),
        "known_gaps": [
            "Only 2 of ~9 known NW-53 jetties currently in data layer (Kaushlendra adding rest).",
            "Distances are straight-line (haversine), not actual navigable waterway route length.",
            "No real feasibility scoring model yet -- distance is one input, not a complete score.",
            "No real congestion/traffic baseline sourced yet.",
            "logistics.json Bhiwandi entry is a non-MMLP private cluster -- financial/intermodal assessment still needs official data."
        ]
    }
    return report

if __name__ == "__main__":
    report = build_report()
    with open("mmr_feasibility_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("MMR feasibility skeleton report generated: mmr_feasibility_report.json")
    print(json.dumps(report, indent=2))

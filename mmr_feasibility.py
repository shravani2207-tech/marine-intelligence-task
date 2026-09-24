import json
import math
from datetime import datetime, timezone

from mmr_canonical_envelope import envelope, point_geom, SCHEMA_VERSION

def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, dict) and "value" in data and "Count" in data:
        return data["value"]
    return data

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))

def get_mmr_jetties(waterways_data):
    terminals = waterways_data["iwt_terminals"] if isinstance(waterways_data, dict) else waterways_data
    return [t for t in terminals if "NW-53" in t.get("waterway_name", "") and t.get("coordinate_verification") != "UNVERIFIED"]

def get_mmr_ports(ports_data):
    target_names = {"Mumbai Port", "Jawaharlal Nehru Port", "Rewas Port"}
    ports = ports_data["value"] if isinstance(ports_data, dict) and "value" in ports_data else ports_data
    return [p for p in ports if p["port_name"] in target_names]

def get_environmental_constraints(env_data):
    entries = env_data["value"] if isinstance(env_data, dict) and "value" in env_data else env_data
    return [e for e in entries if "MMR" in e.get("coverage_area", "") or "Thane" in e.get("coverage_area", "")]

def waterway_feasibility(jetties, ports):
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
        "distance_methodology": "Haversine great-circle distance (straight-line), NOT actual navigable waterway route length.",
        "status": "DISTANCE_COMPUTED_NO_FEASIBILITY_SCORE_YET",
        "note": "Real feasibility score not yet computed -- needs methodology beyond distance (navigability, depth, seasonal data)."
    }

def decongestion_assessment():
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real road-traffic baseline data before any estimate can be produced.",
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

def corridor_score(jetties):
    n = len(jetties)
    if n < 2:
        return 0.0, [f"Only {n} NW-53 jetty(ies) with coordinates -- need >= 2 to score a corridor."]
    sorted_j = sorted(jetties, key=lambda j: j["latitude"])
    gaps_km = [
        haversine_km(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
        for a, b in zip(sorted_j, sorted_j[1:])
    ]
    target_jetty_count = 9
    coverage_score = min(n / target_jetty_count, 1.0) * 60
    gap_flag_threshold_km = 15
    flags = []
    spacing_penalty = 0
    for g in gaps_km:
        if g > gap_flag_threshold_km:
            spacing_penalty += 5
            flags.append(f"Large gap ({g:.1f} km) between consecutive NW-53 jetties -- possible missing terminal in the sequence.")
    spacing_score = max(40 - spacing_penalty, 0)
    return round(coverage_score + spacing_score, 1), flags

def intermodal_score(waterway_feasibility_result):
    connectivity = waterway_feasibility_result["jetty_to_port_connectivity"]
    if not connectivity:
        return 0.0, ["No jetty-to-port connectivity data available."]
    nearest = [c["nearest_port_distance_km"] for c in connectivity]
    avg_nearest = sum(nearest) / len(nearest)
    falloff_km = 50
    score = max(0.0, 100 - (avg_nearest / falloff_km) * 100)
    flags = []
    if avg_nearest > 40:
        flags.append(f"Average jetty-to-nearest-major-port distance is high ({avg_nearest:.1f} km, straight-line).")
    return round(score, 1), flags

def build_report():
    waterways = load_json("waterways.json")
    ports = load_json("ports.json")
    environmental = load_json("environmental.json")
    jetties = get_mmr_jetties(waterways)
    mmr_ports = get_mmr_ports(ports)
    constraints = get_environmental_constraints(environmental)
    wf = waterway_feasibility(jetties, mmr_ports)
    c_score, c_flags = corridor_score(jetties)
    i_score, i_flags = intermodal_score(wf)
    report = {
        "study": "NW53 Kalyan-Thane-Mumbai Waterway Feasibility",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "waterway_feasibility": wf,
        "structural_scores": {
            "corridor_score": c_score,
            "intermodal_score": i_score,
            "flags": c_flags + i_flags,
            "note": "Structural scores only. Not a substitute for navigability, depth, seasonal, or congestion data."
        },
        "decongestion_assessment": decongestion_assessment(),
        "environmental_flags": environmental_overlay(constraints, jetties),
        "known_gaps": [
            "Only 2 of ~9 known NW-53 jetties currently in data layer.",
            "Distances are straight-line (haversine), not actual navigable waterway route length.",
            "Structural scores are directional only.",
            "No real congestion/traffic baseline sourced yet.",
            "logistics.json Bhiwandi entry is a non-MMLP private cluster.",
            "corridor_score/intermodal_score thresholds are placeholders, not sourced."
        ]
    }
    return report

def build_feasibility_assessment_entity(report, jetties):
    sorted_j = sorted(jetties, key=lambda j: j["latitude"])
    corridor_coords = [(j["longitude"], j["latitude"]) for j in sorted_j]
    if len(corridor_coords) >= 2:
        geom = {"type": "LineString", "coordinates": [[c[0], c[1]] for c in corridor_coords]}
    elif corridor_coords:
        geom = point_geom(corridor_coords[0][0], corridor_coords[0][1])
    else:
        geom = None
    return envelope(
        entity_id="FEASIBILITY_NW53_MMR",
        entity_type="feasibility_assessment",
        name="NW-53 Kalyan-Thane-Mumbai Waterway Feasibility Assessment",
        geometry=geom,
        source="mmr_feasibility.py (generated, not an external source)",
        authority="marine-intelligence-task internal analysis -- not an official government assessment",
        properties={
            "structural_scores": report["structural_scores"],
            "decongestion_assessment": report["decongestion_assessment"],
            "environmental_flags": report["environmental_flags"],
        },
        confidence="LOW",
        known_unknowns=report["known_gaps"]
    )

if __name__ == "__main__":
    waterways = load_json("waterways.json")
    jetties = get_mmr_jetties(waterways)
    report = build_report()
    with open("mmr_feasibility_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("MMR feasibility report generated: mmr_feasibility_report.json")
    assessment_entity = build_feasibility_assessment_entity(report, jetties)
    with open("mmr_feasibility_assessment.json", "w", encoding="utf-8") as f:
        json.dump(assessment_entity, f, indent=2)
    print("Canonical feasibility_assessment entity generated: mmr_feasibility_assessment.json")
    print(json.dumps(report, indent=2))

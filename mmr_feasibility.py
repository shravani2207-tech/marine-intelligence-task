import json
from datetime import datetime, timezone

# =====================================================================
# MMR FEASIBILITY & CONGESTION ANALYSIS -- SKELETON (Objective 3)
# Consumes existing data layer (waterways.json, ports.json, environmental.json)
# Does NOT duplicate Scenario Simulation -- this is a feasibility scoring
# module meant to feed INTO that existing capability, not replace it.
# =====================================================================

def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)

def get_mmr_jetties(waterways_data):
    """Filter iwt_terminals for the NW-53 (Kalyan-Thane-Mumbai) corridor."""
    terminals = waterways_data["iwt_terminals"] if isinstance(waterways_data, dict) and "iwt_terminals" in waterways_data else waterways_data
    return [t for t in terminals if "NW-53" in t.get("waterway_name", "")]

def get_mmr_ports(ports_data):
    """Filter ports relevant to MMR intermodal connectivity."""
    target_names = {"Mumbai Port", "Jawaharlal Nehru Port", "Rewas Port"}
    ports = ports_data["value"] if isinstance(ports_data, dict) and "value" in ports_data else ports_data
    return [p for p in ports if p["port_name"] in target_names]

def get_environmental_constraints(env_data):
    """Filter environmental datasets relevant to MMR/Thane Creek."""
    entries = env_data["value"] if isinstance(env_data, dict) and "value" in env_data else env_data
    return [e for e in entries if "MMR" in e.get("coverage_area", "") or "Thane" in e.get("coverage_area", "")]

def waterway_feasibility(jetties, ports):
    """
    PLACEHOLDER scoring -- not a validated model yet.
    Currently just confirms data presence and proximity notes.
    TODO (Aman): replace with real feasibility scoring methodology
    (navigability depth, seasonal variation, dredging need, etc.)
    """
    return {
        "jetty_count": len(jetties),
        "jetties": [j["terminal_name"] for j in jetties],
        "connected_ports": [p["port_name"] for p in ports],
        "status": "DATA_PRESENT_NO_SCORING_YET",
        "note": "Real feasibility score not yet computed -- needs methodology (navigability, depth, seasonal data)."
    }

def decongestion_assessment():
    """
    PLACEHOLDER -- no real traffic/congestion data sourced yet.
    Per playbook: must expose methodology, baseline, and uncertainty
    -- never fabricate a number.
    """
    return {
        "status": "NOT_YET_ASSESSED",
        "note": "Requires real road-traffic baseline data (e.g. Maharashtra traffic dept, Google/TomTom congestion index) before any estimate can be produced.",
        "methodology": "TBD"
    }

def environmental_overlay(constraints, jetties):
    """Flag jetties that fall inside/near a known environmental constraint."""
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
            "No real feasibility scoring model yet -- placeholder only.",
            "No real congestion/traffic baseline sourced yet.",
            "logistics.json has no confirmed Bhiwandi MMLP -- financial/intermodal assessment incomplete."
        ]
    }
    return report

if __name__ == "__main__":
    report = build_report()
    with open("mmr_feasibility_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("MMR feasibility skeleton report generated: mmr_feasibility_report.json")
    print(json.dumps(report, indent=2))





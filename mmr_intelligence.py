from __future__ import annotations
import json
import math
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

SCHEMA_VERSION = "1.0.0"
PIPELINE_VERSION = "mmr_intelligence_pipeline@0.2.0"
SOURCE_COMMIT = "4f5c9cc"  # repo state this pipeline was written against

# ---------------------------------------------------------------------------
# CONFIG - point these at your actual repo files.
# ---------------------------------------------------------------------------
CONFIG = {
    "waterways_json": "data/waterways.json",              # now 26 terminals + 25 stations
    "ports_json": "data/ports.json",
    "environmental_json": "data/environmental.json",
    "logistics_json": "data/logistics.json",
    "dpr_2024_traffic_json": "data/dpr_2024_traffic.json",  # 12 routes / 6 jetties, VERIFIED
    "mmr_feasibility_assessment_json": "mmr_feasibility_assessment.json",
    "mmr_financial_assessment_json": "mmr_financial_assessment.json",
    "roads_json": None,   # MISSING per component status map
    "rail_json": None,    # MISSING per component status map
    "traffic_congestion_json": None,  # road congestion baseline - MISSING (distinct from DPR traffic)
    "output_path": "mmr_intelligence_result.json",
    "environmental_flag_radius_km": 5.0,
    "logistics_near_radius_km": 15.0,
    # coordinates within this tolerance of each other are treated as duplicates
    "duplicate_coord_tolerance_deg": 1e-6,
}

# ---------------------------------------------------------------------------
# NW-53 verification registry
#
# This is deliberately hand-maintained, not inferred from waterways.json,
# because the verification status is a provenance judgment (DPR anomaly
# cross-checks, coordinate sanity review) that doesn't live in the raw
# coordinate data itself. Update this block as verification work lands
# (e.g. after the Friday EOD check on Dombivli / Parsik Bunder).
# ---------------------------------------------------------------------------
VERIFICATION_REGISTRY = {
    "kolshet":        {"status": "usable", "note": "Verified usable."},
    "gaimukh":        {"status": "usable", "note": "Verified usable."},
    "vasai":          {"status": "usable", "note": "Verified usable."},
    "nagla bunder":   {"status": "usable", "note": "Verified usable."},
    "dombivli": {
        "status": "pending_verification",
        "note": "DPR coordinate reported near 72.0E, flagged anomalous. "
                 "Cross-verification target: Friday EOD. Excluded from scoring until resolved.",
    },
    "parsik bunder": {
        "status": "pending_verification",
        "note": "DPR coordinate reported near 72.0E, flagged anomalous. "
                 "Cross-verification target: Friday EOD. Excluded from scoring until resolved.",
    },
    "kalher":      {"status": "pending_verification", "note": "Verification pending; not yet a validated production location."},
    "anjur dive":  {"status": "pending_verification", "note": "Verification pending; not yet a validated production location."},
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Optional[str]) -> Optional[Any]:
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def get_verification(terminal: dict) -> dict:
    """Look up a terminal's verification status. Anything not explicitly
    registered as 'usable' defaults to pending -- the registry is an
    allowlist, not a denylist, so new/unrecognized terminals never sneak
    into scoring unverified."""
    name = (terminal.get("terminal_name") or "").strip().lower()
    entry = VERIFICATION_REGISTRY.get(name)
    if entry:
        return entry
    return {
        "status": "pending_verification",
        "note": f"'{terminal.get('terminal_name')}' is not present in VERIFICATION_REGISTRY; "
                "treated as unverified by default until explicitly reviewed and added.",
    }


@dataclass
class StageResult:
    stage: str
    status: str  # ASSESSED | NOT_YET_ASSESSED | PARTIAL | EXCLUDED_PENDING_VERIFICATION
    value: Any = None
    confidence: Optional[str] = None
    basis: str = ""
    source: list = field(default_factory=list)
    limitations: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def not_yet_assessed(stage: str, missing_inputs: list, note: str = "") -> StageResult:
    return StageResult(
        stage=stage,
        status="NOT_YET_ASSESSED",
        value=None,
        confidence=None,
        basis=note or "Blocked on missing authoritative input.",
        source=[],
        limitations=[f"Missing input: {m}" for m in missing_inputs],
    )


# ---------------------------------------------------------------------------
# Data-quality gate: duplicate / anomalous coordinates
# Runs once across all loaded entities before per-terminal analysis.
# ---------------------------------------------------------------------------
def data_quality_scan(datasets: dict, config: dict) -> dict:
    tol = config["duplicate_coord_tolerance_deg"]
    points = []  # (label, dataset_name, lat, lon)
    for dataset_name, records in datasets.items():
        if not records:
            continue
        for r in records:
            lat, lon = r.get("latitude"), r.get("longitude")
            if lat is None or lon is None:
                continue
            label = r.get("terminal_name") or r.get("port_name") or r.get("park_name") \
                or r.get("dataset_name") or r.get("station_name") or r.get("terminal_id") or "unknown"
            points.append((label, dataset_name, lat, lon))

    duplicates = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            l1, d1, la1, lo1 = points[i]
            l2, d2, la2, lo2 = points[j]
            if abs(la1 - la2) <= tol and abs(lo1 - lo2) <= tol:
                duplicates.append({
                    "entity_a": {"label": l1, "dataset": d1}, "entity_b": {"label": l2, "dataset": d2},
                    "latitude": la1, "longitude": lo1,
                })

    anomalies = []
    for dataset_name, records in datasets.items():
        if not records:
            continue
        for r in records:
            name = (r.get("terminal_name") or "").strip().lower()
            lon = r.get("longitude")
            if name in ("dombivli", "parsik bunder") and lon is not None and round(lon, 1) == 72.0:
                anomalies.append({
                    "label": r.get("terminal_name"), "dataset": dataset_name, "longitude": lon,
                    "note": "Matches the documented ~72.0E DPR coordinate anomaly; pending cross-verification.",
                })

    return {
        "duplicate_coordinates": duplicates,
        "known_coordinate_anomalies": anomalies,
        "note": "Duplicate check is exact-match within tolerance across all loaded datasets "
                "(this is what surfaces issues like Kottapuram/Alappuzha sharing coordinates). "
                "Anomaly check is a named allowlist of previously flagged records, not a general "
                "outlier detector.",
    }


# ---------------------------------------------------------------------------
# Stage 1: MMR Waterways (base entities)
# ---------------------------------------------------------------------------
def stage_waterways(config: dict) -> list[dict]:
    raw = load_json(config["waterways_json"])
    if raw is None:
        return []
    return raw.get("iwt_terminals", raw if isinstance(raw, list) else [])


# ---------------------------------------------------------------------------
# Stage 2: Infrastructure
# ---------------------------------------------------------------------------
def stage_infrastructure(terminal: dict, ports: Optional[list]) -> StageResult:
    if not ports:
        return not_yet_assessed("infrastructure", ["ports.json"])
    lat, lon = terminal.get("latitude"), terminal.get("longitude")
    if lat is None or lon is None:
        return not_yet_assessed("infrastructure", ["terminal.latitude/longitude"])

    nearby = []
    for p in ports:
        try:
            d = haversine_km(lat, lon, p["latitude"], p["longitude"])
        except (KeyError, TypeError):
            continue
        nearby.append({"port_id": p.get("port_id"), "port_name": p.get("port_name"), "distance_km": round(d, 2)})
    nearby.sort(key=lambda x: x["distance_km"])

    return StageResult(
        stage="infrastructure",
        status="ASSESSED",
        value={"nearby_ports": nearby[:5]},
        confidence="MEDIUM",
        basis="Haversine distance from terminal to each port in ports.json, sorted ascending.",
        source=["ports.json"],
        limitations=["Point coordinates only; no channel depth or berth-side draft data."],
    )


# ---------------------------------------------------------------------------
# Stage 3: Connectivity (road/rail) - still MISSING per component status map
# ---------------------------------------------------------------------------
def stage_connectivity(terminal: dict, config: dict) -> StageResult:
    have_road = config.get("roads_json") and os.path.exists(config["roads_json"] or "")
    have_rail = config.get("rail_json") and os.path.exists(config["rail_json"] or "")
    if not have_road and not have_rail:
        return not_yet_assessed(
            "connectivity",
            ["road network dataset (e.g. OSM/NHAI)", "rail network dataset (e.g. Indian Railways GIS)"],
            "Component status map lists road/rail connectivity as MISSING at commit "
            f"{SOURCE_COMMIT}; cannot be scored without a dataset.",
        )
    return not_yet_assessed("connectivity", ["scoring logic not yet implemented for provided dataset"])


# ---------------------------------------------------------------------------
# Stage 4: Environmental Constraints
# ---------------------------------------------------------------------------
def stage_environmental(terminal: dict, environmental: Optional[list], config: dict) -> StageResult:
    if not environmental:
        return not_yet_assessed("environmental_constraints", ["environmental.json"])
    lat, lon = terminal.get("latitude"), terminal.get("longitude")
    if lat is None or lon is None:
        return not_yet_assessed("environmental_constraints", ["terminal.latitude/longitude"])

    radius = config["environmental_flag_radius_km"]
    flags = []
    for e in environmental:
        e_lat, e_lon = e.get("latitude"), e.get("longitude")
        if e_lat is None or e_lon is None:
            continue
        d = haversine_km(lat, lon, e_lat, e_lon)
        if d <= radius:
            flags.append({"dataset_id": e.get("dataset_id"), "dataset_name": e.get("dataset_name"), "distance_km": round(d, 2)})

    level = "HIGH" if flags else "LOW"
    return StageResult(
        stage="environmental_constraints",
        status="ASSESSED",
        value={"constraint_level": level, "nearby_constraints": flags},
        confidence="LOW",
        basis=f"Point-distance proximity check (<= {radius} km) against environmental.json centroids.",
        source=["environmental.json"],
        limitations=[
            "Floodplain/watershed/protected-area polygons remain approximate bounding areas "
            "per the component status map (NEEDS INTEGRATION against official GIS boundaries).",
            "Point-to-point proximity is a coarse proxy for actual polygon overlap.",
        ],
    )


# ---------------------------------------------------------------------------
# Stage 5: Logistics Opportunities
# ---------------------------------------------------------------------------
def stage_logistics(terminal: dict, logistics: Optional[list], config: dict) -> StageResult:
    if not logistics:
        return not_yet_assessed("logistics_opportunity", ["logistics.json"])
    lat, lon = terminal.get("latitude"), terminal.get("longitude")
    if lat is None or lon is None:
        return not_yet_assessed("logistics_opportunity", ["terminal.latitude/longitude"])

    radius = config["logistics_near_radius_km"]
    near = []
    for p in logistics:
        p_lat, p_lon = p.get("latitude"), p.get("longitude")
        if p_lat is None or p_lon is None:
            continue
        d = haversine_km(lat, lon, p_lat, p_lon)
        if d <= radius:
            near.append({"park_id": p.get("park_id"), "park_name": p.get("park_name"), "distance_km": round(d, 2)})
    near.sort(key=lambda x: x["distance_km"])

    level = "HIGH" if len(near) >= 2 else ("MEDIUM" if near else "LOW")
    notes = []
    if any("Bhiwandi" in (n.get("park_name") or "") for n in near):
        notes.append("Includes Bhiwandi cluster, which is private/non-MMLP, not an official PM GatiShakti hub.")

    return StageResult(
        stage="logistics_opportunity",
        status="ASSESSED",
        value={"opportunity_level": level, "nearby_clusters": near},
        confidence="MEDIUM",
        basis=f"Count of logistics.json clusters within {radius} km, banded HIGH(>=2)/MEDIUM(1)/LOW(0).",
        source=["logistics.json"],
        limitations=notes,
    )


# ---------------------------------------------------------------------------
# Stage 6 (new): DPR 2024 Traffic
# ---------------------------------------------------------------------------
def stage_traffic(terminal: dict, dpr_traffic: Optional[dict]) -> StageResult:
    if not dpr_traffic:
        return not_yet_assessed("dpr_2024_traffic", ["dpr_2024_traffic.json"])

    name = (terminal.get("terminal_name") or "").strip().lower()
    covered = dpr_traffic.get("jetties_covered", [])
    covered_lower = [c.strip().lower() for c in covered]
    if name not in covered_lower:
        return not_yet_assessed(
            "dpr_2024_traffic", [f"DPR 2024 traffic coverage for '{terminal.get('terminal_name')}'"],
            "DPR 2024 traffic is verified for 12 routes / 6 named jetties; this terminal is not "
            "among the covered set.",
        )

    routes = [r for r in dpr_traffic.get("routes", []) if name in [j.strip().lower() for j in r.get("jetties", [])]]
    return StageResult(
        stage="dpr_2024_traffic",
        status="ASSESSED",
        value={"routes_covering_this_jetty": len(routes), "route_ids": [r.get("route_id") for r in routes]},
        confidence="MEDIUM",
        basis="DPR 2024 traffic_information() dataset, status DPR_2024_VERIFIED, 12 routes / 6 jetties.",
        source=["dpr_2024_traffic.json"],
        limitations=["Covers the 6 named DPR jetties only; not a live/real-time traffic feed."],
    )


# ---------------------------------------------------------------------------
# Stage 7: Movement Feasibility
# NW-53 Scoring Rule applied here: a terminal that is not verification
# status "usable" is excluded outright, regardless of what upstream data
# would otherwise support -- this mirrors the documented pipeline treatment
# for Dombivli / Parsik Bunder / Kalher / Anjur Dive.
# ---------------------------------------------------------------------------
def stage_movement_feasibility(terminal: dict, infra, connectivity, environmental, logistics, traffic) -> StageResult:
    verification = get_verification(terminal)
    if verification["status"] != "usable":
        return StageResult(
            stage="movement_feasibility",
            status="EXCLUDED_PENDING_VERIFICATION",
            value=None,
            confidence=None,
            basis="NW-53 Scoring Rule: only verification-status 'usable' jetties participate in "
                  "pipeline scoring. This terminal is excluded, not scored as low/uncertain.",
            source=[],
            limitations=[verification["note"]],
        )

    upstream = [infra, connectivity, environmental, logistics, traffic]
    used = [s for s in upstream if s.status == "ASSESSED"]
    missing = [s.stage for s in upstream if s.status != "ASSESSED"]

    if not used:
        return not_yet_assessed("movement_feasibility", ["at least one ASSESSED upstream stage"])

    confidence_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    weakest = min(used, key=lambda s: confidence_rank.get(s.confidence, 0))
    status = "ASSESSED" if not missing else "PARTIAL"

    return StageResult(
        stage="movement_feasibility",
        status=status,
        value={
            "contributing_stages": [s.stage for s in used],
            "excluded_stages": missing,
            "qualitative_summary": _qualitative_feasibility(infra, environmental, logistics, traffic),
        },
        confidence=weakest.confidence,
        basis="Composite of ASSESSED upstream stages only for a verification-status 'usable' jetty; "
              "confidence capped at weakest contributing stage. No numeric feasibility score is "
              "produced while connectivity (road/rail) remains unassessed.",
        source=list({src for s in used for src in s.source}),
        limitations=[f"Excludes: {m} (NOT_YET_ASSESSED)" for m in missing],
    )


def _qualitative_feasibility(infra, environmental, logistics, traffic) -> str:
    parts = []
    if infra.status == "ASSESSED" and infra.value["nearby_ports"]:
        parts.append(f"nearest port {infra.value['nearby_ports'][0]['distance_km']} km away")
    if environmental.status == "ASSESSED":
        parts.append(f"environmental constraint level {environmental.value['constraint_level']}")
    if logistics.status == "ASSESSED":
        parts.append(f"logistics opportunity {logistics.value['opportunity_level']}")
    if traffic.status == "ASSESSED":
        parts.append(f"{traffic.value['routes_covering_this_jetty']} DPR-2024-verified route(s)")
    return "; ".join(parts) if parts else "insufficient ASSESSED data for a qualitative summary"


# ---------------------------------------------------------------------------
# Stage 8: Congestion Impact - still MISSING
# ---------------------------------------------------------------------------
def stage_congestion(config: dict) -> StageResult:
    if config.get("traffic_congestion_json") and os.path.exists(config["traffic_congestion_json"]):
        return not_yet_assessed("congestion_impact", ["scoring logic not yet implemented for provided dataset"])
    return not_yet_assessed(
        "congestion_impact",
        ["Road congestion baseline (e.g. TomTom / Google Traffic / Maharashtra Traffic Dept)"],
        "Listed as MISSING in the component status map at commit " + SOURCE_COMMIT +
        ". Note: DPR 2024 traffic (stage 6) is waterway route traffic, not road congestion, "
        "and does not unblock this stage.",
    )


# ---------------------------------------------------------------------------
# Stage 9: Economic / Operational Factors - still NOT_YET_ASSESSED
# ---------------------------------------------------------------------------
def stage_economic(config: dict) -> StageResult:
    financial = load_json(config["mmr_financial_assessment_json"])
    if financial is None:
        return not_yet_assessed("economic_operational", ["mmr_financial_assessment.json"])
    rate_config = financial.get("RATE_CONFIG") or financial.get("rate_config")
    if not rate_config or all(v is None for v in rate_config.values()):
        return not_yet_assessed(
            "economic_operational",
            ["land_dev_cost_per_hectare_inr", "water_channel_dev_cost_per_km_inr",
             "port_infra_setup_cost_per_berth_inr", "logistics_cost_per_tonne_km_inr"],
            "RATE_CONFIG remains unpopulated at commit " + SOURCE_COMMIT + "; framework is REUSABLE "
            "but authoritative benchmark rates are still required.",
        )
    return StageResult(
        stage="economic_operational",
        status="ASSESSED",
        value=financial.get("roi_summary"),
        confidence="MEDIUM",
        basis="Passed through from mmr_financial_assessment.py using populated RATE_CONFIG.",
        source=["mmr_financial_assessment.json"],
        limitations=["Verify RATE_CONFIG benchmark vintage/date before trusting ROI figures."],
    )


# ---------------------------------------------------------------------------
# Stage 10: Final Intelligence Result
# ---------------------------------------------------------------------------
def build_final_result(terminal: dict, stages: dict, verification: dict) -> dict:
    if verification["status"] != "usable":
        overall_status = "EXCLUDED_PENDING_VERIFICATION"
        overall_confidence = None
    else:
        all_statuses = [s.status for s in stages.values()]
        if all(s == "NOT_YET_ASSESSED" for s in all_statuses):
            overall_status = "NOT_YET_ASSESSED"
        elif all(s == "ASSESSED" for s in all_statuses):
            overall_status = "ASSESSED"
        else:
            overall_status = "PARTIAL"
        assessed = [s for s in stages.values() if s.status == "ASSESSED" and s.confidence]
        confidence_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
        overall_confidence = (
            min(assessed, key=lambda s: confidence_rank[s.confidence]).confidence if assessed else None
        )

    return {
        "entity_id": f"INTELLIGENCE_{terminal.get('terminal_id', 'UNKNOWN')}",
        "entity_type": "movement_intelligence_result",
        "name": terminal.get("terminal_name"),
        "waterway_name": terminal.get("waterway_name"),
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "source_commit": SOURCE_COMMIT,
        "timestamp": now_iso(),
        "verification_status": verification["status"],
        "verification_note": verification["note"],
        "included_in_scoring": verification["status"] == "usable",
        "overall_status": overall_status,
        "overall_confidence": overall_confidence,
        "overall_confidence_note": (
            "Overall confidence is the MINIMUM confidence across ASSESSED stages, not an average. "
            "A single weak or missing input caps the whole result; this is deliberate."
        ),
        "stages": {name: s.to_dict() for name, s in stages.items()},
        "provenance": {
            "origin": "mmr_intelligence_pipeline.py",
            "added_by": "automated_pipeline",
            "method": "deterministic_composition_of_documented_modules",
        },
    }


def run_pipeline(config: dict = CONFIG) -> dict:
    terminals = stage_waterways(config)
    ports = load_json(config["ports_json"])
    environmental = load_json(config["environmental_json"])
    logistics = load_json(config["logistics_json"])
    dpr_traffic = load_json(config["dpr_2024_traffic_json"])

    quality = data_quality_scan(
        {"waterways": terminals, "ports": ports, "environmental": environmental, "logistics": logistics},
        config,
    )

    results = []
    for terminal in terminals:
        verification = get_verification(terminal)
        infra = stage_infrastructure(terminal, ports)
        connectivity = stage_connectivity(terminal, config)
        env = stage_environmental(terminal, environmental, config)
        log = stage_logistics(terminal, logistics, config)
        traffic = stage_traffic(terminal, dpr_traffic)
        feas = stage_movement_feasibility(terminal, infra, connectivity, env, log, traffic)
        congestion = stage_congestion(config)
        econ = stage_economic(config)

        stages = {
            "infrastructure": infra,
            "connectivity": connectivity,
            "environmental_constraints": env,
            "logistics_opportunity": log,
            "dpr_2024_traffic": traffic,
            "movement_feasibility": feas,
            "congestion_impact": congestion,
            "economic_operational": econ,
        }
        results.append(build_final_result(terminal, stages, verification))

    output = {
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": PIPELINE_VERSION,
        "source_commit": SOURCE_COMMIT,
        "generated_at": now_iso(),
        "data_quality": quality,
        "results": results,
    }

    with open(config["output_path"], "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        print("Final result written to ", os.path.abspath(config["output_path"]))
    return output


if __name__ == "__main__":
    output = run_pipeline()
    dq = output["data_quality"]
    if dq["duplicate_coordinates"]:
        print(f"DATA QUALITY WARNING: {len(dq['duplicate_coordinates'])} duplicate-coordinate pair(s) found.")
    for r in output["results"]:
        print(f"  {r['entity_id']} ({r['name']}): verification={r['verification_status']} "
              f"included_in_scoring={r['included_in_scoring']} overall_status={r['overall_status']} "
              f"confidence={r['overall_confidence']}")

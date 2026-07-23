import json
from datetime import datetime, timezone

with open("spatial_truth_export.json") as f:
    data = json.load(f)

nodes = []
edges = []
now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# =====================================================================
# Map rivers -> Geographic Nodes (entity_type: River)
# =====================================================================
for feature in data["river_network"]["features"]:
    props = feature["properties"]
    nodes.append({
        "entity_id": props["river_id"],
        "entity_type": "River",
        "name": props["river_name"],
        "status": "Operational",
        "version": "1.0",
        "owner": "Shravani - National Geospatial Intelligence Layer",
        "created_at": now,
        "updated_at": now,
        "trace_id": f"NGIL_{props['river_id']}"
    })

# =====================================================================
# Map infrastructure -> Infrastructure Nodes
# =====================================================================
for feature in data["infrastructure_matrix"]["features"]:
    props = feature["properties"]
    nodes.append({
        "entity_id": props["infra_id"],
        "entity_type": props["type"],  # Dam, Barrage, Port, Lock, Reservoir, Wetland, etc.
        "name": props["name"],
        "status": "Operational",
        "version": "1.0",
        "owner": "Shravani - National Geospatial Intelligence Layer",
        "created_at": now,
        "updated_at": now,
        "trace_id": f"NGIL_{props['infra_id']}"
    })
    # Spatial relationship: infra located_in / part_of river
    edges.append({
        "relationship_id": f"REL_LOC_{props['infra_id']}",
        "source": props["infra_id"],
        "target": next(r["river_id"] for r in [
            fr["properties"] for fr in data["river_network"]["features"]
        ] if r["river_name"] == props["associated_river"]),
        "relationship": "located_in",
        "confidence": 0.75,
        "authority": "NGIL",
        "evidence_id": "EV_NGIL_REPRESENTATIVE_GEOMETRY",
        "validation_status": "Unvalidated",
        "version": "1.0",
        "created_at": now
    })

# =====================================================================
# Map provenance_topology -> upstream_of / downstream_of edges
# =====================================================================
for i, t in enumerate(data["provenance_topology"]):
    up_infra = next((f["properties"]["infra_id"] for f in data["infrastructure_matrix"]["features"] if f["properties"]["name"] == t["upstream_node"]), None)
    down_infra = next((f["properties"]["infra_id"] for f in data["infrastructure_matrix"]["features"] if f["properties"]["name"] == t["downstream_node"]), None)
    if up_infra and down_infra:
        edges.append({
            "relationship_id": f"REL_TOPO_{i+1:03d}",
            "source": up_infra,
            "target": down_infra,
            "relationship": "upstream_of",
            "confidence": 0.7,
            "authority": "NGIL",
            "evidence_id": "EV_NGIL_TOPOLOGY_DERIVATION",
            "validation_status": "Unvalidated",
            "version": "1.0",
            "created_at": now
        })

# =====================================================================
# Map flood_risk_overlay -> River state / risk relationship
# =====================================================================
for i, fr in enumerate(data["flood_risk_overlay"]):
    river_id = next((r["properties"]["river_id"] for r in data["river_network"]["features"] if r["properties"]["river_name"] == fr["river"]), None)
    if river_id:
        risk_node_id = f"RISK_{river_id}"
        nodes.append({
            "entity_id": risk_node_id,
            "entity_type": "Risk",
            "name": f"{fr['river']} Flood Risk",
            "status": fr["flood_risk"],
            "version": "1.0",
            "owner": "Shravani - National Geospatial Intelligence Layer",
            "created_at": now,
            "updated_at": now,
            "trace_id": f"NGIL_{risk_node_id}"
        })
        edges.append({
            "relationship_id": f"REL_RISK_{i+1:03d}",
            "source": risk_node_id,
            "target": river_id,
            "relationship": "constrains",
            "confidence": 0.6,
            "authority": "NGIL",
            "evidence_id": "EV_NGIL_HISTORICAL_FLOOD_PATTERN",
            "validation_status": "Unvalidated",
            "version": "1.0",
            "created_at": now
        })

kg_export = {
    "graph_metadata": {
        "source_system": "marine-intelligence-task (National Geospatial Intelligence Layer)",
        "target_system": "namami-gange-intelligence (GOUDHA Knowledge Intelligence Layer)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_reference": "GRAPH_SCHEMA.md v1.0",
        "note": "All confidence and validation_status values are placeholders pending SVACS validation on Ankita's side. Geometry underlying these nodes is representative, not survey-grade -- see COVERAGE_MATRIX_AND_GAP_ANALYSIS.md."
    },
    "nodes": nodes,
    "edges": edges
}

with open("knowledge_graph_export.json", "w") as f:
    json.dump(kg_export, f, indent=2)

print(f"Knowledge Graph export generated: {len(nodes)} nodes, {len(edges)} edges")
print("Saved to knowledge_graph_export.json")

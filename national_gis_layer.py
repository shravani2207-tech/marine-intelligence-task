import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
import json
import os
from datetime import datetime, timezone

print("===============================================================")
print("SHRAVANI'S NATIONAL GEOSPATIAL INTELLIGENCE LAYER RUNNING")
print("===============================================================")

GEO_CRS = "EPSG:4326"

# =====================================================================
# PHASE 1: NATIONAL DATASET EXPANSION (All 10 Core River Basins)
# =====================================================================
print("\n[Phase 1] Initializing Multi-River Spatial Data Fabric...")

river_coordinates = {
    "Ganga": [(78.0, 30.0), (79.5, 27.8), (80.0, 26.0), (82.0, 25.5), (84.0, 25.0), (86.5, 23.5), (88.0, 22.0)],
    "Yamuna": [(77.0, 31.0), (77.2, 28.6), (79.0, 27.0), (81.8, 25.4)],
    "Brahmaputra": [(95.5, 29.0), (94.0, 28.0), (91.0, 26.0), (92.5, 25.5), (90.0, 25.2)],
    "Godavari": [(73.5, 19.9), (76.0, 19.3), (79.0, 18.5), (81.0, 17.5), (81.7, 16.7)],
    "Krishna": [(73.6, 17.9), (75.5, 16.8), (77.0, 16.0), (79.0, 16.0), (80.5, 15.8)],
    "Narmada": [(81.7, 22.7), (78.5, 22.5), (76.0, 22.2), (73.8, 21.8), (72.8, 21.6)],
    "Tapi": [(78.0, 21.5), (76.2, 21.8), (74.0, 21.3), (72.7, 21.1)],
    "Mahanadi": [(82.0, 20.5), (81.8, 20.2), (83.5, 20.9), (84.0, 21.5), (85.5, 20.6), (86.7, 20.3)],
    "Kaveri": [(75.9, 12.4), (76.9, 12.0), (78.0, 11.5), (79.0, 11.2), (79.8, 11.1)],
    "Indus_Basin": [(78.0, 34.5), (75.0, 34.0), (73.0, 32.5), (71.5, 31.5), (71.0, 31.0)]
}

river_list = []
geometry_lines = []
for name, coords in river_coordinates.items():
    river_list.append(name)
    geometry_lines.append(LineString(coords))

gdf_rivers = gpd.GeoDataFrame({
    'river_id': [f"RIV_{name.upper()[:3]}_001" for name in river_list],
    'river_name': river_list,
    'geometry': geometry_lines
}, crs=GEO_CRS)

print(f"Created base map for {len(gdf_rivers)} National River Networks.")

waterway_list = [
    {"nw_id": "NW-1", "name": "Ganga (Haldia-Allahabad)", "river": "Ganga", "coords": [(88.1, 22.0), (81.8, 25.4)]},
    {"nw_id": "NW-2", "name": "Brahmaputra (Sadiya-Dhubri)", "river": "Brahmaputra", "coords": [(95.4, 27.8), (89.9, 26.0)]},
    {"nw_id": "NW-3", "name": "West Coast Canal (Kollam-Kottapuram)", "river": "Kerala Backwaters", "coords": [(76.6, 8.9), (76.2, 10.1)]},
    {"nw_id": "NW-4", "name": "Godavari-Krishna Canal System", "river": "Godavari-Krishna", "coords": [(81.7, 16.7), (80.5, 15.8)]},
    {"nw_id": "NW-16", "name": "Barak River", "river": "Barak", "coords": [(93.0, 24.8), (92.5, 24.3)]},
]
gdf_waterways = gpd.GeoDataFrame({
    'nw_id': [w['nw_id'] for w in waterway_list],
    'nw_name': [w['name'] for w in waterway_list],
    'associated_river': [w['river'] for w in waterway_list],
    'geometry': [LineString(w['coords']) for w in waterway_list]
}, crs=GEO_CRS)
print(f"Registered {len(gdf_waterways)} National Waterway segments (representative subset).")

infra_records = [
    {"id": "INFRA_01", "name": "Farakka Barrage", "type": "Barrage", "river": "Ganga", "pt": (88.0, 24.8)},
    {"id": "INFRA_02", "name": "Kolkata Port Terminal", "type": "Port", "river": "Ganga", "pt": (88.0, 22.0)},
    {"id": "INFRA_03", "name": "Varanasi Multi-Modal Terminal", "type": "Inland Terminal", "river": "Ganga", "pt": (83.0, 25.3)},
    {"id": "INFRA_04", "name": "Bijnor Barrage", "type": "Barrage", "river": "Ganga", "pt": (78.1, 29.4)},
    {"id": "INFRA_05", "name": "Wazirabad Barrage", "type": "Barrage", "river": "Yamuna", "pt": (77.2, 28.6)},
    {"id": "INFRA_06", "name": "Hathnikund Barrage", "type": "Barrage", "river": "Yamuna", "pt": (77.3, 30.3)},
    {"id": "INFRA_07", "name": "Guwahati Inland Jetty", "type": "Jetty", "river": "Brahmaputra", "pt": (91.7, 26.2)},
    {"id": "INFRA_08", "name": "Pandu Port", "type": "Port", "river": "Brahmaputra", "pt": (91.7, 26.2)},
    {"id": "INFRA_09", "name": "Dowleswaram Barrage", "type": "Barrage", "river": "Godavari", "pt": (81.8, 16.9)},
    {"id": "INFRA_10", "name": "Polavaram Dam (under construction)", "type": "Dam", "river": "Godavari", "pt": (81.6, 17.2)},
    {"id": "INFRA_11", "name": "Prakasam Barrage", "type": "Barrage", "river": "Krishna", "pt": (80.6, 16.5)},
    {"id": "INFRA_12", "name": "Nagarjuna Sagar Dam", "type": "Dam", "river": "Krishna", "pt": (79.3, 16.6)},
    {"id": "INFRA_13", "name": "Sardar Sarovar Dam", "type": "Dam", "river": "Narmada", "pt": (73.7, 21.8)},
    {"id": "INFRA_14", "name": "Bharuch Bridge Corridor", "type": "Bridge", "river": "Narmada", "pt": (72.9, 21.7)},
    {"id": "INFRA_15", "name": "Ukai Dam", "type": "Dam", "river": "Tapi", "pt": (73.6, 21.2)},
    {"id": "INFRA_16", "name": "Hirakud Dam", "type": "Dam", "river": "Mahanadi", "pt": (83.9, 21.5)},
    {"id": "INFRA_17", "name": "Paradip Port", "type": "Port", "river": "Mahanadi", "pt": (86.7, 20.3)},
    {"id": "INFRA_18", "name": "Krishna Raja Sagara Dam", "type": "Dam", "river": "Kaveri", "pt": (76.6, 12.4)},
    {"id": "INFRA_19", "name": "Mettur Dam", "type": "Dam", "river": "Kaveri", "pt": (77.8, 11.8)},
    {"id": "INFRA_20", "name": "Leh Bridge Corridor", "type": "Bridge", "river": "Indus_Basin", "pt": (77.6, 34.2)},
]

gdf_infra = gpd.GeoDataFrame({
    'infra_id': [r['id'] for r in infra_records],
    'name': [r['name'] for r in infra_records],
    'type': [r['type'] for r in infra_records],
    'associated_river': [r['river'] for r in infra_records],
    'geometry': [Point(r['pt']) for r in infra_records]
}, crs=GEO_CRS)

print(f"Placed {len(gdf_infra)} infrastructure nodes into the spatial fabric (dams, barrages, ports, jetties, bridges, terminals).")

print("\n[Phase 2] Computing Hydrological & Topology Relationships for all rivers...")

topology_map = []
for river_name in river_list:
    river_geom = gdf_rivers[gdf_rivers['river_name'] == river_name].geometry.iloc[0]
    river_infra = gdf_infra[gdf_infra['associated_river'] == river_name]
    if len(river_infra) < 2:
        continue
    positions = []
    for _, row in river_infra.iterrows():
        pos = river_geom.project(row.geometry, normalized=True)
        positions.append((pos, row['name']))
    positions.sort(key=lambda x: x[0])
    for i in range(len(positions) - 1):
        topology_map.append({
            "river": river_name,
            "upstream_node": positions[i][1],
            "downstream_node": positions[i + 1][1],
            "impact": f"Changes at {positions[i][1]} directly affect downstream conditions at {positions[i + 1][1]}."
        })

print(f"River topology and directional dependency map generated for {len(set(t['river'] for t in topology_map))} rivers ({len(topology_map)} relationships).")

flood_risk_overlay = [
    {"river": "Ganga", "flood_risk": "HIGH", "basis": "Historic monsoon flooding, Bihar/Bengal floodplain"},
    {"river": "Brahmaputra", "flood_risk": "HIGH", "basis": "Annual monsoon flooding, Assam floodplain"},
    {"river": "Yamuna", "flood_risk": "MEDIUM", "basis": "Delhi-NCR urban floodplain encroachment"},
    {"river": "Godavari", "flood_risk": "MEDIUM", "basis": "Seasonal delta flooding, Andhra Pradesh"},
    {"river": "Krishna", "flood_risk": "MEDIUM", "basis": "Seasonal delta flooding"},
    {"river": "Narmada", "flood_risk": "LOW", "basis": "Dam-regulated flow, Sardar Sarovar"},
    {"river": "Tapi", "flood_risk": "MEDIUM", "basis": "Surat urban floodplain, historic 2006 flood"},
    {"river": "Mahanadi", "flood_risk": "HIGH", "basis": "Odisha delta flooding, cyclone exposure"},
    {"river": "Kaveri", "flood_risk": "LOW", "basis": "Dam-regulated flow, interstate water sharing"},
    {"river": "Indus_Basin", "flood_risk": "LOW", "basis": "High-altitude, glacier-fed, limited monsoon exposure"},
]

navigation_corridors = [
    {"corridor": "NW-1 Ganga Corridor", "connects": ["Kolkata Port Terminal", "Varanasi Multi-Modal Terminal"], "cargo_type": "Bulk, container"},
    {"corridor": "NW-2 Brahmaputra Corridor", "connects": ["Pandu Port", "Guwahati Inland Jetty"], "cargo_type": "Bulk, passenger"},
    {"corridor": "Mahanadi-Paradip Corridor", "connects": ["Hirakud Dam", "Paradip Port"], "cargo_type": "Coal, bulk minerals"},
]

print("Flood-risk and navigation-corridor overlays generated.")

print("\n[Phase 3 & 4] Running Integrity Checks & Schema Formatting...")

validation_results = {
    "crs_consistency": bool(gdf_rivers.crs == GEO_CRS and gdf_infra.crs == GEO_CRS and gdf_waterways.crs == GEO_CRS),
    "river_count": len(gdf_rivers),
    "expected_river_count": 10,
    "multi_river_coverage": len(gdf_rivers) == 10,
    "infra_count": len(gdf_infra),
    "topology_relationships": len(topology_map),
    "rivers_with_topology": len(set(t['river'] for t in topology_map)),
    "waterway_segments": len(gdf_waterways),
    "geometry_validity": bool(gdf_rivers.geometry.is_valid.all() and gdf_infra.geometry.is_valid.all()),
}

for check, result in validation_results.items():
    status = "PASSED" if (result is True or (isinstance(result, int) and result > 0)) else "REVIEW"
    print(f"  {check}: {result} [{status}]")

master_db_export = {
    "layer_metadata": {
        "owner": "Shravani (National Geospatial Intelligence Layer)",
        "version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spatial_reproducibility": True,
        "crs": GEO_CRS,
        "coverage_note": "Representative multi-river prototype dataset. Geometry is approximate, not survey-grade. See docs/GAP_ANALYSIS.md for production data-acquisition plan."
    },
    "river_network": json.loads(gdf_rivers.to_json()),
    "national_waterways": json.loads(gdf_waterways.to_json()),
    "infrastructure_matrix": json.loads(gdf_infra.to_json()),
    "provenance_topology": topology_map,
    "flood_risk_overlay": flood_risk_overlay,
    "navigation_corridors": navigation_corridors,
    "validation_results": validation_results
}

with open("spatial_truth_export.json", "w") as f:
    json.dump(master_db_export, f, indent=2)

print("\nData convergence successful. Export saved to 'spatial_truth_export.json'.")
print(f"PLATFORM METRICS: {len(gdf_rivers)} rivers, {len(gdf_infra)} infra nodes, {len(gdf_waterways)} waterway segments, {len(topology_map)} topology relationships.")
print("===============================================================")

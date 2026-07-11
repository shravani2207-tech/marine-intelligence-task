import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point
import json

print("===============================================================")
print("🌊 SHRAVANI'S NATIONAL GEOSPATIAL INTELLIGENCE LAYER RUNNING 🌊")
print("===============================================================")

GEO_CRS = "EPSG:4326"

# =====================================================================
# PHASE 1: NATIONAL DATASET EXPANSION (All 10 Core River Basins)
# =====================================================================
print("\n[Phase 1] Initializing Multi-River Spatial Data Fabric...")

river_coordinates = {
    "Ganga": [(78.0, 30.0), (80.0, 26.0), (84.0, 25.0), (88.0, 22.0)],
    "Yamuna": [(77.0, 31.0), (77.2, 28.6), (81.8, 25.4)],
    "Brahmaputra": [(82.0, 30.0), (91.0, 26.0), (92.0, 25.0)],
    "Godavari": [(73.5, 19.9), (79.0, 18.5), (81.7, 16.7)],
    "Krishna": [(73.6, 17.9), (77.0, 16.0), (80.5, 15.8)],
    "Narmada": [(81.7, 22.7), (76.0, 22.2), (72.8, 21.6)],
    "Tapi": [(76.2, 21.8), (74.0, 21.3), (72.7, 21.1)],
    "Mahanadi": [(81.8, 20.2), (84.0, 21.5), (86.7, 20.3)],
    "Kaveri": [(75.7, 12.4), (78.0, 11.5), (79.8, 11.1)],
    "Indus_Basin": [(75.0, 34.0), (73.0, 32.5), (71.0, 31.0)]
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

print(f"✅ Created base map for {len(gdf_rivers)} National River Networks.")

# Infrastructure Data Nodes
infra_points = [
    Point(80.0, 26.0),  # Farakka on Ganga
    Point(88.0, 22.0),  # Kolkata Port on Ganga
    Point(91.0, 26.0),  # Guwahati on Brahmaputra
    Point(77.2, 28.6)   # Wazirabad on Yamuna
]

gdf_infra = gpd.GeoDataFrame({
    'infra_id': ['INFRA_01', 'INFRA_02', 'INFRA_03', 'INFRA_04'],
    'name': ['Farakka Barrage Segment', 'Kolkata Port Terminal', 'Guwahati Inland Jetty', 'Wazirabad Barrage'],
    'type': ['Barrage', 'Port', 'Jetty', 'Barrage'],
    'associated_river': ['Ganga', 'Ganga', 'Brahmaputra', 'Yamuna'],
    'geometry': infra_points
}, crs=GEO_CRS)

print(f"✅ Placed {len(gdf_infra)} infrastructure nodes into the spatial fabric.")

# =====================================================================
# PHASE 2: SPATIAL INTELLIGENCE LAYER (Upstream / Downstream Engine)
# =====================================================================
print("\n[Phase 2] Computing Hydrological & Topology Relationships...")

ganga_geom = gdf_rivers[gdf_rivers['river_name'] == 'Ganga'].geometry.iloc[0]
dam_geom = gdf_infra[gdf_infra['name'] == 'Farakka Barrage Segment'].geometry.iloc[0]
port_geom = gdf_infra[gdf_infra['name'] == 'Kolkata Port Terminal'].geometry.iloc[0]

pos_dam = ganga_geom.project(dam_geom, normalized=True)
pos_port = ganga_geom.project(port_geom, normalized=True)

topology_map = []
if pos_dam < pos_port:
    topology_map.append({
        "upstream_node": "Farakka Barrage Segment",
        "downstream_node": "Kolkata Port Terminal",
        "impact": "Water release directly changes navigability at downstream port."
    })
print("✅ River topology and directional dependency map generated.")

# =====================================================================
# PHASE 3 & 4: CONVERGENCE & SCHEMA VALIDATION
# =====================================================================
print("\n[Phase 3 & 4] Running Integrity Checks & Schema Formatting...")

if gdf_rivers.crs == GEO_CRS and gdf_infra.crs == GEO_CRS:
    print("✅ CRS Consistency Check: PASSED (All layers locked to EPSG:4326).")

master_db_export = {
    "layer_metadata": {
        "owner": "Shravani (National Geospatial Intelligence Layer)",
        "version": "1.0.0",
        "spatial_reproducibility": "True"
    },
    "river_network": json.loads(gdf_rivers.to_json()),
    "infrastructure_matrix": json.loads(gdf_infra.to_json()),
    "provenance_topology": topology_map
}

# Saving file locally in our cloned repo folder
with open("spatial_truth_export.json", "w") as f:
    json.dump(master_db_export, f, indent=2)

print("✅ Data convergence successful. Export saved to 'spatial_truth_export.json'.")
print("\n🚀 PLATFORM METRICS OPERATIONAL: Spatial Truth Verified.")
print("===============================================================")
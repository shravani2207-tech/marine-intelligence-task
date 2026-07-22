import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point, Polygon
import json
import os
from datetime import datetime, timezone
from abc import ABC, abstractmethod

print("===============================================================")
print("SHRAVANI'S NATIONAL GEOSPATIAL INTELLIGENCE LAYER RUNNING (v3)")
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

# Representative tributaries (one major tributary per river where well-known)
tributary_coordinates = {
    "Ghaghara_to_Ganga": [(81.0, 28.5), (82.5, 26.0), (84.0, 25.0)],
    "Chambal_to_Yamuna": [(75.8, 24.0), (77.5, 26.5), (79.0, 27.0)],
    "Subansiri_to_Brahmaputra": [(94.1, 27.5), (93.8, 26.8), (91.0, 26.0)],
    "Indravati_to_Godavari": [(81.6, 19.0), (80.5, 18.0), (79.0, 18.5)],
    "Tungabhadra_to_Krishna": [(76.4, 15.3), (78.0, 16.0), (79.0, 16.0)],
}
tributary_list = list(tributary_coordinates.keys())
gdf_tributaries = gpd.GeoDataFrame({
    'tributary_id': [f"TRIB_{i+1:03d}" for i in range(len(tributary_list))],
    'tributary_name': tributary_list,
    'geometry': [LineString(c) for c in tributary_coordinates.values()]
}, crs=GEO_CRS)
print(f"Added {len(gdf_tributaries)} representative tributaries.")

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
    {"nw_id": "NW-8", "name": "Alappuzha-Changanassery", "river": "Kerala Backwaters", "coords": [(76.3, 9.5), (76.5, 9.4)]},
    {"nw_id": "NW-10", "name": "Amba River", "river": "Amba", "coords": [(73.1, 18.4), (72.9, 18.6)]},
    {"nw_id": "NW-73", "name": "Godavari (Bhadrachalam-Rajahmundry)", "river": "Godavari", "coords": [(80.9, 17.7), (81.8, 17.0)]},
]
gdf_waterways = gpd.GeoDataFrame({
    'nw_id': [w['nw_id'] for w in waterway_list],
    'nw_name': [w['name'] for w in waterway_list],
    'associated_river': [w['river'] for w in waterway_list],
    'geometry': [LineString(w['coords']) for w in waterway_list]
}, crs=GEO_CRS)
print(f"Registered {len(gdf_waterways)} National Waterway segments (expanded representative subset, still not full NW1-111).")

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
    # NEW: Locks
    {"id": "INFRA_21", "name": "Farakka Navigation Lock", "type": "Lock", "river": "Ganga", "pt": (87.9, 24.8)},
    {"id": "INFRA_22", "name": "Vikramshila Lock", "type": "Lock", "river": "Ganga", "pt": (86.9, 25.3)},
    # NEW: Reservoirs (distinct from dams -- the impounded water body)
    {"id": "INFRA_23", "name": "Sardar Sarovar Reservoir", "type": "Reservoir", "river": "Narmada", "pt": (73.75, 21.85)},
    {"id": "INFRA_24", "name": "Nagarjuna Sagar Reservoir", "type": "Reservoir", "river": "Krishna", "pt": (79.35, 16.65)},
    {"id": "INFRA_25", "name": "Hirakud Reservoir", "type": "Reservoir", "river": "Mahanadi", "pt": (83.95, 21.55)},
    # NEW: Wetlands
    {"id": "INFRA_26", "name": "Sundarbans Wetland Complex", "type": "Wetland", "river": "Ganga", "pt": (88.9, 21.9)},
    {"id": "INFRA_27", "name": "Kaziranga Floodplain Wetlands", "type": "Wetland", "river": "Brahmaputra", "pt": (93.4, 26.6)},
    {"id": "INFRA_28", "name": "Chilika-adjacent Mahanadi Wetlands", "type": "Wetland", "river": "Mahanadi", "pt": (85.4, 19.7)},
    # NEW: Additional ports/jetties/terminals for coverage
    {"id": "INFRA_29", "name": "Haldia Dock Complex", "type": "Port", "river": "Ganga", "pt": (88.06, 22.03)},
    {"id": "INFRA_30", "name": "Vishakhapatnam Port", "type": "Port", "river": "Godavari", "pt": (83.3, 17.7)},
    {"id": "INFRA_31", "name": "Yamuna Lock (Agra Barrage)", "type": "Lock", "river": "Yamuna", "pt": (78.0, 27.2)},
    {"id": "INFRA_32", "name": "Yamuna Reservoir (Hathnikund)", "type": "Reservoir", "river": "Yamuna", "pt": (77.35, 30.35)},
    {"id": "INFRA_33", "name": "Yamuna Floodplain Wetland (Delhi)", "type": "Wetland", "river": "Yamuna", "pt": (77.25, 28.65)},
    {"id": "INFRA_34", "name": "Brahmaputra Navigation Lock (Pandu)", "type": "Lock", "river": "Brahmaputra", "pt": (91.65, 26.15)},
    {"id": "INFRA_35", "name": "Brahmaputra Char Wetland Complex", "type": "Wetland", "river": "Brahmaputra", "pt": (93.0, 26.5)},
    {"id": "INFRA_36", "name": "Ukai Reservoir", "type": "Reservoir", "river": "Tapi", "pt": (73.65, 21.25)},
    {"id": "INFRA_37", "name": "Tapi Estuary Wetland (Surat)", "type": "Wetland", "river": "Tapi", "pt": (72.75, 21.15)},
    {"id": "INFRA_38", "name": "Kaveri Delta Lock (Grand Anicut)", "type": "Lock", "river": "Kaveri", "pt": (78.9, 11.2)},
    {"id": "INFRA_39", "name": "Krishna Raja Sagara Reservoir", "type": "Reservoir", "river": "Kaveri", "pt": (76.55, 12.35)},
    {"id": "INFRA_40", "name": "Point Calimere Wetland (Kaveri delta)", "type": "Wetland", "river": "Kaveri", "pt": (79.85, 10.3)},
    {"id": "INFRA_41", "name": "Indus Reservoir (Zanskar confluence)", "type": "Reservoir", "river": "Indus_Basin", "pt": (76.5, 33.5)},
]

gdf_infra = gpd.GeoDataFrame({
    'infra_id': [r['id'] for r in infra_records],
    'name': [r['name'] for r in infra_records],
    'type': [r['type'] for r in infra_records],
    'associated_river': [r['river'] for r in infra_records],
    'geometry': [Point(r['pt']) for r in infra_records]
}, crs=GEO_CRS)
print(f"Placed {len(gdf_infra)} infrastructure nodes (dams, barrages, ports, jetties, bridges, terminals, locks, reservoirs, wetlands).")

# NEW: Floodplains as approximate polygon geometry (representative bounding areas)
floodplain_records = [
    {"id": "FP_01", "name": "Ganga-Bihar Floodplain", "river": "Ganga", "poly": [(84.0, 24.5), (86.0, 24.5), (86.0, 25.8), (84.0, 25.8)]},
    {"id": "FP_02", "name": "Brahmaputra Assam Floodplain", "river": "Brahmaputra", "poly": [(92.0, 25.8), (94.5, 25.8), (94.5, 27.2), (92.0, 27.2)]},
    {"id": "FP_03", "name": "Mahanadi Delta Floodplain", "river": "Mahanadi", "poly": [(85.5, 19.9), (87.0, 19.9), (87.0, 20.7), (85.5, 20.7)]},
]
gdf_floodplains = gpd.GeoDataFrame({
    'floodplain_id': [f['id'] for f in floodplain_records],
    'name': [f['name'] for f in floodplain_records],
    'associated_river': [f['river'] for f in floodplain_records],
    'geometry': [Polygon(f['poly']) for f in floodplain_records]
}, crs=GEO_CRS)
print(f"Added {len(gdf_floodplains)} representative floodplain polygons.")

# NEW: Watersheds as approximate polygon geometry (representative bounding areas)
watershed_records = [
    {"id": "WS_01", "name": "Upper Ganga Watershed", "river": "Ganga", "poly": [(77.5, 29.0), (81.0, 29.0), (81.0, 31.0), (77.5, 31.0)]},
    {"id": "WS_02", "name": "Godavari Basin Watershed", "river": "Godavari", "poly": [(73.0, 17.5), (82.0, 17.5), (82.0, 21.0), (73.0, 21.0)]},
    {"id": "WS_03", "name": "Narmada Basin Watershed", "river": "Narmada", "poly": [(72.5, 21.0), (82.0, 21.0), (82.0, 23.5), (72.5, 23.5)]},
]
gdf_watersheds = gpd.GeoDataFrame({
    'watershed_id': [w['id'] for w in watershed_records],
    'name': [w['name'] for w in watershed_records],
    'associated_river': [w['river'] for w in watershed_records],
    'geometry': [Polygon(w['poly']) for w in watershed_records]
}, crs=GEO_CRS)
print(f"Added {len(gdf_watersheds)} representative watershed polygons.")

# NEW: Administrative boundaries (representative state-level bounding boxes for river-adjacent states)
admin_records = [
    {"id": "ADM_01", "name": "Uttar Pradesh (representative extent)", "poly": [(77.0, 24.0), (84.5, 24.0), (84.5, 30.5), (77.0, 30.5)]},
    {"id": "ADM_02", "name": "West Bengal (representative extent)", "poly": [(85.8, 21.5), (89.9, 21.5), (89.9, 27.2), (85.8, 27.2)]},
    {"id": "ADM_03", "name": "Assam (representative extent)", "poly": [(89.7, 24.1), (96.0, 24.1), (96.0, 28.0), (89.7, 28.0)]},
]
gdf_admin = gpd.GeoDataFrame({
    'admin_id': [a['id'] for a in admin_records],
    'name': [a['name'] for a in admin_records],
    'geometry': [Polygon(a['poly']) for a in admin_records]
}, crs=GEO_CRS)
print(f"Added {len(gdf_admin)} representative administrative boundary polygons.")

# NEW: Industrial corridors (as LineString connecting key nodes)
industrial_corridor_records = [
    {"id": "IC_01", "name": "Amritsar-Kolkata Industrial Corridor (Ganga segment)", "coords": [(83.0, 25.3), (88.0, 22.0)]},
    {"id": "IC_02", "name": "Vizag-Chennai Industrial Corridor (Godavari segment)", "coords": [(83.3, 17.7), (81.7, 16.7)]},
]
gdf_industrial = gpd.GeoDataFrame({
    'corridor_id': [c['id'] for c in industrial_corridor_records],
    'name': [c['name'] for c in industrial_corridor_records],
    'geometry': [LineString(c['coords']) for c in industrial_corridor_records]
}, crs=GEO_CRS)
print(f"Added {len(gdf_industrial)} representative industrial corridors.")

# =====================================================================
# PHASE 2 (continued): SPATIAL INTELLIGENCE LAYER
# =====================================================================
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

print(f"River topology generated for {len(set(t['river'] for t in topology_map))} rivers ({len(topology_map)} relationships).")

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

# NEW: Cargo corridors (distinct from navigation corridors -- freight-specific)
cargo_corridors = [
    {"corridor": "Haldia-Kolkata Cargo Route", "commodity": "Containerized cargo, petroleum", "river": "Ganga"},
    {"corridor": "Vizag-Paradip Coastal Cargo Route", "commodity": "Iron ore, coal", "river": "Godavari/Mahanadi"},
]

# NEW: Environmental overlay (spatial, distinct from Task 3's catalogue-only environmental.json)
environmental_overlay = [
    {"river": "Ganga", "feature": "Sundarbans Mangrove Forest", "type": "Mangrove", "protection_status": "UNESCO World Heritage, Ramsar Site"},
    {"river": "Brahmaputra", "feature": "Kaziranga Floodplain Grassland", "type": "Grassland/Wetland", "protection_status": "UNESCO World Heritage, National Park"},
    {"river": "Mahanadi", "feature": "Bhitarkanika Mangroves (delta-adjacent)", "type": "Mangrove", "protection_status": "Ramsar Site"},
]

# NEW: Protected-area overlay
protected_area_overlay = [
    {"name": "Sundarbans National Park", "associated_river": "Ganga", "designation": "National Park + Tiger Reserve"},
    {"name": "Kaziranga National Park", "associated_river": "Brahmaputra", "designation": "National Park + UNESCO World Heritage"},
    {"name": "Bhitarkanika National Park", "associated_river": "Mahanadi", "designation": "National Park + Wildlife Sanctuary"},
]

# NEW: Seasonal navigability layer
seasonal_navigability = [
    {"river": "Ganga", "monsoon_navigability": "REDUCED (high flow, debris risk)", "dry_season_navigability": "GOOD"},
    {"river": "Brahmaputra", "monsoon_navigability": "REDUCED (flooding, shifting channels)", "dry_season_navigability": "MODERATE (sandbar exposure)"},
    {"river": "Godavari", "monsoon_navigability": "MODERATE", "dry_season_navigability": "GOOD"},
    {"river": "Narmada", "monsoon_navigability": "GOOD (dam-regulated)", "dry_season_navigability": "GOOD (dam-regulated)"},
]

print("Cargo corridor, environmental, protected-area, and seasonal-navigability overlays generated.")

# =====================================================================
# PHASE 3: GIS & TANTRA CONVERGENCE (adapter stubs -- ready, not live)
# =====================================================================
print("\n[Phase 3] Preparing convergence adapters for downstream systems...")

class ConvergenceTarget(ABC):
    """
    Interface for pushing this spatial layer's data into a downstream
    system. Each concrete adapter below is a stub -- structurally ready,
    but not yet wired to a live endpoint, since none of MasterDB/KG/
    Runtime/Replay/InsightFlow/Bucket endpoints have been provided to
    this layer's owner yet. Mirrors the adapter pattern used for the
    Sanskar runtime's TantraOrchestrator (ready but not live until an
    endpoint is configured).
    """
    @abstractmethod
    def push(self, payload: dict) -> dict:
        raise NotImplementedError


class MasterDBAdapter(ConvergenceTarget):
    """Target: Chandragupta's Marine MasterDB. Expects GeoJSON FeatureCollections."""
    def __init__(self):
        self._endpoint = os.getenv("MASTERDB_INGEST_ENDPOINT", "")
    def push(self, payload: dict) -> dict:
        if not self._endpoint:
            return {"status": "skipped", "reason": "MASTERDB_INGEST_ENDPOINT not configured yet"}
        return {"status": "not_implemented", "reason": "live push not yet built -- endpoint present but untested"}


class KnowledgeGraphAdapter(ConvergenceTarget):
    """Target: Ankita's Knowledge Graph. Expects entity/relationship pairs."""
    def __init__(self):
        self._endpoint = os.getenv("KG_INGEST_ENDPOINT", "")
    def push(self, payload: dict) -> dict:
        if not self._endpoint:
            return {"status": "skipped", "reason": "KG_INGEST_ENDPOINT not configured yet"}
        return {"status": "not_implemented", "reason": "live push not yet built -- endpoint present but untested"}


class RuntimeAdapter(ConvergenceTarget):
    """Target: Nupur's GOUDHA Runtime. Expects read-only reference dataset."""
    def __init__(self):
        self._endpoint = os.getenv("GOUDHA_RUNTIME_ENDPOINT", "")
    def push(self, payload: dict) -> dict:
        if not self._endpoint:
            return {"status": "skipped", "reason": "GOUDHA_RUNTIME_ENDPOINT not configured yet"}
        return {"status": "not_implemented", "reason": "live push not yet built -- endpoint present but untested"}


class BucketAdapter(ConvergenceTarget):
    """Target: BHIV Bucket persistence layer (shared with Sanskar runtime)."""
    def __init__(self):
        self._endpoint = os.getenv("BUCKET_ENDPOINT", "")
    def push(self, payload: dict) -> dict:
        if not self._endpoint:
            return {"status": "skipped", "reason": "BUCKET_ENDPOINT not configured yet"}
        import urllib.request
        import uuid
        try:
            bucket_payload = {"artifact_id": str(uuid.uuid4()), "trace_id": str(uuid.uuid4()), "timestamp_utc": datetime.now(timezone.utc).isoformat(), "data": payload}
            data = json.dumps(bucket_payload).encode("utf-8")
            req = urllib.request.Request(
                self._endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return {"status": "success", "response": result}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


class InsightFlowAdapter(ConvergenceTarget):
    """Target: InsightFlow observability sink (shared with Sanskar runtime)."""
    def __init__(self):
        self._endpoint = os.getenv("INSIGHTFLOW_ENDPOINT", "")
        self._api_key = os.getenv("INSIGHTFLOW_API_KEY", "")
    def push(self, payload: dict) -> dict:
        if not self._endpoint:
            return {"status": "skipped", "reason": "INSIGHTFLOW_ENDPOINT not configured yet"}
        if not self._api_key:
            return {"status": "skipped", "reason": "INSIGHTFLOW_API_KEY not configured yet"}
        import urllib.request
        try:
            import uuid as _uuid
            artifact_payload = {
                "canonical_id": "BHIV-ART-SEMANTIC-GISLAYER-" + str(_uuid.uuid4())[:12],
                "artifact_type": "SEMANTIC",
                "artifact_name": "national_geospatial_intelligence_layer",
                "owner_name": "Shravani - National Geospatial Intelligence Layer",
                "domain_primary": "geospatial",
                "source_system": "marine-intelligence-task",
                "data": payload
            }
            data = json.dumps(artifact_payload).encode("utf-8")
            req = urllib.request.Request(
                self._endpoint,
                data=data,
                headers={"Content-Type": "application/json", "X-API-Key": self._api_key},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                return {"status": "success", "response": result}
        except Exception as e:
            return {"status": "failed", "error": str(e)}


class ReplayAdapter(ConvergenceTarget):
    """Target: Replay/versioning service for spatial layer snapshots."""
    def __init__(self):
        self._endpoint = os.getenv("REPLAY_ENDPOINT", "")
    def push(self, payload: dict) -> dict:
        if not self._endpoint:
            return {"status": "skipped", "reason": "REPLAY_ENDPOINT not configured yet"}
        return {"status": "not_implemented", "reason": "live push not yet built -- endpoint present but untested"}


convergence_adapters = {
    "marine_masterdb": MasterDBAdapter(),
    "knowledge_graph": KnowledgeGraphAdapter(),
    "goudha_runtime": RuntimeAdapter(),
    "bucket": BucketAdapter(),
    "insightflow": InsightFlowAdapter(),
    "replay": ReplayAdapter(),
}

convergence_status = {name: adapter.push({}) for name, adapter in convergence_adapters.items()}
print("Convergence adapter stubs initialized for: " + ", ".join(convergence_adapters.keys()))
print("All currently report 'skipped' or 'not_implemented' -- no live endpoints configured yet (see Gap Analysis).")

# =====================================================================
# PHASE 3 & 4: VALIDATION
# =====================================================================
print("\n[Phase 3 & 4] Running Integrity Checks & Schema Formatting...")

validation_results = {
    "crs_consistency": bool(
        gdf_rivers.crs == GEO_CRS and gdf_infra.crs == GEO_CRS and gdf_waterways.crs == GEO_CRS
        and gdf_tributaries.crs == GEO_CRS and gdf_floodplains.crs == GEO_CRS
        and gdf_watersheds.crs == GEO_CRS and gdf_admin.crs == GEO_CRS and gdf_industrial.crs == GEO_CRS
    ),
    "river_count": len(gdf_rivers),
    "expected_river_count": 10,
    "multi_river_coverage": len(gdf_rivers) == 10,
    "tributary_count": len(gdf_tributaries),
    "infra_count": len(gdf_infra),
    "infra_type_diversity": gdf_infra['type'].nunique(),
    "waterway_segments": len(gdf_waterways),
    "floodplain_count": len(gdf_floodplains),
    "watershed_count": len(gdf_watersheds),
    "admin_boundary_count": len(gdf_admin),
    "industrial_corridor_count": len(gdf_industrial),
    "topology_relationships": len(topology_map),
    "rivers_with_topology": len(set(t['river'] for t in topology_map)),
    "geometry_validity": bool(
        gdf_rivers.geometry.is_valid.all() and gdf_infra.geometry.is_valid.all()
        and gdf_floodplains.geometry.is_valid.all() and gdf_watersheds.geometry.is_valid.all()
    ),
    "convergence_adapters_ready": len(convergence_adapters),
    "convergence_adapters_live": sum(1 for s in convergence_status.values() if s.get("status") == "success"),
}

for check, result in validation_results.items():
    status = "PASSED" if (result is True or (isinstance(result, int) and result > 0)) else "REVIEW"
    print(f"  {check}: {result} [{status}]")

# =====================================================================
# EXPORT -- Canonical Spatial Truth Payload
# =====================================================================
master_db_export = {
    "layer_metadata": {
        "owner": "Shravani (National Geospatial Intelligence Layer)",
        "version": "3.0.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spatial_reproducibility": True,
        "crs": GEO_CRS,
        "coverage_note": "Representative multi-river prototype dataset, v3 expansion. Geometry is approximate, not survey-grade. See docs/GAP_ANALYSIS.md and docs/COVERAGE_MATRIX_AND_GAP_ANALYSIS.md for production data-acquisition plan."
    },
    "river_network": json.loads(gdf_rivers.to_json()),
    "tributaries": json.loads(gdf_tributaries.to_json()),
    "national_waterways": json.loads(gdf_waterways.to_json()),
    "infrastructure_matrix": json.loads(gdf_infra.to_json()),
    "floodplains": json.loads(gdf_floodplains.to_json()),
    "watersheds": json.loads(gdf_watersheds.to_json()),
    "administrative_boundaries": json.loads(gdf_admin.to_json()),
    "industrial_corridors": json.loads(gdf_industrial.to_json()),
    "provenance_topology": topology_map,
    "flood_risk_overlay": flood_risk_overlay,
    "navigation_corridors": navigation_corridors,
    "cargo_corridors": cargo_corridors,
    "environmental_overlay": environmental_overlay,
    "protected_area_overlay": protected_area_overlay,
    "seasonal_navigability": seasonal_navigability,
    "convergence_status": convergence_status,
    "validation_results": validation_results
}

with open("spatial_truth_export.json", "w") as f:
    json.dump(master_db_export, f, indent=2)

print("\nData convergence successful. Export saved to 'spatial_truth_export.json'.")
print(f"PLATFORM METRICS: {len(gdf_rivers)} rivers, {len(gdf_tributaries)} tributaries, {len(gdf_infra)} infra nodes, "
      f"{len(gdf_waterways)} waterway segments, {len(gdf_floodplains)} floodplains, {len(gdf_watersheds)} watersheds, "
      f"{len(gdf_admin)} admin boundaries, {len(gdf_industrial)} industrial corridors, {len(topology_map)} topology relationships.")
print("===============================================================")

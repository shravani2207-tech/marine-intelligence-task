# Spatial Layer Architecture & GIS Integration Guide
## National Geospatial Intelligence Layer -- Namami Gange TANTRA

---

## 1. Architecture OverviewRiver Coordinate Definitions]
|
v
[GeoDataFrame Construction] --(geopandas, shapely)--
|
+--> river_network (LineString per river, 10 rivers)
+--> national_waterways (LineString per NW segment, 5 segments)
+--> infrastructure_matrix (Point per node, 20 nodes)
|
v
[Spatial Intelligence Engine]
|
+--> topology_map (upstream/downstream per river, via .project())
+--> flood_risk_overlay (qualitative risk banding per river)
+--> navigation_corridors (derived from waterway + infra proximity)
|
v
[Validation Layer]
|
+--> CRS consistency check (EPSG:4326 across all layers)
+--> Coverage check (river count, infra count, topology count)
+--> Geometry validity check (shapely .is_valid)
|
v
[Canonical Export -- spatial_truth_export.json]
|
+--> layer_metadata (owner, version, timestamp, CRS, coverage_note)
+--> river_network (GeoJSON FeatureCollection)
+--> national_waterways (GeoJSON FeatureCollection)
+--> infrastructure_matrix (GeoJSON FeatureCollection)
+--> provenance_topology (relationship list)
+--> flood_risk_overlay (list)
+--> navigation_corridors (list)
+--> validation_results (dict)---

## 2. Design Principles Applied

- **Single CRS**: Every layer is built and validated against EPSG:4326 (WGS84) --
  no reprojection logic needed downstream.
- **Deterministic construction**: All coordinates are hardcoded per-run (no
  external API calls), so re-running the script produces identical geometry
  every time -- satisfies the "replay-safe" and "deterministic" principles
  from the Namami Gange TANTRA Federation core principles.
- **Provenance-first export**: Every export carries `layer_metadata` with
  owner, version, generation timestamp, and an explicit coverage_note so
  downstream consumers know this is a representative prototype, not
  survey-grade production data.
- **Separation of concerns**: Geometry construction, intelligence derivation
  (topology/overlays), and validation are distinct sections in the script,
  making it straightforward to swap in real data sources per phase without
  rewriting the whole pipeline.

---

## 3. Integration Points (per brief's Integration Block)

### 3.1 Marine MasterDB (Owner: Chandragupta)
- **What Chandragupta consumes**: `river_network`, `national_waterways`, and
  `infrastructure_matrix` sections of `spatial_truth_export.json` -- each is
  a standard GeoJSON FeatureCollection, directly loadable into PostGIS via
  `ogr2ogr` or `geopandas.read_file()` without transformation.
- **What this layer does NOT do**: Define or modify the Marine MasterDB
  schema. Schema ownership remains fully with Chandragupta.
- **Integration status**: Export format is ready for ingestion. Live
  ingestion into an actual MasterDB instance has not yet been demonstrated
  (pending MasterDB endpoint/access details from Chandragupta).

### 3.2 Knowledge Graph (Owner: Ankita)
- **What Ankita consumes**: Entity lists (river names, infra node names,
  types, associated_river relationships) that can be mapped to KG nodes and
  edges (e.g. river --[HAS_INFRASTRUCTURE]--> infra_node,
  infra_node --[UPSTREAM_OF]--> infra_node).
- **What this layer does NOT do**: Build the Knowledge Graph, ontology, or
  semantic relationships itself -- only supplies the geospatial entities and
  their raw relationships (via provenance_topology).
- **Integration status**: Entity/relationship shape is stable and
  JSON-serializable. Formal KG ontology mapping not yet performed (pending
  Ankita's ontology schema).

### 3.3 GOUDHA Runtime (Owner: Nupur)
- **What Nupur consumes**: `spatial_truth_export.json` as a read-only
  reference dataset during runtime execution -- e.g. to answer "which
  infrastructure is upstream of this point" using provenance_topology.
- **What this layer does NOT do**: Implement runtime services, execution
  logic, or GOUDHA-specific processing.
- **Integration status**: Not yet integrated -- no live runtime consumption
  demonstrated (pending Nupur's runtime interface spec).

---

## 4. How to Consume This Data

### Load the full export (Python)
```python
import json

with open("spatial_truth_export.json") as f:
    spatial_data = json.load(f)

rivers = spatial_data["river_network"]["features"]
infra = spatial_data["infrastructure_matrix"]["features"]
topology = spatial_data["provenance_topology"]
```

### Load as GeoDataFrames directly (geopandas)
```python
import geopandas as gpd

gdf_rivers = gpd.read_file("spatial_truth_export.json", layer=None)
# or, more reliably given the nested structure:
import json
with open("spatial_truth_export.json") as f:
    data = json.load(f)
gdf_rivers = gpd.GeoDataFrame.from_features(data["river_network"]["features"], crs="EPSG:4326")
```

### Query upstream/downstream relationships
```python
ganga_topology = [t for t in spatial_data["provenance_topology"] if t["river"] == "Ganga"]
```

---

## 5. Known Architectural Limitations

- Geometry is representative (3-7 points per river), not survey-grade --
  unsuitable for precise navigation or engineering decisions without
  replacement by authoritative source data.
- Topology logic uses `.project()` (linear position along the LineString),
  not actual flow direction/discharge data -- correct for rivers whose
  digitized direction matches real flow, but not independently verified
  per river.
- No versioning/replay mechanism yet -- `spatial_truth_export.json` is
  overwritten on each run rather than appended/versioned. Replay
  compatibility (per TANTRA convergence requirements) is a documented gap.
- No live connection to Bucket, InsightFlow, or Replay services -- this
  layer currently runs and exports standalone, outside the TANTRA runtime
  request flow.

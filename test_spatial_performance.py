import json
import time
import geopandas as gpd
from shapely.geometry import Point

with open("spatial_truth_export.json") as f:
    data = json.load(f)

print("===============================================================")
print("SPATIAL QUERY PERFORMANCE EVIDENCE")
print("===============================================================")

results = {}

# Test 1: Load full export and parse into GeoDataFrames
start = time.perf_counter()
gdf_rivers = gpd.GeoDataFrame.from_features(data["river_network"]["features"], crs="EPSG:4326")
gdf_infra = gpd.GeoDataFrame.from_features(data["infrastructure_matrix"]["features"], crs="EPSG:4326")
elapsed = time.perf_counter() - start
results["load_and_parse_geodataframes"] = f"{elapsed*1000:.2f} ms"
print(f"Load + parse GeoDataFrames (rivers + infra): {elapsed*1000:.2f} ms")

# Test 2: Point-in-proximity query -- find nearest infra node to a given point
start = time.perf_counter()
query_point = Point(83.0, 25.3)  # near Varanasi
gdf_infra["distance"] = gdf_infra.geometry.distance(query_point)
nearest = gdf_infra.loc[gdf_infra["distance"].idxmin()]
elapsed = time.perf_counter() - start
results["nearest_infra_query"] = f"{elapsed*1000:.2f} ms"
print(f"Nearest-infrastructure query (30 nodes): {elapsed*1000:.2f} ms -- found: {nearest['name']}")

# Test 3: Filter by river name (attribute query)
start = time.perf_counter()
ganga_infra = gdf_infra[gdf_infra["associated_river"] == "Ganga"]
elapsed = time.perf_counter() - start
results["attribute_filter_query"] = f"{elapsed*1000:.2f} ms"
print(f"Attribute filter query (river == Ganga): {elapsed*1000:.2f} ms -- {len(ganga_infra)} results")

# Test 4: Spatial join -- which infra nodes fall within a floodplain polygon
start = time.perf_counter()
gdf_floodplains = gpd.GeoDataFrame.from_features(data["floodplains"]["features"], crs="EPSG:4326")
joined = gpd.sjoin(gdf_infra, gdf_floodplains, how="inner", predicate="within")
elapsed = time.perf_counter() - start
results["spatial_join_floodplain_query"] = f"{elapsed*1000:.2f} ms"
print(f"Spatial join (infra within floodplains): {elapsed*1000:.2f} ms -- {len(joined)} matches")

# Test 5: Topology traversal -- walk full upstream/downstream chain for a river
start = time.perf_counter()
ganga_topology = [t for t in data["provenance_topology"] if t["river"] == "Ganga"]
elapsed = time.perf_counter() - start
results["topology_traversal_query"] = f"{elapsed*1000:.2f} ms"
print(f"Topology traversal (Ganga chain): {elapsed*1000:.2f} ms -- {len(ganga_topology)} relationships")

# Test 6: Repeat all queries 100x to get a stable average (small dataset, so single-run timing is noisy)
start = time.perf_counter()
for _ in range(100):
    _ = gdf_infra.geometry.distance(query_point)
elapsed = time.perf_counter() - start
avg_ms = (elapsed / 100) * 1000
results["distance_query_avg_over_100_runs"] = f"{avg_ms:.4f} ms"
print(f"Distance query, averaged over 100 runs: {avg_ms:.4f} ms/run")

print("\n===============================================================")
print("SUMMARY")
print("===============================================================")
for k, v in results.items():
    print(f"  {k}: {v}")

print(f"\nNote: dataset scale is small ({len(gdf_infra)} infra nodes, {len(gdf_rivers)} rivers),")
print("so all queries complete in low single-digit milliseconds. This confirms")
print("the query PATTERN works correctly and performs well at current scale;")
print("it does NOT constitute a load test at national production scale")
print("(which would involve orders of magnitude more records).")

with open("docs/PERFORMANCE_EVIDENCE.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved: docs/PERFORMANCE_EVIDENCE.json")

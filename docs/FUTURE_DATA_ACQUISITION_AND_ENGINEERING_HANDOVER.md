# Future Data Acquisition Plan & Engineering Handover
## National Geospatial Intelligence Layer -- Namami Gange TANTRA

---

## PART 1: Future Data Acquisition Plan

### 1.1 Priority Order for Real Data Integration

| Priority | Data Needed | Source | Replaces |
|---|---|---|---|
| 1 (Highest) | Survey-grade river network geometry (all 10 rivers) | Survey of India / CWC river atlas | Approximate coordinates in national_gis_layer.py |
| 2 | Full National Waterways catalogue (NW1-111) | iwai.nic.in | 5-segment representative subset |
| 3 | Dam/barrage/reservoir registry with precise coordinates | CWC National Register of Large Dams | Manually curated infra_records list |
| 4 | Wetlands, floodplains, watersheds (as geometry) | NRSC Bhuvan | Not currently present (full gap) |
| 5 | Administrative boundaries | Survey of India | Not currently present (full gap) |
| 6 | Flood hazard model output (quantitative) | CWC Flood Forecasting / NRSC Bhuvan flood atlas | Qualitative HIGH/MEDIUM/LOW labels |
| 7 | Protected areas | protectedplanet.net (already used in Task 3 environmental.json, needs spatial geometry not just catalogue) | Not currently present (full gap) |
| 8 | Industrial corridors | PM GatiShakti / logistics.gov.in | Not currently present (full gap) |

### 1.2 Acquisition Approach
1. Start with Priority 1-2 (river geometry, waterways) since every downstream
   layer (topology, overlays) depends on river geometry accuracy.
2. Most sources listed (CWC, IWAI, Survey of India, NRSC Bhuvan) require
   either registered API access or manual shapefile download -- this is an
   access/credentials task, not a coding task, and should be requested
   through official channels before further automation is built.
3. Once real geometry is available, `national_gis_layer.py`'s Phase 1
   section is designed to be swapped in-place: replace `river_coordinates`
   dict values with real LineString coordinate lists, re-run the script,
   and Phases 2-4 (topology, overlays, validation) will automatically
   re-derive against the new geometry with no logic changes needed.

### 1.3 Estimated Effort (once data access is granted)
- River geometry replacement: 1-2 hours per river (import + CRS conversion + validation)
- Full NW1-111 catalogue: 4-6 hours (bulk import + segment mapping)
- Dam/barrage precision pass: 3-4 hours
- Wetlands/floodplains/watersheds (new layers): 6-8 hours (new GeoDataFrames + integration)
- Admin boundaries: 2-3 hours (likely available as ready shapefiles from Survey of India)

---

## PART 2: Engineering Handover

### 2.1 What This Layer Is
A working, deterministic, validated prototype of a National Geospatial
Intelligence Layer covering all 10 named river basins, built with
geopandas/shapely, exported as CRS-consistent GeoJSON, with basic topology
and overlay intelligence layered on top.

### 2.2 Entry Point
`national_gis_layer.py` -- run with `python national_gis_layer.py`.
Requires `geopandas`, `pandas`, `shapely` (all standard PyPI packages).

### 2.3 Critical Files (in order of importance)
1. **national_gis_layer.py** -- the entire pipeline: geometry construction,
   topology derivation, overlay generation, validation, export. This is the
   only file that needs to be edited to add real data or new rivers/layers.
2. **spatial_truth_export.json** -- the canonical output. This is what
   downstream consumers (Chandragupta, Ankita, Nupur) should read from.
   Regenerated every time national_gis_layer.py is run.
3. **docs/COVERAGE_MATRIX_AND_GAP_ANALYSIS.md** -- the single most
   important reference for anyone picking this up: shows exactly what is
   covered and what isn't, per river and per system.

### 2.4 How to Extend This Layer
- **Add a new river**: add an entry to `river_coordinates` dict in Phase 1.
  Topology and flood-risk logic will need a matching entry added manually
  (flood_risk_overlay list) since those are curated, not auto-generated.
- **Add a new infrastructure node**: add an entry to `infra_records` list
  with `associated_river` set correctly -- topology will pick it up
  automatically on next run.
- **Add a new overlay layer** (e.g. environmental): follow the same pattern
  as `flood_risk_overlay` -- a list of dicts keyed by river/region, added
  to `master_db_export` before the final JSON write.

### 2.5 What NOT to Touch
- Do not modify Marine MasterDB schema (owned by Chandragupta).
- Do not build Knowledge Graph ontology (owned by Ankita).
- Do not implement GOUDHA runtime services (owned by Nupur).
- This layer only produces spatial data and exports it -- it does not
  consume or call into any of those three systems.

### 2.6 Known Limitations (carried forward from Gap Analysis)
See `docs/COVERAGE_MATRIX_AND_GAP_ANALYSIS.md` Section 7 for the full
honest assessment: this is a national-scale prototype and architecture
proof, not a survey-grade production dataset. Scaling requires direct
access to Survey of India / CWC / IWAI / NRSC Bhuvan data sources.

### 2.7 Contact / Ownership
Layer owner: Shravani Harde (National Geospatial Intelligence Layer +
Spatial Data Fabric), per the original task brief's ownership boundaries.

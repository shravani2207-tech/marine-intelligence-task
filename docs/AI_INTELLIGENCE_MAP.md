# AI Intelligence Map: Marine Intelligence & National Geospatial Layer

**System:** Marine Intelligence Platform / TANTRA / BHIV Bharat Mala MMR Extension
**Status:** Production-ready normalized data layer + Multi-river spatial intelligence prototype + MMR assessment framework
**Coordinate System:** WGS84 (`EPSG:4326`) with `EPSG:3857` used for metric distance calculations

---

## 1. Overview

This project provides a common **geospatial data and intelligence layer** for the Marine Intelligence Platform.

It combines:

* National rivers and waterways
* Ports and terminals
* Dams, bridges, locks and other infrastructure
* Environmental and flood-risk areas
* Logistics hubs
* MMR / NW-53 corridor data
* Spatial and feasibility analysis
* Knowledge graph mapping
* TANTRA and downstream system integrations

### Main flow

```text
Raw Data
   ↓
Data Validation & Normalization
   ↓
National GIS / MMR Analysis
   ↓
Canonical JSON Outputs
   ↓
Knowledge Graph + TANTRA Adapters
   ↓
Runtime / MasterDB / Bucket / InsightFlow / Replay
```

---

# 2. Main Modules

| Module                        | Main Purpose                                                  |
| ----------------------------- | ------------------------------------------------------------- |
| `national_gis_layer.py`       | Builds national river, waterway and infrastructure GIS layers |
| `mmr_canonical_envelope.py`   | Creates a common data format for MMR entities                 |
| `mmr_feasibility.py`          | Checks distances, connectivity and corridor feasibility       |
| `mmr_financial_assessment.py` | Provides CAPEX, OPEX and ROI calculation structure            |
| `mmr_scenario_simulation.py`  | Provides long-term traffic and RIS scenario modelling         |
| `map_to_knowledge_graph.py`   | Converts GIS data into Knowledge Graph nodes and edges        |
| `test_spatial_performance.py` | Measures spatial processing performance                       |

---

# 3. Current Data

The project currently contains the following datasets:

| Dataset              | Records | Purpose                                     |
| -------------------- | ------: | ------------------------------------------- |
| `ports.json`         |      40 | Ports and maritime infrastructure           |
| `coastal_zones.json` |      10 | Coastal economic zones                      |
| `waterways.json`     |      47 | 22 IWT terminals + 25 monitoring stations   |
| `environmental.json` |      16 | Environmental and protected-area references |
| `logistics.json`     |      11 | Logistics parks and multimodal hubs         |

Main data sources include IWAI, India-WRIS, Sagarmala, MMB, NRSC Bhuvan, UNEP, Protected Planet and other referenced government/industry sources.

---

# 4. National GIS Layer

The national GIS layer currently contains:

### Rivers and Waterways

* 11 river basins
* 5 representative tributaries
* 14 National Waterway stretches

### Infrastructure

43 infrastructure points including:

* Dams
* Barrages
* Ports
* Jetties
* Bridges
* Terminal
* Locks
* Reservoirs
* Wetlands

### Other Spatial Layers

* 3 floodplain areas
* 3 watershed areas
* 3 administrative boundaries
* 2 industrial corridors

### Spatial Overlays

The system also creates:

* Flood-risk zones
* Navigation corridors
* Cargo corridors
* Environmental constraints
* Protected areas
* Seasonal navigability information

---

# 5. Spatial Processing

The project uses:

### `EPSG:4326`

Used for storing normal latitude/longitude coordinates.

### `EPSG:3857`

Used when metric distance calculations are required.

The system performs:

* Distance calculations
* Nearest infrastructure searches
* Polygon spatial joins
* Geometry validation
* River topology analysis
* Upstream/downstream relationships

---

# 6. River Topology

The GIS layer creates a basic river topology model.

It uses `shapely.project()` to determine the position of infrastructure or points along river lines.

This allows the system to identify:

```text
Upstream
   ↓
River Node
   ↓
River Node
   ↓
Downstream
```

Currently, the system contains **32 upstream/downstream relationships across 11 rivers**.

---

# 7. MMR / NW-53 Analysis

The MMR module focuses on the Mumbai Metropolitan Region and the NW-53 corridor.

The current model includes:

* NW-53 waterway
* Kolshet terminal
* Gaimukh terminal
* MMR ports
* Thane Creek environmental constraint
* Bhiwandi logistics cluster

The system can calculate:

* Jetty-to-port distance
* Terminal connectivity
* Corridor coverage
* Terminal spacing
* Port proximity
* Environmental flags

---

# 8. Feasibility Scoring

The feasibility module provides structural scores based on spatial data.

### Corridor Coverage

Checks whether enough terminals are available along the corridor.

### Spacing Penalty

Penalizes large gaps between terminals.

Current threshold:

```text
Terminal gap > 15 km → penalty
```

### Intermodal Distance

Checks the distance between jetties and major ports.

Current reference threshold:

```text
Distance > 40 km → penalty
```

These are **structural analytical scores**, not final business decisions.

---

# 9. Financial Assessment

`mmr_financial_assessment.py` provides the framework for estimating:

* Land development cost
* Water-channel development cost
* Port and berth infrastructure cost
* Logistics transportation cost
* CAPEX
* OPEX
* ROI

However, the actual rate values are currently not populated.

Therefore:

```text
Current status: NOT_YET_ASSESSED
```

Real benchmark values are required before the financial results can be treated as production financial estimates.

---

# 10. Scenario Simulation

`mmr_scenario_simulation.py` provides a framework for long-term waterway scenarios.

It includes:

* Fairway information
* Traffic information
* Inland AIS data structure
* Water-level and tide information
* Locks and berth information
* Notices to Skippers
* Cargo and fleet management

It also supports long-term traffic growth calculations using:

```text
Future Traffic = Base Traffic × (1 + Growth Rate)^Years
```

The current framework supports:

* 50-year scenarios
* 100-year scenarios

Actual scenario results require real traffic and operational data.

---

# 11. Knowledge Graph

The GIS data can be converted into a Knowledge Graph using:

`map_to_knowledge_graph.py`

The system creates nodes such as:

* River
* Dam
* Barrage
* Port
* Jetty
* Lock
* Reservoir
* Wetland
* Risk

It also creates relationships such as:

```text
located_in
upstream_of
constrains
```

Example:

```text
Port
  ↓ located_in
River / Region

Dam
  ↓ upstream_of
River Node

Wetland
  ↓ constrains
Waterway
```

---

# 12. Canonical Data Format

MMR entities use a common canonical structure.

Important fields include:

```text
entity_id
entity_type
name
geometry
spatial_reference
source
authority
timestamp
schema_version
provenance
confidence
known_unknowns
properties
```

Current schema version:

```text
1.0.0
```

This gives different systems a common format for exchanging spatial data.

---

# 13. TANTRA / Convergence Integrations

The GIS layer contains adapters for downstream systems.

| Adapter                 | Purpose                                       |
| ----------------------- | --------------------------------------------- |
| `MasterDBAdapter`       | Sends spatial data to Marine MasterDB         |
| `KnowledgeGraphAdapter` | Sends graph nodes and relationships           |
| `RuntimeAdapter`        | Sends reference data to GOUDHA Runtime        |
| `BucketAdapter`         | Stores data using BHIV hash-chain persistence |
| `InsightFlowAdapter`    | Sends observability and telemetry data        |
| `ReplayAdapter`         | Stores versioned snapshots for replay         |

These integrations are controlled through environment variables.

If an endpoint is not configured, the adapter skips the operation instead of failing the complete GIS process.

---

# 14. Runtime Pipelines

## Pipeline 1 — Data Normalization

```text
Raw Data
   ↓
JSON Dataset
   ↓
Schema Validation
   ↓
Normalized Data
```

## Pipeline 2 — National GIS

```text
national_gis_layer.py
   ↓
Build GIS Layers
   ↓
Validate Geometry
   ↓
Build River Topology
   ↓
Create Spatial Overlays
   ↓
Generate spatial_truth_export.json
   ↓
Send to Convergence Adapters
```

## Pipeline 3 — MMR Assessment

```text
MMR Canonical Envelope
        ↓
   Feasibility
        ↓
   Financial Model
        ↓
Scenario Simulation
```

## Pipeline 4 — Knowledge Graph

```text
spatial_truth_export.json
        ↓
map_to_knowledge_graph.py
        ↓
knowledge_graph_export.json
```

## Pipeline 5 — Performance Testing

```text
spatial_truth_export.json
        ↓
test_spatial_performance.py
        ↓
PERFORMANCE_EVIDENCE.json
```

---

# 15. Current Dummy / Placeholder Data

Some parts of the system still use approximate or placeholder data.

| Area                  | Current Situation                  | Required for Production     |
| --------------------- | ---------------------------------- | --------------------------- |
| River coordinates     | Representative paths               | Accurate hydrographic data  |
| Waterway coordinates  | Approximate vectors                | Official survey/chart data  |
| Floodplain polygons   | Approximate bounding areas         | Official GIS boundaries     |
| Financial rates       | Not populated                      | Real cost benchmarks        |
| Traffic growth        | Not populated                      | Real traffic/cargo data     |
| Decongestion analysis | Not populated                      | Road traffic baseline       |
| NW-53 jetties         | Only Kolshet and Gaimukh mapped    | Remaining jetty coordinates |
| Convergence endpoints | Environment variables may be empty | Actual service endpoints    |

---

# 16. Important Production Limitations

The current GIS layer should **not** be treated as a final navigation or engineering system.

For example, representative river lines are useful for:

* Testing
* Spatial analysis
* Prototype intelligence
* Data integration
* Knowledge Graph development

But they are not sufficient for:

* Nautical navigation
* Dredging decisions
* Detailed engineering
* Final infrastructure planning

Accurate official survey and hydrographic datasets are required for those activities.

---

# 17. Evidence and Validation

The project already has several verification mechanisms.

### Spatial Validation

`spatial_truth_export.json` contains validation information for:

* CRS consistency
* River counts
* Infrastructure counts
* Topology relationships
* Geometry validity

### Performance Evidence

`docs/PERFORMANCE_EVIDENCE.json` contains spatial performance measurements.

### Audit Evidence

`mmr_evidence_log.json` records:

* Changes
* Timestamps
* Validation results
* Evidence information

### Replay Support

`ReplayAdapter` and `BucketAdapter` support:

* `parent_hash`
* `trace_id`
* `artifact_id`
* `schema_version`
* Versioned snapshots

This allows previous spatial states to be tracked and replayed.

---

# 18. Current Outputs

The system can generate:

```text
spatial_truth_export.json
knowledge_graph_export.json
mmr_canonical_envelope.json
mmr_feasibility_assessment.json
mmr_financial_assessment.json
mmr_scenario_simulation_assessment.json
```

Additional reports and evidence files are also generated for performance, validation and audit purposes.

---

# 19. Current Status

### Completed

* National GIS data layer
* Multi-river spatial model
* River topology
* Spatial validation
* MMR canonical data structure
* MMR feasibility framework
* Financial assessment framework
* Scenario simulation framework
* Knowledge Graph mapping
* Performance testing
* Evidence and replay hooks
* TANTRA convergence adapter structure

### Still Requires Real Data

* Accurate hydrographic river geometry
* Complete NW-53 jetty coordinates
* Real financial benchmarks
* Real traffic/cargo statistics
* Real road congestion data
* Production convergence endpoints

---

# 20. Final Summary

The project now provides a **common geospatial intelligence foundation** for the Marine Intelligence and BHIV Bharat Mala systems.

The current platform can:

```text
Store Spatial Data
       ↓
Validate Data
       ↓
Analyze Rivers & Infrastructure
       ↓
Analyze MMR / NW-53
       ↓
Generate Feasibility & Scenario Models
       ↓
Create Knowledge Graph Data
       ↓
Export Canonical JSON
       ↓
Connect to TANTRA / Runtime / MasterDB
       ↓
Maintain Audit & Replay Evidence
```

The main remaining work is to replace placeholder data with **official, real-world datasets** and configure the production downstream endpoints.

**Overall status:**
**Core geospatial intelligence and integration framework completed. Production-grade real-world analysis requires enrichment with authoritative spatial, traffic, financial and operational datasets.**

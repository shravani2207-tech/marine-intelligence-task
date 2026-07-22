# Failure Scenarios & Error Handling
## National Geospatial Intelligence Layer -- Namami Gange TANTRA

---

## 1. Missing or Malformed Coordinate Data

**Scenario:** A river or infrastructure entry has an invalid coordinate
(e.g. out-of-range latitude/longitude, or a non-numeric value).

**Current behavior:** national_gis_layer.py would raise a shapely
GEOSException or a TypeError at the LineString()/Point() construction
step, halting the script before any export is written -- this fails
loudly rather than silently producing bad data.

**Tested:** Not explicitly tested with an injected bad coordinate in this
session. Recommended follow-up: add a coordinate range validator before
GeoDataFrame construction.

---

## 2. River With Fewer Than 2 Infrastructure Nodes

**Scenario:** A river (e.g. Tapi, Indus_Basin) has only 0 or 1 associated
infrastructure node.

**Current behavior:** CONFIRMED, actually occurred. The topology loop
explicitly checks if len(river_infra) < 2: continue -- rivers with fewer
than 2 nodes are silently skipped for topology generation, but the script
does NOT crash. This is why Tapi and Indus Basin currently have zero
topology relationships.

**Impact:** Documented in Coverage Matrix as a known gap, not a bug --
graceful degradation by design.

---

## 3. Convergence Adapter Called Without Endpoint Configured

**Scenario:** Any of the 6 convergence adapters is called before its
environment variable is set.

**Current behavior:** CONFIRMED, this is the current live state of all 6
adapters. Each push() call checks for its endpoint env var first and
returns a skipped status without raising an exception. The main pipeline
always completes successfully even though zero live convergence has
occurred.

**Not yet tested:** What happens if an endpoint IS configured but
unreachable. No real endpoints have been provided yet, so this failure
mode is currently only theoretical.

---

## 4. Duplicate or Conflicting River/Infra IDs

**Scenario:** Two infrastructure records accidentally share the same
infra_id.

**Current behavior:** Not explicitly validated. Risk is low in current
dataset (all IDs manually verified sequential), but is a genuine gap for
future contributors adding records by hand.

---

## 5. Empty or Corrupted spatial_truth_export.json on Read

**Scenario:** A downstream consumer reads the export file mid-write.

**Current behavior:** The export write is not atomic. Recommended
follow-up: write to a temp file and atomically rename once complete.

---

## 6. Script Run With Missing Dependencies

**Scenario:** geopandas, shapely, or pandas not installed.

**Current behavior:** CONFIRMED via testing -- raises a standard
ModuleNotFoundError immediately, before any processing begins. No
partial/corrupt output is possible.

---

## Summary

| Failure Mode | Status | Severity |
|---|---|---|
| Invalid coordinates | Not tested, fails loudly by nature of shapely | Medium |
| River with <2 infra nodes | Handled gracefully (by design) | None |
| Convergence adapter, no endpoint | Handled gracefully (by design) | None |
| Convergence adapter, endpoint unreachable | Untested (no real endpoints yet) | Unknown |
| Duplicate IDs | Not validated | Low |
| Non-atomic export write | Not fixed | Low |
| Missing dependencies | Handled (fails loudly) | Low |

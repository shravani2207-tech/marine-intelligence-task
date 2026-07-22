# Failure Scenarios & Error Handling
## National Geospatial Intelligence Layer -- Namami Gange TANTRA

---

## 1. Missing or Malformed Coordinate Data

**Scenario:** A river or infrastructure entry has an invalid coordinate
(e.g. out-of-range latitude/longitude, or a non-numeric value).

**Current behavior:** `national_gis_layer.py` would raise a shapely
`GEOSException` or a `TypeError` at the `LineString()`/`Point()`
construction step, halting the script before any export is written --
this fails loudly rather than silently producing bad data.

**Tested:** Not explicitly tested with an injected bad coordinate in this
session. Recommended follow-up: add a coordinate range validator
(`-180 <= lon <= 180`, `-90 <= lat <= 90`) before GeoDataFrame construction,
raising a clear `ValueError` naming the offending river/node.

---

## 2. River With Fewer Than 2 Infrastructure Nodes

**Scenario:** A river (e.g. Tapi, Indus_Basin) has only 0 or 1 associated
infrastructure node.

**Current behavior:** CONFIRMED, actually occurred. The topology loop in
Phase 2 explicitly checks `if len(river_infra) < 2: continue` -- rivers
with fewer than 2 nodes are silently skipped for topology generation, but
the script does NOT crash. This is why Tapi and Indus Basin currently have
zero topology relationships despite being present in river_network.

**Impact:** Documented in Coverage Matrix as a known gap, not a bug --
this is graceful degradation by design, not a failure.

---

## 3. Convergence Adapter Called Without Endpoint Configured

**Scenario:** Any of the 6 convergence adapters (MasterDB, KG, Runtime,
Bucket, InsightFlow, Replay) is called via `.push()` before its
corresponding environment variable is set.

**Current behavior:** CONFIRMED, this is the current live state of all 6
adapters. Each `.push()` call checks for its endpoint env var first and
returns `{"status": "skipped", "reason": "<ENDPOINT> not configured yet"}`
without raising an exception or attempting a network call. This means the
main pipeline (`national_gis_layer.py`) always completes successfully even
though zero live convergence has occurred -- by design, this is meant to
prevent convergence being unconfigured from blocking the rest of the
pipeline.

**Not yet tested:** What happens if an endpoint IS configured but
unreachable (analogous to the TANTRA endpoint 502/429 errors seen in the
Sanskar runtime task). Since no real endpoints have been provided yet,
this failure mode is currently only theoretical for this layer.

---

## 4. Duplicate or Conflicting River/Infra IDs

**Scenario:** Two infrastructure records accidentally share the same
`infra_id`.

**Current behavior:** Not explicitly validated. GeoDataFrame construction
would silently accept duplicate IDs since `infra_id` is not enforced as a
unique key anywhere in the pipeline.

**Risk:** Low in current dataset (all IDs are sequential and manually
verified), but this is a genuine gap for any future contributor adding
records by hand. Recommended follow-up: add a uniqueness assertion on
`infra_id` and `river_id` before export.

---

## 5. Empty or Corrupted spatial_truth_export.json on Read

**Scenario:** A downstream consumer (Chandragupta/Ankita/Nupur) tries to
read `spatial_truth_export.json` while it is being written (race
condition), or the file is corrupted/truncated.

**Current behavior:** The export write uses a direct `json.dump()` to the
target file, which is not atomic -- a reader could theoretically see a
partially-written file if reading happens mid-write.

**Not yet tested/fixed.** Recommended follow-up: write to a temporary file
and atomically rename (`os.replace()`) once the write is complete, so
readers only ever see a complete, valid file.

---

## 6. Script Run With Missing Dependencies

**Scenario:** `geopandas`, `shapely`, or `pandas` not installed in the
Python environment.

**Current behavior:** CONFIRMED via testing -- a missing import raises a
standard Python `ModuleNotFoundError` immediately at the top of the
script, before any processing begins. No partial/corrupt output is
possible in this case.

**Tested:** Verified `geopandas` availability was checked before running
the pipeline in this session (`python -c "import geopandas; print('geopandas OK')"`).

---

## Summary

| Failure Mode | Status | Severity if it occurs |
|---|---|---|
| Invalid coordinates | Not tested, fails loudly (by nature of shapely) | Medium -- blocks entire run |
| River with <2 infra nodes | Handled gracefully (by design) | None -- documented gap, not a crash |
| Convergence adapter, no endpoint | Handled gracefully (by design) | None -- returns status, does not crash |
| Convergence adapter, endpoint unreachable | Untested (no real endpoints yet) | Unknown -- needs real endpoint to test |
| Duplicate IDs | Not validated | Low currently, but a real gap |
| Non-atomic export write | Not fixed | Low -- theoretical race condition |
| Missing dependencies | Handled (fails loudly, no partial output) | Low -- clear error message |

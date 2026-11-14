import json
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mmr_shared_filters import get_mmr_jetties
from mmr_feasibility import load_json, build_report
from mmr_canonical_envelope import build_entities
from mmr_scenario_simulation import traffic_information
from mmr_intelligence import (
    CONFIG,
    get_verification,
    stage_traffic,
    run_pipeline,
    load_json as intel_load_json,
)

BASE_DIR = Path(__file__).resolve().parent.parent


class TestNW53Verification(unittest.TestCase):
    def setUp(self):
        self.waterways_path = BASE_DIR / "waterways.json"
        self.waterways = load_json(str(self.waterways_path))

    def test_waterways_loading_and_bom(self):
        """Ensure all core datasets load without BOM issues."""
        for filename in ["waterways.json", "ports.json", "environmental.json", "logistics.json"]:
            data = load_json(filename)
            self.assertIsNotNone(data, f"Failed to load {filename}")
            intel_data = intel_load_json(str(BASE_DIR / filename))
            self.assertIsNotNone(intel_data, f"intel_load_json failed for {filename}")

    def test_nw53_terminal_counts_and_registry_status(self):
        """Test that the 6 NW-53 terminals yield 4 usable and 2 pending verification."""
        terminals = [t for t in self.waterways["iwt_terminals"] if "NW-53" in t.get("waterway_name", "")]
        self.assertEqual(len(terminals), 6, "Expected exactly 6 NW-53 terminals in waterways.json")

        usable_count = 0
        pending_count = 0
        for t in terminals:
            v = get_verification(t)
            if v["status"] == "usable":
                usable_count += 1
            elif v["status"] == "pending_verification":
                pending_count += 1

        self.assertEqual(usable_count, 4, "Expected exactly 4 usable NW-53 terminals")
        self.assertEqual(pending_count, 2, "Expected exactly 2 pending verification NW-53 terminals")

        # Specific terminal checks
        by_name = {t["terminal_name"]: t for t in terminals}
        self.assertEqual(get_verification(by_name["Kolshet Jetty"])["status"], "usable")
        self.assertEqual(get_verification(by_name["Gaimukh Jetty"])["status"], "usable")
        self.assertEqual(get_verification(by_name["Vasai Terminal"])["status"], "usable")
        self.assertEqual(get_verification(by_name["Nagla Bunder Terminal"])["status"], "usable")
        self.assertEqual(get_verification(by_name["Dombivli Terminal"])["status"], "pending_verification")
        self.assertEqual(get_verification(by_name["Parsik Bunder Terminal"])["status"], "pending_verification")

    def test_borehole_references_cannot_be_exported_as_jetty_points(self):
        """Unverified borehole coordinates must be excluded from get_mmr_jetties."""
        terminals = [t for t in self.waterways["iwt_terminals"] if "NW-53" in t.get("waterway_name", "")]
        by_name = {t["terminal_name"]: t for t in terminals}

        self.assertEqual(by_name["Dombivli Terminal"].get("coordinate_verification"), "UNVERIFIED")
        self.assertEqual(by_name["Parsik Bunder Terminal"].get("coordinate_verification"), "UNVERIFIED")

        filtered = get_mmr_jetties(self.waterways)
        filtered_names = {t["terminal_name"] for t in filtered}
        expected = {"Kolshet Jetty", "Gaimukh Jetty", "Vasai Terminal", "Nagla Bunder Terminal"}
        self.assertEqual(filtered_names, expected)
        self.assertNotIn("Dombivli Terminal", filtered_names)
        self.assertNotIn("Parsik Bunder Terminal", filtered_names)

    def test_feasibility_scoring_excludes_unverified_terminals(self):
        """Feasibility scoring must only include the 4 verified jetties."""
        report = build_report()
        wf = report["waterway_feasibility"]
        self.assertEqual(wf["jetty_count"], 4)
        self.assertNotIn("Dombivli Terminal", wf["jetties"])
        self.assertNotIn("Parsik Bunder Terminal", wf["jetties"])

    def test_canonical_envelope_excludes_unverified_terminals(self):
        """Canonical envelope must not include Dombivli or Parsik Bunder."""
        entities = build_entities()
        terminal_entities = [e for e in entities if e["entity_type"] == "iwt_terminal"]
        terminal_ids = {e["entity_id"] for e in terminal_entities}
        self.assertEqual(len(terminal_entities), 4)
        self.assertIn("TERMINAL_21", terminal_ids)
        self.assertIn("TERMINAL_22", terminal_ids)
        self.assertIn("TERMINAL_23", terminal_ids)
        self.assertIn("TERMINAL_25", terminal_ids)
        self.assertNotIn("TERMINAL_24", terminal_ids)
        self.assertNotIn("TERMINAL_26", terminal_ids)

    def test_kalher_and_anjur_dive_not_in_spatial_terminals(self):
        """Kalher and Anjur Dive must not be fabricated as spatial terminals."""
        all_names = [t.get("terminal_name", "").lower() for t in self.waterways.get("iwt_terminals", [])]
        self.assertFalse(any("kalher" in name for name in all_names))
        self.assertFalse(any("anjur" in name for name in all_names))

        scenario_info = traffic_information()
        coord_status = scenario_info["terminal_coordinate_status"]
        self.assertEqual(coord_status.get("Kalher"), "pending verification")
        self.assertEqual(coord_status.get("Anjur Dive"), "pending verification")

    def test_traffic_data_separate_from_spatial_eligibility(self):
        """Traffic data for routes is preserved while coordinates remain unverified."""
        scenario_info = traffic_information()
        routes = scenario_info["traffic_by_route"]
        dombivli_routes = [r for r in routes if "Dombivli" in r["route"]]
        parsik_routes = [r for r in routes if "Parsik Bunder" in r["route"]]
        self.assertTrue(len(dombivli_routes) > 0)
        self.assertTrue(len(parsik_routes) > 0)

        coord_status = scenario_info["terminal_coordinate_status"]
        self.assertEqual(coord_status["Dombivli"], "UNVERIFIED")
        self.assertEqual(coord_status["Parsik Bunder"], "UNVERIFIED")

    def test_missing_dpr_traffic_reported_in_intelligence_pipeline(self):
        """When dpr_2024_traffic.json is missing, a clear, actionable missing status is returned."""
        result = stage_traffic({"terminal_name": "Kolshet Jetty"}, None)
        self.assertEqual(result.status, "NOT_YET_ASSESSED")
        self.assertIn("dpr_2024_traffic.json", result.limitations[0])

    def test_intelligence_pipeline_execution(self):
        """Run full mmr_intelligence pipeline and verify terminal classifications."""
        output = run_pipeline(CONFIG)
        self.assertGreater(len(output["results"]), 0)

        results_by_id = {r["entity_id"]: r for r in output["results"]}
        # NW-53 checks
        self.assertEqual(results_by_id["INTELLIGENCE_21"]["verification_status"], "usable")
        self.assertEqual(results_by_id["INTELLIGENCE_21"]["included_in_scoring"], True)
        self.assertEqual(results_by_id["INTELLIGENCE_22"]["verification_status"], "usable")
        self.assertEqual(results_by_id["INTELLIGENCE_22"]["included_in_scoring"], True)
        self.assertEqual(results_by_id["INTELLIGENCE_23"]["verification_status"], "usable")
        self.assertEqual(results_by_id["INTELLIGENCE_23"]["included_in_scoring"], True)
        self.assertEqual(results_by_id["INTELLIGENCE_25"]["verification_status"], "usable")
        self.assertEqual(results_by_id["INTELLIGENCE_25"]["included_in_scoring"], True)

        self.assertEqual(results_by_id["INTELLIGENCE_24"]["verification_status"], "pending_verification")
        self.assertEqual(results_by_id["INTELLIGENCE_24"]["included_in_scoring"], False)
        self.assertEqual(results_by_id["INTELLIGENCE_24"]["overall_status"], "EXCLUDED_PENDING_VERIFICATION")

        self.assertEqual(results_by_id["INTELLIGENCE_26"]["verification_status"], "pending_verification")
        self.assertEqual(results_by_id["INTELLIGENCE_26"]["included_in_scoring"], False)
        self.assertEqual(results_by_id["INTELLIGENCE_26"]["overall_status"], "EXCLUDED_PENDING_VERIFICATION")

        # Anomaly detection in data quality
        anomalies = output["data_quality"]["known_coordinate_anomalies"]
        anomaly_labels = [a["label"] for a in anomalies]
        self.assertIn("Dombivli Terminal", anomaly_labels)
        self.assertIn("Parsik Bunder Terminal", anomaly_labels)


if __name__ == "__main__":
    unittest.main()

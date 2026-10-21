from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olm_math_ucrt_downstream_replay_20260814.py"
REPORT = ROOT / "refs/conformance/olm_math_ucrt_downstream_replay_readiness_20260814.json"


def load_tool():
    spec = importlib.util.spec_from_file_location("olm_ucrt_downstream", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OLMUcrtDownstreamReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_tool()
        cls.report = json.loads(REPORT.read_text())

    def test_persisted_host_substitute_plumbing_is_exact_and_non_promoting(self) -> None:
        self.assertTrue(self.module.validate_report(self.report))
        self.assertEqual(self.report["directional"]["matching_cells"], 6)
        self.assertEqual(self.report["distance"]["matching_host_substituted_cells"], 8)
        self.assertFalse(self.report["decision"]["directional_six_candidate_for_promotion"])
        self.assertFalse(self.report["decision"]["distance_power_eight_candidate_for_promotion"])
        self.assertFalse(self.report["actual_aex_table_replay"]["available"])
        self.assertTrue(self.report["actual_aex_table_replay"]["required_for_promotion"])

    def test_output_or_claim_recanonicalization_is_rejected(self) -> None:
        for mutate in (
            lambda value: value["directional"]["cells"][0].update({"raw_sha256": "0" * 64}),
            lambda value: value["distance"]["cells"][0].update({"matches_host_substituted_oracle": False}),
            lambda value: value["decision"].update({"directional_six_candidate_for_promotion": True}),
            lambda value: value.update({"extra": True}),
        ):
            candidate = copy.deepcopy(self.report)
            mutate(candidate)
            self.assertFalse(self.module.validate_report(candidate))

    def test_result_table_writer_has_no_duplicate_keys(self) -> None:
        expf, powf = self.module.maps_from_host()
        self.assertLessEqual(len(expf), 494)
        self.assertEqual(len(powf), 850)
        self.assertTrue(all(len(key) == 10 and len(value) == 10 for key, value in expf.items()))

    def test_full_five_count_return_needs_no_cross_generation_table(self) -> None:
        from tests.test_olm_math_ucrt_batch_return_20260814 import OLMUcrtMathBatchReturnTest
        builder = OLMUcrtMathBatchReturnTest()
        builder.module = load_tool().load(ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py",
                                          "olm_ucrt_return_for_downstream_test")
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-downstream-generation-") as raw:
            path = builder.build_valid_return(Path(raw))
            expf, powf, validated = self.module.maps_from_return(path)
            self.assertLessEqual(len(expf), 494)
            self.assertEqual(len(powf), 850)
            self.assertEqual(validated["vectors"]["directional_expf"], 494)
            self.assertEqual(validated["vectors"]["directional_powf"], 787)

            # Replace the generic semantic-return fixture with the keyed host
            # table used by the replay plumbing self-test.  This exercises the
            # positive promotion decision without pretending those words are
            # native Windows evidence.
            host_expf, _ = self.module.maps_from_host()
            batch = path / builder.module.BATCH_ID
            child_path = batch / "directional/run_summary.json"
            child = json.loads(child_path.read_text())
            for row in child["rows"]:
                row["native_ucrt_result_bits"] = host_expf[row["argument_bits"]]
            child_bytes = builder.module.canonical(child)
            child_path.write_bytes(child_bytes)
            parent_path = batch / "run_summary.json"
            parent = json.loads(parent_path.read_text())
            parent["children"]["directional"]["summary_sha256"] = hashlib.sha256(child_bytes).hexdigest()
            parent_path.write_bytes(builder.module.canonical(parent))

            replay = self.module.replay(path)
            self.assertEqual(replay["directional"]["matching_cells"], 6)
            self.assertEqual(replay["distance"]["matching_host_substituted_cells"], 8)
            self.assertFalse(replay["decision"]["directional_six_candidate_for_promotion"])
            self.assertFalse(replay["decision"]["distance_power_eight_candidate_for_promotion"])
            self.assertEqual(replay["decision"]["distance_blocker"],
                             "actual-AEX native-table replay remains absent")


if __name__ == "__main__":
    unittest.main()

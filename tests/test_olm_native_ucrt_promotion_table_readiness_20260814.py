from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olm_native_ucrt_promotion_table_readiness_20260814.py"
CONSUMER_READINESS = ROOT / "refs/conformance/olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OLMNativeUcrtPromotionTableReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load(TOOL, "olm_native_ucrt_promotion_table")
        cls.downstream = load(cls.module.DOWNSTREAM, "olm_native_ucrt_promotion_downstream")
        cls.return_module = load(ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py",
                                 "olm_native_ucrt_promotion_return")
        cls.return_tests = load(ROOT / "tests/test_olm_math_ucrt_batch_return_20260814.py",
                                "olm_native_ucrt_promotion_return_tests")

    def exact_return(self, root: Path) -> Path:
        builder = self.return_tests.OLMUcrtMathBatchReturnTest()
        builder.module = self.return_module
        path = builder.build_valid_return(root)
        batch = path / self.return_module.BATCH_ID
        host_expf, _ = self.downstream.maps_from_host()
        child_path = batch / "directional/run_summary.json"
        child = json.loads(child_path.read_text())
        for row in child["rows"]:
            key = "0x00000000" if row["argument_bits"] == "0x80000000" else row["argument_bits"]
            row["native_ucrt_result_bits"] = host_expf[key]
        child_bytes = self.return_module.canonical(child)
        child_path.write_bytes(child_bytes)
        parent_path = batch / "run_summary.json"
        parent = json.loads(parent_path.read_text())
        parent["children"]["directional"]["summary_sha256"] = hashlib.sha256(child_bytes).hexdigest()
        parent_path.write_bytes(self.return_module.canonical(parent))
        return path

    def test_current_sources_remain_exactly_fail_closed(self) -> None:
        self.assertEqual(self.module.live_source_gate(), self.module.SOURCE_SHA256)

    def consumer_replay(self) -> dict:
        persisted = json.loads(CONSUMER_READINESS.read_text())["consumer"]
        return {"status": persisted["status"], "summary": persisted["summary"],
                "directional_rows": persisted["directional_rows"],
                "distance_rows": persisted["distance_rows"]}

    def test_synthetic_validated_return_assembles_closed_tables(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-table-negative-") as raw:
            report = self.module.build_from_consumer(self.exact_return(Path(raw)), self.consumer_replay())
            self.assertTrue(self.module.validate(report, live=False))
            self.assertEqual(len(report["tables"]["directional_expf"]), 377)
            self.assertEqual(len(report["tables"]["directional_powf"]), 787)
            self.assertEqual(len(report["tables"]["distance_powf"]), 63)
            header = self.module.render_header(report)
            self.assertIn("lookup_directional_expf", header)
            self.assertIn("lookup_directional_powf", header)
            self.assertIn("lookup_distance_powf", header)

    def test_incomplete_direct_owner_replay_cannot_emit_tables(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-table-positive-") as raw:
            replay = self.consumer_replay()
            replay["summary"] = dict(replay["summary"], total_same_table_exact=13)
            with self.assertRaisesRegex(RuntimeError, "direct-owner RAW closure incomplete"):
                self.module.build_from_consumer(self.exact_return(Path(raw)), replay)

    def test_recanonicalized_table_and_claim_tamper_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-table-tamper-") as raw:
            report = self.module.build_from_consumer(self.exact_return(Path(raw)), self.consumer_replay())
        for mutate in (
            lambda value: value.update(extra=True),
            lambda value: value["authorities"].update(native_dual_owner_consumer_sha256="0" * 64),
            lambda value: value["final_raw"]["directional_cells"][0].update(
                same_table_full_raw_exact=False),
            lambda value: value["integration_contract"].update(mac_public_effectmain_exact_claimed=True),
            lambda value: value["tables"]["directional_expf"].append(
                dict(value["tables"]["directional_expf"][0])),
        ):
            changed = copy.deepcopy(report)
            mutate(changed)
            changed["tables_sha256"] = self.module.digest(changed["tables"])
            self.assertFalse(self.module.validate(changed, live=False))


if __name__ == "__main__":
    unittest.main()

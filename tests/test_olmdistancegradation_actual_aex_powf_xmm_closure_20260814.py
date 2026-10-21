from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdistancegradation_actual_aex_powf_xmm_closure_20260814.py"
REPORT = ROOT / "refs/conformance/olmdistancegradation_actual_aex_powf_xmm_closure_20260814.json"
TOOL_SHA256 = "877fa6111c7bdc393f10d69fb540be39a69abf5415999ce12aa0e32491530fc9"
REPORT_SHA256 = "741dce6e7a1dd852d237072502341b40721b7cc7a9000c279f6234c10f07108a"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_tool():
    spec = importlib.util.spec_from_file_location("dg_actual_powf_xmm", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


class DGActualAexPowfXmmClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_tool(); cls.report = json.loads(REPORT.read_text())

    def test_pinned_live_closure(self) -> None:
        self.assertEqual(sha(TOOL), TOOL_SHA256)
        self.assertEqual(sha(REPORT), REPORT_SHA256)
        self.assertTrue(self.module.validate(self.report))
        self.assertEqual(self.report["summary"]["actual_aex_calls"], 992)
        self.assertEqual(self.report["production_only_irrelevance"]["pair_count"], 7)

    def test_default_is_read_only(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(TOOL), "--validate-only"], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_recanonicalized_trace_and_claim_tamper_rejected(self) -> None:
        mutations = (
            lambda value: value["cells"][0]["actual_trace"][0].update({"input_bits": "0x00000000"}),
            lambda value: value["summary"].update({"actual_nonproduction_pairs": 1}),
            lambda value: value["production_only_irrelevance"]["replays"]["all_zero"].update({"matching_cells": 7}),
            lambda value: value["boundary"].update({"production_admission_changed": True}),
            lambda value: value.update({"unexpected": True}),
        )
        for mutation in mutations:
            candidate = copy.deepcopy(self.report); mutation(candidate)
            if "cells" in candidate:
                candidate["cells_sha256"] = self.module.digest(candidate["cells"])
                for cell in candidate["cells"]:
                    cell["actual_trace_sha256"] = self.module.digest(cell["actual_trace"])
            self.assertFalse(self.module.validate(candidate))

    def test_all_actual_calls_are_monotone_production_positions(self) -> None:
        for cell in self.report["cells"]:
            positions = cell["production_subsequence_positions"]
            self.assertEqual(len(positions), 124)
            self.assertEqual(positions, sorted(positions))
            self.assertEqual(len(set(positions)), 124)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmdirectionalblur_remaining6_ucrt_powf_census_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_ucrt_powf_census_20260814.json"


def load_module():
    spec = importlib.util.spec_from_file_location("directional_powf_census", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalPowfCensusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_live_report_and_exact_key_census(self) -> None:
        self.assertTrue(self.module.validate(self.report))
        self.assertEqual(len(self.report["powf_pairs"]), 787)
        self.assertEqual(self.report["calls"]["powf_occurrences"], 47514)
        self.assertTrue(self.report["calls"]["all_six_exported_raw_exact"])

    def test_default_is_read_only(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(TOOL)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_recanonicalized_pair_and_scope_tamper_rejected(self) -> None:
        for mutate in (
            lambda value: value["powf_pairs"][2].update({"input_bits": "0x00000001"}),
            lambda value: value["boundary"].update({"native_windows_return_received": True}),
            lambda value: value.update({"unexpected": True}),
        ):
            changed = copy.deepcopy(self.report)
            mutate(changed)
            changed["powf_pairs_sha256"] = self.module.hashlib.sha256(
                json.dumps(changed["powf_pairs"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            self.assertFalse(self.module.validate(changed))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/probe_olmradialblur_type3_layer_span_actual_aex_20260811.py"


def load_module():
    spec = importlib.util.spec_from_file_location("radial_type3_span", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadialType3LayerSpanTests(unittest.TestCase):
    def test_actual_composers_and_static_boundary(self) -> None:
        report = load_module().probe()
        self.assertEqual(report["status"], "exact_static_and_executed_composer_contract")
        self.assertEqual({row["depth"] for row in report["rows"]}, {8, 16, 32})
        self.assertEqual({row["noise_variation"] for row in report["rows"]}, {25, 100})
        self.assertTrue(all(row["invariance_control"]["exact"] for row in report["rows"]))
        self.assertIn("RenderWorld Type3", report["not_admitted"])


if __name__ == "__main__":
    unittest.main()

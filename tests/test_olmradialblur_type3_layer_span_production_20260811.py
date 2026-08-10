from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/emulation/test_olmradialblur_type3_layer_span_production_20260811.py"


class RadialType3ProductionTests(unittest.TestCase):
    def test_all_actual_aex_span_words(self) -> None:
        spec = importlib.util.spec_from_file_location("radial_type3_production", SCRIPT)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        result = module.run()
        self.assertEqual(result["status"], "exact")
        self.assertEqual(result["rows"], 6)
        self.assertFalse(result["special_values_admitted"])
        self.assertFalse(result["renderworld_type3_admitted"])


if __name__ == "__main__":
    unittest.main()

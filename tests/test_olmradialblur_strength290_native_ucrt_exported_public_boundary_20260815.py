from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/emulation/test_olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.py"
REPORT = ROOT / "refs/conformance/olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.json"


def module():
    spec = importlib.util.spec_from_file_location("radial_native_boundary", TOOL)
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class RadialNativeUcrtBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tool = module()
        cls.value = json.loads(REPORT.read_text())

    def test_frozen_evidence_is_live_valid(self) -> None:
        self.assertTrue(self.tool.validate(self.value))
        self.assertEqual(self.value["native_table"]["original_calls"], 725)
        self.assertEqual(self.value["comparison"]["different_float_words"], 80)

    def test_exact_or_promotion_tamper_is_rejected(self) -> None:
        for path, replacement in [
            (("comparison", "same_source_full_raw_exact"), True),
            (("comparison", "native_exported_sha256"), "0" * 64),
            (("public_admission", "justified"), True),
            (("public_admission", "production_changed"), True),
        ]:
            value = copy.deepcopy(self.value)
            value[path[0]][path[1]] = replacement
            self.assertFalse(self.tool.validate(value, live=False))

    def test_vector_and_call_census_tamper_is_rejected(self) -> None:
        for field in ("vectors", "original_calls", "log2f_calls", "atan2f_calls", "unique_replayed_vectors"):
            value = copy.deepcopy(self.value)
            value["native_table"][field] += 1
            self.assertFalse(self.tool.validate(value, live=False))

    def test_embedded_native_row_tamper_is_rejected(self) -> None:
        value = copy.deepcopy(self.value)
        value["native_rows"][0]["native_ucrt_result_bits"] = "0x00000000"
        self.assertFalse(self.tool.validate(value, live=False))


if __name__ == "__main__":
    unittest.main()

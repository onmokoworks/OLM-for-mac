from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "tools/emulation/test_olmdirectionalblur_type3_public_owner_boundary_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_type3_public_owner_boundary_20260814.json"
GEN_SHA256 = "db3917cd47cc7eb8b64ae2985e622574c68064dfce7c62e2f2c76ec4b1291c27"


def load_module():
    spec = importlib.util.spec_from_file_location("dblur_type3_public_boundary", GEN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalType3PublicOwnerBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_is_externally_pinned(self) -> None:
        self.assertEqual(hashlib.sha256(GEN.read_bytes()).hexdigest(), GEN_SHA256)

    def test_saved_report_validates(self) -> None:
        self.assertTrue(self.module.validate(self.report))

    def test_exact_rows(self) -> None:
        self.assertEqual([row["depth"] for row in self.report["rows"]], [8, 16, 32])
        self.assertTrue(all(row["raw_exact"] and row["output_padding_preserved"] for row in self.report["rows"]))

    def test_recanonicalized_row_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["rows"][0]["windows_exported_smart_sha256"] = "0" * 64
        changed["rows_sha256"] = self.module.canonical_sha(changed["rows"])
        self.assertFalse(self.module.validate(changed, live=False))

    def test_claim_tamper_rejected(self) -> None:
        changed = copy.deepcopy(self.report)
        changed["boundary"]["native_windows_exercised"] = True
        self.assertFalse(self.module.validate(changed, live=False))


if __name__ == "__main__":
    unittest.main()

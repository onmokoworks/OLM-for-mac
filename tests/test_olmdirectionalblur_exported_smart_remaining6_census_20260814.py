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
GENERATOR = ROOT / "tools/emulation/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_exported_smart_remaining6_census_20260814.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("remaining6_census", GENERATOR)
    if not spec or not spec.loader:
        raise RuntimeError("generator import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RemainingSixCensusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_identity_and_persisted_report(self) -> None:
        self.assertTrue(self.module.validate(self.report))

    def test_default_is_read_only(self) -> None:
        before = REPORT.read_bytes()
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_recanonicalized_row_and_diff_tamper_rejected(self) -> None:
        attacks = []
        extra_row = copy.deepcopy(self.report)
        extra_row["rows"][0]["unexpected"] = True
        attacks.append(extra_row)
        extra_diff = copy.deepcopy(self.report)
        extra_diff["rows"][0]["historical_diffs"][0]["unexpected"] = True
        attacks.append(extra_diff)
        changed_value = copy.deepcopy(self.report)
        changed_value["rows"][0]["historical_diffs"][0]["mac_value"] = 0
        attacks.append(changed_value)
        changed_hex = copy.deepcopy(self.report)
        changed_hex["rows"][0]["historical_diffs"][0]["mac_hex"] = "00"
        attacks.append(changed_hex)
        paired_hex = copy.deepcopy(self.report)
        paired_hex["rows"][0]["historical_diffs"][0].update(
            {"mac_hex": "fd", "worker_hex": "fe", "mac_value": 253, "worker_value": 254}
        )
        attacks.append(paired_hex)
        reordered = copy.deepcopy(self.report)
        reordered["rows"][0], reordered["rows"][1] = reordered["rows"][1], reordered["rows"][0]
        attacks.append(reordered)
        for attack in attacks:
            attack["rows_sha256"] = self.module.digest(attack["rows"])
            self.assertFalse(self.module.validate(attack, live=False))

    def test_identity_summary_boundary_and_schema_tamper_rejected(self) -> None:
        attacks = []
        extra_identity = copy.deepcopy(self.report)
        extra_identity["identities"]["unexpected"] = "x"
        attacks.append(extra_identity)
        changed_identity = copy.deepcopy(self.report)
        changed_identity["identities"]["production_source_sha256"] = "0" * 64
        attacks.append(changed_identity)
        changed_summary = copy.deepcopy(self.report)
        changed_summary["summary"]["PF32_words_different"] = 19
        attacks.append(changed_summary)
        changed_boundary = copy.deepcopy(self.report)
        changed_boundary["boundary"]["actual_aex_iterate_callback_guest_code_executed"] = False
        attacks.append(changed_boundary)
        changed_static = copy.deepcopy(self.report)
        changed_static["static_control_flow"]["separate_post_owner_pixel_transform_call"] = True
        attacks.append(changed_static)
        extra_top = copy.deepcopy(self.report)
        extra_top["unexpected"] = True
        attacks.append(extra_top)
        for attack in attacks:
            self.assertFalse(self.module.validate(attack))


if __name__ == "__main__":
    unittest.main()

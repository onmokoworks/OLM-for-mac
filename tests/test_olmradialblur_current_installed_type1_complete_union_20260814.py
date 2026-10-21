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
GENERATOR = ROOT / "tools/emulation/test_olmradialblur_current_installed_type1_complete_union_20260814.py"
REPORT = ROOT / "refs/conformance/olmradialblur_current_installed_type1_complete_union_20260814.json"
NOTE = REPORT.with_suffix(".md")
GENERATOR_SHA256 = "1d32e213c64a7687fc31a3469aa5434290c3ef875310f79e9f94643baeb79420"
REPORT_SHA256 = "58f02746c8e6d364fc4bec2f60329cf73168be5f2309ba2d80cef4720bb1c444"
NOTE_SHA256 = "fc934be8db3afdcfc77a77666444a6b5b491cf16da06552b5bb930155484f722"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("radial_installed_type1", GENERATOR)
    if not spec or not spec.loader:
        raise RuntimeError("generator import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RadialInstalledType1CompleteUnionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_authoritative_hashes_and_live_validation(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(NOTE), NOTE_SHA256)
        self.assertTrue(self.module.validate(self.report))

    def test_default_is_read_only(self) -> None:
        before = (REPORT.read_bytes(), NOTE.read_bytes())
        run = subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("PASS_OLMRADIALBLUR_CURRENT_INSTALLED_TYPE1_COMPLETE_UNION_AE_FREE", run.stdout)
        self.assertEqual((REPORT.read_bytes(), NOTE.read_bytes()), before)

    def test_complete_family_partition(self) -> None:
        families = self.report["families"]
        self.assertEqual([row["name"] for row in families],
                         ["pairwise", "edge_noise", "size_noise", "dual_strength", "any_size_edge_noise"])
        self.assertEqual(sum(row["positive_cells_per_slice"] for row in families), 106)
        self.assertEqual(sum(row["mutation_rejects_per_slice"] for row in families), 57)
        self.assertEqual(self.report["families_sha256"], self.module.canonical(families))
        self.assertEqual(self.report["summary"]["positive_cells_total"], 212)
        self.assertEqual(self.report["summary"]["mutation_rejects_total"], 114)

    def test_recanonicalized_family_and_transcript_tamper_rejected(self) -> None:
        attacks = []
        swapped = copy.deepcopy(self.report)
        swapped["families"][0], swapped["families"][1] = swapped["families"][1], swapped["families"][0]
        attacks.append(swapped)
        count = copy.deepcopy(self.report)
        count["families"][0]["positive_cells_per_slice"] = 17
        attacks.append(count)
        line = copy.deepcopy(self.report)
        line["families"][0]["runs"][0]["lines"][0] += " changed"
        attacks.append(line)
        architecture = copy.deepcopy(self.report)
        architecture["families"][0]["runs"][0]["architecture"] = "ppc64"
        attacks.append(architecture)
        extra = copy.deepcopy(self.report)
        extra["families"][0]["unexpected"] = True
        attacks.append(extra)
        for attack in attacks:
            attack["families_sha256"] = self.module.canonical(attack["families"])
            self.assertFalse(self.module.validate(attack, live=False))

    def test_claim_identity_and_summary_tamper_rejected(self) -> None:
        attacks = []
        for section, key, value in (
            ("scope", "native_after_effects", True),
            ("scope", "production_or_install_changed", True),
            ("summary", "positive_cells_per_slice", 105),
            ("summary", "classic_smart_padded_output_exact", False),
            ("authorities", "installed_binary", "0" * 64),
        ):
            changed = copy.deepcopy(self.report)
            changed[section][key] = value
            attacks.append(changed)
        claim = copy.deepcopy(self.report)
        claim["claim_boundary"] = "arbitrary Type1 inputs are exact"
        attacks.append(claim)
        top = copy.deepcopy(self.report)
        top["unexpected"] = True
        attacks.append(top)
        for attack in attacks:
            self.assertFalse(self.module.validate(attack, live=False))

    def test_ae_process_set_empty(self) -> None:
        self.assertEqual(self.module.ae_processes(), [])
        self.assertEqual(self.report["after_effects_processes"], [])


if __name__ == "__main__":
    unittest.main()

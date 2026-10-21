from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "handoffs/olmradialblur_type3_all_depth_universal_candidate_20260813/verify_candidate.py"
REPORT = VERIFIER.parent / "build_identity.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module():
    spec = importlib.util.spec_from_file_location("radial_current_candidate", VERIFIER)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class RadialCurrentUniversalCandidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = module()
        cls.report = json.loads(REPORT.read_text())

    def test_pinned_verifier_and_report(self):
        self.assertEqual(sha(VERIFIER), "f7ae638b4004b83e5f9c820c89abfa8084763f2d6a92f40b74c87d0222f15f8c")
        self.assertEqual(sha(REPORT), "c3e0db105c0bf0b967ccd3ccd788d66ff779671d492c408ad306dabe9259ed70")

    def test_default_is_read_only(self):
        before = REPORT.read_bytes()
        subprocess.run([sys.executable, str(VERIFIER)], cwd=ROOT, check=True)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_live_candidate(self):
        self.mod.validate(self.report)

    def test_authority_and_binary_tamper_rejected(self):
        for mutation in (
            lambda d: d["authorities"]["source"].__setitem__("sha256", "0" * 64),
            lambda d: d["authorities"]["type3_all_depth"].__setitem__("sha256", "f" * 64),
            lambda d: d["candidate"].__setitem__("binary_sha256", "0" * 64),
            lambda d: d["candidate"]["slices"][0].__setitem__("minos", "26.2"),
            lambda d: d["candidate"]["codesign"].__setitem__("signature", "Developer ID"),
            lambda d: d["scope"].__setitem__("after_effects_launched", True),
        ):
            altered = copy.deepcopy(self.report)
            mutation(altered)
            with self.assertRaises(ValueError):
                self.mod.validate(altered)

    def test_unknown_key_rejected(self):
        altered = copy.deepcopy(self.report)
        altered["extra"] = True
        with self.assertRaises(ValueError):
            self.mod.validate(altered)


if __name__ == "__main__":
    unittest.main()

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
VERIFIER = ROOT / "handoffs/olmblur_pf16_legacy_retained_public_universal_candidate_20260813/verify_candidate.py"
REPORT = VERIFIER.parent / "build_identity.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


SPEC = importlib.util.spec_from_file_location("blur_legacy_candidate", VERIFIER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Candidate(unittest.TestCase):
    def test_external_pins(self) -> None:
        self.assertEqual(sha(VERIFIER), "266fffb9ea65851b8783530d28fd6fe0a938c91a196b5873d191e83d512f70a4")
        self.assertEqual(sha(REPORT), "063513dde58e31b2ad1bae6f479beeb7ee76f92c887f6b03acb67cad28786e44")

    def test_default_read_only(self) -> None:
        before = REPORT.read_bytes()
        subprocess.run([sys.executable, str(VERIFIER)], cwd=ROOT, check=True)
        self.assertEqual(REPORT.read_bytes(), before)

    def test_compiled_inputs(self) -> None:
        data = json.loads(REPORT.read_text())
        self.assertEqual(len(data["compiled_inputs"]), 29)
        MODULE.validate(data)

    def test_recanonicalized_tamper(self) -> None:
        original = json.loads(REPORT.read_text())
        for mutation in (
            lambda d: d.update(extra=True),
            lambda d: d["authorities"]["source"].update(sha256="0" * 64),
            lambda d: d["authorities"]["owner_legacy_retained"].update(sha256="0" * 64),
            lambda d: d.update(compiled_inputs_digest="0" * 64),
            lambda d: d["compiled_inputs"][0].update(bytes=0),
            lambda d: d["candidate"].update(binary_sha256="0" * 64),
            lambda d: d["candidate"]["slices"][0].update(minos="26.2"),
            lambda d: d["candidate"]["slices"][1].update(exports=["_EffectMain"]),
            lambda d: d["candidate"]["inventory"][0].update(sha256="0" * 64),
            lambda d: d["candidate"]["codesign"].update(signature="Developer ID"),
            lambda d: d["installed_observation"].update(candidate_not_installed=False),
            lambda d: d["scope"].update(after_effects_launched=True),
        ):
            data = copy.deepcopy(original)
            mutation(data)
            with self.assertRaises((ValueError, RuntimeError, KeyError, TypeError)):
                MODULE.validate(data)


if __name__ == "__main__":
    unittest.main()

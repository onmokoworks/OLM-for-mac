from __future__ import annotations

import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "handoffs/olmradialblur_smart_cleanup_universal_candidate_20260813"
VALIDATOR = HERE / "test_build_identity.py"
MANIFEST = HERE / "build_identity.json"
EXECUTABLE = HERE / "candidate/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RadialSmartCleanupCandidate(unittest.TestCase):
    def test_external_identities_and_live_validation(self) -> None:
        self.assertEqual(sha(VALIDATOR), "6a0a5f2cab16464441848d59c54f3983112f8e47225453e0f08a99472394307c")
        self.assertEqual(sha(MANIFEST), "44fed698aecd0f8a71d4afc5bbe5f58a393037b3068ed44db05037c903e13abe")
        self.assertEqual(sha(EXECUTABLE), "1bd0d6eeebc646272b0d1c13a963609dd458eea269df133d49978b6f3a66baa6")
        subprocess.run([sys.executable, "-m", "unittest", str(VALIDATOR), "-q"],
                       cwd=ROOT, check=True)


if __name__ == "__main__":
    unittest.main()

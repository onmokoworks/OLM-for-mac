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
TOOL = ROOT / "tools/emulation/audit_olm_hostless_batch4_install_readiness_20260813.py"
REPORT = ROOT / "refs/conformance/olm_hostless_batch4_install_readiness_20260813.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
GENERATOR_SHA256 = "8fae1cf657a881dbf2b3eda41d6abfab1ac98aa1d12bfb72590a4259f0a96e0e"
REPORT_SHA256 = "62def0d8d85a70b78266ba74ae1197f1abe918872546b526655cd329082f2093"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("batch4_readiness", TOOL)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class Batch4Readiness(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(REPORT.read_text())

    def test_external_identities(self) -> None:
        self.assertEqual(sha256(TOOL), GENERATOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)

    def test_default_is_live_and_read_only(self) -> None:
        watched = [REPORT, IDENTITY]
        watched += [audit.SPECS[name]["bundle"] / "Contents/MacOS" / name for name in audit.SPECS]
        before = {str(path): sha256(path) for path in watched}
        result = subprocess.run([sys.executable, str(TOOL)], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertIn("PASS_HOSTLESS_BATCH4", result.stdout)
        self.assertEqual(before, {str(path): sha256(path) for path in watched})

    def test_live_report_validates(self) -> None:
        audit.validate(copy.deepcopy(self.data))

    def test_recanonicalized_tamper_groups_fail_closed(self) -> None:
        mutations = (
            lambda d: d.update(extra=True),
            lambda d: d["accepted_identity"].update(sha256="0" * 64),
            lambda d: d["candidates"]["OLMBlur"]["source"].update(sha256="1" * 64),
            lambda d: d["candidates"]["OLMSmoother"]["bundle"]["inventory"][0].update(bytes=0),
            lambda d: d["candidates"]["OLMSmoother2"]["bundle"]["slices"]["arm64"].update(exports=[]),
            lambda d: d["candidates"]["OLMColorKey"]["bundle"].update(strict_deep_adhoc_codesign=False),
            lambda d: d["installed_before"]["OLMBlur"].update(binary_sha256="2" * 64),
            lambda d: d["smoother_v3_post_build_allowed_drift"].clear(),
            lambda d: d.update(after_effects_processes=[123]),
            lambda d: d["scope"].update(installed=True),
        )
        for mutation in mutations:
            changed = copy.deepcopy(self.data)
            mutation(changed)
            with self.subTest(changed=changed):
                with self.assertRaises((ValueError, RuntimeError)):
                    audit.validate(changed)


if __name__ == "__main__":
    unittest.main()

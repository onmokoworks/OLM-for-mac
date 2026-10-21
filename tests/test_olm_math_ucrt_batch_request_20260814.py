from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools/emulation/test_olm_math_ucrt_batch_request_20260814.py"
REPORT = ROOT / "refs/conformance/olm_math_ucrt_batch_request_20260814.json"
NOTE = REPORT.with_suffix(".md")
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olm_math_ucrt_batch_20260814"
ANALYZER = ROOT / "scripts/analyze_olm_math_ucrt_batch_return_20260814.py"
GENERATOR_SHA256 = "9c562e6109e10528cf7bfb20916c96163940ee6129a14c70c6b8d20163b8def9"
REPORT_SHA256 = "db4ac894a156895d5c1ecfdd9a777196710913f1a0c5095053a2d47493312b2d"
ZIP_SHA256 = "3bb9f841ea7cb0585cc9855473ce9bb45a140eb838486fd7a9bb39646a666637"
ANALYZER_SHA256 = "d5da42b05446d0dcd25790ce5bbcafb1d157bcae0db86b03588133fec895c91d"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("olm_math_ucrt_batch", GENERATOR)
    if not spec or not spec.loader:
        raise RuntimeError("generator import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OLMUcrtMathBatchRequestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_identities_and_live_validation(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertEqual(sha256(REPORT), REPORT_SHA256)
        self.assertEqual(sha256(ANALYZER), ANALYZER_SHA256)
        self.assertTrue(self.module.validate(self.report))
        self.assertEqual(self.report["return_validation"]["sha256"], ANALYZER_SHA256)
        self.assertEqual(self.report["children"]["directional"]["vectors"], 494)
        self.assertEqual(self.report["children"]["directional_powf"]["vectors"], 787)
        self.assertEqual(self.report["children"]["distance"]["vectors"], 63)
        self.assertEqual(self.report["package"]["transfer_zip_sha256"], ZIP_SHA256)
        self.assertEqual(sha256(self.module.PACKAGE_ZIP), ZIP_SHA256)

    def test_default_and_validate_only_are_read_only(self) -> None:
        before = {path: path.read_bytes() for path in (REPORT, NOTE)}
        for extra in ([], ["--validate-only"]):
            run = subprocess.run(
                [sys.executable, str(GENERATOR), *extra], cwd=ROOT,
                capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("PASS_OLM_MATH_UCRT_BATCH_REQUEST_READY_AE_FREE", run.stdout)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_scope_and_report_tamper_rejected(self) -> None:
        attacks = []
        for section, key, value in (
            ("boundary", "production_admission_changed", True),
            ("boundary", "native_windows_return_included", True),
            ("boundary", "returned_words_alone_sufficient_for_promotion", True),
            ("acceptance", "after_effects_required", True),
            ("acceptance", "all_1344_rows_required", False),
        ):
            changed = copy.deepcopy(self.report)
            changed[section][key] = value
            attacks.append(changed)
        changed = copy.deepcopy(self.report)
        changed["unexpected"] = True
        attacks.append(changed)
        for attack in attacks:
            self.assertFalse(self.module.validate(attack))

    def test_manifest_and_script_tamper_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="olm-ucrt-batch-") as temp:
            package = Path(temp) / "package"
            shutil.copytree(PACKAGE, package)
            manifest_path = package / "request_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["vectors"]["total"] = 220
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
            with self.assertRaises(ValueError):
                self.module.validate_package(package)
            manifest_path.write_bytes((PACKAGE / manifest_path.name).read_bytes())

            script_path = package / "run_olm_math_ucrt_batch.ps1"
            script_path.write_text(script_path.read_text().replace("-ne 494", "-ne 493"))
            with self.assertRaises(ValueError):
                self.module.validate_package(package)

    def test_exact_ae_free_batch_contract(self) -> None:
        self.assertEqual(self.report["acceptance"], {
            "after_effects_required": False,
            "all_1344_rows_required": True,
            "one_amd64_process": True,
            "same_system32_ucrt_identity_required": True,
        })
        script = (PACKAGE / "run_olm_math_ucrt_batch.ps1").read_text().lower()
        for forbidden in ("afterfx", "aerender", "doscript", "start-process"):
            self.assertNotIn(forbidden, script)


if __name__ == "__main__":
    unittest.main()

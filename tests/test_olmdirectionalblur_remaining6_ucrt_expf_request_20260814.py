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
GENERATOR = ROOT / "tools/emulation/test_olmdirectionalblur_remaining6_ucrt_expf_request_20260814.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_remaining6_ucrt_expf_request_20260814.json"
PACKAGE = ROOT / "refs/runtime_trace_packages/olm_runtime_trace_olmdirectionalblur_remaining6_ucrt_expf_20260814"
GENERATOR_SHA256 = "b8bccea3d1a5011cea41aa963564bb0a51594c2c69837d50db7b2b0007712ce9"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("directional_ucrt_request", GENERATOR)
    if not spec or not spec.loader:
        raise RuntimeError("generator import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DirectionalRemainingSixUcrtRequestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.report = json.loads(REPORT.read_text())

    def test_generator_and_persisted_report(self) -> None:
        self.assertEqual(sha256(GENERATOR), GENERATOR_SHA256)
        self.assertTrue(self.module.validate(self.report))

    def test_default_and_validate_only_are_read_only(self) -> None:
        before = {path: path.read_bytes() for path in (REPORT, REPORT.with_suffix(".md"))}
        for extra in ([], ["--validate-only"]):
            run = subprocess.run(
                [sys.executable, str(GENERATOR), *extra], cwd=ROOT,
                capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("PASS_OLMDIRECTIONALBLUR_REMAINING6_NATIVE_UCRT_REQUEST_READY_AE_FREE", run.stdout)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_float32_vector_reconstruction_and_boundaries(self) -> None:
        rows = self.module.expected_vectors()
        self.assertEqual(len(rows), 494)
        self.assertEqual([(row["count"], row["index"]) for row in rows[:9]],
                         [(8, index) for index in range(8)] + [(50, 0)])
        self.assertEqual((rows[-1]["count"], rows[-1]["index"]), (240, 239))
        self.assertEqual(self.module.digest(rows), self.report["vectors"]["rows_sha256"])

    def test_vector_and_manifest_mutations_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="directional-ucrt-request-tamper-") as temp:
            base = Path(temp) / "package"
            shutil.copytree(PACKAGE, base)
            vectors_path = base / "expf_vectors.json"
            original_vectors = json.loads(vectors_path.read_text())
            mutations = []
            changed_first = copy.deepcopy(original_vectors)
            changed_first[0]["argument_bits"] = "0x00000000"
            mutations.append((vectors_path, changed_first))
            changed_middle = copy.deepcopy(original_vectors)
            changed_middle[57]["numerator_bits"] = "0x00000000"
            mutations.append((vectors_path, changed_middle))
            reordered = copy.deepcopy(original_vectors)
            reordered[-1], reordered[-2] = reordered[-2], reordered[-1]
            mutations.append((vectors_path, reordered))
            extra_key = copy.deepcopy(original_vectors)
            extra_key[0]["unexpected"] = True
            mutations.append((vectors_path, extra_key))
            for path, value in mutations:
                path.write_text(json.dumps(value, indent=2) + "\n")
                with self.assertRaises(ValueError):
                    self.module.validate_package(base, live=False)
                path.write_bytes((PACKAGE / path.name).read_bytes())

            manifest_path = base / "request_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            for mutator in (
                lambda value: value.update({"unexpected": True}),
                lambda value: value["provenance"].update({"production_source_sha256": "0" * 64}),
                lambda value: value["claims_not_made"].remove("No production admission from this table alone"),
                lambda value: value["target"].update({"path": "C:\\temp\\ucrtbase.dll"}),
            ):
                changed = copy.deepcopy(manifest)
                mutator(changed)
                manifest_path.write_text(json.dumps(changed, indent=2) + "\n")
                with self.assertRaises(ValueError):
                    self.module.validate_package(base, live=False)
                manifest_path.write_bytes((PACKAGE / manifest_path.name).read_bytes())

    def test_capture_code_and_file_set_mutations_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="directional-ucrt-request-code-") as temp:
            base = Path(temp) / "package"
            shutil.copytree(PACKAGE, base)
            csharp = base / "UcrtExpfCapture.cs"
            csharp.write_text(csharp.read_text().replace('EntryPoint = "expf"', 'EntryPoint = "exp"'))
            with self.assertRaises(ValueError):
                self.module.validate_package(base, live=False)
            csharp.write_bytes((PACKAGE / csharp.name).read_bytes())

            script = base / "run_olmdirectionalblur_remaining6_ucrt_expf.ps1"
            script.write_text(script.read_text().replace("System32\\ucrtbase.dll", "SysWOW64\\ucrtbase.dll"))
            with self.assertRaises(ValueError):
                self.module.validate_package(base, live=False)
            script.write_bytes((PACKAGE / script.name).read_bytes())

            (base / "unexpected.txt").write_text("unexpected\n")
            with self.assertRaises(ValueError):
                self.module.validate_package(base, live=False)

    def test_report_claim_and_schema_tamper_rejected(self) -> None:
        attacks = []
        for path, value in (
            (("boundary", "production_admission_changed"), True),
            (("boundary", "native_windows_return_included"), True),
            (("acceptance", "after_effects_required"), True),
            (("vectors", "count"), 493),
            (("target", "path"), "C:\\temp\\ucrtbase.dll"),
        ):
            changed = copy.deepcopy(self.report)
            changed[path[0]][path[1]] = value
            attacks.append(changed)
        extra = copy.deepcopy(self.report)
        extra["unexpected"] = True
        attacks.append(extra)
        for attack in attacks:
            self.assertFalse(self.module.validate(attack))


if __name__ == "__main__":
    unittest.main()

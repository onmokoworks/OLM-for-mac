from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenericBetaWindowsOracleHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="generic_beta_oracle_test_")
        self.root = Path(self.temp.name)
        self.packager = load(ROOT / "scripts/package_generic_beta_windows_oracle.py", "generic_beta_packager_test")
        self.packager.OUT = self.root / "bundle"
        fake_aex_dir = self.root / "fake-aex"
        fake_aex_dir.mkdir()
        self.packager.AEX = {}
        for plugin in ("OLMToonDilate", "ColorKeep", "OLMColorKey"):
            path = fake_aex_dir / f"{plugin}.aex"
            path.write_bytes(f"deterministic fake AEX for {plugin}\n".encode())
            self.packager.AEX[plugin] = path
        self.assertEqual(self.packager.main(), 0)
        self.verifier = load(self.packager.OUT / "VERIFY_RETURN.py", "generic_beta_verifier_test")
        self.return_dir = self.root / "return"
        self.return_dir.mkdir()
        request = json.loads((self.packager.OUT / "campaign-manifest.json").read_text())
        rows = []
        for index, case in enumerate(request["cases"]):
            output = self.return_dir / f"output_{index:03d}.png"
            output.write_bytes(f"oracle-{case['id']}\n".encode())
            source = next(row for row in request["inputs"] if row["id"] == case["input"])
            rows.append({
                "id": case["id"], "plugin": case["plugin"], "input": case["input"],
                "parameters": case["parameter_set"], "status": "ok", "exit_code": 0,
                "render_error": 0, "input_sha256": source["sha256"],
                "output_sha256": self.verifier.sha(output), "output_file": output.name,
            })
        self.report = {
            "schema_version": 1, "request_id": request["request_id"], "status": "complete",
            "worker": {"path": "C:\\tools\\aex-guest-worker.exe", "sha256": "a" * 64},
            "aex_sha256": {}, "cases": rows,
        }
        self._write_report()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_report(self) -> None:
        (self.return_dir / "GENERIC_BETA_WINDOWS_ORACLE_RETURN.json").write_text(json.dumps(self.report))

    def _verify(self) -> int:
        argv = ["verify", str(self.return_dir), "--request", str(self.packager.OUT / "campaign-manifest.json")]
        with mock.patch.object(sys, "argv", argv):
            return self.verifier.main()

    def test_success_return(self) -> None:
        self.assertEqual(self._verify(), 0)

    def test_checksum_tamper_is_rejected(self) -> None:
        with (self.packager.OUT / "inputs/odd_alpha_17x11.png").open("ab") as handle:
            handle.write(b"tamper")
        with self.assertRaisesRegex(SystemExit, "request checksum mismatch"):
            self._verify()

    def test_missing_case_is_rejected(self) -> None:
        self.report["cases"].pop()
        self._write_report()
        with self.assertRaisesRegex(SystemExit, "identity/cardinality"):
            self._verify()

    def test_duplicate_case_is_rejected(self) -> None:
        self.report["cases"][-1] = dict(self.report["cases"][0])
        self._write_report()
        with self.assertRaisesRegex(SystemExit, "identity/cardinality"):
            self._verify()

    def test_missing_worker_hash_is_rejected(self) -> None:
        del self.report["worker"]["sha256"]
        self._write_report()
        with self.assertRaisesRegex(SystemExit, "worker hash"):
            self._verify()

    def test_render_error_is_rejected(self) -> None:
        self.report["cases"][0]["render_error"] = 7
        self._write_report()
        with self.assertRaisesRegex(SystemExit, "failed execution"):
            self._verify()

    def test_nonzero_exit_code_is_rejected(self) -> None:
        self.report["cases"][0]["exit_code"] = 9
        self._write_report()
        with self.assertRaisesRegex(SystemExit, "failed execution"):
            self._verify()

    def test_runner_max_pixels_selects_odd_and_sd_and_marks_hd_pending(self) -> None:
        runner = load(ROOT / "scripts/run_generic_beta_oracle_bundle.py", "generic_beta_runner_test")
        manifest = json.loads((self.packager.OUT / "campaign-manifest.json").read_text())
        selected, pending = runner.select_cases(manifest, 640 * 360)
        self.assertEqual(len(selected), 14)
        self.assertEqual(len(pending), 7)
        self.assertTrue(all("hd_random" not in row["id"] for row in selected))
        self.assertTrue(all("hd_random" in case_id for case_id in pending))

    def test_runner_selects_explicit_case(self) -> None:
        runner = load(ROOT / "scripts/run_generic_beta_oracle_bundle.py", "generic_beta_runner_case_test")
        manifest = json.loads((self.packager.OUT / "campaign-manifest.json").read_text())
        case_id = "ColorKeep_hd_random_count_1"
        selected, pending = runner.select_cases(manifest, None, {case_id})
        self.assertEqual([row["id"] for row in selected], [case_id])
        self.assertEqual(len(pending), 20)


if __name__ == "__main__":
    unittest.main()

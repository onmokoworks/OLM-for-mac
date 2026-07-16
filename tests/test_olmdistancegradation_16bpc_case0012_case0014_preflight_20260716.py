from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "preflight_olmdistancegradation_16bpc_case0012_case0014_proof_render_20260716.py"


def load_module():
    spec = importlib.util.spec_from_file_location("olmdg_preflight_20260716", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DistanceGradationProofRenderPreflightTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="olmdg_preflight_20260716_"))
        self.module = load_module()
        self.request_dir = self.tmp / "request"
        (self.request_dir / "input").mkdir(parents=True)
        (self.request_dir / "expected").mkdir()
        self.media_core = self.tmp / "MediaCore"
        self.media_core.mkdir()
        self.plugin_binary = self._create_plugin(self.media_core / "OLMDistanceGradation.plugin")
        self.expected_sha256 = hashlib.sha256(self.plugin_binary.read_bytes()).hexdigest()
        self._create_request()
        self._sync_module_canonical_identity()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _create_plugin(self, bundle: Path) -> Path:
        binary = bundle / "Contents" / "MacOS" / "OLMDistanceGradation"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"olmdg-proof-preflight-fixture\n")
        return binary

    def _create_request(self) -> None:
        request_manifest = {
            "kind": "olm_ae_pixel_validation_request",
            "request_id": self.module.REQUEST_ID,
            "reference_manifest": "reference_manifest.json",
            "input_dir": "input",
            "expected_dir": "expected",
            "cases": [],
        }
        reference_manifest = {
            "project": {"bits_per_channel": 16},
            "cases": [],
        }
        for case_id in self.module.CASE_IDS:
            suffix = case_id.split("__")[-1]
            before_name = f"{suffix}_before_effects.png"
            frame_name = f"{suffix}.png"
            request_manifest["cases"].append(
                {
                    "id": case_id,
                    "before_effects_frame": before_name,
                    "frame": frame_name,
                }
            )
            reference_manifest["cases"].append(
                {
                    "id": case_id,
                    "before_effects_frame": before_name,
                    "frame": frame_name,
                    "bits_per_channel": 16,
                    "comp": {"name": f"{case_id}_software_16bpc_24"},
                    "requested_effect": {
                        "name": "Distance Gradation",
                        "match_name": "OLM Distance Gradation",
                    },
                    "project_gpu_accel_type": {"current_name": "SOFTWARE"},
                }
            )
            (self.request_dir / "input" / before_name).write_bytes(b"input\n")
            (self.request_dir / "expected" / frame_name).write_bytes(b"expected\n")
        (self.request_dir / "request_manifest.json").write_text(
            json.dumps(request_manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.request_dir / "reference_manifest.json").write_text(
            json.dumps(reference_manifest, indent=2) + "\n",
            encoding="utf-8",
        )

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _sync_module_canonical_identity(self) -> None:
        request_manifest_path = self.request_dir / "request_manifest.json"
        reference_manifest_path = self.request_dir / "reference_manifest.json"
        request_manifest = self._read_json(request_manifest_path)
        reference_manifest = self._read_json(reference_manifest_path)
        request_cases = {case["id"]: case for case in request_manifest["cases"]}
        reference_cases = {case["id"]: case for case in reference_manifest["cases"]}
        canonical_cases = {}
        for case_id in self.module.CASE_IDS:
            request_case = request_cases[case_id]
            reference_case = reference_cases[case_id]
            before_path = self.request_dir / "input" / request_case["before_effects_frame"]
            frame_path = self.request_dir / "expected" / request_case["frame"]
            canonical_cases[case_id] = {
                "before_effects_frame": request_case["before_effects_frame"],
                "before_effects_frame_sha256": hashlib.sha256(before_path.read_bytes()).hexdigest(),
                "frame": request_case["frame"],
                "frame_sha256": hashlib.sha256(frame_path.read_bytes()).hexdigest(),
                "reference_comp_name": reference_case["comp"]["name"],
                "requested_effect_match_name": reference_case["requested_effect"]["match_name"],
                "project_gpu_accel_type": reference_case["project_gpu_accel_type"]["current_name"],
                "bits_per_channel": reference_case["bits_per_channel"],
            }
        self.module.CANONICAL_REQUEST_MANIFEST_SHA256 = hashlib.sha256(
            request_manifest_path.read_bytes()
        ).hexdigest()
        self.module.CANONICAL_REFERENCE_MANIFEST_SHA256 = hashlib.sha256(
            reference_manifest_path.read_bytes()
        ).hexdigest()
        self.module.CANONICAL_REQUEST_CASES = canonical_cases
        self.module.CANONICAL_REQUEST_IDENTITY = {
            "request_id": self.module.REQUEST_ID,
            "request_manifest_sha256": self.module.CANONICAL_REQUEST_MANIFEST_SHA256,
            "reference_manifest_sha256": self.module.CANONICAL_REFERENCE_MANIFEST_SHA256,
            "cases": canonical_cases,
        }

    def _completed(self, args: list[str], *, stdout: str = "", stderr: str = "", returncode: int = 0):
        return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr=stderr)

    def test_refuses_without_disposable_project_flag_but_records_mapping_state(self) -> None:
        calls: list[list[str]] = []

        def fake_run(args):
            calls.append(list(args))
            if args[:2] == ["pgrep", "-x"]:
                return self._completed(args, stdout="7653\n", returncode=0)
            if args[:1] == ["vmmap"]:
                return self._completed(args, stdout="", returncode=0)
            raise AssertionError(args)

        output_json = self.tmp / "report.json"
        output_md = self.tmp / "report.md"
        with mock.patch.object(self.module, "run_subprocess", side_effect=fake_run):
            rc = self.module.main(
                [
                    "--request-dir",
                    str(self.request_dir),
                    "--media-core-dir",
                    str(self.media_core),
                    "--expect-plugin-sha256",
                    self.expected_sha256,
                    "--output-json",
                    str(output_json),
                    "--output-md",
                    str(output_md),
                ]
            )

        self.assertEqual(rc, 2)
        report = json.loads(output_json.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "blocked_refused_missing_disposable_project_flag")
        self.assertEqual(report["running_ae_checks"]["single_running_pid"], 7653)
        self.assertFalse(report["running_ae_checks"]["dg_binary_mapped_in_single_running_ae"])
        self.assertTrue(report["installed_plugin_checks"]["sha256_matches_expected"])
        self.assertTrue(report["request_checks"]["request_manifest_sha256_matches_canonical"])
        self.assertTrue(report["request_checks"]["reference_manifest_sha256_matches_canonical"])
        self.assertIn("proof_render:explicit_disposable_project_flag_required", report["failures"]["guard"])
        self.assertEqual(calls, [["pgrep", "-x", "After Effects"], ["vmmap", "7653"]])

    def test_becomes_ready_with_explicit_disposable_project_flag(self) -> None:
        binary_path = self.plugin_binary.resolve()

        def fake_run(args):
            if args[:2] == ["pgrep", "-x"]:
                return self._completed(args, stdout="7653\n", returncode=0)
            if args[:1] == ["vmmap"]:
                return self._completed(
                    args,
                    stdout=f"__TEXT 00000000-00000000 [ 4K] r-x/r-x SM=COW  {binary_path}\n",
                    returncode=0,
                )
            raise AssertionError(args)

        output_json = self.tmp / "ready.json"
        with mock.patch.object(self.module, "run_subprocess", side_effect=fake_run):
            rc = self.module.main(
                [
                    "--request-dir",
                    str(self.request_dir),
                    "--media-core-dir",
                    str(self.media_core),
                    "--expect-plugin-sha256",
                    self.expected_sha256,
                    "--disposable-project",
                    "--output-json",
                    str(output_json),
                ]
            )

        self.assertEqual(rc, 0)
        report = json.loads(output_json.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "ready_for_disposable_project_proof_render_no_execution")
        self.assertTrue(report["running_ae_checks"]["dg_binary_mapped_in_single_running_ae"])
        commands = report["proof_render_guard"]["preview_commands"]
        self.assertEqual([row["case_id"] for row in commands], list(self.module.CASE_IDS))
        self.assertIn("OLM_AE_FORCE_NEW_PROJECT=1", commands[0]["shell_command"])
        self.assertIn("run_ae_single_case.py", report["proof_render_guard"]["existing_runner_api"])
        self.assertEqual(
            report["canonical_request_identity"]["request_manifest_sha256"],
            self.module.CANONICAL_REQUEST_MANIFEST_SHA256,
        )

    def test_fails_closed_when_media_core_contains_recursive_bundle_descendants(self) -> None:
        self._create_plugin(self.media_core / "nested" / "OLMDistanceGradation.plugin")

        def fake_run(args):
            if args[:2] == ["pgrep", "-x"]:
                return self._completed(args, stdout="", returncode=1)
            raise AssertionError(args)

        output_json = self.tmp / "multi.json"
        with mock.patch.object(self.module, "run_subprocess", side_effect=fake_run):
            rc = self.module.main(
                [
                    "--request-dir",
                    str(self.request_dir),
                    "--media-core-dir",
                    str(self.media_core),
                    "--expect-plugin-sha256",
                    self.expected_sha256,
                    "--output-json",
                    str(output_json),
                ]
            )

        self.assertEqual(rc, 2)
        report = json.loads(output_json.read_text(encoding="utf-8"))
        self.assertEqual(report["installed_plugin_checks"]["bundle_count"], 2)
        self.assertEqual(
            report["installed_plugin_checks"]["recursive_descendant_candidates"],
            [
                str((self.media_core / "nested" / "OLMDistanceGradation.plugin").resolve()).replace(
                    str(Path(tempfile.gettempdir()).resolve()), "$TMP"
                )
            ],
        )
        self.assertIn("plugin:direct_media_core_bundle_only", report["failures"]["structural"])

    def test_rejects_case_asset_path_traversal(self) -> None:
        request_manifest_path = self.request_dir / "request_manifest.json"
        request_manifest = self._read_json(request_manifest_path)
        request_manifest["cases"][0]["before_effects_frame"] = "../escape.png"
        self._write_json(request_manifest_path, request_manifest)

        def fake_run(args):
            if args[:2] == ["pgrep", "-x"]:
                return self._completed(args, stdout="", returncode=1)
            raise AssertionError(args)

        output_json = self.tmp / "path-traversal.json"
        with mock.patch.object(self.module, "run_subprocess", side_effect=fake_run):
            rc = self.module.main(
                [
                    "--request-dir",
                    str(self.request_dir),
                    "--media-core-dir",
                    str(self.media_core),
                    "--expect-plugin-sha256",
                    self.expected_sha256,
                    "--output-json",
                    str(output_json),
                ]
            )

        self.assertEqual(rc, 2)
        report = self._read_json(output_json)
        self.assertEqual(report["status"], "blocked_structural_preflight_failure")
        self.assertIn(
            "olmdistancegradation_extended__case_0012:before_effects_frame_outside_base_dir",
            report["failures"]["structural"],
        )

    def test_blocks_malformed_json_without_traceback(self) -> None:
        (self.request_dir / "request_manifest.json").write_text("{\n", encoding="utf-8")

        def fake_run(args):
            if args[:2] == ["pgrep", "-x"]:
                return self._completed(args, stdout="", returncode=1)
            raise AssertionError(args)

        output_json = self.tmp / "malformed.json"
        with mock.patch.object(self.module, "run_subprocess", side_effect=fake_run):
            rc = self.module.main(
                [
                    "--request-dir",
                    str(self.request_dir),
                    "--media-core-dir",
                    str(self.media_core),
                    "--expect-plugin-sha256",
                    self.expected_sha256,
                    "--output-json",
                    str(output_json),
                ]
            )

        self.assertEqual(rc, 2)
        report = self._read_json(output_json)
        self.assertEqual(report["request_checks"]["request_manifest_load_status"], "blocked_malformed_json")
        self.assertIn("request_manifest:malformed_json", report["failures"]["structural"])

    def test_subprocess_failures_produce_deterministic_blocked_reports(self) -> None:
        cases = [
            (
                "pgrep_timeout",
                subprocess.TimeoutExpired(["pgrep", "-x", "After Effects"], timeout=120),
                "ae_process:pgrep_timeout",
                "timeout",
                None,
            ),
            (
                "pgrep_oserror",
                OSError("pgrep unavailable"),
                "ae_process:pgrep_oserror",
                "oserror",
                None,
            ),
            (
                "vmmap_timeout",
                subprocess.TimeoutExpired(["vmmap", "7653"], timeout=120),
                "ae_process:vmmap_timeout:7653",
                None,
                "vmmap_timeout",
            ),
            (
                "vmmap_oserror",
                OSError("vmmap unavailable"),
                "ae_process:vmmap_oserror:7653",
                None,
                "vmmap_oserror",
            ),
        ]
        for label, exc, failure, pgrep_status, vmmap_status in cases:
            with self.subTest(label=label):
                def fake_run(args):
                    if args[:2] == ["pgrep", "-x"]:
                        if label.startswith("pgrep_"):
                            raise exc
                        return self._completed(args, stdout="7653\n", returncode=0)
                    if args[:1] == ["vmmap"]:
                        raise exc
                    raise AssertionError(args)

                output_json = self.tmp / f"{label}.json"
                with mock.patch.object(self.module, "run_subprocess", side_effect=fake_run):
                    rc = self.module.main(
                        [
                            "--request-dir",
                            str(self.request_dir),
                            "--media-core-dir",
                            str(self.media_core),
                            "--expect-plugin-sha256",
                            self.expected_sha256,
                            "--output-json",
                            str(output_json),
                        ]
                    )

                self.assertEqual(rc, 2)
                report = self._read_json(output_json)
                self.assertEqual(report["status"], "blocked_structural_preflight_failure")
                self.assertIn(failure, report["failures"]["structural"])
                if pgrep_status is not None:
                    self.assertEqual(report["running_ae_checks"]["pgrep_status"], pgrep_status)
                if vmmap_status is not None:
                    self.assertEqual(report["running_ae_checks"]["processes"][0]["status"], vmmap_status)

    def test_redacts_local_paths_in_serialized_evidence(self) -> None:
        value = {
            "repo": str(self.module.ROOT / "scripts" / "runner.py"),
            "home": str(Path.home() / "Library" / "Plug-ins"),
            "tmp": str(self.tmp / "result.json"),
        }
        redacted = self.module.redact_local_paths(value)
        serialized = json.dumps(redacted)
        self.assertNotIn(str(Path.home()), serialized)
        self.assertNotIn(str(Path(tempfile.gettempdir()).resolve()), serialized)
        self.assertEqual(redacted["repo"], "$REPO/scripts/runner.py")
        self.assertTrue(redacted["home"].startswith("$HOME/"))
        self.assertTrue(redacted["tmp"].startswith("$TMP/"))


if __name__ == "__main__":
    unittest.main()

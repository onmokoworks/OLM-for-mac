from __future__ import annotations

import ast
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_olm_generic_beta_gate.py"
SPEC = importlib.util.spec_from_file_location("generic_beta_gate", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("generic beta gate module loader is unavailable")
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class GenericBetaGateTests(unittest.TestCase):
    def test_default_report_matches_the_public_audit_reference(self):
        self.assertEqual(GATE.DEFAULT_REPORT, ROOT / "reports/olm_generic_beta_gate.json")

    def test_manifest_is_explicit_unique_and_covers_ten_plugins_and_shared_gates(self):
        tests = [row[1] for row in GATE.MANIFEST]
        self.assertEqual(len(tests), len(set(tests)))
        plugins = {row[0] for row in GATE.MANIFEST}
        self.assertTrue({"ColorKeep", "OLMBlur", "OLMColorKey", "OLMDistanceGradation",
                         "OLMKiraKira", "OLMRadialBlur", "OLMSmoother", "OLMSmoother2",
                         "OLMToonDilate", "common-world", "property", "oracle",
                         "performance", "package-hash", "windows-oracle-bundle",
                         "ae-smoke", "gate-self", "documentation"}.issubset(plugins))
        self.assertTrue(all((ROOT / test).is_file() and (ROOT / source).is_file()
                            for _, test, source in GATE.MANIFEST))

    def test_stdlib_runner_pass_fail_and_skip_exit_codes(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_unit_") as raw:
            base = Path(raw)
            passing = base / "test_pass.py"
            failing = base / "test_fail.py"
            skipped = base / "test_skip.py"
            empty = base / "test_empty.py"
            passing.write_text("def test_ok():\n    assert 2 + 2 == 4\n", encoding="utf-8")
            failing.write_text("def test_bad():\n    assert False\n", encoding="utf-8")
            skipped.write_text("import pytest\n@pytest.mark.skipif(True, reason='bounded')\ndef test_skip(): pass\n", encoding="utf-8")
            empty.write_text("def helper(): pass\n", encoding="utf-8")
            self.assertEqual(GATE.run_test_file(passing), 0)
            self.assertEqual(GATE.run_test_file(failing), 1)
            self.assertEqual(GATE.run_test_file(skipped), 77)
            self.assertEqual(GATE.run_test_file(empty), 1)

    def test_parameterized_module_test_fails_instead_of_silent_ignore(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_parameterized_") as raw:
            path = Path(raw) / "test_parameterized.py"
            path.write_text(
                "def test_needs_fixture(tmp_path):\n    assert tmp_path\n",
                encoding="utf-8",
            )
            self.assertEqual(GATE.run_test_file(path), 1)

    def test_partial_skip_is_incomplete_for_the_outer_gate(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_partial_skip_") as raw:
            path = Path(raw) / "test_partial_skip.py"
            path.write_text(
                "import unittest\n"
                "def test_pass(): pass\n"
                "def test_skip(): raise unittest.SkipTest('missing evidence')\n",
                encoding="utf-8",
            )
            self.assertEqual(GATE.run_test_file(path), 77)

    def test_allow_skip_is_the_only_outer_gate_override_for_partial_evidence(self):
        skipped_row = {"plugin": "demo", "status": "SKIP"}
        manifest = [("demo", "unused-test", "unused-source")]
        with tempfile.TemporaryDirectory(prefix="generic_gate_allow_skip_") as raw:
            report = Path(raw) / "gate.json"
            with mock.patch.object(GATE, "MANIFEST", manifest), \
                 mock.patch.object(GATE, "execute_entry", return_value=skipped_row), \
                 mock.patch("builtins.print"):
                self.assertEqual(GATE.main(["--report", str(report)]), 1)
                self.assertEqual(
                    GATE.main(["--report", str(report), "--allow-skip"]), 0
                )

    def test_gate_self_and_required_dependency_closures_are_manifested(self):
        rows = {(plugin, test, source) for plugin, test, source in GATE.MANIFEST}
        self.assertIn((
            "gate-self",
            "tests/test_run_olm_generic_beta_gate.py",
            "scripts/run_olm_generic_beta_gate.py",
        ), rows)
        self.assertIn((
            "OLMKiraKira",
            "tests/test_olmkirakira_mode3_ui_length_beta_20260821.py",
            "mac/OLMKiraKira/OLMKiraKira.cpp",
        ), rows)
        self.assertIn((
            "OLMKiraKira",
            "tests/test_olmkirakira_mode3_ui_windows_owner_20260821.py",
            "tools/emulation/test_olmkirakira_mode3_ui_windows_owner_20260821.py",
        ), rows)
        directional_required = {
            "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
            "mac/OLMDirectionalBlur/OLMDirectionalBlur.h",
            "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.h",
            "core/dblur_frontonly.cpp",
            "core/dblur_frontonly.h",
            "core/dblur_generic_budget.h",
            "core/dblur_rotate.cpp",
            "core/dblur_rotate.h",
            "core/dblur_rowdriver.cpp",
            "core/dblur_rowdriver.h",
            "core/dblur_field.cpp",
            "core/dblur_field.h",
            "core/dblur_gaussian.h",
            "core/dblur_noise.h",
            "core/olm_checked_allocation.h",
            "core/olm_sha256_rows.h",
            "refs/conformance/dblur_mode1_backonly_portable_20260805.json",
        }
        self.assertTrue(
            directional_required.issubset(GATE.DIRECTIONAL_NEUTRAL_DEPENDENCIES)
        )
        kirakira_required = {
            "mac/OLMKiraKira/OLMKiraKira.cpp",
            "mac/OLMKiraKira/OLMKiraKira.h",
            "mac/OLMKiraKira/OLMKiraKira_Strings.cpp",
            "mac/OLMKiraKira/OLMKiraKira_Strings.h",
            "core/kirakira_gaussian.h",
            "core/kirakira_highlight.h",
            "core/kirakira_mode4.h",
            "core/kirakira_warp.h",
            "core/kirakira_merge2.h",
            "tests/olmkirakira_generic_beta_sanitizer_harness.cpp",
            "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp",
            "tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py",
            "tools/emulation/test_kirakira_mode3_default50_canonical.cpp",
            "refs/conformance/olmkirakira_mode3_geometry_generalization_actual_aex_20260810.json",
        }
        self.assertTrue(
            kirakira_required.issubset(GATE.KIRAKIRA_MODE3_UI_DEPENDENCIES)
        )
        kirakira_windows_owner_required = {
            "tests/test_olmkirakira_mode3_ui_windows_owner_20260821.py",
            "tools/emulation/test_olmkirakira_mode3_ui_windows_owner_20260821.py",
            "refs/conformance/olmkirakira_mode3_ui_windows_owner_20260821.json",
            "refs/conformance/olmkirakira_mode3_ui_windows_owner_20260821.sha256",
            "refs/upstream_official/20260619_olm_official_zips/SHA256SUMS.txt",
            "tests/olmkirakira_generic_beta_sanitizer_harness.cpp",
            "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp",
            "mac/OLMKiraKira/OLMKiraKira.cpp",
            "mac/OLMKiraKira/OLMKiraKira.h",
            "mac/OLMKiraKira/OLMKiraKira_Strings.cpp",
            "mac/OLMKiraKira/OLMKiraKira_Strings.h",
            "core/kirakira_gaussian.h",
            "core/kirakira_highlight.h",
            "core/kirakira_mode4.h",
            "core/kirakira_warp.h",
            "core/kirakira_merge2.h",
        }
        self.assertEqual(
            set(GATE.KIRAKIRA_MODE3_WINDOWS_OWNER_DEPENDENCIES),
            kirakira_windows_owner_required,
        )
        root = ROOT.resolve(strict=True)
        for dependency in GATE.KIRAKIRA_MODE3_WINDOWS_OWNER_DEPENDENCIES:
            with self.subTest(kirakira_windows_owner_dependency=dependency):
                relative = Path(dependency)
                self.assertFalse(relative.is_absolute())
                self.assertNotIn("..", relative.parts)
                resolved = (ROOT / relative).resolve(strict=True)
                try:
                    resolved.relative_to(root)
                except ValueError:
                    self.fail(f"Kira Windows-owner dependency escapes repo: {dependency}")
        external_sdk_prefixes = ("Headers/", "Util/", "Resources/")
        self.assertFalse(any(
            dependency.startswith(external_sdk_prefixes)
            for dependency in GATE.KIRAKIRA_MODE3_UI_DEPENDENCIES
        ))
        required = {
            "tests/test_ae_batch_png_integrity.py": {
                "scripts/run_ae_validation_batch.py",
                "scripts/ae_pixel_validation_render.jsx",
                "scripts/run_ae_single_case.py",
            },
            "tests/test_generic_beta_perf_smoke_runner.py": {
                "tools/perf/run_generic_beta_smoke.py",
                "reports/generic_beta_perf_smoke.json",
                *GATE.PERFORMANCE_DRIVERS,
            },
            "tests/test_beta_support_documentation.py": {
                "docs/BETA_SUPPORT.md",
                "reports/public_beta_completion_audit_20260820.json",
                "reports/public_beta_roi_v2_package_20260820.json",
                "refs/conformance/olm_all10_roi_v2_quick_ae_smoke_20260820.json",
                "refs/conformance/olm_all10_roi_v2_quick_ae_smoke_raw_20260820.json",
                "tools/emulation/test_dblur_generic_backonly_beta_20260821.py",
                "tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py",
                *GATE.DIRECTIONAL_NEUTRAL_DEPENDENCIES,
                "tests/test_olmkirakira_mode3_ui_length_beta_20260821.py",
                *GATE.KIRAKIRA_MODE3_UI_DEPENDENCIES,
            },
            "tests/test_olmkirakira_mode3_ui_length_beta_20260821.py": {
                *GATE.KIRAKIRA_MODE3_UI_DEPENDENCIES,
            },
            "tests/test_olmkirakira_mode3_ui_windows_owner_20260821.py": {
                *GATE.KIRAKIRA_MODE3_WINDOWS_OWNER_DEPENDENCIES,
            },
            "tests/test_olmradialblur_generic_budget_20260821.py": {
                *GATE.RADIAL_SIZE_NOISE_DEPENDENCIES,
            },
            "tests/test_olmradialblur_size_noise_effectmain_20260821.py": {
                *GATE.RADIAL_SIZE_NOISE_DEPENDENCIES,
                "Util/AEGP_SuiteHandler.cpp",
                "Util/AEGP_SuiteHandler.h",
                "Util/MissingSuiteError.cpp",
            },
            "tools/emulation/test_dblur_generic_backonly_beta_20260821.py": {
                *GATE.DIRECTIONAL_NEUTRAL_DEPENDENCIES,
            },
            "tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py": {
                *GATE.DIRECTIONAL_NEUTRAL_DEPENDENCIES,
                "mac/OLMDirectionalBlur/OLMDirectionalBlur_Strings.cpp",
                "Util/AEGP_SuiteHandler.cpp",
                "Util/MissingSuiteError.cpp",
            },
        }
        for test, expected in required.items():
            self.assertTrue(expected.issubset(GATE.DEPENDENCY_PATHS[test]))
            source = next(source for _, candidate, source in GATE.MANIFEST
                          if candidate == test)
            hashes = GATE.dependency_hashes(test, source)
            self.assertTrue(all(isinstance(value, str) and len(value) == 64
                                for value in hashes.values()), hashes)

    def test_missing_explicit_dependency_fails_before_launch(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_dependency_") as raw:
            base = Path(raw)
            test = base / "test_demo.py"
            source = base / "source.cpp"
            missing = base / "missing.jsx"
            test.write_text("def test_ok(): pass\n", encoding="utf-8")
            source.write_text("// source\n", encoding="utf-8")
            with mock.patch.dict(
                GATE.DEPENDENCY_PATHS, {str(test): (str(missing),)}, clear=False
            ), mock.patch.object(GATE.subprocess, "Popen") as popen:
                row = GATE.execute_entry(
                    "demo", str(test), str(source), timeout=1
                )
            self.assertEqual(row["status"], "FAIL")
            self.assertIn(str(missing), row["stderr"])
            popen.assert_not_called()

    def test_main_publishes_running_before_execution_then_final_same_run_id(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_atomic_") as raw:
            report = Path(raw) / "gate.json"
            report.write_text('{"status":"PASS","run_id":"stale"}\n')
            observed = {}

            def execute(*_args):
                running = json.loads(report.read_text())
                self.assertEqual(running["status"], "RUNNING")
                self.assertNotEqual(running["run_id"], "stale")
                observed["run_id"] = running["run_id"]
                return {"plugin": "demo", "status": "PASS"}

            manifest = [("demo", "unused-test", "unused-source")]
            with mock.patch.object(GATE, "MANIFEST", manifest), \
                 mock.patch.object(GATE, "execute_entry", side_effect=execute), \
                 mock.patch("builtins.print"):
                self.assertEqual(GATE.main(["--report", str(report)]), 0)
            final = json.loads(report.read_text())
            self.assertEqual(final["status"], "PASS")
            self.assertEqual(final["run_id"], observed["run_id"])
            self.assertEqual(len(final["gate_sha256"]), 64)
            self.assertEqual(len(final["manifest_sha256"]), 64)

    def test_keyboard_interrupt_cannot_leave_stale_pass(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_interrupt_") as raw:
            report = Path(raw) / "gate.json"
            report.write_text('{"status":"PASS","run_id":"stale"}\n')
            manifest = [("demo", "unused-test", "unused-source")]
            with mock.patch.object(GATE, "MANIFEST", manifest), \
                 mock.patch.object(GATE, "execute_entry", side_effect=KeyboardInterrupt), \
                 mock.patch("builtins.print"):
                with self.assertRaises(KeyboardInterrupt):
                    GATE.main(["--report", str(report)])
            current = json.loads(report.read_text())
            self.assertEqual(current["status"], "RUNNING")
            self.assertNotEqual(current["run_id"], "stale")

    def test_failed_final_replace_leaves_complete_running_report(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_final_replace_") as raw:
            report = Path(raw) / "gate.json"
            report.write_text('{"status":"PASS","run_id":"stale"}\n')
            manifest = [("demo", "unused-test", "unused-source")]
            real_replace = GATE.os.replace
            replace_calls = 0

            def fail_final_replace(source, destination):
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls == 2:
                    raise OSError("simulated final replace failure")
                return real_replace(source, destination)

            with mock.patch.object(GATE, "MANIFEST", manifest), \
                 mock.patch.object(
                     GATE, "execute_entry",
                     return_value={"plugin": "demo", "status": "PASS"},
                 ), mock.patch.object(GATE.os, "replace", side_effect=fail_final_replace), \
                 mock.patch("builtins.print"):
                with self.assertRaisesRegex(OSError, "simulated final replace"):
                    GATE.main(["--report", str(report)])
            current = json.loads(report.read_text())
            self.assertEqual(current["status"], "RUNNING")
            self.assertNotEqual(current["run_id"], "stale")
            self.assertEqual(list(report.parent.glob(f".{report.name}.*.tmp")), [])

    def test_atomic_replace_failure_preserves_destination_and_cleans_temp(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_replace_helper_") as raw:
            report = Path(raw) / "gate.json"
            old = {"status": "RUNNING", "run_id": "old"}
            report.write_text(json.dumps(old) + "\n")
            with mock.patch.object(
                GATE.os, "replace", side_effect=OSError("simulated replace failure")
            ):
                with self.assertRaisesRegex(OSError, "simulated replace"):
                    GATE.atomic_write_json(report, {"status": "PASS"})
            self.assertEqual(json.loads(report.read_text()), old)
            self.assertEqual(list(report.parent.glob(f".{report.name}.*.tmp")), [])

    @unittest.skipUnless(os.name == "posix", "process-group test requires POSIX")
    def test_timeout_kills_descendant_process_group_and_preserves_output(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_process_group_") as raw:
            base = Path(raw)
            test = base / "test_hangs.py"
            source = base / "source.cpp"
            pgid_file = base / "pgid.txt"
            test.write_text(
                "import os, subprocess, sys, time\n"
                "from pathlib import Path\n"
                "child = subprocess.Popen([sys.executable, '-c', "
                "\"import sys,time; print('grandchild-out', flush=True); "
                "print('grandchild-err', file=sys.stderr, flush=True); time.sleep(30)\"])\n"
                f"Path({str(pgid_file)!r}).write_text(str(os.getpgrp()))\n"
                "print('parent-out', flush=True)\n"
                "print('parent-err', file=sys.stderr, flush=True)\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            source.write_text("// timeout source\n", encoding="utf-8")
            started = time.monotonic()
            row = GATE.execute_entry("demo", str(test), str(source), timeout=0.3)
            elapsed = time.monotonic() - started
            pgid = int(pgid_file.read_text())
            try:
                self.assertEqual(row["status"], "FAIL")
                self.assertTrue(row["timed_out"])
                self.assertIsNone(row["exit_code"])
                self.assertLess(elapsed, 3.0)
                self.assertEqual(row["stdout"].count("parent-out"), 1)
                self.assertEqual(row["stdout"].count("grandchild-out"), 1)
                self.assertEqual(row["stderr"].count("parent-err"), 1)
                self.assertEqual(row["stderr"].count("grandchild-err"), 1)
                self.assertIsInstance(row["stdout"], str)
                self.assertIsInstance(row["stderr"], str)
                self.assertNotEqual(pgid, os.getpgrp())
                deadline = time.monotonic() + 2.0
                while True:
                    try:
                        os.killpg(pgid, 0)
                    except ProcessLookupError:
                        break
                    if time.monotonic() >= deadline:
                        self.fail(f"timed-out process group {pgid} still exists")
                    time.sleep(0.02)
            finally:
                if pgid != os.getpgrp():
                    try:
                        os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    @unittest.skipUnless(os.name == "posix", "detached-process test requires POSIX")
    def test_timeout_drain_remains_bounded_for_detached_pipe_holder(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_detached_drain_") as raw:
            base = Path(raw)
            test = base / "test_detaches.py"
            source = base / "source.cpp"
            child_pid_file = base / "child_pid.txt"
            test.write_text(
                "import subprocess, sys, time\n"
                "from pathlib import Path\n"
                "child = subprocess.Popen([sys.executable, '-c', "
                "\"import sys,time; print('detached-out', flush=True); "
                "print('detached-err', file=sys.stderr, flush=True); time.sleep(30)\"], "
                "start_new_session=True)\n"
                f"Path({str(child_pid_file)!r}).write_text(str(child.pid))\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            source.write_text("// detached timeout source\n", encoding="utf-8")
            started = time.monotonic()
            row = GATE.execute_entry("demo", str(test), str(source), timeout=0.3)
            elapsed = time.monotonic() - started
            child_pid = int(child_pid_file.read_text())
            try:
                self.assertEqual(row["status"], "FAIL")
                self.assertTrue(row["timed_out"])
                self.assertTrue(row["timeout_drain_incomplete"])
                self.assertLess(elapsed, 3.0)
                self.assertEqual(row["stdout"].count("detached-out"), 1)
                self.assertEqual(row["stderr"].count("detached-err"), 1)
                self.assertNotEqual(child_pid, os.getpgrp())
            finally:
                try:
                    os.killpg(child_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_optimized_interpreter_is_rejected_before_evidence_collection(self):
        with tempfile.TemporaryDirectory(prefix="generic_gate_optimized_") as raw:
            test = Path(raw) / "test_assertion.py"
            report = Path(raw) / "gate.json"
            test.write_text("def test_must_fail():\n    assert False\n")
            environment = os.environ.copy()
            environment.pop("PYTHONOPTIMIZE", None)
            run = subprocess.run(
                [sys.executable, "-O", str(SCRIPT), "--run-test-file", str(test)],
                cwd=ROOT, env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(run.returncode, 1)
            self.assertIn("optimized Python", run.stderr)
            full = subprocess.run(
                [sys.executable, "-O", str(SCRIPT), "--report", str(report)],
                cwd=ROOT, env=environment, text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(full.returncode, 1)
            optimized_report = json.loads(report.read_text())
            self.assertEqual(optimized_report["status"], "FAIL")
            self.assertIn("assert-based evidence", optimized_report["error"])
            self.assertEqual(optimized_report["entries"], [])

    def test_manifest_has_no_fixture_dependent_module_tests(self):
        parameterized = []
        for _, test_rel, _ in GATE.MANIFEST:
            if test_rel.startswith("tools/"):
                continue
            tree = ast.parse((ROOT / test_rel).read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                        node.name.startswith("test_"):
                    parameters = (
                        node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                    )
                    if parameters:
                        parameterized.append((test_rel, node.name))
        self.assertEqual(parameterized, [])

    def test_missing_source_fails_closed_and_records_identity_fields(self):
        row = GATE.execute_entry("demo", "tests/absent.py", "mac/absent.cpp", 1)
        self.assertEqual(row["status"], "FAIL")
        self.assertIsNone(row["test_sha256"])
        self.assertIsNone(row["source_sha256"])
        self.assertIn("command", row)
        self.assertIn("duration_seconds", row)

    def test_manifest_rows_are_suitable_for_plugin_summary(self):
        grouped = {}
        for plugin, test, _ in GATE.MANIFEST:
            grouped.setdefault(plugin, []).append(test)
        self.assertGreaterEqual(len(grouped["OLMColorKey"]), 2)
        self.assertGreaterEqual(len(grouped["common-world"]), 2)
        self.assertTrue(all(paths for paths in grouped.values()))

    def test_parameter_and_deep_generic_entries_are_manifested(self):
        rows = {(plugin, test, source) for plugin, test, source in GATE.MANIFEST}
        self.assertIn((
            "OLMSmoother2",
            "tests/test_olmsmoother2_gamma_colors_beta_20260820.py",
            "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
        ), rows)
        self.assertIn((
            "OLMColorKey",
            "tests/test_olmcolorkey_generic_pixel_local_pairwise.py",
            "mac/OLMColorKey/OLMColorKey.cpp",
        ), rows)
        self.assertIn((
            "OLMDirectionalBlur",
            "tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py",
            "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        ), rows)
        self.assertIn((
            "OLMDirectionalBlur",
            "tools/emulation/test_dblur_generic_backonly_beta_20260821.py",
            "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        ), rows)
        self.assertIn((
            "OLMDirectionalBlur",
            "tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py",
            "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        ), rows)
        self.assertIn((
            "OLMDirectionalBlur",
            "tools/emulation/test_dblur_generic_admission_budget_20260821.py",
            "core/dblur_generic_budget.h",
        ), rows)
        self.assertIn((
            "OLMDirectionalBlur",
            "tools/emulation/test_olmdirectionalblur_smart_cleanup_atomic_20260813.py",
            "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        ), rows)

    def test_skip_is_fail_closed_by_default_cli_contract(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"INCOMPLETE" if has_skip and not args.allow_skip', source)
        self.assertIn('parser.add_argument("--allow-skip"', source)


if __name__ == "__main__":
    unittest.main()

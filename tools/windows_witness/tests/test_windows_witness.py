from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.windows_witness.compiler import _queue_source, compile_witness
from tools.windows_witness.core import SpecError, load_spec
from tools.windows_witness.runtime import bundle_return, validate_trace


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic"
SPEC = EXAMPLE / "witness-spec.json"
LAUNCHER = ROOT / "runtime" / "run_witness.ps1"


def complete_trace(contract: dict, *, duplicate: bool = False, pid_drift: bool = False, bad_value: bool = False) -> str:
    lines = []
    for index, case in enumerate(contract["cases"]):
        pid = 999 if pid_drift and index == 1 else 4242
        value = "not-a-number" if bad_value and index == 1 else str(index + 7)
        line = (
            "SYNTH_CAPTURE run_id=synth-fixture ae_pid={} module_base=0x7ff800000000 "
            "aex_sha256={} project_bpc=16 renderer=Software case_id={} sample={} value={}"
        ).format(pid, contract["plugin"]["aex_sha256"], case["id"], case["template_values"]["sample"], value)
        lines.append(line)
        if duplicate and index == 0:
            lines.append(line)
    return "\n".join(lines) + "\n"


def address_relation_contract(contract: dict) -> dict:
    related = copy.deepcopy(contract)
    event = related["validation"]["events"][0]
    event["required_fields"].extend(["address", "base", "row", "row0", "col", "col0", "stride"])
    event["field_relations"] = [{
        "type": "address_arithmetic",
        "address_field": "address",
        "base_field": "base",
        "row_field": "row",
        "row_origin_field": "row0",
        "column_field": "col",
        "column_origin_field": "col0",
        "stride_field": "stride",
        "element_size": 4,
        "channel_offset": 8,
    }]
    return related


def trace_with_address_fields(contract: dict) -> str:
    fields = "base=0000`0000`00001000 row=3 row0=1 col=7 col0=2 stride=10 address=0x106c"
    return complete_trace(contract).replace(" value=", f" {fields} value=")


class CompilerTests(unittest.TestCase):
    def _collector_fixture(self, root: Path) -> Path:
        fixture = root / "collector-fixture"
        shutil.copytree(EXAMPLE, fixture)
        for name, content in {
            "fake_injector.exe": "macOS test placeholder; never executed\n",
            "fake_collector.dll": "macOS test placeholder; never loaded\n",
            "collector-config.json.in": '{"run_id":"{{RUN_ID}}","pid":"{{AE_PID}}","case":"{{CASE_ID}}","output":"{{OUTPUT_DIR}}"}\n',
        }.items():
            (fixture / name).write_text(content, encoding="utf-8")
        spec_path = fixture / "witness-spec.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        spec.pop("cdb")
        for case in spec["cases"]:
            case.pop("cdb_template")
            case.pop("addresses")
        spec["transport"] = {
            "kind": "in_process_collector",
            "injector_path": "fake_injector.exe",
            "collector_dll": "fake_collector.dll",
            "config_template": "collector-config.json.in",
            "required_outputs": ["collector_trace.txt", "collector_status.json", "collector.jsonl"],
            "arm_timeout_seconds": 7,
            "capture_timeout_seconds": 11,
        }
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        return spec_path

    def test_in_process_collector_package_is_generated_without_building_windows_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            spec_path = self._collector_fixture(Path(temp))
            package, archive = compile_witness(spec_path, Path(temp) / "package", Path(temp) / "package.zip")
            contract = json.loads((package / "witness-contract.json").read_text(encoding="utf-8"))
            self.assertEqual(contract["transport"]["kind"], "in_process_collector")
            self.assertEqual(contract["transport"]["arm_timeout_seconds"], 7)
            self.assertEqual(contract["transport"]["capture_timeout_seconds"], 11)
            self.assertTrue((package / "collector" / "injector.exe").is_file())
            self.assertTrue((package / "collector" / "collector.dll").is_file())
            self.assertTrue((package / "collector" / "config.json.in").is_file())
            with zipfile.ZipFile(archive) as contents:
                self.assertIn("collector/injector.exe", contents.namelist())
                self.assertNotIn("cdb/000_case_0001.cdb.in", contents.namelist())

    def test_in_process_collector_rejects_missing_or_unresolved_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            spec_path = self._collector_fixture(Path(temp))
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            spec["transport"]["injector_path"] = "missing.exe"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(SpecError, "missing collector asset"):
                compile_witness(spec_path, Path(temp) / "package", Path(temp) / "package.zip")

            second_spec_path = self._collector_fixture(Path(temp) / "second")
            spec = json.loads(second_spec_path.read_text(encoding="utf-8"))
            (second_spec_path.parent / "collector-config.json.in").write_text("{{UNKNOWN}}\n", encoding="utf-8")
            with self.assertRaisesRegex(SpecError, "unsupported or unresolved placeholder"):
                compile_witness(second_spec_path, Path(temp) / "package-2", Path(temp) / "package-2.zip")

    def test_in_process_collector_requires_canonical_outputs_and_unique_basenames(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            missing_spec_path = self._collector_fixture(Path(temp) / "missing")
            missing = json.loads(missing_spec_path.read_text(encoding="utf-8"))
            missing["transport"]["required_outputs"] = ["foo.txt", "bar.txt"]
            missing_spec_path.write_text(json.dumps(missing), encoding="utf-8")
            with self.assertRaisesRegex(SpecError, "must include collector_trace.txt and collector_status.json"):
                compile_witness(missing_spec_path, Path(temp) / "missing-package", Path(temp) / "missing.zip")

            collision_spec_path = self._collector_fixture(Path(temp) / "collision")
            collision = json.loads(collision_spec_path.read_text(encoding="utf-8"))
            collision["transport"]["required_outputs"] = [
                "collector_trace.txt",
                "collector_status.json",
                "sub/collector.jsonl",
                "other/collector.jsonl",
            ]
            collision_spec_path.write_text(json.dumps(collision), encoding="utf-8")
            with self.assertRaisesRegex(SpecError, "unique basenames"):
                compile_witness(collision_spec_path, Path(temp) / "collision-package", Path(temp) / "collision.zip")

    def test_compile_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            package_a, zip_a = compile_witness(SPEC, temp_path / "package-a", temp_path / "a.zip")
            package_b, zip_b = compile_witness(SPEC, temp_path / "package-b", temp_path / "b.zip")
            self.assertEqual(zip_a.read_bytes(), zip_b.read_bytes())
            contract = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
            self.assertEqual([case["id"] for case in contract["cases"]], ["case_0001", "case_0002"])
            self.assertEqual([case["order"] for case in contract["cases"]], [0, 1])
            self.assertIn("cdb_trace_case_0001.txt", contract["return_bundle"]["include_logs"])
            self.assertIn("cdb_trace_case_0002.txt", contract["return_bundle"]["include_logs"])
            self.assertIn("afterfx_bootstrap.cdb", contract["return_bundle"]["include_logs"])
            self.assertIn("afterfx_bootstrap_cdb_trace.txt", contract["return_bundle"]["include_logs"])
            self.assertIn("afterfx_launch_wrapper.cmd", contract["return_bundle"]["include_logs"])
            self.assertIn("launched_queue.jsx", contract["return_bundle"]["include_logs"])
            self.assertIn("capture_diagnostics.json", contract["return_bundle"]["include_logs"])
            queue = (package_a / "scripts" / "ae_witness_queue.jsx").read_text(encoding="utf-8")
            self.assertIn('"root=" + root + "\\n" +', queue)
            self.assertIn('"queue_sha256=" + queueSha256 + "\\n", false);', queue)
            self.assertIn('env("WINDOWS_WITNESS_QUEUE_SHA256")', queue)
            self.assertIn('rename("queue_bootstrap.log")', queue)
            self.assertIn('runId + "\\n"', queue)
            self.assertNotIn('runId + "\n"', queue)
            with zipfile.ZipFile(zip_a) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertIn("artifacts/run_witness.ps1", names)
                self.assertIn("scripts/witness_runtime.py", names)
                self.assertIn("cdb/000_case_0001.cdb.in", names)
                self.assertTrue(all(info.date_time == (2026, 1, 1, 0, 0, 0) for info in archive.infolist()))

    def test_legacy_cdb_contract_remains_the_default_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            package, _ = compile_witness(SPEC, Path(temp) / "package", Path(temp) / "package.zip")
            contract = json.loads((package / "witness-contract.json").read_text(encoding="utf-8"))
            self.assertNotIn("transport", contract)
            self.assertEqual(contract["cases"][0]["package_cdb_template"], "cdb/000_case_0001.cdb.in")

    def test_plugin_cache_rescan_is_explicit_opt_in_and_packed_into_the_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "fixture"
            shutil.copytree(EXAMPLE, fixture)
            path = fixture / "witness-spec.json"
            spec = json.loads(path.read_text(encoding="utf-8"))
            spec["plugin"]["cache_rescan"] = True
            path.write_text(json.dumps(spec), encoding="utf-8")
            package, _ = compile_witness(path, fixture / "package", fixture / "package.zip")
            contract = json.loads((package / "witness-contract.json").read_text(encoding="utf-8"))
            self.assertTrue(contract["plugin"]["cache_rescan"])
            self.assertIn("plugin_cache_rescan.json", contract["return_bundle"]["include_logs"])

    def test_plugin_cache_rescan_rejects_non_boolean_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "fixture"
            shutil.copytree(EXAMPLE, fixture)
            path = fixture / "witness-spec.json"
            spec = json.loads(path.read_text(encoding="utf-8"))
            spec["plugin"]["cache_rescan"] = "yes"
            path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(SpecError, "plugin.cache_rescan must be boolean"):
                compile_witness(path, fixture / "package", fixture / "package.zip")

    def test_generated_windows_queue_normalizes_package_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            package, _ = compile_witness(SPEC, Path(temp) / "package", Path(temp) / "package.zip")
            queue = (package / "scripts" / "ae_witness_queue.jsx").read_text(encoding="utf-8")
            self.assertIn("root = new Folder(root).fsName;", queue)
            self.assertIn('var requestDir = new Folder(root + "/request").fsName;', queue)

    def test_windows_renderers_normalize_import_paths_for_ae(self) -> None:
        specs_root = Path(__file__).resolve().parents[3] / "refs" / "windows_witness_specs"
        renderers = sorted(specs_root.glob("*/renderer.jsx"))
        self.assertGreaterEqual(len(renderers), 1)
        import_renderers = 0
        for renderer in renderers:
            with self.subTest(renderer=renderer.parent.name):
                source = renderer.read_text(encoding="utf-8")
                if "importFile" not in source:
                    continue
                import_renderers += 1
                self.assertIn("file = new File(file.fsName);", source)
        self.assertGreaterEqual(import_renderers, 1)

    def test_rejects_non_truncating_cdb_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "fixture"
            shutil.copytree(EXAMPLE, fixture)
            template = fixture / "probe.cdb.in"
            template.write_text(template.read_text(encoding="utf-8").replace(".logopen /t", ".logopen"), encoding="utf-8")
            with self.assertRaisesRegex(SpecError, r"logopen /t"):
                load_spec(fixture / "witness-spec.json")

    def test_rejects_unknown_cdb_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "fixture"
            shutil.copytree(EXAMPLE, fixture)
            template = fixture / "probe.cdb.in"
            template.write_text(template.read_text(encoding="utf-8") + "\n.echo {{UNKNOWN}}\n", encoding="utf-8")
            with self.assertRaisesRegex(SpecError, "unsupported placeholder"):
                load_spec(fixture / "witness-spec.json")

    def test_rejects_identity_contract_without_renderer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "fixture"
            shutil.copytree(EXAMPLE, fixture)
            path = fixture / "witness-spec.json"
            spec = json.loads(path.read_text(encoding="utf-8"))
            spec["validation"]["identity_fields"].remove("renderer")
            path.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(SpecError, "common run identity"):
                load_spec(path)

    def test_address_relation_spec_validation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            for name, mutate, message in (
                ("unknown_field", lambda relation: relation.__setitem__("row_field", "not_required"), "required field"),
                ("bad_element_size", lambda relation: relation.__setitem__("element_size", 0), "positive integer"),
                ("boolean_element_size", lambda relation: relation.__setitem__("element_size", True), "positive integer"),
                ("bad_channel_offset", lambda relation: relation.__setitem__("channel_offset", -1), "nonnegative integer"),
                ("unknown_type", lambda relation: relation.__setitem__("type", "expression"), "type is invalid"),
            ):
                with self.subTest(name=name):
                    fixture = Path(temp) / name
                    shutil.copytree(EXAMPLE, fixture)
                    path = fixture / "witness-spec.json"
                    spec = json.loads(path.read_text(encoding="utf-8"))
                    spec = address_relation_contract(spec)
                    mutate(spec["validation"]["events"][0]["field_relations"][0])
                    path.write_text(json.dumps(spec), encoding="utf-8")
                    with self.assertRaisesRegex(SpecError, message):
                        load_spec(path)

    def test_rejects_archive_path_collisions_in_spec(self) -> None:
        def mutated_spec(name: str) -> tuple[Path, dict]:
            fixture = Path(temp) / name
            shutil.copytree(EXAMPLE, fixture)
            path = fixture / "witness-spec.json"
            return path, json.loads(path.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp:
            cases = {
                "duplicate_export": lambda spec: spec["cases"][1]["exports"][0].__setitem__("archive_path", "exports/case_0001.png"),
                "casefold_export": lambda spec: spec["cases"][1]["exports"][0].__setitem__("archive_path", "EXPORTS/CASE_0001.PNG"),
                "log_collision": lambda spec: (
                    spec["return_bundle"].__setitem__("include_logs", ["queue.log"]),
                    spec["cases"][0]["exports"][0].__setitem__("archive_path", "logs/queue.log"),
                ),
                "json_collision": lambda spec: spec["cases"][0]["exports"][0].__setitem__(
                    "archive_path", spec["return_bundle"]["json_name"]
                ),
            }
            for name, mutate in cases.items():
                with self.subTest(name=name):
                    path, spec = mutated_spec(name)
                    mutate(spec)
                    path.write_text(json.dumps(spec), encoding="utf-8")
                    with self.assertRaisesRegex(SpecError, "collides"):
                        load_spec(path)

    def test_rejects_unsafe_archive_paths_in_spec(self) -> None:
        def mutated_spec(name: str) -> tuple[Path, dict]:
            fixture = Path(temp) / name
            shutil.copytree(EXAMPLE, fixture)
            path = fixture / "witness-spec.json"
            return path, json.loads(path.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp:
            cases = {
                "export_backslash": lambda spec: spec["cases"][0]["exports"][0].__setitem__("archive_path", r"exports\case_0001.png"),
                "export_absolute": lambda spec: spec["cases"][0]["exports"][0].__setitem__("archive_path", "/exports/case_0001.png"),
                "export_drive": lambda spec: spec["cases"][0]["exports"][0].__setitem__("archive_path", "C:/exports/case_0001.png"),
                "export_empty_component": lambda spec: spec["cases"][0]["exports"][0].__setitem__("archive_path", "exports//case_0001.png"),
                "export_dot_component": lambda spec: spec["cases"][0]["exports"][0].__setitem__("archive_path", "exports/./case_0001.png"),
                "export_dotdot_component": lambda spec: spec["cases"][0]["exports"][0].__setitem__("archive_path", "exports/../case_0001.png"),
                "json_name_backslash": lambda spec: spec["return_bundle"].__setitem__("json_name", r"status\return.json"),
                "log_dotdot": lambda spec: spec["return_bundle"].__setitem__("include_logs", ["../queue.log"]),
            }
            for name, mutate in cases.items():
                with self.subTest(name=name):
                    path, spec = mutated_spec(name)
                    mutate(spec)
                    path.write_text(json.dumps(spec), encoding="utf-8")
                    with self.assertRaisesRegex(SpecError, r"backslashes|relative path|drive path|unsafe path component"):
                        load_spec(path)

    def test_rejects_request_manifest_request_id_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            for name, mutate in {
                "missing_request_id": lambda manifest: manifest.pop("request_id", None),
                "mismatched_request_id": lambda manifest: manifest.__setitem__("request_id", "wrong_request"),
            }.items():
                with self.subTest(name=name):
                    fixture = Path(temp) / name
                    shutil.copytree(EXAMPLE, fixture)
                    manifest_path = fixture / "request" / "request_manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    mutate(manifest)
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(SpecError, "request_id"):
                        load_spec(fixture / "witness-spec.json")

    def test_compile_rejects_unsafe_request_asset_zip_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            for name, mutate in {
                "backslash_filename": lambda request_dir: (request_dir / r"bad\name.txt").write_text("bad\n", encoding="utf-8"),
            }.items():
                with self.subTest(name=name):
                    fixture = Path(temp) / name
                    shutil.copytree(EXAMPLE, fixture)
                    mutate(fixture / "request")
                    with self.assertRaisesRegex(SpecError, r"backslashes"):
                        compile_witness(fixture / "witness-spec.json", fixture / "package", fixture / "package.zip")

    def test_launcher_source_guards_known_windows_failures(self) -> None:
        source = LAUNCHER.read_text(encoding="utf-8")
        exact_bootstrap_exit_failure = {
            "status": "exact_bind_failure",
            "failure": {
                "stage": "cdb_launch",
                "reason": "CDB bootstrap did not detach from the launched After Effects process",
                "missing_fields": ["cdb_bootstrap_exit"],
            },
        }
        self.assertEqual(exact_bootstrap_exit_failure["failure"]["missing_fields"], ["cdb_bootstrap_exit"])
        self.assertNotIn("-ArgumentList @('-m', '-r', $queuePath)", source)
        self.assertIn("$launchDir = Join-Path $env:PUBLIC", source)
        self.assertIn("Copy-Item -LiteralPath $queuePath -Destination $queueLaunch", source)
        self.assertIn("function ConvertTo-WindowsCommandLineArgument", source)
        self.assertIn("$directQueueLaunch = ([string]$env:WINDOWS_WITNESS_DIRECT_R -eq '1') -or ($transportKind -eq 'in_process_collector')", source)
        self.assertIn("Join-WindowsCommandLine @($AfterFxPath)", source)
        self.assertNotIn("Join-WindowsCommandLine @($AfterFxPath, '-m')", source)
        self.assertIn("$queueDispatchCommandLine = Join-WindowsCommandLine @($AfterFxPath, '-ro', $normalizedQueuePath)", source)
        self.assertIn("$dispatchScheduledTaskName = '\\OLM_Witness_Dispatch_'", source)
        self.assertIn("schtasks.exe /Create /TN $dispatchScheduledTaskName", source)
        self.assertIn("schtasks.exe /Run /TN $dispatchScheduledTaskName", source)
        self.assertIn("$mainAePid = [int]$launch.Id", source)
        self.assertIn("'jsx_dispatch'", source)
        self.assertIn("$launchArgumentValues = @('/d', '/s', '/c', $launchWrapper)", source)
        self.assertIn("$text.Replace('.logopen /t ', '.logopen ')", source)
        self.assertNotIn("'-cf', $bootstrapCdbScript, '--', $AfterFxPath", source)
        self.assertIn("schtasks.exe /Create /TN $scheduledTaskName", source)
        self.assertNotIn("'-o', '-pd', '-g', '-G'", source)
        self.assertIn("$launchArguments = Join-WindowsCommandLine $launchArgumentValues", source)
        self.assertIn("-FilePath $CdbPath", source)
        self.assertNotIn("$observedCommandLine.IndexOf($normalizedQueuePath", source)
        self.assertNotIn("'jsx_command_line_preflight'", source)
        self.assertIn("('OLMWitness\\w_' + $shortId)", source)
        self.assertIn("$bootstrapCdbTrace = Join-Path $launchDir 'boot.log'", source)
        self.assertIn("Copy-WitnessLaunchEvidence", source)
        self.assertIn("afterfx_dispatch_wrapper.cmd", source)
        self.assertIn("Get-ChildItem -Path ($activeCdbTrace + '.*')", source)
        self.assertIn("$activeCdbTraceEvidence + $suffix", source)
        self.assertIn("ARTIFACT_PATH=$trace", source)
        self.assertNotIn("$dispatchArguments", source)
        self.assertIn("'jsx_dispatch'", source)
        self.assertIn('schtasks.exe /Run /TN $scheduledTaskName', source)
        self.assertNotIn('ld:AfterFX.exe', source)
        self.assertNotIn("WITNESS_CDB_PLUGIN_LOADED", source)
        self.assertNotIn("sxi ibp", source)
        self.assertIn("'jsx_launch'", source)
        self.assertIn("while ((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $queueBootstrap -PathType Leaf))", source)
        self.assertIn("Remove-Item -LiteralPath $queueBootstrap -Force", source)
        self.assertIn("Read-QueueBootstrapBinding $queueBootstrap", source)
        self.assertIn("'queue_binding'", source)
        self.assertIn("[string]$queueBootstrapBinding.run_id -cne $runId", source)
        self.assertIn("[string]$queueBootstrapBinding.queue_sha256 -cne $queueHash", source)
        self.assertIn("if ($null -eq $boundPid) { $boundPid = [int]$ae.Id }", source)
        self.assertIn("bootstrap_plugin_load_claimed = [bool]$bootstrapPluginLoadClaimed", source)
        self.assertIn("queue_bootstrap_marker_observed = [bool]$queueBootstrapObserved", source)
        self.assertIn("afterfx_process_diagnostics.json", source)
        bundle_at = source.index("& py -3 $runtimePath bundle")
        cleanup_at = source.index("Stop-WitnessProcesses\n  $captureDiagnostics")
        self.assertLess(cleanup_at, bundle_at)

    def test_launcher_records_typed_hits_and_terminates_capture_timeout(self) -> None:
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("function Get-TypedHitCount", source)
        self.assertIn("typed_hit_count", source)
        self.assertIn("cdb_capture_timeout_without_typed_hit", source)
        self.assertIn("terminated_after_capture_timeout", source)
        self.assertIn("function Stop-CdbCapture", source)
        self.assertIn("Stop-CdbCapture\n    Finish (Failure 'cdb_capture'", source)
        self.assertIn("CDB was terminated and AfterFX was stopped", source)
        self.assertIn("cdb_alive_after_cleanup", source)

    def test_launcher_collector_branch_is_fail_closed_and_pid_bound(self) -> None:
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("$transportKind = if ($contract.transport", source)
        self.assertIn("@('--pid', [string]$boundPid, '--dll', $dllPath, '--config', $configPath)", source)
        self.assertIn("collector_status.json", source)
        self.assertIn("$status.status -ne 'ok'", source)
        self.assertIn("Set-Content -LiteralPath $continue -Value 'continue'", source)
        collector_branch = source[source.index("    $collectorOutputDir"):]
        self.assertLess(collector_branch.index("Wait-CollectorStatus $collectorStatusPath 'armed'"), collector_branch.index("Set-Content -LiteralPath $continue -Value 'continue'"))
        self.assertLess(collector_branch.index("Set-Content -LiteralPath $continue -Value 'continue'"), collector_branch.index("Read-CollectorStatus $collectorStatusPath 'ok'"))
        self.assertLess(collector_branch.index("Read-CollectorStatus $collectorStatusPath 'ok'"), collector_branch.index("Validate-CollectorOutputs $case"))
        injector_launch = source[source.index("$script:injectorProcess = Start-Process"):]
        self.assertIn("-Wait -PassThru", injector_launch.splitlines()[0])
        self.assertLess(source.index("-Wait -PassThru"), source.index("$injectorExitCode = $injectorProcess.ExitCode"))

    def test_launcher_cache_rescan_only_removes_exact_plugin_cache_entries(self) -> None:
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("function Invoke-PluginCacheRescan", source)
        self.assertIn("function Test-PluginCacheModuleMatch", source)
        self.assertIn("function Get-PluginCacheRoots", source)
        self.assertIn("plugin_cache_rescan.json", source)
        self.assertIn("match_rule = 'registry leaf must equal module_filename or module_filename + underscore suffix'", source)
        self.assertIn("Get-ChildItem -LiteralPath $root.PSPath -Recurse", source)
        self.assertIn("Remove-Item -LiteralPath $match.PSPath -Recurse -Force", source)
        self.assertNotIn("Remove-Item -LiteralPath $root.PSPath -Recurse -Force", source)
        self.assertIn("Failure 'plugin_cache_rescan'", source)

    def test_collector_transport_uses_single_direct_queue_launch(self) -> None:
        source = LAUNCHER.read_text(encoding="utf-8")
        selector = "($transportKind -eq 'in_process_collector')"
        direct_launch = "Join-WindowsCommandLine @($AfterFxPath, '-ro', $normalizedQueuePath)"
        ordinary_launch = "Join-WindowsCommandLine @($AfterFxPath)"
        dispatch_guard = "if (!$directQueueLaunch) {"
        self.assertIn(selector, source)
        self.assertIn(direct_launch, source)
        self.assertIn(ordinary_launch, source)
        self.assertIn(dispatch_guard, source)
        self.assertLess(source.index(selector), source.index(direct_launch))
        self.assertLess(source.index(direct_launch), source.index(ordinary_launch))
        self.assertLess(source.index(ordinary_launch), source.index(dispatch_guard))
        guarded_dispatch = source[source.index(dispatch_guard):]
        self.assertIn("$dispatchScheduledTaskName", guarded_dispatch)
        self.assertIn("schtasks.exe /Run /TN $dispatchScheduledTaskName", guarded_dispatch)

    def test_generated_queue_does_not_start_a_second_ae_script(self) -> None:
        queue = _queue_source(load_spec(SPEC))
        self.assertIn('var rendererSource = read(root + "/scripts/renderer.jsx");', queue)
        self.assertIn("eval(rendererSource);", queue)
        self.assertNotIn("$.evalFile", queue)

    def test_collector_trace_uses_the_existing_flat_event_validator(self) -> None:
        base_contract = load_spec(SPEC)
        collector_contract = copy.deepcopy(base_contract)
        collector_contract["transport"] = {"kind": "in_process_collector"}
        result = validate_trace(collector_contract, complete_trace(base_contract), {"run_id": "synth-fixture", "ae_pid": 4242, "module_base": "0x7ff800000000"})
        self.assertEqual(result["status"], "answered")


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_spec(SPEC)
        cls.identity = {"run_id": "synth-fixture", "ae_pid": 4242, "module_base": "0x7ff800000000"}

    def test_complete_trace_answers(self) -> None:
        result = validate_trace(self.contract, complete_trace(self.contract), self.identity)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(len(result["events"]), 2)

    def test_trace_failures_are_closed(self) -> None:
        variants = {
            "missing_case": complete_trace(self.contract).splitlines()[0] + "\n",
            "duplicate": complete_trace(self.contract, duplicate=True),
            "identity_drift": complete_trace(self.contract, pid_drift=True),
            "field_constraint": complete_trace(self.contract, bad_value=True),
        }
        for name, trace in variants.items():
            with self.subTest(name=name):
                result = validate_trace(self.contract, trace, self.identity)
                self.assertEqual(result["status"], "exact_bind_failure")
                self.assertTrue(result["failure"]["missing_fields"])

    def test_trace_rejects_duplicate_fields_within_one_event_line(self) -> None:
        trace = complete_trace(self.contract).replace("sample=left", "sample=left sample=shadow", 1)
        result = validate_trace(self.contract, trace, self.identity)
        self.assertEqual(result["status"], "exact_bind_failure")
        self.assertIn("capture:duplicate_field:sample", result["failure"]["missing_fields"])

    def test_address_arithmetic_relation_accepts_matching_cdb_pointers(self) -> None:
        contract = address_relation_contract(self.contract)
        result = validate_trace(contract, trace_with_address_fields(contract), self.identity)
        self.assertEqual(result["status"], "answered")

    def test_address_arithmetic_relation_rejects_bogus_inputs(self) -> None:
        contract = address_relation_contract(self.contract)
        valid = trace_with_address_fields(contract)
        variants = {
            "address": valid.replace("address=0x106c", "address=0x1068"),
            "base": valid.replace("base=0000`0000`00001000", "base=0000`0000`00001004"),
            "row": valid.replace("row=3 ", "row=4 "),
            "row_origin": valid.replace("row0=1 ", "row0=2 "),
            "column": valid.replace("col=7 ", "col=8 "),
            "column_origin": valid.replace("col0=2 ", "col0=3 "),
            "stride": valid.replace("stride=10 ", "stride=11 "),
            "unparseable": valid.replace("row=3 ", "row=0x3 "),
        }
        for name, trace in variants.items():
            with self.subTest(name=name):
                result = validate_trace(contract, trace, self.identity)
                self.assertEqual(result["status"], "exact_bind_failure")
                self.assertTrue(any(":relation:address=" in item for item in result["failure"]["missing_fields"]))

    def _make_work(self, root: Path) -> Path:
        for case in self.contract["cases"]:
            artifact = root / "exports" / case["id"] / f"{case['id']}.png"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes(("PNG-" + case["id"]).encode("ascii"))
        (root / "queue.log").write_text("queue\n", encoding="utf-8")
        return root

    def test_return_bundle_is_deterministic_and_collects_exports(self) -> None:
        status = validate_trace(self.contract, complete_trace(self.contract), self.identity)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            work_a = self._make_work(base / "a")
            work_b = self._make_work(base / "b")
            result_a, zip_a = bundle_return(self.contract, copy.deepcopy(status), work_a)
            result_b, zip_b = bundle_return(self.contract, copy.deepcopy(status), work_b)
            self.assertEqual(result_a["status"], "answered")
            self.assertEqual(len(result_a["artifacts"]), 2)
            self.assertEqual(zip_a.read_bytes(), zip_b.read_bytes())
            with zipfile.ZipFile(zip_a) as archive:
                self.assertEqual(archive.namelist(), sorted(archive.namelist()))

    def test_missing_required_export_changes_success_to_failure(self) -> None:
        status = validate_trace(self.contract, complete_trace(self.contract), self.identity)
        with tempfile.TemporaryDirectory() as temp:
            result, _ = bundle_return(self.contract, status, Path(temp))
            self.assertEqual(result["status"], "exact_bind_failure")
            self.assertEqual(result["failure"]["stage"], "artifact_collection")

    def test_return_bundle_rejects_colliding_archive_layout(self) -> None:
        answered = validate_trace(self.contract, complete_trace(self.contract), self.identity)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            cases = {
                "log_collision": lambda contract, work: (
                    contract["return_bundle"].__setitem__("include_logs", ["queue.log"]),
                    contract["cases"][0]["exports"][0].__setitem__("archive_path", "logs/queue.log"),
                    self._make_work(work),
                ),
                "json_collision": lambda contract, work: (
                    contract["cases"][0]["exports"][0].__setitem__("archive_path", contract["return_bundle"]["json_name"]),
                    self._make_work(work),
                ),
                "duplicate_zip_entries": lambda contract, work: (
                    contract["return_bundle"].__setitem__("include_logs", ["dup.log", "DUP.log"]),
                    self._make_work(work),
                    (work / "dup.log").write_text("dup\n", encoding="utf-8"),
                    (work / "DUP.log").write_text("dup\n", encoding="utf-8"),
                ),
            }
            for name, mutate in cases.items():
                with self.subTest(name=name):
                    contract = copy.deepcopy(self.contract)
                    work = base / name
                    mutate(contract, work)
                    result, zip_path = bundle_return(contract, copy.deepcopy(answered), work)
                    self.assertEqual(result["status"], "exact_bind_failure")
                    self.assertEqual(result["failure"]["stage"], "return_bundle_validation")
                    with zipfile.ZipFile(zip_path) as archive:
                        self.assertEqual(archive.namelist(), [contract["return_bundle"]["json_name"]])

    def test_return_bundle_rejects_unsafe_archive_paths(self) -> None:
        answered = validate_trace(self.contract, complete_trace(self.contract), self.identity)
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            cases = {
                "export_backslash": lambda contract, work: (
                    contract["cases"][0]["exports"][0].__setitem__("archive_path", r"exports\case_0001.png"),
                    self._make_work(work),
                ),
                "export_absolute": lambda contract, work: (
                    contract["cases"][0]["exports"][0].__setitem__("archive_path", "/exports/case_0001.png"),
                    self._make_work(work),
                ),
                "export_drive": lambda contract, work: (
                    contract["cases"][0]["exports"][0].__setitem__("archive_path", "C:/exports/case_0001.png"),
                    self._make_work(work),
                ),
                "export_empty_component": lambda contract, work: (
                    contract["cases"][0]["exports"][0].__setitem__("archive_path", "exports//case_0001.png"),
                    self._make_work(work),
                ),
                "export_dot_component": lambda contract, work: (
                    contract["cases"][0]["exports"][0].__setitem__("archive_path", "exports/./case_0001.png"),
                    self._make_work(work),
                ),
                "export_dotdot_component": lambda contract, work: (
                    contract["cases"][0]["exports"][0].__setitem__("archive_path", "exports/../case_0001.png"),
                    self._make_work(work),
                ),
                "log_backslash": lambda contract, work: (
                    contract["return_bundle"].__setitem__("include_logs", [r"bad\name.log"]),
                    self._make_work(work),
                    (work / r"bad\name.log").write_text("bad\n", encoding="utf-8"),
                ),
            }
            for name, mutate in cases.items():
                with self.subTest(name=name):
                    contract = copy.deepcopy(self.contract)
                    work = base / name
                    mutate(contract, work)
                    result, zip_path = bundle_return(contract, copy.deepcopy(answered), work)
                    self.assertEqual(result["status"], "exact_bind_failure")
                    self.assertEqual(result["failure"]["stage"], "return_bundle_validation")
                    self.assertTrue(result["failure"]["missing_fields"])
                    with zipfile.ZipFile(zip_path) as archive:
                        self.assertEqual(archive.namelist(), [contract["return_bundle"]["json_name"]])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.windows_witness.compiler import compile_witness
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
        self.assertIn("$afterFxCommandLine = Join-WindowsCommandLine @($AfterFxPath, '-r', $normalizedQueuePath)", source)
        self.assertIn("$launchArgumentValues = @('-pd', '-hd', '-logo', $bootstrapCdbTrace, '-cf', $bootstrapCdbScript, $AfterFxPath, '-r', $normalizedQueuePath)", source)
        self.assertNotIn("'-cf', $bootstrapCdbScript, '--', $AfterFxPath", source)
        self.assertNotIn("$env:ComSpec, '/d', '/s', '/c', $launchWrapper", source)
        self.assertNotIn("'-o', '-pd', '-g', '-G'", source)
        self.assertIn("$launchArguments = Join-WindowsCommandLine $launchArgumentValues", source)
        self.assertIn("-FilePath $CdbPath", source)
        self.assertIn("-ArgumentList $launchArguments", source)
        self.assertNotIn("$observedCommandLine.IndexOf($normalizedQueuePath", source)
        self.assertNotIn("'jsx_command_line_preflight'", source)
        self.assertIn("('OLMWitness\\w_' + $shortId)", source)
        self.assertIn("$bootstrapCdbTrace = Join-Path $launchDir 'boot.log'", source)
        self.assertIn("Copy-WitnessLaunchEvidence", source)
        self.assertNotIn("$dispatchArguments", source)
        self.assertNotIn("'jsx_dispatch'", source)
        self.assertIn('.echo WITNESS_CDB_AFTERFX_INITIAL_BREAK', source)
        self.assertNotIn('ld:AfterFX.exe', source)
        self.assertNotIn("WITNESS_CDB_TARGET_MODULE_LOADED", source)
        self.assertNotIn("sxi ibp", source)
        self.assertIn("'cdb_bootstrap'", source)
        self.assertIn("'cdb_bootstrap_exit'", source)
        self.assertIn("'jsx_launch'", source)
        self.assertIn("while ((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $queueBootstrap -PathType Leaf))", source)
        self.assertIn("Remove-Item -LiteralPath $queueBootstrap -Force", source)
        self.assertIn("Read-QueueBootstrapBinding $queueBootstrap", source)
        self.assertIn("'queue_binding'", source)
        self.assertIn("[string]$queueBootstrapBinding.run_id -cne $runId", source)
        self.assertIn("[string]$queueBootstrapBinding.queue_sha256 -cne $queueHash", source)
        self.assertIn("[int]$postBootstrapState[0].pid -ne $bootstrapAePid", source)
        self.assertIn("bootstrap_plugin_load_claimed = [bool]$bootstrapPluginLoadClaimed", source)
        self.assertIn("queue_bootstrap_marker_observed = [bool]$queueBootstrapObserved", source)
        self.assertIn("afterfx_process_diagnostics.json", source)
        bundle_at = source.index("& py -3 $runtimePath bundle")
        success_cleanup_at = source.index("if ($code -eq 0) { Stop-WitnessProcesses }")
        self.assertGreater(success_cleanup_at, bundle_at)


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

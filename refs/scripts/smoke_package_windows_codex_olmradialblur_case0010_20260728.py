#!/usr/bin/env python3
"""Smoke the immutable OLMRadialBlur case_0010 Windows Codex child package."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import stat
import zipfile
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = (
    ROOT / "scripts" / "package_windows_codex_olmradialblur_case0010_20260728.py"
)
BATCH_PACKAGER_PATH = (
    ROOT / "scripts" / "package_windows_codex_batch_handoff_20260728.py"
)
RUNTIME_PATH = ROOT / "tools" / "windows_witness" / "runtime.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def synthetic_records(builder):
    runtime_identity = {
        "run_id": "rb10upstream-synthetic",
        "ae_pid": 4242,
        "module_base": "0x7ff800000000",
    }
    common = {
        **runtime_identity,
        "aex_sha256": builder.AEX_SHA256,
        "project_bpc": "8",
        "renderer": "Software",
        "case_id": "case_0010",
        "witness_id": builder.WITNESS_ID,
        "request_id": builder.REQUEST_ID,
        "project_id": builder.PROJECT_ID,
        "plugin_id": builder.PLUGIN_ID,
        "runtime_id": builder.RUNTIME_ID,
        "input_sha256": builder.INPUT_SHA256,
        "claim_boundary": builder.CLAIM_BOUNDARY,
        "final_writeback_boundary": builder.FINAL_WRITEBACK_BOUNDARY,
        "effect_artifact_role": builder.EFFECT_ARTIFACT_ROLE,
        "normalized_base": "10000000",
        "accumulated_base": "20000000",
        "validity_base": "30000000",
    }
    records = {}
    witness_spec = builder.spec()
    for event in witness_spec["validation"]["events"]:
        fields = dict(common)
        for field, constraint in event["field_constraints"].items():
            if "equals" in constraint:
                fields[field] = str(constraint["equals"])
        for field in event["required_fields"]:
            if field in fields:
                continue
            if field.endswith("_rgba") or field.endswith("_rgba_f32"):
                fields[field] = "3f800000,3f000000,3e800000,3f800000"
            elif field.endswith("_f252"):
                fields[field] = "3f800000"
            elif field == "sampler_result_address":
                fields[field] = "40000000"
            elif field.endswith("_address"):
                fields[field] = "1"
            else:
                raise AssertionError(
                    f"no synthetic value for {event['name']}:{field}"
                )
        if event["name"] == "normalized_cells":
            bases = {
                "normalized": int(fields["normalized_base"], 16),
                "accumulated": int(fields["accumulated_base"], 16),
                "validity": int(fields["validity_base"], 16),
            }
            sizes = {"normalized": 16, "accumulated": 16, "validity": 4}
            for cell in builder.CELL_EXPR:
                row = int(fields[f"cell{cell}_row"])
                column = int(fields[f"cell{cell}_column"])
                index = row * int(fields["stride"]) + column
                for plane in ("normalized", "accumulated", "validity"):
                    fields[f"cell{cell}_{plane}_address"] = (
                        f"{bases[plane] + index * sizes[plane]:x}"
                    )
        records[event["name"]] = {
            "prefix": event["prefix"],
            "fields": fields,
        }
    return witness_spec, runtime_identity, records


def trace_text(records) -> str:
    lines = []
    for name in ("normalized_cells", "sampler_output"):
        row = records[name]
        values = " ".join(
            f"{key}={value}" for key, value in row["fields"].items()
        )
        lines.append(f"{row['prefix']} {values}")
    return "\n".join(lines) + "\n"


def assert_adversarial_trace_gates(builder, runtime) -> None:
    witness_spec, identity, valid_records = synthetic_records(builder)
    answered = runtime.validate_trace(
        witness_spec, trace_text(valid_records), identity
    )
    assert answered["status"] == "answered", answered

    failures = {}

    poison = deepcopy(valid_records)
    for event_name in poison:
        poison[event_name]["fields"]["normalized_base"] = "deadbeef"
    normalized = poison["normalized_cells"]["fields"]
    for cell in builder.CELL_EXPR:
        index = (
            int(normalized[f"cell{cell}_row"]) * int(normalized["stride"])
            + int(normalized[f"cell{cell}_column"])
        )
        normalized[f"cell{cell}_normalized_address"] = (
            f"{int('deadbeef', 16) + index * 16:x}"
        )
    failures["poison_base"] = poison

    zero = deepcopy(valid_records)
    zero["sampler_output"]["fields"]["sampler_result_address"] = "0"
    failures["zero_pointer"] = zero

    inconsistent = deepcopy(valid_records)
    address = inconsistent["normalized_cells"]["fields"][
        "cell00_normalized_address"
    ]
    inconsistent["normalized_cells"]["fields"][
        "cell00_normalized_address"
    ] = f"{int(address, 16) + 16:x}"
    failures["inconsistent_cell_address"] = inconsistent

    shared_mismatch = deepcopy(valid_records)
    shared_mismatch["sampler_output"]["fields"][
        "accumulated_base"
    ] = "20000010"
    failures["shared_base_mismatch"] = shared_mismatch

    wrong_coordinate = deepcopy(valid_records)
    wrong_coordinate["sampler_output"]["fields"][
        "sample_x_f32"
    ] = "44c87adf"
    failures["wrong_sample_float_word"] = wrong_coordinate

    for label, records in failures.items():
        result = runtime.validate_trace(
            witness_spec, trace_text(records), identity
        )
        assert result["status"] == "exact_bind_failure", (label, result)


def mocked_cleanup_decision(
    *,
    request_id,
    prelaunch,
    context,
    sidecar,
    live_processes,
):
    """Ensure r4 preserves the r3 allowlist and fail-closed process policy."""

    expected_prefix = "\\OLM_Witness_" + re.sub(
        r"[^A-Za-z0-9_-]", "_", request_id
    ) + "_"
    tasks = []
    stopped = []
    unresolved = False
    if context:
        task = context.get("scheduled_task_name", "")
        run_token = re.sub(
            r"[^A-Za-z0-9_-]", "_", context.get("run_id", "")
        )
        if (
            context.get("request_id") == request_id
            and task.startswith(expected_prefix)
            and task.endswith(run_token)
        ):
            tasks.append(task)
        else:
            unresolved = True
    if not sidecar:
        if context and context.get("task_run_requested"):
            unresolved = True
        return tasks, stopped, unresolved
    if not context:
        return tasks, stopped, True
    fields_match = (
        sidecar.get("request_id") == request_id
        and sidecar.get("run_id") == context.get("run_id")
        and sidecar.get("project_id") == context.get("project_id")
        and sidecar.get("scheduled_task_name")
        == context.get("scheduled_task_name")
        and sidecar.get("ownership")
        == "exact_fresh_scheduled_task_launch"
        and sidecar.get("pid") not in {row["pid"] for row in prelaunch}
        and sidecar.get("creation_time_utc", "")
        >= context.get("launch_window_start_utc", "")
    )
    live = {
        row["pid"]: row for row in live_processes
    }.get(sidecar.get("pid"))
    live_match = live is None or (
        live.get("creation_time_utc") == sidecar.get("creation_time_utc")
        and live.get("executable_path") == sidecar.get("executable_path")
        and live.get("executable_sha256")
        == sidecar.get("executable_sha256")
    )
    if not fields_match or not live_match:
        return tasks, stopped, True
    if live:
        stopped.append(live["pid"])
    return tasks, stopped, unresolved


def assert_adversarial_ownership_policy(builder) -> None:
    request_id = builder.REQUEST_ID
    run_id = "rb10upstream-owned"
    task = (
        "\\OLM_Witness_"
        + re.sub(r"[^A-Za-z0-9_-]", "_", request_id)
        + "_"
        + run_id
    )
    user = {
        "pid": 100,
        "creation_time_utc": "2026-07-28T01:00:00.0000000Z",
        "executable_path": r"C:\Adobe\AfterFX.exe",
        "executable_sha256": "a" * 64,
    }
    owned = {
        "pid": 200,
        "creation_time_utc": "2026-07-28T02:00:01.0000000Z",
        "executable_path": r"C:\Adobe\AfterFX.exe",
        "executable_sha256": "a" * 64,
    }
    context = {
        "request_id": request_id,
        "run_id": run_id,
        "project_id": builder.PROJECT_ID,
        "scheduled_task_name": task,
        "task_run_requested": True,
        "launch_window_start_utc": "2026-07-28T02:00:00.0000000Z",
    }
    sidecar = {
        **owned,
        "request_id": request_id,
        "run_id": run_id,
        "project_id": builder.PROJECT_ID,
        "scheduled_task_name": task,
        "ownership": "exact_fresh_scheduled_task_launch",
    }

    _, stopped, unresolved = mocked_cleanup_decision(
        request_id=request_id,
        prelaunch=[user],
        context=context,
        sidecar=sidecar,
        live_processes=[user, owned],
    )
    assert stopped == [owned["pid"]] and not unresolved

    # Scheduler parentage is deliberately absent from the decision; exact
    # launch/task/sidecar identity owns PID 200 without assuming parentage.
    concurrent_user = {**owned, "pid": 201}
    _, stopped, _ = mocked_cleanup_decision(
        request_id=request_id,
        prelaunch=[user],
        context=context,
        sidecar=sidecar,
        live_processes=[user, owned, concurrent_user],
    )
    assert stopped == [owned["pid"]]
    assert user["pid"] not in stopped and concurrent_user["pid"] not in stopped

    # Missing sidecar, recycled PID, task mismatch, and a sidecar targeting a
    # prelaunch user PID all fail closed without a process stop.
    mutations = [
        (context, None, [user, owned]),
        (
            context,
            sidecar,
            [
                user,
                {
                    **owned,
                    "creation_time_utc": "2026-07-28T03:00:00.0000000Z",
                },
            ],
        ),
        (
            {**context, "scheduled_task_name": task + "_mismatch"},
            sidecar,
            [user, owned],
        ),
        (
            context,
            {
                **sidecar,
                "pid": user["pid"],
                "creation_time_utc": user["creation_time_utc"],
            },
            [user, owned],
        ),
    ]
    for mutated_context, mutated_sidecar, live in mutations:
        _, stopped, unresolved = mocked_cleanup_decision(
            request_id=request_id,
            prelaunch=[user],
            context=mutated_context,
            sidecar=mutated_sidecar,
            live_processes=live,
        )
        assert stopped == [] and unresolved
        assert user["pid"] not in stopped


def assert_installed_aex_path_bindings(builder, package_text) -> None:
    expected = (
        r"C:\Program Files\Adobe\Common\Plug-ins\7.0"
        r"\MediaCore\OLM\OLMRadialBlur.aex"
    )
    bare = (
        r"C:\Program Files\Adobe\Common\Plug-ins\7.0"
        r"\MediaCore\OLMRadialBlur.aex"
    )
    assert builder.DEFAULT_AEX_PATH == expected
    for name, text in package_text.items():
        logical_text = text.replace("\\\\", "\\")
        assert bare not in logical_text, (name, bare)
    for name in (
        "witness-contract.json",
        "run.ps1",
        "artifacts/run_witness.ps1",
        "README.md",
    ):
        assert expected in package_text[name].replace("\\\\", "\\"), name


def main() -> int:
    builder = load(BUILDER_PATH, "rb10_child_builder")
    batch = load(BATCH_PACKAGER_PATH, "windows_batch_packager")
    runtime = load(RUNTIME_PATH, "windows_witness_runtime")
    assert re.fullmatch(builder.POINTER_PATTERN, "10000000")
    for rejected in ("0", "00000000", "deadbeef", "0xdeadbeef"):
        assert re.fullmatch(builder.POINTER_PATTERN, rejected) is None
    assert_adversarial_trace_gates(builder, runtime)
    assert_adversarial_ownership_policy(builder)
    result = builder.verify_target()
    target = Path(result["target"])
    package = target / "package.zip"
    manifest_path = target / "job_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package_sha = hashlib.sha256(package.read_bytes()).hexdigest()
    assert manifest["schema"] == "windows_codex_batch_job_v1"
    assert manifest["job_id"] == builder.JOB_ID
    assert manifest["request_id"] == builder.REQUEST_ID
    assert manifest["package_sha256"] == package_sha
    assert manifest["entrypoint"] == "run.ps1"
    assert manifest["failure_policy"] == "independent"
    assert manifest["success_status"] == "answered"
    assert manifest["failure_status"] == "exact_bind_failure"

    regular_files = batch.validate_child_zip(package.read_bytes(), package.name)
    assert manifest["entrypoint"] in regular_files
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert all("__MACOSX" not in name for name in names)
        assert not any(Path(name).name.casefold() == "return.zip" for name in names)
        for info in archive.infolist():
            mode = info.external_attr >> 16
            assert stat.S_ISREG(mode)
            assert info.date_time == (2026, 1, 1, 0, 0, 0)
        package_manifest = json.loads(archive.read("package-manifest.json"))
        contract = json.loads(archive.read("witness-contract.json"))
        runner = archive.read("run.ps1").decode("ascii")
        inner_runner = archive.read(
            "artifacts/run_witness.ps1"
        ).decode("utf-8")
        readme = archive.read("README.md").decode("utf-8")
        renderer = archive.read("scripts/renderer.jsx").decode("utf-8")
        cdb = archive.read("cdb/000_case_0010.cdb.in").decode("ascii")
        package_text = {}
        for name in names:
            try:
                package_text[name] = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
        assert_installed_aex_path_bindings(builder, package_text)
        request = json.loads(archive.read("request/request_manifest.json"))
        input_bytes = archive.read("request/input/case_0010_before_effects.png")
        legacy_reference_bytes = archive.read("request/expected/case_0010.png")
        assert package_manifest["request_id"] == builder.REQUEST_ID
        assert package_manifest["entrypoint"] == manifest["entrypoint"]
        assert package_manifest["claim_boundary"] == builder.CLAIM_BOUNDARY
        assert (
            package_manifest["final_writeback_boundary"]
            == builder.FINAL_WRITEBACK_BOUNDARY
        )
        inventory = {
            row["path"]: row for row in package_manifest["files"]
        }
        assert set(inventory) == set(names) - {"package-manifest.json"}
        for path, row in inventory.items():
            payload = archive.read(path)
            assert hashlib.sha256(payload).hexdigest() == row["sha256"]
            assert len(payload) == row["size_bytes"]
        assert request["request_id"] == builder.REQUEST_ID
        assert request["gate_kind"] == "windows_live_raw_witness_only"
        assert hashlib.sha256(input_bytes).hexdigest() == builder.INPUT_SHA256
        assert (
            hashlib.sha256(legacy_reference_bytes).hexdigest()
            == builder.LEGACY_REFERENCE_SHA256
        )
        assert contract["request_id"] == builder.REQUEST_ID
        assert contract["plugin"]["aex_sha256"] == builder.AEX_SHA256
        assert contract["plugin"]["default_aex_path"] == builder.DEFAULT_AEX_PATH
        assert contract["project"] == {
            "bits_per_channel": 8,
            "environment": {
                "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT": "1",
                "OLM_AE_FORCE_SOFTWARE": "1",
            },
            "renderer": "Software",
        }
        assert contract["success_status"] == "answered"
        assert contract["failure_status"] == "exact_bind_failure"
        assert contract["cases"][0]["addresses"] == {
            "normalization_done": "0x4df0",
            "sampler_call": "0x4eb9",
            "sampler_return": "0x4ec8",
        }
        exports = contract["cases"][0]["exports"]
        assert len(exports) == 2 and all(row["required"] for row in exports)
        export_names = {
            Path(row["archive_path"]).name for row in exports
        }
        assert export_names == {
            "effect_on_artifact_presence_case_0010.png",
            "raw_no_effect_fixture_control_case_0010.png",
        }
        assert "raw_no_effect_fixture_control=" in renderer
        assert "could not retain raw before-effects no-effect fixture control" in renderer
        assert '.logopen /t "{{TRACE_PATH}}"' in cdb
        assert "RB10_NORMALIZED" in cdb
        assert "RB10_SAMPLER_OUTPUT" in cdb
        assert "cell00_f250_rgba" in cdb
        assert "cell11_f252" in cdb
        assert "cell11_normalized_rgba" in cdb
        assert "sampler_result_rgba_f32" in cdb
        assert "sampler_result_address" in cdb
        assert "output_rgba_f32" not in cdb
        assert "rotation_entry" not in cdb
        assert "{{CASE_VALUE:claim_boundary}}" in cdb
        assert "sample_x_f32=%08x sample_y_f32=%08x" in cdb
        assert "normalized_base=%p accumulated_base=%p validity_base=%p" in cdb
        assert (
            contract["cases"][0]["template_values"]["claim_boundary"]
            == builder.CLAIM_BOUNDARY
        )
        assert (
            contract["cases"][0]["template_values"][
                "final_writeback_boundary"
            ]
            == builder.FINAL_WRITEBACK_BOUNDARY
        )
        events = {
            event["name"]: event
            for event in contract["validation"]["events"]
        }
        assert set(events) == {"normalized_cells", "sampler_output"}
        assert len(events["normalized_cells"]["field_relations"]) == 12
        for event in events.values():
            for base in (
                "normalized_base",
                "accumulated_base",
                "validity_base",
            ):
                assert base in event["required_fields"]
                assert event["field_constraints"][base][
                    "pattern"
                ] == builder.POINTER_PATTERN
        assert events["sampler_output"]["field_constraints"][
            "sample_x_f32"
        ] == {"equals": "44c87ade"}
        assert events["sampler_output"]["field_constraints"][
            "sample_y_f32"
        ] == {"equals": "44531452"}
        assert "try {" in runner
        assert "} catch {" in runner
        assert "} finally {" in runner
        assert "$runner = Start-Process" in runner
        assert "OWNED_PROCESS_REGISTRY.json" in runner
        assert "OWNERSHIP_CLEANUP.json" in runner
        assert "executable_path" in runner and "creation_date" in runner
        assert "Stop-RegisteredProcesses" in runner
        assert "if ($name -ine 'cdb.exe') { continue }" in runner
        assert "owned_afterfx_process.json" in runner
        assert "launch_ownership_context.json" in runner
        assert "possible recycled PID" in runner
        assert "missing_owned_pid_sidecar_no_process_touched" in runner
        assert "task_name_mismatch_not_touched" in runner
        assert "cleanup_unresolved" in runner
        assert "foreach ($state in @(Get-AfterFxState))" not in runner
        assert "output_world_exact = $false" in runner
        assert "export_pixel_classified = $false" in runner
        assert "ae_exact = $false" in runner
        assert "later_job_required = $true" in runner
        assert "final output-world writeback" in readme
        assert "requires a later separately grounded job" in readme
        assert "artifacts\\run_witness.ps1" not in readme
        assert readme.count("run.ps1") == 1
        assert "Cleanup is therefore fail-closed, not guaranteed" in readme
        assert "Pre-existing and concurrent user" in readme
        assert "$directQueueLaunch = $true # package r4" in inner_runner
        assert inner_runner.count("schtasks.exe /Create") == 1
        assert inner_runner.count("schtasks.exe /Run") == 1
        assert "\\OLM_Witness_Dispatch_" not in inner_runner
        assert "prelaunchAeSnapshot" in inner_runner
        assert "launchWindowStartUtc" in inner_runner
        assert "Publish-LaunchOwnershipContext $false" in inner_runner
        assert "Publish-LaunchOwnershipContext $true" in inner_runner
        assert "Publish-OwnedAfterFx $launchStates[0]" in inner_runner
        assert "Publish-OwnedCdb" in inner_runner
        assert "owned_cdb_process.json" in inner_runner
        assert "exact_fresh_scheduled_task_launch" in inner_runner
        assert "PID existed in prelaunch snapshot" in inner_runner
        assert "possible recycled PID" in inner_runner
        assert "missing_owned_pid_sidecar_no_afterfx_process_touched" in inner_runner
        assert "missing_cdb_ownership_sidecar_no_process_touched" in inner_runner
        assert "task_name_mismatch_not_touched" in inner_runner
        assert "foreach ($state in @(Get-AfterFxState))" not in inner_runner
        assert "After Effects must be fully closed before this run" not in inner_runner

    loaded = batch.load_job(manifest_path, 1)
    parent_job = loaded[0]
    assert parent_job["job_id"] == manifest["job_id"]
    assert parent_job["package_sha256"] == package_sha
    assert parent_job["entrypoint"] == manifest["entrypoint"]
    assert parent_job["failure_policy"] == "independent"
    assert parent_job["success_status"] == "answered"
    assert parent_job["failure_status"] == "exact_bind_failure"
    if len(loaded) >= 3:
        assert loaded[2] == package.read_bytes()
    print(
        "status=pass "
        f"job_id={builder.JOB_ID} package_sha256={package_sha} "
        "parent_child_schema=windows_codex_batch_job_v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

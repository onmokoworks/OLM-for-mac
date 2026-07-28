#!/usr/bin/env python3
"""Local compile-only/mock smoke for the DG PF16 r3 child."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    ROOT
    / "scripts"
    / "package_windows_codex_olmdistancegradation_pf16_boundary_r3_20260728.py"
)
BATCH = ROOT / "scripts" / "package_windows_codex_batch_handoff_20260728.py"
RUNTIME = ROOT / "tools" / "windows_witness" / "runtime.py"
R2_SMOKE = (
    ROOT
    / "refs"
    / "scripts"
    / "smoke_package_windows_codex_olmdistancegradation_pf16_boundary_r2_20260728.py"
)


def load(path: Path, name: str):
    module_spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(module_spec)
    assert module_spec.loader
    module_spec.loader.exec_module(module)
    return module


builder = load(BUILDER, "olmdg_pf16_r3")
batch = load(BATCH, "windows_batch")
runtime = load(RUNTIME, "windows_witness_runtime")
r2_smoke = load(R2_SMOKE, "olmdg_pf16_r2_smoke_helpers")


def parse_stale_guard(line: str) -> list[tuple[str, str]]:
    """Parse the constrained guard and reject duplicate named parameters."""
    outer = re.fullmatch(r"\s*if \((.*)\) \{\s*", line)
    if outer is None:
        raise ValueError("not an if guard")
    expression = outer.group(1)
    grouped = re.fullmatch(r"\((.*)\) -or \((.*)\)", expression)
    command_texts = list(grouped.groups()) if grouped else [expression]
    commands = []
    for command_text in command_texts:
        tokens = command_text.split()
        if not tokens or tokens[0] != "Test-Path":
            raise ValueError("guard contains a non-Test-Path command")
        parameters: dict[str, str] = {}
        index = 1
        while index < len(tokens):
            token = tokens[index]
            if not token.startswith("-") or index + 1 >= len(tokens):
                raise ValueError(f"malformed Test-Path token: {token}")
            name = token[1:].casefold()
            if name in parameters:
                raise ValueError(f"duplicate named parameter: {token}")
            parameters[name] = tokens[index + 1]
            index += 2
        if set(parameters) != {"literalpath"}:
            raise ValueError(f"unexpected Test-Path parameters: {sorted(parameters)}")
        commands.append(("Test-Path", parameters["literalpath"]))
    if len(commands) != 2:
        raise ValueError("stale guard must group two independent commands")
    return commands


def evaluate_stale_guard(
    commands: list[tuple[str, str]], existing: set[str]
) -> tuple[bool, list[str]]:
    calls: list[str] = []

    def mock_test_path(variable: str) -> bool:
        calls.append(variable)
        return variable in existing

    return any(mock_test_path(variable) for _, variable in commands), calls


def assert_stale_guard_regression(root_runner: str) -> None:
    line = next(
        row
        for row in root_runner.splitlines()
        if "one-shot package contains stale evidence/work" not in row
        and "Test-Path" in row
        and "$evidenceRoot" in row
        and "$workRoot" in row
    )
    commands = parse_stale_guard(line)
    assert commands == [
        ("Test-Path", "$evidenceRoot"),
        ("Test-Path", "$workRoot"),
    ]
    scenarios = (
        (set(), False, ["$evidenceRoot", "$workRoot"]),
        ({"$evidenceRoot"}, True, ["$evidenceRoot"]),
        ({"$workRoot"}, True, ["$evidenceRoot", "$workRoot"]),
        ({"$evidenceRoot", "$workRoot"}, True, ["$evidenceRoot"]),
    )
    for existing, expected, expected_calls in scenarios:
        actual, calls = evaluate_stale_guard(commands, existing)
        assert actual is expected
        assert calls == expected_calls

    broken = builder.BROKEN_STALE_GUARD.strip()
    try:
        parse_stale_guard(broken)
    except ValueError as exc:
        assert "duplicate named parameter: -LiteralPath" in str(exc)
    else:
        raise AssertionError("mock parser accepted the actual r2 duplicate parameter")


def main() -> int:
    subprocess.run([sys.executable, str(BUILDER), "--verify"], check=True)
    target = builder.TARGET
    job, package, snapshot = batch.load_job(target / "job_manifest.json", 1)
    assert package == (target / "package.zip").resolve()
    assert hashlib.sha256(snapshot).hexdigest() == job["package_sha256"]

    with tempfile.TemporaryDirectory(prefix="dg_r3_a_") as first:
        one = builder.build_bytes(Path(first))
    with tempfile.TemporaryDirectory(prefix="dg_r3_b_") as second:
        two = builder.build_bytes(Path(second))
    assert one == two
    assert one == tuple(
        (target / name).read_bytes()
        for name in ("package.zip", "job_manifest.json", "package.zip.sha256")
    )

    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert len(names) == len(set(name.casefold() for name in names))
        required = {
            "run.ps1",
            "README.md",
            "package-manifest.json",
            "witness-contract.json",
            "scripts/validate_direct_boundary.py",
            "anchors/entry_1170480.json",
        }
        assert required <= set(names)
        contract = json.loads(archive.read("witness-contract.json"))
        manifest = json.loads(archive.read("package-manifest.json"))
        readme = archive.read("README.md").decode("ascii")
        root_runner = archive.read("run.ps1").decode("ascii")
        inner = archive.read("artifacts/run_witness.ps1").decode("utf-8")
        assert_stale_guard_regression(root_runner)
        builder.validate_root_runner(root_runner)
        assert "direct boundary r3" in readme
        assert "duplicate LiteralPath binding" in readme
        assert manifest["entrypoint"] == "run.ps1"
        assert manifest["internal_runner"]["role"] == "internal_not_entrypoint"
        assert manifest["runtime_binary_exact"] is False
        assert "foreach ($state in @(Get-AfterFxState))" not in inner
        for marker in (
            "launch_ownership_context.json",
            "owned_afterfx_process.json",
            "owned_cdb_process.json",
            "creation_time_utc",
            "executable_sha256",
            "cleanup_unresolved",
        ):
            assert marker in inner

        probes = [
            archive.read(name).decode("ascii")
            for name in names
            if name.startswith("cdb/") and name.endswith(".cdb.in")
        ]
        assert len(probes) == 6
        for probe in probes:
            builder.r2.validate_entry_cdb_source(probe)
            entry = next(
                row
                for row in probe.splitlines()
                if row.startswith("bp {{ADDRESS:entry}}")
            )
            assert "@rbx" not in entry.lower()
            assert "@rcx+0x94" in entry
            assert "poi(@rsp+0x28)" in entry
            assert "(@xmm6&0xffffffff)" in probe

        validator_path = Path(tempfile.mkdtemp()) / "typed.py"
        validator_path.write_bytes(
            archive.read("scripts/validate_direct_boundary.py")
        )
        typed = load(validator_path, "typed_validator")
        validated = runtime.validate_trace(
            contract,
            r2_smoke.fixture_trace(contract),
            {
                "run_id": "fixture-run",
                "ae_pid": 4242,
                "module_base": "0x180000000",
            },
        )
        assert validated["status"] == "answered", validated
        accepted = typed.validate_document(validated)
        assert accepted["pf16_word_scalar_count"] == 78
        assert accepted["float32_lane_count"] == 24

        adversarial = copy.deepcopy(validated)
        next(
            row
            for row in adversarial["events"]
            if "stored_pf16_words_agrb" in row["fields"]
        )["fields"]["stored_pf16_words_agrb"] = "32769,0,0,0"
        try:
            typed.validate_document(adversarial)
        except ValueError:
            pass
        else:
            raise AssertionError("typed validator accepted an out-of-range PF16 word")

    poisoned = builder.r2.CDB_TEMPLATE.replace("@rcx+0x94", "@rbx+0x94", 1)
    try:
        builder.r2.validate_entry_cdb_source(poisoned)
    except ValueError:
        pass
    else:
        raise AssertionError("entry validator accepted RBX at function entry")

    print(
        json.dumps(
            {
                "status": "ok",
                "job_id": builder.JOB_ID,
                "package_sha256": job["package_sha256"],
                "stale_guard_mock_matrix": 4,
                "actual_r2_duplicate_literalpath_rejected": True,
                "events": 30,
                "entry_rbx_rejected": True,
                "typed_out_of_range_rejected": True,
                "shared_load_job": "accepted",
                "deterministic_builds": 2,
                "windows_execution": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

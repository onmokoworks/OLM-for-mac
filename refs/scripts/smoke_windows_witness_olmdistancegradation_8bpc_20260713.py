#!/usr/bin/env python3
"""Smoke the real OLMDistanceGradation common-core witness package."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.windows_witness.compiler import compile_witness  # noqa: E402
from tools.windows_witness.core import load_spec  # noqa: E402
from tools.windows_witness.runtime import validate_trace  # noqa: E402


SPEC = ROOT / "refs/windows_witness_specs/olmdistancegradation_8bpc_typed_boundary_20260713/witness-spec.json"
CASES = ("case_0001", "case_0015", "case_0029")
HASH = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
IDENTITY = {"run_id": "dg8typed-fixture", "ae_pid": 5936, "module_base": "0x7fffcd660000"}


def _common(case_id: str, *, run_id: str = "dg8typed-fixture") -> str:
    return (
        f"run_id={run_id} ae_pid=5936 module_base=0x7fffcd660000 aex_sha256={HASH} "
        f"project_bpc=8 renderer=Software case_id={case_id}"
    )


def complete_trace(*, omit_case: str | None = None, mixed_case: str | None = None) -> str:
    lines: list[str] = []
    for case_id in CASES:
        if case_id == omit_case:
            continue
        common = _common(case_id, run_id="dg8typed-other" if case_id == mixed_case else "dg8typed-fixture")
        point = f"{common} x=397 y=281 output_addr=0x1000"
        lines.extend(
            [
                f"DG8_FIELD_IN {point} field_base=0x2000 field_rowbytes=1e00 field_addr=0x3000 pixel_size=4 address_formula=base+y*rowbytes+x*4 typed_rgba=01,02,03,ff",
                f"DG8_FIELD_OUT {point} field_base=0x2000 field_rowbytes=1e00 field_addr=0x3000 pixel_size=4 address_formula=base+y*rowbytes+x*4 typed_rgba=01,02,03,ff",
                f"DG8_COMPOSE_IN {point} source_base=0x4000 source_rowbytes=1e00 source_addr=0x5000 pixel_size=4 address_formula=base+y*rowbytes+x*4 field_green=02 x_before_invert=0.007843 x_after_invert=0.992157 typed_rgba=10,20,30,ff",
                f"DG8_COMPOSE_OUT {point} pre_store_rgba_float=1.0,2.0,3.0,255.0 typed_rgba=1.0,2.0,3.0,255.0",
                f"DG8_HOST_STORE {point} typed_rgba=01,02,03,ff",
                f"DG8_PF8_DEPTH {common} rva=1170870 hit_count=1",
                f"DG8_PF32_DEPTH {common} rva=1170c90 hit_count=0",
            ]
        )
    return "\n".join(lines) + "\n"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def main() -> int:
    contract = load_spec(SPEC)
    if contract["plugin"]["default_aex_path"] != r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex":
        return fail("default AEX path is not the audited MediaCore binary")
    if contract["host"]["afterfx_path"] != r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe":
        return fail("AfterFX path is not the AE 25.2 baseline")
    request = json.loads((SPEC.parent / "request/request_manifest.json").read_text(encoding="utf-8"))
    if request.get("request_id") != contract["request_id"]:
        return fail("embedded request_id does not match the witness contract")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        package_a, zip_a = compile_witness(SPEC, root / "package-a", root / "a.zip")
        package_b, zip_b = compile_witness(SPEC, root / "package-b", root / "b.zip")
        if zip_a.read_bytes() != zip_b.read_bytes():
            return fail("compiler output is not deterministic")

        manifest = json.loads((package_a / "package-manifest.json").read_text(encoding="utf-8"))
        if manifest.get("request_id") != contract["request_id"] or manifest.get("entrypoint") != "artifacts/run_witness.ps1":
            return fail("package manifest identity or entrypoint is wrong")
        inventory = manifest.get("files", [])
        inventory_paths = [item["path"] for item in inventory]
        expected_inventory = sorted(
            path.relative_to(package_a).as_posix()
            for path in package_a.rglob("*")
            if path.is_file() and path.name != "package-manifest.json"
        )
        if inventory_paths != expected_inventory or len(inventory_paths) != len(set(inventory_paths)):
            return fail("package manifest inventory is incomplete, unsorted, or duplicated")
        for item in inventory:
            path = package_a / item["path"]
            if item["sha256"] != _sha256(path) or item["size_bytes"] != path.stat().st_size:
                return fail(f"package manifest metadata drifted for {item['path']}")
        with zipfile.ZipFile(zip_a) as archive:
            names = archive.namelist()
            package_files = sorted(path.relative_to(package_a).as_posix() for path in package_a.rglob("*") if path.is_file())
            if names != package_files or names != sorted(names):
                return fail("ZIP and package directory contents differ")
            if any(info.date_time != (2026, 1, 1, 0, 0, 0) for info in archive.infolist()):
                return fail("ZIP timestamps are not deterministic")

        generated_contract = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
        if [case["id"] for case in generated_contract["cases"]] != list(CASES):
            return fail("serial case order changed")
        queue = (package_a / "scripts/ae_witness_queue.jsx").read_text(encoding="utf-8")
        renderer = (package_a / "scripts/renderer.jsx").read_text(encoding="utf-8")
        launcher = (package_a / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        if (
            "effect_loaded=1" not in renderer
            or "parameters_applied=1" not in renderer
            or "cases.length - 1" not in queue
            or 'i === 0 ? "1" : "0"' not in queue
        ):
            return fail("fresh-process serial readiness contract is missing")
        for token in (
            "function ConvertTo-WindowsCommandLineArgument",
            "$launchArgumentValues = @('-o', '-g', '-G', '-cf', $bootstrapCdbScript, $env:ComSpec, '/d', '/s', '/c', $launchWrapper)",
            "$afterFxCommandLine = Join-WindowsCommandLine @($AfterFxPath, '-r', $normalizedQueuePath)",
            "$observedCommandLine.IndexOf($normalizedQueuePath, [StringComparison]::OrdinalIgnoreCase)",
            "'jsx_command_line_preflight'",
            "('OLMWitness\\w_' + $shortId)",
            "$bootstrapCdbTrace = Join-Path $launchDir 'boot.log'",
            "WITNESS_CDB_TARGET_MODULE_LOADED",
            "sxi ibp",
            "'cdb_child_tracking'",
            "$shortTrace = Join-Path $launchDir",
            "Copy-WitnessLaunchEvidence",
        ):
            if token not in launcher:
                return fail(f"launcher is missing CDB/AfterFX transport guard: {token}")
        required_logs = {
            "afterfx_launcher_stdout.txt",
            "afterfx_launcher_stderr.txt",
            "afterfx_process_diagnostics.json",
            "afterfx_bootstrap.cdb",
            "afterfx_bootstrap_cdb_trace.txt",
            "afterfx_launch_wrapper.cmd",
            "launched_queue.jsx",
            "queue_bootstrap.log",
            "queue.log",
            "combined_cdb_trace.txt",
            "runtime_identity.json",
            "validation_status.json",
        }
        for case_id in CASES:
            required_logs.update(
                {
                    f"ready_{case_id}.marker",
                    f"continue_{case_id}.marker",
                    f"probe_{case_id}.cdb",
                    f"cdb_trace_{case_id}.txt",
                    f"cdb_stdout_{case_id}.txt",
                    f"cdb_stderr_{case_id}.txt",
                    f"ae_{case_id}.log",
                    f"ae_result_{case_id}.json",
                }
            )
        if not required_logs <= set(generated_contract["return_bundle"]["include_logs"]):
            return fail("compiler-enumerated raw logs are incomplete")
        for path in (package_a / "cdb").glob("*.cdb.in"):
            if '.logopen /t "{{TRACE_PATH}}"' not in path.read_text(encoding="ascii"):
                return fail(f"CDB template is not truncating: {path.name}")

    complete = validate_trace(contract, complete_trace(), IDENTITY)
    missing = validate_trace(contract, complete_trace(omit_case="case_0015"), IDENTITY)
    mixed = validate_trace(contract, complete_trace(mixed_case="case_0029"), IDENTITY)
    if complete.get("status") != "answered" or len(complete.get("events", [])) != 21:
        return fail("generic validator rejected the complete 21-event trace")
    if missing.get("status") != "exact_bind_failure" or not missing.get("failure", {}).get("missing_fields"):
        return fail("generic validator accepted a missing-case trace")
    if mixed.get("status") != "exact_bind_failure" or not mixed.get("failure", {}).get("missing_fields"):
        return fail("generic validator accepted a mixed-run trace")

    print("[OK] OLMDistanceGradation 8bpc typed-boundary common-core witness is deterministic and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

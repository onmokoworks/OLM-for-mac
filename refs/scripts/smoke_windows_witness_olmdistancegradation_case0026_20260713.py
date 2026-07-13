#!/usr/bin/env python3
"""Smoke the case_0026 16bpc livefield common-core Windows witness."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.windows_witness.runtime import bundle_return, validate_trace  # noqa: E402


GENERATOR = ROOT / "scripts/package_windows_witness_olmdistancegradation_case0026_20260713.py"
SPEC_ROOT = ROOT / "refs/windows_witness_specs/olmdistancegradation_case0026_16bpc_livefield_20260713"
SPEC = SPEC_ROOT / "witness-spec.json"
SOURCE_ROOT = ROOT / "refs/runtime_trace_support/olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713/case"
HASH = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
CASE_ID = "olmdistancegradation_extended__case_0026"
WITNESS_ID = "olmdistancegradation-case0026-16bpc-livefield-v1"
POINTS = ((907, 222), (395, 477), (1589, 579), (898, 670))
IDENTITY = {"run_id": "dg16-case0026-fixture", "ae_pid": 6260, "module_base": "0x7fffab120000"}
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def compile_package(temp: Path, name: str) -> tuple[Path, Path]:
    package = temp / name
    archive = temp / f"{name}.zip"
    completed = subprocess.run(
        [sys.executable, str(GENERATOR), "--output-dir", str(package), "--zip", str(archive)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "ok"
    assert result["compiler"] == "tools.windows_witness.compile"
    return package, archive


def common(*, run_id: str = "dg16-case0026-fixture") -> str:
    return (
        f"run_id={run_id} ae_pid=6260 module_base=0x7fffab120000 "
        f"aex_sha256={HASH} project_bpc=16 renderer=Software case_id={CASE_ID} "
        f"witness_id={WITNESS_ID}"
    )


def complete_trace(*, mixed_prefix: str | None = None) -> str:
    lines: list[str] = []
    for index, (x, y) in enumerate(POINTS):
        base = 0x100000 + index * 0x1000
        identity = common(run_id="dg16-case0026-mixed" if mixed_prefix == f"FIELD_{x}_{y}" else "dg16-case0026-fixture")
        lines.extend(
            [
                f"OLMDG_LFS_ENTRY_{x}_{y} {common()} hook_rva=1170480 x={x} y={y} output=0x{base:x} pre_output_words_agrb=32768,100,200,300 in_out=3 inside_threshold=158 outside_threshold=13 use_bg=1 invert=1 render_mode=1 interp_mode=4 power_bits=0x40263bec grad_r_bits=0x3de0e0ff grad_g_bits=0x00000000 grad_b_bits=0x3f6eeeef bg_r_bits=0x3f800000 bg_g_bits=0x00000000 bg_b_bits=0x00000000",
                f"OLMDG_LFS_FIELD_{x}_{y} {identity} hook_rva=117057d x={x} y={y} rcx=0x{base + 0x100:x} rcx_plus2_word=1234 field_words_agrb=32768,1234,2345,3456 field_base=0x{base + 0x200:x} field_header=0x{base + 0x300:x} field_rowbytes=15360 field_pixel_size=8",
                f"OLMDG_LFS_SOURCE_{x}_{y} {common()} hook_rva=11705f1 x={x} y={y} rdx=0x{base + 0x400:x} source_words_agrb=32768,4567,5678,6789",
                f"OLMDG_LFS_RETURN_{x}_{y} {common()} hook_rva=1170480 x={x} y={y} output=0x{base:x} post_output_words_agrb=32768,7890,8901,9012",
            ]
        )
    return "\n".join(lines) + "\n"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    generator_source = GENERATOR.read_text(encoding="utf-8")
    assert '"-m"' in generator_source and '"tools.windows_witness.compile"' in generator_source
    assert "compile_witness" not in generator_source

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["plugin"]["aex_sha256"] == HASH
    assert spec["plugin"]["default_aex_path"] == r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex"
    assert spec["host"]["afterfx_path"] == r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe"
    assert spec["project"]["bits_per_channel"] == 16
    assert spec["project"]["renderer"] == "Software"
    assert [case["id"] for case in spec["cases"]] == [CASE_ID]
    case = spec["cases"][0]
    assert case["addresses"] == {"entry": "0x1170480", "field": "0x117057d", "source": "0x11705f1"}
    assert case["exports"] == [
        {
            "source": "exports/{case_id}/case_0026.png",
            "archive_path": "return/actual_case_0026.png",
            "required": True,
        }
    ]
    assert len(spec["validation"]["events"]) == 16
    assert all(event["cardinality"] == {"scope": "per_case", "min": 1, "max": 1} for event in spec["validation"]["events"])

    template = (SPEC_ROOT / "livefield_source.cdb.in").read_text(encoding="ascii")
    assert '.logopen /t "{{TRACE_PATH}}"' in template
    for rva in ("0x1170480", "0x117057d", "0x11705f1"):
        assert rva in json.dumps(case["addresses"])
    for term in (
        "dwo(@rbx+0x94)==3",
        "dwo(@rbx+0xd0)==0x40263bec",
        "field_rowbytes=15360",
        "field_pixel_size=8",
        "pre_output_words_agrb",
        "post_output_words_agrb",
        "source_words_agrb",
        "field_words_agrb",
        "OLMDG_LFS_BREAKPOINTS_ARMED",
    ):
        assert term in template
    for placeholder in ("RUN_ID", "AE_PID", "MODULE_BASE", "AEX_SHA256", "PROJECT_BPC", "RENDERER", "CASE_ID"):
        assert "{{" + placeholder + "}}" in template

    exact_pairs = (
        ("renderer.jsx", "ae_render_single_case.jsx"),
        ("request/reference_manifest.json", "reference_manifest.json"),
        ("request/input/case_0026_before_effects.png", "input/case_0026_before_effects.png"),
        ("request/expected/case_0026.png", "expected/case_0026.png"),
    )
    for packaged, source in exact_pairs:
        assert (SPEC_ROOT / packaged).read_bytes() == (SOURCE_ROOT / source).read_bytes(), packaged
    request = json.loads((SPEC_ROOT / "request/request_manifest.json").read_text(encoding="utf-8"))
    source_request = json.loads((SOURCE_ROOT / "request_manifest.json").read_text(encoding="utf-8"))
    source_request["request_id"] = spec["request_id"]
    assert request == source_request

    complete = complete_trace()
    accepted = validate_trace(spec, complete, IDENTITY)
    assert accepted["status"] == "answered"
    assert len(accepted["events"]) == 16
    missing = complete.replace(next(line for line in complete.splitlines(True) if line.startswith("OLMDG_LFS_SOURCE_395_477 ")), "")
    duplicate_line = next(line for line in complete.splitlines(True) if line.startswith("OLMDG_LFS_RETURN_907_222 "))
    fixtures = {
        "missing": missing,
        "mixed": complete_trace(mixed_prefix="FIELD_1589_579"),
        "duplicate": complete + duplicate_line,
        "constraint": complete.replace("field_rowbytes=15360", "field_rowbytes=7680", 1),
    }
    for name, trace in fixtures.items():
        rejected = validate_trace(spec, trace, IDENTITY)
        assert rejected["status"] == "exact_bind_failure", name
        assert rejected["failure"]["missing_fields"], name

    with tempfile.TemporaryDirectory(prefix="olmdg_case0026_common_core_") as raw:
        temp = Path(raw)
        package_a, zip_a = compile_package(temp, "package-a")
        package_b, zip_b = compile_package(temp, "package-b")
        assert zip_a.read_bytes() == zip_b.read_bytes()
        manifest = json.loads((package_a / "package-manifest.json").read_text(encoding="utf-8"))
        inventory = manifest["files"]
        assert [item["path"] for item in inventory] == sorted(item["path"] for item in inventory)
        assert len(inventory) == len({item["path"] for item in inventory})
        for item in inventory:
            path = package_a / item["path"]
            assert item["sha256"] == digest(path)
            assert item["size_bytes"] == path.stat().st_size
        with zipfile.ZipFile(zip_a) as archive:
            assert archive.namelist() == sorted(archive.namelist())
            assert all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist())
            assert archive.read("request/input/case_0026_before_effects.png") == (SPEC_ROOT / "request/input/case_0026_before_effects.png").read_bytes()

        contract = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
        renderer = (package_a / "scripts/renderer.jsx").read_text(encoding="utf-8")
        queue = (package_a / "scripts/ae_witness_queue.jsx").read_text(encoding="utf-8")
        launcher = (package_a / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        assert "effect_loaded=1" in renderer and "parameters_applied=1" in renderer
        assert 'i === 0 ? "1" : "0"' in queue
        for term in ("Get-Process -Name AfterFX", "Get-FileHash", "same_run_identity", "Render-Cdb"):
            assert term in launcher
        assert '.logopen /t "{{TRACE_PATH}}"' in (package_a / "cdb/000_olmdistancegradation_extended__case_0026.cdb.in").read_text(encoding="ascii")

        work = temp / "work"
        output = work / f"exports/{CASE_ID}/case_0026.png"
        output.parent.mkdir(parents=True)
        actual_bytes = b"actual-case0026-render-bytes\x00\xff"
        output.write_bytes(actual_bytes)
        bundled, returned_zip = bundle_return(contract, copy.deepcopy(accepted), work)
        assert bundled["status"] == "answered"
        assert bundled["artifacts"] == [
            {
                "case_id": CASE_ID,
                "archive_path": "return/actual_case_0026.png",
                "sha256": hashlib.sha256(actual_bytes).hexdigest(),
                "size_bytes": len(actual_bytes),
            }
        ]
        with zipfile.ZipFile(returned_zip) as archive:
            assert archive.read("return/actual_case_0026.png") == actual_bytes

        missing_work = temp / "missing-output"
        rejected_bundle, _ = bundle_return(contract, copy.deepcopy(accepted), missing_work)
        assert rejected_bundle["status"] == "exact_bind_failure"
        assert rejected_bundle["failure"]["stage"] == "artifact_collection"

    print("[OK] OLMDistanceGradation case_0026 16bpc livefield common-core witness is deterministic and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

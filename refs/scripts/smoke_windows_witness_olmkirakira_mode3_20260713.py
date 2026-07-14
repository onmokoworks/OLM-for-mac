#!/usr/bin/env python3
"""Smoke the real common-core OLMKiraKira Mode 3 live-Gaussian witness."""

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

from tools.windows_witness.core import load_spec  # noqa: E402
from tools.windows_witness.runtime import bundle_return, validate_trace  # noqa: E402


GENERATOR = ROOT / "scripts/package_windows_witness_olmkirakira_mode3_20260713.py"
SPEC_ROOT = ROOT / "refs/windows_witness_specs/olmkirakira_mode3_live_gaussian_20260713"
SPEC = SPEC_ROOT / "witness-spec.json"
SOURCE_GENERATOR = ROOT / "scripts/package_olmkirakira_mode3_live_gaussian_20260713.py"
SOURCE_REFERENCE = ROOT / "refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMKiraKira/reference_manifest.json"
SOURCE_INPUT = ROOT / (
    "handoff/ae_pixel_validation_20260618/requests/"
    "ae_pixel_olm_final_random10_olm_kira_kira_20260629/input/"
    "olm_final_random10_olm_kira_kira_20260629__software__fr24__"
    "final_random10_olm_kira_kira_03_before_effects.png"
)
SOURCE_RENDERER = ROOT / "scripts/ae_render_single_case.jsx"
CASE_ID = "final_random10_olm_kira_kira_03"
HASH = "60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7"
WITNESS_ID = "olmkirakira-mode3-live-gaussian-common-core-v1"
IDENTITY = {"run_id": "kk-mode3-fixture", "ae_pid": 7313, "module_base": "0x7fffbe430000"}
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def common(*, pid: int = 7313) -> str:
    return (
        f"run_id=kk-mode3-fixture ae_pid={pid} module_base=0x7fffbe430000 "
        f"aex_sha256={HASH} project_bpc=32 renderer=Software case_id={CASE_ID} "
        f"witness_id={WITNESS_ID}"
    )


def complete_trace(*, drift: bool = False) -> str:
    base = common()
    returned = common(pid=9999) if drift else base
    return "\n".join(
        [
            f"KK_WRAPPER {base} stage=gaussian_wrapper wrapper_rva=1272ec0 rcx=0x1000 rdx=0x2000 r8=0x3000 r9=0x4000",
            f"KK_CREATE {base} stage=gaussian_create create_rva=1266730 rcx=0x1100 rdx=0x2200 r8=0x3300 r9=0x4400",
            f"KK_KERNEL_ENTRY {base} stage=first_getKernel_entry getKernel_rva=12754a0 ecx=21 xmm1=2.5 r8=5 output_mat=0x000000f4237fabe0 return_address=0x00007fffbf69685c",
            f"KK_KERNEL_RETURN {returned} stage=first_getKernel_return getKernel_rva=12754a0 getKernelReturn_rva=126685c output_mat=0x000000f4237fabe0 data=0x000001b824640b40 word_count=21 raw_bytes=84 element=float32 encoding=raw_little_endian_words source=cv_Mat_data_after_return",
        ]
    ) + "\n"


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


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    source = SOURCE_GENERATOR.read_text(encoding="utf-8")
    for exact in (CASE_ID, HASH, "0x1272ec0", "0x1266730", "0x12754a0", "0x126685c"):
        assert exact in source

    contract = load_spec(SPEC)
    assert contract["project"] == {
        "bits_per_channel": 32,
        "renderer": "Software",
        "environment": {
            "OLM_AE_PARAM_OVERRIDES_JSON": '{"OLM OLM Kira Kira-0003":5,"OLM OLM Kira Kira-0004":0,"OLM OLM Kira Kira-0005":0,"OLM OLM Kira Kira-0026":0}'
        },
    }
    assert contract["plugin"]["aex_sha256"] == HASH
    assert contract["plugin"]["default_aex_path"] == r"C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMKiraKira.aex"
    assert contract["host"]["afterfx_path"] == r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe"
    assert [case["id"] for case in contract["cases"]] == [CASE_ID]
    case = contract["cases"][0]
    assert case["addresses"] == {
        "wrapper": "0x1272ec0",
        "create": "0x1266730",
        "getKernel": "0x12754a0",
        "getKernelReturn": "0x126685c",
    }
    assert [(event["prefix"], event["cardinality"]) for event in contract["validation"]["events"]] == [
        ("KK_WRAPPER", {"scope": "per_case", "min": 1, "max": 1}),
        ("KK_CREATE", {"scope": "per_case", "min": 1, "max": 1}),
        ("KK_KERNEL_ENTRY", {"scope": "per_case", "min": 1, "max": 1}),
        ("KK_KERNEL_RETURN", {"scope": "per_case", "min": 1, "max": 1}),
    ]
    assert all("compose" not in event["name"] and "quant" not in event["name"] for event in contract["validation"]["events"])
    assert [export["archive_path"] for export in case["exports"]] == [
        "return/gaussian_kernel_21_f32_le.bin",
        "return/case_03.png",
    ]

    assert (SPEC_ROOT / "renderer.jsx").read_bytes() == SOURCE_RENDERER.read_bytes()
    source_reference = json.loads(SOURCE_REFERENCE.read_text(encoding="utf-8"))
    packaged_reference = json.loads((SPEC_ROOT / "request/reference_manifest.json").read_text(encoding="utf-8"))
    source_reference["request_package"]["request_dir"] = "refs/reference_requests"
    assert packaged_reference == source_reference
    assert (SPEC_ROOT / "request/input/case_03_before_effects.png").read_bytes() == SOURCE_INPUT.read_bytes()
    request = json.loads((SPEC_ROOT / "request/request_manifest.json").read_text(encoding="utf-8"))
    assert request["cases"] == [{"id": CASE_ID, "before_effects_frame": "case_03_before_effects.png", "frame": "case_03.png"}]
    reference = json.loads((SPEC_ROOT / "request/reference_manifest.json").read_text(encoding="utf-8"))
    selected = next(row for row in reference["cases"] if row["id"] == CASE_ID)
    blur_mode = next(param["value"] for param in selected["effects"][0]["params"] if param["name"] == "Blur Mode")
    assert blur_mode == 3

    template = (SPEC_ROOT / "mode3_live_gaussian.cdb.in").read_text(encoding="ascii")
    assert '.logopen /t "{{TRACE_PATH}}"' in template
    assert ".writemem" in template and "+0x53" in template
    for placeholder in ("RUN_ID", "AE_PID", "MODULE_BASE", "AEX_SHA256", "PROJECT_BPC", "RENDERER", "CASE_ID", "TRACE_PATH", "ARTIFACT_PATH"):
        assert "{{" + placeholder + "}}" in template
    for name in ("wrapper", "create", "getKernel", "getKernelReturn"):
        assert "{{ADDRESS:" + name + "}}" in template

    accepted = validate_trace(contract, complete_trace(), IDENTITY)
    assert accepted["status"] == "answered" and len(accepted["events"]) == 4
    entry_line = next(line for line in complete_trace().splitlines(True) if line.startswith("KK_KERNEL_ENTRY "))
    variants = {
        "missing": complete_trace().replace(entry_line, ""),
        "identity_drift": complete_trace(drift=True),
        "duplicate": complete_trace() + entry_line,
    }
    for name, trace in variants.items():
        rejected = validate_trace(contract, trace, IDENTITY)
        assert rejected["status"] == "exact_bind_failure", name
        assert rejected["failure"]["missing_fields"], name

    with tempfile.TemporaryDirectory(prefix="olmkirakira_common_core_smoke_") as raw:
        temp = Path(raw)
        package_a, zip_a = compile_package(temp, "package-a")
        package_b, zip_b = compile_package(temp, "package-b")
        assert zip_a.read_bytes() == zip_b.read_bytes()
        with zipfile.ZipFile(zip_a) as archive:
            assert archive.namelist() == sorted(archive.namelist())
            assert all(info.date_time == FIXED_ZIP_TIME for info in archive.infolist())
            assert archive.read("request/input/case_03_before_effects.png") == SOURCE_INPUT.read_bytes()
        generated = json.loads((package_a / "witness-contract.json").read_text(encoding="utf-8"))
        renderer = (package_a / "scripts/renderer.jsx").read_text(encoding="utf-8")
        assert "effect_loaded=1 parameters_applied=1" in renderer
        launcher = (package_a / "artifacts/run_witness.ps1").read_text(encoding="utf-8")
        for term in ("Get-Process -Name AfterFX", "effect_loaded=1", "parameters_applied=1", "Get-FileHash", "Render-Cdb"):
            assert term in launcher

        work = temp / "work"
        kernel_path = work / f"cdb_trace_{CASE_ID}.txt.gaussian_kernel_21_f32_le.bin"
        png_path = work / "exports" / CASE_ID / "case_03.png"
        kernel_path.parent.mkdir(parents=True)
        png_path.parent.mkdir(parents=True)
        kernel_bytes = b"".join(index.to_bytes(4, "little") for index in range(21))
        png_bytes = b"\x89PNG\r\n\x1a\nactual-render-output\x00\xff"
        kernel_path.write_bytes(kernel_bytes)
        png_path.write_bytes(png_bytes)
        bundled, returned_zip = bundle_return(generated, copy.deepcopy(accepted), work)
        assert bundled["status"] == "answered"
        assert bundled["artifacts"] == [
            {"case_id": CASE_ID, "archive_path": "return/gaussian_kernel_21_f32_le.bin", "sha256": sha256(kernel_bytes), "size_bytes": 84},
            {"case_id": CASE_ID, "archive_path": "return/case_03.png", "sha256": sha256(png_bytes), "size_bytes": len(png_bytes)},
        ]
        with zipfile.ZipFile(returned_zip) as archive:
            assert archive.read("return/gaussian_kernel_21_f32_le.bin") == kernel_bytes
            assert archive.read("return/case_03.png") == png_bytes

        missing_work = temp / "missing-work"
        missing_kernel = missing_work / f"cdb_trace_{CASE_ID}.txt.gaussian_kernel_21_f32_le.bin"
        missing_kernel.parent.mkdir(parents=True)
        missing_kernel.write_bytes(kernel_bytes)
        missing_bundle, _ = bundle_return(generated, copy.deepcopy(accepted), missing_work)
        assert missing_bundle["status"] == "exact_bind_failure"
        assert missing_bundle["failure"]["stage"] == "artifact_collection"

    print("[OK] real common-core OLMKiraKira Mode 3 live-Gaussian witness is deterministic and fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

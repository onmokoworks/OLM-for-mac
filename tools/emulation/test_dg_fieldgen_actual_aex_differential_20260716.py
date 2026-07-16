#!/usr/bin/env python3
"""Three-case actual-AEX vs current Mac-core DG field-helper differential.

This is helper parity only. It does not claim full After Effects field-generation
parity, host staging parity, source-mask ownership parity, or render parity.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from aex_loader import AexLoader  # noqa: E402
import cv_bridge as cvb  # noqa: E402
import opencv_impls as ocv  # noqa: E402
from test_dg_fieldgen_p1b import build_context, build_host_suites, setup_tls  # noqa: E402

AEX = ROOT / "plugins_2025/DistanceGradation.aex"
EXPECTED_AEX_SHA256 = "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae"
FUN_FIELDGEN = 0x181174760
FUN_RESIZE = 0x1812AEF70
FUN_NORMALIZE = 0x18117CA50
WIDTH, HEIGHT = 17, 11

EXPECTED_CALLBACK_COUNTS = {
    "PFHandle.dispose": 8,
    "PFHandle.lock": 8,
    "PFHandle.new": 8,
    "PFHandle.unlock": 8,
    "SPBasic.AcquireSuite": 16,
    "SPBasic.ReleaseSuite": 16,
    "cv::dist_transform": 1,
    "cv::normalize_minmax": 1,
    "cv::resize_same_shape": 2,
    "cv::threshold": 1,
}
EXPECTED_DETOUR_HITS = ["resize", "resize", "normalize"]
EXPECTED_IMPORT_COUNTS = {"VCRUNTIME140.dll!memset": 16}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f32_bits(value: np.float32) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def quantize_pf8(field: np.ndarray) -> np.ndarray:
    """Diagnostic OpenCV-style float-to-U8 conversion (nearest even)."""
    return np.clip(np.rint(field.astype(np.float64) * 255.0), 0, 255).astype(np.uint8)


def strict_mask() -> np.ndarray:
    mask = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)
    mask[5, 8] = 0
    return mask


def ramp_mask() -> np.ndarray:
    mask = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)
    mask[:, (0, 8, 16)] = 0
    return mask


CASES = (
    {
        "id": "param8_1_strict_threshold_0",
        "mask": strict_mask(),
        "raw_threshold": 0,
        "param8": 1,
        "ds_scale": 1.0,
        "anchors": ((8, 5), (9, 5), (9, 6)),
        "expected_anchor_aex": (0.0, 1.0, 1.0),
    },
    {
        "id": "param8_0_trunc_ramp_ds1",
        "mask": ramp_mask(),
        "raw_threshold": 4,
        "param8": 0,
        "ds_scale": 1.0,
        "anchors": ((0, 5), (1, 5), (2, 5), (4, 5)),
    },
    {
        "id": "param8_0_trunc_ramp_ds_half",
        "mask": ramp_mask(),
        "raw_threshold": 4,
        "param8": 0,
        "ds_scale": 0.5,
        "anchors": ((0, 5), (1, 5), (2, 5), (4, 5)),
    },
)


def compile_core_bridge(tmp: Path) -> tuple[ctypes.CDLL, list[str]]:
    compiler = shutil.which("clang++")
    if not compiler:
        raise RuntimeError("clang++ is required to call the current Mac core")
    dylib = tmp / "libdg_fieldgen_actual_aex_20260716.dylib"
    command = [
        compiler,
        "-std=c++17",
        "-O2",
        "-dynamiclib",
        str(ROOT / "core/olmdistancegradation_fieldgen.cpp"),
        str(HERE / "dg_fieldgen_actual_aex_bridge_20260716.cpp"),
        "-o",
        str(dylib),
    ]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    library = ctypes.CDLL(str(dylib))
    function = library.dg_distance_to_normalized_u8_20260716
    function.argtypes = [
        np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, flags="C_CONTIGUOUS"),
        ctypes.c_size_t,
        ctypes.c_size_t,
        np.ctypeslib.ndpointer(dtype=np.float32, ndim=2, flags="C_CONTIGUOUS"),
        ctypes.c_float,
        ctypes.c_int,
    ]
    function.restype = ctypes.c_int
    recorded_command = [
        Path(compiler).name,
        "-std=c++17",
        "-O2",
        "-dynamiclib",
        "core/olmdistancegradation_fieldgen.cpp",
        "tools/emulation/dg_fieldgen_actual_aex_bridge_20260716.cpp",
        "-o",
        "<temporary>/libdg_fieldgen_actual_aex_20260716.dylib",
    ]
    return library, recorded_command


def run_portable(library: ctypes.CDLL, case: dict[str, object]) -> np.ndarray:
    output = np.full((HEIGHT, WIDTH), np.float32(-777.0), dtype=np.float32)
    threshold = np.float32(case["raw_threshold"] * case["ds_scale"])
    ok = library.dg_distance_to_normalized_u8_20260716(
        case["mask"], WIDTH, HEIGHT, output, threshold, int(case["param8"] == 1)
    )
    if ok != 1:
        raise RuntimeError(f"current Mac core rejected {case['id']}")
    return output


def callback_counts(loader: AexLoader) -> dict[str, int]:
    return dict(sorted(Counter(label for label, _args, _ret in loader.callback_log).items()))


def import_counts(loader: AexLoader) -> dict[str, int]:
    return dict(sorted(Counter(f"{call.dll}!{call.name}" for call in loader.import_log).items()))


def run_aex(case: dict[str, object]) -> tuple[np.ndarray, dict[str, object]]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    setup_tls(loader)
    ocv.register_opencv_impls(
        loader,
        "DistanceGradation",
        ops=["threshold", "dist_transform", "resize_same_shape", "normalize_minmax"],
    )
    hits: list[str] = []

    def hit(label: str):
        def hook(_loader: AexLoader, _address: int, _size: int) -> None:
            hits.append(label)
        return hook

    loader.add_code_hook(FUN_RESIZE, hit("resize"))
    loader.add_code_hook(FUN_NORMALIZE, hit("normalize"))
    spbasic = build_host_suites(loader)
    context = build_context(loader, spbasic)
    source = cvb.build_ipl(loader, case["mask"], align_step=4)
    destination = cvb.build_ipl(
        loader, np.full((HEIGHT, WIDTH), np.float32(-777.0), dtype=np.float32), align_step=16
    )
    registers = loader.call_function(
        FUN_FIELDGEN,
        int_args=[
            context,
            source,
            destination,
            case["raw_threshold"],
            0,
            WIDTH,
            HEIGHT,
            case["param8"],
        ],
        max_instructions=5_000_000,
    )
    output = cvb.read_ipl(loader, destination).astype(np.float32, copy=True)
    execution = {
        "instructions": registers["instructions"],
        "detour_hits": hits,
        "callback_counts": callback_counts(loader),
        "import_counts": import_counts(loader),
        "detours_match": hits == EXPECTED_DETOUR_HITS,
        "callbacks_match": callback_counts(loader) == EXPECTED_CALLBACK_COUNTS,
        "imports_match": import_counts(loader) == EXPECTED_IMPORT_COUNTS,
    }
    if not execution["detours_match"]:
        raise RuntimeError(f"detour mismatch for {case['id']}: {hits}")
    if not execution["callbacks_match"]:
        raise RuntimeError(f"callback mismatch for {case['id']}: {execution['callback_counts']}")
    if not execution["imports_match"]:
        raise RuntimeError(f"import mismatch for {case['id']}: {execution['import_counts']}")
    return output, execution


def sample_rows(mask: np.ndarray, aex: np.ndarray, portable: np.ndarray) -> list[dict[str, object]]:
    aex_pf8 = quantize_pf8(aex)
    portable_pf8 = quantize_pf8(portable)
    rows = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            av = np.float32(aex[y, x])
            pv = np.float32(portable[y, x])
            rows.append(
                {
                    "xy": [x, y],
                    "source_mask_u8": int(mask[y, x]),
                    "aex_f32": float(av),
                    "aex_f32_bits": f32_bits(av),
                    "portable_f32": float(pv),
                    "portable_f32_bits": f32_bits(pv),
                    "aex_pf8": int(aex_pf8[y, x]),
                    "portable_pf8": int(portable_pf8[y, x]),
                    "f32_bits_match": f32_bits(av) == f32_bits(pv),
                    "pf8_match": int(aex_pf8[y, x]) == int(portable_pf8[y, x]),
                }
            )
    return rows


def run() -> dict[str, object]:
    actual_hash = sha256(AEX) if AEX.exists() else None
    report: dict[str, object] = {
        "schema": "olmdistancegradation.fieldgen-helper-actual-aex-differential/1",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "fail_closed",
        "scope": "FUN_181174760 helper parity only; not full AE field-generation parity",
        "binary": {
            "path": str(AEX.relative_to(ROOT)),
            "sha256": actual_hash,
            "expected_sha256": EXPECTED_AEX_SHA256,
            "hash_match": actual_hash == EXPECTED_AEX_SHA256,
            "function_va": hex(FUN_FIELDGEN),
        },
        "portable": {
            "implementation": "core/olmdistancegradation_fieldgen.cpp::distance_to_normalized_u8",
            "mac_call_contract": "threshold = raw_threshold * ds_scale",
        },
        "pf8_quantization": "diagnostic round-to-nearest-even(clamp(field * 255, 0, 255))",
        "cases": [],
    }
    if actual_hash != EXPECTED_AEX_SHA256:
        report["failure"] = "AEX hash mismatch or binary absent"
        return report

    try:
        with tempfile.TemporaryDirectory(prefix="dg_fieldgen_diff_") as tmp_name:
            library, command = compile_core_bridge(Path(tmp_name))
            report["portable"]["compile_command"] = command
            for definition in CASES:
                case = dict(definition)
                mask = case.pop("mask")
                case["mask"] = mask
                aex, execution = run_aex(case)
                portable = run_portable(library, case)
                rows = sample_rows(mask, aex, portable)
                if len(rows) != WIDTH * HEIGHT:
                    raise RuntimeError(f"sample count mismatch for {case['id']}: {len(rows)}")
                anchor_rows = []
                for x, y in case["anchors"]:
                    anchor_rows.append(next(row for row in rows if row["xy"] == [x, y]))
                if "expected_anchor_aex" in case:
                    actual = tuple(row["aex_f32"] for row in anchor_rows)
                    if actual != case["expected_anchor_aex"]:
                        raise RuntimeError(f"strict threshold anchor mismatch: {actual}")
                report["cases"].append(
                    {
                        "id": case["id"],
                        "source_mask_u8": mask.tolist(),
                        "staged_width": WIDTH,
                        "staged_height": HEIGHT,
                        "raw_threshold": case["raw_threshold"],
                        "param8": case["param8"],
                        "ds_scale": case["ds_scale"],
                        "portable_effective_threshold": case["raw_threshold"] * case["ds_scale"],
                        "execution": execution,
                        "anchors": anchor_rows,
                        "samples": rows,
                        "float32_exact_count": sum(row["f32_bits_match"] for row in rows),
                        "pf8_exact_count": sum(row["pf8_match"] for row in rows),
                        "sample_count": len(rows),
                        "sample_count_match": len(rows) == WIDTH * HEIGHT,
                    }
                )
    except Exception as error:
        report["failure"] = f"{type(error).__name__}: {error}"
        return report

    cases = report["cases"]
    if len(cases) != len(CASES):
        report["failure"] = f"case count mismatch: {len(cases)}"
        return report
    strict_ok = [row["aex_f32"] for row in cases[0]["anchors"]] == [0.0, 1.0, 1.0]
    ramp_exact = cases[1]["float32_exact_count"] == WIDTH * HEIGHT
    ds_difference = cases[2]["float32_exact_count"] < WIDTH * HEIGHT
    all_guards = all(
        case["execution"][key]
        for case in cases
        for key in ("detours_match", "callbacks_match", "imports_match")
    ) and all(case["sample_count_match"] for case in cases)
    observed_codes = sorted({row["aex_pf8"] for case in cases for row in case["samples"]})
    report["quantization_anchors"] = {
        "requested_pf8_codes": [2, 10, 64],
        "requested_normalized_values": ["2/255", "10/255", "64/255"],
        "observed_pf8_codes": observed_codes,
        "attained": {str(code): code in observed_codes for code in (2, 10, 64)},
        "unattainable_reason": (
            "For a 17x11 EDT containing a zero source, the smallest positive raw distance is 1 "
            "and the largest possible raw distance is sqrt(356); normalization therefore cannot "
            "produce PF8 codes 2 or 10. Code 64 is attained by the four-pixel ramp."
        ),
    }
    report["facts"] = {
        "strict_threshold_anchor_is_0_1_1": strict_ok,
        "ds1_trunc_ramp_is_float32_exact": ramp_exact,
        "ds_half_exposes_aex_mac_core_difference": ds_difference,
        "all_fail_closed_guards_match": all_guards,
    }
    report["inference"] = (
        "The ds_scale=0.5 difference is consistent with the current Mac caller scaling the raw "
        "threshold while FUN_181174760 receives the raw threshold in this direct helper call."
    )
    report["status"] = "pass" if strict_ok and ramp_exact and ds_difference and all_guards else "fail_closed"
    return report


def write_markdown(report: dict[str, object], path: Path) -> None:
    facts = report.get("facts", {})
    anchors = report.get("quantization_anchors", {})
    lines = [
        "# OLMDistanceGradation FUN_181174760 helper differential",
        "",
        f"- Status: `{report['status']}`",
        "- Scope: **helper parity only; not full AE field-generation parity**.",
        f"- AEX SHA-256 pin matched: `{report['binary']['hash_match']}` (`{report['binary']['sha256']}`).",
        "- Geometry: three `17x11` staged-mask cases using the existing fieldgen harness detours.",
        "",
        "## FACT",
        "",
        f"- `param8=1`, raw threshold `0`, `ds_scale=1`: strict-threshold anchors are `(0,1,1)`: `{facts.get('strict_threshold_anchor_is_0_1_1')}`.",
        f"- `param8=0`, raw threshold `4`, `ds_scale=1`: AEX and current core ramp are float32 exact: `{facts.get('ds1_trunc_ramp_is_float32_exact')}`.",
        f"- Repeating the ramp with explicit `ds_scale=0.5` exposes a field difference: `{facts.get('ds_half_exposes_aex_mac_core_difference')}`.",
        f"- Detour, callback, import, and sample-count guards all matched: `{facts.get('all_fail_closed_guards_match')}`.",
        f"- Requested PF8 anchors attained: `{json.dumps(anchors.get('attained', {}), sort_keys=True)}`.",
        f"- `{anchors.get('unattainable_reason', '')}`",
        "- The JSON records each source 8U mask, staged dimensions, raw threshold, param8, ds_scale, and all 187 AEX/core float32 and PF8 samples per case.",
        "",
        "## INFERENCE",
        "",
        f"- {report.get('inference', 'No inference: execution failed closed.')}",
        "- This bounded direct-call result does not cover AE host masks, resize to a different shape, full field construction, compose, or render output.",
        "",
        "## Smoke",
        "",
        "- Command: `tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_actual_aex_differential_20260716.py`",
        f"- Result: `{report['status']}`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = run()
    json_path = ROOT / "refs/conformance/olmdistancegradation_fieldgen_actual_aex_differential_20260716.json"
    md_path = ROOT / "refs/conformance/olmdistancegradation_fieldgen_actual_aex_differential_20260716.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    print(json.dumps({
        "status": report["status"],
        "facts": report.get("facts"),
        "quantization_anchors": report.get("quantization_anchors"),
        "failure": report.get("failure"),
        "outputs": [str(json_path.relative_to(ROOT)), str(md_path.relative_to(ROOT))],
    }, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

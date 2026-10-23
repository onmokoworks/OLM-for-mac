#!/usr/bin/env python3
"""Fresh, AE-free public admission negative closure for frozen OLMToonDilate.

Default execution is read-only: it rebuilds an isolated bundle and real-SDK
probe, replays every negative, validates the complete matrix, then compares the
fresh semantic report with the checked-in report.  Pass --write intentionally
to replace the JSON and Markdown artifacts.
"""

from __future__ import annotations

from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[2] / "tools/ucrt_cxx.py")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import copy
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
PROJECT = ROOT / "mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj"
PROBE = ROOT / "tools/emulation/probe_olmtoondilate_public_admission_negative_closure_20260813.cpp"
REPORT = ROOT / "refs/conformance/olmtoondilate_public_admission_negative_closure_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olmtoondilate_public_admission_negative_closure_20260813.md"
SOURCE_SHA256 = "42b47acbc3cd37bcaefdedc1b46f0507ed2e478c5eaab921f645f9055a9c8470"

DEPTHS = (8, 16, 32)
FAMILIES = ("copy", "fractional", "tie_semialpha", "high_downsample", "corner_seed")
MUTATIONS = (
    "input_data_null", "output_data_null", "input_span_overflow", "output_span_overflow",
    "input_width_plus1", "input_height_plus1", "output_width_plus1", "output_height_plus1",
    "input_rowbytes_plus1", "output_rowbytes_plus1",
    "input_extent_left_plus1", "input_extent_top_plus1", "input_extent_right_plus1", "input_extent_bottom_plus1",
    "output_extent_left_plus1", "output_extent_top_plus1", "output_extent_right_plus1", "output_extent_bottom_plus1",
    "input_origin_x_plus1", "input_origin_y_plus1", "output_origin_x_plus1", "output_origin_y_plus1",
    "host_output_origin_x_plus1", "host_output_origin_y_plus1", "input_flags_bit0", "output_flags_bit0",
    "input_format_other", "output_format_other", "declared_depth_other",
    "radius_nextafter_down", "radius_nextafter_up", "copy_radius_negative_zero",
    "downsample_x_num_plus1", "downsample_x_den_plus1", "downsample_y_num_plus1", "downsample_y_den_plus1",
    "source_first_pixel_bit0", "source_middle_pixel_bit0", "source_last_pixel_bit0", "input_padding_bit0",
    "overlap_exact", "overlap_output_after_input", "overlap_output_before_input",
)
CALLBACKS = (
    ("pre_callback_null", 516, "smart_pre_guard", (0,0,0,0,0,0,0,0,0)),
    ("pre_callback_error", 61, "checkout_layer", (1,0,0,0,0,0,0,0,0)),
    ("pixels_callback_null", 516, "smart_render_guard", (1,0,0,0,0,0,0,0,0)),
    ("pixels_callback_error", 62, "checkout_layer_pixels", (1,1,0,0,0,0,0,0,0)),
    ("pixels_success_null_world", 516, "world_checkout", (1,1,1,0,0,0,0,0,0)),
    ("output_callback_null", 516, "smart_render_guard", (1,0,0,0,0,0,0,0,0)),
    ("output_callback_error", 63, "checkout_output", (1,1,1,0,0,0,0,0,0)),
    ("output_success_null_world", 516, "world_checkout", (1,1,1,0,0,0,0,0,0)),
    ("checkout_param_callback_null", 516, "smart_render_guard", (1,0,0,0,0,0,0,0,0)),
    ("checkout_param_callback_error", 64, "checkout_param", (1,1,1,1,0,0,0,0,0)),
    ("checkin_param_callback_null", 516, "smart_render_guard", (1,0,0,0,0,0,0,0,0)),
    ("checkin_param_callback_error", 65, "checkin_param", (1,1,1,1,1,0,0,0,0)),
    ("pica_null", 516, "smart_render_guard", (1,0,0,0,0,0,0,0,0)),
    ("acquire_suite_function_null", 516, "world_suite_guard", (1,1,1,1,1,0,0,0,0)),
    ("release_suite_function_null", 516, "world_suite_guard", (1,1,1,1,1,0,0,0,0)),
    ("acquire_suite_error", 71, "acquire_world_suite", (1,1,1,1,1,1,0,0,0)),
    ("acquire_suite_success_null", 516, "world_suite_pointer", (1,1,1,1,1,1,1,0,0)),
    ("get_pixel_format_function_null", 516, "world_suite_pointer", (1,1,1,1,1,1,1,0,0)),
    ("get_input_pixel_format_error", 81, "input_pixel_format", (1,1,1,1,1,1,1,1,0)),
    ("get_output_pixel_format_error", 82, "output_pixel_format", (1,1,1,1,1,1,1,2,0)),
    ("release_suite_error", 83, "release_world_suite", (1,1,1,1,1,1,1,2,0)),
    ("optional_checkin_null_success", 0, "success_optional_callback_unused", (1,1,1,1,1,1,1,2,0)),
    ("optional_checkin_error_success", 0, "success_optional_callback_unused", (1,1,1,1,1,1,1,2,0)),
)
COUNT_KEYS = ("pre_checkout", "checkout_layer_pixels", "checkout_output", "checkout_param",
              "checkin_param", "acquire_world_suite", "release_world_suite", "get_pixel_format",
              "optional_checkin_layer_pixels")
RAW_KEYS = {"schema", "admission", "callbacks", "all_exact"}
ROW_KEYS = {"id", "exact", "stage", "actual_err", "input_storage_untouched", "output_storage_exact",
            "input_header_untouched", "output_header_untouched", "preserve_request_lifecycle_exact",
            "pre_render_lifecycle_exact", "pre_render_flags_exact", "callbacks"}
REPORT_KEYS = {"status", "schema", "production_source", "production_source_sha256", "probe_source",
               "probe_source_sha256", "owner", "architecture", "build_commands", "matrix",
               "row_digest_sha256", "admission", "callbacks", "claim_boundary"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_admission_ids() -> list[str]:
    ids = []
    for depth in DEPTHS:
        for family in FAMILIES:
            for mutation in MUTATIONS:
                if mutation == "copy_radius_negative_zero" and family != "copy":
                    continue
                ids.append(f"PF{depth}_{family}__{mutation}")
    return ids


def expected_callback_ids() -> list[str]:
    return [f"PF{depth}_copy__{name}" for depth in DEPTHS for name, *_ in CALLBACKS]


def row_digest(raw: dict) -> str:
    projection = {"admission": raw["admission"], "callbacks": raw["callbacks"]}
    return hashlib.sha256(json.dumps(projection, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _validate_common(row: dict, *, success: bool = False) -> None:
    if set(row) != ROW_KEYS or not isinstance(row.get("callbacks"), dict) or set(row["callbacks"]) != set(COUNT_KEYS):
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: row schema drifted: {row.get('id')}")
    required_true = ("exact", "input_storage_untouched", "output_storage_exact",
                     "input_header_untouched", "output_header_untouched",
                     "preserve_request_lifecycle_exact", "pre_render_lifecycle_exact", "pre_render_flags_exact")
    if any(row.get(key) is not True for key in required_true):
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: immutable/lifecycle gate failed: {row.get('id')}")
    if success and row.get("actual_err") != 0:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: success control failed: {row.get('id')}")


def validate_raw(raw: dict) -> dict:
    if set(raw) != RAW_KEYS:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: raw top-level schema drifted")
    if raw.get("schema") != "olmtoondilate.public-admission-negative/1" or raw.get("all_exact") is not True:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: probe schema/verdict drifted")
    admission = raw.get("admission")
    callbacks = raw.get("callbacks")
    admission_ids, callback_ids = expected_admission_ids(), expected_callback_ids()
    if not isinstance(admission, list) or [r.get("id") for r in admission] != admission_ids or len(set(admission_ids)) != len(admission_ids):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: admission identity/order drifted")
    if not isinstance(callbacks, list) or [r.get("id") for r in callbacks] != callback_ids or len(set(callback_ids)) != len(callback_ids):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: callback identity/order drifted")
    admission_counts = dict(zip(COUNT_KEYS, (1,1,1,1,1,1,1,2,0)))
    for row in admission:
        _validate_common(row)
        mutation = row["id"].split("__", 1)[1]
        expected_stage = "depth_format_gate" if mutation in {"input_format_other", "output_format_other", "declared_depth_other"} else "public_admission"
        if row.get("stage") != expected_stage or row.get("actual_err") != 516 or row.get("callbacks") != admission_counts:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: admission error/stage/counters drifted: {row.get('id')}")
    callback_expectations = {name: (err, stage, dict(zip(COUNT_KEYS, counts))) for name, err, stage, counts in CALLBACKS}
    for row in callbacks:
        name = row["id"].split("__", 1)[1]
        err, stage, counts = callback_expectations[name]
        _validate_common(row, success=err == 0)
        if row.get("actual_err") != err or row.get("stage") != stage or row.get("callbacks") != counts:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: callback error/stage/counters drifted: {row.get('id')}")
    return {
        "admission_rows_exact": len(admission), "callback_rows_exact": len(callbacks),
        "total_rows_exact": len(admission) + len(callbacks), "unique_ordered_ids_exact": True,
        "errors_stages_counters_exact": True, "full_storage_headers_padding_guards_exact": True,
        "optional_checkin_unused_exact": True, "returns_extra_pixels_flag_lifecycle_exact": True,
    }


def validate_report(report: dict) -> None:
    if set(report) != REPORT_KEYS:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: report top-level schema drifted")
    raw = {"schema":"olmtoondilate.public-admission-negative/1", "all_exact":True,
           "admission":report.get("admission"), "callbacks":report.get("callbacks")}
    gates = validate_raw(raw)
    expected_matrix = {"depths":list(DEPTHS), "families":list(FAMILIES), **gates}
    exact = (
        report.get("status") == "PASS_PUBLIC_ADMISSION_NEGATIVE_CLOSURE"
        and report.get("schema") == "olmtoondilate.public-admission-negative-report/1"
        and report.get("production_source") == str(SOURCE.relative_to(ROOT))
        and report.get("production_source_sha256") == SOURCE_SHA256
        and report.get("probe_source") == str(PROBE.relative_to(ROOT))
        and report.get("probe_source_sha256") == sha256(PROBE)
        and report.get("owner") == "fresh isolated arm64 bundle public EffectMain SmartPreRender -> SmartRender"
        and report.get("architecture") == "arm64-macos"
        and report.get("build_commands") == ["isolated xcodebuild candidate bundle", "real-SDK clang++ probe", "dlopen EffectMain replay"]
        and report.get("matrix") == expected_matrix
        and report.get("row_digest_sha256") == row_digest(raw)
        and report.get("claim_boundary") == "AE-free, install-free source-built public owner rejection closure; callback rows cover null pointers, returned errors, and success controls, not thrown callbacks or allocation failures; no native AE-host or installed-binary claim."
    )
    if not exact:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: report identity/matrix/digest/claim drifted")


def run_checked(command: list[str], label: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {label} failed rc={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def fresh_report() -> dict:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("BLOCKED_FAIL_CLOSED: arm64 macOS required")
    if sha256(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: frozen source identity drifted")
    compiler, xcodebuild, xcrun = map(shutil.which, (_UCRT_CXX, "xcodebuild", "xcrun"))
    if not all((compiler, xcodebuild, xcrun)):
        raise RuntimeError("BLOCKED_FAIL_CLOSED: build tools unavailable")
    sdk = run_checked([xcrun, "--show-sdk-path"], "SDK lookup").stdout.strip()
    with tempfile.TemporaryDirectory(prefix="olmtoondilate_admission_negative_") as tmp_text:
        tmp = Path(tmp_text); product = tmp / "Product"; probe_bin = tmp / "probe"
        run_checked([xcodebuild, "-project", str(PROJECT), "-target", "OLMToonDilate", "-configuration", "Debug",
                     "ARCHS=arm64", "ONLY_ACTIVE_ARCH=YES", "CODE_SIGNING_ALLOWED=NO",
                     f"CONFIGURATION_BUILD_DIR={product}", f"SYMROOT={tmp/'sym'}", f"OBJROOT={tmp/'obj'}",
                     f"SHARED_PRECOMPS_DIR={tmp/'precomp'}", "build"], "isolated bundle build")
        candidate = product / "OLMToonDilate.plugin/Contents/MacOS/OLMToonDilate"
        run_checked([_UCRT_CXX, "--compiler", compiler, "-std=c++17", "-O2", "-arch", "arm64", "-isysroot", sdk,
                     "-I", str(resolve_asset(ROOT/"Headers")), "-I", str(resolve_asset(ROOT/"Headers/SP")), "-I", str(resolve_asset(ROOT/"Util")),
                     "-I", str(resolve_asset(ROOT/"Resources")), str(PROBE), "-o", str(probe_bin)], "real-SDK probe build")
        execution = run_checked([str(probe_bin), str(candidate)], "public negative replay")
        raw = json.loads(execution.stdout)
        gates = validate_raw(raw)
    if sha256(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: source changed during replay")
    return {
        "status": "PASS_PUBLIC_ADMISSION_NEGATIVE_CLOSURE",
        "schema": "olmtoondilate.public-admission-negative-report/1",
        "production_source": str(SOURCE.relative_to(ROOT)), "production_source_sha256": SOURCE_SHA256,
        "probe_source": str(PROBE.relative_to(ROOT)), "probe_source_sha256": sha256(PROBE),
        "owner": "fresh isolated arm64 bundle public EffectMain SmartPreRender -> SmartRender",
        "architecture": "arm64-macos",
        "build_commands": ["isolated xcodebuild candidate bundle", "real-SDK clang++ probe", "dlopen EffectMain replay"],
        "matrix": {"depths": list(DEPTHS), "families": list(FAMILIES), **gates},
        "row_digest_sha256": row_digest(raw),
        "admission": raw["admission"], "callbacks": raw["callbacks"],
        "claim_boundary": "AE-free, install-free source-built public owner rejection closure; callback rows cover null pointers, returned errors, and success controls, not thrown callbacks or allocation failures; no native AE-host or installed-binary claim.",
    }


def markdown(report: dict) -> str:
    matrix = report["matrix"]
    return (
        "# OLMToonDilate public admission negative closure — 2026-08-13\n\n"
        f"Verdict: `{report['status']}`\n\n"
        f"Frozen production source: `{report['production_source_sha256']}`. A fresh isolated arm64 bundle rejected "
        f"all {matrix['admission_rows_exact']} admission one-aways and satisfied {matrix['callback_rows_exact']} "
        f"callback/lifecycle rows across PF8/PF16/PF32 ({matrix['total_rows_exact']} total).\n\n"
        "Every rejection pins the exact PF_Err, rejection stage, callback counts, unused optional layer checkin, "
        "and byte-for-byte immutability of input/output storage (including padding/guards) plus both world headers. "
        "The matrix covers all five admitted families, every geometry/extent/origin/flag/format/depth/radius/" 
        "downsample field, first/middle/last source bytes, input padding, and exact/directional partial overlap.\n\n"
        "Callback closure covers null and returned-error layer/output/parameter callbacks, null pica and suite "
        "function pointers, suite acquisition/get-format/release failures, null-world returns, and successful proof "
        "that optional `checkin_layer_pixels` is unused. This is AE-free and install-free; it does not claim native "
        "After Effects host execution.\n\n"
        "Reproduce read-only: `python3 tools/emulation/test_olmtoondilate_public_admission_negative_closure_20260813.py`\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    report = fresh_report()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"; doc = markdown(report)
    if args.write:
        REPORT.write_text(encoded, encoding="utf-8"); MARKDOWN.write_text(doc, encoding="utf-8")
    else:
        if not REPORT.is_file() or not MARKDOWN.is_file():
            raise RuntimeError("BLOCKED_FAIL_CLOSED: saved artifacts absent; use --write intentionally")
        saved = json.loads(REPORT.read_text(encoding="utf-8"))
        validate_report(saved)
        if saved != report or MARKDOWN.read_text(encoding="utf-8") != doc:
            raise RuntimeError("BLOCKED_FAIL_CLOSED: fresh replay differs from saved artifacts")
    print(json.dumps({"status":report["status"], "rows":report["matrix"]["total_rows_exact"],
                      "row_digest_sha256":report["row_digest_sha256"], "mode":"write" if args.write else "read-only"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

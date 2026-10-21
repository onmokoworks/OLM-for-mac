#!/usr/bin/env python3
"""Close one fixed Kira Mode3 32x18 tuple through public Classic and Smart."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
BASE_HARNESS = ROOT / "tools/emulation/olmkirakira_public_smart_bounded_closure_harness_20260812.cpp"
ORACLE_PROBE = ROOT / "tools/emulation/probe_olmkirakira_mode3_32x18_exported_candidate_20260814.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode3_32x18_public_closure_20260814.json"
DOC = REPORT.with_suffix(".md")
EXPECTED = {
    8: "77c5825780a940fcb87825807c9d91eda4919e97f72b4c34977e05f7e6d3ac6e",
    16: "4d635cd68aacbdcbd6670d597fbe27e04444dd499a6c63f9b74153941a6189e8",
    32: "9ffcaf2aedd97e989bfa1a2825e3f3ef2bd26aa40be9d74f71db85c7fa7abf23",
}
NEGATIVES = {
    "pre_request_unlisted", "rotation_one", "source_mutation",
    "input_width", "output_extent", "output_rowbytes_extra", "declared_depth",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def transformed_harness() -> str:
    code = BASE_HARNESS.read_text(encoding="utf-8")
    tuple_block = re.compile(r"static const Tuple kTuples\[\] = \{.*?\n\};", re.S)
    code, count = tuple_block.subn(
        'static const Tuple kTuples[] = {\n'
        '    {"m3_h50_r0_32x18", 3, 1, 0, .1, 50, 0, 0, false, false, false},\n'
        '};', code,
    )
    if count != 1:
        raise AssertionError("tuple block marker drift")
    replacements = {
        "request->rect.right == 5 && request->rect.bottom == 3":
            "request->rect.right == 32 && request->rect.bottom == 18",
        "result->result_rect = {0, 0, 5, 3};": "result->result_rect = {0, 0, 32, 18};",
        "result->max_result_rect = {0, 0, 5, 3};": "result->max_result_rect = {0, 0, 32, 18};",
        "result->ref_width = 5;": "result->ref_width = 32;",
        "result->ref_height = 3;": "result->ref_height = 18;",
        "for (int y = 0; y < 3; ++y)": "for (int y = 0; y < 18; ++y)",
        "constexpr int W = 5, H = 3, PAD = 12;": "constexpr int W = 32, H = 18, PAD = 12;",
        "PF_LRect{0,0,5,3} : PF_LRect{1,1,4,3}": "PF_LRect{0,0,32,18} : PF_LRect{0,0,32,18}",
        "pre_out.result_rect.right == 5 && pre_out.result_rect.bottom == 3":
            "pre_out.result_rect.right == 32 && pre_out.result_rect.bottom == 18",
        "pre_out.max_result_rect.right == 5 && pre_out.max_result_rect.bottom == 3":
            "pre_out.max_result_rect.right == 32 && pre_out.max_result_rect.bottom == 18",
        "init_params(ramp_case ? kTuples[12] : kTuples[9]);": "init_params(kTuples[0]);",
        "set_pixel(p, i, !ramp_case);": "set_pixel(p, i, false);",
        "PF_LRect{1,1,4,3};": "PF_LRect{0,0,32,18};",
        "PreRenderData bad_pre{5,3};": "PreRenderData bad_pre{32,18};",
        "bad_pre.comp_width=4": "bad_pre.comp_width=31",
        "bad_pre.comp_height=2": "bad_pre.comp_height=17",
    }
    for old, new in replacements.items():
        if old not in code:
            raise AssertionError(f"harness marker drift: {old!r}")
        code = code.replace(old, new)
    code = code.replace(
        "else if (!std::strcmp(name, \"tuple_mutation\")) g_defs[OLMKIRAKIRA_CHANNEL].u.pd.value = 2;",
        "else if (!std::strcmp(name, \"tuple_mutation\")) g_defs[OLMKIRAKIRA_CHANNEL].u.pd.value = 2;\n"
        "    else if (!std::strcmp(name, \"rotation_one\")) g_defs[OLMKIRAKIRA_GLOW_ROTATION].u.fs_d.value = 1.0;",
    )
    # For indices beyond the old 5x3 fixture, every typed source must first wrap
    # to the declared source byte, then undergo the public depth conversion.
    code = code.replace("cv(i * 15)", "cv((i * 15) & 255)")
    code = code.replace("cv(64 + i * 11)", "cv((64 + i * 11) & 255)")
    code = code.replace("cv(i * 11)", "cv((i * 11) & 255)")
    code = code.replace("cv(i * 7)", "cv((i * 7) & 255)")
    code = code.replace("i * 15 / 255.0f", "((i * 15) & 255) / 255.0f")
    code = code.replace("(64 + i * 11) / 255.0f", "((64 + i * 11) & 255) / 255.0f")
    code = code.replace("i * 11 / 255.0f", "((i * 11) & 255) / 255.0f")
    code = code.replace("i * 7 / 255.0f", "((i * 7) & 255) / 255.0f")
    main = r'''int main() {
    int failed = 0;
    failed |= run_case<PF_Pixel8>(PF_PixelFormat_ARGB32, 8, kTuples[0], -1, -1, true);
    failed |= run_case<PF_Pixel16>(PF_PixelFormat_ARGB64, 16, kTuples[0], -1, -1, true);
    failed |= run_case<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, kTuples[0], -1, -1, true);
    for (int ordinal = 0; ordinal < 25; ++ordinal) {
        failed |= run_case<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, kTuples[0], ordinal, -1, true);
        failed |= run_case<PF_PixelFloat>(PF_PixelFormat_ARGB128, 32, kTuples[0], -1, ordinal, true);
    }
    for (const char *name : {"pre_request_unlisted", "rotation_one", "source_mutation",
             "input_width", "output_extent", "output_rowbytes_extra", "declared_depth"})
        failed |= run_negative(name);
    return failed;
}'''
    code, count = re.subn(r"int main\(\) \{.*?\n\}", main, code, count=1, flags=re.S)
    if count != 1:
        raise AssertionError("main marker drift")
    return code


def parse_line(line: str) -> dict[str, str]:
    return dict(part.split("=", 1) for part in shlex.split(line)[1:] if "=" in part)


def active_sha(row: dict[str, str], field: str) -> str:
    return sha_bytes(bytes.fromhex(row[field]))


def run_public_harness() -> tuple[list[dict], list[dict], list[dict]]:
    code = transformed_harness()
    with tempfile.TemporaryDirectory(prefix="kira_mode3_32x18_public_") as raw:
        directory = Path(raw)
        cpp = directory / "closure.cpp"
        exe = directory / "closure"
        cpp.write_text(code, encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        define = '-DKIRA_SOURCE="' + str(SOURCE) + '"'
        command = [
            "clang++", "-std=c++20", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-isysroot", sdk, "-w", "-I", str(ROOT / "Headers"),
            "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
            "-I", str(ROOT / "Resources"), define, str(cpp),
            str(ROOT / "Util/AEGP_SuiteHandler.cpp"),
            str(ROOT / "Util/MissingSuiteError.cpp"),
            "-framework", "Cocoa", "-o", str(exe),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(built.stderr[-12000:])
        ran = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
        if ran.returncode:
            raise RuntimeError(f"harness={ran.returncode}\n{ran.stdout[-12000:]}\n{ran.stderr}")
    case_rows = [parse_line(line) for line in ran.stdout.splitlines() if line.startswith("REQUEST_CONTROL ")]
    positives = [row for row in case_rows if row["fail"] == "-1/-1"]
    lifecycle = [row for row in case_rows if row["fail"] != "-1/-1"]
    negative_rows = [parse_line(line) for line in ran.stdout.splitlines() if line.startswith("NEG ")]
    if len(positives) != 3 or len(lifecycle) != 50:
        raise AssertionError((len(positives), len(lifecycle)))
    cells = []
    for row in positives:
        depth = int(row["depth"])
        smart_sha = active_sha(row, "smart_hex")
        classic_sha = active_sha(row, "classic_hex")
        if not (row["pre"] == row["smart"] == row["classic"] == "0" and
                row["callbacks"] == "1/1/1/0" and row["params"] == "25/25" and
                row["param_order"] == row["input"] == row["headers"] == row["pads"] ==
                row["exact"] == row["extra"] == row["requested_full"] == "1" and
                smart_sha == classic_sha == EXPECTED[depth]):
            raise AssertionError(row)
        cells.append({
            "depth": depth, "oracle_sha256": EXPECTED[depth],
            "mac_smart_sha256": smart_sha, "mac_classic_sha256": classic_sha,
            "input_header_and_full_storage_immutable": True,
            "input_and_output_padding_preserved": True,
            "parameter_checkout_checkin": [25, 25],
            "pixel_callbacks": [1, 1, 1, 0],
        })
    lifecycle_rows = []
    for row in lifecycle:
        if row["injected_ok"] != "1" or row["input"] != "1" or row["headers"] != "1":
            raise AssertionError(row)
        lifecycle_rows.append({
            "failure": row["fail"], "error": int(row["smart"]),
            "callback_shape": row["callbacks"], "attempts": row["attempts"],
            "input_immutable": True, "output_untouched": True,
        })
    if {row["name"] for row in negative_rows} != NEGATIVES:
        raise AssertionError({row["name"] for row in negative_rows})
    negatives = []
    for row in negative_rows:
        if not (int(row["error"]) != 0 and row["output_untouched"] == "1" and
                row["input_headers_immutable"] == "1"):
            raise AssertionError(row)
        negatives.append({
            "name": row["name"], "error": int(row["error"]),
            "callbacks": row["callbacks"], "output_untouched": True,
            "input_and_headers_immutable": True,
        })
    return cells, lifecycle_rows, negatives


def run_oracle_probe() -> dict:
    ran = subprocess.run(["python3", str(ORACLE_PROBE)], cwd=ROOT, capture_output=True, text=True)
    if ran.returncode:
        raise RuntimeError(ran.stdout + ran.stderr)
    data = json.loads(ran.stdout)
    if data["status"] != "exact_candidate":
        raise AssertionError(data)
    got = {int(row["depth"][2:]): row["windows_exported_smart_raw_sha256"] for row in data["rows"]}
    if got != EXPECTED or not all(row["windows_guards_intact"] for row in data["rows"]):
        raise AssertionError(data)
    return data


def generate() -> dict:
    oracle = run_oracle_probe()
    cells, lifecycle, negatives = run_public_harness()
    return {
        "schema": "olmkirakira.mode3-32x18-public-closure/1",
        "date": "2026-08-14",
        "status": "raw_exact_bounded_public_classic_and_smart",
        "identities": {
            "production_source_sha256": sha(SOURCE),
            "base_harness_sha256": sha(BASE_HARNESS),
            "oracle_probe_sha256": sha(ORACLE_PROBE),
            "aex_sha256": oracle["aex_sha256"],
        },
        "fixture": oracle["fixture"],
        "positive_cells": cells,
        "parameter_lifecycle_failures": lifecycle,
        "negative_rows": negatives,
        "contract": {
            "dimensions": [32, 18], "row_padding_bytes": 12,
            "tuple": "Mode3/Merge1/Horizontal50/Rotation0/Gain0.1/default remaining controls",
            "source": "exact wrapped-linear RGBA fixture only",
            "smart_request": "full 32x18 only",
            "windows_route": "exported SmartPreRender -> SmartRender",
            "mac_routes": ["public PF_Cmd_RENDER", "public SmartPreRender -> SmartRender"],
            "ae_launched": False, "installed": False,
        },
        "boundary": (
            "Exactly three cells: this one tuple/source/layout at PF8/PF16/PF32. Rotation1, "
            "source mutation, other layout/extent/rowbytes/depth, partial 32x18 requests, and "
            "parameter lifecycle failures remain fail-closed before output mutation."
        ),
    }


def validate(data: dict) -> None:
    fresh = generate()
    if data != fresh:
        raise AssertionError("fresh Kira Mode3 32x18 closure differs from canonical report")


def markdown(data: dict) -> str:
    return (
        "# OLMKiraKira Mode3 32x18 bounded public closure (2026-08-14)\n\n"
        "Status: **raw_exact_bounded_public_classic_and_smart**\n\n"
        "The one wrapped-linear 32x18 RGBA source at Mode3 / Merge1 / Horizontal Length 50 / "
        "Rotation 0 / Brightness Gain 0.1 is raw-active-byte exact across the current Windows "
        "exported Smart owner and the Mac public Classic and Smart owners at PF8, PF16, and PF32. "
        "Input storage/headers and 12-byte row padding remain immutable.\n\n"
        "Rotation 1, source mutation, layout/extent/rowbytes/depth mutations, a partial request, "
        "and every parameter checkout/checkin ordinal fail closed with output untouched. No install "
        "or After Effects launch is performed.\n\n"
        "Verify: `python3 tools/emulation/test_olmkirakira_mode3_32x18_public_closure_20260814.py`\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        data = generate()
        REPORT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        DOC.write_text(markdown(data), encoding="utf-8")
    else:
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        validate(data)
    print(json.dumps({"status": data["status"], "cells": len(data["positive_cells"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

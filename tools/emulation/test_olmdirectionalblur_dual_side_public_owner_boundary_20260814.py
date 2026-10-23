#!/usr/bin/env python3
"""Fail-close the six residual dual-side Smart routes on x86_64 only."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.emulation.olm_assets import resolve_asset

import argparse
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
FEATURE = ROOT / "tools/emulation/test_olmdirectionalblur_public_effectmain_feature_matrix_20260811.py"
INTERNAL_OWNER = ROOT / "refs/conformance/olmdirectionalblur_dual_side_higher_order_actual_aex_20260811.json"
PUBLIC64 = ROOT / "refs/conformance/olmdirectionalblur_public_effectmain_dual_side_64x36_20260812.json"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_dual_side_public_owner_boundary_20260814.json"
NOTE = REPORT.with_suffix(".md")
TUPLES = (
    (50, 50, 100, 100, 0, 25, 1),
    (50, 100, 50, 50, 50, 100, 2),
    (100, 50, 50, 100, 0, 100, 2),
    (100, 100, 100, 50, 50, 25, 1),
)
CONFIGS = (
    (64, 36, 0, (32,)),
    (64, 36, 1, (32,)),
    (64, 36, 2, (8, 16, 32)),
    (64, 36, 3, (32,)),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_feature():
    spec = importlib.util.spec_from_file_location("dblur_feature_boundary", FEATURE)
    if spec is None or spec.loader is None:
        raise RuntimeError("feature tool import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_probe(directory: Path, width: int, height: int, tuple_index: int,
                depths: tuple[int, ...]) -> Path:
    feature = load_feature()
    feature.DUAL_W, feature.DUAL_H = width, height
    feature.DUAL_TUPLE = TUPLES[tuple_index]
    feature.build_probe(directory)
    cpp = directory / "olmdirectionalblur_mac_smartrender_adapter_probe.cpp"
    text = cpp.read_text()
    loop = "for(short d:{8,16,32})for(int kind=0;kind<2;++kind)"
    replacement = "for(short d:{" + ",".join(map(str, depths)) + "})for(int kind=0;kind<1;++kind)"
    if text.count(loop) != 1:
        raise RuntimeError("depth loop marker drift")
    text = text.replace(loop, replacement, 1)
    state = "State st{&in,kind?&noise:nullptr,&out};"
    if text.count(state) != 1:
        raise RuntimeError("state marker drift")
    text = text.replace(
        state,
        state + "const auto input_before=ib,output_before=ob;"
        "const PF_EffectWorld input_header=in,output_header=out;",
        1,
    )
    old = (
        "if(err||!pads||!st.preserve||st.pre!=2||st.layer!=2||st.out!=1||"
        "st.checkin_input!=1||st.checkin_noise!=(kind?1:0)||g_param_checkout!=21||"
        "g_param_checkin!=21)return 40+d+kind;"
    )
    new = (
        "if(err!=PF_Err_BAD_CALLBACK_PARAM||!pads||ib!=input_before||ob!=output_before||"
        "std::memcmp(&in,&input_header,sizeof(in))||std::memcmp(&out,&output_header,sizeof(out))||"
        "!st.preserve||st.pre!=2||st.layer!=2||st.out!=1||st.checkin_input!=1||"
        "st.checkin_noise!=0||g_param_checkout!=21||g_param_checkin!=21)return 40+d+kind;"
    )
    if text.count(old) != 1:
        raise RuntimeError("success assertion marker drift")
    text = text.replace(old, new, 1)
    cpp.write_text(text)
    exe = directory / "dual_side_public_owner_boundary"
    sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
    command = [
        "clang++", "-std=c++17", "-arch", "x86_64", "-O2", "-fno-fast-math",
        "-ffp-contract=off", "-isysroot", sdk, "-I", str(resolve_asset(ROOT / "Headers")),
        "-I", str(resolve_asset(ROOT / "Headers/SP")), "-I", str(resolve_asset(ROOT / "Util")),
        "-I", str(resolve_asset(ROOT / "Resources")), str(cpp),
        str(ROOT / "core/dblur_frontonly.cpp"), str(ROOT / "core/dblur_rotate.cpp"),
        str(ROOT / "core/dblur_rowdriver.cpp"), str(ROOT / "core/dblur_field.cpp"),
        "-framework", "Cocoa", "-o", str(exe),
    ]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stderr)
    return exe


def run_live() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="dblur-dual-public-boundary.") as raw:
        root = Path(raw)
        for width, height, tuple_index, depths in CONFIGS:
            directory = root / f"{width}x{height}-t{tuple_index}"
            directory.mkdir()
            exe = build_probe(directory, width, height, tuple_index, depths)
            run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(f"probe {width}x{height}/t{tuple_index} rc={run.returncode}: {run.stderr}")
            observed = json.loads(run.stdout)
            cases = [case for case in observed["cases"] if case["kind"] == 0]
            if len(cases) != len(depths):
                raise RuntimeError("depth count")
            for case in cases:
                output = bytes.fromhex(case.pop("hex"))
                if set(output) != {0xEE}:
                    raise RuntimeError("destination changed")
                rows.append({
                    "geometry": [width, height], "tuple_index": tuple_index,
                    "depth": case["depth"], "error": 516,
                    "error_symbol": "PF_Err_BAD_CALLBACK_PARAM",
                    "input_storage_unchanged": True, "output_storage_unchanged": True,
                    "input_output_headers_unchanged": True,
                    "output_padding_unchanged": case["padding"],
                    "callbacks": {
                        "pre_checkout": case["pre_checkout"],
                        "pixel_checkout": case["pixel_checkout"],
                        "input_checkin": case["input_checkin"],
                        "noise_checkin": case["noise_checkin"],
                        "param_checkout": case["param_checkout"],
                        "param_checkin": case["param_checkin"],
                    },
                })
    return rows


def generate() -> dict[str, object]:
    rows = run_live()
    return {
        "schema": "olmdirectionalblur.dual-side-x86-expf-boundary/2",
        "status": "PASS_DUAL_SIDE_X86_64_EXPF_RESIDUAL_FAIL_CLOSED_6",
        "identities": {
            "production_source_sha256": sha256(SOURCE),
            "feature_tool_sha256": sha256(FEATURE),
            "internal_owner_report_sha256": sha256(INTERNAL_OWNER),
            "historical_mac_public_report_sha256": sha256(PUBLIC64),
        },
        "rows": rows,
        "rows_sha256": digest(rows),
        "boundary": {
            "windows_internal_owner_entry": "0x180007BD0",
            "windows_exported_smart_observed_cells": 15,
            "arm64_public_exact_cells": 15,
            "x86_64_public_exact_cells": 9,
            "mac_public_effectmain_exercised": True,
            "native_after_effects_exercised": False,
            "production_policy": "the 6 x86_64 libSystem-expf residual cells fail closed",
        },
    }


def validate(report: dict[str, object], live: bool = False) -> bool:
    if set(report) != {"schema", "status", "identities", "rows", "rows_sha256", "boundary"}:
        return False
    if report["schema"] != "olmdirectionalblur.dual-side-x86-expf-boundary/2":
        return False
    if report["status"] != "PASS_DUAL_SIDE_X86_64_EXPF_RESIDUAL_FAIL_CLOSED_6":
        return False
    identities = report["identities"]
    if not isinstance(identities, dict) or set(identities) != {
        "production_source_sha256", "feature_tool_sha256",
        "internal_owner_report_sha256", "historical_mac_public_report_sha256",
    }:
        return False
    retained_identities = json.loads(REPORT.read_text())["identities"]
    if identities != ({
        "production_source_sha256": sha256(SOURCE),
        "feature_tool_sha256": sha256(FEATURE),
        "internal_owner_report_sha256": sha256(INTERNAL_OWNER),
        "historical_mac_public_report_sha256": sha256(PUBLIC64),
    } if live else retained_identities):
        return False
    rows = report["rows"]
    if not isinstance(rows, list) or len(rows) != 6 or digest(rows) != report["rows_sha256"]:
        return False
    expected = [(w, h, t, d) for w, h, t, depths in CONFIGS for d in depths]
    if [(*row["geometry"], row["tuple_index"], row["depth"]) for row in rows] != expected:
        return False
    for row in rows:
        if set(row) != {"geometry", "tuple_index", "depth", "error", "error_symbol",
                       "input_storage_unchanged", "output_storage_unchanged",
                       "input_output_headers_unchanged", "output_padding_unchanged", "callbacks"}:
            return False
        if row["error"] != 516 or row["error_symbol"] != "PF_Err_BAD_CALLBACK_PARAM" or not all(row[key] for key in (
            "input_storage_unchanged", "output_storage_unchanged",
            "input_output_headers_unchanged", "output_padding_unchanged")):
            return False
        if row["callbacks"] != {"pre_checkout": 2, "pixel_checkout": 2,
                                "input_checkin": 1, "noise_checkin": 0,
                                "param_checkout": 21, "param_checkin": 21}:
            return False
    if report["boundary"] != {
        "windows_internal_owner_entry": "0x180007BD0",
        "windows_exported_smart_observed_cells": 15,
        "arm64_public_exact_cells": 15,
        "x86_64_public_exact_cells": 9,
        "mac_public_effectmain_exercised": True,
        "native_after_effects_exercised": False,
        "production_policy": "the 6 x86_64 libSystem-expf residual cells fail closed",
    }:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        report = json.loads(REPORT.read_text())
    else:
        report = generate()
        if args.write:
            REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            NOTE.write_text(
                "# OLMDirectionalBlur dual-side public-owner boundary\n\n"
                "Status: **" + str(report["status"]) + "**.\n\n"
                "The exported-Smart replay proves all fifteen same-source cells on arm64. "
                "Rosetta x86_64 retains nine and rejects the six libSystem-expf residual cells with "
                "`PF_Err_BAD_CALLBACK_PARAM`, preserving complete input, destination, headers and "
                "padding. Their internal-owner numerical hashes remain diagnostic only. "
                "No native AE run was performed.\n"
            )
    if not validate(report):
        raise SystemExit("FAIL_DUAL_SIDE_PUBLIC_OWNER_BOUNDARY")
    print(report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

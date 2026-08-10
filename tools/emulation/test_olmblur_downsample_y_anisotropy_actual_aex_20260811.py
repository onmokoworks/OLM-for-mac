#!/usr/bin/env python3
"""Prove OLMBlur downsample_y is inactive when downsample_x is 1/1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810 as base

ROOT = Path(__file__).resolve().parents[2]
SOURCE_FIXTURE = Path(__file__).parent / "fixtures/olmblur_amount_repeat_legacy_matrix_20260810"
FIXTURE = Path(__file__).parent / "fixtures/olmblur_downsample_y_anisotropy_20260811"
MANIFEST = FIXTURE / "manifest.json"
REPORT = ROOT / "refs/conformance/olmblur_downsample_y_anisotropy_actual_aex_20260811.json"
DECOMP = ROOT / "decomp/OLMBlur.aex.c.txt"
RATIOS = ((1, 2), (1, 1), (2, 1))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export() -> None:
    source_manifest = json.loads((SOURCE_FIXTURE / "manifest.json").read_text())
    rows = [row for row in source_manifest["cases"] if row["repeat"] in (1, 2)]
    assert len(rows) == 24
    FIXTURE.mkdir(parents=True, exist_ok=True)
    cases = []
    for row in rows:
        for num, den in RATIOS:
            item = {key: row[key] for key in ("depth", "amount", "smoothness", "repeat", "bias_direction", "legacy",
                                                "source_sha256", "expected_sha256", "instructions", "callback_count")}
            item.update({"id": f"{row['id']}_dy{num}_{den}", "downsample_x": [1, 1], "downsample_y": [num, den],
                         "source": str((SOURCE_FIXTURE / row["source"]).relative_to(ROOT)),
                         "expected": str((SOURCE_FIXTURE / row["expected"]).relative_to(ROOT)),
                         "oracle_reuse": row["id"]})
            cases.append(item)
    MANIFEST.write_text(json.dumps({"schema": "olmblur.downsample-y-anisotropy.actual-aex/1",
        "plugin": "OLMBlur", "actual_aex_sha256": base.AEX_SHA256, "geometry": [24, 24],
        "worker_scale_contract": {"numerator_offset": "context+0x11c", "denominator_offset": "context+0x120",
            "meaning": "single horizontal render-scale rational; no second/y rational is consumed by the six typed workers"},
        "oracle": "hash-pinned actual-AEX complete buffers at x scale 1/1; reused across y ratios",
        "cases": cases}, indent=2, sort_keys=True) + "\n")


def probe_source() -> str:
    source = base.public_probe_source()
    replacements = {
        "if (argc != 12) return 2;": "if (argc != 14) return 2;",
        "const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), legacy = std::atoi(argv[8]), padding = std::atoi(argv[9]);":
            "const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), legacy = std::atoi(argv[8]), dy_num = std::atoi(argv[9]), dy_den = std::atoi(argv[10]), padding = std::atoi(argv[11]);",
        "const auto source = read_file(argv[10]), expected = read_file(argv[11]);":
            "const auto source = read_file(argv[12]), expected = read_file(argv[13]);",
        "in_data.downsample_x = {1,1}; in_data.downsample_y = {1,1};":
            "in_data.downsample_x = {1,1}; in_data.downsample_y = {dy_num,dy_den};",
    }
    for old, new in replacements.items():
        if old not in source:
            raise RuntimeError(f"probe shape drift: {old}")
        source = source.replace(old, new)
    return source


def compile_probe(directory: Path) -> Path:
    source = directory / "probe.cpp"
    source.write_text(probe_source().replace("__OLMBLUR_MAC_SOURCE__", str(ROOT / "mac/OLMBlur/OLMBlur.cpp").replace("\\", "\\\\").replace('"', '\\"')))
    executable = directory / "probe"
    sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
    command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-DOLMBLUR_HOSTLESS_RENDER_HARNESS=1",
        "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk, "-I", str(ROOT/"Headers"), "-I", str(ROOT/"Headers/SP"),
        "-I", str(ROOT/"Util"), "-I", str(ROOT/"Resources"), "-I", str(ROOT/"core"), str(source),
        *[str(ROOT/p) for p in ("core/olmblur_helper.cpp", "core/olmblur_fullworker_helper.cpp", "core/olmblur_worker16_nonlegacy.cpp",
        "core/olmblur_worker16_legacy.cpp", "core/olmblur_worker32_nonlegacy.cpp", "core/olmblur_worker32_legacy.cpp",
        "core/olmblur_worker8_legacy.cpp", "core/olmblur_worker_orchestration.cpp")], "-framework", "Cocoa", "-o", str(executable)]
    subprocess.run(command, cwd=ROOT, check=True)
    return executable


def verify() -> None:
    assert sha256(base.AEX.read_bytes()) == base.AEX_SHA256
    manifest = json.loads(MANIFEST.read_text())
    assert len(manifest["cases"]) == 72
    decomp = DECOMP.read_text(errors="replace")
    scale_expressions = re.findall(r"param_1 \+ 0x11c.*?param_1 \+ 0x120", decomp, re.S)
    assert len(scale_expressions) >= 6
    production = (ROOT / "mac/OLMBlur/OLMBlur.cpp").read_text()
    assert "in_data->downsample_x.num" in production and "in_data->downsample_x.den" in production
    blur_render = production[production.index("BlurRender("):production.index("static PF_Err\nRender(")]
    assert "downsample_y" not in blur_render
    results = []
    with tempfile.TemporaryDirectory(prefix="olmblur_downsample_y_") as name:
        executable = compile_probe(Path(name))
        for case in manifest["cases"]:
            source, expected = ROOT/case["source"], ROOT/case["expected"]
            assert sha256(source.read_bytes()) == case["source_sha256"]
            assert sha256(expected.read_bytes()) == case["expected_sha256"]
            num, den = case["downsample_y"]
            padding = {8: 17, 16: 23, 32: 32}[case["depth"]]
            run = subprocess.run([str(executable), str(case["depth"]), "24", "24", str(case["amount"]), "100",
                str(case["repeat"]), "1", str(case["legacy"]), str(num), str(den), str(padding), str(source), str(expected)],
                capture_output=True, text=True, cwd=ROOT)
            if run.returncode:
                raise RuntimeError(f"{case['id']}: {run.stdout}\n{run.stderr}")
            observed = json.loads(run.stdout)
            assert observed["mismatched_bytes"] == observed["padding_mismatches"] == 0
            results.append({"id": case["id"], "oracle_reuse": case["oracle_reuse"], "production": observed})
    REPORT.write_text(json.dumps({"schema": "olmblur.downsample-y-anisotropy.production/1", "status": "exact_no_effect",
        "actual_aex_sha256": base.AEX_SHA256, "case_count": 72, "geometry": [24,24],
        "matrix": {"depth": [8,16,32], "amount": [5,129.4], "repeat": [1,2], "legacy": [0,1],
                   "downsample_x": [1,1], "downsample_y": [[n,d] for n,d in RATIOS]},
        "decision": "downsample_y does not affect Amount, geometry, or kernel in this fixed-world OLMBlur family",
        "binary_contract": "all six typed AEX workers consume the single context+0x11c/+0x120 scale rational; retained x=1/1 worker outputs are the y-invariant oracle",
        "production_contract": "BlurRender consumes downsample_x only; public SmartPreRender/SmartRender output remains exact for all y ratios",
        "cases": results, "not_proven": ["native AE preview world sizing", "world dimensions changed by host", "non-square pixel aspect", "other geometry/bias/smoothness"]}, indent=2, sort_keys=True)+"\n")
    print("PASS_OLMBLUR_DOWNSAMPLE_Y_ANISOTROPY cases=72 exact_no_effect=1")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    export() if args.export else verify()

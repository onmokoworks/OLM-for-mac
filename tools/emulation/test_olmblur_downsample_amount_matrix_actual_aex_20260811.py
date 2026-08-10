#!/usr/bin/env python3
"""OLMBlur PF_InData downsample_x x Amount rational-contract matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810 as base

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/olmblur_downsample_amount_matrix_20260811"
MANIFEST = FIXTURE / "manifest.json"
REPORT = ROOT / "refs/conformance/olmblur_downsample_amount_matrix_actual_aex_20260811.json"
RATIOS = ((1, 2), (1, 1), (2, 1))
AMOUNTS = (5.0, 129.4)
REPEATS = (1, 2)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def export() -> None:
    assert sha256(base.AEX.read_bytes()) == base.AEX_SHA256
    FIXTURE.mkdir(parents=True, exist_ok=True)
    cases = []
    for depth in (8, 16, 32):
        source = base.source_bytes(depth)
        source_name = f"source_{base.FILE_NAMES[depth]}"
        (FIXTURE / source_name).write_bytes(source)
        for amount in AMOUNTS:
            for repeat in REPEATS:
                for legacy in (0, 1):
                    for num, den in RATIOS:
                        effective = amount * num / den
                        expected, run = base.run_actual(depth, legacy, effective, repeat, source)
                        tag = str(amount).replace(".", "_")
                        case_id = f"pf{depth}_amount{tag}_repeat{repeat}_legacy{legacy}_ds{num}_{den}"
                        expected_name = f"expected_{case_id}.bin"
                        (FIXTURE / expected_name).write_bytes(expected)
                        cases.append({"id": case_id, "depth": depth, "amount": amount,
                            "effective_worker_amount": effective, "repeat": repeat, "legacy": legacy,
                            "downsample_x": [num, den], "downsample_y": [1, 1],
                            "smoothness": 100.0, "bias_direction": 1,
                            "source": source_name, "source_sha256": sha256(source),
                            "expected": expected_name, "expected_sha256": sha256(expected), **run})
                        print(f"AEX {case_id} effective={effective:.9g} instructions={run['instructions']}", flush=True)
    MANIFEST.write_text(json.dumps({"schema": "olmblur.downsample-amount.actual-aex/1",
        "plugin": "OLMBlur", "actual_aex_sha256": base.AEX_SHA256,
        "geometry": [base.WIDTH, base.HEIGHT], "world_dimensions_constant": True,
        "contract": "actual typed worker receives UI Amount * PF_InData.downsample_x.num / den",
        "cases": cases}, indent=2, sort_keys=True) + "\n")


def probe_source() -> str:
    source = base.public_probe_source()
    replacements = {
        "if (argc != 12) return 2;": "if (argc != 14) return 2;",
        "const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), legacy = std::atoi(argv[8]), padding = std::atoi(argv[9]);":
            "const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), legacy = std::atoi(argv[8]), ds_num = std::atoi(argv[9]), ds_den = std::atoi(argv[10]), padding = std::atoi(argv[11]);",
        "const auto source = read_file(argv[10]), expected = read_file(argv[11]);":
            "const auto source = read_file(argv[12]), expected = read_file(argv[13]);",
        "in_data.downsample_x = {1,1}; in_data.downsample_y = {1,1};":
            "in_data.downsample_x = {ds_num,ds_den}; in_data.downsample_y = {1,1};",
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
    assert manifest["actual_aex_sha256"] == base.AEX_SHA256 and len(manifest["cases"]) == 72
    results = []
    with tempfile.TemporaryDirectory(prefix="olmblur_downsample_") as name:
        executable = compile_probe(Path(name))
        for case in manifest["cases"]:
            source, expected = FIXTURE/case["source"], FIXTURE/case["expected"]
            assert sha256(source.read_bytes()) == case["source_sha256"]
            assert sha256(expected.read_bytes()) == case["expected_sha256"]
            num, den = case["downsample_x"]
            padding = {8: 17, 16: 23, 32: 32}[case["depth"]]
            run = subprocess.run([str(executable), str(case["depth"]), str(base.WIDTH), str(base.HEIGHT), str(case["amount"]),
                "100", str(case["repeat"]), "1", str(case["legacy"]), str(num), str(den), str(padding), str(source), str(expected)],
                capture_output=True, text=True, cwd=ROOT)
            if run.returncode:
                raise RuntimeError(f"{case['id']}: {run.stdout}\n{run.stderr}")
            observed = json.loads(run.stdout)
            assert observed["mismatched_bytes"] == observed["padding_mismatches"] == 0
            results.append({"id": case["id"], "effective_worker_amount": case["effective_worker_amount"],
                            "expected_sha256": case["expected_sha256"], "production": observed})
    REPORT.write_text(json.dumps({"schema": "olmblur.downsample-amount.production/1", "status": "exact",
        "actual_aex_sha256": base.AEX_SHA256, "geometry": [base.WIDTH, base.HEIGHT], "case_count": len(results),
        "matrix": {"depth": [8,16,32], "amount": list(AMOUNTS), "repeat": list(REPEATS), "legacy": [0,1],
                   "downsample_x": [[n,d] for n,d in RATIOS], "smoothness": 100, "bias_direction": 1},
        "contract": "constant 24x24 worlds; production reads PF_InData rational and scales Amount exactly once",
        "path": "actual-AEX typed worker at effective Amount -> production EffectMain SmartPreRender/SmartRender at UI Amount + downsample rational",
        "cases": results, "not_proven": ["native AE preview world sizing", "actual AEX public SmartRender callback chain", "downsample_y anisotropy", "other geometry/bias/smoothness"]}, indent=2, sort_keys=True)+"\n")
    print("PASS_OLMBLUR_DOWNSAMPLE_AMOUNT_MATRIX cases=72 rational_contract=1 raw_exact=72")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    export() if args.export else verify()

#!/usr/bin/env python3
"""Bounded OLMBlur Amount x Repeat x Legacy matrix.

``--export`` executes the six pinned actual-AEX typed workers and retains their
complete 24x24 buffers.  The default mode takes those hash-pinned buffers
through the production Mac EffectMain SmartPreRender -> SmartRender route.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402
from test_olmblur_fullentry import build_context, build_pf_suites  # noqa: E402
import test_olmblur_nondefault_smoothness_effectmain_actual_aex_20260810 as public  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMBlur.aex"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
FIXTURE = Path(__file__).parent / "fixtures/olmblur_amount_repeat_legacy_matrix_20260810"
MANIFEST = FIXTURE / "manifest.json"
REPORT = ROOT / "refs/conformance/olmblur_amount_repeat_legacy_matrix_actual_aex_20260810.json"
WIDTH = HEIGHT = 24
AMOUNTS = (5.0, 129.4)
REPEATS = (1, 2, 10)
ENTRIES = {
    (8, 0): 0x180003710, (8, 1): 0x180007300,
    (16, 0): 0x180002280, (16, 1): 0x180005F20,
    (32, 0): 0x180004B80, (32, 1): 0x1800086D0,
}
PIXEL_BYTES = {8: 4, 16: 8, 32: 16}
FILE_NAMES = {8: "argb8.bin", 16: "argb16.bin", 32: "argb32.bin"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_bytes(depth: int) -> bytes:
    data = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            selector = (x * 5 + y * 3) % 17
            if depth == 8:
                values = (0, 1, 64, 127, 128, 192, 254, 255)
                a = 0 if selector == 0 else values[(x + 3 * y) % len(values)]
                rgba = (a, values[(2*x+y+1)%8], values[(x+5*y+2)%8], values[(7*x+3*y+3)%8])
                data.extend(rgba)
            elif depth == 16:
                values = (0, 1, 8192, 16384, 32767, 32768)
                a = 0 if selector == 0 else values[(x + 3 * y) % len(values)]
                data.extend(struct.pack("<4H", a, values[(2*x+y+1)%6], values[(x+5*y+2)%6], values[(7*x+3*y+3)%6]))
            else:
                values = (-0.5, 0.0, 1.0/255.0, 0.25, 0.5, 1.0, 1.25, 2.0)
                a = 0.0 if selector == 0 else values[(x + 3 * y) % len(values)]
                data.extend(struct.pack("<4f", a, values[(2*x+y+1)%8], values[(x+5*y+2)%8], values[(7*x+3*y+3)%8]))
    return bytes(data)


def alloc(loader: AexLoader, data: bytes) -> int:
    address = loader.bump_alloc(len(data), align=64)
    loader.write_bytes(address, data)
    return address


def run_actual(depth: int, legacy: int, amount: float, repeat: int, source: bytes) -> tuple[bytes, dict]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    loader.register_import_impl("pow", lambda uc, args: (loader.write_xmm_f64(0, math.pow(loader.read_xmm_f64(0), loader.read_xmm_f64(1))) or 0))
    loader.register_import_impl("powf", lambda uc, args: (loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1))) or 0))
    spbasic, events = build_pf_suites(loader)
    context = build_context(loader, spbasic)
    source_data, output_data = alloc(loader, source), alloc(loader, source)

    def world(data: int) -> int:
        address = loader.host_alloc(0x80)
        loader.write_bytes(address, b"\0" * 0x80)
        loader.write_bytes(address + 0x18, struct.pack("<Q", data))
        loader.write_bytes(address + 0x20, struct.pack("<I", WIDTH * PIXEL_BYTES[depth]))
        loader.write_bytes(address + 0x24, struct.pack("<I", WIDTH))
        loader.write_bytes(address + 0x28, struct.pack("<I", HEIGHT))
        loader.write_bytes(address + 0x2C, struct.pack("<H", depth))
        return address

    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\0" * 0x40)
    loader.write_bytes(params + 0x18, struct.pack("<I", depth))
    loader.write_bytes(params + 0x20, struct.pack("<f", amount))
    loader.write_bytes(params + 0x24, struct.pack("<f", 100.0))
    loader.write_bytes(params + 0x28, struct.pack("<I", repeat))
    loader.write_bytes(params + 0x2C, struct.pack("<I", 1))
    loader.write_bytes(params + 0x30, bytes((legacy,)))
    result = loader.call_function(ENTRIES[(depth, legacy)], int_args=[context, world(source_data), world(output_data), params], max_instructions=100_000_000)
    if result["instructions"] >= 100_000_000:
        raise RuntimeError(f"instruction cap: depth={depth} legacy={legacy} amount={amount} repeat={repeat}")
    return loader.read_bytes(output_data, len(source)), {"instructions": result["instructions"], "callback_count": len(events)}


def export() -> None:
    assert sha256(AEX.read_bytes()) == AEX_SHA256
    FIXTURE.mkdir(parents=True, exist_ok=True)
    cases = []
    for depth in (8, 16, 32):
        source = source_bytes(depth)
        source_path = FIXTURE / f"source_{FILE_NAMES[depth]}"
        source_path.write_bytes(source)
        for amount in AMOUNTS:
            for repeat in REPEATS:
                for legacy in (0, 1):
                    expected, run = run_actual(depth, legacy, amount, repeat, source)
                    case_id = f"pf{depth}_amount{str(amount).replace('.', '_')}_repeat{repeat}_legacy{legacy}"
                    expected_path = FIXTURE / f"expected_{case_id}.bin"
                    expected_path.write_bytes(expected)
                    cases.append({"id": case_id, "depth": depth, "amount": amount, "smoothness": 100.0,
                                  "repeat": repeat, "bias_direction": 1, "legacy": legacy,
                                  "source": source_path.name, "source_sha256": sha256(source),
                                  "expected": expected_path.name, "expected_sha256": sha256(expected), **run})
                    print(f"AEX {case_id} instructions={run['instructions']}", flush=True)
    MANIFEST.write_text(json.dumps({"schema": "olmblur.amount-repeat-legacy-matrix.actual-aex/1",
        "plugin": "OLMBlur", "actual_aex_sha256": AEX_SHA256, "geometry": [WIDTH, HEIGHT],
        "pixel_layout": "typed little-endian ARGB", "cases": cases}, indent=2, sort_keys=True) + "\n")


def public_probe_source() -> str:
    source = public.probe_source()
    replacements = {
        "if (argc != 11) return 2;": "if (argc != 12) return 2;",
        "const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), padding = std::atoi(argv[8]);":
            "const int repeat = std::atoi(argv[6]), bias = std::atoi(argv[7]), legacy = std::atoi(argv[8]), padding = std::atoi(argv[9]);",
        "const auto source = read_file(argv[9]), expected = read_file(argv[10]);":
            "const auto source = read_file(argv[10]), expected = read_file(argv[11]);",
        "g_params[3].u.sd.value = repeat; g_params[4].u.pd.value = bias; g_params[5].u.bd.value = 1;":
            "g_params[3].u.sd.value = repeat; g_params[4].u.pd.value = bias; g_params[5].u.bd.value = legacy;",
    }
    for old, new in replacements.items():
        if old not in source:
            raise RuntimeError(f"public probe shape drift: {old}")
        source = source.replace(old, new)
    return source


def compile_public(directory: Path) -> Path:
    source = directory / "probe.cpp"
    source.write_text(public_probe_source().replace("__OLMBLUR_MAC_SOURCE__", str(ROOT / "mac/OLMBlur/OLMBlur.cpp").replace("\\", "\\\\").replace('"', '\\"')))
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
    assert sha256(AEX.read_bytes()) == AEX_SHA256
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["actual_aex_sha256"] == AEX_SHA256 and len(manifest["cases"]) == 36
    results = []
    with tempfile.TemporaryDirectory(prefix="olmblur_combo_") as name:
        executable = compile_public(Path(name))
        for case in manifest["cases"]:
            source, expected = FIXTURE/case["source"], FIXTURE/case["expected"]
            assert sha256(source.read_bytes()) == case["source_sha256"]
            assert sha256(expected.read_bytes()) == case["expected_sha256"]
            padding = {8: 17, 16: 23, 32: 32}[case["depth"]]
            run = subprocess.run([str(executable), str(case["depth"]), str(WIDTH), str(HEIGHT), str(case["amount"]),
                "100", str(case["repeat"]), "1", str(case["legacy"]), str(padding), str(source), str(expected)],
                capture_output=True, text=True, cwd=ROOT)
            if run.returncode:
                raise RuntimeError(f"{case['id']}: {run.stdout}\n{run.stderr}")
            observed = json.loads(run.stdout)
            assert observed["mismatched_bytes"] == observed["padding_mismatches"] == 0
            results.append({"id": case["id"], "expected_sha256": case["expected_sha256"], "production": observed})
    REPORT.write_text(json.dumps({"schema": "olmblur.amount-repeat-legacy-matrix.production/1", "status": "exact",
        "actual_aex_sha256": AEX_SHA256, "geometry": [WIDTH, HEIGHT], "case_count": len(results),
        "matrix": {"depth": [8,16,32], "amount": list(AMOUNTS), "repeat": list(REPEATS), "legacy": [0,1],
                   "smoothness": 100, "bias_direction": 1},
        "path": "retained actual-AEX typed worker -> production Mac EffectMain SmartPreRender/SmartRender",
        "cases": results, "not_proven": ["actual Windows AEX public SmartRender callback chain", "native AE render at these 36 cells", "other geometry/bias/smoothness/downsample"]}, indent=2, sort_keys=True)+"\n")
    print("PASS_OLMBLUR_AMOUNT_REPEAT_LEGACY_MATRIX cases=36 raw_exact=36 public_smart_chain=36")


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--export", action="store_true")
    parsed = args.parse_args()
    export() if parsed.export else verify()

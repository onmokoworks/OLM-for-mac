#!/usr/bin/env python3
"""Compare production ColorKeep callbacks with actual-AEX padded-frame oracles."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
REPORT = ROOT / "refs/conformance/colorkeep_typed_padded_frame_actual_aex_20260805.json"
WIDTH, HEIGHT, PADDING = 4, 3, 8
COLORS = ((1.0, 0.0, 0.25, 0.5), (0.75, 0.25, 0.5, 0.75), (0.5, 0.5, 0.75, 1.0), (0.25, 0.75, 1.0, 0.0), (1.0, 1.0, 0.0, 0.25))
DEPTHS = {
    "PF8": (0x180001580, "<4B", ((255, 0, 64, 128), (64, 191, 255, 0), (255, 255, 0, 64), (255, 254, 0, 64))),
    "PF16": (0x180001280, "<4H", ((32768, 0, 8192, 16384), (8192, 24576, 32768, 0), (32768, 32768, 0, 8192), (32768, 32767, 0, 8192))),
    "PF32": (0x180001850, "<4f", (COLORS[0], COLORS[3], COLORS[4], (0.55, 0.91, 0.81, 0.71))),
}


def actual_frame(entry: int, fmt: str, pixels: tuple[tuple[float | int, ...], ...]) -> bytes:
    pixel_size = struct.calcsize(fmt)
    rowbytes = WIDTH * pixel_size + PADDING
    output = bytearray([0xEE] * (rowbytes * HEIGHT))
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    refcon = loader.host_alloc(0x28 + len(COLORS) * 16)
    src, dst = loader.host_alloc(pixel_size), loader.host_alloc(pixel_size)
    loader.write_bytes(refcon + 0x24, struct.pack("<i", len(COLORS)))
    for index, color in enumerate(COLORS):
        loader.write_bytes(refcon + 0x28 + index * 16, struct.pack("<4f", *color))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            value = pixels[(y * WIDTH + x) % len(pixels)]
            loader.write_bytes(src, struct.pack(fmt, *value))
            loader.write_bytes(dst, b"\xa5" * pixel_size)
            loader.call_function(entry, int_args=[refcon, x, y, src, dst], max_instructions=10_000)
            start = y * rowbytes + x * pixel_size
            output[start:start + pixel_size] = loader.read_bytes(dst, pixel_size)
    return bytes(output)


def byte_array(name: str, data: bytes) -> str:
    return f"static const unsigned char {name}[] = {{{','.join(str(v) for v in data)}}};"


def production_frames() -> bytes:
    input_blobs = {}
    for depth, (_, fmt, pixels) in DEPTHS.items():
        rows = []
        for y in range(HEIGHT):
            rows.append(b"".join(struct.pack(fmt, *pixels[(y * WIDTH + x) % len(pixels)]) for x in range(WIDTH)) + b"\xcc" * PADDING)
        input_blobs[depth] = b"".join(rows)
    colors = struct.pack("<20f", *(v for color in COLORS for v in color))
    source = "\n".join([
        "#include <cstdio>", "#include <cstring>", '#include "mac/ColorKeep/ColorKeep.cpp"',
        byte_array("colors", colors), byte_array("input8", input_blobs["PF8"]),
        byte_array("input16", input_blobs["PF16"]), byte_array("input32", input_blobs["PF32"]),
        "template<class P, PF_Err (*F)(void*,A_long,A_long,P*,P*)> void run(const unsigned char* raw){",
        "ColorKeepInfo info; std::memset(&info,0,sizeof(info)); info.count=5; std::memcpy(info.colors,colors,sizeof(colors));",
        "const int rb=4*sizeof(P)+8; unsigned char out[3*(4*sizeof(P)+8)]; std::memset(out,0xEE,sizeof(out));",
        "for(int y=0;y<3;y++)for(int x=0;x<4;x++){P in; std::memcpy(&in,raw+y*rb+x*sizeof(P),sizeof(P)); F(&info,x,y,&in,reinterpret_cast<P*>(out+y*rb+x*sizeof(P)));}",
        "std::fwrite(out,1,sizeof(out),stdout);}",
        "int main(){run<PF_Pixel8,ColorKeep8Func>(input8);run<PF_Pixel16,ColorKeep16Func>(input16);run<PF_PixelFloat,ColorKeepFloatFunc>(input32);return 0;}",
    ])
    with tempfile.TemporaryDirectory(prefix="colorkeep_frame_") as raw:
        directory = Path(raw)
        cpp, exe = directory / "probe.cpp", directory / "probe"
        cpp.write_text(source, encoding="utf-8")
        command = ["xcrun", "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off", "-D__MACH__", "-Wno-pragma-pack", "-I.", "-IHeaders", "-IHeaders/SP", "-IUtil", "-IResources", str(cpp), "mac/ColorKeep/ColorKeep_Strings.cpp", "Util/AEGP_SuiteHandler.cpp", "Util/MissingSuiteError.cpp", "-framework", "Cocoa", "-o", str(exe)]
        build = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
        assert build.returncode == 0, build.stderr.decode(errors="replace")
        run = subprocess.run([str(exe)], cwd=ROOT, capture_output=True, check=False)
        assert run.returncode == 0, run.stderr.decode(errors="replace")
        return run.stdout


def main() -> int:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    expected_parts, depth_reports = [], {}
    for depth, (entry, fmt, pixels) in DEPTHS.items():
        frame = actual_frame(entry, fmt, pixels)
        expected_parts.append(frame)
        ps, rb = struct.calcsize(fmt), WIDTH * struct.calcsize(fmt) + PADDING
        assert all(frame[y * rb + WIDTH * ps:(y + 1) * rb] == b"\xee" * PADDING for y in range(HEIGHT))
        depth_reports[depth] = {"entry": f"0x{entry:x}", "width": WIDTH, "height": HEIGHT, "rowbytes": rb, "padding_bytes": PADDING, "oracle_sha256": hashlib.sha256(frame).hexdigest(), "pixels": WIDTH * HEIGHT}
    expected = b"".join(expected_parts)
    observed = production_frames()
    assert observed == expected
    report = {"status": "exact", "aex_sha256": AEX_SHA256, "production_source": "mac/ColorKeep/ColorKeep.cpp", "dispatch_evidence": "tests/test_colorkeep_windows_callback_contract_20260731.py binds EffectMain legacy/smart commands to the typed callbacks", "depths": depth_reports, "combined_output_sha256": hashlib.sha256(observed).hexdigest(), "scope": "PF8/PF16/PF32, 4x3, five enabled colors, match/unrolled/tail/no-match pattern, 8-byte row padding", "not_proven": ["After Effects host execution/export", "frames or parameters outside this fixed fixture"]}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

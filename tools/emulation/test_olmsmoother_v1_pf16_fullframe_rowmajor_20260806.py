#!/usr/bin/env python3
"""Compare deterministic PF16 row-major production output with Windows AE."""
import ctypes
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXR_TOOLS = ROOT / "refs/runtime_trace_support/olm_windows_32bpc_typed_procedural_fixture_20260713/fixture"
sys.path.insert(0, str(EXR_TOOLS))
from compare_float_exr import read_planes

ARCHIVE = ROOT / "refs/returns/windows/RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip"
ROW = "outputs\\olmsmoother_v1__canonical_3__case_0001__16bpc\\"
HARNESS = ROOT / "tools/emulation/olmsmoother_v1_pf16_control_harness_20260806.cpp"
MAC_EFFECT = ROOT / "tmp/olmsmoother_v1_pf16_boundary_endpoint_20260806/mac/olmsmoother_v1__canonical_3__case_0001__16bpc/effect_on_00024.exr"


def pf16_words(path: Path, decode_export_rgb=False):
    planes, width, height = read_planes(path)
    decoded = {name: struct.unpack("<%df" % (width * height), data)
               for name, data in planes.items()}
    words = []
    for index in range(width * height):
        for name in ("A", "R", "G", "B"):
            value = decoded[name][index]
            if decode_export_rgb and name != "A" and value > 0.0:
                value = value ** (1.0 / 2.4)
            scaled = value * 32768.0
            word = round(scaled)
            assert abs(scaled - word) < 0.1 and 0 <= word <= 32768, (name, index, scaled)
            words.append(word)
    return words, width, height


def main():
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        with zipfile.ZipFile(ARCHIVE) as archive:
            off = directory / "no_effect.exr"
            on = directory / "effect_on.exr"
            off.write_bytes(archive.read(ROW + "no_effect.exr"))
            on.write_bytes(archive.read(ROW + "effect_on.exr"))
        source, width, height = pf16_words(off)
        expected, target_width, target_height = pf16_words(MAC_EFFECT)
        assert (width, height) == (target_width, target_height) == (960, 540)

        library = directory / "pf16_rowmajor.dylib"
        subprocess.run(["clang++", "-std=c++17", "-O2", "-fPIC", "-shared",
                        "-I" + str(ROOT / "cli/OLMSmoother/shim"), str(HARNESS),
                        "-o", str(library)], check=True, capture_output=True)
        port = ctypes.CDLL(str(library))
        src = (ctypes.c_uint16 * len(source))(*source)
        dst = (ctypes.c_uint16 * len(source))(*source)
        port.olmsmoother_render16_rowmajor(src, dst, width, height, 6)
        got = list(dst)
        differences = [(i // 4 % width, i // 4 // width, i % 4, expected[i], got[i])
                       for i in range(len(got)) if got[i] != expected[i]]
        # AE's IterateSuite order is not row-major: only the two overlapping
        # edge tails differ.  Keep this as a bounded diagnostic; production
        # must retain host iteration rather than impose this order.
        assert len(differences) == 30, differences[:50]
        assert {(x, y) for x, y, _c, _e, _g in differences} == (
            {(x, 440) for x in range(945, 960)} |
            {(860, y) for y in range(525, 540)})
        print("PASS PF16 960x540 row-major diagnostic: AE host-order boundary=30 R words")


if __name__ == "__main__":
    main()

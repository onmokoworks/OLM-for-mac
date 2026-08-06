#!/usr/bin/env python3
"""Prove the bounded PF16 Outside/RGB/no-bg interpolation x invert family."""

import hashlib
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "tools/emulation"
sys.path.insert(0, str(HERE))

from export_dg_fieldgen_fixture import run_aex_fieldgen
from test_dg_compose import (
    OFF_BG_B, OFF_BG_G, OFF_BG_R, OFF_DEGENERATE, OFF_FIELD_WORLD_PTR,
    OFF_GRAD_B, OFF_GRAD_G, OFF_GRAD_R, OFF_INOUT_MODE, OFF_INTERP_MODE,
    OFF_INVERT, OFF_POWER, OFF_RENDER_MODE, OFF_SRC_WORLD_PTR, OFF_USE_BG,
    alloc_refcon, build_world, call_compose, make_loader,
)

HARNESS = HERE / "dg_classic_pf16_outside_interp_family_nobg_harness_20260806.cpp"
WIDTH, HEIGHT = 17, 11
INPUT_ROWBYTES, OUTPUT_ROWBYTES = 146, 150
INTERPOLATIONS = (("constant", 1, 1.0), ("linear", 2, 1.0),
                  ("sphere", 3, 1.0), ("power", 4, 2.5))
EXPECTED_ACTIVE_SHA256 = {
    "constant.invert_0": "5030551e163c16bec51f84ffbafd29c1544da95a6999916268189560b0ef4689",
    "constant.invert_1": "070af26f37cd39052ab7a47ee18ea9c3ca0238d68afcd7c09a03460ed8f42973",
    "linear.invert_0": "c1c1f7b88fe7f49642815e62649254152a361f00d2a26bd453a809aaedc61850",
    "linear.invert_1": "c1424a239fbc3814ac63d6b87119c54f46239742fb2b648b5f2fccad1dd5a0fd",
    "sphere.invert_0": "ea19a4fda3714aa90158eaf22465af7a7d584e512e9787e0e7b760ebcbfdf3e7",
    "sphere.invert_1": "fa99bf9d4284a748f6ad3549a56581d40f8f38332857c54bc7fdb91e0166c989",
    "power.invert_0": "527250c88eca3ee69a43c4f097c0e3953839f5c2bdd986be9e554c33cb315f26",
    "power.invert_1": "864950cf175ed9a124a00f9ca2d23fbdb98a7807e0b1489bd203901f391c71df",
}


def main() -> int:
    # A thick transparent island reaches distances 1..4, so all four
    # interpolation transforms are independently observable after PF16 staging.
    mask = np.ones((HEIGHT, WIDTH), dtype=np.uint8)
    mask[2:9, 4:13] = 0
    fields = {}
    field_shas = {}
    for param8 in (0, 1):
        field, trace = run_aex_fieldgen((mask == 0).astype(np.uint8), 4, param8)
        fields[param8] = field
        field_shas[param8] = hashlib.sha256(field.astype("<f4").tobytes()).hexdigest()
        assert trace["hits"]
    assert field_shas == {
        0: "b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112",
        1: "13a74e7dc8897b6489f66b39e0e4505a4e46a943f3635b5b0c68bbe571b682cf",
    }

    source_pixels = {}
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if mask[y, x]:
                source_pixels[x, y] = (
                    32768, (x * 997 + y * 211) % 32769,
                    (x * 613 + y * 1231) % 32769,
                    (x * 1499 + y * 307) % 32769,
                )

    loader = make_loader()
    loader.register_libm_impls(max_threads=1)
    source_world = build_world(loader, WIDTH, HEIGHT, source_pixels)
    field_worlds = {}
    for param8, field in fields.items():
        field_words = np.rint(np.clip(field, 0, 1) * 32768).astype("<u2")
        field_pixels = {(x, y): (0, int(field_words[y, x]), 0, 0)
                        for y in range(HEIGHT) for x in range(WIDTH)}
        field_worlds[param8] = build_world(loader, WIDTH, HEIGHT, field_pixels)
    refcon = alloc_refcon(loader)

    def put(offset: int, fmt: str, value) -> None:
        loader.write_bytes(refcon + offset, struct.pack(fmt, value))

    fixed = (
        (OFF_SRC_WORLD_PTR, "<Q", source_world),
        (OFF_DEGENERATE, "<B", 0), (OFF_USE_BG, "<B", 0),
        (OFF_INOUT_MODE, "<i", 2), (OFF_RENDER_MODE, "<i", 1),
        (OFF_GRAD_G, "<f", 0.0), (OFF_GRAD_R, "<f", 28 / 255),
        (OFF_GRAD_B, "<f", 238 / 255), (OFF_BG_G, "<f", 0.0),
        (OFF_BG_R, "<f", 1.0), (OFF_BG_B, "<f", 0.0),
    )
    for entry in fixed:
        put(*entry)

    source_active = b"".join(
        struct.pack("<4H", a, r, g, b)
        for a, g, r, b in (source_pixels.get((x, y), (0, 0, 0, 0))
                           for y in range(HEIGHT) for x in range(WIDTH))
    )
    source_padded = b"".join(
        source_active[y * WIDTH * 8:(y + 1) * WIDTH * 8] + b"\xa5" * (INPUT_ROWBYTES - WIDTH * 8)
        for y in range(HEIGHT)
    )

    observed = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        source_path, expected_path, executable = temp / "source", temp / "expected", temp / "harness"
        source_path.write_bytes(source_padded)
        build = subprocess.run([
            "clang++", "-std=c++17", "-O0", "-I", str(HERE / "dg_renderbits_real_harness_20260716"),
            str(HARNESS), str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(executable),
        ], capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        for name, mode, power in INTERPOLATIONS:
            for invert in (False, True):
                put(OFF_FIELD_WORLD_PTR, "<Q", field_worlds[1 if name == "constant" else 0])
                put(OFF_INVERT, "<B", int(invert))
                put(OFF_INTERP_MODE, "<i", mode)
                put(OFF_POWER, "<f", power)
                actual_words = [call_compose(loader, refcon, x, y)
                                for y in range(HEIGHT) for x in range(WIDTH)]
                active = b"".join(struct.pack("<4H", a, r, g, b) for a, g, r, b in actual_words)
                key = f"{name}.invert_{int(invert)}"
                observed[key] = hashlib.sha256(active).hexdigest()
                expected = b"".join(
                    active[y * WIDTH * 8:(y + 1) * WIDTH * 8] + b"\xa5" * (OUTPUT_ROWBYTES - WIDTH * 8)
                    for y in range(HEIGHT)
                )
                expected_path.write_bytes(expected)
                run = subprocess.run([
                    str(executable), str(source_path), str(expected_path), name,
                    "invert" if invert else "normal",
                ], capture_output=True, text=True)
                assert run.returncode == 0, run.stderr
                print(run.stdout, end="")
    assert observed == EXPECTED_ACTIVE_SHA256
    assert len(set(observed.values())) == len(observed), "family must contain eight output discriminators"
    print("field_sha256", field_shas)
    print("PASS_OLMDISTANCEGRADATION_CLASSIC_PF16_OUTSIDE_INTERP_FAMILY_NOBG_EXACT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

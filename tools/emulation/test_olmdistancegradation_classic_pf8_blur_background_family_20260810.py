#!/usr/bin/env python3
"""Actual-AEX PF8 Inside/RGB interpolation x blur x background family."""
import hashlib, json, struct, subprocess, sys, tempfile
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
    alloc_refcon, make_loader,
)
from test_olmdistancegradation_classic_pf8_blur_modes45_family_20260810 import (
    AEX, AEX_SHA256, H, INPUT_ROWBYTES, OUTPUT_ROWBYTES, W, actual_blur, world8,
)

COMPOSE8 = 0x181170870
HARNESS = HERE / "dg_classic_pf8_blur_modes45_family_harness_20260810.cpp"
REPORT = ROOT / "refs/conformance/olmdistancegradation_classic_pf8_blur_background_family_exact_20260810.json"
DOC = ROOT / "refs/conformance/olmdistancegradation_classic_pf8_blur_background_family_exact_20260810.md"


def main():
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    mask = np.ones((H, W), np.uint8)
    mask[2:9, 4:13] = 0
    source_pixels = [
        (255, (x * 997 + y * 211) % 256, (x * 613 + y * 1231) % 256,
         (x * 1499 + y * 307) % 256) if mask[y, x] else (0, 0, 0, 0)
        for y in range(H) for x in range(W)
    ]
    source_active = b"".join(bytes((a, r, g, b)) for a, g, r, b in source_pixels)
    source_padded = b"".join(
        source_active[y * W * 4:(y + 1) * W * 4] + b"\xa5" * (INPUT_ROWBYTES - W * 4)
        for y in range(H)
    )
    loader = make_loader()
    loader.register_libm_impls(max_threads=1)
    source_world = world8(loader, b"".join(bytes(pixel) for pixel in source_pixels))
    refcon = alloc_refcon(loader)

    def put(offset, fmt, value):
        loader.write_bytes(refcon + offset, struct.pack(fmt, value))

    for item in (
        (OFF_SRC_WORLD_PTR, "<Q", source_world), (OFF_DEGENERATE, "<B", 0),
        (OFF_INVERT, "<B", 1), (OFF_INOUT_MODE, "<i", 1),
        (OFF_RENDER_MODE, "<i", 1), (OFF_POWER, "<f", 1.0),
        (OFF_GRAD_G, "<f", 0.0), (OFF_GRAD_R, "<f", 28 / 255),
        (OFF_GRAD_B, "<f", 238 / 255), (OFF_BG_G, "<f", 160 / 255),
        (OFF_BG_R, "<f", 16 / 255), (OFF_BG_B, "<f", 48 / 255),
    ):
        put(*item)

    rows = []
    surfaces = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        source_path, expected_path, executable = temp / "source", temp / "expected", temp / "harness"
        source_path.write_bytes(source_padded)
        build = subprocess.run([
            "clang++", "-std=c++17", "-O0", "-I", str(HERE / "dg_renderbits_real_harness_20260716"),
            str(HARNESS), str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(executable),
        ], capture_output=True, text=True)
        assert build.returncode == 0, build.stderr

        for interp_name, interp_mode, constant in (("constant", 1, True), ("linear", 2, False)):
            field, field_trace = run_aex_fieldgen(mask, 4, 1 if constant else 0)
            preblur = (field >= 1.0).astype(np.float32) if constant else field
            for blur_mode in (2, 3):
                blurred, instructions = actual_blur(preblur, blur_mode)
                staged = np.rint(np.clip(blurred, 0, 1) * 255).astype(np.uint8)
                surface_key = f"{interp_name}.mode{blur_mode}"
                surfaces[surface_key] = {
                    "field_sha256": hashlib.sha256(field.astype("<f4").tobytes()).hexdigest(),
                    "preblur_sha256": hashlib.sha256(preblur.astype("<f4").tobytes()).hexdigest(),
                    "blurred_sha256": hashlib.sha256(blurred.tobytes()).hexdigest(),
                    "staged_u8_sha256": hashlib.sha256(staged.tobytes()).hexdigest(),
                    "blur_instructions": instructions,
                }
                field_world = world8(loader, b"".join(
                    bytes((0, int(staged[y, x]),
                           int(staged[y, x]) if interp_name == "linear" else 0, 0))
                    for y in range(H) for x in range(W)
                ))
                put(OFF_FIELD_WORLD_PTR, "<Q", field_world)
                put(OFF_INTERP_MODE, "<i", interp_mode)
                for background in (0, 1):
                    put(OFF_USE_BG, "<B", background)
                    output = []
                    for y in range(H):
                        for x in range(W):
                            pixel = loader.bump_alloc(4, align=8)
                            loader.write_bytes(pixel, b"\xee" * 4)
                            loader.call_function(COMPOSE8, int_args=[refcon, x, y, 0, pixel],
                                                 max_instructions=200_000)
                            raw = loader.read_bytes(pixel, 4)
                            output.append(bytes((raw[0], raw[2], raw[1], raw[3])))
                    active = b"".join(output)
                    expected = b"".join(
                        active[y * W * 4:(y + 1) * W * 4] + b"\xa5" * (OUTPUT_ROWBYTES - W * 4)
                        for y in range(H)
                    )
                    expected_path.write_bytes(expected)
                    run = subprocess.run([
                        str(executable), str(source_path), str(expected_path), interp_name,
                        str(background), str(blur_mode),
                    ], capture_output=True, text=True)
                    assert run.returncode == 0, run.stderr
                    print(run.stdout, end="")
                    rows.append({
                        "interpolation": interp_name, "blur_mode": blur_mode,
                        "use_background": bool(background),
                        "output_active_sha256": hashlib.sha256(active).hexdigest(),
                        "output_padded_sha256": hashlib.sha256(expected).hexdigest(),
                        "bytes_compared": len(expected), "mismatches": 0,
                        "fieldgen_trace_events": len(field_trace),
                    })

    assert len(rows) == 8
    assert len({row["output_active_sha256"] for row in rows}) == 8
    assert len({value["blurred_sha256"] for value in surfaces.values()}) == 4
    report = {
        "schema": "olmdistancegradation.classic-pf8-blur-background-family/1",
        "status": "exact",
        "aex_sha256": AEX_SHA256,
        "scope": "PF8 17x11 padded actual numerical chain FUN_181174760 -> FUN_1812864d0 -> FUN_181170870; Inside/RGB, invert on, threshold4, blur size1, full resolution; Constant/Linear x Background off/on x mode2/3",
        "surfaces": surfaces,
        "rows": rows,
        "distinctness": "four blurred surfaces and eight final active outputs are pairwise distinct",
        "claims_not_made": ["public classic wrapper and host resize/staging", "Blur Modes 4/5 (separate evidence)", "other sizes/geometries/ownership/render branches", "PF16/PF32", "PF32 SmartRender", "AE host execution"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMDistanceGradation PF8 blur × background family\n\n"
        "Status: **exact** for the declared bounded numerical chain.\n\n"
        "A padded 17x11 transparent-island fixture crosses Constant/Linear, Background "
        "off/on, and Blur Mode 2 box/3 Gaussian. The hash-pinned actual Windows AEX "
        "executes `FUN_181174760`, `FUN_1812864d0`, and all 187 PF8 `FUN_181170870` "
        "callbacks per cell. Production matches all 869 bytes in each of eight cells, "
        "including eleven padding bytes per row. Four blurred surfaces and all eight final "
        "active outputs are pairwise distinct.\n\n"
        "The public classic wrapper and host resize/staging remain separate. Blur Modes 4/5 "
        "are covered by their own focused evidence. Other depths, sizes, ownership/render "
        "branches, PF32 SmartRender, and AE-host execution are not claimed.\n"
    )
    print("PASS_OLMDISTANCEGRADATION_CLASSIC_PF8_BLUR_BACKGROUND_FAMILY_EXACT")


if __name__ == "__main__":
    raise SystemExit(main())

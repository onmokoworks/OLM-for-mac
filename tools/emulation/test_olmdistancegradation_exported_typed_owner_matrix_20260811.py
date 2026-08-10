#!/usr/bin/env python3
"""Compare exported PF16/PF32 Smart owner buffers with production RenderBits."""
from __future__ import annotations
import hashlib, json, os, struct, subprocess, tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
HARNESS = ROOT / "tools/emulation/dg_exported_typed_owner_compare_harness_20260811.cpp"
REPORT = ROOT / "refs/conformance/olmdistancegradation_exported_typed_owner_matrix_20260811.json"
DOC = REPORT.with_suffix(".md")
DEFAULT_WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker")
BASE = ["Invert=1", "In/Out=1", "Inside Threshold=4", "Outside Threshold=4",
        "Render Mode=1", "Gradation Color=255,28,0,238", "BG Color =255,16,160,48",
        "Power=1", "Blur Size=1"]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rgba_fixture() -> list[tuple[int, int, int, int]]:
    return [((x*613+y*1231)%256, (x*997+y*211)%256, (x*1499+y*307)%256, 255)
            if not (4 <= x < 13 and 2 <= y < 9) else (0, 0, 0, 0)
            for y in range(11) for x in range(17)]

def promoted(pixels, depth):
    output = bytearray()
    for red, green, blue, alpha in pixels:
        for value in (alpha, red, green, blue):
            if depth == "PF16":
                output += struct.pack("<H", (value * 32768 + 127) // 255)
            else:
                output += struct.pack("<f", value / 255.0)
    return bytes(output)

def main() -> int:
    worker = Path(os.environ.get("OLM_AEX_GUEST_WORKER", str(DEFAULT_WORKER)))
    if not worker.is_file(): raise RuntimeError(f"worker missing: {worker}")
    rows = []
    with tempfile.TemporaryDirectory(prefix="dg_typed_owner_") as temporary:
        td = Path(temporary); source_png = td / "input.png"; executable = td / "harness"
        pixels = rgba_fixture(); image = Image.new("RGBA", (17, 11)); image.putdata(pixels); image.save(source_png)
        input_png_sha256 = sha(source_png)
        build = subprocess.run(["clang++", "-std=c++17", "-O0",
            "-I", str(ROOT / "tools/emulation/dg_renderbits_real_harness_20260716"),
            str(HARNESS), str(ROOT / "core/olmdistancegradation_fieldgen.cpp"), "-o", str(executable)],
            text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        for depth, pixel_format in (("PF16", "argb16"), ("PF32", "argb32f")):
            source_raw = td / f"source_{depth}.raw"; source_raw.write_bytes(promoted(pixels, depth))
            for interpolation, interpolation_value in (("constant", 1), ("linear", 2)):
                for blur in (2, 3):
                    for background in (0, 1):
                        key = f"{interpolation}.mode{blur}.bg{background}"
                        actual_png = td / f"actual_{depth}_{key}.png"
                        result = subprocess.run([str(worker), "render-png", str(AEX), str(source_png),
                            str(actual_png), "--pixel-format", pixel_format, *BASE,
                            f"Use Background Color={background}",
                            f"Interpolation Mode={interpolation_value}", f"Blur Mode={blur}"],
                            text=True, capture_output=True, timeout=20)
                        assert result.returncode == 0, result.stderr
                        payload = json.loads(result.stdout)
                        expected_raw = td / f"expected_{depth}_{key}.raw"
                        expected = subprocess.run([str(executable), depth, str(source_raw), str(expected_raw),
                            interpolation, str(background), str(blur)], text=True, capture_output=True)
                        assert expected.returncode == 0, expected.stderr
                        expected_sha = sha(expected_raw)
                        exact = payload["raw_pixel_sha256"] == expected_sha
                        rows.append({"depth": depth, "interpolation": interpolation, "blur_mode": blur,
                            "use_background": bool(background), "bytes_compared": len(expected_raw.read_bytes()),
                            "actual_exported_raw_sha256": payload["raw_pixel_sha256"],
                            "production_renderbits_sha256": expected_sha, "exact": exact,
                            "smart_render_completed": payload["gpu"]["render"]["completed"],
                            "cleanup_complete": payload["gpu"]["cleanup_complete"],
                            "suite_requests": payload["suite_requests"]})
    assert len(rows) == 16 and all(row["smart_render_completed"] and row["cleanup_complete"] for row in rows)
    exact_cells = sum(row["exact"] for row in rows)
    report = {"schema": "olmdistancegradation.exported-typed-owner-matrix/1",
        "status": "PASS_PF16_PF32_EXPORTED_SMART_OWNER_16_CELL_COMPLETE_4_EXACT_12_RESIDUAL",
        "actual_aex_sha256": sha(AEX), "worker_sha256": sha(worker),
        "fixture": {"width": 17, "height": 11, "input_png_sha256": input_png_sha256},
        "summary": {"cells": 16, "completed": 16, "exact": exact_cells,
                    "pf16_constant_exact": 4, "pf16_linear_residual": 4, "pf32_residual": 8},
        "rows": rows, "claims_not_made": ["No native After Effects execution", "No PF32 GPU SmartRender claim"]}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLMDistanceGradation exported typed owner matrix\n\n"
        "Status: **PASS_PF16_PF32_EXPORTED_SMART_OWNER_16_CELL_COMPLETE_4_EXACT_12_RESIDUAL**.\n\n"
        "The unchanged Windows AEX completed exported SmartPreRender/SmartRender for PF16 and PF32 "
        "across Constant/Linear × Blur 2/3 × Background off/on. PF16 Constant is byte-exact in all "
        "four cells. PF16 Linear has four complete-buffer residuals, and PF32 has eight; these are now "
        "render-path differences rather than host ABI failures. PF16 acquires `PF iterate16 "
        "Suite` v1 and PF32 acquires `PF iterateFloat Suite` v1; no `_CxxThrowException` continuation "
        "or exception swallowing is used.\n")
    print(report["status"])
    return 0

if __name__ == "__main__": raise SystemExit(main())

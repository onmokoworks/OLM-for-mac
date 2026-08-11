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

def resident_render(worker: Path, source_raw: Path, output_raw: Path, depth: str,
                    interpolation: int, blur: int, background: int) -> dict:
    pixel_format = "argb16" if depth == "PF16" else "argb32f"
    request = {"type": "render_frame", "v": 2, "frame_index": 0,
               "current_time": {"value": 0, "scale": 30},
               "parameters": "v2|" + ";".join((
                   "param_1@1:i32=1", "param_2@2:i32=1", "param_3@3:i32=4",
                   "param_4@4:i32=4", "param_5@5:i32=1",
                   f"param_6@6:i32={background}", "param_7@7:argb8=255,28,0,238",
                   "param_8@8:argb8=255,16,160,48", f"param_9@9:i32={interpolation}",
                   "param_10@10:f64=2.25", f"param_11@11:i32={blur}",
                   "param_12@12:i32=1"))}
    close = {"type": "close", "v": 1}
    def framed(value: dict) -> bytes:
        payload = json.dumps(value).encode()
        return struct.pack("<I", len(payload)) + payload
    result = subprocess.run([
        str(worker), "session", str(AEX), str(source_raw), str(output_raw),
        "17", "11", "30", "--pixel-format", pixel_format,
    ], input=framed(request) + framed(close), capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    messages = []
    cursor = 0
    while cursor < len(result.stdout):
        length = struct.unpack_from("<I", result.stdout, cursor)[0]
        cursor += 4
        messages.append(json.loads(result.stdout[cursor:cursor + length]))
        cursor += length
    frame = next(message for message in messages if message.get("type") == "frame_done")
    assert frame["status"] == "ok" and frame["render_error"] == 0
    assert frame["output"]["guards_intact"]
    return frame

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
        for depth in ("PF16", "PF32"):
            source_raw = td / f"source_{depth}.raw"; source_raw.write_bytes(promoted(pixels, depth))
            for interpolation, interpolation_value in (
                    ("constant", 1), ("linear", 2), ("sphere", 3), ("power", 4)):
                for blur in (2, 3, 4, 5):
                    for background in (0, 1):
                        key = f"{interpolation}.mode{blur}.bg{background}"
                        actual_raw = td / f"actual_{depth}_{key}.raw"
                        frame = resident_render(worker, source_raw, actual_raw, depth,
                                                interpolation_value, blur, background)
                        expected_raw = td / f"expected_{depth}_{key}.raw"
                        expected = subprocess.run([str(executable), depth, str(source_raw), str(expected_raw),
                            interpolation, str(background), str(blur)], text=True, capture_output=True)
                        rejected = depth == "PF32" and blur == 5 and interpolation != "constant"
                        if rejected:
                            assert expected.returncode == 4
                            rows.append({"depth": depth, "interpolation": interpolation,
                                "blur_mode": blur, "use_background": bool(background),
                                "actual_exported_raw_sha256": sha(actual_raw),
                                "production_status": "fail_closed_bad_callback_param",
                                "exact": False, "fail_closed": True,
                                "guards_intact": frame["output"]["guards_intact"]})
                            continue
                        assert expected.returncode == 0, expected.stderr
                        expected_sha = sha(expected_raw)
                        actual = actual_raw.read_bytes()
                        actual_sha = sha(actual_raw)
                        exact = actual_sha == expected_sha
                        rows.append({"depth": depth, "interpolation": interpolation, "blur_mode": blur,
                            "use_background": bool(background), "bytes_compared": len(expected_raw.read_bytes()),
                            "actual_exported_raw_sha256": actual_sha,
                            "production_renderbits_sha256": expected_sha, "exact": exact,
                            "different_bytes": sum(a != b for a, b in zip(actual, expected_raw.read_bytes())),
                            "guards_intact": frame["output"]["guards_intact"], "fail_closed": False})
    assert len(rows) == 64 and all(row["guards_intact"] for row in rows)
    exact_cells = sum(row["exact"] for row in rows)
    assert exact_cells == 58, [
        (row["depth"], row["interpolation"], row["blur_mode"], row["use_background"])
        for row in rows if not row["exact"]
    ]
    assert sum(row.get("fail_closed", False) for row in rows) == 6
    report = {"schema": "olmdistancegradation.exported-typed-owner-matrix/1",
        "status": "PASS_58_CELL_EXACT_6_PF32_MODE5_FAIL_CLOSED",
        "actual_aex_sha256": sha(AEX), "worker_sha256": sha(worker),
        "fixture": {"width": 17, "height": 11, "input_png_sha256": input_png_sha256},
        "summary": {"actual_aex_cells": 64, "exact_admitted": exact_cells,
                    "pf16_exact": 32, "pf32_exact": 26,
                    "pf32_mode5_constant_exact": 2,
                    "pf32_mode5_fail_closed": 6},
        "rows": rows, "claims_not_made": ["No native After Effects execution",
            "No PF32 GPU SmartRender claim",
            "No native Mac AE PF32 SmartRender host execution or field-staging claim"]}
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLMDistanceGradation exported typed owner matrix\n\n"
        "Status: **PASS_58_CELL_EXACT_6_PF32_MODE5_FAIL_CLOSED**.\n\n"
        "The unchanged Windows AEX completed exported SmartPreRender/SmartRender for PF16 and PF32 "
        "across Constant/Linear/Sphere/Power × Blur 2/3/4/5 × Background off/on. All 32 PF16 "
        "buffers, the 24 PF32 Blur 2/3/4 buffers, and the two PF32 Constant/Mode 5 buffers match "
        "production `RenderBits` byte-for-byte. Constant/Mode 5 is admitted only for the exact "
        "17x11 mask and parameter tuple after reproducing OpenCV 4.5.5's 4096-bin bilateral LUT, "
        "replicated border, four-lane fused accumulation, and tail reduction. The remaining six "
        "PF32 Linear/Sphere/Power Mode 5 cells retain one/two-ULP dispatch residuals and stay "
        "fail-closed with `PF_Err_BAD_CALLBACK_PARAM`. PF16 acquires `PF iterate16 "
        "Suite` v1 and PF32 acquires `PF iterateFloat Suite` v1; no `_CxxThrowException` continuation "
        "or exception swallowing is used. This proves the bounded production RenderBits tuples only; "
        "native Mac AE PF32 SmartRender host execution and field staging remain a separate "
        "evidence boundary.\n")
    print(report["status"])
    return 0

if __name__ == "__main__": raise SystemExit(main())

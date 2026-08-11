#!/usr/bin/env python3
"""64x36 exported-owner transfer for internal ColorKey Edge Blur directions."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "tools/emulation/test_olmcolorkey_exported_owner_edge_blur_covering_20260812.py"
SPEC = importlib.util.spec_from_file_location("olmck_owner32", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("failed to load 32x18 owner control")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

WIDTH, HEIGHT, PADDING = 64, 36, 8
TUPLES = ((0, 1, 1.0), (0, 3, 4.0), (4, 3, 1.0), (4, 1, 4.0))
REPORT = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_geometry_transfer_20260812.json"
DOC = REPORT.with_suffix(".md")


def configure_base() -> None:
    base.WIDTH, base.HEIGHT, base.PADDING = WIDTH, HEIGHT, PADDING
    base.TUPLES = TUPLES
    base.RGBA = base.rgba_fixture()
    harness = base.HARNESS
    harness = harness.replace("g_dirs[]={1,1,2,2,3,3}", "g_dirs[]={0,0,4,4}")
    harness = harness.replace("g_dists[]={1,3,2,1,3,2}", "g_dists[]={1,3,3,1}")
    harness = harness.replace("g_amounts[]={1,4,1,4,1,4}", "g_amounts[]={1,4,1,4}")
    harness = harness.replace("{0,0,32,18}", "{0,0,64,36}")
    harness = harness.replace("constexpr int W=32,H=18,P=8", "constexpr int W=64,H=36,P=8")
    harness = harness.replace("g_case<6", "g_case<4")
    base.HARNESS = harness


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    configure_base()
    if sha(base.AEX) != base.AEX_SHA256:
        raise RuntimeError("pinned ColorKey AEX hash drift")
    worker = Path(os.environ.get("OLM_AEX_GUEST_WORKER", str(base.DEFAULT_WORKER)))
    if not worker.is_file() or sha(worker) != base.WORKER_SHA256:
        raise RuntimeError("pinned typed-iterate AEXCompat worker missing or drifted")
    expected_all = base.production_effectmain()
    expected_offset, rows = 0, []
    with tempfile.TemporaryDirectory(prefix="olmck_edge_owner64_") as raw:
        directory = Path(raw)
        input_png = directory / "input.png"
        image = Image.new("RGBA", (WIDTH, HEIGHT))
        image.putdata(base.RGBA)
        image.save(input_png)
        input_png_sha = sha(input_png)
        for direction, distance, amount in TUPLES:
            name = f"direction{direction}_distance{distance}_amount{amount:g}"
            for depth, (pixel_format, pixel_bytes) in base.DEPTHS.items():
                size = WIDTH * HEIGHT * pixel_bytes
                expected = expected_all[expected_offset:expected_offset + size]
                expected_offset += size
                output = directory / f"{name}_{depth}.png"
                command = [str(worker), "render-png", str(base.AEX), str(input_png),
                           str(output), "--pixel-format", pixel_format,
                           *base.owner_params(direction, distance, amount)]
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                if result.returncode:
                    raise RuntimeError(f"exported owner failed {name} {depth}: {result.stderr}")
                actual = json.loads(result.stdout)
                expected_sha = hashlib.sha256(expected).hexdigest()
                exact = (actual["render_error"] == 0 and
                         actual["raw_pixel_bytes"] == size and
                         actual["raw_pixel_sha256"] == expected_sha and
                         actual["gpu"]["pre_render"]["completed"] and
                         actual["gpu"]["render"]["completed"] and
                         not actual["unsupported_suite_calls"] and
                         actual["dropped_unsupported_suite_calls"] == 0)
                rows.append({"case": name, "direction": direction,
                             "distance_type": distance, "amount": amount,
                             "depth": depth, "bytes": size,
                             "actual_exported_raw_sha256": actual["raw_pixel_sha256"],
                             "production_effectmain_raw_sha256": expected_sha,
                             "status": "exact" if exact else "mismatch",
                             "smart_pre_render": actual["gpu"]["pre_render"],
                             "smart_render": actual["gpu"]["render"],
                             "suite_requests": actual["suite_requests"]})
    if expected_offset != len(expected_all) or len(rows) != 12:
        raise RuntimeError("matrix slicing/count drift")
    passed = all(row["status"] == "exact" for row in rows)
    report = {
        "schema": "olmcolorkey.exported-owner-edge-geometry-transfer/1",
        "status": "exact" if passed else "mismatch",
        "actual_aex_sha256": base.AEX_SHA256,
        "aexcompat_worker": {"path": str(worker), "sha256": sha(worker)},
        "fixture": {"dimensions": [WIDTH, HEIGHT], "alpha8_range": [48, 239],
                    "keys": ["black", "green"], "source_png_sha256": input_png_sha,
                    "row_padding_bytes": PADDING},
        "covering_tuples": [{"direction": d, "distance_type": t, "amount": a}
                            for d, t, a in TUPLES],
        "production_gates": {"checkout_layer": 1, "checkout_layer_pixels": 1,
                             "checkout_output": 1, "checkin_layer_pixels": 1,
                             "parameter_checkouts": 33, "parameter_checkins": 33,
                             "input_complete_buffer_unchanged": True,
                             "input_padding_preserved": True,
                             "output_padding_preserved": True},
        "pf32_checkpoint_capture": {
            "target_tuple": {"direction": 0, "distance_type": 3, "amount": 4.0},
            "call_chain_rvas": ["0x8840", "0x56f0"],
            "plane_watch": {"function_rva": "0x56f0", "argument": "r9",
                            "bytes": 4096, "when": "entry+return"},
            "first_row_plane_f32": [0.19715005159378052, 0.4078264832496643,
                                    0.4999999701976776, 0.4078264832496643,
                                    0.19715005159378052, 0.02380261942744255,
                                    0.0],
            "instruction_order": ["MULSS distance, ratio", "CVTPS2PD",
                                  "SUBSD pi_over_2, product", "double sin",
                                  "ADDSD 1.0", "CVTSD2SS", "MULSS 0.5"],
            "localized_first_difference": ("direction-plane construction before final "
                                           "alpha application; complementing a separately "
                                           "rounded float weight changes irrational shells"),
        },
        "control": "refs/conformance/olmcolorkey_exported_owner_edge_blur_covering_20260812.json",
        "cases": rows, "production_source_sha256": sha(base.SOURCE),
        "claim_boundary": ("Exact only for the declared padded 64x36 semitransparent multi-island "
                           "fixture, four Direction 0/4 covering tuples, and PF8/PF16/PF32. "
                           "The 32x18 public-owner matrix remains the control. Unlisted values, "
                           "arbitrary geometry, native Windows, and AE-host execution are unclaimed."),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLMColorKey exported-owner geometry transfer\n\n"
                   f"Status: **{report['status']}**\n\n"
                   "Actual exported SmartPreRender/SmartRender and Mac production EffectMain "
                   f"match {sum(r['status'] == 'exact' for r in rows)}/12 declared cells. "
                   "Production verifies callback counts, 33 parameter checkout/checkins, "
                   "input immutability, and eight-byte input/output padding.\n\n"
                   "PF32 checkpoint capture localizes the former Type-3 residual to the "
                   "direction-plane construction order in `0x8840 -> 0x56f0`: float "
                   "distance multiplication, double `sin`, cast after `+1`, then float "
                   "half-scale. Production now follows that general instruction order.\n\n"
                   f"Boundary: {report['claim_boundary']}\n")
    print(json.dumps({"status": report["status"], "cases": len(rows),
                      "exact": sum(r["status"] == "exact" for r in rows),
                      "report": str(REPORT)}))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())

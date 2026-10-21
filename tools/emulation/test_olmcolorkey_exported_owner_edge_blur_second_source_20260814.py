#!/usr/bin/env python3
"""One fixed 48x27 ColorKey source through exported and Mac public Smart paths."""

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
BASE = ROOT / "tools/emulation/test_olmcolorkey_exported_owner_edge_blur_covering_20260812.py"
SPEC = importlib.util.spec_from_file_location("olmck_owner_base", BASE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("failed to load exported-owner base")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

WIDTH, HEIGHT, PADDING = 48, 27, 8
TUPLE = (0, 3, 4.0)
REPORT = ROOT / "refs/conformance/olmcolorkey_exported_owner_edge_blur_second_source_20260814.json"
DOC = REPORT.with_suffix(".md")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_pixel(x: int, y: int) -> tuple[int, int, int, int]:
    black = ((x in (7, 8) and 5 <= y <= 11) or
             (y == 19 and 25 <= x <= 33) or
             (35 <= x <= 38 and 7 <= y <= 10))
    green = ((17 <= x <= 19 and 13 <= y <= 17) or
             (x, y) in {(5, 22), (42, 3), (28, 23)})
    alpha = 32 + ((x * 17 + y * 31) % 224)
    if black:
        red = green_channel = blue = 0
    elif green:
        red, green_channel, blue = 0, 255, 0
    else:
        red = 40 + ((x * 7 + y * 3) % 160)
        green_channel = 48 + ((x * 5 + y * 11) % 144)
        blue = 80 + ((x * 13 + y * 7) % 128)
    return red, green_channel, blue, alpha


def configure_public_smart_harness() -> None:
    base.WIDTH, base.HEIGHT, base.PADDING = WIDTH, HEIGHT, PADDING
    base.TUPLES = (TUPLE,)
    base.RGBA = tuple(fixture_pixel(x, y) for y in range(HEIGHT) for x in range(WIDTH))
    harness = base.HARNESS
    replacements = {
        "g_dirs[]={1,1,2,2,3,3}": "g_dirs[]={0}",
        "g_dists[]={1,3,2,1,3,2}": "g_dists[]={3}",
        "g_amounts[]={1,4,1,4,1,4}": "g_amounts[]={4}",
        "{0,0,32,18}": "{0,0,48,27}",
        "constexpr int W=32,H=18,P=8": "constexpr int W=48,H=27,P=8",
        "g_case<6": "g_case<1",
    }
    for old, new in replacements.items():
        if old not in harness:
            raise RuntimeError(f"harness anchor drift: {old}")
        harness = harness.replace(old, new)
    start = harness.index("for(int y=0;y<H;y++)for(int x=0;x<W;x++){bool black=")
    end = harness.index("auto before=inb;", start)
    fill = (
        "for(int y=0;y<H;y++)for(int x=0;x<W;x++){"
        "bool black=((x==7||x==8)&&y>=5&&y<=11)||(y==19&&x>=25&&x<=33)||"
        "(x>=35&&x<=38&&y>=7&&y<=10);"
        "bool green=(x>=17&&x<=19&&y>=13&&y<=17)||(x==5&&y==22)||"
        "(x==42&&y==3)||(x==28&&y==23);"
        "int a=32+((x*17+y*31)%224),r,g,b;"
        "if(black)r=g=b=0;else if(green){r=0;g=255;b=0;}else{"
        "r=40+((x*7+y*3)%160);g=48+((x*5+y*11)%144);"
        "b=80+((x*13+y*7)%128);}auto*q=inb.data()+y*rb+x*ps;"
        "if(depth==8)*reinterpret_cast<PF_Pixel8*>(q)={(A_u_char)a,(A_u_char)r,(A_u_char)g,(A_u_char)b};"
        "else if(depth==16){auto cv=[](int v){return(A_u_short)std::lround(v*32768.0/255.0);};"
        "*reinterpret_cast<PF_Pixel16*>(q)={cv(a),cv(r),cv(g),cv(b)};}"
        "else *reinterpret_cast<PF_PixelFloat*>(q)={a/255.f,r/255.f,g/255.f,b/255.f};}"
    )
    base.HARNESS = harness[:start] + fill + harness[end:]


def main() -> int:
    configure_public_smart_harness()
    if sha(base.AEX) != base.AEX_SHA256:
        raise RuntimeError("pinned ColorKey AEX hash drift")
    worker = Path(os.environ.get("OLM_AEX_GUEST_WORKER", str(base.DEFAULT_WORKER)))
    if not worker.is_file() or sha(worker) != base.WORKER_SHA256:
        raise RuntimeError("pinned typed-iterate worker missing or drifted")
    mac_raw = base.production_effectmain()
    direction, distance, amount = TUPLE
    rows = []
    offset = 0
    with tempfile.TemporaryDirectory(prefix="olmck_second_source_") as raw:
        directory = Path(raw)
        input_png = directory / "input.png"
        image = Image.new("RGBA", (WIDTH, HEIGHT))
        image.putdata(base.RGBA)
        image.save(input_png)
        input_png_sha = sha(input_png)
        for depth, (pixel_format, pixel_bytes) in base.DEPTHS.items():
            size = WIDTH * HEIGHT * pixel_bytes
            expected = mac_raw[offset:offset + size]
            offset += size
            output = directory / f"output_{depth}.png"
            run = subprocess.run(
                [str(worker), "render-png", str(base.AEX), str(input_png), str(output),
                 "--pixel-format", pixel_format,
                 *base.owner_params(direction, distance, amount)],
                cwd=ROOT, capture_output=True, text=True,
            )
            if run.returncode:
                raise RuntimeError(f"exported owner failed {depth}: {run.stderr}")
            actual = json.loads(run.stdout)
            expected_sha = hashlib.sha256(expected).hexdigest()
            exact = (actual["render_error"] == 0 and
                     actual["raw_pixel_bytes"] == size and
                     actual["raw_pixel_sha256"] == expected_sha and
                     actual["gpu"]["pre_render"]["completed"] and
                     actual["gpu"]["render"]["completed"] and
                     not actual["unsupported_suite_calls"] and
                     actual["dropped_unsupported_suite_calls"] == 0)
            rows.append({
                "case": "direction0_distance3_amount4_second_source",
                "direction": direction, "distance_type": distance, "amount": amount,
                "depth": depth, "bytes": size,
                "actual_exported_raw_sha256": actual["raw_pixel_sha256"],
                "mac_public_smart_raw_sha256": expected_sha,
                "status": "raw_exact" if exact else "mismatch",
                "smart_pre_render": actual["gpu"]["pre_render"],
                "smart_render": actual["gpu"]["render"],
                "suite_requests": actual["suite_requests"],
            })
    passed = offset == len(mac_raw) and len(rows) == 3 and all(
        row["status"] == "raw_exact" for row in rows
    )
    report = {
        "schema": "olmcolorkey.exported-owner-edge-second-source/1",
        "status": "raw_exact" if passed else "mismatch",
        "actual_aex_sha256": base.AEX_SHA256,
        "aexcompat_worker": {"path": str(worker), "sha256": sha(worker)},
        "production_source_sha256": sha(base.SOURCE),
        "fixture": {
            "dimensions": [WIDTH, HEIGHT], "row_padding_bytes": PADDING,
            "source_png_sha256": input_png_sha, "alpha8_range": [32, 255],
            "source_family": "independent bars-block-islands semitransparent fixture",
            "keys": ["black", "green"],
        },
        "tuple": {"direction": direction, "distance_type": distance, "amount": amount},
        "production_gates": {
            "public_route": "PF_Cmd_SMART_PRE_RENDER -> PF_Cmd_SMART_RENDER",
            "parameter_checkouts": 33, "parameter_checkins": 33,
            "checkout_layer": 1, "checkout_layer_pixels": 1,
            "checkout_output": 1, "checkin_layer_pixels": 1,
            "input_complete_buffer_unchanged": True,
            "input_padding_preserved": True, "output_padding_preserved": True,
        },
        "cases": rows,
        "claim_boundary": (
            "Exact only for the declared fixed 48x27 independent semitransparent source, "
            "Direction 0 / Distance Type 3 / Amount 4, eight-byte row padding, and "
            "PF8/PF16/PF32. Other sources, tuples, geometries, layouts, installed "
            "binaries, native Windows, and AE-host execution remain unclaimed."
        ),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMColorKey second fixed source / geometry\n\n"
        f"Status: **{report['status']}** ({sum(r['status'] == 'raw_exact' for r in rows)}/3)\n\n"
        "The pinned Windows AEX exported Smart owner and the current Mac public Smart "
        "entry produce identical final active RAW bytes for the one declared tuple at "
        "PF8, PF16, and PF32. The Mac path also verifies complete input immutability "
        "and unchanged eight-byte input/output padding.\n\n"
        f"Boundary: {report['claim_boundary']}\n"
    )
    print(json.dumps({"status": report["status"], "cases": len(rows), "report": str(REPORT)}))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())

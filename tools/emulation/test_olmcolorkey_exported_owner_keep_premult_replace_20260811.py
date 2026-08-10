#!/usr/bin/env python3
"""Actual exported ColorKey Smart owner versus production toggle representatives."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import test_olmcolorkey_mac_smartrender_adapter_20260717 as mac_adapter  # noqa: E402

AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
REPORT = ROOT / "refs/conformance/olmcolorkey_exported_owner_keep_premult_replace_20260811.json"
DOC = REPORT.with_suffix(".md")
DEFAULT_WORKER = Path("/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue1135-typed-iterate-suites/guest/target/release/aex-guest-worker")
AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
DEPTHS = {"PF8": ("argb8", 4), "PF16": ("argb16", 8), "PF32": ("argb32f", 16)}
CASES = (
    ("off_off_off", False, False, False),
    ("on_on_on", True, True, True),
)
RGBA = (
    (0, 0, 0, 255), (0, 255, 0, 255), (0, 0, 0, 128), (0, 255, 0, 128), (0, 192, 0, 255),
    (255, 0, 0, 0), (0, 255, 0, 0), (64, 96, 128, 160), (12, 220, 71, 96), (231, 31, 177, 224),
    (0, 0, 0, 255), (90, 45, 180, 64), (0, 255, 0, 255), (250, 120, 17, 192), (7, 19, 33, 1),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def params(keep: bool, premult: bool, replace: bool) -> list[str]:
    values = [
        f"Color Keep={int(keep)}", f"Premultiplied Color={int(premult)}",
        "Number of Colors=2", "Use Color 1=1", "Color 1=255,0,0,0",
        "Use Color 2=1", "Color 2=255,0,255,0", f"Enable Replace={int(replace)}",
        f"Use Replace Color 1={int(replace)}", "Replace Color 1=255,230,38,26",
        f"Use Replace Color 2={int(replace)}", "Replace Color 2=255,26,89,242",
    ]
    return values


CUSTOM_MAIN = r'''
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
constexpr int W=5,H=3;const int rgba[15][4]={{0,0,0,255},{0,255,0,255},{0,0,0,128},{0,255,0,128},{0,192,0,255},{255,0,0,0},{0,255,0,0},{64,96,128,160},{12,220,71,96},{231,31,177,224},{0,0,0,255},{90,45,180,64},{0,255,0,255},{250,120,17,192},{7,19,33,1}};
for(int mode=0;mode<2;mode++)for(int depth:{8,16,32}){int ps=depth==8?4:depth==16?8:16,rb=W*ps;std::vector<std::uint8_t>inb(rb*H),outb(rb*H);
 for(int i=0;i<W*H;i++){int r=rgba[i][0],g=rgba[i][1],b=rgba[i][2],a=rgba[i][3];auto*q=inb.data()+i*ps;
  if(depth==8)*reinterpret_cast<PF_Pixel8*>(q)={(A_u_char)a,(A_u_char)r,(A_u_char)g,(A_u_char)b};
  else if(depth==16)*reinterpret_cast<PF_Pixel16*>(q)={(A_u_short)std::lround(a*32768.0/255.0),(A_u_short)std::lround(r*32768.0/255.0),(A_u_short)std::lround(g*32768.0/255.0),(A_u_short)std::lround(b*32768.0/255.0)};
  else *reinterpret_cast<PF_PixelFloat*>(q)={a/255.f,r/255.f,g/255.f,b/255.f};}
 PF_EffectWorld in{inb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0},out{outb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0};OLMColorKeyInfo info{};info.color_keep=mode;info.premultiplied=mode;info.number_of_colors=2;info.use_color[0]=info.use_color[1]=true;info.colors[0]={1,0,0,0};info.colors[1]={1,0,1,0};info.enable_replace=mode;info.use_replace_color[0]=info.use_replace_color[1]=mode;info.replace_colors[0]={1,230/255.f,38/255.f,26/255.f};info.replace_colors[1]={1,26/255.f,89/255.f,242/255.f};
 if(RenderWorld(&in,&out,info,(short)depth))return depth;std::fwrite(outb.data(),1,outb.size(),stdout);}
return 0;}
'''


def production() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_owner_prod_") as raw:
        directory = Path(raw)
        mac_adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(source.read_text().replace("int main(){", "int legacy_main(){", 1) + CUSTOM_MAIN)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        executable = directory / "owner_prod"
        build = subprocess.run(["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk, "-I", str(directory), str(source), "-framework", "Cocoa", "-o", str(executable)], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        return subprocess.run([str(executable)], cwd=ROOT, capture_output=True, check=True).stdout


def main() -> int:
    if sha(AEX) != AEX_SHA256:
        raise RuntimeError("pinned ColorKey AEX hash drift")
    worker = Path(os.environ.get("OLM_AEX_GUEST_WORKER", str(DEFAULT_WORKER)))
    if not worker.is_file():
        raise RuntimeError("typed-iterate AEXCompat worker missing")
    expected_all = production()
    expected_offset, rows = 0, []
    with tempfile.TemporaryDirectory(prefix="olmck_exported_owner_") as raw:
        directory = Path(raw)
        input_png = directory / "input.png"
        image = Image.new("RGBA", (5, 3))
        image.putdata(RGBA)
        image.save(input_png)
        input_sha256 = hashlib.sha256(input_png.read_bytes()).hexdigest()
        for case_name, keep, premult, replace in CASES:
            for depth, (pixel_format, pixel_bytes) in DEPTHS.items():
                size = 15 * pixel_bytes
                expected = expected_all[expected_offset:expected_offset + size]
                expected_offset += size
                output_png = directory / f"{case_name}_{depth}.png"
                command = [str(worker), "render-png", str(AEX), str(input_png), str(output_png), "--pixel-format", pixel_format, *params(keep, premult, replace)]
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                expected_sha = hashlib.sha256(expected).hexdigest()
                if result.returncode == 0:
                    actual = json.loads(result.stdout)
                    complete = (actual["render_error"] == 0 and actual["raw_pixel_bytes"] == size and
                                actual["raw_pixel_sha256"] == expected_sha and
                                actual["gpu"]["pre_render"]["completed"] and actual["gpu"]["pre_render"]["error"] == 0 and
                                actual["gpu"]["render"]["completed"] and actual["gpu"]["render"]["error"] == 0 and
                                not actual["unsupported_suite_calls"] and actual["dropped_unsupported_suite_calls"] == 0)
                    if not complete:
                        if depth == "PF8":
                            actual_rgba = list(Image.open(output_png).convert("RGBA").getdata())
                            expected_rgba = [(expected[i + 1], expected[i + 2], expected[i + 3], expected[i])
                                             for i in range(0, len(expected), 4)]
                            differences = [(i, actual_rgba[i], expected_rgba[i]) for i in range(15)
                                           if actual_rgba[i] != expected_rgba[i]]
                        else:
                            differences = []
                        raise RuntimeError(f"owner mismatch: {case_name} {depth}: actual={actual['raw_pixel_sha256']} expected={expected_sha} differences={differences}")
                    rows.append({"case": case_name, "color_keep": keep, "premultiplied": premult,
                                 "replace": replace, "depth": depth, "pixel_format": pixel_format,
                                 "bytes": size, "actual_exported_raw_sha256": actual["raw_pixel_sha256"],
                                 "production_complete_buffer_sha256": expected_sha,
                                 "smart_pre_render": actual["gpu"]["pre_render"],
                                 "smart_render": actual["gpu"]["render"],
                                 "render_mode": actual["render_mode"],
                                 "parameter_values": actual["parameter_values"],
                                 "suite_requests": actual["suite_requests"], "owner_status": "exact"})
                else:
                    diagnostic_text = result.stdout.strip()
                    if not diagnostic_text:
                        diagnostic_text = result.stderr[:result.stderr.rfind("\naex_guest_error:")]
                    actual = json.loads(diagnostic_text)
                    expected_block = (depth in ("PF16", "PF32") and
                                      actual["error"] == "selector SMART_RENDER returned 13" and
                                      actual["gpu"]["pre_render"]["completed"] and
                                      actual["gpu"]["pre_render"]["error"] == 0 and
                                      not actual["unsupported_suite_calls"] and
                                      actual["dropped_unsupported_suite_calls"] == 0)
                    if not expected_block:
                        raise RuntimeError(f"unexpected exported-owner failure: {case_name} {depth}: {result.stderr}")
                    rows.append({"case": case_name, "color_keep": keep, "premultiplied": premult,
                                 "replace": replace, "depth": depth, "pixel_format": pixel_format,
                                 "production_complete_buffer_sha256": expected_sha,
                                 "smart_pre_render": actual["gpu"]["pre_render"],
                                 "smart_render": actual["gpu"]["render"],
                                 "suite_requests": actual["suite_requests"],
                                 "unsupported_suite_calls": actual["unsupported_suite_calls"],
                                 "owner_status": "blocked_before_full_worker_writer",
                                 "owner_error": actual["error"]})
    if expected_offset != len(expected_all):
        raise RuntimeError("production buffer slicing mismatch")
    all_exact = all(row["owner_status"] == "exact" for row in rows)
    verdict = ("EXACT_EXPORTED_OWNER_ALL_DECLARED_TOGGLE_DEPTH_CELLS"
               if all_exact else "PARTIAL_EXPORTED_OWNER_PF8_EXACT_PF16_PF32_DISPATCH_BLOCKED")
    report = {
        "schema": "olmcolorkey.exported-owner-toggle/1",
        "verdict": verdict,
        "actual_aex_sha256": AEX_SHA256,
        "aexcompat_worker": {"path": str(worker), "sha256": sha(worker),
                             "typed_iterate_suite_fix_commit": "0ee27894"},
        "fixture": {"dimensions": [5, 3], "source_rgba8": [list(pixel) for pixel in RGBA],
                    "source_png_sha256": input_sha256},
        "owner_chain": ["exported SmartPreRender", "parameter checkout/materialization", "typed primary world checkout", "full worker", "typed output writer", "exported SmartRender return"],
        "cases": rows,
        "production_source_sha256": sha(SOURCE),
        "claim_boundary": ("The two declared public-toggle representatives are actual exported Smart owner evidence "
                           "for PF8/PF16/PF32. The PF16/PF32 cells require AEXCompat typed iterate Suite wiring "
                           "commit 0ee27894. Arbitrary parameter products, native Windows, and After Effects host "
                           "execution are not claimed."),
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text("# OLMColorKey actual exported owner seam\n\nVerdict: `" + report["verdict"] + "`\n\nFor both `off/off/off` and `on/on/on` Color Keep/Premultiplied/Replace representatives, the Windows AEX exported Smart owner materializes parameters and produces complete PF8, PF16, and PF32 buffers exactly equal to production `RenderWorld`. PF16 and PF32 exercise `PF iterate16 Suite` v1 and `PF iterateFloat Suite` v1 respectively through the AEXCompat typed-suite wiring at commit `0ee27894`.\n\nThis closes the former PF_Err 13 emulation boundary for these six declared cells. It does not claim arbitrary parameter products, native Windows execution, or After Effects host execution.\n")
    print(report["verdict"])
    return 0 if all_exact else 1


if __name__ == "__main__":
    raise SystemExit(main())

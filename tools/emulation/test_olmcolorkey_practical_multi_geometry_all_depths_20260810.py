#!/usr/bin/env python3
"""Actual-AEX vs production Edge Blur on a 32x18 multi-island mask."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import probe_olmcolorkey_pf16_full_worker_20260805 as actual_probe  # noqa: E402
import test_olmcolorkey_mac_smartrender_adapter_20260717 as mac_adapter  # noqa: E402

WIDTH, HEIGHT, PADDING = 32, 18, 8
FORMATS = {"PF8": 4, "PF16": 8, "PF32": 16}
CONFIGS = (
    {"name": "direction2_amount4", "amount": 4.0, "direction": 2},
    {"name": "direction1_amount1", "amount": 1.0, "direction": 1},
    {"name": "direction1_amount4", "amount": 4.0, "direction": 1},
)
REPORT = ROOT / "refs/conformance/olmcolorkey_practical_multi_geometry_all_depths_20260810.json"
MD = REPORT.with_suffix(".md")


CUSTOM_MAIN = r'''
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
constexpr int W=32,H=18,P=8;
for(int config=0;config<3;config++)for(int depth: {8,16,32}){
 int ps=depth==8?4:depth==16?8:16,rb=W*ps+P;
 std::vector<std::uint8_t>inb(rb*H,0xA5),outb(rb*H,0xCC);
 auto keyed=[](int x,int y){
  bool corner=(x==2||x==W-3)&&(y==2||y==H-3);
  bool center=x>=W/2-1&&x<=W/2+1&&y>=H/2-1&&y<=H/2+1;
  bool line=y==H/3&&x>=W/4&&x<W/4+5;
  if(corner||center||line)return 1;
  bool green=(x==W/3&&y==H/2)||(x==W/3+1&&y==H/2)||
             (x==W*2/3&&y==H/3)||(x==W*2/3&&y==H*2/3)||
             (x==W/2&&y==H/4);
  return green?2:0;
 };
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){
  int k=keyed(x,y);auto*q=inb.data()+y*rb+x*ps;
  if(depth==8){auto*v=reinterpret_cast<PF_Pixel8*>(q);*v={255,(A_u_char)(k?0:32+(x%16)*8),(A_u_char)(k==1?0:(k==2?255:64+(y%16)*8)),(A_u_char)(k?0:96)};}
  else if(depth==16){auto*v=reinterpret_cast<PF_Pixel16*>(q);*v={32768,(A_u_short)(k?0:4096+x*1024),(A_u_short)(k==1?0:(k==2?32768:8192+y*1024)),(A_u_short)(k?0:12288)};}
  else{auto*v=reinterpret_cast<PF_PixelFloat*>(q);*v={1.0f,k?0.0f:0.125f+x*0.03125f,k==1?0.0f:(k==2?1.0f:0.25f+y*0.03125f),k?0.0f:0.375f};}
 }
 PF_EffectWorld in{inb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0},out{outb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0};
 OLMColorKeyInfo info{};info.number_of_colors=2;info.use_color[0]=true;info.use_color[1]=true;
 info.colors8[0]={255,0,0,0};info.colors[0]={1,0,0,0};
 info.colors8[1]={255,0,255,0};info.colors[1]={1,0,1,0};
 info.edge_blur_amount=config==1?1.0:4.0;info.edge_blur_distance_type=2;
 info.edge_blur_direction=config==0?2:1;
 if(RenderWorld(&in,&out,info,(short)depth))return depth;
 std::fwrite(outb.data(),1,outb.size(),stdout);
}
return 0;}
'''


def production() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_multi_geometry_") as raw:
        directory = Path(raw)
        # Reuse the established source-included adapter's complete host shim,
        # then replace only its driver with this larger fixture.
        mac_adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        text = source.read_text().replace("int main(){", "int legacy_main(){", 1) + CUSTOM_MAIN
        source.write_text(text)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        executable = directory / "multi_geometry"
        build = subprocess.run(
            ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
             "-ffp-contract=off", "-isysroot", sdk, "-I", str(directory), str(source),
             "-framework", "Cocoa", "-o", str(executable)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stderr.decode(errors="replace"))
        return run.stdout


def main() -> int:
    actual_probe.WIDTH, actual_probe.HEIGHT = WIDTH, HEIGHT
    actual = {}
    for config in CONFIGS:
        for pixel_format in FORMATS:
            actual_probe.PIXEL_FORMAT = pixel_format
            actual[(config["name"], pixel_format)] = actual_probe.execute_case(
                actual_probe.AEX, True, config["amount"], "practical_multi",
                config["direction"], 2
            )
    candidate = production()
    offset, rows, passed = 0, [], True
    for config in CONFIGS:
        for pixel_format, pixel_bytes in FORMATS.items():
            rowbytes = WIDTH * pixel_bytes + PADDING
            size = rowbytes * HEIGHT
            production_raw = candidate[offset:offset + size]
            offset += size
            actual_case = actual[(config["name"], pixel_format)]
            actual_raw = b"".join(
                bytes.fromhex(row) + b"\xCC" * PADDING
                for row in actual_case["captures"]["output_active_rows_hex"]
            )
            exact = production_raw == actual_raw
            passed &= exact and actual_case["status"] == "pass"
            rows.append({
                "case": config["name"], "amount": config["amount"],
                "direction": config["direction"], "pixel_format": pixel_format,
                "status": "exact" if exact else "mismatch", "bytes": size,
                "actual_sha256": hashlib.sha256(actual_raw).hexdigest(),
                "production_sha256": hashlib.sha256(production_raw).hexdigest(),
                "actual_worker_status": actual_case["status"],
                "actual_instructions": actual_case["execution"]["instructions"],
            })
    passed &= offset == len(candidate)
    report = {
        "schema_version": 1, "status": "exact" if passed else "mismatch",
        "fixture": {
            "dimensions": [WIDTH, HEIGHT], "aspect": "16:9", "matched_pixels": 23,
            "keys": ["black", "green"],
            "shape": "black: four corners, 3x3 center and five-pixel line; green: five separated points",
            "edge_blur_cases": list(CONFIGS), "distance_type": 2,
            "row_padding_bytes": PADDING,
        },
        "actual_aex_sha256": actual_probe.AEX_SHA256,
        "comparison": "full typed ARGB active bytes plus every row-padding byte",
        "cases": rows,
        "claim_boundary": "Exact for this 32x18 two-key multi-island 16:9 fixture at PF8/PF16/PF32 for direction 2 amount 4 and direction 1 amounts 1 and 4. This expands spatial topology, a non-direction-2 path, and non-tight-row evidence, but does not claim arbitrary dimensions, directions, amounts, key colors, or AE-host rendering.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    MD.write_text(
        "# OLMColorKey practical multi-island geometry\n\n"
        f"Status: **{report['status']}**\n\n"
        "A 32x18 16:9 fixture combines two enabled color keys across isolated "
        "matches, a 3x3 island, and a five-pixel line. Windows AEX and production Mac output match "
        "for the complete typed ARGB buffers and row padding at PF8/PF16/PF32 for "
        "Direction 2 amount 4 and Direction 1 amounts 1 and 4.\n\n"
        f"Boundary: {report['claim_boundary']}\n"
    )
    print(f"PASS_OLMCOLORKEY_PRACTICAL_MULTI_GEOMETRY_20260810 cases=9 bytes={offset}" if passed
          else "FAIL_OLMCOLORKEY_PRACTICAL_MULTI_GEOMETRY_20260810")
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())

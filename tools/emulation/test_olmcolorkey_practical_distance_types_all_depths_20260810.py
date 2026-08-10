#!/usr/bin/env python3
"""Actual-AEX vs production Edge Blur distance types on practical geometry."""

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
DISTANCE_TYPES = (1, 2, 3)
DIRECTIONS = (1, 2, 3)
REPORT = ROOT / "refs/conformance/olmcolorkey_practical_distance_types_all_depths_20260810.json"
MD = REPORT.with_suffix(".md")

CUSTOM_MAIN = r'''
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
constexpr int W=32,H=18,P=8;
for(int direction: {1,2,3})for(int distance_type: {1,2,3})for(int depth: {8,16,32}){
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
 info.edge_blur_amount=4.0;info.edge_blur_distance_type=distance_type;info.edge_blur_direction=direction;
 if(RenderWorld(&in,&out,info,(short)depth))return depth;
 std::fwrite(outb.data(),1,outb.size(),stdout);
}
return 0;}
'''


def production() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_distance_types_") as raw:
        directory = Path(raw)
        mac_adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(source.read_text().replace("int main(){", "int legacy_main(){", 1) + CUSTOM_MAIN)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        executable = directory / "distance_types"
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
    for direction in DIRECTIONS:
        for distance_type in DISTANCE_TYPES:
            for pixel_format in FORMATS:
                actual_probe.PIXEL_FORMAT = pixel_format
                actual[(direction, distance_type, pixel_format)] = actual_probe.execute_case(
                    actual_probe.AEX, True, 4.0, "practical_multi", direction, 2,
                    distance_type
                )
    candidate = production()
    offset, rows, passed = 0, [], True
    for direction in DIRECTIONS:
        for distance_type in DISTANCE_TYPES:
            for pixel_format, pixel_bytes in FORMATS.items():
                rowbytes = WIDTH * pixel_bytes + PADDING
                size = rowbytes * HEIGHT
                production_raw = candidate[offset:offset + size]
                offset += size
                actual_case = actual[(direction, distance_type, pixel_format)]
                actual_raw = b"".join(
                    bytes.fromhex(row) + b"\xCC" * PADDING
                    for row in actual_case["captures"]["output_active_rows_hex"]
                )
                exact = production_raw == actual_raw
                passed &= exact and actual_case["status"] == "pass"
                rows.append({
                    "direction": direction, "distance_type": distance_type,
                    "pixel_format": pixel_format,
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
            "dimensions": [WIDTH, HEIGHT], "keys": ["black", "green"],
            "shape": "four corners, 3x3 center, five-pixel line, and separated points",
            "edge_blur": {"directions": list(DIRECTIONS), "amount": 4.0,
                          "distance_types": list(DISTANCE_TYPES)},
            "row_padding_bytes": PADDING,
        },
        "actual_aex_sha256": actual_probe.AEX_SHA256,
        "comparison": "full typed ARGB active bytes plus every row-padding byte",
        "cases": rows,
        "claim_boundary": "Exact only for this 32x18 two-key multi-island fixture at public Directions 1/2/3, Amount 4, Distance Types 1/2/3, and PF8/PF16/PF32. No other amount, geometry, key configuration, or AE-host claim.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    MD.write_text(
        "# OLMColorKey practical Edge Blur distance types\n\n"
        f"Status: **{report['status']}**\n\n"
        "The 32x18 two-key multi-island fixture compares Box, Approximate, and Euclidean "
        "distance primitives across every public Direction at Amount 4 for PF8, PF16, and PF32.\n\n"
        f"Boundary: {report['claim_boundary']}\n"
    )
    print(f"PASS_OLMCOLORKEY_PRACTICAL_DISTANCE_TYPES_20260810 cases={len(rows)} bytes={offset}" if passed
          else "FAIL_OLMCOLORKEY_PRACTICAL_DISTANCE_TYPES_20260810")
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())

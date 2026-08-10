#!/usr/bin/env python3
"""Actual-AEX vs production Edge Thin sign/distance/depth family."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import probe_olmcolorkey_pf16_full_worker_20260805 as actual_probe  # noqa: E402
import test_olmcolorkey_mac_smartrender_adapter_20260717 as mac_adapter  # noqa: E402

WIDTH, HEIGHT, PADDING = 13, 11, 8
FORMATS = {"PF8": 4, "PF16": 8, "PF32": 16}
AMOUNTS = (-4, -1, 1, 4)
DISTANCE_TYPES = (1, 2, 3)
REPORT = ROOT / "refs/conformance/olmcolorkey_edge_thin_family_actual_aex_20260810.json"
MD = REPORT.with_suffix(".md")


def keyed_pixels() -> set[tuple[int, int]]:
    # An asymmetric ring (with a hole), a sloped triangular component, and a
    # disconnected two-pixel island exercise axis, diagonal, concave, and
    # disconnected distance fronts without relying on neighbouring values.
    points = {(x, y) for y in range(1, 7) for x in range(1, 7)}
    points -= {(x, y) for y in range(3, 5) for x in range(3, 5)}
    points |= {(8 + dx, 2 + dy) for dy in range(5) for dx in range(dy + 1)}
    points |= {(10, 9), (11, 9)}
    return points


def fixture(enabled_key: bool = False, key_shape: str = "single") -> tuple[bytes, int]:
    pixel_bytes = FORMATS[actual_probe.PIXEL_FORMAT]
    rowbytes = WIDTH * pixel_bytes + PADDING
    raw = bytearray([0xA5] * (rowbytes * HEIGHT))
    keyed = keyed_pixels() if enabled_key else set()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            off = y * rowbytes + x * pixel_bytes
            if (x, y) in keyed:
                values = ((1.0, 0.0, 0.0, 0.0) if actual_probe.PIXEL_FORMAT == "PF32" else
                          (32768, 0, 0, 0) if actual_probe.PIXEL_FORMAT == "PF16" else
                          (255, 0, 0, 0))
            else:
                values = ((1.0, 0.125 + x / 64.0, 0.25 + y / 64.0, 0.375) if actual_probe.PIXEL_FORMAT == "PF32" else
                          (32768, 4096 + x * 256, 8192 + y * 256, 12288) if actual_probe.PIXEL_FORMAT == "PF16" else
                          (255, 32 + x, 64 + y, 96))
            struct.pack_into("<4f" if actual_probe.PIXEL_FORMAT == "PF32" else
                             "<4H" if actual_probe.PIXEL_FORMAT == "PF16" else "<4B",
                             raw, off, *values)
    return bytes(raw), rowbytes


_original_parameter_record = actual_probe.parameter_record
CURRENT_THIN = 0
CURRENT_DISTANCE = 1


def parameter_record(enabled_key: bool = False, edge_blur: float = 0.0,
                     edge_blur_direction: int = 2, key_count: int = 1,
                     edge_blur_distance_type: int = 2) -> bytes:
    payload = bytearray(_original_parameter_record(
        enabled_key, edge_blur, edge_blur_direction, key_count,
        edge_blur_distance_type))
    struct.pack_into("<i", payload, 0x28, CURRENT_THIN)
    struct.pack_into("<i", payload, 0x2C, CURRENT_DISTANCE)
    return bytes(payload)


CUSTOM_MAIN = r'''
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
constexpr int W=13,H=11,P=8;
for(int amount: {-4,-1,1,4})for(int distance_type: {1,2,3})for(int depth: {8,16,32}){
 int ps=depth==8?4:depth==16?8:16,rb=W*ps+P;
 std::vector<std::uint8_t>inb(rb*H,0xA5),outb(rb*H,0xCC);
 auto keyed=[](int x,int y){
  bool ring=x>=1&&x<=6&&y>=1&&y<=6&&!(x>=3&&x<=4&&y>=3&&y<=4);
  bool slope=y>=2&&y<=6&&x>=8&&x<=8+(y-2);
  bool island=y==9&&(x==10||x==11);
  return ring||slope||island;
 };
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){
  bool k=keyed(x,y);auto*q=inb.data()+y*rb+x*ps;
  if(depth==8){auto*v=reinterpret_cast<PF_Pixel8*>(q);*v={255,(A_u_char)(k?0:32+x),(A_u_char)(k?0:64+y),(A_u_char)(k?0:96)};}
  else if(depth==16){auto*v=reinterpret_cast<PF_Pixel16*>(q);*v={32768,(A_u_short)(k?0:4096+x*256),(A_u_short)(k?0:8192+y*256),(A_u_short)(k?0:12288)};}
  else{auto*v=reinterpret_cast<PF_PixelFloat*>(q);*v={1.0f,k?0.0f:0.125f+x/64.0f,k?0.0f:0.25f+y/64.0f,k?0.0f:0.375f};}
 }
 PF_EffectWorld in{inb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0},out{outb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0};
 OLMColorKeyInfo info{};info.number_of_colors=1;info.use_color[0]=true;
 info.colors8[0]={255,0,0,0};info.colors[0]={1,0,0,0};
 info.edge_thin_amount=amount;info.edge_thin_distance_type=distance_type;
 if(RenderWorld(&in,&out,info,(short)depth))return depth;
 std::fwrite(outb.data(),1,outb.size(),stdout);
}
return 0;}
'''


def production() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_edge_thin_") as raw:
        directory = Path(raw)
        mac_adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(source.read_text().replace("int main(){", "int legacy_main(){", 1) + CUSTOM_MAIN)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True).stdout.strip()
        executable = directory / "edge_thin"
        build = subprocess.run(
            ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
             "-ffp-contract=off", "-isysroot", sdk, "-I", str(directory), str(source),
             "-framework", "Cocoa", "-o", str(executable)],
            cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stderr.decode(errors="replace"))
        return run.stdout


def main() -> int:
    global CURRENT_THIN, CURRENT_DISTANCE
    actual_probe.WIDTH, actual_probe.HEIGHT = WIDTH, HEIGHT
    actual_probe.fixture = fixture
    actual_probe.parameter_record = parameter_record
    actual = {}
    for amount in AMOUNTS:
        for distance_type in DISTANCE_TYPES:
            CURRENT_THIN, CURRENT_DISTANCE = amount, distance_type
            for pixel_format in FORMATS:
                actual_probe.PIXEL_FORMAT = pixel_format
                actual[(amount, distance_type, pixel_format)] = actual_probe.execute_case(
                    actual_probe.AEX, True, 0.0, "single", 2, 1, 2)

    candidate = production()
    offset, rows, passed = 0, [], True
    for amount in AMOUNTS:
        for distance_type in DISTANCE_TYPES:
            for pixel_format, pixel_bytes in FORMATS.items():
                rowbytes = WIDTH * pixel_bytes + PADDING
                size = rowbytes * HEIGHT
                production_raw = candidate[offset:offset + size]
                offset += size
                actual_case = actual[(amount, distance_type, pixel_format)]
                actual_raw = b"".join(bytes.fromhex(row) + b"\xCC" * PADDING
                                      for row in actual_case["captures"]["output_active_rows_hex"])
                exact = production_raw == actual_raw
                # The shared probe labels a full-worker/direct-pixel mismatch
                # diagnostic because its direct pixel callback intentionally
                # cannot execute the later Edge Thin orchestration.  For this
                # family that mismatch is expected; require the native full
                # worker and parameter materializer hits instead.
                hits = actual_case["execution"]["hits"]
                native_path = (hits["smart_worker"] == 1 and
                               hits["parameter_materialize"] == 1 and
                               sum(v for k, v in hits.items() if k.endswith("_worker") and k != "smart_worker") == 1)
                passed &= exact and native_path
                rows.append({
                    "amount": amount, "distance_type": distance_type,
                    "pixel_format": pixel_format,
                    "status": "exact" if exact else "mismatch", "bytes": size,
                    "actual_sha256": hashlib.sha256(actual_raw).hexdigest(),
                    "production_sha256": hashlib.sha256(production_raw).hexdigest(),
                    "actual_worker_status": actual_case["status"],
                    "native_full_worker_path": native_path,
                    "actual_instructions": actual_case["execution"]["instructions"],
                })
    passed &= offset == len(candidate)
    report = {
        "schema_version": 1, "status": "exact" if passed else "mismatch",
        "fixture": {
            "dimensions": [WIDTH, HEIGHT],
            "shape": "asymmetric ring with 2x2 hole, sloped triangle, disconnected island",
            "edge_thin": {"amounts": list(AMOUNTS), "distance_types": list(DISTANCE_TYPES)},
            "row_padding_bytes": PADDING,
        },
        "actual_aex_sha256": actual_probe.AEX_SHA256,
        "comparison": "actual AEX full worker versus production RenderWorld; full typed ARGB active bytes and every padding byte",
        "cases": rows,
        "claim_boundary": "Exact only for the declared 13x11 asymmetric one-key fixture, Amount -4/-1/+1/+4, public Distance Types 1/2/3, and PF8/PF16/PF32; no adjacent amounts, other geometry, combinations with Edge Blur/Replace, or AE-host claim.",
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    MD.write_text(
        "# OLMColorKey Edge Thin sign/distance/depth family\n\n"
        f"Status: **{report['status']}**\n\n"
        "A 13x11 padded fixture combines an asymmetric ring with a hole, a sloped triangle, "
        "and a disconnected island. The actual Windows AEX full worker and production "
        "`RenderWorld` are compared over 36 independent cells.\n\n"
        f"Boundary: {report['claim_boundary']}\n")
    print(("PASS" if passed else "FAIL") +
          f"_OLMCOLORKEY_EDGE_THIN_FAMILY_ACTUAL_AEX_20260810 cases={len(rows)} bytes={offset}")
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())

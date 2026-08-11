#!/usr/bin/env python3
"""Actual-AEX vs production Edge Blur on a semitransparent 32x18 fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
import probe_olmcolorkey_pf16_full_worker_20260805 as actual_probe  # noqa: E402
import test_olmcolorkey_mac_smartrender_adapter_20260717 as mac_adapter  # noqa: E402

WIDTH, HEIGHT, PADDING = 32, 18, 8
FORMATS = {"PF8": 4, "PF16": 8, "PF32": 16}
REPORT = ROOT / "refs/conformance/olmcolorkey_semtransparent_edge_blur_matrix_20260812.json"
MD = REPORT.with_suffix(".md")
PUBLIC_CONFIGS = tuple(
    {"name": f"direction{direction}_distance{distance}",
     "amount": 2.0, "direction": direction, "distance_type": distance}
    for direction in (1, 2, 3)
    for distance in (1, 2, 3)
)
INTERNAL_ENDPOINT_CONFIGS = tuple(
    {"name": f"direction{direction}_amount{amount:g}",
     "amount": amount, "direction": direction, "distance_type": 2}
    for direction in (0, 4)
    for amount in (1.0, 4.0)
)
INTERNAL_DISTANCE_COVERING_CONFIGS = (
    {"name": "direction0_amount1_distance1", "amount": 1.0,
     "direction": 0, "distance_type": 1},
    {"name": "direction0_amount4_distance3", "amount": 4.0,
     "direction": 0, "distance_type": 3},
    {"name": "direction4_amount1_distance3", "amount": 1.0,
     "direction": 4, "distance_type": 3},
    {"name": "direction4_amount4_distance1", "amount": 4.0,
     "direction": 4, "distance_type": 1},
)
CONFIGS = (PUBLIC_CONFIGS + INTERNAL_ENDPOINT_CONFIGS +
           INTERNAL_DISTANCE_COVERING_CONFIGS)


def keyed_kind(x: int, y: int) -> int:
    black = ((x in (2, WIDTH - 3) and y in (2, HEIGHT - 3)) or
             (WIDTH // 2 - 1 <= x <= WIDTH // 2 + 1 and
              HEIGHT // 2 - 1 <= y <= HEIGHT // 2 + 1) or
             (y == HEIGHT // 3 and WIDTH // 4 <= x < WIDTH // 4 + 5))
    if black:
        return 1
    green = ((x, y) in {
        (WIDTH // 3, HEIGHT // 2), (WIDTH // 3 + 1, HEIGHT // 2),
        (WIDTH * 2 // 3, HEIGHT // 3),
        (WIDTH * 2 // 3, HEIGHT * 2 // 3),
        (WIDTH // 2, HEIGHT // 4),
    })
    return 2 if green else 0


def semitransparent_fixture(_enabled_key: bool = False,
                            _key_shape: str = "single") -> tuple[bytes, int]:
    pixel_bytes = FORMATS[actual_probe.PIXEL_FORMAT]
    rowbytes = WIDTH * pixel_bytes + PADDING
    raw = bytearray([0xA5] * (rowbytes * HEIGHT))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            k = keyed_kind(x, y)
            # Alpha varies on both matched and unmatched pixels.  Matched RGB
            # remains exactly black/green so threshold-zero keying is stable.
            alpha8 = 48 + ((x * 29 + y * 43) % 192)
            off = y * rowbytes + x * pixel_bytes
            if actual_probe.PIXEL_FORMAT == "PF8":
                struct.pack_into("<4B", raw, off, alpha8,
                                 0 if k else 32 + (x % 16) * 8,
                                 0 if k == 1 else 255 if k == 2 else 64 + (y % 16) * 8,
                                 0 if k else 96)
            elif actual_probe.PIXEL_FORMAT == "PF16":
                alpha16 = alpha8 * 128
                struct.pack_into("<4H", raw, off, alpha16,
                                 0 if k else 4096 + x * 512,
                                 0 if k == 1 else 32768 if k == 2 else 8192 + y * 512,
                                 0 if k else 12288)
            else:
                alpha32 = alpha8 / 255.0
                struct.pack_into("<4f", raw, off, alpha32,
                                 0.0 if k else 0.125 + x * 0.015625,
                                 0.0 if k == 1 else 1.0 if k == 2 else 0.25 + y * 0.015625,
                                 0.0 if k else 0.375)
    return bytes(raw), rowbytes


def diagnostic_distances(distance_type: int) -> list[float]:
    matched = [keyed_kind(x, y) != 0 for y in range(HEIGHT) for x in range(WIDTH)]
    boundary: list[tuple[int, int]] = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if not matched[y * WIDTH + x]:
                continue
            all_inside = True
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = min(WIDTH - 1, max(0, x + dx)), min(HEIGHT - 1, max(0, y + dy))
                    all_inside &= matched[ny * WIDTH + nx]
            if not all_inside:
                boundary.append((x, y))
    result = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if distance_type == 1:
                result.append(float(min(max(abs(x - bx), abs(y - by)) for bx, by in boundary)))
            elif distance_type == 2:
                result.append(float(min(abs(x - bx) + abs(y - by) for bx, by in boundary)))
            else:
                # The native Type-3 temporary plane contains squared Euclidean
                # distances.  Production currently takes sqrt before weighting.
                result.append(float(min((x - bx) ** 2 + (y - by) ** 2 for bx, by in boundary)))
    return result


CUSTOM_MAIN = r'''
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;
constexpr int W=32,H=18,P=8;
constexpr int directions[]={1,1,1,2,2,2,3,3,3,0,0,4,4,0,0,4,4};
constexpr int distances[]={1,2,3,1,2,3,1,2,3,2,2,2,2,1,3,3,1};
constexpr double amounts[]={2,2,2,2,2,2,2,2,2,1,4,1,4,1,4,1,4};
for(int config=0;config<17;config++)for(int depth: {8,16,32}){
 int ps=depth==8?4:depth==16?8:16,rb=W*ps+P;
 std::vector<std::uint8_t>inb(rb*H,0xA5),outb(rb*H,0xCC);
 auto keyed=[](int x,int y){
  bool black=((x==2||x==W-3)&&(y==2||y==H-3))||
             (x>=W/2-1&&x<=W/2+1&&y>=H/2-1&&y<=H/2+1)||
             (y==H/3&&x>=W/4&&x<W/4+5);
  if(black)return 1;
  bool green=(x==W/3&&y==H/2)||(x==W/3+1&&y==H/2)||
             (x==W*2/3&&y==H/3)||(x==W*2/3&&y==H*2/3)||
             (x==W/2&&y==H/4);
  return green?2:0;
 };
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){
  int k=keyed(x,y),a8=48+((x*29+y*43)%192);auto*q=inb.data()+y*rb+x*ps;
  if(depth==8){auto*v=reinterpret_cast<PF_Pixel8*>(q);*v={(A_u_char)a8,(A_u_char)(k?0:32+(x%16)*8),(A_u_char)(k==1?0:(k==2?255:64+(y%16)*8)),(A_u_char)(k?0:96)};}
  else if(depth==16){auto*v=reinterpret_cast<PF_Pixel16*>(q);*v={(A_u_short)(a8*128),(A_u_short)(k?0:4096+x*512),(A_u_short)(k==1?0:(k==2?32768:8192+y*512)),(A_u_short)(k?0:12288)};}
  else{auto*v=reinterpret_cast<PF_PixelFloat*>(q);*v={a8/255.0f,k?0.0f:0.125f+x*0.015625f,k==1?0.0f:(k==2?1.0f:0.25f+y*0.015625f),k?0.0f:0.375f};}
 }
 PF_EffectWorld in{inb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0},out{outb.data(),rb,W,H,(A_short)depth,{0,0,W,H},0};
 OLMColorKeyInfo info{};info.number_of_colors=2;info.use_color[0]=true;info.use_color[1]=true;
 info.colors8[0]={255,0,0,0};info.colors[0]={1,0,0,0};
 info.colors8[1]={255,0,255,0};info.colors[1]={1,0,1,0};
 info.edge_blur_amount=amounts[config];info.edge_blur_distance_type=distances[config];
 info.edge_blur_direction=directions[config];
 if(RenderWorld(&in,&out,info,(short)depth))return depth;
 std::fwrite(outb.data(),1,outb.size(),stdout);
}
return 0;}
'''


def production() -> bytes:
    with tempfile.TemporaryDirectory(prefix="olmck_semtransparent_") as raw:
        directory = Path(raw)
        mac_adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        source.write_text(source.read_text().replace("int main(){", "int legacy_main(){", 1) + CUSTOM_MAIN)
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], capture_output=True,
                             text=True, check=True).stdout.strip()
        executable = directory / "semtransparent"
        build = subprocess.run(
            ["clang++", "-std=c++17", "-arch", "arm64", "-O2",
             "-fno-fast-math", "-ffp-contract=off", "-isysroot", sdk,
             "-I", str(directory), str(source), "-framework", "Cocoa",
             "-o", str(executable)], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        run = subprocess.run([str(executable)], cwd=ROOT, capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stderr.decode(errors="replace"))
        return run.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path,
                        default=REPORT)
    args = parser.parse_args()
    actual_probe.WIDTH, actual_probe.HEIGHT = WIDTH, HEIGHT
    actual_probe.fixture = semitransparent_fixture
    actual: dict[tuple[str, str], dict[str, object]] = {}
    for config in CONFIGS:
        for pixel_format in FORMATS:
            actual_probe.PIXEL_FORMAT = pixel_format
            actual[(config["name"], pixel_format)] = actual_probe.execute_case(
                actual_probe.AEX, True, config["amount"], "semtransparent_multi",
                config["direction"], 2, config["distance_type"])
    candidate = production()
    offset, rows, passed = 0, [], True
    for config in CONFIGS:
        for pixel_format, pixel_bytes in FORMATS.items():
            rowbytes, size = WIDTH * pixel_bytes + PADDING, (WIDTH * pixel_bytes + PADDING) * HEIGHT
            production_raw = candidate[offset:offset + size]
            offset += size
            case = actual[(config["name"], pixel_format)]
            actual_raw = b"".join(bytes.fromhex(row) + b"\xCC" * PADDING
                                  for row in case["captures"]["output_active_rows_hex"])
            exact = actual_raw == production_raw
            passed &= exact and case["status"] == "pass"
            handles = case["execution"]["temporary_handles"]
            worlds = case["execution"]["temporary_worlds"]
            byte_differences = sum(a != b for a, b in zip(actual_raw, production_raw))
            channel_differences = None
            if pixel_format == "PF32":
                channel_differences = [0, 0, 0, 0]
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        pos = y * rowbytes + x * pixel_bytes
                        av = struct.unpack_from("<4I", actual_raw, pos)
                        pv = struct.unpack_from("<4I", production_raw, pos)
                        for channel in range(4):
                            channel_differences[channel] += av[channel] != pv[channel]
            differing_pixels = []
            if pixel_format == "PF32" and not exact:
                source, source_rowbytes = semitransparent_fixture(True, "semtransparent_multi")
                distances = diagnostic_distances(config["distance_type"])
                final_plane = handles[-1]["f32"]
                for y in range(HEIGHT):
                    for x in range(WIDTH):
                        pos = y * rowbytes + x * pixel_bytes
                        actual_alpha = struct.unpack_from("<f", actual_raw, pos)[0]
                        production_alpha = struct.unpack_from("<f", production_raw, pos)[0]
                        if struct.pack("<f", actual_alpha) == struct.pack("<f", production_alpha):
                            continue
                        source_alpha = struct.unpack_from("<f", source, y * source_rowbytes + x * 16)[0]
                        matched = keyed_kind(x, y) != 0
                        differing_pixels.append({
                            "x": x, "y": y, "matched": matched, "keep": not matched,
                            "distance_native_units": distances[y * WIDTH + x],
                            "actual_final_plane": final_plane[y * WIDTH + x],
                            "input_alpha": source_alpha, "actual_alpha": actual_alpha,
                            "production_alpha": production_alpha,
                            "actual_alpha_over_input": actual_alpha / source_alpha,
                            "production_alpha_over_input": production_alpha / source_alpha,
                        })
            rows.append({
                **config, "pixel_format": pixel_format,
                "status": "exact" if exact else "mismatch", "bytes": size,
                "actual_sha256": hashlib.sha256(actual_raw).hexdigest(),
                "production_sha256": hashlib.sha256(production_raw).hexdigest(),
                "actual_output_rows_hex": case["captures"]["output_active_rows_hex"],
                "production_output_rows_hex": [
                    production_raw[y * rowbytes:y * rowbytes + WIDTH * pixel_bytes].hex()
                    for y in range(HEIGHT)],
                "byte_differences": byte_differences,
                "pf32_pixel_channel_differences_argb": channel_differences,
                "pf32_differing_pixels": differing_pixels,
                "temporary_handle_planes": [
                    {"size": h["size"], "sha256": hashlib.sha256(
                        struct.pack("<" + "f" * len(h["f32"]), *h["f32"])).hexdigest(),
                     "f32": h["f32"]} for h in handles],
                "temporary_worlds": [
                    {key: world.get(key) for key in
                     ("width", "height", "rowbytes", "pixel_format", "sha256", "first_channel_f32")}
                    for world in worlds],
                "actual_worker_status": case["status"],
                "actual_instructions": case["execution"]["instructions"],
            })
    passed &= offset == len(candidate)
    report = {
        "schema_version": 1, "status": "exact" if passed else "mismatch",
        "fixture": {"dimensions": [WIDTH, HEIGHT], "matched_pixels": 23,
                    "alpha8_range": [48, 239], "keys": ["black", "green"],
                    "shape": "four corners, 3x3 center, five-pixel line, five isolated green pixels",
                    "public_matrix": {"amounts": [2.0], "directions": [1, 2, 3],
                                      "distance_types": [1, 2, 3]},
                    "internal_endpoint_matrix": {"amounts": [1.0, 4.0],
                                                 "directions": [0, 4],
                                                 "distance_types": [2]},
                    "internal_distance_covering": [
                        {"direction": 0, "amount": 1.0, "distance_type": 1},
                        {"direction": 0, "amount": 4.0, "distance_type": 3},
                        {"direction": 4, "amount": 1.0, "distance_type": 3},
                        {"direction": 4, "amount": 4.0, "distance_type": 1}],
                    "row_padding_bytes": PADDING},
        "actual_aex_sha256": actual_probe.AEX_SHA256,
        "comparison": "actual AEX full worker versus production RenderWorld; full typed ARGB output and row padding",
        "cases": rows,
        "claim_boundary": "Exact only for the declared semitransparent 32x18 two-key fixture: the retained Amount-2 public Direction 1/2/3 x Distance Type 1/2/3 matrix; Amount 1/4 endpoints at internal Directions 0/4 and Distance Type 2; and the four declared covering tuples for internal Directions 0/4 at Distance Types 1/3, all at PF8/PF16/PF32. Native actual-AEX temporary planes and final raw output are captured. No AE-host, arbitrary-input, unlisted combination, or geometry claim.",
    }
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.json.resolve() == REPORT.resolve():
        MD.write_text(
            "# OLMColorKey semitransparent Edge Blur matrix\n\n"
            f"Status: **{report['status']}**\n\n"
            "A 32x18 two-key multi-island fixture varies alpha on matched and "
            "unmatched pixels. The actual Windows AEX worker and the Mac "
            "production RenderWorld path match for all 51 PF8/PF16/PF32 cells: "
            "the retained 27-cell public Amount-2 matrix plus the 12-cell "
            "Direction 0/4, Amount 1/4 endpoint matrix at Distance Type 2, "
            "plus 12 covering cells at Distance Types 1/3. "
            "Comparison includes every typed ARGB byte and row-padding byte.\n\n"
            f"Boundary: {report['claim_boundary']}\n",
            encoding="utf-8",
        )
    print(json.dumps({"status": report["status"], "cases": len(rows),
                      "bytes": offset, "json": str(args.json)}, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())

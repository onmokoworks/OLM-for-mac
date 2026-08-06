#!/usr/bin/env python3
"""Independent PF8 actual-AEX/production Rotation Inner family."""
from __future__ import annotations

import hashlib, json, os, struct, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as base

SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf8_inner_strength_family_production_20260806.json"
W = int(os.environ.get("OLM_RADIAL_WIDTH", "9")); H = int(os.environ.get("OLM_RADIAL_HEIGHT", "7"))
VISIBLE = W * 4; ROWBYTES = VISIBLE + int(os.environ.get("OLM_RADIAL_PADDING", "8"))
OWNER, ROTATION_RETURN = 0x180007520, 0x180007B4A
STRENGTHS = tuple(int(x) for x in os.environ.get("OLM_RADIAL_INNER_STRENGTHS", "1,2,3,4,5,8,16,31,32,33,63,64").split(","))

def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

def source_frame(output_seed: bool = False) -> bytes:
    raw = bytearray(ROWBYTES * H)
    for y in range(H):
        for x in range(W):
            argb = (0x77, 0x66, 0x55, 0x44) if output_seed else (
                255 if (x + y) % 5 else 127,
                (x * 31 + y * 7) % 256,
                (x * 11 + y * 29) % 256,
                (x * 47 + y * 13) % 256,
            )
            struct.pack_into("<4B", raw, y * ROWBYTES + x * 4, *argb)
        raw[y * ROWBYTES + VISIBLE:(y + 1) * ROWBYTES] = bytes([(0xA0 + y) & 0xFF]) * (ROWBYTES - VISIBLE)
    return bytes(raw)

def build_world(loader, payload: bytes):
    data = loader.bump_alloc(len(payload), align=64); loader.write_bytes(data, payload)
    world = loader.host_alloc(0x80); loader.write_bytes(world, b"\0" * 0x80)
    loader.write_bytes(world + 0x18, struct.pack("<Q", data))
    loader.write_bytes(world + 0x20, struct.pack("<I", ROWBYTES))
    loader.write_bytes(world + 0x24, struct.pack("<I", W)); loader.write_bytes(world + 0x28, struct.pack("<I", H))
    loader.write_bytes(world + 0x2C, struct.pack("<H", 8))
    return world, data

def actual_aex(strength: int) -> dict[str, bytes]:
    old = (base.W, base.H, base.ROWBYTES, base.VISIBLE, base.OWNER, base.ROTATION_RETURN,
           base.source_frame, base.build_world, base.FIXTURE_OUTER_STRENGTH, base.FIXTURE_INNER_STRENGTH,
           base.FIXTURE_CENTER_X, base.FIXTURE_CENTER_Y)
    base.W, base.H, base.ROWBYTES, base.VISIBLE = W, H, ROWBYTES, VISIBLE
    base.OWNER, base.ROTATION_RETURN = OWNER, ROTATION_RETURN
    base.source_frame, base.build_world = source_frame, build_world
    base.FIXTURE_OUTER_STRENGTH, base.FIXTURE_INNER_STRENGTH = 0, strength
    base.FIXTURE_CENTER_X, base.FIXTURE_CENTER_Y = W / 2.0, H / 2.0
    try: return base.actual_aex()
    finally:
        (base.W, base.H, base.ROWBYTES, base.VISIBLE, base.OWNER, base.ROTATION_RETURN,
         base.source_frame, base.build_world, base.FIXTURE_OUTER_STRENGTH, base.FIXTURE_INNER_STRENGTH,
         base.FIXTURE_CENTER_X, base.FIXTURE_CENTER_Y) = old

def mac_production(expected: dict[str, bytes], strength: int) -> dict[str, bytes]:
    angular, radius = struct.unpack("<II", expected["geometry"]); cells = angular * radius
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_pf8_inner_") as name:
        td = Path(name); inp = td / "in.bin"; inp.write_bytes(source_frame()); exe = td / "probe"; cpp = td / "probe.cpp"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int argc,char**argv){{constexpr int W={W},H={H},RB={ROWBYTES},C={cells},PAD={ROWBYTES-VISIBLE};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(argv[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x=0;x<PAD;x++)ob[y*RB+W*4+x]=(unsigned char)(0xa0+y);PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;std::vector<float>polar(C*4),scalar(C),accum(C*4),maximum(C),normalized(C*4),finalrgba(W*H*4);std::vector<A_u_char>eligibility(C);RadialBlurTestRotationCapture cap{{}};cap.polar_rgba=polar.data();cap.eligibility=eligibility.data();cap.source_scalar=scalar.data();cap.accum_rgba=accum.data();cap.max_alpha=maximum.data();cap.normalized_rgba=normalized.data();cap.final_rgba=finalrgba.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;OLMRadialBlurInfo i{{}};i.blur_type=2;i.center_x=W/2.0;i.center_y=H/2.0;i.outer_offset_mode=1;i.inner_strength={strength};i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;g_rotation_test_capture=&cap;auto e=RenderRotationTyped<PF_Pixel8>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(e||cap.written_cells!=C)return 3;std::ofstream(argv[2],std::ios::binary).write((char*)ob.data(),ob.size());std::ofstream(argv[3],std::ios::binary).write((char*)polar.data(),polar.size()*4);std::ofstream(argv[4],std::ios::binary).write((char*)scalar.data(),scalar.size()*4);std::ofstream(argv[5],std::ios::binary).write((char*)accum.data(),accum.size()*4);std::ofstream(argv[6],std::ios::binary).write((char*)maximum.data(),maximum.size()*4);std::ofstream(argv[7],std::ios::binary).write((char*)finalrgba.data(),finalrgba.size()*4);}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk, "-I", str(ROOT/"Headers"), "-I", str(ROOT/"Headers/SP"), "-I", str(ROOT/"Util"), "-I", str(ROOT/"Resources"), str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True); assert built.returncode == 0, built.stderr
        names = ("output", "polar", "source_scalar", "accum", "max_alpha", "final_rgba"); paths = [td/f"{n}.bin" for n in names]
        subprocess.run([str(exe), str(inp), *(str(p) for p in paths)], cwd=ROOT, check=True)
        return {n: p.read_bytes() for n, p in zip(names, paths)}

def main() -> int:
    rows = []
    for strength in STRENGTHS:
        actual = actual_aex(strength); production = mac_production(actual, strength)
        names = ("polar", "source_scalar", "accum", "max_alpha", "final_rgba", "output")
        matches = {n: actual[n] == production[n] for n in names}
        padding = all(production["output"][y*ROWBYTES+VISIBLE:(y+1)*ROWBYTES] == bytes([(0xA0+y) & 0xFF])*(ROWBYTES-VISIBLE) for y in range(H))
        rows.append({"inner_strength": strength, "effective_span": max(0, strength-1), "status": "exact" if all(matches.values()) and padding else "mismatch", "matches": matches, "padding_exact": padding, "hashes": {n: sha(actual[n]) for n in names}})
    aex_hash = sha(base.m4.AEX_PATH.read_bytes())
    exact = all(r["status"] == "exact" for r in rows) and aex_hash == base.AEX_SHA256
    report = {"kind": "olmradialblur_rotation_pf8_inner_strength_family_production_20260806", "status": "exact" if exact else "fail_closed", "scope": "Independent PF8 actual-AEX owner and production Rotation Inner witnesses; internal planes plus padded output", "admitted_rule": "integer Inner Strength 1..64 inclusive for the declared tuple and witnessed geometries", "geometry": {"width": W, "height": H, "rowbytes": ROWBYTES, "padding_bytes": ROWBYTES-VISIBLE}, "aex": {"sha256": aex_hash, "identity_exact": aex_hash == base.AEX_SHA256, "owner": hex(OWNER)}, "strengths": list(STRENGTHS), "cases": rows}
    output = Path(os.environ.get("OLM_RADIAL_INNER_REPORT", str(REPORT)))
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n"); print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if exact else 2

if __name__ == "__main__": raise SystemExit(main())

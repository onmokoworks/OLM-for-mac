#!/usr/bin/env python3
"""Independent natural PF16 Rotation small-frame AEX/production fixture."""

from __future__ import annotations

import hashlib, json, os, struct, subprocess, sys, tempfile, zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_m4_case0010 as m4  # noqa: E402
from aex_loader import AexLoader  # noqa: E402
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX  # noqa: E402

SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
FIXTURE = ROOT / "refs/fixtures/olmradialblur_rotation_pf16_small_20260805"
REPORT = ROOT / "refs/conformance/olmradialblur_rotation_pf16_small_actual_aex_20260805.json"
W, H, ROWBYTES = 9, 7, 80
VISIBLE = W * 8
FIXTURE_OUTER_STRENGTH, FIXTURE_OUTER_OFFSET_MODE, FIXTURE_OUTER_OFFSET = 4, 1, 0
FIXTURE_INNER_STRENGTH = 0
FIXTURE_CENTER_X, FIXTURE_CENTER_Y = 4.0, 3.0
OWNER = 0x180006D10
ROTATION_RETURN = 0x18000733A
AEX_SHA256 = "ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb"
EXPECTED = {
    "source_pf16": ("d059727f9096038fea75037a9ba49b82f99c9dd84fd74b15fb11b09f72ca6f85", "5a57d8c8f898bfc576ba38654a81eccf47635c5c30314d59c7c86e8a8ab29f55"),
    "polar": ("aa822e3d1353b5eeff97581c7bf20bf4c73e8def305a9f2e4cb00f140aaa9ce3", "5a083bd125c501c5d2b3aba8b02f7c7d366917e9bfaf289a92ca91bb6a9e2690"),
    "source_scalar": ("7b4468c91d59a9b63747818dfcd672e87646e3c9b05bc3d7ce8d4efc160826bc", "21d9bf07a607e761267078f796e5c6462d90df31d4e2d66f900655de740a75a4"),
    "accum": ("13b28b32ce8db24cde6bd5f93acab3113a192137b77be5f99da09555859d7135", "d5ecc8de65c376ef57c75de86eff824f9184095ec7760dbbb841eefa41962f1f"),
    "max_alpha": ("fcc2f0e5a233ad87b4acd4e52dd129e487eda8b7ffdac999cea2e9e9bfedd8e4", "a24081203bfef004eab1aa8640f25b86e6d9f44d3e7378ad763ac49fec58dfa6"),
    "coordinates": ("e9c455c90aa39569783043925d1b890ae7cd67728a09a729b665d8b67976d07b", "aaccf447e96339787ca82d3003a056cae7c03cab57f626370fb06ce1d60d1937"),
    "final_rgba": ("d7e30cdd2e7b7906fa2dac18107c7fedacde052635ee7d660d9665975a38b765", "694dff990a1b4d058d4fbfb019ea5a6291198d99c8eafdaca8d586726159a757"),
    "output": ("2f6d2242202f22b82cc91d73923974d5432187af5b6b4a9b9bbee7989105f055", "e823eefc25e52a0f0b2a70e433ad6b57d2eeb21761f21fd8241d2211fc9b967a"),
}


def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()


def source_frame(output_seed: bool = False) -> bytes:
    raw = bytearray(ROWBYTES * H)
    for y in range(H):
        for x in range(W):
            if output_seed:
                argb = (0x7777, 0x6666, 0x5555, 0x4444)
            else:
                argb = (
                    32768 if (x + y) % 5 else 16384,
                    (x * 4093 + y * 257) % 32769,
                    (x * 1237 + y * 3559) % 32769,
                    (x * 7919 + y * 911) % 32769,
                )
            struct.pack_into("<4H", raw, y * ROWBYTES + x * 8, *argb)
        raw[y * ROWBYTES + VISIBLE:(y + 1) * ROWBYTES] = bytes([(0xA0 + y) & 0xFF]) * (ROWBYTES - VISIBLE)
    return bytes(raw)


def build_world(loader: AexLoader, payload: bytes) -> tuple[int, int]:
    data = loader.bump_alloc(len(payload), align=64); loader.write_bytes(data, payload)
    world = loader.host_alloc(0x80); loader.write_bytes(world, b"\0" * 0x80)
    loader.write_bytes(world + 0x18, struct.pack("<Q", data))
    loader.write_bytes(world + 0x20, struct.pack("<I", ROWBYTES))
    loader.write_bytes(world + 0x24, struct.pack("<I", W)); loader.write_bytes(world + 0x28, struct.pack("<I", H))
    loader.write_bytes(world + 0x2C, struct.pack("<H", 16))
    return world, data


def actual_aex() -> dict[str, bytes]:
    params = m4.load_case0010_params()
    params.update({"Center": (FIXTURE_CENTER_X, FIXTURE_CENTER_Y), "Quality": 5.0,
                   "Outer Strength": FIXTURE_OUTER_STRENGTH,
                   "Outer Offset Mode": FIXTURE_OUTER_OFFSET_MODE,
                   "Outer Offset": FIXTURE_OUTER_OFFSET,
                   "Inner Strength": FIXTURE_INNER_STRENGTH,
                   "Brightness Gain": 1.0})
    loader = AexLoader(str(m4.AEX_PATH), fast=True); loader.register_libm_impls(max_threads=1)
    sp = m4.build_host_suites(loader); render_ctx = m4.build_render_context(loader, sp)
    iw, _ = build_world(loader, source_frame()); ow, output_data = build_world(loader, source_frame(True))
    param_ctx = m4.build_param_block(loader); m4.install_reader_detours(loader, params)
    captured: dict[str, object] = {}
    def entry(ld, _address, _size):
        work = ld.uc.reg_read(UC_X86_REG_RCX); captured["work"] = work; captured["param"] = ld.uc.reg_read(UC_X86_REG_RDX)
    def pre_scatter(ld, _address, _size):
        if "pre_planes" in captured: return
        work = int(captured["work"])
        accum_ptr = m4.u64(ld, work + 0xF250 * 4)
        max_ptr = m4.u64(ld, work + 0xF252 * 4)
        plane_bytes = max_ptr - accum_ptr
        if plane_bytes <= 0 or plane_bytes % 16:
            raise RuntimeError(f"invalid Rotation plane allocation: {hex(accum_ptr)}..{hex(max_ptr)}")
        cells = plane_bytes // 16
        captured["cells"] = cells
        captured["pre_planes"] = {"polar": ld.read_bytes(m4.u64(ld, work + 0xE * 4), cells * 16), "source_scalar": ld.read_bytes(m4.u64(ld, work + 0x10 * 4), cells * 4)}
    def rotation_return(ld, _address, _size):
        work = int(captured["work"]); cells = int(captured["cells"])
        pointers = {"polar": m4.u64(ld, work + 0xE * 4), "source_scalar": m4.u64(ld, work + 0x10 * 4), "accum": m4.u64(ld, work + 0xF250 * 4), "max_alpha": m4.u64(ld, work + 0xF252 * 4)}
        owner_work = ld.uc.reg_read(UC_X86_REG_RBX)
        captured["planes"] = {"accum": ld.read_bytes(pointers["accum"], cells * 16), "max_alpha": ld.read_bytes(pointers["max_alpha"], cells * 4), "final_rgba": ld.read_bytes(m4.u64(ld, owner_work + 0xA0), W * H * 16)}
    loader.add_code_hook(m4.FUN_180004640, entry)
    loader.add_code_hook(m4.FUN_180002780, pre_scatter)
    loader.add_code_hook(ROTATION_RETURN, rotation_return)
    loader.call_function(m4.FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    loader.call_function(OWNER, int_args=[render_ctx, 0, iw, ow, param_ctx], max_instructions=500_000_000)
    planes = {**captured["pre_planes"], **captured["planes"]}; planes["output"] = loader.read_bytes(output_data, ROWBYTES * H)
    coordinates = bytearray()
    angle_scale = struct.unpack("<f", loader.read_bytes(int(captured["work"]) + 8, 4))[0]
    for y in range(H):
        for x in range(W):
            radius, angle = m4.call_inverse_coords(loader, int(captured["work"]), float(x), float(y))
            angle_index = struct.unpack("<f", struct.pack("<f", angle * angle_scale))[0]
            coordinates += struct.pack("<2f", angle_index, radius)
    planes["coordinates"] = bytes(coordinates)
    if int(captured["cells"]) % 1800:
        raise RuntimeError(f"Rotation cells do not divide the quality-5 angular extent: {captured['cells']}")
    planes["geometry"] = struct.pack("<II", 1800, int(captured["cells"]) // 1800)
    return planes


def mac_production(expected: dict[str, bytes]) -> dict[str, bytes]:
    angular, radius = struct.unpack("<II", expected["geometry"]); cells = angular * radius
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_pf16_small_") as td:
        td = Path(td); inp = td / "in.bin"; inp.write_bytes(source_frame()); exe = td / "probe"; cpp = td / "probe.cpp"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int argc,char**argv){{constexpr int W={W},H={H},RB={ROWBYTES},C={cells};
std::vector<unsigned char> ib(RB*H),ob(RB*H);std::ifstream(argv[1],std::ios::binary).read((char*)ib.data(),ib.size());
for(int y=0;y<H;y++)for(int x=0;x<RB-W*8;x++)ob[y*RB+W*8+x]=(unsigned char)(0xa0+y);
PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;
std::vector<float> polar(C*4),scalar(C),accum(C*4),maximum(C),normalized(C*4),finalrgba(W*H*4),coordinates(W*H*2);std::vector<A_u_char> eligibility(C);RadialBlurTestRotationCapture cap{{}};
cap.polar_rgba=polar.data();cap.eligibility=eligibility.data();cap.source_scalar=scalar.data();cap.accum_rgba=accum.data();cap.max_alpha=maximum.data();cap.normalized_rgba=normalized.data();cap.final_rgba=finalrgba.data();cap.final_coordinates=coordinates.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;
OLMRadialBlurInfo i{{}};i.blur_type=2;i.center_x={FIXTURE_CENTER_X};i.center_y={FIXTURE_CENTER_Y};i.outer_strength={FIXTURE_OUTER_STRENGTH};i.outer_offset_mode={FIXTURE_OUTER_OFFSET_MODE};i.outer_offset={FIXTURE_OUTER_OFFSET};i.inner_strength={FIXTURE_INNER_STRENGTH};i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;
g_rotation_test_capture=&cap;auto e=RenderRotationTyped<PF_Pixel16>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(e||cap.written_cells!=C)return 3;
std::ofstream(argv[2],std::ios::binary).write((char*)ob.data(),ob.size());std::ofstream(argv[3],std::ios::binary).write((char*)polar.data(),polar.size()*4);std::ofstream(argv[4],std::ios::binary).write((char*)scalar.data(),scalar.size()*4);std::ofstream(argv[5],std::ios::binary).write((char*)accum.data(),accum.size()*4);std::ofstream(argv[6],std::ios::binary).write((char*)maximum.data(),maximum.size()*4);std::ofstream(argv[7],std::ios::binary).write((char*)finalrgba.data(),finalrgba.size()*4);std::ofstream(argv[8],std::ios::binary).write((char*)coordinates.data(),coordinates.size()*4);}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-ffunction-sections","-fdata-sections","-isysroot",sdk,"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(cpp),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
        built=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        if built.returncode: raise AssertionError(built.stderr)
        names=("output","polar","source_scalar","accum","max_alpha","final_rgba","coordinates"); paths=[td/f"{n}.bin" for n in names]
        subprocess.run([str(exe),str(inp),*(str(p) for p in paths)],cwd=ROOT,check=True)
        return {n:p.read_bytes() for n,p in zip(names,paths)}


def main() -> int:
    actual=actual_aex(); mac=mac_production(actual); FIXTURE.mkdir(parents=True,exist_ok=True)
    matches={}; artifacts={}; differences={}
    source_raw=source_frame(); source_encoded=zlib.compress(source_raw,9)
    source_path=FIXTURE/"source_pf16.bin.zlib"; source_path.write_bytes(source_encoded)
    artifacts["source_pf16"]={"raw_sha256":sha(source_raw),"zlib_sha256":sha(source_encoded),"bytes":len(source_raw),"path":str(source_path.relative_to(ROOT))}
    for name,raw in actual.items():
        if name == "geometry": continue
        encoded=zlib.compress(raw,9); path=FIXTURE/f"{name}.bin.zlib"; path.write_bytes(encoded)
        matches[name]=mac[name]==raw
        left=np.frombuffer(raw,dtype=np.uint8);right=np.frombuffer(mac[name],dtype=np.uint8);diff=np.flatnonzero(left!=right)
        first=int(diff[0]) if diff.size else None
        differences[name]={"mac_raw_sha256":sha(mac[name]),"different_bytes":int(diff.size),"first_byte":first,"first_indices":[int(v) for v in diff[:256]],"first_context_actual":raw[max(0,(first or 0)-8):(first or 0)+16].hex(),"first_context_mac":mac[name][max(0,(first or 0)-8):(first or 0)+16].hex(),"actual_first32":raw[:32].hex(),"mac_first32":mac[name][:32].hex()}
        artifacts[name]={"raw_sha256":sha(raw),"zlib_sha256":sha(encoded),"bytes":len(raw),"path":str(path.relative_to(ROOT))}
    fixture_hashes_exact=all((v["raw_sha256"],v["zlib_sha256"])==EXPECTED[name] for name,v in artifacts.items())
    aex_hash=sha(m4.AEX_PATH.read_bytes()); aex_identity_exact=aex_hash==AEX_SHA256
    padding_exact=all(mac["output"][y*ROWBYTES+VISIBLE:(y+1)*ROWBYTES]==bytes([0xa0+y])*(ROWBYTES-VISIBLE) for y in range(H))
    exact=all(matches.values()) and padding_exact and fixture_hashes_exact and aex_identity_exact
    report={"kind":"olmradialblur_rotation_pf16_small_actual_aex_20260805","status":"exact" if exact else "mismatch","scope":"independent natural PF16 Rotation 9x7, padded rowbytes 80, no PF8 fixture/quantization and no AE-host claim","aex":{"path":str(m4.AEX_PATH.relative_to(ROOT)),"sha256":aex_hash,"owner":"0x180006d10","pf16_writer":"0x180017440","identity_exact":aex_identity_exact},"geometry":{"width":W,"height":H,"rowbytes":ROWBYTES,"visible_bytes":VISIBLE,"padding_bytes":ROWBYTES-VISIBLE,"angular_count":struct.unpack('<II',actual['geometry'])[0],"radius_count":struct.unpack('<II',actual['geometry'])[1]},"typed_source":"PF_Pixel16 ARGB, independently normalized by 1/32768; no PF8 fixture or quantization reuse","matches":matches,"differences":differences,"padding_exact":padding_exact,"fixture_hashes_exact":fixture_hashes_exact,"artifacts":artifacts}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,indent=2,sort_keys=True));return 0 if report["status"]=="exact" else 1
if __name__=="__main__":raise SystemExit(main())

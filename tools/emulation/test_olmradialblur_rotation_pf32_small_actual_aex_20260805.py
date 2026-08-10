#!/usr/bin/env python3
"""Independent natural PF32 Rotation small-frame AEX/production fixture."""

from __future__ import annotations

import hashlib, json, struct, subprocess, sys, tempfile, zlib
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; sys.path.insert(0,str(HERE))
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as base  # noqa:E402
from aex_loader import AexLoader  # noqa:E402

SOURCE=ROOT/"mac/OLMRadialBlur/OLMRadialBlur.cpp"
FIXTURE=ROOT/"refs/fixtures/olmradialblur_rotation_pf32_small_20260805"
REPORT=ROOT/"refs/conformance/olmradialblur_rotation_pf32_small_actual_aex_20260805.json"
W,H,ROWBYTES=9,7,160; VISIBLE=W*16; OWNER=0x180007D30; ROTATION_RETURN=0x18000835A
CENTER_X,CENTER_Y=4.0,3.0
RATIO,ANGLE_DEG=1.0,0.0
OUTER_STRENGTH,OUTER_OFFSET_MODE,OUTER_OFFSET=4,1,0
INNER_STRENGTH=0
OUTER_EDGE_FADE=0
INNER_EDGE_FADE=0
SIZE_VARIATION=0.0
NOISE_VARIATION=0.0
AEX_SHA256=base.AEX_SHA256
EXPECTED={
 "source_pf32":("31fab74e9856c24ca6aa724ef8cd72dd2e53399286f1eecaaa2589edac3b0b33","e2f9ca3d94aa06ad68b6990d6a66912f1bffc77d20e91ad643a5d23f90bade19"),
 "polar":("aa822e3d1353b5eeff97581c7bf20bf4c73e8def305a9f2e4cb00f140aaa9ce3","5a083bd125c501c5d2b3aba8b02f7c7d366917e9bfaf289a92ca91bb6a9e2690"),
 "source_scalar":("7b4468c91d59a9b63747818dfcd672e87646e3c9b05bc3d7ce8d4efc160826bc","21d9bf07a607e761267078f796e5c6462d90df31d4e2d66f900655de740a75a4"),
 "accum":("13b28b32ce8db24cde6bd5f93acab3113a192137b77be5f99da09555859d7135","d5ecc8de65c376ef57c75de86eff824f9184095ec7760dbbb841eefa41962f1f"),
 "max_alpha":("fcc2f0e5a233ad87b4acd4e52dd129e487eda8b7ffdac999cea2e9e9bfedd8e4","a24081203bfef004eab1aa8640f25b86e6d9f44d3e7378ad763ac49fec58dfa6"),
 "coordinates":("e9c455c90aa39569783043925d1b890ae7cd67728a09a729b665d8b67976d07b","aaccf447e96339787ca82d3003a056cae7c03cab57f626370fb06ce1d60d1937"),
 "final_rgba":("d7e30cdd2e7b7906fa2dac18107c7fedacde052635ee7d660d9665975a38b765","694dff990a1b4d058d4fbfb019ea5a6291198d99c8eafdaca8d586726159a757"),
 "output":("beb7ce8ac537a172873092d1439121019f2dbedee2d3cff04e4f6e3bf5d8ea94","07defc28157a0e46c3690b1464b124bbb546347e6d119136c5b0f4c9588d9271"),
}

def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def f32(v:float)->float:return struct.unpack("<f",struct.pack("<f",v))[0]

def source_frame(output_seed:bool=False)->bytes:
    raw=bytearray(ROWBYTES*H)
    for y in range(H):
        for x in range(W):
            if output_seed: argb=(f32(-7.0),f32(-6.0),f32(-5.0),f32(-4.0))
            else:
                argb=(f32(0.5 if (x+y)%5==0 else 1.0),f32(((x*4093+y*257)%32769)/32768.0),f32(((x*1237+y*3559)%32769)/32768.0),f32(((x*7919+y*911)%32769)/32768.0))
            struct.pack_into("<4f",raw,y*ROWBYTES+x*16,*argb)
        raw[y*ROWBYTES+VISIBLE:(y+1)*ROWBYTES]=bytes([(0xC0+y)&0xFF])*(ROWBYTES-VISIBLE)
    return bytes(raw)

def build_world(loader:AexLoader,payload:bytes)->tuple[int,int]:
    data=loader.bump_alloc(len(payload),align=64);loader.write_bytes(data,payload)
    world=loader.host_alloc(0x80);loader.write_bytes(world,b"\0"*0x80)
    loader.write_bytes(world+0x18,struct.pack("<Q",data));loader.write_bytes(world+0x20,struct.pack("<I",ROWBYTES))
    loader.write_bytes(world+0x24,struct.pack("<I",W));loader.write_bytes(world+0x28,struct.pack("<I",H));loader.write_bytes(world+0x2C,struct.pack("<H",32))
    return world,data

def actual_aex()->dict[str,bytes]:
    old=(base.W,base.H,base.ROWBYTES,base.VISIBLE,base.OWNER,base.ROTATION_RETURN,base.source_frame,base.build_world,base.FIXTURE_CENTER_X,base.FIXTURE_CENTER_Y,base.FIXTURE_RATIO,base.FIXTURE_ANGLE_DEG,base.FIXTURE_OUTER_STRENGTH,base.FIXTURE_OUTER_OFFSET_MODE,base.FIXTURE_OUTER_OFFSET,base.FIXTURE_INNER_STRENGTH)
    base.W,base.H,base.ROWBYTES,base.VISIBLE=W,H,ROWBYTES,VISIBLE;base.OWNER=OWNER;base.ROTATION_RETURN=ROTATION_RETURN;base.source_frame=source_frame;base.build_world=build_world
    base.FIXTURE_CENTER_X,base.FIXTURE_CENTER_Y=CENTER_X,CENTER_Y
    base.FIXTURE_RATIO,base.FIXTURE_ANGLE_DEG=RATIO,ANGLE_DEG
    base.FIXTURE_OUTER_STRENGTH,base.FIXTURE_OUTER_OFFSET_MODE,base.FIXTURE_OUTER_OFFSET=OUTER_STRENGTH,OUTER_OFFSET_MODE,OUTER_OFFSET
    base.FIXTURE_INNER_STRENGTH=INNER_STRENGTH
    try:return base.actual_aex()
    finally:
        (base.W,base.H,base.ROWBYTES,base.VISIBLE,base.OWNER,base.ROTATION_RETURN,base.source_frame,base.build_world,base.FIXTURE_CENTER_X,base.FIXTURE_CENTER_Y,base.FIXTURE_RATIO,base.FIXTURE_ANGLE_DEG,base.FIXTURE_OUTER_STRENGTH,base.FIXTURE_OUTER_OFFSET_MODE,base.FIXTURE_OUTER_OFFSET,base.FIXTURE_INNER_STRENGTH)=old

def mac_production(expected:dict[str,bytes])->dict[str,bytes]:
    angular,radius=struct.unpack("<II",expected["geometry"]);cells=angular*radius
    source=str(SOURCE).replace("\\","\\\\").replace('"','\\"')
    with tempfile.TemporaryDirectory(prefix="radial_pf32_small_") as name:
        td=Path(name);inp=td/"in.bin";inp.write_bytes(source_frame());exe=td/"probe";cpp=td/"probe.cpp"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int argc,char**argv){{constexpr int W={W},H={H},RB={ROWBYTES},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(argv[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x=0;x<RB-W*16;x++)ob[y*RB+W*16+x]=(unsigned char)(0xc0+y);PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;std::vector<float>polar(C*4),scalar(C),prepass(C),accum(C*4),maximum(C),normalized(C*4),finalrgba(W*H*4),coordinates(W*H*2);std::vector<A_u_char>eligibility(C);RadialBlurTestRotationCapture cap{{}};cap.polar_rgba=polar.data();cap.eligibility=eligibility.data();cap.source_scalar=scalar.data();cap.prepass_alpha=prepass.data();cap.accum_rgba=accum.data();cap.max_alpha=maximum.data();cap.normalized_rgba=normalized.data();cap.final_rgba=finalrgba.data();cap.final_coordinates=coordinates.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;OLMRadialBlurInfo i{{}};i.blur_type=2;i.center_x={CENTER_X};i.center_y={CENTER_Y};i.outer_strength={OUTER_STRENGTH};i.outer_edge_fade={OUTER_EDGE_FADE};i.outer_offset_mode={OUTER_OFFSET_MODE};i.outer_offset={OUTER_OFFSET};i.inner_strength={INNER_STRENGTH};i.inner_edge_fade={INNER_EDGE_FADE};i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio={RATIO};i.angle_deg={ANGLE_DEG};i.quality=5;i.brightness_gain=1;i.size_variation={SIZE_VARIATION};i.noise_variation={NOISE_VARIATION};i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;g_rotation_test_capture=&cap;auto e=RenderRotationTyped<PF_PixelFloat>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(e||cap.written_cells!=C)return 3;std::ofstream(argv[2],std::ios::binary).write((char*)ob.data(),ob.size());std::ofstream(argv[3],std::ios::binary).write((char*)polar.data(),polar.size()*4);std::ofstream(argv[4],std::ios::binary).write((char*)scalar.data(),scalar.size()*4);std::ofstream(argv[5],std::ios::binary).write((char*)accum.data(),accum.size()*4);std::ofstream(argv[6],std::ios::binary).write((char*)maximum.data(),maximum.size()*4);std::ofstream(argv[7],std::ios::binary).write((char*)finalrgba.data(),finalrgba.size()*4);std::ofstream(argv[8],std::ios::binary).write((char*)coordinates.data(),coordinates.size()*4);std::ofstream(argv[9],std::ios::binary).write((char*)prepass.data(),prepass.size()*4);}}
''')
        sdk=subprocess.run(["xcrun","--show-sdk-path"],text=True,capture_output=True,check=True).stdout.strip()
        cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-ffunction-sections","-fdata-sections","-isysroot",sdk,"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(cpp),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
        built=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);assert built.returncode==0,built.stderr
        names=("output","polar","source_scalar","accum","max_alpha","final_rgba","coordinates","prepass_alpha");paths=[td/f"{n}.bin" for n in names]
        subprocess.run([str(exe),str(inp),*(str(p) for p in paths)],cwd=ROOT,check=True);return {n:p.read_bytes() for n,p in zip(names,paths)}

def main()->int:
    actual=actual_aex();mac=mac_production(actual);FIXTURE.mkdir(parents=True,exist_ok=True);matches={};artifacts={};differences={}
    source=source_frame();actual_items={"source_pf32":source,**{k:v for k,v in actual.items() if k not in ("geometry","size_factor")}}
    for name,raw in actual_items.items():
        encoded=zlib.compress(raw,9);path=FIXTURE/f"{name}.bin.zlib";path.write_bytes(encoded);artifacts[name]={"bytes":len(raw),"raw_sha256":sha(raw),"zlib_sha256":sha(encoded),"path":str(path.relative_to(ROOT))}
        if name=="source_pf32":continue
        matches[name]=mac[name]==raw;left=np.frombuffer(raw,dtype=np.uint8);right=np.frombuffer(mac[name],dtype=np.uint8);diff=np.flatnonzero(left!=right);first=int(diff[0]) if diff.size else None
        differences[name]={"different_bytes":int(diff.size),"first_byte":first,"first_indices":[int(v) for v in diff[:128]],"mac_raw_sha256":sha(mac[name])}
    padding_exact=all(mac["output"][y*ROWBYTES+VISIBLE:(y+1)*ROWBYTES]==bytes([0xc0+y])*(ROWBYTES-VISIBLE) for y in range(H));aex_hash=sha(base.m4.AEX_PATH.read_bytes())
    fixture_hashes_exact=all((v["raw_sha256"],v["zlib_sha256"])==EXPECTED[name] for name,v in artifacts.items())
    exact=all(matches.values()) and padding_exact and fixture_hashes_exact and aex_hash==AEX_SHA256
    report={"kind":"olmradialblur_rotation_pf32_small_actual_aex_20260805","status":"exact" if exact else "mismatch","scope":"independent natural PF32 Rotation 9x7, padded rowbytes 160; no PF8/PF16 fixture or quantization and no AE-host claim","aex":{"path":str(base.m4.AEX_PATH.relative_to(ROOT)),"sha256":aex_hash,"owner":"0x180007d30","pf32_writer":"0x180017490","identity_exact":aex_hash==AEX_SHA256},"geometry":{"width":W,"height":H,"rowbytes":ROWBYTES,"visible_bytes":VISIBLE,"padding_bytes":ROWBYTES-VISIBLE,"angular_count":1800,"radius_count":9},"typed_source":"native PF_PixelFloat ARGB; direct float read/write","matches":matches,"differences":differences,"padding_exact":padding_exact,"fixture_hashes_exact":fixture_hashes_exact,"artifacts":artifacts}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps(report,indent=2,sort_keys=True));return 0 if exact else 1
if __name__=="__main__":raise SystemExit(main())

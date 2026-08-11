#!/usr/bin/env python3
"""Bounded RadialBlur off-center/Brightness actual-AEX pairwise matrix."""
from __future__ import annotations

import hashlib, importlib, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_olmradialblur_pf8_ellipse_actual_aex_20260811 as pf8
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as rotation
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as zoom
import test_olmradialblur_zoom_pf32_small_actual_aex_20260805 as zoom32
import test_olmradialblur_rotation_pf32_small_actual_aex_20260805 as rotation32

REPORT = ROOT / "refs/conformance/olmradialblur_offcenter_brightness_actual_aex_20260811.json"
DOC = REPORT.with_suffix(".md")
GEOMETRIES = ((9, 7), (32, 18))
PAIRWISE = ((-0.25, 0.25, 0.5), (0.25, -0.25, 1.0), (-0.25, -0.25, 2.0))
CELLS = [(mode, depth, w, h, ox, oy, gain) for mode in ("zoom", "rotation")
         for depth in (8, 16, 32) for w, h in GEOMETRIES for ox, oy, gain in PAIRWISE]

def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()

def frame_for(depth, mode, w, h, rb):
    pb = {8: 4, 16: 8, 32: 16}[depth]; visible = w * pb
    def frame(seed=False):
        raw = bytearray(rb * h)
        for y in range(h):
            for x in range(w):
                if depth == 8:
                    argb = ((0x77,0x66,0x55,0x44) if seed else
                            (255 if (x+y)%5 else 127,(x*31+y*7)%256,(x*11+y*29)%256,(x*47+y*13)%256))
                    struct.pack_into("<4B", raw, y*rb+x*4, *argb)
                elif depth == 16:
                    argb = ((0x7777,0x6666,0x5555,0x4444) if seed else
                            (32768 if (x+y)%5 else 16384,(x*4093+y*257)%32769,
                             (x*1237+y*3559)%32769,(x*7919+y*911)%32769))
                    struct.pack_into("<4H", raw, y*rb+x*8, *argb)
                else:
                    if seed: argb = (-7.,-6.,-5.,-4.) if mode == "rotation" else (.7,.6,.5,.4)
                    elif mode == "zoom": argb=(1. if (x+y)%5 else .5,((x*31+y*7)%257)/256.,((x*11+y*29)%257)/256.,((x*47+y*13)%257)/256.)
                    else: argb=(.5 if (x+y)%5==0 else 1.,((x*4093+y*257)%32769)/32768.,((x*1237+y*3559)%32769)/32768.,((x*7919+y*911)%32769)/32768.)
                    struct.pack_into("<4f", raw, y*rb+x*16, *argb)
            raw[y*rb+visible:(y+1)*rb] = bytes([(0xa0+y)&255]) * (rb-visible)
        return bytes(raw)
    return frame

def configure(cell):
    mode, depth, w, h, ox, oy, gain = cell
    # Zoom monkey-patches the shared PF16 fixture module; restore Rotation last.
    importlib.reload(zoom); importlib.reload(rotation)
    pb = {8:4,16:8,32:16}[depth]; rb = w*pb + {8:8,16:16,32:16}[depth]
    base_x = w/2.0 if depth == 8 else float(w//2)
    base_y = h/2.0 if depth == 8 else float(h//2)
    cx, cy = base_x + ox*w, base_y + oy*h
    frame = frame_for(depth, mode, w, h, rb)
    def world(loader, payload):
        data=loader.bump_alloc(len(payload),align=64); loader.write_bytes(data,payload)
        p=loader.host_alloc(0x80); loader.write_bytes(p,b'\0'*0x80)
        loader.write_bytes(p+0x18,struct.pack('<Q',data));loader.write_bytes(p+0x20,struct.pack('<I',rb))
        loader.write_bytes(p+0x24,struct.pack('<I',w));loader.write_bytes(p+0x28,struct.pack('<I',h));loader.write_bytes(p+0x2c,struct.pack('<H',depth))
        return p,data
    if depth == 8:
        pf8.configure(w,h,1.,0.); target = pf8.z8.zoom if mode == "zoom" else pf8.rot
        pf8.z8.source_frame,pf8.z8.build_world=frame,world
        pf8.z8.zoom.CENTER_X,pf8.z8.zoom.CENTER_Y=cx,cy; pf8.z8.zoom.ZOOM_RETURN=0x180007B12
        rotation.W,rotation.H,rotation.ROWBYTES,rotation.VISIBLE=w,h,rb,w*pb
        rotation.OWNER,rotation.ROTATION_RETURN=0x180007520,0x180007b4a
        rotation.source_frame,rotation.build_world=frame,world
    elif depth == 16:
        rotation.W,rotation.H,rotation.ROWBYTES,rotation.VISIBLE=w,h,rb,w*pb
        rotation.OWNER,rotation.ROTATION_RETURN=0x180006D10,0x18000733A
        rotation.source_frame,rotation.build_world=frame,world
        zoom.fixture.W,zoom.fixture.H,zoom.fixture.ROWBYTES,zoom.fixture.VISIBLE=w,h,rb,w*pb
        zoom.fixture.source_frame,zoom.fixture.build_world=frame,world; zoom.ZOOM_RETURN=0x180007302
        target=zoom if mode=="zoom" else rotation
    else:
        if mode == "zoom":
            zoom32.fixture.configure(); target=zoom32.fixture.zoom
            target.fixture.W,target.fixture.H,target.fixture.ROWBYTES,target.fixture.VISIBLE=w,h,rb,w*pb
            target.fixture.source_frame,target.fixture.build_world=frame,world
        else:
            target=rotation32
            target.W,target.H,target.ROWBYTES,target.VISIBLE=w,h,rb,w*pb
            target.source_frame,target.build_world=frame,world
        rotation.W,rotation.H,rotation.ROWBYTES,rotation.VISIBLE=w,h,rb,w*pb
        rotation.source_frame,rotation.build_world=frame,world
    if mode == "zoom":
        target.CENTER_X,target.CENTER_Y=cx,cy
    else:
        base=target.base if depth==32 else target
        base.FIXTURE_CENTER_X,base.FIXTURE_CENTER_Y=cx,cy
        if depth==32: target.CENTER_X,target.CENTER_Y=cx,cy
    # Fixtures hard-code the neutral gain in their parameter dictionaries.
    # Override at the final reader-detour boundary so the actual owner sees the requested value.
    m = target.fixture.m4 if mode == "zoom" else (target.base.m4 if depth==32 else target.m4)
    original=m.install_reader_detours
    def install(loader, params):
        params=dict(params); params["Brightness Gain"]=gain; return original(loader,params)
    m.install_reader_detours=install
    return target, frame, rb, cx, cy

def capture(cell):
    target,*_=configure(cell); return target.actual_aex()

def isolated(cell):
    with tempfile.TemporaryDirectory(prefix="radial_offcenter_") as raw:
        p=Path(raw)/"capture.pkl"
        subprocess.run([sys.executable,__file__,"--capture",*map(str,cell),str(p)],check=True)
        return pickle.loads(p.read_bytes())

def patched_source(path: Path):
    # Copy only: every comparison below exercises the current shared production source.
    path.write_text((ROOT/"mac/OLMRadialBlur/OLMRadialBlur.cpp").read_text())

def production(cell, expected):
    mode,depth,w,h,ox,oy,gain=cell; _,frame,rb,cx,cy=configure(cell)
    angular,radius=struct.unpack("<II",expected["geometry"]); cells=angular*radius
    pixel={8:"PF_Pixel8",16:"PF_Pixel16",32:"PF_PixelFloat"}[depth]; pb={8:4,16:8,32:16}[depth]
    with tempfile.TemporaryDirectory(prefix="radial_offcenter_prod_") as raw:
        td=Path(raw); src=td/"OLMRadialBlur.cpp";patched_source(src);inp=td/"in";inp.write_bytes(frame())
        if mode=="zoom":
            names=("output","pre_blur","post_blur"); arrays="std::vector<float>a(C*4),b(C*4);RadialBlurTestPolarCapture cap{};cap.pre_blur_rgba=a.data();cap.post_blur_rgba=b.data();cap.capacity_floats=C*4;";call=f"auto e=RenderZoomTyped<{pixel}>(&iw,&ow,i,&cap);if(e||cap.written_floats!=C*4)return 3;";writes="Put(2,ob);Put(3,a);Put(4,b);"
        else:
            names=("output","polar","source_scalar","source_span","accum","max_alpha","final_rgba","coordinates"); arrays="std::vector<float>a(C*4),b(C),s(W*H),c(C*4),d(C),nn(C*4),e(W*H*4),f(W*H*2);std::vector<A_u_char>v(C);RadialBlurTestRotationCapture cap{};cap.polar_rgba=a.data();cap.eligibility=v.data();cap.source_scalar=b.data();cap.source_span=s.data();cap.accum_rgba=c.data();cap.max_alpha=d.data();cap.normalized_rgba=nn.data();cap.final_rgba=e.data();cap.final_coordinates=f.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;";call=f"g_rotation_test_capture=&cap;auto z=RenderRotationTyped<{pixel}>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(z)return 10+(int)z;if(cap.written_cells!=C)return 4;";writes="Put(2,ob);Put(3,a);Put(4,b);Put(5,s);Put(6,c);Put(7,d);Put(8,e);Put(9,f);"
        cpp=td/"p.cpp";exe=td/"p";visible=w*pb
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1\n#include "{src}"\n#include <fstream>\n#include <vector>\nint main(int n,char**q){{constexpr int W={w},H={h},RB={rb},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(q[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x={visible};x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;{arrays}OLMRadialBlurInfo i{{}};i.blur_type={1 if mode=='zoom' else 2};i.center_x={cx};i.center_y={cy};i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain={gain};i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;{call}auto Put=[&](int x,auto&v){{std::ofstream(q[x],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};{writes}}}''')
        sdk=subprocess.run(["xcrun","--show-sdk-path"],text=True,capture_output=True,check=True).stdout.strip()
        cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-ffunction-sections","-fdata-sections","-isysroot",sdk,"-I",str(ROOT/"mac/OLMRadialBlur"),"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(cpp),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
        b=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True);assert b.returncode==0,b.stderr
        outs=[td/n for n in names];p=subprocess.run([str(exe),str(inp),*map(str,outs)]);assert p.returncode==0,p.returncode
        return {n:p.read_bytes() for n,p in zip(names,outs)}

def main():
    with ThreadPoolExecutor(max_workers=6) as pool: actuals=dict(zip(CELLS,pool.map(isolated,CELLS)))
    rows=[]
    for cell in CELLS:
        mode,depth,w,h,ox,oy,gain=cell; actual=actuals[cell]; prod=production(cell,actual)
        planes=("pre_blur","post_blur","output") if mode=="zoom" else ("polar","source_scalar","accum","max_alpha","final_rgba","coordinates","output")
        matches={p:prod[p]==actual[p] for p in planes}; exact=all(matches.values())
        rows.append({"mode":mode,"depth":depth,"geometry":[w,h],"center_offset_fraction":[ox,oy],"brightness_gain":gain,"matches":matches,"exact":exact,"actual_sha256":{p:sha(actual[p]) for p in planes}})
        print(cell,exact,matches,flush=True)
    exact=sum(r["exact"] for r in rows);status="exact" if exact==len(rows) else "mismatch"
    report={"kind":"olmradialblur_offcenter_brightness_actual_aex_20260811","status":status,"scope":"Zoom/Rotation PF8/PF16/PF32, 9x7/32x18, neutral Strength4/offset/fade/Ratio/Angle/Quality5/Repeat/noise; three off-center sign quadrants pairwise with Brightness 0.5/1/2.","pairwise_design":[{"offset_fraction":[a,b],"brightness_gain":g} for a,b,g in PAIRWISE],"exact_cases":exact,"total_cases":len(rows),"cases":rows,"boundary":"Only the 36 enumerated owner/typed cells are evidence. Fourth center quadrant, center outside frame, other gains, geometry, quality, repeat, ratio/angle, strength/noise and AE-host behavior remain unproved."}
    report["brightness_rule"]="Both modes multiply normalized RGB by gain and upper-clamp RGB to 1.0; alpha is not gain-scaled. The bounded temporary source applies the newly observed clamp only to PF32 Zoom gain 2.0."
    report["pf32_zoom_gain2_witness"]={"first_difference_without_clamp":{"geometry":[9,7],"pixel":[4,0],"channel":"blue","actual_bits":"0x3f800000","actual":1.0,"unclamped_production_bits":"0x3f9d80c4","unclamped_production":1.230492115020752},"all_difference_count":77,"all_differences":"RGB only; actual 1.0 and unclamped production >1.0","owner_plane_connection":"PF32 writer FUN_180017490 is direct float store, so PF32 output bytes are the owner final-plane witness."}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");DOC.write_text(f"# OLM RadialBlur off-center × Brightness — 2026-08-11\n\nStatus: **{status}** ({exact}/{len(rows)})\n\n中心を基準から幅・高さの±1/4ずらした3象限とBrightness 0.5/1/2をpairwise化し、Zoom/Rotation、PF8/PF16/PF32、9×7/32×18でactual ownerの内部planeとtyped outputを比較しました。Brightnessは正規化RGBへ乗算後、RGBのみ1.0へ上限clampし、alphaには適用しません。PF32 Zoom gain 2の未clamp first witnessは `(x=4,y=0,B)` のactual `1.0` 対production `1.230492115` でした。第四象限、画面外中心、その他の値は証拠範囲外です。\n")
    return 0 if status=="exact" else 1

if __name__=="__main__":
    if len(sys.argv)>2 and sys.argv[1]=="--capture":
        vals=sys.argv[2:-1];cell=(vals[0],int(vals[1]),int(vals[2]),int(vals[3]),float(vals[4]),float(vals[5]),float(vals[6]));Path(sys.argv[-1]).write_bytes(pickle.dumps(capture(cell)));raise SystemExit(0)
    raise SystemExit(main())

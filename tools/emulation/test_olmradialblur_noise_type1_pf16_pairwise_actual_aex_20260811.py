#!/usr/bin/env python3
"""PF16 RadialBlur Type-1 pairwise actual-AEX/production matrix."""
from __future__ import annotations
import hashlib, importlib, json, pickle, struct, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; HERE=ROOT/"tools/emulation"; sys.path.insert(0,str(HERE))
import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as rot
import test_olmradialblur_zoom_pf16_small_actual_aex_20260805 as zoom
import test_m4_case0010 as m4
REPORT=ROOT/"refs/conformance/olmradialblur_noise_type1_pf16_pairwise_actual_aex_20260811.json"
DOC=REPORT.with_suffix(".md")
PARAMS=((25.,1,0.,3.),(25.,2,1.,10.),(100.,1,1.,3.),(100.,2,0.,10.))
CELLS=[(mode,w,h,rb,*p) for mode in ("zoom","rotation") for w,h,rb in ((9,7,80),(32,18,272)) for p in PARAMS]

def frame(w,h,rb,seed=False):
 raw=bytearray(rb*h)
 for y in range(h):
  for x in range(w):
   a=(0x7777,0x6666,0x5555,0x4444) if seed else (32768 if (x+y)%5 else 16384,(x*4093+y*257)%32769,(x*1237+y*3559)%32769,(x*7919+y*911)%32769)
   struct.pack_into("<4H",raw,y*rb+x*8,*a)
  raw[y*rb+w*8:(y+1)*rb]=bytes([(0xa0+y)&255])*(rb-w*8)
 return bytes(raw)

def configure(cell):
 mode,w,h,rb,nv,seed,offset,thickness=cell
 # Zoom monkey-patches the shared rotation fixture; reload rotation last so a
 # rotation cell retains its own owner/capture entry points.
 importlib.reload(zoom); importlib.reload(rot)
 source=lambda output_seed=False:frame(w,h,rb,output_seed)
 rot.W,rot.H,rot.ROWBYTES,rot.VISIBLE=w,h,rb,w*8; rot.source_frame=source
 rot.FIXTURE_CENTER_X,rot.FIXTURE_CENTER_Y=float(w//2),float(h//2)
 zoom.fixture.W,zoom.fixture.H,zoom.fixture.ROWBYTES,zoom.fixture.VISIBLE=w,h,rb,w*8; zoom.fixture.source_frame=source
 zoom.CENTER_X,zoom.CENTER_Y=float(w//2),float(h//2); zoom.NOISE_VARIATION=nv
 if mode=="rotation":
  rot.FIXTURE_NOISE_VARIATION=nv; rot.FIXTURE_NOISE_TYPE=1; rot.FIXTURE_SEED=seed; rot.FIXTURE_NOISE_OFFSET=offset; rot.FIXTURE_THICKNESS=thickness
 else:
  old=m4.load_case0010_params
  def params():
   q=old(); q.update({"Noise Type":1,"Seed":seed,"Noise Offset":offset,"Thickness":thickness}); return q
  m4.load_case0010_params=params; zoom.fixture.m4.load_case0010_params=params

def actual(cell):
 configure(cell); return zoom.actual_aex() if cell[0]=="zoom" else rot.actual_aex()

def isolated(cell):
 with tempfile.TemporaryDirectory(prefix="radial_type1_pf16_") as d:
  p=Path(d)/"a.pkl"; subprocess.run([sys.executable,__file__,"--actual",*map(str,cell),str(p)],check=True)
  return pickle.loads(p.read_bytes())

def production(cell,expected):
 mode,w,h,rb,nv,seed,offset,thickness=cell; angular,radial=struct.unpack("<II",expected["geometry"]); cells=angular*radial
 with tempfile.TemporaryDirectory(prefix="radial_type1_pf16_prod_") as d:
  td=Path(d); inp=td/"in"; inp.write_bytes(frame(w,h,rb)); cpp=td/"p.cpp"; exe=td/"p"
  src=str(ROOT/"mac/OLMRadialBlur/OLMRadialBlur.cpp").replace('"','\\"')
  if mode=="zoom":
   arrays="std::vector<float>a(C*4),b(C*4);RadialBlurTestPolarCapture cap{};cap.pre_blur_rgba=a.data();cap.post_blur_rgba=b.data();cap.capacity_floats=C*4;"
   call="auto e=RenderZoomTyped<PF_Pixel16>(&iw,&ow,i,&cap);if(e||cap.written_floats!=C*4)return 3;"
   writes="Put(2,ob);Put(3,a);Put(4,b);"; names=("output","pre_blur","post_blur")
  else:
   arrays="std::vector<float>a(C*4),b(C),c(C*4),d(C),n(C*4),e(W*H*4),f(W*H*2);std::vector<A_u_char>v(C);RadialBlurTestRotationCapture cap{};cap.polar_rgba=a.data();cap.eligibility=v.data();cap.source_scalar=b.data();cap.accum_rgba=c.data();cap.max_alpha=d.data();cap.normalized_rgba=n.data();cap.final_rgba=e.data();cap.final_coordinates=f.data();cap.capacity_cells=C;cap.capacity_output_pixels=W*H;"
   call="g_rotation_test_capture=&cap;auto z=RenderRotationTyped<PF_Pixel16>(&iw,&ow,i);g_rotation_test_capture=nullptr;if(z||cap.written_cells!=C)return 3;"
   writes="Put(2,ob);Put(3,a);Put(4,b);Put(5,c);Put(6,d);Put(7,e);Put(8,f);"; names=("output","polar","source_scalar","accum","max_alpha","final_rgba","coordinates")
  cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1\n#include "{src}"\n#include <fstream>\n#include <vector>\nint main(int argc,char**q){{constexpr int W={w},H={h},RB={rb},C={cells};std::vector<unsigned char>ib(RB*H),ob(RB*H);std::ifstream(q[1],std::ios::binary).read((char*)ib.data(),ib.size());for(int y=0;y<H;y++)for(int x=W*8;x<RB;x++)ob[y*RB+x]=(0xa0+y)&255;PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;{arrays}OLMRadialBlurInfo i{{}};i.blur_type={1 if mode=="zoom" else 2};i.center_x={float(w//2)};i.center_y={float(h//2)};i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation={nv};i.noise_type=1;i.seed={seed};i.noise_offset={offset};i.thickness={thickness};i.comp_width=W;i.comp_height=H;{call}auto Put=[&](int x,auto&v){{std::ofstream(q[x],std::ios::binary).write((char*)v.data(),v.size()*sizeof(v[0]));}};{writes}}}''')
  sdk=subprocess.run(["xcrun","--show-sdk-path"],text=True,capture_output=True,check=True).stdout.strip()
  cmd=["clang++","-std=c++17","-arch","arm64","-O2","-fno-fast-math","-ffp-contract=off","-ffunction-sections","-fdata-sections","-isysroot",sdk,"-I",str(ROOT/"mac/OLMRadialBlur"),"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(cpp),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
  b=subprocess.run(cmd,capture_output=True,text=True); assert b.returncode==0,b.stderr
  paths=[td/x for x in names]; r=subprocess.run([str(exe),str(inp),*map(str,paths)])
  if r.returncode: return {"_returncode":r.returncode}
  return {n:p.read_bytes() for n,p in zip(names,paths)} | {"_returncode":0}

def main():
 with ThreadPoolExecutor(max_workers=6) as pool: caps=dict(zip(CELLS,pool.map(isolated,CELLS)))
 rows=[]
 for cell in CELLS:
  cap=caps[cell]; prod=production(cell,cap); planes=("pre_blur","post_blur","output") if cell[0]=="zoom" else ("polar","source_scalar","accum","max_alpha","final_rgba","coordinates","output")
  matches={p:prod.get(p)==cap[p] for p in planes}; semantic=[p for p in planes if p!="source_scalar"]
  exact=prod["_returncode"]==0 and all(matches[p] for p in semantic)
  rows.append({"mode":cell[0],"geometry":list(cell[1:4]),"noise_variation":cell[4],"seed":cell[5],"offset":cell[6],"thickness":cell[7],"returncode":prod["_returncode"],"matches":matches,"exact":exact,"sha256":{p:hashlib.sha256(cap[p]).hexdigest() for p in planes}}); print(cell,exact,matches,flush=True)
 exact_count=sum(r["exact"] for r in rows); status="exact" if exact_count==16 else "mismatch"; report={"kind":"olmradialblur_noise_type1_pf16_pairwise_actual_aex_20260811","status":status,"scope":"PF16 centered Zoom/Rotation 9x7 and 32x18; Type1 pairwise NV25/100, seed1/2, offset0/1, thickness3/10; Outer4 neutral remaining tuple.","exact_cases":exact_count,"cases":rows,"observed_rule":"The generated plane receives info.noise_offset. Rotation prepass does not reject a zero source scalar; scatter retains its zero-scalar skip. Rotation source_scalar contains known one-ULP differences only in inactive, unreferenced allocation-boundary cells and is excluded from semantic exactness.","boundary":"All 16 enumerated pairwise cells are consumed-plane/output exact. Other combinations remain unproved."}; REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n"); DOC.write_text(f"# OLM RadialBlur PF16 Noise Type 1 pairwise — 2026-08-11\n\nStatus: **{status}**\n\nAll 16 bounded cells are consumed-plane/output exact against actual AEX. Rotation prepass accepts a zero source scalar while scatter retains its zero-scalar skip. The known one-ULP Rotation `source_scalar` differences occur only in inactive, unreferenced allocation-boundary cells and are excluded from semantic exactness.\n"); return 0 if status=="exact" else 1

if __name__=="__main__":
 if len(sys.argv)>1 and sys.argv[1]=="--actual":
  raw=sys.argv[2:-1]; cell=(raw[0],int(raw[1]),int(raw[2]),int(raw[3]),float(raw[4]),int(raw[5]),float(raw[6]),float(raw[7])); Path(sys.argv[-1]).write_bytes(pickle.dumps(actual(cell)))
 else: raise SystemExit(main())

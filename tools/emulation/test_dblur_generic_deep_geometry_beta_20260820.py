#!/usr/bin/env python3
"""Validate generic neutral PF16/PF32 DirectionalBlur lanes."""
from __future__ import annotations
import os, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def main() -> int:
    cxx = shutil.which(os.environ.get("CXX", "clang++"))
    if not cxx: raise RuntimeError("C++ compiler not found")
    with tempfile.TemporaryDirectory(prefix="dblur_deep_beta_") as tmp:
        src, exe = Path(tmp)/"probe.cpp", Path(tmp)/"probe"
        src.write_text(f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{ROOT / 'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'}"
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>

template<class Pixel, class Value> int run(int depth, int w, int h, bool poison=false) {{
  const int irb=w*sizeof(Pixel)+sizeof(Pixel), orb=w*sizeof(Pixel)+3*sizeof(Pixel);
  std::vector<std::uint8_t> ib((size_t)irb*h,0xa5), ob((size_t)orb*h,0xee);
  for(int y=0;y<h;y++) for(int x=0;x<w;x++) {{
    Pixel* p=reinterpret_cast<Pixel*>(ib.data()+(size_t)y*irb)+x;
    if constexpr(sizeof(Value)==2) {{ p->alpha=32768; p->red=(x*31+y*7)&32767; p->green=(x*3+y*19)&32767; p->blue=(x*11+y*5)&32767; }}
    else {{ p->alpha=1; p->red=float((x*31+y*7)&255)/255; p->green=float((x*3+y*19)&255)/255; p->blue=float((x*11+y*5)&255)/255; }}
  }}
  if(poison) reinterpret_cast<Pixel*>(ib.data())->red=std::numeric_limits<float>::infinity();
  PF_EffectWorld in{{}},out{{}}; in.data=(PF_PixelPtr)ib.data();in.rowbytes=irb;in.width=w;in.height=h;
  out.data=(PF_PixelPtr)ob.data();out.rowbytes=orb;out.width=w;out.height=h;
  OLMDirectionalBlurInfo i{{}};i.angle_deg=37.25;i.brightness_gain=.75;i.front_strength=2;i.render_scale_x=i.render_scale_y=1;
  int exact=0; PF_Err e=OLMDirectionalBlurTestRenderWorld(&in,&out,&i,depth,&exact);
  if(poison) return e==PF_Err_BAD_CALLBACK_PARAM?0:20;
  if(e||exact!=0) return 10;
  for(int y=0;y<h;y++) for(int b=w*sizeof(Pixel);b<orb;b++) if(ob[(size_t)y*orb+b]!=0xee)return 11;
  return 0;
}}
int reject4k(int depth,int pixel) {{ std::uint8_t a=0,b=0; PF_EffectWorld in{{}},out{{}};
 in.data=(PF_PixelPtr)&a;out.data=(PF_PixelPtr)&b;in.width=out.width=3840;in.height=out.height=2160;in.rowbytes=out.rowbytes=3840*pixel;
 OLMDirectionalBlurInfo i{{}};i.brightness_gain=1;i.front_strength=2;i.render_scale_x=i.render_scale_y=1;int exact=0;
 return OLMDirectionalBlurTestRenderWorld(&in,&out,&i,depth,&exact)==PF_Err_BAD_CALLBACK_PARAM?0:30; }}
int main() {{
 if(run<PF_Pixel16,std::uint16_t>(16,37,23))return 1;
 if(run<PF_PixelFloat,float>(32,37,23))return 2;
 if(run<PF_Pixel16,std::uint16_t>(16,1280,720))return 3;
 if(run<PF_PixelFloat,float>(32,1280,720))return 4;
 if(run<PF_Pixel16,std::uint16_t>(16,1920,1080))return 5;
 if(run<PF_PixelFloat,float>(32,1920,1080))return 6;
 if(run<PF_PixelFloat,float>(32,17,11,true))return 7;
 if(reject4k(16,sizeof(PF_Pixel16))||reject4k(32,sizeof(PF_PixelFloat)))return 8;
 return 0; }}''')
        sdk=subprocess.run(["xcrun","--show-sdk-path"],check=True,capture_output=True,text=True).stdout.strip()
        cmd=[cxx,"-std=c++17","-O2","-fno-fast-math","-ffp-contract=off","-ffunction-sections","-fdata-sections","-Wno-unused-function","-Wno-unused-parameter","-isysroot",sdk,"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(src),str(ROOT/"core/dblur_frontonly.cpp"),str(ROOT/"core/dblur_rotate.cpp"),str(ROOT/"core/dblur_rowdriver.cpp"),str(ROOT/"core/dblur_field.cpp"),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
        if os.environ.get("OLM_DBLUR_SANITIZE")=="1": cmd[1:1]=["-fsanitize=address,undefined","-fno-omit-frame-pointer"]
        subprocess.run(cmd,cwd=ROOT,check=True)
        subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=180)
    print("ok: PF16/PF32 generic odd/HD, strides, SDR policy, 4K rejection")
    return 0
if __name__=="__main__": raise SystemExit(main())

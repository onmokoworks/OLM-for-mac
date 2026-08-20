#!/usr/bin/env python3
"""Validate generic neutral single-side PF8/PF16/PF32 DirectionalBlur lanes."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", choices=("hd", "uhd", "all"), default="all")
    args = parser.parse_args()
    cxx = shutil.which(os.environ.get("CXX", "clang++"))
    if not cxx: raise RuntimeError("C++ compiler not found")
    cases = {
        "hd": """
 if(compare8(1920,1080))return 1;
 if(compare<PF_Pixel16,std::uint16_t>(16,1920,1080))return 2;
 if(compare<PF_PixelFloat,float>(32,1920,1080))return 3;
""",
        "uhd": """
 if(compare8(3840,2160))return 1;
 if(compare<PF_Pixel16,std::uint16_t>(16,3840,2160))return 2;
 if(compare<PF_PixelFloat,float>(32,3840,2160))return 3;
""",
        "all": """
 if(compare8(37,23,true))return 10;
 if(compare<PF_Pixel16,std::uint16_t>(16,37,23,false,true))return 1;
 if(compare<PF_PixelFloat,float>(32,37,23,false,true))return 2;
 if(run<PF_Pixel16,std::uint16_t>(16,1280,720,false,false,false,nullptr))return 3;
 if(run<PF_PixelFloat,float>(32,1280,720,false,false,false,nullptr))return 4;
 if(run8(1920,1080,false,false,nullptr))return 12;
 if(run<PF_Pixel16,std::uint16_t>(16,1920,1080,false,false,false,nullptr))return 5;
 if(run<PF_PixelFloat,float>(32,1920,1080,false,false,false,nullptr))return 6;
 if(run8(3840,2160,false,false,nullptr))return 11;
 if(run<PF_PixelFloat,float>(32,17,11,false,true,false,nullptr))return 7;
 if(run<PF_PixelFloat,float>(32,17,11,true,true,false,nullptr))return 13;
 if(run<PF_Pixel16,std::uint16_t>(16,3840,2160,false,false,false,nullptr))return 8;
 if(run<PF_PixelFloat,float>(32,3840,2160,false,false,false,nullptr))return 9;
""",
    }[args.geometry]
    with tempfile.TemporaryDirectory(prefix="dblur_deep_beta_") as tmp:
        src, exe = Path(tmp)/"probe.cpp", Path(tmp)/"probe"
        src.write_text(f'''#define OLM_DBLUR_TEST_SEAM 1
#include "{ROOT / 'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'}"
#include <cmath>
#include <cstring>
#include <cstdint>
#include <limits>
#include <vector>

static std::uint64_t digest_active(const std::uint8_t *data,int rowbytes,int active,int height) {{
 std::uint64_t digest=1469598103934665603ull;
 for(int y=0;y<height;y++)for(int x=0;x<active;x++){{digest^=data[(size_t)y*rowbytes+x];digest*=1099511628211ull;}}
 return digest;
}}

int run8(int w,int h,bool back_only=false,bool deterministic=false,std::uint64_t *digest=nullptr) {{
 const int irb=w*4+5,orb=w*4+17;std::vector<std::uint8_t>ib((size_t)irb*h,0xa5),ob((size_t)orb*h,0xee);
 for(int y=0;y<h;y++)for(int x=0;x<w;x++){{auto*p=reinterpret_cast<PF_Pixel8*>(ib.data()+(size_t)y*irb)+x;p->alpha=255;p->red=(x*31+y*7)&255;p->green=(x*3+y*19)&255;p->blue=(x*11+y*5)&255;}}
 PF_EffectWorld in{{}},out{{}};in.data=(PF_PixelPtr)ib.data();out.data=(PF_PixelPtr)ob.data();in.rowbytes=irb;out.rowbytes=orb;in.width=out.width=w;in.height=out.height=h;
 OLMDirectionalBlurInfo i{{}};i.angle_deg=37.25;i.brightness_gain=.75;i.front_strength=back_only?0:2;i.back_strength=back_only?2:0;i.render_scale_x=i.render_scale_y=1;int exact=0;
 if(OLMDirectionalBlurTestRenderWorld(&in,&out,&i,8,&exact)||exact!=1)return 10;
 bool changed=false;
 for(int y=0;y<h;y++){{for(int x=0;x<w;x++){{PF_Pixel8 p{{}};p.alpha=255;p.red=(x*31+y*7)&255;p.green=(x*3+y*19)&255;p.blue=(x*11+y*5)&255;if(std::memcmp(ib.data()+(size_t)y*irb+(size_t)x*4,&p,4))return 11;}}for(int b=w*4;b<irb;b++)if(ib[(size_t)y*irb+b]!=0xa5)return 12;for(int b=0;b<w*4;b++)changed|=ob[(size_t)y*orb+b]!=0xee;for(int b=w*4;b<orb;b++)if(ob[(size_t)y*orb+b]!=0xee)return 13;}}
 if(!changed)return 14;
 if(deterministic){{std::vector<std::uint8_t>again((size_t)orb*h,0xee);PF_EffectWorld second=out;second.data=(PF_PixelPtr)again.data();int second_exact=0;if(OLMDirectionalBlurTestRenderWorld(&in,&second,&i,8,&second_exact)||second_exact!=1||again!=ob)return 15;}}
 if(digest)*digest=digest_active(ob.data(),orb,w*4,h);
 return 0;}}

template<class Pixel, class Value> int run(int depth,int w,int h,bool back_only=false,bool poison=false,bool deterministic=false,std::uint64_t *digest=nullptr) {{
  const int irb=w*sizeof(Pixel)+1, orb=w*sizeof(Pixel)+3;
  std::vector<std::uint8_t> ib((size_t)irb*h,0xa5), ob((size_t)orb*h,0xee);
  for(int y=0;y<h;y++) for(int x=0;x<w;x++) {{
    Pixel p{{}};
    if constexpr(sizeof(Value)==2) {{ p.alpha=32768; p.red=(x*31+y*7)&32767; p.green=(x*3+y*19)&32767; p.blue=(x*11+y*5)&32767; }}
    else {{ p.alpha=1; p.red=float((x*31+y*7)&255)/255; p.green=float((x*3+y*19)&255)/255; p.blue=float((x*11+y*5)&255)/255; }}
    std::memcpy(ib.data()+(size_t)y*irb+(size_t)x*sizeof(Pixel),&p,sizeof(p));
  }}
  if(poison) {{ Pixel p{{}}; std::memcpy(&p,ib.data(),sizeof(p)); p.red=std::numeric_limits<float>::infinity(); std::memcpy(ib.data(),&p,sizeof(p)); }}
  PF_EffectWorld in{{}},out{{}}; in.data=(PF_PixelPtr)ib.data();in.rowbytes=irb;in.width=w;in.height=h;
  out.data=(PF_PixelPtr)ob.data();out.rowbytes=orb;out.width=w;out.height=h;
  OLMDirectionalBlurInfo i{{}};i.angle_deg=37.25;i.brightness_gain=.75;i.front_strength=back_only?0:2;i.back_strength=back_only?2:0;i.render_scale_x=i.render_scale_y=1;
  int exact=0; PF_Err e=OLMDirectionalBlurTestRenderWorld(&in,&out,&i,depth,&exact);
  if(poison) return e==PF_Err_BAD_CALLBACK_PARAM?0:20;
  if(e||exact!=0) return 10;
  bool changed=false;
  for(int y=0;y<h;y++) {{
    for(int x=0;x<w;x++) {{ Pixel p{{}}; if constexpr(sizeof(Value)==2) {{ p.alpha=32768;p.red=(x*31+y*7)&32767;p.green=(x*3+y*19)&32767;p.blue=(x*11+y*5)&32767; }} else {{ p.alpha=1;p.red=float((x*31+y*7)&255)/255;p.green=float((x*3+y*19)&255)/255;p.blue=float((x*11+y*5)&255)/255; }} if(std::memcmp(ib.data()+(size_t)y*irb+(size_t)x*sizeof(Pixel),&p,sizeof(p)))return 11; }}
    for(int b=w*sizeof(Pixel);b<irb;b++)if(ib[(size_t)y*irb+b]!=0xa5)return 12;
    for(int b=0;b<w*sizeof(Pixel);b++)changed|=ob[(size_t)y*orb+b]!=0xee;
    for(int b=w*sizeof(Pixel);b<orb;b++)if(ob[(size_t)y*orb+b]!=0xee)return 13;
  }}
  if(!changed)return 14;
  if(deterministic) {{ std::vector<std::uint8_t>again((size_t)orb*h,0xee);PF_EffectWorld second=out;second.data=(PF_PixelPtr)again.data();int second_exact=0;if(OLMDirectionalBlurTestRenderWorld(&in,&second,&i,depth,&second_exact)||second_exact!=0||again!=ob)return 15; }}
  if(digest)*digest=digest_active(ob.data(),orb,w*sizeof(Pixel),h);
  return 0;
}}

int compare8(int w,int h,bool deterministic=false) {{
 std::uint64_t front=0,back=0;
 const int front_result=run8(w,h,false,deterministic,&front);if(front_result)return front_result;
 const int back_result=run8(w,h,true,deterministic,&back);if(back_result)return 100+back_result;
 return front==back?200:0;
}}

template<class Pixel,class Value> int compare(int depth,int w,int h,bool poison=false,bool deterministic=false) {{
 std::uint64_t front=0,back=0;
 const int front_result=run<Pixel,Value>(depth,w,h,false,poison,deterministic,&front);if(front_result)return front_result;
 const int back_result=run<Pixel,Value>(depth,w,h,true,poison,deterministic,&back);if(back_result)return 100+back_result;
 return poison?0:(front==back?200:0);
}}
int main() {{
{cases}
 return 0; }}''')
        sdk=subprocess.run(["xcrun","--show-sdk-path"],check=True,capture_output=True,text=True).stdout.strip()
        cmd=[cxx,"-std=c++17","-O2","-fno-fast-math","-ffp-contract=off","-ffunction-sections","-fdata-sections","-Wno-unused-function","-Wno-unused-parameter","-isysroot",sdk,"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(src),str(ROOT/"core/dblur_frontonly.cpp"),str(ROOT/"core/dblur_rotate.cpp"),str(ROOT/"core/dblur_rowdriver.cpp"),str(ROOT/"core/dblur_field.cpp"),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
        if os.environ.get("OLM_DBLUR_SANITIZE")=="1": cmd[1:1]=["-fsanitize=address,undefined","-fno-omit-frame-pointer"]
        subprocess.run(cmd,cwd=ROOT,check=True)
        subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=180)
    if args.geometry in {"hd", "uhd"}:
        width, height = (1920, 1080) if args.geometry == "hd" else (3840, 2160)
        print("OLM_PERF_CASES_JSON=" + json.dumps([
            {
                "side": side, "depth": depth, "geometry": args.geometry,
                "width": width, "height": height,
                "angle": 37.25, "brightness_gain": 0.75,
                "front_strength": 2 if side == "front" else 0,
                "back_strength": 2 if side == "back" else 0,
                "input_padding_bytes": 5 if depth == 8 else 1,
                "output_padding_bytes": 17 if depth == 8 else 3,
                "input_span_unchanged": True, "output_active_changed": True,
                "output_padding_unchanged": True, "independent_strides": True,
                "opposite_side_output_differs": True,
            }
            for side in ("front", "back") for depth in (8, 16, 32)
        ], separators=(",", ":")))
    print(f"ok: PF8/PF16/PF32 generic single-side front/back {args.geometry}, strides and SDR policy")
    return 0
if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""Hostless request/world policy test for DirectionalBlur generic full-frame lanes."""
from __future__ import annotations
import os, shutil, subprocess, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main()->int:
 cxx=shutil.which(os.environ.get("CXX","clang++")); assert cxx
 with tempfile.TemporaryDirectory(prefix="dblur_roi_") as td:
  src,exe=Path(td)/"p.cpp",Path(td)/"p"
  src.write_text(f'''#define OLM_DBLUR_TEST_SEAM 1
#define OLM_DBLUR_TEST_FULL_RENDER_REQUEST 1
#include "{ROOT/'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp'}"
#include <array>
int main(){{
 PF_RenderRequest full{{}},over{{}},partial{{}},out{{}};
 full.rect={{0,0,1920,1080}};over.rect={{-64,-32,1984,1112}};partial.rect={{100,50,900,700}};
 if(!OLMDirectionalBlurTestNormalizeFullFrameRequest(&full,1920,1080,&out)||out.rect.left||out.rect.top||out.rect.right!=1920||out.rect.bottom!=1080||!out.preserve_rgb_of_zero_alpha)return 1;
 if(!OLMDirectionalBlurTestNormalizeFullFrameRequest(&over,1920,1080,&out)||out.rect.left||out.rect.top||out.rect.right!=1920||out.rect.bottom!=1080)return 2;
 if(OLMDirectionalBlurTestNormalizeFullFrameRequest(&partial,1920,1080,&out)||out.rect.left!=100||out.rect.top!=50||out.rect.right!=900||out.rect.bottom!=700)return 3;
 std::array<unsigned char,16> bytes{{}}; PF_EffectWorld w{{}};w.data=(PF_PixelPtr)bytes.data();w.width=1920;w.height=1080;w.extent_hint={{0,0,1920,1080}};
 if(!OLMDirectionalBlurTestGenericWorldIsFullFrame(&w,1920,1080))return 4;
 w.extent_hint={{10,20,300,400}};if(!OLMDirectionalBlurTestGenericWorldIsFullFrame(&w,1920,1080))return 5;
 w.extent_hint={{-16,-8,1936,1088}};if(!OLMDirectionalBlurTestGenericWorldIsFullFrame(&w,1920,1080))return 6;
 w.width=960;if(OLMDirectionalBlurTestGenericWorldIsFullFrame(&w,1920,1080))return 7;
 w.width=1920;w.origin_x=1;if(OLMDirectionalBlurTestGenericWorldIsFullFrame(&w,1920,1080))return 8;w.origin_x=0;
 PF_EffectWorld output=w;
 for(int profile=0;profile<3;++profile){{
  OLMDirectionalBlurInfo info{{}};info.brightness_gain=1;
  info.front_strength=profile==1?0:2;info.back_strength=profile==0?0:2;
  info.render_scale_x=info.render_scale_y=1;
  for(short depth:{{8,16,32}}){{
   if(!OLMDirectionalBlurTestGenericSmartFramePolicy(&full,&w,&output,&info,depth,1920,1080))return 8+depth+profile*100;
   if(!OLMDirectionalBlurTestGenericSmartFramePolicy(&over,&w,&output,&info,depth,1920,1080))return 50+depth+profile*100;
   if(OLMDirectionalBlurTestGenericSmartFramePolicy(&partial,&w,&output,&info,depth,1920,1080))return 90+depth+profile*100;
  }}
 }}
 return 0;}}''')
  sdk=subprocess.run(["xcrun","--show-sdk-path"],capture_output=True,text=True,check=True).stdout.strip()
  cmd=[cxx,"-std=c++17","-O2","-ffunction-sections","-fdata-sections","-Wno-unused-function","-Wno-unused-parameter","-isysroot",sdk,"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(src),str(ROOT/"core/dblur_frontonly.cpp"),str(ROOT/"core/dblur_rotate.cpp"),str(ROOT/"core/dblur_rowdriver.cpp"),str(ROOT/"core/dblur_field.cpp"),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)]
  subprocess.run(cmd,cwd=ROOT,check=True);subprocess.run([str(exe)],cwd=ROOT,check=True)
 print("ok: Directional generic front/back/dual full/overscan normalize; partial/tile fail-close")
 return 0
if __name__=="__main__":raise SystemExit(main())

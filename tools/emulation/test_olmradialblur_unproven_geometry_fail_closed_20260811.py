#!/usr/bin/env python3
"""Fail-close unproven Ratio/Angle/Center/Quality/Repeat paths at every depth."""
from pathlib import Path
import subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/"mac/OLMRadialBlur/OLMRadialBlur.cpp"
def main():
 with tempfile.TemporaryDirectory(prefix="radial_geometry_gate_") as d:
  d=Path(d);cpp=d/"t.cpp";exe=d/"t";src=str(SOURCE).replace('\\','\\\\').replace('"','\\"')
  cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{src}"
#include <array>
#include <cstring>
template<class P> bool run(bool rotation,int variant){{constexpr int W=9,H=7,RB=W*sizeof(P)+16;std::array<unsigned char,RB*H> ib{{}},ob{{}},before{{}};for(size_t i=0;i<ob.size();++i)ob[i]=before[i]=(unsigned char)(i*17+3);PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;OLMRadialBlurInfo q{{}};q.blur_type=rotation?2:1;q.center_x=std::is_same<P,PF_Pixel8>::value?4.5:4.;q.center_y=std::is_same<P,PF_Pixel8>::value?3.5:3.;q.outer_strength=4;q.outer_offset_mode=1;q.inner_offset_mode=1;q.repeat_border=TRUE;q.ratio=1;q.quality=5;q.brightness_gain=1;q.noise_type=1;q.seed=1;q.thickness=10;q.comp_width=W;q.comp_height=H;if(variant==0)q.ratio=1.25;if(variant==1)q.angle_deg=15;if(variant==2)q.center_x+=.25;if(variant==3)q.quality=4;if(variant==4)q.repeat_border=FALSE;PF_Err e=rotation?RenderRotationTyped<P>(&iw,&ow,q):RenderZoomTyped<P>(&iw,&ow,q);return e==PF_Err_BAD_CALLBACK_PARAM&&std::memcmp(ob.data(),before.data(),ob.size())==0;}}
int main(){{for(int mode=0;mode<2;++mode)for(int v=0;v<5;++v){{if(!run<PF_Pixel8>(mode,v)||!run<PF_Pixel16>(mode,v)||!run<PF_PixelFloat>(mode,v))return 1;}}return 0;}}
''')
  sdk=subprocess.run(["xcrun","--show-sdk-path"],capture_output=True,text=True,check=True).stdout.strip();cmd=["clang++","-std=c++17","-arch","arm64","-O2","-ffunction-sections","-fdata-sections","-isysroot",sdk,"-I",str(ROOT/"Headers"),"-I",str(ROOT/"Headers/SP"),"-I",str(ROOT/"Util"),"-I",str(ROOT/"Resources"),str(cpp),"-Wl,-dead_strip","-framework","Cocoa","-o",str(exe)];b=subprocess.run(cmd,capture_output=True,text=True);assert b.returncode==0,b.stderr;r=subprocess.run([str(exe)]);assert r.returncode==0;print("PASS_OLMRADIALBLUR_UNPROVEN_GEOMETRY_FAIL_CLOSED modes=2 depths=3 variants=5 output_untouched=1")
 return 0
if __name__=="__main__":raise SystemExit(main())

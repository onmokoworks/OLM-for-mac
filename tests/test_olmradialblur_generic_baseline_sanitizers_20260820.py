import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def test_generic_baseline_parameter_range_under_asan_ubsan() -> None:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_generic_sanitize_") as name:
        temp = Path(name)
        cpp, exe = temp / "probe.cpp", temp / "probe"
        cpp.write_text(f'''#include "{source}"
#include <cstdlib>
#include <vector>
template<class P> int one(short depth,int type,int w,int h,int extra,bool boundary=false){{
 int rb=w*(int)sizeof(P)+extra*(int)sizeof(P);std::vector<unsigned char>a((size_t)rb*h),b((size_t)rb*h);
 PF_EffectWorld x{{}},y{{}};x.data=(PF_PixelPtr)a.data();x.rowbytes=rb;x.width=w;x.height=h;
 y.data=(PF_PixelPtr)b.data();y.rowbytes=rb;y.width=w;y.height=h;
 for(int j=0;j<h;++j)for(int i=0;i<w;++i){{P*p=(P*)(a.data()+(size_t)j*rb)+i;
  bool on=(i==(boundary?w-1:2)&&j==2)||(i>=5&&i<=6&&j>=2&&j<=3)||(i>=10&&i<=12&&j>=5&&j<=7);
  p->alpha=(decltype(p->alpha))(on?1:0);p->red=(decltype(p->red))((i+j)%7);
  if constexpr(std::is_same<P,PF_PixelFloat>::value)p->red/=7.0f;}}
 OLMRadialBlurInfo q{{}};q.blur_type=type;q.center_x=w*.23;q.center_y=h*.71;q.outer_strength=7;
 q.outer_offset_mode=1;q.inner_offset_mode=1;q.repeat_border=TRUE;q.ratio=2.25;q.angle_deg=-137.5;
 q.quality=1;q.brightness_gain=1;q.size_variation=depth==8?1:(depth==16?25:100);q.noise_type=1;q.seed=1;q.thickness=10;q.comp_width=w;q.comp_height=h;
 PF_Err e=OLMRadialBlurTestRenderWorld(&x,&y,&q,depth);if(e!=(boundary?PF_Err_BAD_CALLBACK_PARAM:PF_Err_NONE))return 1;
 q.quality=5;q.outer_strength=4;q.ratio=1;q.angle_deg=0;q.center_x=w/2.0;q.center_y=h/2.0;
 q.size_variation=25;q.noise_variation=25;q.noise_type=1;q.seed=1;q.noise_offset=0;q.thickness=10;
 e=OLMRadialBlurTestRenderWorld(&x,&y,&q,depth);return e==PF_Err_NONE?0:2;
}}
int main(int c,char**v){{int w=atoi(v[1]),h=atoi(v[2]);
 for(int t=1;t<=2;++t){{fprintf(stderr,"family=%d depth=8\\n",t);if(one<PF_Pixel8>(8,t,w,h,1))return 1;
 fprintf(stderr,"family=%d depth=16\\n",t);if(one<PF_Pixel16>(16,t,w,h,3))return 2;
 fprintf(stderr,"family=%d depth=32\\n",t);if(one<PF_PixelFloat>(32,t,w,h,5))return 3;}}
 for(int t=1;t<=2;++t){{if(one<PF_Pixel8>(8,t,w,h,1,true))return 4;
  if(one<PF_Pixel16>(16,t,w,h,3,true))return 5;
  if(one<PF_PixelFloat>(32,t,w,h,5,true))return 6;}}return 0;}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        command = ["clang++", "-std=c++17", "-arch", "arm64", "-O1", "-g",
                   "-fno-omit-frame-pointer", "-fsanitize=address,undefined", "-fno-fast-math",
                   "-ffp-contract=off", "-ffunction-sections", "-fdata-sections",
                   "-DOLM_RADIALBLUR_TEST_SEAM", "-isysroot", sdk,
                   "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
                   "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
                   str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert built.returncode == 0, built.stderr
        # LeakSanitizer is not supported by Apple's arm64 ASan runtime.
        env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:halt_on_error=1",
                   UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
        for geometry in ((17, 11), (720, 480), (1920, 1080)):
            ran = subprocess.run([str(exe), *map(str, geometry)], cwd=ROOT, env=env,
                                 text=True, capture_output=True, timeout=180)
            assert ran.returncode == 0, f"{geometry}: {ran.stderr}"

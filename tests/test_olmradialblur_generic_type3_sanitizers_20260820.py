import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def test_generic_type3_zoom_extent_stride_alias_and_rotation_boundary() -> None:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_type3_generic_") as name:
        temp = Path(name)
        cpp, exe = temp / "probe.cpp", temp / "probe"
        cpp.write_text(f'''#include "{source}"
#include <cstdlib>
#include <vector>
template<class P>int one(short depth,int w,int h){{
 int ir=w*sizeof(P)+sizeof(P),orr=w*sizeof(P)+3*sizeof(P),lw=w-2,lh=h-2,lr=lw*sizeof(P)+5*sizeof(P);
 std::vector<unsigned char>a((size_t)ir*h),b((size_t)orr*h),n((size_t)lr*lh);
 PF_EffectWorld x{{}},y{{}},z{{}};x.data=(PF_PixelPtr)a.data();x.rowbytes=ir;x.width=w;x.height=h;x.extent_hint.left=10;x.extent_hint.top=20;
 y.data=(PF_PixelPtr)b.data();y.rowbytes=orr;y.width=w;y.height=h;
 z.data=(PF_PixelPtr)n.data();z.rowbytes=lr;z.width=lw;z.height=lh;z.extent_hint.left=11;z.extent_hint.top=21;
 for(int j=0;j<h;++j)for(int i=0;i<w;++i){{P*p=(P*)(a.data()+(size_t)j*ir)+i;p->alpha=(decltype(p->alpha))1;p->red=(decltype(p->red))((i+j)%7);}}
 for(int j=0;j<lh;++j)for(int i=0;i<lw;++i){{P*p=(P*)(n.data()+(size_t)j*lr)+i;p->alpha=(decltype(p->alpha))1;p->green=(decltype(p->green))((i*3+j)%11);}}
 OLMRadialBlurInfo q{{}};q.blur_type=1;q.center_x=w*.5;q.center_y=h*.5;q.outer_strength=4;q.outer_offset_mode=1;q.inner_offset_mode=1;
 q.repeat_border=TRUE;q.ratio=1;q.quality=5;q.brightness_gain=1;q.noise_variation=25;q.noise_type=3;q.comp_width=w;q.comp_height=h;
 if(OLMRadialBlurTestRenderWorldWithNoiseLayer(&x,&y,&z,&q,depth)!=PF_Err_NONE)return 1;
 q.blur_type=2;if(OLMRadialBlurTestRenderWorldWithNoiseLayer(&x,&y,&z,&q,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 2;
 q.blur_type=1;PF_EffectWorld alias=x;if(OLMRadialBlurTestRenderWorldWithNoiseLayer(&x,&y,&alias,&q,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 3;
 return 0;
}}
int main(int c,char**v){{int w=atoi(v[1]),h=atoi(v[2]);if(one<PF_Pixel8>(8,w,h))return 1;if(one<PF_Pixel16>(16,w,h))return 2;if(one<PF_PixelFloat>(32,w,h))return 3;return 0;}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        build = subprocess.run([
            "clang++", "-std=c++17", "-arch", "arm64", "-O1", "-g",
            "-fno-omit-frame-pointer", "-fsanitize=address,undefined", "-fno-fast-math",
            "-ffp-contract=off", "-ffunction-sections", "-fdata-sections",
            "-DOLM_RADIALBLUR_TEST_SEAM", "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe),
        ], cwd=ROOT, text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0:halt_on_error=1",
                   UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
        for geometry in ((17, 11), (1920, 1080)):
            run = subprocess.run([str(exe), *map(str, geometry)], cwd=ROOT, env=env,
                                 text=True, capture_output=True, timeout=180)
            assert run.returncode == 0, f"{geometry}: {run.stderr}"

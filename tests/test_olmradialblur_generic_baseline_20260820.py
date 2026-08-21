import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def test_generic_baseline_accepts_arbitrary_pixels_geometry_and_padding() -> None:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_generic_baseline_") as name:
        temp = Path(name)
        cpp = temp / "probe.cpp"
        exe = temp / "probe"
        cpp.write_text(f'''#include "{source}"
#include <cstring>
#include <vector>

template <typename P> int run(short depth, int blur_type) {{
  constexpr int W=17,H=11;
  const int tight=W*(int)sizeof(P), padded=tight+3*(int)sizeof(P);
  std::vector<unsigned char> ib((size_t)padded*H,0xa5), ob((size_t)padded*H,0x5a);
  PF_EffectWorld iw{{}},ow{{}};
  iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=padded;iw.width=W;iw.height=H;
  ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=padded;ow.width=W;ow.height=H;
  for(int y=0;y<H;++y) for(int x=0;x<W;++x) {{
    P *p=reinterpret_cast<P *>(ib.data()+(size_t)y*padded)+x;
    std::memset(p,0,sizeof(P));
    p->alpha=(decltype(p->alpha))((x*13+y*7+1)%17+1);
    p->red=(decltype(p->red))((x*5+y*3+2)%19);
    p->green=(decltype(p->green))((x*2+y*11+3)%23);
    p->blue=(decltype(p->blue))((x*7+y*5+4)%29);
    if constexpr(std::is_same<P,PF_PixelFloat>::value){{
      p->alpha/=32.0f;p->red/=32.0f;p->green/=32.0f;p->blue/=32.0f;
    }}
  }}
  OLMRadialBlurInfo i{{}};i.blur_type=blur_type;
  i.center_x=std::is_same<P,PF_Pixel8>::value?W/2.0:W/2;
  i.center_y=std::is_same<P,PF_Pixel8>::value?H/2.0:H/2;
  i.outer_strength=4;i.outer_offset_mode=1;i.inner_offset_mode=1;
  i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;
  i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;
  if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_NONE)return 1;
  bool changed=false;for(int y=0;y<H;++y) for(int x=0;x<W;++x) {{
    const P *a=reinterpret_cast<const P *>(ib.data()+(size_t)y*padded)+x;
    const P *b=reinterpret_cast<const P *>(ob.data()+(size_t)y*padded)+x;
    if(std::memcmp(a,b,sizeof(P))!=0)changed=true;
  }}
  if(!changed)return 2;
  i.center_x=W*.17;i.center_y=H*.83;i.ratio=3.75;i.angle_deg=271.25;
  i.quality=2.5;i.outer_strength=17;
  if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_NONE)return 3;
  i.inner_strength=7;i.outer_edge_fade=25;i.inner_edge_fade=50;
  if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_NONE)return 4;
  if(blur_type==2){{i.outer_offset_mode=2;i.outer_offset=2;i.inner_offset_mode=3;i.inner_offset=4;
    if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_NONE)return 5;}}
	i.outer_offset_mode=1;i.outer_offset=0;i.inner_offset_mode=1;i.inner_offset=0;
	i.inner_strength=0;i.outer_edge_fade=0;i.inner_edge_fade=0;i.quality=5;
	i.noise_variation=25;i.noise_type=1;i.seed=2;i.noise_offset=1;i.thickness=10;
	if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_NONE)return 11;
	i.noise_variation=100;i.noise_type=2;i.seed=1;i.noise_offset=0;i.thickness=3;
	if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_NONE)return 12;
	i.center_x=W/2.0;i.center_y=H/2.0;i.outer_strength=4;i.ratio=1;i.angle_deg=0;i.quality=5;
	i.size_variation=25;i.noise_variation=25;i.noise_type=1;i.seed=1;i.noise_offset=0;i.thickness=10;
	if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_NONE)return 13;
	i.size_variation=100;i.noise_variation=100;i.noise_type=2;
	if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_NONE)return 14;
	i.size_variation=0;
	i.noise_variation=0;i.noise_type=1;
  i.inner_strength=0;
	i.outer_edge_fade=0;i.inner_edge_fade=0;i.outer_offset_mode=1;i.outer_offset=0;i.inner_offset_mode=1;i.inner_offset=0;
	i.ratio=.5;if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 6;i.ratio=1;
  i.quality=5.01;if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 6;i.quality=1;
  i.outer_strength=65;if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 7;i.outer_strength=1;
  i.center_x=-.01;if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 8;i.center_x=1;
  i.angle_deg=360.01;if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 9;
	i.angle_deg=0;i.noise_variation=.01;if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 10;
  return 0;
}}
template <typename P> int malformed(short depth) {{
  constexpr int W=17,H=11;const int rb=W*(int)sizeof(P)+4*(int)sizeof(P);
  std::vector<unsigned char> a((size_t)rb*H+8,0),b((size_t)rb*H+8,0x5a),before=b;
  PF_EffectWorld x{{}},y{{}};x.data=(PF_PixelPtr)a.data();x.rowbytes=rb;x.width=W;x.height=H;
  y.data=(PF_PixelPtr)b.data();y.rowbytes=rb;y.width=W;y.height=H;
  OLMRadialBlurInfo q{{}};q.blur_type=1;q.center_x=8;q.center_y=5;q.outer_strength=4;
  q.outer_offset_mode=1;q.inner_offset_mode=1;q.repeat_border=TRUE;q.ratio=1;q.quality=5;
  q.brightness_gain=1;q.noise_type=1;q.seed=1;q.thickness=10;q.comp_width=W;q.comp_height=H;
  x.rowbytes=0;if(OLMRadialBlurTestRenderWorld(&x,&y,&q,depth)!=PF_Err_BAD_CALLBACK_PARAM||b!=before)return 1;
  x.rowbytes=rb;y.rowbytes=-rb;if(OLMRadialBlurTestRenderWorld(&x,&y,&q,depth)!=PF_Err_BAD_CALLBACK_PARAM||b!=before)return 2;
  y.rowbytes=rb;
  if(alignof(P)>1){{x.rowbytes=rb-1;if(OLMRadialBlurTestRenderWorld(&x,&y,&q,depth)!=PF_Err_BAD_CALLBACK_PARAM||b!=before)return 3;
    x.rowbytes=rb;x.data=(PF_PixelPtr)(a.data()+1);if(OLMRadialBlurTestRenderWorld(&x,&y,&q,depth)!=PF_Err_BAD_CALLBACK_PARAM||b!=before)return 4;}}
  x.data=(PF_PixelPtr)a.data();x.rowbytes=rb;
  if constexpr(std::is_same<P,PF_Pixel16>::value){{
    ((P*)a.data())->red=32769;if(OLMRadialBlurTestRenderWorld(&x,&y,&q,depth)!=PF_Err_BAD_CALLBACK_PARAM||b!=before)return 5;
  }} else if constexpr(std::is_same<P,PF_PixelFloat>::value){{
    const float bad[]={{-0.01f,1.01f,NAN,INFINITY,-INFINITY}};
    for(float value:bad){{((P*)a.data())->red=value;if(OLMRadialBlurTestRenderWorld(&x,&y,&q,depth)!=PF_Err_BAD_CALLBACK_PARAM||b!=before)return 6;}}
  }}
  return 0;
}}
int main(){{
  for(int type=1;type<=2;++type){{
    if(int e=run<PF_Pixel8>(8,type))return 10*type+e;
    if(int e=run<PF_Pixel16>(16,type))return 20*type+e;
    if(int e=run<PF_PixelFloat>(32,type))return 30*type+e;
  }}
  if(int e=malformed<PF_Pixel8>(8))return 100+e;
  if(int e=malformed<PF_Pixel16>(16))return 110+e;
  if(int e=malformed<PF_PixelFloat>(32))return 120+e;
  return 0;
}}
''')
        sdk = subprocess.run(
            ["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True
        ).stdout.strip()
        command = [
            "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-ffunction-sections", "-fdata-sections",
            "-DOLM_RADIALBLUR_TEST_SEAM", "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(cpp), "-Wl,-dead_strip",
            "-framework", "Cocoa", "-o", str(exe),
        ]
        built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert built.returncode == 0, built.stderr
        ran = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
        assert ran.returncode == 0, f"baseline probe returned {ran.returncode}: {ran.stderr}"

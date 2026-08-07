import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def test_typed_inner_geometry_guard_accepts_centered_padded_and_rejects_near_misses() -> None:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_inner_guard_") as name:
        temp = Path(name)
        cpp = temp / "probe.cpp"
        exe = temp / "probe"
        cpp.write_text(f'''#include "{source}"
#include <vector>
template <typename P> PF_Err run(double cx,double cy,double cw,double ch,int irb,int orb,int ow,int oh){{
  constexpr int W=9,H=7;std::vector<unsigned char>ib(4096),ob(4096);
  PF_EffectWorld iw{{}},out{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=irb;iw.width=W;iw.height=H;
  out.data=(PF_PixelPtr)ob.data();out.rowbytes=orb;out.width=ow;out.height=oh;
  OLMRadialBlurInfo i{{}};i.blur_type=2;i.center_x=cx;i.center_y=cy;i.comp_width=cw;i.comp_height=ch;
  i.outer_offset_mode=1;i.inner_strength=3;i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;
  i.brightness_gain=1;i.noise_type=1;i.seed=1;i.thickness=10;
  return RenderRotationTyped<P>(&iw,&out,i);
}}
int main(){{
  if(run<PF_Pixel16>(4,3,9,7,80,88,9,7)!=PF_Err_NONE)return 1;
  if(run<PF_PixelFloat>(4,3,9,7,160,176,9,7)!=PF_Err_NONE)return 2;
  if(run<PF_Pixel16>(4.5,3,9,7,80,88,9,7)!=PF_Err_BAD_CALLBACK_PARAM)return 3;
  if(run<PF_PixelFloat>(4,3,8,7,160,176,9,7)!=PF_Err_BAD_CALLBACK_PARAM)return 4;
  if(run<PF_Pixel16>(4,3,9,7,71,88,9,7)!=PF_Err_BAD_CALLBACK_PARAM)return 5;
  if(run<PF_PixelFloat>(4,3,9,7,160,176,8,7)!=PF_Err_BAD_CALLBACK_PARAM)return 6;
  return 0;
}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        command = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
                   "-ffp-contract=off", "-ffunction-sections", "-fdata-sections",
                   "-isysroot", sdk, "-I", str(ROOT / "Headers"),
                   "-I", str(ROOT / "Headers/SP"), "-I", str(ROOT / "Util"),
                   "-I", str(ROOT / "Resources"), str(cpp), "-Wl,-dead_strip",
                   "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        assert built.returncode == 0, built.stderr
        ran = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
        assert ran.returncode == 0, f"guard probe returned {ran.returncode}: {ran.stderr}"

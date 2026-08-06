#!/usr/bin/env python3
"""Production RenderWorld must reject unsupported RadialBlur branches."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def main() -> int:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="olmradial-fail-closed-") as td_raw:
        td = Path(td_raw)
        cpp = td / "probe.cpp"
        exe = td / "probe"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <array>
#include <cstring>

template <typename PixelT> int run(short depth) {{
  constexpr int W=3,H=2,RB=W*sizeof(PixelT)+7;
  std::array<unsigned char,RB*H> in{{}},out{{}};
  for(size_t n=0;n<in.size();++n) in[n]=(unsigned char)(n*17+3);
  out.fill(0xcd); const auto before=out;
  PF_EffectWorld iw{{}},ow{{}}; iw.data=(PF_PixelPtr)in.data(); iw.rowbytes=RB; iw.width=W; iw.height=H;
  ow.data=(PF_PixelPtr)out.data(); ow.rowbytes=RB; ow.width=W; ow.height=H;
  OLMRadialBlurInfo i{{}}; i.center_x=1;i.center_y=1;i.outer_strength=4;i.outer_offset_mode=1;
  i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;
  i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;
  i.blur_type=1;i.inner_strength=1;
  if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM||out!=before)return 10;
  i.inner_strength=0;i.noise_variation=1;
  if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM||out!=before)return 11;
  i.blur_type=2;i.noise_variation=0;i.inner_strength=1;
  if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM||out!=before)return 12;
  i.inner_strength=0;i.noise_variation=1;
  if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM||out!=before)return 13;
  i.noise_variation=0;i.size_variation=1;
  if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,depth)!=PF_Err_BAD_CALLBACK_PARAM||out!=before)return 14;
  return 0;
}}
int main() {{ if(run<PF_Pixel8>(8))return 1;if(run<PF_Pixel16>(16))return 2;if(run<PF_PixelFloat>(32))return 3;return 0; }}
''', encoding="utf-8")
        sdk = subprocess.check_output(["xcrun", "--show-sdk-path"], text=True).strip()
        cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off",
               "-ffunction-sections", "-fdata-sections", "-isysroot", sdk,
               "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
               "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
               str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if built.returncode:
            raise AssertionError(built.stderr)
        subprocess.run([str(exe)], cwd=ROOT, check=True)
    production = SOURCE.read_text(encoding="utf-8")
    assert "CopyWorld<PixelT>(input, output);" not in production[production.index("static PF_Err RenderZoomTyped"):production.index("static PF_Err RenderZoom8")]
    print("PASS_OLMRADIALBLUR_UNSUPPORTED_VARIATION_FAIL_CLOSED_20260806 depths=3 cases=5 output_untouched=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

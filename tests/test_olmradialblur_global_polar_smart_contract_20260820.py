
from pathlib import Path as _HarnessPath
_UCRT_CXX = str(_HarnessPath(__file__).resolve().parents[1] / "tools/ucrt_cxx.py")
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def test_smart_request_and_checkout_rectangles_are_preserved() -> None:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_global_smart_") as name:
        temp = Path(name)
        cpp, exe = temp / "probe.cpp", temp / "probe"
        cpp.write_text(f'''#include "{source}"
static PF_LRect supplied;
static PF_Err checkout(PF_ProgPtr,A_long slot,A_long,A_long,A_u_long,PF_ParamDef *p){{
 *p={{}};if(slot==OLMRADIALBLUR_NOISE_TYPE)p->u.pd.value=1;return 0;
}}
static PF_Err checkin(PF_ProgPtr,PF_ParamDef*){{return 0;}}
static PF_Err layer(PF_ProgPtr,PF_ParamIndex,A_long,const PF_RenderRequest *r,
 A_long,A_long,A_u_long,PF_CheckoutResult *out){{
 if(r->rect.left!=3||r->rect.top!=2||r->rect.right!=8||r->rect.bottom!=7||
    !r->preserve_rgb_of_zero_alpha)return 123;
 *out={{}};out->result_rect=supplied;out->max_result_rect=supplied;
 out->ref_width=17;out->ref_height=11;return 0;
}}
int main(){{
 PF_InData in{{}};in.width=17;in.height=11;in.downsample_x={{1,2}};in.downsample_y={{1,3}};
 in.inter.checkout_param=checkout;in.inter.checkin_param=checkin;
 PF_PreRenderInput pi{{}};pi.output_request.rect={{3,2,8,7}};
 PF_PreRenderCallbacks cb{{}};cb.checkout_layer=layer;
 for(int expanded=0;expanded<2;++expanded){{
  supplied=expanded?PF_LRect{{-2,-1,19,12}}:PF_LRect{{3,2,8,7}};
  PF_PreRenderOutput po{{}};PF_PreRenderExtra extra{{&pi,&po,&cb}};
  if(SmartPreRender(&in,nullptr,&extra))return 1;
  if(std::memcmp(&po.result_rect,&supplied,sizeof(supplied))||
     std::memcmp(&po.max_result_rect,&supplied,sizeof(supplied)))return 2;
  if(!po.pre_render_data||!po.delete_pre_render_data_func)return 3;
  po.delete_pre_render_data_func(po.pre_render_data);
 }}
 return 0;
}}

''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        build = subprocess.run([
            _UCRT_CXX, "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
            "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk,
            "-I", str(ROOT / "Headers"), "-I", str(ROOT / "Headers/SP"),
            "-I", str(ROOT / "Util"), "-I", str(ROOT / "Resources"),
            str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe),
        ], cwd=ROOT, text=True, capture_output=True)
        assert build.returncode == 0, build.stderr
        run = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
        assert run.returncode == 0, run.stderr


def test_smart_lifecycle_advertises_extra_pixels_and_preserves_cleanup() -> None:
    text = SOURCE.read_text()
    assert "PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS" in text
    assert "extra->output->result_rect = in_result.result_rect" in text
    assert "extra->output->max_result_rect = in_result.max_result_rect" in text
    assert "smartrender-partial-checkout" not in text
    assert text.index("if (noise_checked_out)") < text.index("if (input_checked_out)")
    assert "render_complete = err == PF_Err_NONE" in text
    assert "staged_output.assign(active_row_bytes * height, 0)" in text
    assert "staged_world.rowbytes = static_cast<A_long>(active_row_bytes)" in text
    assert "input_format != expected_format || output_format != expected_format" in text
    assert "(noise_world && noise_format != expected_format)" in text

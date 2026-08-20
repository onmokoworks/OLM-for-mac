import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"


def test_global_polar_request_normalizes_to_full_frame_and_rejects_tiles() -> None:
    source = str(SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_global_smart_") as name:
        temp = Path(name)
        cpp, exe = temp / "probe.cpp", temp / "probe"
        cpp.write_text(f'''#include "{source}"
#include <vector>
int main(){{
 PF_InData in{{}};in.width=17;in.height=11;PF_RenderRequest request{{}};
 request.rect.left=3;request.rect.top=2;request.rect.right=8;request.rect.bottom=7;
 PF_LRect full{{}};if(!NormalizeGlobalPolarRenderRequest(&in,&request,&full))return 1;
 if(full.left||full.top||full.right!=17||full.bottom!=11)return 2;
 if(request.rect.left||request.rect.top||request.rect.right!=17||request.rect.bottom!=11)return 3;
 if(request.preserve_rgb_of_zero_alpha==FALSE)return 4;
 std::vector<unsigned char> storage(17*11*4);PF_EffectWorld world{{}};
 world.data=(PF_PixelPtr)storage.data();world.width=17;world.height=11;world.rowbytes=17*4;
 if(!IsGlobalPolarFullFrameWorld(&world,full))return 5;
 world.width=8;if(IsGlobalPolarFullFrameWorld(&world,full))return 6;
 world.width=17;world.height=7;if(IsGlobalPolarFullFrameWorld(&world,full))return 7;
	world.height=11;world.origin_x=1;if(IsGlobalPolarFullFrameWorld(&world,full))return 8;
	world.origin_x=0;world.origin_y=-1;if(IsGlobalPolarFullFrameWorld(&world,full))return 9;
	world.origin_y=0;world.extent_hint.left=5;world.extent_hint.top=4;
	world.extent_hint.right=9;world.extent_hint.bottom=8;
	if(!IsGlobalPolarFullFrameWorld(&world,full))return 10;
 return 0;
}}
''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        build = subprocess.run([
            "clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math",
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
    assert "extra->output->result_rect = full_frame_rect" in text
    assert "IsGlobalPolarFullFrameWorld(input_world, pre->full_frame_rect)" in text
    assert "IsGlobalPolarFullFrameWorld(output_world, pre->full_frame_rect)" in text
    assert text.index("if (noise_checked_out)") < text.index("if (input_checked_out)")
    assert "render_complete = err == PF_Err_NONE" in text

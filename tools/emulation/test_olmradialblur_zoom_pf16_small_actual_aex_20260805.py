#!/usr/bin/env python3
"""PF16 Zoom small-frame actual-AEX/production fixture."""

import json, struct, subprocess, tempfile
from pathlib import Path

import test_olmradialblur_rotation_pf16_small_actual_aex_20260805 as fixture
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RCX

fixture.FIXTURE = fixture.ROOT / "refs/fixtures/olmradialblur_zoom_pf16_small_20260805"
fixture.REPORT = fixture.ROOT / "refs/conformance/olmradialblur_zoom_pf16_small_actual_aex_20260805.json"
fixture.EXPECTED = {
    "source_pf16": ("d059727f9096038fea75037a9ba49b82f99c9dd84fd74b15fb11b09f72ca6f85", "5a57d8c8f898bfc576ba38654a81eccf47635c5c30314d59c7c86e8a8ab29f55"),
    "pre_blur": ("27c95680ec8f1d897eeddcd456456bfad1ae1406c121e7f39a6a1e9863d72dc0", "25ea86099c1168b122dba225079c1708b3e67695ac7613ca4d72b47cbf03ed5a"),
    "post_blur": ("d85a97a70daaab76fb339bcb21b31125e88b87c076bbe5005b1216e8374140ab", "85503846b2a43c3abc21102cec5108ee9c30b11e4efeeeb96295d4099959a25c"),
    "output": ("0b0bff1ccc6023d1583775165dde69dd2d0b0f97e7af946062f737ab6fc893aa", "7ac84c2629e7a7ae4dc1865583906f829903b0bbf0ad51b2a3cb819f408ab096"),
}

ZOOM_ENTRY = 0x1800056F0
ZOOM_COLLAPSE = 0x180005C9F
ZOOM_RETURN = 0x180007302
OUTER_STRENGTH = 4
OUTER_OFFSET_MODE = 1
OUTER_OFFSET = 0
INNER_STRENGTH = 0
NOISE_VARIATION = 0.0
CENTER_X = 4.0
CENTER_Y = 3.0
KIND = "olmradialblur_zoom_pf16_small_actual_aex_20260805"
SCOPE = "independent PF16 Zoom outer-only Strength 4, mode 1/offset 0, padded 9x7; no PF32/PF8 quantization reuse or AE-host claim"
PIXEL_CPP = "PF_Pixel16"
PIXEL_BYTES = 8
USE_RENDER_WORLD_FINAL = False
RENDER_WORLD_BITDEPTH = 16


def actual_aex():
    params = fixture.m4.load_case0010_params()
    params.update({
        "Blur Type": 1, "Center": (CENTER_X, CENTER_Y), "Quality": 5.0,
        "Outer Strength": OUTER_STRENGTH, "Outer Offset Mode": OUTER_OFFSET_MODE, "Outer Offset": OUTER_OFFSET,
        "Inner Strength": INNER_STRENGTH, "Noise Variation": NOISE_VARIATION,
        "Brightness Gain": 1.0,
    })
    loader = fixture.AexLoader(str(fixture.m4.AEX_PATH), fast=True)
    loader.register_libm_impls(max_threads=1)
    sp = fixture.m4.build_host_suites(loader)
    render_ctx = fixture.m4.build_render_context(loader, sp)
    iw, _ = fixture.build_world(loader, fixture.source_frame())
    ow, output_data = fixture.build_world(loader, fixture.source_frame(True))
    param_ctx = fixture.m4.build_param_block(loader)
    fixture.m4.install_reader_detours(loader, params)
    captured = {}

    def entry(ld, _address, _size):
        captured["work"] = ld.uc.reg_read(UC_X86_REG_RCX)

    def collapse(ld, _address, _size):
        if "pre_blur" in captured:
            return
        work = int(captured["work"])
        min_radius = struct.unpack("<i", ld.read_bytes(work + 0x18, 4))[0]
        max_radius = struct.unpack("<i", ld.read_bytes(work + 0x1C, 4))[0]
        angle_step = struct.unpack("<f", ld.read_bytes(work + 0x14, 4))[0]
        radius_count = max_radius - min_radius + 1
        angular_count = int(round(6.283185307179586 / angle_step))
        cells = radius_count * angular_count
        captured["geometry"] = (angular_count, radius_count)
        captured["pre_blur"] = ld.read_bytes(fixture.m4.u64(ld, work + 0x38), cells * 16)

    def zoom_return(ld, _address, _size):
        work = int(captured["work"])
        angular_count, radius_count = captured["geometry"]
        cells = angular_count * radius_count
        captured["post_blur"] = ld.read_bytes(fixture.m4.u64(ld, work + 7 * 8), cells * 16)
        owner_work = ld.uc.reg_read(UC_X86_REG_RBX)
        captured["owner_final_rgba_sha256_witness"] = fixture.sha(
            ld.read_bytes(fixture.m4.u64(ld, owner_work + 0xA0), fixture.W * fixture.H * 16))

    loader.add_code_hook(ZOOM_ENTRY, entry)
    loader.add_code_hook(ZOOM_COLLAPSE, collapse)
    loader.add_code_hook(ZOOM_RETURN, zoom_return)
    loader.call_function(fixture.m4.FUN_180008690, int_args=[0, 0, 0, param_ctx, render_ctx], max_instructions=5_000_000)
    loader.call_function(fixture.OWNER, int_args=[render_ctx, 0, iw, ow, param_ctx], max_instructions=500_000_000)
    captured["output"] = loader.read_bytes(output_data, fixture.ROWBYTES * fixture.H)
    angular_count, radius_count = captured.pop("geometry")
    captured["geometry"] = struct.pack("<II", angular_count, radius_count)
    captured.pop("work", None)
    # Keep the owner float-plane identity in the report metadata rather than
    # pretending production exposed the same internal buffer.
    captured.pop("owner_final_rgba_sha256_witness", None)
    return captured


def mac_production(expected):
    angular_count, radius_count = struct.unpack("<II", expected["geometry"])
    cells = angular_count * radius_count
    source = str(fixture.SOURCE).replace("\\", "\\\\").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="radial_zoom_pf16_small_") as td_raw:
        td = Path(td_raw)
        inp = td / "in.bin"
        inp.write_bytes(fixture.source_frame())
        cpp, exe = td / "probe.cpp", td / "probe"
        cpp.write_text(f'''#define OLM_RADIALBLUR_TEST_SEAM 1
#include "{source}"
#include <fstream>
#include <vector>
int main(int argc,char**argv){{constexpr int W={fixture.W},H={fixture.H},RB={fixture.ROWBYTES},C={cells};
std::vector<unsigned char> ib(RB*H),ob(RB*H);std::ifstream(argv[1],std::ios::binary).read((char*)ib.data(),ib.size());
for(int y=0;y<H;y++)for(int x=0;x<RB-W*{PIXEL_BYTES};x++)ob[y*RB+W*{PIXEL_BYTES}+x]=(unsigned char)(0xa0+y);
PF_EffectWorld iw{{}},ow{{}};iw.data=(PF_PixelPtr)ib.data();iw.rowbytes=RB;iw.width=W;iw.height=H;ow.data=(PF_PixelPtr)ob.data();ow.rowbytes=RB;ow.width=W;ow.height=H;
std::vector<float> pre(C*4),post(C*4);RadialBlurTestPolarCapture cap{{}};cap.pre_blur_rgba=pre.data();cap.post_blur_rgba=post.data();cap.capacity_floats=C*4;
OLMRadialBlurInfo i{{}};i.blur_type=1;i.center_x={CENTER_X};i.center_y={CENTER_Y};i.outer_strength={OUTER_STRENGTH};i.outer_offset_mode={OUTER_OFFSET_MODE};i.outer_offset={OUTER_OFFSET};i.inner_strength={INNER_STRENGTH};i.inner_offset_mode=1;i.repeat_border=TRUE;i.ratio=1;i.quality=5;i.brightness_gain=1;i.noise_variation={NOISE_VARIATION};i.noise_type=1;i.seed=1;i.thickness=10;i.comp_width=W;i.comp_height=H;
auto e=RenderZoomTyped<{PIXEL_CPP}>(&iw,&ow,i,&cap);if(e||cap.written_floats!=C*4)return 3;
if ({str(USE_RENDER_WORLD_FINAL).lower()}) {{
for(int y=0;y<H;y++)for(int x=0;x<RB-W*{PIXEL_BYTES};x++)ob[y*RB+W*{PIXEL_BYTES}+x]=(unsigned char)(0xa0+y);
if(OLMRadialBlurTestRenderWorld(&iw,&ow,&i,{RENDER_WORLD_BITDEPTH}))return 4;
}}
std::ofstream(argv[2],std::ios::binary).write((char*)ob.data(),ob.size());std::ofstream(argv[3],std::ios::binary).write((char*)pre.data(),pre.size()*4);std::ofstream(argv[4],std::ios::binary).write((char*)post.data(),post.size()*4);
}}''')
        sdk = subprocess.run(["xcrun", "--show-sdk-path"], text=True, capture_output=True, check=True).stdout.strip()
        cmd = ["clang++", "-std=c++17", "-arch", "arm64", "-O2", "-fno-fast-math", "-ffp-contract=off", "-ffunction-sections", "-fdata-sections", "-isysroot", sdk, "-I", str(fixture.ROOT/"Headers"), "-I", str(fixture.ROOT/"Headers/SP"), "-I", str(fixture.ROOT/"Util"), "-I", str(fixture.ROOT/"Resources"), str(cpp), "-Wl,-dead_strip", "-framework", "Cocoa", "-o", str(exe)]
        built = subprocess.run(cmd, cwd=fixture.ROOT, capture_output=True, text=True)
        if built.returncode:
            raise AssertionError(built.stderr)
        output, pre, post = td/"output.bin", td/"pre.bin", td/"post.bin"
        subprocess.run([str(exe), str(inp), str(output), str(pre), str(post)], cwd=fixture.ROOT, check=True)
        return {"output": output.read_bytes(), "pre_blur": pre.read_bytes(), "post_blur": post.read_bytes()}


fixture.actual_aex = actual_aex
fixture.mac_production = mac_production


def main():
    code = fixture.main()
    report = json.loads(fixture.REPORT.read_text())
    report["kind"] = KIND
    report["scope"] = SCOPE
    report["aex"]["zoom_core"] = "0x1800056f0"
    report["parameter_branch"] = {"blur_type": 1, "outer_strength": OUTER_STRENGTH, "outer_offset_mode": OUTER_OFFSET_MODE, "outer_offset": OUTER_OFFSET, "inner_strength": 0}
    report["production_change_required"] = False
    report["universal_reinstall_required"] = False
    report["exact_boundary"] = {
        "actual_aex_core": "FUN_1800056f0",
        "typed_owner": "FUN_180006d10",
        "typed_writer": "FUN_180017440",
        "compared": ["pre_blur_float32_plane", "post_blur_float32_plane", "PF16 output bytes", "row padding"],
        "internal_owner_final_float_plane": "observed by hook but excluded because the production seam does not expose an equivalent buffer; final PF16 bytes independently compare exact",
    }
    report["non_overlap"] = {
        "existing_case0009_pf32": False,
        "reason": "This case supplies an independent PF_Pixel16 source and exercises the PF16 truncate writer on a reduced padded frame.",
    }
    fixture.REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

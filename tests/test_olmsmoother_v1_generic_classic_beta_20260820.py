from __future__ import annotations

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


HARNESS = r"""
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

template <typename P>
static bool run_case(int depth, int width, int height, int input_pad, int output_pad,
                     int tolerance, bool use_key=false) {
    const int active = width * (int)sizeof(P);
    const int in_rb = active + input_pad, out_rb = active + output_pad;
    std::vector<uint8_t> input((size_t)in_rb * height, 0x6d);
    std::vector<uint8_t> first((size_t)out_rb * height, 0xa5);
    std::vector<uint8_t> second((size_t)out_rb * height, 0xa5);
    for (int y = 0; y < height; ++y) for (int x = 0; x < width; ++x) {
        P p{};
        if constexpr (sizeof(P) == 4) {
            p.alpha = 255; p.red = (x * 37 + y * 11) & 255;
            p.green = (x * 13 + y * 53) & 255; p.blue = (x * 71 + y * 7) & 255;
        } else {
            p.alpha = 32768; p.red = (x * 1237 + y * 311) & 32767;
            p.green = (x * 613 + y * 953) & 32767; p.blue = (x * 371 + y * 1707) & 32767;
        }
		if (use_key && ((x == 0 && y == 0) ||
		                (x == width/2 && y == height/2) ||
		                (x == width-1 && y == height-1))) {
			if constexpr (sizeof(P) == 4) {
				p.alpha=255; p.red=17; p.green=29; p.blue=43;
			} else {
				auto widen=[](unsigned v){return (uint16_t)((v*0x8000u+0x80u)/255u);};
				p.alpha=32768;p.red=widen(17);p.green=widen(29);p.blue=widen(43);
			}
		}
        std::memcpy(input.data() + (size_t)y * in_rb + (size_t)x * sizeof(P), &p, sizeof(P));
    }
    const std::vector<uint8_t> original_input = input;
    auto render = [&](std::vector<uint8_t>& output) {
        PF_EffectWorld iw{}, ow{};
        iw.data=input.data(); iw.width=width; iw.height=height; iw.rowbytes=in_rb;
        iw.bitdepth=depth; iw.extent_hint={0,0,width,height};
        ow=iw; ow.data=output.data(); ow.rowbytes=out_rb;
        PF_ParamDef defs[SM_NUM_PARAMS]{}; PF_ParamDef *params[SM_NUM_PARAMS]{};
        for (int i=0;i<SM_NUM_PARAMS;++i) params[i]=defs+i;
        defs[SM_INPUT].u.ld=iw; defs[SM_USE_KEY].u.bd.value=use_key ? 1 : 0;
        defs[SM_KEY_COLOR].u.cd.value={255,17,29,43}; defs[SM_TOLERANCE].u.sd.value=tolerance;
        PF_InData id{}; PF_OutData od{};
        return EffectMain(PF_Cmd_RENDER,&id,&od,params,&ow,nullptr);
    };
    if (render(first) != 0 || render(second) != 0 || first != second ||
        input != original_input) return false;
    for (int y=0;y<height;++y) for (int i=active;i<out_rb;++i)
        if (first[(size_t)y*out_rb+i] != 0xa5) return false;
    return true;
}

static bool arbitrary_keyed_source_accepted() {
    const int w=13,h=9,rb=w*4+8;
    std::vector<uint8_t> input((size_t)rb*h,0x31), output((size_t)rb*h,0xa5);
    PF_EffectWorld iw{},ow{}; iw.data=input.data(); iw.width=w;iw.height=h;iw.rowbytes=rb;
    iw.bitdepth=8;iw.extent_hint={0,0,w,h};ow=iw;ow.data=output.data();
    PF_ParamDef d[SM_NUM_PARAMS]{};PF_ParamDef*p[SM_NUM_PARAMS]{};for(int i=0;i<SM_NUM_PARAMS;++i)p[i]=d+i;
    d[0].u.ld=iw;d[SM_USE_KEY].u.bd.value=1;d[SM_KEY_COLOR].u.cd.value={255,1,2,3};d[SM_TOLERANCE].u.sd.value=6;
    PF_InData id{};PF_OutData od{};
    int err=EffectMain(PF_Cmd_RENDER,&id,&od,p,&ow,nullptr);
    if (err != 0) return false;
    for(int y=0;y<h;++y)for(int x=w*4;x<rb;++x)
        if(output[(size_t)y*rb+x]!=0xa5)return false;
    return true;
}

template <typename P>
static bool tile_compose_is_not_full_frame(int depth, bool use_key) {
    const int width=64,height=36,split=31,pixel=(int)sizeof(P);
    std::vector<uint8_t> input((size_t)width*height*pixel);
    for(int y=0;y<height;++y)for(int x=0;x<width;++x){
        P p{};
        unsigned band=((x+y/3)/5)&1;
        if constexpr(sizeof(P)==4){
            p={255,(uint8_t)(band?220:24),(uint8_t)((x*19+y*7)&255),(uint8_t)(band?31:231)};
            if(use_key && x==split && y%5==0)p={255,17,29,43};
        }else{
            auto w=[](unsigned v){return(uint16_t)((v*0x8000u+0x80u)/255u);};
            p={32768,w(band?220:24),w((x*19+y*7)&255),w(band?31:231)};
            if(use_key && x==split && y%5==0)p={32768,w(17),w(29),w(43)};
        }
        std::memcpy(input.data()+((size_t)y*width+x)*pixel,&p,pixel);
    }
    auto render=[&](const std::vector<uint8_t>& src,int w,int h){
        const int rb=w*pixel+12;
        std::vector<uint8_t> padded_in((size_t)rb*h,0x6d),out((size_t)(rb+8)*h,0xa5);
        for(int y=0;y<h;++y)std::memcpy(padded_in.data()+(size_t)y*rb,src.data()+(size_t)y*w*pixel,(size_t)w*pixel);
        PF_EffectWorld iw{},ow{};iw.data=padded_in.data();iw.width=w;iw.height=h;iw.rowbytes=rb;iw.bitdepth=depth;iw.extent_hint={0,0,w,h};
        ow=iw;ow.data=out.data();ow.rowbytes=rb+8;
        PF_ParamDef d[SM_NUM_PARAMS]{};PF_ParamDef*p[SM_NUM_PARAMS]{};for(int i=0;i<SM_NUM_PARAMS;++i)p[i]=d+i;
        d[0].u.ld=iw;d[SM_USE_KEY].u.bd.value=use_key?1:0;d[SM_KEY_COLOR].u.cd.value={255,17,29,43};d[SM_TOLERANCE].u.sd.value=6;
        PF_InData id{};PF_OutData od{};if(EffectMain(PF_Cmd_RENDER,&id,&od,p,&ow,nullptr)!=0)return std::vector<uint8_t>{};
        std::vector<uint8_t> active((size_t)w*h*pixel);
        for(int y=0;y<h;++y)std::memcpy(active.data()+(size_t)y*w*pixel,out.data()+(size_t)y*(rb+8),(size_t)w*pixel);
        return active;
    };
    auto full=render(input,width,height);if(full.empty())return false;
    std::vector<uint8_t> left((size_t)split*height*pixel),right((size_t)(width-split)*height*pixel);
    for(int y=0;y<height;++y){
        std::memcpy(left.data()+(size_t)y*split*pixel,input.data()+(size_t)y*width*pixel,(size_t)split*pixel);
        std::memcpy(right.data()+(size_t)y*(width-split)*pixel,input.data()+((size_t)y*width+split)*pixel,(size_t)(width-split)*pixel);
    }
    auto lo=render(left,split,height),ro=render(right,width-split,height);if(lo.empty()||ro.empty())return false;
    std::vector<uint8_t> composed((size_t)width*height*pixel);
    for(int y=0;y<height;++y){
        std::memcpy(composed.data()+(size_t)y*width*pixel,lo.data()+(size_t)y*split*pixel,(size_t)split*pixel);
        std::memcpy(composed.data()+((size_t)y*width+split)*pixel,ro.data()+(size_t)y*(width-split)*pixel,(size_t)(width-split)*pixel);
    }
    size_t differing_bytes=0, first=full.size();
    for(size_t i=0;i<full.size();++i)if(full[i]!=composed[i]){if(first==full.size())first=i;++differing_bytes;}
    std::printf("TILE_COUNTEREXAMPLE depth=%d key=%d differing_bytes=%zu first_byte=%zu\n",
                depth,use_key?1:0,differing_bytes,first);
    return differing_bytes != 0;
}

int main(int argc, char **argv) {
    if ((argc == 7 || argc == 8) && (std::strcmp(argv[1], "pf8") == 0 ||
                      std::strcmp(argv[1], "pf16") == 0)) {
        const int width=std::atoi(argv[2]),height=std::atoi(argv[3]);
        const int input_pad=std::atoi(argv[4]),output_pad=std::atoi(argv[5]);
        const int tolerance=std::atoi(argv[6]);
		const bool use_key=argc == 8 && std::strcmp(argv[7],"key") == 0;
		if (std::strcmp(argv[1], "pf8") == 0) {
			if (!run_case<PF_Pixel8>(8,width,height,input_pad,output_pad,tolerance,use_key)) return 10;
		} else if (!run_case<PF_Pixel16>(16,width,height,input_pad,output_pad,tolerance,use_key)) return 11;
		return 0;
    }
    for (int tolerance=0; tolerance<=255; ++tolerance) {
        if (!run_case<PF_Pixel8>(8,13,9,5,17,tolerance)) return 1;
        if (!run_case<PF_Pixel16>(16,19,11,10,26,tolerance)) return 2;
		if (!run_case<PF_Pixel8>(8,13,9,5,17,tolerance,true)) return 6;
		if (!run_case<PF_Pixel16>(16,19,11,10,26,tolerance,true)) return 7;
    }
    if (!run_case<PF_Pixel8>(8,321,181,7,23,0)) return 3;
    if (!run_case<PF_Pixel16>(16,320,180,14,30,255)) return 4;
	if (!run_case<PF_Pixel8>(8,321,181,7,23,0,true)) return 8;
	if (!run_case<PF_Pixel16>(16,320,180,14,30,255,true)) return 9;
	if (!arbitrary_keyed_source_accepted()) return 5;
	if (!tile_compose_is_not_full_frame<PF_Pixel8>(8,false)) return 20;
	if (!tile_compose_is_not_full_frame<PF_Pixel8>(8,true)) return 21;
	if (!tile_compose_is_not_full_frame<PF_Pixel16>(16,false)) return 22;
	if (!tile_compose_is_not_full_frame<PF_Pixel16>(16,true)) return 23;
    return 0;
}
"""


class GenericClassicBeta(unittest.TestCase):
    def compile_and_run(self, flags: list[str], args: list[str]) -> None:
        with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-beta-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(textwrap.dedent(HARNESS))
            build = subprocess.run(
                ["clang++", "-std=c++17", *flags, "-I", str(ROOT / "cli/OLMSmoother/shim"),
                 "-I", str(ROOT), str(source), "-o", str(binary)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(binary), *args], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_sanitized_odd_sd_all_tolerances_and_determinism(self) -> None:
        self.compile_and_run(
            ["-O1", "-g", "-fno-omit-frame-pointer", "-fsanitize=address,undefined"], [])

    def test_optimized_sd_hd_determinism(self) -> None:
        self.compile_and_run(["-O2"], ["pf16", "1280", "720", "18", "34", "255"])

    def test_optimized_keyed_hd_and_4k_determinism(self) -> None:
        self.compile_and_run(["-O2"], ["pf8", "1920", "1080", "13", "29", "0", "key"])
        self.compile_and_run(["-O2"], ["pf16", "3840", "2160", "18", "34", "255", "key"])


if __name__ == "__main__":
    unittest.main()

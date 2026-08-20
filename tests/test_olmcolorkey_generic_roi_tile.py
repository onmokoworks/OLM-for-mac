from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "tools/emulation/test_olmcolorkey_mac_smartrender_adapter_20260717.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location("_olmck_roi_adapter", ADAPTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CUSTOM_MAIN = r'''
template<class P> P roi_pixel(int x,int y);
template<> PF_Pixel8 roi_pixel<PF_Pixel8>(int x,int y){if((x+y*3)%11==0)return{211,0,0,0};return{(A_u_char)(80+(x+y)%170),(A_u_char)(1+x),(A_u_char)(2+y),(A_u_char)(3+x+y)};}
template<> PF_Pixel16 roi_pixel<PF_Pixel16>(int x,int y){if((x+y*3)%11==0)return{27119,0,0,0};return{(A_u_short)(10000+x+y),(A_u_short)(1+x),(A_u_short)(2+y),(A_u_short)(3+x+y)};}
template<> PF_PixelFloat roi_pixel<PF_PixelFloat>(int x,int y){if((x+y*3)%11==0)return{.73f,0,0,0};return{.4f,.01f+x*.001f,.02f+y*.001f,.03f+(x+y)*.001f};}
template<class P> bool roi_depth(int depth){
 const int W=23,H=15,OX=10,OY=20,TX=5,TY=4,TW=11,TH=7,ps=sizeof(P);
 const int irb=W*ps+16,frb=W*ps+32,trb=TW*ps+48;
 std::vector<std::uint8_t> ib(irb*H,0xA5),full(frb*H,0xEE),smart(trb*TH,0xCC),classic(trb*TH,0xDD);
 for(int y=0;y<H;y++)for(int x=0;x<W;x++){P p=roi_pixel<P>(x,y);std::memcpy(ib.data()+y*irb+x*ps,&p,ps);}
 PF_EffectWorld in{ib.data(),irb,W,H,(A_short)depth,{0,0,W,H},OX,OY,0};
 PF_EffectWorld fw{full.data(),frb,W,H,(A_short)depth,{0,0,W,H},OX,OY,0};
 PF_EffectWorld sw{smart.data(),trb,TW,TH,(A_short)depth,{TX,TY,TX+TW,TY+TH},OX+TX,OY+TY,0};
 PF_EffectWorld cw{classic.data(),trb,TW,TH,(A_short)depth,{TX,TY,TX+TW,TY+TH},OX+TX,OY+TY,0};
 OLMColorKeyInfo info{};info.color_space=1;info.force_lower_precision=1;info.edge_thin_distance_type=1;info.edge_blur_distance_type=1;info.edge_blur_direction=102;info.number_of_colors=1;info.use_color[0]=true;info.colors8[0]={255,0,0,0};info.colors[0]={1,0,0,0};
 if(RenderWorld(&in,&fw,info,depth))return false;
 g_case=0;State ss{&in,&sw};PF_InData sid{&ss,7,1,24,nullptr};PF_OutData od{};PF_SmartRenderInput si{(A_short)depth,nullptr};PF_SmartRenderCallbacks scb{pixels_checkout,output_checkout,checkin};PF_SmartRenderExtra se{&si,&scb};
 if(EffectMain(PF_Cmd_SMART_RENDER,&sid,&od,nullptr,nullptr,&se))return false;
 PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS]{};PF_ParamDef* params[OLMCOLORKEY_NUM_PARAMS];for(int i=0;i<OLMCOLORKEY_NUM_PARAMS;i++)params[i]=&defs[i];defs[OLMCOLORKEY_INPUT].u.ld=in;defs[OLMCOLORKEY_COLOR_SPACE].u.pd.value=1;defs[OLMCOLORKEY_FORCE_LOWER_PRECISION].u.pd.value=1;defs[OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE].u.pd.value=1;defs[OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE].u.pd.value=1;defs[OLMCOLORKEY_EDGE_BLUR_DIRECTION].u.pd.value=2;defs[OLMCOLORKEY_NUMBER_OF_COLORS].u.sd.value=1;defs[OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_USE_COLOR].u.bd.value=true;defs[OLMCOLORKEY_COLOR_FIRST+COLOR_OFFSET_COLOR].u.cd.value={255,0,0,0};
 PF_InData cid{nullptr,7,1,24,nullptr};if(Render(&cid,&od,params,&cw))return false;
 for(int y=0;y<TH;y++){const auto* expected=full.data()+(y+TY)*frb+TX*ps;if(std::memcmp(expected,smart.data()+y*trb,TW*ps)||std::memcmp(expected,classic.data()+y*trb,TW*ps))return false;for(int i=TW*ps;i<trb;i++)if(smart[y*trb+i]!=0xCC||classic[y*trb+i]!=0xDD)return false;}
 OLMColorKeyInfo edge=info;edge.edge_thin_amount=1;if(IsPublicAdmission<P>(&in,&sw,edge))return false;edge=info;edge.edge_blur_amount=1;edge.edge_blur_distance_type=1;edge.edge_blur_direction=101;if(IsPublicAdmission<P>(&in,&sw,edge))return false;
 return true;
}
int main(){g_color_suite=g_color_suite_instance;g_ansi_suite=g_ansi_suite_instance;bool ok=roi_depth<PF_Pixel8>(8)&&roi_depth<PF_Pixel16>(16)&&roi_depth<PF_PixelFloat>(32);std::fprintf(stderr,"GENERIC_ROI_TILE pass=%d depths=3 classic=1 smart=1\n",ok?1:0);return ok?0:1;}
'''


def test_nonzero_origin_roi_tile_classic_smart_parity() -> None:
    adapter = _load_adapter()
    with tempfile.TemporaryDirectory(prefix="olmck-roi-tile.") as raw:
        directory = Path(raw)
        adapter.compile_probe(directory)
        source = directory / "olmcolorkey_mac_smartrender_adapter_probe.cpp"
        text = source.read_text()
        text = text.replace(
            "struct PF_EffectWorld { PF_PixelPtr data; A_long rowbytes, width, height; A_short bitdepth; PF_LRect extent_hint; A_long dephault; };",
            "struct PF_EffectWorld { PF_PixelPtr data; A_long rowbytes, width, height; A_short bitdepth; PF_LRect extent_hint; A_long origin_x, origin_y, dephault; };",
        )
        text = text.replace(
            "#define OLMCOLORKEY_HOSTLESS_RENDER_HARNESS 1",
            "#define OLMCOLORKEY_HOSTLESS_RENDER_HARNESS 1\n#define OLMCOLORKEY_HOSTLESS_WORLD_HAS_ORIGIN 1",
        )
        text = text.replace("int main(){", "int legacy_main(){", 1) + CUSTOM_MAIN
        source.write_text(text)
        sdk = subprocess.run(
            ["xcrun", "--show-sdk-path"], capture_output=True, text=True, check=True
        ).stdout.strip()
        executable = directory / "roi"
        subprocess.run([
            "clang++", "-std=c++17", "-arch", "arm64", "-O1",
            "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
            "-isysroot", sdk, "-I", str(directory), str(source),
            "-framework", "Cocoa", "-o", str(executable),
        ], cwd=ROOT, check=True)
        run = subprocess.run(
            [str(executable)], cwd=ROOT, capture_output=True, text=True, check=True
        )
    assert run.stderr.strip() == "GENERIC_ROI_TILE pass=1 depths=3 classic=1 smart=1"

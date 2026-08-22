from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


HARNESS = r"""
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include "mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

static PF_ParamDef params_store[SM_NUM_PARAMS];
static PF_EffectWorld *smart_input_world=nullptr,*smart_output_world=nullptr;
static int layer_calls=0,output_calls=0,param_calls=0,param_checkins=0,layer_checkins=0;
static int param_checkin_fail=-1,param_checkin_ordinal=0,layer_checkin_fail=0;

static PF_Err Layer(PF_ProgPtr,A_long index,PF_EffectWorld **world){
    ++layer_calls;if(index!=SM_INPUT)return 91;*world=smart_input_world;return 0;
}
static PF_Err Output(PF_ProgPtr,PF_EffectWorld **world){++output_calls;*world=smart_output_world;return 0;}
static PF_Err Checkout(A_long index,PF_ParamDef *param){++param_calls;*param=params_store[index];return 0;}
static void Checkin(PF_ParamDef*){++param_checkins;}
static PF_Err CheckinError(PF_ParamDef*){
    int ordinal=param_checkin_ordinal++;return ordinal==param_checkin_fail?95:0;
}
static void LayerCheckin(PF_ProgPtr,A_long index){if(index==SM_INPUT)++layer_checkins;}
static PF_Err LayerCheckinError(PF_ProgPtr,A_long){return layer_checkin_fail;}

template<class P> static void fill(std::vector<uint8_t>& bytes,int rb,int w,int h,bool key){
    for(int y=0;y<h;++y)for(int x=0;x<w;++x){
        P p{};
        if constexpr(sizeof(P)==sizeof(PF_Pixel8)){
            p={255,(uint8_t)((x*37+y*11)&255),(uint8_t)((x*13+y*53)&255),(uint8_t)((x*71+y*7)&255)};
            if(key&&((x+y*3)%17==0))p={255,17,29,43};
        }else{
            auto q=[](unsigned v){return(uint16_t)((v*0x8000u+0x80u)/255u);};
            p={32768,q((x*37+y*11)&255),q((x*13+y*53)&255),q((x*71+y*7)&255)};
            if(key&&((x+y*3)%17==0))p={32768,q(17),q(29),q(43)};
        }
        std::memcpy(bytes.data()+(size_t)y*rb+(size_t)x*sizeof(P),&p,sizeof(P));
    }
}

static void reset_callbacks(){
    layer_calls=output_calls=param_calls=param_checkins=layer_checkins=0;
    param_checkin_fail=-1;param_checkin_ordinal=0;layer_checkin_fail=0;
    g_cli_checkout_param_hook=&Checkout;g_cli_checkin_param_hook=&Checkin;
    g_cli_checkin_param_error_hook=&CheckinError;
    g_olmsmoother_cli_checkin_layer_hook=&LayerCheckin;
    g_olmsmoother_cli_checkin_layer_error_hook=&LayerCheckinError;
}

static int smart(PF_EffectWorld&iw,PF_EffectWorld&ow,int depth){
    smart_input_world=&iw;smart_output_world=&ow;
    PF_SmartRenderCallbacks cb{&Layer,&Output};PF_SmartRenderInput si{(short)depth};
    PF_SmartRenderExtra ex{&si,&cb};PF_InData id{};PF_OutData od{};
    return EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&ex);
}

template<class P> static bool parity(int depth,int w,int h,int in_pad,int classic_pad,int smart_pad,bool key,int tolerance){
    const int active=w*(int)sizeof(P),irb=active+in_pad,crb=active+classic_pad,srb=active+smart_pad;
    std::vector<uint8_t> input((size_t)irb*h,0x6d),classic((size_t)crb*h,0xa5),smart_out((size_t)srb*h,0xa5);
    fill<P>(input,irb,w,h,key);auto original=input;
    PF_EffectWorld iw{},cw{},sw{};iw.data=input.data();iw.width=w;iw.height=h;iw.rowbytes=irb;iw.bitdepth=depth;iw.extent_hint={0,0,w,h};
    cw=iw;cw.data=classic.data();cw.rowbytes=crb;sw=iw;sw.data=smart_out.data();sw.rowbytes=srb;
    PF_ParamDef defs[SM_NUM_PARAMS]{};PF_ParamDef*ptrs[SM_NUM_PARAMS]{};for(int i=0;i<SM_NUM_PARAMS;++i)ptrs[i]=defs+i;
    defs[SM_INPUT].u.ld=iw;defs[SM_USE_KEY].u.bd.value=key?1:0;defs[SM_KEY_COLOR].u.cd.value={255,17,29,43};defs[SM_TOLERANCE].u.sd.value=tolerance;
    PF_InData id{};PF_OutData od{};if(EffectMain(PF_Cmd_RENDER,&id,&od,ptrs,&cw,nullptr)!=0)return false;
    std::memcpy(params_store,defs,sizeof(defs));reset_callbacks();if(smart(iw,sw,depth)!=0)return false;
    if(layer_calls!=1||output_calls!=1||param_calls!=SM_NUM_PARAMS-1||param_checkins!=SM_NUM_PARAMS-1||layer_checkins!=1||input!=original)return false;
    for(int y=0;y<h;++y){
        if(std::memcmp(classic.data()+(size_t)y*crb,smart_out.data()+(size_t)y*srb,active)!=0)return false;
        for(int x=active;x<crb;++x)if(classic[(size_t)y*crb+x]!=0xa5)return false;
        for(int x=active;x<srb;++x)if(smart_out[(size_t)y*srb+x]!=0xa5)return false;
    }
    return true;
}

static bool cleanup_atomic(bool layer_failure){
    const int w=13,h=9,active=w*4,irb=active+5,orb=active+17;
    std::vector<uint8_t> input((size_t)irb*h,0x6d),out((size_t)orb*h,0xa5);fill<PF_Pixel8>(input,irb,w,h,true);
    PF_EffectWorld iw{},ow{};iw.data=input.data();iw.width=w;iw.height=h;iw.rowbytes=irb;iw.bitdepth=8;iw.extent_hint={0,0,w,h};ow=iw;ow.data=out.data();ow.rowbytes=orb;
    std::memset(params_store,0,sizeof(params_store));params_store[SM_INPUT].u.ld=iw;params_store[SM_USE_KEY].u.bd.value=1;params_store[SM_KEY_COLOR].u.cd.value={255,17,29,43};params_store[SM_TOLERANCE].u.sd.value=127;
    reset_callbacks();if(layer_failure)layer_checkin_fail=96;else param_checkin_fail=0;
    const auto before=out;int err=smart(iw,ow,8);
    return err!=0&&out==before&&param_checkins==SM_NUM_PARAMS-1&&layer_checkins==1;
}

static bool windows_oracle_pf16(const char*path,bool key,int tolerance){
    const int w=64,h=36,active=w*(int)sizeof(PF_Pixel16),rb=active+32;
    std::vector<uint8_t> input((size_t)rb*h),classic((size_t)rb*h,0xa5),smart_out((size_t)rb*h,0xa5);
    const unsigned alphas[]={0,1,17,32,63,64,95,127,128,159,191,223,254,255};
    auto q=[](unsigned v){return(uint16_t)((v*0x8000u+0x80u)/255u);};
    for(int y=0;y<h;++y){
        for(int x=0;x<w;++x){
            const bool island=(x==0&&y==0)||(x==w-1&&y==0)||(x==w/2&&y==h/2)||
                              (x==0&&y==h-1)||(x==w-1&&y==h-1);
            unsigned a=255,r=0,g=0,b=0;
            if(island){r=202;g=187;b=230;}
            else{
                if((x+y*3)%11==0)a=alphas[(x*5+y*3)%14];
                if(x<16&&y<16&&a==255)r=g=b=(x*17+y*23)&255;
                else{r=std::min((unsigned)((x*37+y*19+13)&255),a);
                     g=std::min((unsigned)((x*11+y*53+201)&255),a);
                     b=std::min((unsigned)((x*71+y*7+41)&255),a);}
            }
            PF_Pixel16 p{q(a),q(r),q(g),q(b)};
            std::memcpy(input.data()+(size_t)y*rb+(size_t)x*sizeof(p),&p,sizeof(p));
        }
        std::memset(input.data()+(size_t)y*rb+active,0xc0+(y%31),32);
    }
    const auto original=input;
    PF_EffectWorld iw{},cw{},sw{};iw.data=input.data();iw.width=w;iw.height=h;iw.rowbytes=rb;iw.bitdepth=16;iw.extent_hint={0,0,w,h};
    cw=iw;cw.data=classic.data();sw=iw;sw.data=smart_out.data();
    PF_ParamDef defs[SM_NUM_PARAMS]{};PF_ParamDef*ptrs[SM_NUM_PARAMS]{};for(int i=0;i<SM_NUM_PARAMS;++i)ptrs[i]=defs+i;
    defs[SM_INPUT].u.ld=iw;defs[SM_USE_KEY].u.bd.value=key?1:0;defs[SM_KEY_COLOR].u.cd.value={255,202,187,230};defs[SM_TOLERANCE].u.sd.value=tolerance;
    PF_InData id{};PF_OutData od{};if(EffectMain(PF_Cmd_RENDER,&id,&od,ptrs,&cw,nullptr)!=0)return false;
    std::memcpy(params_store,defs,sizeof(defs));reset_callbacks();if(smart(iw,sw,16)!=0)return false;
    if(classic!=smart_out||input!=original||layer_calls!=1||output_calls!=1||
       param_calls!=SM_NUM_PARAMS-1||param_checkins!=SM_NUM_PARAMS-1||layer_checkins!=1)return false;
    std::FILE*f=std::fopen(path,"wb");if(!f)return false;
    const bool wrote=std::fwrite(smart_out.data(),1,smart_out.size(),f)==smart_out.size();
    return std::fclose(f)==0&&wrote;
}

int main(int argc,char**argv){
    if(argc==5&&std::strcmp(argv[1],"oracle-pf16")==0)
        return windows_oracle_pf16(argv[4],std::atoi(argv[2])!=0,std::atoi(argv[3]))?0:30;
    if(argc==3){
        const bool uhd=std::strcmp(argv[1],"uhd")==0,want8=std::strcmp(argv[2],"pf8")==0;
        const int w=uhd?3840:1920,h=uhd?2160:1080;
        if(want8)return parity<PF_Pixel8>(8,w,h,5,13,29,true,127)?0:20;
        return parity<PF_Pixel16>(16,w,h,10,26,42,true,127)?0:21;
    }
    PF_InData id{};PF_OutData od{};if(EffectMain(PF_Cmd_GLOBAL_SETUP,&id,&od,nullptr,nullptr,nullptr)!=0||od.out_flags2!=0x08000400)return 1;
    if(!parity<PF_Pixel8>(8,67,43,5,13,29,false,0))return 2;
    if(!parity<PF_Pixel8>(8,67,43,7,15,31,true,255))return 3;
    if(!parity<PF_Pixel16>(16,65,41,10,26,42,false,37))return 4;
    if(!parity<PF_Pixel16>(16,65,41,14,30,46,true,211))return 5;
    if(!cleanup_atomic(false)||!cleanup_atomic(true))return 6;
    const int w=7,h=5,rb=w*(int)sizeof(PF_PixelFloat)+16;std::vector<uint8_t> in((size_t)rb*h,0x3c),out((size_t)rb*h,0xa5);
    PF_EffectWorld iw{},ow{};iw.data=in.data();iw.width=w;iw.height=h;iw.rowbytes=rb;iw.bitdepth=32;iw.extent_hint={0,0,w,h};ow=iw;ow.data=out.data();
    std::memset(params_store,0,sizeof(params_store));params_store[SM_INPUT].u.ld=iw;params_store[SM_KEY_COLOR].u.cd.value={255,17,29,43};params_store[SM_TOLERANCE].u.sd.value=6;
    reset_callbacks();auto before=out;if(smart(iw,ow,32)==0||out!=before)return 7;
    std::puts("PASS smoother-v1-smart-pf8-pf16");return 0;
}
"""


class SmootherV1SmartBeta(unittest.TestCase):
    def compile_and_run(self, flags: list[str], runs: list[list[str]] | None = None) -> None:
        with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-smart-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(textwrap.dedent(HARNESS))
            build = subprocess.run(
                ["clang++", "-std=c++17", *flags, "-I", str(ROOT / "cli/OLMSmoother/shim"),
                 "-I", str(ROOT), str(source), "-o", str(binary)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            for args in runs or [[]]:
                run = subprocess.run([str(binary), *args], cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_optimized_classic_smart_parity_and_cleanup_atomicity(self) -> None:
        self.compile_and_run(["-O2"])

    def test_smart_lane_under_address_and_undefined_sanitizers(self) -> None:
        self.compile_and_run([
            "-O1", "-g", "-fno-omit-frame-pointer", "-fsanitize=address,undefined",
        ])

    def test_optimized_hd_uhd_classic_smart_parity(self) -> None:
        self.compile_and_run(["-O2"], [
            ["hd", "pf8"], ["hd", "pf16"],
            ["uhd", "pf8"], ["uhd", "pf16"],
        ])

    def test_current_classic_and_smart_match_windows_pf16_practical_oracle(self) -> None:
        report_path = ROOT / "refs/conformance/olmsmoother_v1_pf16_practical_geometry_actual_aex_20260812.json"
        report = json.loads(report_path.read_text())
        self.assertEqual(report["status"], "exact")
        self.assertEqual(
            report["actual_aex_sha256"],
            "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82",
        )
        expected = {
            (row["use_key"], row["tolerance"]): (row["raw_sha256"], row["active_sha256"])
            for row in report["practical_cases"]
        }
        self.assertEqual(set(expected), {(0, 6), (0, 127), (1, 6), (1, 127)})
        with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-windows-smart-") as tmp:
            source = Path(tmp) / "probe.cpp"
            binary = Path(tmp) / "probe"
            source.write_text(textwrap.dedent(HARNESS))
            build = subprocess.run(
                ["clang++", "-std=c++17", "-O2", "-I", str(ROOT / "cli/OLMSmoother/shim"),
                 "-I", str(ROOT), str(source), "-o", str(binary)],
                cwd=ROOT, text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            for (use_key, tolerance), (raw_sha, active_sha) in expected.items():
                output = Path(tmp) / f"oracle-{use_key}-{tolerance}.bin"
                run = subprocess.run(
                    [str(binary), "oracle-pf16", str(use_key), str(tolerance), str(output)],
                    cwd=ROOT, text=True, capture_output=True,
                )
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                payload = output.read_bytes()
                self.assertEqual(len(payload), 544 * 36)
                active = b"".join(payload[y * 544:y * 544 + 512] for y in range(36))
                self.assertEqual(hashlib.sha256(payload).hexdigest(), raw_sha)
                self.assertEqual(hashlib.sha256(active).hexdigest(), active_sha)


if __name__ == "__main__":
    unittest.main()

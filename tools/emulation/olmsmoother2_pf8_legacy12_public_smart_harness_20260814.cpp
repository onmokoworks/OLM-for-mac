#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <dlfcn.h>
#include <fstream>
#include <string>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#define EffectMain SourceBuiltOLMSmoother2EffectMain
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
#undef EffectMain

namespace {
constexpr int kWidth = 1920, kHeight = 1080, kRowbytes = kWidth * 4;
constexpr size_t kBytes = static_cast<size_t>(kRowbytes) * kHeight;
constexpr const char *kInputSha = "1c15f67a9d0818a0a0266971720e855acac70a89e2690ccbedf5e142fc1c64f3";
using Effect = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef *[], PF_LayerDef *, void *);

struct Tuple {
    const char *name, *output_sha;
    int enable, invert, smooth, range, extra, version, gamma_mode, gamma_count, palette;
    double gamma;
};
const Tuple kTuples[] = {
    {"case01","93f6b8dc4c258adf94f2aada8454394b58f5388128e46c980769490998b8b43b",0,0,100,2,0,2,GAMMA_NONE,1,0,2.40000009536743},
    {"case02","04a1eb8eed6e5b39b700efe557e4cdc17a6a4f6d7d4814108b20addbc8274988",1,1,100,2,0,2,GAMMA_NONE,1,0,2.40000009536743},
    {"case03","c9aae14a55d447faaa79d2c28331f5d91cb040eb0ebf5aebf87ba631bcbf0755",1,0,0,2,0,2,GAMMA_NONE,1,0,2.40000009536743},
    {"case04","cdcf1c120b7e7f59b7d73ae1b46e6f8fe3ffc809a53aa2b0e6a7ffb1d7e38b64",1,0,100,2,100,2,GAMMA_NONE,1,0,2.40000009536743},
    {"case05","8aedc3f58fb52f6fb374f55af634564ce98978002f9f492895daae87327acbc2",1,0,100,100,100,2,GAMMA_NONE,1,0,2.40000009536743},
    {"case06","d62bebdf630f08aef989229fb950efe79c038c4cc9efef5cd3d27fdccd19248f",1,0,100,0,100,2,GAMMA_NONE,1,0,2.40000009536743},
    {"case07","c8e87d45a6d2fed12e57a2e32880048ba70150d7e7337a9936471228c240902c",1,0,100,26,40,2,GAMMA_NONE,1,0,2.40000009536743},
    {"case08","9406ce4d6c5e50e3be5dc96a6e98a41869976dd797be4fe4b4363ec263230bc0",1,0,29,26,40,2,GAMMA_NONE,1,0,2.40000009536743},
    {"case09","f06b05eb681d29a18765a51d3469cf82f4a90828dd3e29ccc978544acbabc123",1,0,100,26,40,1,GAMMA_NONE,1,0,2.40000009536743},
    {"case10","495248cf85e33b6d73cfbe174bfea8279f10d235beca796a5866bb4ab3915b2e",1,0,100,22,40,2,GAMMA_COLORS_ONLY,3,0,1.36872434616089},
    {"case11","788423e8bf3e1ecdc1032409b9db587cd451285e61a7e2ebe6c1734aa0e22e7d",1,0,100,22,40,2,GAMMA_COLORS_ONLY,5,1,2.16954731941223},
    {"case12","5680e178cc246dc08d42845568f0c5df581e6f1023c7f2573d4cd9028b93b92f",1,0,100,88,40,2,GAMMA_COLORS_ONLY,5,2,2.16954731941223},
};

enum Mode { OK, SOURCE_FIRST, SOURCE_MIDDLE, SOURCE_LAST, GAMMA_NEXT, KEY_ONE,
    PALETTE_ONE, WIDTH_ONE, ROWBYTES_ONE, INPUT_FLAGS_ONE, OUTPUT_FLAGS_ONE,
    ORIGIN_ONE, DOWNSAMPLE_ONE, EXTENT_ONE, FORMAT_ONE, ALIAS, OVERLAP,
    LAYER_ERROR, OUTPUT_ERROR, PARAM_CHECKOUT_ERROR, PARAM_CHECKIN_ERROR,
    WORLD_ERROR, COLOR_ERROR, COLOR_WRONG_SUCCESS };

std::vector<unsigned char> g_source;
PF_ParamDef g_params[SM_NUM_PARAMS];
PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
Mode g_mode = OK;
int g_layer, g_output_calls, g_param_out, g_param_in, g_aw, g_rw, g_ac, g_rc, g_formats, g_colors;
PF_WorldSuite2 g_world_suite{};
PF_ColorParamSuite1 g_color_suite{};

std::string Hex(const unsigned char *data, size_t size) {
    static const char digits[] = "0123456789abcdef";
    std::string result; result.reserve(size * 2);
    for (size_t i=0;i<size;++i) { result.push_back(digits[data[i]>>4]); result.push_back(digits[data[i]&15]); }
    return result;
}
std::string Sha256(const void *data, size_t size) {
    olm::Sha256 sha; sha.update(data,size); unsigned char digest[32]; sha.final(digest); return Hex(digest,32);
}
std::vector<unsigned char> Read(const char *path) {
    std::ifstream stream(path,std::ios::binary);
    return std::vector<unsigned char>(std::istreambuf_iterator<char>(stream),{});
}
void Color(PF_ParamDef &p, unsigned char a, unsigned char r, unsigned char g, unsigned char b) { p.u.cd.value={a,r,g,b}; }
void FillParams(const PF_EffectWorld &world, const Tuple &t) {
    std::memset(g_params,0,sizeof(g_params)); g_params[0].u.ld=world;
    g_params[SM_ENABLE_KEY].u.bd.value=t.enable; g_params[SM_INVERT_KEY].u.bd.value=t.invert;
    Color(g_params[SM_KEY_COLOR],255,255,255,255);
    g_params[SM_SMOOTHNESS].u.sd.value=t.smooth; g_params[SM_SMOOTH_RANGE].u.sd.value=t.range;
    g_params[SM_EXTRA_SMOOTH].u.sd.value=t.extra; g_params[SM_VERSION].u.pd.value=t.version;
    g_params[SM_GAMMA_MODE].u.pd.value=t.gamma_mode; g_params[SM_GAMMA_VALUE].u.fs_d.value=t.gamma;
    g_params[SM_NUM_GAMMA_COLORS].u.sd.value=t.gamma_count;
    for (int i=0;i<NUM_GAMMA_COLORS;++i) {
        const bool red=t.palette==2&&i==0, blue=t.palette!=0&&i==NUM_GAMMA_COLORS-1;
        Color(g_params[SM_GAMMA_COLOR_0+i],255,red?255:0,0,blue?255:0);
    }
}
PF_Err GetFormat(const PF_EffectWorld *, PF_PixelFormat *format) {
    ++g_formats; if(g_mode==WORLD_ERROR)return 71; *format=g_mode==FORMAT_ONE?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB32; return 0;
}
PF_Err GetColor(PF_ProgPtr,const PF_ParamDef *p,PF_PixelFloat *out) {
    ++g_colors; if(g_mode==COLOR_ERROR)return 72;
    out->alpha=p->u.cd.value.alpha/255.f; out->red=p->u.cd.value.red/255.f;
    out->green=p->u.cd.value.green/255.f; out->blue=p->u.cd.value.blue/255.f;
    if(g_mode==COLOR_WRONG_SUCCESS&&g_colors==1)out->red=std::nextafter(out->red,2.f); return 0;
}
SPErr Acquire(const char *name,int32 version,const void **suite) {
    if(!std::strcmp(name,kPFWorldSuite)&&version==kPFWorldSuiteVersion2){++g_aw;g_world_suite.PF_GetPixelFormat=GetFormat;*suite=&g_world_suite;return 0;}
    if(!std::strcmp(name,kPFColorParamSuite)&&version==kPFColorParamSuiteVersion1){++g_ac;g_color_suite.PF_GetFloatingPointColorFromColorDef=GetColor;*suite=&g_color_suite;return 0;}
    return kSPBadParameterError;
}
SPErr Release(const char *name,int32 version) {
    if(!std::strcmp(name,kPFWorldSuite)&&version==kPFWorldSuiteVersion2){++g_rw;return 0;}
    if(!std::strcmp(name,kPFColorParamSuite)&&version==kPFColorParamSuiteVersion1){++g_rc;return 0;}
    return kSPBadParameterError;
}
PF_Err CheckoutParam(PF_ProgPtr,PF_ParamIndex index,A_long,A_long,A_u_long,PF_ParamDef *p){++g_param_out;if(g_mode==PARAM_CHECKOUT_ERROR&&index==SM_GAMMA_VALUE)return 73;*p=g_params[index];return 0;}
PF_Err CheckinParam(PF_ProgPtr,PF_ParamDef*){++g_param_in;return g_mode==PARAM_CHECKIN_ERROR&&g_param_in==1?74:0;}
PF_Err Layer(PF_ProgPtr,A_long index,PF_EffectWorld **w){++g_layer;if(g_mode==LAYER_ERROR)return 75;if(index!=SM_INPUT)return PF_Err_BAD_CALLBACK_PARAM;*w=g_input;return 0;}
PF_Err Output(PF_ProgPtr,PF_EffectWorld **w){++g_output_calls;if(g_mode==OUTPUT_ERROR)return 76;*w=g_output;return 0;}
PF_Err CheckinLayer(PF_ProgPtr,A_long){return 0;}

bool Run(Effect effect,const Tuple &tuple,const char *name,Mode mode) {
    g_mode=mode; std::vector<unsigned char> input=g_source, output(kBytes+64,0xee); unsigned char *dst=output.data()+32;
    if(mode==SOURCE_FIRST)input[0]^=1; if(mode==SOURCE_MIDDLE)input[kBytes/2]^=1; if(mode==SOURCE_LAST)input[kBytes-1]^=1;
    PF_EffectWorld iw{},ow{}; iw.data=(PF_PixelPtr)input.data(); iw.width=kWidth;iw.height=kHeight;iw.rowbytes=kRowbytes;iw.extent_hint={0,0,kWidth,kHeight};iw.world_flags=0;ow=iw;ow.data=(PF_PixelPtr)dst;
    FillParams(iw,tuple);
    if(mode==GAMMA_NEXT)g_params[SM_GAMMA_VALUE].u.fs_d.value=std::nextafter(g_params[SM_GAMMA_VALUE].u.fs_d.value,3.0);
    if(mode==KEY_ONE)--g_params[SM_KEY_COLOR].u.cd.value.blue;
    if(mode==PALETTE_ONE)g_params[SM_GAMMA_COLOR_2].u.cd.value.green=1;
    if(mode==WIDTH_ONE)iw.width=ow.width=kWidth-1; if(mode==ROWBYTES_ONE)iw.rowbytes=ow.rowbytes=kRowbytes+1;
    if(mode==INPUT_FLAGS_ONE)iw.world_flags=PF_WorldFlag_DEEP; if(mode==OUTPUT_FLAGS_ONE)ow.world_flags=PF_WorldFlag_DEEP;
    if(mode==EXTENT_ONE)iw.extent_hint.right=kWidth-1; if(mode==ALIAS)ow.data=iw.data; if(mode==OVERLAP)ow.data=(PF_PixelPtr)(input.data()+4);
    g_input=&iw;g_output=&ow;g_layer=g_output_calls=g_param_out=g_param_in=g_aw=g_rw=g_ac=g_rc=g_formats=g_colors=0;
    SPBasicSuite basic{};basic.AcquireSuite=Acquire;basic.ReleaseSuite=Release;
    PF_InData in{};PF_OutData out{};in.effect_ref=(PF_ProgPtr)1;in.pica_basicP=&basic;in.current_time=7;in.time_step=1;in.time_scale=24;in.downsample_x={1,1};in.downsample_y={1,1};
    if(mode==ORIGIN_ONE)in.output_origin_x=1;if(mode==DOWNSAMPLE_ONE)in.downsample_x.num=2;
    in.inter.checkout_param=CheckoutParam;in.inter.checkin_param=CheckinParam;
    PF_SmartRenderInput si{};si.bitdepth=8;PF_SmartRenderCallbacks cb{};cb.checkout_layer_pixels=Layer;cb.checkout_output=Output;cb.checkin_layer_pixels=CheckinLayer;PF_SmartRenderExtra ex{&si,&cb};
    const auto input_before=input,output_before=output;const PF_EffectWorld iw_before=iw,ow_before=ow;
    PF_Err err=effect(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&ex);
    const bool headers=!std::memcmp(&iw,&iw_before,sizeof(iw))&&!std::memcmp(&ow,&ow_before,sizeof(ow));
    const bool guards=std::all_of(output.begin(),output.begin()+32,[](unsigned char v){return v==0xee;})&&std::all_of(output.end()-32,output.end(),[](unsigned char v){return v==0xee;});
    bool pass;
    if(mode==OK)pass=err==0&&input==input_before&&headers&&guards&&Sha256(dst,kBytes)==tuple.output_sha&&g_layer==1&&g_output_calls==1&&g_param_out==SM_NUM_PARAMS-1&&g_param_in==SM_NUM_PARAMS-1&&g_aw==2&&g_rw==2&&g_ac==1&&g_rc==1&&g_formats==2&&g_colors==6;
    else pass=err!=0&&input==input_before&&headers&&guards&&output==output_before;
    std::printf("CASE %s pass=%d err=%d layer=%d output=%d params=%d/%d worlds=%d/%d colors=%d/%d/%d\n",name,pass,err,g_layer,g_output_calls,g_param_out,g_param_in,g_aw,g_rw,g_ac,g_rc,g_colors);
    return pass;
}
} // namespace

int main(int argc,char **argv){
    if(argc!=2&&argc!=3)return 2;g_source=Read(argv[1]);if(g_source.size()!=kBytes||Sha256(g_source.data(),g_source.size())!=kInputSha)return 3;
    void *handle=nullptr;Effect effect=SourceBuiltOLMSmoother2EffectMain;if(argc==3){handle=dlopen(argv[2],RTLD_NOW|RTLD_LOCAL);if(!handle)return 5;effect=(Effect)dlsym(handle,"EffectMain");if(!effect)return 6;}
    int pass=0,total=0;for(const auto&t:kTuples){++total;if(Run(effect,t,t.name,OK))++pass;++total;std::string n=std::string(t.name)+"_gamma_next";if(Run(effect,t,n.c_str(),GAMMA_NEXT))++pass;}
    const Tuple&t=kTuples[6];struct Row{const char*name;Mode mode;} rows[]={{"source_first",SOURCE_FIRST},{"source_middle",SOURCE_MIDDLE},{"source_last",SOURCE_LAST},{"key_one",KEY_ONE},{"palette_one",PALETTE_ONE},{"width_one",WIDTH_ONE},{"rowbytes_one",ROWBYTES_ONE},{"input_flags_one",INPUT_FLAGS_ONE},{"output_flags_one",OUTPUT_FLAGS_ONE},{"origin_one",ORIGIN_ONE},{"downsample_one",DOWNSAMPLE_ONE},{"extent_one",EXTENT_ONE},{"format_one",FORMAT_ONE},{"alias",ALIAS},{"overlap",OVERLAP},{"layer_error",LAYER_ERROR},{"output_error",OUTPUT_ERROR},{"param_checkout_error",PARAM_CHECKOUT_ERROR},{"param_checkin_error",PARAM_CHECKIN_ERROR},{"world_error",WORLD_ERROR},{"color_error",COLOR_ERROR},{"color_wrong_success",COLOR_WRONG_SUCCESS}};
    for(const auto&r:rows){++total;if(Run(effect,t,r.name,r.mode))++pass;}std::printf("SUMMARY pass=%d total=%d\n",pass,total);if(handle)dlclose(handle);return pass==total?0:4;
}

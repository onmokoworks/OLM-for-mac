#include <cstdio>
#include <cstring>
#include <algorithm>
#include <vector>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

static PF_ParamDef g_params[SM_NUM_PARAMS];
static PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
static int g_layer_error = 0, g_output_error = 0, g_param_fail = -1;
static int g_layer_calls = 0, g_output_calls = 0, g_param_calls = 0;
static int g_param_checkins = 0, g_layer_checkins = 0;
static int g_param_checkin_error_at = -1, g_param_checkin_error_calls = 0;
static int g_layer_checkin_error = 0, g_layer_checkin_error_calls = 0;

static PF_Err Layer(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
    ++g_layer_calls; if (g_layer_error) return g_layer_error;
    if (index != SM_INPUT) return 91; *world = g_input; return 0;
}
static PF_Err Output(PF_ProgPtr, PF_EffectWorld **world) {
    ++g_output_calls; if (g_output_error) return g_output_error; *world = g_output; return 0;
}
static PF_Err Param(A_long index, PF_ParamDef *param) {
    ++g_param_calls; if (index == g_param_fail) return 93; *param = g_params[index]; return 0;
}
static void ParamCheckin(PF_ParamDef *) { ++g_param_checkins; }
static PF_Err ParamCheckinError(PF_ParamDef *) {
    const int ordinal = g_param_checkin_error_calls++;
    return ordinal == g_param_checkin_error_at ? 95 : 0;
}
static void LayerCheckin(PF_ProgPtr, A_long index) { if (index == SM_INPUT) ++g_layer_checkins; }
static PF_Err LayerCheckinError(PF_ProgPtr, A_long index) {
    if (index == SM_INPUT) ++g_layer_checkin_error_calls;
    return g_layer_checkin_error;
}
static PF_Err PreFail(PF_ProgPtr,A_long,A_long,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*) { return 94; }

struct Fixture {
    std::vector<unsigned char> input, output;
    PF_EffectWorld iw{}, ow{};
    PF_ParamDef defs[SM_NUM_PARAMS]{};
    PF_ParamDef *params[SM_NUM_PARAMS]{};
    Fixture(int depth, int width, int height, int padding) {
        const int pixel = depth == 8 ? (int)sizeof(PF_Pixel8) : depth == 16 ? (int)sizeof(PF_Pixel16) : (int)sizeof(PF_PixelFloat);
        const int rb = width * pixel + padding;
        input.assign((size_t)rb * height, 0x3c); output.assign((size_t)rb * height, 0xa5);
        iw.data=input.data(); iw.width=width; iw.height=height; iw.rowbytes=rb; iw.bitdepth=depth; iw.extent_hint={0,0,width,height};
        ow=iw; ow.data=output.data();
        for (int i=0;i<SM_NUM_PARAMS;++i) params[i]=defs+i;
        defs[SM_INPUT].u.ld=iw; defs[SM_USE_KEY].u.bd.value=0;
        defs[SM_KEY_COLOR].u.cd.value={255,202,187,230}; defs[SM_TOLERANCE].u.sd.value=6;
    }
};

static unsigned short Widen(unsigned value) {
    return (unsigned short)((value * 0x8000u + 0x80u) / 0xffu);
}

static void FillChecker7x5(Fixture &f) {
    const int key[][2]={{0,0},{6,0},{3,2},{0,4},{6,4}};
    auto is_key=[&](int x,int y){for(auto &q:key)if(q[0]==x&&q[1]==y)return true;return false;};
    for(int y=0;y<5;++y) for(int x=0;x<7;++x) {
        const unsigned v=((x+y)&1)?128:0;
        if(f.iw.bitdepth==8) {
            PF_Pixel8 p=is_key(x,y)?PF_Pixel8{255,202,187,230}:PF_Pixel8{255,(unsigned char)v,(unsigned char)v,(unsigned char)v};
            std::memcpy(f.input.data()+y*f.iw.rowbytes+x*sizeof(p),&p,sizeof(p));
        } else {
            PF_Pixel16 p=is_key(x,y)?PF_Pixel16{32768,Widen(202),Widen(187),Widen(230)}:PF_Pixel16{32768,Widen(v),Widen(v),Widen(v)};
            std::memcpy(f.input.data()+y*f.iw.rowbytes+x*sizeof(p),&p,sizeof(p));
        }
    }
    f.defs[SM_INPUT].u.ld=f.iw;
}

static void FillPractical64x36(Fixture &f) {
    const int alphas[]={0,1,17,32,63,64,95,127,128,159,191,223,254,255};
    auto key=[&](int x,int y){return (x==0&&y==0)||(x==63&&y==0)||(x==32&&y==18)||(x==0&&y==35)||(x==63&&y==35);};
    for(int y=0;y<36;++y) for(int x=0;x<64;++x) {
        unsigned a,r,g,b;
        if(key(x,y)){a=255;r=202;g=187;b=230;}
        else {
            a=((x+y*3)%11==0)?alphas[(x*5+y*3)%14]:255;
            if(x<16&&y<16&&a==255){r=g=b=(x*17+y*23)&255;}
            else {r=std::min((unsigned)((x*37+y*19+13)&255),a);g=std::min((unsigned)((x*11+y*53+201)&255),a);b=std::min((unsigned)((x*71+y*7+41)&255),a);}
        }
        PF_Pixel16 p={Widen(a),Widen(r),Widen(g),Widen(b)};
        std::memcpy(f.input.data()+y*f.iw.rowbytes+x*sizeof(p),&p,sizeof(p));
    }
    f.defs[SM_INPUT].u.ld=f.iw;
}

static int Classic(Fixture &f) {
    PF_InData id{}; PF_OutData od{};
    return EffectMain(PF_Cmd_RENDER,&id,&od,f.params,&f.ow,nullptr);
}
static int Smart(Fixture &f) {
    std::memcpy(g_params,f.defs,sizeof(g_params)); g_input=&f.iw; g_output=&f.ow;
    g_cli_checkout_param_hook=&Param; g_cli_checkin_param_hook=&ParamCheckin;
    g_cli_checkin_param_error_hook=&ParamCheckinError;
    g_olmsmoother_cli_checkin_layer_hook=&LayerCheckin;
    g_olmsmoother_cli_checkin_layer_error_hook=&LayerCheckinError;
    PF_SmartRenderCallbacks cb{&Layer,&Output}; PF_SmartRenderInput input{f.iw.bitdepth};
    PF_SmartRenderExtra extra{&input,&cb}; PF_InData id{}; PF_OutData od{};
    return EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&extra);
}
static bool Untouched(const Fixture &f) { for (auto b:f.output) if (b!=0xa5) return false; return true; }
static bool PaddingUntouched(const Fixture &f) {
    const int pixel = f.iw.bitdepth == 8 ? (int)sizeof(PF_Pixel8) : (int)sizeof(PF_Pixel16);
    const int active = f.iw.width * pixel;
    for (int y=0;y<f.ow.height;++y) for (int x=active;x<f.ow.rowbytes;++x)
        if (f.output[(size_t)y*f.ow.rowbytes+x] != 0xa5) return false;
    return true;
}
static void Print(const char *name, bool pass) { std::printf("CASE %s %s\n",name,pass?"PASS":"FAIL"); }

int main() {
    int failures=0; auto check=[&](const char*n,bool ok){Print(n,ok);if(!ok)++failures;};
    { Fixture f(8,7,5,8); FillChecker7x5(f); check("accept_pf8_7x5",Classic(f)==0); }
    { Fixture f(16,64,36,32); FillPractical64x36(f); check("accept_pf16_64x36",Classic(f)==0); }
    { Fixture f(16,64,36,32); FillPractical64x36(f); f.input.insert(f.input.begin(),0); f.iw.data=f.input.data()+1; f.defs[0].u.ld=f.iw; check("accept_pf16_unaligned_input_via_aligned_staging",Classic(f)==0); }
    { Fixture f(8,7,5,8); FillChecker7x5(f); f.input[0]^=1; check("arbitrary_source_pf8_accept",Classic(f)==0&&PaddingUntouched(f)); }
    { Fixture f(16,64,36,32); FillPractical64x36(f); f.input[f.iw.rowbytes*18+32*sizeof(PF_Pixel16)]^=1; check("arbitrary_source_pf16_accept",Classic(f)==0&&PaddingUntouched(f)); }
    { Fixture f(8,7,5,8); FillChecker7x5(f); f.ow.data=(unsigned char*)f.iw.data+1; check("partial_overlap_forward_reject",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(8,7,5,8); FillChecker7x5(f); f.iw.data=(unsigned char*)f.ow.data+1; f.defs[0].u.ld=f.iw; check("partial_overlap_backward_reject",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(32,7,5,8); check("classic_pf32_reject",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(8,7,5,8); f.ow.bitdepth=16; check("output_format_mismatch",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(8,7,5,8); f.iw.data=nullptr; f.defs[0].u.ld=f.iw; check("null_input_data",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(8,7,5,8); f.ow.data=nullptr; check("null_output_data",Classic(f)!=0); }
    { Fixture f(8,7,5,8); f.ow.data=f.iw.data; check("alias_reject",Classic(f)!=0); }
    { Fixture f(8,7,5,8); --f.ow.height; check("dimension_mismatch",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(8,7,5,8); f.output.resize((size_t)(++f.ow.rowbytes)*f.ow.height,0xa5); f.ow.data=f.output.data(); check("independent_rowbytes_accept",Classic(f)==0&&PaddingUntouched(f)); }
    { Fixture f(8,7,5,8); f.iw.rowbytes=f.ow.rowbytes=27; f.defs[0].u.ld=f.iw; check("short_rowbytes",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(8,7,5,8); f.defs[SM_USE_KEY].u.bd.value=2; check("tuple_usekey",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(8,7,5,8); f.defs[SM_TOLERANCE].u.sd.value=2; check("tolerance_full_range_accept",Classic(f)==0&&PaddingUntouched(f)); }
    { Fixture f(8,7,5,8); ++f.defs[SM_KEY_COLOR].u.cd.value.red; check("key_color_ignored_when_key_off",Classic(f)==0&&PaddingUntouched(f)); }
    { Fixture f(8,8,5,8); check("general_geometry_accept",Classic(f)==0&&PaddingUntouched(f)); }
    { Fixture f(8,7,5,9); check("general_layout_accept",Classic(f)==0&&PaddingUntouched(f)); }
    { Fixture f(8,7,5,8); f.iw.height=f.ow.height=INT32_MAX; f.defs[0].u.ld=f.iw; check("row_offset_overflow",Classic(f)!=0&&Untouched(f)); }
    { Fixture f(8,7,5,8); f.iw.extent_hint.left=f.ow.extent_hint.left=1;f.defs[0].u.ld=f.iw;bool origin=Classic(f)!=0&&Untouched(f);
      Fixture g(16,7,5,8);--g.iw.extent_hint.right;--g.ow.extent_hint.right;g.defs[0].u.ld=g.iw;bool roi=Classic(g)!=0&&Untouched(g);
      check("nonzero_origin_and_partial_roi_reject",origin&&roi); }
    { Fixture f(8,7,5,8); PF_InData id{};PF_OutData od{}; check("null_params",EffectMain(PF_Cmd_RENDER,&id,&od,nullptr,&f.ow,nullptr)!=0&&Untouched(f)); }

    { Fixture f(8,7,5,8); g_layer_error=0;g_output_error=0;g_param_fail=-1;
      g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;
      int e=Smart(f); check("smart_unowned_entry_reject",e!=0&&g_layer_calls==1&&g_output_calls==1&&g_param_calls==SM_NUM_PARAMS-1&&g_param_checkins==SM_NUM_PARAMS-1&&g_layer_checkins==1&&Untouched(f)); }

    { Fixture f(8,7,5,8); g_layer_error=0;g_output_error=0;g_param_fail=2;
      g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;
      int e=Smart(f); check("smart_partial_param_checkin",e!=0&&g_layer_calls==1&&g_output_calls==1&&g_param_calls==2&&g_param_checkins==1&&g_layer_checkins==1&&Untouched(f)); }
    { Fixture f(8,7,5,8); g_layer_error=0;g_output_error=92;g_param_fail=-1;
      g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;
      int e=Smart(f); check("smart_output_failure_checkin",e!=0&&g_layer_calls==1&&g_output_calls==1&&g_param_calls==0&&g_param_checkins==0&&g_layer_checkins==1&&Untouched(f)); }
    { Fixture f(8,7,5,8); g_layer_error=92;g_output_error=0;g_param_fail=-1;
      g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;
      int e=Smart(f); check("smart_layer_failure_no_checkin",e!=0&&g_layer_calls==1&&g_output_calls==0&&g_layer_checkins==0&&Untouched(f)); }
    { Fixture f(8,7,5,8); g_layer_error=0;g_output_error=0;g_param_fail=-1;g_param_checkin_error_at=0;g_param_checkin_error_calls=0;g_layer_checkin_error=0;g_layer_checkin_error_calls=0;
      g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;
      int e=Smart(f); check("smart_param_checkin_error_preserves_primary_and_continues",e==PF_Err_BAD_CALLBACK_PARAM&&g_param_checkins==SM_NUM_PARAMS-1&&g_param_checkin_error_calls==SM_NUM_PARAMS-1&&g_layer_checkins==1&&Untouched(f));g_param_checkin_error_at=-1; }
    { Fixture f(8,7,5,8); g_layer_error=0;g_output_error=0;g_param_fail=-1;g_param_checkin_error_calls=0;g_layer_checkin_error=96;g_layer_checkin_error_calls=0;
      g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;
      int e=Smart(f); check("smart_layer_checkin_error_preserves_primary",e==PF_Err_BAD_CALLBACK_PARAM&&g_param_checkins==SM_NUM_PARAMS-1&&g_layer_checkins==1&&g_layer_checkin_error_calls==1&&Untouched(f));g_layer_checkin_error=0; }
    { PF_PreRenderInput pi{};PF_PreRenderOutput po{{11,12,13,14},{21,22,23,24}};PF_PreRenderCallbacks cb{&PreFail};PF_PreRenderExtra ex{&pi,&po,&cb};PF_InData id{};PF_OutData od{};int e=EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&ex);check("pre_failure_rect_untouched",e==94&&po.result_rect.left==11&&po.result_rect.top==12&&po.result_rect.right==13&&po.result_rect.bottom==14&&po.max_result_rect.left==21&&po.max_result_rect.top==22&&po.max_result_rect.right==23&&po.max_result_rect.bottom==24); }
    std::printf("SUMMARY %d %d\n",30-failures,30); return failures?2:0;
}

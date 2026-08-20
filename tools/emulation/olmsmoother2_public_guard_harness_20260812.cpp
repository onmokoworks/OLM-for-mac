#include <cstdio>
#include <cstring>
#include <cmath>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static PF_ParamDef g_params[SM_NUM_PARAMS];
static PF_EffectWorld *g_input=nullptr,*g_output=nullptr;
static int g_layer_error=0,g_output_error=0,g_param_fail=-1;
static int g_layer_calls=0,g_output_calls=0,g_param_calls=0,g_param_checkins=0,g_layer_checkins=0;
static PF_Err Layer(PF_ProgPtr,A_long i,PF_EffectWorld **w){++g_layer_calls;if(g_layer_error)return g_layer_error;if(i!=SM_INPUT)return 91;*w=g_input;return 0;}
static PF_Err Output(PF_ProgPtr,PF_EffectWorld **w){++g_output_calls;if(g_output_error)return g_output_error;*w=g_output;return 0;}
static PF_Err Param(A_long i,PF_ParamDef *p){++g_param_calls;if(i==g_param_fail)return 93;*p=g_params[i];return 0;}
static void ParamCheckin(PF_ParamDef*){++g_param_checkins;}
static PF_Err ParamCheckinFail(PF_ParamDef*){return 96;}
static PF_Err ColorFail(PF_ProgPtr,PF_ParamDef*,PF_PixelFloat*){return 97;}
static PF_Err ColorWrong(PF_ProgPtr ref,PF_ParamDef*def,PF_PixelFloat*out){const PF_Err e=cli_get_float_color(ref,def,out);out->red=std::nextafter(out->red,INFINITY);return e;}
static void LayerCheckin(PF_ProgPtr,A_long i){if(i==SM_INPUT)++g_layer_checkins;}
static PF_Err PreFail(PF_ProgPtr,A_long,A_long,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult*){return 94;}

struct Fixture{
 std::vector<unsigned char> input,output;PF_EffectWorld iw{},ow{};PF_ParamDef defs[SM_NUM_PARAMS]{};PF_ParamDef*params[SM_NUM_PARAMS]{};
 Fixture(int depth,int w,int h,int pad){int ps=depth==8?4:depth==16?8:16,rb=w*ps+pad;input.assign((size_t)rb*h,0x3c);output.assign((size_t)rb*h,0xa5);iw.data=input.data();iw.width=w;iw.height=h;iw.rowbytes=rb;iw.bitdepth=depth;iw.extent_hint={0,0,w,h};ow=iw;ow.data=output.data();for(int i=0;i<SM_NUM_PARAMS;i++)params[i]=defs+i;defs[0].u.ld=iw;defs[SM_ENABLE_KEY].u.bd.value=1;defs[SM_KEY_COLOR].u.cd.value={255,202,187,230};defs[SM_INVERT_KEY].u.bd.value=0;defs[SM_SMOOTHNESS].u.sd.value=100;defs[SM_EXTRA_SMOOTH].u.sd.value=100;defs[SM_SMOOTH_RANGE].u.sd.value=100;defs[SM_VERSION].u.pd.value=1;defs[SM_GAMMA_MODE].u.pd.value=GAMMA_COLORS_ONLY;defs[SM_GAMMA_VALUE].u.fs_d.value=1.8;defs[SM_NUM_GAMMA_COLORS].u.sd.value=2;defs[SM_GAMMA_COLOR_0].u.cd.value={255,255,0,0};defs[SM_GAMMA_COLOR_1].u.cd.value={255,202,187,230};}
};
static unsigned short Widen(unsigned value){return(unsigned short)std::lround(value*32768.0/255.0);}
static void FillGamma18(Fixture&f){
 static const unsigned char rgb[25][3]={{202,187,230},{255,0,0},{65,1,1},{0,255,0},{206,55,161},{86,55,26},{43,73,217},{231,16,235},{116,106,230},{1,9,43},{91,38,34},{99,183,84},{230,125,149},{208,155,60},{168,21,161},{233,157,226},{8,57,119},{159,56,196},{232,156,109},{50,140,246},{229,135,20},{36,6,46},{176,107,229},{168,83,193},{235,7,162}};
 for(int y=0;y<5;y++)for(int x=0;x<5;x++){const auto*q=rgb[y*5+x];unsigned char*dst=f.input.data()+y*f.iw.rowbytes+x*(f.iw.bitdepth==8?4:f.iw.bitdepth==16?8:16);if(f.iw.bitdepth==8){PF_Pixel8 p={255,q[0],q[1],q[2]};memcpy(dst,&p,sizeof(p));}else if(f.iw.bitdepth==16){PF_Pixel16 p={32768,Widen(q[0]),Widen(q[1]),Widen(q[2])};memcpy(dst,&p,sizeof(p));}else{PF_PixelFloat p={1.f,q[0]/255.f,q[1]/255.f,q[2]/255.f};memcpy(dst,&p,sizeof(p));}}
 f.defs[0].u.ld=f.iw;
}
static void Fill3x2(Fixture&f){
 const PF_PixelFloat p[6]={{1,0,0,0},{1,0,1,1},{1,1,0,1},{1,1,1,0},{1,.25f,.25f,.25f},{1,.75f,.75f,.75f}};
 for(int y=0;y<2;y++)for(int x=0;x<3;x++)memcpy(f.input.data()+y*f.iw.rowbytes+x*sizeof(PF_PixelFloat),p+y*3+x,sizeof(PF_PixelFloat));f.defs[0].u.ld=f.iw;
}
static int Classic(Fixture&f){PF_InData id{};PF_OutData od{};return EffectMain(PF_Cmd_RENDER,&id,&od,f.params,&f.ow,nullptr);}
static int Smart(Fixture&f){memcpy(g_params,f.defs,sizeof(g_params));g_input=&f.iw;g_output=&f.ow;g_cli_checkout_param_hook=&Param;g_cli_checkin_param_hook=&ParamCheckin;g_olmsmoother2_cli_checkin_layer_hook=&LayerCheckin;PF_SmartRenderCallbacks cb{&Layer,&Output};PF_SmartRenderInput si{f.iw.bitdepth};PF_SmartRenderExtra ex{&si,&cb};PF_InData id{};PF_OutData od{};return EffectMain(PF_Cmd_SMART_RENDER,&id,&od,nullptr,nullptr,&ex);}
static bool Untouched(const Fixture&f){for(auto b:f.output)if(b!=0xa5)return false;return true;}
int main(){int fail=0;auto ck=[&](const char*n,bool x){printf("CASE %s %s\n",n,x?"PASS":"FAIL");if(!x)++fail;};
 {Fixture f(8,5,5,5);FillGamma18(f);ck("accept_gamma18_pf8",Smart(f)==0);}
 {Fixture f(16,5,5,7);FillGamma18(f);f.defs[SM_VERSION].u.pd.value=2;f.defs[SM_INVERT_KEY].u.bd.value=1;ck("accept_gamma18_pf16_smart",Smart(f)==0);}
 {Fixture f(32,5,5,13);FillGamma18(f);ck("accept_gamma18_pf32_smart",Smart(f)==0);}
 {Fixture f(8,5,5,5);FillGamma18(f);g_cli_checkin_param_error_hook=&ParamCheckinFail;g_layer_error=g_output_error=0;g_param_fail=-1;g_param_checkins=0;int e=Smart(f);g_cli_checkin_param_error_hook=nullptr;ck("checkin_error_atomic_reject",e==96&&g_param_checkins==SM_NUM_PARAMS-1&&Untouched(f));}
 {Fixture f(8,5,5,5);FillGamma18(f);auto saved=g_color_suite.PF_GetFloatingPointColorFromColorDef;g_color_suite.PF_GetFloatingPointColorFromColorDef=&ColorFail;int e=Smart(f);g_color_suite.PF_GetFloatingPointColorFromColorDef=saved;ck("color_error_atomic_reject",e==97&&Untouched(f));}
 {Fixture f(8,5,5,5);FillGamma18(f);auto saved=g_color_suite.PF_GetFloatingPointColorFromColorDef;g_color_suite.PF_GetFloatingPointColorFromColorDef=&ColorWrong;int e=Smart(f);g_color_suite.PF_GetFloatingPointColorFromColorDef=saved;ck("color_value_one_ulp_atomic_reject",e!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);FillGamma18(f);f.input[0]^=1;ck("source_mutation_gamma18_pf8_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(16,5,5,7);FillGamma18(f);f.input[f.iw.rowbytes*2+2*sizeof(PF_Pixel16)]^=1;f.defs[SM_VERSION].u.pd.value=2;f.defs[SM_INVERT_KEY].u.bd.value=1;ck("source_mutation_gamma18_pf16_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(32,5,5,13);FillGamma18(f);f.input[f.iw.rowbytes*4+4*sizeof(PF_PixelFloat)]^=1;ck("source_mutation_gamma18_pf32_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);FillGamma18(f);f.ow.data=(unsigned char*)f.iw.data+1;ck("partial_overlap_forward_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);FillGamma18(f);f.iw.data=(unsigned char*)f.ow.data+1;f.defs[0].u.ld=f.iw;ck("partial_overlap_backward_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(32,5,5,13);ck("classic_pf32_reject",Classic(f)!=0&&Untouched(f));}
 {Fixture f(16,5,5,7);ck("classic_pf16_unowned_reject",Classic(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.ow.bitdepth=16;ck("output_format_mismatch",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.iw.data=nullptr;f.defs[0].u.ld=f.iw;ck("null_input_data",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.ow.data=nullptr;ck("null_output_data",Smart(f)!=0);}
 {Fixture f(8,5,5,5);f.ow.data=f.iw.data;ck("alias_reject",Smart(f)!=0);}
 {Fixture f(8,5,5,5);--f.ow.width;ck("dimension_mismatch",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);++f.ow.rowbytes;ck("rowbytes_mismatch",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.iw.rowbytes=f.ow.rowbytes=19;f.defs[0].u.ld=f.iw;ck("short_rowbytes",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.defs[SM_GAMMA_VALUE].u.fs_d.value=1.81;ck("tuple_gamma",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.defs[SM_SMOOTH_RANGE].u.sd.value=99;ck("tuple_smoothing",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.defs[SM_NUM_GAMMA_COLORS].u.sd.value=3;ck("tuple_palette_count",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);++f.defs[SM_GAMMA_COLOR_1].u.cd.value.blue;ck("tuple_palette_color",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,6,5,5);ck("geometry_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,6);ck("layout_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.iw.height=f.ow.height=INT32_MAX;f.defs[0].u.ld=f.iw;ck("row_offset_overflow",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);++f.ow.extent_hint.bottom;ck("extent_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);f.defs[SM_GAMMA_COLOR_2].u.cd.value.red=1;ck("inactive_palette_tail_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(16,3,2,6);memset(f.defs,0,sizeof(f.defs));for(int i=0;i<SM_NUM_PARAMS;i++)f.params[i]=f.defs+i;f.defs[0].u.ld=f.iw;f.defs[SM_SMOOTHNESS].u.sd.value=100;f.defs[SM_SMOOTH_RANGE].u.sd.value=1;f.defs[SM_VERSION].u.pd.value=2;f.defs[SM_GAMMA_MODE].u.pd.value=GAMMA_NONE;f.defs[SM_GAMMA_VALUE].u.fs_d.value=2.4;ck("reject_unowned_3x2_pf16",Smart(f)!=0&&Untouched(f));}
 {Fixture f(32,3,2,12);memset(f.defs,0,sizeof(f.defs));for(int i=0;i<SM_NUM_PARAMS;i++)f.params[i]=f.defs+i;Fill3x2(f);f.defs[SM_SMOOTHNESS].u.sd.value=100;f.defs[SM_SMOOTH_RANGE].u.sd.value=1;f.defs[SM_VERSION].u.pd.value=2;f.defs[SM_GAMMA_MODE].u.pd.value=GAMMA_NONE;f.defs[SM_GAMMA_VALUE].u.fs_d.value=2.4;ck("accept_3x2_pf32_smart",Smart(f)==0);}
 {Fixture f(32,3,2,12);memset(f.defs,0,sizeof(f.defs));for(int i=0;i<SM_NUM_PARAMS;i++)f.params[i]=f.defs+i;Fill3x2(f);f.input[f.iw.rowbytes+sizeof(PF_PixelFloat)]^=1;f.defs[SM_SMOOTHNESS].u.sd.value=100;f.defs[SM_SMOOTH_RANGE].u.sd.value=1;f.defs[SM_VERSION].u.pd.value=2;f.defs[SM_GAMMA_MODE].u.pd.value=GAMMA_NONE;f.defs[SM_GAMMA_VALUE].u.fs_d.value=2.4;ck("source_mutation_3x2_pf32_reject",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,3,2,3);memset(f.defs,0,sizeof(f.defs));for(int i=0;i<SM_NUM_PARAMS;i++)f.params[i]=f.defs+i;f.defs[0].u.ld=f.iw;f.defs[SM_SMOOTHNESS].u.sd.value=100;f.defs[SM_SMOOTH_RANGE].u.sd.value=1;f.defs[SM_VERSION].u.pd.value=2;f.defs[SM_GAMMA_MODE].u.pd.value=GAMMA_NONE;f.defs[SM_GAMMA_VALUE].u.fs_d.value=2.4;ck("reject_inferred_3x2_pf8",Smart(f)!=0&&Untouched(f));}
 {Fixture f(32,3,2,12);memset(f.defs,0,sizeof(f.defs));for(int i=0;i<SM_NUM_PARAMS;i++)f.params[i]=f.defs+i;f.defs[0].u.ld=f.iw;f.defs[SM_SMOOTHNESS].u.sd.value=100;f.defs[SM_SMOOTH_RANGE].u.sd.value=1;f.defs[SM_VERSION].u.pd.value=2;f.defs[SM_GAMMA_MODE].u.pd.value=GAMMA_NONE;f.defs[SM_GAMMA_VALUE].u.fs_d.value=2.4;f.defs[SM_INVERT_KEY].u.bd.value=1;ck("reject_3x2_inactive_invert",Smart(f)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);PF_InData id{};PF_OutData od{};ck("null_params",EffectMain(PF_Cmd_RENDER,&id,&od,nullptr,&f.ow,nullptr)!=0&&Untouched(f));}
 {Fixture f(8,5,5,5);g_layer_error=0;g_output_error=0;g_param_fail=4;g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;int e=Smart(f);ck("smart_partial_param_checkin",e!=0&&g_layer_calls==1&&g_output_calls==1&&g_param_calls==4&&g_param_checkins==3&&g_layer_checkins==1&&Untouched(f));}
 {Fixture f(8,5,5,5);g_layer_error=0;g_output_error=92;g_param_fail=-1;g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;int e=Smart(f);ck("smart_output_failure_checkin",e!=0&&g_layer_calls==1&&g_output_calls==1&&g_param_calls==0&&g_param_checkins==0&&g_layer_checkins==1&&Untouched(f));}
 {Fixture f(8,5,5,5);g_layer_error=92;g_output_error=0;g_param_fail=-1;g_layer_calls=g_output_calls=g_param_calls=g_param_checkins=g_layer_checkins=0;int e=Smart(f);ck("smart_layer_failure_no_checkin",e!=0&&g_layer_calls==1&&g_output_calls==0&&g_layer_checkins==0&&Untouched(f));}
 {PF_PreRenderInput pi{};PF_PreRenderOutput po{{11,12,13,14},{21,22,23,24}};PF_PreRenderCallbacks cb{&PreFail};PF_PreRenderExtra ex{&pi,&po,&cb};PF_InData id{};id.width=16;id.height=16;id.downsample_x={1,1};id.downsample_y={1,1};PF_OutData od{};int e=EffectMain(PF_Cmd_SMART_PRE_RENDER,&id,&od,nullptr,nullptr,&ex);ck("pre_failure_rect_untouched",e==94&&po.result_rect.left==11&&po.result_rect.top==12&&po.result_rect.right==13&&po.result_rect.bottom==14&&po.max_result_rect.left==21&&po.max_result_rect.top==22&&po.max_result_rect.right==23&&po.max_result_rect.bottom==24);}
 printf("SUMMARY %d %d\n",39-fail,39);return fail?2:0;}

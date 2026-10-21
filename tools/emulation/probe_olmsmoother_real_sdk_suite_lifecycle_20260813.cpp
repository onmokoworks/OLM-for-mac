#include <cstdio>
#include <cstring>
#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#if defined(TEST_SMOOTHER_V1)
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
#elif defined(TEST_SMOOTHER_V2)
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
#else
#error Select TEST_SMOOTHER_V1 or TEST_SMOOTHER_V2
#endif

enum Mode { OK, ACQUIRE_ERROR, SUCCESS_NULL, FUNCTION_NULL, CALLBACK_ERROR, RELEASE_ERROR };
static Mode g_mode=OK;
static int g_acquire=0,g_release=0,g_get=0,g_color=0;
static PF_WorldSuite2 g_world{};
#if defined(TEST_SMOOTHER_V2)
static PF_ColorParamSuite1 g_colors{};
#endif

static PF_Err get_format(const PF_EffectWorld*,PF_PixelFormat *format){
 ++g_get;if(g_mode==CALLBACK_ERROR)return 73;*format=PF_PixelFormat_ARGB32;return PF_Err_NONE;
}
#if defined(TEST_SMOOTHER_V2)
static PF_Err get_color(PF_ProgPtr,const PF_ParamDef *param,PF_PixelFloat *out){
 ++g_color;if(g_mode==CALLBACK_ERROR)return 74;
 out->alpha=param->u.cd.value.alpha/255.f;out->red=param->u.cd.value.red/255.f;
 out->green=param->u.cd.value.green/255.f;out->blue=param->u.cd.value.blue/255.f;return PF_Err_NONE;
}
#endif
static SPErr acquire(const char *name,int32 version,const void **suite){
 ++g_acquire;if(g_mode==ACQUIRE_ERROR)return 71;if(!suite)return kSPBadParameterError;
 if(g_mode==SUCCESS_NULL){*suite=nullptr;return kSPNoError;}
 if(!std::strcmp(name,kPFWorldSuite)&&version==kPFWorldSuiteVersion2){
  g_world.PF_GetPixelFormat=g_mode==FUNCTION_NULL?nullptr:get_format;*suite=&g_world;return kSPNoError;
 }
#if defined(TEST_SMOOTHER_V2)
 if(!std::strcmp(name,kPFColorParamSuite)&&version==kPFColorParamSuiteVersion1){
  g_colors.PF_GetFloatingPointColorFromColorDef=g_mode==FUNCTION_NULL?nullptr:get_color;*suite=&g_colors;return kSPNoError;
 }
#endif
 return kSPBadParameterError;
}
static SPErr release(const char*,int32){++g_release;return g_mode==RELEASE_ERROR?72:kSPNoError;}
static void reset(Mode mode){g_mode=mode;g_acquire=g_release=g_get=g_color=0;}
static bool world_case(Mode mode,PF_Err expected,int releases){
 reset(mode);SPBasicSuite basic{};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;
 PF_InData in{};PF_OutData out{};PF_EffectWorld world{};short depth=0;in.pica_basicP=&basic;
 PF_Err err=WorldDepth(&in,&out,&world,&depth);
 const bool pass=err==expected&&g_acquire==1&&g_release==releases&&
                 g_get==((mode==OK||mode==CALLBACK_ERROR||mode==RELEASE_ERROR)?1:0)&&
                 (mode!=OK||depth==8);
 std::printf("WORLD mode=%d pass=%d err=%d acquire=%d get=%d release=%d\n",mode,pass,err,g_acquire,g_get,g_release);return pass;
}
#if defined(TEST_SMOOTHER_V2)
static bool color_case(Mode mode,PF_Err expected,int releases,int calls){
 reset(mode);SPBasicSuite basic{};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;PF_InData in{};in.pica_basicP=&basic;
 PF_ParamDef defs[SM_NUM_PARAMS]{};PF_ParamDef *params[SM_NUM_PARAMS]{};
 for(int i=0;i<SM_NUM_PARAMS;++i)params[i]=defs+i;
 defs[SM_KEY_COLOR].u.cd.value={255,1,2,3};for(int i=0;i<NUM_GAMMA_COLORS;++i)defs[SM_GAMMA_COLOR_0+i].u.cd.value={255,(A_u_char)i,2,3};
 SMParams decoded{};PF_Err err=FetchParams(&in,params,&decoded);
 const bool pass=err==expected&&g_acquire==1&&g_release==releases&&g_color==calls;
 std::printf("COLOR mode=%d pass=%d err=%d acquire=%d calls=%d release=%d\n",mode,pass,err,g_acquire,g_color,g_release);return pass;
}
#endif
int main(){
 bool ok=true;ok&=world_case(OK,PF_Err_NONE,1);ok&=world_case(ACQUIRE_ERROR,71,0);
 ok&=world_case(SUCCESS_NULL,PF_Err_BAD_CALLBACK_PARAM,1);ok&=world_case(FUNCTION_NULL,PF_Err_BAD_CALLBACK_PARAM,1);
 ok&=world_case(CALLBACK_ERROR,73,1);ok&=world_case(RELEASE_ERROR,72,1);
#if defined(TEST_SMOOTHER_V2)
 ok&=color_case(OK,PF_Err_NONE,1,1+NUM_GAMMA_COLORS);ok&=color_case(ACQUIRE_ERROR,71,0,0);
 ok&=color_case(SUCCESS_NULL,PF_Err_BAD_CALLBACK_PARAM,1,0);ok&=color_case(FUNCTION_NULL,PF_Err_BAD_CALLBACK_PARAM,1,0);
 ok&=color_case(CALLBACK_ERROR,74,1,1);ok&=color_case(RELEASE_ERROR,72,1,1+NUM_GAMMA_COLORS);
#endif
 std::printf("SUITE_LIFECYCLE_EXACT=%d\n",ok);return ok?0:3;
}

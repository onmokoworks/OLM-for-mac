#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <fstream>
#include <iterator>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#define EffectMain SourceBuiltOLMSmootherEffectMain
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
#undef EffectMain

using Effect = PF_Err (*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef*[],PF_LayerDef*,void*);
static int g_depth,g_acquire,g_release,g_formats; static PF_WorldSuite2 g_world{};
static PF_Err GetFormat(const PF_EffectWorld*,PF_PixelFormat*f){++g_formats;*f=g_depth==8?PF_PixelFormat_ARGB32:PF_PixelFormat_ARGB64;return 0;}
template<class P,class F>static PF_Err Iterate(PF_InData*,A_long start,A_long end,PF_EffectWorld*src,const PF_Rect*,void*ref,F fn,PF_EffectWorld*dst){auto*s=(unsigned char*)src->data,*d=(unsigned char*)dst->data;for(A_long y=start;y<end;++y){auto*sr=(P*)(s+(int64_t)y*src->rowbytes);auto*dr=(P*)(d+(int64_t)y*dst->rowbytes);for(A_long x=0;x<src->width;++x){PF_Err e=fn(ref,x,y,&sr[x],&dr[x]);if(e)return e;}}return 0;}
static PF_Err Iterate8(PF_InData*i,A_long s,A_long e,PF_EffectWorld*w,const PF_Rect*r,void*c,PF_Err(*f)(void*,A_long,A_long,PF_Pixel*,PF_Pixel*),PF_EffectWorld*o){return Iterate<PF_Pixel8>(i,s,e,w,r,c,f,o);}
static PF_Err Iterate16(PF_InData*i,A_long s,A_long e,PF_EffectWorld*w,const PF_Rect*r,void*c,PF_Err(*f)(void*,A_long,A_long,PF_Pixel16*,PF_Pixel16*),PF_EffectWorld*o){return Iterate<PF_Pixel16>(i,s,e,w,r,c,f,o);}
static PF_Iterate8Suite1 g_iter8{Iterate8};static PF_Iterate16Suite1 g_iter16{Iterate16};
static SPErr Acquire(const char*n,int32 v,const void**s){++g_acquire;if(!std::strcmp(n,kPFWorldSuite)&&v==kPFWorldSuiteVersion2){g_world.PF_GetPixelFormat=GetFormat;*s=&g_world;return 0;}if(!std::strcmp(n,kPFIterate8Suite)&&v==kPFIterate8SuiteVersion1){*s=&g_iter8;return 0;}if(!std::strcmp(n,kPFIterate16Suite)&&v==kPFIterate16SuiteVersion1){*s=&g_iter16;return 0;}return kSPBadParameterError;}
static SPErr Release(const char*,int32){++g_release;return 0;}

struct Result{PF_Err err;std::vector<unsigned char>input,output;int acquire,release,formats;};
static Result Run(Effect effect,const std::vector<unsigned char>&payload,int depth,int w,int h,int rb,int use_key,int tolerance,int ka,int kr,int kg,int kb){
 std::vector<unsigned char>input=payload,output((size_t)rb*h,0xa5);PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.width=w;iw.height=h;iw.rowbytes=rb;iw.extent_hint={0,0,w,h};ow=iw;ow.data=(PF_PixelPtr)output.data();PF_ParamDef defs[SM_NUM_PARAMS]{};PF_ParamDef*params[SM_NUM_PARAMS]{};for(int i=0;i<SM_NUM_PARAMS;++i)params[i]=defs+i;defs[SM_INPUT].u.ld=iw;defs[SM_USE_KEY].u.bd.value=use_key;defs[SM_TOLERANCE].u.sd.value=tolerance;defs[SM_KEY_COLOR].u.cd.value={(A_u_char)ka,(A_u_char)kr,(A_u_char)kg,(A_u_char)kb};SPBasicSuite basic{};basic.AcquireSuite=Acquire;basic.ReleaseSuite=Release;PF_InData in{};in.pica_basicP=&basic;PF_OutData out{};g_depth=depth;g_acquire=g_release=g_formats=0;PF_Err err=effect(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);return{err,input,output,g_acquire,g_release,g_formats};
}
static bool Padding(const std::vector<unsigned char>&b,int depth,int w,int h,int rb){int active=w*(depth==8?4:8);for(int y=0;y<h;++y)for(int x=active;x<rb;++x)if(b[(size_t)y*rb+x]!=0xa5)return false;return true;}
int main(int argc,char**argv){if(argc!=13)return 2;const char*installed_path=argv[1];const char*input_path=argv[2];int depth=std::atoi(argv[3]),w=std::atoi(argv[4]),h=std::atoi(argv[5]),rb=std::atoi(argv[6]),use=std::atoi(argv[7]),tol=std::atoi(argv[8]),ka=std::atoi(argv[9]),kr=std::atoi(argv[10]),kg=std::atoi(argv[11]),kb=std::atoi(argv[12]);std::ifstream stream(input_path,std::ios::binary);std::vector<unsigned char>payload((std::istreambuf_iterator<char>(stream)),{});if(payload.size()!=(size_t)rb*h)return 3;void*handle=dlopen(installed_path,RTLD_NOW|RTLD_LOCAL);if(!handle){std::fprintf(stderr,"%s\n",dlerror());return 4;}auto installed=(Effect)dlsym(handle,"EffectMain");if(!installed)return 5;auto source=Run(SourceBuiltOLMSmootherEffectMain,payload,depth,w,h,rb,use,tol,ka,kr,kg,kb);auto live=Run(installed,payload,depth,w,h,rb,use,tol,ka,kr,kg,kb);bool ok=source.err==0&&live.err==0&&source.input==payload&&live.input==payload&&source.output==live.output&&Padding(source.output,depth,w,h,rb)&&Padding(live.output,depth,w,h,rb)&&source.formats==2&&live.acquire==source.acquire&&live.release==source.release&&live.formats==source.formats;std::printf("pass=%d source_err=%d installed_err=%d bytes=%zu\n",ok?1:0,source.err,live.err,live.output.size());dlclose(handle);return ok?0:6;}

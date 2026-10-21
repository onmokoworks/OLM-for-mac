#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>
#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../../mac/OLMBlur/OLMBlur.cpp"

static PF_EffectWorld *g_input=nullptr,*g_output=nullptr;
static PF_PixelFormat g_format=PF_PixelFormat_INVALID;
static PF_WorldSuite2 g_world_suite{};
static int g_acquire=0,g_release=0,g_get=0,g_copy=0;

static std::vector<unsigned char> read_file(const std::string &path){
  std::ifstream f(path,std::ios::binary);return {std::istreambuf_iterator<char>(f),{}};
}
static PF_Err copy_world(PF_ProgPtr,PF_EffectWorld *src,PF_EffectWorld *dst,PF_Rect*,PF_Rect*){
  ++g_copy;if(!src||!dst||!src->data||!dst->data||src->width!=dst->width||src->height!=dst->height||src->rowbytes!=dst->rowbytes)return 91;
  for(A_long y=0;y<src->height;++y)std::memcpy(reinterpret_cast<unsigned char*>(dst->data)+static_cast<size_t>(y)*dst->rowbytes,reinterpret_cast<unsigned char*>(src->data)+static_cast<size_t>(y)*src->rowbytes,src->rowbytes);
  return PF_Err_NONE;
}
static PF_Err get_format(const PF_EffectWorld *world,PF_PixelFormat *format){
  ++g_get;if(!format||(world!=g_input&&world!=g_output))return 92;*format=g_format;return PF_Err_NONE;
}
static SPErr acquire_suite(const char *name,int32 version,const void **suite){
  ++g_acquire;if(!name||std::strcmp(name,kPFWorldSuite)||version!=kPFWorldSuiteVersion2||!suite)return kSPBadParameterError;*suite=&g_world_suite;return kSPNoError;
}
static SPErr release_suite(const char *name,int32 version){++g_release;return name&&!std::strcmp(name,kPFWorldSuite)&&version==kPFWorldSuiteVersion2?kSPNoError:kSPBadParameterError;}

static bool run_case(const std::string &dir,short depth,int bias,int legacy,double amount,bool admitted){
  const int pixel_bytes=depth==8?4:depth==16?8:16,padding=depth==8?17:depth==16?23:32,rowbytes=24*pixel_bytes+padding;
  const char *name=depth==8?"source_argb8.bin":depth==16?"source_argb16.bin":"source_argb32.bin";
  const auto source=read_file(dir+"/"+name);if(source.size()!=static_cast<size_t>(24*24*pixel_bytes))return false;
  std::vector<unsigned char> input(static_cast<size_t>(rowbytes)*24,0xA5),output(static_cast<size_t>(rowbytes)*24,0xEE);
  for(int y=0;y<24;++y)std::memcpy(input.data()+static_cast<size_t>(y)*rowbytes,source.data()+static_cast<size_t>(y)*24*pixel_bytes,24*pixel_bytes);
  const auto input_before=input,output_before=output;
  PF_EffectWorld in{},out{};in.data=reinterpret_cast<PF_PixelPtr>(input.data());in.rowbytes=rowbytes;in.width=in.height=24;in.extent_hint={0,0,24,24};out=in;out.data=reinterpret_cast<PF_PixelPtr>(output.data());
  g_output=&out;g_format=depth==8?PF_PixelFormat_ARGB32:depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;g_acquire=g_release=g_get=g_copy=0;
  SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;PF_UtilCallbacks utils{};utils.copy=copy_world;PF_InData id{};PF_OutData od{};id.pica_basicP=&basic;id.utils=&utils;
  PF_ParamDef defs[6]{};defs[0].u.ld=in;defs[1].u.fs_d.value=amount;defs[2].u.fd.value=100*65536;defs[3].u.sd.value=2;defs[4].u.pd.value=bias;defs[5].u.bd.value=legacy;PF_ParamDef *params[]={&defs[0],&defs[1],&defs[2],&defs[3],&defs[4],&defs[5]};g_input=&defs[0].u.ld;
  const PF_EffectWorld input_header=defs[0].u.ld,out_header=out;const PF_Err err=EffectMain(PF_Cmd_RENDER,&id,&od,params,&out,nullptr);
  bool active=true,pad=true;for(int y=0;y<24;++y){active&=!std::memcmp(output.data()+static_cast<size_t>(y)*rowbytes,source.data()+static_cast<size_t>(y)*24*pixel_bytes,24*pixel_bytes);for(int x=24*pixel_bytes;x<rowbytes;++x)pad&=output[static_cast<size_t>(y)*rowbytes+x]==0xA5;}
  const bool headers=!std::memcmp(&defs[0].u.ld,&input_header,sizeof(input_header))&&!std::memcmp(&out,&out_header,sizeof(out));
  const bool exact=admitted?(!err&&active&&pad&&input==input_before&&headers&&g_acquire==1&&g_get==2&&g_release==1&&g_copy==1):(err==PF_Err_BAD_CALLBACK_PARAM&&output==output_before&&input==input_before&&headers&&g_copy==0);
  std::printf("CLASSIC PF%d_bias%d_legacy%d_amount%.1f exact=%d err=%d copy=%d suite=%d/%d/%d\n",depth,bias,legacy,amount,exact,err,g_copy,g_acquire,g_get,g_release);return exact;
}
int main(int argc,char **argv){if(argc!=2)return 2;g_world_suite.PF_GetPixelFormat=get_format;bool ok=true;int positives=0,negatives=0;for(short depth:{(short)8,(short)16})for(int bias:{1,2})for(int legacy:{0,1}){ok&=run_case(argv[1],depth,bias,legacy,5.0,true);++positives;}ok&=run_case(argv[1],32,1,0,5.0,false);++negatives;ok&=run_case(argv[1],8,1,0,6.0,false);++negatives;std::printf("all_exact=%d positive_rows=%d negative_rows=%d\n",ok,positives,negatives);return ok?0:3;}

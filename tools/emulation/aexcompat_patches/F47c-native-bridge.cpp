// SDK-typed C ABI bridge. Pixels and parameter definitions are snapshots of the
// Rust ClassicHost arena; no numerical implementation or plug-in source here.
#include "AEConfig.h"
#include "AE_Effect.h"
#include "AE_EffectCB.h"
#include "AE_EffectCBSuites.h"
#include "SPBasic.h"
#include "SPErrorCodes.h"
#include <dlfcn.h>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <algorithm>

using Entry = PF_Err (*)(PF_Cmd, PF_InData*, PF_OutData*, PF_ParamDef**, PF_LayerDef*, void*);
struct State {
 PF_EffectWorld *src, *dst;
 PF_ParamDef *params;
 short depth;
 int declarations=0, acquisitions=0, releases=0, formats=0, checkouts=0, checkins=0;
 bool failed=false;
};
static thread_local State *s;
static PF_Err fail(const char *name) {
 std::fprintf(stderr,"F47c unsupported/invalid callback: %s\n",name);
 if(s) s->failed=true;
 return PF_Err_BAD_CALLBACK_PARAM;
}
static PF_Err add(PF_ProgPtr, A_long index, PF_ParamDef *p) {
 if(!p || s->declarations>=5 || (index!=-1 && index!=s->declarations+1)) return fail("add_param");
 ++s->declarations;
 if(p->param_type!=s->params[s->declarations].param_type) return fail("parameter type drift");
 return 0;
}
static PF_Err param(PF_ProgPtr, PF_ParamIndex i,A_long,A_long,A_u_long,PF_ParamDef *p) {
 if(!p || i<1 || i>5) return fail("checkout_param");
 *p=s->params[i]; ++s->checkouts; return 0;
}
static PF_Err checkin(PF_ProgPtr,PF_ParamDef *p) {
 if(!p) return fail("checkin_param"); ++s->checkins; return 0;
}
static PF_Err pre(PF_ProgPtr,PF_ParamIndex i,A_long id,const PF_RenderRequest *r,A_long,A_long,A_u_long,PF_CheckoutResult *out) {
 if(i || id || !r || !out) return fail("checkout_layer");
 *out={}; out->result_rect=s->src->extent_hint; out->max_result_rect=s->src->extent_hint;
 out->ref_width=s->src->width; out->ref_height=s->src->height; return 0;
}
static PF_Err pixels(PF_ProgPtr,A_long id,PF_EffectWorld **w) {
 if(id || !w) return fail("checkout_layer_pixels"); *w=s->src; return 0;
}
static PF_Err output(PF_ProgPtr,PF_EffectWorld **w) {
 if(!w) return fail("checkout_output"); *w=s->dst; return 0;
}
static PF_Err pixel_checkin(PF_ProgPtr,A_long id) {return id?fail("checkin_layer_pixels"):0;}
static PF_Err format(const PF_EffectWorld *w,PF_PixelFormat *f) {
 if(!f || (w!=s->src && w!=s->dst)) return fail("GetPixelFormat");
 *f=s->depth==8?PF_PixelFormat_ARGB32:s->depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
 ++s->formats; return 0;
}
static PF_Err new_world(PF_ProgPtr,A_long,A_long,PF_Boolean,PF_PixelFormat,PF_EffectWorld*) {return fail("NewWorld");}
static PF_Err dispose_world(PF_ProgPtr,PF_EffectWorld*) {return fail("DisposeWorld");}
static PF_WorldSuite2 world_suite={new_world,dispose_world,format};
static SPErr acquire(const char *name,int32 version,const void **ptr) {
 if(ptr) *ptr=nullptr;
 const bool ok=name && ptr && !std::strcmp(name,kPFWorldSuite) && version==kPFWorldSuiteVersion2;
 std::fprintf(stderr,"F47c AcquireSuite %s %d supported=%d\n",name?name:"<null>",version,ok);
 if(!ok) {fail("AcquireSuite"); return kSPSuiteNotFoundError;}
 *ptr=&world_suite; ++s->acquisitions; return 0;
}
static SPErr release(const char *name,int32 version) {
 if(!name || std::strcmp(name,kPFWorldSuite) || version!=kPFWorldSuiteVersion2 || s->releases>=s->acquisitions) {
 fail("ReleaseSuite"); return kSPSuiteNotFoundError;
 }
 ++s->releases; return 0;
}
static PF_Err copy(PF_ProgPtr,PF_EffectWorld *src,PF_EffectWorld *dst,PF_Rect *sr,PF_Rect *dr) {
 const size_t packed=size_t(src?src->width:0)*s->depth/8*4;
 if(!src || !dst || !src->data || !dst->data || sr || dr || src->width!=dst->width || src->height!=dst->height || src->rowbytes<packed || dst->rowbytes<packed) return fail("copy");
 for(int y=0;y<src->height;++y) std::memmove((char*)dst->data+y*dst->rowbytes,(char*)src->data+y*src->rowbytes,packed);
 return 0;
}
static PF_Err abort_cb(PF_ProgPtr) {return 0;}
static PF_Err progress(PF_ProgPtr,A_long,A_long) {return 0;}
static PF_Handle new_handle(A_u_longlong) {fail("new_handle"); return nullptr;}
static void *lock_handle(PF_Handle) {fail("lock_handle"); return nullptr;}
static void unlock_handle(PF_Handle) {fail("unlock_handle");}
static void dispose_handle(PF_Handle) {fail("dispose_handle");}
static A_u_longlong handle_size(PF_Handle) {fail("handle_size"); return 0;}
extern "C" int f47c_render(const char *path, const unsigned char *input_bytes,
 unsigned char *parameter_bytes, unsigned char *src_bytes,unsigned char *dst_bytes,
 unsigned char *src_pixels,unsigned char *dst_pixels,short depth,const int *request) {
 if(s || !path || (depth!=8 && depth!=16 && depth!=32)) return 516;
 void *module=dlopen(path,RTLD_NOW|RTLD_LOCAL);
 if(!module) {std::fprintf(stderr,"F47c dlopen: %s\n",dlerror()); return 516;}
 auto entry=reinterpret_cast<Entry>(dlsym(module,"EffectMain"));
 if(!entry) {dlclose(module); return 516;}
 PF_InData in; std::memcpy(&in,input_bytes,sizeof(in));
 PF_EffectWorld src,dst;
 std::memcpy(&src,src_bytes,sizeof(src)); std::memcpy(&dst,dst_bytes,sizeof(dst));
 const size_t src_size=size_t(src.rowbytes)*src.height, dst_size=size_t(dst.rowbytes)*dst.height;
 std::vector<unsigned char> source(src_size+128,0xA7), destination(dst_size+128,0xA7);
 std::memcpy(source.data()+64,src_pixels,src_size); std::memcpy(destination.data()+64,dst_pixels,dst_size);
 src.data=reinterpret_cast<PF_Pixel*>(source.data()+64); dst.data=reinterpret_cast<PF_Pixel*>(destination.data()+64);
 PF_ParamDef params[6]; std::memcpy(params,parameter_bytes,sizeof(params));
 State state{&src,&dst,params,depth}; s=&state;
 PF_OutData out{}; SPBasicSuite basic{}; PF_UtilCallbacks utils{};
 basic.AcquireSuite=acquire; basic.ReleaseSuite=release;
 in.pica_basicP=&basic; in.utils=&utils; in.inter={};
 in.inter.add_param=add; in.inter.checkout_param=param; in.inter.checkin_param=checkin;
 in.inter.abort=abort_cb; in.inter.progress=progress;
 in.global_data=nullptr; in.sequence_data=nullptr; in.frame_data=nullptr;
 utils.copy=copy; utils.host_new_handle=new_handle; utils.host_lock_handle=lock_handle;
 utils.host_unlock_handle=unlock_handle; utils.host_dispose_handle=dispose_handle; utils.host_get_handle_size=handle_size;
 bool global=false,sequence=false; PF_Err err=0;
 auto call=[&](PF_Cmd cmd,void *extra=nullptr) {
  PF_Err e=entry(cmd,&in,&out,nullptr,nullptr,extra);
  std::fprintf(stderr,"F47c selector %d error=%d\n",int(cmd),int(e));
  in.global_data=out.global_data; in.sequence_data=out.sequence_data; return e;
 };
 try {
  err=call(PF_Cmd_GLOBAL_SETUP); global=!err;
  if(!err) err=call(PF_Cmd_PARAMS_SETUP);
  if(!err && (state.declarations!=5 || out.num_params!=6)) err=fail("declaration count");
  if(!err) {err=call(PF_Cmd_SEQUENCE_SETUP); sequence=!err;}
  PF_PreRenderInput pi{}; PF_PreRenderOutput po{}; PF_PreRenderCallbacks pc{}; PF_PreRenderExtra pe{};
  pi.bitdepth=depth; pi.output_request.rect={request[0],request[1],request[2],request[3]};
  pc.checkout_layer=pre; pe.input=&pi; pe.output=&po; pe.cb=&pc;
  if(!err) err=call(PF_Cmd_SMART_PRE_RENDER,&pe);
  PF_SmartRenderInput si{}; PF_SmartRenderCallbacks sc{}; PF_SmartRenderExtra se{};
  si.bitdepth=depth; si.output_request=pi.output_request; si.pre_render_data=po.pre_render_data;
  sc.checkout_layer_pixels=pixels; sc.checkout_output=output; sc.checkin_layer_pixels=pixel_checkin;
  se.input=&si; se.cb=&sc;
  if(!err) err=call(PF_Cmd_SMART_RENDER,&se);
  if(po.pre_render_data) {fail("unexpected pre_render_data");}
  if(sequence) {auto e=call(PF_Cmd_SEQUENCE_SETDOWN); if(!err) err=e;}
  if(global) {auto e=call(PF_Cmd_GLOBAL_SETDOWN); if(!err) err=e;}
 } catch(...) {err=fail("exception across entry");}
 if(state.acquisitions!=state.releases || state.checkouts!=state.checkins) err=fail("unbalanced checkout/suite");
 std::fprintf(stderr,"F47c counters declarations=%d acquire=%d release=%d formats=%d checkout=%d checkin=%d\n",state.declarations,state.acquisitions,state.releases,state.formats,state.checkouts,state.checkins);
 auto guards=[](const std::vector<unsigned char>& v) {
  return std::all_of(v.begin(),v.begin()+64,[](auto b){return b==0xA7;}) &&
         std::all_of(v.end()-64,v.end(),[](auto b){return b==0xA7;});
 };
 if(!guards(source) || !guards(destination) || std::memcmp(src_pixels,source.data()+64,src_size))
  err=fail("native snapshot guards/input mutation");
 std::memcpy(dst_pixels,destination.data()+64,dst_size);
 if(state.failed && !err) err=516;
 s=nullptr; dlclose(module); return err;
}

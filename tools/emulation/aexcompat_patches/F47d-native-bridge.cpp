// SDK-typed C ABI bridge. Pixels and parameter definitions are snapshots of the
// Rust ClassicHost arena; no numerical implementation or plug-in source here.
#include "AEConfig.h"
#include "AE_Effect.h"
#include "AE_EffectCB.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "AE_GeneralPlug.h"
#include "SPBasic.h"
#include "SPErrorCodes.h"
#include <dlfcn.h>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <algorithm>
#include <unordered_map>

using Entry = PF_Err (*)(PF_Cmd, PF_InData*, PF_OutData*, PF_ParamDef**, PF_LayerDef*, void*);
#ifdef OLM_F52_BUNDLE_GEOMETRY
static Entry f52_bundle_entry;
static PF_Err EffectMain(PF_Cmd cmd,PF_InData *in,PF_OutData *out,PF_ParamDef **params,PF_LayerDef *world,void *extra) {
 return f52_bundle_entry(cmd,in,out,params,world,extra);
}
#include "../../fuzz/harnesses/geometry.hpp"
#undef EffectMain
#endif
struct State {
 PF_EffectWorld *src, *dst;
 PF_ParamDef *params;
 short depth;
 int count;
 int declarations=0, acquisitions=0, releases=0, formats=0, checkouts=0, checkins=0;
 bool failed=false;
 bool default_ramps=false;
 std::unordered_map<PF_Handle,A_u_longlong> handles;
};
static thread_local State *s;
static PF_Err fail(const char *name) {
 std::fprintf(stderr,"F47c unsupported/invalid callback: %s\n",name);
 if(s) s->failed=true;
 return PF_Err_BAD_CALLBACK_PARAM;
}
static PF_Err add(PF_ProgPtr, A_long index, PF_ParamDef *p) {
 if(!p || s->declarations>=s->count-1 || (index!=-1 && index!=s->declarations+1)) return fail("add_param");
 ++s->declarations;
 auto &actual=s->params[s->declarations];
 if(s->default_ramps && p->param_type==PF_Param_ARBITRARY_DATA && actual.param_type==PF_Param_ARBITRARY_DATA) {
  // The scalar-only fuzz protocol never supplies arbitrary payloads. Retain
  // the native builder's default handles, as the existing source host does.
  actual=*p; actual.u.arb_d.value=p->u.arb_d.dephault;
 } else if(s->default_ramps && p->param_type==PF_Param_FLOAT_SLIDER && actual.param_type==PF_Param_ANGLE) {
  // Kira's recovered source interface consumes the original raw fixed angle
  // as degrees. This is the same typed mapping as adapters/olmkirakira.py.
  const auto raw=actual.u.ad.value; actual=*p; actual.u.fs_d.value=raw;
  std::fprintf(stderr,"F47d parameter ANGLE-to-FLOAT_SLIDER slot=%d\n",s->declarations);
 } else if(p->param_type!=actual.param_type) return fail("parameter type drift");
 return 0;
}
static PF_Err param(PF_ProgPtr, PF_ParamIndex i,A_long,A_long,A_u_long,PF_ParamDef *p) {
 if(!p || i<1 || i>=s->count) return fail("checkout_param");
 *p=s->params[i]; ++s->checkouts; return 0;
}
static PF_Err checkin(PF_ProgPtr,PF_ParamDef *p) {
 if(!p) return fail("checkin_param"); ++s->checkins; return 0;
}
static PF_Err pre(PF_ProgPtr,PF_ParamIndex i,A_long id,const PF_RenderRequest *r,A_long,A_long,A_u_long,PF_CheckoutResult *out) {
 if(i>0 && i<s->count && s->params[i].param_type==PF_Param_LAYER) { *out={}; return PF_Err_BAD_CALLBACK_PARAM; }
 if(i || id || !r || !out) return fail("checkout_layer");
 *out={}; out->result_rect=s->src->extent_hint; out->max_result_rect=s->src->extent_hint;
 out->ref_width=s->src->width; out->ref_height=s->src->height; return 0;
}
static PF_Err pixels(PF_ProgPtr,A_long id,PF_EffectWorld **w) {
 if(id>0 && id<s->count && s->params[id].param_type==PF_Param_LAYER && w) { *w=nullptr; return PF_Err_BAD_CALLBACK_PARAM; }
 if(id || !w) return fail("checkout_layer_pixels"); *w=s->src; return 0;
}
static PF_Err output(PF_ProgPtr,PF_EffectWorld **w) {
 if(!w) return fail("checkout_output"); *w=s->dst; return 0;
}
static PF_Err pixel_checkin(PF_ProgPtr,A_long id) {return id?fail("checkin_layer_pixels"):0;}
static PF_Err format(const PF_EffectWorld *w,PF_PixelFormat *f) {
 if(!f || (w!=s->src && w!=s->dst && w!=&s->params[0].u.ld)) return fail("GetPixelFormat");
 *f=s->depth==8?PF_PixelFormat_ARGB32:s->depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
 ++s->formats; return 0;
}
static PF_Err new_world(PF_ProgPtr,A_long,A_long,PF_Boolean,PF_PixelFormat,PF_EffectWorld*) {return fail("NewWorld");}
static PF_Err dispose_world(PF_ProgPtr,PF_EffectWorld*) {return fail("DisposeWorld");}
static PF_WorldSuite2 world_suite={new_world,dispose_world,format};
static PF_Err color(PF_ProgPtr,const PF_ParamDef *p,PF_PixelFloat *c) {
 if(!p || !c || p->param_type!=PF_Param_COLOR) return fail("ColorParam");
 c->alpha=p->u.cd.value.alpha/255.0f; c->red=p->u.cd.value.red/255.0f;
 c->green=p->u.cd.value.green/255.0f; c->blue=p->u.cd.value.blue/255.0f; return 0;
}
static PF_ColorParamSuite1 color_suite={color};
// SDK ordinary iterate clips the requested area to both worlds; independent rowbytes.
template<typename Pixel>
static PF_Err iterate(PF_InData*,A_long,A_long,PF_EffectWorld *src,const PF_Rect *area,
 void *refcon,PF_Err (*fn)(void*,A_long,A_long,Pixel*,Pixel*),PF_EffectWorld *dst) {
 if(!src || !dst || !src->data || !dst->data || !fn ||
    src->width<0 || dst->width<0 || src->height<0 || dst->height<0 ||
    src->rowbytes<src->width*sizeof(Pixel) || dst->rowbytes<dst->width*sizeof(Pixel)) return fail("iterate");
 const A_long left=area?std::max<A_long>(0,area->left):0;
 const A_long top=area?std::max<A_long>(0,area->top):0;
 const A_long right=std::min<A_long>(std::min(src->width,dst->width),area?area->right:dst->width);
 const A_long bottom=std::min<A_long>(std::min(src->height,dst->height),area?area->bottom:dst->height);
 for(A_long y=top;y<bottom;++y) for(A_long x=left;x<right;++x) {
  Pixel in_pixel,out_pixel;
  auto in_ptr=(char*)src->data+y*src->rowbytes+x*sizeof(Pixel);
  auto out_ptr=(char*)dst->data+y*dst->rowbytes+x*sizeof(Pixel);
  std::memcpy(&in_pixel,in_ptr,sizeof(Pixel)); std::memcpy(&out_pixel,out_ptr,sizeof(Pixel));
  auto err=fn(refcon,x,y,&in_pixel,&out_pixel); if(err) return err;
  std::memcpy(out_ptr,&out_pixel,sizeof(Pixel));
 }
 return 0;
}
static PF_Iterate8Suite2 iterate8={iterate<PF_Pixel>};
static PF_Iterate16Suite2 iterate16={iterate<PF_Pixel16>};
static PF_IterateFloatSuite2 iterate_float={iterate<PF_PixelFloat>};
static A_Err register_plugin(AEGP_GlobalRefcon,const A_char *name,AEGP_PluginID *id) {
 if(!name || !id) return fail("RegisterWithAEGP"); *id=1; return 0;
}
static AEGP_UtilitySuite6 utility_suite{};
static PF_Handle new_handle(A_u_longlong size) {
 if(!size || size>16*1024*1024) {fail("new_handle size"); return nullptr;}
 auto h=reinterpret_cast<PF_Handle>(std::malloc(sizeof(void*)));
 if(!h) return nullptr;
 *h=static_cast<char*>(std::calloc(1,size));
 if(!*h) {std::free(h);return nullptr;}
 s->handles[h]=size; return h;
}
static void *lock_handle(PF_Handle h) {
 if(!s->handles.count(h)) {fail("lock_handle");return nullptr;} return *h;
}
static void unlock_handle(PF_Handle h) {if(!s->handles.count(h)) fail("unlock_handle");}
static void dispose_handle(PF_Handle h) {
 if(!s->handles.erase(h)) {fail("dispose_handle");return;}
 std::free(*h);std::free(h);
}
static A_u_longlong handle_size(PF_Handle h) {
 auto it=s->handles.find(h); if(it==s->handles.end()) {fail("handle_size");return 0;} return it->second;
}
static PF_Err resize_handle(A_HandleSize,PF_Handle*) {return fail("resize_handle");}
static PF_HandleSuite1 handle_suite={new_handle,lock_handle,unlock_handle,dispose_handle,handle_size,resize_handle};
static PF_Err register_ui(PF_ProgPtr,PF_CustomUIInfo *info) {
 if(!info) return fail("register_ui");
 std::fprintf(stderr,"F47d register_ui events=%d\n",int(info->events)); return 0;
}
static const void *suite(const char *name,int32 version) {
 if(!name) return nullptr;
 if(!std::strcmp(name,kPFHandleSuite) && version==kPFHandleSuiteVersion1) return &handle_suite;
 if(!std::strcmp(name,kPFIterate8Suite) && version==kPFIterate8SuiteVersion2) return &iterate8;
 if(!std::strcmp(name,kPFIterate16Suite) && version==kPFIterate16SuiteVersion2) return &iterate16;
 if(!std::strcmp(name,kPFIterateFloatSuite) && version==kPFIterateFloatSuiteVersion2) return &iterate_float;
 if(!std::strcmp(name,kAEGPUtilitySuite) && version==kAEGPUtilitySuiteVersion6) {
  utility_suite.AEGP_RegisterWithAEGP=register_plugin; return &utility_suite;
 }
 if(!std::strcmp(name,kPFWorldSuite) && version==kPFWorldSuiteVersion2) return &world_suite;
 if(!std::strcmp(name,kPFColorParamSuite) && version==kPFColorParamSuiteVersion1) return &color_suite;
 return nullptr;
}
static SPErr acquire(const char *name,int32 version,const void **ptr) {
 const void *value=suite(name,version);
 std::fprintf(stderr,"F47c AcquireSuite %s %d supported=%d\n",name?name:"<null>",version,value!=nullptr);
 if(ptr) *ptr=value;
 if(!ptr || !value) {fail("AcquireSuite"); return kSPSuiteNotFoundError;}
 ++s->acquisitions; return 0;
}
static SPErr release(const char *name,int32 version) {
 if(!suite(name,version) || s->releases>=s->acquisitions) {fail("ReleaseSuite"); return kSPSuiteNotFoundError;}
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
extern "C" int f47c_render(const char *path, const unsigned char *input_bytes,
 unsigned char *parameter_bytes, unsigned char *src_bytes,unsigned char *dst_bytes,
 unsigned char *src_pixels,unsigned char *dst_pixels,short depth,const int *request, int count, int smart) {
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
 std::vector<PF_ParamDef> params(count); std::memcpy(params.data(),parameter_bytes,count*sizeof(PF_ParamDef));
 params[0].u.ld=src;
 std::vector<PF_ParamDef*> pointers;
 for(auto &p:params) {
  if(p.param_type==PF_Param_LAYER && &p!=&params[0]) p.u.ld={};
  pointers.push_back(&p);
 }
 State state{&src,&dst,params.data(),depth,count}; s=&state;
 const char *profile=std::getenv("OLM_NATIVE_PARAMETER_PROFILE");
 state.default_ramps=profile && !std::strcmp(profile,"kirakira-default-ramps");
 PF_OutData out{}; SPBasicSuite basic{}; PF_UtilCallbacks utils{};
 basic.AcquireSuite=acquire; basic.ReleaseSuite=release;
 in.pica_basicP=&basic; in.utils=&utils; in.inter={};
 in.inter.add_param=add; in.inter.checkout_param=param; in.inter.checkin_param=checkin;
 in.inter.register_ui=register_ui; in.inter.abort=abort_cb; in.inter.progress=progress;
 in.global_data=nullptr; in.sequence_data=nullptr; in.frame_data=nullptr;
 utils.copy=copy; utils.host_new_handle=new_handle; utils.host_lock_handle=lock_handle;
 utils.host_unlock_handle=unlock_handle; utils.host_dispose_handle=dispose_handle; utils.host_get_handle_size=handle_size;
 bool global=false,sequence=false; PF_Err err=0;
 auto call=[&](PF_Cmd cmd,void *extra=nullptr) {
#ifdef OLM_F52_BUNDLE_GEOMETRY
  f52_bundle_entry=entry;
  PF_Err e=f52_entry(cmd,&in,&out,pointers.data(),&dst,extra);
#else
  PF_Err e=entry(cmd,&in,&out,pointers.data(),&dst,extra);
#endif
  std::fprintf(stderr,"F47c selector %d error=%d\n",int(cmd),int(e));
  in.global_data=out.global_data; in.sequence_data=out.sequence_data; return e;
 };
 try {
  err=call(PF_Cmd_GLOBAL_SETUP); global=!err;
  if(!err) err=call(PF_Cmd_PARAMS_SETUP);
  if(!err && (state.declarations!=count-1 || out.num_params!=count)) err=fail("declaration count");
  if(!err) {err=call(PF_Cmd_SEQUENCE_SETUP); sequence=!err;}
  PF_PreRenderInput pi{}; PF_PreRenderOutput po{}; PF_PreRenderCallbacks pc{}; PF_PreRenderExtra pe{};
  pi.bitdepth=depth; pi.output_request.rect={request[0],request[1],request[2],request[3]};
  pc.checkout_layer=pre; pe.input=&pi; pe.output=&po; pe.cb=&pc;
  if(!err && smart) err=call(PF_Cmd_SMART_PRE_RENDER,&pe);
  PF_SmartRenderInput si{}; PF_SmartRenderCallbacks sc{}; PF_SmartRenderExtra se{};
  si.bitdepth=depth; si.output_request=pi.output_request; si.pre_render_data=po.pre_render_data;
  sc.checkout_layer_pixels=pixels; sc.checkout_output=output; sc.checkin_layer_pixels=pixel_checkin;
  se.input=&si; se.cb=&sc;
  if(!err) err=smart?call(PF_Cmd_SMART_RENDER,&se):call(PF_Cmd_RENDER);
  if(po.pre_render_data) { if(po.delete_pre_render_data_func) po.delete_pre_render_data_func(po.pre_render_data); else fail("missing pre_render_data deleter"); }
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
 while(!state.handles.empty()) dispose_handle(state.handles.begin()->first);
 s=nullptr; dlclose(module); return err;
}

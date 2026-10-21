#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <fstream>
#include <cstdlib>
#include <string>
#include <vector>
#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../../mac/OLMBlur/OLMBlur.cpp"

static bool g_fail_next_new = false;
void *operator new(std::size_t size) {
  if (g_fail_next_new) { g_fail_next_new=false; throw std::bad_alloc(); }
  if (void *p=std::malloc(size)) return p; throw std::bad_alloc();
}
void operator delete(void *p) noexcept { std::free(p); }
void operator delete(void *p, std::size_t) noexcept { std::free(p); }

static PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
static short g_depth = 0;
static int g_legacy = 0;
static int g_pre = 0, g_pixels = 0, g_output_hits = 0, g_optional_checkin = 0;
static int g_param_out = 0, g_param_in = 0, g_copy = 0;
static int g_acquire = 0, g_release = 0, g_get_format = 0;
static bool g_request_exact = false;
static PF_RenderRequest g_expected_request{};
static PF_WorldSuite2 g_world_suite{};
static PF_WorldSuite2 g_null_world_suite{};
enum CallbackMode { NORMAL, LAYER_ERROR, OUTPUT_ERROR, PARAM_OUT_ERROR, PARAM_IN_ERROR,
  ACQUIRE_ERROR, ACQUIRE_NULL, FORMAT_FN_NULL, INPUT_FORMAT_ERROR, OUTPUT_FORMAT_ERROR,
  RELEASE_ERROR, ACQUIRE_THROW_PF, ACQUIRE_THROW_OOM, ACQUIRE_THROW_OTHER,
  GET_THROW_PF, GET_THROW_OOM, GET_THROW_OTHER, RELEASE_THROW_PF, RELEASE_THROW_OOM,
  RELEASE_THROW_OTHER, LAYER_THROW_PF, LAYER_THROW_OOM, LAYER_THROW_OTHER,
  OUTPUT_THROW_PF, OUTPUT_THROW_OOM, OUTPUT_THROW_OTHER, PARAM_OUT_THROW_PF,
  PARAM_OUT_THROW_OOM, PARAM_OUT_THROW_OTHER, PARAM_IN_THROW_PF,
  PARAM_IN_THROW_OOM, PARAM_IN_THROW_OTHER, COPY_ERROR, COPY_THROW_PF,
  COPY_THROW_OOM, COPY_THROW_OTHER, PRE_ERROR, PRE_THROW_PF, PRE_THROW_OOM,
  PRE_THROW_OTHER };
static CallbackMode g_mode = NORMAL;
static int g_fail_ordinal = 0;
static double g_amount = 5.0;
static int g_smooth = 100 * 65536, g_repeat = 1, g_bias = 1;
static PF_PixelFormat g_input_format_override = PF_PixelFormat_INVALID;
static PF_PixelFormat g_output_format_override = PF_PixelFormat_INVALID;

static std::vector<unsigned char> read_file(const std::string &path) {
  std::ifstream f(path, std::ios::binary);
  return std::vector<unsigned char>(std::istreambuf_iterator<char>(f), {});
}

static PF_Err copy_world(PF_ProgPtr, PF_EffectWorld *src, PF_EffectWorld *dst,
                         PF_Rect *, PF_Rect *) {
  ++g_copy;
  if (g_mode == COPY_ERROR) return 86;
  if (g_mode == COPY_THROW_PF) { PF_Err e=87; throw e; }
  if (g_mode == COPY_THROW_OOM) throw std::bad_alloc();
  if (g_mode == COPY_THROW_OTHER) throw 87.5;
  if (!src || !dst || !src->data || !dst->data || src->width != dst->width ||
      src->height != dst->height || src->rowbytes != dst->rowbytes) return 91;
  for (A_long y = 0; y < src->height; ++y) {
    std::memcpy(reinterpret_cast<unsigned char *>(dst->data) + static_cast<size_t>(y) * dst->rowbytes,
                reinterpret_cast<unsigned char *>(src->data) + static_cast<size_t>(y) * src->rowbytes,
                static_cast<size_t>(src->rowbytes));
  }
  return PF_Err_NONE;
}

static PF_Err checkout_param(PF_ProgPtr, PF_ParamIndex index, A_long, A_long,
                             A_u_long, PF_ParamDef *param) {
  if (!param || index < 1 || index > 5) return 92;
  std::memset(param, 0, sizeof(*param)); ++g_param_out;
  if (g_mode == PARAM_OUT_ERROR && g_param_out == g_fail_ordinal) return 72;
  if (g_param_out == g_fail_ordinal && g_mode == PARAM_OUT_THROW_PF) { PF_Err e=81; throw e; }
  if (g_param_out == g_fail_ordinal && g_mode == PARAM_OUT_THROW_OOM) throw std::bad_alloc();
  if (g_param_out == g_fail_ordinal && g_mode == PARAM_OUT_THROW_OTHER) throw 81.5;
  if (index == 1) param->u.fs_d.value = g_amount;
  else if (index == 2) param->u.fd.value = g_smooth;
  else if (index == 3) param->u.sd.value = g_repeat;
  else if (index == 4) param->u.pd.value = g_bias;
  else param->u.bd.value = g_legacy;
  return PF_Err_NONE;
}
static PF_Err checkin_param(PF_ProgPtr, PF_ParamDef *) {
  ++g_param_in;
  if (g_param_in == g_fail_ordinal && g_mode == PARAM_IN_THROW_PF) { PF_Err e=82; throw e; }
  if (g_param_in == g_fail_ordinal && g_mode == PARAM_IN_THROW_OOM) throw std::bad_alloc();
  if (g_param_in == g_fail_ordinal && g_mode == PARAM_IN_THROW_OTHER) throw 82.5;
  return g_mode == PARAM_IN_ERROR && g_param_in == g_fail_ordinal ? 73 : PF_Err_NONE;
}

static PF_Err pre_checkout(PF_ProgPtr, PF_ParamIndex index, A_long checkout_id,
                           const PF_RenderRequest *request, A_long, A_long,
                           A_u_long, PF_CheckoutResult *result) {
  ++g_pre;
  if (g_mode == PRE_ERROR) return 88;
  if (g_mode == PRE_THROW_PF) { PF_Err e=89; throw e; }
  if (g_mode == PRE_THROW_OOM) throw std::bad_alloc();
  if (g_mode == PRE_THROW_OTHER) throw 89.5;
  g_request_exact = index == 0 && checkout_id == 0 && request &&
                    std::memcmp(request, &g_expected_request, sizeof(*request)) == 0;
  if (!result) return 93;
  std::memset(result, 0, sizeof(*result));
  result->result_rect = {0, 0, 24, 24};
  result->max_result_rect = {0, 0, 24, 24};
  result->ref_width = 24; result->ref_height = 24;
  return PF_Err_NONE;
}
static PF_Err pixels(PF_ProgPtr, A_long id, PF_EffectWorld **world) {
  ++g_pixels; if (g_mode == LAYER_ERROR) return 70;
  if (g_mode == LAYER_THROW_PF) { PF_Err e=83; throw e; }
  if (g_mode == LAYER_THROW_OOM) throw std::bad_alloc();
  if (g_mode == LAYER_THROW_OTHER) throw 83.5;
  if (id != 0 || !world) return 94; *world = g_input; return PF_Err_NONE;
}
static PF_Err optional_checkin(PF_ProgPtr, A_long) { ++g_optional_checkin; return PF_Err_NONE; }
static PF_Err checkout_output(PF_ProgPtr, PF_EffectWorld **world) {
  ++g_output_hits; if (g_mode == OUTPUT_ERROR) return 71;
  if (g_mode == OUTPUT_THROW_PF) { PF_Err e=84; throw e; }
  if (g_mode == OUTPUT_THROW_OOM) throw std::bad_alloc();
  if (g_mode == OUTPUT_THROW_OTHER) throw 84.5;
  if (!world) return 95; *world = g_output; return PF_Err_NONE;
}

static PF_Err get_format(const PF_EffectWorld *world, PF_PixelFormat *format) {
  ++g_get_format;
  if (!format || (world != g_input && world != g_output)) return 96;
  if (g_mode == GET_THROW_PF) { PF_Err e=77; throw e; }
  if (g_mode == GET_THROW_OOM) throw std::bad_alloc();
  if (g_mode == GET_THROW_OTHER) throw 77.5;
  if (world == g_input && g_mode == INPUT_FORMAT_ERROR) return 75;
  if (world == g_output && g_mode == OUTPUT_FORMAT_ERROR) return 76;
  const PF_PixelFormat normal = g_depth == 8 ? PF_PixelFormat_ARGB32 :
            g_depth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
  *format = world == g_input && g_input_format_override != PF_PixelFormat_INVALID ? g_input_format_override :
            world == g_output && g_output_format_override != PF_PixelFormat_INVALID ? g_output_format_override : normal;
  return PF_Err_NONE;
}
static SPErr acquire_suite(const char *name, int32 version, const void **suite) {
  ++g_acquire;
  if (!name || std::strcmp(name, kPFWorldSuite) || version != kPFWorldSuiteVersion2 || !suite)
    return kSPBadParameterError;
  if (g_mode == ACQUIRE_ERROR) return 74;
  if (g_mode == ACQUIRE_THROW_PF) { PF_Err e=78; throw e; }
  if (g_mode == ACQUIRE_THROW_OOM) throw std::bad_alloc();
  if (g_mode == ACQUIRE_THROW_OTHER) throw 78.5;
  *suite = g_mode == ACQUIRE_NULL ? nullptr : g_mode == FORMAT_FN_NULL ? &g_null_world_suite : &g_world_suite;
  return kSPNoError;
}
static SPErr release_suite(const char *name, int32 version) {
  ++g_release;
  if (g_mode == RELEASE_THROW_PF) { PF_Err e=79; throw e; }
  if (g_mode == RELEASE_THROW_OOM) throw std::bad_alloc();
  if (g_mode == RELEASE_THROW_OTHER) throw 79.5;
  if (g_mode == RELEASE_ERROR) return 80;
  return name && !std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2 ? kSPNoError : kSPBadParameterError;
}

static unsigned char *misaligned_payload(std::vector<unsigned char> &storage,
                                         size_t payload, size_t alignment) {
  for (size_t offset = 19; offset < 19 + alignment + 1; ++offset) {
    unsigned char *p = storage.data() + offset;
    if (alignment == 1 || reinterpret_cast<uintptr_t>(p) % alignment == 1 % alignment) {
      if (static_cast<size_t>(storage.data() + storage.size() - p) >= payload + 19) return p;
    }
  }
  return nullptr;
}

struct RunResult { bool pass; std::string id; int optional_present; int pre_err, render_err; };

enum NegMutation { SRC_FIRST, SRC_MIDDLE, SRC_LAST, AMOUNT_UP, AMOUNT_DOWN,
  SMOOTH_DOWN, SMOOTH_UP, REPEAT_DOWN, REPEAT_UP, BIAS_DOWN, BIAS_UP,
  LEGACY_INVALID, INPUT_WIDTH, OUTPUT_HEIGHT, INPUT_ROWBYTES, OUTPUT_ROWBYTES,
  INPUT_EXTENT, OUTPUT_EXTENT, INPUT_ORIGIN, OUTPUT_ORIGIN, INPUT_FLAGS,
  OUTPUT_FLAGS, INPUT_FORMAT, OUTPUT_FORMAT, DEPTH_WRONG, DSX_NUM, DSX_DEN,
  DSY_NUM, DSY_DEN, EXACT_ALIAS, OVERLAP_FORWARD, OVERLAP_BACKWARD,
  INPUT_DATA_NULL, OUTPUT_DATA_NULL, NULL_LAYER_FN, NULL_OUTPUT_FN,
  NULL_PARAM_OUT_FN, NULL_PARAM_IN_FN, NULL_PICA, NULL_ACQUIRE_FN,
  NULL_RELEASE_FN, STAGE_OOM, CALLBACK_MODE };

struct NegSpec { const char *id; short depth; NegMutation mutation; CallbackMode mode; int ordinal; PF_Err expected; };

static RunResult run_case(const std::string &fixture, short depth, int legacy, bool checkin_present) {
  const int pixel_bytes = depth == 8 ? 4 : depth == 16 ? 8 : 16;
  const int padding = depth == 8 ? 17 : depth == 16 ? 23 : 32;
  const int rowbytes = 24 * pixel_bytes + padding;
  const size_t payload_size = static_cast<size_t>(rowbytes) * 24;
  const char *source_name = depth == 8 ? "source_argb8.bin" : depth == 16 ? "source_argb16.bin" : "source_argb32.bin";
  const std::string expected_name = "expected_pf" + std::to_string(depth) +
      "_amount5_0_repeat1_legacy" + std::to_string(legacy) + ".bin";
  const auto source = read_file(fixture + "/" + source_name);
  const auto expected = read_file(fixture + "/" + expected_name);
  std::vector<unsigned char> input_store(19 + 16 + payload_size + 19, 0xC7);
  std::vector<unsigned char> output_store(19 + 16 + payload_size + 19, 0xD9);
  unsigned char *input_data = misaligned_payload(input_store, payload_size, pixel_bytes);
  unsigned char *output_data = misaligned_payload(output_store, payload_size, pixel_bytes);
  if (!input_data || !output_data || source.size() != static_cast<size_t>(24*24*pixel_bytes) ||
      expected.size() != source.size()) return {false,"fixture",checkin_present,0,0};
  for (int y=0; y<24; ++y) {
    std::memcpy(input_data + static_cast<size_t>(y)*rowbytes,
                source.data() + static_cast<size_t>(y)*24*pixel_bytes, 24*pixel_bytes);
    std::memset(input_data + static_cast<size_t>(y)*rowbytes + 24*pixel_bytes, 0xA5, padding);
    std::memset(output_data + static_cast<size_t>(y)*rowbytes, 0xEE, rowbytes);
  }
  const auto input_before = input_store, output_before = output_store;
  PF_EffectWorld input{}, output{};
  input.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
  input.data = reinterpret_cast<PF_PixelPtr>(input_data); input.rowbytes = rowbytes; input.width = input.height = 24;
  input.extent_hint = {0,0,24,24}; input.origin_x = input.origin_y = 0;
  output = input; output.data = reinterpret_cast<PF_PixelPtr>(output_data);
  const PF_EffectWorld input_header = input, output_header = output;
  g_input=&input; g_output=&output; g_depth=depth; g_legacy=legacy;
  g_pre=g_pixels=g_output_hits=g_optional_checkin=g_param_out=g_param_in=g_copy=0;
  g_acquire=g_release=g_get_format=0; g_request_exact=false;
  g_mode=NORMAL;g_fail_ordinal=0;g_amount=5.0;g_smooth=100*65536;g_repeat=1;g_bias=1;
  g_input_format_override=g_output_format_override=PF_PixelFormat_INVALID;
  SPBasicSuite basic{}; basic.AcquireSuite=acquire_suite; basic.ReleaseSuite=release_suite;
  PF_UtilCallbacks utils{}; utils.copy=copy_world;
  PF_InData in{}; PF_OutData out{}; in.effect_ref=reinterpret_cast<PF_ProgPtr>(0x1234);
  in.current_time=7; in.time_step=1; in.time_scale=24; in.downsample_x={1,1}; in.downsample_y={1,1};
  in.pica_basicP=&basic; in.utils=&utils; in.inter.checkout_param=checkout_param; in.inter.checkin_param=checkin_param;
  PF_PreRenderInput pre_input{}; pre_input.output_request.rect={0,0,24,24};
  pre_input.output_request.preserve_rgb_of_zero_alpha=FALSE; g_expected_request=pre_input.output_request;
  PF_PreRenderOutput pre_output{}; PF_PreRenderCallbacks pre_cb{}; pre_cb.checkout_layer=pre_checkout;
  PF_PreRenderExtra pre_extra{&pre_input,&pre_output,&pre_cb};
  const PF_Err pre_err=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pre_extra);
  PF_SmartRenderInput smart_input{}; smart_input.bitdepth=depth;
  PF_SmartRenderCallbacks smart_cb{}; smart_cb.checkout_layer_pixels=pixels;
  smart_cb.checkin_layer_pixels=checkin_present ? optional_checkin : nullptr;
  smart_cb.checkout_output=checkout_output;
  PF_SmartRenderExtra smart_extra{&smart_input,&smart_cb};
  const PF_Err render_err=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&smart_extra);
  bool active_exact=true,padding_exact=true,guards_exact=true;
  for(int y=0;y<24;++y){
    active_exact &= !std::memcmp(output_data+static_cast<size_t>(y)*rowbytes,
                                expected.data()+static_cast<size_t>(y)*24*pixel_bytes,24*pixel_bytes);
    for(int i=24*pixel_bytes;i<rowbytes;++i) padding_exact &= output_data[static_cast<size_t>(y)*rowbytes+i]==0xA5;
  }
  for(int i=1;i<=19;++i){guards_exact &= input_data[-i]==0xC7 && output_data[-i]==0xD9;
    guards_exact &= input_data[payload_size-1+i]==0xC7 && output_data[payload_size-1+i]==0xD9;}
  const bool pass=!pre_err&&!render_err&&active_exact&&padding_exact&&guards_exact&&
      input_store==input_before&&std::memcmp(&input,&input_header,sizeof(input))==0&&
      std::memcmp(&output,&output_header,sizeof(output))==0&&g_request_exact&&
      pre_output.result_rect.right==24&&pre_output.result_rect.bottom==24&&
      pre_output.max_result_rect.right==24&&pre_output.max_result_rect.bottom==24&&
      g_pre==1&&g_pixels==1&&g_output_hits==1&&g_optional_checkin==0&&
      g_param_out==5&&g_param_in==5&&g_copy==1&&g_acquire==1&&g_get_format==2&&g_release==1&&
      reinterpret_cast<uintptr_t>(input_data)%pixel_bytes==(pixel_bytes==1?0:1)&&
      output_store!=output_before;
  return {pass,"PF"+std::to_string(depth)+"_legacy"+std::to_string(legacy)+(checkin_present?"_present":"_null"),checkin_present,pre_err,render_err};
}

static bool run_negative(const std::string &fixture, const NegSpec &spec) {
  const short depth=spec.depth; const int pixel_bytes=depth==8?4:depth==16?8:16;
  const int padding=depth==8?17:depth==16?23:32; const int rowbytes=24*pixel_bytes+padding;
  const size_t payload_size=static_cast<size_t>(rowbytes)*24;
  const char *source_name=depth==8?"source_argb8.bin":depth==16?"source_argb16.bin":"source_argb32.bin";
  const auto source=read_file(fixture+"/"+source_name);
  std::vector<unsigned char> input_store(19+16+payload_size+19,0xC7),output_store(19+16+payload_size+19,0xD9);
  unsigned char *input_data=misaligned_payload(input_store,payload_size,pixel_bytes);
  unsigned char *output_data=misaligned_payload(output_store,payload_size,pixel_bytes);
  if(!input_data||!output_data||source.size()!=static_cast<size_t>(24*24*pixel_bytes))return false;
  for(int y=0;y<24;++y){std::memcpy(input_data+static_cast<size_t>(y)*rowbytes,source.data()+static_cast<size_t>(y)*24*pixel_bytes,24*pixel_bytes);
    std::memset(input_data+static_cast<size_t>(y)*rowbytes+24*pixel_bytes,0xA5,padding);std::memset(output_data+static_cast<size_t>(y)*rowbytes,0xEE,rowbytes);}
  if(spec.mutation==SRC_FIRST)input_data[0]^=1;
  if(spec.mutation==SRC_MIDDLE)input_data[static_cast<size_t>(12)*rowbytes+12*pixel_bytes]^=1;
  if(spec.mutation==SRC_LAST)input_data[static_cast<size_t>(23)*rowbytes+24*pixel_bytes-1]^=1;
  PF_EffectWorld input{},output{};input.world_flags=depth==8?0:PF_WorldFlag_DEEP;input.data=reinterpret_cast<PF_PixelPtr>(input_data);
  input.rowbytes=rowbytes;input.width=input.height=24;input.extent_hint={0,0,24,24};input.origin_x=input.origin_y=0;output=input;output.data=reinterpret_cast<PF_PixelPtr>(output_data);
  g_mode=spec.mode;g_fail_ordinal=spec.ordinal;g_amount=5.0;g_smooth=100*65536;g_repeat=1;g_bias=1;g_legacy=0;
  g_input_format_override=g_output_format_override=PF_PixelFormat_INVALID;
  if(spec.mutation==AMOUNT_UP)g_amount=std::nextafter(5.0,INFINITY);
  if(spec.mutation==AMOUNT_DOWN)g_amount=std::nextafter(5.0,-INFINITY);
  if(spec.mutation==SMOOTH_DOWN)--g_smooth;if(spec.mutation==SMOOTH_UP)++g_smooth;
  if(spec.mutation==REPEAT_DOWN)g_repeat=0;if(spec.mutation==REPEAT_UP)g_repeat=2;
  if(spec.mutation==BIAS_DOWN)g_bias=0;if(spec.mutation==BIAS_UP)g_bias=2;
  if(spec.mutation==LEGACY_INVALID)g_legacy=2;
  if(spec.mutation==INPUT_WIDTH)--input.width;if(spec.mutation==OUTPUT_HEIGHT)++output.height;
  if(spec.mutation==INPUT_ROWBYTES)--input.rowbytes;if(spec.mutation==OUTPUT_ROWBYTES)++output.rowbytes;
  if(spec.mutation==INPUT_EXTENT)--input.extent_hint.left;if(spec.mutation==OUTPUT_EXTENT)++output.extent_hint.right;
  if(spec.mutation==INPUT_ORIGIN)++input.origin_x;if(spec.mutation==OUTPUT_ORIGIN)--output.origin_y;
  if(spec.mutation==INPUT_FLAGS)input.world_flags^=PF_WorldFlag_WRITEABLE;
  if(spec.mutation==OUTPUT_FLAGS)output.world_flags^=PF_WorldFlag_WRITEABLE;
  if(spec.mutation==INPUT_FORMAT)g_input_format_override=depth==8?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB32;
  if(spec.mutation==OUTPUT_FORMAT)g_output_format_override=depth==32?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
  if(spec.mutation==EXACT_ALIAS)output.data=input.data;
  if(spec.mutation==OVERLAP_FORWARD)output.data=reinterpret_cast<PF_PixelPtr>(input_data+1);
  if(spec.mutation==OVERLAP_BACKWARD)input.data=reinterpret_cast<PF_PixelPtr>(output_data+1);
  if(spec.mutation==INPUT_DATA_NULL)input.data=nullptr;if(spec.mutation==OUTPUT_DATA_NULL)output.data=nullptr;
  const auto input_before=input_store,output_before=output_store;const PF_EffectWorld input_header=input,output_header=output;
  g_input=&input;g_output=&output;g_depth=depth;g_pre=g_pixels=g_output_hits=g_optional_checkin=g_param_out=g_param_in=g_copy=0;g_acquire=g_release=g_get_format=0;g_request_exact=false;
  SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;PF_UtilCallbacks utils{};utils.copy=copy_world;
  PF_InData in{};PF_OutData out{};in.effect_ref=reinterpret_cast<PF_ProgPtr>(0x1234);in.current_time=7;in.time_step=1;in.time_scale=24;in.downsample_x={1,1};in.downsample_y={1,1};in.pica_basicP=&basic;in.utils=&utils;in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;
  if(spec.mutation==DSX_NUM)in.downsample_x.num=2;if(spec.mutation==DSX_DEN)in.downsample_x.den=2;
  if(spec.mutation==DSY_NUM)in.downsample_y.num=2;if(spec.mutation==DSY_DEN)in.downsample_y.den=2;
  if(spec.mutation==NULL_PICA)in.pica_basicP=nullptr;if(spec.mutation==NULL_ACQUIRE_FN)basic.AcquireSuite=nullptr;if(spec.mutation==NULL_RELEASE_FN)basic.ReleaseSuite=nullptr;
  PF_PreRenderInput pi{};pi.output_request.rect={0,0,24,24};g_expected_request=pi.output_request;PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre_checkout;PF_PreRenderExtra pe{&pi,&po,&pcb};
  const PF_Err pre_err=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
  PF_SmartRenderInput si{};si.bitdepth=spec.mutation==DEPTH_WRONG?(depth==8?16:8):depth;PF_SmartRenderCallbacks scb{};scb.checkout_layer_pixels=spec.mutation==NULL_LAYER_FN?nullptr:pixels;scb.checkin_layer_pixels=optional_checkin;scb.checkout_output=spec.mutation==NULL_OUTPUT_FN?nullptr:checkout_output;PF_SmartRenderExtra se{&si,&scb};
  if(spec.mutation==NULL_PARAM_OUT_FN)in.inter.checkout_param=nullptr;if(spec.mutation==NULL_PARAM_IN_FN)in.inter.checkin_param=nullptr;
  if(spec.mutation==STAGE_OOM)g_fail_next_new=true;
  const PF_Err actual=pre_err?pre_err:EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
  const bool copy_failure_mode=spec.mode==COPY_ERROR||spec.mode==COPY_THROW_PF||
    spec.mode==COPY_THROW_OOM||spec.mode==COPY_THROW_OTHER;
  const bool exact=actual==spec.expected&&input_store==input_before&&output_store==output_before&&
    !std::memcmp(&input,&input_header,sizeof(input))&&!std::memcmp(&output,&output_header,sizeof(output))&&
    g_copy==(copy_failure_mode?1:0)&&g_optional_checkin==0;
  std::printf("NEG %s exact=%d expected=%d actual=%d copy=%d param=%d/%d suite=%d/%d/%d\n",spec.id,exact,spec.expected,actual,g_copy,g_param_out,g_param_in,g_acquire,g_get_format,g_release);
  return exact;
}

struct PreSpec { const char *id; int graph; CallbackMode mode; PF_Err expected; };
static bool run_pre_negative(const PreSpec &spec) {
  g_mode=spec.mode;g_pre=0;g_request_exact=false;
  PF_InData in{};PF_OutData out{};in.effect_ref=reinterpret_cast<PF_ProgPtr>(0x1234);in.current_time=7;in.time_step=1;in.time_scale=24;
  PF_PreRenderInput pi{};pi.output_request.rect={3,5,17,19};pi.output_request.preserve_rgb_of_zero_alpha=TRUE;g_expected_request=pi.output_request;
  PF_PreRenderOutput po{};std::memset(&po,0xA7,sizeof(po));const PF_PreRenderOutput before=po;
  PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre_checkout;PF_PreRenderExtra pe{&pi,&po,&pcb};
  PF_PreRenderExtra *extra=&pe;
  if(spec.graph==1)extra=nullptr;else if(spec.graph==2)pe.input=nullptr;else if(spec.graph==3)pe.output=nullptr;else if(spec.graph==4)pe.cb=nullptr;else if(spec.graph==5)pcb.checkout_layer=nullptr;
  const PF_Err actual=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,extra);
  const bool unchanged=!std::memcmp(&po,&before,sizeof(po));
  const bool exact=actual==spec.expected&&unchanged&&g_pre==(spec.graph?0:1);
  std::printf("PRENEG %s exact=%d expected=%d actual=%d pre=%d unchanged=%d\n",spec.id,exact,spec.expected,actual,g_pre,unchanged);
  return exact;
}

static bool run_pre_success() {
  g_mode=NORMAL;g_pre=0;g_request_exact=false;PF_InData in{};PF_OutData out{};in.effect_ref=reinterpret_cast<PF_ProgPtr>(0x1234);in.current_time=7;in.time_step=1;in.time_scale=24;
  PF_PreRenderInput pi{};pi.output_request.rect={3,5,17,19};pi.output_request.preserve_rgb_of_zero_alpha=TRUE;g_expected_request=pi.output_request;
  PF_PreRenderOutput po{};PF_PreRenderCallbacks pcb{};pcb.checkout_layer=pre_checkout;PF_PreRenderExtra pe{&pi,&po,&pcb};const PF_Err actual=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
  const bool exact=!actual&&g_pre==1&&g_request_exact&&po.result_rect.left==0&&po.result_rect.top==0&&po.result_rect.right==24&&po.result_rect.bottom==24&&po.max_result_rect.left==0&&po.max_result_rect.top==0&&po.max_result_rect.right==24&&po.max_result_rect.bottom==24&&!po.solid&&!po.pre_render_data&&!po.delete_pre_render_data_func&&po.flags==0;
  std::printf("PREPOS exact=%d actual=%d pre=%d request_exact=%d\n",exact,actual,g_pre,g_request_exact);return exact;
}

int main(int argc,char **argv){
  if(argc!=2)return 2;g_world_suite.PF_GetPixelFormat=get_format;std::vector<RunResult> rows;bool ok=true;
  for(short depth:{(short)8,(short)16,(short)32})for(int legacy:{0,1})for(bool present:{true,false}){
    auto r=run_case(argv[1],depth,legacy,present);ok&=r.pass;rows.push_back(r);
    std::printf("%s pass=%d pre=%d render=%d optional_present=%d\n",r.id.c_str(),r.pass,r.pre_err,r.render_err,r.optional_present);
  }
  const NegSpec negatives[]={
    {"PF8_source_first",8,SRC_FIRST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"PF8_source_middle",8,SRC_MIDDLE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"PF8_source_last",8,SRC_LAST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"PF16_source_first",16,SRC_FIRST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"PF16_source_middle",16,SRC_MIDDLE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"PF16_source_last",16,SRC_LAST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"PF32_source_first",32,SRC_FIRST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"PF32_source_middle",32,SRC_MIDDLE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"PF32_source_last",32,SRC_LAST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"amount_up",8,AMOUNT_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"amount_down",8,AMOUNT_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"smooth_down",8,SMOOTH_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"smooth_up",8,SMOOTH_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"repeat_down",8,REPEAT_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"repeat_up",8,REPEAT_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"bias_down",8,BIAS_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"bias_up",8,BIAS_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"legacy_invalid",8,LEGACY_INVALID,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_width",8,INPUT_WIDTH,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_height",8,OUTPUT_HEIGHT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_rowbytes",8,INPUT_ROWBYTES,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_rowbytes",8,OUTPUT_ROWBYTES,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_extent",8,INPUT_EXTENT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_extent",8,OUTPUT_EXTENT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_origin",8,INPUT_ORIGIN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_origin",8,OUTPUT_ORIGIN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_flags",8,INPUT_FLAGS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_flags",8,OUTPUT_FLAGS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_format",8,INPUT_FORMAT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_format",8,OUTPUT_FORMAT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"depth_wrong",8,DEPTH_WRONG,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsx_num",8,DSX_NUM,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsx_den",8,DSX_DEN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsy_num",8,DSY_NUM,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsy_den",8,DSY_DEN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"alias",8,EXACT_ALIAS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"overlap_forward",8,OVERLAP_FORWARD,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"overlap_backward",8,OVERLAP_BACKWARD,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_null",8,INPUT_DATA_NULL,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_null",8,OUTPUT_DATA_NULL,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"null_layer_fn",8,NULL_LAYER_FN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_output_fn",8,NULL_OUTPUT_FN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_param_out_fn",8,NULL_PARAM_OUT_FN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_param_in_fn",8,NULL_PARAM_IN_FN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_pica",8,NULL_PICA,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_acquire_fn",8,NULL_ACQUIRE_FN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_release_fn",8,NULL_RELEASE_FN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"layer_error",8,CALLBACK_MODE,LAYER_ERROR,0,70},{"output_error",8,CALLBACK_MODE,OUTPUT_ERROR,0,71},
    {"param_checkout_1",8,CALLBACK_MODE,PARAM_OUT_ERROR,1,72},{"param_checkout_2",8,CALLBACK_MODE,PARAM_OUT_ERROR,2,72},{"param_checkout_3",8,CALLBACK_MODE,PARAM_OUT_ERROR,3,72},{"param_checkout_4",8,CALLBACK_MODE,PARAM_OUT_ERROR,4,72},{"param_checkout_5",8,CALLBACK_MODE,PARAM_OUT_ERROR,5,72},
    {"param_checkin_1",8,CALLBACK_MODE,PARAM_IN_ERROR,1,73},{"param_checkin_2",8,CALLBACK_MODE,PARAM_IN_ERROR,2,73},{"param_checkin_3",8,CALLBACK_MODE,PARAM_IN_ERROR,3,73},{"param_checkin_4",8,CALLBACK_MODE,PARAM_IN_ERROR,4,73},{"param_checkin_5",8,CALLBACK_MODE,PARAM_IN_ERROR,5,73},
    {"suite_acquire_error",8,CALLBACK_MODE,ACQUIRE_ERROR,0,74},{"suite_null",8,CALLBACK_MODE,ACQUIRE_NULL,0,PF_Err_BAD_CALLBACK_PARAM},{"format_fn_null",8,CALLBACK_MODE,FORMAT_FN_NULL,0,PF_Err_BAD_CALLBACK_PARAM},{"format_input_error",8,CALLBACK_MODE,INPUT_FORMAT_ERROR,0,75},{"format_output_error",8,CALLBACK_MODE,OUTPUT_FORMAT_ERROR,0,76},{"suite_release_error",8,CALLBACK_MODE,RELEASE_ERROR,0,80},
    {"acquire_throw_pf",8,CALLBACK_MODE,ACQUIRE_THROW_PF,0,78},{"acquire_throw_oom",8,CALLBACK_MODE,ACQUIRE_THROW_OOM,0,PF_Err_OUT_OF_MEMORY},{"acquire_throw_other",8,CALLBACK_MODE,ACQUIRE_THROW_OTHER,0,PF_Err_INTERNAL_STRUCT_DAMAGED},
    {"get_throw_pf",8,CALLBACK_MODE,GET_THROW_PF,0,77},{"get_throw_oom",8,CALLBACK_MODE,GET_THROW_OOM,0,PF_Err_OUT_OF_MEMORY},{"get_throw_other",8,CALLBACK_MODE,GET_THROW_OTHER,0,PF_Err_INTERNAL_STRUCT_DAMAGED},
    {"release_throw_pf",8,CALLBACK_MODE,RELEASE_THROW_PF,0,79},{"release_throw_oom",8,CALLBACK_MODE,RELEASE_THROW_OOM,0,PF_Err_OUT_OF_MEMORY},{"release_throw_other",8,CALLBACK_MODE,RELEASE_THROW_OTHER,0,PF_Err_INTERNAL_STRUCT_DAMAGED},
    {"layer_throw_pf",8,CALLBACK_MODE,LAYER_THROW_PF,0,83},{"layer_throw_oom",8,CALLBACK_MODE,LAYER_THROW_OOM,0,PF_Err_OUT_OF_MEMORY},{"layer_throw_other",8,CALLBACK_MODE,LAYER_THROW_OTHER,0,PF_Err_INTERNAL_STRUCT_DAMAGED},
    {"output_throw_pf",8,CALLBACK_MODE,OUTPUT_THROW_PF,0,84},{"output_throw_oom",8,CALLBACK_MODE,OUTPUT_THROW_OOM,0,PF_Err_OUT_OF_MEMORY},{"output_throw_other",8,CALLBACK_MODE,OUTPUT_THROW_OTHER,0,PF_Err_INTERNAL_STRUCT_DAMAGED},
    {"param_out_throw_pf",8,CALLBACK_MODE,PARAM_OUT_THROW_PF,3,81},{"param_out_throw_oom",8,CALLBACK_MODE,PARAM_OUT_THROW_OOM,3,PF_Err_OUT_OF_MEMORY},{"param_out_throw_other",8,CALLBACK_MODE,PARAM_OUT_THROW_OTHER,3,PF_Err_INTERNAL_STRUCT_DAMAGED},
    {"param_in_throw_pf",8,CALLBACK_MODE,PARAM_IN_THROW_PF,3,82},{"param_in_throw_oom",8,CALLBACK_MODE,PARAM_IN_THROW_OOM,3,PF_Err_OUT_OF_MEMORY},{"param_in_throw_other",8,CALLBACK_MODE,PARAM_IN_THROW_OTHER,3,PF_Err_INTERNAL_STRUCT_DAMAGED},
    {"copy_error",8,CALLBACK_MODE,COPY_ERROR,0,86},{"copy_throw_pf",8,CALLBACK_MODE,COPY_THROW_PF,0,87},{"copy_throw_oom",8,CALLBACK_MODE,COPY_THROW_OOM,0,PF_Err_OUT_OF_MEMORY},{"copy_throw_other",8,CALLBACK_MODE,COPY_THROW_OTHER,0,PF_Err_INTERNAL_STRUCT_DAMAGED},
    {"stage_oom",8,STAGE_OOM,NORMAL,0,PF_Err_OUT_OF_MEMORY}};
  bool neg_ok=true;for(const auto&s:negatives)neg_ok&=run_negative(argv[1],s);
  const PreSpec pre_negatives[]={{"null_extra",1,NORMAL,PF_Err_BAD_CALLBACK_PARAM},{"null_input",2,NORMAL,PF_Err_BAD_CALLBACK_PARAM},{"null_output",3,NORMAL,PF_Err_BAD_CALLBACK_PARAM},{"null_cb",4,NORMAL,PF_Err_BAD_CALLBACK_PARAM},{"null_checkout_fn",5,NORMAL,PF_Err_BAD_CALLBACK_PARAM},{"checkout_error",0,PRE_ERROR,88},{"checkout_throw_pf",0,PRE_THROW_PF,89},{"checkout_throw_oom",0,PRE_THROW_OOM,PF_Err_OUT_OF_MEMORY},{"checkout_throw_other",0,PRE_THROW_OTHER,PF_Err_INTERNAL_STRUCT_DAMAGED}};
  bool pre_ok=run_pre_success();for(const auto&s:pre_negatives)pre_ok&=run_pre_negative(s);
  std::printf("all_exact=%d positive_rows=%zu negative_rows=%zu pre_positive_rows=1 pre_negative_rows=%zu\n",ok&&neg_ok&&pre_ok,rows.size(),sizeof(negatives)/sizeof(*negatives),sizeof(pre_negatives)/sizeof(*pre_negatives));return ok&&neg_ok&&pre_ok?0:4;
}

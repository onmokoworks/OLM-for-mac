// Real SDK host callbacks adapted from test_dblur_generic_backonly_effectmain_20260821.py.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <limits>
#include <type_traits>
#include <vector>
#include <sys/mman.h>

#include "../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"

#define REQUIRE(condition, code) do { if (!(condition)) { \
  std::fprintf(stderr, "FAIL code=%d line=%d\n", (code), __LINE__); return (code); \
} } while (0)

static constexpr std::uint8_t kInputCanary = 0xa5;
static constexpr std::uint8_t kOutputCanary = 0xee;
static constexpr PF_Err kCheckoutFailure = 710;
static constexpr PF_Err kCheckinFailure = 810;
static constexpr PF_Err kLayerCheckinFailure = 811;
static constexpr PF_Err kOutputFailure = 910;

struct HostState {
  PF_EffectWorld* input = nullptr;
  PF_EffectWorld* output = nullptr;
  PF_ParamDef* defs = nullptr;
  PF_PixelFormat format = PF_PixelFormat_INVALID;
  int pre_calls = 0;
  int pre_input_calls = 0;
  int pre_noise_calls = 0;
  int pixel_calls = 0;
  int pixel_input_calls = 0;
  int pixel_noise_calls = 0;
  int output_checkout = 0;
  int layer_checkin = 0;
  int param_checkout_attempts = 0;
  int param_checkin_attempts = 0;
  int acquire = 0;
  int release = 0;
  int world_calls = 0;
  int front_seen = -1;
  int back_seen = -1;
  int fail_checkout_index = -1;
  int fail_checkin_id = -1;
  int fail_layer_checkin_id = -1;
  bool fail_output = false;
  bool preserve = true;
  bool full_request = true;
  std::vector<int> checkout_order;
  std::vector<int> checkin_order;
  std::vector<int> layer_checkin_order;
};

static HostState* g_host = nullptr;
static PF_WorldSuite2 g_world_suite = {};

static PF_Err GetPixelFormat(const PF_EffectWorld*, PF_PixelFormat* format) {
  if (!g_host || !format) return PF_Err_BAD_CALLBACK_PARAM;
  ++g_host->world_calls;
  *format = g_host->format;
  return PF_Err_NONE;
}

static SPErr AcquireSuite(const char* name, int32 version, const void** suite) {
  if (!g_host || !suite) return kSPBadParameterError;
  ++g_host->acquire;
  if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) {
    g_world_suite.PF_NewWorld = nullptr;
    g_world_suite.PF_DisposeWorld = nullptr;
    g_world_suite.PF_GetPixelFormat = GetPixelFormat;
    *suite = &g_world_suite;
    return kSPNoError;
  }
  *suite = nullptr;
  return kSPBadParameterError;
}

static SPErr ReleaseSuite(const char*, int32) {
  if (g_host) ++g_host->release;
  return kSPNoError;
}

static PF_Err CheckoutParam(PF_ProgPtr effect_ref, PF_ParamIndex index,
                            A_long, A_long, A_u_long, PF_ParamDef* param) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !param || index <= OLMDIRECTIONALBLUR_INPUT ||
      index >= OLMDIRECTIONALBLUR_NUM_PARAMS) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->param_checkout_attempts;
  if (index == state->fail_checkout_index) return kCheckoutFailure;
  *param = state->defs[index];
  state->checkout_order.push_back(index);
  if (index == OLMDIRECTIONALBLUR_FRONT_STRENGTH) {
    state->front_seen = param->u.sd.value;
  }
  if (index == OLMDIRECTIONALBLUR_BACK_STRENGTH) {
    state->back_seen = param->u.sd.value;
  }
  return PF_Err_NONE;
}

static PF_Err CheckinParam(PF_ProgPtr effect_ref, PF_ParamDef* param) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !param) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->param_checkin_attempts;
  state->checkin_order.push_back(param->uu.id);
  return param->uu.id == state->fail_checkin_id ? kCheckinFailure : PF_Err_NONE;
}

static PF_Err PreCheckout(PF_ProgPtr effect_ref, PF_ParamIndex index,
                          A_long checkout_id, const PF_RenderRequest* request,
                          A_long, A_long, A_u_long, PF_CheckoutResult* result) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !request || !result || index != checkout_id) {
    return PF_Err_BAD_CALLBACK_PARAM;
  }
  ++state->pre_calls;
  state->preserve = state->preserve && request->preserve_rgb_of_zero_alpha;
  state->full_request = state->full_request && request->rect.left == 0 &&
    request->rect.top == 0 && request->rect.right == state->input->width &&
    request->rect.bottom == state->input->height;
  if (index == OLMDIRECTIONALBLUR_NOISE_LAYER) {
    ++state->pre_noise_calls;
    return PF_Err_BAD_CALLBACK_PARAM;
  }
  if (index != OLMDIRECTIONALBLUR_INPUT) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->pre_input_calls;
  std::memset(result, 0, sizeof(*result));
  result->result_rect = {0, 0, state->input->width, state->input->height};
  result->max_result_rect = result->result_rect;
  result->ref_width = state->input->width;
  result->ref_height = state->input->height;
  return PF_Err_NONE;
}

static PF_Err CheckoutPixels(PF_ProgPtr effect_ref, A_long checkout_id,
                             PF_EffectWorld** world) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !world) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->pixel_calls;
  if (checkout_id == OLMDIRECTIONALBLUR_INPUT) {
    ++state->pixel_input_calls;
    *world = state->input;
    return PF_Err_NONE;
  }
  if (checkout_id == OLMDIRECTIONALBLUR_NOISE_LAYER) {
    ++state->pixel_noise_calls;
    *world = nullptr;
    return PF_Err_BAD_CALLBACK_PARAM;
  }
  return PF_Err_BAD_CALLBACK_PARAM;
}

static PF_Err CheckinPixels(PF_ProgPtr effect_ref, A_long checkout_id) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->layer_checkin;
  state->layer_checkin_order.push_back((int)checkout_id);
  if (checkout_id != OLMDIRECTIONALBLUR_INPUT) return PF_Err_BAD_CALLBACK_PARAM;
  return checkout_id == state->fail_layer_checkin_id
    ? kLayerCheckinFailure : PF_Err_NONE;
}

static PF_Err CheckoutOutput(PF_ProgPtr effect_ref, PF_EffectWorld** world) {
  HostState* state = reinterpret_cast<HostState*>(effect_ref);
  if (!state || !world) return PF_Err_BAD_CALLBACK_PARAM;
  ++state->output_checkout;
  if (state->fail_output) return kOutputFailure;
  *world = state->output;
  return PF_Err_NONE;
}

static SPBasicSuite MakeBasic() {
  SPBasicSuite basic = {};
  basic.AcquireSuite = AcquireSuite;
  basic.ReleaseSuite = ReleaseSuite;
  return basic;
}

static PF_InData MakeInData(HostState* state, SPBasicSuite* basic) {
  PF_InData in = {};
  in.effect_ref = reinterpret_cast<PF_ProgPtr>(state);
  in.pica_basicP = basic;
  in.current_time = 7;
  in.time_step = 1;
  in.time_scale = 24;
  in.width = state->input->width;
  in.height = state->input->height;
  in.output_origin_x = 0;
  in.output_origin_y = 0;
  in.downsample_x = {1, 1};
  in.downsample_y = {1, 1};
  in.inter.checkout_param = CheckoutParam;
  in.inter.checkin_param = CheckinParam;
  return in;
}

static PF_EffectWorld MakeWorld(void* data, A_long rowbytes, A_long width,
                                A_long height, short depth) {
  PF_EffectWorld world = {};
  world.data = reinterpret_cast<PF_PixelPtr>(data);
  world.rowbytes = rowbytes;
  world.width = width;
  world.height = height;
  world.extent_hint = {0, 0, width, height};
  world.origin_x = 0;
  world.origin_y = 0;
  world.world_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
  return world;
}

static void InitParams(PF_ParamDef defs[OLMDIRECTIONALBLUR_NUM_PARAMS],
                       PF_ParamDef* params[OLMDIRECTIONALBLUR_NUM_PARAMS],
                       const PF_EffectWorld& input, int back_strength,
                       int front_strength = 0) {
  std::memset(defs, 0, sizeof(PF_ParamDef) * OLMDIRECTIONALBLUR_NUM_PARAMS);
  for (int i = 0; i < OLMDIRECTIONALBLUR_NUM_PARAMS; ++i) {
    defs[i].uu.id = i;
    params[i] = &defs[i];
  }
  defs[OLMDIRECTIONALBLUR_INPUT].u.ld = input;
  defs[OLMDIRECTIONALBLUR_ANGLE].u.ad.value =
    static_cast<PF_Fixed>(std::lround(37.25 * 65536.0));
  defs[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN].u.fs_d.value = 0.75;
  defs[OLMDIRECTIONALBLUR_SIZE_VARIATION].u.fd.value = 0;
  defs[OLMDIRECTIONALBLUR_FRONT_STRENGTH].u.sd.value = front_strength;
  defs[OLMDIRECTIONALBLUR_FRONT_ALPHA_FADE].u.sd.value = 0;
  defs[OLMDIRECTIONALBLUR_FRONT_SHARP_TAIL].u.fd.value = 0;
  defs[OLMDIRECTIONALBLUR_BACK_STRENGTH].u.sd.value = back_strength;
  defs[OLMDIRECTIONALBLUR_BACK_ALPHA_FADE].u.sd.value = 0;
  defs[OLMDIRECTIONALBLUR_BACK_SHARP_TAIL].u.fd.value = 0;
  defs[OLMDIRECTIONALBLUR_NOISE_VARIATION].u.fd.value = 0;
  defs[OLMDIRECTIONALBLUR_NOISE_TYPE].u.pd.value = 1;
  defs[OLMDIRECTIONALBLUR_NOISE_LAYER].u.ld.dephault = FALSE;
  defs[OLMDIRECTIONALBLUR_SEED].u.sd.value = 1;
  defs[OLMDIRECTIONALBLUR_NOISE_OFFSET].u.ad.value = 0;
  defs[OLMDIRECTIONALBLUR_THICKNESS].u.fs_d.value = 10.0;
}

static std::vector<int> ExpectedParams() {
  std::vector<int> result;
  for (int i = 1; i < OLMDIRECTIONALBLUR_NUM_PARAMS; ++i) result.push_back(i);
  return result;
}

static PF_Err InvokeClassic(HostState* state, SPBasicSuite* basic,
                            PF_ParamDef* params[OLMDIRECTIONALBLUR_NUM_PARAMS]) {
  g_host = state;
  PF_InData in = MakeInData(state, basic);
  PF_OutData out = {};
  return EffectMain(PF_Cmd_RENDER, &in, &out, params, state->output, nullptr);
}

static PF_Err InvokeSmart(HostState* state, SPBasicSuite* basic, short depth,
                          bool full_request, PF_Err* pre_error = nullptr) {
  g_host = state;
  PF_InData in = MakeInData(state, basic);
  PF_OutData out = {};
  PF_PreRenderInput pre_input = {};
  pre_input.bitdepth = depth;
  pre_input.output_request.rect = full_request
    ? PF_LRect{0, 0, state->input->width, state->input->height}
    : PF_LRect{0, 0, state->input->width - 1, state->input->height};
  PF_PreRenderOutput pre_output = {};
  PF_PreRenderCallbacks pre_callbacks = {};
  pre_callbacks.checkout_layer = PreCheckout;
  PF_PreRenderExtra pre_extra = {&pre_input, &pre_output, &pre_callbacks};
  const PF_Err pre_err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in, &out,
                                    nullptr, nullptr, &pre_extra);
  if (pre_error) *pre_error = pre_err;
  if (pre_err) {
    if (pre_output.delete_pre_render_data_func && pre_output.pre_render_data) {
      pre_output.delete_pre_render_data_func(pre_output.pre_render_data);
    }
    return pre_err;
  }
  PF_SmartRenderInput smart_input = {};
  smart_input.bitdepth = depth;
  smart_input.output_request = pre_input.output_request;
  smart_input.pre_render_data = pre_output.pre_render_data;
  PF_SmartRenderCallbacks smart_callbacks = {};
  smart_callbacks.checkout_layer_pixels = CheckoutPixels;
  smart_callbacks.checkin_layer_pixels = CheckinPixels;
  smart_callbacks.checkout_output = CheckoutOutput;
  PF_SmartRenderExtra smart_extra = {&smart_input, &smart_callbacks};
  const PF_Err smart_err = EffectMain(PF_Cmd_SMART_RENDER, &in, &out,
                                      nullptr, nullptr, &smart_extra);
  if (pre_output.delete_pre_render_data_func && pre_output.pre_render_data) {
    pre_output.delete_pre_render_data_func(pre_output.pre_render_data);
  }
  return smart_err;
}


#include <sstream>
#include <string>
int main(int argc,char**argv) {
 if(argc!=6)return 64;int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]);
 if(w<1||h<1||w>64||h>64||(depth!=16&&depth!=32))return 64;
 const size_t ps=depth==16?8:16,active=w*ps,irb=active+5,orb=active+11;
 std::vector<unsigned char> input(irb*h,0x3c),output(orb*h,0xa5);
 for(int y=0;y<h;++y)if(fread(input.data()+y*irb,1,active,stdin)!=active)return 65;
 if(getchar()!=EOF)return 65;const auto before=input;
 auto iw=MakeWorld(input.data(),irb,w,h,depth),ow=MakeWorld(output.data(),orb,w,h,depth);
 PF_ParamDef defs[OLMDIRECTIONALBLUR_NUM_PARAMS];PF_ParamDef*params[OLMDIRECTIONALBLUR_NUM_PARAMS];
 InitParams(defs,params,iw,3,4);defs[1].u.ad.value=17*65536+16384;defs[2].u.fs_d.value=1;defs[20].u.fs_d.value=3;
 std::stringstream specification(argv[4]);std::string component;
 while(std::getline(specification,component,',')) {
  int slot;double value;if(sscanf(component.c_str(),"%d=%lf",&slot,&value)!=2)return 64;
  if(slot==1||slot==19)defs[slot].u.ad.value=static_cast<PF_Fixed>(std::llround(value*65536));
  else if(slot==3||slot==7||slot==12||slot==15)defs[slot].u.fd.value=static_cast<PF_Fixed>(std::llround(value*65536));
  else if(slot==2||slot==20)defs[slot].u.fs_d.value=value;
  else if(slot==5||slot==6||slot==10||slot==11||slot==16||slot==18)defs[slot].u.sd.value=static_cast<A_long>(value);
  else return 64;
 }
 HostState state;state.input=&iw;state.output=&ow;state.defs=defs;state.format=depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
 SPBasicSuite basic=MakeBasic();std::string mode(argv[5]);
 if(mode=="budget"||mode=="budgetclassic") {
  iw.width=ow.width=2000;iw.height=ow.height=2000;iw.rowbytes=ow.rowbytes=2000*ps;
  iw.extent_hint=ow.extent_hint={0,0,2000,2000};iw.data=reinterpret_cast<PF_PixelPtr>(0x100000000ull);
  defs[0].u.ld=iw;defs[5].u.sd.value=defs[10].u.sd.value=4000;
 }
 if(mode=="memorybudget") {
  iw.height=ow.height=2;iw.extent_hint=ow.extent_hint={0,0,w,2};
  ow.rowbytes=1700000000;iw.data=reinterpret_cast<PF_PixelPtr>(0x100000000ull);defs[0].u.ld=iw;
 }

 if(mode=="negative"||mode=="negativeclassic")defs[19].u.ad.value=-720*65536;
 if(mode=="checkin")state.fail_checkin_id=3;
 if(mode=="layercheckin")state.fail_layer_checkin_id=OLMDIRECTIONALBLUR_INPUT;
 if(mode=="checkout")state.fail_checkout_index=3;
 if(mode=="output")state.fail_output=true;
 PF_Err err=(mode=="classic"||mode=="budgetclassic"||mode=="negativeclassic")?InvokeClassic(&state,&basic,params):InvokeSmart(&state,&basic,depth,mode!="partial");
 if(input!=before)return 66;
 for(int y=0;y<h;++y)for(size_t x=active;x<orb;++x)if(output[y*orb+x]!=0xa5)return 67;
 if(err)for(int y=0;y<h;++y)for(size_t x=0;x<active;++x)if(output[y*orb+x]!=0xa5)return 68;
 if(state.acquire!=state.release)return 69;
 printf("ERROR %d\nCOUNTS %d %d %d %d %d\nRAW ",int(err),state.param_checkout_attempts,state.param_checkin_attempts,state.layer_checkin,state.acquire,state.release);
 if(!err)for(int y=0;y<h;++y)for(size_t x=0;x<active;++x)printf("%02x",output[y*orb+x]);puts("");
 return 0;
}

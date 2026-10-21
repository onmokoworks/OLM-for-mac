#define main olmblur_base_probe_main
#include "probe_olmblur_smart_public_admission_20260813.cpp"
#undef main

#include <array>

enum SmallMutation {
  S_OK, S_SOURCE_FIRST, S_SOURCE_MIDDLE, S_SOURCE_LAST, S_AMOUNT_UP, S_AMOUNT_DOWN,
  S_SMOOTH_DOWN, S_SMOOTH_UP, S_REPEAT_DOWN, S_REPEAT_UP, S_BIAS_DOWN, S_BIAS_UP,
  S_LEGACY_ONE, S_LEGACY_INVALID, S_INPUT_WIDTH, S_OUTPUT_HEIGHT, S_INPUT_ROWBYTES,
  S_OUTPUT_ROWBYTES, S_INPUT_EXTENT, S_OUTPUT_EXTENT, S_INPUT_ORIGIN, S_OUTPUT_ORIGIN,
  S_INPUT_FLAGS, S_OUTPUT_FLAGS, S_INPUT_FORMAT, S_OUTPUT_FORMAT, S_DEPTH, S_DSX_NUM,
  S_DSX_DEN, S_DSY_NUM, S_DSY_DEN, S_ALIAS, S_OVERLAP_FORWARD, S_OVERLAP_BACKWARD,
  S_INPUT_NULL, S_OUTPUT_NULL, S_NULL_LAYER, S_NULL_OUTPUT, S_NULL_PARAM_OUT,
  S_NULL_PARAM_IN, S_NULL_PICA, S_NULL_ACQUIRE, S_NULL_RELEASE, S_STAGE_OOM,
  S_CALLBACK
};

struct SmallSpec {
  const char *id; SmallMutation mutation; CallbackMode mode; int ordinal; PF_Err expected;
};

static const std::array<uint16_t, 140> kExpected = {{
  32768,1558,30659,614,32768,1938,30679,886,32768,2476,30708,1272,
  32768,3116,30742,1732,32768,3756,30775,2191,32768,4295,30804,2577,
  32768,4674,30824,2849,32768,1567,31087,629,32768,1947,31107,901,
  32768,2485,31135,1288,32768,3125,31169,1747,32768,3765,31203,2206,
  32768,4304,31231,2592,32768,4683,31251,2865,32768,1579,31651,649,
  32768,1958,31671,921,32768,2497,31699,1308,32768,3137,31733,1767,
  32768,3777,31767,2226,32768,4316,31795,2613,32768,4695,31815,2885,
  32768,1591,32215,669,32768,1970,32235,942,32768,2509,32263,1328,
  32768,3149,32297,1787,32768,3789,32331,2246,32768,4327,32359,2633,
  32768,4707,32379,2905,32768,1600,32642,685,32768,1979,32662,957,
  32768,2518,32691,1343,32768,3158,32724,1802,32768,3798,32758,2262,
  32768,4336,32787,2648,32768,4716,32807,2920
}};

static void fill_small_source(unsigned char *data, int rowbytes) {
  for (int y=0;y<5;++y) for (int x=0;x<7;++x) {
    const uint16_t p[4] = {32768,(uint16_t)(1000+701*x+17*y),
      (uint16_t)(30000+37*x+811*y),(uint16_t)(200+503*x+29*y)};
    std::memcpy(data+(size_t)y*rowbytes+(size_t)x*8,p,sizeof(p));
  }
}

static bool run_small(const SmallSpec &spec, bool checkin_present=false) {
  constexpr int width=7,height=5,pixel_bytes=8,padding=13,rowbytes=69;
  constexpr size_t payload=(size_t)rowbytes*height;
  std::vector<unsigned char> input_store(19+16+payload+19,0xC7),output_store(19+16+payload+19,0xD9);
  unsigned char *input_data=misaligned_payload(input_store,payload,pixel_bytes);
  unsigned char *output_data=misaligned_payload(output_store,payload,pixel_bytes);
  if(!input_data||!output_data)return false;
  for(int y=0;y<height;++y){std::memset(input_data+(size_t)y*rowbytes,0xA5,rowbytes);
    std::memset(output_data+(size_t)y*rowbytes,0xEE,rowbytes);} fill_small_source(input_data,rowbytes);
  if(spec.mutation==S_SOURCE_FIRST)input_data[0]^=1;
  if(spec.mutation==S_SOURCE_MIDDLE)input_data[2*rowbytes+3*pixel_bytes]^=1;
  if(spec.mutation==S_SOURCE_LAST)input_data[4*rowbytes+7*pixel_bytes-1]^=1;
  PF_EffectWorld input{},output{};input.world_flags=PF_WorldFlag_DEEP;
  input.data=(PF_PixelPtr)input_data;input.rowbytes=rowbytes;input.width=width;input.height=height;
  input.extent_hint={0,0,width,height};input.origin_x=input.origin_y=0;output=input;output.data=(PF_PixelPtr)output_data;
  g_mode=spec.mode;g_fail_ordinal=spec.ordinal;g_amount=4.0;g_smooth=100*65536;g_repeat=1;g_bias=1;g_legacy=0;
  g_input_format_override=g_output_format_override=PF_PixelFormat_INVALID;
  if(spec.mutation==S_AMOUNT_UP)g_amount=std::nextafter(4.0,INFINITY);
  if(spec.mutation==S_AMOUNT_DOWN)g_amount=std::nextafter(4.0,-INFINITY);
  if(spec.mutation==S_SMOOTH_DOWN)--g_smooth;if(spec.mutation==S_SMOOTH_UP)++g_smooth;
  if(spec.mutation==S_REPEAT_DOWN)g_repeat=0;if(spec.mutation==S_REPEAT_UP)g_repeat=2;
  if(spec.mutation==S_BIAS_DOWN)g_bias=0;if(spec.mutation==S_BIAS_UP)g_bias=2;
  if(spec.mutation==S_LEGACY_ONE)g_legacy=1;if(spec.mutation==S_LEGACY_INVALID)g_legacy=2;
  if(spec.mutation==S_INPUT_WIDTH)--input.width;if(spec.mutation==S_OUTPUT_HEIGHT)++output.height;
  if(spec.mutation==S_INPUT_ROWBYTES)--input.rowbytes;if(spec.mutation==S_OUTPUT_ROWBYTES)++output.rowbytes;
  if(spec.mutation==S_INPUT_EXTENT)--input.extent_hint.left;if(spec.mutation==S_OUTPUT_EXTENT)++output.extent_hint.right;
  if(spec.mutation==S_INPUT_ORIGIN)++input.origin_x;if(spec.mutation==S_OUTPUT_ORIGIN)--output.origin_y;
  if(spec.mutation==S_INPUT_FLAGS)input.world_flags^=PF_WorldFlag_WRITEABLE;
  if(spec.mutation==S_OUTPUT_FLAGS)output.world_flags^=PF_WorldFlag_WRITEABLE;
  if(spec.mutation==S_INPUT_FORMAT)g_input_format_override=PF_PixelFormat_ARGB32;
  if(spec.mutation==S_OUTPUT_FORMAT)g_output_format_override=PF_PixelFormat_ARGB128;
  if(spec.mutation==S_ALIAS)output.data=input.data;
  if(spec.mutation==S_OVERLAP_FORWARD)output.data=(PF_PixelPtr)(input_data+1);
  if(spec.mutation==S_OVERLAP_BACKWARD)input.data=(PF_PixelPtr)(output_data+1);
  if(spec.mutation==S_INPUT_NULL)input.data=nullptr;if(spec.mutation==S_OUTPUT_NULL)output.data=nullptr;
  const auto input_before=input_store,output_before=output_store;const PF_EffectWorld input_header=input,output_header=output;
  g_input=&input;g_output=&output;g_depth=16;g_pre=g_pixels=g_output_hits=g_optional_checkin=g_param_out=g_param_in=g_copy=0;
  g_acquire=g_release=g_get_format=0;g_request_exact=false;
  SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;
  PF_UtilCallbacks utils{};utils.copy=copy_world;PF_InData in{};PF_OutData out{};
  in.effect_ref=(PF_ProgPtr)0x1234;in.current_time=7;in.time_step=1;in.time_scale=24;
  in.downsample_x={1,1};in.downsample_y={1,1};in.pica_basicP=&basic;in.utils=&utils;
  in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;
  if(spec.mutation==S_DSX_NUM)in.downsample_x.num=2;if(spec.mutation==S_DSX_DEN)in.downsample_x.den=2;
  if(spec.mutation==S_DSY_NUM)in.downsample_y.num=2;if(spec.mutation==S_DSY_DEN)in.downsample_y.den=2;
  if(spec.mutation==S_NULL_PICA)in.pica_basicP=nullptr;if(spec.mutation==S_NULL_ACQUIRE)basic.AcquireSuite=nullptr;
  if(spec.mutation==S_NULL_RELEASE)basic.ReleaseSuite=nullptr;
  PF_SmartRenderInput si{};si.bitdepth=spec.mutation==S_DEPTH?8:16;PF_SmartRenderCallbacks cb{};
  cb.checkout_layer_pixels=spec.mutation==S_NULL_LAYER?nullptr:pixels;
  cb.checkin_layer_pixels=checkin_present?optional_checkin:nullptr;
  cb.checkout_output=spec.mutation==S_NULL_OUTPUT?nullptr:checkout_output;PF_SmartRenderExtra se{&si,&cb};
  if(spec.mutation==S_NULL_PARAM_OUT)in.inter.checkout_param=nullptr;
  if(spec.mutation==S_NULL_PARAM_IN)in.inter.checkin_param=nullptr;
  if(spec.mutation==S_STAGE_OOM)g_fail_next_new=true;
  const PF_Err actual=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
  bool success_exact=true;int mismatch_words=0;int first_mismatch=-1;uint16_t first_actual=0,first_expected=0;
  if(spec.mutation==S_OK)for(int y=0;y<height;++y){
    const uint16_t *actual_words=reinterpret_cast<const uint16_t*>(output_data+(size_t)y*rowbytes);
    const uint16_t *expected_words=kExpected.data()+(size_t)y*width*4;
    for(int i=0;i<width*4;++i)if(actual_words[i]!=expected_words[i]){success_exact=false;++mismatch_words;
      if(first_mismatch<0){first_mismatch=y*width*4+i;first_actual=actual_words[i];first_expected=expected_words[i];}}
    for(int i=width*pixel_bytes;i<rowbytes;++i)success_exact&=output_data[(size_t)y*rowbytes+i]==0xA5;
  }
  const bool failure_untouched=spec.mutation==S_OK||output_store==output_before;
  const bool input_exact=input_store==input_before;
  const bool headers_exact=!std::memcmp(&input,&input_header,sizeof(input))&&
    !std::memcmp(&output,&output_header,sizeof(output));
  const bool exact=actual==spec.expected&&input_exact&&failure_untouched&&success_exact&&headers_exact&&
    g_optional_checkin==0;
  std::printf("SMALL %s exact=%d expected=%d actual=%d params=%d/%d suite=%d/%d/%d copy=%d input=%d output=%d success=%d headers=%d mismatches=%d first=%d/%u/%u\n",
    spec.id,exact,spec.expected,actual,g_param_out,g_param_in,g_acquire,g_get_format,g_release,g_copy,
    input_exact,failure_untouched,success_exact,headers_exact,mismatch_words,first_mismatch,first_actual,first_expected);
  return exact;
}

#ifndef OLMBLUR_PF16_7X5_NO_MAIN
int main(){g_world_suite.PF_GetPixelFormat=get_format;bool ok=true;
  const SmallSpec positive={"positive",S_OK,NORMAL,0,PF_Err_NONE};ok&=run_small(positive,true);ok&=run_small(positive,false);
  const SmallSpec rows[]={
    {"source_first",S_SOURCE_FIRST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"source_middle",S_SOURCE_MIDDLE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"source_last",S_SOURCE_LAST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"amount_up",S_AMOUNT_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"amount_down",S_AMOUNT_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"smooth_down",S_SMOOTH_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"smooth_up",S_SMOOTH_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"repeat_down",S_REPEAT_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"repeat_up",S_REPEAT_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"bias_down",S_BIAS_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"bias_up",S_BIAS_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"legacy_one",S_LEGACY_ONE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"legacy_invalid",S_LEGACY_INVALID,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_width",S_INPUT_WIDTH,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_height",S_OUTPUT_HEIGHT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_rowbytes",S_INPUT_ROWBYTES,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_rowbytes",S_OUTPUT_ROWBYTES,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_extent",S_INPUT_EXTENT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_extent",S_OUTPUT_EXTENT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_origin",S_INPUT_ORIGIN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_origin",S_OUTPUT_ORIGIN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_flags",S_INPUT_FLAGS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_flags",S_OUTPUT_FLAGS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_format",S_INPUT_FORMAT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_format",S_OUTPUT_FORMAT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"depth",S_DEPTH,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsx_num",S_DSX_NUM,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsx_den",S_DSX_DEN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsy_num",S_DSY_NUM,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsy_den",S_DSY_DEN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"alias",S_ALIAS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"overlap_forward",S_OVERLAP_FORWARD,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"overlap_backward",S_OVERLAP_BACKWARD,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_null",S_INPUT_NULL,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_null",S_OUTPUT_NULL,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_layer",S_NULL_LAYER,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_output",S_NULL_OUTPUT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"null_param_out",S_NULL_PARAM_OUT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_param_in",S_NULL_PARAM_IN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_pica",S_NULL_PICA,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_acquire",S_NULL_ACQUIRE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_release",S_NULL_RELEASE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"layer_error",S_CALLBACK,LAYER_ERROR,0,70},{"output_error",S_CALLBACK,OUTPUT_ERROR,0,71},
    {"param_checkout_1",S_CALLBACK,PARAM_OUT_ERROR,1,72},{"param_checkout_2",S_CALLBACK,PARAM_OUT_ERROR,2,72},{"param_checkout_3",S_CALLBACK,PARAM_OUT_ERROR,3,72},{"param_checkout_4",S_CALLBACK,PARAM_OUT_ERROR,4,72},{"param_checkout_5",S_CALLBACK,PARAM_OUT_ERROR,5,72},
    {"param_checkin_1",S_CALLBACK,PARAM_IN_ERROR,1,73},{"param_checkin_2",S_CALLBACK,PARAM_IN_ERROR,2,73},{"param_checkin_3",S_CALLBACK,PARAM_IN_ERROR,3,73},{"param_checkin_4",S_CALLBACK,PARAM_IN_ERROR,4,73},{"param_checkin_5",S_CALLBACK,PARAM_IN_ERROR,5,73},
    {"suite_acquire",S_CALLBACK,ACQUIRE_ERROR,0,74},{"suite_null",S_CALLBACK,ACQUIRE_NULL,0,PF_Err_BAD_CALLBACK_PARAM},{"format_input",S_CALLBACK,INPUT_FORMAT_ERROR,0,75},{"format_output",S_CALLBACK,OUTPUT_FORMAT_ERROR,0,76},{"suite_release",S_CALLBACK,RELEASE_ERROR,0,80},
    {"copy_error",S_CALLBACK,COPY_ERROR,0,86},{"copy_throw_oom",S_CALLBACK,COPY_THROW_OOM,0,4},{"stage_oom",S_STAGE_OOM,NORMAL,0,4}};
  for(const auto&r:rows)ok&=run_small(r);std::printf("small_all_exact=%d positive=2 negative=%zu\n",ok,sizeof(rows)/sizeof(*rows));return ok?0:4;}
#endif

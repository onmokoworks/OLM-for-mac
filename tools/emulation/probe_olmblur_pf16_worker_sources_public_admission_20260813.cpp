#define OLMBLUR_PF16_7X5_NO_MAIN 1
#include "probe_olmblur_pf16_7x5_public_admission_20260813.cpp"
#undef OLMBLUR_PF16_7X5_NO_MAIN

#include "../../core/olm_sha256_rows.h"

struct WorkerCell {
  const char *id;
  int width, height, rowbytes;
  double amount;
  int smooth_fixed, repeat, bias, legacy, source_kind;
  const char *source_sha256;
  const char *output_sha256;
};

static const WorkerCell kWorkerCells[] = {
  {"12x12_repeat1_nonlegacy",12,12,109,3.0,6553600,1,1,0,0,"df143537b2c987564fd2c0d0b4f9ad3b2332c4db8d5ccbaf8ac3ebc71b05bb8d","f4a8b917c50936578f0573b943e5d9baad29af87b8f17f2efec4765c74771922"},
  {"12x12_repeat2_nonlegacy",12,12,109,3.0,6553600,2,1,0,0,"df143537b2c987564fd2c0d0b4f9ad3b2332c4db8d5ccbaf8ac3ebc71b05bb8d","28d648118306c3ed9bedbcd7e99c7af8f8bc26813b701b366c56b966f3a3e846"},
  {"18x18_repeat1_nonlegacy",18,18,157,11.0,6553600,1,1,0,0,"bc3bfbf7c3d5a908690b71819c9dd83e4bddb9b6f09a417ff06ec6cc3d3943ae","fbf43a4c4832c1c2a8e30187361ddaec6bf95c36a793f71573d8b1db4652a46e"},
  {"18x18_repeat3_nonlegacy",18,18,157,11.0,6553600,3,2,0,0,"bc3bfbf7c3d5a908690b71819c9dd83e4bddb9b6f09a417ff06ec6cc3d3943ae","64355b2ce493e3d318de8fa09f45234b98236029347b62e9d09e4ef8cb98a4bc"},
  {"12x12_repeat2_legacy",12,12,109,3.0,6553600,2,1,1,1,"c97013f8c7c515a75701bb0979f435a0f81bbe9309157cc56a6135e7dbef0eb4","6119d2c5760e5f5234b9c53c990dad3a529777124bdbab794dc46bd562c1e9c0"},
  {"18x18_repeat3_legacy",18,18,157,11.0,6553600,3,2,1,1,"6f911aa2fb9d2aa0f5c9db56936ff1bb0b2a5710cd49adc8e05467722ddef565","b47c25529ac36c0c7af7fb43659d67a5e7d3a4d77172706813dad47e1a700d26"},
  {"18x12_repeat2_legacy_mixed_alpha",18,12,157,3.0,6553600,2,2,1,2,"c402d7ee39d3ef39015414094c13ca7f7308bad7414872a5edf6aa6005bdc6f9","28b16efe8ef4535661f1f514ff69195e944d1c071d78df1e8f5a8034cbcdc346"},
  {"20x16_smooth62_5_legacy",20,16,173,7.0,4096000,4,1,1,3,"d73bbdd3cf1872f20883fa596615702552eadf308e40552763d1eaa698007366","2e97a898b15328c6fb11876f88951c9b1a593a66eb23bcbe89b94784c477ca1b"},
};

static const WorkerCell kRejectedCells[] = {};

static void fill_worker_source(unsigned char *data, int rowbytes, const WorkerCell &cell) {
  const int width=cell.width,height=cell.height;
  for (int y=0;y<height;++y) for (int x=0;x<width;++x) {
    uint16_t p[4]{};
    if(cell.source_kind==2){
      const bool boundary=x==0||x==width-1||y==0||y==height-1;
      const bool hole=(x*7+y*11)%13==0;
      p[0]=(uint16_t)(boundary||hole?0:8192+((x*29+y*17)%4)*16384);
      p[1]=12800;p[2]=25600;p[3]=30000;
    }else if(cell.source_kind==3){
      static const uint16_t words[]={0,1,32767,32768};
      p[0]=words[(x+3*y)%4];p[1]=words[(x+y+1)%4];
      p[2]=words[(2*x+y+2)%4];p[3]=words[(x+2*y+3)%4];
    }else{
      p[0]=(uint16_t)(cell.source_kind==1?32768:(((x*5+y*3)%17)==0?0:32768));
      p[1]=(uint16_t)((257*x+31*y+101)%32769);
      p[2]=(uint16_t)((113*x+211*y+307)%32769);
      p[3]=(uint16_t)((401*x+97*y+503)%32769);
    }
    std::memcpy(data+(size_t)y*rowbytes+(size_t)x*8,p,sizeof(p));
  }
}

static bool run_worker_cell(const WorkerCell &cell, const SmallSpec &spec,
                            bool checkin_present=false) {
  const int width=cell.width,height=cell.height,pixel_bytes=8,rowbytes=cell.rowbytes;
  const size_t payload=(size_t)rowbytes*(size_t)height;
  std::vector<unsigned char> input_store(19+16+payload+19,0xC7),output_store(19+16+payload+19,0xD9);
  unsigned char *input_data=misaligned_payload(input_store,payload,pixel_bytes);
  unsigned char *output_data=misaligned_payload(output_store,payload,pixel_bytes);
  if(!input_data||!output_data)return false;
  for(int y=0;y<height;++y){std::memset(input_data+(size_t)y*rowbytes,0xA5,rowbytes);
    std::memset(output_data+(size_t)y*rowbytes,0xEE,rowbytes);} fill_worker_source(input_data,rowbytes,cell);
  const bool generated_source_exact=olm::sha256_active_rows_match_hex(
    input_data,rowbytes,(size_t)width*pixel_bytes,height,cell.source_sha256);
  if(spec.mutation==S_SOURCE_FIRST)input_data[0]^=1;
  if(spec.mutation==S_SOURCE_MIDDLE)input_data[(size_t)(height/2)*rowbytes+(size_t)(width/2)*pixel_bytes]^=1;
  if(spec.mutation==S_SOURCE_LAST)input_data[(size_t)(height-1)*rowbytes+(size_t)width*pixel_bytes-1]^=1;
  PF_EffectWorld input{},output{};input.world_flags=PF_WorldFlag_DEEP;
  input.data=(PF_PixelPtr)input_data;input.rowbytes=rowbytes;input.width=width;input.height=height;
  input.extent_hint={0,0,width,height};input.origin_x=input.origin_y=0;output=input;output.data=(PF_PixelPtr)output_data;
  g_mode=spec.mode;g_fail_ordinal=spec.ordinal;g_amount=cell.amount;g_smooth=cell.smooth_fixed;g_repeat=cell.repeat;g_bias=cell.bias;g_legacy=cell.legacy;
  g_input_format_override=g_output_format_override=PF_PixelFormat_INVALID;
  if(spec.mutation==S_AMOUNT_UP)g_amount=std::nextafter(cell.amount,INFINITY);
  if(spec.mutation==S_AMOUNT_DOWN)g_amount=std::nextafter(cell.amount,-INFINITY);
  if(spec.mutation==S_SMOOTH_DOWN)--g_smooth;if(spec.mutation==S_SMOOTH_UP)++g_smooth;
  if(spec.mutation==S_REPEAT_DOWN)g_repeat=cell.repeat-1;if(spec.mutation==S_REPEAT_UP)g_repeat=cell.repeat+1;
  if(spec.mutation==S_BIAS_DOWN)g_bias=cell.bias-1;if(spec.mutation==S_BIAS_UP)g_bias=cell.bias+1;
  if(spec.mutation==S_LEGACY_ONE)g_legacy=cell.legacy?0:1;if(spec.mutation==S_LEGACY_INVALID)g_legacy=2;
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
  bool success_exact=true;
  if(spec.mutation==S_OK){
    success_exact=olm::sha256_active_rows_match_hex(output_data,rowbytes,(size_t)width*pixel_bytes,height,cell.output_sha256);
    for(int y=0;y<height;++y)for(int i=width*pixel_bytes;i<rowbytes;++i)
      success_exact&=output_data[(size_t)y*rowbytes+i]==0xA5;
  }
  const bool failure_untouched=spec.mutation==S_OK||output_store==output_before;
  const bool input_exact=input_store==input_before;
  const bool headers_exact=!std::memcmp(&input,&input_header,sizeof(input))&&
    !std::memcmp(&output,&output_header,sizeof(output));
  const bool exact=actual==spec.expected&&generated_source_exact&&input_exact&&failure_untouched&&success_exact&&headers_exact&&g_optional_checkin==0;
  std::printf("WORKER %s %s exact=%d expected=%d actual=%d params=%d/%d suite=%d/%d/%d copy=%d input=%d output=%d success=%d headers=%d\n",
    cell.id,spec.id,exact,spec.expected,actual,g_param_out,g_param_in,g_acquire,g_get_format,g_release,g_copy,
    input_exact,failure_untouched,success_exact,headers_exact);
  return exact;
}

#ifndef OLMBLUR_PF16_WORKER_SOURCES_NO_MAIN
int main(){g_world_suite.PF_GetPixelFormat=get_format;bool ok=true;size_t positives=0,negatives=0;
  const SmallSpec positive={"positive",S_OK,NORMAL,0,PF_Err_NONE};
  const SmallSpec rows[]={
    {"source_first",S_SOURCE_FIRST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"source_middle",S_SOURCE_MIDDLE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"source_last",S_SOURCE_LAST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"amount_up",S_AMOUNT_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"amount_down",S_AMOUNT_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"smooth_down",S_SMOOTH_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"smooth_up",S_SMOOTH_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"repeat_down",S_REPEAT_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"repeat_up",S_REPEAT_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"bias_down",S_BIAS_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"bias_up",S_BIAS_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"legacy_toggle",S_LEGACY_ONE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"legacy_invalid",S_LEGACY_INVALID,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
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
  for(const auto &cell:kWorkerCells){ok&=run_worker_cell(cell,positive,true);ok&=run_worker_cell(cell,positive,false);positives+=2;
    for(const auto &row:rows){if(cell.legacy==0 && cell.width==12 && ((cell.repeat==1 && row.mutation==S_REPEAT_UP) ||
      (cell.repeat==2 && row.mutation==S_REPEAT_DOWN)))continue;ok&=run_worker_cell(cell,row);++negatives;}
    }
  const SmallSpec smooth_mismatch={"retained_smooth62_5_public_mismatch",S_CALLBACK,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM};
  for(const auto &cell:kRejectedCells){ok&=run_worker_cell(cell,smooth_mismatch);++negatives;}
  std::printf("worker_sources_all_exact=%d positive=%zu negative=%zu\n",ok,
    positives,negatives);
  return ok?0:4;}
#endif

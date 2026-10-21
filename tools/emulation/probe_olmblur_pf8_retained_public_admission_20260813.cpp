#define OLMBLUR_PF16_WORKER_SOURCES_NO_MAIN 1
#include "probe_olmblur_pf16_worker_sources_public_admission_20260813.cpp"
#undef OLMBLUR_PF16_WORKER_SOURCES_NO_MAIN

struct PF8Cell {
  const char *id;
  int width, height;
  double amount;
  int smooth_fixed, repeat, bias, legacy, source_kind;
  const char *source_sha256;
  const char *output_sha256;
};

static const PF8Cell kPF8Cells[] = {
  {"nonlegacy_12x12_repeat2",12,12,3.0,6553600,2,1,0,0,"cd47374c1febd0b96676975e0ec02e97b62417a54f9d351995a8e356f4953c8c","b76687e43911deaf3add6c025f955ae852d599b264e567f0c1c1201939ed823b"},
  {"nonlegacy_18x18_repeat3",18,18,11.0,6553600,3,2,0,0,"dda0693f106bc532ef9eb91b3f26c1b257009095e88e3f5e8a1f097a150857bf","069f73793776c475293e72d219b2d43d58319ef68f56e3c79150a3adefcd876e"},
  {"nonlegacy_24x24_repeat1",24,24,129.4,6553600,1,1,0,0,"d0f15a0688bb1f46d516fd9eda08c670953fcf5dab1cad578e8aa14fe23e37bf","9e1890b407be13fdd1cc546081555060eb741c21d817ef519f7f4321a576dc11"},
  {"nonlegacy_24x24_repeat2",24,24,129.4,6553600,2,2,0,0,"d0f15a0688bb1f46d516fd9eda08c670953fcf5dab1cad578e8aa14fe23e37bf","2501da9f856ff5d8cc25dac1c12088f8d65eeee4ec5ef40bc58e4d8f3032cf62"},
  {"legacy_12x12_repeat2",12,12,3.0,6553600,2,1,1,1,"586835578947adf0b3f1a5a5e574398ca66df585766d3af9fd6381ae92225e4a","2d8a58a1fc24f03a2082a2d20ec824ea63f1c7f0f658ea8f3506329e39cac9cd"},
  {"legacy_18x18_repeat3",18,18,11.0,6553600,3,2,1,1,"dac589013b502bab4b245ab77028a823782f09f5fba333c26f775536b389ba04","286b898d8aa8742573965764088c4d1c7f2835e7214f30f1ffce9e6251ecddef"},
  {"legacy_18x12_mixed_alpha",18,12,3.0,6553600,2,2,1,2,"aa8120e34bbcffd2b5eab03b01c9df29a073d3d985a8b505612b9b553ca9aae0","663cb730bdaa4cf552fa74e1e18120e74e0efccda17a11f3f29d29095ca94dba"},
  {"legacy_6x6_boundary_repeat10",6,6,248.6,6553600,10,1,1,3,"680c3cf7dffabc4d4527f3a3698bea01d3a7352786c47e2389891d8f3f19083e","c72f434389bffe31e9164d8c23605657f33b2c421ece6f49b62074afa533a5d7"},
  {"legacy_12x12_boundary_repeat10",12,12,248.6,6553600,10,1,1,3,"e4dd7db49faf3373caa42916e7c8aad47d0fd5385c4a04f6293f12d13dddd29b","d6dbac193bd935e97a3b944596c1e2439d70d70ea089750feed877873dd68d9a"},
  {"legacy_16x16_repeat1",16,16,5.0,6553600,1,1,1,1,"2506b82ef7f054d4c7eff5eb6916f98deb18bff118d81366944a4cdf49f51395","2d14e67722a6b7cccb42c4a4429d3a216cfc2079977ec763127da684e3436c14"},
  {"legacy_10x8_boundary_reverse",10,8,1.0,6553600,2,2,1,3,"21f943c064c606a63f5fd11db556abf61bd8abb022c6e41b164fc8220b9df882","16c35706fddef21394a8ed7f702dbbf6cfae3471edd256a015eaaac05cc3179c"},
  {"legacy_19x13_smooth43_75",19,13,9.0,2867200,3,2,1,4,"81a9e964e8e74810d0cc4d4dbf5d3522cfc5f1513f6d50b306c3628ddfda39f3","3b557809537eac30baa547dacba705071b1ad2293d90b73adcad1b8c4e3ec5ab"},
};

static const PF8Cell kPF8Rejected[] = {};

static void fill_pf8_source(unsigned char *data, int rowbytes, const PF8Cell &cell) {
  for(int y=0;y<cell.height;++y) for(int x=0;x<cell.width;++x) {
    unsigned char p[4]{};
    if(cell.source_kind==2) {
      const bool boundary=x==0||x==cell.width-1||y==0||y==cell.height-1;
      const bool hole=(x*7+y*11)%13==0;
      p[0]=(unsigned char)(boundary||hole?0:32+((x*29+y*17)%4)*64);p[1]=50;p[2]=100;p[3]=150;
    } else if(cell.source_kind==3) {
      const bool boundary=x==0||x==cell.width-1||y==0||y==cell.height-1;
      p[0]=255;p[1]=(unsigned char)(boundary?((x*19+y*23+7)&255):((31+x*9+y*13)&255));p[2]=p[3]=0;
    } else if(cell.source_kind==4) {
      static const unsigned char v[]={0,1,127,128,254,255};
      p[0]=v[(x+5*y)%6];p[1]=v[(2*x+y+1)%6];p[2]=v[(x+3*y+2)%6];p[3]=v[(5*x+2*y+3)%6];
    } else {
      p[0]=(unsigned char)(cell.source_kind==1?255:(((x*5+y*3)%17)==0?0:255));
      p[1]=(unsigned char)((17*x+3*y+11)&255);p[2]=(unsigned char)((7*x+19*y+23)&255);p[3]=(unsigned char)((29*x+13*y+37)&255);
    }
    std::memcpy(data+(size_t)y*rowbytes+(size_t)x*4,p,4);
  }
}

static bool run_pf8_cell(const PF8Cell &cell,const SmallSpec &spec,bool checkin_present=false) {
  const int width=cell.width,height=cell.height,pixel_bytes=4,rowbytes=width*4+13;
  const size_t payload=(size_t)rowbytes*(size_t)height;
  std::vector<unsigned char> input_store(19+16+payload+19,0xC7),output_store(19+16+payload+19,0xD9);
  unsigned char *input_data=misaligned_payload(input_store,payload,pixel_bytes);
  unsigned char *output_data=misaligned_payload(output_store,payload,pixel_bytes);
  if(!input_data||!output_data)return false;
  for(int y=0;y<height;++y){std::memset(input_data+(size_t)y*rowbytes,0xA5,rowbytes);std::memset(output_data+(size_t)y*rowbytes,0xEE,rowbytes);}
  fill_pf8_source(input_data,rowbytes,cell);
  const bool generated_source_exact=olm::sha256_active_rows_match_hex(input_data,rowbytes,(size_t)width*4,height,cell.source_sha256);
  if(spec.mutation==S_SOURCE_FIRST)input_data[0]^=1;
  if(spec.mutation==S_SOURCE_MIDDLE)input_data[(size_t)(height/2)*rowbytes+(size_t)(width/2)*4]^=1;
  if(spec.mutation==S_SOURCE_LAST)input_data[(size_t)(height-1)*rowbytes+(size_t)width*4-1]^=1;
  PF_EffectWorld input{},output{};input.data=(PF_PixelPtr)input_data;input.rowbytes=rowbytes;input.width=width;input.height=height;
  input.extent_hint={0,0,width,height};output=input;output.data=(PF_PixelPtr)output_data;
  g_mode=spec.mode;g_fail_ordinal=spec.ordinal;g_amount=cell.amount;g_smooth=cell.smooth_fixed;g_repeat=cell.repeat;g_bias=cell.bias;g_legacy=cell.legacy;
  g_input_format_override=g_output_format_override=PF_PixelFormat_INVALID;
  if(spec.mutation==S_AMOUNT_UP)g_amount=std::nextafter(cell.amount,INFINITY);if(spec.mutation==S_AMOUNT_DOWN)g_amount=std::nextafter(cell.amount,-INFINITY);
  if(spec.mutation==S_SMOOTH_DOWN)--g_smooth;if(spec.mutation==S_SMOOTH_UP)++g_smooth;if(spec.mutation==S_REPEAT_DOWN)--g_repeat;if(spec.mutation==S_REPEAT_UP)++g_repeat;
  if(spec.mutation==S_BIAS_DOWN)--g_bias;if(spec.mutation==S_BIAS_UP)++g_bias;if(spec.mutation==S_LEGACY_ONE)g_legacy=cell.legacy?0:1;if(spec.mutation==S_LEGACY_INVALID)g_legacy=2;
  if(spec.mutation==S_INPUT_WIDTH)--input.width;if(spec.mutation==S_OUTPUT_HEIGHT)++output.height;if(spec.mutation==S_INPUT_ROWBYTES)--input.rowbytes;if(spec.mutation==S_OUTPUT_ROWBYTES)++output.rowbytes;
  if(spec.mutation==S_INPUT_EXTENT)--input.extent_hint.left;if(spec.mutation==S_OUTPUT_EXTENT)++output.extent_hint.right;if(spec.mutation==S_INPUT_ORIGIN)++input.origin_x;if(spec.mutation==S_OUTPUT_ORIGIN)--output.origin_y;
  if(spec.mutation==S_INPUT_FLAGS)input.world_flags^=PF_WorldFlag_WRITEABLE;if(spec.mutation==S_OUTPUT_FLAGS)output.world_flags^=PF_WorldFlag_WRITEABLE;
  if(spec.mutation==S_INPUT_FORMAT)g_input_format_override=PF_PixelFormat_ARGB64;if(spec.mutation==S_OUTPUT_FORMAT)g_output_format_override=PF_PixelFormat_ARGB128;
  if(spec.mutation==S_ALIAS)output.data=input.data;if(spec.mutation==S_OVERLAP_FORWARD)output.data=(PF_PixelPtr)(input_data+1);if(spec.mutation==S_OVERLAP_BACKWARD)input.data=(PF_PixelPtr)(output_data+1);
  if(spec.mutation==S_INPUT_NULL)input.data=nullptr;if(spec.mutation==S_OUTPUT_NULL)output.data=nullptr;
  const auto input_before=input_store,output_before=output_store;const PF_EffectWorld input_header=input,output_header=output;
  g_input=&input;g_output=&output;g_depth=8;g_pre=g_pixels=g_output_hits=g_optional_checkin=g_param_out=g_param_in=g_copy=0;g_acquire=g_release=g_get_format=0;g_request_exact=false;
  SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;PF_UtilCallbacks utils{};utils.copy=copy_world;PF_InData in{};PF_OutData out{};
  in.effect_ref=(PF_ProgPtr)0x1234;in.current_time=7;in.time_step=1;in.time_scale=24;in.downsample_x={1,1};in.downsample_y={1,1};in.pica_basicP=&basic;in.utils=&utils;in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;
  if(spec.mutation==S_DSX_NUM)in.downsample_x.num=2;if(spec.mutation==S_DSX_DEN)in.downsample_x.den=2;if(spec.mutation==S_DSY_NUM)in.downsample_y.num=2;if(spec.mutation==S_DSY_DEN)in.downsample_y.den=2;
  if(spec.mutation==S_NULL_PICA)in.pica_basicP=nullptr;if(spec.mutation==S_NULL_ACQUIRE)basic.AcquireSuite=nullptr;if(spec.mutation==S_NULL_RELEASE)basic.ReleaseSuite=nullptr;
  PF_SmartRenderInput si{};si.bitdepth=spec.mutation==S_DEPTH?16:8;PF_SmartRenderCallbacks cb{};cb.checkout_layer_pixels=spec.mutation==S_NULL_LAYER?nullptr:pixels;cb.checkin_layer_pixels=checkin_present?optional_checkin:nullptr;cb.checkout_output=spec.mutation==S_NULL_OUTPUT?nullptr:checkout_output;PF_SmartRenderExtra se{&si,&cb};
  if(spec.mutation==S_NULL_PARAM_OUT)in.inter.checkout_param=nullptr;if(spec.mutation==S_NULL_PARAM_IN)in.inter.checkin_param=nullptr;if(spec.mutation==S_STAGE_OOM)g_fail_next_new=true;
  const PF_Err actual=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
  bool success_exact=true;if(spec.mutation==S_OK&&cell.output_sha256){success_exact=olm::sha256_active_rows_match_hex(output_data,rowbytes,(size_t)width*4,height,cell.output_sha256);for(int y=0;y<height;++y)for(int i=width*4;i<rowbytes;++i)success_exact&=output_data[(size_t)y*rowbytes+i]==0xA5;}
  const bool failure_untouched=spec.mutation==S_OK||output_store==output_before;const bool input_exact=input_store==input_before;
  const bool headers_exact=!std::memcmp(&input,&input_header,sizeof(input))&&!std::memcmp(&output,&output_header,sizeof(output));
  const bool exact=actual==spec.expected&&generated_source_exact&&input_exact&&failure_untouched&&success_exact&&headers_exact&&g_optional_checkin==0;
  std::printf("PF8 %s %s exact=%d expected=%d actual=%d params=%d/%d suite=%d/%d/%d copy=%d input=%d output=%d success=%d headers=%d\n",cell.id,spec.id,exact,spec.expected,actual,g_param_out,g_param_in,g_acquire,g_get_format,g_release,g_copy,input_exact,failure_untouched,success_exact,headers_exact);
  return exact;
}

#ifndef OLMBLUR_PF8_RETAINED_NO_MAIN
int main(){g_world_suite.PF_GetPixelFormat=get_format;bool ok=true;size_t positives=0,negatives=0;
  const SmallSpec positive={"positive",S_OK,NORMAL,0,PF_Err_NONE};
  const SmallSpec rows[]={
    {"source_first",S_SOURCE_FIRST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"source_middle",S_SOURCE_MIDDLE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"source_last",S_SOURCE_LAST,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"amount_up",S_AMOUNT_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"amount_down",S_AMOUNT_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"smooth_down",S_SMOOTH_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"smooth_up",S_SMOOTH_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"repeat_down",S_REPEAT_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"repeat_up",S_REPEAT_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"bias_down",S_BIAS_DOWN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"bias_up",S_BIAS_UP,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"legacy_toggle",S_LEGACY_ONE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"legacy_invalid",S_LEGACY_INVALID,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_width",S_INPUT_WIDTH,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_height",S_OUTPUT_HEIGHT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_rowbytes",S_INPUT_ROWBYTES,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_rowbytes",S_OUTPUT_ROWBYTES,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_extent",S_INPUT_EXTENT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_extent",S_OUTPUT_EXTENT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_origin",S_INPUT_ORIGIN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_origin",S_OUTPUT_ORIGIN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_flags",S_INPUT_FLAGS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_flags",S_OUTPUT_FLAGS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"input_format",S_INPUT_FORMAT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_format",S_OUTPUT_FORMAT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"depth",S_DEPTH,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsx_num",S_DSX_NUM,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsx_den",S_DSX_DEN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsy_num",S_DSY_NUM,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"dsy_den",S_DSY_DEN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"alias",S_ALIAS,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"overlap_forward",S_OVERLAP_FORWARD,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"overlap_backward",S_OVERLAP_BACKWARD,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"input_null",S_INPUT_NULL,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"output_null",S_OUTPUT_NULL,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"null_layer",S_NULL_LAYER,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_output",S_NULL_OUTPUT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_param_out",S_NULL_PARAM_OUT,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_param_in",S_NULL_PARAM_IN,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_pica",S_NULL_PICA,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_acquire",S_NULL_ACQUIRE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},{"null_release",S_NULL_RELEASE,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM},
    {"layer_error",S_CALLBACK,LAYER_ERROR,0,70},{"output_error",S_CALLBACK,OUTPUT_ERROR,0,71},{"param_checkout_1",S_CALLBACK,PARAM_OUT_ERROR,1,72},{"param_checkout_2",S_CALLBACK,PARAM_OUT_ERROR,2,72},{"param_checkout_3",S_CALLBACK,PARAM_OUT_ERROR,3,72},{"param_checkout_4",S_CALLBACK,PARAM_OUT_ERROR,4,72},{"param_checkout_5",S_CALLBACK,PARAM_OUT_ERROR,5,72},
    {"param_checkin_1",S_CALLBACK,PARAM_IN_ERROR,1,73},{"param_checkin_2",S_CALLBACK,PARAM_IN_ERROR,2,73},{"param_checkin_3",S_CALLBACK,PARAM_IN_ERROR,3,73},{"param_checkin_4",S_CALLBACK,PARAM_IN_ERROR,4,73},{"param_checkin_5",S_CALLBACK,PARAM_IN_ERROR,5,73},{"suite_acquire",S_CALLBACK,ACQUIRE_ERROR,0,74},{"suite_null",S_CALLBACK,ACQUIRE_NULL,0,PF_Err_BAD_CALLBACK_PARAM},{"format_input",S_CALLBACK,INPUT_FORMAT_ERROR,0,75},{"format_output",S_CALLBACK,OUTPUT_FORMAT_ERROR,0,76},{"suite_release",S_CALLBACK,RELEASE_ERROR,0,80},{"copy_error",S_CALLBACK,COPY_ERROR,0,86},{"copy_throw_oom",S_CALLBACK,COPY_THROW_OOM,0,4},{"stage_oom",S_STAGE_OOM,NORMAL,0,4}};
  for(const auto&cell:kPF8Cells){ok&=run_pf8_cell(cell,positive,true);ok&=run_pf8_cell(cell,positive,false);positives+=2;for(const auto&row:rows){ok&=run_pf8_cell(cell,row);++negatives;}}
  const SmallSpec rejected={"retained_public_mismatch",S_CALLBACK,NORMAL,0,PF_Err_BAD_CALLBACK_PARAM};for(const auto&cell:kPF8Rejected){ok&=run_pf8_cell(cell,rejected);++negatives;}
  std::printf("pf8_retained_all_exact=%d positive=%zu negative=%zu\n",ok,positives,negatives);return ok?0:4;
}
#endif

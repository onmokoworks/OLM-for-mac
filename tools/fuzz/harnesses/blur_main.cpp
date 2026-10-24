// Uses the retained OLMBlur real-SDK public callbacks and their parameter units.
int main(int argc,char **argv) {
    if(argc!=7)return 64;
    int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]);
    if(w<1||h<1||w>4096||h>4096||(depth!=8&&depth!=16&&depth!=32))return 64;
    size_t ps=depth/8*4,active=w*ps,rb=active+atoi(argv[6]);
    std::vector<unsigned char> input(rb*h,0xa5),output(rb*h,0xee);
    for(int y=0;y<h;++y)if(fread(input.data()+y*rb,1,active,stdin)!=active)return 65;
    if(getchar()!=EOF)return 65;const auto before=input,output_before=output;
    PF_ParamDef defs[6]{};PF_ParamDef *params[6];
    for(int i=0;i<6;++i)params[i]=defs+i;
    if(!fuzz_parameters(argv[5],defs,6))return 66;
    PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.rowbytes=rb;iw.width=w;iw.height=h;
    iw.extent_hint={0,0,w,h};iw.world_flags=depth==8?0:PF_WorldFlag_DEEP;
    ow=iw;ow.data=(PF_PixelPtr)output.data();defs[0].u.ld=iw;
    g_input=&defs[0].u.ld;g_output=&ow;g_depth=depth;
    g_amount=defs[1].u.fs_d.value;g_smooth=defs[2].u.fd.value;g_repeat=defs[3].u.sd.value;
    g_bias=defs[4].u.pd.value;g_legacy=defs[5].u.bd.value;
    g_world_suite.PF_GetPixelFormat=get_format;
    SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;
    PF_UtilCallbacks utils{};utils.copy=copy_world;
    PF_InData in{};PF_OutData out{};in.pica_basicP=&basic;in.utils=&utils;in.width=w;in.height=h;
    in.downsample_x={1,1};in.downsample_y={1,1};in.time_step=1;in.time_scale=24;
    in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;
    PF_Err error;
    if(!strcmp(argv[4],"classic"))error=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    else {
        PF_PreRenderInput pi{};pi.bitdepth=depth;pi.output_request.rect={0,0,w,h};g_expected_request=pi.output_request;
        PF_PreRenderOutput po{};PF_PreRenderCallbacks pc{};pc.checkout_layer=pre_checkout;
        PF_PreRenderExtra pe{&pi,&po,&pc};error=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
        if(!error) {
            PF_SmartRenderInput si{};si.bitdepth=depth;si.pre_render_data=po.pre_render_data;si.output_request=pi.output_request;
            PF_SmartRenderCallbacks sc{pixels,optional_checkin,checkout_output};PF_SmartRenderExtra se{&si,&sc};
            error=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
        }
        if(po.delete_pre_render_data_func&&po.pre_render_data)po.delete_pre_render_data_func(po.pre_render_data);
    }
    if(input!=before)return 67;
    for(int y=0;y<h;++y)for(size_t x=active;x<rb;++x)if(output[y*rb+x]!=0xee)return 68;
    if(error&&output!=output_before)return 69;
    if(g_param_out!=g_param_in||g_acquire!=g_release)return 70;
    fprintf(stderr,"ERROR %d\nCOUNTS %d %d %d %d %d %d\n",int(error),g_pre,g_pixels,g_output_hits,g_param_out,g_param_in,g_copy);
    if(!error)for(int y=0;y<h;++y)fwrite(output.data()+y*rb,1,active,stdout);
    return 0;
}

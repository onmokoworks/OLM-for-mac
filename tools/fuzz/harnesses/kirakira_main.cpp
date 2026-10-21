// Appended to the existing bounded public host's callbacks and default ramps.
int main(int argc,char **argv) {
    if(argc!=8)return 64;
    int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]);
    if(w<1||h<1||w>256||h>256||(depth!=8&&depth!=16&&depth!=32))return 64;
    size_t ps=depth/8*4,active=w*ps,irb=active+atoi(argv[6]),orb=active+atoi(argv[7]);
    std::vector<unsigned char> input(irb*h,0xa5),output(orb*h,0xee);
    for(int y=0;y<h;++y)if(fread(input.data()+y*irb,1,active,stdin)!=active)return 65;
    if(getchar()!=EOF)return 65;const auto before=input,output_before=output;
    init_params(kTuples[0]);
    if(!fuzz_parameters(argv[5],g_defs,OLMKIRAKIRA_NUM_PARAMS))return 66;
    PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.rowbytes=irb;iw.width=w;iw.height=h;
    iw.extent_hint={0,0,w,h};iw.world_flags=depth==8?0:PF_WorldFlag_DEEP;
    ow=iw;ow.data=(PF_PixelPtr)output.data();ow.rowbytes=orb;
    HostState state{&iw,&ow};PF_InData in{};PF_OutData out{};
    in.pica_basicP=&g_basic;in.effect_ref=(PF_ProgPtr)&state;in.width=w;in.height=h;
    in.downsample_x={1,1};in.downsample_y={1,1};in.time_step=1;in.time_scale=24;
    in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;
    g_format_input_world=&iw;g_format_output_world=g_format_classic_world=&ow;
    g_input_format=g_output_format=depth==8?PF_PixelFormat_ARGB32:depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
    PF_ParamDef *params[OLMKIRAKIRA_NUM_PARAMS];
    for(int i=0;i<OLMKIRAKIRA_NUM_PARAMS;++i)params[i]=g_defs+i;
    g_defs[0].u.ld=iw;g_format_classic_input_world=&g_defs[0].u.ld;
    PF_Err error=0;
    if(!strcmp(argv[4],"classic"))error=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    else {
        PF_PreRenderInput pi{};pi.bitdepth=depth;pi.output_request.rect={0,0,w,h};
        PF_PreRenderOutput po{};PF_PreRenderCallbacks pc{};pc.checkout_layer=pre_checkout;
        PF_PreRenderExtra pe{&pi,&po,&pc};error=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
        if(!error) {
            PF_SmartRenderInput si{};si.bitdepth=depth;si.pre_render_data=po.pre_render_data;si.output_request=pi.output_request;
            PF_SmartRenderCallbacks sc{checkout_pixels,checkin_pixels,checkout_output};PF_SmartRenderExtra se{&si,&sc};
            error=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
        }
        if(po.delete_pre_render_data_func&&po.pre_render_data)po.delete_pre_render_data_func(po.pre_render_data);
    }
    if(input!=before)return 67;
    for(int y=0;y<h;++y)for(size_t x=active;x<orb;++x)if(output[y*orb+x]!=0xee)return 68;
    if(error&&output!=output_before)return 69;
    if(g_checkout_attempts!=g_checkin_attempts)return 70;
    while(!g_sizes.empty())host_dispose_handle(g_sizes.begin()->first);
    fprintf(stderr,"ERROR %d\nCOUNTS %d %d %d %d %d\n",int(error),state.pre,state.pixels,state.output_checkout,g_checkout_attempts,g_checkin_attempts);
    if(!error)for(int y=0;y<h;++y)fwrite(output.data()+y*orb,1,active,stdout);
    return 0;
}

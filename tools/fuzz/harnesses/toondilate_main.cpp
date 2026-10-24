// Drives the production EffectMain through the retained same-source SDK host.
int main(int argc,char **argv) {
    if(argc!=8)return 64;
    int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]);
    if(w<1||h<1||w>4096||h>4096||(depth!=8&&depth!=16&&depth!=32))return 64;
    size_t ps=depth/8*4,active=w*ps,irb=active+atoi(argv[6]),orb=active+atoi(argv[7]);
    std::vector<unsigned char> input(irb*h,0xa5),outbuf(orb*h,0xee);
    for(int y=0;y<h;++y)if(fread(input.data()+y*irb,1,active,stdin)!=active)return 65;
    if(getchar()!=EOF)return 65;const auto before=input,output_before=outbuf;
    PF_ParamDef defs[2]{};PF_ParamDef *params[]={defs,defs+1};
    if(!fuzz_parameters(argv[5],defs,2))return 66;
    g_radius=defs[1].u.fs_d.value;g_depth=depth;
    PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.rowbytes=irb;iw.width=w;iw.height=h;
    iw.extent_hint={0,0,w,h};iw.world_flags=depth==8?0:PF_WorldFlag_DEEP;
    ow=iw;ow.data=(PF_PixelPtr)outbuf.data();ow.rowbytes=orb;
    defs[0].u.ld=iw;g_input=&defs[0].u.ld;g_output=&ow;
    g_world_suite.PF_GetPixelFormat=get_pixel_format;
    SPBasicSuite basic{};basic.AcquireSuite=acquire_suite;basic.ReleaseSuite=release_suite;
    PF_InData in{};PF_OutData out{};in.pica_basicP=&basic;in.width=w;in.height=h;
    in.downsample_x={1,1};in.downsample_y={1,1};in.time_step=1;in.time_scale=24;
    in.inter.checkout_param=checkout_param;in.inter.checkin_param=checkin_param;
    PF_Err error;
    if(!strcmp(argv[4],"classic"))error=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    else {
        PF_PreRenderInput pi{};pi.bitdepth=depth;pi.output_request.rect={0,0,w,h};
        PF_PreRenderOutput po{};PF_PreRenderCallbacks pc{};pc.checkout_layer=pre_checkout;
        PF_PreRenderExtra pe{&pi,&po,&pc};error=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
        if(!error) {
            PF_SmartRenderInput si{};si.bitdepth=depth;si.pre_render_data=po.pre_render_data;si.output_request=pi.output_request;
            PF_SmartRenderCallbacks cb{pixels,checkin,output};PF_SmartRenderExtra se{&si,&cb};
            error=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
        }
        if(po.delete_pre_render_data_func&&po.pre_render_data)po.delete_pre_render_data_func(po.pre_render_data);
    }
    if(input!=before)return 67;
    for(int y=0;y<h;++y)for(size_t x=active;x<orb;++x)if(outbuf[y*orb+x]!=0xee)return 68;
    if(error&&outbuf!=output_before)return 69;
    if(g_param!=g_param_checkin||g_suite_acquire!=g_suite_release||g_suite_bad)return 70;
    fprintf(stderr,"ERROR %d\nCOUNTS %d %d %d %d %d %d\n",int(error),g_pre,g_pixels,g_output_hits,g_checkin,g_param,g_param_checkin);
    if(!error)for(int y=0;y<h;++y)fwrite(outbuf.data()+y*orb,1,active,stdout);
    return 0;
}

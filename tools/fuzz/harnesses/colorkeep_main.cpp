// Same public iterate/color/parameter callbacks as the retained covering host.
int main(int argc,char **argv) {
    if(argc!=8)return 64;
    int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]);
    if(w<1||h<1||w>256||h>256||(depth!=8&&depth!=16&&depth!=32))return 64;
    size_t ps=depth/8*4,active=w*ps,irb=active+atoi(argv[6]),orb=active+atoi(argv[7]);
    std::vector<unsigned char> input(irb*h,0xa5),outbuf(orb*h,0xee);
    for(int y=0;y<h;++y)if(fread(input.data()+y*irb,1,active,stdin)!=active)return 65;
    if(getchar()!=EOF)return 65;const auto before=input,output_before=outbuf;
    if(!fuzz_parameters(argv[5],fuzz_defs,102))return 66;
    PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.rowbytes=irb;iw.width=w;iw.height=h;
    iw.extent_hint={0,0,w,h};iw.world_flags=depth==8?0:PF_WorldFlag_DEEP;
    ow=iw;ow.data=(PF_PixelPtr)outbuf.data();ow.rowbytes=orb;
    fuzz_defs[0].u.ld=iw;gin=&fuzz_defs[0].u.ld;gout=&ow;gdepth=depth;
    s8.iterate=i8;s16.iterate=i16;sf.iterate=iff;sc.PF_GetFloatingPointColorFromColorDef=color;sw.PF_GetPixelFormat=worldfmt;
    PF_ParamDef *params[102];for(int i=0;i<102;++i)params[i]=fuzz_defs+i;
    SPBasicSuite basic{};basic.AcquireSuite=acquire;basic.ReleaseSuite=release;
    PF_InData in{};PF_OutData out{};in.pica_basicP=&basic;in.width=w;in.height=h;
    in.downsample_x={1,1};in.downsample_y={1,1};in.time_step=1;in.time_scale=24;
    in.inter.checkout_param=checkout;in.inter.checkin_param=check_param;
    PF_Err error;
    if(!strcmp(argv[4],"classic"))error=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    else {
        PF_PreRenderInput pi{};pi.bitdepth=depth;pi.output_request.rect={0,0,w,h};
        PF_PreRenderOutput po{};PF_PreRenderCallbacks pc{};pc.checkout_layer=pre;
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
    if(checks!=param_checkins)return 70;
    fprintf(stderr,"ERROR %d\nCOUNTS %d %d %d %d %d %d\n",int(error),pre_hits,layer_hits,output_hits,checkin_hits,checks,param_checkins);
    if(!error)for(int y=0;y<h;++y)fwrite(outbuf.data()+y*orb,1,active,stdout);
    return 0;
}

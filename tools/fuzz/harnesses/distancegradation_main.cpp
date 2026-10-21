// Reuses the public owner contract's SDK shim and checkout callbacks.
int main(int argc,char **argv) {
    if(argc!=8)return 64;
    W=atoi(argv[1]);H=atoi(argv[2]);int depth=atoi(argv[3]);
    if(W<1||H<1||W>256||H>256||(depth!=8&&depth!=16&&depth!=32))return 64;
    int ps=depth/8*4,active=W*ps,irb=active+atoi(argv[6]),orb=active+atoi(argv[7]);
    std::vector<unsigned char> input(irb*H,0xa5),output(orb*H,0xee);
    for(int y=0;y<H;++y)if(fread(input.data()+y*irb,1,active,stdin)!=(size_t)active)return 65;
    if(getchar()!=EOF)return 65;const auto before=input,output_before=output;
    if(!fuzz_parameters(argv[5],g_params.data(),DG_NUM_PARAMS))return 66;
    PF_EffectWorld iw{input.data(),W,H,irb,(short)depth,{0,0,W,H}};
    PF_EffectWorld ow{output.data(),W,H,orb,(short)depth,{0,0,W,H}};
    g_input=&iw;g_output=&ow;g_params[0].u.ld=iw;
    dg_harness_checkout_param=checkout_param;dg_harness_checkin_param=checkin_param;
    PF_InData in{};PF_OutData out{};in.width=W;in.height=H;
    in.downsample_x={1,1};in.downsample_y={1,1};in.time_step=1;in.time_scale=24;
    PF_ParamDef *params[DG_NUM_PARAMS];for(int i=0;i<DG_NUM_PARAMS;++i)params[i]=&g_params[i];
    PF_Err error;
    if(!strcmp(argv[4],"classic"))error=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    else {
        PF_PreRenderInput pi{};pi.bitdepth=depth;pi.output_request.rect={0,0,W,H};
        PF_PreRenderOutput po{};PF_PreRenderCallbacks pc{pre_checkout};PF_PreRenderExtra pe{&pi,&po,&pc};
        error=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
        if(!error) {
            PF_SmartRenderInput si{(short)depth};si.pre_render_data=po.pre_render_data;
            PF_SmartRenderCallbacks cb{checkout_pixels,checkin_pixels,checkout_output};PF_SmartRenderExtra se{&si,&cb};
            error=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
        }
        if(po.delete_pre_render_data_func&&po.pre_render_data)po.delete_pre_render_data_func(po.pre_render_data);
    }
    if(input!=before)return 67;
    for(int y=0;y<H;++y)for(int x=active;x<orb;++x)if(output[y*orb+x]!=0xee)return 68;
    if(error&&output!=output_before)return 69;
    if(g_param_checkout!=g_param_checkin)return 70;
    fprintf(stderr,"ERROR %d\nCOUNTS %d %d %d %d %d %d\n",int(error),g_pre,g_pixels,g_output_checkout,g_layer_checkin,g_param_checkout,g_param_checkin);
    if(!error)for(int y=0;y<H;++y)fwrite(output.data()+y*orb,1,active,stdout);
    return 0;
}

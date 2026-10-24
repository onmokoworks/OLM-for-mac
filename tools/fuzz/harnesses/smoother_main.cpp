#include <fstream>
#include <sstream>
#include <string>
static PF_Err FuzzPre(PF_ProgPtr,A_long index,A_long id,PF_RenderRequest*,A_long,A_long,A_long,PF_CheckoutResult *r) {
    if(index!=SM_INPUT||id!=SM_INPUT)return 90;
    r->result_rect=r->max_result_rect={0,0,g_input->width,g_input->height};return 0;
}
int main(int argc,char **argv) {
    if(argc!=7)return 64;
    int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]);
    if(w<1||h<1||w>4096||h>4096||(depth!=8&&depth!=16&&depth!=32))return 64;
    Fixture f(depth,w,h,atoi(argv[6]));int active=w*depth/8*4;
    for(int y=0;y<h;++y)if(fread(f.input.data()+y*f.iw.rowbytes,1,active,stdin)!=(size_t)active)return 65;
    if(getchar()!=EOF)return 65;const auto before=f.input,output_before=f.output;
    std::ifstream file(argv[5]);std::string line;
    while(std::getline(file,line)) {
        std::istringstream row(line);int slot;char kind;double v;
        if(!(row>>slot>>kind>>v)||slot<=0||slot>=SM_NUM_PARAMS)return 66;
        if(slot==SM_KEY_COLOR) {
            int r,g,b;if(kind!='c'||!(row>>r>>g>>b))return 66;
            f.defs[slot].u.cd.value={(unsigned char)v,(unsigned char)r,(unsigned char)g,(unsigned char)b};
        } else if(slot==SM_USE_KEY)f.defs[slot].u.bd.value=(A_long)v;
        else f.defs[slot].u.sd.value=(A_long)v;
    }
    PF_InData in{};PF_OutData out{};in.time_step=1;in.time_scale=24;
    PF_Err error;
    if(!strcmp(argv[4],"classic"))error=EffectMain(PF_Cmd_RENDER,&in,&out,f.params,&f.ow,nullptr);
    else {
        std::memcpy(g_params,f.defs,sizeof(g_params));g_input=&f.iw;g_output=&f.ow;
        g_cli_checkout_param_hook=&Param;g_cli_checkin_param_hook=&ParamCheckin;
        g_cli_checkin_param_error_hook=&ParamCheckinError;
        g_olmsmoother_cli_checkin_layer_hook=&LayerCheckin;
        g_olmsmoother_cli_checkin_layer_error_hook=&LayerCheckinError;
        PF_PreRenderInput pi{};pi.bitdepth=depth;PF_PreRenderOutput po{};
        PF_PreRenderCallbacks pc{FuzzPre};PF_PreRenderExtra pe{&pi,&po,&pc};
        error=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
        if(!error) {
            PF_SmartRenderInput si{(short)depth};PF_SmartRenderCallbacks cb{Layer,Output};PF_SmartRenderExtra se{&si,&cb};
            error=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
        }
    }
    if(f.input!=before)return 67;
    for(int y=0;y<h;++y)for(int x=active;x<f.ow.rowbytes;++x)if(f.output[y*f.ow.rowbytes+x]!=0xa5)return 68;
    if(error&&f.output!=output_before)return 69;
    if(g_param_calls!=g_param_checkins)return 70;
    fprintf(stderr,"ERROR %d\nCOUNTS %d %d %d %d %d\n",int(error),g_layer_calls,g_output_calls,g_param_calls,g_param_checkins,g_layer_checkins);
    if(!error)for(int y=0;y<h;++y)fwrite(f.output.data()+y*f.ow.rowbytes,1,active,stdout);
    return 0;
}

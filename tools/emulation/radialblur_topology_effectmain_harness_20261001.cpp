// Real-SDK public Classic/Smart harness; parameter units follow ParamsSetup.
#include "production_under_test.cpp"
#include <fstream>
#include <sstream>
#include <string>

static PF_EffectWorld *g_input, *g_output;
static PF_ParamDef g_defs[OLMRADIALBLUR_NUM_PARAMS];
static PF_PixelFormat g_format;
static int g_param_out, g_param_in, g_pixel_out, g_pixel_in, g_pre, g_acquire, g_release;
static PF_Err format(const PF_EffectWorld*, PF_PixelFormat *v) { *v=g_format; return 0; }
static PF_WorldSuite2 g_suite{nullptr,nullptr,format};
static SPErr acquire(const char *name, int32 version, const void **suite) {
    if (strcmp(name,kPFWorldSuite)||version!=kPFWorldSuiteVersion2) return kSPBadParameterError;
    ++g_acquire; *suite=&g_suite; return kSPNoError;
}
static SPErr release(const char*,int32) { ++g_release; return kSPNoError; }
static PF_Err checkout(PF_ProgPtr, A_long slot, A_long, A_long, A_u_long, PF_ParamDef *v) {
    if (slot<=0||slot>=OLMRADIALBLUR_NUM_PARAMS) return PF_Err_BAD_CALLBACK_PARAM;
    ++g_param_out; *v=g_defs[slot]; return 0;
}
static PF_Err checkin(PF_ProgPtr,PF_ParamDef*) { ++g_param_in; return 0; }
static PF_Err pre(PF_ProgPtr,PF_ParamIndex slot,A_long id,const PF_RenderRequest *request,
                  A_long,A_long,A_u_long,PF_CheckoutResult *result) {
    if(slot||id||!request->preserve_rgb_of_zero_alpha||request->rect.left||request->rect.top||
       request->rect.right!=g_input->width||request->rect.bottom!=g_input->height) return 710;
    ++g_pre; *result={};result->result_rect={0,0,g_input->width,g_input->height};
    result->max_result_rect=result->result_rect;result->ref_width=g_input->width;result->ref_height=g_input->height;return 0;
}
static PF_Err pixels(PF_ProgPtr,A_long slot,PF_EffectWorld **v) {
    if(slot)return 711; ++g_pixel_out; *v=g_input; return 0;
}
static PF_Err pixels_in(PF_ProgPtr,A_long slot) { if(slot)return 712; ++g_pixel_in;return 0; }
static PF_Err output(PF_ProgPtr,PF_EffectWorld **v) { *v=g_output;return 0; }

int main(int argc,char **argv) {
    if(argc!=6)return 64;
    const int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]);
    if(w<1||h<1||w>64||h>64||(depth!=8&&depth!=16&&depth!=32))return 64;
    const size_t ps=depth==8?4:depth==16?8:16,active=w*ps,irb=active+3*ps,orb=active+5*ps;
    std::vector<unsigned char> a(irb*h,0xa5),b(orb*h,0xee);
    for(int y=0;y<h;++y)if(fread(a.data()+y*irb,1,active,stdin)!=active)return 65;
    if(getchar()!=EOF)return 65;const auto before=a,output_before=b;
    PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)a.data();iw.rowbytes=irb;iw.width=w;iw.height=h;
    iw.extent_hint={0,0,w,h};iw.world_flags=depth==8?0:PF_WorldFlag_DEEP;
    ow=iw;ow.data=(PF_PixelPtr)b.data();ow.rowbytes=orb;
    g_input=&iw;g_output=&ow;g_format=depth==8?PF_PixelFormat_ARGB32:depth==16?PF_PixelFormat_ARGB64:PF_PixelFormat_ARGB128;
    PF_ParamDef *params[OLMRADIALBLUR_NUM_PARAMS];
    for(int i=0;i<OLMRADIALBLUR_NUM_PARAMS;++i){g_defs[i]={};g_defs[i].uu.id=i;params[i]=&g_defs[i];}
    g_defs[0].u.ld=iw;
    std::ifstream file(argv[5]);std::string line;
    while(std::getline(file,line)) {
        std::istringstream row(line);int slot;char kind;double v,z=0;
        if(!(row>>slot>>kind>>v)||slot<=0||slot>=OLMRADIALBLUR_NUM_PARAMS)return 66;
        if(kind=='p') {if(!(row>>z))return 66;g_defs[slot].u.td.x_value=(PF_Fixed)llround(v*65536);g_defs[slot].u.td.y_value=(PF_Fixed)llround(z*65536);}
        else if(kind=='a')g_defs[slot].u.ad.value=(PF_Fixed)llround(v*65536);
        else if(kind=='i')g_defs[slot].u.sd.value=(A_long)v;
        else if(kind=='u')g_defs[slot].u.pd.value=(A_long)v;
        else if(kind=='b')g_defs[slot].u.bd.value=v!=0;
        else if(kind=='s')g_defs[slot].u.fs_d.value=v;
        else return 66;
    }
    SPBasicSuite basic{acquire,release};PF_InData in{};PF_OutData out{};
    in.pica_basicP=&basic;in.width=w;in.height=h;in.downsample_x={1,1};in.downsample_y={1,1};
    in.current_time=0;in.time_step=1;in.time_scale=24;in.inter.checkout_param=checkout;in.inter.checkin_param=checkin;
    PF_Err error=0;
    if(!strcmp(argv[4],"classic"))error=EffectMain(PF_Cmd_RENDER,&in,&out,params,&ow,nullptr);
    else {
        PF_PreRenderInput pi{};pi.bitdepth=depth;pi.output_request.rect={0,0,w,h};
        PF_PreRenderOutput po{};PF_PreRenderCallbacks pc{};pc.checkout_layer=pre;PF_PreRenderExtra pe{&pi,&po,&pc};
        error=EffectMain(PF_Cmd_SMART_PRE_RENDER,&in,&out,nullptr,nullptr,&pe);
        if(!error) {
            PF_SmartRenderInput si{};si.bitdepth=depth;si.output_request=pi.output_request;si.pre_render_data=po.pre_render_data;
            PF_SmartRenderCallbacks sc{pixels,pixels_in,output};PF_SmartRenderExtra se{&si,&sc};
            error=EffectMain(PF_Cmd_SMART_RENDER,&in,&out,nullptr,nullptr,&se);
        }
        if(po.delete_pre_render_data_func&&po.pre_render_data)po.delete_pre_render_data_func(po.pre_render_data);
    }
    if(a!=before)return 67;
    for(int y=0;y<h;++y)for(size_t x=active;x<orb;++x)if(b[y*orb+x]!=0xee)return 68;
    if(error&&b!=output_before)return 69;if(g_acquire!=g_release||g_param_out!=g_param_in||g_pixel_out!=g_pixel_in)return 70;
    const auto info=InfoFromParams(params,w,h);
    fprintf(stderr,"ERROR %d\nCOUNTS %d %d %d %d %d %d %d\nINFO %.17g %ld %ld %ld\n",(int)error,
            g_pre,g_param_out,g_param_in,g_pixel_out,g_pixel_in,g_acquire,g_release,
            info.angle_deg,(long)info.outer_edge_fade,(long)info.inner_edge_fade,(long)info.noise_offset);
    if(!error)for(int y=0;y<h;++y)if(fwrite(b.data()+y*orb,1,active,stdout)!=active)return 71;
    return 0;
}

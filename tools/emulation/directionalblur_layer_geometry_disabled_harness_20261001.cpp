#define OLM_DBLUR_TEST_SEAM 1
#include "../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <sstream>
#include <string>

int main(int argc,char**argv) {
    if(argc!=7)return 64;
    const int layer_width=atoi(argv[5]),layer_height=atoi(argv[6]);
    if(layer_width<1||layer_height<1||layer_width>64||layer_height>64)return 64;
    int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]);
    if(w<1||h<1||w>64||h>64||(depth!=8&&depth!=16&&depth!=32))return 64;
    PF_ParamDef d[OLMDIRECTIONALBLUR_NUM_PARAMS]{};PF_ParamDef*p[OLMDIRECTIONALBLUR_NUM_PARAMS]{};
    for(int i=0;i<OLMDIRECTIONALBLUR_NUM_PARAMS;++i)p[i]=d+i;
    d[OLMDIRECTIONALBLUR_ANGLE].u.ad.value=17*65536+16384;
    d[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN].u.fs_d.value=1;
    d[OLMDIRECTIONALBLUR_FRONT_STRENGTH].u.sd.value=4;
    d[OLMDIRECTIONALBLUR_BACK_STRENGTH].u.sd.value=3;
    d[OLMDIRECTIONALBLUR_NOISE_TYPE].u.pd.value=3;
    d[OLMDIRECTIONALBLUR_NOISE_VARIATION].u.fd.value=73*65536+49152;
    d[OLMDIRECTIONALBLUR_NOISE_LAYER].u.ld.dephault=TRUE;
    d[OLMDIRECTIONALBLUR_SEED].u.sd.value=1;
    d[OLMDIRECTIONALBLUR_THICKNESS].u.fs_d.value=3;
    std::stringstream specification(argv[4]);std::string component;
    while(std::getline(specification,component,',')) {
        int slot;double value;if(sscanf(component.c_str(),"%d=%lf",&slot,&value)!=2)return 64;
        if(slot==1||slot==19)d[slot].u.ad.value=static_cast<PF_Fixed>(std::llround(value*65536));
        else if(slot==3||slot==7||slot==12||slot==15)d[slot].u.fd.value=static_cast<PF_Fixed>(std::llround(value*65536));
        else if(slot==2||slot==20)d[slot].u.fs_d.value=value;
        else if(slot==5||slot==6||slot==10||slot==11||slot==16||slot==18)d[slot].u.sd.value=static_cast<A_long>(value);
        else return 64;
    }
    const auto info=InfoFromParams(p,1,1);
    size_t size=depth==8?4:depth==16?8:16,active=w*size,rb=active+16;
    std::vector<unsigned char>input(rb*h,0x3c),output(rb*h,0xa5);
    for(int y=0;y<h;++y)if(fread(input.data()+y*rb,1,active,stdin)!=active)return 65;
    const size_t layer_active=layer_width*size,layer_rb=layer_active+16;
    std::vector<unsigned char>layer(layer_rb*layer_height,0x5a);
    for(int y=0;y<layer_height;++y)if(fread(layer.data()+y*layer_rb,1,layer_active,stdin)!=layer_active)return 65;
    if(getchar()!=EOF)return 65;const auto original=input,layer_before=layer;
    PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.width=w;iw.height=h;iw.rowbytes=rb;iw.extent_hint={0,0,w,h};
    ow.data=(PF_PixelPtr)output.data();ow.width=w;ow.height=h;ow.rowbytes=rb;ow.extent_hint={0,0,w,h};
    PF_EffectWorld lw=iw;lw.data=(PF_PixelPtr)layer.data();lw.width=layer_width;lw.height=layer_height;lw.rowbytes=layer_rb;lw.extent_hint={0,0,layer_width,layer_height};
    int route=-1;PF_Err err=RenderWorld(&iw,&ow,&lw,info,depth,&route);
    printf("PUBLIC_ERROR %d\n",int(err));
    // Analysis candidate grounded in the AEX dimension gate: no field exists
    // when the checked-out Layer differs from the full render dimensions.
    if(err&&depth!=8) {
        auto without_noise=info;without_noise.noise_variation=0;
        err=RenderWorld(&iw,&ow,nullptr,without_noise,depth);
        route=1001;
    }
    if(input!=original||layer!=layer_before)return 66;
    if(err)for(int y=0;y<h;++y)for(size_t x=0;x<active;++x)if(output[y*rb+x]!=0xa5)return 68;
    for(int y=0;y<h;++y)for(size_t x=active;x<rb;++x)if(output[y*rb+x]!=0xa5)return 67;
    printf("ERROR %d\nROUTE %d\nRAW ",int(err),route);
    if(!err)for(int y=0;y<h;++y)for(size_t x=0;x<active;++x)printf("%02x",output[y*rb+x]);puts("");
    return 0;
}

#define OLM_DBLUR_TEST_SEAM 1
#include "../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

int main(int argc,char**argv) {
    if(argc!=6&&argc!=7)return 64;
    int w=atoi(argv[1]),h=atoi(argv[2]),depth=atoi(argv[3]),slot=atoi(argv[4]);
    if(w<1||h<1||w>64||h>64||(depth!=8&&depth!=16&&depth!=32))return 64;
    PF_ParamDef d[OLMDIRECTIONALBLUR_NUM_PARAMS]{};PF_ParamDef*p[OLMDIRECTIONALBLUR_NUM_PARAMS]{};
    for(int i=0;i<OLMDIRECTIONALBLUR_NUM_PARAMS;++i)p[i]=d+i;
    d[OLMDIRECTIONALBLUR_ANGLE].u.ad.value=17*65536+16384;
    d[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN].u.fs_d.value=1;
    d[OLMDIRECTIONALBLUR_FRONT_STRENGTH].u.sd.value=4;
    d[OLMDIRECTIONALBLUR_BACK_STRENGTH].u.sd.value=3;
    d[OLMDIRECTIONALBLUR_NOISE_TYPE].u.pd.value=1;
    d[OLMDIRECTIONALBLUR_SEED].u.sd.value=1;
    d[OLMDIRECTIONALBLUR_THICKNESS].u.fs_d.value=3;
    PF_Fixed fixed=static_cast<PF_Fixed>(std::llround(atof(argv[5])*65536));
    if(slot==19)d[slot].u.ad.value=fixed;
    else if(slot==3||slot==7||slot==12||slot==15)d[slot].u.fd.value=fixed;
    else return 64;
    const auto info=InfoFromParams(p,1,1);
    double value=slot==3?info.size_variation:slot==7?info.front_sharp_tail:slot==12?info.back_sharp_tail:slot==15?info.noise_variation:info.noise_offset;
    float normalized=static_cast<float>(value)/(slot==19?36.0f:100.0f);unsigned bits;memcpy(&bits,&normalized,4);
    printf("INFO %.17g\nBITS %u\n",value,bits);
    size_t size=depth==8?4:depth==16?8:16,active=w*size,rb=active+16;
    std::vector<unsigned char>input(rb*h,0x3c),output(rb*h,0xa5);
    for(int y=0;y<h;++y)if(fread(input.data()+y*rb,1,active,stdin)!=active)return 65;
    if(getchar()!=EOF)return 65;const auto original=input;
    PF_EffectWorld iw{},ow{};iw.data=(PF_PixelPtr)input.data();iw.width=w;iw.height=h;iw.rowbytes=rb;iw.extent_hint={0,0,w,h};
    ow.data=(PF_PixelPtr)output.data();ow.width=w;ow.height=h;ow.rowbytes=rb;ow.extent_hint={0,0,w,h};
    int route=-1;PF_Err err=OLMDirectionalBlurTestRenderWorldRoute(&iw,&ow,&info,depth,&route);
    printf("PUBLIC_ERROR %d\n",int(err));
    // Analysis-only bypass: test the existing typed core before changing any
    // public admission. The report distinguishes this from dispatcher output.
    if(err&&argc==7&&atoi(argv[6])==1&&depth!=8) {
        if(depth==16) {
            std::vector<std::uint16_t> src(w*h*4),dst(src.size());
            for(int y=0;y<h;++y)memcpy(src.data()+y*w*4,input.data()+y*rb,active);
            err=olm_dblur_full_argb16(src.data(),dst.data(),w,h,4,0,info.front_sharp_tail,3,0,info.back_sharp_tail,info.size_variation,1,info.angle_deg,info.noise_variation,1,1,info.noise_offset,3,nullptr,0,1);
            if(!err)for(int y=0;y<h;++y)memcpy(output.data()+y*rb,dst.data()+y*w*4,active);
        } else {
            std::vector<float> src(w*h*4),dst(src.size());
            for(int y=0;y<h;++y)memcpy(src.data()+y*w*4,input.data()+y*rb,active);
            err=olm_dblur_full_argb32(src.data(),dst.data(),w,h,4,0,info.front_sharp_tail,3,0,info.back_sharp_tail,info.size_variation,info.angle_deg,1,info.noise_variation,1,1,info.noise_offset,3,nullptr,0,1);
            if(!err)for(int y=0;y<h;++y)memcpy(output.data()+y*rb,dst.data()+y*w*4,active);
        }
        route=1001;
    }
    if(input!=original)return 66;
    if(err)for(int y=0;y<h;++y)for(size_t x=0;x<active;++x)if(output[y*rb+x]!=0xa5)return 68;
    for(int y=0;y<h;++y)for(size_t x=active;x<rb;++x)if(output[y*rb+x]!=0xa5)return 67;
    printf("ERROR %d\nROUTE %d\nRAW ",int(err),route);
    if(!err)for(int y=0;y<h;++y)for(size_t x=0;x<active;++x)printf("%02x",output[y*rb+x]);puts("");
    return 0;
}

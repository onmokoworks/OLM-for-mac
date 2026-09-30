#define OLM_DBLUR_TEST_SEAM 1
#include "../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 7) return 64;
    int w=atoi(argv[1]), h=atoi(argv[2]), depth=atoi(argv[3]);
    if (w<1 || h<1 || w>64 || h>64 || (depth!=8 && depth!=16 && depth!=32)) return 64;
    size_t size=depth==8?4:(depth==16?8:16), active=w*size, rb=active+16;
    std::vector<unsigned char> input(rb*h,0x3c), output(rb*h,0xa5);
    for (int y=0;y<h;++y) if (fread(input.data()+y*rb,1,active,stdin)!=active) return 65;
    if (getchar()!=EOF) return 65;
    const auto original=input;
    PF_EffectWorld iw{},ow{};
    iw.data=(PF_PixelPtr)input.data(); iw.width=w; iw.height=h; iw.rowbytes=rb; iw.extent_hint={0,0,w,h};
    ow.data=(PF_PixelPtr)output.data(); ow.width=w; ow.height=h; ow.rowbytes=rb; ow.extent_hint={0,0,w,h};
    PF_ParamDef definitions[OLMDIRECTIONALBLUR_NUM_PARAMS]{};
    PF_ParamDef* parameters[OLMDIRECTIONALBLUR_NUM_PARAMS]{};
    for (int i=0;i<OLMDIRECTIONALBLUR_NUM_PARAMS;++i) parameters[i]=&definitions[i];
    definitions[OLMDIRECTIONALBLUR_ANGLE].u.ad.value=static_cast<PF_Fixed>(std::llround(atof(argv[4])*65536.0));
    definitions[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN].u.fs_d.value=1;
    definitions[OLMDIRECTIONALBLUR_FRONT_STRENGTH].u.sd.value=atoi(argv[5]);
    definitions[OLMDIRECTIONALBLUR_BACK_STRENGTH].u.sd.value=atoi(argv[6]);
    definitions[OLMDIRECTIONALBLUR_NOISE_TYPE].u.pd.value=1;
    definitions[OLMDIRECTIONALBLUR_SEED].u.sd.value=1;
    definitions[OLMDIRECTIONALBLUR_THICKNESS].u.fs_d.value=3;
    OLMDirectionalBlurInfo info=InfoFromParams(parameters,1,1);
    int route=-1;
    PF_Err err=OLMDirectionalBlurTestRenderWorldRoute(&iw,&ow,&info,depth,&route);
    if (err || input!=original) { fprintf(stderr,"error=%d route=%d\n",int(err),route); return 66; }
    for (int y=0;y<h;++y) for (size_t x=active;x<rb;++x) if (output[y*rb+x]!=0xa5) return 67;
    printf("RAW "); for (int y=0;y<h;++y) for (size_t x=0;x<active;++x) printf("%02x",output[y*rb+x]); puts("");
    printf("ROUTE %d\n",route);
    printf("ANGLE %.17g\n",static_cast<double>(info.angle_deg));
    return 0;
}

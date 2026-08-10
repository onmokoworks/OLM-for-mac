#include <cmath>
#include <cstdio>
#include <cstring>
#include <type_traits>
#include <vector>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static constexpr int W = 5, H = 5, N = W * H;
static const unsigned char RGB[N][3] = {
    {13, 201, 71}, {240, 17, 133}, {33, 89, 250}, {199, 144, 7}, {81, 2, 173},
    {6, 77, 222}, {151, 219, 38}, {244, 102, 63}, {57, 188, 116}, {123, 45, 209},
    {217, 31, 94}, {42, 231, 155}, {174, 83, 12}, {9, 164, 247}, {232, 196, 51},
    {69, 114, 184}, {255, 61, 3}, {28, 214, 98}, {187, 7, 226}, {104, 171, 39},
    {3, 129, 198}, {143, 238, 76}, {221, 54, 168}, {91, 11, 242}, {166, 153, 24},
};

template<class P> static P make_pixel(int n, bool premul);

template<> PF_Pixel8 make_pixel<PF_Pixel8>(int n, bool premul) {
    static const unsigned char alpha[] = {0, 1, 64, 128, 191, 255};
    const unsigned a = alpha[n % 6];
    auto c = [&](unsigned v) { return premul ? (unsigned char)((v * a + 127u) / 255u) : (unsigned char)v; };
    return PF_Pixel8{(unsigned char)a, c(RGB[n][0]), c(RGB[n][1]), c(RGB[n][2])};
}

template<> PF_Pixel16 make_pixel<PF_Pixel16>(int n, bool premul) {
    static const unsigned short alpha[] = {0, 1, 8192, 16384, 24576, 32768};
    const unsigned a = alpha[n % 6];
    auto q = [](unsigned v) { return (unsigned)std::lround(v * 32768.0 / 255.0); };
    auto c = [&](unsigned v) { const unsigned x = q(v); return premul ? (unsigned short)(((unsigned long long)x * a + 16384u) / 32768u) : (unsigned short)x; };
    PF_Pixel16 p{}; p.alpha=(unsigned short)a; p.red=c(RGB[n][0]); p.green=c(RGB[n][1]); p.blue=c(RGB[n][2]); return p;
}

template<> PF_PixelFloat make_pixel<PF_PixelFloat>(int n, bool premul) {
    static const float alpha[] = {0.f, 1.f/32768.f, .25f, .5f, .75f, 1.f};
    const float a = alpha[n % 6];
    auto c = [&](unsigned v) { const float x=(float)v/255.f; return premul ? x*a : x; };
    return PF_PixelFloat{a, c(RGB[n][0]), c(RGB[n][1]), c(RGB[n][2])};
}

template<class P>
static int run(const char *depth, int version, bool premul, bool enable_key=false, bool gamma_all=false) {
    const size_t pad = std::is_same<P,PF_Pixel8>::value ? 5 : (std::is_same<P,PF_Pixel16>::value ? 7 : 13);
    const size_t rowbytes = W * sizeof(P) + pad;
    std::vector<unsigned char> input(rowbytes * H, 0x3c), output(rowbytes * H, 0xa5);
    for (int y=0; y<H; ++y) for (int x=0; x<W; ++x) {
        const P p=make_pixel<P>(y*W+x,premul);
        std::memcpy(input.data()+y*rowbytes+x*sizeof(P), &p, sizeof(P));
    }
    PF_EffectWorld iw{}, ow{};
    iw.data=input.data(); iw.width=W; iw.height=H; iw.rowbytes=(A_long)rowbytes; iw.extent_hint={0,0,W,H};
    ow.data=output.data(); ow.width=W; ow.height=H; ow.rowbytes=(A_long)rowbytes; ow.extent_hint={0,0,W,H};
    PF_ParamDef storage[SM_NUM_PARAMS]{}; PF_ParamDef *params[SM_NUM_PARAMS]{};
    for (int i=0;i<SM_NUM_PARAMS;++i) params[i]=storage+i;
    storage[SM_ENABLE_KEY].u.bd.value=enable_key; storage[SM_INVERT_KEY].u.bd.value=0;
    storage[SM_KEY_COLOR].u.cd.value={255,13,201,71};
    storage[SM_SMOOTHNESS].u.sd.value=73; storage[SM_EXTRA_SMOOTH].u.sd.value=41;
    storage[SM_SMOOTH_RANGE].u.sd.value=37; storage[SM_VERSION].u.pd.value=version;
    storage[SM_GAMMA_MODE].u.pd.value=gamma_all?GAMMA_ALL_COLORS:GAMMA_NONE; storage[SM_GAMMA_VALUE].u.fs_d.value=2.4;
    storage[SM_NUM_GAMMA_COLORS].u.sd.value=1;
    PF_InData in_data{};
    if (RenderBits<P>(&in_data,params,&iw,&ow)!=PF_Err_NONE) return 2;
    const char *family=enable_key?"key_gammaall":(gamma_all?"gammaall":"base");
    std::printf("%s_v%d_%s_%s ",depth,version,premul?"premul":"straight",family);
    for (unsigned char b: output) std::printf("%02x",b);
    std::puts("");
    return 0;
}

int main() {
    for (int version=1;version<=2;++version) for (int premul=0;premul<=1;++premul) {
        if (run<PF_Pixel8>("PF8",version,premul) || run<PF_Pixel16>("PF16",version,premul) || run<PF_PixelFloat>("PF32",version,premul)) return 2;
    }
    for (int premul=0;premul<=1;++premul) {
        if (run<PF_Pixel8>("PF8",2,premul,false,true) || run<PF_Pixel16>("PF16",2,premul,false,true) || run<PF_PixelFloat>("PF32",2,premul,false,true)) return 2;
        if (run<PF_Pixel8>("PF8",2,premul,true,true) || run<PF_Pixel16>("PF16",2,premul,true,true) || run<PF_PixelFloat>("PF32",2,premul,true,true)) return 2;
    }
    return 0;
}

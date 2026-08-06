#include <cstdio>
#include <cstring>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

template <typename P>
static int run_one(const char *depth, const P pixels[6], size_t padding)
{
	constexpr int width = 3, height = 2;
	const size_t rowbytes = width * sizeof(P) + padding;
	std::vector<unsigned char> in(rowbytes * height, 0x3c), out(rowbytes * height, 0xa5);
	for (int y = 0; y < height; ++y)
		for (int x = 0; x < width; ++x)
			std::memcpy(in.data() + y * rowbytes + x * sizeof(P), &pixels[y * width + x], sizeof(P));
	PF_EffectWorld iw{}, ow{};
	iw.data=in.data(); iw.width=width; iw.height=height; iw.rowbytes=rowbytes; iw.extent_hint={0,0,width,height};
	ow.data=out.data(); ow.width=width; ow.height=height; ow.rowbytes=rowbytes; ow.extent_hint={0,0,width,height};
	PF_ParamDef defs[SM_NUM_PARAMS]{}; PF_ParamDef *params[SM_NUM_PARAMS]{};
	for(int i=0;i<SM_NUM_PARAMS;++i) params[i]=&defs[i];
	defs[SM_SMOOTHNESS].u.sd.value=100; defs[SM_EXTRA_SMOOTH].u.sd.value=0;
	defs[SM_SMOOTH_RANGE].u.sd.value=1; defs[SM_VERSION].u.pd.value=SMOOTHER_V1;
	defs[SM_GAMMA_MODE].u.pd.value=GAMMA_NONE; defs[SM_GAMMA_VALUE].u.fs_d.value=2.4;
	PF_InData id{}; if(RenderBits<P>(&id,params,&iw,&ow)!=PF_Err_NONE) return 2;
	std::printf("%s ",depth); for(unsigned char b:out) std::printf("%02x",b); std::printf("\n");
	return 0;
}

int main()
{
	const PF_Pixel16 p16[6]={{32768,0,0,0},{32768,32768,0,0},{32768,0,32768,0},{32768,0,0,32768},{32768,32768,32768,32768},{32768,16384,16384,16384}};
	const PF_PixelFloat p32[6]={{1,0,0,0},{1,1,0,0},{1,0,1,0},{1,0,0,1},{1,1,1,1},{1,.5f,.5f,.5f}};
	if(int rc=run_one("PF16",p16,6)) return rc; return run_one("PF32",p32,12);
}

#include <cstdio>
#include <cstring>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

int main()
{
	constexpr int width = 3, height = 2;
	constexpr size_t padding = 5;
	const size_t rowbytes = width * sizeof(PF_Pixel8) + padding;
	const PF_Pixel8 pixels[6] = {
		{255,  64, 128, 191}, {255, 191,  64, 128}, {255, 128, 191,  64},
		{255,  32, 223,  96}, {255, 223,  96,  32}, {255,  96,  32, 223},
	};
	std::vector<unsigned char> input(rowbytes * height, 0x3c), output(rowbytes * height, 0xa5);
	for (int y = 0; y < height; ++y)
		for (int x = 0; x < width; ++x)
			std::memcpy(input.data() + y * rowbytes + x * sizeof(PF_Pixel8),
			            &pixels[y * width + x], sizeof(PF_Pixel8));
	PF_EffectWorld iw{}, ow{};
	iw.data=input.data(); iw.width=width; iw.height=height; iw.rowbytes=rowbytes; iw.extent_hint={0,0,width,height};
	ow.data=output.data(); ow.width=width; ow.height=height; ow.rowbytes=rowbytes; ow.extent_hint={0,0,width,height};
	PF_ParamDef defs[SM_NUM_PARAMS]{}; PF_ParamDef *params[SM_NUM_PARAMS]{};
	for (int i=0; i<SM_NUM_PARAMS; ++i) params[i]=&defs[i];
	defs[SM_SMOOTHNESS].u.sd.value=100;
	defs[SM_EXTRA_SMOOTH].u.sd.value=0;
	defs[SM_SMOOTH_RANGE].u.sd.value=1;
	defs[SM_VERSION].u.pd.value=SMOOTHER_V2;
	defs[SM_GAMMA_MODE].u.pd.value=GAMMA_ALL_COLORS;
	defs[SM_GAMMA_VALUE].u.fs_d.value=2.4;
	PF_InData in_data{};
	if (RenderBits<PF_Pixel8>(&in_data,params,&iw,&ow)!=PF_Err_NONE) return 2;
	for(unsigned char byte:output) std::printf("%02x",byte);
	std::puts("");
	return 0;
}

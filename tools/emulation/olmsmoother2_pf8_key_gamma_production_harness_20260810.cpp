#include <cstdio>
#include <cstring>
#include <vector>
#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static int run(const char *label, bool invert)
{
	constexpr int width = 3, height = 2;
	constexpr size_t padding = 5;
	const size_t rowbytes = width * sizeof(PF_Pixel8) + padding;
	const PF_Pixel8 pixels[6] = {
		{255, 1, 1, 1}, {255, 255, 0, 0}, {255, 0, 1, 1},
		{255, 0, 255, 0}, {255, 1, 1, 1}, {255, 96, 191, 64},
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
	defs[SM_ENABLE_KEY].u.bd.value=1; defs[SM_INVERT_KEY].u.bd.value=invert ? 1 : 0;
	defs[SM_KEY_COLOR].u.cd.value={255,1,1,1};
	defs[SM_SMOOTHNESS].u.sd.value=100; defs[SM_SMOOTH_RANGE].u.sd.value=1;
	defs[SM_VERSION].u.pd.value=SMOOTHER_V2;
	defs[SM_GAMMA_MODE].u.pd.value=GAMMA_COLORS_ONLY; defs[SM_GAMMA_VALUE].u.fs_d.value=2.4;
	defs[SM_NUM_GAMMA_COLORS].u.sd.value=2;
	defs[SM_GAMMA_COLOR_0].u.cd.value={255,255,0,0};
	defs[SM_GAMMA_COLOR_1].u.cd.value={255,1,1,1};
	PF_InData in_data{};
	if (RenderBits<PF_Pixel8>(&in_data,params,&iw,&ow)!=PF_Err_NONE) return 2;
	std::printf("%s ",label); for(unsigned char byte:output) std::printf("%02x",byte); std::puts("");
	return 0;
}

int main() { if (int rc=run("noninvert",false)) return rc; return run("invert",true); }

#include <cstdio>
#include <cstring>

#include "../../mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

template <typename P>
static int run_one(const char *depth, const P &input_pixel)
{
	P output_pixel{};
	PF_EffectWorld input{};
	PF_EffectWorld output{};
	input.data = const_cast<P *>(&input_pixel);
	input.width = input.height = 1;
	input.rowbytes = sizeof(P);
	input.extent_hint = PF_LRect{0, 0, 1, 1};
	output.data = &output_pixel;
	output.width = output.height = 1;
	output.rowbytes = sizeof(P);
	output.extent_hint = PF_LRect{0, 0, 1, 1};

	PF_ParamDef defs[SM_NUM_PARAMS]{};
	PF_ParamDef *params[SM_NUM_PARAMS]{};
	for (int i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &defs[i];
	defs[SM_SMOOTHNESS].u.sd.value = 0;
	defs[SM_EXTRA_SMOOTH].u.sd.value = 0;
	defs[SM_SMOOTH_RANGE].u.sd.value = 1;
	defs[SM_VERSION].u.pd.value = SMOOTHER_V1;
	defs[SM_GAMMA_MODE].u.pd.value = GAMMA_NONE;
	defs[SM_GAMMA_VALUE].u.fs_d.value = 2.4;
	defs[SM_NUM_GAMMA_COLORS].u.sd.value = 0;

	PF_InData in_data{};
	const PF_Err err = RenderBits<P>(&in_data, params, &input, &output);
	if (err != PF_Err_NONE) return 10 + err;

	const unsigned char *bytes = reinterpret_cast<const unsigned char *>(&output_pixel);
	std::printf("%s ", depth);
	for (size_t i = 0; i < sizeof(P); ++i) std::printf("%02x", bytes[i]);
	std::printf("\n");
	return 0;
}

int main()
{
	const PF_Pixel16 p16{20480, 4045, 16384, 28723};
	const PF_PixelFloat p32{0.625f, 0.1234567f, 0.5f, 0.8765432f};
	if (const int rc = run_one("PF16", p16)) return rc;
	return run_one("PF32", p32);
}

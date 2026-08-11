#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

int main()
{
	PF_InData in_data{};
	in_data.downsample_x = {1, 1};
	in_data.downsample_y = {1, 1};
	PF_PixelFloat source_pixel{1, 0, 0, 0}, output_pixel{};
	PF_LayerDef source{&source_pixel, 1, 1, (A_long)sizeof(source_pixel), 32, {0, 0, 1, 1}};
	PF_LayerDef output{&output_pixel, 1, 1, (A_long)sizeof(output_pixel), 32, {0, 0, 1, 1}};
	std::array<PF_ParamDef, DG_NUM_PARAMS> storage{};
	PF_ParamDef *params[DG_NUM_PARAMS];
	for (int i = 0; i < DG_NUM_PARAMS; ++i) params[i] = &storage[i];
	storage[DG_INPUT].u.ld = source;
	storage[DG_INVERT].u.bd.value = 1;
	storage[DG_IN_OUT].u.pd.value = IN_OUT_INSIDE;
	storage[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
	storage[DG_USE_BG_COLOR].u.bd.value = 0;
	storage[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
	storage[DG_BG_COLOR].u.cd.value = {255, 16, 160, 48};
	storage[DG_INTERP_MODE].u.pd.value = INTERP_LINEAR;
	storage[DG_POWER].u.fs_d.value = 2.25;
	storage[DG_BLUR_MODE].u.pd.value = BLUR_MODE_BILATERAL;
	storage[DG_BLUR_SIZE].u.sd.value = 1;
	const PF_Err err = RenderBits<PF_PixelFloat>(
		&in_data, params, &source, &output, true);
	if (err != PF_Err_BAD_CALLBACK_PARAM) return 1;
	std::puts("PASS PF32 Smart unadmitted Mode5 tuple fail-closed");
	return 0;
}

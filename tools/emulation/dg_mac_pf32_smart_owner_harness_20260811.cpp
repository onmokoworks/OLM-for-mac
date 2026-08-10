#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>

static constexpr int W = 17, H = 11, RB = W * sizeof(PF_PixelFloat) + 16;
static PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
static std::array<PF_ParamDef, DG_NUM_PARAMS> g_params{};

static PF_Err checkout_pixels(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
	if (index != DG_INPUT || !world) return PF_Err_BAD_CALLBACK_PARAM;
	*world = g_input; return PF_Err_NONE;
}
static PF_Err checkout_output(PF_ProgPtr, PF_EffectWorld **world) {
	if (!world) return PF_Err_BAD_CALLBACK_PARAM;
	*world = g_output; return PF_Err_NONE;
}
static PF_Err checkout_param(A_long index, PF_ParamDef *param) {
	if (index <= 0 || index >= DG_NUM_PARAMS || !param) return PF_Err_BAD_CALLBACK_PARAM;
	*param = g_params[index]; return PF_Err_NONE;
}

int main() {
	std::array<std::uint8_t, RB * H> input_bytes{}, smart_bytes{}, direct_bytes{};
	for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) {
		auto *pixel = reinterpret_cast<PF_PixelFloat *>(input_bytes.data() + y * RB) + x;
		pixel->alpha = (x >= 4 && x < 13 && y >= 2 && y < 9) ? 0.0f : 1.0f;
		pixel->red = ((x * 613 + y * 1231) % 256) / 255.0f;
		pixel->green = ((x * 997 + y * 211) % 256) / 255.0f;
		pixel->blue = ((x * 1499 + y * 307) % 256) / 255.0f;
	}
	PF_EffectWorld input{input_bytes.data(), W, H, RB, 32, {0, 0, W, H}};
	PF_EffectWorld smart{smart_bytes.data(), W, H, RB, 32, {0, 0, W, H}};
	PF_EffectWorld direct{direct_bytes.data(), W, H, RB, 32, {0, 0, W, H}};
	g_input = &input; g_output = &smart; dg_harness_checkout_param = checkout_param;
	g_params[DG_INVERT].u.bd.value = 1;
	g_params[DG_IN_OUT].u.pd.value = IN_OUT_INSIDE;
	g_params[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	g_params[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	g_params[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
	g_params[DG_USE_BG_COLOR].u.bd.value = 1;
	g_params[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
	g_params[DG_BG_COLOR].u.cd.value = {255, 16, 160, 48};
	g_params[DG_INTERP_MODE].u.pd.value = INTERP_LINEAR;
	g_params[DG_POWER].u.fs_d.value = 1;
	g_params[DG_BLUR_MODE].u.pd.value = 2;
	g_params[DG_BLUR_SIZE].u.sd.value = 1;
	PF_InData in{}; in.downsample_x = {1, 1}; in.downsample_y = {1, 1};
	PF_OutData out{}; PF_SmartRenderInput smart_input{32};
	PF_SmartRenderCallbacks callbacks{checkout_pixels, checkout_output};
	PF_SmartRenderExtra extra{&smart_input, &callbacks};
	if (SmartRender(&in, &out, &extra) != PF_Err_NONE) return 2;
	PF_ParamDef *params[DG_NUM_PARAMS]; params[0] = &g_params[0]; g_params[0].u.ld = input;
	for (int index = 1; index < DG_NUM_PARAMS; ++index) params[index] = &g_params[index];
	if (RenderBits<PF_PixelFloat>(&in, params, &input, &direct, true) != PF_Err_NONE) return 3;
	if (std::memcmp(smart_bytes.data(), direct_bytes.data(), smart_bytes.size()) != 0) return 4;
	bool nonzero = false;
	for (std::uint8_t byte : smart_bytes) nonzero |= byte != 0;
	if (!nonzero) return 5;
	smart_input.bitdepth = 24;
	if (SmartRender(&in, &out, &extra) != PF_Err_BAD_CALLBACK_PARAM) return 6;
	std::puts("PASS_OLMDISTANCEGRADATION_MAC_PF32_SMART_OWNER");
	return 0;
}

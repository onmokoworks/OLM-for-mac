#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

static constexpr int W = 17, H = 11;
static PF_EffectWorld *g_input = nullptr, *g_output = nullptr;
static std::array<PF_ParamDef, DG_NUM_PARAMS> g_params{};

static PF_Err checkout_pixels(PF_ProgPtr, A_long index, PF_EffectWorld **world) {
	if (index != DG_INPUT || !world) return PF_Err_BAD_CALLBACK_PARAM;
	*world = g_input;
	return PF_Err_NONE;
}

static PF_Err checkout_output(PF_ProgPtr, PF_EffectWorld **world) {
	if (!world) return PF_Err_BAD_CALLBACK_PARAM;
	*world = g_output;
	return PF_Err_NONE;
}

static PF_Err checkout_param(A_long index, PF_ParamDef *param) {
	if (index <= 0 || index >= DG_NUM_PARAMS || !param) return PF_Err_BAD_CALLBACK_PARAM;
	*param = g_params[index];
	return PF_Err_NONE;
}

template <typename Pixel>
static void fill_source(std::vector<std::uint8_t> &bytes, int rowbytes) {
	for (int y = 0; y < H; ++y) {
		for (int x = 0; x < W; ++x) {
			Pixel *pixel = reinterpret_cast<Pixel *>(bytes.data() + y * rowbytes) + x;
			const bool transparent = x >= 4 && x < 13 && y >= 2 && y < 9;
			if constexpr (sizeof(Pixel) == sizeof(PF_Pixel8)) {
				pixel->alpha = transparent ? 0 : 255;
				pixel->red = (x * 613 + y * 1231) % 256;
				pixel->green = (x * 997 + y * 211) % 256;
				pixel->blue = (x * 1499 + y * 307) % 256;
			} else {
				pixel->alpha = transparent ? 0 : 32768;
				pixel->red = (x * 613 + y * 1231) % 32769;
				pixel->green = (x * 997 + y * 211) % 32769;
				pixel->blue = (x * 1499 + y * 307) % 32769;
			}
		}
	}
}

template <typename Pixel>
static int run_case(short depth, A_long interpolation, A_long blur, bool background) {
	const int rowbytes = W * (int)sizeof(Pixel) + 16;
	std::vector<std::uint8_t> input_bytes((size_t)rowbytes * H, 0xa5);
	std::vector<std::uint8_t> smart_bytes((size_t)rowbytes * H, 0x5a);
	std::vector<std::uint8_t> direct_bytes((size_t)rowbytes * H, 0x5a);
	fill_source<Pixel>(input_bytes, rowbytes);
	const std::vector<std::uint8_t> input_before = input_bytes;

	PF_EffectWorld input{input_bytes.data(), W, H, rowbytes, depth, {0, 0, W, H}};
	PF_EffectWorld smart{smart_bytes.data(), W, H, rowbytes, depth, {0, 0, W, H}};
	PF_EffectWorld direct{direct_bytes.data(), W, H, rowbytes, depth, {0, 0, W, H}};
	g_input = &input;
	g_output = &smart;
	dg_harness_checkout_param = checkout_param;
	g_params = {};
	g_params[DG_INVERT].u.bd.value = 1;
	g_params[DG_IN_OUT].u.pd.value = IN_OUT_INSIDE;
	g_params[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	g_params[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	g_params[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
	g_params[DG_USE_BG_COLOR].u.bd.value = background;
	g_params[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
	g_params[DG_BG_COLOR].u.cd.value = {255, 16, 160, 48};
	g_params[DG_INTERP_MODE].u.pd.value = interpolation;
	g_params[DG_POWER].u.fs_d.value = 2.25;
	g_params[DG_BLUR_MODE].u.pd.value = blur;
	g_params[DG_BLUR_SIZE].u.sd.value = 1;

	PF_InData in{};
	in.downsample_x = {1, 1};
	in.downsample_y = {1, 1};
	PF_OutData out{};
	PF_SmartRenderInput smart_input{depth};
	PF_SmartRenderCallbacks callbacks{checkout_pixels, checkout_output};
	PF_SmartRenderExtra extra{&smart_input, &callbacks};
	if (SmartRender(&in, &out, &extra) != PF_Err_NONE) return 10 + depth;

	PF_ParamDef *params[DG_NUM_PARAMS];
	g_params[DG_INPUT].u.ld = input;
	for (int index = 0; index < DG_NUM_PARAMS; ++index) params[index] = &g_params[index];
	if (RenderBits<Pixel>(&in, params, &input, &direct, true) != PF_Err_NONE) return 20 + depth;
	if (input_bytes != input_before || smart_bytes != direct_bytes) return 30 + depth;
	return 0;
}

int main() {
	for (A_long interpolation : {INTERP_SPHERE, INTERP_POWER}) {
		for (A_long blur : {BLUR_MODE_NO_SCALE, BLUR_MODE_MEDIAN}) {
			const bool background = blur == BLUR_MODE_MEDIAN;
			if (int err = run_case<PF_Pixel8>(8, interpolation, blur, background)) return err;
			if (int err = run_case<PF_Pixel16>(16, interpolation, blur, background)) return err;
		}
	}
	std::puts("PASS_OLMDISTANCEGRADATION_MAC_PF8_PF16_SMART_FULL_OWNER");
	return 0;
}

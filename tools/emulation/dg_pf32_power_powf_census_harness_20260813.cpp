#include "dg_renderbits_real_harness_20260716_sdk_shim.h"

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

struct PowfCall {
	int blur_mode;
	int use_background;
	int pixel_index;
	std::uint32_t input_bits;
	std::uint32_t exponent_bits;
	std::uint32_t host_result_bits;
};

static std::vector<PowfCall> g_powf_calls;
static int g_blur_mode = 0;
static int g_use_background = 0;
static int g_pixel_index = 0;

static std::uint32_t FloatBits(float value) {
	std::uint32_t bits = 0;
	std::memcpy(&bits, &value, sizeof(bits));
	return bits;
}

static float CapturePowf(float input, float exponent) {
	// __builtin_powf bypasses the macro below while retaining the host's actual
	// float pow leaf.  The host result is diagnostic only; the request package
	// produced from this census requires native Windows ucrtbase.dll!powf.
	const float result = __builtin_powf(input, exponent);
	g_powf_calls.push_back(PowfCall{
		g_blur_mode,
		g_use_background,
		g_pixel_index++,
		FloatBits(input),
		FloatBits(exponent),
		FloatBits(result),
	});
	return result;
}

#define powf CapturePowf
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#undef powf

static PF_PixelFloat FixturePixel(int x, int y) {
	const bool transparent = x >= 4 && x < 13 && y >= 2 && y < 9;
	const int red = (x * 613 + y * 1231) % 256;
	const int green = (x * 997 + y * 211) % 256;
	const int blue = (x * 1499 + y * 307) % 256;
	return PF_PixelFloat{
		transparent ? 0.0f : 1.0f,
		static_cast<float>(red) / 255.0f,
		static_cast<float>(green) / 255.0f,
		static_cast<float>(blue) / 255.0f,
	};
}

static void InitializeParams(std::array<PF_ParamDef, DG_NUM_PARAMS> &storage,
		std::array<PF_ParamDef *, DG_NUM_PARAMS> &params, const PF_LayerDef &input,
		int blur_mode, int use_background) {
	for (int index = 0; index < DG_NUM_PARAMS; ++index) {
		params[index] = &storage[index];
	}
	storage[DG_INPUT].u.ld = input;
	storage[DG_INVERT].u.bd.value = 1;
	storage[DG_IN_OUT].u.pd.value = IN_OUT_INSIDE;
	storage[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
	storage[DG_USE_BG_COLOR].u.bd.value = use_background;
	storage[DG_GRAD_COLOR].u.cd.value = PF_Pixel8{255, 28, 0, 238};
	storage[DG_BG_COLOR].u.cd.value = PF_Pixel8{255, 16, 160, 48};
	storage[DG_INTERP_MODE].u.pd.value = INTERP_POWER;
	storage[DG_POWER].u.fs_d.value = 2.25;
	storage[DG_BLUR_MODE].u.pd.value = blur_mode;
	storage[DG_BLUR_SIZE].u.sd.value = 1;
}

static int RenderCell(const std::string &output_directory, int blur_mode,
		int use_background) {
	constexpr int width = 17;
	constexpr int height = 11;
	std::vector<PF_PixelFloat> source(width * height);
	std::vector<PF_PixelFloat> output(width * height);
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			source[static_cast<std::size_t>(y) * width + x] = FixturePixel(x, y);
		}
	}
	PF_LayerDef input{source.data(), width, height,
		width * static_cast<A_long>(sizeof(PF_PixelFloat)), 32,
		{0, 0, width, height}};
	std::array<PF_ParamDef, DG_NUM_PARAMS> storage{};
	std::array<PF_ParamDef *, DG_NUM_PARAMS> params{};
	InitializeParams(storage, params, input, blur_mode, use_background);
	PF_InData in_data{};
	in_data.downsample_x = {1, 1};
	in_data.downsample_y = {1, 1};
	DGParams settings;
	AEFX_CLR_STRUCT(settings);
	PF_Err err = FetchParams(&in_data, params.data(), &settings);
	if (err != PF_Err_NONE) return 10;
	settings.w = width;
	settings.h = height;
	settings.pixel_size = sizeof(PF_PixelFloat);
	settings.smart_owner = true;
	settings.pf32_smart_matrix_admitted = true;

	std::vector<float> alpha(width * height);
	for (int index = 0; index < width * height; ++index) {
		alpha[index] = source[index].alpha;
	}
	DistanceField field;
	build_distance_field(alpha.data(), field, settings, width, height);
	const bool blurred = settings.blur_mode != BLUR_MODE_NONE && settings.blur_size > 0;
	const float *auxiliary = !field.pre_blur_x.empty() ? field.pre_blur_x.data()
		: (blurred ? field.x.data() : field.d_alpha.data());

	g_blur_mode = blur_mode;
	g_use_background = use_background;
	g_pixel_index = 0;
	const std::size_t call_start = g_powf_calls.size();
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			const int index = y * width + x;
			const PF_PixelFloat &pixel = source[index];
			PF_PixelFloat &result = output[index];
			compose_pixel(pixel.alpha, pixel.red, pixel.green, pixel.blue,
				auxiliary[index], field.x[index], settings,
				result.alpha, result.red, result.green, result.blue);
		}
	}
	if (g_powf_calls.size() - call_start != static_cast<std::size_t>(width * height)) {
		return 11;
	}
	const std::string path = output_directory + "/power.mode" +
		std::to_string(blur_mode) + ".bg" + std::to_string(use_background) + ".raw";
	std::ofstream stream(path, std::ios::binary);
	stream.write(reinterpret_cast<const char *>(output.data()),
		static_cast<std::streamsize>(output.size() * sizeof(PF_PixelFloat)));
	return stream ? 0 : 12;
}

int main(int argc, char **argv) {
	if (argc != 2) return 2;
	for (int blur_mode = 2; blur_mode <= 5; ++blur_mode) {
		for (int use_background = 0; use_background <= 1; ++use_background) {
			const int result = RenderCell(argv[1], blur_mode, use_background);
			if (result != 0) return result;
		}
	}
	std::puts("blur_mode,use_background,pixel_index,input_bits,exponent_bits,host_result_bits");
	for (const PowfCall &call : g_powf_calls) {
		std::printf("%d,%d,%d,%08x,%08x,%08x\n", call.blur_mode,
			call.use_background, call.pixel_index, call.input_bits,
			call.exponent_bits, call.host_result_bits);
	}
	return g_powf_calls.size() == 8u * 17u * 11u ? 0 : 13;
}

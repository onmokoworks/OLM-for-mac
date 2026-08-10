#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

static std::vector<std::uint8_t> read_all(const char *path)
{
	std::ifstream stream(path, std::ios::binary);
	return {std::istreambuf_iterator<char>(stream), {}};
}

int main(int argc, char **argv)
{
	if (argc != 4) return 2;
	auto source = read_all(argv[1]);
	auto expected = read_all(argv[2]);
	const std::string name(argv[3]);
	constexpr int width = 17, height = 11, input_rowbytes = 146, output_rowbytes = 150;
	if (source.size() != input_rowbytes * height || expected.size() != output_rowbytes * height) return 3;

	A_long in_out, render_mode, interp_mode;
	float power = 1.0f;
	if (name == "inside_rgb_sphere") {
		in_out = IN_OUT_INSIDE; render_mode = RENDER_MODE_RGB; interp_mode = INTERP_SPHERE;
	} else if (name == "outside_layer_power") {
		in_out = IN_OUT_OUTSIDE; render_mode = RENDER_MODE_LAYER; interp_mode = INTERP_POWER; power = 2.5f;
	} else if (name == "both_rgb_linear") {
		in_out = IN_OUT_BOTH; render_mode = RENDER_MODE_RGB; interp_mode = INTERP_LINEAR;
	} else if (name == "both_layer_constant") {
		in_out = IN_OUT_BOTH; render_mode = RENDER_MODE_LAYER; interp_mode = INTERP_CONSTANT;
	} else return 4;

	std::vector<std::uint8_t> output(output_rowbytes * height, 0xa5);
	PF_LayerDef input_world{source.data(), width, height, input_rowbytes, 16, {0, 0, width, height}};
	PF_LayerDef output_world{output.data(), width, height, output_rowbytes, 16, {0, 0, width, height}};
	std::array<PF_ParamDef, DG_NUM_PARAMS> storage{};
	PF_ParamDef *params[DG_NUM_PARAMS];
	for (int i = 0; i < DG_NUM_PARAMS; ++i) params[i] = &storage[i];
	storage[DG_INPUT].u.ld = input_world;
	storage[DG_INVERT].u.bd.value = 1;
	storage[DG_IN_OUT].u.pd.value = in_out;
	storage[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_RENDER_MODE].u.pd.value = render_mode;
	storage[DG_USE_BG_COLOR].u.bd.value = 1;
	storage[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
	storage[DG_BG_COLOR].u.cd.value = {255, 16, 160, 48};
	storage[DG_INTERP_MODE].u.pd.value = interp_mode;
	storage[DG_POWER].u.fs_d.value = power;
	storage[DG_BLUR_MODE].u.pd.value = BLUR_MODE_NONE;
	PF_InData in_data{};
	in_data.downsample_x = {1, 1};
	in_data.downsample_y = {1, 1};
	if (RenderBits<PF_Pixel16>(&in_data, params, &input_world, &output_world) != PF_Err_NONE) return 5;
	size_t mismatches = 0;
	for (size_t i = 0; i < output.size(); ++i) mismatches += output[i] != expected[i];
	if (mismatches) {
		std::fprintf(stderr, "mismatched bytes=%zu case=%s\n", mismatches, name.c_str());
		for (size_t i = 0, shown = 0; i < output.size() && shown < 16; ++i) if (output[i] != expected[i]) {
			std::fprintf(stderr, "bad %zu got %u expected %u\n", i, (unsigned)output[i], (unsigned)expected[i]);
			++shown;
		}
		return 1;
	}
	std::printf("PASS case=%s bytes=%zu mismatches=0 rowbytes=%d/%d\n",
	            name.c_str(), output.size(), input_rowbytes, output_rowbytes);
	return 0;
}

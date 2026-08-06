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
	if (argc != 5) return 2;
	const std::string interpolation(argv[3]);
	const bool invert = std::strcmp(argv[4], "invert") == 0;
	A_long interpolation_mode = 0;
	float power = 1.0f;
	if (interpolation == "constant") interpolation_mode = INTERP_CONSTANT;
	else if (interpolation == "linear") interpolation_mode = INTERP_LINEAR;
	else if (interpolation == "sphere") interpolation_mode = INTERP_SPHERE;
	else if (interpolation == "power") {
		interpolation_mode = INTERP_POWER;
		power = 2.5f;
	} else return 3;

	auto source = read_all(argv[1]);
	auto expected = read_all(argv[2]);
	constexpr int width = 17, height = 11, input_rowbytes = 146, output_rowbytes = 150;
	if (source.size() != input_rowbytes * height || expected.size() != output_rowbytes * height) return 4;
	std::vector<std::uint8_t> output(output_rowbytes * height, 0xa5);
	PF_LayerDef input_world{source.data(), width, height, input_rowbytes, 16, {0, 0, width, height}};
	PF_LayerDef output_world{output.data(), width, height, output_rowbytes, 16, {0, 0, width, height}};
	std::array<PF_ParamDef, DG_NUM_PARAMS> storage{};
	PF_ParamDef *params[DG_NUM_PARAMS];
	for (int i = 0; i < DG_NUM_PARAMS; ++i) params[i] = &storage[i];
	storage[DG_INPUT].u.ld = input_world;
	storage[DG_INVERT].u.bd.value = invert ? 1 : 0;
	storage[DG_IN_OUT].u.pd.value = IN_OUT_OUTSIDE;
	storage[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
	storage[DG_USE_BG_COLOR].u.bd.value = 0;
	storage[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
	storage[DG_BG_COLOR].u.cd.value = {255, 255, 0, 0};
	storage[DG_INTERP_MODE].u.pd.value = interpolation_mode;
	storage[DG_POWER].u.fs_d.value = power;
	storage[DG_BLUR_MODE].u.pd.value = BLUR_MODE_NONE;
	PF_InData in_data{};
	in_data.downsample_x = {1, 1};
	in_data.downsample_y = {1, 1};
	if (RenderBits<PF_Pixel16>(&in_data, params, &input_world, &output_world) != PF_Err_NONE) return 5;
	size_t mismatches = 0;
	for (size_t i = 0; i < output.size(); ++i) mismatches += output[i] != expected[i];
	if (mismatches) {
		std::fprintf(stderr, "mismatched bytes=%zu interpolation=%s invert=%d\n",
		             mismatches, interpolation.c_str(), invert ? 1 : 0);
		for (size_t i = 0, shown = 0; i < output.size() && shown < 12; ++i) {
			if (output[i] != expected[i]) {
				std::fprintf(stderr, "bad %zu got %u expected %u\n", i,
				             (unsigned)output[i], (unsigned)expected[i]);
				++shown;
			}
		}
		return 1;
	}
	std::printf("PASS interpolation=%s invert=%d bytes=%zu mismatches=0 rowbytes=%d/%d\n",
	            interpolation.c_str(), invert ? 1 : 0, output.size(), input_rowbytes, output_rowbytes);
	return 0;
}

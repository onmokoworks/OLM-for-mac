#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

static std::vector<std::uint8_t> read_all(const char *path) {
	std::ifstream stream(path, std::ios::binary);
	return {std::istreambuf_iterator<char>(stream), {}};
}

int main(int argc, char **argv) {
	if (argc != 6) return 2;
	auto source = read_all(argv[1]);
	auto expected = read_all(argv[2]);
	const std::string interp(argv[3]);
	const bool background = std::atoi(argv[4]) != 0;
	const int blur = std::atoi(argv[5]);
	constexpr int w = 17, h = 11, input_rowbytes = 75, output_rowbytes = 79;
	if (source.size() != input_rowbytes * h || expected.size() != output_rowbytes * h ||
	    (interp != "constant" && interp != "linear") || blur < 2 || blur > 5) return 3;

	std::vector<std::uint8_t> output(output_rowbytes * h, 0xa5);
	PF_LayerDef input{source.data(), w, h, input_rowbytes, 8, {0, 0, w, h}};
	PF_LayerDef result{output.data(), w, h, output_rowbytes, 8, {0, 0, w, h}};
	std::array<PF_ParamDef, DG_NUM_PARAMS> storage{};
	PF_ParamDef *params[DG_NUM_PARAMS];
	for (int i = 0; i < DG_NUM_PARAMS; ++i) params[i] = &storage[i];
	storage[DG_INPUT].u.ld = input;
	storage[DG_INVERT].u.bd.value = 1;
	storage[DG_IN_OUT].u.pd.value = IN_OUT_INSIDE;
	storage[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
	storage[DG_USE_BG_COLOR].u.bd.value = background;
	storage[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
	storage[DG_BG_COLOR].u.cd.value = {255, 16, 160, 48};
	storage[DG_INTERP_MODE].u.pd.value = interp == "constant" ? INTERP_CONSTANT : INTERP_LINEAR;
	storage[DG_POWER].u.fs_d.value = 1.0;
	storage[DG_BLUR_MODE].u.pd.value = blur;
	storage[DG_BLUR_SIZE].u.sd.value = 1;
	PF_InData in_data{};
	in_data.downsample_x = {1, 1};
	in_data.downsample_y = {1, 1};
	if (RenderBits<PF_Pixel8>(&in_data, params, &input, &result) != PF_Err_NONE) return 4;

	size_t mismatches = 0;
	for (size_t i = 0; i < output.size(); ++i) mismatches += output[i] != expected[i];
	if (mismatches) {
		std::fprintf(stderr, "mismatched bytes=%zu interp=%s background=%d blur=%d\n",
		             mismatches, interp.c_str(), background ? 1 : 0, blur);
		for (size_t i = 0, shown = 0; i < output.size() && shown < 16; ++i) {
			if (output[i] != expected[i]) {
				std::fprintf(stderr, "bad %zu got %u expected %u\n", i,
				             (unsigned)output[i], (unsigned)expected[i]);
				++shown;
			}
		}
		return 1;
	}
	std::printf("PASS interp=%s background=%d blur=%d bytes=%zu mismatches=0\n",
	            interp.c_str(), background ? 1 : 0, blur, output.size());
	return 0;
}

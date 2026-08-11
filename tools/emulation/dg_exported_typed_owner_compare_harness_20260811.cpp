#include "dg_renderbits_real_harness_20260716_sdk_shim.h"
#include "../../mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

static std::vector<std::uint8_t> read_all(const char *path) {
	std::ifstream stream(path, std::ios::binary);
	return {std::istreambuf_iterator<char>(stream), {}};
}

template <typename Pixel>
static int render(const std::vector<std::uint8_t> &source, const char *output_path,
		const std::string &interp, bool background, int blur) {
	constexpr int width = 17, height = 11;
	const int rowbytes = width * static_cast<int>(sizeof(Pixel));
	if (source.size() != static_cast<std::size_t>(rowbytes * height)) return 3;
	std::vector<std::uint8_t> output(source.size());
	PF_LayerDef input{const_cast<std::uint8_t *>(source.data()), width, height, rowbytes,
		static_cast<int>(sizeof(Pixel) == 8 ? 16 : 32), {0, 0, width, height}};
	PF_LayerDef destination{output.data(), width, height, rowbytes,
		static_cast<int>(sizeof(Pixel) == 8 ? 16 : 32), {0, 0, width, height}};
	std::array<PF_ParamDef, DG_NUM_PARAMS> storage{};
	PF_ParamDef *params[DG_NUM_PARAMS];
	for (int index = 0; index < DG_NUM_PARAMS; ++index) params[index] = &storage[index];
	storage[DG_INPUT].u.ld = input;
	storage[DG_INVERT].u.bd.value = 1;
	storage[DG_IN_OUT].u.pd.value = IN_OUT_INSIDE;
	storage[DG_INSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_OUTSIDE_THRESHOLD].u.sd.value = 4;
	storage[DG_RENDER_MODE].u.pd.value = RENDER_MODE_RGB;
	storage[DG_USE_BG_COLOR].u.bd.value = background;
	storage[DG_GRAD_COLOR].u.cd.value = {255, 28, 0, 238};
	storage[DG_BG_COLOR].u.cd.value = {255, 16, 160, 48};
	storage[DG_INTERP_MODE].u.pd.value = interp == "constant" ? INTERP_CONSTANT
		: interp == "linear" ? INTERP_LINEAR
		: interp == "sphere" ? INTERP_SPHERE : INTERP_POWER;
	storage[DG_POWER].u.fs_d.value = 2.25;
	storage[DG_BLUR_MODE].u.pd.value = blur;
	storage[DG_BLUR_SIZE].u.sd.value = 1;
	PF_InData in_data{};
	in_data.downsample_x = {1, 1};
	in_data.downsample_y = {1, 1};
	if (RenderBits<Pixel>(&in_data, params, &input, &destination, true) != 0) return 4;
	std::ofstream stream(output_path, std::ios::binary);
	stream.write(reinterpret_cast<const char *>(output.data()), static_cast<std::streamsize>(output.size()));
	return stream ? 0 : 5;
}

int main(int argc, char **argv) {
	if (argc != 7) return 2;
	auto source = read_all(argv[2]);
	const std::string depth(argv[1]), interp(argv[4]);
	const bool background = std::atoi(argv[5]) != 0;
	const int blur = std::atoi(argv[6]);
	if (interp != "constant" && interp != "linear" && interp != "sphere" && interp != "power") return 3;
	if (blur < 2 || blur > 5) return 3;
	if (depth == "PF16") return render<PF_Pixel16>(source, argv[3], interp, background, blur);
	if (depth == "PF32") return render<PF_PixelFloat>(source, argv[3], interp, background, blur);
	return 3;
}

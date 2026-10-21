#include "olm_sha256_rows.h"

#define OLM_RADIALBLUR_TEST_SEAM 1
#ifndef OLM_RADIAL_SOURCE_INCLUDE
#define OLM_RADIAL_SOURCE_INCLUDE "../../mac/OLMRadialBlur/OLMRadialBlur.cpp"
#endif
#include OLM_RADIAL_SOURCE_INCLUDE

#include <array>
#include <cstdio>
#include <cstring>
#include <vector>

struct Controls {
	double noise_variation;
	int seed;
	double offset;
	double thickness;
};

static const std::array<Controls, 4> kControls{{
	{25.0, 1, 0.0, 3.0}, {25.0, 2, 1.0, 10.0},
	{100.0, 1, 1.0, 3.0}, {100.0, 2, 0.0, 10.0},
}};

template <typename PixelT>
static void Fill(std::vector<unsigned char> &storage, int width, int height, int rowbytes)
{
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			PixelT *pixel = reinterpret_cast<PixelT *>(storage.data() + y * rowbytes) + x;
			if constexpr (sizeof(PixelT) == sizeof(PF_Pixel8)) {
				*pixel = {
					(A_u_char)((x + y) % 5 ? 255 : 127),
					(A_u_char)((x * 31 + y * 7) % 256),
					(A_u_char)((x * 11 + y * 29) % 256),
					(A_u_char)((x * 47 + y * 13) % 256),
				};
			} else {
				*pixel = {
					(A_u_short)((x + y) % 5 ? 32768 : 16384),
					(A_u_short)((x * 4093 + y * 257) % 32769),
					(A_u_short)((x * 1237 + y * 3559) % 32769),
					(A_u_short)((x * 7919 + y * 911) % 32769),
				};
			}
		}
		std::fill(storage.begin() + y * rowbytes + width * sizeof(PixelT),
		          storage.begin() + (y + 1) * rowbytes, (unsigned char)(0xa0 + y));
	}
}

static std::string ActiveDigest(
	const std::vector<unsigned char> &storage, int rowbytes, int active, int height)
{
	olm::Sha256 hash;
	for (int y = 0; y < height; ++y) hash.update(storage.data() + y * rowbytes, active);
	unsigned char digest[32]; hash.final(digest);
	char text[65];
	for (int i = 0; i < 32; ++i) std::snprintf(text + i * 2, 3, "%02x", digest[i]);
	text[64] = 0;
	return text;
}

template <typename PixelT>
static int RunDepth(int depth, int width, int height)
{
	const int pad = depth == 8 ? 8 : 16;
	const int active = width * (int)sizeof(PixelT);
	const int rowbytes = active + pad;
	std::vector<unsigned char> canonical((size_t)rowbytes * height);
	Fill<PixelT>(canonical, width, height, rowbytes);
	for (size_t control = 0; control < kControls.size(); ++control) {
		auto input = canonical;
		std::vector<unsigned char> output((size_t)rowbytes * height, 0xee);
		PF_EffectWorld iw{}, ow{};
		iw.data = reinterpret_cast<PF_PixelPtr>(input.data()); iw.rowbytes = rowbytes;
		iw.width = width; iw.height = height;
		ow = iw; ow.data = reinterpret_cast<PF_PixelPtr>(output.data());
		OLMRadialBlurInfo info{};
		info.blur_type = 2; info.center_x = depth == 8 ? width / 2.0 : width / 2;
		info.center_y = depth == 8 ? height / 2.0 : height / 2;
		info.outer_strength = 4; info.outer_offset_mode = 1;
		info.inner_offset_mode = 1; info.repeat_border = TRUE;
		info.ratio = 1; info.quality = 5; info.brightness_gain = 1;
		info.noise_variation = kControls[control].noise_variation;
		info.noise_type = 1; info.seed = kControls[control].seed;
		info.noise_offset = kControls[control].offset;
		info.thickness = kControls[control].thickness;
		info.comp_width = width; info.comp_height = height;
		const auto before = input;
		const PF_Err error = OLMRadialBlurTestRenderWorld(&iw, &ow, &info, depth);
		if (error != PF_Err_NONE || input != before) return 10 + depth + (int)control;
		for (int y = 0; y < height; ++y)
			for (int x = active; x < rowbytes; ++x)
				if (output[(size_t)y * rowbytes + x] != 0xee) return 20 + depth;
		std::printf("POS PF%d %dx%d c%zu %s\n", depth, width, height, control,
		            ActiveDigest(output, rowbytes, active, height).c_str());
	}
	#ifndef OLM_RADIAL_SKIP_MUTATION_CHECKS
	for (int mutation = 0; mutation < 3; ++mutation) {
		auto input = canonical;
		const size_t offset = mutation == 0 ? 0 : mutation == 1
			? (size_t)(height / 2) * rowbytes + active / 2
			: (size_t)(height - 1) * rowbytes + active - 1;
		input[offset] ^= 1;
		const auto before = input;
		std::vector<unsigned char> output((size_t)rowbytes * height, 0xee);
		PF_EffectWorld iw{}, ow{};
		iw.data = reinterpret_cast<PF_PixelPtr>(input.data()); iw.rowbytes = rowbytes;
		iw.width = width; iw.height = height;
		ow = iw; ow.data = reinterpret_cast<PF_PixelPtr>(output.data());
		OLMRadialBlurInfo info{};
		info.blur_type = 2; info.center_x = depth == 8 ? width / 2.0 : width / 2;
		info.center_y = depth == 8 ? height / 2.0 : height / 2;
		info.outer_strength = 4; info.outer_offset_mode = 1;
		info.inner_offset_mode = 1; info.repeat_border = TRUE;
		info.ratio = 1; info.quality = 5; info.brightness_gain = 1;
		info.noise_variation = 25; info.noise_type = 1; info.seed = 1;
		info.noise_offset = 0; info.thickness = 3;
		info.comp_width = width; info.comp_height = height;
		const PF_Err error = OLMRadialBlurTestRenderWorld(&iw, &ow, &info, depth);
		if (error != PF_Err_BAD_CALLBACK_PARAM || input != before ||
		    !std::all_of(output.begin(), output.end(), [](unsigned char v) { return v == 0xee; }))
			return 100 + depth + mutation;
		std::printf("NEG PF%d %dx%d m%d reject\n", depth, width, height, mutation);
	}
	#endif
	return 0;
}

int main()
{
	for (auto geometry : {std::pair<int, int>{9, 7}, {32, 18}}) {
		int error = RunDepth<PF_Pixel8>(8, geometry.first, geometry.second);
		if (error) return error;
		error = RunDepth<PF_Pixel16>(16, geometry.first, geometry.second);
		if (error) return error;
	}
	return 0;
}

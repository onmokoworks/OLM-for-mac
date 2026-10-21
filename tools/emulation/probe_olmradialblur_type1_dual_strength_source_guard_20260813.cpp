#include "olm_sha256_rows.h"

#define OLM_RADIALBLUR_TEST_SEAM 1
#ifndef OLM_RADIAL_SOURCE_INCLUDE
#define OLM_RADIAL_SOURCE_INCLUDE "../../mac/OLMRadialBlur/OLMRadialBlur.cpp"
#endif
#include OLM_RADIAL_SOURCE_INCLUDE

#include <algorithm>
#include <array>
#include <cstdio>
#include <cstring>
#include <vector>

template <typename PixelT>
static void Fill(std::vector<unsigned char> &raw, int rowbytes, bool component)
{
	constexpr int width = 32, height = 18;
	for (int y = 0; y < height; ++y) {
		for (int x = 0; x < width; ++x) {
			const bool live = !component ||
				(x >= 2 && x <= 4 && y >= 2 && y <= 4) ||
				(x >= 13 && x <= 14 && y >= 9 && y <= 10) || (x == 27 && y == 14);
			PixelT value{};
			if (live) {
				if constexpr (std::is_same<PixelT, PF_Pixel8>::value) value = {
					(A_u_char)(component ? 255 : ((x + y) % 5 ? 255 : 127)),
					(A_u_char)((x * 31 + y * 7) % 256),
					(A_u_char)((x * 11 + y * 29) % 256),
					(A_u_char)((x * 47 + y * 13) % 256)};
				else if constexpr (std::is_same<PixelT, PF_Pixel16>::value) value = {
					(A_u_short)(component ? 32768 : ((x + y) % 5 ? 32768 : 16384)),
					(A_u_short)((x * 4093 + y * 257) % 32769),
					(A_u_short)((x * 1237 + y * 3559) % 32769),
					(A_u_short)((x * 7919 + y * 911) % 32769)};
				else value = {
					component ? 1.0f : ((x + y) % 5 ? 1.0f : 0.5f),
					(float)(((x * 4093 + y * 257) % 32769) / 32768.0),
					(float)(((x * 1237 + y * 3559) % 32769) / 32768.0),
					(float)(((x * 7919 + y * 911) % 32769) / 32768.0)};
			}
			std::memcpy(raw.data() + (size_t)y * rowbytes + (size_t)x * sizeof(PixelT),
			            &value, sizeof(value));
		}
		std::fill(raw.begin() + (size_t)y * rowbytes + width * sizeof(PixelT),
		          raw.begin() + (size_t)(y + 1) * rowbytes, (unsigned char)(0xa0 + y));
	}
}

static std::string ActiveDigest(const std::vector<unsigned char> &raw, int rb, int active)
{
	olm::Sha256 hash;
	for (int y = 0; y < 18; ++y) hash.update(raw.data() + (size_t)y * rb, active);
	unsigned char digest[32]; hash.final(digest); char text[65];
	for (int i = 0; i < 32; ++i) std::snprintf(text + i * 2, 3, "%02x", digest[i]);
	text[64] = 0; return text;
}

template <typename PixelT>
static OLMRadialBlurInfo Info(int depth, int inner, bool component, double noise)
{
	OLMRadialBlurInfo info{}; info.blur_type = 2; info.center_x = depth == 8 ? 16.0 : 16;
	info.center_y = depth == 8 ? 9.0 : 9; info.outer_strength = 4;
	info.outer_offset_mode = 1; info.inner_strength = inner; info.inner_offset_mode = 1;
	info.repeat_border = TRUE; info.ratio = 1; info.quality = 5; info.brightness_gain = 1;
	info.size_variation = component ? 25 : 0; info.noise_variation = noise;
	info.noise_type = 1; info.seed = 1; info.thickness = 10;
	info.comp_width = 32; info.comp_height = 18; return info;
}

template <typename PixelT>
static int RunDepth(int depth)
{
	const int active = 32 * (int)sizeof(PixelT), rb = active + (depth == 8 ? 8 : 16);
	for (bool component : {false, true}) {
		std::vector<unsigned char> canonical((size_t)rb * 18); Fill<PixelT>(canonical, rb, component);
		const std::array<double, 2> noises{{25, 100}};
		for (int inner : {2, 4}) for (double noise : noises) {
			if (component && noise == 100) continue;
			auto input = canonical, before = canonical;
			std::vector<unsigned char> output((size_t)rb * 18, 0xee);
			PF_EffectWorld iw{}, ow{}; iw.data = (PF_PixelPtr)input.data(); iw.rowbytes = rb;
			iw.width = 32; iw.height = 18; ow = iw; ow.data = (PF_PixelPtr)output.data();
			auto info = Info<PixelT>(depth, inner, component, noise);
			const PF_Err err = OLMRadialBlurTestRenderWorld(&iw, &ow, &info, depth);
			if (err || input != before) return 10 + depth;
			for (int y = 0; y < 18; ++y) for (int x = active; x < rb; ++x)
				if (output[(size_t)y * rb + x] != 0xee) return 20 + depth;
			std::printf("POS PF%d %s i%d nv%.0f %s\n", depth,
			            component ? "component" : "plain", inner, noise,
			            ActiveDigest(output, rb, active).c_str());
		}
	#ifndef OLM_RADIAL_SKIP_MUTATION_CHECKS
		for (int mutation = 0; mutation < 3; ++mutation) {
			auto input = canonical, before = canonical;
			const size_t offset = mutation == 0 ? 0 : mutation == 1
				? (size_t)9 * rb + active / 2 : (size_t)17 * rb + active - 1;
			input[offset] ^= 1; before = input;
			std::vector<unsigned char> output((size_t)rb * 18, 0xee);
			PF_EffectWorld iw{}, ow{}; iw.data = (PF_PixelPtr)input.data(); iw.rowbytes = rb;
			iw.width = 32; iw.height = 18; ow = iw; ow.data = (PF_PixelPtr)output.data();
			auto info = Info<PixelT>(depth, 2, component, 25);
			const PF_Err err = OLMRadialBlurTestRenderWorld(&iw, &ow, &info, depth);
			if (err != PF_Err_BAD_CALLBACK_PARAM || input != before ||
			    !std::all_of(output.begin(), output.end(), [](unsigned char v){ return v == 0xee; }))
				return 100 + depth + mutation;
			std::printf("NEG PF%d %s m%d reject\n", depth,
			            component ? "component" : "plain", mutation);
		}
	#endif
	}
	return 0;
}

int main()
{
	if (int e = RunDepth<PF_Pixel8>(8)) return e;
	if (int e = RunDepth<PF_Pixel16>(16)) return e;
	return RunDepth<PF_PixelFloat>(32);
}

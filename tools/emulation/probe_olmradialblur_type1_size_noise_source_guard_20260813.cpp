#include "olm_sha256_rows.h"
#define OLM_RADIALBLUR_TEST_SEAM 1
#ifndef OLM_RADIAL_SOURCE_INCLUDE
#define OLM_RADIAL_SOURCE_INCLUDE "../../mac/OLMRadialBlur/OLMRadialBlur.cpp"
#endif
#include OLM_RADIAL_SOURCE_INCLUDE
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <vector>

template <typename P> static void Fill(std::vector<unsigned char>& raw, int rb)
{
	for (int y = 0; y < 18; ++y) {
		for (int x = 0; x < 32; ++x) {
			const bool live = (x >= 2 && x <= 4 && y >= 2 && y <= 4) ||
				(x >= 13 && x <= 14 && y >= 9 && y <= 10) || (x == 27 && y == 14);
			P p{};
			if (live) {
				if constexpr (std::is_same<P, PF_Pixel8>::value) p = {255,
					(A_u_char)((x * 31 + y * 7) % 256), (A_u_char)((x * 11 + y * 29) % 256),
					(A_u_char)((x * 47 + y * 13) % 256)};
				else if constexpr (std::is_same<P, PF_Pixel16>::value) p = {32768,
					(A_u_short)((x * 4093 + y * 257) % 32769),
					(A_u_short)((x * 1237 + y * 3559) % 32769),
					(A_u_short)((x * 7919 + y * 911) % 32769)};
				else p = {1.f, (float)(((x * 4093 + y * 257) % 32769) / 32768.),
					(float)(((x * 1237 + y * 3559) % 32769) / 32768.),
					(float)(((x * 7919 + y * 911) % 32769) / 32768.)};
			}
			std::memcpy(raw.data() + (size_t)y * rb + (size_t)x * sizeof(P), &p, sizeof p);
		}
		std::fill(raw.begin() + (size_t)y * rb + 32 * sizeof(P),
		          raw.begin() + (size_t)(y + 1) * rb, (unsigned char)(0xa0 + y));
	}
}

static std::string Digest(const std::vector<unsigned char>& raw, int rb, int active)
{
	olm::Sha256 h; for (int y = 0; y < 18; ++y) h.update(raw.data() + (size_t)y * rb, active);
	unsigned char d[32]; h.final(d); char s[65];
	for (int i = 0; i < 32; ++i) std::snprintf(s + i * 2, 3, "%02x", d[i]);
	s[64] = 0; return s;
}

static OLMRadialBlurInfo Info(double gain, double size, double noise)
{
	OLMRadialBlurInfo i{}; i.blur_type = 2; i.center_x = 16; i.center_y = 9;
	i.outer_strength = 4; i.outer_offset_mode = 1; i.inner_offset_mode = 1;
	i.repeat_border = TRUE; i.ratio = 1; i.quality = 5; i.brightness_gain = gain;
	i.size_variation = size; i.noise_variation = noise; i.noise_type = 1;
	i.seed = 1; i.thickness = 10; i.comp_width = 32; i.comp_height = 18; return i;
}

template <typename P> static int Run(int depth)
{
	const int active = 32 * (int)sizeof(P), rb = active + (depth == 8 ? 8 : 16);
	std::vector<unsigned char> canonical((size_t)rb * 18); Fill<P>(canonical, rb);
	for (double gain : {.5, 1., 2.}) for (double size : {25., 100.}) for (double noise : {25., 100.}) {
		auto input = canonical, before = input; std::vector<unsigned char> output((size_t)rb * 18, 0xee);
		PF_EffectWorld iw{}, ow{}; iw.data = (PF_PixelPtr)input.data(); iw.rowbytes = rb;
		iw.width = 32; iw.height = 18; ow = iw; ow.data = (PF_PixelPtr)output.data();
		auto info = Info(gain, size, noise); const PF_Err err = OLMRadialBlurTestRenderWorld(&iw, &ow, &info, depth);
		if (err || input != before) return 10 + depth;
		for (int y = 0; y < 18; ++y) for (int x = active; x < rb; ++x)
			if (output[(size_t)y * rb + x] != 0xee) return 20 + depth;
		std::printf("POS PF%d g%.1f sv%.0f nv%.0f %s\n", depth, gain, size, noise,
		            Digest(output, rb, active).c_str());
	}
#ifndef OLM_RADIAL_SKIP_MUTATION_CHECKS
	for (int mutation = 0; mutation < 3; ++mutation) {
		auto input = canonical; const size_t off = mutation == 0 ? 0 : mutation == 1
			? (size_t)9 * rb + active / 2 : (size_t)17 * rb + active - 1;
		input[off] ^= 1; auto before = input; std::vector<unsigned char> output((size_t)rb * 18, 0xee);
		PF_EffectWorld iw{}, ow{}; iw.data = (PF_PixelPtr)input.data(); iw.rowbytes = rb;
		iw.width = 32; iw.height = 18; ow = iw; ow.data = (PF_PixelPtr)output.data();
		auto info = Info(1., 25., 25.); const PF_Err err = OLMRadialBlurTestRenderWorld(&iw, &ow, &info, depth);
		if (err != PF_Err_BAD_CALLBACK_PARAM || input != before ||
		    !std::all_of(output.begin(), output.end(), [](unsigned char v){ return v == 0xee; }))
			return 100 + depth + mutation;
		std::printf("NEG PF%d component m%d reject\n", depth, mutation);
	}
#endif
	return 0;
}

int main()
{
	if (int e = Run<PF_Pixel8>(8)) return e;
	if (int e = Run<PF_Pixel16>(16)) return e;
	return Run<PF_PixelFloat>(32);
}

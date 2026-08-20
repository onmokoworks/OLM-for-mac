#include <cstdio>
#include <cstring>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../mac/OLMColorKey/OLMColorKey.cpp"

static OLMColorKeyInfo PixelLocalInfo()
{
	OLMColorKeyInfo info = {};
	info.color_space = 1;
	info.force_lower_precision = 1;
	info.edge_thin_distance_type = 1;
	info.edge_blur_distance_type = 1;
	info.edge_blur_direction = 102;
	info.number_of_colors = 1;
	info.use_color[0] = true;
	info.colors8[0] = {255, 0, 0, 0};
	info.colors[0] = {1.0f, 0.0f, 0.0f, 0.0f};
	return info;
}

static PF_EffectWorld World(std::vector<std::uint8_t> &bytes, A_long rowbytes,
	                         A_long width, A_long height)
{
	PF_EffectWorld world = {};
	world.data = reinterpret_cast<PF_PixelPtr>(bytes.data());
	world.rowbytes = rowbytes;
	world.width = width;
	world.height = height;
	world.extent_hint = {0, 0, width, height};
	return world;
}

template <typename PixelT> static PixelT SourcePixel(A_long x, A_long y);
template <> PF_Pixel8 SourcePixel<PF_Pixel8>(A_long x, A_long y)
{
	if (x == 3 && y == 2) return {211, 0, 0, 0};
	return {(A_u_char)(90 + (x + y) % 150), (A_u_char)(1 + x % 250),
	        (A_u_char)(2 + y % 250), (A_u_char)(3 + (x * 7 + y) % 250)};
}
template <> PF_Pixel16 SourcePixel<PF_Pixel16>(A_long x, A_long y)
{
	if (x == 3 && y == 2) return {27119, 0, 0, 0};
	return {(A_u_short)(12000 + x + y), (A_u_short)(1 + x),
	        (A_u_short)(2 + y), (A_u_short)(3 + x * 7 + y)};
}
template <> PF_PixelFloat SourcePixel<PF_PixelFloat>(A_long x, A_long y)
{
	if (x == 3 && y == 2) return {0.73f, 0, 0, 0};
	return {0.2f + x * 0.001f, 0.01f + x * 0.001f,
	        0.02f + y * 0.001f, 0.03f + (x + y) * 0.001f};
}

template <typename PixelT>
static bool Run(short depth, A_long width, A_long height)
{
	const A_long active = width * (A_long)sizeof(PixelT);
	const A_long input_rowbytes = active + 16;
	const A_long output_rowbytes = active + 32;
	std::vector<std::uint8_t> input((size_t)input_rowbytes * height, 0xA5);
	std::vector<std::uint8_t> output((size_t)output_rowbytes * height, 0xEE);
	for (A_long y = 0; y < height; ++y) for (A_long x = 0; x < width; ++x) {
		const PixelT pixel = SourcePixel<PixelT>(x, y);
		std::memcpy(input.data() + (size_t)y * input_rowbytes +
		            (size_t)x * sizeof(PixelT), &pixel, sizeof(pixel));
	}
	const auto input_before = input;
	PF_EffectWorld in = World(input, input_rowbytes, width, height);
	PF_EffectWorld out = World(output, output_rowbytes, width, height);
	ColorKeyPreparedRender prepared;
	if (PrepareRenderWorld(&in, &out, PixelLocalInfo(), depth, &prepared)) return false;
	CommitPreparedRender(prepared, &out);
	if (input != input_before) return false;
	for (A_long y = 0; y < height; ++y) {
		for (A_long x = 0; x < width; ++x) {
			PixelT actual;
			std::memcpy(&actual, output.data() + (size_t)y * output_rowbytes +
			            (size_t)x * sizeof(PixelT), sizeof(actual));
			PixelT expected = SourcePixel<PixelT>(x, y);
			if (x == 3 && y == 2) expected.alpha = 0;
			if (std::memcmp(&actual, &expected, sizeof(actual))) return false;
		}
		for (A_long i = active; i < output_rowbytes; ++i)
			if (output[(size_t)y * output_rowbytes + i] != 0xEE) return false;
	}

	PF_EffectWorld bad = in;
	bad.rowbytes = active - 1;
	if (PrepareRenderWorld(&bad, &out, PixelLocalInfo(), depth, &prepared) !=
	    PF_Err_BAD_CALLBACK_PARAM) return false;
	PF_EffectWorld overlap = in;
	overlap.data = in.data;
	if (PrepareRenderWorld(&in, &overlap, PixelLocalInfo(), depth, &prepared) !=
	    PF_Err_BAD_CALLBACK_PARAM) return false;
	OLMColorKeyInfo edge = PixelLocalInfo();
	edge.edge_blur_amount = 1.0;
	if (PrepareRenderWorld(&in, &out, edge, depth, &prepared) !=
	    PF_Err_BAD_CALLBACK_PARAM) return false;
	OLMColorKeyInfo invalid_thin = PixelLocalInfo();
	invalid_thin.edge_thin_amount = 101.0;
	if (PrepareRenderWorld(&in, &out, invalid_thin, depth, &prepared) !=
	    PF_Err_BAD_CALLBACK_PARAM) return false;
	invalid_thin.edge_thin_amount = 1.0;
	invalid_thin.edge_thin_distance_type = 0;
	if (PrepareRenderWorld(&in, &out, invalid_thin, depth, &prepared) !=
	    PF_Err_BAD_CALLBACK_PARAM) return false;
	return true;
}

int main()
{
	const bool ok = Run<PF_Pixel8>(8, 17, 11) &&
	                Run<PF_Pixel16>(16, 63, 35) &&
	                Run<PF_PixelFloat>(32, 320, 181);
	std::fprintf(stderr, "GENERIC_PIXEL_LOCAL_BETA pass=%d\n", ok ? 1 : 0);
	return ok ? 0 : 1;
}

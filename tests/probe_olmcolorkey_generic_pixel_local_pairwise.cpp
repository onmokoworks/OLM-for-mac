#include <cstdio>
#include <cstring>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../mac/OLMColorKey/OLMColorKey.cpp"

struct MatrixCell {
	short depth;
	A_long width, height, color_space, colors;
	bool keep, replace, premultiplied;
	double edge_thin_amount = 0.0;
	A_long edge_thin_distance_type = 1;
	double edge_blur_amount = 0.0;
	A_long edge_blur_distance_type = 1;
	A_long edge_blur_direction = 102;
};

static const MatrixCell kCells[] = {
	{8, 17, 11, 1, 1, false, false, false},
	{16, 63, 35, 2, 2, true, false, true},
	{32, 127, 71, 4, 25, false, false, true},
	{8, 191, 107, 5, 2, true, true, false},
	{16, 320, 181, 6, 25, true, true, true},
	{32, 641, 359, 1, 2, false, false, false},
	{8, 1280, 720, 2, 25, true, true, true},
	{16, 1920, 1080, 4, 1, false, false, false},
	{32, 1920, 1080, 5, 2, true, false, true},
	{8, 3840, 2160, 6, 25, true, true, false},
	{8, 321, 181, 1, 2, false, false, false, 1.0, 1},
	{16, 720, 480, 2, 1, true, false, true, -2.0, 2},
	{32, 1920, 1080, 5, 2, false, false, false, 3.0, 3},
	{8, 3840, 2160, 1, 1, true, true, false, -4.0, 3},
	{8, 65, 37, 1, 1, false, false, false, 0, 1, 1, 1, 101},
	{16, 321, 181, 2, 2, true, false, true, 0, 1, 4, 3, 101},
	{32, 720, 480, 4, 25, false, false, false, 0, 1, 1, 2, 102},
	{8, 1920, 1080, 5, 2, true, true, false, 0, 1, 4, 1, 102},
	{16, 67, 39, 6, 1, false, false, true, 0, 1, 1, 3, 103},
	{32, 319, 179, 1, 25, true, false, false, 0, 1, 4, 2, 103},
	{8, 720, 480, 2, 1, false, false, false, 0, 1, 1, 1, 100},
	{16, 1920, 1080, 4, 2, true, true, true, 0, 1, 4, 3, 100},
	{32, 69, 41, 5, 25, false, false, true, 0, 1, 1, 3, 104},
	{8, 323, 183, 6, 2, true, false, false, 0, 1, 4, 1, 104},
	{8, 71, 43, 1, 1, false, false, false, 0, 1, .5, 2, 102},
	{16, 160, 90, 2, 2, true, false, true, 0, 1, 1.5, 2, 102},
	{32, 321, 183, 4, 25, false, false, false, 0, 1, 2, 2, 102},
	{8, 640, 360, 5, 2, true, true, false, 0, 1, 2.5, 2, 102},
	{16, 67, 45, 6, 1, false, false, true, 0, 1, 3, 2, 102},
	{32, 319, 181, 1, 25, true, false, false, 0, 1, 3.5, 2, 102},
	{8, 720, 480, 2, 1, false, false, false, 0, 1, 4, 2, 102},
	{16, 73, 47, 4, 2, true, true, true, 0, 1, 2, 2, 100},
	{32, 323, 185, 5, 25, false, false, true, 0, 1, 2, 2, 101},
	{8, 640, 361, 6, 2, true, false, false, 0, 1, 2, 2, 103},
	{16, 75, 49, 1, 1, false, false, false, 0, 1, 2, 2, 104},
	{32, 325, 187, 2, 2, true, true, true, 0, 1, 1, 2, 101},
};

template <typename PixelT> struct Traits;
template <> struct Traits<PF_Pixel8> {
	static PF_Pixel8 pixel(A_long x, A_long y) {
		if ((x + y * 3) % 97 == 0) return {211, 0, 0, 0};
		return {(A_u_char)(64 + (x + y) % 191), (A_u_char)(1 + x % 254),
		        (A_u_char)(1 + y % 254), (A_u_char)(1 + (x * 7 + y) % 254)};
	}
};
template <> struct Traits<PF_Pixel16> {
	static PF_Pixel16 pixel(A_long x, A_long y) {
		if ((x + y * 3) % 97 == 0) return {27119, 0, 0, 0};
		return {(A_u_short)(8000 + (x + y) % 24000), (A_u_short)(1 + x % 32000),
		        (A_u_short)(1 + y % 32000), (A_u_short)(1 + (x * 7 + y) % 32000)};
	}
};
template <> struct Traits<PF_PixelFloat> {
	static PF_PixelFloat pixel(A_long x, A_long y) {
		if ((x + y * 3) % 97 == 0) return {0.73f, 0, 0, 0};
		return {0.25f + (x + y) % 500 * 0.001f, 0.01f + x % 900 * 0.001f,
		        0.01f + y % 900 * 0.001f, 0.01f + (x * 7 + y) % 900 * 0.001f};
	}
};

static PF_EffectWorld World(std::vector<std::uint8_t> &bytes, A_long rowbytes,
	                         A_long width, A_long height)
{
	PF_EffectWorld world = {};
	world.data = reinterpret_cast<PF_PixelPtr>(bytes.data());
	world.rowbytes = rowbytes; world.width = width; world.height = height;
	world.extent_hint = {0, 0, width, height};
	return world;
}

static OLMColorKeyInfo Info(const MatrixCell &cell)
{
	OLMColorKeyInfo info = {};
	info.color_keep = cell.keep; info.premultiplied = cell.premultiplied;
	info.color_space = cell.color_space; info.force_lower_precision = 1;
	info.edge_thin_amount = cell.edge_thin_amount;
	info.edge_thin_distance_type = cell.edge_thin_distance_type;
	info.edge_blur_amount = cell.edge_blur_amount;
	info.edge_blur_distance_type = cell.edge_blur_distance_type;
	info.edge_blur_direction = cell.edge_blur_direction;
	info.number_of_colors = cell.colors;
	info.enable_replace = cell.replace;
	for (A_long i = 0; i < cell.colors; ++i) {
		info.use_color[i] = true; info.use_replace_color[i] = cell.replace;
		info.colors8[i] = i == 0 ? PF_Pixel8{255, 0, 0, 0}
		                              : PF_Pixel8{255, (A_u_char)i, (A_u_char)(i * 3), (A_u_char)(i * 7)};
		info.colors[i] = {1.0f, info.colors8[i].red / 255.0f,
		                  info.colors8[i].green / 255.0f, info.colors8[i].blue / 255.0f};
		info.replace_colors[i] = {1.0f, 0.9f, 0.2f, 0.1f};
	}
	return info;
}

template <typename PixelT>
static bool RunTyped(const MatrixCell &cell)
{
	const A_long active = cell.width * (A_long)sizeof(PixelT);
	const A_long padded_in = active + 16, padded_out = active + 32;
	std::vector<std::uint8_t> tight_in((size_t)active * cell.height);
	std::vector<std::uint8_t> tight_out((size_t)active * cell.height, 0xCC);
	std::vector<std::uint8_t> padded_input((size_t)padded_in * cell.height, 0xA5);
	std::vector<std::uint8_t> padded_output((size_t)padded_out * cell.height, 0xEE);
	for (A_long y = 0; y < cell.height; ++y) for (A_long x = 0; x < cell.width; ++x) {
		const PixelT p = Traits<PixelT>::pixel(x, y);
		std::memcpy(tight_in.data() + (size_t)y * active + (size_t)x * sizeof(PixelT), &p, sizeof(p));
		std::memcpy(padded_input.data() + (size_t)y * padded_in + (size_t)x * sizeof(PixelT), &p, sizeof(p));
	}
	const auto tight_before = tight_in, padded_before = padded_input;
	PF_EffectWorld ti = World(tight_in, active, cell.width, cell.height);
	PF_EffectWorld to = World(tight_out, active, cell.width, cell.height);
	PF_EffectWorld pi = World(padded_input, padded_in, cell.width, cell.height);
	PF_EffectWorld po = World(padded_output, padded_out, cell.width, cell.height);
	if (RenderWorld(&ti, &to, Info(cell), cell.depth) ||
	    RenderWorld(&pi, &po, Info(cell), cell.depth)) return false;
	if (tight_in != tight_before || padded_input != padded_before) return false;
	for (A_long y = 0; y < cell.height; ++y) {
		if (std::memcmp(tight_out.data() + (size_t)y * active,
		                padded_output.data() + (size_t)y * padded_out, active)) return false;
		for (A_long i = active; i < padded_out; ++i)
			if (padded_output[(size_t)y * padded_out + i] != 0xEE) return false;
	}
	return true;
}

int main(int argc, char **argv)
{
	const char *geometry = argc == 3 && std::strcmp(argv[1], "--geometry") == 0
	    ? argv[2] : "all";
	int passed = 0;
	for (const MatrixCell &cell : kCells) {
		const bool is_hd = cell.width == 1920 && cell.height == 1080;
		const bool is_uhd = cell.width == 3840 && cell.height == 2160;
		const bool is_sanitizer =
		    (cell.edge_thin_amount != 0.0 || cell.edge_blur_amount != 0.0) &&
		    cell.width <= 720;
		if ((std::strcmp(geometry, "hd") == 0 && !is_hd) ||
		    (std::strcmp(geometry, "uhd") == 0 && !is_uhd) ||
		    (std::strcmp(geometry, "sanitizer") == 0 && !is_sanitizer)) continue;
		const bool ok = cell.depth == 8 ? RunTyped<PF_Pixel8>(cell) :
		                cell.depth == 16 ? RunTyped<PF_Pixel16>(cell) :
		                                   RunTyped<PF_PixelFloat>(cell);
		if (!ok) return 1;
		++passed;
	}
	if (passed == 0) return 2;
	std::fprintf(stderr, "GENERIC_PIXEL_LOCAL_PAIRWISE pass=1 geometry=%s cells=%d\n",
	             geometry, passed);
	return 0;
}

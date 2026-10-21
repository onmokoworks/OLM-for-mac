#include <cstdio>
#include <cstring>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../../mac/OLMColorKey/OLMColorKey.cpp"

struct EdgeTuple { A_long direction; A_long distance; double amount; A_long width; A_long height; };

static const EdgeTuple kEdgeTuples[] = {
	{1, 1, 1.0, 32, 18}, {1, 3, 4.0, 32, 18},
	{2, 2, 1.0, 32, 18}, {2, 1, 4.0, 32, 18},
	{3, 3, 1.0, 32, 18}, {3, 2, 4.0, 32, 18},
	{0, 1, 1.0, 64, 36}, {0, 3, 4.0, 64, 36},
	{4, 3, 1.0, 64, 36}, {4, 1, 4.0, 64, 36},
	{0, 3, 4.0, 48, 27},
};

static OLMColorKeyInfo EdgeInfo(const EdgeTuple &tuple)
{
	OLMColorKeyInfo info = {};
	info.color_space = 1;
	info.force_lower_precision = 1;
	info.edge_thin_distance_type = 2;
	info.edge_blur_amount = tuple.amount;
	info.edge_blur_distance_type = tuple.distance;
	info.edge_blur_direction = tuple.direction + 100;
	info.number_of_colors = 2;
	info.use_color[0] = info.use_color[1] = true;
	info.colors8[0] = {255, 0, 0, 0};
	info.colors8[1] = {255, 0, 255, 0};
	info.colors[0] = {1.0f, 0.0f, 0.0f, 0.0f};
	info.colors[1] = {1.0f, 0.0f, 1.0f, 0.0f};
	return info;
}

static OLMColorKeyInfo LabInfo(bool reversed)
{
	OLMColorKeyInfo info = {};
	info.threshold = 0.085;
	info.color_space = 3;
	info.force_lower_precision = 1;
	info.edge_thin_distance_type = 1;
	info.edge_blur_distance_type = 1;
	info.edge_blur_direction = 102;
	info.number_of_colors = 2;
	info.use_color[0] = info.use_color[1] = true;
	info.colors8[0] = reversed ? PF_Pixel8{255, 26, 191, 204}
	                           : PF_Pixel8{255, 204, 38, 26};
	info.colors8[1] = reversed ? PF_Pixel8{255, 204, 38, 26}
	                           : PF_Pixel8{255, 26, 191, 204};
	info.colors[0] = reversed ? PF_PixelFloat{1, 26 / 255.0f, 191 / 255.0f, 204 / 255.0f}
	                          : PF_PixelFloat{1, 204 / 255.0f, 38 / 255.0f, 26 / 255.0f};
	info.colors[1] = reversed ? PF_PixelFloat{1, 204 / 255.0f, 38 / 255.0f, 26 / 255.0f}
	                          : PF_PixelFloat{1, 26 / 255.0f, 191 / 255.0f, 204 / 255.0f};
	return info;
}

static OLMColorKeyInfo ToggleInfo(bool keep, bool premultiplied, bool replace)
{
	OLMColorKeyInfo info = {};
	info.color_keep = keep; info.premultiplied = premultiplied;
	info.color_space = 1; info.force_lower_precision = 1;
	info.edge_thin_distance_type = 1; info.edge_blur_distance_type = 1;
	info.edge_blur_direction = 102; info.number_of_colors = 2;
	info.enable_replace = replace;
	info.use_color[0] = info.use_color[1] = true;
	info.use_replace_color[0] = info.use_replace_color[1] = replace;
	info.colors8[0] = {255, 0, 0, 0}; info.colors8[1] = {255, 0, 255, 0};
	info.colors[0] = {1, 0, 0, 0}; info.colors[1] = {1, 0, 1, 0};
	info.replace_colors[0] = {1, 230 / 255.0f, 38 / 255.0f, 26 / 255.0f};
	info.replace_colors[1] = {1, 26 / 255.0f, 89 / 255.0f, 242 / 255.0f};
	return info;
}

template <typename PixelT>
static void FillEdge(std::vector<std::uint8_t> &storage, A_long rowbytes,
	                 A_long width, A_long height)
{
	for (A_long y = 0; y < height; ++y) {
		for (A_long x = 0; x < width; ++x) {
			const PixelT pixel = width == 48 && height == 27
			    ? EdgeSecondFixturePixel<PixelT>(x, y)
			    : EdgeFixturePixel<PixelT>(x, y, width, height);
			std::memcpy(storage.data() + (size_t)y * rowbytes + (size_t)x * sizeof(PixelT),
			            &pixel, sizeof(pixel));
		}
	}
}

template <typename PixelT>
static void FillToggle(std::vector<std::uint8_t> &storage, A_long rowbytes)
{
	for (A_long y = 0; y < 7; ++y) for (A_long x = 0; x < 11; ++x) {
		const PixelT pixel = ToggleFixturePixel<PixelT>(x, y);
		std::memcpy(storage.data() + (size_t)y * rowbytes +
		            (size_t)x * sizeof(PixelT), &pixel, sizeof(pixel));
	}
}

template <typename PixelT> static PixelT LabPixel();
template <> PF_Pixel8 LabPixel<PF_Pixel8>() { return {255, 26, 191, 204}; }
template <> PF_Pixel16 LabPixel<PF_Pixel16>() { return {32768, 3341, 24544, 26214}; }
template <> PF_PixelFloat LabPixel<PF_PixelFloat>() { return {1, 26 / 255.0f, 191 / 255.0f, 204 / 255.0f}; }

static PF_EffectWorld World(std::vector<std::uint8_t> &storage,
	                        A_long rowbytes, A_long width, A_long height)
{
	PF_EffectWorld world = {};
	world.data = reinterpret_cast<PF_PixelPtr>(storage.data());
	world.rowbytes = rowbytes;
	world.width = width;
	world.height = height;
	world.extent_hint = {0, 0, width, height};
	world.origin_x = world.origin_y = 0;
	return world;
}

template <typename PixelT>
static bool Rejects(PF_EffectWorld input, PF_EffectWorld output,
	                const OLMColorKeyInfo &info, short depth,
	                const std::vector<std::uint8_t> &)
{
	ColorKeyPreparedRender prepared;
	const PF_Err err = PrepareRenderWorld(&input, &output, info, depth, &prepared);
	return err == PF_Err_BAD_CALLBACK_PARAM;
}

template <typename PixelT>
static bool RunCell(const OLMColorKeyInfo &info, A_long width, A_long height,
	                short depth, int fixture_kind, int *negative_count)
{
	const A_long rowbytes = width * (A_long)sizeof(PixelT) + 8;
	std::vector<std::uint8_t> input((size_t)rowbytes * height, 0xA5);
	std::vector<std::uint8_t> output((size_t)rowbytes * height, 0xEE);
	if (fixture_kind == 1) FillEdge<PixelT>(input, rowbytes, width, height);
	else if (fixture_kind == 2) FillToggle<PixelT>(input, rowbytes);
	else {
		const PixelT pixel = LabPixel<PixelT>();
		std::memcpy(input.data(), &pixel, sizeof(pixel));
	}
	const std::vector<std::uint8_t> input_before = input;
	const std::vector<std::uint8_t> output_before = output;
	PF_EffectWorld input_world = World(input, rowbytes, width, height);
	PF_EffectWorld output_world = World(output, rowbytes, width, height);
	ColorKeyPreparedRender prepared;
	if (PrepareRenderWorld(&input_world, &output_world, info, depth, &prepared)) return false;
	if (input != input_before || output != output_before) return false;
	CommitPreparedRender(prepared, &output_world);
	if (input != input_before) return false;
	const std::vector<std::uint8_t> committed_output = output;
	for (A_long y = 0; y < height; ++y) {
		for (A_long i = width * (A_long)sizeof(PixelT); i < rowbytes; ++i) {
			if (output[(size_t)y * rowbytes + i] != 0xEE) return false;
		}
		std::fwrite(output.data() + (size_t)y * rowbytes, 1,
		            (size_t)width * sizeof(PixelT), stdout);
	}

	for (int point = 0; point < 3; ++point) {
		std::vector<std::uint8_t> mutated = input;
		const size_t active = (size_t)width * height * sizeof(PixelT);
		const size_t logical = point == 0 ? 0 : point == 1 ? active / 2 : active - 1;
		const size_t row_active = (size_t)width * sizeof(PixelT);
		const size_t offset = (logical / row_active) * rowbytes + logical % row_active;
		mutated[offset] ^= 1;
		PF_EffectWorld changed = World(mutated, rowbytes, width, height);
		if (!Rejects<PixelT>(changed, output_world, info, depth, output)) return false;
		++*negative_count;
	}
	OLMColorKeyInfo changed_info = info;
	if (fixture_kind == 1) changed_info.edge_blur_amount = std::nextafter(info.edge_blur_amount, 100.0);
	else if (fixture_kind == 2) changed_info.color_space = 2;
	else changed_info.threshold = std::nextafter(info.threshold, 1.0);
	if (!Rejects<PixelT>(input_world, output_world, changed_info, depth, output)) return false;
	++*negative_count;

	PF_EffectWorld changed = input_world;
	changed.rowbytes += 1;
	if (!Rejects<PixelT>(changed, output_world, info, depth, output)) return false;
	++*negative_count;
	changed = input_world;
	changed.extent_hint.right -= 1;
	if (!Rejects<PixelT>(changed, output_world, info, depth, output)) return false;
	++*negative_count;
	changed = input_world;
	changed.origin_x = 1;
	if (!Rejects<PixelT>(changed, output_world, info, depth, output)) return false;
	++*negative_count;
	PF_EffectWorld aliased = output_world;
	aliased.data = input_world.data;
	if (!Rejects<PixelT>(input_world, aliased, info, depth, input)) return false;
	++*negative_count;
	PF_EffectWorld partial = output_world;
	partial.data = reinterpret_cast<PF_PixelPtr>(
	    reinterpret_cast<std::uint8_t *>(input_world.data) + sizeof(PixelT));
	if (!Rejects<PixelT>(input_world, partial, info, depth, input)) return false;
	++*negative_count;
	return input == input_before && output == committed_output;
}

template <typename PixelT>
static bool RunDepth(short depth, int *positive_count, int *negative_count)
{
	for (const EdgeTuple &tuple : kEdgeTuples) {
		if (!RunCell<PixelT>(EdgeInfo(tuple), tuple.width, tuple.height,
		                     depth, 1, negative_count)) return false;
		++*positive_count;
	}
	for (bool reversed : {false, true}) {
		if (!RunCell<PixelT>(LabInfo(reversed), 1, 1, depth, false,
		                     negative_count)) return false;
		++*positive_count;
	}
	for (bool keep : {false, true}) for (bool premultiplied : {false, true})
		for (bool replace : {false, true}) {
		if (!RunCell<PixelT>(ToggleInfo(keep, premultiplied, replace), 11, 7,
		                     depth, 2,
		                     negative_count)) return false;
		++*positive_count;
	}
	return true;
}

int main()
{
	int positives = 0;
	int negatives = 0;
	const bool pass = RunDepth<PF_Pixel8>(8, &positives, &negatives) &&
	                  RunDepth<PF_Pixel16>(16, &positives, &negatives) &&
	                  RunDepth<PF_PixelFloat>(32, &positives, &negatives);
	std::fprintf(stderr, "SOURCE_BOUND_ATOMIC pass=%d positives=%d negatives=%d\n",
	             pass, positives, negatives);
	return pass && positives == 63 && negatives == 567 ? 0 : 3;
}

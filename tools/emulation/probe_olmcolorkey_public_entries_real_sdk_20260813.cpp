#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../../mac/OLMColorKey/OLMColorKey.cpp"

struct EdgeTuple {
	A_long direction;
	A_long distance;
	double amount;
	A_long width;
	A_long height;
};

static const EdgeTuple kEdgeTuples[] = {
	{1, 1, 1.0, 32, 18}, {1, 3, 4.0, 32, 18},
	{2, 2, 1.0, 32, 18}, {2, 1, 4.0, 32, 18},
	{3, 3, 1.0, 32, 18}, {3, 2, 4.0, 32, 18},
	{0, 1, 1.0, 64, 36}, {0, 3, 4.0, 64, 36},
	{4, 3, 1.0, 64, 36}, {4, 1, 4.0, 64, 36},
	{0, 3, 4.0, 48, 27},
};

struct HostState {
	PF_EffectWorld *input = NULL;
	PF_EffectWorld *output = NULL;
	PF_ParamDef *params = NULL;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	int pre = 0;
	int layer = 0;
	int output_checkout = 0;
	int layer_checkin = 0;
	int param_checkout = 0;
	int param_checkin = 0;
	int acquire = 0;
	int release = 0;
	int world_calls = 0;
	int color_calls = 0;
	int fail_stage = 0;
	bool preserve = true;
};

static HostState *g_host = NULL;
static PF_WorldSuite2 g_world_suite = {};
static PF_ColorParamSuite1 g_color_suite = {};

static PF_Err GetFormat(const PF_EffectWorld *, PF_PixelFormat *format)
{
	++g_host->world_calls;
	*format = g_host->format;
	return PF_Err_NONE;
}

static PF_Err GetColor(PF_ProgPtr, const PF_ParamDef *param, PF_PixelFloat *color)
{
	++g_host->color_calls;
	color->alpha = param->u.cd.value.alpha / 255.0f;
	color->red = param->u.cd.value.red / 255.0f;
	color->green = param->u.cd.value.green / 255.0f;
	color->blue = param->u.cd.value.blue / 255.0f;
	return PF_Err_NONE;
}

static SPErr Acquire(const char *name, int32 version, const void **suite)
{
	++g_host->acquire;
	if (!std::strcmp(name, kPFWorldSuite) && version == kPFWorldSuiteVersion2) {
		g_world_suite.PF_GetPixelFormat = GetFormat;
		*suite = &g_world_suite;
		return kSPNoError;
	}
	if (!std::strcmp(name, kPFColorParamSuite) &&
	    version == kPFColorParamSuiteVersion1) {
		g_color_suite.PF_GetFloatingPointColorFromColorDef = GetColor;
		*suite = &g_color_suite;
		return kSPNoError;
	}
	return kSPBadParameterError;
}

static SPErr Release(const char *, int32)
{
	++g_host->release;
	return kSPNoError;
}

static PF_Err CheckoutParam(PF_ProgPtr, PF_ParamIndex index,
	                        A_long, A_long, A_u_long, PF_ParamDef *param)
{
	++g_host->param_checkout;
	*param = g_host->params[index];
	return PF_Err_NONE;
}

static PF_Err CheckinParam(PF_ProgPtr, PF_ParamDef *)
{
	++g_host->param_checkin;
	return PF_Err_NONE;
}

static PF_Err CheckoutLayer(PF_ProgPtr, PF_ParamIndex, A_long,
	                        const PF_RenderRequest *request, A_long, A_long,
	                        A_u_long, PF_CheckoutResult *result)
{
	++g_host->pre;
	if (g_host->fail_stage == 9) return 89;
	if (g_host->fail_stage == 10) throw (PF_Err)90;
	if (g_host->fail_stage == 11) throw std::bad_alloc();
	if (g_host->fail_stage == 12) throw std::runtime_error("pre");
	g_host->preserve = request->preserve_rgb_of_zero_alpha;
	result->result_rect = {0, 0, g_host->input->width, g_host->input->height};
	result->max_result_rect = result->result_rect;
	return PF_Err_NONE;
}

static PF_Err CheckoutPixels(PF_ProgPtr, A_long, PF_EffectWorld **world)
{
	++g_host->layer;
	if (g_host->fail_stage == 1) return 81;
	*world = g_host->fail_stage == 2 ? NULL : g_host->input;
	return PF_Err_NONE;
}

static PF_Err CheckinPixels(PF_ProgPtr, A_long)
{
	++g_host->layer_checkin;
	if (g_host->fail_stage == 5) return 85;
	if (g_host->fail_stage == 6) throw (PF_Err)86;
	if (g_host->fail_stage == 7) throw std::bad_alloc();
	if (g_host->fail_stage == 8) throw std::runtime_error("checkin");
	return PF_Err_NONE;
}

static PF_Err CheckoutOutput(PF_ProgPtr, PF_EffectWorld **world)
{
	++g_host->output_checkout;
	if (g_host->fail_stage == 3) return 83;
	*world = g_host->fail_stage == 4 ? NULL : g_host->output;
	return PF_Err_NONE;
}

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
	info.color_keep = keep;
	info.premultiplied = premultiplied;
	info.color_space = 1;
	info.force_lower_precision = 1;
	info.edge_thin_distance_type = 1;
	info.edge_blur_distance_type = 1;
	info.edge_blur_direction = 102;
	info.number_of_colors = 2;
	info.enable_replace = replace;
	info.use_color[0] = info.use_color[1] = true;
	info.use_replace_color[0] = info.use_replace_color[1] = replace;
	info.colors8[0] = {255, 0, 0, 0};
	info.colors8[1] = {255, 0, 255, 0};
	info.colors[0] = {1.0f, 0.0f, 0.0f, 0.0f};
	info.colors[1] = {1.0f, 0.0f, 1.0f, 0.0f};
	info.replace_colors[0] = {1.0f, 230 / 255.0f, 38 / 255.0f, 26 / 255.0f};
	info.replace_colors[1] = {1.0f, 26 / 255.0f, 89 / 255.0f, 242 / 255.0f};
	return info;
}

static void FillParams(const OLMColorKeyInfo &info,
	                   PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS],
	                   PF_ParamDef *params[OLMCOLORKEY_NUM_PARAMS])
{
	std::memset(defs, 0, sizeof(PF_ParamDef) * OLMCOLORKEY_NUM_PARAMS);
	for (int i = 0; i < OLMCOLORKEY_NUM_PARAMS; ++i) params[i] = &defs[i];
	defs[OLMCOLORKEY_COLOR_KEEP].u.bd.value = info.color_keep;
	defs[OLMCOLORKEY_THRESHOLD].u.fs_d.value = info.threshold;
	defs[OLMCOLORKEY_PREMULTIPLIED].u.bd.value = info.premultiplied;
	defs[OLMCOLORKEY_COLOR_SPACE].u.pd.value = info.color_space;
	defs[OLMCOLORKEY_FORCE_LOWER_PRECISION].u.pd.value = info.force_lower_precision;
	defs[OLMCOLORKEY_PER_COLOR].u.bd.value = info.per_color;
	defs[OLMCOLORKEY_PER_COMPONENT].u.bd.value = info.per_component;
	defs[OLMCOLORKEY_THRESHOLD_R].u.fs_d.value = info.threshold_r;
	defs[OLMCOLORKEY_THRESHOLD_G].u.fs_d.value = info.threshold_g;
	defs[OLMCOLORKEY_THRESHOLD_B].u.fs_d.value = info.threshold_b;
	defs[OLMCOLORKEY_EDGE_THIN_AMOUNT].u.sd.value = info.edge_thin_amount;
	defs[OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE].u.pd.value = info.edge_thin_distance_type;
	defs[OLMCOLORKEY_EDGE_BLUR_AMOUNT].u.fs_d.value = info.edge_blur_amount;
	defs[OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE].u.pd.value = info.edge_blur_distance_type;
	defs[OLMCOLORKEY_EDGE_BLUR_DIRECTION].u.pd.value = info.edge_blur_direction - 100;
	defs[OLMCOLORKEY_NUMBER_OF_COLORS].u.sd.value = info.number_of_colors;
	defs[OLMCOLORKEY_ENABLE_REPLACE].u.bd.value = info.enable_replace;
	for (int i = 0; i < info.number_of_colors; ++i) {
		defs[ColorParamIndex(i, COLOR_OFFSET_COLOR)].u.cd.value = info.colors8[i];
		auto byte = [](float value) -> A_u_char {
			return (A_u_char)std::lround((double)value * 255.0);
		};
		defs[ColorParamIndex(i, COLOR_OFFSET_REPLACE_COLOR)].u.cd.value = {
			byte(info.replace_colors[i].alpha), byte(info.replace_colors[i].red),
			byte(info.replace_colors[i].green), byte(info.replace_colors[i].blue)};
		defs[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD)].u.fs_d.value = info.thresholds[i];
		defs[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_R)].u.fs_d.value = info.thresholds_r[i];
		defs[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_G)].u.fs_d.value = info.thresholds_g[i];
		defs[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_B)].u.fs_d.value = info.thresholds_b[i];
		defs[ColorParamIndex(i, COLOR_OFFSET_USE_COLOR)].u.bd.value = info.use_color[i];
		defs[ColorParamIndex(i, COLOR_OFFSET_USE_REPLACE)].u.bd.value = info.use_replace_color[i];
	}
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
			std::memcpy(storage.data() + (size_t)y * rowbytes +
			                (size_t)x * sizeof(PixelT), &pixel, sizeof(pixel));
		}
	}
}

template <typename PixelT>
static void FillToggle(std::vector<std::uint8_t> &storage, A_long rowbytes)
{
	for (A_long y = 0; y < 7; ++y) {
		for (A_long x = 0; x < 11; ++x) {
			const PixelT pixel = ToggleFixturePixel<PixelT>(x, y);
			std::memcpy(storage.data() + (size_t)y * rowbytes +
			                (size_t)x * sizeof(PixelT), &pixel, sizeof(pixel));
		}
	}
}

template <typename PixelT> static PixelT LabPixel();
template <> PF_Pixel8 LabPixel<PF_Pixel8>() { return {255, 26, 191, 204}; }
template <> PF_Pixel16 LabPixel<PF_Pixel16>() { return {32768, 3341, 24544, 26214}; }
template <> PF_PixelFloat LabPixel<PF_PixelFloat>() { return {1, 26 / 255.0f, 191 / 255.0f, 204 / 255.0f}; }

static PF_EffectWorld MakeWorld(std::vector<std::uint8_t> &storage,
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

static PF_InData MakeInData(HostState *state, SPBasicSuite *basic)
{
	PF_InData in_data = {};
	in_data.effect_ref = reinterpret_cast<PF_ProgPtr>(state);
	in_data.pica_basicP = basic;
	in_data.output_origin_x = in_data.output_origin_y = 0;
	in_data.downsample_x = {1, 1};
	in_data.downsample_y = {1, 1};
	in_data.inter.checkout_param = CheckoutParam;
	in_data.inter.checkin_param = CheckinParam;
	return in_data;
}

template <typename PixelT>
static bool RunOne(const OLMColorKeyInfo &info, A_long width, A_long height,
	               short depth, PF_PixelFormat format, int fixture_kind,
	               int *classic_count, int *smart_count)
{
	const A_long rowbytes = width * (A_long)sizeof(PixelT) + 8;
	std::vector<std::uint8_t> input((size_t)rowbytes * height, 0xA5);
	if (fixture_kind == 1) FillEdge<PixelT>(input, rowbytes, width, height);
	else if (fixture_kind == 2) FillToggle<PixelT>(input, rowbytes);
	else {
		const PixelT pixel = LabPixel<PixelT>();
		std::memcpy(input.data(), &pixel, sizeof(pixel));
	}
	const std::vector<std::uint8_t> input_before = input;
	PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS] = {};
	PF_ParamDef *params[OLMCOLORKEY_NUM_PARAMS] = {};
	FillParams(info, defs, params);

	SPBasicSuite basic = {};
	basic.AcquireSuite = Acquire;
	basic.ReleaseSuite = Release;
	for (int route = 0; route < 2; ++route) {
		std::vector<std::uint8_t> output((size_t)rowbytes * height, 0xEE);
		PF_EffectWorld input_world = MakeWorld(input, rowbytes, width, height);
		PF_EffectWorld output_world = MakeWorld(output, rowbytes, width, height);
		defs[OLMCOLORKEY_INPUT].u.ld = input_world;
		HostState state;
		state.input = &input_world;
		state.output = &output_world;
		state.params = defs;
		state.format = format;
		g_host = &state;
		PF_InData in_data = MakeInData(&state, &basic);
		PF_OutData out_data = {};
		PF_Err err = PF_Err_NONE;
		if (route == 0) {
			err = EffectMain(PF_Cmd_RENDER, &in_data, &out_data,
			                 params, &output_world, NULL);
			if (err || state.acquire != 2 || state.release != 2 ||
			    state.world_calls != 2 || state.color_calls != 4) return false;
			++*classic_count;
		} else {
			PF_PreRenderInput pre_input = {};
			PF_PreRenderOutput pre_output = {};
			PF_PreRenderCallbacks pre_callbacks = {};
			pre_callbacks.checkout_layer = CheckoutLayer;
			PF_PreRenderExtra pre_extra = {&pre_input, &pre_output, &pre_callbacks};
			err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in_data, &out_data,
			                 NULL, NULL, &pre_extra);
			if (err) return false;
			PF_SmartRenderInput smart_input = {};
			smart_input.bitdepth = depth;
			PF_SmartRenderCallbacks smart_callbacks = {};
			smart_callbacks.checkout_layer_pixels = CheckoutPixels;
			smart_callbacks.checkin_layer_pixels = CheckinPixels;
			smart_callbacks.checkout_output = CheckoutOutput;
			PF_SmartRenderExtra smart_extra = {&smart_input, &smart_callbacks};
			err = EffectMain(PF_Cmd_SMART_RENDER, &in_data, &out_data,
			                 NULL, NULL, &smart_extra);
			if (err || state.pre != 1 || state.layer != 1 ||
			    state.output_checkout != 1 || state.layer_checkin != 1 ||
			    state.param_checkout != 33 || state.param_checkin != 33 ||
			    state.acquire != 2 || state.release != 2 ||
			    state.world_calls != 2 || state.color_calls != 4 || state.preserve)
				return false;
			++*smart_count;
		}
		if (input != input_before) return false;
		for (A_long y = 0; y < height; ++y) {
			for (A_long i = width * (A_long)sizeof(PixelT); i < rowbytes; ++i) {
				if (output[(size_t)y * rowbytes + i] != 0xEE) return false;
			}
			std::fwrite(output.data() + (size_t)y * rowbytes, 1,
			            (size_t)width * sizeof(PixelT), stdout);
		}
	}
	return true;
}

template <typename PixelT>
static bool RunDepth(short depth, PF_PixelFormat format,
	                 int *classic_count, int *smart_count)
{
	for (const EdgeTuple &tuple : kEdgeTuples) {
		if (!RunOne<PixelT>(EdgeInfo(tuple), tuple.width, tuple.height,
		                    depth, format, 1, classic_count, smart_count))
			return false;
	}
	for (bool reversed : {false, true}) {
		if (!RunOne<PixelT>(LabInfo(reversed), 1, 1, depth, format,
		                    0, classic_count, smart_count)) return false;
	}
	for (bool keep : {false, true}) {
		for (bool premultiplied : {false, true}) {
			for (bool replace : {false, true}) {
				if (!RunOne<PixelT>(ToggleInfo(keep, premultiplied, replace),
				                    11, 7, depth, format, 2,
				                    classic_count, smart_count)) return false;
			}
		}
	}
	return true;
}

static bool SmartCallbackNegatives()
{
	const EdgeTuple &tuple = kEdgeTuples[0];
	const A_long rowbytes = tuple.width * (A_long)sizeof(PF_Pixel8) + 8;
	std::vector<std::uint8_t> input((size_t)rowbytes * tuple.height, 0xA5);
	FillEdge<PF_Pixel8>(input, rowbytes, tuple.width, tuple.height);
	const std::vector<std::uint8_t> input_before = input;
	PF_ParamDef defs[OLMCOLORKEY_NUM_PARAMS] = {};
	PF_ParamDef *params[OLMCOLORKEY_NUM_PARAMS] = {};
	FillParams(EdgeInfo(tuple), defs, params);
	SPBasicSuite basic = {};
	basic.AcquireSuite = Acquire;
	basic.ReleaseSuite = Release;
	for (int stage = 1; stage <= 8; ++stage) {
		std::vector<std::uint8_t> output((size_t)rowbytes * tuple.height, 0xEE);
		const std::vector<std::uint8_t> output_before = output;
		PF_EffectWorld input_world = MakeWorld(input, rowbytes, tuple.width, tuple.height);
		PF_EffectWorld output_world = MakeWorld(output, rowbytes, tuple.width, tuple.height);
		HostState state;
		state.input = &input_world;
		state.output = &output_world;
		state.params = defs;
		state.format = PF_PixelFormat_ARGB32;
		state.fail_stage = stage;
		g_host = &state;
		PF_InData in_data = MakeInData(&state, &basic);
		PF_OutData out_data = {};
		PF_SmartRenderInput smart_input = {};
		smart_input.bitdepth = 8;
		PF_SmartRenderCallbacks callbacks = {};
		callbacks.checkout_layer_pixels = CheckoutPixels;
		callbacks.checkin_layer_pixels = CheckinPixels;
		callbacks.checkout_output = CheckoutOutput;
		PF_SmartRenderExtra extra = {&smart_input, &callbacks};
		const PF_Err err = EffectMain(PF_Cmd_SMART_RENDER, &in_data, &out_data,
		                              NULL, NULL, &extra);
		const PF_Err expected = stage == 1 ? 81 : stage == 2 || stage == 4 ?
		                            PF_Err_BAD_CALLBACK_PARAM : stage == 3 ? 83 :
		                            stage == 5 ? 85 : stage == 6 ? 86 :
		                            stage == 7 ? (PF_Err)4 : PF_Err_INTERNAL_STRUCT_DAMAGED;
		if (err != expected || input != input_before || output != output_before ||
		    state.layer != 1 || state.layer_checkin != (stage == 1 ? 0 : 1) ||
		    state.output_checkout != (stage <= 2 ? 0 : 1)) return false;
	}
	return true;
}

static bool SmartPreNegatives()
{
	SPBasicSuite basic = {};
	basic.AcquireSuite = Acquire;
	basic.ReleaseSuite = Release;
	for (int index = 0; index < 5; ++index) {
		HostState state;
		state.fail_stage = index < 4 ? 9 + index : 0;
		g_host = &state;
		PF_InData in_data = MakeInData(&state, &basic);
		PF_OutData out_data = {};
		PF_PreRenderInput input = {};
		PF_PreRenderOutput output;
		std::memset(&output, 0x5A, sizeof(output));
		const PF_PreRenderOutput before = output;
		PF_PreRenderCallbacks callbacks = {};
		callbacks.checkout_layer = index == 4 ? NULL : CheckoutLayer;
		PF_PreRenderExtra extra = {&input, &output, &callbacks};
		const PF_Err err = EffectMain(PF_Cmd_SMART_PRE_RENDER, &in_data,
		                              &out_data, NULL, NULL, &extra);
		const PF_Err expected = index == 0 ? 89 : index == 1 ? 90 :
		                            index == 2 ? (PF_Err)4 :
		                            index == 3 ? PF_Err_INTERNAL_STRUCT_DAMAGED :
		                            PF_Err_BAD_CALLBACK_PARAM;
		if (err != expected || std::memcmp(&output, &before, sizeof(output)) ||
		    state.pre != (index == 4 ? 0 : 1)) return false;
	}
	return true;
}

int main()
{
	int classic = 0, smart = 0;
	const bool pass = RunDepth<PF_Pixel8>(8, PF_PixelFormat_ARGB32, &classic, &smart) &&
	                  RunDepth<PF_Pixel16>(16, PF_PixelFormat_ARGB64, &classic, &smart) &&
	                  RunDepth<PF_PixelFloat>(32, PF_PixelFormat_ARGB128, &classic, &smart) &&
	                  SmartCallbackNegatives() && SmartPreNegatives();
	std::fprintf(stderr, "COLORKEY_PUBLIC_ENTRIES pass=%d classic=%d smart=%d callback_negatives=13\n",
	             pass, classic, smart);
	return pass && classic == 63 && smart == 63 ? 0 : 3;
}

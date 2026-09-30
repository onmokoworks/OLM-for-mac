// Real-SDK callback fixture for the independent legal Thin owner campaign.
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <vector>

#include "AE_Effect.h"
#include "AE_EffectCBSuites.h"
#include "AE_EffectSuites.h"
#include "SPBasic.h"

#include "../../mac/OLMColorKey/OLMColorKey.cpp"

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

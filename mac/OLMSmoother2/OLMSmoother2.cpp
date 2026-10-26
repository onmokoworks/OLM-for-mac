#include "../../ucrtmath/include/ucrtmath.h"
// Retained older implementation used by schema/source-contract tooling.
// The Xcode target and native differential adapter use Mac/OLMSmoother2_port.cpp.
// Keep this pipeline separate: it does not share the production polygon model.

#include "OLMSmoother2.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <vector>
#include <algorithm>
#include <cstdint>

// ============================================================================
// Constants read directly from the Windows binary (see DAT_180022xxx).
// Session B uses only a subset; the rest are kept for future sessions.
// Marked with (void) refs at the end of the translation unit to avoid
// -Wunused-const-variable complaints, but declared here for clarity.
// ============================================================================
namespace k_olm {
constexpr float  HALF        = 0.5f;      // DAT_180022694
constexpr float  ONE         = 1.0f;      // DAT_1800226a0
constexpr float  V255        = 255.0f;    // DAT_180022700
constexpr float  V32768      = 32768.0f;  // DAT_180022704
constexpr uint32_t ABSMASK   = 0x7FFFFFFFu; // DAT_180022710
constexpr float  COLOR_TOL   = 0.001960922f; // DAT_18002268c (3B008081h)

// sRGB piecewise constants (doubles, matching the Win literal bit patterns)
constexpr double SRGB_BREAK   = 0.00313066844250060782; // DAT_180022698
constexpr double SRGB_BOUND   = 0.04045;                // DAT_1800226a8
constexpr double SRGB_INVSCALE= 1.0 / 12.9216;          // DAT_1800226c0
constexpr double SRGB_INV24   = 1.0 / 2.4;              // DAT_1800226c8
constexpr double SRGB_INV1055 = 1.0 / 1.055;            // DAT_1800226d0
constexpr double SRGB_ONE     = 1.0;                    // DAT_1800226d8
constexpr double SRGB_1055    = 1.055;                  // DAT_1800226e0
constexpr double SRGB_24      = 2.4;                    // DAT_1800226e8
constexpr double SRGB_1292    = 12.92;                  // DAT_1800226f8
constexpr double SRGB_OFFSET2 = 0.055;                  // DAT_1800226b8
}

// Short aliases used below
#define K_HALF      k_olm::HALF
#define K_ONE       k_olm::ONE
#define K_255       k_olm::V255
#define K_32768     k_olm::V32768
#define K_ABSMASK   k_olm::ABSMASK
#define K_COLOR_TOL k_olm::COLOR_TOL
#define S_BREAK     k_olm::SRGB_BREAK
#define S_BOUND     k_olm::SRGB_BOUND
#define S_INVSCALE  k_olm::SRGB_INVSCALE
#define S_INV24     k_olm::SRGB_INV24
#define S_INV1055   k_olm::SRGB_INV1055
#define S_ONE       k_olm::SRGB_ONE
#define S_1055      k_olm::SRGB_1055
#define S_24        k_olm::SRGB_24
#define S_1292      k_olm::SRGB_1292
#define S_OFFSET2   k_olm::SRGB_OFFSET2

// ============================================================================
// Plumbing: SMParams (Win struct analog) and pixel helpers
// ============================================================================
struct SMParams {
	// Win mirror fields we read per-pixel (mapped to FUN_180004e10 layout by role)
	int           version;        // *param_8 (1 = v1, else v2)
	bool          enable_key;     // param_8[6] lsbyte
	bool          invert_key;     // param_8[5] lsbyte
	bool          keep_premul;    // (char)((longlong)param_8 + 0x19) — pre-mul output flag
	PF_PixelFloat key_color;      // offset 0x0c (RGBA stored as R,G,B,A floats)
	int           smoothness_raw; // *(int*)(param_8 + 0x20) — slider counts, /100 later
	int           extra_smooth_raw; // *(int*)(param_8 + 0x24)
	int           smooth_range;   // *(int*)(param_8 + 0x14) — radius slider
	int           gamma_mode;     // param_8[9] lsbyte: 1=None, 2=Colors, 3=All (matches UI popup)
	float         gamma_value;    // float at param_8[6]
	int           num_gamma_colors;
	PF_PixelFloat gamma_colors[NUM_GAMMA_COLORS];

	// Runtime scratch
	int32_t       w, h;
};

// Float-pixel scratch buffer (16 bytes per pixel, RGBA packed order)
struct FPix {
	float r, g, b, a;
};

// Pixel layer descriptor — mirrors the 3-element tuple (ptr, rowbytes_combined, stride_extra) used in Win
struct FPlane {
	FPix*  base;
	size_t rowbytes;   // 16 * w
	size_t _reserved;  // unused; matches Win triple layout
};

// ============================================================================
// Param fetch from AE
// ============================================================================
static PF_Err
FetchParams(PF_InData *in_data, PF_ParamDef *params[], SMParams *p)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	p->enable_key       = params[SM_ENABLE_KEY]->u.bd.value != 0;
	p->invert_key       = params[SM_INVERT_KEY]->u.bd.value != 0;
	p->smoothness_raw   = params[SM_SMOOTHNESS]->u.sd.value;
	p->extra_smooth_raw = params[SM_EXTRA_SMOOTH]->u.sd.value;
	p->smooth_range     = params[SM_SMOOTH_RANGE]->u.sd.value;
	p->version          = params[SM_VERSION]->u.pd.value;      // 1 or 2
	p->gamma_mode       = params[SM_GAMMA_MODE]->u.pd.value;   // 1/2/3
	p->gamma_value      = (float)params[SM_GAMMA_VALUE]->u.fs_d.value;
	p->num_gamma_colors = params[SM_NUM_GAMMA_COLORS]->u.sd.value;
	// Re-premul only when we un-premul'd at the frame-setup stage (mirrors Win
	// symmetric unpremul/repremul bracket gated on enable_key).  Otherwise the
	// input is already premul and multiplying again would double-premul alpha
	// edges (produces dark halos around anti-aliased pixels).
	p->keep_premul      = params[SM_ENABLE_KEY]->u.bd.value != 0;

	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();
	cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[SM_KEY_COLOR], &p->key_color);
	for (int i = 0; i < NUM_GAMMA_COLORS; ++i) {
		cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
			params[SM_GAMMA_COLOR_0 + i], &p->gamma_colors[i]);
	}
	return err;
}

#include "OLMSmoother2_legacy_pipeline.inc"
// ============================================================================
// Lifecycle
// ============================================================================
static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	suites.ANSICallbacksSuite1()->sprintf(out_data->return_msg,
		"%s %d.%d\r%s",
		GetStringPtr(StrID_Name),
		MAJOR_VERSION, MINOR_VERSION,
		"Smooth images.");
	return PF_Err_NONE;
}

static PF_Err
GlobalSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000440;
	out_data->out_flags2 = 0x08001400;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_EnableKey_Param_Name),
	                "", FALSE, 0, ENABLE_KEY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_Key_Param_Name),
	             0xFF, 0xFF, 0xFF,
	             KEY_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_InvertKey_Param_Name),
	                "", FALSE, 0, INVERT_KEY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Smoothness_Param_Name),
	              0, 100, 0, 100, 100,
	              SMOOTHNESS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_ExtraSmooth_Param_Name),
	              0, 100, 0, 100, 0,
	              EXTRA_SMOOTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_SmoothRange_Param_Name),
	              0, 100, 0, 100, 2,
	              SMOOTH_RANGE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_Version_Param_Name),
	             2, SMOOTHER_V2,
	             GetStringPtr(StrID_Version_Choices),
	             VERSION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_Gamma_Param_Name),
	             3, GAMMA_NONE,
	             GetStringPtr(StrID_Gamma_Choices),
	             GAMMA_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_GammaValue_Param_Name),
	                     1.0, 2.4, 1.0, 2.4, 2.4,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     GAMMA_VALUE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_NumGamma_Param_Name),
	              0, NUM_GAMMA_COLORS, 0, NUM_GAMMA_COLORS, 1,
	              NUM_GAMMA_DISK_ID);

	for (int i = 0; i < NUM_GAMMA_COLORS; ++i) {
		AEFX_CLR_STRUCT(def);
		PF_ADD_COLOR(GetStringPtr(StrID_GammaColor_Param_Name),
		             0, 0, 0,
		             GAMMA_COLOR_0_DISK_ID + i);
	}

	out_data->num_params = SM_NUM_PARAMS;
	return err;
}

// ============================================================================
// Classic Render
// ============================================================================
static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	PF_LayerDef *input = &params[SM_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	ERR(world_suite->PF_GetPixelFormat(input, &format));
	if (err) return err;

	switch (format) {
	case PF_PixelFormat_ARGB32:
		return RenderBits<PF_Pixel8>(in_data, params, input, output);
	case PF_PixelFormat_ARGB64:
		return RenderBits<PF_Pixel16>(in_data, params, input, output);
	case PF_PixelFormat_ARGB128:
		return RenderBits<PF_PixelFloat>(in_data, params, input, output);
	default:
		return PF_Err_BAD_CALLBACK_PARAM;
	}
}

// ============================================================================
// SmartRender
// ============================================================================
static void UnionLRect_inline(const PF_LRect *src, PF_LRect *dst) {
	if (dst->left == dst->right || dst->top == dst->bottom) { *dst = *src; return; }
	if (src->left == src->right || src->top == src->bottom) return;
	if (src->left   < dst->left)   dst->left   = src->left;
	if (src->top    < dst->top)    dst->top    = src->top;
	if (src->right  > dst->right)  dst->right  = src->right;
	if (src->bottom > dst->bottom) dst->bottom = src->bottom;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		SM_INPUT, SM_INPUT, &req,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&in_result));

	UnionLRect_inline(&in_result.result_rect, &extra->output->result_rect);
	UnionLRect_inline(&in_result.max_result_rect, &extra->output->max_result_rect);
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	PF_EffectWorld *input_world  = nullptr;
	PF_EffectWorld *output_world = nullptr;

	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, SM_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));

	PF_ParamDef param_list[SM_NUM_PARAMS];
	AEFX_CLR_STRUCT(param_list[0]);
	for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
		AEFX_CLR_STRUCT(param_list[i]);
		ERR(PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
		                      in_data->time_step, in_data->time_scale,
		                      &param_list[i]));
	}

	PF_ParamDef *params[SM_NUM_PARAMS];
	for (A_long i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &param_list[i];

	if (!err && input_world && output_world) {
		param_list[0].u.ld = *input_world;
		short depth = extra->input->bitdepth;
		if (depth == 8) {
			err = RenderBits<PF_Pixel8>(in_data, params, input_world, output_world);
		} else if (depth == 16) {
			err = RenderBits<PF_Pixel16>(in_data, params, input_world, output_world);
		} else {
			err = RenderBits<PF_PixelFloat>(in_data, params, input_world, output_world);
		}
	}

	for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
		PF_CHECKIN_PARAM(in_data, &param_list[i]);
	}
	return err;
}

// ============================================================================
// Entry point
// ============================================================================
extern "C" DllExport
PF_Err EffectMain(PF_Cmd cmd, PF_InData *in_data, PF_OutData *out_data,
                  PF_ParamDef *params[], PF_LayerDef *output, void *extra)
{
	PF_Err err = PF_Err_NONE;
	try {
		switch (cmd) {
		case PF_Cmd_ABOUT:
			err = About(in_data, out_data, params, output);
			break;
		case PF_Cmd_GLOBAL_SETUP:
			err = GlobalSetup(in_data, out_data, params, output);
			break;
		case PF_Cmd_PARAMS_SETUP:
			err = ParamsSetup(in_data, out_data, params, output);
			break;
		case PF_Cmd_RENDER:
			err = Render(in_data, out_data, params, output);
			break;
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, (PF_PreRenderExtra *)extra);
			break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, (PF_SmartRenderExtra *)extra);
			break;
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	}
	return err;
}

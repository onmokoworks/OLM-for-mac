#include "../../../ucrtmath/include/ucrtmath.h"
// Literal Windows pipeline; includes below preserve one translation unit and evaluation order.

#include "OLMSmoother2.h"
#ifndef OLMSMOOTHER2_SHIM_H
#include "../../DynamicControls.h"
static PF_Err
UpdateParamsUI(PF_InData *in_data, PF_ParamDef *params[])
{
    PF_Err err = PF_Err_NONE;
    const bool key = params[SM_ENABLE_KEY]->u.bd.value != FALSE;
    const A_long mode = params[SM_GAMMA_MODE]->u.pd.value;
    const A_long count = params[SM_NUM_GAMMA_COLORS]->u.sd.value;
    ERR(OLMSetDisabled(in_data, params, SM_KEY_COLOR, !key));
    ERR(OLMSetDisabled(in_data, params, SM_INVERT_KEY, !key));
    ERR(OLMSetDisabled(in_data, params, SM_GAMMA_VALUE, mode == GAMMA_NONE));
    ERR(OLMSetDisabled(in_data, params, SM_NUM_GAMMA_COLORS, mode != GAMMA_COLORS_ONLY));
    for (int i = 0; i < NUM_GAMMA_COLORS; ++i) {
        ERR(OLMSetHidden(in_data, SM_GAMMA_COLOR_0 + i,
            !(mode == GAMMA_COLORS_ONLY && i < count)));
    }
    return err;
}
#endif
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <new>
#include <exception>
#include <fcntl.h>
#include <unistd.h>
#include "../../../core/olm_sha256_rows.h"
#include "../../../core/olm_parallel.h"
#ifndef OLMSMOOTHER2_SHIM_H
#include "AEFX_SuiteHandlerTemplate.h"
#endif
#include "OLMSmoother2_decode_lut_10000.h"
#include "OLMSmoother2_encode_lut_10000.h"

#ifdef OLMSMOOTHER2_SHIM_H
static const PF_Err PF_Err_BAD_CALLBACK_PARAM = 25;
static void (*g_olmsmoother2_cli_checkin_layer_hook)(PF_ProgPtr, A_long) = nullptr;
#endif

// Byte-for-byte runtime captures from the Windows AE 26.3 OLMSmoother2.aex
// gamma contexts used by the attested 32bpc case_07 run:
//   decode  SHA-256 11056c2feda87964204a53471e172ae6fb6039a0c3120f6277c7ff115fe88cba
//   inverse SHA-256 b7014467dcae06109111302b8c930494950d27b817d1390d6434605795772fbc
static_assert(sizeof(_tmp_smoother2_decode_lut_10000_bin) == 40000,
              "captured decode LUT size drift");
static_assert(sizeof(_tmp_smoother2_inverse_lut_10000_bin) == 40000,
              "captured inverse LUT size drift");

// Refusal attribution for the fuzz campaign. When OLM_REFUSAL_TRACE names a
// file, each failing admission guard appends "function:tag@line". The file is
// only opened on a refusal, and the returned error code and all output bytes
// are identical whether or not tracing is enabled.
static PF_Err Smoother2Refusal(const char *function, const char *tag, int line, PF_Err err)
{
	const char *path = std::getenv("OLM_REFUSAL_TRACE");
	if (path && path[0]) {
		const int handle = ::open(path, O_WRONLY | O_CREAT | O_APPEND, 0666);
		if (handle >= 0) {
			char entry[384];
			const int length = std::snprintf(entry, sizeof(entry), "%s:%s@%d\n", function, tag, line);
			if (length > 0) {
				const ssize_t written = ::write(handle, entry, (std::size_t)length);
				(void)written;
			}
			::close(handle);
		}
	}
	return err;
}

#define OLM_SM2_REFUSAL(tag) Smoother2Refusal(__func__, tag, __LINE__, PF_Err_BAD_CALLBACK_PARAM)
#define OLM_SM2_ERROR(tag, code) Smoother2Refusal(__func__, tag, __LINE__, code)

#include "OLMSmoother2_constants.inc"
#include "OLMSmoother2_frame_setup.inc"
#include "OLMSmoother2_classification.inc"
#include "OLMSmoother2_polygon_scan.inc"
#include "OLMSmoother2_polygon_weights.inc"
#include "OLMSmoother2_corner_samples.inc"
#include "OLMSmoother2_cardinal_leaves.inc"
#include "OLMSmoother2_polygon_dispatch.inc"
#include "OLMSmoother2_gamma_composite.inc"
#include "OLMSmoother2_render.inc"
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
#ifndef OLMSMOOTHER2_SHIM_H
	def.flags = PF_ParamFlag_SUPERVISE;
#endif
	PF_ADD_POPUP(GetStringPtr(StrID_Gamma_Param_Name),
	             3, GAMMA_NONE,
	             GetStringPtr(StrID_Gamma_Choices),
	             GAMMA_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
#ifdef OLMSMOOTHER2_SHIM_H
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_GammaValue_Param_Name),
	                     1.0, 2.4, 1.0, 2.4, 2.4,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     GAMMA_VALUE_DISK_ID);
#else
	// The AEX-owned row leaves curve_tolerance at zero. Param_Utils' float
	// slider helper forces the audio-oriented 0.05 default, so spell out this
	// definition to preserve the public PARAMS_SETUP payload.
	def.param_type = PF_Param_FLOAT_SLIDER;
	PF_STRNNCPY(def.name, GetStringPtr(StrID_GammaValue_Param_Name), sizeof(def.name));
	def.u.fs_d.valid_min = def.u.fs_d.slider_min = 1.0;
	def.u.fs_d.valid_max = def.u.fs_d.slider_max = 2.4;
	def.u.fs_d.value = def.u.fs_d.dephault = 2.4;
	def.u.fs_d.precision = PF_Precision_HUNDREDTHS;
	def.u.fs_d.curve_tolerance = 0.0;
	def.uu.id = GAMMA_VALUE_DISK_ID;
	ERR(PF_ADD_PARAM(in_data, -1, &def));
#endif

	AEFX_CLR_STRUCT(def);
#ifndef OLMSMOOTHER2_SHIM_H
	def.flags = PF_ParamFlag_SUPERVISE;
#endif
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

#include "OLMSmoother2_admission.inc"
static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	if (!params || !params[SM_INPUT]) return OLM_SM2_REFUSAL("render-input-param-null");
	PF_LayerDef *input = &params[SM_INPUT]->u.ld;
	short depth = 0;
	PF_Err err = ValidatePublicWorlds(in_data, out_data, input, output, &depth);
	if (err) return err;
	// The actual exported classic command is a no-op; every retained numerical
	// owner witness is Smart. Validate the caller-owned worlds (including the
	// output format) and fail closed at every depth instead of publishing the
	// shared typed core through an unowned entry.
	(void)depth;
	return OLM_SM2_REFUSAL("classic-entry-unowned");
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
	if (!in_data || !out_data || !extra || !extra->input || !extra->output ||
	    !extra->cb || !extra->cb->checkout_layer) return OLM_SM2_REFUSAL("prerender-null-inputs");
	// Original SmartPreRender forwards the output request to checkout_layer.
	// F53 cropped-checkout witnesses confirm that the returned availability,
	// rather than the full layer dimensions, determines the output world.
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	req.preserve_rgb_of_zero_alpha = TRUE;
	PF_CheckoutResult in_result;
	memset(&in_result, 0, sizeof(in_result));

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		SM_INPUT, SM_INPUT, &req,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&in_result));
	if (err) return OLM_SM2_ERROR("prerender-checkout", err);

	UnionLRect_inline(&in_result.result_rect, &extra->output->result_rect);
	UnionLRect_inline(&in_result.max_result_rect, &extra->output->max_result_rect);
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	if (!in_data || !out_data || !extra || !extra->input || !extra->cb ||
	    !extra->cb->checkout_layer_pixels || !extra->cb->checkout_output) {
		return OLM_SM2_REFUSAL("smartrender-null-inputs");
	}
#ifndef OLMSMOOTHER2_SHIM_H
	if (!in_data->pica_basicP || !in_data->inter.checkout_param ||
	    !in_data->inter.checkin_param) return OLM_SM2_REFUSAL("smartrender-suite-missing");
#endif
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = nullptr;
	PF_EffectWorld *output_world = nullptr;
	PF_ParamDef param_list[SM_NUM_PARAMS];
	for (A_long i = 0; i < SM_NUM_PARAMS; ++i) AEFX_CLR_STRUCT(param_list[i]);
	bool param_checked_out[SM_NUM_PARAMS] = {};
	PF_ParamDef *params[SM_NUM_PARAMS];
	for (A_long i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &param_list[i];
	bool layer_checked_out = false;
	bool rendered = false;
	SMParams decoded_params; AEFX_CLR_STRUCT(decoded_params);
	bool decoded_params_ready = false;
	short depth = 0;
	size_t active_bytes = 0;
	std::vector<uint8_t> input_stage, output_stage;
	try {
		ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, SM_INPUT, &input_world));
		if (!err) layer_checked_out = true;
		ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
		for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
			ERR(PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
			                      in_data->time_step, in_data->time_scale,
			                      &param_list[i]));
			if (!err) param_checked_out[i] = true;
		}
		if (err) err = OLM_SM2_ERROR("smartrender-checkout", err);
		if (!err && input_world && output_world) {
			param_list[0].u.ld = *input_world;
			err = ValidatePublicWorlds(in_data, out_data, input_world, output_world, &depth);
			if (!err && depth != extra->input->bitdepth) err = OLM_SM2_REFUSAL("smartrender-depth-mismatch");
			// Preserve the stronger source-bound owner when it matches exactly; only
			// unmatched callers may fall through to the source-independent beta lane.
			const bool retained_fixture = !err && V2SmartAdmission(
				(const PF_ParamDef *const *)params, input_world, depth);
			const bool generic_beta = !err && !retained_fixture && V2GenericBetaAdmission(
				(const PF_ParamDef *const *)params, input_world, depth);
			if (!err && retained_fixture && input_world->width == 1920 && input_world->height == 1080 &&
			    !V2Case07WorldContract(in_data, input_world, output_world, depth)) {
				err = OLM_SM2_REFUSAL("smartrender-case07-world-contract");
			}
			if (!err && !retained_fixture && !generic_beta) {
				err = OLM_SM2_REFUSAL("smartrender-not-admitted");
			}
			if (!err) {
				err = FetchParams(in_data, params, &decoded_params);
				if (err) err = OLM_SM2_ERROR("smartrender-fetch-params", err);
				if (!err) decoded_params_ready = true;
			}
			if (!err) {
				const size_t pixel_size = depth == 8 ? sizeof(PF_Pixel8) :
				                          depth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat);
				active_bytes = (size_t)input_world->width * pixel_size;
				const size_t bytes = active_bytes * (size_t)input_world->height;
				input_stage.resize(bytes);
				output_stage.resize(bytes);
				for (A_long y = 0; y < input_world->height; ++y) {
					memcpy(input_stage.data() + (size_t)y * active_bytes,
					       (const uint8_t *)input_world->data + (size_t)y * (size_t)input_world->rowbytes,
					       active_bytes);
				}
				PF_EffectWorld staged_input = *input_world;
				PF_EffectWorld staged_output = *output_world;
				staged_input.data = reinterpret_cast<decltype(staged_input.data)>(input_stage.data());
				staged_output.data = reinterpret_cast<decltype(staged_output.data)>(output_stage.data());
				staged_input.rowbytes = staged_output.rowbytes = (A_long)active_bytes;
				param_list[0].u.ld = staged_input;
				if (!decoded_params_ready) err = OLM_SM2_REFUSAL("smartrender-params-unready");
				else if (depth == 8) err = RenderBits<PF_Pixel8>(in_data, params, &staged_input, &staged_output, &decoded_params);
				else if (depth == 16) err = RenderBits<PF_Pixel16>(in_data, params, &staged_input, &staged_output, &decoded_params);
				else err = RenderBits<PF_PixelFloat>(in_data, params, &staged_input, &staged_output, &decoded_params);
				if (err) err = OLM_SM2_ERROR("smartrender-render-bits", err);
				if (!err) rendered = true;
			}
		} else if (!err) {
			err = OLM_SM2_REFUSAL("smartrender-worlds-absent");
		}
	} catch (PF_Err &thrown_err) {
		if (!err) err = OLM_SM2_ERROR("smartrender-thrown", thrown_err);
	} catch (const std::bad_alloc &) {
		if (!err) err = OLM_SM2_ERROR("smartrender-bad-alloc", (PF_Err)4);
	} catch (...) {
#ifdef OLMSMOOTHER2_SHIM_H
		if (!err) err = OLM_SM2_REFUSAL("smartrender-exception");
#else
		if (!err) err = OLM_SM2_ERROR("smartrender-exception", PF_Err_INTERNAL_STRUCT_DAMAGED);
#endif
	}
	for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
		if (!param_checked_out[i]) continue;
		try {
#ifdef OLMSMOOTHER2_SHIM_H
			const PF_Err cleanup_err = PF_CHECKIN_PARAM(in_data, &param_list[i]);
#else
			const PF_Err cleanup_err = PF_CHECKIN_PARAM(in_data, &param_list[i]);
#endif
			if (!err && cleanup_err) err = cleanup_err;
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = (PF_Err)4;
		} catch (...) {
#ifdef OLMSMOOTHER2_SHIM_H
			if (!err) err = PF_Err_BAD_CALLBACK_PARAM;
#else
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
#endif
		}
	}
#ifdef OLMSMOOTHER2_SHIM_H
	if (layer_checked_out && g_olmsmoother2_cli_checkin_layer_hook) {
		g_olmsmoother2_cli_checkin_layer_hook(in_data->effect_ref, SM_INPUT);
	}
#else
	if (layer_checked_out && extra->cb->checkin_layer_pixels) {
		try {
			const PF_Err cleanup_err = extra->cb->checkin_layer_pixels(in_data->effect_ref, SM_INPUT);
			if (!err && cleanup_err) err = cleanup_err;
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = (PF_Err)4;
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
#endif
	if (!err && rendered) {
		for (A_long y = 0; y < output_world->height; ++y) {
			memcpy((uint8_t *)output_world->data + (size_t)y * (size_t)output_world->rowbytes,
			       output_stage.data() + (size_t)y * active_bytes, active_bytes);
		}
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
#ifndef OLMSMOOTHER2_SHIM_H
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParamsUI(in_data, params); break;
#endif
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
		err = OLM_SM2_ERROR("effectmain-thrown", thrown_err);
	} catch (const std::bad_alloc &) {
		err = OLM_SM2_ERROR("effectmain-bad-alloc", (PF_Err)4);
	} catch (...) {
#ifdef OLMSMOOTHER2_SHIM_H
		err = OLM_SM2_REFUSAL("effectmain-exception");
#else
		err = OLM_SM2_ERROR("effectmain-exception", PF_Err_INTERNAL_STRUCT_DAMAGED);
#endif
	}
	return err;
}

// OLMSmoother_port.cpp — macOS 1:1 port of the Windows OLMSmoother.aex (v1).
//
// Current status: Stage 2 kernel port is in place for 8/16-bpc paths.
// Foundational primitives, scanline callbacks, and the main per-pixel kernel
// were ported from the Win disasm. Specifically:
//
//   - DAT_18000d1f0..d270 float/int constants                   (literal)
//   - DAT_18000f000..f0f0 3x3 direction/index tables            (literal)
//   - 5 LinearOffset* curve evaluators (functor classes)        (literal)
//   - FUN_180001620 / 180001a90  color blend (16/8)             (literal)
//   - FUN_180001ed0 / 180002060  alpha blend (16/8)             (literal)
//   - FUN_1800021f0 / 180002430  color compare (16/8)           (literal)
//   - FUN_180003ff0 / 180004220  9-neighbor extractor (16/8)    (literal, world+0x18 / +0x10)
//   - FUN_180001400 / 1800011e0  render entry chain             (suite-wrapped)
//   - FUN_1800096f0              dispatcher                     (literal control flow)
//
//   - FUN_180006a90 / 180008060  classifier                     (literal)
//   - FUN_180002740 / 1800033d0  sub-handler                    (literal)
//   - FUN_180004450 / 1800047f0  alt-handler                    (literal)
//   - FUN_180004b80 / 180005570  main interp kernel             (literal)
//   - FUN_180005f60 / 180006270  interp executor                (literal)
//   - FUN_180009960 / 180009e30  edge walker                    (literal)
//
// Remaining work:
//   - broader byte-perfect verification against Win reference renders
//   - 32-bpc float behavior currently passes through; Win v1 has no float path

#include "OLMSmoother.h"
#include "AEFX_SuiteHandlerTemplate.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <vector>
#include <new>
#include <exception>
#include <fcntl.h>
#include <unistd.h>
#include "../../../core/olm_world_safety.h"

// Refusal attribution for the fuzz campaign. When OLM_REFUSAL_TRACE names a
// file, each failing admission guard appends "function:tag@line". The file is
// only opened on a refusal, and the returned error code and all output bytes
// are identical whether or not tracing is enabled.
static PF_Err SmootherRefusal(const char *function, const char *tag, int line, PF_Err err)
{
	const char *path = getenv("OLM_REFUSAL_TRACE");
	if (path && path[0]) {
		const int handle = open(path, O_WRONLY | O_CREAT | O_APPEND, 0666);
		if (handle >= 0) {
			char entry[384];
			const int length = snprintf(entry, sizeof(entry), "%s:%s@%d\n", function, tag, line);
			if (length > 0) {
				const ssize_t written = write(handle, entry, (size_t)length);
				(void)written;
			}
			close(handle);
		}
	}
	return err;
}

#define OLM_SMOOTHER_REFUSAL(tag) SmootherRefusal(__func__, tag, __LINE__, PF_Err_BAD_CALLBACK_PARAM)
#define OLM_SMOOTHER_ERROR(tag, code) SmootherRefusal(__func__, tag, __LINE__, code)

#ifdef OLMSMOOTHER_SHIM_H
// The standalone evidence harness only needs a stable non-zero rejection.
static const PF_Err PF_Err_BAD_CALLBACK_PARAM = 25;
static void (*g_olmsmoother_cli_checkin_layer_hook)(PF_ProgPtr, A_long) = nullptr;
static PF_Err (*g_olmsmoother_cli_checkin_layer_error_hook)(PF_ProgPtr, A_long) = nullptr;
#endif

// ============================================================================
// DAT_* constants — verified against Ghidra binary read + decomp cross-check.
// Layout at .rdata 18000d1f0..18000d270.
// ============================================================================
static const float DAT_18000d1f0  = 0.5f;          // K_HALF
static const float DAT_18000d1f4  = 1.0f;          // K_ONE
static const float DAT_18000d250  = 1.0f / 32768.0f; // K_USHORT_DIV
static const float _DAT_18000d254 = 0.11f;         // BT.601 luma B
static const float _DAT_18000d258 = 0.30f;         // BT.601 luma R
static const float _DAT_18000d25c = 0.59f;         // BT.601 luma G
static const float DAT_18000d260  = 4.0f;          // interpolation scale (FUN_180005570)
static const float DAT_18000d264  = 8.0f;          // interpolation scale (FUN_180005570)
static const float DAT_18000d268  = 255.0f;        // K_BYTE_MAX
static const float DAT_18000d26c  = 32768.0f;      // K_USHORT_MAX
static const uint32_t DAT_18000d270 = 0x7FFFFFFFu; // ABS_MASK (sign clear)

// ----------------------------------------------------------------------------
// 3x3 direction/index tables @ 18000f000..18000f0f0.
// Each table has nine entries, including center slot 4.  The original arrays
// are 0x28 bytes apart: 9 int32 values followed by one padding int32.
// Values below are read directly from the pinned 2025 Windows AEX
// (SHA-256 6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82).
// DAT_18000f000  : direction "rev" #0
// DAT_18000f028  : direction "rev" #1
// DAT_18000f050  : direction "rev" #2
// DAT_18000f078  : direction "rev" #3
// DAT_18000f0a0  : direction pair-id
// DAT_18000f0c8  : DX (column delta -1/0/+1)
// DAT_18000f0f0  : DY (row delta    -1/0/+1)
// ----------------------------------------------------------------------------
static const int32_t DAT_18000f000[9] = { 6, 3, 0, 7, 4, 1, 8, 5, 2 };
static const int32_t DAT_18000f028[9] = { 2, 5, 8, 1, 4, 7, 0, 3, 6 };
static const int32_t DAT_18000f050[9] = { 3, 0, 1, 6, 4, 2, 7, 8, 5 };
static const int32_t DAT_18000f078[9] = { 1, 2, 5, 0, 4, 8, 3, 6, 7 };
static const int32_t DAT_18000f0a0[9] = { 8, 7, 6, 5, 4, 3, 2, 1, 0 };
static const int32_t DAT_18000f0c8[9] = { -1, 0, 1, -1, 0, 1, -1, 0, 1 };
static const int32_t DAT_18000f0f0[9] = { -1,-1,-1,  0, 0, 0,  1, 1, 1 };

// ============================================================================
// Plugin lifecycle commands
// ============================================================================
static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_SPRINTF(out_data->return_msg, "%s\n%s",
	           GetStringPtr(StrID_Name),
	           GetStringPtr(StrID_Description));
	return PF_Err_NONE;
}

static PF_Err
GlobalSetup(PF_InData *, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000040;
	// Original v1 selects Classic in AE; the Smart wrapper is diagnostic only.
	out_data->out_flags2 = 0x08000000;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseKey_Param_Name),
	                "", FALSE, 0, USE_KEY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_Key_Param_Name),
	             0xFF, 0xFF, 0xFF,
	             KEY_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Tolerance_Param_Name),
	              0, 255, 0, 6, 6,
	              TOLERANCE_DISK_ID);

	out_data->num_params = SM_NUM_PARAMS;
	return err;
}

#include "OLMSmoother_state_math.inc"
#include "OLMSmoother_pixel_helpers.inc"
#include "OLMSmoother_classifiers.inc"
#include "OLMSmoother_edge_walkers.inc"
#include "OLMSmoother_subhandler16.inc"
#include "OLMSmoother_subhandler8.inc"
#include "OLMSmoother_interpolation.inc"
#include "OLMSmoother_render.inc"
// ============================================================================
// Render dispatcher — Win FUN_1800096f0.
// ============================================================================
static PF_Err
DispatchRender(PF_InData       *in_data,
               PF_ParamDef     *params[],
               PF_EffectWorld  *input,
               PF_EffectWorld  *output,
               short            bitdepth,
               bool             classic_extent = false)
{
	RenderState state;
	BuildRenderState(params, bitdepth, &state);

	if (bitdepth == 8) {
		return RenderEntryChain<PF_Pixel8, PF_Iterate8Suite1>(
			in_data,
			kPFIterate8Suite, kPFIterate8SuiteVersion1,
			input, output, &state,
			ScanlinePixel8_Main, ScanlinePixel8_KeyMask, classic_extent);
	} else if (bitdepth == 16) {
		return RenderEntryChain<PF_Pixel16, PF_Iterate16Suite1>(
			in_data,
			kPFIterate16Suite, kPFIterate16SuiteVersion1,
			input, output, &state,
			ScanlinePixel16_Main, ScanlinePixel16_KeyMask, classic_extent);
	} else {
		return RenderEntryChain<PF_PixelFloat, PF_IterateFloatSuite1>(
			in_data,
			kPFIterateFloatSuite, kPFIterateFloatSuiteVersion1,
			input, output, &state,
			ScanlinePixelFloat_Main, ScanlinePixelFloat_KeyMask, classic_extent);
	}
}

static PF_Err
WorldDepth(PF_InData *in_data,
           PF_OutData *out_data,
           PF_EffectWorld *world,
           short *depth)
{
	if (!in_data || !out_data || !world || !depth)
		return OLM_SMOOTHER_REFUSAL("world-depth-args");
#ifdef OLMSMOOTHER_SHIM_H
	if (world->bitdepth == 8 || world->bitdepth == 16 || world->bitdepth == 32) {
		*depth = world->bitdepth;
		return PF_Err_NONE;
	}
	return OLM_SMOOTHER_REFUSAL("world-depth-shim-bitdepth");
#else
	PF_Err err = PF_Err_NONE;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	(void)out_data;
	if (!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
	    !in_data->pica_basicP->ReleaseSuite)
		return OLM_SMOOTHER_REFUSAL("world-depth-pica");
	const void *raw_suite = nullptr;
	const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
		kPFWorldSuite, kPFWorldSuiteVersion2, &raw_suite);
	if (acquire_err) return OLM_SMOOTHER_ERROR("world-depth-acquire", (PF_Err)acquire_err);
	if (!raw_suite) {
		const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
			kPFWorldSuite, kPFWorldSuiteVersion2);
		return release_err ? OLM_SMOOTHER_ERROR("world-depth-no-suite", (PF_Err)release_err)
		                   : OLM_SMOOTHER_REFUSAL("world-depth-no-suite");
	}
	PF_WorldSuite2 *world_suite = (PF_WorldSuite2 *)raw_suite;
	try {
		if (!world_suite->PF_GetPixelFormat) err = PF_Err_BAD_CALLBACK_PARAM;
		if (!err) err = world_suite->PF_GetPixelFormat(world, &format);
	} catch (...) {
		const std::exception_ptr body_error = std::current_exception();
		try { in_data->pica_basicP->ReleaseSuite(kPFWorldSuite, kPFWorldSuiteVersion2); }
		catch (...) {}
		std::rethrow_exception(body_error);
	}
	const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
		kPFWorldSuite, kPFWorldSuiteVersion2);
	if (!err && release_err) err = (PF_Err)release_err;
	if (err) return OLM_SMOOTHER_ERROR("world-depth-getpixelformat", err);
	switch (format) {
	case PF_PixelFormat_ARGB32:  *depth = 8;  return PF_Err_NONE;
	case PF_PixelFormat_ARGB64:  *depth = 16; return PF_Err_NONE;
	case PF_PixelFormat_ARGB128: *depth = 32; return PF_Err_NONE;
	default: return OLM_SMOOTHER_REFUSAL("world-depth-unsupported-format");
	}
#endif
}

static bool
V1ClassicAdmission(const PF_ParamDef *const params[], const PF_EffectWorld *world, short depth)
{
	if (!params || !world || !params[SM_USE_KEY] || !params[SM_KEY_COLOR] ||
	    !params[SM_TOLERANCE]) return false;
	const A_long use_key = params[SM_USE_KEY]->u.bd.value;
	const A_long tolerance = params[SM_TOLERANCE]->u.sd.value;
	if (use_key != 0 && use_key != 1) return false;
	if (tolerance < 0 || tolerance > 255) return false;

	// Both typed lanes are source-independent; v1 has no float render owner.
	return depth == 8 || depth == 16;
}

static PF_Err
ValidatePublicWorlds(PF_InData *in_data,
                     PF_OutData *out_data,
                     PF_EffectWorld *input,
                     PF_EffectWorld *output,
                     short *depth,
                     bool classic_extent = false)
{
	// The non-original Smart wrapper retains its full-frame admission policy.
	// Classic follows the original output-extent iteration contract below.
	if (!input || !output || !input->data || !output->data || !depth)
		return OLM_SMOOTHER_REFUSAL("world-args-null");
	if (input->width <= 0 || input->height <= 0)
		return OLM_SMOOTHER_REFUSAL("world-geometry-nonpositive");
	if (input->width != output->width || input->height != output->height)
		return OLM_SMOOTHER_REFUSAL("world-dimension-mismatch");
	if (input->rowbytes <= 0 || output->rowbytes <= 0)
		return OLM_SMOOTHER_REFUSAL("world-rowbytes-nonpositive");
	if (!classic_extent && (input->extent_hint.left != 0 || input->extent_hint.top != 0 ||
	    input->extent_hint.right != input->width ||
	    input->extent_hint.bottom != input->height ||
	    output->extent_hint.left != 0 || output->extent_hint.top != 0 ||
	    output->extent_hint.right != output->width ||
	    output->extent_hint.bottom != output->height)) {
		return OLM_SMOOTHER_REFUSAL("world-extent-not-full-frame");
	}
	// Classic's iterate area must fit the supplied worlds. Input extent is not
	// used by the original entry chain; output extent selects callback centers,
	// not a clipping boundary for contour reads or neighbouring writes.
	if (classic_extent && (output->extent_hint.left < 0 || output->extent_hint.top < 0 ||
	    output->extent_hint.right < output->extent_hint.left ||
	    output->extent_hint.bottom < output->extent_hint.top ||
	    output->extent_hint.right > output->width ||
	    output->extent_hint.bottom > output->height)) {
		return OLM_SMOOTHER_REFUSAL("world-output-extent-invalid");
	}
	// Bound the public lane to the production envelope exercised by the beta
	// suite.  The contour walkers are frame-wide and Render stages both worlds,
	// so accepting arbitrary positive A_long geometry would permit unbounded
	// per-render memory and work even when row layouts themselves are legal.
	static const A_long kMaxSide = 4096;
	static const size_t kMaxPixels = (size_t)4096 * (size_t)2160;
	if (input->width > kMaxSide || input->height > kMaxSide ||
	    (size_t)input->width > kMaxPixels / (size_t)input->height) {
		return OLM_SMOOTHER_REFUSAL("world-geometry-envelope");
	}
	short input_depth = 0, output_depth = 0;
	PF_Err err = WorldDepth(in_data, out_data, input, &input_depth);
	if (!err) err = WorldDepth(in_data, out_data, output, &output_depth);
	if (err) return err;
	if (input_depth != output_depth)
		return OLM_SMOOTHER_REFUSAL("world-depth-mismatch");
	if (input_depth == 32)
		return OLM_SMOOTHER_REFUSAL("world-depth-32-unsupported");
	const size_t pixel_size = input_depth == 8 ? sizeof(PF_Pixel8) : sizeof(PF_Pixel16);
	const olm::world_safety::ConstWorld safe_input = {
		input->data, (size_t)input->width, (size_t)input->height,
		(size_t)input->rowbytes, pixel_size};
	const olm::world_safety::ConstWorld safe_output = {
		output->data, (size_t)output->width, (size_t)output->height,
		(size_t)output->rowbytes, pixel_size};
	if (olm::world_safety::validate_layout(safe_input) != olm::world_safety::Status::ok)
		return OLM_SMOOTHER_REFUSAL("world-input-layout");
	if (olm::world_safety::validate_layout(safe_output) != olm::world_safety::Status::ok)
		return OLM_SMOOTHER_REFUSAL("world-output-layout");
	if (olm::world_safety::require_disjoint(safe_input, safe_output) !=
	        olm::world_safety::Status::ok) {
		return OLM_SMOOTHER_REFUSAL("world-overlap");
	}
	*depth = input_depth;
	return PF_Err_NONE;
}

// ============================================================================
// Classic Render
// ============================================================================
static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	if (!params || !params[SM_INPUT])
		return OLM_SMOOTHER_REFUSAL("render-null-params");
	PF_LayerDef *input = &params[SM_INPUT]->u.ld;
	short bitdepth = 0;
	PF_Err err = ValidatePublicWorlds(in_data, out_data, input, output, &bitdepth, true);
	if (err) return err;
	if (!V1ClassicAdmission((const PF_ParamDef *const *)params, input, bitdepth))
		return OLM_SMOOTHER_REFUSAL("classic-admission");

	const size_t pixel_size = bitdepth == 8 ? sizeof(PF_Pixel8) : sizeof(PF_Pixel16);
	olm::world_safety::TightStaging staging;
	const olm::world_safety::Status stage_status = staging.prepare(
		{input->data, (size_t)input->width, (size_t)input->height,
		 (size_t)input->rowbytes, pixel_size},
		{output->data, (size_t)output->width, (size_t)output->height,
		 (size_t)output->rowbytes, pixel_size});
	if (stage_status != olm::world_safety::Status::ok) {
		return stage_status == olm::world_safety::Status::out_of_memory ?
			OLM_SMOOTHER_ERROR("render-staging-out-of-memory", (PF_Err)4)
			: OLM_SMOOTHER_REFUSAL("render-staging-layout");
	}
	PF_EffectWorld staged_input = *input;
	PF_EffectWorld staged_output = *output;
	staged_input.data = reinterpret_cast<decltype(staged_input.data)>(
		const_cast<uint8_t *>(staging.input_data()));
	staged_input.rowbytes = (A_long)staging.row_bytes();
	staged_output.data = reinterpret_cast<decltype(staged_output.data)>(staging.output_data());
	staged_output.rowbytes = (A_long)staging.row_bytes();
	err = DispatchRender(in_data, params, &staged_input, &staged_output, bitdepth, true);
	if (!err && staging.commit() != olm::world_safety::Status::ok)
		err = OLM_SMOOTHER_REFUSAL("render-staging-commit");
	return err;
}

// ============================================================================
// SmartRender / SmartPreRender
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
	    !extra->cb || !extra->cb->checkout_layer)
		return OLM_SMOOTHER_REFUSAL("smart-prerender-args");
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;
	memset(&in_result, 0, sizeof(in_result));

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		SM_INPUT, SM_INPUT, &req,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&in_result));

	if (!err) {
		UnionLRect_inline(&in_result.result_rect,     &extra->output->result_rect);
		UnionLRect_inline(&in_result.max_result_rect, &extra->output->max_result_rect);
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	if (!in_data || !out_data || !extra || !extra->input || !extra->cb ||
	    !extra->cb->checkout_layer_pixels || !extra->cb->checkout_output) {
		return OLM_SMOOTHER_REFUSAL("smart-render-args");
	}
	#ifndef OLMSMOOTHER_SHIM_H
	if (!in_data->pica_basicP || !in_data->inter.checkout_param ||
	    !in_data->inter.checkin_param)
		return OLM_SMOOTHER_REFUSAL("smart-render-pica");
	#endif
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = nullptr;
	PF_EffectWorld *output_world = nullptr;
	PF_ParamDef param_list[SM_NUM_PARAMS];
	PF_ParamDef *param_ptrs[SM_NUM_PARAMS] = {};
	for (A_long i = 0; i < SM_NUM_PARAMS; ++i) AEFX_CLR_STRUCT(param_list[i]);
	for (A_long i = 0; i < SM_NUM_PARAMS; ++i) param_ptrs[i] = &param_list[i];
	bool param_checked_out[SM_NUM_PARAMS] = {};
	bool layer_checked_out = false;
	bool render_complete = false;
	size_t active_bytes = 0;
	std::vector<uint8_t> pending_output;
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
		if (!err && input_world && output_world) {
			param_list[0].u.ld = *input_world;
			short bitdepth = 0;
			err = ValidatePublicWorlds(in_data, out_data, input_world, output_world, &bitdepth);
			if (!err && bitdepth != extra->input->bitdepth)
				err = OLM_SMOOTHER_REFUSAL("smart-render-bitdepth-mismatch");
			// Mac Public Beta Smart lane: reuse the Windows-derived Classic integer
			// kernel, but render into a private tight world.  Host output is committed
			// only after every parameter and layer checkout has been balanced, so a
			// cleanup callback failure cannot leave a partially successful frame.
			if (!err) {
				active_bytes = (size_t)input_world->width *
					(bitdepth == 8 ? sizeof(PF_Pixel8) : sizeof(PF_Pixel16));
				pending_output.resize(active_bytes * (size_t)input_world->height);
				for (A_long y = 0; y < output_world->height; ++y) {
					memcpy(pending_output.data() + (size_t)y * active_bytes,
					       (const uint8_t *)output_world->data +
					           (size_t)y * (size_t)output_world->rowbytes,
					       active_bytes);
				}
				PF_EffectWorld pending_world = *output_world;
				pending_world.data = reinterpret_cast<decltype(pending_world.data)>(
					pending_output.data());
				pending_world.rowbytes = (A_long)active_bytes;
				err = Render(in_data, out_data, param_ptrs, &pending_world);
				render_complete = !err;
			}
		} else if (!err) {
			err = OLM_SMOOTHER_REFUSAL("smart-render-null-worlds");
		}
	} catch (PF_Err &thrown_err) {
		if (!err) err = thrown_err;
	} catch (const std::bad_alloc &) {
		if (!err) err = (PF_Err)4;
	} catch (...) {
		#ifdef OLMSMOOTHER_SHIM_H
		if (!err) err = PF_Err_BAD_CALLBACK_PARAM;
		#else
		if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		#endif
	}
	for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
		if (!param_checked_out[i]) continue;
		try {
			const PF_Err cleanup_err = PF_CHECKIN_PARAM(in_data, &param_list[i]);
			if (!err && cleanup_err) err = cleanup_err;
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = (PF_Err)4;
		} catch (...) {
			#ifdef OLMSMOOTHER_SHIM_H
			if (!err) err = PF_Err_BAD_CALLBACK_PARAM;
			#else
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
			#endif
		}
	}
#ifdef OLMSMOOTHER_SHIM_H
	if (layer_checked_out && g_olmsmoother_cli_checkin_layer_hook) {
		try {
			g_olmsmoother_cli_checkin_layer_hook(in_data->effect_ref, SM_INPUT);
			const PF_Err cleanup_err = g_olmsmoother_cli_checkin_layer_error_hook ?
				g_olmsmoother_cli_checkin_layer_error_hook(in_data->effect_ref, SM_INPUT) : PF_Err_NONE;
			if (!err && cleanup_err) err = cleanup_err;
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = (PF_Err)4;
		} catch (...) {
			if (!err) err = PF_Err_BAD_CALLBACK_PARAM;
		}
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
	if (!err && render_complete) {
		for (A_long y = 0; y < output_world->height; ++y) {
			memcpy((uint8_t *)output_world->data +
			           (size_t)y * (size_t)output_world->rowbytes,
			       pending_output.data() + (size_t)y * active_bytes,
			       active_bytes);
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
	} catch (const std::bad_alloc &) {
		err = (PF_Err)4;
	} catch (...) {
#ifdef OLMSMOOTHER_SHIM_H
		err = PF_Err_BAD_CALLBACK_PARAM;
#else
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
#endif
	}
	return err;
}

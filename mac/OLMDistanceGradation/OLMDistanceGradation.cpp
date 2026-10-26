#include "../../core/olm_exact_math.h"
#include "OLMDistanceGradation.h"
#include <AEFX_SuiteHelper.h>
#include "../../core/olmdistancegradation_fieldgen.h"
#include "../../core/olm_world_safety.h"
#include "../../core/olm_parallel.h"
#include <math.h>
#include <string.h>
#include <vector>
#include <algorithm>
#include <limits>
#include <new>
#include <fcntl.h>
#include <unistd.h>
#include <cstdlib>
#include <cstdio>

// Refusal attribution for the fuzz campaign. When OLM_REFUSAL_TRACE names a
// file, each failing admission guard appends "function:tag". The file is only
// opened on a refusal, and the returned error code and all output bytes are
// identical whether or not tracing is enabled.
static PF_Err DistanceRefusal(const char *function, const char *tag, int line, PF_Err err)
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

#define OLM_DG_REFUSAL(tag) DistanceRefusal(__func__, tag, __LINE__, PF_Err_BAD_CALLBACK_PARAM)
#define OLM_DG_ERROR(tag, code) DistanceRefusal(__func__, tag, __LINE__, code)



static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	suites.ANSICallbacksSuite1()->sprintf(out_data->return_msg,
		"%s v%d.%d.%d\r%s",
		GetStringPtr(StrID_Name),
		MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
		GetStringPtr(StrID_Description));
	return PF_Err_NONE;
}

// Captured AEX GlobalSetup flags; preserve the exact exported capability masks.
static constexpr A_long kGlobalOutFlags = 0x06000040;
static constexpr A_long kGlobalOutFlags2 = 0x08001400;

static PF_Err
GlobalSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = kGlobalOutFlags;
	out_data->out_flags2 = kGlobalOutFlags2;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_Invert_Param_Name),
	                "", FALSE, 0, INVERT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_InOut_Param_Name),
	             3, 0,
	             GetStringPtr(StrID_InOut_Choices),
	             IN_OUT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_InsideThreshold_Param_Name),
	              0, 1000, 0, 512, 128,
	              INSIDE_THRESHOLD_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_OutsideThreshold_Param_Name),
	              0, 1000, 0, 512, 128,
	              OUTSIDE_THRESHOLD_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_RenderMode_Param_Name),
	             2, RENDER_MODE_RGB,
	             GetStringPtr(StrID_RenderMode_Choices),
	             RENDER_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseBgColor_Param_Name),
	                "", FALSE, 0, USE_BG_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_GradColor_Param_Name),
	             0xFF, 0x00, 0x00,
	             GRAD_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	{
		PF_ADD_COLOR(GetStringPtr(StrID_BgColor_Param_Name),
		             0, 0, 0,
		             BG_COLOR_DISK_ID);
	}

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_InterpMode_Param_Name),
	             4, INTERP_LINEAR,
	             GetStringPtr(StrID_InterpMode_Choices),
	             INTERP_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Power_Param_Name),
	                     0.01, 5.0, 0.01, 5.0, 1.0,
	                     PF_Precision_HUNDREDTHS, 0, PF_ParamFlag_START_COLLAPSED,
	                     POWER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_BlurMode_Param_Name),
	             5, BLUR_MODE_NONE,
	             GetStringPtr(StrID_BlurMode_Choices),
	             BLUR_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = PF_ParamFlag_START_COLLAPSED;
	PF_ADD_SLIDER(GetStringPtr(StrID_BlurSize_Param_Name),
	              0, 4096, 0, 500, 0,
	              BLUR_SIZE_DISK_ID);

	out_data->num_params = DG_NUM_PARAMS;
	return err;
}

static PF_Err
UpdateParamEnabled(PF_InData *in_data, A_long index, bool disabled)
{
	PF_Err err = PF_Err_NONE;
	PF_ParamDef copy;
	AEFX_CLR_STRUCT(copy);
	ERR(PF_CHECKOUT_PARAM(in_data, index, in_data->current_time,
	                      in_data->time_step, in_data->time_scale, &copy));
	if (!err) {
		// The Windows AEX replaces the UI flags with exactly one of these two
		// values; it does not preserve unrelated bits from the checked-out copy.
		copy.ui_flags = disabled ? PF_PUI_DISABLED : 0;
		AEGP_SuiteHandler suites(in_data->pica_basicP);
		ERR(suites.ParamUtilsSuite3()->PF_UpdateParamUI(
			in_data->effect_ref, index, &copy));
	}
	PF_CHECKIN_PARAM(in_data, &copy);
	return err;
}

static PF_Err
UpdateParamsUI(PF_InData *in_data)
{
	PF_Err err = PF_Err_NONE;
	PF_ParamDef value;

	AEFX_CLR_STRUCT(value);
	ERR(PF_CHECKOUT_PARAM(in_data, DG_INTERP_MODE, in_data->current_time,
	                      in_data->time_step, in_data->time_scale, &value));
	const A_long interp_mode = value.u.pd.value;
	PF_CHECKIN_PARAM(in_data, &value);
	if (err) return err;
	if (!err) ERR(UpdateParamEnabled(in_data, DG_POWER, interp_mode != INTERP_POWER));
	if (err) return err;

	AEFX_CLR_STRUCT(value);
	if (!err) ERR(PF_CHECKOUT_PARAM(in_data, DG_IN_OUT, in_data->current_time,
	                                in_data->time_step, in_data->time_scale, &value));
	const A_long in_out = value.u.pd.value;
	PF_CHECKIN_PARAM(in_data, &value);
	if (err) return err;
	if (!err) ERR(UpdateParamEnabled(in_data, DG_OUTSIDE_THRESHOLD, in_out == IN_OUT_INSIDE));
	if (err) return err;
	if (!err) ERR(UpdateParamEnabled(in_data, DG_INSIDE_THRESHOLD, in_out == IN_OUT_OUTSIDE));
	if (err) return err;

	AEFX_CLR_STRUCT(value);
	if (!err) ERR(PF_CHECKOUT_PARAM(in_data, DG_RENDER_MODE, in_data->current_time,
	                                in_data->time_step, in_data->time_scale, &value));
	const A_long render_mode = value.u.pd.value;
	PF_CHECKIN_PARAM(in_data, &value);
	if (err) return err;

	AEFX_CLR_STRUCT(value);
	if (!err) ERR(PF_CHECKOUT_PARAM(in_data, DG_USE_BG_COLOR, in_data->current_time,
	                                in_data->time_step, in_data->time_scale, &value));
	const bool use_bg = value.u.bd.value != 0;
	PF_CHECKIN_PARAM(in_data, &value);
	if (err) return err;
	if (!err) ERR(UpdateParamEnabled(in_data, DG_GRAD_COLOR, render_mode != RENDER_MODE_RGB));
	if (err) return err;
	if (!err) ERR(UpdateParamEnabled(in_data, DG_BG_COLOR, !use_bg));
	if (err) return err;

	AEFX_CLR_STRUCT(value);
	if (!err) ERR(PF_CHECKOUT_PARAM(in_data, DG_BLUR_MODE, in_data->current_time,
	                                in_data->time_step, in_data->time_scale, &value));
	const A_long blur_mode = value.u.pd.value;
	PF_CHECKIN_PARAM(in_data, &value);
	if (err) return err;
	if (!err) ERR(UpdateParamEnabled(in_data, DG_BLUR_SIZE, blur_mode == BLUR_MODE_NONE));

	return err;
}

// ============================================================================
// Params snapshot
// ============================================================================
struct DGParams {
	bool          invert;
	A_long        in_out;           // IN_OUT_*
	A_long        inside_threshold, outside_threshold;
	A_long        render_mode;      // RENDER_MODE_*
	bool          use_bg;
	PF_PixelFloat grad_color, bg_color;
	A_long        interp_mode;      // INTERP_*
	float         power;
	A_long        blur_mode;        // BLUR_MODE_*
	A_long        blur_size;

	A_long        w, h;             // output dimensions
	// downsample scale (full-res -> current-res)
	float         ds_x, ds_y;
	long          reconstructed_w, reconstructed_h;
	long          blur_size_y;
	size_t        pixel_size;       // sizeof(render pixel P); selects the source-mask alpha rule
	bool          smart_owner;      // exported Smart owner routing, distinct from legacy classic owner
	bool          degenerate_mask;  // original owner refcon +0x90: zero or all mask pixels set
	bool          pf32_smart_matrix_admitted;
	bool          pf32_smart_oracle_profile_admitted;
};

// The original bilateral filter clamps its radius to at least one: Size0
// is an effective three-tap diameter, just like Size1, on PF8/PF32 Smart.
static bool has_effective_blur(const DGParams &p)
{
	return p.blur_mode != BLUR_MODE_NONE &&
		(p.blur_size > 0 || (p.smart_owner && p.reconstructed_w && p.blur_size_y > 0 &&
		 (p.blur_mode == BLUR_MODE_NO_SCALE || p.blur_mode == BLUR_MODE_SCALE)) || (p.smart_owner && p.pixel_size != sizeof(PF_Pixel16) &&
		 p.blur_mode == BLUR_MODE_BILATERAL));
}

static PF_Err
FetchParams(PF_InData *in_data, PF_ParamDef *params[], DGParams *p)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	p->invert            = params[DG_INVERT]->u.bd.value != 0;
	p->in_out            = params[DG_IN_OUT]->u.pd.value;
	p->inside_threshold  = params[DG_INSIDE_THRESHOLD]->u.sd.value;
	p->outside_threshold = params[DG_OUTSIDE_THRESHOLD]->u.sd.value;
	p->render_mode       = params[DG_RENDER_MODE]->u.pd.value;
	p->use_bg            = params[DG_USE_BG_COLOR]->u.bd.value != 0;
	p->interp_mode       = params[DG_INTERP_MODE]->u.pd.value;
	p->power             = (float)params[DG_POWER]->u.fs_d.value;
	p->blur_mode         = params[DG_BLUR_MODE]->u.pd.value;
	p->blur_size         = params[DG_BLUR_SIZE]->u.sd.value;

	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();
	if (!cps || !cps->PF_GetFloatingPointColorFromColorDef) return OLM_DG_REFUSAL("color-suite-missing");
	ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[DG_GRAD_COLOR], &p->grad_color));
	ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[DG_BG_COLOR], &p->bg_color));
	if (err) return err;

	p->ds_x = (float)in_data->downsample_x.num / (float)in_data->downsample_x.den;
	p->ds_y = (float)in_data->downsample_y.num / (float)in_data->downsample_y.den;
	return err;
}

#include "DistanceFilters.inc"
#include "BilateralFilters.inc"
#include "DistanceField.inc"
#include "PixelCompose.inc"
#include "Admission.inc"
// ============================================================================
// Core render: reads src layer, builds distance field, writes dst layer.
// ============================================================================
template<typename P>
static PF_Err
RenderBits(PF_InData *in_data, PF_ParamDef *params[],
           PF_LayerDef *input, PF_LayerDef *output, bool smart_owner = false)
{
	PF_Err err = PF_Err_NONE;
	// Classic retains its same-shape contract. Smart builds the field from the
	// entire input, then stages the packed prefix consumed by the original owner
	// for a smaller result_rect allocation. Validate each world independently.
	if (!input || !output || !input->data || !output->data ||
	    !in_data || (!smart_owner && (in_data->output_origin_x != 0 || in_data->output_origin_y != 0 ||
	    in_data->pre_effect_source_origin_x != 0 || in_data->pre_effect_source_origin_y != 0 ||
	    input->width != output->width || input->height != output->height)) ||
	    output->width <= 0 || output->height <= 0 ||
	    output->width > input->width || output->height > input->height ||
	    input->width <= 0 || input->height <= 0 ||
	    input->width > std::numeric_limits<A_long>::max() / (A_long)sizeof(P) ||
	    input->rowbytes < input->width * (A_long)sizeof(P) ||
	    output->rowbytes < output->width * (A_long)sizeof(P)) {
		return OLM_DG_REFUSAL("world-layout");
	}

	DGParams p; AEFX_CLR_STRUCT(p);
	ERR(FetchParams(in_data, params, &p));
	if (err) return err;
	long w = input->width;
	long h = input->height;
	size_t pixel_count = 0;
	if (!checked_pixel_count(w, h, &pixel_count)) return OLM_DG_REFUSAL("pixel-count");
	p.w = w; p.h = h;
	p.pixel_size = sizeof(P);
	p.smart_owner = smart_owner;
	if (smart_owner) {
		// Typed owners: uint32 multiply, float32 inverse-size divide, truncation.
		// cvSmooth separately uses uint32 multiply/divide for each axis.
		if (in_data->downsample_x.num <= 0 || in_data->downsample_x.den <= 0 ||
		    in_data->downsample_y.num <= 0 || in_data->downsample_y.den <= 0)
			return OLM_DG_REFUSAL("smart-scale");
		const float rw = (float)(uint32_t)((uint64_t)w * in_data->downsample_x.den) / (float)in_data->downsample_x.num;
		const float rh = (float)(uint32_t)((uint64_t)h * in_data->downsample_y.den) / (float)in_data->downsample_y.num;
		if (!(rw >= 1 && rh >= 1 && rw < 2147483648.0f && rh < 2147483648.0f))
			return OLM_DG_REFUSAL("smart-reconstructed-size");
		p.reconstructed_w = (long)rw; p.reconstructed_h = (long)rh;
		size_t reconstructed_count;
		if (!checked_pixel_count(p.reconstructed_w,p.reconstructed_h,&reconstructed_count))
			return OLM_DG_REFUSAL("smart-reconstructed-count");
		const long bx = (uint32_t)((uint64_t)p.blur_size * in_data->downsample_x.num) / (uint32_t)in_data->downsample_x.den;
		const long by = (uint32_t)((uint64_t)p.blur_size * in_data->downsample_y.num) / (uint32_t)in_data->downsample_y.den;
		p.blur_size_y = by;
		p.blur_size = bx;
		p.ds_x = p.ds_y = 1.0f;
	}

	// Power with exponent exactly one is the same finite-field operation as
	// Linear. Normalize this control before applying the existing Smart domain
	// and filter admission rules; arbitrary Power retains its separate guard.
	if (smart_owner && sizeof(P) == sizeof(PF_PixelFloat) &&
	    p.interp_mode == INTERP_POWER && p.power == 1.0f)
		p.interp_mode = INTERP_LINEAR;
	if (smart_owner && sizeof(P) == sizeof(PF_PixelFloat) &&
	    !pf32_smart_worlds_are_bounded_sdr(input, output, p)) {
		return OLM_DG_REFUSAL("pf32-smart-bounded-sdr");
	}

	// Extract normalized alpha for DT
	std::vector<float> alpha(pixel_count, 0.0f);
	for (long y = 0; y < h; ++y) {
		const P *row = (const P *)((char *)input->data + (size_t)y * input->rowbytes);
		float *arow = alpha.data() + (size_t)y * w;
		for (long x = 0; x < w; ++x) {
			float a, r, g, b;
			load_rgba_norm(&row[x], a, r, g, b);
			arow[x] = a;
		}
	}
	if (smart_owner && sizeof(P) == sizeof(PF_PixelFloat)) {
		p.pf32_smart_matrix_admitted =
			is_admitted_pf32_smart_exported_matrix(p, alpha, w, h);
		if (p.pf32_smart_matrix_admitted && p.interp_mode == INTERP_POWER &&
		    !is_admitted_pf32_power_source(input, w, h)) {
			p.pf32_smart_matrix_admitted = false;
		}
		// Power uses the shared UCRT FLOAT32 operation. Reuse only the
		// existing filter admission; source/layout checks above retain their
		// original Power restrictions (finite SDR), and rendering keeps Power.
		DGParams admission = p;
		if (p.interp_mode == INTERP_POWER && std::isfinite(p.power) &&
		    p.power >= 0.01f && p.power <= 5.0f &&
		    (p.blur_mode != BLUR_MODE_MEDIAN || p.blur_size <= 2))
			admission.interp_mode = INTERP_LINEAR;
		const bool unblurred_beta = is_admitted_pf32_smart_unblurred_beta(admission);
		const bool blurred_beta = is_admitted_pf32_smart_blurred_beta(admission, w, h);
		p.pf32_smart_oracle_profile_admitted =
			is_admitted_pf32_smart_oracle_profile(p);
		if (!p.pf32_smart_matrix_admitted && !unblurred_beta && !blurred_beta &&
		    !is_admitted_pf32_smart_bilateral_beta(p) &&
		    !is_admitted_pf32_smart_bilateral_general_beta(p, w, h) &&
		    !is_admitted_pf32_smart_bilateral_scalar_beta(admission, w, h) &&
		    !p.pf32_smart_oracle_profile_admitted) {
			return OLM_DG_REFUSAL("pf32-smart-profile");
		}
	}

	DistanceField df;
	// FUN_1811749a0 converts alpha to uint8 with nearest-even rounding, then
	// thresholds at 1. FUN_181183000 counts that mask; each typed owner sets
	// refcon +0x90 when the count is zero or width*height. Keep the existing
	// distance-field mask contract separate from this owner-level decision.
	bool any_owned = false, any_unowned = false, bounded_alpha = true;
	for (float a : alpha) {
		if (!std::isfinite(a) || a < 0.0f || a > 1.0f) bounded_alpha = false;
		const bool owned = smart_owner ? source_mask_owns_alpha(a, sizeof(P), true)
		                              : a * 255.0f >= 1.5f;
		any_owned |= owned;
		any_unowned |= !owned;
	}
	// Original Smart owner 18117339f..1811733ba tests the converted mask count,
	// regardless of source alpha range. The census and field construction use
	// the same Smart conversion; Classic retains its bounded-alpha contract.
	p.degenerate_mask =
		(bounded_alpha || smart_owner) &&
		(!any_owned || !any_unowned);
	build_distance_field(alpha.data(), df, p, w, h);
	debug_dump_distance_field(getenv("OLM_DG_DEBUG_DUMP_PATH"), alpha.data(), df, p, w, h, sizeof(P));

	// Original owner copies a packed prefix of the field to the output world;
	// Iterate reads the source at local coordinates, without world-origin adjustment.
	const auto shade_row = [&](size_t row) {
		const long y = (long)row;
		const P *src = (const P *)((char *)input->data  + (size_t)y * input->rowbytes);
		P *dst       = (P *)      ((char *)output->data + (size_t)y * output->rowbytes);
		const float *xrow = df.x.data()       + (size_t)y * output->width;
		const bool blurred = has_effective_blur(p);
		const float *aux = !df.pre_blur_x.empty() ? df.pre_blur_x.data()
		                 : (blurred ? df.x.data() : df.d_alpha.data());
		const float *arow = aux + (size_t)y * output->width;
		shade_scanline<P>(src, dst, xrow, arow, p, output->width, output->height, y, input);
	};
#ifdef OLM_REFERENCE_BUILD
	olm::parallel_rows_reference((size_t)output->height, shade_row);
#else
	// Debug files retain sequential record order. Smart rows read only the
	// source/field; overlapping worlds and Classic retain their original walk.
	const bool threaded = smart_owner &&
		(size_t)output->width * (size_t)output->height >= 65536 &&
		!getenv("OLM_DG_SHADE_DEBUG_PATH") &&
		!getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_PATH") &&
		olm::world_safety::require_disjoint(
			{input->data, (size_t)input->width, (size_t)input->height,
			 (size_t)input->rowbytes, sizeof(P)},
			{output->data, (size_t)output->width, (size_t)output->height,
			 (size_t)output->rowbytes, sizeof(P)}) == olm::world_safety::Status::ok;
	olm::parallel_rows((size_t)output->height,
		threaded ? 1 : (size_t)output->height, shade_row);
#endif

	return err;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	if (!in_data || !out_data || !params || !output ||
	    in_data->output_origin_x != 0 || in_data->output_origin_y != 0 ||
	    in_data->pre_effect_source_origin_x != 0 || in_data->pre_effect_source_origin_y != 0) {
		return OLM_DG_REFUSAL("render-arguments-origin");
	}
	for (A_long i = 0; i < DG_NUM_PARAMS; ++i) {
		if (!params[i]) return OLM_DG_REFUSAL("render-param-null");
	}
	PF_LayerDef *input = &params[DG_INPUT]->u.ld;
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	ERR(world_suite->PF_GetPixelFormat(input, &input_format));
	ERR(world_suite->PF_GetPixelFormat(output, &output_format));
	if (err) return err;
	if (input_format != output_format) return OLM_DG_REFUSAL("render-format-mismatch");

	switch (input_format) {
	case PF_PixelFormat_ARGB32:
		return RenderBits<PF_Pixel8>(in_data, params, input, output);
	case PF_PixelFormat_ARGB64:
		return RenderBits<PF_Pixel16>(in_data, params, input, output);
	case PF_PixelFormat_ARGB128:
		return RenderBits<PF_PixelFloat>(in_data, params, input, output);
	default:
		return OLM_DG_REFUSAL("render-format-unsupported");
	}
}

// ============================================================================
// SmartRender
// ============================================================================

static void UnionLRect_inline(const PF_LRect *src, PF_LRect *dst) {
	if (dst->left == dst->right || dst->top == dst->bottom) {
		*dst = *src;
		return;
	}
	if (src->left == src->right || src->top == src->bottom) return;
	if (src->left   < dst->left)   dst->left   = src->left;
	if (src->top    < dst->top)    dst->top    = src->top;
	if (src->right  > dst->right)  dst->right  = src->right;
	if (src->bottom > dst->bottom) dst->bottom = src->bottom;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	if (!in_data || !out_data || !extra || !extra->input || !extra->output || !extra->cb ||
	    !extra->cb->checkout_layer ||
	    (extra->input->bitdepth != 8 && extra->input->bitdepth != 16 &&
	     extra->input->bitdepth != 32)) {
		return OLM_DG_REFUSAL("prerender-arguments-depth");
	}
	PF_Err err = PF_Err_NONE;
	if (in_data->width <= 0 || in_data->height <= 0 ||
	    in_data->downsample_x.num <= 0 || in_data->downsample_x.den <= 0 ||
	    in_data->downsample_y.num <= 0 || in_data->downsample_y.den <= 0) {
		return OLM_DG_REFUSAL("prerender-size-downsample");
	}
	PF_RenderRequest req = extra->input->output_request;
	// Original public command 0x17 forwards the requested rectangle unchanged.
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		DG_INPUT, DG_INPUT, &req,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&in_result));

	if (!err) {
		UnionLRect_inline(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect_inline(&in_result.max_result_rect, &extra->output->max_result_rect);
	}
	return err;
}

// Windows Smart PF16 enters its typed iterator with the source in params[0]
// and a scalar field already staged in the destination world.  The callback
// preserves source ownership in alpha and expands destination green (the
// staged field lane) to RGB.  Keep this separate from classic RenderBits:
// classic PF16 owns field generation, while this Smart boundary owns only the
// final typed merge.
static PF_Err
RenderSmartPF16PreseededField(const PF_EffectWorld *input_world,
                             PF_EffectWorld *output_world)
{
	if (!input_world || !output_world || !input_world->data || !output_world->data ||
	    input_world->width != output_world->width ||
	    input_world->height != output_world->height ||
	    input_world->width < 0 || input_world->height < 0 ||
	    input_world->rowbytes < input_world->width * (A_long)sizeof(PF_Pixel16) ||
	    output_world->rowbytes < output_world->width * (A_long)sizeof(PF_Pixel16)) {
		return OLM_DG_REFUSAL("smart-pf16-preseed-layout");
	}
	for (A_long y = 0; y < input_world->height; ++y) {
		const PF_Pixel16 *src = reinterpret_cast<const PF_Pixel16 *>(
			reinterpret_cast<const char *>(input_world->data) + (size_t)y * input_world->rowbytes);
		PF_Pixel16 *dst = reinterpret_cast<PF_Pixel16 *>(
			reinterpret_cast<char *>(output_world->data) + (size_t)y * output_world->rowbytes);
		for (A_long x = 0; x < input_world->width; ++x) {
			const uint16_t field = dst[x].green;
			dst[x].alpha = src[x].alpha;
			dst[x].red = dst[x].green = dst[x].blue = field;
		}
	}
	return PF_Err_NONE;
}

// The PF8 Smart callback is a separate typed contract: destination green is
// decoded as the 8-bit field, alpha uses the callback's float truncation path,
// and RGB is opaque white.  Do not route it through PF16 word quantization.
static PF_Err
RenderSmartPF8PreseededField(const PF_EffectWorld *input_world,
                            PF_EffectWorld *output_world)
{
	if (!input_world || !output_world || !input_world->data || !output_world->data ||
	    input_world->width != output_world->width ||
	    input_world->height != output_world->height ||
	    input_world->width < 0 || input_world->height < 0 ||
	    input_world->rowbytes < input_world->width * (A_long)sizeof(PF_Pixel8) ||
	    output_world->rowbytes < output_world->width * (A_long)sizeof(PF_Pixel8)) {
		return OLM_DG_REFUSAL("smart-pf8-preseed-layout");
	}
	for (A_long y = 0; y < input_world->height; ++y) {
		const PF_Pixel8 *src = reinterpret_cast<const PF_Pixel8 *>(
			reinterpret_cast<const char *>(input_world->data) + (size_t)y * input_world->rowbytes);
		PF_Pixel8 *dst = reinterpret_cast<PF_Pixel8 *>(
			reinterpret_cast<char *>(output_world->data) + (size_t)y * output_world->rowbytes);
		for (A_long x = 0; x < input_world->width; ++x) {
			const uint8_t field_byte = dst[x].green;
			if (src[x].alpha == 0) {
				dst[x].alpha = 0;
				dst[x].red = dst[x].green = dst[x].blue = field_byte;
				continue;
			}
			const float src_a = (float)src[x].alpha * (1.0f / 255.0f);
			const float field = (float)field_byte * (1.0f / 255.0f);
			dst[x].alpha = (uint8_t)(src_a * (1.0f - field) * 255.0f);
			dst[x].red = dst[x].green = dst[x].blue = 255;
		}
	}
	return PF_Err_NONE;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	if (!in_data || !out_data || !extra || !extra->input || !extra->cb ||
	    !extra->cb->checkout_layer_pixels || !extra->cb->checkin_layer_pixels ||
	    !extra->cb->checkout_output ||
	    (extra->input->bitdepth != 8 && extra->input->bitdepth != 16 &&
	     extra->input->bitdepth != 32)) {
		return OLM_DG_REFUSAL("smart-arguments-depth");
	}
	PF_Err err = PF_Err_NONE;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);

	PF_EffectWorld *input_world  = nullptr;
	PF_EffectWorld *output_world = nullptr;
	bool input_checked_out = false;
	bool render_complete = false;
	olm::world_safety::TightStaging staging;
	std::vector<uint8_t> full_output;
	PF_EffectWorld backing_output{};
	PF_ParamDef param_list[DG_NUM_PARAMS];
	bool param_checked_out[DG_NUM_PARAMS] = {};
	for (A_long i = 0; i < DG_NUM_PARAMS; ++i) AEFX_CLR_STRUCT(param_list[i]);
	try {
		err = extra->cb->checkout_layer_pixels(in_data->effect_ref, DG_INPUT, &input_world);
		input_checked_out = err == PF_Err_NONE;
		if (!err) err = extra->cb->checkout_output(in_data->effect_ref, &output_world);

		// Checkout params via PF_ParamDef stack. The per-item flags make the
		// cleanup below exact even when checkout or rendering throws midway.
		for (A_long i = 1; i < DG_NUM_PARAMS; ++i) {
			if (err) break;
			err = PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
			                        in_data->time_step, in_data->time_scale,
			                        &param_list[i]);
			param_checked_out[i] = err == PF_Err_NONE;
		}

		PF_ParamDef *params[DG_NUM_PARAMS];
		params[0] = &param_list[0];
		for (A_long i = 1; i < DG_NUM_PARAMS; ++i) params[i] = &param_list[i];

			if (!err && (!input_world || !output_world || !input_world->data || !output_world->data)) {
			err = OLM_DG_REFUSAL("smart-world-null");
		}
		PF_PixelFormat input_format = PF_PixelFormat_INVALID;
		PF_PixelFormat output_format = PF_PixelFormat_INVALID;
		if (!err) err = world_suite->PF_GetPixelFormat(input_world, &input_format);
		if (!err) err = world_suite->PF_GetPixelFormat(output_world, &output_format);
		const short depth = extra->input->bitdepth;
		const PF_PixelFormat expected_format = depth == 8 ? PF_PixelFormat_ARGB32
			: depth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
		if (!err && (input_format != expected_format || output_format != expected_format ||
		             input_format != output_format)) {
			err = OLM_DG_REFUSAL("smart-format-mismatch");
		}


		if (!err) {
			const size_t pixel_bytes = depth == 8 ? sizeof(PF_Pixel8) :
				(depth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat));
			using namespace olm::world_safety;
			const ConstWorld source{input_world->data, (size_t)input_world->width,
				(size_t)input_world->height, (size_t)input_world->rowbytes, pixel_bytes};
			const ConstWorld dest{output_world->data, (size_t)output_world->width,
				(size_t)output_world->height, (size_t)output_world->rowbytes, pixel_bytes};
			Layout layout{};
			if (input_world->rowbytes <= 0 || output_world->rowbytes <= 0 ||
			    validate_layout(source, &layout) != Status::ok ||
			    validate_layout(dest) != Status::ok || require_disjoint(source, dest) != Status::ok ||
			    output_world->width > input_world->width || output_world->height > input_world->height)
				throw OLM_DG_REFUSAL("smart-world-layout");
			full_output.resize(layout.tight_bytes);
			backing_output = *input_world;
			backing_output.data = (decltype(backing_output.data))full_output.data();
			backing_output.rowbytes = (A_long)layout.active_row_bytes;
			const Status stage_status = staging.prepare(source,
				{backing_output.data, source.width, source.height, layout.active_row_bytes, pixel_bytes});
			if (stage_status != olm::world_safety::Status::ok) {
				err = stage_status == olm::world_safety::Status::out_of_memory ?
					PF_Err_OUT_OF_MEMORY : PF_Err_BAD_CALLBACK_PARAM;
			}
		}

		if (!err) {
			// Fill params[DG_INPUT]->u.ld for the render helpers
			PF_EffectWorld staged_input = *input_world;
			PF_EffectWorld staged_output = *output_world;
			staged_input.data = (decltype(staged_input.data))staging.input_data();
			staged_output.data = (decltype(staged_output.data))staging.output_data();
			staged_input.rowbytes = staged_output.rowbytes = (A_long)staging.row_bytes();
			param_list[0].u.ld = staged_input;
			if (depth == 8) {
				err = RenderBits<PF_Pixel8>(in_data, params, &staged_input, &staged_output, true);
			} else if (depth == 16) {
				err = RenderBits<PF_Pixel16>(in_data, params, &staged_input, &staged_output, true);
			} else if (depth == 32) {
				err = RenderBits<PF_PixelFloat>(in_data, params, &staged_input, &staged_output, true);
			}
			render_complete = !err;
		}
	} catch (const PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}

	for (A_long i = 1; i < DG_NUM_PARAMS; ++i) {
		if (!param_checked_out[i]) continue;
		try {
			PF_CHECKIN_PARAM(in_data, &param_list[i]);
		} catch (const PF_Err &thrown_err) {
			if (!err) err = thrown_err;
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
	if (input_checked_out) {
		try {
			PF_Err checkin_err = extra->cb->checkin_layer_pixels(in_data->effect_ref, DG_INPUT);
			if (!err) err = checkin_err;
		} catch (const PF_Err &thrown_err) {
			if (!err) err = thrown_err;
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
	if (!err && render_complete) {
		const size_t active = (size_t)output_world->width * (extra->input->bitdepth / 8 * 4);
		for (A_long y = 0; y < output_world->height; ++y)
			std::memcpy((uint8_t*)output_world->data + (size_t)y * output_world->rowbytes,
				staging.output_data() + (size_t)y * staging.row_bytes(), active);
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
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParamsUI(in_data);
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
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return err;
}

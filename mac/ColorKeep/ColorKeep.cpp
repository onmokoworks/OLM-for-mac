#include "ColorKeep.h"
#include "AEFX_SuiteHandlerTemplate.h"
#include <stdint.h>
#include <math.h>
#include <new>
#include <vector>

static void UnionLRect(const PF_LRect *src, PF_LRect *dst)
{
	if (dst->left == dst->right || dst->top == dst->bottom) {
		*dst = *src;
	} else if (src->left != src->right && src->top != src->bottom) {
		if (src->left   < dst->left)   dst->left   = src->left;
		if (src->top    < dst->top)    dst->top    = src->top;
		if (src->right  > dst->right)  dst->right  = src->right;
		if (src->bottom > dst->bottom) dst->bottom = src->bottom;
	}
}

static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	suites.ANSICallbacksSuite1()->sprintf(out_data->return_msg,
		"%s v%d.%d%d\r%s",
		GetStringPtr(StrID_Name),
		MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
		GetStringPtr(StrID_Description));
	return PF_Err_NONE;
}

static PF_Err
GlobalSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000040;
	out_data->out_flags2 = 0x08001400;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	def.flags = PF_ParamFlag_SUPERVISE;
	PF_ADD_SLIDER(GetStringPtr(StrID_EnabledColorNum_Param_Name),
	              0, COLORKEEP_MAX_COLORS,
	              0, COLORKEEP_MAX_COLORS,
	              1,
	              ENABLED_COLOR_NUM_DISK_ID);

	for (int i = 0; i < COLORKEEP_MAX_COLORS; ++i) {
		AEFX_CLR_STRUCT(def);
		PF_ADD_COLOR(GetStringPtr(StrID_Color_Param_Name),
		             0, 0, 0,
		             COLOR_DISK_ID_FIRST + i);
	}

	out_data->num_params = COLORKEEP_NUM_PARAMS;
	return err;
}

static PF_Err
SetColorsEnabled(PF_InData *in_data, PF_ParamDef *params[])
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ParamUtilsSuite3 *pu = suites.ParamUtilsSuite3();

	A_long enabledCount = params[COLORKEEP_ENABLED_COLOR_NUM]->u.sd.value;
	if (enabledCount < 0) enabledCount = 0;
	if (enabledCount > COLORKEEP_MAX_COLORS) enabledCount = COLORKEEP_MAX_COLORS;

	for (int i = 0; i < COLORKEEP_MAX_COLORS; ++i) {
		A_long paramIndex = COLORKEEP_COLOR_FIRST + i;
		PF_ParamDef paramCopy = *params[paramIndex];
		if (i < enabledCount)
			paramCopy.ui_flags &= ~PF_PUI_DISABLED;
		else
			paramCopy.ui_flags |= PF_PUI_DISABLED;
		ERR(pu->PF_UpdateParamUI(in_data->effect_ref, paramIndex, &paramCopy));
	}
	return err;
}

static PF_Err
CheckoutInfo(PF_InData *in_data, PF_ParamDef *params[], ColorKeepInfo *info,
	         A_long colors_to_read)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();

	info->count = params[COLORKEEP_ENABLED_COLOR_NUM]->u.sd.value;
	if (info->count < 0) info->count = 0;
	if (info->count > COLORKEEP_MAX_COLORS) info->count = COLORKEEP_MAX_COLORS;

	for (A_long i = 0; i < colors_to_read; ++i) {
		PF_ParamDef *cp = params[COLORKEEP_COLOR_FIRST + i];
		info->colors8[i] = cp->u.cd.value;
		PF_PixelFloat fp = {0};
		ERR(cps->PF_GetFloatingPointColorFromColorDef(
			in_data->effect_ref, cp, &fp));
		info->colors[i] = fp;
	}
	return err;
}

// These are the exact float32 constants used by the Windows 2025 AEX.
static const float kColorKeep8Bias = 0.00196078442968428125f; // 0x3B008081
static const float kColorKeep8Scale = 255.0f;                 // 0x437F0000
static const float kColorKeep16Bias = 0.0000152587890625f;    // 0x37800000
static const float kColorKeep16Scale = 32768.0f;              // 0x47000000
static const float kColorKeepFloatTolerance = 1.0e-4f;        // 0x38D1B717

static bool ColorKeepCountIsAdmitted(A_long count)
{
	return count >= 1 && count <= COLORKEEP_MAX_COLORS;
}

static bool ColorKeepIsOneToOne(const PF_InData *in_data,
	                            const PF_EffectWorld *output)
{
	return in_data && output &&
		in_data->downsample_x.num == 1 && in_data->downsample_x.den == 1 &&
		in_data->downsample_y.num == 1 && in_data->downsample_y.den == 1 &&
		in_data->output_origin_x == output->origin_x &&
		in_data->output_origin_y == output->origin_y;
}

static PF_Err ColorKeepValidateWorldPair(const PF_EffectWorld *input,
	                                      const PF_EffectWorld *output,
	                                      short bitdepth)
{
	if (!input || !output || !input->data || !output->data) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	A_long pixel_bytes = 0;
	size_t pixel_alignment = 0;
	switch (bitdepth) {
	case 8:
		pixel_bytes = (A_long)sizeof(PF_Pixel8);
		pixel_alignment = alignof(PF_Pixel8);
		break;
	case 16:
		pixel_bytes = (A_long)sizeof(PF_Pixel16);
		pixel_alignment = alignof(PF_Pixel16);
		break;
	case 32:
		pixel_bytes = (A_long)sizeof(PF_PixelFloat);
		pixel_alignment = alignof(PF_PixelFloat);
		break;
	default:
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (input->width <= 0 || input->height <= 0 ||
	    output->width <= 0 || output->height <= 0 ||
	    input->width > INT32_MAX / pixel_bytes) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const A_long active_rowbytes = input->width * pixel_bytes;
	if (output->width > INT32_MAX / pixel_bytes ||
	    input->rowbytes < active_rowbytes ||
	    output->rowbytes < output->width * pixel_bytes) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const bool expected_deep = bitdepth == 16;
	const bool input_is_deep = (input->world_flags & PF_WorldFlag_DEEP) != 0;
	const bool output_is_deep = (output->world_flags & PF_WorldFlag_DEEP) != 0;
	if (input_is_deep != expected_deep ||
	    output_is_deep != expected_deep ||
	    (int64_t)output->origin_x < input->origin_x ||
	    (int64_t)output->origin_y < input->origin_y ||
	    (int64_t)output->origin_x + output->width > (int64_t)input->origin_x + input->width ||
	    (int64_t)output->origin_y + output->height > (int64_t)input->origin_y + input->height) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const uintptr_t input_begin = reinterpret_cast<uintptr_t>(input->data);
	const uintptr_t output_begin = reinterpret_cast<uintptr_t>(output->data);
	if (input_begin % pixel_alignment != 0 || output_begin % pixel_alignment != 0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t input_span = (size_t)input->rowbytes * (size_t)input->height;
	const size_t output_span = (size_t)output->rowbytes * (size_t)output->height;
	if (input_begin > UINTPTR_MAX - input_span || output_begin > UINTPTR_MAX - output_span) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const uintptr_t input_end = input_begin + input_span;
	const uintptr_t output_end = output_begin + output_span;
	if (input_begin < output_end && output_begin < input_end) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	return PF_Err_NONE;
}

static inline u_char ColorKeepQuantize8(float value)
{
	const float biased = value + kColorKeep8Bias;
	const float scaled = biased * kColorKeep8Scale;
	return (u_char)((int)scaled);
}

static inline u_short ColorKeepQuantize16(float value)
{
	const float biased = value + kColorKeep16Bias;
	const float scaled = biased * kColorKeep16Scale;
	return (u_short)((int)scaled);
}

static PF_Err
ColorKeep8Func(void *refcon, A_long, A_long, PF_Pixel8 *inP, PF_Pixel8 *outP)
{
	ColorKeepInfo *info = (ColorKeepInfo*)refcon;
	bool match = false;
	for (A_long i = 0; i < info->count; ++i) {
		const PF_PixelFloat &c = info->colors[i];
		if (inP->red == ColorKeepQuantize8(c.red) &&
		    inP->green == ColorKeepQuantize8(c.green) &&
		    inP->blue == ColorKeepQuantize8(c.blue) &&
		    inP->alpha == ColorKeepQuantize8(c.alpha)) {
			match = true; break;
		}
	}
	outP->red = inP->red; outP->green = inP->green; outP->blue = inP->blue;
	outP->alpha = match ? inP->alpha : 0;
	return PF_Err_NONE;
}

static PF_Err
ColorKeep16Func(void *refcon, A_long, A_long, PF_Pixel16 *inP, PF_Pixel16 *outP)
{
	ColorKeepInfo *info = (ColorKeepInfo*)refcon;
	bool match = false;
	for (A_long i = 0; i < info->count; ++i) {
		const PF_PixelFloat &c = info->colors[i];
		if (inP->red == ColorKeepQuantize16(c.red) &&
		    inP->green == ColorKeepQuantize16(c.green) &&
		    inP->blue == ColorKeepQuantize16(c.blue) &&
		    inP->alpha == ColorKeepQuantize16(c.alpha)) {
			match = true; break;
		}
	}
	outP->red = inP->red; outP->green = inP->green; outP->blue = inP->blue;
	outP->alpha = match ? inP->alpha : 0;
	return PF_Err_NONE;
}

static PF_Err
ColorKeepFloatFunc(void *refcon, A_long, A_long, PF_PixelFloat *inP, PF_PixelFloat *outP)
{
	ColorKeepInfo *info = (ColorKeepInfo*)refcon;
	bool match = false;
	for (A_long i = 0; i < info->count; ++i) {
		const PF_PixelFloat &c = info->colors[i];
		// Windows 2025 uses COMISS followed by JA for every absolute
		// difference. Express the same ordered-greater-than rejection so
		// an unordered (NaN) comparison follows the native fall-through.
		if (!(fabsf(inP->red - c.red) > kColorKeepFloatTolerance) &&
		    !(fabsf(inP->green - c.green) > kColorKeepFloatTolerance) &&
		    !(fabsf(inP->blue - c.blue) > kColorKeepFloatTolerance) &&
		    !(fabsf(inP->alpha - c.alpha) > kColorKeepFloatTolerance)) {
			match = true; break;
		}
	}
	outP->red = inP->red; outP->green = inP->green; outP->blue = inP->blue;
	outP->alpha = match ? inP->alpha : 0.0f;
	return PF_Err_NONE;
}

template <typename PixelT, typename PixelFuncT>
static PF_Err ColorKeepRenderRows(PF_EffectWorld *input,
	                              PF_EffectWorld *output,
	                              ColorKeepInfo *info,
	                              PixelFuncT pixel_func)
{
	const A_long offset_x = output->origin_x - input->origin_x;
	const A_long offset_y = output->origin_y - input->origin_y;
	for (A_long y = 0; y < output->height; ++y) {
		PixelT *in_row = reinterpret_cast<PixelT *>(
			reinterpret_cast<uint8_t *>(input->data) +
			(size_t)(y + offset_y) * (size_t)input->rowbytes);
		PixelT *out_row = reinterpret_cast<PixelT *>(
			reinterpret_cast<uint8_t *>(output->data) +
			(size_t)y * (size_t)output->rowbytes);
		for (A_long x = 0; x < output->width; ++x) {
			const PF_Err err = pixel_func((void *)info, x, y,
			                              in_row + x + offset_x, out_row + x);
			if (err) return err;
		}
	}
	return PF_Err_NONE;
}

template <typename PixelT, typename IterateSuiteT, typename PixelFuncT>
static PF_Err ColorKeepRenderMapped(PF_InData *in_data,
	                                IterateSuiteT *iterate_suite,
	                                PF_EffectWorld *input,
	                                PF_EffectWorld *output,
	                                ColorKeepInfo *info,
	                                PixelFuncT pixel_func)
{
	const size_t output_span = (size_t)output->rowbytes * (size_t)output->height;
	std::vector<uint8_t> staging(output_span);
	memcpy(staging.data(), output->data, output_span);
	PF_EffectWorld staged_output = *output;
	staged_output.data = reinterpret_cast<PF_PixelPtr>(staging.data());
	PF_Err err = PF_Err_NONE;
	if (input->width == output->width && input->height == output->height &&
	    input->origin_x == output->origin_x && input->origin_y == output->origin_y) {
		err = iterate_suite->iterate(in_data, 0, output->height, input, NULL,
		                            (void *)info, pixel_func, &staged_output);
	} else {
		err = ColorKeepRenderRows<PixelT>(input, &staged_output, info, pixel_func);
	}
	if (!err) memcpy(output->data, staging.data(), output_span);
	return err;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	if (!in_data || !out_data || !params || !output ||
	    !params[COLORKEEP_INPUT] || !params[COLORKEEP_ENABLED_COLOR_NUM] ||
	    !in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
	    !in_data->pica_basicP->ReleaseSuite) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	const A_long count = params[COLORKEEP_ENABLED_COLOR_NUM]->u.sd.value;
	if (!ColorKeepCountIsAdmitted(count)) return PF_Err_BAD_CALLBACK_PARAM;
	for (A_long i = 0; i < count; ++i) {
		if (!params[COLORKEEP_COLOR_FIRST + i]) return PF_Err_BAD_CALLBACK_PARAM;
	}

	PF_EffectWorld *input = &params[COLORKEEP_INPUT]->u.ld;
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite(in_data, kPFWorldSuite,
	                                             kPFWorldSuiteVersion2);
	ERR(world_suite->PF_GetPixelFormat(input, &input_format));
	ERR(world_suite->PF_GetPixelFormat(output, &output_format));
	if (err) return err;
	if (input_format != output_format) return PF_Err_BAD_CALLBACK_PARAM;

	short bitdepth = 0;
	switch (input_format) {
	case PF_PixelFormat_ARGB32: bitdepth = 8; break;
	case PF_PixelFormat_ARGB64: bitdepth = 16; break;
	default: return PF_Err_BAD_CALLBACK_PARAM;
	}
	ERR(ColorKeepValidateWorldPair(input, output, bitdepth));
	if (err) return err;
	if (!ColorKeepIsOneToOne(in_data, output)) return PF_Err_BAD_CALLBACK_PARAM;

	ColorKeepInfo info;
	AEFX_CLR_STRUCT(info);
	ERR(CheckoutInfo(in_data, params, &info, count));
	if (err) return err;
	if (info.count != count) return PF_Err_BAD_CALLBACK_PARAM;
	if (bitdepth == 16) {
		ERR(ColorKeepRenderMapped<PF_Pixel16>(in_data, suites.Iterate16Suite2(),
		                                      input, output, &info, ColorKeep16Func));
	} else {
		ERR(ColorKeepRenderMapped<PF_Pixel8>(in_data, suites.Iterate8Suite2(),
		                                     input, output, &info, ColorKeep8Func));
	}
	return err;
}

typedef struct {
	ColorKeepInfo info;
} PreRenderData;

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
	    !extra->cb->checkout_layer) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;

	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		COLORKEEP_INPUT, COLORKEEP_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->cb ||
	    !extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
	    !extra->cb->checkin_layer_pixels ||
	    !in_data->pica_basicP ||
	    !in_data->pica_basicP->AcquireSuite || !in_data->pica_basicP->ReleaseSuite ||
	    !in_data->inter.checkout_param || !in_data->inter.checkin_param) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, COLORKEEP_INPUT, &input_world));
	const bool input_checked_out = err == PF_Err_NONE;
	if (!err) ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (!err) ERR(ColorKeepValidateWorldPair(input_world, output_world,
	                                         extra->input->bitdepth));
	if (!err && !ColorKeepIsOneToOne(in_data, output_world))
		err = PF_Err_BAD_CALLBACK_PARAM;
	if (err || !input_world || !output_world) {
		if (!err) err = PF_Err_BAD_CALLBACK_PARAM;
		if (input_checked_out && extra->cb->checkin_layer_pixels) {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
				in_data->effect_ref, COLORKEEP_INPUT);
			if (!err) err = checkin_err;
		}
		return err;
	}
	PF_ParamDef checked_params[COLORKEEP_MAX_COLORS + 1];
	bool checked_out[COLORKEEP_MAX_COLORS + 1] = {false};
	std::vector<uint8_t> smart_output_stage;
	PF_EffectWorld smart_output_world;
	AEFX_CLR_STRUCT(smart_output_world);
	size_t smart_output_span = 0;
	bool smart_rendered = false;
	for (A_long i = 0; i <= COLORKEEP_MAX_COLORS; ++i) AEFX_CLR_STRUCT(checked_params[i]);
	try {
		PF_PixelFormat input_format = PF_PixelFormat_INVALID;
		PF_PixelFormat output_format = PF_PixelFormat_INVALID;
		AEFX_SuiteScoper<PF_WorldSuite2> world_suite(in_data, kPFWorldSuite,
		                                             kPFWorldSuiteVersion2);
		ERR(world_suite->PF_GetPixelFormat(input_world, &input_format));
		ERR(world_suite->PF_GetPixelFormat(output_world, &output_format));
		PF_PixelFormat expected_format = PF_PixelFormat_INVALID;
		switch (extra->input->bitdepth) {
		case 8: expected_format = PF_PixelFormat_ARGB32; break;
		case 16: expected_format = PF_PixelFormat_ARGB64; break;
		case 32: expected_format = PF_PixelFormat_ARGB128; break;
		default: break;
		}
		if (!err && (input_format != expected_format ||
		             output_format != expected_format)) {
			err = PF_Err_BAD_CALLBACK_PARAM;
		}

		ColorKeepInfo info;
		AEFX_CLR_STRUCT(info);
		PF_Err phase_err = PF_CHECKOUT_PARAM(in_data, COLORKEEP_ENABLED_COLOR_NUM,
		                      in_data->current_time, in_data->time_step, in_data->time_scale,
		                      &checked_params[0]);
		if (!phase_err) checked_out[0] = true;
		if (!err) err = phase_err;
		if (!err) {
			info.count = checked_params[0].u.sd.value;
			if (!ColorKeepCountIsAdmitted(info.count)) err = PF_Err_BAD_CALLBACK_PARAM;
		}

		for (A_long i = 0; i < info.count && !err; ++i) {
			phase_err = PF_CHECKOUT_PARAM(in_data, COLORKEEP_COLOR_FIRST + i,
			                 in_data->current_time, in_data->time_step, in_data->time_scale,
			                 &checked_params[i + 1]);
			if (!phase_err) checked_out[i + 1] = true;
			if (!err) err = phase_err;
		}
		PF_ColorParamSuite1 *cps = NULL;
		if (!err) cps = suites.ColorParamSuite1();
		for (A_long i = 0; i < info.count && !err; ++i) {
			PF_ParamDef &cp = checked_params[i + 1];
			if (checked_out[i + 1]) {
				PF_PixelFloat fp = {0};
				phase_err = cps->PF_GetFloatingPointColorFromColorDef(
					in_data->effect_ref, &cp, &fp);
				info.colors8[i] = cp.u.cd.value;
				info.colors[i] = fp;
				if (!err) err = phase_err;
			}
		}
		for (A_long i = 0; i <= COLORKEEP_MAX_COLORS; ++i) {
			if (checked_out[i]) {
				checked_out[i] = false;
				phase_err = PF_CHECKIN_PARAM(in_data, &checked_params[i]);
				if (!err) err = phase_err;
			}
		}

			const short bpc = extra->input->bitdepth;
			if (!err) {
				smart_output_span = (size_t)output_world->rowbytes * (size_t)output_world->height;
				smart_output_stage.resize(smart_output_span);
				memcpy(smart_output_stage.data(), output_world->data, smart_output_span);
				smart_output_world = *output_world;
				smart_output_world.data = reinterpret_cast<PF_PixelPtr>(smart_output_stage.data());
			}
			if (!err && bpc == 8) {
				ERR(ColorKeepRenderMapped<PF_Pixel8>(in_data, suites.Iterate8Suite2(),
				                                     input_world, &smart_output_world, &info, ColorKeep8Func));
			} else if (!err && bpc == 16) {
				ERR(ColorKeepRenderMapped<PF_Pixel16>(in_data, suites.Iterate16Suite2(),
				                                      input_world, &smart_output_world, &info, ColorKeep16Func));
			} else if (!err && bpc == 32) {
				ERR(ColorKeepRenderMapped<PF_PixelFloat>(in_data, suites.IterateFloatSuite2(),
				                                         input_world, &smart_output_world, &info, ColorKeepFloatFunc));
			} else if (!err) {
				err = PF_Err_BAD_CALLBACK_PARAM;
			}
			smart_rendered = err == PF_Err_NONE;
	} catch (PF_Err &thrown_err) {
		if (!err) err = thrown_err;
	} catch (const std::bad_alloc &) {
		if (!err) err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	for (A_long i = 0; i <= COLORKEEP_MAX_COLORS; ++i) {
		if (checked_out[i]) {
			checked_out[i] = false;
			try {
				const PF_Err cleanup_err = PF_CHECKIN_PARAM(in_data, &checked_params[i]);
				if (!err) err = cleanup_err;
			} catch (PF_Err &cleanup_err) {
				if (!err) err = cleanup_err;
			} catch (...) {
				if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
			}
		}
	}

	if (input_checked_out && extra->cb->checkin_layer_pixels) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
				in_data->effect_ref, COLORKEEP_INPUT);
			if (!err) err = checkin_err;
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
	if (!err && smart_rendered)
		memcpy(output_world->data, smart_output_stage.data(), smart_output_span);
	return err;
}

extern "C" DllExport
PF_Err PluginDataEntryFunction2(
	PF_PluginDataPtr  inPtr,
	PF_PluginDataCB2  inPluginDataCallBackPtr,
	SPBasicSuite     *inSPBasicSuitePtr,
	const char       *inHostName,
	const char       *inHostVersion)
{
	PF_Err result = PF_Err_INVALID_CALLBACK;
	result = PF_REGISTER_EFFECT_EXT2(
		inPtr, inPluginDataCallBackPtr,
		"Color Keep",
		"OLM Color Keep",
		"OLM Plug-ins",
		AE_RESERVED_INFO,
		"EffectMain",
		"https://olm.co.jp/");
	return result;
}

PF_Err
EffectMain(PF_Cmd cmd, PF_InData *in_data, PF_OutData *out_data,
           PF_ParamDef *params[], PF_LayerDef *output, void *extra)
{
	PF_Err err = PF_Err_NONE;
	try {
		switch (cmd) {
		case PF_Cmd_ABOUT:
			err = About(in_data, out_data, params, output); break;
		case PF_Cmd_GLOBAL_SETUP:
			err = GlobalSetup(in_data, out_data, params, output); break;
		case PF_Cmd_PARAMS_SETUP:
			err = ParamsSetup(in_data, out_data, params, output); break;
		case PF_Cmd_RENDER:
			err = Render(in_data, out_data, params, output); break;
		case PF_Cmd_USER_CHANGED_PARAM:
			err = SetColorsEnabled(in_data, params); break;
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = SetColorsEnabled(in_data, params); break;
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, (PF_PreRenderExtra*)extra); break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, (PF_SmartRenderExtra*)extra); break;
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

#include "../../ucrtmath/include/ucrtmath.h"
#include "OLMKiraKira.h"
#include "AEFX_SuiteHandlerTemplate.h"
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
#include "../../core/kirakira_gaussian.h"
#include "../../core/kirakira_highlight_gaussian.h"
#include "../../core/kirakira_highlight.h"
#include "../../core/kirakira_mode4.h"
#include "../../core/kirakira_warp.h"
#include "../../core/kirakira_merge2.h"
#include "../../core/kirakira_sincos.h"

#include "RampEditor.h"
#include <map>
#include <mutex>
#include <algorithm>
#include <cstdarg>
#include <cstdint>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <fcntl.h>
#include <unistd.h>
#include <vector>

namespace {

#include "KiraWorld.inc"

#include "KiraFilters.inc"

#include "KiraRender.inc"

#include "KiraParameters.inc"

#include "KiraAdmission.inc"

#include "KiraRampUI.inc"

// Original UPDATE: each Use Ramp toggles its solid color and arbitrary editor.
static PF_Err UpdateRampUI(PF_InData *in_data, PF_ParamDef *params[]) {
    PF_Err err=PF_Err_NONE;
    AEFX_SuiteScoper<PF_ParamUtilsSuite3> suite(in_data,kPFParamUtilsSuite,kPFParamUtilsSuiteVersion3);
    for(int use : {13,19,25,31,37}) {
        const bool ramp=params[use]->u.bd.value!=0;
        for(int slot : {use-2,use+1}) {
            PF_ParamDef def=*params[slot];
            const bool disabled=slot==use-2 ? ramp : !ramp;
            if(disabled) def.ui_flags |= PF_PUI_DISABLED;
            else def.ui_flags &= ~PF_PUI_DISABLED;
            ERR(suite->PF_UpdateParamUI(in_data->effect_ref,slot,&def));
        }
    }
    return err;
}

static PF_Err ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_Channel_Param_Name), 6, 1,
	             GetStringPtr(StrID_Channel_Choices), CHANNEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_BlurMode_Param_Name), 3, 2,
	             GetStringPtr(StrID_BlurMode_Choices), BLUR_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_MergeMode_Param_Name), 2, 1,
	             GetStringPtr(StrID_MergeMode_Choices), MERGE_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_ApproximatedInput_Param_Name), "", FALSE, 0,
	                APPROX_INPUT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BrightnessGain_Param_Name),
	                     1.0, 100.0, 1.0, 100.0, 1.0,
	                     PF_Precision_TENTHS, 0, 0, BRIGHTNESS_GAIN_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_StrengthMultiplier_Param_Name), 0, 1000, 0, 200, 100,
	              STRENGTH_MULTIPLIER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_FadeOut_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0, FADE_OUT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_GlowOpacity_Param_Name), 0, 10000, 0, 100, 100,
	              GLOW_OPACITY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_SourceOpacity_Param_Name), 0, 100, 0, 100, 100,
	              SOURCE_OPACITY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_VerticalLength_Param_Name), 0, 1000, 0, 300, 50,
	              VERTICAL_LENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_VerticalColor_Param_Name), 255, 255, 255,
	             VERTICAL_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_VerticalRamp_Param_Name), VERTICAL_RAMP_GROUP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0,
	                VERTICAL_USE_RAMP_DISK_ID);
	ERR(AddRampParam(in_data, VERTICAL_RAMP_SPACER_DISK_ID, VERTICAL_RAMP_SPACER_DISK_ID));
	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(VERTICAL_RAMP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_HorizontalLength_Param_Name), 0, 1000, 0, 300, 50,
	              HORIZONTAL_LENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_HorizontalColor_Param_Name), 255, 255, 255,
	             HORIZONTAL_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_HorizontalRamp_Param_Name), HORIZONTAL_RAMP_GROUP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0,
	                HORIZONTAL_USE_RAMP_DISK_ID);
	ERR(AddRampParam(in_data, HORIZONTAL_RAMP_SPACER_DISK_ID, HORIZONTAL_RAMP_SPACER_DISK_ID));
	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(HORIZONTAL_RAMP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_DiagonalLength_Param_Name), 0, 1000, 0, 300, 50,
	              DIAGONAL_LENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_DiagonalColor_Param_Name), 255, 255, 255,
	             DIAGONAL_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_DiagonalRamp_Param_Name), DIAGONAL_RAMP_GROUP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0, DIAGONAL_USE_RAMP_DISK_ID);
	ERR(AddRampParam(in_data, DIAGONAL_RAMP_SPACER_DISK_ID, DIAGONAL_RAMP_SPACER_DISK_ID));
	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(DIAGONAL_RAMP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Diagonal2Length_Param_Name), 0, 1000, 0, 300, 50,
	              DIAGONAL2_LENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_Diagonal2Color_Param_Name), 255, 255, 255,
	             DIAGONAL2_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_Diagonal2Ramp_Param_Name), DIAGONAL2_RAMP_GROUP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0,
	                DIAGONAL2_USE_RAMP_DISK_ID);
	ERR(AddRampParam(in_data, DIAGONAL2_RAMP_SPACER_DISK_ID, DIAGONAL2_RAMP_SPACER_DISK_ID));
	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(DIAGONAL2_RAMP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_HighlightRadius_Param_Name), 0, 500, 0, 500, 0,
	              HIGHLIGHT_RADIUS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_HighlightColor_Param_Name), 255, 255, 255,
	             HIGHLIGHT_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_HighlightRamp_Param_Name), HIGHLIGHT_RAMP_GROUP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0,
	                HIGHLIGHT_USE_RAMP_DISK_ID);
	ERR(AddRampParam(in_data, HIGHLIGHT_RAMP_SPACER_DISK_ID, HIGHLIGHT_RAMP_SPACER_DISK_ID));
	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(HIGHLIGHT_RAMP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_GlowRotation_Param_Name),
	                     -360.0, 360.0, -180.0, 180.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0, GLOW_ROTATION_DISK_ID);

	// Register the ECW event surface after defining its custom controls. The
	// Windows AEX registers exactly PF_CustomEFlag_EFFECT with all dimensions
	// and alignments zero. Without this call AE creates no effect-window
	// context and crashes in CECCustomControl::GetContext before PF_Event_DRAW.
	PF_CustomUIInfo custom_ui;
	AEFX_CLR_STRUCT(custom_ui);
	custom_ui.events = PF_CustomEFlag_EFFECT;
	ERR(PF_REGISTER_UI(in_data, &custom_ui));

	out_data->num_params = OLMKIRAKIRA_NUM_PARAMS;
	return err;
}

static PF_Err Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	KiraDiagnosticLog("classic enter");
	PF_Err err = PF_Err_NONE;
	if (!in_data || !in_data->pica_basicP || !out_data || !params || !output ||
		!params[OLMKIRAKIRA_INPUT]) {
		return OLM_KIRA_REFUSAL("classic-callback-shape");
	}
	for (A_long index = 0; index < OLMKIRAKIRA_NUM_PARAMS; ++index) {
		if (!params[index]) return OLM_KIRA_REFUSAL("classic-missing-param");
	}
	OLMKiraKiraInfo info;
	ERR(ReadRenderInfo(in_data, params, &info));
	if (err) return err;
	KiraDiagnosticInfo("classic", info);
	PF_EffectWorld *input = &params[OLMKIRAKIRA_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	ERR(ValidateWorldPair(in_data, out_data, input, output, 0, &format));
	if (err) return err;
	const ClassicClosureSourceFamily source_family =
		ClassicClosureSourceFamilyForTuple(info);
	const bool classic_closure = IsClassicClosureLayout(input, output, format);
	const bool mode3_32x18_closure =
		IsMode3Closure32x18Tuple(info) &&
		IsMode3Closure32x18Layout(input, output, format);
	const bool exact_closure =
		(classic_closure || mode3_32x18_closure) &&
		source_family != ClassicClosureSource_None &&
		ClassicClosureSourceMatches(input, format, source_family);
	// Exact bytes retain exact precedence. A different source, legal stride, or
	// content extent is intentionally reclassified into the generic lane rather
	// than inheriting the older fixture-only rejection boundary.
	const bool generic_beta =
		!exact_closure &&
		(IsGenericBetaTupleForGeometry(info, input->width, input->height) ||
		 IsAlphaBoxTuple(info, format)) &&
		IsGenericBetaClassicLayout(input, output, PixelSizeForFormat(format)) &&
		GenericBetaInputIsFiniteSDR(input, format);
	KiraDiagnosticLog("classic admission exact=%d generic=%d family=%d",
		(int)exact_closure, (int)generic_beta, (int)source_family);
	if (!exact_closure && !generic_beta) {
		KiraDiagnosticLog("classic reject tuple_layout_source");
		return OLM_KIRA_REFUSAL("tuple-layout-source");
	}
	const short bitdepth = BitDepthForFormat(format);
	ERR(RenderWorld(input, output, info, bitdepth));
	KiraDiagnosticLog("classic return error=%d", (int)err);
	return err;
}

typedef struct {
	PF_FpLong comp_width;
	PF_FpLong comp_height;
	bool generic_full_frame_request;
} PreRenderData;

constexpr A_long kSmartClosureWidth = 5;
constexpr A_long kSmartClosureHeight = 3;
constexpr A_long kMode3SmartClosureWidth = 32;
constexpr A_long kMode3SmartClosureHeight = 18;

static bool WorldStorageRangesDoNotOverlap(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output, size_t pixel_size)
{
    if (!WorldLayoutIsSafe(input, pixel_size) || !WorldLayoutIsSafe(output, pixel_size))
        return false;
    const uint64_t input_span = static_cast<uint64_t>(input->rowbytes) *
        static_cast<uint64_t>(input->height - 1) + static_cast<uint64_t>(input->width) * pixel_size;
    const uint64_t output_span = static_cast<uint64_t>(output->rowbytes) *
        static_cast<uint64_t>(output->height - 1) + static_cast<uint64_t>(output->width) * pixel_size;
	const uintptr_t input_begin = reinterpret_cast<uintptr_t>(input->data);
	const uintptr_t output_begin = reinterpret_cast<uintptr_t>(output->data);
	if (input_span > static_cast<uint64_t>(UINTPTR_MAX - input_begin) ||
		output_span > static_cast<uint64_t>(UINTPTR_MAX - output_begin)) {
		return false;
	}
	const uintptr_t input_end = input_begin + static_cast<uintptr_t>(input_span);
	const uintptr_t output_end = output_begin + static_cast<uintptr_t>(output_span);
	return input_end <= output_begin || output_end <= input_begin;
}

static bool SmartClosureWorldPairIsSafeForDimensions(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	PF_PixelFormat format,
	A_long width,
	A_long height)
{
	const size_t pixel_size = PixelSizeForFormat(format);
	const PF_WorldFlags expected_world_flags =
		format == PF_PixelFormat_ARGB32 ? 0 : PF_WorldFlag_DEEP;
	return pixel_size && input && output &&
		input->width == width && input->height == height &&
		output->width == width && output->height == height &&
		input->origin_x == 0 && input->origin_y == 0 &&
		output->origin_x == 0 && output->origin_y == 0 &&
		input->extent_hint.left == 0 && input->extent_hint.top == 0 &&
		input->extent_hint.right == width && input->extent_hint.bottom == height &&
		output->extent_hint.left == 0 && output->extent_hint.top == 0 &&
		output->extent_hint.right == width && output->extent_hint.bottom == height &&
		WorldLayoutIsSafe(input, pixel_size) && WorldLayoutIsSafe(output, pixel_size) &&
		input->world_flags == expected_world_flags &&
		output->world_flags == expected_world_flags &&
		WorldStorageRangesDoNotOverlap(input, output, pixel_size);
}

// The AEX writer uses source-width row strides and output-width/height loops
// (18114de30..18114df58); world origins and content extents are not read.
static bool SmartWorldPairHasBoundedOutput(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output, size_t pixel_size)
{
	return input && output &&
		IsSmartOwnerFullFrameDimensions(input->width, input->height) &&
		output->width <= input->width && output->height <= input->height &&
		WorldStorageRangesDoNotOverlap(input, output, pixel_size);
}

static void UnionSmartRect(const PF_LRect &source, PF_LRect &destination)
{
	// Original 181234f10: an empty destination is replaced, otherwise union
	// only a nonempty source. Preserve host-initialized output bounds.
	if (destination.left >= destination.right || destination.top >= destination.bottom) {
		destination = source;
	} else if (source.left < source.right && source.top < source.bottom) {
		destination.left = std::min(destination.left, source.left);
		destination.top = std::min(destination.top, source.top);
		destination.right = std::max(destination.right, source.right);
		destination.bottom = std::max(destination.bottom, source.bottom);
	}
}

static void DeletePreRenderData(void *data)
{
	delete reinterpret_cast<PreRenderData *>(data);
}

static PF_Err SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	if (extra && extra->input) {
		const PF_LRect &rect = extra->input->output_request.rect;
		KiraDiagnosticLog("pre enter request=%ld,%ld,%ld,%ld bitdepth=%d",
			(long)rect.left, (long)rect.top, (long)rect.right, (long)rect.bottom,
			(int)extra->input->bitdepth);
	}
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
		!extra->cb->checkout_layer) {
		KiraDiagnosticLog("pre reject callback_shape");
		return OLM_KIRA_REFUSAL("pre-callback-shape");
	}
	// Original 181151710 forwards the request unchanged; 181234f10 unions
	// checkout bounds into the output. Neither aspect nor extent is a gate.
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);
	PF_Err err = PF_Err_NONE;
	try {
		err = extra->cb->checkout_layer(in_data->effect_ref,
			OLMKIRAKIRA_INPUT, OLMKIRAKIRA_INPUT, &req, in_data->current_time,
			in_data->time_step, in_data->time_scale, &in_result);
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	if (err) {
		KiraDiagnosticLog("pre checkout_layer error=%d", (int)err);
		return err;
	}
	KiraDiagnosticLog(
		"pre checkout_result ref=%ldx%ld result=%ld,%ld,%ld,%ld max=%ld,%ld,%ld,%ld",
		(long)in_result.ref_width, (long)in_result.ref_height,
		(long)in_result.result_rect.left, (long)in_result.result_rect.top,
		(long)in_result.result_rect.right, (long)in_result.result_rect.bottom,
		(long)in_result.max_result_rect.left, (long)in_result.max_result_rect.top,
		(long)in_result.max_result_rect.right, (long)in_result.max_result_rect.bottom);

	PreRenderData *pre = new (std::nothrow) PreRenderData;
	if (!pre) {
		KiraDiagnosticLog("pre reject allocation");
		return PF_Err_OUT_OF_MEMORY;
	}
	pre->comp_width = in_result.ref_width;
	pre->comp_height = in_result.ref_height;
	pre->generic_full_frame_request = true;
	UnionSmartRect(in_result.result_rect, extra->output->result_rect);
	UnionSmartRect(in_result.max_result_rect, extra->output->max_result_rect);
	extra->output->flags |= PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS;
	extra->output->pre_render_data = pre;
	extra->output->delete_pre_render_data_func = DeletePreRenderData;
	return PF_Err_NONE;
}

static PF_Err SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	KiraDiagnosticLog("smart enter bitdepth=%d predata=%p",
		(extra && extra->input) ? (int)extra->input->bitdepth : -1,
		(extra && extra->input) ? extra->input->pre_render_data : nullptr);
	if (!in_data || !in_data->pica_basicP || !out_data || !extra ||
		!extra->input || !extra->cb ||
		!extra->cb->checkout_layer_pixels || !extra->cb->checkout_output) {
		KiraDiagnosticLog("smart reject callback_shape");
		return OLM_KIRA_REFUSAL("smart-callback-shape");
	}
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	try {
		err = extra->cb->checkout_layer_pixels(
			in_data->effect_ref, OLMKIRAKIRA_INPUT, &input_world);
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	if (err) {
		KiraDiagnosticLog("smart checkout_layer_pixels error=%d", (int)err);
		return err;
	}
	try {
		KiraDiagnosticWorld("input_after_checkout", input_world);
		if (!input_world || !input_world->data)
			err = PF_Err_BAD_CALLBACK_PARAM;
		if (!err) {
			err = extra->cb->checkout_output(in_data->effect_ref, &output_world);
			if (!err && (!output_world || !output_world->data))
				err = PF_Err_BAD_CALLBACK_PARAM;
		}
		KiraDiagnosticLog("smart checkout_output cumulative_error=%d", (int)err);
		KiraDiagnosticWorld("output_after_checkout", output_world);

		PF_PixelFormat format = PF_PixelFormat_INVALID;
		if (!err) {
			err = ValidateWorldPair(in_data, out_data, input_world, output_world,
				extra->input->bitdepth, &format, true);
		}
		KiraDiagnosticLog("smart validate_world error=%d format=%d",
			(int)err, (int)format);
		const PreRenderData *pre =
			reinterpret_cast<const PreRenderData *>(extra->input->pre_render_data);
		const bool pre_is_classic = pre &&
			pre->comp_width == kSmartClosureWidth &&
			pre->comp_height == kSmartClosureHeight;
		const bool pre_is_mode3_32x18 = pre &&
			pre->comp_width == kMode3SmartClosureWidth &&
			pre->comp_height == kMode3SmartClosureHeight;
		const bool pre_is_generic_beta = pre &&
			pre->generic_full_frame_request &&
			IsSmartOwnerFullFrameDimensions(
				static_cast<A_long>(pre->comp_width),
				static_cast<A_long>(pre->comp_height));
		const bool exact_world_layout =
			(pre_is_classic || pre_is_mode3_32x18) &&
			SmartClosureWorldPairIsSafeForDimensions(
				input_world, output_world, format,
				static_cast<A_long>(pre->comp_width),
				static_cast<A_long>(pre->comp_height));
		const bool generic_world_layout = pre &&
			SmartWorldPairHasBoundedOutput(input_world, output_world, PixelSizeForFormat(format));
		KiraDiagnosticLog(
			"smart layout pre_classic=%d pre_mode3_32=%d pre_generic=%d exact=%d generic=%d pre=%gx%g",
			(int)pre_is_classic, (int)pre_is_mode3_32x18,
			(int)pre_is_generic_beta, (int)exact_world_layout,
			(int)generic_world_layout,
			pre ? (double)pre->comp_width : -1.0,
			pre ? (double)pre->comp_height : -1.0);
		if (!err && !exact_world_layout && !generic_world_layout) {
			err = OLM_KIRA_REFUSAL("world-layout");
			KiraDiagnosticLog("smart reject world_layout");
		}
		OLMKiraKiraInfo info;
		if (!err) err = CheckoutSmartInfo(in_data, &info);
		KiraDiagnosticLog("smart checkout_info error=%d", (int)err);
		if (!err) {
			info.comp_width = input_world->width;
			if (in_data->downsample_x.num <= 0 || in_data->downsample_x.den <= 0)
				return OLM_KIRA_REFUSAL("invalid-downsample");
			if ((float)in_data->downsample_x.num / (float)in_data->downsample_x.den <= 0.5f)
				info.approximated_input = FALSE;
			KiraDiagnosticInfo("smart", info);
			const ClassicClosureSourceFamily source_family =
				ClassicClosureSourceFamilyForTuple(info);
			const bool exact_tuple_is_admitted =
				(pre_is_classic && IsClassicClosureTuple(info)) ||
				(pre_is_mode3_32x18 && IsMode3Closure32x18Tuple(info));
			// The exact fixture remains isolated by source, tuple, and full-frame
			// geometry; byte stride and base alignment do not alter its pixels.
			// Other sources still require the generic SDR and budget checks.
			const bool exact_closure = exact_world_layout &&
				exact_tuple_is_admitted &&
				source_family != ClassicClosureSource_None &&
				ClassicClosureSourceMatches(input_world, format, source_family);
			const bool generic_beta = !exact_closure &&
				generic_world_layout &&
				KiraSmartGeometryFits(input_world->width, input_world->height, info) &&
				(IsGenericBetaTupleForGeometry(
					info, input_world->width, input_world->height, true) ||
				 IsAlphaBoxTuple(info, format, true, true, true) ||
				 IsSmartScalarBrightnessBoxTuple(info, format) ||
				 IsSmartApproximationTuple(info, format, input_world->width, input_world->height) ||
				 IsSmartColorBoxTuple(info, format) ||
				 IsSmartDirectionalGaussianTuple(info, format, input_world->width, input_world->height) ||
				 IsSmartZeroRayTuple(info, input_world->width, input_world->height)) &&
				(GenericBetaInputIsFiniteSDR(input_world, format) ||
				 SmartAlphaInputIsSupported(input_world, format, info) ||
                 SmartFilteredInputIsSupported(input_world, format, info));
			KiraDiagnosticLog(
				"smart admission family=%d exact_tuple=%d exact=%d generic=%d",
				(int)source_family, (int)exact_tuple_is_admitted,
				(int)exact_closure, (int)generic_beta);
			if (!exact_closure && !generic_beta) {
				err = OLM_KIRA_REFUSAL("tuple-or-source");
				KiraDiagnosticLog("smart reject tuple_or_source");
			}
		}
		if (!err) {
			err = RenderWorld(input_world, output_world, info,
				BitDepthForFormat(format),
				(float)in_data->downsample_x.num / (float)in_data->downsample_x.den);
			KiraDiagnosticLog("smart render_world error=%d", (int)err);
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	KiraDiagnosticLog("smart return error=%d", (int)err);
	// The Windows Smart owner relies on command-lifetime validity and does not
	// invoke the SDK's optional checkin_layer_pixels callback.
	return err;
}

}  // namespace

extern "C" DllExport
PF_Err PluginDataEntryFunction2(
	PF_PluginDataPtr  inPtr,
	PF_PluginDataCB2  inPluginDataCallBackPtr,
	SPBasicSuite     *,
	const char       *,
	const char       *)
{
	PF_Err result = PF_Err_INVALID_CALLBACK;
	result = PF_REGISTER_EFFECT_EXT2(
		inPtr, inPluginDataCallBackPtr,
		"OLM Kira Kira",
		"OLM OLM Kira Kira",
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
		case PF_Cmd_SEQUENCE_SETDOWN: {
            std::lock_guard<std::recursive_mutex> guard(ramp_ui_mutex);
            ramp_ui_instances.erase(in_data->effect_ref);
            break;
        }
        case PF_Cmd_GLOBAL_SETDOWN: {
            std::lock_guard<std::recursive_mutex> guard(ramp_ui_mutex);
            ramp_ui_instances.clear();
            break;
        }
		case PF_Cmd_UPDATE_PARAMS_UI:
            err = UpdateRampUI(in_data, params); break;
		case PF_Cmd_EVENT:
			err = RampEvent(in_data, params, static_cast<PF_EventExtra *>(extra)); break;
		case PF_Cmd_ARBITRARY_CALLBACK:
			err = RampArbitraryCallback(in_data, static_cast<PF_ArbParamsExtra *>(extra)); break;
		case PF_Cmd_RENDER:
			err = Render(in_data, out_data, params, output); break;
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

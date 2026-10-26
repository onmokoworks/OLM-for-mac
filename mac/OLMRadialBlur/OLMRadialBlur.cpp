#include "RadialScatterSIMD.h"
#include "RadialRotationRows.h"
#include "../../core/olm_exact_math.h"
#include "OLMRadialBlur.h"
#include "../DynamicControls.h"
#include "../../core/dblur_noise.h"
#include "../../core/x86_float.h"
#include "../../core/olm_sha256_rows.h"

#include <AEFX_SuiteHandlerTemplate.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdlib>
#include <complex>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <exception>
#include <fcntl.h>
#include <limits>
#include <map>
#include <memory>
#include <thread>
#include <type_traits>
#include <unistd.h>
#include <vector>

// Refusal attribution for the fuzz campaign. When OLM_REFUSAL_TRACE names a
// file, each failing admission guard appends "function:tag". The file is only
// opened on a refusal, and the returned error code and all output bytes are
// identical whether or not tracing is enabled.
static PF_Err RadialRefusal(const char *function, const char *tag, int line, PF_Err err)
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

#define OLM_RADIAL_REFUSAL(tag) RadialRefusal(__func__, tag, __LINE__, PF_Err_BAD_CALLBACK_PARAM)
#define OLM_RADIAL_ERROR(tag, code) RadialRefusal(__func__, tag, __LINE__, code)

// EXPERIMENT ONLY: a scratch build may name admission-guard tags in
// OLM_RADIAL_EXPERIMENT_BYPASS to fall through those guards. Empty by default,
// so shipped behavior and output bytes are unchanged (verified by corpus replay).
#ifndef OLM_RADIAL_EXPERIMENT_BYPASS
#define OLM_RADIAL_EXPERIMENT_BYPASS ""
#endif

static bool RadialExperimentBypass(const char *tag)
{
	static constexpr const char *bypass = OLM_RADIAL_EXPERIMENT_BYPASS;
	if (bypass[0] == '\0') return false;
	const std::size_t tag_length = std::strlen(tag);
	for (const char *item = bypass; *item;) {
		const char *separator = std::strchr(item, ',');
		const std::size_t item_length = separator
			? static_cast<std::size_t>(separator - item) : std::strlen(item);
		if (item_length == tag_length && std::strncmp(item, tag, tag_length) == 0) return true;
		if (!separator) break;
		item = separator + 1;
	}
	return false;
}

#include "RadialMath.inc"
#include "RadialDiagnostics.inc"

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

static PF_Err
GlobalSetup(PF_InData *, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x06008040;
	out_data->out_flags2 = 0x08001408;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	def.flags = 0x62;
	PF_ADD_POPUP(GetStringPtr(StrID_BlurType_Param_Name),
	             2, 1, GetStringPtr(StrID_BlurType_Choices),
	             BLUR_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x60;
	PF_ADD_POINT(GetStringPtr(StrID_Center_Param_Name), 50, 50, FALSE,
	             CENTER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x20;
	PF_ADD_TOPIC(GetStringPtr(StrID_OuterBlur_Param_Name), OUTER_BLUR_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x1;
	def.ui_flags = 0x40;
	PF_ADD_SLIDER(GetStringPtr(StrID_OuterStrength_Param_Name),
	              0, 2000, 0, 2000, 0,
	              OUTER_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x62;
	PF_ADD_POPUP(GetStringPtr(StrID_OuterOffsetMode_Param_Name),
	             3, 1, GetStringPtr(StrID_OffsetMode_Choices),
	             OUTER_OFFSET_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x1;
	def.ui_flags = 0x40;
	PF_ADD_SLIDER(GetStringPtr(StrID_OuterOffset_Param_Name),
	              0, 500, 0, 500, 0,
	              OUTER_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x1;
	def.ui_flags = 0x40;
	PF_ADD_SLIDER(GetStringPtr(StrID_OuterEdgeFade_Param_Name),
	              0, 100, 0, 100, 0,
	              OUTER_EDGE_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(OUTER_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x20;
	PF_ADD_TOPIC(GetStringPtr(StrID_InnerBlur_Param_Name), INNER_BLUR_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x1;
	def.ui_flags = 0x40;
	PF_ADD_SLIDER(GetStringPtr(StrID_InnerStrength_Param_Name),
	              0, 2000, 0, 2000, 0,
	              INNER_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x62;
	PF_ADD_POPUP(GetStringPtr(StrID_InnerOffsetMode_Param_Name),
	             3, 1, GetStringPtr(StrID_OffsetMode_Choices),
	             INNER_OFFSET_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x1;
	def.ui_flags = 0x40;
	PF_ADD_SLIDER(GetStringPtr(StrID_InnerOffset_Param_Name),
	              0, 500, 0, 500, 0,
	              INNER_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x1;
	def.ui_flags = 0x40;
	PF_ADD_SLIDER(GetStringPtr(StrID_InnerEdgeFade_Param_Name),
	              0, 100, 0, 100, 0,
	              INNER_EDGE_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(INNER_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x62;
	PF_ADD_CHECKBOX(GetStringPtr(StrID_RepeatBorder_Param_Name), "", TRUE, 0,
	                REPEAT_BORDER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x20;
	PF_ADD_TOPIC(GetStringPtr(StrID_Ellipse_Param_Name), ELLIPSE_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x40;
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Ratio_Param_Name),
	                     1.0, 5.0, 1.0, 5.0, 1.0,
	                     PF_Precision_HUNDREDTHS, 0, 0x40,
	                     RATIO_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x60;
	PF_ADD_ANGLE(GetStringPtr(StrID_Angle_Param_Name), 0, ANGLE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(ELLIPSE_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x40;
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Quality_Param_Name),
	                     1.0, 50.0, 1.0, 50.0, 5.0,
	                     PF_Precision_HUNDREDTHS, 0, 0x40,
	                     QUALITY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x40;
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BrightnessGain_Param_Name),
	                     0.0, 10.0, 0.0, 2.0, 1.0,
	                     PF_Precision_TENTHS, 0, 0x40,
	                     BRIGHTNESS_GAIN_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x40;
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_SizeVariation_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0x40,
	                     SIZE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x20;
	PF_ADD_TOPIC(GetStringPtr(StrID_NoiseParams_Param_Name), NOISE_PARAMS_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x40;
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_NoiseVariation_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0x40,
	                     NOISE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x62;
	PF_ADD_POPUP(GetStringPtr(StrID_NoiseType_Param_Name),
	             3, 1, GetStringPtr(StrID_NoiseType_Choices),
	             NOISE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x62;
	PF_ADD_LAYER(GetStringPtr(StrID_NoiseLayer_Param_Name), PF_LayerDefault_NONE, NOISE_LAYER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x1;
	def.ui_flags = 0x40;
	PF_ADD_SLIDER(GetStringPtr(StrID_Seed_Param_Name),
	              1, 1000, 1, 1000, 1,
	              SEED_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x60;
	PF_ADD_ANGLE(GetStringPtr(StrID_NoiseOffset_Param_Name), 0, NOISE_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = 0x40;
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Thickness_Param_Name),
	                     1.0, 100.0, 1.0, 100.0, 10.0,
	                     PF_Precision_HUNDREDTHS, 0, 0x40,
	                     THICKNESS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(NOISE_BLANK_DISK_ID);

	out_data->num_params = OLMRADIALBLUR_NUM_PARAMS;
	return err;
}

static PF_Err
UpdateParamsUI(PF_InData *in_data, PF_ParamDef *params[])
{
	if (!params) return PF_Err_NONE;
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ParamUtilsSuite3 *param_utils = suites.ParamUtilsSuite3();

	auto set_disabled = [&](A_long index, bool disabled) {
		if (err || !params[index]) return;
		PF_ParamDef copy = *params[index];
		if (disabled) copy.ui_flags |= PF_PUI_DISABLED;
		else copy.ui_flags &= ~PF_PUI_DISABLED;
		err = param_utils->PF_UpdateParamUI(in_data->effect_ref, index, &copy);
	};

	const bool layer_noise = params[OLMRADIALBLUR_NOISE_TYPE] &&
		params[OLMRADIALBLUR_NOISE_TYPE]->u.pd.value == 3;
	ERR(OLMSetHidden(in_data, OLMRADIALBLUR_NOISE_LAYER, !layer_noise));
	ERR(OLMSetHidden(in_data, OLMRADIALBLUR_SEED, layer_noise));
	ERR(OLMSetHidden(in_data, OLMRADIALBLUR_NOISE_OFFSET, layer_noise));
	ERR(OLMSetHidden(in_data, OLMRADIALBLUR_THICKNESS, layer_noise));

	const bool rotation = params[OLMRADIALBLUR_BLUR_TYPE] &&
		params[OLMRADIALBLUR_BLUR_TYPE]->u.pd.value == 2;
	const bool outer_strength_disabled = rotation &&
		params[OLMRADIALBLUR_OUTER_OFFSET_MODE] &&
		params[OLMRADIALBLUR_OUTER_OFFSET_MODE]->u.pd.value == 3;
	const bool inner_strength_disabled = rotation &&
		params[OLMRADIALBLUR_INNER_OFFSET_MODE] &&
		params[OLMRADIALBLUR_INNER_OFFSET_MODE]->u.pd.value == 3;
	set_disabled(OLMRADIALBLUR_OUTER_STRENGTH, outer_strength_disabled);
	set_disabled(OLMRADIALBLUR_OUTER_OFFSET, !rotation);
	set_disabled(OLMRADIALBLUR_OUTER_OFFSET_MODE, !rotation);
	set_disabled(OLMRADIALBLUR_INNER_STRENGTH, inner_strength_disabled);
	set_disabled(OLMRADIALBLUR_INNER_OFFSET, !rotation);
	set_disabled(OLMRADIALBLUR_INNER_OFFSET_MODE, !rotation);


	return err;
}

// AE rowbytes are byte strides: odd padding must not create typed references
// into unaligned storage. Keep channel arithmetic on aligned local pixels.
#include "../../core/olm_world_safety.h"
#include "RadialAdmission.inc"
#include "RadialSampling.inc"
#include "RadialPixelTraits.inc"
#include "RadialZoomKernels.inc"
#if defined(OLM_RADIALBLUR_TEST_SEAM)
#include "../../tools/fuzz/harnesses/radialblur/RadialTestWorkers.inc"
#endif
#include "RadialLayerAdmission.inc"
#include "RadialZoom.inc"
#include "RadialRotation.inc"
#include "RadialLayerCompose.inc"
static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
	PF_EffectWorld *noise_world, const OLMRadialBlurInfo &info, short bitdepth,
	bool smart_render = false)
{
	if (IsRadialNoOpControlProfile(info)) return RenderRadialNoOpCopy(input, output, info, bitdepth);
	if (info.noise_type == 3 && info.noise_variation != 0.0 && !RequiresNoiseLayer(info) &&
		!RadialExperimentBypass("type3-zero-noise")) {
		// Zero Type-3 amount uses the deterministic missing-layer span contract.
		// Negative amounts remain outside the admitted layer/procedural lanes.
		return OLM_RADIAL_REFUSAL("type3-zero-noise");
	}
	if (RequiresNoiseLayer(info)) {
		PF_Err noise_err = ValidateNoiseLayerWorld(noise_world, bitdepth);
		if (noise_err) return noise_err;
		if (!RadialPayloadsDisjoint(input, noise_world, bitdepth / 8 * 4) ||
			!RadialPayloadsDisjoint(output, noise_world, bitdepth / 8 * 4)) return OLM_RADIAL_REFUSAL("noise-payload-overlap");
		// Only the exact-source 9x7 Zoom/NV25 tuple is admitted below. Every
		// other Type-3 layer state remains fail-closed in RenderZoomTyped.
		if (info.blur_type != 1) return OLM_RADIAL_REFUSAL("type3-nonzoom");
		if (bitdepth == 8) return RenderZoom8(input, output, info, noise_world);
		if (bitdepth == 16) return RenderZoom16(input, output, info, noise_world);
		if (bitdepth == 32) return RenderZoomFloat(input, output, info, noise_world);
		return OLM_RADIAL_REFUSAL("type3-bitdepth");
	}
	// Preserve the world contract for requests already owned by the generic
	// family. Expanding Offset admission must not take away the older Zoom
	// dispatch for controls that previously selected it.
	if (IsGenericRadialControlProfile(info)) {
		bool admitted = false;
		if (bitdepth == 8) admitted = IsGenericBaselineWorldPair<PF_Pixel8>(input, output, info) &&
			GenericRadialInputIsSDR<PF_Pixel8>(input);
		else if (bitdepth == 16) admitted = IsGenericBaselineWorldPair<PF_Pixel16>(input, output, info) &&
			GenericRadialInputIsSDR<PF_Pixel16>(input);
		else if (bitdepth == 32) admitted = IsGenericBaselineWorldPair<PF_PixelFloat>(input, output, info);
		else return OLM_RADIAL_REFUSAL("generic-bitdepth");
		// Before Offset expansion, generic Zoom accepted only Outer Add/0 or
		// Max/Override 2/4, with Inner Add/0. Other Zoom offset controls reached
		// RenderZoomTyped, whose own admission and F08 worker selection remain
		// authoritative outside the generic world's aligned SDR contract.
		const bool previous_generic_zoom_offsets =
			((info.outer_offset_mode == 1 && info.outer_offset == 0) ||
			 ((info.outer_offset_mode == 2 || info.outer_offset_mode == 3) &&
			  (info.outer_offset == 2 || info.outer_offset == 4))) &&
			info.inner_offset_mode == 1 && info.inner_offset == 0;
		if (!admitted && info.blur_type == 1 && !previous_generic_zoom_offsets) {
			if (bitdepth == 8) return RenderZoom8(input, output, info);
			if (bitdepth == 16) return RenderZoom16(input, output, info);
			return RenderZoomFloat(input, output, info);
		}
		if (!admitted && !RadialExperimentBypass("generic-world-not-admitted"))
			return OLM_RADIAL_REFUSAL("generic-world-not-admitted");
		// Original typed callers copy the world first and stop when all six
		// Strength, Offset and Fade integers are zero, regardless of Gain/Noise.
		if (info.outer_strength == 0 && info.inner_strength == 0 &&
			info.outer_offset == 0 && info.inner_offset == 0 &&
			info.outer_edge_fade == 0 && info.inner_edge_fade == 0) {
			const size_t pixel_bytes = bitdepth == 8 ? sizeof(PF_Pixel8) :
				bitdepth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat);
			for (A_long y = 0; y < input->height; ++y) {
				std::memcpy(reinterpret_cast<A_u_char *>(output->data) + (size_t)y * output->rowbytes,
					reinterpret_cast<const A_u_char *>(input->data) + (size_t)y * input->rowbytes,
					(size_t)input->width * pixel_bytes);
			}
			return PF_Err_NONE;
		}
		if (!CheckedRadialGenericBudget(input->width, input->height, bitdepth, info, smart_render))
			return OLM_RADIAL_ERROR("generic-budget", PF_Err_OUT_OF_MEMORY);
	}
	if (bitdepth == 8) {
		if (info.blur_type == 2) return RenderRotationTyped<PF_Pixel8>(input, output, info);
		return RenderZoom8(input, output, info);
	}
	if (bitdepth == 16) {
		if (info.blur_type == 2) return RenderRotationTyped<PF_Pixel16>(input, output, info);
		return RenderZoom16(input, output, info);
	}
	if (bitdepth == 32) {
		if (info.blur_type == 2) return RenderRotationTyped<PF_PixelFloat>(input, output, info);
		return RenderZoomFloat(input, output, info);
	}
	return OLM_RADIAL_REFUSAL("render-bitdepth");
}

#if defined(OLM_RADIALBLUR_TEST_SEAM)
#include "../../tools/fuzz/harnesses/radialblur/RadialTestEntry.inc"
#endif
static OLMRadialBlurInfo InfoFromParams(PF_ParamDef *params[], PF_FpLong comp_width, PF_FpLong comp_height)
{
	OLMRadialBlurInfo info;
	info.blur_type = params[OLMRADIALBLUR_BLUR_TYPE]->u.pd.value;
	info.center_x = (PF_FpLong)params[OLMRADIALBLUR_CENTER]->u.td.x_value / 65536.0;
	info.center_y = (PF_FpLong)params[OLMRADIALBLUR_CENTER]->u.td.y_value / 65536.0;
	info.outer_strength = params[OLMRADIALBLUR_OUTER_STRENGTH]->u.sd.value;
	// ParamsSetup declares integer sliders; native e270 preserves their i32 values.
	info.outer_edge_fade = params[OLMRADIALBLUR_OUTER_EDGE_FADE]->u.sd.value;
	info.outer_offset_mode = params[OLMRADIALBLUR_OUTER_OFFSET_MODE]->u.pd.value;
	info.outer_offset = params[OLMRADIALBLUR_OUTER_OFFSET]->u.sd.value;
	info.inner_strength = params[OLMRADIALBLUR_INNER_STRENGTH]->u.sd.value;
	info.inner_edge_fade = params[OLMRADIALBLUR_INNER_EDGE_FADE]->u.sd.value;
	info.inner_offset_mode = params[OLMRADIALBLUR_INNER_OFFSET_MODE]->u.pd.value;
	info.inner_offset = params[OLMRADIALBLUR_INNER_OFFSET]->u.sd.value;
	info.repeat_border = params[OLMRADIALBLUR_REPEAT_BORDER]->u.bd.value;
	info.ratio = params[OLMRADIALBLUR_RATIO]->u.fs_d.value;
	info.angle_deg = (PF_FpLong)params[OLMRADIALBLUR_ANGLE]->u.ad.value / 65536.0;
	info.quality = params[OLMRADIALBLUR_QUALITY]->u.fs_d.value;
	info.brightness_gain = params[OLMRADIALBLUR_BRIGHTNESS_GAIN]->u.fs_d.value;
	info.size_variation = params[OLMRADIALBLUR_SIZE_VARIATION]->u.fs_d.value;
	info.noise_variation = params[OLMRADIALBLUR_NOISE_VARIATION]->u.fs_d.value;
	info.noise_type = params[OLMRADIALBLUR_NOISE_TYPE]->u.pd.value;
	info.noise_layer = params[OLMRADIALBLUR_NOISE_LAYER]->u.ld.dephault;
	info.seed = params[OLMRADIALBLUR_SEED]->u.sd.value;
	info.noise_offset = RadialNoiseOffsetRadians(
		params[OLMRADIALBLUR_NOISE_OFFSET]->u.ad.value);
	info.thickness = params[OLMRADIALBLUR_THICKNESS]->u.fs_d.value;
	info.comp_width = comp_width;
	info.comp_height = comp_height;
	return info;
}

static PF_Err
GetRadialPixelFormats(
	PF_InData *in_data,
	const PF_EffectWorld *input_world,
	const PF_EffectWorld *output_world,
	const PF_EffectWorld *noise_world,
	PF_PixelFormat *input_format,
	PF_PixelFormat *output_format,
	PF_PixelFormat *noise_format)
{
	if (!in_data || !input_world || !output_world || !input_format || !output_format ||
		(noise_world && !noise_format) || !in_data->pica_basicP ||
		!in_data->pica_basicP->AcquireSuite || !in_data->pica_basicP->ReleaseSuite) {
		return OLM_RADIAL_REFUSAL("pixel-format-inputs");
	}
	const void *suite_ptr = NULL;
	PF_Err err = PF_Err_NONE;
	bool acquired = false;
	try {
		const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
			kPFWorldSuite, kPFWorldSuiteVersion2, &suite_ptr);
		if (acquire_err != kSPNoError) {
			err = static_cast<PF_Err>(acquire_err);
		} else {
			acquired = true;
			const PF_WorldSuite2 *world_suite =
				reinterpret_cast<const PF_WorldSuite2 *>(suite_ptr);
			if (!world_suite || !world_suite->PF_GetPixelFormat) {
				err = OLM_RADIAL_REFUSAL("world-suite-missing-getpixelformat");
			} else {
				err = world_suite->PF_GetPixelFormat(input_world, input_format);
				if (!err) err = world_suite->PF_GetPixelFormat(output_world, output_format);
				if (!err && noise_world) {
					err = world_suite->PF_GetPixelFormat(noise_world, noise_format);
				}
			}
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = OLM_RADIAL_ERROR("format-bad-alloc", PF_Err_OUT_OF_MEMORY);
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	if (acquired) {
		try {
			const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
				kPFWorldSuite, kPFWorldSuiteVersion2);
			if (!err && release_err != kSPNoError) err = static_cast<PF_Err>(release_err);
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = OLM_RADIAL_ERROR("format-release-bad-alloc", PF_Err_OUT_OF_MEMORY);
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
	return err;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	if (!in_data || !out_data || !params || !output ||
		!params[OLMRADIALBLUR_INPUT]) return OLM_RADIAL_REFUSAL("render-params-null");
	for (A_long index = 1; index < OLMRADIALBLUR_NUM_PARAMS; ++index) {
		if (!params[index]) return OLM_RADIAL_REFUSAL("render-param-null");
	}
	OLMRadialBlurInfo info = InfoFromParams(params,
		params[OLMRADIALBLUR_INPUT]->u.ld.width,
		params[OLMRADIALBLUR_INPUT]->u.ld.height);
	PF_EffectWorld *input = &params[OLMRADIALBLUR_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	PF_PixelFormat noise_format = PF_PixelFormat_INVALID;
	PF_EffectWorld *noise_world = NULL;
	if (RequiresNoiseLayer(info)) {
		if (!params[OLMRADIALBLUR_NOISE_LAYER]) return OLM_RADIAL_REFUSAL("render-noise-param-null");
		noise_world = &params[OLMRADIALBLUR_NOISE_LAYER]->u.ld;
	}
	PF_Err err = GetRadialPixelFormats(in_data, input, output, noise_world,
		&format, &output_format, noise_world ? &noise_format : NULL);
	if (err) return err;
	if (output_format != format || (noise_world && noise_format != format)) {
		return OLM_RADIAL_REFUSAL("render-format-mismatch");
	}

	short bitdepth = 0;
	switch (format) {
	case PF_PixelFormat_ARGB32:
		bitdepth = 8;
		break;
	case PF_PixelFormat_ARGB64:
		bitdepth = 16;
		break;
	case PF_PixelFormat_ARGB128:
		bitdepth = 32;
		break;
	default:
		return OLM_RADIAL_REFUSAL("render-bitdepth-unknown");
	}
	return RenderWorld(input, output, noise_world, info, bitdepth);
}

typedef struct {
	PF_FpLong comp_width;
	PF_FpLong comp_height;
	PF_Boolean requires_noise_layer;
} PreRenderData;

#include "RadialWorldStorage.inc"
static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
		!extra->cb->checkout_layer || !in_data->inter.checkout_param ||
		!in_data->inter.checkin_param) return OLM_RADIAL_REFUSAL("prerender-inputs");
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	req.preserve_rgb_of_zero_alpha = TRUE;
	// AEX 4010 forwards the requested rectangle and unions the checkout's
	// result/max rectangles. Extent hints and pixel aspect do not crop it.
	PF_CheckoutResult in_result = {};
	PF_CheckoutResult noise_result = {};
	PF_ParamDef noise_type;
	PF_ParamDef noise_variation;
	AEFX_CLR_STRUCT(noise_type);
	AEFX_CLR_STRUCT(noise_variation);
	bool noise_type_checked_out = false;
	bool noise_variation_checked_out = false;
	bool requires_noise_layer = false;

	std::exception_ptr thrown;
	try {
		err = PF_CHECKOUT_PARAM(in_data, OLMRADIALBLUR_NOISE_TYPE,
			in_data->current_time, in_data->time_step, in_data->time_scale, &noise_type);
		noise_type_checked_out = err == PF_Err_NONE;
		if (!err) {
			err = PF_CHECKOUT_PARAM(in_data, OLMRADIALBLUR_NOISE_VARIATION,
				in_data->current_time, in_data->time_step, in_data->time_scale, &noise_variation);
			noise_variation_checked_out = err == PF_Err_NONE;
		}
		if (!err) requires_noise_layer = noise_type.u.pd.value == 3 &&
			noise_variation.u.fs_d.value > 0.0;
	} catch (...) {
		thrown = std::current_exception();
	}
	if (noise_variation_checked_out) {
		try {
			const PF_Err checkin_err = PF_CHECKIN_PARAM(in_data, &noise_variation);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) { if (!err && !thrown) thrown = std::current_exception(); }
	}
	if (noise_type_checked_out) {
		try {
			const PF_Err checkin_err = PF_CHECKIN_PARAM(in_data, &noise_type);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) { if (!err && !thrown) thrown = std::current_exception(); }
	}
	if (thrown) std::rethrow_exception(thrown);
	if (err) return err;

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMRADIALBLUR_INPUT, OLMRADIALBLUR_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));
	if (!err && requires_noise_layer) {
		ERR(extra->cb->checkout_layer(in_data->effect_ref,
			OLMRADIALBLUR_NOISE_LAYER, OLMRADIALBLUR_NOISE_LAYER, &req,
			in_data->current_time, in_data->time_step, in_data->time_scale,
			&noise_result));
	}

	if (!err) {
		std::unique_ptr<PreRenderData> pre(new PreRenderData);
		pre->comp_width = in_result.ref_width > 0 ? (PF_FpLong)in_result.ref_width : 0.0;
		pre->comp_height = in_result.ref_height > 0 ? (PF_FpLong)in_result.ref_height : 0.0;
		pre->requires_noise_layer = requires_noise_layer ? TRUE : FALSE;
		// The source checkout defines the renderable result, including ROI and
		// downsampled bounds. Do not advertise full-resolution composition size.
		extra->output->result_rect = in_result.result_rect;
		extra->output->max_result_rect = in_result.max_result_rect;
		extra->output->flags = (PF_RenderOutputFlags)(
			extra->output->flags | PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS);
		extra->output->pre_render_data = pre.release();
		extra->output->delete_pre_render_data_func = DeletePreRenderData;
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	if (!in_data || !out_data || !extra || !extra->input || !extra->cb ||
		!extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
		!extra->cb->checkin_layer_pixels || !in_data->inter.checkout_param ||
		!in_data->inter.checkin_param) return OLM_RADIAL_REFUSAL("smartrender-inputs");
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *noise_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	const PreRenderData *pre =
		reinterpret_cast<const PreRenderData *>(extra->input->pre_render_data);
	const bool requires_noise_layer = pre && pre->requires_noise_layer != FALSE;
	bool input_checked_out = false;
	bool noise_checked_out = false;
	PF_ParamDef checked[OLMRADIALBLUR_NUM_PARAMS] = {};
	PF_ParamDef *param_ptrs[OLMRADIALBLUR_NUM_PARAMS] = {};
	bool param_checked_out[OLMRADIALBLUR_NUM_PARAMS] = {};
	std::vector<std::uint8_t> staged_output;
	std::vector<PF_Pixel16> aligned_input16;
	std::vector<PF_PixelFloat> aligned_input32;
	PF_EffectWorld aligned_input_world = {};
	PF_EffectWorld staged_world = {};
	std::size_t active_row_bytes = 0;
	std::size_t output_row_bytes = 0;
	bool render_complete = false;
	bool no_op_copy = false;
	std::exception_ptr thrown;
	try {
		err = extra->cb->checkout_layer_pixels(
			in_data->effect_ref, OLMRADIALBLUR_INPUT, &input_world);
		input_checked_out = err == PF_Err_NONE;
		if (!err && (!input_world || !input_world->data)) err = OLM_RADIAL_REFUSAL("smartrender-input-world");
		if (!err && requires_noise_layer) {
			err = extra->cb->checkout_layer_pixels(
				in_data->effect_ref, OLMRADIALBLUR_NOISE_LAYER, &noise_world);
			noise_checked_out = err == PF_Err_NONE;
			// C57: the original accepts a zero-sized descriptor, then clears
			// context+A8 on the dimension check. A null descriptor itself is
			// dereferenced by the original and remains outside this contract.
			if (!err && (!noise_world || (!noise_world->data &&
				(noise_world->width != 0 || noise_world->height != 0))))
				err = OLM_RADIAL_REFUSAL("smartrender-noise-world");
			if (!err && !noise_world->data) noise_world = nullptr;
		}
		if (!err) {
			err = extra->cb->checkout_output(in_data->effect_ref, &output_world);
			if (!err && (!output_world || !output_world->data)) err = OLM_RADIAL_REFUSAL("smartrender-output-world");
		}
		if (!err && (!pre || input_world->width <= 0 || input_world->height <= 0 ||
			output_world->width <= 0 || output_world->height <= 0 ||
			output_world->width > input_world->width || output_world->height > input_world->height))
			err = OLM_RADIAL_REFUSAL("smartrender-world-bounds");

		if (!err && (!RadialPayloadsDisjoint(input_world, output_world, extra->input->bitdepth / 8 * 4) ||
			(noise_world && (!RadialPayloadsDisjoint(input_world, noise_world, extra->input->bitdepth / 8 * 4) ||
			                 !RadialPayloadsDisjoint(output_world, noise_world, extra->input->bitdepth / 8 * 4))))) {
			err = OLM_RADIAL_REFUSAL("smartrender-payload-overlap");
		}
		for (int i = 1; !err && i < OLMRADIALBLUR_NUM_PARAMS; ++i) {
			AEFX_CLR_STRUCT(checked[i]);
			err = PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
				in_data->time_step, in_data->time_scale, &checked[i]);
			if (!err) {
				param_checked_out[i] = true;
				param_ptrs[i] = &checked[i];
			}
		}
		param_ptrs[OLMRADIALBLUR_INPUT] = NULL;

		PF_FpLong comp_w = input_world ? input_world->width : 0.0;
		PF_FpLong comp_h = input_world ? input_world->height : 0.0;
		if (pre) {
			if (pre->comp_width > 0.0) comp_w = pre->comp_width;
			if (pre->comp_height > 0.0) comp_h = pre->comp_height;
		}
		if (!err) {
			OLMRadialBlurInfo info = InfoFromParams(param_ptrs, comp_w, comp_h);
			// Getter de60/1a190 undoes per-axis sampling before the caller
			// subtracts source origins and applies the single float32 X ratio.
			if (in_data->downsample_x.num && in_data->downsample_y.num &&
				in_data->downsample_x.den && in_data->downsample_y.den) {
				info.smart_downsample = RadialF32Div((float)in_data->downsample_x.num,
					(float)in_data->downsample_x.den);
				info.center_x = (info.center_x * ((double)in_data->downsample_x.den / in_data->downsample_x.num)
					- input_world->origin_x) * (double)info.smart_downsample;
				info.center_y = (info.center_y * ((double)in_data->downsample_y.den / in_data->downsample_y.num)
					- input_world->origin_y) * (double)info.smart_downsample;
			}
			info.comp_width = input_world->width;
			info.comp_height = input_world->height;
			no_op_copy = info.outer_strength == 0 && info.inner_strength == 0 &&
				info.outer_offset == 0 && info.inner_offset == 0 &&
				info.outer_edge_fade == 0 && info.inner_edge_fade == 0;
			if (RequiresNoiseLayer(info) != requires_noise_layer) {
				err = OLM_RADIAL_REFUSAL("smartrender-noise-requirement");
			}
			// With an empty checked-out Layer the original never reads Noise
			// Variation: its span allocation is left unwritten. Reuse C46's
			// deterministic zero-span contract, preserving the size/fade plane.
			if (!err && requires_noise_layer && !noise_world)
				info.noise_variation = 0.0;
			if (!err) {
				PF_PixelFormat input_format = PF_PixelFormat_INVALID;
				PF_PixelFormat noise_format = PF_PixelFormat_INVALID;
				PF_PixelFormat output_format = PF_PixelFormat_INVALID;
				err = GetRadialPixelFormats(in_data, input_world, output_world, noise_world,
					&input_format, &output_format, noise_world ? &noise_format : NULL);
				PF_PixelFormat expected_format = PF_PixelFormat_INVALID;
				switch (extra->input->bitdepth) {
				case 8: expected_format = PF_PixelFormat_ARGB32; break;
				case 16: expected_format = PF_PixelFormat_ARGB64; break;
				case 32: expected_format = PF_PixelFormat_ARGB128; break;
				default: break;
				}
				if (!err && (expected_format == PF_PixelFormat_INVALID ||
					input_format != expected_format || output_format != expected_format ||
					(noise_world && noise_format != expected_format))) err = OLM_RADIAL_REFUSAL("smartrender-format");
			}
			const std::size_t input_alignment = extra->input->bitdepth == 16 ? alignof(PF_Pixel16) :
				extra->input->bitdepth == 32 ? alignof(PF_PixelFloat) : 1;
			const bool stage_input = !IsRadialNoOpControlProfile(info) &&
				((reinterpret_cast<std::uintptr_t>(input_world->data) % input_alignment) != 0 ||
				 (static_cast<std::size_t>(input_world->rowbytes) % input_alignment) != 0);
			if (!err && !IsRadialNoOpControlProfile(info) && IsGenericRadialControlProfile(info) &&
				!CheckedRadialGenericBudget(input_world->width, input_world->height,
					extra->input->bitdepth, info, true, nullptr, nullptr, stage_input)) {
				err = OLM_RADIAL_ERROR("smartrender-generic-budget", PF_Err_OUT_OF_MEMORY);
			}
			std::uintptr_t output_begin = 0, output_end = 0;
			if (!err && (!RadialPayloadSpan(output_world, &output_begin, &output_end, extra->input->bitdepth / 8 * 4) ||
				!RadialActiveRowBytes(extra->input->bitdepth, output_world->width,
				                          &active_row_bytes) ||
				active_row_bytes > static_cast<std::size_t>(output_world->rowbytes))) {
				err = OLM_RADIAL_REFUSAL("smartrender-output-span");
			}
			output_row_bytes = active_row_bytes;
			if (!err && (!RadialActiveRowBytes(extra->input->bitdepth, input_world->width, &active_row_bytes) ||
				active_row_bytes > static_cast<std::size_t>(input_world->rowbytes) ||
				active_row_bytes > static_cast<std::size_t>(std::numeric_limits<A_long>::max())))
				err = OLM_RADIAL_REFUSAL("smartrender-input-rowbytes");
			if (!err) {
				const std::size_t height = static_cast<std::size_t>(input_world->height);
				if (height == 0 || active_row_bytes >
					std::numeric_limits<std::size_t>::max() / height) {
					err = OLM_RADIAL_REFUSAL("smartrender-stage-overflow");
				} else {
					staged_output.assign(active_row_bytes * height, 0);
				}
			}
			if (!err) {
				staged_world = *input_world;
				staged_world.data = reinterpret_cast<PF_PixelPtr>(staged_output.data());
				staged_world.rowbytes = static_cast<A_long>(active_row_bytes);
				#if defined(OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE)
				ERR(CaptureDiagnosticPF32World("input", input_world, info, extra->input->bitdepth));
				#endif
				PF_EffectWorld *render_input = input_world;
				// AE worlds are byte-strided. Preserve every active input byte while
				// giving the typed workers (including admission probes) aligned rows.
				// The original checked-out world remains owned by the host; no-op
				// copies retain their byte-only path. Output publication stays atomic.
				if (!err && stage_input) {
					if (active_row_bytes > static_cast<std::size_t>(input_world->rowbytes)) {
						err = OLM_RADIAL_REFUSAL("smartrender-input-rowbytes");
					} else {
						const std::size_t bytes = active_row_bytes * static_cast<std::size_t>(input_world->height);
						void *aligned_data = nullptr;
						if (extra->input->bitdepth == 16) {
							aligned_input16.resize(bytes / sizeof(PF_Pixel16));
							aligned_data = aligned_input16.data();
						} else {
							aligned_input32.resize(bytes / sizeof(PF_PixelFloat));
							aligned_data = aligned_input32.data();
						}
						for (A_long y = 0; y < input_world->height; ++y)
							std::memcpy(reinterpret_cast<std::uint8_t *>(aligned_data) +
								static_cast<std::size_t>(y) * active_row_bytes,
								reinterpret_cast<const std::uint8_t *>(input_world->data) +
								static_cast<std::size_t>(y) * input_world->rowbytes, active_row_bytes);
						aligned_input_world = *input_world;
						aligned_input_world.data = reinterpret_cast<PF_PixelPtr>(aligned_data);
						aligned_input_world.rowbytes = static_cast<A_long>(active_row_bytes);
						render_input = &aligned_input_world;
					}
				}
				if (!err) err = RenderWorld(render_input, &staged_world, noise_world, info,
				                            extra->input->bitdepth, true);
				render_complete = err == PF_Err_NONE;
				#if defined(OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE)
				if (!err) ERR(CaptureDiagnosticPF32World("output", &staged_world, info,
				                                             extra->input->bitdepth));
				#endif
			}
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	for (int i = 1; i < OLMRADIALBLUR_NUM_PARAMS; ++i) {
		if (!param_checked_out[i]) continue;
		try {
			const PF_Err checkin_err = PF_CHECKIN_PARAM(in_data, &checked[i]);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (noise_checked_out) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
				in_data->effect_ref, OLMRADIALBLUR_NOISE_LAYER);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (input_checked_out) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
				in_data->effect_ref, OLMRADIALBLUR_INPUT);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (thrown) std::rethrow_exception(thrown);
	if (!err && render_complete) {
		// AEX's typed writer indexes the computed plane with OUTPUT width,
		// without an output-origin adjustment (7360..741b). Its initial suite
		// copy, retained by the no-op branch, instead preserves source rows.
		for (A_long y = 0; y < output_world->height; ++y) {
			std::memcpy(reinterpret_cast<std::uint8_t *>(output_world->data) +
					static_cast<std::size_t>(y) * output_world->rowbytes,
				staged_output.data() + static_cast<std::size_t>(y) *
					(no_op_copy ? active_row_bytes : output_row_bytes),
				output_row_bytes);
		}
	}
	return err;
}

extern "C" DllExport
PF_Err PluginDataEntryFunction2(
	PF_PluginDataPtr  inPtr,
	PF_PluginDataCB2  inPluginDataCallBackPtr,
	SPBasicSuite      *,
	const char        *,
	const char        *,
	PF_PluginDataPtr)
{
	PF_Err result = PF_Err_INVALID_CALLBACK;
	result = PF_REGISTER_EFFECT_EXT2(
		inPtr,
		inPluginDataCallBackPtr,
		"OLM RadialBlur",
		"OLM RadialBlur",
		"OLM Plug-ins",
		AE_RESERVED_INFO,
		"EffectMain",
		"https://olm.co.jp/");
	return result;
}

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
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParamsUI(in_data, params);
			break;
		case PF_Cmd_USER_CHANGED_PARAM:
		case PF_Cmd_EVENT:
			// The pinned AEX handlers are no-ops for the current standard
			// parameter surface. EVENT only dispatches for a legacy custom
			// parameter type which none of the 30 definitions uses.
			break;
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, reinterpret_cast<PF_PreRenderExtra *>(extra));
			break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, reinterpret_cast<PF_SmartRenderExtra *>(extra));
			break;
		default:
			break;
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = OLM_RADIAL_ERROR("effectmain-bad-alloc", PF_Err_OUT_OF_MEMORY);
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return err;
}

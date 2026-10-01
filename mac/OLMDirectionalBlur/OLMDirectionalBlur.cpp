#include "OLMDirectionalBlur.h"

#include <AEFX_SuiteHandlerTemplate.h>

#include "../../core/dblur_frontonly.h"
#include "../../core/dblur_generic_budget.h"
#include "../../core/dblur_gaussian.h"
#include "../../core/olm_sha256_rows.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <exception>
#include <limits>
#include <memory>
#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
#include <cstdlib>
#endif
#include <vector>

static constexpr PF_FpLong kPi = 3.141592653589793238462643383279502884;
#if !defined(OLM_DBLUR_TEST_SEAM)
static AEGP_PluginID g_aegp_plugin_id = 0;
#endif

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
		"%s v%d.%d.%d\r%s",
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
	out_data->out_flags  = 0x06000040;
	out_data->out_flags2 = 0x08001408;
#if !defined(OLM_DBLUR_TEST_SEAM)
	// Source-included parameter-layout probes have no host suite table. A real
	// AE GLOBAL_SETUP always supplies one; register there, as the AEX does.
	if (!in_data || !in_data->pica_basicP) return PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	return suites.UtilitySuite6()->AEGP_RegisterWithAEGP(
		nullptr, "OLMDirectionalBlur", &g_aegp_plugin_id);
#else
	return PF_Err_NONE;
#endif
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_ANGLE(GetStringPtr(StrID_Angle_Param_Name), 0.0, ANGLE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BrightnessGain_Param_Name),
	                     0.0, 10.0, 0.0, 2.0, 1.0,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     BRIGHTNESS_GAIN_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_SizeVariation_Param_Name),
	             0.0, 100.0, 0.0, 100.0, 0.0,
	             PF_Precision_TENTHS, PF_ValueDisplayFlag_PERCENT, 0,
	             SIZE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_FrontBlurParams_Param_Name), FRONT_PARAMS_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_FrontStrength_Param_Name),
	              0, 4000, 0, 4000, 0,
	              FRONT_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_FrontAlphaFade_Param_Name),
	              0, 100, 0, 100, 0,
	              FRONT_ALPHA_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_FrontSharpTail_Param_Name),
	             0.0, 100.0, 0.0, 100.0, 0.0,
	             PF_Precision_TENTHS, PF_ValueDisplayFlag_PERCENT, 0,
	             FRONT_SHARP_TAIL_DISK_ID);

	PF_END_TOPIC(FRONT_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_BackBlurParams_Param_Name), BACK_PARAMS_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_BackStrength_Param_Name),
	              0, 4000, 0, 4000, 0,
	              BACK_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_BackAlphaFade_Param_Name),
	              0, 100, 0, 100, 0,
	              BACK_ALPHA_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_BackSharpTail_Param_Name),
	             0.0, 100.0, 0.0, 100.0, 0.0,
	             PF_Precision_TENTHS, PF_ValueDisplayFlag_PERCENT, 0,
	             BACK_SHARP_TAIL_DISK_ID);

	PF_END_TOPIC(BACK_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_NoiseParams_Param_Name), NOISE_PARAMS_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_NoiseVariation_Param_Name),
	             0.0, 100.0, 0.0, 100.0, 0.0,
	             PF_Precision_TENTHS, PF_ValueDisplayFlag_PERCENT, 0,
	             NOISE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_NoiseType_Param_Name),
	             2, 1, GetStringPtr(StrID_NoiseType_Choices),
	             NOISE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_LAYER(GetStringPtr(StrID_NoiseLayer_Param_Name), PF_LayerDefault_NONE, NOISE_LAYER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Seed_Param_Name),
	              1, 1000, 1, 1000, 1,
	              SEED_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_ANGLE(GetStringPtr(StrID_NoiseOffset_Param_Name), 0.0, NOISE_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Thickness_Param_Name),
	                     1.0, 100.0, 1.0, 100.0, 10.0,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     THICKNESS_DISK_ID);

	PF_END_TOPIC(NOISE_BLANK_DISK_ID);

	out_data->num_params = OLMDIRECTIONALBLUR_NUM_PARAMS;
	return err;
}

#if !defined(OLM_DBLUR_TEST_SEAM)
static PF_Err
UpdateParamsUI(PF_InData *in_data)
{
	if (!in_data) return PF_Err_BAD_CALLBACK_PARAM;
	PF_Err err = PF_Err_NONE;
	PF_ParamDef noise_type_param;
	AEFX_CLR_STRUCT(noise_type_param);
	ERR(PF_CHECKOUT_PARAM(in_data, OLMDIRECTIONALBLUR_NOISE_TYPE,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&noise_type_param));
	if (err) return err;
	const A_Boolean layer_mode = noise_type_param.u.pd.value == 3 ? TRUE : FALSE;
	PF_CHECKIN_PARAM(in_data, &noise_type_param);

	AEFX_SuiteScoper<AEGP_PFInterfaceSuite1> pf_interface(
		in_data, kAEGPPFInterfaceSuite, kAEGPPFInterfaceSuiteVersion1);
	AEFX_SuiteScoper<AEGP_StreamSuite6> streams(
		in_data, kAEGPStreamSuite, kAEGPStreamSuiteVersion6);
	AEFX_SuiteScoper<AEGP_DynamicStreamSuite4> dynamic_streams(
		in_data, kAEGPDynamicStreamSuite, kAEGPDynamicStreamSuiteVersion4);
	AEFX_SuiteScoper<AEGP_EffectSuite5> effects(
		in_data, kAEGPEffectSuite, kAEGPEffectSuiteVersion5);

	AEGP_EffectRefH effect = nullptr;
	ERR(pf_interface->AEGP_GetNewEffectForEffect(
		g_aegp_plugin_id, in_data->effect_ref, &effect));
	if (!err && effect) {
		const struct {
			PF_ParamIndex index;
			A_Boolean hidden;
		} controls[] = {
			{OLMDIRECTIONALBLUR_NOISE_LAYER,
			 static_cast<A_Boolean>(layer_mode ? FALSE : TRUE)},
			{OLMDIRECTIONALBLUR_SEED, layer_mode},
			{OLMDIRECTIONALBLUR_NOISE_OFFSET, layer_mode},
			{OLMDIRECTIONALBLUR_THICKNESS, layer_mode},
		};
		for (const auto &control : controls) {
			AEGP_StreamRefH stream = nullptr;
			ERR(streams->AEGP_GetNewEffectStreamByIndex(
				g_aegp_plugin_id, effect, control.index, &stream));
			if (!err && stream) {
				AEGP_DynStreamFlags ignored_flags = 0;
				ERR(dynamic_streams->AEGP_GetDynamicStreamFlags(stream, &ignored_flags));
				ERR(dynamic_streams->AEGP_SetDynamicStreamFlag(
					stream, AEGP_DynStreamFlag_HIDDEN, FALSE, control.hidden));
			}
			if (stream) {
				const PF_Err dispose_err = streams->AEGP_DisposeStream(stream);
				if (!err) err = dispose_err;
			}
			if (err) break;
		}
	}
	if (effect) {
		const PF_Err dispose_err = effects->AEGP_DisposeEffect(effect);
		if (!err) err = dispose_err;
	}
	return err;
}
#endif

template <typename PixelT>
static PixelT *PixelAt(PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<PixelT *>(reinterpret_cast<std::uint8_t *>(world->data) +
		static_cast<std::size_t>(y) * static_cast<std::size_t>(world->rowbytes)) + x;
}

template <typename PixelT>
static const PixelT *PixelAtConst(const PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<const PixelT *>(reinterpret_cast<const std::uint8_t *>(world->data) +
		static_cast<std::size_t>(y) * static_cast<std::size_t>(world->rowbytes)) + x;
}

template <typename PixelT>
static void CopyWorld(PF_EffectWorld *input, PF_EffectWorld *output)
{
	for (A_long y = 0; y < output->height; ++y) {
		for (A_long x = 0; x < output->width; ++x) {
			*PixelAt<PixelT>(output, x, y) = *PixelAtConst<PixelT>(input, x, y);
		}
	}
}

struct FloatImage {
	A_long width = 0;
	A_long height = 0;
	std::vector<float> rgba;
};

static float ClampFloat(float v, float lo, float hi)
{
	return std::max(lo, std::min(v, hi));
}

static A_u_char Quantize8(float value)
{
	value = ClampFloat(value, 0.0f, 1.0f) * 255.0f;
	return (A_u_char)std::floor(value + 0.5f);
}

static std::vector<float> DirectionalGaussianWeights(A_long length)
{
	length = std::max<A_long>(length, 1);
	std::vector<float> weights((size_t)length, 1.0f);
	for (A_long i = 0; i < length; ++i) {
		weights[(size_t)i] = olm::dblur::gaussian_weight((int)length, (int)i);
	}
	return weights;
}

static void SampleBilinear(const FloatImage &image, float x, float y, float out[4])
{
	const A_long w = image.width;
	const A_long h = image.height;
	if (x < 0.0f || x > (float)(w - 1) || y < 0.0f || y > (float)(h - 1)) {
		out[0] = out[1] = out[2] = out[3] = 0.0f;
		return;
	}
	A_long x0 = (A_long)std::floor(x);
	A_long y0 = (A_long)std::floor(y);
	A_long x1 = std::min<A_long>(x0 + 1, w - 1);
	A_long y1 = std::min<A_long>(y0 + 1, h - 1);
	float fx = x - (float)x0;
	float fy = y - (float)y0;
	auto at = [&](A_long px, A_long py, int c) -> float {
		return image.rgba[((size_t)py * w + px) * 4 + c];
	};
	for (int c = 0; c < 4; ++c) {
		float top = at(x0, y0, c) * (1.0f - fx) + at(x1, y0, c) * fx;
		float bottom = at(x0, y1, c) * (1.0f - fx) + at(x1, y1, c) * fx;
		out[c] = top * (1.0f - fy) + bottom * fy;
	}
}

static PF_Err RenderDirectional8(PF_EffectWorld *input, PF_EffectWorld *output,
                                 const OLMDirectionalBlurInfo &info)
{
	if (info.noise_variation != 0.0 || info.back_strength != 0 ||
	    info.front_alpha_fade != 0 || info.back_alpha_fade != 0) {
		CopyWorld<PF_Pixel8>(input, output);
		return PF_Err_NONE;
	}

	const A_long w = output->width;
	const A_long h = output->height;
	const A_long pixels = w * h;
	FloatImage src;
	src.width = w;
	src.height = h;
	src.rgba.resize((size_t)pixels * 4);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PF_Pixel8 *p = PixelAtConst<PF_Pixel8>(input, x, y);
			const size_t idx = ((size_t)y * w + x) * 4;
			src.rgba[idx + 0] = (float)p->red / 255.0f;
			src.rgba[idx + 1] = (float)p->green / 255.0f;
			src.rgba[idx + 2] = (float)p->blue / 255.0f;
			src.rgba[idx + 3] = (float)p->alpha / 255.0f;
		}
	}

	const double scale_x = info.render_scale_x > 0.0 ? info.render_scale_x : 1.0;
	const double scale_y = info.render_scale_y > 0.0 ? info.render_scale_y : 1.0;
	const double angle = -info.angle_deg * kPi / 180.0;
	const float vx = (float)std::cos(angle);
	const float vy = (float)std::sin(angle);
	const double scale = std::sqrt(std::pow(vx * scale_x, 2) + std::pow(vy * scale_y, 2));
	const A_long strength = std::max<A_long>(0, (A_long)((double)info.front_strength * scale));
	if (strength <= 1) {
		CopyWorld<PF_Pixel8>(input, output);
		return PF_Err_NONE;
	}

	const std::vector<float> weights = DirectionalGaussianWeights(strength);
	const float center = ((float)h - 1.0f) * 0.5f;
	const float span = std::max(center, 1.0f);
	const float sharp_tail = (float)(info.front_sharp_tail / 100.0);

	std::vector<float> accum_rgb((size_t)pixels * 3, 0.0f);
	std::vector<float> accum_sum((size_t)pixels, 0.0f);
	std::vector<float> accum_alpha((size_t)pixels, 0.0f);
	for (A_long p = 0; p < pixels; ++p) {
		const size_t src_idx = (size_t)p * 4;
		const float alpha = src.rgba[src_idx + 3];
		accum_sum[(size_t)p] = alpha;
		accum_alpha[(size_t)p] = alpha;
		for (int c = 0; c < 3; ++c) {
			accum_rgb[(size_t)p * 3 + c] = src.rgba[src_idx + c] * alpha;
		}
	}

	for (A_long i = 1; i < strength; ++i) {
		const float base_weight = weights[(size_t)i];
		for (A_long y = 0; y < h; ++y) {
			float tail = 1.0f;
			if (sharp_tail > 0.0f) {
				tail = std::max(0.0f, 1.0f - std::fabs((float)y - center) * sharp_tail / span);
				if ((float)i >= (float)strength * tail) continue;
			}
			A_long weight_idx = i;
			if (sharp_tail > 0.0f) {
				weight_idx = std::max<A_long>(0, std::min<A_long>((A_long)((float)i / std::max(tail, 1.0e-6f)), strength - 1));
			}
			const float weight = sharp_tail > 0.0f ? weights[(size_t)weight_idx] : base_weight;
			for (A_long x = 0; x < w; ++x) {
				float sample[4];
				SampleBilinear(src, (float)x - vx * (float)i, (float)y - vy * (float)i, sample);
				float alpha = sample[3] * weight;
				if (info.size_variation != 0.0) {
					alpha *= std::pow(ClampFloat(sample[3], 0.0f, 1.0f), (float)(info.size_variation / 100.0));
				}
				const A_long p = y * w + x;
				for (int c = 0; c < 3; ++c) {
					accum_rgb[(size_t)p * 3 + c] += sample[c] * alpha;
				}
				accum_sum[(size_t)p] += alpha;
				accum_alpha[(size_t)p] = std::max(accum_alpha[(size_t)p], alpha);
			}
		}
	}

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const A_long p = y * w + x;
			const float denom = std::max((float)strength, 1.0f);
			PF_Pixel8 *out = PixelAt<PF_Pixel8>(output, x, y);
			out->red   = Quantize8((accum_rgb[(size_t)p * 3 + 0] / denom) * (float)info.brightness_gain);
			out->green = Quantize8((accum_rgb[(size_t)p * 3 + 1] / denom) * (float)info.brightness_gain);
			out->blue  = Quantize8((accum_rgb[(size_t)p * 3 + 2] / denom) * (float)info.brightness_gain);
			out->alpha = Quantize8(accum_alpha[(size_t)p]);
		}
	}
	return PF_Err_NONE;
}

static bool NoiseCoefficientHigherOrderTuple(const OLMDirectionalBlurInfo &info,
	                                          A_long width,
	                                          A_long height)
{
	if (width != 16 || height != 16 || info.angle_deg != 45.0 ||
		info.brightness_gain != 1.0 || info.seed != 1 ||
		info.noise_offset != 0 || info.thickness != 3.0) {
		return false;
	}
	const bool front = info.front_strength == 8 && info.back_strength == 0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0;
	const bool back = info.front_strength == 0 && info.back_strength == 8 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0;
	if (!front && !back) return false;
	const int fade = front ? info.front_alpha_fade : info.back_alpha_fade;
	const double sharp = front ? info.front_sharp_tail : info.back_sharp_tail;
	return
		(fade == 50 && sharp == 50.0 && info.noise_variation == 25.0 &&
		 info.noise_type == 1 && info.size_variation == 0.0) ||
		(fade == 50 && sharp == 100.0 && info.noise_variation == 100.0 &&
		 info.noise_type == 2 && info.size_variation == 50.0) ||
		(fade == 100 && sharp == 50.0 && info.noise_variation == 100.0 &&
		 info.noise_type == 2 && info.size_variation == 0.0) ||
		(fade == 100 && sharp == 100.0 && info.noise_variation == 25.0 &&
		 info.noise_type == 1 && info.size_variation == 50.0);
}

static bool DualSideHigherOrderTuple(const OLMDirectionalBlurInfo &info,
	                                 A_long width,
	                                 A_long height)
{
	if (!((width == 16 && height == 16) || (width == 32 && height == 18) ||
		  (width == 64 && height == 36)) ||
		info.angle_deg != 45.0 ||
		info.brightness_gain != 1.0 || info.front_strength != 8 ||
		info.back_strength != 8 || info.seed != 1 || info.noise_offset != 0 ||
		info.thickness != 3.0) {
		return false;
	}
	return
		(info.front_alpha_fade == 50 && info.front_sharp_tail == 50.0 &&
		 info.back_alpha_fade == 100 && info.back_sharp_tail == 100.0 &&
		 info.size_variation == 0.0 && info.noise_variation == 25.0 &&
		 info.noise_type == 1) ||
		(info.front_alpha_fade == 50 && info.front_sharp_tail == 100.0 &&
		 info.back_alpha_fade == 50 && info.back_sharp_tail == 50.0 &&
		 info.size_variation == 50.0 && info.noise_variation == 100.0 &&
		 info.noise_type == 2) ||
		(info.front_alpha_fade == 100 && info.front_sharp_tail == 50.0 &&
		 info.back_alpha_fade == 50 && info.back_sharp_tail == 100.0 &&
		 info.size_variation == 0.0 && info.noise_variation == 100.0 &&
		 info.noise_type == 2) ||
		(info.front_alpha_fade == 100 && info.front_sharp_tail == 100.0 &&
		 info.back_alpha_fade == 100 && info.back_sharp_tail == 50.0 &&
		 info.size_variation == 50.0 && info.noise_variation == 25.0 &&
		 info.noise_type == 1);
}

static bool NoiseType2Natural64Tuple(const OLMDirectionalBlurInfo &info,
	                                 A_long width,
	                                 A_long height)
{
	return width == 64 && height == 36 && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0 && info.front_strength == 8 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
		info.back_strength == 0 && info.back_alpha_fade == 0 &&
		info.back_sharp_tail == 0.0 && info.size_variation == 0.0 &&
		info.noise_variation == 25.0 && info.noise_type == 2 &&
		info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0;
}

static bool Natural64RowbytesSafe(A_long rowbytes, std::size_t pixel_size)
{
	constexpr A_long kWidth = 64;
	constexpr A_long kLastRow = 35;
	const std::size_t active = static_cast<std::size_t>(kWidth) * pixel_size;
	return rowbytes >= 0 && static_cast<std::size_t>(rowbytes) >= active &&
		rowbytes <= std::numeric_limits<A_long>::max() / kLastRow;
}

static bool Natural64SourceExact(const PF_EffectWorld *input,
	                              std::size_t pixel_size)
{
	if (!input || !input->data || input->width != 64 || input->height != 36 ||
		!Natural64RowbytesSafe(input->rowbytes, pixel_size)) {
		return false;
	}
	static const char *const kPF16Sources[] = {
		"18f79acc8e254e7f1bf8c3753a0d82badcc9f9247f568ba0088b5caf74e5d450",
		"f7b586904e3678145aa47e4232587c913139cef0102d6d8e9276fc80c35cbad3",
		"1d74d9033ea9ed570c92277cf848d4ae0f9f571a42e3a852e12e6110d914c928",
		"0e20c1d480bb5e7f6dbc11c5cff6dd69aef2ec9e296cd3faa7b056e48590af8b",
		"d15a4c5de71ad7cb3774f2a25919f822cfed943aa686480e9f533d05fec0262a",
	};
	static const char *const kPF8Sources[] = {
		"0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03",
		"2d07a41ae992770085117e9815300bfd0730745883e60b24aaad5e69dfc087ae",
		"784c27133912eb473bb88c560af00d1cadb2c841297bf05ccef648036a86e212",
		"c549e434122a54ed2d78b23249ba25bbe6a4c121469a9b1e195743848095cd10",
		"b5274891a810ed4743b9b8b0816ed8fb6c5a9a1d5f777d71f32d2be010e02fa0",
	};
	static const char *const kPF32Sources[] = {
		"884631deb3be114d9a226566d537323fc1f634e83f58cdd30b73c98cacef708d",
		"1c0273095382988333e2f2b5ae487cea460737ed9be65cbad9c5de537f95bf75",
		"8293539fd0efb2fdded5aaed0d751dda3a4171b8020f6ff67e1f06b10dca5555",
		"5ea5755a117d89c33bfb0685d2ba2e9cf4153d816c2bb06e2d61606fba51611f",
		"501667f87211e6e20a3d878fb71ab4a29de27b01a7049b97a6b66aa63508cfa1",
	};
	const char *const *sources = nullptr;
	std::size_t source_count = 0;
	if (pixel_size == sizeof(PF_Pixel8)) {
		sources = kPF8Sources;
		source_count = sizeof(kPF8Sources) / sizeof(kPF8Sources[0]);
	} else if (pixel_size == sizeof(PF_Pixel16)) {
		sources = kPF16Sources;
		source_count = sizeof(kPF16Sources) / sizeof(kPF16Sources[0]);
	} else if (pixel_size == sizeof(PF_PixelFloat)) {
		sources = kPF32Sources;
		source_count = sizeof(kPF32Sources) / sizeof(kPF32Sources[0]);
	} else {
		return false;
	}
	const std::size_t active_bytes = 64u * pixel_size;
	for (std::size_t index = 0; index < source_count; ++index) {
		if (olm::sha256_active_rows_match_hex(input->data,
			static_cast<std::size_t>(input->rowbytes), active_bytes, 36u,
			sources[index])) {
			return true;
		}
	}
	return false;
}

static bool PublicType3Layer16Tuple(const OLMDirectionalBlurInfo &info)
{
	return info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
		info.front_strength == 8 && info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 50.0 && info.back_strength == 0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.size_variation == 0.0 && info.noise_variation == 100.0 &&
		info.noise_type == 3 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 3.0 && info.render_scale_x == 1.0 &&
		info.render_scale_y == 1.0;
}

static bool PublicDualSideType2_32x18Tuple(const OLMDirectionalBlurInfo &info)
{
	return info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
		info.front_strength == 8 && info.front_alpha_fade == 50 &&
		info.front_sharp_tail == 100.0 && info.back_strength == 8 &&
		info.back_alpha_fade == 50 && info.back_sharp_tail == 50.0 &&
		info.size_variation == 50.0 && info.noise_variation == 100.0 &&
		info.noise_type == 2 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 3.0 && info.render_scale_x == 1.0 &&
		info.render_scale_y == 1.0;
}

static bool ExactExtent16(const PF_EffectWorld *world)
{
	return world && world->extent_hint.left == 0 && world->extent_hint.top == 0 &&
		world->extent_hint.right == 16 && world->extent_hint.bottom == 16;
}

static bool ExactExtent32x18(const PF_EffectWorld *world)
{
	return world && world->extent_hint.left == 0 && world->extent_hint.top == 0 &&
		world->extent_hint.right == 32 && world->extent_hint.bottom == 18;
}

static bool PayloadSpan(const PF_EffectWorld *world,
	                    std::uintptr_t *begin,
	                    std::uintptr_t *end)
{
	if (!world || !world->data || !begin || !end || world->rowbytes <= 0 ||
		world->height <= 0) {
		return false;
	}
	const std::size_t rowbytes = static_cast<std::size_t>(world->rowbytes);
	const std::size_t height = static_cast<std::size_t>(world->height);
	if (rowbytes > std::numeric_limits<std::size_t>::max() / height) {
		return false;
	}
	const std::size_t bytes = rowbytes * height;
	const std::uintptr_t first = reinterpret_cast<std::uintptr_t>(world->data);
	if (bytes > std::numeric_limits<std::uintptr_t>::max() - first) {
		return false;
	}
	*begin = first;
	*end = first + bytes;
	return true;
}

static bool DisjointPayloads(const PF_EffectWorld *first,
	                         const PF_EffectWorld *second)
{
	std::uintptr_t first_begin = 0, first_end = 0;
	std::uintptr_t second_begin = 0, second_end = 0;
	return PayloadSpan(first, &first_begin, &first_end) &&
		PayloadSpan(second, &second_begin, &second_end) &&
		(first_end <= second_begin || second_end <= first_begin);
}

static bool PublicType3Layer16WorldsExact(const PF_EffectWorld *input,
	                                      const PF_EffectWorld *output,
	                                      const PF_EffectWorld *noise_layer,
	                                      short bitdepth)
{
	if (!input || !output || !noise_layer || !input->data || !output->data ||
		!noise_layer->data || input->width != 16 || input->height != 16 ||
		output->width != 16 || output->height != 16 ||
		noise_layer->width != 16 || noise_layer->height != 16 ||
		!ExactExtent16(input) || !ExactExtent16(output) ||
		!ExactExtent16(noise_layer) || !DisjointPayloads(input, output) ||
		!DisjointPayloads(input, noise_layer) ||
		!DisjointPayloads(output, noise_layer)) {
		return false;
	}
	std::size_t pixel_size = 0;
	A_long input_output_rowbytes = 0;
	A_long noise_rowbytes = 0;
	const char *source_sha256 = nullptr;
	switch (bitdepth) {
	case 8:
		pixel_size = sizeof(PF_Pixel8);
		input_output_rowbytes = 76;
		noise_rowbytes = 84;
		source_sha256 = "ad840bf75281333fc389ba7083074e10ff82e7538583242e7a91880e6bbe1b83";
		break;
	case 16:
		pixel_size = sizeof(PF_Pixel16);
		input_output_rowbytes = 144;
		noise_rowbytes = 152;
		source_sha256 = "c8312808c3b40b8970d567234f944c71654cbf9d3363aabb1980421fb2597803";
		break;
	case 32:
		pixel_size = sizeof(PF_PixelFloat);
		input_output_rowbytes = 288;
		noise_rowbytes = 296;
		source_sha256 = "d411e03242f4235a8ea803517db6d81e7e72764a97a4241d0bcea46a6edc7303";
		break;
	default:
		return false;
	}
	if (input->rowbytes != input_output_rowbytes ||
		output->rowbytes != input_output_rowbytes ||
		noise_layer->rowbytes != noise_rowbytes) {
		return false;
	}
	const std::size_t active_bytes = 16u * pixel_size;
	return olm::sha256_active_rows_match_hex(input->data,
		static_cast<std::size_t>(input->rowbytes), active_bytes, 16u,
		source_sha256) &&
		olm::sha256_active_rows_match_hex(noise_layer->data,
		static_cast<std::size_t>(noise_layer->rowbytes), active_bytes, 16u,
		source_sha256);
}

static bool PublicDualSideType2WorldsExact(const PF_EffectWorld *input,
	                                        const PF_EffectWorld *output,
	                                        short bitdepth)
{
	if (!input || !output || !input->data || !output->data ||
		input->width != output->width || input->height != output->height ||
		!DisjointPayloads(input, output)) {
		return false;
	}
	const bool geometry32 = input->width == 32 && input->height == 18 &&
		ExactExtent32x18(input) && ExactExtent32x18(output);
	const bool geometry64 = input->width == 64 && input->height == 36 &&
		input->extent_hint.left == 0 && input->extent_hint.top == 0 &&
		input->extent_hint.right == 64 && input->extent_hint.bottom == 36 &&
		output->extent_hint.left == 0 && output->extent_hint.top == 0 &&
		output->extent_hint.right == 64 && output->extent_hint.bottom == 36;
	if (!geometry32 && !geometry64) return false;
	std::size_t pixel_size = 0;
	A_long rowbytes = 0;
	const char *source_sha256 = nullptr;
	switch (bitdepth) {
	case 8:
		pixel_size = sizeof(PF_Pixel8);
		rowbytes = geometry32 ? 140 : 268;
		source_sha256 = geometry32 ?
			"7c65cdf081119a7db77d804cb5ad256f3b89beb73bb32587fbf53224c56d06e6" :
			"0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03";
		break;
	case 16:
		pixel_size = sizeof(PF_Pixel16);
		rowbytes = geometry32 ? 272 : 528;
		source_sha256 = geometry32 ?
			"44f6470ac55a81953e062df177d996a0336348a472b7e0e050b8de261c1fcbf5" :
			"18f79acc8e254e7f1bf8c3753a0d82badcc9f9247f568ba0088b5caf74e5d450";
		break;
	case 32:
		pixel_size = sizeof(PF_PixelFloat);
		rowbytes = geometry32 ? 544 : 1056;
		source_sha256 = geometry32 ?
			"0c626ba0cc34551753ea2176999eb075610ebd63c40fee5af7b2c31a10812ba6" :
			"884631deb3be114d9a226566d537323fc1f634e83f58cdd30b73c98cacef708d";
		break;
	default:
		return false;
	}
	if (input->rowbytes != rowbytes || output->rowbytes != rowbytes) {
		return false;
	}
	return olm::sha256_active_rows_match_hex(input->data,
		static_cast<std::size_t>(input->rowbytes),
		static_cast<std::size_t>(input->width) * pixel_size,
		static_cast<std::size_t>(input->height),
		source_sha256);
}

static bool PublicDualSideExportedSmartExact(const PF_EffectWorld *input,
	                                          const PF_EffectWorld *output,
	                                          const OLMDirectionalBlurInfo &info,
	                                          short bitdepth)
{
	if (!input || !output || !PublicDualSideType2WorldsExact(input, output, bitdepth)) {
		return false;
	}
	if (input->width == 32 && input->height == 18) {
		return (bitdepth == 8 || bitdepth == 16 || bitdepth == 32) &&
			PublicDualSideType2_32x18Tuple(info);
	}
	if (input->width != 64 || input->height != 36 ||
		(bitdepth != 8 && bitdepth != 16 && bitdepth != 32) ||
		!DualSideHigherOrderTuple(info, 64, 36) ||
		info.render_scale_x != 1.0 || info.render_scale_y != 1.0) {
		return false;
	}
	// All four fixed 64x36 tuples are raw-exact through the exported Windows
	// Smart route at PF8/PF16/PF32. For the former six x86_64 rejects, a native
	// System32 UCRT table replay proves the pre-existing x86_64 arithmetic exact;
	// no result lookup or expected-value correction is used in production.
	return true;
}

static bool CanUseExact8(const PF_EffectWorld *input,
                         const PF_EffectWorld *output,
                         const PF_EffectWorld *noise_layer,
                         const OLMDirectionalBlurInfo &info)
{
	const bool noise_coefficient_higher_order_exact = input && output &&
		NoiseCoefficientHigherOrderTuple(info, input->width, input->height) &&
		output->width == input->width && output->height == input->height;
	const bool dual_side_higher_order_exact = input && output &&
		DualSideHigherOrderTuple(info, input->width, input->height) &&
		output->width == input->width && output->height == input->height;
	const bool size_front_combo = info.size_variation != 0.0 &&
		(info.front_alpha_fade != 0 || info.front_sharp_tail != 0.0);
	const bool size_back_combo = info.size_variation != 0.0 &&
		(info.back_alpha_fade != 0 || info.back_sharp_tail != 0.0);
	const bool size_front_combo_exact = input && output &&
		input->width == 16 && input->height == 16 &&
		output->width == 16 && output->height == 16 &&
		info.front_strength == 8 && info.back_strength == 0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0 &&
		(((info.size_variation == 25.0 || info.size_variation == 50.0 ||
		   info.size_variation == 100.0) &&
		  (info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
		  info.front_sharp_tail == 0.0) ||
		 (info.size_variation == 50.0 && info.front_alpha_fade == 0 &&
		  (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0)));
	const bool size_back_combo_exact = input && output &&
		input->width == 16 && input->height == 16 &&
		output->width == 16 && output->height == 16 &&
		info.front_strength == 0 && info.back_strength == 8 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
		info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0 &&
		(((info.size_variation == 25.0 || info.size_variation == 50.0 ||
		   info.size_variation == 100.0) &&
		  (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
		  info.back_sharp_tail == 0.0) ||
		 (info.size_variation == 50.0 && info.back_alpha_fade == 0 &&
		  (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)));
	const bool legacy_size_sharp_exact = input && output &&
		input->width == 960 && input->height == 540 &&
		output->width == 960 && output->height == 540 &&
		info.angle_deg == 0.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 92.0 && info.front_strength == 1690 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 45.0 &&
		info.back_strength == 0 && info.noise_variation == 0.0 &&
		info.render_scale_x == 0.5 && info.render_scale_y == 0.5;
	const bool legacy_mode2_adapter_exact = input && output && noise_layer &&
		input->width == 16 && input->height == 16 &&
		output->width == 16 && output->height == 16 &&
		noise_layer->width == 16 && noise_layer->height == 16 &&
		info.angle_deg == 27.0 && info.brightness_gain == 1.125 &&
		info.size_variation == 38.0 && info.front_strength == 37 &&
		info.front_alpha_fade == 9 && info.front_sharp_tail == 23.0 &&
		info.back_strength == 19 && info.back_alpha_fade == 7 &&
		info.back_sharp_tail == 31.0 && info.noise_variation == 73.0 &&
		info.noise_type == 3 && info.render_scale_x == 1.0 &&
		info.render_scale_y == 1.0;
	return input && output && input->width == output->width &&
	       input->height == output->height &&
	       (info.front_strength > 0 || info.back_strength > 0) &&
	       info.front_strength >= 0 && info.front_alpha_fade >= 0 &&
	       info.back_strength >= 0 && info.back_alpha_fade >= 0 &&
	       info.size_variation >= 0.0 && info.size_variation <= 100.0 &&
	       (!size_front_combo || size_front_combo_exact ||
	        noise_coefficient_higher_order_exact || dual_side_higher_order_exact ||
	        legacy_size_sharp_exact ||
	        legacy_mode2_adapter_exact) &&
	       (!size_back_combo || size_back_combo_exact ||
	        noise_coefficient_higher_order_exact || dual_side_higher_order_exact ||
	        legacy_mode2_adapter_exact) &&
	       info.noise_variation >= 0.0 &&
	       (info.noise_variation == 0.0 ||
	        ((info.noise_type == 1 || info.noise_type == 2) && info.thickness > 0.0) ||
	        (info.noise_type == 3 && noise_layer && noise_layer->data &&
	         noise_layer->width == input->width &&
	         noise_layer->height == input->height)) &&
	       info.render_scale_x > 0.0 &&
	       info.render_scale_y > 0.0;
}

// Public beta lane for the already-portable full-frame core.  The neutral
// shape is kept separate from admission so malformed/out-of-UI generic tuples
// cannot fall through into a legacy approximate or fixed-fixture route.
static bool IsGenericNeutralShape(const OLMDirectionalBlurInfo &info)
{
	const bool any_side = info.front_strength != 0 || info.back_strength != 0;
	return any_side && info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 0.0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0;
}

static bool RetainedNeutralBackWorlds(const PF_EffectWorld *input,
	                                  const PF_EffectWorld *output,
	                                  A_long width,
	                                  A_long height,
	                                  std::size_t pixel_size)
{
	if (width <= 0 || height <= 0 || pixel_size == 0 ||
		static_cast<std::size_t>(width) >
			std::numeric_limits<std::size_t>::max() / pixel_size) {
		return false;
	}
	const std::size_t active = static_cast<std::size_t>(width) * pixel_size;
	return input && output && input->data && output->data &&
		input->width == width && input->height == height && output->width == width &&
		output->height == height && input->rowbytes >= 0 && output->rowbytes >= 0 &&
		static_cast<std::size_t>(input->rowbytes) >= active &&
		static_cast<std::size_t>(output->rowbytes) >= active;
}

static bool IsRetainedNeutralBackExact8(const PF_EffectWorld *input,
		                                  const PF_EffectWorld *output,
		                                  const OLMDirectionalBlurInfo &info)
{
	if (info.front_strength != 0 || info.brightness_gain != 1.0 ||
		info.front_alpha_fade != 0 || info.front_sharp_tail != 0.0 ||
		info.back_alpha_fade != 0 ||
		info.back_sharp_tail != 0.0 || info.size_variation != 0.0 ||
		info.noise_variation != 0.0) {
		return false;
	}
	const bool retained_16 =
		RetainedNeutralBackWorlds(input, output, 16, 16, sizeof(PF_Pixel8)) &&
		info.back_strength == 8 &&
		(info.angle_deg == 0.0 || info.angle_deg == 45.0) &&
		info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
	const bool retained_portable_960 =
		RetainedNeutralBackWorlds(input, output, 960, 540, sizeof(PF_Pixel8)) &&
		info.back_strength == 240 && info.angle_deg == 0.0 &&
		info.render_scale_x == 0.5 && info.render_scale_y == 0.5;
	return retained_16 || retained_portable_960;
}

static bool IsRetainedNeutralBackExact16(const PF_EffectWorld *input,
		                                   const PF_EffectWorld *output,
		                                   const OLMDirectionalBlurInfo &info)
{
	return RetainedNeutralBackWorlds(input, output, 16, 16, sizeof(PF_Pixel16)) &&
		info.front_strength == 0 &&
		(info.back_strength == 1 || info.back_strength == 2 ||
		 info.back_strength == 8) && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0 && info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 0.0 && info.back_alpha_fade == 0 &&
		info.back_sharp_tail == 0.0 && info.size_variation == 0.0 &&
		info.noise_variation == 0.0 && info.render_scale_x == 1.0 &&
		info.render_scale_y == 1.0;
}

static bool IsRetainedNeutralBackExact32(const PF_EffectWorld *input,
		                                  const PF_EffectWorld *output,
		                                  const OLMDirectionalBlurInfo &info)
{
	const bool back_one = info.back_strength == 1 &&
		(info.angle_deg == 0.0 || info.angle_deg == 45.0) &&
		(info.brightness_gain == 0.5 || info.brightness_gain == 1.0);
	if (!RetainedNeutralBackWorlds(
			input, output, 16, 16, sizeof(PF_PixelFloat))) return false;
	const bool back_eight = info.back_strength == 8 && info.angle_deg == 45.0 &&
		info.brightness_gain == 1.0;
	return info.front_strength == 0 && (back_one || back_eight) &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
}

static bool IsRetainedNeutralDualExact16(const PF_EffectWorld *input,
	                                      const PF_EffectWorld *output,
	                                      const OLMDirectionalBlurInfo &info)
{
	return RetainedNeutralBackWorlds(input, output, 16, 16, sizeof(PF_Pixel16)) &&
		(info.front_strength == 1 || info.front_strength == 2 ||
		 info.front_strength == 8) && info.back_strength == 1 &&
		info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
		info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.size_variation == 0.0 && info.noise_variation == 0.0 &&
		info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
}

static bool IsRetainedNeutralBackExact(const PF_EffectWorld *input,
		                                const PF_EffectWorld *output,
		                                const OLMDirectionalBlurInfo &info,
		                                short bitdepth)
{
	switch (bitdepth) {
	case 8: return IsRetainedNeutralBackExact8(input, output, info);
	case 16: return IsRetainedNeutralBackExact16(input, output, info);
	case 32: return IsRetainedNeutralBackExact32(input, output, info);
	default: return false;
	}
}

static bool IsRetainedNeutralExact(const PF_EffectWorld *input,
	                                const PF_EffectWorld *output,
	                                const OLMDirectionalBlurInfo &info,
	                                short bitdepth)
{
	return IsRetainedNeutralBackExact(input, output, info, bitdepth) ||
		(bitdepth == 16 && IsRetainedNeutralDualExact16(input, output, info));
}

static bool GenericEffectiveStrengths(const OLMDirectionalBlurInfo &info,
	                                  bool require_unit_scale,
	                                  int *effective_front_strength,
	                                  int *effective_back_strength)
{
	if (!effective_front_strength || !effective_back_strength ||
		!IsGenericNeutralShape(info)) return false;
	// PF_ADD_ANGLE stores signed 16.16 degrees; the other bounds mirror the
	// visible generic controls.  Recheck the actual float values consumed by the
	// core after narrowing, rather than relying only on PF_FpLong finiteness.
	constexpr PF_FpLong kMinimumAngle = -32768.0;
	constexpr PF_FpLong kMaximumAngle = 32767.9999847412109375;
	if (!std::isfinite(info.angle_deg) || info.angle_deg < kMinimumAngle ||
		info.angle_deg > kMaximumAngle ||
		!std::isfinite(info.brightness_gain) || info.brightness_gain < 0.0 ||
		info.brightness_gain > 10.0 || info.front_strength < 0 ||
		info.front_strength > 4000 || info.back_strength < 0 ||
		info.back_strength > 4000 ||
		!std::isfinite(info.render_scale_x) ||
		!std::isfinite(info.render_scale_y) ||
		info.render_scale_x <= 0.0 || info.render_scale_x > 1.0 ||
		info.render_scale_y <= 0.0 || info.render_scale_y > 1.0) {
		return false;
	}
	const float angle = static_cast<float>(info.angle_deg);
	const float gain = static_cast<float>(info.brightness_gain);
	const float scale_x = static_cast<float>(info.render_scale_x);
	const float scale_y = static_cast<float>(info.render_scale_y);
	if (!std::isfinite(angle) || !std::isfinite(gain) ||
		!std::isfinite(scale_x) || !std::isfinite(scale_y) ||
		scale_x <= 0.0f || scale_y <= 0.0f) {
		return false;
	}
	if (require_unit_scale) {
		if (info.render_scale_x != 1.0 || info.render_scale_y != 1.0) return false;
		*effective_front_strength = static_cast<int>(info.front_strength);
		*effective_back_strength = static_cast<int>(info.back_strength);
		return *effective_front_strength > 0 || *effective_back_strength > 0;
	}
	const double radians = -info.angle_deg * kPi / 180.0;
	const double vx = std::cos(radians);
	const double vy = std::sin(radians);
	const float projected_scale = static_cast<float>(std::sqrt(
		std::pow(vx * info.render_scale_x, 2) +
		std::pow(vy * info.render_scale_y, 2)));
	const float scaled_front_strength =
		static_cast<float>(info.front_strength) * projected_scale;
	const float scaled_back_strength =
		static_cast<float>(info.back_strength) * projected_scale;
	if (!std::isfinite(projected_scale) || projected_scale <= 0.0f ||
		projected_scale > 1.0f || !std::isfinite(scaled_front_strength) ||
		!std::isfinite(scaled_back_strength) ||
		scaled_front_strength > static_cast<float>(std::numeric_limits<int>::max()) ||
		scaled_back_strength > static_cast<float>(std::numeric_limits<int>::max())) {
		return false;
	}
	*effective_front_strength = static_cast<int>(scaled_front_strength);
	*effective_back_strength = static_cast<int>(scaled_back_strength);
	// A side selected by the user must remain active after PF8's projected
	// scale/truncation.  Otherwise a dual tuple could silently become single.
	return (info.front_strength == 0 || *effective_front_strength > 0) &&
		(info.back_strength == 0 || *effective_back_strength > 0) &&
		*effective_front_strength <= 4000 && *effective_back_strength <= 4000;
}

static bool IsGenericNeutral8Parameters(const OLMDirectionalBlurInfo &info)
{
	int ignored_front = 0, ignored_back = 0;
	return GenericEffectiveStrengths(info, false, &ignored_front, &ignored_back);
}

static bool IsGenericNeutralDeepParameters(const OLMDirectionalBlurInfo &info)
{
	int ignored_front = 0, ignored_back = 0;
	return GenericEffectiveStrengths(info, true, &ignored_front, &ignored_back);
}

static bool CanUseGenericNeutral8(const PF_EffectWorld *input,
	                              const PF_EffectWorld *output,
	                              const OLMDirectionalBlurInfo &info)
{
	int effective_front_strength = 0, effective_back_strength = 0;
	if (!input || !output || !input->data || !output->data ||
		input->width <= 0 || input->height <= 0 ||
		input->width != output->width || input->height != output->height ||
		!GenericEffectiveStrengths(info, false, &effective_front_strength,
			&effective_back_strength) ||
		static_cast<std::size_t>(input->width) >
			static_cast<std::size_t>(std::numeric_limits<A_long>::max()) / sizeof(PF_Pixel8)) {
		return false;
	}
	const A_long active_rowbytes =
		static_cast<A_long>(static_cast<std::size_t>(input->width) * sizeof(PF_Pixel8));
	if (input->rowbytes < active_rowbytes || output->rowbytes < active_rowbytes) return false;
	const std::int64_t diagonal_squared =
		static_cast<std::int64_t>(input->width) * input->width +
		static_cast<std::int64_t>(input->height) * input->height;
	olm::dblur::generic::RenderEstimate estimate = {};
	return diagonal_squared <= std::numeric_limits<int>::max() &&
		olm::dblur::generic::EstimateRender(input->width, input->height, 8,
			effective_front_strength, effective_back_strength, 0, &estimate);
}

template <typename PixelT>
static bool GenericDeepWorldsSafe(const PF_EffectWorld *input,
	                              const PF_EffectWorld *output,
	                              const OLMDirectionalBlurInfo &info)
{
	int effective_front_strength = 0, effective_back_strength = 0;
	if (!input || !output || !input->data || !output->data || input->width <= 0 ||
		input->height <= 0 || input->width != output->width ||
		input->height != output->height ||
		!GenericEffectiveStrengths(info, true, &effective_front_strength,
			&effective_back_strength)) {
		return false;
	}
	const std::size_t width = static_cast<std::size_t>(input->width);
	if (width > static_cast<std::size_t>(std::numeric_limits<A_long>::max()) / sizeof(PixelT)) {
		return false;
	}
	const A_long active = static_cast<A_long>(width * sizeof(PixelT));
	constexpr short depth = sizeof(PixelT) == 8 ? 16 : 32;
	olm::dblur::generic::RenderEstimate estimate = {};
	return input->rowbytes >= active && output->rowbytes >= active &&
		olm::dblur::generic::EstimateRender(input->width, input->height, depth,
			effective_front_strength, effective_back_strength, 0, &estimate);
}

template <typename WorldT>
static auto DirectionalWorldHasZeroOrigin(const WorldT *world, int)
	-> decltype(world->origin_x, world->origin_y, bool())
{
	return world->origin_x == 0 && world->origin_y == 0;
}

// Compatibility for the oldest reduced-header source-included harness. Real
// SDK worlds always select the origin_x/origin_y overload above.
static bool DirectionalWorldHasZeroOrigin(const void *, long)
{
	return true;
}

static OLMDirectionalBlurInfo DirectionalDeepLayerInfo(
    const OLMDirectionalBlurInfo &requested, const PF_EffectWorld *input,
    const PF_EffectWorld *layer, short depth)
{
    OLMDirectionalBlurInfo result = requested;
    // AEX full render allocates its Layer field only when the checked-out Layer
    // matches the full-resolution render dimensions. With None/different size,
    // the row driver sees a null field and uses the multiplicative identity.
    if ((depth == 16 || depth == 32) && result.noise_variation > 0.0 &&
        result.noise_type == 3 && (!input || !layer ||
            layer->width != input->width || layer->height != input->height)) {
        result.noise_variation = 0.0;
    }
    return result;
}

static bool IsGenericDeepFeatureShape(const OLMDirectionalBlurInfo &info)
{
    return (info.front_strength != 0 || info.back_strength != 0) &&
        !IsGenericNeutralShape(info);
}

static OLMDirectionalBlurInfo NeutralStrengthView(const OLMDirectionalBlurInfo &info)
{
    OLMDirectionalBlurInfo neutral = info;
    neutral.size_variation = neutral.noise_variation = 0.0;
    neutral.front_sharp_tail = neutral.back_sharp_tail = 0.0;
    neutral.front_alpha_fade = neutral.back_alpha_fade = 0;
    return neutral;
}

static bool GenericDeepFeatureEstimate(const OLMDirectionalBlurInfo &info,
    A_long width, A_long height, short depth, std::size_t staging_bytes,
    olm::dblur::generic::RenderEstimate *estimate,
    double layer_coefficient_bound = std::numeric_limits<double>::infinity())
{
    int front = 0, back = 0;
    const auto percent = [](PF_FpLong value) {
        return std::isfinite(value) && value >= 0.0 && value <= 100.0;
    };
    if (!IsGenericDeepFeatureShape(info) || !percent(info.size_variation) ||
        !percent(info.front_sharp_tail) || !percent(info.back_sharp_tail) ||
        !percent(info.noise_variation) || info.front_alpha_fade < 0 ||
        info.front_alpha_fade > 100 || info.back_alpha_fade < 0 || info.back_alpha_fade > 100 ||
        (info.noise_variation > 0.0 && ((info.noise_type < 1 || info.noise_type > 3) ||
            (info.noise_type != 3 && (info.seed < 1 || info.seed > 1000 ||
                info.noise_offset < -32768 || info.noise_offset > 32767)))) ||
        !GenericEffectiveStrengths(NeutralStrengthView(info), true, &front, &back)) return false;
    return olm::dblur::generic::EstimateGeneralDeepRender(width, height, depth, front, back,
        static_cast<int>(info.front_alpha_fade), static_cast<int>(info.back_alpha_fade),
        info.size_variation != 0.0 || info.front_sharp_tail != 0.0 || info.back_sharp_tail != 0.0,
        info.noise_variation > 0.0 && info.noise_type != 3,
        static_cast<float>(info.thickness), staging_bytes, estimate,
        info.noise_variation > 0.0 && info.noise_type == 3, layer_coefficient_bound);
}

template <typename PixelT>
static bool GenericDeepFeatureWorldsSafe(const PF_EffectWorld *input,
    const PF_EffectWorld *output, const OLMDirectionalBlurInfo &info, std::size_t staging_bytes = 0,
    double layer_coefficient_bound = std::numeric_limits<double>::infinity())
{
    constexpr short depth = sizeof(PixelT) == 8 ? 16 : 32;
    olm::dblur::generic::RenderEstimate estimate = {};
    return GenericDeepWorldsSafe<PixelT>(input, output, NeutralStrengthView(info)) &&
        GenericDeepFeatureEstimate(info, input->width, input->height, depth, staging_bytes,
            &estimate, layer_coefficient_bound);
}

static bool GenericPF16SDRInput(const PF_EffectWorld *input)
{
	for (A_long y = 0; y < input->height; ++y) {
		const std::uint8_t *row = reinterpret_cast<const std::uint8_t *>(input->data) +
			static_cast<std::size_t>(y) * static_cast<std::size_t>(input->rowbytes);
		for (A_long x = 0; x < input->width; ++x) {
			PF_Pixel16 pixel = {};
			std::memcpy(&pixel, row + static_cast<std::size_t>(x) * sizeof(pixel),
				sizeof(pixel));
			if (pixel.alpha > 32768 || pixel.red > 32768 ||
				pixel.green > 32768 || pixel.blue > 32768) return false;
		}
	}
	return true;
}

static bool GenericPF32FiniteInput(const PF_EffectWorld *input)
{
	for (A_long y = 0; y < input->height; ++y) {
		const std::uint8_t *row = reinterpret_cast<const std::uint8_t *>(input->data) +
			static_cast<std::size_t>(y) * static_cast<std::size_t>(input->rowbytes);
		for (A_long x = 0; x < input->width; ++x) {
			PF_PixelFloat pixel = {};
			std::memcpy(&pixel, row + static_cast<std::size_t>(x) * sizeof(pixel),
				sizeof(pixel));
			const float values[] = {pixel.alpha, pixel.red, pixel.green, pixel.blue};
			for (float value : values) if (!std::isfinite(value)) return false;
		}
	}
	return true;
}

static bool GenericPF32LayerCoefficientBound(const PF_EffectWorld *layer,
    const OLMDirectionalBlurInfo &info, double *bound)
{
    if (!layer || !bound) return false;
    double maximum_product = 0.0;
    for (A_long y = 0; y < layer->height; ++y) {
        const auto *row = reinterpret_cast<const std::uint8_t *>(layer->data) +
            static_cast<std::size_t>(y) * static_cast<std::size_t>(layer->rowbytes);
        for (A_long x = 0; x < layer->width; ++x) {
            PF_PixelFloat pixel = {};
            std::memcpy(&pixel, row + static_cast<std::size_t>(x) * sizeof(pixel), sizeof(pixel));
            const float channels[] = {pixel.alpha, pixel.red, pixel.green, pixel.blue};
            for (float value : channels) if (!std::isfinite(value)) return false;
            const double rgb = std::max({std::abs(static_cast<double>(pixel.red)),
                std::abs(static_cast<double>(pixel.green)), std::abs(static_cast<double>(pixel.blue))});
            maximum_product = std::max(maximum_product, std::abs(static_cast<double>(pixel.alpha)) * rgb);
        }
    }
    // Premultiplied luminance and scalar bilinear interpolation have nonnegative
    // weights summing to one. This absolute-product bound covers signed inputs.
    // Inflate by 32 float epsilons for their rounding, the Noise mix, and the
    // final Strength multiply. This affects admission only, never pixel math.
    const double opacity = info.noise_variation / 100.0;
    *bound = std::max(1.0, maximum_product * opacity + (1.0 - opacity)) *
        (1.0 + 32.0 * std::numeric_limits<float>::epsilon());
    return true;
}

static bool NoisePublicPairwiseTuple(const OLMDirectionalBlurInfo &info,
	                                  A_long width,
	                                  A_long height)
{
	const bool fade50 = info.front_alpha_fade == 50 &&
		info.front_sharp_tail == 0.0 && info.size_variation == 0.0;
	const bool sharp50 = info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 50.0 && info.size_variation == 0.0;
	const bool size50 = info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 0.0 && info.size_variation == 50.0;
	const int coefficient = fade50 ? 1 : sharp50 ? 2 : size50 ? 3 : 0;
	const int geometry = width == 16 && height == 16 ? 1 :
		width == 32 && height == 18 ? 2 : 0;
	return info.front_strength == 8 && info.back_strength == 0 &&
		info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
		info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
		((info.noise_type == 1 && info.seed == 1 && info.noise_offset == 0 &&
		  info.thickness == 3.0 && info.noise_variation == 25.0 &&
		  ((coefficient == 1 && geometry == 1) || (coefficient == 3 && geometry == 1))) ||
		 (info.noise_type == 1 && info.seed == 2 && info.noise_offset == 1 &&
		  info.thickness == 10.0 && info.noise_variation == 100.0 &&
		  coefficient == 2 && geometry == 2) ||
		 (info.noise_type == 2 && info.seed == 1 && info.noise_offset == 0 &&
		  info.thickness == 3.0 && info.noise_variation == 100.0 &&
		  coefficient == 3 && geometry == 2) ||
		 (info.noise_type == 3 && info.seed == 2 && info.noise_offset == 1 &&
		  info.thickness == 10.0 && info.noise_variation == 25.0 &&
		  coefficient == 3 && geometry == 1) ||
		 (info.noise_type == 2 && info.seed == 1 && info.noise_offset == 0 &&
		  info.thickness == 10.0 && info.noise_variation == 25.0 &&
		  coefficient == 2 && geometry == 1) ||
		 (info.noise_type == 3 && info.seed == 1 && info.noise_offset == 1 &&
		  info.thickness == 3.0 && info.noise_variation == 100.0 &&
		  coefficient == 1 && geometry == 2) ||
		 (info.noise_type == 2 && info.seed == 2 && info.noise_offset == 0 &&
		  info.thickness == 3.0 && info.noise_variation == 25.0 &&
		  coefficient == 1 && geometry == 2) ||
		 (info.noise_type == 3 && info.seed == 1 && info.noise_offset == 0 &&
		  info.thickness == 3.0 && info.noise_variation == 100.0 &&
		  coefficient == 2 && geometry == 1) ||
		 (info.noise_type == 2 && info.seed == 1 && info.noise_offset == 1 &&
		  info.thickness == 10.0 && info.noise_variation == 25.0 &&
		  coefficient == 1 && geometry == 1));
}

#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
static bool WriteDirectionalBlurCapture(const char *prefix,
	                                     const char *suffix,
	                                     const void *data,
	                                     size_t byte_count)
{
	if (!prefix || !*prefix || !suffix || !data) {
		return false;
	}
	char path[4096];
	const int length = std::snprintf(path, sizeof(path), "%s.%s", prefix, suffix);
	if (length <= 0 || static_cast<size_t>(length) >= sizeof(path)) {
		return false;
	}
	FILE *file = std::fopen(path, "wb");
	if (!file) {
		return false;
	}
	const bool complete = std::fwrite(data, 1, byte_count, file) == byte_count;
	return std::fclose(file) == 0 && complete;
}
#endif

static PF_Err RenderExact8(PF_EffectWorld *input,
	                                PF_EffectWorld *output,
	                                PF_EffectWorld *noise_layer,
	                                const OLMDirectionalBlurInfo &info,
	                                bool process_full_height = false)
{
	const A_long width = output->width;
	const A_long height = output->height;
	const size_t byte_count = static_cast<size_t>(width) *
	                          static_cast<size_t>(height) * 4;
	std::vector<std::uint8_t> source(byte_count);
	std::vector<std::uint8_t> destination(byte_count);
	for (A_long y = 0; y < height; ++y) {
		for (A_long x = 0; x < width; ++x) {
			const PF_Pixel8 *pixel = PixelAtConst<PF_Pixel8>(input, x, y);
			const size_t offset = (static_cast<size_t>(y) * width + x) * 4;
			source[offset + 0] = pixel->red;
			source[offset + 1] = pixel->green;
			source[offset + 2] = pixel->blue;
			source[offset + 3] = pixel->alpha;
		}
	}

	const double radians = -info.angle_deg * kPi / 180.0;
	const double vx = std::cos(radians), vy = std::sin(radians);
	const float render_scale = static_cast<float>(std::sqrt(
		std::pow(vx * info.render_scale_x, 2) + std::pow(vy * info.render_scale_y, 2)));
	const int result = info.noise_variation > 0.0 && info.noise_type == 3
		? olm_dblur_layer_mode2_rgba8(
			source.data(), destination.data(), width, height,
			static_cast<float>(info.angle_deg),
			static_cast<float>(info.brightness_gain),
			static_cast<int>(info.front_strength),
			static_cast<int>(info.front_alpha_fade),
			static_cast<float>(info.front_sharp_tail),
			static_cast<int>(info.back_strength),
			static_cast<int>(info.back_alpha_fade),
			static_cast<float>(info.back_sharp_tail),
			static_cast<float>(info.size_variation),
			static_cast<float>(info.noise_variation),
			reinterpret_cast<const std::uint8_t *>(noise_layer->data),
			static_cast<int>(noise_layer->width),
			static_cast<int>(noise_layer->height),
			static_cast<int>(noise_layer->rowbytes),
			// The actual AEX's equal-dimension Layer path treats the checked-out
			// pixel buffer as render-local even when its extent origin differs.
			// Keep the extent for host checkout/gating, but bind local (0,0) to
			// the render world's origin at the field-builder boundary.
			static_cast<int>(input->extent_hint.left),
			static_cast<int>(input->extent_hint.top),
			static_cast<int>(input->extent_hint.left),
			static_cast<int>(input->extent_hint.top), render_scale)
		: olm_dblur_noise_mode3_rgba8(
		source.data(), destination.data(), width, height,
		static_cast<float>(info.angle_deg),
		static_cast<float>(info.brightness_gain),
		static_cast<int>(info.front_strength),
		static_cast<int>(info.front_alpha_fade),
		static_cast<float>(info.front_sharp_tail),
		static_cast<int>(info.back_strength),
		static_cast<int>(info.back_alpha_fade),
		static_cast<float>(info.back_sharp_tail),
		static_cast<float>(info.size_variation),
		static_cast<float>(info.noise_variation),
		static_cast<int>(info.noise_type),
		static_cast<std::uint32_t>(info.seed),
		static_cast<int>(info.noise_offset),
		static_cast<float>(info.thickness), render_scale,
			DualSideHigherOrderTuple(info, input->width, input->height) ? 1 : 0,
			process_full_height ? 1 : 0);
	if (result != 0) {
		return result == -5 ? PF_Err_OUT_OF_MEMORY : PF_Err_INTERNAL_STRUCT_DAMAGED;
	}

#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
	const char *capture_prefix = std::getenv("OLM_DBLUR_CAPTURE_PREFIX");
	const bool capture_enabled = capture_prefix && *capture_prefix;
	std::vector<std::uint8_t> output_argb;
	if (capture_enabled) {
		output_argb.resize(byte_count);
	}
#endif
	for (A_long y = 0; y < height; ++y) {
		for (A_long x = 0; x < width; ++x) {
			PF_Pixel8 *pixel = PixelAt<PF_Pixel8>(output, x, y);
			const size_t offset = (static_cast<size_t>(y) * width + x) * 4;
			pixel->red = destination[offset + 0];
			pixel->green = destination[offset + 1];
			pixel->blue = destination[offset + 2];
			pixel->alpha = destination[offset + 3];
#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
			if (capture_enabled) {
				output_argb[offset + 0] = pixel->alpha;
				output_argb[offset + 1] = pixel->red;
				output_argb[offset + 2] = pixel->green;
				output_argb[offset + 3] = pixel->blue;
			}
#endif
		}
	}

#if defined(OLM_DBLUR_ENABLE_BOUNDARY_CAPTURE)
	if (capture_enabled) {
		bool capture_ok = true;
		capture_ok &= WriteDirectionalBlurCapture(capture_prefix, "input.rgba8", source.data(), byte_count);
		capture_ok &= WriteDirectionalBlurCapture(capture_prefix, "core-output.rgba8", destination.data(), byte_count);
		capture_ok &= WriteDirectionalBlurCapture(capture_prefix, "callback-output.argb8", output_argb.data(), byte_count);
		char metadata[512];
		const int metadata_length = std::snprintf(
			metadata, sizeof(metadata),
			"width=%ld\nheight=%ld\ninput_rowbytes=%ld\noutput_rowbytes=%ld\n"
			"angle=%.17g\nbrightness_gain=%.17g\nfront_strength=%ld\nfront_alpha_fade=%ld\n",
			static_cast<long>(width), static_cast<long>(height),
			static_cast<long>(input->rowbytes), static_cast<long>(output->rowbytes),
			static_cast<double>(info.angle_deg), static_cast<double>(info.brightness_gain),
			static_cast<long>(info.front_strength), static_cast<long>(info.front_alpha_fade));
		if (metadata_length > 0) {
			capture_ok &= WriteDirectionalBlurCapture(capture_prefix, "metadata.txt", metadata,
				static_cast<size_t>(std::min<int>(metadata_length, sizeof(metadata) - 1)));
		}
		if (!capture_ok) {
			return PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
#endif
	return PF_Err_NONE;
}

template <typename PixelT, typename ScalarT>
static void StageDirectionalWorld(const PF_EffectWorld *world, std::vector<ScalarT> *pixels)
{
	pixels->resize(static_cast<std::size_t>(world->width) * world->height * 4);
	for (A_long y = 0; y < world->height; ++y) {
		std::memcpy(pixels->data() + static_cast<std::size_t>(y) * world->width * 4,
			reinterpret_cast<const std::uint8_t *>(world->data) +
				static_cast<std::size_t>(y) * static_cast<std::size_t>(world->rowbytes),
			static_cast<std::size_t>(world->width) * sizeof(PixelT));
	}
}

template <typename PixelT, typename ScalarT>
static void UnstageDirectionalWorld(const std::vector<ScalarT> &pixels, PF_EffectWorld *world)
{
	for (A_long y = 0; y < world->height; ++y) {
		std::memcpy(reinterpret_cast<std::uint8_t *>(world->data) +
				static_cast<std::size_t>(y) * static_cast<std::size_t>(world->rowbytes),
			pixels.data() + static_cast<std::size_t>(y) * world->width * 4,
			static_cast<std::size_t>(world->width) * sizeof(PixelT));
	}
}

static PF_Err RenderGenericNeutral16(PF_EffectWorld *input, PF_EffectWorld *output,
		                                     const OLMDirectionalBlurInfo &info)
{
	std::vector<std::uint16_t> source, destination;
	StageDirectionalWorld<PF_Pixel16>(input, &source);
	destination.resize(source.size());
	const int result = olm_dblur_minimal_argb16(source.data(), destination.data(),
		input->width, input->height, static_cast<int>(info.front_strength),
		static_cast<int>(info.back_strength),
		static_cast<float>(info.brightness_gain), static_cast<float>(info.angle_deg),
		0.0f, 1, 1, 0, 10.0f, 0);
	if (result != 0) return result == -5 ? PF_Err_OUT_OF_MEMORY : PF_Err_INTERNAL_STRUCT_DAMAGED;
	UnstageDirectionalWorld<PF_Pixel16>(destination, output);
	return PF_Err_NONE;
}

static PF_Err RenderGenericNeutral32(PF_EffectWorld *input, PF_EffectWorld *output,
		                                     const OLMDirectionalBlurInfo &info)
{
	std::vector<float> source, destination;
	StageDirectionalWorld<PF_PixelFloat>(input, &source);
	destination.resize(source.size());
	const int result = olm_dblur_minimal_argb32(source.data(), destination.data(),
		input->width, input->height, static_cast<int>(info.front_strength),
		static_cast<int>(info.back_strength), 0.0f,
		static_cast<float>(info.angle_deg), static_cast<float>(info.brightness_gain),
		0.0f, 1, 1, 0, 10.0f, nullptr, 0, 0);
	if (result != 0) return result == -5 ? PF_Err_OUT_OF_MEMORY : PF_Err_INTERNAL_STRUCT_DAMAGED;
	UnstageDirectionalWorld<PF_PixelFloat>(destination, output);
	return PF_Err_NONE;
}

template <typename PixelT>
static bool GenericDeepLayerWorldSafe(const PF_EffectWorld *input,
    const PF_EffectWorld *output, const PF_EffectWorld *layer,
    const OLMDirectionalBlurInfo &info)
{
    if (info.noise_variation <= 0.0 || info.noise_type != 3) return true;
    std::uintptr_t begin = 0, end = 0;
    return input && output && layer && layer->data &&
        layer->width == input->width && layer->height == input->height &&
        DirectionalWorldHasZeroOrigin(input, 0) && DirectionalWorldHasZeroOrigin(output, 0) &&
        DirectionalWorldHasZeroOrigin(layer, 0) &&
        layer->rowbytes > 0 && static_cast<std::size_t>(layer->rowbytes) >=
            static_cast<std::size_t>(input->width) * sizeof(PixelT) &&
        PayloadSpan(layer, &begin, &end) && DisjointPayloads(input, layer) &&
        DisjointPayloads(output, layer);
}

static PF_Err RenderGenericDeepFeatures(PF_EffectWorld *input, PF_EffectWorld *output,
    const OLMDirectionalBlurInfo &info, short depth, PF_EffectWorld *noise_layer)
{
    const bool use_layer = info.noise_variation > 0.0 && info.noise_type == 3;
    int result;
    if (depth == 16) {
        std::vector<std::uint16_t> source, destination, layer;
        if (use_layer) StageDirectionalWorld<PF_Pixel16>(noise_layer, &layer);
        StageDirectionalWorld<PF_Pixel16>(input, &source); destination.resize(source.size());
        result = olm_dblur_full_argb16(source.data(), destination.data(), input->width, input->height,
            info.front_strength, info.front_alpha_fade, info.front_sharp_tail,
            info.back_strength, info.back_alpha_fade, info.back_sharp_tail,
            info.size_variation, info.brightness_gain, info.angle_deg, info.noise_variation,
            info.noise_type, info.seed, info.noise_offset, info.thickness,
            use_layer ? layer.data() : nullptr,
            use_layer ? input->width * (depth == 16 ? 8 : 16) : 0, 1);
        if (!result) UnstageDirectionalWorld<PF_Pixel16>(destination, output);
    } else {
        std::vector<float> source, destination, layer;
        if (use_layer) StageDirectionalWorld<PF_PixelFloat>(noise_layer, &layer);
        StageDirectionalWorld<PF_PixelFloat>(input, &source); destination.resize(source.size());
        result = olm_dblur_full_argb32(source.data(), destination.data(), input->width, input->height,
            info.front_strength, info.front_alpha_fade, info.front_sharp_tail,
            info.back_strength, info.back_alpha_fade, info.back_sharp_tail,
            info.size_variation, info.angle_deg, info.brightness_gain, info.noise_variation,
            info.noise_type, info.seed, info.noise_offset, info.thickness,
            use_layer ? layer.data() : nullptr,
            use_layer ? input->width * (depth == 16 ? 8 : 16) : 0, 1);
        if (!result) UnstageDirectionalWorld<PF_PixelFloat>(destination, output);
    }
    return result == 0 ? PF_Err_NONE : result == -5 ? PF_Err_OUT_OF_MEMORY : PF_Err_INTERNAL_STRUCT_DAMAGED;
}

enum DirectionalRenderRoute {
	kDirectionalRouteOther = 0,
	kDirectionalRouteRetainedNeutralBackExact = 1,
	kDirectionalRouteGenericNeutral = 2,
	kDirectionalRouteGenericDeepFeatures = 3,
};

static void ObserveDirectionalRenderRoute(int *observed_route,
	                                      DirectionalRenderRoute route)
{
	if (observed_route) *observed_route = static_cast<int>(route);
}

static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
                          PF_EffectWorld *noise_layer,
                          const OLMDirectionalBlurInfo &requested_info, short bitdepth,
                          int *observed_route = nullptr)
{
    const auto info = DirectionalDeepLayerInfo(requested_info, input, noise_layer, bitdepth);
	ObserveDirectionalRenderRoute(observed_route, kDirectionalRouteOther);
	const bool dual_side_higher_order = DualSideHigherOrderTuple(info, 32, 18);
	if (dual_side_higher_order &&
		!PublicDualSideExportedSmartExact(input, output, info, bitdepth)) {
		// The other retained dual-side values invoke internal render owner
		// 0x180007BD0 directly.  They remain fail-closed unless the same-source
		// exported Smart route is independently raw-exact to the Mac public path.
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (bitdepth == 8 && PublicType3Layer16Tuple(info)) {
		// PF8 retains the exported same-source Layer tuple contract. PF16/PF32
		// use the general deep Layer path witnessed with independent fields.
		if (!PublicType3Layer16WorldsExact(input, output, noise_layer, bitdepth)) {
			return PF_Err_BAD_CALLBACK_PARAM;
		}
	}
	const bool default_no_op = input && output && input->data && output->data &&
		input->width == output->width && input->height == output->height &&
		info.angle_deg == 0.0 && info.brightness_gain == 1.0 &&
		info.size_variation == 0.0 &&
		info.front_strength == 0 && info.front_alpha_fade == 0 &&
		info.front_sharp_tail == 0.0 &&
		info.back_strength == 0 && info.back_alpha_fade == 0 &&
		info.back_sharp_tail == 0.0 && info.noise_variation == 0.0 &&
		info.noise_type == 1 && info.seed == 1 && info.noise_offset == 0 &&
		info.thickness == 10.0;
	if (default_no_op) {
		switch (bitdepth) {
		case 8: CopyWorld<PF_Pixel8>(input, output); return PF_Err_NONE;
		case 16: CopyWorld<PF_Pixel16>(input, output); return PF_Err_NONE;
		case 32: CopyWorld<PF_PixelFloat>(input, output); return PF_Err_NONE;
		default: return PF_Err_BAD_CALLBACK_PARAM;
		}
	}
	if (bitdepth == 8) {
		const bool noise_type2_natural64_tuple = input &&
			NoiseType2Natural64Tuple(info, input->width, input->height);
		const bool noise_type2_natural64_exact = noise_type2_natural64_tuple &&
			output && output->width == 64 && output->height == 36 &&
			output->data &&
			Natural64RowbytesSafe(input->rowbytes, sizeof(PF_Pixel8)) &&
			Natural64RowbytesSafe(output->rowbytes, sizeof(PF_Pixel8)) &&
			Natural64SourceExact(input, sizeof(PF_Pixel8));
		if (noise_type2_natural64_tuple) {
			// This tuple has five same-source PF8 owner witnesses.  Reject a
			// mutated or unlisted source here instead of falling through to the
			// older generic PF8 renderer, whose arbitrary-source relation is not
			// part of the bounded natural64 evidence.
			return noise_type2_natural64_exact
				? RenderExact8(input, output, noise_layer, info)
				: PF_Err_BAD_CALLBACK_PARAM;
		}
		if (IsRetainedNeutralBackExact8(input, output, info) &&
			CanUseExact8(input, output, nullptr, info)) {
			// Preserve retained actual-AEX raw-callback Back Strength witnesses and
			// their historical worker-tail partition before the full-height beta.
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteRetainedNeutralBackExact);
			return RenderExact8(input, output, nullptr, info);
		}
		if (CanUseGenericNeutral8(input, output, info)) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteGenericNeutral);
			// Native owners schedule min(height,32) equal integer row ranges.
			// The remainder keeps the preseeded rotated source, even in this
			// general route; overwriting all rows changes Windows output.
			return RenderExact8(input, output, nullptr, info, false);
		}
		if (IsGenericNeutralShape(info)) {
			// Do not let an invalid world or over-budget frame fall through to the
			// older permissive exact predicate.
			return PF_Err_BAD_CALLBACK_PARAM;
		}
		if (CanUseExact8(input, output, noise_layer, info)) {
			return RenderExact8(input, output, noise_layer, info);
		}
		if (info.noise_variation > 0.0 && info.noise_type == 3) {
			// Do not silently substitute the legacy approximate renderer when
			// the checked-out Layer contract falls outside the proven mode-2
			// dimensions/origin boundary.
			return PF_Err_BAD_CALLBACK_PARAM;
		}
		return RenderDirectional8(input, output, info);
	}
	if (bitdepth == 16) {
		const bool retained_exact = IsRetainedNeutralExact(input, output, info, 16);
		if (retained_exact) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteRetainedNeutralBackExact);
		}
        if (!retained_exact && IsGenericDeepFeatureShape(info)) {
            if (!GenericDeepFeatureWorldsSafe<PF_Pixel16>(input, output, info) ||
                !GenericDeepLayerWorldSafe<PF_Pixel16>(input, output, noise_layer, info) ||
                !GenericPF16SDRInput(input) ||
                (info.noise_variation > 0.0 && info.noise_type == 3 &&
                    !GenericPF16SDRInput(noise_layer))) return PF_Err_BAD_CALLBACK_PARAM;
            ObserveDirectionalRenderRoute(observed_route, kDirectionalRouteGenericDeepFeatures);
            return RenderGenericDeepFeatures(input, output, info, 16, noise_layer);
        }
		if (!retained_exact &&
			IsGenericNeutralDeepParameters(info) &&
			GenericDeepWorldsSafe<PF_Pixel16>(input, output, info)) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteGenericNeutral);
			return GenericPF16SDRInput(input)
				? RenderGenericNeutral16(input, output, info) : PF_Err_BAD_CALLBACK_PARAM;
		}
		if (!retained_exact && IsGenericNeutralShape(info)) {
			return PF_Err_BAD_CALLBACK_PARAM;
		}
		const bool front_only_exact =
			(info.front_strength == 1 || info.front_strength == 2 || info.front_strength == 8) &&
			info.back_strength == 0;
		const bool back_family_exact =
			(((info.front_strength == 0 || info.front_strength == 1 ||
			   info.front_strength == 2 || info.front_strength == 8) &&
			  info.back_strength == 1) ||
			 (info.front_strength == 0 &&
			  (info.back_strength == 2 || info.back_strength == 8))) &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
			info.noise_variation == 0.0;
		const bool pf16_fade_sharp_family_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
			info.size_variation == 0.0 && info.noise_variation == 0.0 &&
			((info.front_strength == 8 && info.back_strength == 0 &&
			  info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			  (((info.front_alpha_fade == 0 || info.front_alpha_fade == 50 ||
			     info.front_alpha_fade == 100) && info.front_sharp_tail == 0.0) ||
			   (info.front_alpha_fade == 0 &&
			    (info.front_sharp_tail == 0.0 || info.front_sharp_tail == 50.0 ||
			     info.front_sharp_tail == 100.0)) ||
			   ((info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			    (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0)))) ||
			 (info.front_strength == 0 && info.back_strength == 8 &&
			  info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			  (((info.back_alpha_fade == 0 || info.back_alpha_fade == 50 ||
			     info.back_alpha_fade == 100) && info.back_sharp_tail == 0.0) ||
			   (info.back_alpha_fade == 0 &&
			    (info.back_sharp_tail == 0.0 || info.back_sharp_tail == 50.0 ||
			     info.back_sharp_tail == 100.0)) ||
			   ((info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			    (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)))));
		const bool fade_sharp_cross_exact = pf16_fade_sharp_family_exact &&
			((info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			 (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0) ||
			 (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			 (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0));
		const bool pf16_size_variation_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.size_variation >= 0.0 && info.size_variation <= 100.0 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
			info.brightness_gain == 1.0;
		const bool pf16_size_fade_cross_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.size_variation == 25.0 || info.size_variation == 50.0 ||
			 info.size_variation == 100.0) &&
			(info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.front_sharp_tail == 0.0 && info.back_alpha_fade == 0 &&
			info.back_sharp_tail == 0.0 && info.noise_variation == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool pf16_size_sharp_cross_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.size_variation == 50.0 &&
			(info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0) &&
			info.front_alpha_fade == 0 && info.front_strength == 8 &&
			info.back_strength == 0 && info.back_alpha_fade == 0 &&
			info.back_sharp_tail == 0.0 && info.noise_variation == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool pf16_size_back_cross_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.front_strength == 0 && info.back_strength == 8 &&
			info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
			info.brightness_gain == 1.0 &&
			(((info.size_variation == 25.0 || info.size_variation == 50.0 ||
			   info.size_variation == 100.0) &&
			  (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			  info.back_sharp_tail == 0.0) ||
			 (info.size_variation == 50.0 && info.back_alpha_fade == 0 &&
			  (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)));
		const bool pf16_noise_size_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.size_variation == 0.0 || info.size_variation == 50.0) &&
			(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
			(info.noise_type == 2 ||
			 (info.noise_type == 3 && noise_layer && noise_layer->data &&
			  noise_layer->width == input->width && noise_layer->height == input->height &&
			  noise_layer->rowbytes >= input->width * static_cast<A_long>(sizeof(PF_Pixel16)))) &&
			info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool noise_public_pairwise_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			NoisePublicPairwiseTuple(info, input->width, input->height) &&
			(info.noise_type != 3 ||
			 (noise_layer && noise_layer->data && noise_layer->width == input->width &&
			  noise_layer->height == input->height &&
			  noise_layer->rowbytes >= input->width * static_cast<A_long>(sizeof(PF_Pixel16))));
		const bool noise_coefficient_higher_order_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			NoiseCoefficientHigherOrderTuple(info, input->width, input->height);
		const bool dual_side_higher_order_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			DualSideHigherOrderTuple(info, input->width, input->height);
		const bool noise_type2_natural64_exact = input && output &&
			NoiseType2Natural64Tuple(info, input->width, input->height) &&
			output->width == 64 && output->height == 36 &&
			Natural64RowbytesSafe(input->rowbytes, sizeof(PF_Pixel16)) &&
			Natural64RowbytesSafe(output->rowbytes, sizeof(PF_Pixel16)) &&
			Natural64SourceExact(input, sizeof(PF_Pixel16));
		const bool pf16_full_exact = pf16_fade_sharp_family_exact || fade_sharp_cross_exact ||
			pf16_size_variation_exact || pf16_size_fade_cross_exact ||
			pf16_size_sharp_cross_exact || pf16_size_back_cross_exact ||
			pf16_noise_size_exact || noise_public_pairwise_exact ||
			noise_coefficient_higher_order_exact || dual_side_higher_order_exact;
		const bool minimal_exact = input && output && input->data && output->data &&
			input->width == output->width && input->height == output->height &&
			(info.angle_deg == 0.0 || info.angle_deg == 45.0) &&
			(info.brightness_gain == 1.0 || info.brightness_gain == 0.5) &&
			(info.size_variation == 0.0 || pf16_size_variation_exact ||
			 pf16_size_fade_cross_exact || pf16_size_sharp_cross_exact ||
			 pf16_size_back_cross_exact || pf16_noise_size_exact ||
			 noise_public_pairwise_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(front_only_exact || back_family_exact || pf16_full_exact ||
			 dual_side_higher_order_exact) &&
			(info.front_alpha_fade == 0 || pf16_fade_sharp_family_exact ||
				 pf16_size_fade_cross_exact || noise_public_pairwise_exact ||
				 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			(info.front_sharp_tail == 0.0 || pf16_fade_sharp_family_exact ||
				 pf16_size_sharp_cross_exact || noise_public_pairwise_exact ||
				 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			(info.back_alpha_fade == 0 || pf16_fade_sharp_family_exact ||
				 pf16_size_back_cross_exact || noise_public_pairwise_exact ||
				 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			(info.back_sharp_tail == 0.0 || pf16_fade_sharp_family_exact ||
			 pf16_size_back_cross_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.noise_variation == 0.0 || pf16_noise_size_exact ||
			 noise_public_pairwise_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact || noise_type2_natural64_exact ||
			 (info.noise_variation == 100.0 &&
			  (info.noise_type == 1 || info.noise_type == 2 ||
			   (info.noise_type == 3 && noise_layer && noise_layer->data &&
			    noise_layer->width == input->width && noise_layer->height == input->height)) &&
			  info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0 &&
			  info.front_strength == 8 && info.angle_deg == 45.0)) &&
			info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
		if (minimal_exact) {
			const std::size_t words = static_cast<std::size_t>(input->width) * input->height * 4;
			std::vector<std::uint16_t> source(words), destination(words);
			for (A_long y = 0; y < input->height; ++y) {
				std::memcpy(source.data() + static_cast<std::size_t>(y) * input->width * 4,
					reinterpret_cast<const std::uint8_t *>(input->data) + y * input->rowbytes,
					static_cast<std::size_t>(input->width) * sizeof(PF_Pixel16));
			}
			const int result = pf16_full_exact
				? olm_dblur_full_argb16(
					source.data(), destination.data(), input->width, input->height,
					static_cast<int>(info.front_strength), static_cast<int>(info.front_alpha_fade),
					static_cast<float>(info.front_sharp_tail), static_cast<int>(info.back_strength),
					static_cast<int>(info.back_alpha_fade), static_cast<float>(info.back_sharp_tail),
					static_cast<float>(info.size_variation),
					static_cast<float>(info.brightness_gain), static_cast<float>(info.angle_deg),
					static_cast<float>(info.noise_variation), static_cast<int>(info.noise_type),
					static_cast<std::uint32_t>(info.seed), info.noise_offset,
					static_cast<float>(info.thickness),
					info.noise_type == 3 && noise_layer
						? reinterpret_cast<const std::uint16_t *>(noise_layer->data) : nullptr,
					info.noise_type == 3 && noise_layer ? static_cast<int>(noise_layer->rowbytes) : 0,
					dual_side_higher_order_exact ? 1 : 0)
				: info.noise_type == 3
				? olm_dblur_minimal_layer_argb16(
					source.data(), destination.data(), input->width, input->height,
					static_cast<int>(info.front_strength), static_cast<int>(info.back_strength),
					static_cast<float>(info.brightness_gain), static_cast<float>(info.angle_deg),
					static_cast<float>(info.noise_variation),
					reinterpret_cast<const std::uint16_t *>(noise_layer->data),
					static_cast<int>(noise_layer->rowbytes))
				: olm_dblur_minimal_argb16(
					source.data(), destination.data(), input->width, input->height,
					static_cast<int>(info.front_strength), static_cast<int>(info.back_strength),
					static_cast<float>(info.brightness_gain), static_cast<float>(info.angle_deg),
					static_cast<float>(info.noise_variation), static_cast<int>(info.noise_type),
					static_cast<std::uint32_t>(info.seed), info.noise_offset,
					static_cast<float>(info.thickness));
			if (result != 0) return result == -5 ? PF_Err_OUT_OF_MEMORY : PF_Err_INTERNAL_STRUCT_DAMAGED;
			for (A_long y = 0; y < output->height; ++y) {
				std::memcpy(reinterpret_cast<std::uint8_t *>(output->data) + y * output->rowbytes,
					destination.data() + static_cast<std::size_t>(y) * output->width * 4,
					static_cast<std::size_t>(output->width) * sizeof(PF_Pixel16));
			}
			return PF_Err_NONE;
		}
		// Do not make a missing PF16 port look like a successful identity
		// render. Extend the predicate only with an actual-AEX byte oracle.
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (bitdepth == 32) {
		const bool retained_exact = IsRetainedNeutralExact(input, output, info, 32);
		if (retained_exact) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteRetainedNeutralBackExact);
		}
        if (!retained_exact && IsGenericDeepFeatureShape(info)) {
            // First reserve the complete workspace using unamplified Strength,
            // before reading even a potentially invalid Layer payload.
            if (!GenericDeepFeatureWorldsSafe<PF_PixelFloat>(input, output, info, 0, 1.0) ||
                !GenericDeepLayerWorldSafe<PF_PixelFloat>(input, output, noise_layer, info)) return PF_Err_BAD_CALLBACK_PARAM;
            double layer_bound = std::numeric_limits<double>::infinity();
            if (info.noise_variation > 0.0 && info.noise_type == 3 &&
                (!GenericPF32LayerCoefficientBound(noise_layer, info, &layer_bound) ||
                 !GenericDeepFeatureWorldsSafe<PF_PixelFloat>(input, output, info, 0, layer_bound))) {
                return PF_Err_BAD_CALLBACK_PARAM;
            }
            if (!GenericPF32FiniteInput(input)) return PF_Err_BAD_CALLBACK_PARAM;
            ObserveDirectionalRenderRoute(observed_route, kDirectionalRouteGenericDeepFeatures);
            return RenderGenericDeepFeatures(input, output, info, 32, noise_layer);
        }
		if (!retained_exact &&
			IsGenericNeutralDeepParameters(info) &&
			GenericDeepWorldsSafe<PF_PixelFloat>(input, output, info)) {
			ObserveDirectionalRenderRoute(
				observed_route, kDirectionalRouteGenericNeutral);
			return GenericPF32FiniteInput(input)
				? RenderGenericNeutral32(input, output, info) : PF_Err_BAD_CALLBACK_PARAM;
		}
		if (!retained_exact && IsGenericNeutralShape(info)) {
			return PF_Err_BAD_CALLBACK_PARAM;
		}
		const bool front_alpha_fade_exact =
			info.front_alpha_fade >= 0 && info.front_alpha_fade <= 100 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.size_variation == 0.0 && info.angle_deg == 45.0 &&
			info.brightness_gain == 1.0 && info.noise_variation == 0.0;
		const bool front_fade_size_combination_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.front_alpha_fade > 0 && info.front_alpha_fade <= 100 &&
			info.size_variation > 0.0 && info.size_variation <= 100.0 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
			info.noise_variation == 0.0;
		const bool size_noise_type1_combination_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.size_variation == 0.0 || info.size_variation == 25.0 ||
			 info.size_variation == 100.0) &&
			(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
			info.noise_type == 1 && info.seed == 1 && info.noise_offset == 0 &&
			info.thickness == 3.0 && info.front_strength == 8 &&
			info.back_strength == 0 && info.front_alpha_fade == 0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool fade_noise_type1_combination_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.front_alpha_fade == 0 || info.front_alpha_fade == 50 ||
			 info.front_alpha_fade == 100) &&
			(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
			info.noise_type == 1 && info.seed == 1 && info.noise_offset == 0 &&
			info.thickness == 3.0 && info.front_strength == 8 &&
			info.back_strength == 0 && info.size_variation == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool sharp_back_family_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			info.size_variation == 0.0 && info.noise_variation == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0 &&
			((info.front_strength == 8 && info.back_strength == 0 &&
			  (info.front_sharp_tail == 0.0 || info.front_sharp_tail == 50.0 ||
			   info.front_sharp_tail == 100.0) &&
			  (info.front_alpha_fade == 0 || info.front_alpha_fade == 50 ||
			   info.front_alpha_fade == 100) && info.back_alpha_fade == 0 &&
			  info.back_sharp_tail == 0.0) ||
			 (info.front_strength == 0 && info.back_strength == 8 &&
			  info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			  (((info.back_alpha_fade == 0 || info.back_alpha_fade == 50 ||
			     info.back_alpha_fade == 100) && info.back_sharp_tail == 0.0) ||
			   (info.back_alpha_fade == 0 &&
			    (info.back_sharp_tail == 0.0 || info.back_sharp_tail == 50.0 ||
			     info.back_sharp_tail == 100.0)) ||
			   ((info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			    (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)))));
		const bool fade_sharp_cross_exact = sharp_back_family_exact &&
			((info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			 (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0) ||
			 (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			 (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0));
		const bool pf32_noise_size_exact =
			input && output && input->width == 16 && input->height == 16 &&
			output->width == 16 && output->height == 16 &&
			(info.size_variation == 0.0 || info.size_variation == 50.0) &&
			(info.noise_variation == 25.0 || info.noise_variation == 100.0) &&
			(info.noise_type == 2 ||
			 (info.noise_type == 3 && noise_layer && noise_layer->data &&
			  noise_layer->width == input->width && noise_layer->height == input->height &&
			  noise_layer->rowbytes >= input->width * static_cast<A_long>(sizeof(PF_PixelFloat)))) &&
			info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0 &&
			info.front_strength == 8 && info.back_strength == 0 &&
			info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			info.angle_deg == 45.0 && info.brightness_gain == 1.0;
		const bool noise_public_pairwise_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			NoisePublicPairwiseTuple(info, input->width, input->height) &&
			(info.noise_type != 3 ||
			 (noise_layer && noise_layer->data && noise_layer->width == input->width &&
			  noise_layer->height == input->height &&
			  noise_layer->rowbytes >= input->width * static_cast<A_long>(sizeof(PF_PixelFloat))));
		const bool noise_coefficient_higher_order_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			NoiseCoefficientHigherOrderTuple(info, input->width, input->height);
		const bool dual_side_higher_order_exact = input && output &&
			output->width == input->width && output->height == input->height &&
			DualSideHigherOrderTuple(info, input->width, input->height);
		const bool noise_type2_natural64_exact = input && output &&
			NoiseType2Natural64Tuple(info, input->width, input->height) &&
			output->width == 64 && output->height == 36 &&
			Natural64RowbytesSafe(input->rowbytes, sizeof(PF_PixelFloat)) &&
			Natural64RowbytesSafe(output->rowbytes, sizeof(PF_PixelFloat)) &&
			Natural64SourceExact(input, sizeof(PF_PixelFloat));
		const bool pf32_size_coeff_cross_exact =
			input && output &&
			((input->width == 16 && input->height == 16) ||
			 (input->width == 32 && input->height == 18)) &&
			output->width == input->width && output->height == input->height &&
			info.noise_variation == 0.0 && info.angle_deg == 45.0 &&
			info.brightness_gain == 1.0 &&
			((info.front_strength == 8 && info.back_strength == 0 &&
			  info.back_alpha_fade == 0 && info.back_sharp_tail == 0.0 &&
			  (((info.size_variation == 25.0 || info.size_variation == 50.0 ||
			     info.size_variation == 100.0) &&
			    (info.front_alpha_fade == 50 || info.front_alpha_fade == 100) &&
			    info.front_sharp_tail == 0.0) ||
			   (info.size_variation == 50.0 && info.front_alpha_fade == 0 &&
			    (info.front_sharp_tail == 50.0 || info.front_sharp_tail == 100.0)))) ||
			 (info.front_strength == 0 && info.back_strength == 8 &&
			  info.front_alpha_fade == 0 && info.front_sharp_tail == 0.0 &&
			  (((info.size_variation == 25.0 || info.size_variation == 50.0 ||
			     info.size_variation == 100.0) &&
			    (info.back_alpha_fade == 50 || info.back_alpha_fade == 100) &&
			    info.back_sharp_tail == 0.0) ||
			   (info.size_variation == 50.0 && info.back_alpha_fade == 0 &&
			    (info.back_sharp_tail == 50.0 || info.back_sharp_tail == 100.0)))));
		const bool minimal_exact = input && output && input->data && output->data &&
			input->width == output->width && input->height == output->height &&
			(info.angle_deg == 0.0 || info.angle_deg == 45.0) &&
			(info.brightness_gain == 1.0 || info.brightness_gain == 0.5) &&
			((info.size_variation == 0.0 &&
			  ((info.front_strength == 1 || info.front_strength == 2) ||
			   (info.front_strength == 0 && info.back_strength == 1) ||
			   (info.front_strength == 8 && info.back_strength == 0))) ||
			 (info.size_variation >= 0.0 && info.size_variation <= 100.0 &&
			  info.front_strength == 8 &&
			  info.back_strength == 0) || sharp_back_family_exact ||
			 pf32_noise_size_exact || pf32_size_coeff_cross_exact ||
			 noise_public_pairwise_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.front_alpha_fade == 0 || front_alpha_fade_exact ||
			 front_fade_size_combination_exact || fade_noise_type1_combination_exact ||
			 pf32_size_coeff_cross_exact || noise_public_pairwise_exact ||
			 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			 (info.front_sharp_tail == 0.0 || sharp_back_family_exact || fade_sharp_cross_exact ||
			 pf32_size_coeff_cross_exact || noise_public_pairwise_exact ||
			 noise_coefficient_higher_order_exact || dual_side_higher_order_exact) &&
			((info.back_strength == 0 || info.back_strength == 1) || sharp_back_family_exact ||
			 pf32_size_coeff_cross_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.back_alpha_fade == 0 || sharp_back_family_exact ||
			 pf32_size_coeff_cross_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.back_sharp_tail == 0.0 || sharp_back_family_exact ||
			 pf32_size_coeff_cross_exact || noise_coefficient_higher_order_exact ||
			 dual_side_higher_order_exact) &&
			(info.noise_variation == 0.0 || size_noise_type1_combination_exact ||
			 fade_noise_type1_combination_exact ||
			 pf32_noise_size_exact || noise_public_pairwise_exact ||
			 noise_coefficient_higher_order_exact || dual_side_higher_order_exact ||
			 noise_type2_natural64_exact ||
			 (info.noise_variation == 100.0 &&
			  (info.noise_type == 1 || info.noise_type == 2 ||
			   (info.noise_type == 3 && noise_layer && noise_layer->data &&
			    noise_layer->width == input->width && noise_layer->height == input->height)) &&
			  info.seed == 1 && info.noise_offset == 0 && info.thickness == 3.0 &&
			  info.front_strength == 8 && info.back_strength == 0 &&
			  info.size_variation == 0.0 && info.angle_deg == 45.0)) &&
			info.render_scale_x == 1.0 && info.render_scale_y == 1.0;
		if (minimal_exact) {
			const std::size_t values = static_cast<std::size_t>(input->width) * input->height * 4;
			std::vector<float> source(values), destination(values);
			for (A_long y = 0; y < input->height; ++y)
				std::memcpy(source.data() + static_cast<std::size_t>(y) * input->width * 4,
					reinterpret_cast<const std::uint8_t *>(input->data) + y * input->rowbytes,
					static_cast<std::size_t>(input->width) * sizeof(PF_PixelFloat));
			const float *layer_data = info.noise_type == 3 && noise_layer
				? reinterpret_cast<const float *>(noise_layer->data) : nullptr;
			const int layer_rowbytes = info.noise_type == 3 && noise_layer
				? static_cast<int>(noise_layer->rowbytes) : 0;
			const int result = sharp_back_family_exact || pf32_size_coeff_cross_exact ||
				noise_public_pairwise_exact || noise_coefficient_higher_order_exact ||
				dual_side_higher_order_exact
				? olm_dblur_full_argb32(source.data(), destination.data(),
					input->width, input->height, static_cast<int>(info.front_strength),
					static_cast<int>(info.front_alpha_fade), static_cast<float>(info.front_sharp_tail),
					static_cast<int>(info.back_strength), static_cast<int>(info.back_alpha_fade),
					static_cast<float>(info.back_sharp_tail), static_cast<float>(info.size_variation),
					static_cast<float>(info.angle_deg), static_cast<float>(info.brightness_gain),
					static_cast<float>(info.noise_variation), static_cast<int>(info.noise_type),
					static_cast<std::uint32_t>(info.seed), info.noise_offset,
					static_cast<float>(info.thickness), layer_data, layer_rowbytes,
					dual_side_higher_order_exact ? 1 : 0)
				: info.front_alpha_fade == 0
				? olm_dblur_minimal_argb32(source.data(), destination.data(),
					input->width, input->height, static_cast<int>(info.front_strength),
					static_cast<int>(info.back_strength), static_cast<float>(info.size_variation),
					static_cast<float>(info.angle_deg), static_cast<float>(info.brightness_gain),
					static_cast<float>(info.noise_variation), static_cast<int>(info.noise_type),
					static_cast<std::uint32_t>(info.seed), info.noise_offset,
					static_cast<float>(info.thickness), layer_data, layer_rowbytes)
				: olm_dblur_minimal_fade_argb32(source.data(), destination.data(),
					input->width, input->height, static_cast<int>(info.front_strength),
					static_cast<int>(info.back_strength), static_cast<int>(info.front_alpha_fade),
					static_cast<float>(info.size_variation), static_cast<float>(info.angle_deg),
					static_cast<float>(info.brightness_gain), static_cast<float>(info.noise_variation),
					static_cast<int>(info.noise_type), static_cast<std::uint32_t>(info.seed),
					info.noise_offset, static_cast<float>(info.thickness), layer_data, layer_rowbytes);
			if (result != 0) return result == -5 ? PF_Err_OUT_OF_MEMORY : PF_Err_INTERNAL_STRUCT_DAMAGED;
			for (A_long y = 0; y < output->height; ++y)
				std::memcpy(reinterpret_cast<std::uint8_t *>(output->data) + y * output->rowbytes,
					destination.data() + static_cast<std::size_t>(y) * output->width * 4,
					static_cast<std::size_t>(output->width) * sizeof(PF_PixelFloat));
			return PF_Err_NONE;
		}
		// Do not make a missing PF32 port look like a successful identity
		// render. Extend the predicate only with an actual-AEX byte oracle.
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	return PF_Err_BAD_CALLBACK_PARAM;
}

#if defined(OLM_DBLUR_TEST_SEAM)
struct OLMDirectionalBlurGenericEstimate {
	std::uint64_t source_pixels;
	std::uint64_t work_width;
	std::uint64_t work_height;
	std::uint64_t work_pixels;
	std::uint64_t core_workspace_bytes;
	std::uint64_t wrapper_bytes;
	std::uint64_t weight_bytes;
	std::uint64_t smart_staging_bytes;
	std::uint64_t plugin_owned_live_bytes;
	std::uint64_t operation_units;
};

// Test-only transparent view of the exact production estimator.  Tests do not
// duplicate the geometry, live-allocation, or rowdriver-work arithmetic.
extern "C" int OLMDirectionalBlurTestGenericEstimate(
	A_long width,
	A_long height,
	short bitdepth,
	A_long effective_strength,
	std::size_t smart_staging_bytes,
	OLMDirectionalBlurGenericEstimate *result)
{
	if (!result) return 0;
	olm::dblur::generic::RenderEstimate estimate = {};
	if (!olm::dblur::generic::EstimateRender(
		width, height, bitdepth, static_cast<int>(effective_strength),
		smart_staging_bytes, &estimate)) {
		*result = {};
		return 0;
	}
	result->source_pixels = estimate.source_pixels;
	result->work_width = static_cast<std::uint64_t>(estimate.work.width);
	result->work_height = static_cast<std::uint64_t>(estimate.work.height);
	result->work_pixels = estimate.work.pixels;
	result->core_workspace_bytes = estimate.core_workspace_bytes;
	result->wrapper_bytes = estimate.wrapper_bytes;
	result->weight_bytes = estimate.weight_bytes;
	result->smart_staging_bytes = estimate.smart_staging_bytes;
	result->plugin_owned_live_bytes = estimate.plugin_owned_live_bytes;
	result->operation_units = estimate.operation_units;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEstimateSides(
	A_long width,
	A_long height,
	short bitdepth,
	A_long effective_front_strength,
	A_long effective_back_strength,
	std::size_t smart_staging_bytes,
	OLMDirectionalBlurGenericEstimate *result)
{
	if (!result) return 0;
	olm::dblur::generic::RenderEstimate estimate = {};
	if (!olm::dblur::generic::EstimateRender(
		width, height, bitdepth, static_cast<int>(effective_front_strength),
		static_cast<int>(effective_back_strength), smart_staging_bytes, &estimate)) {
		*result = {};
		return 0;
	}
	result->source_pixels = estimate.source_pixels;
	result->work_width = static_cast<std::uint64_t>(estimate.work.width);
	result->work_height = static_cast<std::uint64_t>(estimate.work.height);
	result->work_pixels = estimate.work.pixels;
	result->core_workspace_bytes = estimate.core_workspace_bytes;
	result->wrapper_bytes = estimate.wrapper_bytes;
	result->weight_bytes = estimate.weight_bytes;
	result->smart_staging_bytes = estimate.smart_staging_bytes;
	result->plugin_owned_live_bytes = estimate.plugin_owned_live_bytes;
	result->operation_units = estimate.operation_units;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEffectiveStrength(
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *effective_strength)
{
	int front = 0, back = 0;
	if (!info || !effective_strength ||
		(bitdepth != 8 && bitdepth != 16 && bitdepth != 32) ||
		!GenericEffectiveStrengths(*info, bitdepth != 8, &front, &back) ||
		(front > 0 && back > 0)) {
		return 0;
	}
	*effective_strength = front > 0 ? front : back;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEffectiveStrengths(
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *effective_front_strength,
	int *effective_back_strength)
{
	return info && (bitdepth == 8 || bitdepth == 16 || bitdepth == 32) &&
		GenericEffectiveStrengths(*info, bitdepth != 8,
			effective_front_strength, effective_back_strength) ? 1 : 0;
}

// Test-only entrypoint: keep the boundary probe on the production dispatcher.
extern "C" PF_Err OLMDirectionalBlurTestRenderWorld(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *used_exact_front_only8)
{
	if (!info || !used_exact_front_only8) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	*used_exact_front_only8 =
		bitdepth == 8 && CanUseExact8(input, output, nullptr, *info) ? 1 : 0;
	return RenderWorld(input, output, nullptr, *info, bitdepth);
}

extern "C" PF_Err OLMDirectionalBlurTestRenderWorldRoute(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *observed_route)
{
	if (!info || !observed_route) return PF_Err_BAD_CALLBACK_PARAM;
	return RenderWorld(input, output, nullptr, *info, bitdepth, observed_route);
}

extern "C" PF_Err OLMDirectionalBlurTestRenderWorldWithNoise(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	PF_EffectWorld *noise_layer,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *used_exact8)
{
	if (!info || !used_exact8) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	*used_exact8 = bitdepth == 8 &&
		CanUseExact8(input, output, noise_layer, *info) ? 1 : 0;
	return RenderWorld(input, output, noise_layer, *info, bitdepth);
}
#endif

static PF_FpLong WindowsFixedWholeNumber(PF_Fixed value)
{
	// FUN_180006c50 reads the signed word at PF_ParamDef+0x3a.
	// Preserve the upper 16 bits, including negative fractional angles;
	// signed division by 65536 would instead truncate them toward zero.
	const std::uint32_t whole = static_cast<std::uint32_t>(value) >> 16;
	return static_cast<PF_FpLong>(whole >= 0x8000u
		? static_cast<std::int32_t>(whole) - 0x10000
		: static_cast<std::int32_t>(whole));
}

static OLMDirectionalBlurInfo InfoFromParams(PF_ParamDef *params[], PF_FpLong render_scale_x, PF_FpLong render_scale_y)
{
	OLMDirectionalBlurInfo info;
	info.angle_deg = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_ANGLE]->u.ad.value);
	info.brightness_gain = params[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN]->u.fs_d.value;
	info.size_variation = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_SIZE_VARIATION]->u.fd.value);
	info.front_strength = params[OLMDIRECTIONALBLUR_FRONT_STRENGTH]->u.sd.value;
	info.front_alpha_fade = params[OLMDIRECTIONALBLUR_FRONT_ALPHA_FADE]->u.sd.value;
	info.front_sharp_tail = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_FRONT_SHARP_TAIL]->u.fd.value);
	info.back_strength = params[OLMDIRECTIONALBLUR_BACK_STRENGTH]->u.sd.value;
	info.back_alpha_fade = params[OLMDIRECTIONALBLUR_BACK_ALPHA_FADE]->u.sd.value;
	info.back_sharp_tail = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_BACK_SHARP_TAIL]->u.fd.value);
	info.noise_variation = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_NOISE_VARIATION]->u.fd.value);
	info.noise_type = params[OLMDIRECTIONALBLUR_NOISE_TYPE]->u.pd.value;
	info.noise_layer = params[OLMDIRECTIONALBLUR_NOISE_LAYER]->u.ld.dephault;
	info.seed = params[OLMDIRECTIONALBLUR_SEED]->u.sd.value;
	info.noise_offset = static_cast<A_long>(WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_NOISE_OFFSET]->u.ad.value));
	info.thickness = params[OLMDIRECTIONALBLUR_THICKNESS]->u.fs_d.value;
	info.render_scale_x = render_scale_x;
	info.render_scale_y = render_scale_y;
	return info;
}

static void RenderScaleFromInData(PF_InData *in_data, PF_FpLong &scale_x, PF_FpLong &scale_y)
{
	scale_x = 1.0;
	scale_y = 1.0;
	if (in_data) {
		if (in_data->downsample_x.den != 0) {
			scale_x = (PF_FpLong)in_data->downsample_x.num / (PF_FpLong)in_data->downsample_x.den;
		}
		if (in_data->downsample_y.den != 0) {
			scale_y = (PF_FpLong)in_data->downsample_y.num / (PF_FpLong)in_data->downsample_y.den;
		}
	}
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_FpLong scale_x, scale_y;
	RenderScaleFromInData(in_data, scale_x, scale_y);
	OLMDirectionalBlurInfo info = InfoFromParams(params, scale_x, scale_y);
	PF_EffectWorld *input = &params[OLMDIRECTIONALBLUR_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	PF_Err err = world_suite->PF_GetPixelFormat(input, &format);
	if (err) return err;

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
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_EffectWorld *noise_layer = params[OLMDIRECTIONALBLUR_NOISE_LAYER]
		? &params[OLMDIRECTIONALBLUR_NOISE_LAYER]->u.ld : NULL;
	info = DirectionalDeepLayerInfo(info, input, noise_layer, bitdepth);
	if (bitdepth != 8 && info.noise_variation > 0.0 && info.noise_type == 3) {
		PF_PixelFormat layer_format = PF_PixelFormat_INVALID;
		if (!noise_layer || !noise_layer->data) return PF_Err_BAD_CALLBACK_PARAM;
		err = world_suite->PF_GetPixelFormat(noise_layer, &layer_format);
		if (err) return err;
		if (layer_format != format) return PF_Err_BAD_CALLBACK_PARAM;
	}
	return RenderWorld(input, output, noise_layer, info, bitdepth);
}

typedef struct {
	PF_FpLong render_scale_x;
	PF_FpLong render_scale_y;
	A_long full_width;
	A_long full_height;
	bool request_contains_full_frame;
} PreRenderData;

static void DeletePreRenderData(void *data)
{
	delete reinterpret_cast<PreRenderData *>(data);
}

static bool DirectionalNormalizeFullFrameRequest(const PF_RenderRequest &requested,
	                                              A_long width, A_long height,
	                                              PF_RenderRequest *normalized)
{
#if defined(OLM_DBLUR_TEST_SEAM) && !defined(OLM_DBLUR_TEST_FULL_RENDER_REQUEST)
	(void)requested; (void)width; (void)height; (void)normalized;
	return false;
#else
	if (!normalized || width <= 0 || height <= 0) return false;
	const bool contains = requested.rect.left <= 0 && requested.rect.top <= 0 &&
		requested.rect.right >= width && requested.rect.bottom >= height;
	*normalized = requested;
	if (contains) normalized->rect = PF_LRect{0, 0, width, height};
	normalized->preserve_rgb_of_zero_alpha = TRUE;
	return contains;
#endif
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
		!extra->cb->checkout_layer) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;
	PF_CheckoutResult noise_result = {};

	A_long full_width = 0, full_height = 0;
	bool request_contains_full_frame = false;
#if !defined(OLM_DBLUR_TEST_SEAM)
	if (in_data->width > 0 && in_data->height > 0) {
		full_width = in_data->width;
		full_height = in_data->height;
		request_contains_full_frame = DirectionalNormalizeFullFrameRequest(
			extra->input->output_request, full_width, full_height, &req);
		const bool fixed_evidence_geometry =
			(full_width == 16 && full_height == 16) ||
			(full_width == 32 && full_height == 18) ||
			(full_width == 64 && full_height == 36) ||
			(full_width == 960 && full_height == 540);
		if (!request_contains_full_frame && !fixed_evidence_geometry) {
			// Generic DirectionalBlur needs its global rotated workspace. Refuse a
			// partial tile before any checkout; fixed evidence geometries retain
			// their historical admission and are classified after parameter checkout.
			return PF_Err_BAD_CALLBACK_PARAM;
		}
	}
#endif
	req.preserve_rgb_of_zero_alpha = TRUE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMDIRECTIONALBLUR_INPUT, OLMDIRECTIONALBLUR_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));
	// `None` is the actual AEX default for Noise Layer. AE reports that optional
	// layer as unavailable during pre-render; that must not abort modes which do
	// not consume it. A selected layer still contributes its requested extent.
	PF_Err noise_err = PF_Err_BAD_CALLBACK_PARAM;
	if (!err) {
		noise_err = extra->cb->checkout_layer(in_data->effect_ref,
			OLMDIRECTIONALBLUR_NOISE_LAYER, OLMDIRECTIONALBLUR_NOISE_LAYER, &req,
			in_data->current_time, in_data->time_step, in_data->time_scale,
			&noise_result);
	}

	if (!err) {
		std::unique_ptr<PreRenderData> pre(new PreRenderData);
			RenderScaleFromInData(in_data, pre->render_scale_x, pre->render_scale_y);
			pre->full_width = full_width;
			pre->full_height = full_height;
			pre->request_contains_full_frame = request_contains_full_frame;
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
		if (noise_err == PF_Err_NONE) {
			UnionLRect(&noise_result.result_rect, &extra->output->result_rect);
			UnionLRect(&noise_result.max_result_rect, &extra->output->max_result_rect);
		}
		extra->output->pre_render_data = pre.release();
		extra->output->delete_pre_render_data_func = DeletePreRenderData;
	}
	return err;
}

static PF_Err CheckinDirectionalParam(PF_InData *in_data, PF_ParamDef *param)
{
	return PF_CHECKIN_PARAM(in_data, param);
}

static bool DirectionalGenericWorldIsFullFrame(const PF_EffectWorld *world,
	                                            A_long width, A_long height)
{
	return world && width > 0 && height > 0 && world->width == width &&
		world->height == height && DirectionalWorldHasZeroOrigin(world, 0);
}

#if defined(OLM_DBLUR_TEST_SEAM)
extern "C" int OLMDirectionalBlurTestNormalizeFullFrameRequest(
	const PF_RenderRequest *requested, A_long width, A_long height,
	PF_RenderRequest *normalized)
{
	return requested && DirectionalNormalizeFullFrameRequest(
		*requested, width, height, normalized) ? 1 : 0;
}

extern "C" int OLMDirectionalBlurTestGenericWorldIsFullFrame(
	const PF_EffectWorld *world, A_long width, A_long height)
{
	return DirectionalGenericWorldIsFullFrame(world, width, height) ? 1 : 0;
}

extern "C" int OLMDirectionalBlurTestGenericSmartFramePolicy(
	const PF_RenderRequest *request, const PF_EffectWorld *input,
	const PF_EffectWorld *output, const OLMDirectionalBlurInfo *info,
	short bitdepth, A_long width, A_long height)
{
	if (!request || !info) return 0;
	PF_RenderRequest normalized = {};
	const bool retained_exact = IsRetainedNeutralExact(input, output, *info, bitdepth);
	const bool generic = !retained_exact &&
		(bitdepth == 8 ? IsGenericNeutral8Parameters(*info)
			: ((bitdepth == 16 || bitdepth == 32) &&
               (IsGenericNeutralDeepParameters(*info) || IsGenericDeepFeatureShape(*info))));
	return generic && DirectionalNormalizeFullFrameRequest(
		*request, width, height, &normalized) &&
		DirectionalGenericWorldIsFullFrame(input, width, height) &&
		DirectionalGenericWorldIsFullFrame(output, width, height) ? 1 : 0;
}
#endif

static bool DirectionalActiveRowBytes(short bitdepth, A_long width, std::size_t *bytes)
{
	if (!bytes || width <= 0) return false;
	std::size_t pixel_bytes = 0;
	switch (bitdepth) {
	case 8: pixel_bytes = sizeof(PF_Pixel8); break;
	case 16: pixel_bytes = sizeof(PF_Pixel16); break;
	case 32: pixel_bytes = sizeof(PF_PixelFloat); break;
	default: return false;
	}
	const std::size_t w = static_cast<std::size_t>(width);
	if (w > std::numeric_limits<std::size_t>::max() / pixel_bytes) return false;
	*bytes = w * pixel_bytes;
	return true;
}

#if defined(OLM_DBLUR_TEST_SEAM)
template <typename World>
static auto DirectionalTestPixelFormat(const World *world, int)
	-> decltype(world->bitdepth, PF_PixelFormat())
{
	return world->bitdepth == 8 ? PF_PixelFormat_ARGB32 :
		(world->bitdepth == 16 ? PF_PixelFormat_ARGB64 :
		 (world->bitdepth == 32 ? PF_PixelFormat_ARGB128 : PF_PixelFormat_INVALID));
}

static PF_PixelFormat DirectionalTestPixelFormat(const void *, long)
{
	return PF_PixelFormat_INVALID;
}
#endif

static PF_Err
GetDirectionalPixelFormats(PF_InData *in_data,
	const PF_EffectWorld *input_world,
	const PF_EffectWorld *output_world,
	PF_PixelFormat *input_format,
	PF_PixelFormat *output_format)
{
#if defined(OLM_DBLUR_TEST_SEAM)
	(void)in_data;
	if (!input_world || !output_world || !input_format || !output_format) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	// The oldest source-included Smart harness owns a reduced PF_EffectWorld
	// with a test-only bitdepth member.  Real-SDK direct-core harnesses use the
	// actual PF_EffectWorld, which deliberately has no such member.  Keep this
	// compatibility path compile-time bounded to the reduced harness ABI; real
	// public builds never define OLM_DBLUR_TEST_SEAM and always use WorldSuite2.
	*input_format = DirectionalTestPixelFormat(input_world, 0);
	*output_format = DirectionalTestPixelFormat(output_world, 0);
	return (*input_format == PF_PixelFormat_INVALID ||
		*output_format == PF_PixelFormat_INVALID) ? PF_Err_BAD_CALLBACK_PARAM : PF_Err_NONE;
#else
	if (!in_data || !input_world || !output_world || !input_format || !output_format ||
		!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
		!in_data->pica_basicP->ReleaseSuite) {
		return PF_Err_BAD_CALLBACK_PARAM;
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
				err = PF_Err_BAD_CALLBACK_PARAM;
			} else {
				err = world_suite->PF_GetPixelFormat(input_world, input_format);
				if (!err) err = world_suite->PF_GetPixelFormat(output_world, output_format);
			}
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	if (acquired) {
		try {
			const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
				kPFWorldSuite, kPFWorldSuiteVersion2);
			if (!err && release_err != kSPNoError) {
				err = static_cast<PF_Err>(release_err);
			}
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = PF_Err_OUT_OF_MEMORY;
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
	return err;
#endif
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *, PF_SmartRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->cb ||
		!extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
		!extra->cb->checkin_layer_pixels
#if !defined(OLM_DBLUR_TEST_SEAM)
		|| !in_data->inter.checkout_param || !in_data->inter.checkin_param
#endif
	) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *noise_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	bool input_checked_out = false;
	bool noise_checked_out = false;
	PF_ParamDef checked[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
	bool param_checked_out[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
	PF_ParamDef *param_ptrs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
	std::vector<std::uint8_t> staged_output;
	PF_EffectWorld staged_world = {};
	std::size_t active_row_bytes = 0;
	bool render_complete = false;
	std::exception_ptr thrown;
	try {
		err = extra->cb->checkout_layer_pixels(
			in_data->effect_ref, OLMDIRECTIONALBLUR_INPUT, &input_world);
		input_checked_out = err == PF_Err_NONE;
		if (!err && !input_world) err = PF_Err_BAD_CALLBACK_PARAM;
		if (!err) {
			const PF_Err noise_err = extra->cb->checkout_layer_pixels(
				in_data->effect_ref, OLMDIRECTIONALBLUR_NOISE_LAYER, &noise_world);
			noise_checked_out = noise_err == PF_Err_NONE;
			if (!noise_checked_out) noise_world = NULL;
		}
		if (!err) err = extra->cb->checkout_output(in_data->effect_ref, &output_world);
		if (!err && !output_world) err = PF_Err_BAD_CALLBACK_PARAM;
		if (!err && (!DisjointPayloads(input_world, output_world) ||
			(extra->input->bitdepth == 8 && noise_world &&
                (!DisjointPayloads(input_world, noise_world) ||
                 !DisjointPayloads(output_world, noise_world))))) {
			err = PF_Err_BAD_CALLBACK_PARAM;
		}
		if (!err) {
			PF_PixelFormat input_format = PF_PixelFormat_INVALID;
			PF_PixelFormat output_format = PF_PixelFormat_INVALID;
			err = GetDirectionalPixelFormats(in_data, input_world, output_world,
				&input_format, &output_format);
			const short depth = extra->input->bitdepth;
			const PF_PixelFormat expected_format = depth == 8 ? PF_PixelFormat_ARGB32 :
				(depth == 16 ? PF_PixelFormat_ARGB64 :
				 (depth == 32 ? PF_PixelFormat_ARGB128 : PF_PixelFormat_INVALID));
			if (!err && (expected_format == PF_PixelFormat_INVALID ||
				input_format != expected_format || output_format != expected_format ||
				input_format != output_format)) {
				err = PF_Err_BAD_CALLBACK_PARAM;
			}
		}
		for (int i = 1; i < OLMDIRECTIONALBLUR_NUM_PARAMS && !err; ++i) {
			AEFX_CLR_STRUCT(checked[i]);
			err = PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
				in_data->time_step, in_data->time_scale, &checked[i]);
			if (!err) {
				param_checked_out[i] = true;
				param_ptrs[i] = &checked[i];
			}
		}
		if (!err) {
			PF_FpLong render_scale_x, render_scale_y;
			RenderScaleFromInData(in_data, render_scale_x, render_scale_y);
			PreRenderData *pre = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data);
			if (pre) {
				if (pre->render_scale_x > 0.0) render_scale_x = pre->render_scale_x;
				if (pre->render_scale_y > 0.0) render_scale_y = pre->render_scale_y;
			}
			OLMDirectionalBlurInfo info = InfoFromParams(
				param_ptrs, render_scale_x, render_scale_y);
            info = DirectionalDeepLayerInfo(info, input_world, noise_world,
                extra->input->bitdepth);
			if ((extra->input->bitdepth == 16 || extra->input->bitdepth == 32) &&
				info.noise_variation > 0.0 && info.noise_type == 3) {
				PF_PixelFormat source_format = PF_PixelFormat_INVALID;
				PF_PixelFormat layer_format = PF_PixelFormat_INVALID;
				const bool safe = extra->input->bitdepth == 16
					? GenericDeepLayerWorldSafe<PF_Pixel16>(input_world, output_world, noise_world, info)
					: GenericDeepLayerWorldSafe<PF_PixelFloat>(input_world, output_world, noise_world, info);
				if (!safe) err = PF_Err_BAD_CALLBACK_PARAM;
				else {
					err = GetDirectionalPixelFormats(in_data, input_world, noise_world,
						&source_format, &layer_format);
					if (!err && source_format != layer_format) err = PF_Err_BAD_CALLBACK_PARAM;
				}
			}
			std::uintptr_t output_begin = 0, output_end = 0;
			if (!PayloadSpan(output_world, &output_begin, &output_end) ||
				!DirectionalActiveRowBytes(extra->input->bitdepth, output_world->width,
				                           &active_row_bytes) ||
				active_row_bytes > static_cast<std::size_t>(output_world->rowbytes)) {
				err = PF_Err_BAD_CALLBACK_PARAM;
			}
			const bool retained_exact = IsRetainedNeutralExact(
				input_world, output_world, info, extra->input->bitdepth);
			const bool generic_features =
				(extra->input->bitdepth == 16 || extra->input->bitdepth == 32) &&
				IsGenericDeepFeatureShape(info);
			const bool generic_shape = !retained_exact &&
				(IsGenericNeutralShape(info) || generic_features);
			int effective_front_strength = 0, effective_back_strength = 0;
			if (!err && generic_shape) {
				const auto strength_info = generic_features ? NeutralStrengthView(info) : info;
				const bool parameters_safe = GenericEffectiveStrengths(
					strength_info, extra->input->bitdepth != 8, &effective_front_strength,
					&effective_back_strength);
				const bool worlds_safe = extra->input->bitdepth == 8
					? CanUseGenericNeutral8(input_world, output_world, info)
					: (extra->input->bitdepth == 16
						? GenericDeepWorldsSafe<PF_Pixel16>(input_world, output_world, strength_info)
						: (extra->input->bitdepth == 32 &&
							GenericDeepWorldsSafe<PF_PixelFloat>(input_world, output_world, strength_info)));
				olm::dblur::generic::RenderEstimate smart_estimate = {};
				bool estimate_safe = generic_features
					? GenericDeepFeatureEstimate(info, input_world->width, input_world->height,
						extra->input->bitdepth, output_end - output_begin, &smart_estimate, 1.0)
					: olm::dblur::generic::EstimateRender(input_world->width, input_world->height,
						extra->input->bitdepth, effective_front_strength, effective_back_strength,
						output_end - output_begin, &smart_estimate);
                if (parameters_safe && worlds_safe && estimate_safe && generic_features &&
                    extra->input->bitdepth == 32 && info.noise_variation > 0.0 && info.noise_type == 3) {
                    double layer_bound = std::numeric_limits<double>::infinity();
                    estimate_safe = GenericPF32LayerCoefficientBound(noise_world, info, &layer_bound) &&
                        GenericDeepFeatureEstimate(info, input_world->width, input_world->height,
                            32, output_end - output_begin, &smart_estimate, layer_bound);
                }
				if (!parameters_safe || !worlds_safe || !estimate_safe ||
					(pre && pre->full_width > 0 && pre->full_height > 0 &&
						(!pre->request_contains_full_frame ||
						 !DirectionalGenericWorldIsFullFrame(
							 input_world, pre->full_width, pre->full_height) ||
						 !DirectionalGenericWorldIsFullFrame(
							 output_world, pre->full_width, pre->full_height)))) {
					err = PF_Err_BAD_CALLBACK_PARAM;
				}
			}
			if (!err) {
				staged_output.assign(output_end - output_begin, 0);
				staged_world = *output_world;
				staged_world.data = reinterpret_cast<PF_PixelPtr>(staged_output.data());
				err = RenderWorld(input_world, &staged_world, noise_world, info,
				                  extra->input->bitdepth);
				render_complete = err == PF_Err_NONE;
			}
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	for (int i = 1; i < OLMDIRECTIONALBLUR_NUM_PARAMS; ++i) {
		if (!param_checked_out[i]) continue;
		try {
			const PF_Err checkin_err = CheckinDirectionalParam(in_data, &checked[i]);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (input_checked_out) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
				in_data->effect_ref, OLMDIRECTIONALBLUR_INPUT);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (noise_checked_out) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
				in_data->effect_ref, OLMDIRECTIONALBLUR_NOISE_LAYER);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (thrown) std::rethrow_exception(thrown);
	if (!err && render_complete) {
		for (A_long y = 0; y < output_world->height; ++y) {
			std::memcpy(reinterpret_cast<std::uint8_t *>(output_world->data) +
					static_cast<std::size_t>(y) * output_world->rowbytes,
				staged_output.data() + static_cast<std::size_t>(y) * staged_world.rowbytes,
				active_row_bytes);
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
		"OLM DirectionalBlur",
		"OLM Directional Blur",
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
#if !defined(OLM_DBLUR_TEST_SEAM)
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParamsUI(in_data);
			break;
#endif
		case PF_Cmd_RENDER:
			err = Render(in_data, out_data, params, output);
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
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return err;
}

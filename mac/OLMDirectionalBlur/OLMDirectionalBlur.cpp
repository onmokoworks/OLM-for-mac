#include "OLMDirectionalBlur.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

static constexpr PF_FpLong kPi = 3.141592653589793238462643383279502884;

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
GlobalSetup(PF_InData *, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
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
	PF_Err err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Angle_Param_Name),
	                     -360.0, 360.0, -360.0, 360.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     ANGLE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BrightnessGain_Param_Name),
	                     0.0, 10.0, 0.0, 10.0, 1.0,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     BRIGHTNESS_GAIN_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_SizeVariation_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     SIZE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_FrontStrength_Param_Name),
	              0, 3000, 0, 3000, 0,
	              FRONT_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_FrontAlphaFade_Param_Name),
	              0, 3000, 0, 3000, 0,
	              FRONT_ALPHA_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_FrontSharpTail_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     FRONT_SHARP_TAIL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_BackStrength_Param_Name),
	              0, 3000, 0, 3000, 0,
	              BACK_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_BackAlphaFade_Param_Name),
	              0, 3000, 0, 3000, 0,
	              BACK_ALPHA_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BackSharpTail_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     BACK_SHARP_TAIL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_NoiseVariation_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     NOISE_VARIATION_DISK_ID);

	out_data->num_params = OLMDIRECTIONALBLUR_NUM_PARAMS;
	return err;
}

template <typename PixelT>
static PixelT *PixelAt(PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<PixelT *>(reinterpret_cast<char *>(world->data) + y * world->rowbytes) + x;
}

template <typename PixelT>
static const PixelT *PixelAtConst(const PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<const PixelT *>(reinterpret_cast<const char *>(world->data) + y * world->rowbytes) + x;
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
	const float denom = 2.0f * ((float)length / 0.5f) * ((float)length / 0.5f) + 1.0e-5f;
	for (A_long i = 0; i < length; ++i) {
		weights[(size_t)i] = std::exp(-((float)(i * i)) / denom);
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

	const double scale = info.frame_rate > 0.0 ? 1.0 / info.frame_rate : 1.0;
	const A_long strength = std::max<A_long>(0, (A_long)((double)info.front_strength * scale));
	if (strength <= 1) {
		CopyWorld<PF_Pixel8>(input, output);
		return PF_Err_NONE;
	}

	const std::vector<float> weights = DirectionalGaussianWeights(strength);
	const double angle = -info.angle_deg * kPi / 180.0;
	const float vx = (float)std::cos(angle);
	const float vy = (float)std::sin(angle);
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

static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
                          const OLMDirectionalBlurInfo &info, short bitdepth)
{
	if (bitdepth == 8) return RenderDirectional8(input, output, info);
	if (bitdepth == 16) {
		CopyWorld<PF_Pixel16>(input, output);
		return PF_Err_NONE;
	}
	if (bitdepth == 32) {
		CopyWorld<PF_PixelFloat>(input, output);
		return PF_Err_NONE;
	}
	return PF_Err_BAD_CALLBACK_PARAM;
}

static OLMDirectionalBlurInfo InfoFromParams(PF_ParamDef *params[], PF_FpLong frame_rate)
{
	OLMDirectionalBlurInfo info;
	info.angle_deg = params[OLMDIRECTIONALBLUR_ANGLE]->u.fs_d.value;
	info.brightness_gain = params[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN]->u.fs_d.value;
	info.size_variation = params[OLMDIRECTIONALBLUR_SIZE_VARIATION]->u.fs_d.value;
	info.front_strength = params[OLMDIRECTIONALBLUR_FRONT_STRENGTH]->u.sd.value;
	info.front_alpha_fade = params[OLMDIRECTIONALBLUR_FRONT_ALPHA_FADE]->u.sd.value;
	info.front_sharp_tail = params[OLMDIRECTIONALBLUR_FRONT_SHARP_TAIL]->u.fs_d.value;
	info.back_strength = params[OLMDIRECTIONALBLUR_BACK_STRENGTH]->u.sd.value;
	info.back_alpha_fade = params[OLMDIRECTIONALBLUR_BACK_ALPHA_FADE]->u.sd.value;
	info.back_sharp_tail = params[OLMDIRECTIONALBLUR_BACK_SHARP_TAIL]->u.fs_d.value;
	info.noise_variation = params[OLMDIRECTIONALBLUR_NOISE_VARIATION]->u.fs_d.value;
	info.frame_rate = frame_rate;
	return info;
}

static PF_FpLong FrameRateFromInData(PF_InData *in_data)
{
	if (in_data && in_data->time_step != 0) {
		return (PF_FpLong)in_data->time_scale / (PF_FpLong)in_data->time_step;
	}
	return 24.0;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *, PF_ParamDef *params[], PF_LayerDef *output)
{
	OLMDirectionalBlurInfo info = InfoFromParams(params, FrameRateFromInData(in_data));
	short bitdepth = PF_WORLD_IS_DEEP(output) ? 16 : 8;
	return RenderWorld(&params[OLMDIRECTIONALBLUR_INPUT]->u.ld, output, info, bitdepth);
}

typedef struct {
	PF_FpLong frame_rate;
} PreRenderData;

static void DeletePreRenderData(void *data)
{
	delete reinterpret_cast<PreRenderData *>(data);
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	req.preserve_rgb_of_zero_alpha = TRUE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMDIRECTIONALBLUR_INPUT, OLMDIRECTIONALBLUR_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
		PreRenderData *pre = new PreRenderData;
		pre->frame_rate = FrameRateFromInData(in_data);
		extra->output->pre_render_data = pre;
		extra->output->delete_pre_render_data_func = DeletePreRenderData;
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *, PF_SmartRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, OLMDIRECTIONALBLUR_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (err || !input_world || !output_world) {
		extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMDIRECTIONALBLUR_INPUT);
		return err;
	}

	PF_ParamDef checked[OLMDIRECTIONALBLUR_NUM_PARAMS];
	PF_ParamDef *param_ptrs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
	for (int i = 1; i < OLMDIRECTIONALBLUR_NUM_PARAMS; ++i) {
		AEFX_CLR_STRUCT(checked[i]);
		ERR(PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
		                      in_data->time_step, in_data->time_scale, &checked[i]));
		param_ptrs[i] = &checked[i];
	}
	param_ptrs[OLMDIRECTIONALBLUR_INPUT] = NULL;

	PF_FpLong frame_rate = FrameRateFromInData(in_data);
	if (PreRenderData *pre = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data)) {
		if (pre->frame_rate > 0.0) frame_rate = pre->frame_rate;
	}

	if (!err) {
		OLMDirectionalBlurInfo info = InfoFromParams(param_ptrs, frame_rate);
		ERR(RenderWorld(input_world, output_world, info, extra->input->bitdepth));
	}

	for (int i = 1; i < OLMDIRECTIONALBLUR_NUM_PARAMS; ++i) {
		PF_CHECKIN_PARAM(in_data, &checked[i]);
	}
	extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMDIRECTIONALBLUR_INPUT);
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
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return err;
}

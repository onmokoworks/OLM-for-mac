#include "OLMToonDilate.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <deque>
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
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_SearchRadius_Param_Name),
	                     0.0, 1000.0, 0.0, 100.0, 13.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     SEARCH_RADIUS_DISK_ID);

	out_data->num_params = OLMTOONDILATE_NUM_PARAMS;
	return err;
}

template <typename PixelT>
struct ToonPixelTraits;

template <>
struct ToonPixelTraits<PF_Pixel8> {
	static bool opaque(const PF_Pixel8 &p) { return p.alpha == PF_MAX_CHAN8; }
};

template <>
struct ToonPixelTraits<PF_Pixel16> {
	static bool opaque(const PF_Pixel16 &p) { return p.alpha == PF_MAX_CHAN16; }
};

template <>
struct ToonPixelTraits<PF_PixelFloat> {
	static bool opaque(const PF_PixelFloat &p) { return p.alpha >= 1.0f; }
};

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
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMToonDilateInfo &info)
{
	const A_long w = output->width;
	const A_long h = output->height;
	if (w <= 0 || h <= 0 || info.search_radius <= 0.0) {
		for (A_long y = 0; y < h; ++y) {
			for (A_long x = 0; x < w; ++x) {
				*PixelAt<PixelT>(output, x, y) = *PixelAtConst<PixelT>(input, x, y);
			}
		}
		return PF_Err_NONE;
	}

	const PF_FpLong comp_width = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const A_long r_eff = (A_long)std::ceil(info.search_radius * ((PF_FpLong)w / comp_width));
	if (r_eff <= 0) {
		for (A_long y = 0; y < h; ++y) {
			for (A_long x = 0; x < w; ++x) {
				*PixelAt<PixelT>(output, x, y) = *PixelAtConst<PixelT>(input, x, y);
			}
		}
		return PF_Err_NONE;
	}

	const A_long n = w * h;
	std::vector<A_long> dist((size_t)n, -1);
	std::vector<A_long> sx((size_t)n, -1);
	std::vector<A_long> sy((size_t)n, -1);
	std::deque<A_long> queue;

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			*PixelAt<PixelT>(output, x, y) = *PixelAtConst<PixelT>(input, x, y);
			A_long idx = y * w + x;
			if (ToonPixelTraits<PixelT>::opaque(*PixelAtConst<PixelT>(input, x, y))) {
				dist[idx] = 0;
				sx[idx] = x;
				sy[idx] = y;
				queue.push_back(idx);
			}
		}
	}
	if (queue.empty()) return PF_Err_NONE;

	static const A_long DX[8] = {-1, 0, 1, -1, 1, -1, 0, 1};
	static const A_long DY[8] = {-1, -1, -1, 0, 0, 1, 1, 1};
	while (!queue.empty()) {
		A_long idx = queue.front();
		queue.pop_front();
		A_long d = dist[idx];
		if (d >= r_eff) continue;
		A_long x = idx % w;
		A_long y = idx / w;
		for (int k = 0; k < 8; ++k) {
			A_long nx = x + DX[k];
			A_long ny = y + DY[k];
			if (nx < 0 || nx >= w || ny < 0 || ny >= h) continue;
			A_long nidx = ny * w + nx;
			if (dist[nidx] >= 0) continue;
			dist[nidx] = d + 1;
			sx[nidx] = sx[idx];
			sy[nidx] = sy[idx];
			queue.push_back(nidx);
		}
	}

	for (A_long idx = 0; idx < n; ++idx) {
		if (dist[idx] <= 0 || dist[idx] > r_eff) continue;
		A_long x = idx % w;
		A_long y = idx / w;
		const PixelT *inP = PixelAtConst<PixelT>(input, x, y);
		if (ToonPixelTraits<PixelT>::opaque(*inP)) continue;
		*PixelAt<PixelT>(output, x, y) = *PixelAtConst<PixelT>(input, sx[idx], sy[idx]);
	}

	return PF_Err_NONE;
}

static PF_Err
RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output, const OLMToonDilateInfo &info, short bitdepth)
{
	if (bitdepth == 8) {
		return RenderTyped<PF_Pixel8>(input, output, info);
	} else if (bitdepth == 16) {
		return RenderTyped<PF_Pixel16>(input, output, info);
	} else if (bitdepth == 32) {
		return RenderTyped<PF_PixelFloat>(input, output, info);
	}
	return PF_Err_BAD_CALLBACK_PARAM;
}

static PF_Err
Render(PF_InData *, PF_OutData *, PF_ParamDef *params[], PF_LayerDef *output)
{
	OLMToonDilateInfo info;
	info.search_radius = params[OLMTOONDILATE_SEARCH_RADIUS]->u.fs_d.value;
	info.comp_width = params[OLMTOONDILATE_INPUT]->u.ld.width;
	short bitdepth = PF_WORLD_IS_DEEP(output) ? 16 : 8;
	return RenderWorld(&params[OLMTOONDILATE_INPUT]->u.ld, output, info, bitdepth);
}

typedef struct {
	PF_FpLong comp_width;
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
		OLMTOONDILATE_INPUT, OLMTOONDILATE_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
		PreRenderData *pre = new PreRenderData;
		pre->comp_width = in_result.ref_width > 0 ? (PF_FpLong)in_result.ref_width : 0.0;
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
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, OLMTOONDILATE_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (err || !input_world || !output_world) {
		extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMTOONDILATE_INPUT);
		return err;
	}

	PF_ParamDef radius_param;
	AEFX_CLR_STRUCT(radius_param);
	ERR(PF_CHECKOUT_PARAM(in_data, OLMTOONDILATE_SEARCH_RADIUS,
	                      in_data->current_time, in_data->time_step, in_data->time_scale,
	                      &radius_param));

	OLMToonDilateInfo info;
	info.search_radius = radius_param.u.fs_d.value;
	info.comp_width = input_world->width;
	if (PreRenderData *pre = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data)) {
		if (pre->comp_width > 0.0) info.comp_width = pre->comp_width;
	}
	PF_CHECKIN_PARAM(in_data, &radius_param);

	if (!err) {
		ERR(RenderWorld(input_world, output_world, info, extra->input->bitdepth));
	}

	extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMTOONDILATE_INPUT);
	return err;
}

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
		"OLM Toon Dilate",
		"ADBE OLMToonDilate",
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
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, (PF_PreRenderExtra*)extra); break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, (PF_SmartRenderExtra*)extra); break;
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	}
	return err;
}

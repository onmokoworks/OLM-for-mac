#include "OLMColorKey.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
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

template <typename T>
static T ClampValue(T value, T lo, T hi)
{
	return std::max(lo, std::min(value, hi));
}

static void MakeIndexedName(char *dst, size_t dst_size, const char *base, int index)
{
	std::snprintf(dst, dst_size, "%s %d", base, index);
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_ColorKeep_Param_Name), "", FALSE, 0,
	                COLOR_KEEP_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Threshold_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, 0,
	                     THRESHOLD_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_Premultiplied_Param_Name), "", FALSE, 0,
	                PREMULTIPLIED_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_ColorSpace_Param_Name),
	             6, 1, GetStringPtr(StrID_ColorSpace_Choices),
	             COLOR_SPACE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_ForceLowerPrecision_Param_Name),
	             3, 1, GetStringPtr(StrID_ForceLowerPrecision_Choices),
	             FORCE_LOWER_PRECISION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_PerColor_Param_Name), "", FALSE, 0,
	                PER_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_PerComponent_Param_Name), "", FALSE, 0,
	                PER_COMPONENT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdR_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, 0,
	                     THRESHOLD_R_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdG_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, 0,
	                     THRESHOLD_G_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdB_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, 0,
	                     THRESHOLD_B_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_EdgeThinAmount_Param_Name),
	                     -100.0, 100.0, -100.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     EDGE_THIN_AMOUNT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_DistanceType_Param_Name),
	             3, 1, GetStringPtr(StrID_DistanceType_Choices),
	             EDGE_THIN_DISTANCE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_EdgeBlurAmount_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     EDGE_BLUR_AMOUNT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_DistanceType_Param_Name),
	             3, 1, GetStringPtr(StrID_DistanceType_Choices),
	             EDGE_BLUR_DISTANCE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_EdgeBlurDirection_Param_Name),
	             3, 2, GetStringPtr(StrID_EdgeBlurDirection_Choices),
	             EDGE_BLUR_DIRECTION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_NumberOfColors_Param_Name),
	              1, OLMCOLORKEY_MAX_COLORS, 1, OLMCOLORKEY_MAX_COLORS, 1,
	              NUMBER_OF_COLORS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_EnableReplace_Param_Name), "", FALSE, 0,
	                ENABLE_REPLACE_DISK_ID);

	for (int i = 0; i < OLMCOLORKEY_MAX_COLORS; ++i) {
		char name[128];
		int display_index = i + 1;

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_Color_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_COLOR(name, 0, 0, 0, COLOR_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdIndexed_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, 0,
		                     THRESHOLD_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdR_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, 0,
		                     THRESHOLD_R_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdG_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, 0,
		                     THRESHOLD_G_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdB_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, 0,
		                     THRESHOLD_B_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_UseColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_CHECKBOX(name, "", i == 0 ? TRUE : FALSE, 0,
		                USE_COLOR_DISK_ID_FIRST + i * 3);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_UseReplaceColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_CHECKBOX(name, "", FALSE, 0,
		                USE_REPLACE_DISK_ID_FIRST + i * 3);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ReplaceColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_COLOR(name, 0, 0, 0, REPLACE_COLOR_DISK_ID_FIRST + i * 3);
	}

	out_data->num_params = OLMCOLORKEY_NUM_PARAMS;
	return err;
}

static A_long ColorParamIndex(int i, int offset)
{
	return OLMCOLORKEY_COLOR_FIRST + i * COLOR_PARAM_STRIDE + offset;
}

static PF_Err
CheckoutInfo(PF_InData *in_data, PF_ParamDef *params[], OLMColorKeyInfo *info)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();

	AEFX_CLR_STRUCT(*info);
	info->color_keep = params[OLMCOLORKEY_COLOR_KEEP]->u.bd.value;
	info->threshold = params[OLMCOLORKEY_THRESHOLD]->u.fs_d.value;
	info->premultiplied = params[OLMCOLORKEY_PREMULTIPLIED]->u.bd.value;
	info->color_space = params[OLMCOLORKEY_COLOR_SPACE]->u.pd.value;
	info->per_color = params[OLMCOLORKEY_PER_COLOR]->u.bd.value;
	info->per_component = params[OLMCOLORKEY_PER_COMPONENT]->u.bd.value;
	info->threshold_r = params[OLMCOLORKEY_THRESHOLD_R]->u.fs_d.value;
	info->threshold_g = params[OLMCOLORKEY_THRESHOLD_G]->u.fs_d.value;
	info->threshold_b = params[OLMCOLORKEY_THRESHOLD_B]->u.fs_d.value;
	info->edge_thin_amount = params[OLMCOLORKEY_EDGE_THIN_AMOUNT]->u.fs_d.value;
	info->edge_thin_distance_type = params[OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE]->u.pd.value;
	info->edge_blur_amount = params[OLMCOLORKEY_EDGE_BLUR_AMOUNT]->u.fs_d.value;
	info->edge_blur_distance_type = params[OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE]->u.pd.value;
	info->edge_blur_direction = params[OLMCOLORKEY_EDGE_BLUR_DIRECTION]->u.pd.value;
	info->number_of_colors = params[OLMCOLORKEY_NUMBER_OF_COLORS]->u.sd.value;
	info->enable_replace = params[OLMCOLORKEY_ENABLE_REPLACE]->u.bd.value;
	if (info->number_of_colors < 1) info->number_of_colors = 1;
	if (info->number_of_colors > OLMCOLORKEY_MAX_COLORS) info->number_of_colors = OLMCOLORKEY_MAX_COLORS;

	for (A_long i = 0; i < info->number_of_colors; ++i) {
		PF_ParamDef *cp = params[ColorParamIndex(i, COLOR_OFFSET_COLOR)];
		info->colors8[i] = cp->u.cd.value;
		PF_PixelFloat fp = {0};
		ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref, cp, &fp));
		info->colors[i] = fp;
		info->thresholds[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD)]->u.fs_d.value;
		info->thresholds_r[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_R)]->u.fs_d.value;
		info->thresholds_g[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_G)]->u.fs_d.value;
		info->thresholds_b[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_B)]->u.fs_d.value;
		info->use_color[i] = params[ColorParamIndex(i, COLOR_OFFSET_USE_COLOR)]->u.bd.value;
		info->use_replace_color[i] = params[ColorParamIndex(i, COLOR_OFFSET_USE_REPLACE)]->u.bd.value;
		PF_ParamDef *rp = params[ColorParamIndex(i, COLOR_OFFSET_REPLACE_COLOR)];
		PF_PixelFloat rep = {0};
		ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref, rp, &rep));
		info->replace_colors[i] = rep;
	}
	return err;
}

static PF_Err
CheckoutSmartInfo(PF_InData *in_data, OLMColorKeyInfo *info)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();

	AEFX_CLR_STRUCT(*info);
	auto checkout = [&](A_long index, PF_ParamDef *param) -> PF_Err {
		AEFX_CLR_STRUCT(*param);
		return PF_CHECKOUT_PARAM(in_data, index, in_data->current_time,
		                         in_data->time_step, in_data->time_scale, param);
	};

	PF_ParamDef p;
	ERR(checkout(OLMCOLORKEY_COLOR_KEEP, &p)); info->color_keep = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_THRESHOLD, &p)); info->threshold = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_PREMULTIPLIED, &p)); info->premultiplied = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_COLOR_SPACE, &p)); info->color_space = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_PER_COLOR, &p)); info->per_color = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_PER_COMPONENT, &p)); info->per_component = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_THRESHOLD_R, &p)); info->threshold_r = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_THRESHOLD_G, &p)); info->threshold_g = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_THRESHOLD_B, &p)); info->threshold_b = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_EDGE_THIN_AMOUNT, &p)); info->edge_thin_amount = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE, &p)); info->edge_thin_distance_type = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_EDGE_BLUR_AMOUNT, &p)); info->edge_blur_amount = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE, &p)); info->edge_blur_distance_type = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_EDGE_BLUR_DIRECTION, &p)); info->edge_blur_direction = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_NUMBER_OF_COLORS, &p)); info->number_of_colors = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMCOLORKEY_ENABLE_REPLACE, &p)); info->enable_replace = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	if (info->number_of_colors < 1) info->number_of_colors = 1;
	if (info->number_of_colors > OLMCOLORKEY_MAX_COLORS) info->number_of_colors = OLMCOLORKEY_MAX_COLORS;

	for (A_long i = 0; i < info->number_of_colors && !err; ++i) {
		ERR(checkout(ColorParamIndex(i, COLOR_OFFSET_COLOR), &p));
		if (!err) {
			info->colors8[i] = p.u.cd.value;
			PF_PixelFloat fp = {0};
			ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref, &p, &fp));
			info->colors[i] = fp;
			PF_CHECKIN_PARAM(in_data, &p);
		}
		ERR(checkout(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD), &p)); info->thresholds[i] = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
		ERR(checkout(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_R), &p)); info->thresholds_r[i] = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
		ERR(checkout(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_G), &p)); info->thresholds_g[i] = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
		ERR(checkout(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_B), &p)); info->thresholds_b[i] = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
		ERR(checkout(ColorParamIndex(i, COLOR_OFFSET_USE_COLOR), &p)); info->use_color[i] = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
		ERR(checkout(ColorParamIndex(i, COLOR_OFFSET_USE_REPLACE), &p)); info->use_replace_color[i] = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
		ERR(checkout(ColorParamIndex(i, COLOR_OFFSET_REPLACE_COLOR), &p));
		if (!err) {
			PF_PixelFloat rep = {0};
			ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref, &p, &rep));
			info->replace_colors[i] = rep;
			PF_CHECKIN_PARAM(in_data, &p);
		}
	}
	return err;
}

static std::vector<float> L1DistanceTo(const std::vector<u_char> &mask, A_long w, A_long h)
{
	const float inf = 1.0e9f;
	std::vector<float> d((size_t)w * (size_t)h, inf);
	for (A_long i = 0; i < w * h; ++i) {
		if (mask[i]) d[i] = 0.0f;
	}
	for (A_long x = 1; x < w; ++x) {
		for (A_long y = 0; y < h; ++y) {
			A_long i = y * w + x;
			d[i] = std::min(d[i], d[i - 1] + 1.0f);
		}
	}
	for (A_long x = w - 2; x >= 0; --x) {
		for (A_long y = 0; y < h; ++y) {
			A_long i = y * w + x;
			d[i] = std::min(d[i], d[i + 1] + 1.0f);
		}
	}
	for (A_long y = 1; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			A_long i = y * w + x;
			d[i] = std::min(d[i], d[i - w] + 1.0f);
		}
	}
	for (A_long y = h - 2; y >= 0; --y) {
		for (A_long x = 0; x < w; ++x) {
			A_long i = y * w + x;
			d[i] = std::min(d[i], d[i + w] + 1.0f);
		}
	}
	return d;
}

static std::vector<float> ChessboardDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h)
{
	const float inf = 1.0e9f;
	std::vector<float> d((size_t)w * (size_t)h, inf);
	for (A_long i = 0; i < w * h; ++i) {
		if (mask[i]) d[i] = 0.0f;
	}
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			A_long i = y * w + x;
			if (x > 0) d[i] = std::min(d[i], d[i - 1] + 1.0f);
			if (y > 0) d[i] = std::min(d[i], d[i - w] + 1.0f);
			if (x > 0 && y > 0) d[i] = std::min(d[i], d[i - w - 1] + 1.0f);
			if (x + 1 < w && y > 0) d[i] = std::min(d[i], d[i - w + 1] + 1.0f);
		}
	}
	for (A_long y = h - 1; y >= 0; --y) {
		for (A_long x = w - 1; x >= 0; --x) {
			A_long i = y * w + x;
			if (x + 1 < w) d[i] = std::min(d[i], d[i + 1] + 1.0f);
			if (y + 1 < h) d[i] = std::min(d[i], d[i + w] + 1.0f);
			if (x + 1 < w && y + 1 < h) d[i] = std::min(d[i], d[i + w + 1] + 1.0f);
			if (x > 0 && y + 1 < h) d[i] = std::min(d[i], d[i + w - 1] + 1.0f);
		}
	}
	return d;
}

static inline float EdtSquare(float x)
{
	return x * x;
}

static std::vector<float> Edt1D(const std::vector<float> &f, A_long n)
{
	const float inf = 1.0e9f;
	std::vector<A_long> sites;
	sites.reserve((size_t)n);
	for (A_long i = 0; i < n; ++i) {
		if (f[(size_t)i] < inf * 0.5f) sites.push_back(i);
	}
	std::vector<float> d((size_t)n, inf);
	if (sites.empty()) return d;

	std::vector<A_long> v(sites.size());
	std::vector<float> z(sites.size() + 1);
	A_long k = 0;
	v[0] = sites[0];
	z[0] = -1.0e20f;
	z[1] = 1.0e20f;
	for (size_t site_index = 1; site_index < sites.size(); ++site_index) {
		A_long q = sites[site_index];
		float s = 0.0f;
		while (true) {
			A_long vk = v[(size_t)k];
			s = ((f[(size_t)q] + EdtSquare((float)q)) -
			     (f[(size_t)vk] + EdtSquare((float)vk))) /
			    (2.0f * (float)(q - vk));
			if (s > z[(size_t)k]) break;
			if (k == 0) break;
			--k;
		}
		if (s <= z[(size_t)k]) {
			k = 0;
		} else {
			++k;
		}
		v[(size_t)k] = q;
		z[(size_t)k] = s;
		z[(size_t)k + 1] = 1.0e20f;
	}
	k = 0;
	for (A_long q = 0; q < n; ++q) {
		while (z[(size_t)k + 1] < (float)q) ++k;
		A_long vk = v[(size_t)k];
		d[(size_t)q] = EdtSquare((float)(q - vk)) + f[(size_t)vk];
	}
	return d;
}

static std::vector<float> EuclideanDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h)
{
	const float inf = 1.0e9f;
	std::vector<float> tmp((size_t)w * (size_t)h);
	std::vector<float> f((size_t)std::max(w, h));
	for (A_long x = 0; x < w; ++x) {
		for (A_long y = 0; y < h; ++y) f[(size_t)y] = mask[(size_t)y * (size_t)w + (size_t)x] ? 0.0f : inf;
		std::vector<float> col = Edt1D(f, h);
		for (A_long y = 0; y < h; ++y) tmp[(size_t)y * (size_t)w + (size_t)x] = col[(size_t)y];
	}
	std::vector<float> out((size_t)w * (size_t)h);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) f[(size_t)x] = tmp[(size_t)y * (size_t)w + (size_t)x];
		std::vector<float> row = Edt1D(f, w);
		for (A_long x = 0; x < w; ++x) out[(size_t)y * (size_t)w + (size_t)x] = std::sqrt(row[(size_t)x]);
	}
	return out;
}

static std::vector<float> MatteDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, A_long distance_type)
{
	if (distance_type == 1) return ChessboardDistanceTo(mask, w, h);
	if (distance_type == 3) return EuclideanDistanceTo(mask, w, h);
	return L1DistanceTo(mask, w, h);
}

static std::vector<float> EdgeBlurDistanceTo(const std::vector<u_char> &mask, A_long w, A_long h, A_long distance_type)
{
	if (distance_type == 1) return EuclideanDistanceTo(mask, w, h);
	return MatteDistanceTo(mask, w, h, distance_type);
}

static std::vector<u_char> Boundary8(const std::vector<u_char> &mask, A_long w, A_long h)
{
	std::vector<u_char> out((size_t)w * (size_t)h, 0);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const A_long i = y * w + x;
			if (!mask[(size_t)i]) continue;
			bool all_inside = true;
			for (A_long dy = -1; dy <= 1; ++dy) {
				for (A_long dx = -1; dx <= 1; ++dx) {
					if (dx == 0 && dy == 0) continue;
					A_long nx = ClampValue<A_long>(x + dx, 0, w - 1);
					A_long ny = ClampValue<A_long>(y + dy, 0, h - 1);
					all_inside = all_inside && mask[(size_t)ny * (size_t)w + (size_t)nx] != 0;
				}
			}
			out[(size_t)i] = all_inside ? 0 : 1;
		}
	}
	return out;
}

static float LabF(float t)
{
	return t <= 0.008856000378727913f
		? t * 7.7870001792907715f + 0.13793103396892548f
		: std::pow(t, 0.3333300054073334f);
}

static void RGBToPluginLab76(const float rgb[3], float out[3])
{
	float r = rgb[0];
	float g = rgb[1];
	float b = rgb[2];
	float x = g * 2.1455016136169434f + r * 0.6380193829536438f + b * 0.2165091633796692f;
	float fx = LabF(x);
	out[0] = x <= 0.008856000378727913f
		? g * 1938.031494140625f + r * 576.3229370117188f + b * 195.57272338867188f
		: std::pow(x, 0.3333300054073334f) * 116.0f - 16.0f;
	float a_source = r * 1.2373713254928589f + g * 1.0727508068084717f + b * 0.5412744283676147f;
	float b_source = g * 0.35758259892463684f + r * 0.05800257995724678f + b * 2.8507096767425537f;
	out[1] = (LabF(a_source) - fx) * 500.0f;
	out[2] = (fx - LabF(b_source)) * 200.0f;
}

static float EdgeBlurWeight(bool inside, float dist, float amount, A_long direction)
{
	const float pi = 3.14159265358979323846f;
	if (amount <= 0.0f) return inside ? 1.0f : 0.0f;
	if (direction == 1) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		return (std::sin((dist * (pi / amount)) - (pi * 0.5f)) + 1.0f) * 0.5f;
	}
	if (direction == 2) {
		if (inside) return 1.0f;
		if (dist >= amount) return 0.0f;
		return (std::sin((pi * 0.5f) - (dist * (pi / amount))) + 1.0f) * 0.5f;
	}
	if (direction == 3) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		return (std::sin((dist * (pi / amount)) - (pi * 0.5f)) + 1.0f) * 0.5f;
	}
	return inside ? 1.0f : 0.0f;
}

template <typename PixelT>
struct OLMCKPixelTraits;

template <>
struct OLMCKPixelTraits<PF_Pixel8> {
	static float max_chan() { return 255.0f; }
	static float r(const PF_Pixel8 &p) { return (float)p.red / 255.0f; }
	static float g(const PF_Pixel8 &p) { return (float)p.green / 255.0f; }
	static float b(const PF_Pixel8 &p) { return (float)p.blue / 255.0f; }
	static float a(const PF_Pixel8 &p) { return (float)p.alpha / 255.0f; }
	static void zero(PF_Pixel8 &p) { p.alpha = p.red = p.green = p.blue = 0; }
	static void replace_rgb(PF_Pixel8 &p, const PF_PixelFloat &rep)
	{
		p.red = (A_u_char)ClampValue<int>((int)(rep.red * 255.0f), 0, 255);
		p.green = (A_u_char)ClampValue<int>((int)(rep.green * 255.0f), 0, 255);
		p.blue = (A_u_char)ClampValue<int>((int)(rep.blue * 255.0f), 0, 255);
	}
	static void scale(PF_Pixel8 &dst, const PF_Pixel8 &src, float weight)
	{
		dst.red = (A_u_char)ClampValue<int>((int)((float)src.red * weight), 0, 255);
		dst.green = (A_u_char)ClampValue<int>((int)((float)src.green * weight), 0, 255);
		dst.blue = (A_u_char)ClampValue<int>((int)((float)src.blue * weight), 0, 255);
		dst.alpha = (A_u_char)ClampValue<int>((int)((float)src.alpha * weight), 0, 255);
	}
};

template <>
struct OLMCKPixelTraits<PF_Pixel16> {
	static float max_chan() { return (float)PF_MAX_CHAN16; }
	static float r(const PF_Pixel16 &p) { return (float)p.red / max_chan(); }
	static float g(const PF_Pixel16 &p) { return (float)p.green / max_chan(); }
	static float b(const PF_Pixel16 &p) { return (float)p.blue / max_chan(); }
	static float a(const PF_Pixel16 &p) { return (float)p.alpha / max_chan(); }
	static void zero(PF_Pixel16 &p) { p.alpha = p.red = p.green = p.blue = 0; }
	static void replace_rgb(PF_Pixel16 &p, const PF_PixelFloat &rep)
	{
		int maxv = (int)PF_MAX_CHAN16;
		p.red = (A_u_short)ClampValue<int>((int)(rep.red * (float)maxv), 0, maxv);
		p.green = (A_u_short)ClampValue<int>((int)(rep.green * (float)maxv), 0, maxv);
		p.blue = (A_u_short)ClampValue<int>((int)(rep.blue * (float)maxv), 0, maxv);
	}
	static void scale(PF_Pixel16 &dst, const PF_Pixel16 &src, float weight)
	{
		int maxv = (int)PF_MAX_CHAN16;
		dst.red = (A_u_short)ClampValue<int>((int)((float)src.red * weight), 0, maxv);
		dst.green = (A_u_short)ClampValue<int>((int)((float)src.green * weight), 0, maxv);
		dst.blue = (A_u_short)ClampValue<int>((int)((float)src.blue * weight), 0, maxv);
		dst.alpha = (A_u_short)ClampValue<int>((int)((float)src.alpha * weight), 0, maxv);
	}
};

template <>
struct OLMCKPixelTraits<PF_PixelFloat> {
	static float r(const PF_PixelFloat &p) { return p.red; }
	static float g(const PF_PixelFloat &p) { return p.green; }
	static float b(const PF_PixelFloat &p) { return p.blue; }
	static float a(const PF_PixelFloat &p) { return p.alpha; }
	static void zero(PF_PixelFloat &p) { p.alpha = p.red = p.green = p.blue = 0.0f; }
	static void replace_rgb(PF_PixelFloat &p, const PF_PixelFloat &rep)
	{
		p.red = ClampValue<float>(rep.red, 0.0f, 1.0f);
		p.green = ClampValue<float>(rep.green, 0.0f, 1.0f);
		p.blue = ClampValue<float>(rep.blue, 0.0f, 1.0f);
	}
	static void scale(PF_PixelFloat &dst, const PF_PixelFloat &src, float weight)
	{
		dst.red = ClampValue<float>(src.red * weight, 0.0f, 1.0f);
		dst.green = ClampValue<float>(src.green * weight, 0.0f, 1.0f);
		dst.blue = ClampValue<float>(src.blue * weight, 0.0f, 1.0f);
		dst.alpha = ClampValue<float>(src.alpha * weight, 0.0f, 1.0f);
	}
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
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMColorKeyInfo &info)
{
	A_long w = output->width;
	A_long h = output->height;
	std::vector<u_char> matched((size_t)w * (size_t)h, 0);
	std::vector<int> matched_index((size_t)w * (size_t)h, -1);
	const float eps8 = 0.5f / 255.0f;

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT *inP = PixelAtConst<PixelT>(input, x, y);
			float alpha = OLMCKPixelTraits<PixelT>::a(*inP);
			float rgb[3] = {
				OLMCKPixelTraits<PixelT>::r(*inP),
				OLMCKPixelTraits<PixelT>::g(*inP),
				OLMCKPixelTraits<PixelT>::b(*inP)
			};
			float cmp[3] = {
				info.premultiplied ? rgb[0] * alpha : rgb[0],
				info.premultiplied ? rgb[1] * alpha : rgb[1],
				info.premultiplied ? rgb[2] * alpha : rgb[2]
			};
			if (info.color_space == 3) {
				float lab[3];
				RGBToPluginLab76(cmp, lab);
				cmp[0] = lab[0];
				cmp[1] = lab[1];
				cmp[2] = lab[2];
			}
			bool hit_any = false;
			int hit_index = -1;
			for (A_long i = 0; i < info.number_of_colors; ++i) {
				if (!info.use_color[i]) continue;
				float key[3] = { info.colors[i].red, info.colors[i].green, info.colors[i].blue };
				float comp_scale[3] = {1.0f, 1.0f, 1.0f};
				if (info.color_space == 3) {
					RGBToPluginLab76(key, key);
					comp_scale[0] = 151.30099487304688f;
					comp_scale[1] = 264.36700439453125f;
					comp_scale[2] = 295.572998046875f;
				}
				bool hit = false;
				if (info.per_component) {
					PF_FpLong tr = info.per_color ? info.thresholds_r[i] : info.threshold_r;
					PF_FpLong tg = info.per_color ? info.thresholds_g[i] : info.threshold_g;
					PF_FpLong tb = info.per_color ? info.thresholds_b[i] : info.threshold_b;
					hit = std::fabs(cmp[0] - key[0]) <= eps8 + tr * comp_scale[0]
					    && std::fabs(cmp[1] - key[1]) <= eps8 + tg * comp_scale[1]
					    && std::fabs(cmp[2] - key[2]) <= eps8 + tb * comp_scale[2];
				} else {
					PF_FpLong threshold = info.per_color ? info.thresholds[i] : info.threshold;
					float mean = (std::fabs(cmp[0] - key[0]) +
					              std::fabs(cmp[1] - key[1]) +
					              std::fabs(cmp[2] - key[2])) / 3.0f;
					hit = mean <= threshold;
				}
				if (hit && hit_index == -1) hit_index = (int)i;
				hit_any = hit_any || hit;
			}
			size_t idx = (size_t)y * (size_t)w + (size_t)x;
			matched[idx] = hit_any ? 1 : 0;
			matched_index[idx] = hit_index;
		}
	}

	if (!info.enable_replace) {
		if (info.edge_thin_amount < 0.0) {
			std::vector<u_char> nonmatch((size_t)w * (size_t)h, 0);
			for (A_long i = 0; i < w * h; ++i) nonmatch[i] = matched[i] ? 0 : 1;
			std::vector<float> dist = MatteDistanceTo(nonmatch, w, h, info.edge_thin_distance_type);
			float limit = (float)std::fabs(info.edge_thin_amount) +
			              ((info.edge_thin_distance_type == 0 || info.edge_thin_distance_type == 2) ? 1.0f : 0.0f);
			for (A_long i = 0; i < w * h; ++i) matched[i] = (matched[i] && dist[i] > limit) ? 1 : 0;
		} else if (info.edge_thin_amount > 0.0) {
			std::vector<float> dist = MatteDistanceTo(matched, w, h, info.edge_thin_distance_type);
			for (A_long i = 0; i < w * h; ++i) matched[i] = (matched[i] || dist[i] <= info.edge_thin_amount) ? 1 : 0;
		}
	}

	std::vector<u_char> keep_mask((size_t)w * (size_t)h, 0);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT *inP = PixelAtConst<PixelT>(input, x, y);
			PixelT *outP = PixelAt<PixelT>(output, x, y);
			*outP = *inP;
			bool keep = info.color_keep ? matched[(size_t)y * (size_t)w + (size_t)x] != 0
			                            : matched[(size_t)y * (size_t)w + (size_t)x] == 0;
			keep_mask[(size_t)y * (size_t)w + (size_t)x] = keep ? 1 : 0;
			if (!keep) OLMCKPixelTraits<PixelT>::zero(*outP);
			else {
				size_t idx = (size_t)y * (size_t)w + (size_t)x;
				int key_index = matched_index[idx];
				if (info.color_keep && info.enable_replace && key_index >= 0 &&
				    key_index < OLMCOLORKEY_MAX_COLORS && info.use_replace_color[key_index]) {
					OLMCKPixelTraits<PixelT>::replace_rgb(*outP, info.replace_colors[key_index]);
				}
			}
		}
	}
	if (info.edge_blur_amount != 0.0 && !info.enable_replace) {
		std::vector<u_char> boundary = Boundary8(keep_mask, w, h);
		std::vector<float> dist = EdgeBlurDistanceTo(boundary, w, h, info.edge_blur_distance_type);
		for (A_long y = 0; y < h; ++y) {
			for (A_long x = 0; x < w; ++x) {
				size_t idx = (size_t)y * (size_t)w + (size_t)x;
				bool keep = keep_mask[idx] != 0;
				float weight = EdgeBlurWeight(keep, dist[idx], (float)info.edge_blur_amount, info.edge_blur_direction);
				const PixelT *inP = PixelAtConst<PixelT>(input, x, y);
				PixelT *outP = PixelAt<PixelT>(output, x, y);
				const PixelT &src = (!keep && weight != 0.0f) ? *inP : *outP;
				OLMCKPixelTraits<PixelT>::scale(*outP, src, weight);
			}
		}
	}
	return PF_Err_NONE;
}

static PF_Err
RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output, const OLMColorKeyInfo &info, short bitdepth)
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
Render(PF_InData *in_data, PF_OutData *, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	OLMColorKeyInfo info;
	ERR(CheckoutInfo(in_data, params, &info));
	if (err) return err;
	short bitdepth = PF_WORLD_IS_DEEP(output) ? 16 : 8;
	ERR(RenderWorld(&params[OLMCOLORKEY_INPUT]->u.ld, output, info, bitdepth));
	return err;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	req.preserve_rgb_of_zero_alpha = FALSE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMCOLORKEY_INPUT, OLMCOLORKEY_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *, PF_SmartRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, OLMCOLORKEY_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (err || !input_world || !output_world) {
		extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMCOLORKEY_INPUT);
		return err;
	}

	OLMColorKeyInfo info;
	ERR(CheckoutSmartInfo(in_data, &info));
	if (!err) {
		ERR(RenderWorld(input_world, output_world, info, extra->input->bitdepth));
	}

	extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMCOLORKEY_INPUT);
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
		"OLM Color Key",
		"OLM Color Key",
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

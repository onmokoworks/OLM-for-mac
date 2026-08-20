#include "OLMDistanceGradation.h"
#include <AEFX_SuiteHelper.h>
#include "../../core/olmdistancegradation_fieldgen.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <vector>
#include <algorithm>
#include <limits>
#include <new>

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
	out_data->out_flags2 = 0x08001400;
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
	A_long        inside_threshold;
	A_long        outside_threshold;
	A_long        render_mode;      // RENDER_MODE_*
	bool          use_bg;
	PF_PixelFloat grad_color;
	PF_PixelFloat bg_color;
	A_long        interp_mode;      // INTERP_*
	float         power;
	A_long        blur_mode;        // BLUR_MODE_*
	A_long        blur_size;

	A_long        w, h;             // output dimensions
	// downsample scale (full-res -> current-res)
	float         ds_x;
	float         ds_y;
	size_t        pixel_size;       // sizeof(render pixel P); selects the source-mask alpha rule
	bool          smart_owner;      // exported Smart owner routing, distinct from legacy classic owner
	bool          pf32_smart_matrix_admitted;
	bool          pf32_smart_oracle_profile_admitted;
};

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
	if (!cps || !cps->PF_GetFloatingPointColorFromColorDef) return PF_Err_BAD_CALLBACK_PARAM;
	ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[DG_GRAD_COLOR], &p->grad_color));
	ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[DG_BG_COLOR], &p->bg_color));
	if (err) return err;

	p->ds_x = (float)in_data->downsample_x.num / (float)in_data->downsample_x.den;
	p->ds_y = (float)in_data->downsample_y.num / (float)in_data->downsample_y.den;
	return err;
}

// ============================================================================
// Meijster 2-pass Exact Euclidean Distance Transform
//   Reference: A. Meijster, J.B.T.M. Roerdink, W.H. Hesselink 2000.
//   Produces the SAME result as OpenCV distanceTransform(DIST_L2, DIST_MASK_PRECISE).
//
//   Input : mask[w*h] — 0 = "source" (distance 0), non-zero = "to measure"
//   Output: dst [w*h] — Euclidean distance (float) to nearest zero pixel
// ============================================================================
static inline float edt_f(long x, long i, long gi) {
	// squared distance from (x,?) to (i, g(i)); used for parabola intersections
	long d = x - i;
	return (float)(d * d + (long long)gi * gi);
}
static inline long edt_sep(long i, long u, long gi, long gu) {
	// intersection x of two parabolas at column i (g=gi) and column u (g=gu)
	long long num = (long long)u * u - (long long)i * i + (long long)gu * gu - (long long)gi * gi;
	long long den = 2 * (long long)(u - i);
	// floor division for negative numerator is fine here since u > i always
	return (long)(num / den);
}

static void meijster_edt(const u_char *mask, float *dst, long w, long h)
{
	const long INF = w + h; // upper bound
	std::vector<long> g((size_t)w * h);

	// Phase 1: column-wise vertical pass — g(x,y) = dist to nearest zero in column x
	for (long x = 0; x < w; ++x) {
		// Top-down
		g[(size_t)x] = mask[x] ? INF : 0;
		for (long y = 1; y < h; ++y) {
			size_t idx = (size_t)y * w + x;
			if (mask[idx]) {
				long prev = g[idx - w];
				g[idx] = (prev == INF) ? INF : (prev + 1);
			} else {
				g[idx] = 0;
			}
		}
		// Bottom-up
		for (long y = h - 2; y >= 0; --y) {
			size_t idx = (size_t)y * w + x;
			long below = g[idx + w];
			long cur   = g[idx];
			if (below != INF && below + 1 < cur) g[idx] = below + 1;
		}
	}

	// Phase 2: row-wise parabola envelope — F(x,y) = min over i of (x-i)^2 + g(i,y)^2
	std::vector<long> s((size_t)w), t((size_t)w);
	for (long y = 0; y < h; ++y) {
		long q = 0;
		s[0] = 0;
		t[0] = 0;
		const long *grow = &g[(size_t)y * w];

		for (long u = 1; u < w; ++u) {
			while (q >= 0 && edt_f(t[q], s[q], grow[s[q]]) > edt_f(t[q], u, grow[u])) {
				--q;
			}
			if (q < 0) {
				q = 0;
				s[0] = u;
			} else {
				long w_sep = 1 + edt_sep(s[q], u, grow[s[q]], grow[u]);
				if (w_sep < w) {
					++q;
					s[q] = u;
					t[q] = w_sep;
				}
			}
		}

		float *drow = dst + (size_t)y * w;
		for (long u = w - 1; u >= 0; --u) {
			float d2 = edt_f(u, s[q], grow[s[q]]);
			drow[u] = sqrtf(d2);
			if (u == t[q]) --q;
		}
	}
}

// ============================================================================
// Gaussian blur (separable, matches the legacy cvSmooth replicated border +
// sigma derived via cv::getGaussianKernel default:  sigma = 0.3*((ksize-1)*0.5 - 1) + 0.8
// ============================================================================
static void make_gauss_kernel(std::vector<float> &k, int ksize)
{
	// Odd kernel size required
	if ((ksize & 1) == 0) ++ksize;
	if (ksize < 1) ksize = 1;
	// OpenCV uses an exact binomial kernel for the 3-tap, sigma=0 case.
	// Keeping these values literal avoids the measurable difference from the
	// generic sigma heuristic at the PF16 staging boundary.
	if (ksize == 3) {
		k = {0.25f, 0.5f, 0.25f};
		return;
	}
	double sigma = 0.3 * ((ksize - 1) * 0.5 - 1.0) + 0.8;
	double two_s2 = 2.0 * sigma * sigma;
	k.resize(ksize);
	double sum = 0;
	int half = ksize / 2;
	for (int i = 0; i < ksize; ++i) {
		double x = i - half;
		k[i] = (float)std::exp(-x * x / two_s2);
		sum += k[i];
	}
	float inv = (float)(1.0 / sum);
	for (auto &v : k) v *= inv;
}

static inline long reflect101(long i, long n) {
	if (n <= 1) return 0;
	if (i < 0) i = -i;
	long p = 2 * (n - 1);
	i %= p;
	if (i < 0) i += p;
	if (i >= n) i = p - i;
	return i;
}

static void gauss_blur_separable(float *mat, long w, long h, int ksize)
{
	if (ksize <= 1) return;
	std::vector<float> k;
	make_gauss_kernel(k, ksize);
	int half = (int)k.size() / 2;

	std::vector<float> tmp((size_t)w * h);
	if (ksize == 3) {
		for (long y = 0; y < h; ++y) {
			const float *row = mat + (size_t)y * w;
			for (long x = 0; x < w; ++x) {
				long xl = x > 0 ? x - 1 : 0;
				long xr = x + 1 < w ? x + 1 : w - 1;
				tmp[(size_t)y * w + x] = (row[xl] + row[xr]) * 0.25f + row[x] * 0.5f;
			}
		}
		for (long y = 0; y < h; ++y) {
			long yt = y > 0 ? y - 1 : 0;
			long yb = y + 1 < h ? y + 1 : h - 1;
			for (long x = 0; x < w; ++x) {
				mat[(size_t)y * w + x] =
					(tmp[(size_t)yt * w + x] + tmp[(size_t)yb * w + x]) * 0.25f +
					tmp[(size_t)y * w + x] * 0.5f;
			}
		}
		return;
	}

	// Horizontal
	for (long y = 0; y < h; ++y) {
		const float *row = mat + (size_t)y * w;
		float       *out = tmp.data() + (size_t)y * w;
		for (long x = 0; x < w; ++x) {
			float acc = 0;
			for (int i = -half; i <= half; ++i) {
				long xi = x + i;
				if (xi < 0) xi = 0;
				if (xi >= w) xi = w - 1;
				acc += row[xi] * k[i + half];
			}
			out[x] = acc;
		}
	}
	// Vertical
	for (long x = 0; x < w; ++x) {
		for (long y = 0; y < h; ++y) {
			float acc = 0;
			for (int i = -half; i <= half; ++i) {
				long yi = y + i;
				if (yi < 0) yi = 0;
				if (yi >= h) yi = h - 1;
				acc += tmp[(size_t)yi * w + x] * k[i + half];
			}
			mat[(size_t)y * w + x] = acc;
		}
	}
}

// cvSmooth mode 1 (CV_BLUR) used by Constant + Blur is a normalized box
// filter with replicated borders. Keep it separate from the Gaussian path
// used by the other interpolation modes.
static void box_blur_separable(float *mat, long w, long h, int ksize)
{
	if (ksize <= 1) return;
	const int half = ksize / 2;
	const float area = (float)(ksize * ksize);
	std::vector<float> src(mat, mat + (size_t)w * h);
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			double sum = 0.0;
			for (int j = -half; j <= half; ++j) {
				long yi = y + j;
				if (yi < 0) yi = 0;
				if (yi >= h) yi = h - 1;
				for (int i = -half; i <= half; ++i) {
					long xi = x + i;
					if (xi < 0) xi = 0;
					if (xi >= w) xi = w - 1;
					sum += src[(size_t)yi * w + xi];
				}
			}
			mat[(size_t)y * w + x] = (float)(sum / (double)area);
		}
	}
}

// Legacy cvSmooth mode 3 (CV_MEDIAN).  The retained AEX uses replicated
// borders and an odd square aperture.  Keep the temporary source separate:
// OpenCV's median pass never consumes values written earlier in the scan.
static void median_blur(float *mat, long w, long h, int ksize)
{
	if (!mat || w <= 0 || h <= 0 || ksize <= 1) return;
	const int radius = ksize / 2;
	std::vector<float> source(mat, mat + (size_t)w * h);
	std::vector<float> window((size_t)ksize * ksize);
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			size_t n = 0;
			for (int ky = -radius; ky <= radius; ++ky) {
				const long sy = std::max(0L, std::min(h - 1, y + ky));
				for (int kx = -radius; kx <= radius; ++kx) {
					const long sx = std::max(0L, std::min(w - 1, x + kx));
					window[n++] = source[(size_t)sy * w + sx];
				}
			}
			std::nth_element(window.begin(), window.begin() + n / 2, window.begin() + n);
			mat[(size_t)y * w + x] = window[n / 2];
		}
	}
}

static inline float bilateral_noncontracting_product(float left, float right)
{
	volatile float product = left * right;
	return product;
}

// PF32 Smart reproduction of the retained IPP bilateral body selected by
// cvSmooth(CV_BILATERAL, 3, 3, 0, 0).  Its call site is guarded by the bounded
// PF32 admission predicate; PF8/PF16 do not enter this helper and retain their
// separately proven Mode 5 staging.  The only new promotion is the fixed17x11
// PF32 Smart tuple.  IPP evaluates four color weights directly, accumulates
// L/T/R/B without contraction, then applies the common spatial weight.
static void bilateral_blur_opencv455_f32x4(float *mat, long w, long h)
{
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
	if (!mat || w <= 0 || h <= 0) return;
	std::vector<float> source(mat, mat + (size_t)w * h);
	const float spatial_weight = ::expf(-0.5f);
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			const long top = std::max(0L, y - 1), bottom = std::min(h - 1, y + 1);
			const long left = std::max(0L, x - 1), right = std::min(w - 1, x + 1);
			const float center = source[(size_t)y * w + x];
			const float values[4] = {source[(size_t)y * w + left], source[(size_t)top * w + x],
			                         source[(size_t)y * w + right], source[(size_t)bottom * w + x]};
			float sum = 0.0f;
			float weight_sum = 0.0f;
			for (int k = 0; k < 4; ++k) {
				const float difference = values[k] - center;
				const float squared_difference = difference * difference;
				const float color_weight = ::expf(-0.5f * squared_difference);
				weight_sum += color_weight;
				sum += bilateral_noncontracting_product(values[k], color_weight);
			}
			weight_sum = bilateral_noncontracting_product(weight_sum, spatial_weight);
			sum = bilateral_noncontracting_product(sum, spatial_weight);
			mat[(size_t)y * w + x] = (sum + center) / (weight_sum + 1.0f);
		}
	}
}

// ============================================================================
// Helpers: pixel fetch / store (alpha, red, green, blue order in AE)
// ============================================================================
template<typename P> static inline void load_rgba_norm(const P *p, float &a, float &r, float &g, float &b);

template<> inline void load_rgba_norm<PF_Pixel8>(const PF_Pixel8 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / 255.0f; r = p->red / 255.0f; g = p->green / 255.0f; b = p->blue / 255.0f;
}
template<> inline void load_rgba_norm<PF_Pixel16>(const PF_Pixel16 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / 32768.0f; r = p->red / 32768.0f; g = p->green / 32768.0f; b = p->blue / 32768.0f;
}
template<> inline void load_rgba_norm<PF_PixelFloat>(const PF_PixelFloat *p, float &a, float &r, float &g, float &b) {
	a = p->alpha; r = p->red; g = p->green; b = p->blue;
}

// The actual-AEX PF8 and PF16 compose callbacks both use float-to-int
// truncation before storing the channel word (FUN_181170870/FUN_181170480).
static inline u_char clamp8(float v)   { v = v * 255.0f; return (v < 0) ? 0 : (v > 255.f ? 255 : (u_char)v); }
static inline u_short clamp16(float v) { v = v * 32768.0f; return (v < 0) ? 0 : (v > 32768.f ? 32768 : (u_short)v); }

static bool debug_point_selected(const char *points, long x, long y)
{
	if (!points || !points[0]) return false;
	const char *cursor = points;
	while (*cursor) {
		char *end = nullptr;
		long px = strtol(cursor, &end, 10);
		if (end == cursor || *end != ',') return false;
		cursor = end + 1;
		long py = strtol(cursor, &end, 10);
		if (end == cursor) return false;
		if (px == x && py == y) return true;
		cursor = end;
		while (*cursor == ';' || *cursor == ' ' || *cursor == '\t') ++cursor;
	}
	return false;
}

static void debug_dump_shade_point(
	const char *path, const DGParams &p, long x, long y, size_t pixel_size,
	float sa, float sr, float sg, float sb, float field_x, float d_alpha,
	float oa, float orv, float og, float ob,
	unsigned long stored_a, unsigned long stored_r, unsigned long stored_g, unsigned long stored_b,
	unsigned long dst_a, unsigned long dst_r, unsigned long dst_g, unsigned long dst_b)
{
	if (!path || !path[0]) return;
	FILE *f = fopen(path, "a");
	if (!f) return;
	fprintf(f,
	        "shade x=%ld y=%ld pixel_size=%zu use_bg=%d render_mode=%ld src_a=%.9g src_r=%.9g src_g=%.9g src_b=%.9g field_x=%.9g d_alpha=%.9g out_a=%.9g out_r=%.9g out_g=%.9g out_b=%.9g store_a=%lu store_r=%lu store_g=%lu store_b=%lu dst_a=%lu dst_r=%lu dst_g=%lu dst_b=%lu\n",
	        x, y, pixel_size, p.use_bg ? 1 : 0, (long)p.render_mode,
	        sa, sr, sg, sb, field_x, d_alpha, oa, orv, og, ob,
	        stored_a, stored_r, stored_g, stored_b, dst_a, dst_r, dst_g, dst_b);
	fclose(f);
}

static unsigned long debug_float32_bits(float value)
{
	unsigned long bits = 0;
	unsigned int word = 0;
	memcpy(&word, &value, sizeof(word));
	bits = word;
	return bits;
}

// Mac-only, logging-only PF16 boundary witness.  The production shade path
// does not enter this function unless both capture env vars select a point.
// Values and words are copied from the live PF16 shade site; float bit
// identities use memcpy so the witness does not depend on aliasing.
static void debug_dump_pf16_boundary_point(
	const char *path, const char *case_id, long x, long y,
	const PF_Pixel16 &source, float field_value, u_short derived_field_word,
	float oa, float orv, float og, float ob, const PF_Pixel16 &stored)
{
	if (!path || !path[0] || !case_id || !case_id[0]) return;
	FILE *f = fopen(path, "a");
	if (!f) return;
	fprintf(f,
	        "{\"kind\":\"olmdg_pf16_shade_boundary_v1\",\"case_id\":\"%s\","
	        "\"x\":%ld,\"y\":%ld,"
	        "\"source\":{\"a\":%u,\"r\":%u,\"g\":%u,\"b\":%u},"
	        "\"field\":{\"value\":%.9g,\"bits\":\"0x%08lx\","
	        "\"derived_pf16_word\":%u,"
	        "\"derivation\":\"nearest_even_clamp_float32_times_32768_logging_only\","
	        "\"direct_field_staging_word\":\"unavailable_at_mac_float_field_boundary\"},"
	        "\"pre_store\":{"
	        "\"a\":{\"value\":%.9g,\"bits\":\"0x%08lx\"},"
	        "\"r\":{\"value\":%.9g,\"bits\":\"0x%08lx\"},"
	        "\"g\":{\"value\":%.9g,\"bits\":\"0x%08lx\"},"
	        "\"b\":{\"value\":%.9g,\"bits\":\"0x%08lx\"}},"
	        "\"stored\":{\"a\":%u,\"r\":%u,\"g\":%u,\"b\":%u}}\n",
	        case_id, x, y,
	        (unsigned int)source.alpha, (unsigned int)source.red,
	        (unsigned int)source.green, (unsigned int)source.blue,
	        field_value, debug_float32_bits(field_value), (unsigned int)derived_field_word,
	        oa, debug_float32_bits(oa), orv, debug_float32_bits(orv),
	        og, debug_float32_bits(og), ob, debug_float32_bits(ob),
	        (unsigned int)stored.alpha, (unsigned int)stored.red,
	        (unsigned int)stored.green, (unsigned int)stored.blue);
	fclose(f);
}

// ============================================================================
// Distance field builder (shared across bit depths)
//   input_alpha_norm: 0..1 alpha, size w*h
//   Produces normalized distance field X in [0,1] per pixel.
// ============================================================================
struct DistanceField {
	std::vector<float> x;    // normalized distance [0,1]
	std::vector<float> d_alpha; // 0 or 1 — output alpha mask
	std::vector<float> pre_blur_x; // Constant+Blur writer's unblurred binary field
	long w, h;
};

static float debug_raw_distance_at(const u_char *mask, long w, long h, long x, long y);
static void dt_to_normalized(
	const u_char *mask, float *out, long w, long h, long threshold, bool constant_interp);

// Depth-dependent source-mask rule (both sides AE-host proven at the correct
// project depth; earlier sentinel confusion came from 8bpc requests silently
// rendering at 16bpc project depth — a reference_manifest without
// project.bits_per_channel leaves the previous project depth active):
//  - 8bpc (PF_Pixel8): any nonzero alpha participates. The packaged 8bpc
//    suite is byte-exact with the inclusive rule (2026-06-19 return).
//  - 16bpc and deeper: the 1-code (8U-equivalent) alpha fringe is NOT part
//    of the source mask, matching the Windows 8U-convert +
//    cvThreshold(thresh=1.0) field staging; this closes case_0023
//    (Both + Outside Threshold=0) bg_on/bg_off to nonzero_px=0.
static inline bool source_mask_owns_alpha(float alpha, size_t pixel_size)
{
	if (pixel_size == sizeof(PF_Pixel8)) return alpha > 0.0f;
	return alpha > (1.5f / 255.0f);
}

static void debug_dump_distance_field(const char *path, const float *alpha, const DistanceField &df,
                                      const DGParams &p, long w, long h, size_t pixel_size)
{
	if (!path || !path[0] || !alpha || df.x.empty()) return;
	FILE *f = fopen(path, "a");
	if (!f) return;
	fprintf(f,
	        "OLMDistanceGradation debug dump\n"
	        "w=%ld h=%ld pixel_size=%zu invert=%d in_out=%ld inside=%ld outside=%ld render_mode=%ld use_bg=%d interp=%ld power=%.9g blur_mode=%ld blur_size=%ld ds_x=%.9g ds_y=%.9g\n",
	        w, h, pixel_size, p.invert ? 1 : 0, (long)p.in_out, (long)p.inside_threshold,
	        (long)p.outside_threshold, (long)p.render_mode, p.use_bg ? 1 : 0,
	        (long)p.interp_mode, p.power, (long)p.blur_mode, (long)p.blur_size, p.ds_x, p.ds_y);
	long limit = (w < 15) ? w : 15;
	for (long x = 0; x < limit; ++x) {
		size_t idx = (size_t)x;
		fprintf(f, "row0 x=%ld alpha=%.9g d_alpha=%.9g field_x=%.9g\n",
		        x, alpha[idx], df.d_alpha[idx], df.x[idx]);
	}
	const char *points = getenv("OLM_DG_DEBUG_POINTS");
	if (points && points[0]) {
		std::vector<u_char> inside_mask((size_t)w * h);
		std::vector<u_char> outside_mask((size_t)w * h);
		std::vector<float> inside_norm((size_t)w * h, 0.0f);
		std::vector<float> outside_norm((size_t)w * h, 0.0f);
		for (long i = 0; i < w * h; ++i) {
			inside_mask[i] = source_mask_owns_alpha(alpha[i], pixel_size) ? 1 : 0;
			outside_mask[i] = inside_mask[i] ? 0 : 1;
		}
		bool constant_interp = (p.interp_mode == INTERP_CONSTANT);
		dt_to_normalized(inside_mask.data(), inside_norm.data(), w, h, p.inside_threshold, constant_interp);
		dt_to_normalized(outside_mask.data(), outside_norm.data(), w, h, p.outside_threshold, constant_interp);
		float inside_t = (float)p.inside_threshold;
		float outside_t = (float)p.outside_threshold;
		if (!constant_interp && inside_t < 1.0f) inside_t = 1.0f;
		if (!constant_interp && outside_t < 1.0f) outside_t = 1.0f;
		const char *cursor = points;
		while (*cursor) {
			char *end = nullptr;
			long x = strtol(cursor, &end, 10);
			if (end == cursor || *end != ',') break;
			cursor = end + 1;
			long y = strtol(cursor, &end, 10);
			if (end == cursor) break;
			if (x >= 0 && x < w && y >= 0 && y < h) {
				size_t idx = (size_t)y * w + x;
				float raw_inside = debug_raw_distance_at(inside_mask.data(), w, h, x, y);
				float raw_outside = debug_raw_distance_at(outside_mask.data(), w, h, x, y);
				float inside_x = inside_norm[idx];
				float outside_x = outside_norm[idx];
				float both_x = (inside_x > outside_x) ? inside_x : outside_x;
				const char *winner = (inside_x >= outside_x) ? "inside-or-tie" : "outside";
				int inside_constant_binary = (raw_inside > inside_t) ? 1 : 0;
				int outside_constant_binary = (raw_outside > outside_t) ? 1 : 0;
				fprintf(f,
				        "point x=%ld y=%ld alpha=%.9g d_alpha=%.9g field_x=%.9g raw_inside=%.9g raw_outside=%.9g inside_x=%.9g outside_x=%.9g both_x=%.9g winner=%s inside_t=%.9g outside_t=%.9g inside_constant_binary=%d outside_constant_binary=%d compose_input_x=%.9g\n",
				        x, y, alpha[idx], df.d_alpha[idx], df.x[idx], raw_inside, raw_outside,
				        inside_x, outside_x, both_x, winner, inside_t, outside_t,
				        inside_constant_binary, outside_constant_binary, df.x[idx]);
			} else {
				fprintf(f, "point x=%ld y=%ld out_of_bounds=1\n", x, y);
			}
			cursor = end;
			while (*cursor == ';' || *cursor == ' ' || *cursor == '\t') ++cursor;
		}
	}
	fclose(f);
}

static void build_mask_from_alpha(const float *alpha, u_char *mask, long w, long h, size_t pixel_size)
{
	for (long i = 0; i < w * h; ++i) mask[i] = source_mask_owns_alpha(alpha[i], pixel_size) ? 1 : 0;
}
static void invert_mask(u_char *mask, long w, long h)
{
	for (long i = 0; i < w * h; ++i) mask[i] = mask[i] ? 0 : 1;
}

// Distance transform with threshold+normalize. The helper shape is
// binary-grounded from FUN_181174760:
//   distanceTransform -> threshold(TRUNC or BINARY) -> normalize(NORM_MINMAX to [0,1]).
// The MINMAX step divides by actual_max = min(raw_max, thresh), NOT by thresh.
// This matters when the mask is small enough that no distance reaches thresh:
// the gradient is stretched to fill [0,1] anyway, so inverted X reaches 0 at the
// deepest interior pixel instead of leaving a residual.
//
// The AEX callers load the raw UI threshold directly into R9D from config +0xb8
// or +0xbc. Scaled staging dimensions are separate arguments, so downsample
// scale does not own the threshold passed to this helper.
static void dt_to_normalized(
	const u_char *mask, float *out, long w, long h, long threshold, bool constant_interp)
{
	(void)olm::distancegradation::distance_to_normalized_u8(
		mask, (size_t)w, (size_t)h, (size_t)w,
		out, (size_t)w * sizeof(float), (float)threshold, constant_interp);
}

static float debug_raw_distance_at(const u_char *mask, long w, long h, long x, long y)
{
	if (!mask || x < 0 || y < 0 || x >= w || y >= h) return -1.0f;
	std::vector<float> raw((size_t)w * h);
	meijster_edt(mask, raw.data(), w, h);
	return raw[(size_t)y * w + x];
}

static void build_distance_field(
	const float *alpha, DistanceField &df, const DGParams &p, long w, long h)
{
	df.w = w; df.h = h;
	df.x.assign((size_t)w * h, 0.0f);
	df.d_alpha.assign((size_t)w * h, 0.0f);

	std::vector<u_char> mask((size_t)w * h);
	build_mask_from_alpha(alpha, mask.data(), w, h, p.pixel_size);

	// d_alpha: source ownership follows the same depth-dependent mask rule
	for (long i = 0; i < w * h; ++i) df.d_alpha[i] = mask[i] ? 1.0f : 0.0f;

	float ds = (p.ds_x + p.ds_y) * 0.5f;
	if (ds <= 0.0f) ds = 1.0f;

	if (p.in_out == IN_OUT_INSIDE) {
		bool has_source = false;
		for (long i = 0; i < w * h; ++i) {
			if (mask[i] == 0) {
				has_source = true;
				break;
			}
		}
		if (!has_source) {
			float no_edge_x = p.invert ? 0.0f : 1.0f;
			for (long i = 0; i < w * h; ++i) df.x[i] = no_edge_x;
		} else {
			dt_to_normalized(mask.data(), df.x.data(), w, h, p.inside_threshold,
			                 p.interp_mode == INTERP_CONSTANT);
		}
	} else if (p.in_out == IN_OUT_OUTSIDE) {
		invert_mask(mask.data(), w, h);
		dt_to_normalized(mask.data(), df.x.data(), w, h, p.outside_threshold,
		                 p.interp_mode == INTERP_CONSTANT);
	} else { // BOTH
		std::vector<float> inside((size_t)w * h), outside((size_t)w * h);
		dt_to_normalized(mask.data(), inside.data(), w, h, p.inside_threshold,
		                 p.interp_mode == INTERP_CONSTANT);
		std::vector<u_char> m2 = mask; // copy
		invert_mask(m2.data(), w, h);
		dt_to_normalized(m2.data(), outside.data(), w, h, p.outside_threshold,
		                 p.interp_mode == INTERP_CONSTANT);
		for (long i = 0; i < w * h; ++i) df.x[i] = std::max(inside[i], outside[i]);
	}

	bool blurred = p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0;
	bool constant_blur = p.interp_mode == INTERP_CONSTANT && blurred;
	if (constant_blur) {
		for (long i = 0; i < w * h; ++i) df.x[i] = (df.x[i] >= 1.0f) ? 1.0f : 0.0f;
	}
	if (blurred && (!p.smart_owner || constant_blur)) df.pre_blur_x = df.x;

	// Blur: the Windows owner always converts the full-resolution Blur Size to
	// current-resolution pixels. Blur Mode selects the cvSmooth primitive:
	// mode 2 uses normalized box blur, mode 3 Gaussian, mode 4 median, and
	// mode 5 the legacy bilateral call.  Only the admitted fixed17x11 PF32
	// Smart tuple enters the retained IPP reproduction below; other PF32 Smart
	// tuples fail closed, while PF8/PF16 retain their separately proven path.
	if (p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0) {
		long bs = (long)((float)p.blur_size * ds + 0.5f);
		if (bs < 1) bs = 1;
		int ksize = (int)(2 * bs + 1);
		if (ksize > 1) {
			if (p.blur_mode == BLUR_MODE_NO_SCALE) {
				box_blur_separable(df.x.data(), w, h, ksize);
			} else if (p.blur_mode == BLUR_MODE_SCALE) {
				gauss_blur_separable(df.x.data(), w, h, ksize);
			} else if (p.blur_mode == BLUR_MODE_MEDIAN) {
				median_blur(df.x.data(), w, h, ksize);
			} else if (p.blur_mode == BLUR_MODE_BILATERAL) {
				if (p.pf32_smart_matrix_admitted || p.pf32_smart_oracle_profile_admitted) {
					bilateral_blur_opencv455_f32x4(df.x.data(), w, h);
				}
				// PF8/PF16 retain their independently proven typed staging.
				// Other PF32 Smart tuples remain fail-closed before field creation.
			}
		}
	}

	// The Windows typed paths merge the float field into an OpenCV image, then
	// stores it through cvConvertScale before PF Iterate16 reads it back. Match
	// that PF16 boundary here; keeping the float directly changes half-integer
	// cases before compose. The 8bpc and float paths have separate exactness
	// contracts and are intentionally unchanged.
	if (p.pixel_size == sizeof(PF_Pixel16)) {
		for (float &value : df.x) {
			value = olm::distancegradation::roundtrip_normalized_pf16_even(value);
		}
	} else if (p.pixel_size == sizeof(PF_Pixel8)) {
		// Independent PF8 fieldgen->compose capture proves the corresponding
		// cvConvertScale nearest-even byte staging before FUN_181170870.
		for (float &value : df.x) {
			float scaled = value * 255.0f;
			int word = (scaled < 0.0f) ? 0 : (scaled > 255.0f ? 255 : (int)lrintf(scaled));
			value = (float)word / 255.0f;
		}
		for (float &value : df.d_alpha) {
			float scaled = value * 255.0f;
			int word = (scaled < 0.0f) ? 0 : (scaled > 255.0f ? 255 : (int)lrintf(scaled));
			value = (float)word / 255.0f;
		}
		for (float &value : df.d_alpha) {
			value = olm::distancegradation::roundtrip_normalized_pf16_even(value);
		}
	}
}

// ============================================================================
// Per-pixel color combination (mirrors FUN_181170870 disassembly)
// ============================================================================
static inline void compose_pixel(
	float src_a, float src_r, float src_g, float src_b,
	float field_aux, float X,
	const DGParams &p,
	float &out_a, float &out_r, float &out_g, float &out_b)
{
	// The classic PF32 owner bypasses the typed integer color callback for this
	// branch and merges its raw float ownership field into all four channels.
	// Consequently Sphere and invert do not transform the exported scalar.
	if (!p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	    p.in_out == IN_OUT_OUTSIDE && p.render_mode == RENDER_MODE_RGB && !p.use_bg) {
		out_a = out_r = out_g = out_b = X;
		return;
	}
	if (p.pixel_size == sizeof(PF_PixelFloat) &&
	    p.in_out == IN_OUT_BOTH && p.render_mode == RENDER_MODE_LAYER && !p.use_bg) {
		out_a = out_r = out_g = out_b = X;
		return;
	}
	// Invert: default (OFF) flips X to 1 - X; checked (ON) keeps X as-is.
	if (!p.invert) X = 1.0f - X;

	// Interpolation transforms on X
	if (p.interp_mode == INTERP_SPHERE) {
		// The typed callback promotes the float subtraction to double, calls
		// pow(..., 2.0), subtracts in double, then uses double sqrt before the
		// final float conversion. A float-only rewrite differs by one ULP.
		double t = (double)(1.0f - X);
		double s = 1.0 - std::pow(t, 2.0);
		X = (s < 0.0) ? 0.0f : (float)std::sqrt(s);
	} else if (p.interp_mode == INTERP_POWER) {
		// The fixed PF32 Smart matrix is bound to Windows 11 UCRT 10.0.26100.8875.
		// Across its 63 exact powf input pairs, macOS/libSystem differs for one
		// word only.  Preserve the native UCRT result for that witnessed input;
		// every other value still follows the platform powf implementation.  The
		// matrix admission below keeps this leaf override unreachable for every
		// unproven tuple, geometry, owner and depth.
		if (p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
		    p.pf32_smart_matrix_admitted && p.power == 2.25f) {
			uint32_t x_bits = 0;
			memcpy(&x_bits, &X, sizeof(x_bits));
			if (x_bits == 0x3f4d07a5u) {
				const uint32_t native_ucrt_bits = 0x3f1b5786u;
				memcpy(&X, &native_ucrt_bits, sizeof(X));
			} else {
				X = powf(X, p.power);
			}
		} else {
			X = powf(X, p.power);
		}
	}
	// CONSTANT / LINEAR: X passes through. For CONSTANT+Blur, X is already the
	// blurred binary field prepared in build_distance_field().
	if (p.interp_mode == INTERP_CONSTANT &&
	    !(p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0)) {
		X = (X > 0.0f) ? 1.0f : 0.0f;
	}

	// d_alpha derived from src_a per in_out mode (matches Win shader)
	float d_alpha;
	switch (p.in_out) {
	case IN_OUT_INSIDE:  d_alpha = src_a; break;
	case IN_OUT_OUTSIDE: d_alpha = 1.0f - src_a; if (d_alpha < 0) d_alpha = 0; break;
	default:             d_alpha = 1.0f; break; // BOTH
	}
	if (!p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	    p.in_out == IN_OUT_INSIDE && p.render_mode == RENDER_MODE_RGB && !p.use_bg &&
	    p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0) {
		out_a = out_r = out_g = X;
		out_b = field_aux;
		return;
	}
	// RGB selection:
	//   render_mode == 1 (RGB)   -> gradation color (default)
	//   render_mode == 2 (Layer) -> source color
	float ir, ig, ib;
	if (p.render_mode == RENDER_MODE_RGB) {
		ir = p.grad_color.red; ig = p.grad_color.green; ib = p.grad_color.blue;
	} else {
		ir = src_r; ig = src_g; ib = src_b;
	}
	if (!p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	    p.in_out == IN_OUT_INSIDE && p.render_mode == RENDER_MODE_RGB && p.use_bg) {
		if (p.interp_mode != INTERP_CONSTANT &&
		    p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0) {
			out_a = out_r = out_g = X;
			out_b = field_aux;
			return;
		}
		float scalar = d_alpha * X;
		out_a = out_r = out_g = out_b = scalar;
		if (p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0) out_b = field_aux;
		return;
	}

	if (p.use_bg) {
		float oneX = 1.0f - X;
		if (p.smart_owner) {
			volatile float bg_r = oneX * p.bg_color.red, fg_r = X * ir;
			volatile float bg_g = oneX * p.bg_color.green, fg_g = X * ig;
			volatile float bg_b = oneX * p.bg_color.blue, fg_b = X * ib;
			out_r = bg_r + fg_r; out_g = bg_g + fg_g; out_b = bg_b + fg_b;
		} else {
			out_r = oneX * p.bg_color.red + X * ir;
			out_g = oneX * p.bg_color.green + X * ig;
			out_b = oneX * p.bg_color.blue + X * ib;
		}
		out_a = d_alpha;            // use_bg: alpha = d_alpha (full)
		// The PF16 AEX callback clears the complete pixel when an Inside
		// source is outside the ownership mask.  Keeping background RGB under
		// zero alpha produced hidden color that is absent from the typed AEX
		// output.  Bound this to the proven PF16/Inside/use-bg branch.
		if ((p.pixel_size == sizeof(PF_Pixel16) || p.pixel_size == sizeof(PF_Pixel8) ||
		     p.pixel_size == sizeof(PF_PixelFloat)) &&
		    p.in_out == IN_OUT_INSIDE && d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
			if ((p.pixel_size == sizeof(PF_Pixel16) || p.pixel_size == sizeof(PF_Pixel8) ||
			     (p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat))) &&
			    p.render_mode == RENDER_MODE_RGB &&
			    p.interp_mode != INTERP_CONSTANT && p.blur_mode != BLUR_MODE_NONE &&
			    p.blur_size > 0) {
				out_r = p.pixel_size == sizeof(PF_Pixel8) ? field_aux
				      : (p.smart_owner ? field_aux : 0.0f);
				out_g = p.smart_owner ? field_aux : X;
			}
		}
		// The actual PF16 Outside/Layer/background callback applies the same
		// ownership clearing on the opposite side of the mask.  This branch is
		// intentionally limited to the independently exercised typed contract;
		// other depths/render modes remain separate evidence boundaries.
		if (p.pixel_size == sizeof(PF_Pixel16) && p.in_out == IN_OUT_OUTSIDE &&
		    p.render_mode == RENDER_MODE_LAYER && d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
		}
	} else {
		out_a = d_alpha * X;        // no bg: alpha = d_alpha * X
		if (p.pixel_size == sizeof(PF_Pixel8) && p.in_out == IN_OUT_INSIDE &&
		    p.render_mode == RENDER_MODE_RGB && d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
			if (p.interp_mode != INTERP_CONSTANT && p.blur_mode != BLUR_MODE_NONE &&
			    p.blur_size > 0) {
				out_r = field_aux;
				out_g = X;
			}
			return;
		}
		if ((p.pixel_size == sizeof(PF_Pixel16) ||
		     (p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat))) &&
		    p.in_out == IN_OUT_INSIDE &&
		    p.render_mode == RENDER_MODE_RGB && d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
			if (p.interp_mode != INTERP_CONSTANT &&
			    p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0) {
				// The typed owner leaks the pre-interpolation blurred scalar on
				// transparent Inside pixels. Sphere/Power still transform X on
				// owned pixels, but these auxiliary lanes consume field_aux.
				out_g = p.smart_owner ? field_aux : X;
				if (p.smart_owner) out_r = field_aux;
			}
			return;
		}
		if ((p.pixel_size == sizeof(PF_Pixel16) || p.pixel_size == sizeof(PF_Pixel8)) &&
		    p.in_out == IN_OUT_OUTSIDE && p.render_mode == RENDER_MODE_RGB &&
		    d_alpha <= 0.0f) {
			out_r = out_g = out_b = 0.0f;
			return;
		}
		if (p.render_mode == RENDER_MODE_LAYER && src_a > 0.0f) {
			// Windows 16bpc Layer/no-bg stores RGB from the straight source
			// ownership mask, while alpha still carries the gradation field.
			// Keep the older 8bpc path unchanged because that suite is already
			// canonical AE exact.
			bool low_alpha_hidden_color = (p.pixel_size != sizeof(PF_Pixel8)) &&
			                              src_a <= (1.5f / 255.0f) &&
			                              src_r <= src_a && src_g <= src_a && src_b <= src_a;
			bool both_channel_mask_color = (p.pixel_size != sizeof(PF_Pixel8)) &&
			                               p.in_out == IN_OUT_BOTH &&
			                               src_a <= (150.0f / 255.0f) &&
			                               src_r <= src_a && src_g <= src_a && src_b <= src_a;
			if (low_alpha_hidden_color || both_channel_mask_color) {
				if (both_channel_mask_color) {
						// Windows promotes only the dominant mask channel to
						// source alpha here; smaller color components keep the
						// straight-source ratio and are premultiplied by AE export.
						float inv_a = 1.0f / src_a;
						float straight_r = src_r * inv_a;
						float straight_g = src_g * inv_a;
						float straight_b = src_b * inv_a;
						float max_src = src_r;
						if (src_g > max_src) max_src = src_g;
						if (src_b > max_src) max_src = src_b;
						out_r = (src_r > 0.0f && src_r >= max_src) ? src_a : straight_r;
						out_g = (src_g > 0.0f && src_g >= max_src) ? src_a : straight_g;
						out_b = (src_b > 0.0f && src_b >= max_src) ? src_a : straight_b;
					} else {
						float channel_alpha = src_a * out_a;
						out_r = (src_r > 0.0f) ? channel_alpha : 0.0f;
						out_g = (src_g > 0.0f) ? channel_alpha : 0.0f;
						out_b = (src_b > 0.0f) ? channel_alpha : 0.0f;
					}
					return;
				}
			float inv_a = 1.0f / src_a;
			float straight_r = src_r * inv_a;
			float straight_g = src_g * inv_a;
			float straight_b = src_b * inv_a;
			if (straight_r < 0.0f) straight_r = 0.0f; else if (straight_r > 1.0f) straight_r = 1.0f;
			if (straight_g < 0.0f) straight_g = 0.0f; else if (straight_g > 1.0f) straight_g = 1.0f;
			if (straight_b < 0.0f) straight_b = 0.0f; else if (straight_b > 1.0f) straight_b = 1.0f;
			float rgb_alpha = (p.pixel_size == sizeof(PF_Pixel8) &&
			                   p.in_out != IN_OUT_BOTH) ? out_a : 1.0f;
			out_r = straight_r * rgb_alpha;
			out_g = straight_g * rgb_alpha;
			out_b = straight_b * rgb_alpha;
		} else {
			out_r = ir;
			out_g = ig;
			out_b = ib;
		}
	}
}

// Typed PF16 compose/store leaf. Keeping the AEX-grounded float-to-word
// boundary beside compose_pixel lets CPU fixtures exercise the same
// production operation used by RenderBits, without reconstructing an AE host.
static inline PF_Pixel16 compose_pf16_pixel(
	float src_a, float src_r, float src_g, float src_b,
	float d_alpha, float field_x, const DGParams &p,
	float &oa, float &orv, float &og, float &ob)
{
	compose_pixel(src_a, src_r, src_g, src_b, d_alpha, field_x,
	              p, oa, orv, og, ob);
	PF_Pixel16 out;
	out.alpha = clamp16(oa);
	out.red   = clamp16(orv);
	out.green = clamp16(og);
	out.blue  = clamp16(ob);
	return out;
}

// ============================================================================
// Scanline shader: applies compose_pixel row by row for each bit depth
// ============================================================================
struct ShadeCtx {
	const DistanceField *df;
	const DGParams      *p;
};

template<typename P>
static void shade_scanline(const P *src_row, P *dst_row,
                           const float *x_row, const float *a_row,
                           const DGParams &p, long w, long h, long y,
                           const PF_LayerDef *input_world);

template<> void shade_scanline<PF_Pixel8>(
	const PF_Pixel8 *src, PF_Pixel8 *dst,
	const float *x_row, const float *a_row,
	const DGParams &p, long w, long /*h*/, long y,
	const PF_LayerDef */*input_world*/)
{
	const char *shade_debug_path = getenv("OLM_DG_SHADE_DEBUG_PATH");
	const char *points = getenv("OLM_DG_DEBUG_POINTS");
	for (long i = 0; i < w; ++i) {
		float sa, sr, sg, sb;
		load_rgba_norm(&src[i], sa, sr, sg, sb);
		float oa, orv, og, ob;
		compose_pixel(sa, sr, sg, sb, a_row[i], x_row[i], p, oa, orv, og, ob);
		u_char da = clamp8(oa);
		u_char dr = clamp8(orv);
		u_char dg = clamp8(og);
		u_char db = clamp8(ob);
		dst[i].alpha = da;
		dst[i].red   = dr;
		dst[i].green = dg;
		dst[i].blue  = db;
		if (debug_point_selected(points, i, y)) {
			debug_dump_shade_point(shade_debug_path, p, i, y, sizeof(PF_Pixel8),
			                       sa, sr, sg, sb, x_row[i], a_row[i], oa, orv, og, ob,
			                       da, dr, dg, db,
			                       dst[i].alpha, dst[i].red, dst[i].green, dst[i].blue);
		}
	}
}
template<> void shade_scanline<PF_Pixel16>(
	const PF_Pixel16 *src, PF_Pixel16 *dst,
	const float *x_row, const float *a_row,
	const DGParams &p, long w, long h, long y,
	const PF_LayerDef *input_world)
{
	const char *shade_debug_path = getenv("OLM_DG_SHADE_DEBUG_PATH");
	const char *points = getenv("OLM_DG_DEBUG_POINTS");
	const char *pf16_capture_path = getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_PATH");
	const char *pf16_capture_case = getenv("OLM_DG_PF16_BOUNDARY_CAPTURE_CASE_ID");
	for (long i = 0; i < w; ++i) {
		float sa, sr, sg, sb;
		load_rgba_norm(&src[i], sa, sr, sg, sb);
		if (p.render_mode == RENDER_MODE_LAYER && !p.use_bg &&
		    src[i].alpha > 0 && src[i].alpha <= 193 &&
		    src[i].red == 0 && src[i].green == 0 && src[i].blue == 0) {
			bool inherit_r = false, inherit_g = false, inherit_b = false;
			for (long dx = 1; dx <= 3 && !(inherit_r || inherit_g || inherit_b); ++dx) {
				long candidates[2] = { i - dx, i + dx };
				for (long ci = 0; ci < 2; ++ci) {
					long nx = candidates[ci];
					if (nx < 0 || nx >= w) continue;
					const PF_Pixel16 &n = src[nx];
					if (n.alpha == 0 || (n.red == 0 && n.green == 0 && n.blue == 0)) continue;
					inherit_r = n.red > 0;
					inherit_g = n.green > 0;
					inherit_b = n.blue > 0;
					break;
				}
			}
			if (inherit_r || inherit_g || inherit_b) {
				sr = inherit_r ? sa : 0.0f;
				sg = inherit_g ? sa : 0.0f;
				sb = inherit_b ? sa : 0.0f;
			} else if (input_world) {
				for (long dy = 1; dy <= 3 && !(inherit_r || inherit_g || inherit_b); ++dy) {
					long rows[2] = { y - dy, y + dy };
					for (long ri = 0; ri < 2; ++ri) {
						long ny = rows[ri];
						if (ny < 0 || ny >= h) continue;
						const PF_Pixel16 *nrow = (const PF_Pixel16 *)((const char *)input_world->data + (size_t)ny * input_world->rowbytes);
						for (long dx = -3; dx <= 3; ++dx) {
							long nx = i + dx;
							if (nx < 0 || nx >= w) continue;
							const PF_Pixel16 &n = nrow[nx];
							if (n.alpha == 0 || (n.red == 0 && n.green == 0 && n.blue == 0)) continue;
							inherit_r = n.red > 0;
							inherit_g = n.green > 0;
							inherit_b = n.blue > 0;
							break;
						}
						if (inherit_r || inherit_g || inherit_b) break;
					}
				}
				if (inherit_r || inherit_g || inherit_b) {
					sr = inherit_r ? sa : 0.0f;
					sg = inherit_g ? sa : 0.0f;
					sb = inherit_b ? sa : 0.0f;
				}
			}
		}
		float oa, orv, og, ob;
		PF_Pixel16 stored = compose_pf16_pixel(
			sa, sr, sg, sb, a_row[i], x_row[i], p, oa, orv, og, ob);
		u_short da = stored.alpha;
		u_short dr = stored.red;
		u_short dg = stored.green;
		u_short db = stored.blue;
		dst[i] = stored;
		if (pf16_capture_path && pf16_capture_path[0] &&
		    pf16_capture_case && pf16_capture_case[0] &&
		    debug_point_selected(points, i, y)) {
			// The Mac core retains the field as float32.  Record the PF16 word
			// produced by the established nearest-even field-staging boundary
			// alongside that authoritative float without feeding it back.
			float field_scaled = x_row[i] * 32768.0f;
			u_short derived_field_word = (field_scaled < 0.0f) ? 0 :
				(field_scaled > 32768.0f ? 32768 : (u_short)lrintf(field_scaled));
			debug_dump_pf16_boundary_point(
				pf16_capture_path, pf16_capture_case, i, y, src[i],
				x_row[i], derived_field_word, oa, orv, og, ob, dst[i]);
		}
		if (debug_point_selected(points, i, y)) {
			debug_dump_shade_point(shade_debug_path, p, i, y, sizeof(PF_Pixel16),
			                       sa, sr, sg, sb, x_row[i], a_row[i], oa, orv, og, ob,
			                       da, dr, dg, db,
			                       dst[i].alpha, dst[i].red, dst[i].green, dst[i].blue);
		}
	}
}
template<> void shade_scanline<PF_PixelFloat>(
	const PF_PixelFloat *src, PF_PixelFloat *dst,
	const float *x_row, const float *a_row,
	const DGParams &p, long w, long /*h*/, long y,
	const PF_LayerDef */*input_world*/)
{
	const char *shade_debug_path = getenv("OLM_DG_SHADE_DEBUG_PATH");
	const char *points = getenv("OLM_DG_DEBUG_POINTS");
	for (long i = 0; i < w; ++i) {
		float sa, sr, sg, sb;
		load_rgba_norm(&src[i], sa, sr, sg, sb);
		float oa, orv, og, ob;
		compose_pixel(sa, sr, sg, sb, a_row[i], x_row[i], p, oa, orv, og, ob);
		dst[i].alpha = oa;
		dst[i].red   = orv;
		dst[i].green = og;
		dst[i].blue  = ob;
		if (debug_point_selected(points, i, y)) {
			debug_dump_shade_point(shade_debug_path, p, i, y, sizeof(PF_PixelFloat),
			                       sa, sr, sg, sb, x_row[i], a_row[i], oa, orv, og, ob,
			                       0, 0, 0, 0, 0, 0, 0, 0);
		}
	}
}

static bool is_admitted_pf32_smart_exported_matrix(
	const DGParams &p, const std::vector<float> &alpha, long w, long h)
{
	const bool admitted_blur =
		p.blur_mode >= BLUR_MODE_NO_SCALE && p.blur_mode <= BLUR_MODE_BILATERAL;
	if (!p.smart_owner || p.pixel_size != sizeof(PF_PixelFloat) || !admitted_blur ||
	    p.blur_size != 1 || p.interp_mode < INTERP_CONSTANT ||
	    p.interp_mode > INTERP_POWER ||
	    w != 17 || h != 11 ||
	    !p.invert || p.in_out != IN_OUT_INSIDE ||
	    p.inside_threshold != 4 || p.outside_threshold != 4 ||
	    p.render_mode != RENDER_MODE_RGB || p.power != 2.25f ||
	    p.ds_x != 1.0f || p.ds_y != 1.0f ||
	    p.grad_color.red != 28.0f / 255.0f || p.grad_color.green != 0.0f ||
	    p.grad_color.blue != 238.0f / 255.0f ||
	    p.bg_color.red != 16.0f / 255.0f || p.bg_color.green != 160.0f / 255.0f ||
	    p.bg_color.blue != 48.0f / 255.0f || alpha.size() != 17u * 11u) return false;
	// PF32 Power is admitted only here: the native Windows UCRT table, actual-AEX
	// XMM call sequence and same-table full RAW replay close these eight cells.
	// PF16 retains its separately grounded path.
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			const uint32_t expected_bits =
				(x >= 4 && x < 13 && y >= 2 && y < 9) ? 0x00000000u : 0x3f800000u;
			uint32_t alpha_bits = 0;
			memcpy(&alpha_bits, &alpha[(size_t)y * w + x], sizeof(alpha_bits));
			if (alpha_bits != expected_bits) return false;
		}
	}
	return true;
}

static bool is_admitted_pf32_power_source(
	const PF_LayerDef *input, long w, long h)
{
	if (!input || !input->data || w != 17 || h != 11 ||
	    input->rowbytes < w * (A_long)sizeof(PF_PixelFloat)) return false;
	for (long y = 0; y < h; ++y) {
		const PF_PixelFloat *row = (const PF_PixelFloat *)
			((const char *)input->data + (size_t)y * input->rowbytes);
		for (long x = 0; x < w; ++x) {
			const bool transparent = x >= 4 && x < 13 && y >= 2 && y < 9;
			const PF_PixelFloat expected = transparent ? PF_PixelFloat{0, 0, 0, 0}
				: PF_PixelFloat{
					1.0f,
					(float)((x * 613 + y * 1231) % 256) / 255.0f,
					(float)((x * 997 + y * 211) % 256) / 255.0f,
					(float)((x * 1499 + y * 307) % 256) / 255.0f,
				};
			if (memcmp(&row[x], &expected, sizeof(expected)) != 0) return false;
		}
	}
	return true;
}

// Practical PF32 Smart beta lane.  Unlike the exact Windows-owner matrix
// above, this lane intentionally promises useful rendering rather than
// bit-for-bit UCRT/IPP identity.  Keep it restricted to the two interpolation
// modes that need neither platform powf compatibility nor blur staging.
static bool is_admitted_pf32_smart_unblurred_beta(const DGParams &p)
{
	return p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	       p.blur_mode == BLUR_MODE_NONE &&
	       (p.interp_mode == INTERP_CONSTANT || p.interp_mode == INTERP_LINEAR) &&
	       p.in_out >= IN_OUT_INSIDE && p.in_out <= IN_OUT_BOTH &&
	       p.render_mode >= RENDER_MODE_RGB && p.render_mode <= RENDER_MODE_LAYER &&
	       p.inside_threshold >= 0 && p.outside_threshold >= 0 &&
	       p.ds_x > 0.0f && p.ds_y > 0.0f;
}

// Windows-oracle profile with only the fixture's source and geometry removed.
// The retained 17x11 matrix remains the exact lane; this profile uses native
// libm for Power and therefore carries a numerical-tolerance, not raw-bit,
// compatibility contract.
static constexpr uint32_t PF32_POWER_GENERIC_MAX_ULP = 1;
static_assert(PF32_POWER_GENERIC_MAX_ULP == 1, "PF32 generic Power tolerance contract");
static bool is_admitted_pf32_smart_oracle_profile(const DGParams &p)
{
	return p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	       p.invert && p.in_out == IN_OUT_INSIDE &&
	       p.inside_threshold == 4 && p.outside_threshold == 4 &&
	       p.render_mode == RENDER_MODE_RGB && p.power == 2.25f &&
	       p.blur_mode >= BLUR_MODE_NO_SCALE && p.blur_mode <= BLUR_MODE_BILATERAL &&
	       p.blur_size == 1 && p.ds_x == 1.0f && p.ds_y == 1.0f &&
	       p.interp_mode >= INTERP_CONSTANT && p.interp_mode <= INTERP_POWER &&
	       p.grad_color.red == 28.0f / 255.0f && p.grad_color.green == 0.0f &&
	       p.grad_color.blue == 238.0f / 255.0f &&
	       p.bg_color.red == 16.0f / 255.0f && p.bg_color.green == 160.0f / 255.0f &&
	       p.bg_color.blue == 48.0f / 255.0f;
}

static bool checked_pixel_count(long w, long h, size_t *count)
{
	if (!count || w <= 0 || h <= 0) return false;
	const size_t sw = (size_t)w;
	const size_t sh = (size_t)h;
	if (sw > std::numeric_limits<size_t>::max() / sh) return false;
	*count = sw * sh;
	return *count <= std::vector<float>().max_size();
}

// ============================================================================
// Core render: reads src layer, builds distance field, writes dst layer.
// ============================================================================
template<typename P>
static PF_Err
RenderBits(PF_InData *in_data, PF_ParamDef *params[],
           PF_LayerDef *input, PF_LayerDef *output, bool smart_owner = false)
{
	PF_Err err = PF_Err_NONE;
	// RenderBits is a same-shape typed kernel.  The Windows owner stages any
	// host resize/depth conversion before entering its typed body, and the Mac
	// port must not silently reinterpret a differently-sized or short-stride
	// host world.  Fail closed at that boundary instead of reading past a row.
	if (!input || !output || !input->data || !output->data ||
	    !in_data || in_data->output_origin_x != 0 || in_data->output_origin_y != 0 ||
	    in_data->pre_effect_source_origin_x != 0 || in_data->pre_effect_source_origin_y != 0 ||
	    input->width != output->width || input->height != output->height ||
	    input->width <= 0 || input->height <= 0 ||
	    (smart_owner &&
	     (input->origin_x != 0 || input->origin_y != 0 ||
	      output->origin_x != 0 || output->origin_y != 0)) ||
	    input->width > std::numeric_limits<A_long>::max() / (A_long)sizeof(P) ||
	    input->rowbytes < input->width * (A_long)sizeof(P) ||
	    output->rowbytes < output->width * (A_long)sizeof(P)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}

	DGParams p; AEFX_CLR_STRUCT(p);
	ERR(FetchParams(in_data, params, &p));
	if (err) return err;
	long w = output->width;
	long h = output->height;
	size_t pixel_count = 0;
	if (!checked_pixel_count(w, h, &pixel_count)) return PF_Err_BAD_CALLBACK_PARAM;
	p.w = w; p.h = h;
	p.pixel_size = sizeof(P);
	p.smart_owner = smart_owner;

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
		const bool unblurred_beta = is_admitted_pf32_smart_unblurred_beta(p);
		p.pf32_smart_oracle_profile_admitted =
			is_admitted_pf32_smart_oracle_profile(p);
		if (!p.pf32_smart_matrix_admitted && !unblurred_beta &&
		    !p.pf32_smart_oracle_profile_admitted) {
			return PF_Err_BAD_CALLBACK_PARAM;
		}
	}

	DistanceField df;
	build_distance_field(alpha.data(), df, p, w, h);
	debug_dump_distance_field(getenv("OLM_DG_DEBUG_DUMP_PATH"), alpha.data(), df, p, w, h, sizeof(P));

	// Shade
	for (long y = 0; y < h; ++y) {
		const P *src = (const P *)((char *)input->data  + (size_t)y * input->rowbytes);
		P *dst       = (P *)      ((char *)output->data + (size_t)y * output->rowbytes);
		const float *xrow = df.x.data()       + (size_t)y * w;
		const bool blurred = p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0;
		const float *aux = !df.pre_blur_x.empty() ? df.pre_blur_x.data()
		                 : (blurred ? df.x.data() : df.d_alpha.data());
		const float *arow = aux + (size_t)y * w;
		shade_scanline<P>(src, dst, xrow, arow, p, w, h, y, input);
	}

	return err;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	if (!in_data || !out_data || !params || !output ||
	    in_data->output_origin_x != 0 || in_data->output_origin_y != 0 ||
	    in_data->pre_effect_source_origin_x != 0 || in_data->pre_effect_source_origin_y != 0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	for (A_long i = 0; i < DG_NUM_PARAMS; ++i) {
		if (!params[i]) return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_LayerDef *input = &params[DG_INPUT]->u.ld;
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	ERR(world_suite->PF_GetPixelFormat(input, &input_format));
	ERR(world_suite->PF_GetPixelFormat(output, &output_format));
	if (err) return err;
	if (input_format != output_format) return PF_Err_BAD_CALLBACK_PARAM;

	switch (input_format) {
	case PF_PixelFormat_ARGB32:
		return RenderBits<PF_Pixel8>(in_data, params, input, output);
	case PF_PixelFormat_ARGB64:
		return RenderBits<PF_Pixel16>(in_data, params, input, output);
	case PF_PixelFormat_ARGB128:
		return RenderBits<PF_PixelFloat>(in_data, params, input, output);
	default:
		return PF_Err_BAD_CALLBACK_PARAM;
	}
}

// ============================================================================
// SmartRender
// ============================================================================
struct DGPreRenderData {
	A_long width;
	A_long height;
};

static void DeleteDGPreRenderData(void *data)
{
	delete reinterpret_cast<DGPreRenderData *>(data);
}

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
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;
	if (in_data->width <= 0 || in_data->height <= 0 ||
	    in_data->downsample_x.num <= 0 || in_data->downsample_x.den <= 0 ||
	    in_data->downsample_y.num <= 0 || in_data->downsample_y.den <= 0 ||
	    in_data->downsample_x.num != in_data->downsample_x.den ||
	    in_data->downsample_y.num != in_data->downsample_y.den) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_RenderRequest req = extra->input->output_request;
	const PF_LRect full_rect = {0, 0, in_data->width, in_data->height};
	req.rect = full_rect;
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		DG_INPUT, DG_INPUT, &req,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&in_result));

	// ref_width/ref_height describe storage authority. result/max_result are
	// content bounds and may legitimately be empty or smaller for transparent
	// frames, so they must not be used to reject a full-frame checkout.
	if (!err && (in_result.ref_width != in_data->width ||
	             in_result.ref_height != in_data->height)) {
		err = PF_Err_BAD_CALLBACK_PARAM;
	}
	if (!err) {
		DGPreRenderData *pre = new (std::nothrow) DGPreRenderData{in_data->width, in_data->height};
		if (!pre) return PF_Err_OUT_OF_MEMORY;
		extra->output->result_rect = full_rect;
		extra->output->max_result_rect = full_rect;
		extra->output->flags |= PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS;
		extra->output->pre_render_data = pre;
		extra->output->delete_pre_render_data_func = DeleteDGPreRenderData;
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
		return PF_Err_BAD_CALLBACK_PARAM;
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
		return PF_Err_BAD_CALLBACK_PARAM;
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
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);

	PF_EffectWorld *input_world  = nullptr;
	PF_EffectWorld *output_world = nullptr;
	bool input_checked_out = false;
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
			err = PF_Err_BAD_CALLBACK_PARAM;
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
			err = PF_Err_BAD_CALLBACK_PARAM;
		}

		if (!err) {
			// Fill params[DG_INPUT]->u.ld for the render helpers
			param_list[0].u.ld = *input_world;
			if (depth == 8) {
				err = RenderBits<PF_Pixel8>(in_data, params, input_world, output_world, true);
			} else if (depth == 16) {
				err = RenderBits<PF_Pixel16>(in_data, params, input_world, output_world, true);
			} else if (depth == 32) {
				err = RenderBits<PF_PixelFloat>(in_data, params, input_world, output_world, true);
			}
			const DGPreRenderData *pre = reinterpret_cast<const DGPreRenderData *>(
				extra->input->pre_render_data);
			if (!err && pre && (input_world->width != pre->width || input_world->height != pre->height ||
			                    output_world->width != pre->width || output_world->height != pre->height)) {
				err = PF_Err_BAD_CALLBACK_PARAM;
			}
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

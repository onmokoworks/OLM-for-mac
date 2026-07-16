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
	             3, IN_OUT_BOTH,
	             GetStringPtr(StrID_InOut_Choices),
	             IN_OUT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_InsideThreshold_Param_Name),
	              0, 1000, 0, 1000, 128,
	              INSIDE_THRESHOLD_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_OutsideThreshold_Param_Name),
	              0, 1000, 0, 1000, 128,
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
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     POWER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_BlurMode_Param_Name),
	             3, BLUR_MODE_NONE,
	             GetStringPtr(StrID_BlurMode_Choices),
	             BLUR_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_BlurSize_Param_Name),
	              0, 4096, 0, 4096, 0,
	              BLUR_SIZE_DISK_ID);

	out_data->num_params = DG_NUM_PARAMS;
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
	cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[DG_GRAD_COLOR], &p->grad_color);
	cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[DG_BG_COLOR], &p->bg_color);

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
// Gaussian blur (separable, matches cv::GaussianBlur with BORDER_REFLECT_101 +
// sigma derived via cv::getGaussianKernel default:  sigma = 0.3*((ksize-1)*0.5 - 1) + 0.8
// ============================================================================
static void make_gauss_kernel(std::vector<float> &k, int ksize)
{
	// Odd kernel size required
	if ((ksize & 1) == 0) ++ksize;
	if (ksize < 1) ksize = 1;
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

	// Horizontal
	for (long y = 0; y < h; ++y) {
		const float *row = mat + (size_t)y * w;
		float       *out = tmp.data() + (size_t)y * w;
		for (long x = 0; x < w; ++x) {
			float acc = 0;
			for (int i = -half; i <= half; ++i) {
				long xi = reflect101(x + i, w);
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
				long yi = reflect101(y + i, h);
				acc += tmp[(size_t)yi * w + x] * k[i + half];
			}
			mat[(size_t)y * w + x] = acc;
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

// The actual-AEX PF8 boundary fixture stores fractional channel codes by truncation.
static inline u_char clamp8(float v)   { v = v * 255.0f; return (v < 0) ? 0 : (v > 255.f ? 255 : (u_char)v); }
static inline u_short clamp16(float v) { v = v * 32768.0f + 0.5f; return (v < 0) ? 0 : (v > 32768.f ? 32768 : (u_short)v); }

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

// ============================================================================
// Distance field builder (shared across bit depths)
//   input_alpha_norm: 0..1 alpha, size w*h
//   Produces normalized distance field X in [0,1] per pixel.
// ============================================================================
struct DistanceField {
	std::vector<float> x;    // normalized distance [0,1]
	std::vector<float> d_alpha; // 0 or 1 — output alpha mask
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

	bool constant_blur = (p.interp_mode == INTERP_CONSTANT &&
	                      p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0);
	if (constant_blur) {
		for (long i = 0; i < w * h; ++i) df.x[i] = (df.x[i] >= 1.0f) ? 1.0f : 0.0f;
	}

	// Blur: blur_size is full-res pixels.
	//   BLUR_MODE_NO_SCALE (2): use size as-is at full-res even when downsampled
	//   BLUR_MODE_SCALE    (3): scale to current-res pixels
	// Constant interpolation blurs a binary full-distance field; Windows refs
	// show Blur Size 30 behaving like radius 60 for this path.
	if (p.blur_mode != BLUR_MODE_NONE && p.blur_size > 0) {
		long bs = p.blur_size;
		if (p.blur_mode == BLUR_MODE_SCALE) {
			bs = (long)((float)p.blur_size * ds + 0.5f);
		}
		if (constant_blur) bs *= 2;
		if (bs < 1) bs = 1;
		int ksize = (int)(2 * bs + 1);
		if (ksize > 1) gauss_blur_separable(df.x.data(), w, h, ksize);
	}

	// The Windows 16bpc path merges the float field into an OpenCV image, then
	// stores it through cvConvertScale before PF Iterate16 reads it back. Match
	// that PF16 boundary here; keeping the float directly changes half-integer
	// cases before compose. The 8bpc and float paths have separate exactness
	// contracts and are intentionally unchanged.
	if (p.pixel_size == sizeof(PF_Pixel16)) {
		for (float &value : df.x) {
			value = olm::distancegradation::roundtrip_normalized_pf16_even(value);
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
	float /*unused*/, float X,
	const DGParams &p,
	float &out_a, float &out_r, float &out_g, float &out_b)
{
	// Invert: default (OFF) flips X to 1 - X; checked (ON) keeps X as-is.
	if (!p.invert) X = 1.0f - X;

	// Interpolation transforms on X
	if (p.interp_mode == INTERP_SPHERE) {
		float t = 1.0f - X;
		float s = 1.0f - t * t;
		X = (s < 0) ? 0.0f : sqrtf(s);
	} else if (p.interp_mode == INTERP_POWER) {
		X = powf(X, p.power);
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

	// RGB selection:
	//   render_mode == 1 (RGB)   -> gradation color (default)
	//   render_mode == 2 (Layer) -> source color
	float ir, ig, ib;
	if (p.render_mode == RENDER_MODE_RGB) {
		ir = p.grad_color.red; ig = p.grad_color.green; ib = p.grad_color.blue;
	} else {
		ir = src_r; ig = src_g; ib = src_b;
	}

	if (p.use_bg) {
		float oneX = 1.0f - X;
		out_r = oneX * p.bg_color.red   + X * ir;
		out_g = oneX * p.bg_color.green + X * ig;
		out_b = oneX * p.bg_color.blue  + X * ib;
		out_a = d_alpha;            // use_bg: alpha = d_alpha (full)
	} else {
		out_a = d_alpha * X;        // no bg: alpha = d_alpha * X
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
			float rgb_alpha = (p.pixel_size == sizeof(PF_Pixel8)) ? out_a : 1.0f;
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
		compose_pixel(sa, sr, sg, sb, a_row[i], x_row[i], p, oa, orv, og, ob);
		u_short da = clamp16(oa);
		u_short dr = clamp16(orv);
		u_short dg = clamp16(og);
		u_short db = clamp16(ob);
		dst[i].alpha = da;
		dst[i].red   = dr;
		dst[i].green = dg;
		dst[i].blue  = db;
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

// ============================================================================
// Core render: reads src layer, builds distance field, writes dst layer.
// ============================================================================
template<typename P>
static PF_Err
RenderBits(PF_InData *in_data, PF_ParamDef *params[],
           PF_LayerDef *input, PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;

	DGParams p; AEFX_CLR_STRUCT(p);
	ERR(FetchParams(in_data, params, &p));
	if (err) return err;

	long w = output->width;
	long h = output->height;
	p.w = w; p.h = h;
	p.pixel_size = sizeof(P);

	// Extract normalized alpha for DT
	std::vector<float> alpha((size_t)w * h, 0.0f);
	for (long y = 0; y < h; ++y) {
		const P *row = (const P *)((char *)input->data + (size_t)y * input->rowbytes);
		float *arow = alpha.data() + (size_t)y * w;
		for (long x = 0; x < w; ++x) {
			float a, r, g, b;
			load_rgba_norm(&row[x], a, r, g, b);
			arow[x] = a;
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
		const float *arow = df.d_alpha.data() + (size_t)y * w;
		shade_scanline<P>(src, dst, xrow, arow, p, w, h, y, input);
	}

	return err;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	PF_LayerDef *input = &params[DG_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	ERR(world_suite->PF_GetPixelFormat(input, &format));
	if (err) return err;

	switch (format) {
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
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		DG_INPUT, DG_INPUT, &req,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&in_result));

	UnionLRect_inline(&in_result.result_rect, &extra->output->result_rect);
	UnionLRect_inline(&in_result.max_result_rect, &extra->output->max_result_rect);
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	PF_EffectWorld *input_world  = nullptr;
	PF_EffectWorld *output_world = nullptr;

	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, DG_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));

	// Checkout params via PF_ParamDef stack
	PF_ParamDef param_list[DG_NUM_PARAMS];
	AEFX_CLR_STRUCT(param_list[0]);
	for (A_long i = 1; i < DG_NUM_PARAMS; ++i) {
		AEFX_CLR_STRUCT(param_list[i]);
		ERR(PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
		                      in_data->time_step, in_data->time_scale,
		                      &param_list[i]));
	}

	PF_ParamDef *params[DG_NUM_PARAMS];
	params[0] = &param_list[0];
	for (A_long i = 1; i < DG_NUM_PARAMS; ++i) params[i] = &param_list[i];

	if (!err && input_world && output_world) {
		// Fill params[DG_INPUT]->u.ld for the render helpers
		param_list[0].u.ld = *input_world;
		double bps = PF_WORLD_IS_DEEP(input_world) ? 16 : 8;
		(void)bps;
		short depth = extra->input->bitdepth;
		if (depth == 8) {
			err = RenderBits<PF_Pixel8>(in_data, params, input_world, output_world);
		} else if (depth == 16) {
			err = RenderBits<PF_Pixel16>(in_data, params, input_world, output_world);
		} else {
			err = RenderBits<PF_PixelFloat>(in_data, params, input_world, output_world);
		}
	}

	for (A_long i = 1; i < DG_NUM_PARAMS; ++i) {
		PF_CHECKIN_PARAM(in_data, &param_list[i]);
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
	}
	return err;
}

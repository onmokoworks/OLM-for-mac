#include "OLMKiraKira.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

namespace {

constexpr float kFd90RayEpsilon = 0.001f;

struct FloatRGBA {
	float r = 0.0f;
	float g = 0.0f;
	float b = 0.0f;
	float a = 0.0f;
};

struct KiraKiraDebugPoint {
	A_long x = 0;
	A_long y = 0;
};

struct KiraKiraDebugConfig {
	const char *dump_path = nullptr;
	std::vector<KiraKiraDebugPoint> points;
};

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

static float Clamp01(float v)
{
	return std::min(1.0f, std::max(0.0f, v));
}

static std::vector<KiraKiraDebugPoint> ParseKiraKiraDebugPoints(const char *spec)
{
	std::vector<KiraKiraDebugPoint> points;
	if (!spec || !*spec) return points;
	const char *p = spec;
	while (*p) {
		int x = -1;
		int y = -1;
		int consumed = 0;
		if (std::sscanf(p, "%d,%d%n", &x, &y, &consumed) == 2 && consumed > 0) {
			points.push_back({ (A_long)x, (A_long)y });
			p += consumed;
			while (*p == ';' || *p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') ++p;
		} else {
			break;
		}
	}
	return points;
}

static KiraKiraDebugConfig LoadKiraKiraDebugConfig()
{
	KiraKiraDebugConfig config;
	config.dump_path = std::getenv("OLMKIRAKIRA_DEBUG_DUMP_PATH");
	config.points = ParseKiraKiraDebugPoints(std::getenv("OLMKIRAKIRA_DEBUG_POINTS"));
	if (!config.dump_path || !*config.dump_path || config.points.empty()) {
		config.dump_path = nullptr;
		config.points.clear();
	}
	return config;
}

static bool KiraKiraDebugHasPoint(const KiraKiraDebugConfig &debug, A_long x, A_long y)
{
	for (const KiraKiraDebugPoint &point : debug.points) {
		if (point.x == x && point.y == y) return true;
	}
	return false;
}

static void KiraKiraDebugDumpPoint(
	const KiraKiraDebugConfig &debug,
	short bitdepth,
	A_long width,
	A_long height,
	A_long x,
	A_long y,
	const FloatRGBA &src,
	const FloatRGBA &glow_normalized,
	float glow_alpha_after_opacity,
	const FloatRGBA &out_prequantized)
{
	if (!debug.dump_path || !KiraKiraDebugHasPoint(debug, x, y)) return;
	FILE *fp = std::fopen(debug.dump_path, "a");
	if (!fp) return;
	const A_u_char out8r = static_cast<A_u_char>(std::lround(Clamp01(out_prequantized.r) * 255.0f));
	const A_u_char out8g = static_cast<A_u_char>(std::lround(Clamp01(out_prequantized.g) * 255.0f));
	const A_u_char out8b = static_cast<A_u_char>(std::lround(Clamp01(out_prequantized.b) * 255.0f));
	const A_u_char out8a = static_cast<A_u_char>(std::lround(Clamp01(out_prequantized.a) * 255.0f));
	std::fprintf(
		fp,
		"OLMKIRAKIRA_DEBUG_POINT bitdepth=%d w=%d h=%d x=%d y=%d "
		"src=(%.9g,%.9g,%.9g,%.9g) src_hex=(%a,%a,%a,%a) "
		"glow_norm=(%.9g,%.9g,%.9g,%.9g) glow_norm_hex=(%a,%a,%a,%a) "
		"glow_alpha_after_opacity=%.9g glow_alpha_after_opacity_hex=%a "
		"out_prequantized=(%.9g,%.9g,%.9g,%.9g) out_prequantized_hex=(%a,%a,%a,%a) "
		"out_u8=(%u,%u,%u,%u)\n",
		(int)bitdepth,
		(int)width,
		(int)height,
		(int)x,
		(int)y,
		src.r, src.g, src.b, src.a,
		(double)src.r, (double)src.g, (double)src.b, (double)src.a,
		glow_normalized.r, glow_normalized.g, glow_normalized.b, glow_normalized.a,
		(double)glow_normalized.r, (double)glow_normalized.g, (double)glow_normalized.b, (double)glow_normalized.a,
		glow_alpha_after_opacity,
		(double)glow_alpha_after_opacity,
		out_prequantized.r, out_prequantized.g, out_prequantized.b, out_prequantized.a,
		(double)out_prequantized.r, (double)out_prequantized.g, (double)out_prequantized.b, (double)out_prequantized.a,
		(unsigned int)out8r,
		(unsigned int)out8g,
		(unsigned int)out8b,
		(unsigned int)out8a
	);
	std::fclose(fp);
}

static int Reflect101Index(int i, int n)
{
	if (n <= 1) return 0;
	while (i < 0 || i >= n) {
		if (i < 0) i = -i;
		if (i >= n) i = 2 * n - i - 2;
	}
	return i;
}

static A_long AexRotatedExtent(A_long major, A_long minor, double abs_major, double abs_minor)
{
	return std::max<A_long>(major + 4, (A_long)((double)major * abs_major + (double)minor * abs_minor + 4.0));
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
struct PixelTraits;

template <>
struct PixelTraits<PF_Pixel8> {
	static FloatRGBA Read(const PF_Pixel8 &p) {
		return {
			p.red / 255.0f,
			p.green / 255.0f,
			p.blue / 255.0f,
			p.alpha / 255.0f
		};
	}
	static PF_Pixel8 Write(const FloatRGBA &p) {
		PF_Pixel8 out;
		out.alpha = static_cast<A_u_char>(std::lround(Clamp01(p.a) * 255.0f));
		out.red   = static_cast<A_u_char>(std::lround(Clamp01(p.r) * 255.0f));
		out.green = static_cast<A_u_char>(std::lround(Clamp01(p.g) * 255.0f));
		out.blue  = static_cast<A_u_char>(std::lround(Clamp01(p.b) * 255.0f));
		return out;
	}
};

template <>
struct PixelTraits<PF_Pixel16> {
	static FloatRGBA Read(const PF_Pixel16 &p) {
		return {
			p.red / 65535.0f,
			p.green / 65535.0f,
			p.blue / 65535.0f,
			p.alpha / 65535.0f
		};
	}
	static PF_Pixel16 Write(const FloatRGBA &p) {
		PF_Pixel16 out;
		out.alpha = static_cast<A_u_short>(std::lround(Clamp01(p.a) * 65535.0f));
		out.red   = static_cast<A_u_short>(std::lround(Clamp01(p.r) * 65535.0f));
		out.green = static_cast<A_u_short>(std::lround(Clamp01(p.g) * 65535.0f));
		out.blue  = static_cast<A_u_short>(std::lround(Clamp01(p.b) * 65535.0f));
		return out;
	}
};

template <>
struct PixelTraits<PF_PixelFloat> {
	static FloatRGBA Read(const PF_PixelFloat &p) {
		return {p.red, p.green, p.blue, p.alpha};
	}
	static PF_PixelFloat Write(const FloatRGBA &p) {
		PF_PixelFloat out;
		out.alpha = Clamp01(p.a);
		out.red   = Clamp01(p.r);
		out.green = Clamp01(p.g);
		out.blue  = Clamp01(p.b);
		return out;
	}
};

static std::vector<float> DirectionBoxBlur(
	const std::vector<float> &input,
	A_long width,
	A_long height,
	A_long length,
	A_long dx,
	A_long dy,
	A_long passes)
{
	if (length <= 1) return input;
	std::vector<float> src = input;
	std::vector<float> dst(src.size());
	const A_long left = length / 2;
	const A_long right = length - left - 1;
	for (A_long pass = 0; pass < passes; ++pass) {
		std::fill(dst.begin(), dst.end(), 0.0f);
		for (A_long y = 0; y < height; ++y) {
			for (A_long x = 0; x < width; ++x) {
				double sum = 0.0;
				for (A_long k = -left; k <= right; ++k) {
					A_long sx = Reflect101Index((int)(x + dx * k), (int)width);
					A_long sy = Reflect101Index((int)(y + dy * k), (int)height);
					sum += src[(size_t)sy * width + sx];
				}
				dst[(size_t)y * width + x] = (float)(sum / (double)length);
			}
		}
		src.swap(dst);
	}
	return src;
}

static float SampleBilinearZero(const std::vector<float> &input, A_long width, A_long height, double x, double y)
{
	A_long x0 = (A_long)std::floor(x);
	A_long y0 = (A_long)std::floor(y);
	A_long x1 = x0 + 1;
	A_long y1 = y0 + 1;
	double tx = x - (double)x0;
	double ty = y - (double)y0;
	auto sample_zero = [&](A_long sx, A_long sy) -> float {
		if (sx < 0 || sy < 0 || sx >= width || sy >= height) return 0.0f;
		return input[(size_t)sy * width + sx];
	};
	float v00 = sample_zero(x0, y0);
	float v10 = sample_zero(x1, y0);
	float v01 = sample_zero(x0, y1);
	float v11 = sample_zero(x1, y1);
	double a = v00 * (1.0 - tx) + v10 * tx;
	double b = v01 * (1.0 - tx) + v11 * tx;
	return (float)(a * (1.0 - ty) + b * ty);
}

static std::vector<float> WarpGetRotDirect(
	const std::vector<float> &input,
	A_long src_width,
	A_long src_height,
	A_long dst_width,
	A_long dst_height,
	double center_x,
	double center_y,
	double angle_deg)
{
	const double pi = 3.14159265358979323846;
	const double rad = angle_deg * pi / 180.0;
	const double alpha = std::cos(rad);
	const double beta = std::sin(rad);
	const double m00 = alpha;
	const double m01 = beta;
	const double m02 = (1.0 - alpha) * center_x - beta * center_y;
	const double m10 = -beta;
	const double m11 = alpha;
	const double m12 = beta * center_x + (1.0 - alpha) * center_y;
	const double det = m00 * m11 - m01 * m10;
	std::vector<float> output((size_t)dst_width * dst_height);
	for (A_long y = 0; y < dst_height; ++y) {
		for (A_long x = 0; x < dst_width; ++x) {
			const double dx = (double)x - m02;
			const double dy = (double)y - m12;
			const double sx = (m11 * dx - m01 * dy) / det;
			const double sy = (-m10 * dx + m00 * dy) / det;
			output[(size_t)y * dst_width + x] = SampleBilinearZero(input, src_width, src_height, sx, sy);
		}
	}
	return output;
}

static std::vector<float> CopyCenteredRoi(
	const std::vector<float> &input,
	A_long src_width,
	A_long src_height,
	A_long dst_width,
	A_long dst_height)
{
	std::vector<float> output((size_t)dst_width * dst_height);
	const A_long x0 = (A_long)((float)src_width * 0.5f) - dst_width / 2;
	const A_long y0 = (A_long)((float)src_height * 0.5f) - dst_height / 2;
	for (A_long y = 0; y < dst_height; ++y) {
		const A_long sy = y + y0;
		if (sy < 0 || sy >= src_height) continue;
		for (A_long x = 0; x < dst_width; ++x) {
			const A_long sx = x + x0;
			if (sx < 0 || sx >= src_width) continue;
			output[(size_t)y * dst_width + x] = input[(size_t)sy * src_width + sx];
		}
	}
	return output;
}

static std::vector<float> RotatedAxisBoxBlur(
	const std::vector<float> &input,
	A_long width,
	A_long height,
	A_long length,
	double angle_deg,
	A_long passes)
{
	if (length <= 1) return input;
	const double pi = 3.14159265358979323846;
	const double rad = angle_deg * pi / 180.0;
	const double ac = std::abs(std::cos(rad));
	const double as = std::abs(std::sin(rad));
	const A_long rw = AexRotatedExtent(width, height, ac, as);
	const A_long rh = AexRotatedExtent(height, width, ac, as);
	const double temp_cx = (double)rw * 0.5;
	const double temp_cy = (double)rh * 0.5;
	std::vector<float> temp_a = CopyCenteredRoi(input, width, height, rw, rh);
	temp_a = WarpGetRotDirect(temp_a, rw, rh, rw, rh, temp_cx, temp_cy, angle_deg);
	std::vector<float> temp_b = DirectionBoxBlur(temp_a, rw, rh, length, 1, 0, passes);
	temp_b = WarpGetRotDirect(temp_b, rw, rh, rw, rh, temp_cx, temp_cy, -angle_deg);
	return CopyCenteredRoi(temp_b, rw, rh, width, height);
}

static void AddColoredUnion(
	std::vector<FloatRGBA> &glow,
	const std::vector<float> &amount,
	const PF_PixelFloat &color,
	double scale)
{
	const size_t pixels = glow.size();
	for (size_t i = 0; i < pixels; ++i) {
		if (amount[i] <= kFd90RayEpsilon) continue;
		float alpha = Clamp01((float)(amount[i] * scale) * color.alpha);
		glow[i].r += alpha * color.red;
		glow[i].g += alpha * color.green;
		glow[i].b += alpha * color.blue;
		glow[i].a = glow[i].a + alpha - glow[i].a * alpha;
	}
}

template <typename PixelT>
static std::vector<float> MakeSeed(PF_EffectWorld *input, const OLMKiraKiraInfo &info)
{
	const A_long w = input->width;
	const A_long h = input->height;
	std::vector<float> seed((size_t)w * h);
	const double exponent = std::max<PF_FpLong>(1.0e-6, info.strength_multiplier);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			FloatRGBA p = PixelTraits<PixelT>::Read(*PixelAtConst<PixelT>(input, x, y));
			float v = 0.0f;
			if (info.channel == 1) {
				v = (float)std::pow(p.a, exponent);
			} else if (info.channel == 2) {
				float luma = p.r * 0.299f + p.g * 0.587f + p.b * 0.114f;
				v = (float)std::pow(luma, exponent) * p.a;
			} else if (info.channel == 4) {
				v = (float)std::pow(std::max({p.r, p.g, p.b}), exponent) * p.a;
			} else {
				v = std::max({
					(float)std::pow(p.r, exponent),
					(float)std::pow(p.g, exponent),
					(float)std::pow(p.b, exponent)
				}) * p.a;
			}
			seed[(size_t)y * w + x] = v;
		}
	}
	return seed;
}

template <typename PixelT>
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMKiraKiraInfo &info, short bitdepth)
{
	const A_long w = output->width;
	const A_long h = output->height;
	if (w <= 0 || h <= 0 || input->width != w || input->height != h) return PF_Err_BAD_CALLBACK_PARAM;
	const KiraKiraDebugConfig debug = LoadKiraKiraDebugConfig();

	const PF_FpLong comp_width = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const double length_scale = comp_width > 0.0 ? (double)w / comp_width : 1.0;
	auto scaled_len = [&](A_long value) -> A_long {
		return std::max<A_long>(0, (A_long)std::lround((double)value * length_scale));
	};

	std::vector<float> seed = MakeSeed<PixelT>(input, info);
	const A_long passes = 3;
	const double glow_rotation = info.glow_rotation;
	const std::vector<float> zero_ray((size_t)w * h, 0.0f);
	auto make_ray = [&](A_long raw_len, double angle) -> std::vector<float> {
		const A_long len = scaled_len(raw_len);
		if (raw_len <= 0 || len <= 0) return zero_ray;
		return RotatedAxisBoxBlur(seed, w, h, len, angle, passes);
	};
	std::vector<float> vertical = make_ray(info.vertical_length, 90.0 + glow_rotation);
	std::vector<float> horizontal = make_ray(info.horizontal_length, glow_rotation);
	std::vector<float> diagonal = make_ray(info.diagonal_length, 45.0 + glow_rotation);
	std::vector<float> diagonal2 = make_ray(info.diagonal2_length, -45.0 + glow_rotation);

	const double gain_scale = 0.62;
	double scale = info.brightness_gain * gain_scale;
	if (info.strength_multiplier <= 1.0e-6) {
		scale = 127.0 / 255.0;
	}
	std::vector<FloatRGBA> glow((size_t)w * h);
	AddColoredUnion(glow, vertical, info.vertical_color, scale);
	AddColoredUnion(glow, horizontal, info.horizontal_color, scale);
	AddColoredUnion(glow, diagonal, info.diagonal_color, scale);
	AddColoredUnion(glow, diagonal2, info.diagonal2_color, scale);

	for (FloatRGBA &g : glow) {
		if (g.a > 1.0e-6f) {
			g.r /= g.a;
			g.g /= g.a;
			g.b /= g.a;
		}
	}

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const size_t idx = (size_t)y * w + x;
			FloatRGBA src = PixelTraits<PixelT>::Read(*PixelAtConst<PixelT>(input, x, y));
			float src_a = src.a * (float)info.source_opacity;
			float glow_a = Clamp01(glow[idx].a * (float)info.glow_opacity);
			const FloatRGBA glow_normalized = glow[idx];
			FloatRGBA out;
			out.r = 1.0f - (1.0f - src.r) * (1.0f - Clamp01(glow[idx].r * glow_a));
			out.g = 1.0f - (1.0f - src.g) * (1.0f - Clamp01(glow[idx].g * glow_a));
			out.b = 1.0f - (1.0f - src.b) * (1.0f - Clamp01(glow[idx].b * glow_a));
			out.a = src_a;
			KiraKiraDebugDumpPoint(debug, bitdepth, w, h, x, y, src, glow_normalized, glow_a, out);
			*PixelAt<PixelT>(output, x, y) = PixelTraits<PixelT>::Write(out);
		}
	}
	return PF_Err_NONE;
}

static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output, const OLMKiraKiraInfo &info, short bitdepth)
{
	if (bitdepth == 8) return RenderTyped<PF_Pixel8>(input, output, info, bitdepth);
	if (bitdepth == 16) return RenderTyped<PF_Pixel16>(input, output, info, bitdepth);
	if (bitdepth == 32) return RenderTyped<PF_PixelFloat>(input, output, info, bitdepth);
	return PF_Err_BAD_CALLBACK_PARAM;
}

static void CopyColorParam(PF_InData *in_data, PF_ParamDef *param, PF_PixelFloat *out)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();
	PF_PixelFloat color = {1.0f, 1.0f, 1.0f, 1.0f};
	if (cps) {
		cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref, param, &color);
	} else {
		color.alpha = param->u.cd.value.alpha / 255.0f;
		color.red = param->u.cd.value.red / 255.0f;
		color.green = param->u.cd.value.green / 255.0f;
		color.blue = param->u.cd.value.blue / 255.0f;
	}
	*out = color;
}

static void ReadRenderInfo(PF_InData *in_data, PF_ParamDef *params[], OLMKiraKiraInfo *info)
{
	AEFX_CLR_STRUCT(*info);
	info->glow_rotation = params[OLMKIRAKIRA_GLOW_ROTATION]->u.fs_d.value;
	info->brightness_gain = params[OLMKIRAKIRA_BRIGHTNESS_GAIN]->u.fs_d.value;
	info->vertical_length = params[OLMKIRAKIRA_VERTICAL_LENGTH]->u.sd.value;
	info->horizontal_length = params[OLMKIRAKIRA_HORIZONTAL_LENGTH]->u.sd.value;
	info->diagonal_length = params[OLMKIRAKIRA_DIAGONAL_LENGTH]->u.sd.value;
	info->diagonal2_length = params[OLMKIRAKIRA_DIAGONAL2_LENGTH]->u.sd.value;
	info->glow_opacity = params[OLMKIRAKIRA_GLOW_OPACITY]->u.sd.value / 100.0;
	info->channel = params[OLMKIRAKIRA_CHANNEL]->u.pd.value;
	info->blur_mode = params[OLMKIRAKIRA_BLUR_MODE]->u.pd.value;
	info->strength_multiplier = params[OLMKIRAKIRA_STRENGTH_MULTIPLIER]->u.sd.value / 100.0;
	info->source_opacity = params[OLMKIRAKIRA_SOURCE_OPACITY]->u.sd.value / 100.0;
	CopyColorParam(in_data, params[OLMKIRAKIRA_VERTICAL_COLOR], &info->vertical_color);
	CopyColorParam(in_data, params[OLMKIRAKIRA_HORIZONTAL_COLOR], &info->horizontal_color);
	CopyColorParam(in_data, params[OLMKIRAKIRA_DIAGONAL_COLOR], &info->diagonal_color);
	CopyColorParam(in_data, params[OLMKIRAKIRA_HIGHLIGHT_COLOR], &info->highlight_color);
	CopyColorParam(in_data, params[OLMKIRAKIRA_DIAGONAL2_COLOR], &info->diagonal2_color);
	info->vertical_use_ramp = params[OLMKIRAKIRA_VERTICAL_USE_RAMP]->u.bd.value;
	info->horizontal_use_ramp = params[OLMKIRAKIRA_HORIZONTAL_USE_RAMP]->u.bd.value;
	info->diagonal_use_ramp = params[OLMKIRAKIRA_DIAGONAL_USE_RAMP]->u.bd.value;
	info->highlight_use_ramp = params[OLMKIRAKIRA_HIGHLIGHT_USE_RAMP]->u.bd.value;
	info->diagonal2_use_ramp = params[OLMKIRAKIRA_DIAGONAL2_USE_RAMP]->u.bd.value;
	info->comp_width = params[OLMKIRAKIRA_INPUT]->u.ld.width;
}

static PF_Err CheckoutSmartInfo(PF_InData *in_data, OLMKiraKiraInfo *info)
{
	PF_Err err = PF_Err_NONE;
	auto checkout = [&](A_long index, PF_ParamDef *param) -> PF_Err {
		AEFX_CLR_STRUCT(*param);
		return PF_CHECKOUT_PARAM(in_data, index, in_data->current_time,
		                         in_data->time_step, in_data->time_scale, param);
	};

	AEFX_CLR_STRUCT(*info);
	PF_ParamDef p;
	ERR(checkout(OLMKIRAKIRA_GLOW_ROTATION, &p)); info->glow_rotation = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_BRIGHTNESS_GAIN, &p)); info->brightness_gain = p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_VERTICAL_LENGTH, &p)); info->vertical_length = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HORIZONTAL_LENGTH, &p)); info->horizontal_length = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL_LENGTH, &p)); info->diagonal_length = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_GLOW_OPACITY, &p)); info->glow_opacity = p.u.sd.value / 100.0; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_CHANNEL, &p)); info->channel = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_BLUR_MODE, &p)); info->blur_mode = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_STRENGTH_MULTIPLIER, &p)); info->strength_multiplier = p.u.sd.value / 100.0; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_SOURCE_OPACITY, &p)); info->source_opacity = p.u.sd.value / 100.0; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_VERTICAL_COLOR, &p)); CopyColorParam(in_data, &p, &info->vertical_color); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HORIZONTAL_COLOR, &p)); CopyColorParam(in_data, &p, &info->horizontal_color); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL_COLOR, &p)); CopyColorParam(in_data, &p, &info->diagonal_color); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HIGHLIGHT_COLOR, &p)); CopyColorParam(in_data, &p, &info->highlight_color); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_VERTICAL_USE_RAMP, &p)); info->vertical_use_ramp = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HORIZONTAL_USE_RAMP, &p)); info->horizontal_use_ramp = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL_USE_RAMP, &p)); info->diagonal_use_ramp = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HIGHLIGHT_USE_RAMP, &p)); info->highlight_use_ramp = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL2_LENGTH, &p)); info->diagonal2_length = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL2_COLOR, &p)); CopyColorParam(in_data, &p, &info->diagonal2_color); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL2_USE_RAMP, &p)); info->diagonal2_use_ramp = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
	return err;
}

static PF_Err About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	suites.ANSICallbacksSuite1()->sprintf(out_data->return_msg,
		"%s v%d.%d.%d\r%s",
		GetStringPtr(StrID_Name),
		MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
		GetStringPtr(StrID_Description));
	return PF_Err_NONE;
}

static PF_Err GlobalSetup(PF_InData *, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000040;
	out_data->out_flags2 = 0x08001400;
	return PF_Err_NONE;
}

static PF_Err ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_GlowRotation_Param_Name),
	                     -360.0, 360.0, -180.0, 180.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0, GLOW_ROTATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BrightnessGain_Param_Name),
	                     1.0, 100.0, 1.0, 100.0, 1.0,
	                     PF_Precision_TENTHS, 0, 0, BRIGHTNESS_GAIN_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_VerticalLength_Param_Name), 0, 1000, 0, 300, 50, VERTICAL_LENGTH_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_HorizontalLength_Param_Name), 0, 1000, 0, 300, 50, HORIZONTAL_LENGTH_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_DiagonalLength_Param_Name), 0, 1000, 0, 300, 50, DIAGONAL_LENGTH_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_HighlightRadius_Param_Name), 0, 500, 0, 500, 0, HIGHLIGHT_RADIUS_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_GlowOpacity_Param_Name), 0, 10000, 0, 100, 100, GLOW_OPACITY_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_Channel_Param_Name), 4, 1, GetStringPtr(StrID_Channel_Choices), CHANNEL_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_BlurMode_Param_Name), 4, 2, GetStringPtr(StrID_BlurMode_Choices), BLUR_MODE_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_ApproximatedInput_Param_Name), "", FALSE, 0, APPROX_INPUT_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_StrengthMultiplier_Param_Name), 0, 1000, 0, 200, 100, STRENGTH_MULTIPLIER_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_SourceOpacity_Param_Name), 0, 100, 0, 100, 100, SOURCE_OPACITY_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_VerticalColor_Param_Name), 255, 255, 255, VERTICAL_COLOR_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_HorizontalColor_Param_Name), 255, 255, 255, HORIZONTAL_COLOR_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_DiagonalColor_Param_Name), 255, 255, 255, DIAGONAL_COLOR_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_HighlightColor_Param_Name), 255, 255, 255, HIGHLIGHT_COLOR_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_MergeMode_Param_Name), 2, 1, GetStringPtr(StrID_MergeMode_Choices), MERGE_MODE_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0, VERTICAL_USE_RAMP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0, HORIZONTAL_USE_RAMP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0, DIAGONAL_USE_RAMP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0, HIGHLIGHT_USE_RAMP_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Diagonal2Length_Param_Name), 0, 1000, 0, 300, 50, DIAGONAL2_LENGTH_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_FadeOut_Param_Name), 0, 1, 0, 1, 0, FADE_OUT_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_Diagonal2Color_Param_Name), 255, 255, 255, DIAGONAL2_COLOR_DISK_ID);
	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseRamp_Param_Name), "", FALSE, 0, DIAGONAL2_USE_RAMP_DISK_ID);

	out_data->num_params = OLMKIRAKIRA_NUM_PARAMS;
	return err;
}

static PF_Err Render(PF_InData *in_data, PF_OutData *, PF_ParamDef *params[], PF_LayerDef *output)
{
	OLMKiraKiraInfo info;
	ReadRenderInfo(in_data, params, &info);
	short bitdepth = PF_WORLD_IS_DEEP(output) ? 16 : 8;
	return RenderWorld(&params[OLMKIRAKIRA_INPUT]->u.ld, output, info, bitdepth);
}

typedef struct {
	PF_FpLong comp_width;
} PreRenderData;

static void DeletePreRenderData(void *data)
{
	delete reinterpret_cast<PreRenderData *>(data);
}

static PF_Err SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	req.preserve_rgb_of_zero_alpha = TRUE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMKIRAKIRA_INPUT, OLMKIRAKIRA_INPUT, &req, in_data->current_time,
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

static PF_Err SmartRender(PF_InData *in_data, PF_OutData *, PF_SmartRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, OLMKIRAKIRA_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (err || !input_world || !output_world) {
		extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMKIRAKIRA_INPUT);
		return err;
	}

	OLMKiraKiraInfo info;
	ERR(CheckoutSmartInfo(in_data, &info));
	info.comp_width = input_world->width;
	if (PreRenderData *pre = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data)) {
		if (pre->comp_width > 0.0) info.comp_width = pre->comp_width;
	}
	if (!err) ERR(RenderWorld(input_world, output_world, info, extra->input->bitdepth));

	extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMKIRAKIRA_INPUT);
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

#include "OLMKiraKira.h"
#include "AEFX_SuiteHandlerTemplate.h"
#include "../../core/kirakira_gaussian.h"
#include "../../core/kirakira_highlight.h"
#include "../../core/kirakira_mode4.h"
#include "../../core/kirakira_warp.h"
#include "../../core/kirakira_merge2.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
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
	static PF_Pixel8 WriteAexTruncate(const FloatRGBA &p) {
		PF_Pixel8 out;
		out.alpha = static_cast<A_u_char>(olm::kirakira::truncate_merge2_channel(p.a, 255.0f));
		out.red   = static_cast<A_u_char>(olm::kirakira::truncate_merge2_channel(p.r, 255.0f));
		out.green = static_cast<A_u_char>(olm::kirakira::truncate_merge2_channel(p.g, 255.0f));
		out.blue  = static_cast<A_u_char>(olm::kirakira::truncate_merge2_channel(p.b, 255.0f));
		return out;
	}
};

template <>
struct PixelTraits<PF_Pixel16> {
	static FloatRGBA Read(const PF_Pixel16 &p) {
		return {
			p.red / static_cast<float>(PF_MAX_CHAN16),
			p.green / static_cast<float>(PF_MAX_CHAN16),
			p.blue / static_cast<float>(PF_MAX_CHAN16),
			p.alpha / static_cast<float>(PF_MAX_CHAN16)
		};
	}
	static PF_Pixel16 Write(const FloatRGBA &p) {
		PF_Pixel16 out;
		out.alpha = static_cast<A_u_short>(std::lround(Clamp01(p.a) * PF_MAX_CHAN16));
		out.red   = static_cast<A_u_short>(std::lround(Clamp01(p.r) * PF_MAX_CHAN16));
		out.green = static_cast<A_u_short>(std::lround(Clamp01(p.g) * PF_MAX_CHAN16));
		out.blue  = static_cast<A_u_short>(std::lround(Clamp01(p.b) * PF_MAX_CHAN16));
		return out;
	}
	static PF_Pixel16 WriteAexTruncate(const FloatRGBA &p) {
		PF_Pixel16 out;
		out.alpha = static_cast<A_u_short>(olm::kirakira::truncate_merge2_channel(p.a, 32768.0f));
		out.red   = static_cast<A_u_short>(olm::kirakira::truncate_merge2_channel(p.r, 32768.0f));
		out.green = static_cast<A_u_short>(olm::kirakira::truncate_merge2_channel(p.g, 32768.0f));
		out.blue  = static_cast<A_u_short>(olm::kirakira::truncate_merge2_channel(p.b, 32768.0f));
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
	static PF_PixelFloat WriteAexTruncate(const FloatRGBA &p) { return Write(p); }
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
	return olm::kirakira::warp_get_rotation_matrix_2d(
		input, src_width, src_height, dst_width, dst_height,
		center_x, center_y, angle_deg);
}

static std::vector<float> CopyCenteredRoi(
	const std::vector<float> &input,
	A_long src_width,
	A_long src_height,
	A_long dst_width,
	A_long dst_height)
{
	return olm::kirakira::centered_crop_scalar(
		input, src_width, src_height, dst_width, dst_height);
}

static std::vector<float> RotatedAxisBoxBlur(
	const std::vector<float> &input,
	A_long width,
	A_long height,
	A_long length,
	double angle_deg,
	A_long passes,
	A_long blur_mode)
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
	if (blur_mode == 4) {
		// Complete actual-AEX forward-warp/recurrence/inverse-warp fixtures
		// cover radius 5 at the bounded canonical-angle leaves plus the original
		// 9x7/5-degree leaf. Unsupported tuples remain identity.
		if (!olm::kirakira::mode4_rotated_scalar_admitted(
				rw, rh, length, angle_deg))
			return input;
		std::vector<float> mode4 = olm::kirakira::mode4_rotated_scalar_chain(
			temp_a, rw, rh, temp_cx, temp_cy, angle_deg, length);
		if (mode4.empty()) return input;
		return CopyCenteredRoi(mode4, rw, rh, width, height);
	}
	temp_a = WarpGetRotDirect(temp_a, rw, rh, rw, rh, temp_cx, temp_cy, angle_deg);
	std::vector<float> temp_b((size_t)rw * rh);
	// Mode 3 is admitted only at complete actual-AEX leaf fixtures.  The row
	// primitive is numerically exact there, but geometry independence has not
	// been proved.  Unsupported Mode-3 tuples fail closed instead of silently
	// substituting the Mode-2 box approximation.
	const bool mode3_admitted =
		olm::kirakira::mode3_gaussian_admitted(rw, rh, length);
	if (blur_mode == 3 && !mode3_admitted) return input;
	if (blur_mode == 3) {
		olm::kirakira::HorizontalGaussian gaussian;
		if (!gaussian.prepare_actual_aex_nonfused(length) ||
			!gaussian.apply(temp_a.data(), rw, temp_b.data(), rw, rw, rh)) {
			return input;
		}
	} else {
		temp_b = DirectionBoxBlur(temp_a, rw, rh, length, 1, 0, passes);
	}
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

// FUN_18114ffd0, bounded to the no-ramp color path.  Unlike the Mode-1
// aggregator this target adds the selected RGB directly, accumulates raw ray
// alpha, then clamps all four channels once after the fifth layer.
static void AddColoredMerge2(
	std::vector<FloatRGBA> &glow,
	const std::vector<float> &amount,
	const PF_PixelFloat &color,
	PF_Boolean use_ramp,
	const OLMKiraKiraRampData &ramp_data)
{
	const olm::kirakira::Merge2Color fixed = {color.red, color.green, color.blue};
	const olm::kirakira::Merge2RampView ramp = {
		reinterpret_cast<const olm::kirakira::Merge2RampStop *>(ramp_data.stops),
		std::min<size_t>(ramp_data.count, 16)
	};
	olm::kirakira::add_colored_merge2(
		glow.data(), amount.data(), glow.size(), fixed, use_ramp ? &ramp : nullptr);
}

static FloatRGBA ComposeMerge2Pixel(
	const FloatRGBA &glow,
	const FloatRGBA &source,
	float glow_opacity,
	float source_opacity)
{
	return olm::kirakira::compose_merge2_pixel(glow, source, glow_opacity, source_opacity);
}

static FloatRGBA ComposePremultiplyPixel(
	const FloatRGBA &glow,
	const FloatRGBA &source,
	float glow_opacity,
	float source_opacity)
{
	return olm::kirakira::compose_premultiply_pixel(
		glow, source, glow_opacity, source_opacity);
}

static std::vector<FloatRGBA> ResizeNearestRGBA(
	const std::vector<FloatRGBA> &input,
	A_long src_width,
	A_long src_height,
	A_long dst_width,
	A_long dst_height)
{
	std::vector<FloatRGBA> output((size_t)dst_width * dst_height);
	for (A_long y = 0; y < dst_height; ++y) {
		const A_long sy = std::min<A_long>(src_height - 1, (y * src_height) / dst_height);
		for (A_long x = 0; x < dst_width; ++x) {
			const A_long sx = std::min<A_long>(src_width - 1, (x * src_width) / dst_width);
			output[(size_t)y * dst_width + x] = input[(size_t)sy * src_width + sx];
		}
	}
	return output;
}

template <typename PixelT>
static std::vector<FloatRGBA> ReadPixels(PF_EffectWorld *input)
{
	const A_long w = input->width;
	const A_long h = input->height;
	std::vector<FloatRGBA> pixels((size_t)w * h);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			pixels[(size_t)y * w + x] = PixelTraits<PixelT>::Read(*PixelAtConst<PixelT>(input, x, y));
		}
	}
	return pixels;
}

static std::vector<float> MakeSeed(
	const std::vector<FloatRGBA> &pixels,
	A_long w,
	A_long h,
	const OLMKiraKiraInfo &info)
{
	std::vector<float> seed((size_t)w * h);
	const double exponent = std::max<PF_FpLong>(1.0e-6, info.strength_multiplier);
	const float fade_threshold = (float)info.fade_out;
	auto apply_fade = [&](float value) -> float {
		if (value == 0.0f) return 0.0f;
		if (fade_threshold < value) return (float)std::pow(value, exponent);
		const float normalized = value / fade_threshold;
		return normalized * normalized * (float)std::pow(fade_threshold, exponent);
	};
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const FloatRGBA &p = pixels[(size_t)y * w + x];
			float v = 0.0f;
			if (info.channel == 1) {
				v = (float)std::pow(p.a, exponent);
			} else if (info.channel == 2) {
				float luma = p.r * 0.2126f + p.g * 0.7152f + p.b * 0.0722f;
				v = apply_fade(luma) * p.a;
			} else if (info.channel == 4) {
				v = apply_fade(std::max({p.r, p.g, p.b})) * p.a;
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

static A_long BlurModePasses(A_long blur_mode)
{
	// Binary-grounded dispatch boundary:
	// 1 -> one cv::boxFilter call; 2 -> three cv::boxFilter calls.
    // Mode 3 targets FUN_181272ec0 (GaussianBlur) with CV_32FC1 input/output,
    // Size(0,1), and
	// sigmaX = length * 0.5. Its forward warp is grounded against OpenCV 4.5.5;
	// the portable Gaussian primitive is being integrated separately. Mode 4's
	// scalar recurrence is selected directly in RotatedAxisBoxBlur; this pass
	// count is therefore ignored for that mode.
	switch (blur_mode) {
		case 1: return 1;
		case 2: return 3;
		case 3:
		case 4:
		default: return 3;
	}
}

template <typename PixelT>
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMKiraKiraInfo &info, short bitdepth)
{
	const A_long w = output->width;
	const A_long h = output->height;
	if (w <= 0 || h <= 0 || input->width != w || input->height != h) return PF_Err_BAD_CALLBACK_PARAM;
	const KiraKiraDebugConfig debug = LoadKiraKiraDebugConfig();

	const PF_FpLong comp_width = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const double render_scale_ratio = comp_width > 0.0 ? (double)w / comp_width : 1.0;
	const bool use_approximated_input = info.approximated_input && render_scale_ratio > 0.5;
	const A_long work_w = use_approximated_input ? std::max<A_long>(1, w / 2) : w;
	const A_long work_h = use_approximated_input ? std::max<A_long>(1, h / 2) : h;
	const double length_scale = use_approximated_input
		? render_scale_ratio * 0.5
		: render_scale_ratio;
	auto scaled_len = [&](A_long value) -> A_long {
		return std::max<A_long>(0, (A_long)((double)value * length_scale));
	};

	const std::vector<FloatRGBA> source_pixels = ReadPixels<PixelT>(input);
	const std::vector<FloatRGBA> working_pixels = use_approximated_input
		? ResizeNearestRGBA(source_pixels, w, h, work_w, work_h)
		: source_pixels;
	const A_long work_width = work_w;
	const A_long work_height = work_h;
	std::vector<float> seed = MakeSeed(working_pixels, work_width, work_height, info);
	const A_long passes = BlurModePasses(info.blur_mode);
	const double glow_rotation = info.glow_rotation;
	const std::vector<float> zero_ray((size_t)work_width * work_height, 0.0f);
	auto make_ray = [&](A_long raw_len, double angle) -> std::vector<float> {
		const A_long len = scaled_len(raw_len);
		if (raw_len <= 0 || len <= 0) return zero_ray;
		return RotatedAxisBoxBlur(seed, work_width, work_height, len, angle, passes, info.blur_mode);
	};
	std::vector<float> vertical = make_ray(info.vertical_length, 90.0 + glow_rotation);
	std::vector<float> horizontal = make_ray(info.horizontal_length, glow_rotation);
	std::vector<float> diagonal = make_ray(info.diagonal_length, 45.0 + glow_rotation);
	std::vector<float> diagonal2 = make_ray(info.diagonal2_length, -45.0 + glow_rotation);
	std::vector<float> highlight = zero_ray;
	const A_long highlight_radius = scaled_len(info.highlight_radius);
	if (highlight_radius > 0 &&
		(info.blur_mode == 1 || info.blur_mode == 2 || info.blur_mode == 4)) {
		// The actual Mode-4 Highlight branch shares Mode 2's three isotropic
		// box-filter calls.  It does not use the directional Mode-4 recurrence.
		const A_long highlight_passes = info.blur_mode == 1 ? 1 : 3;
		highlight = olm::kirakira::highlight_isotropic_box_blur(
			seed, work_width, work_height, highlight_radius * 2 + 1, highlight_passes);
	}

	const double gain_scale = 0.62;
	double scale = info.brightness_gain * gain_scale;
	// The corrected PF32 AE boundary isolates the fifth/highlight-only Mode-4
	// lane.  After undoing Windows AE's measured component transfer, the AEX
	// glow alpha is the three-pass 11x11 box result times Brightness Gain
	// directly; the historical 0.62 scaffold underweights it by exactly 0.62.
	// Keep the older factor on every other bounded lane.
	const double highlight_scale = info.blur_mode == 4
		? info.brightness_gain
		: scale;
	if (info.strength_multiplier <= 1.0e-6) {
		scale = 127.0 / 255.0;
	}
	std::vector<FloatRGBA> glow((size_t)work_width * work_height);
	if (info.merge_mode == 2) {
		AddColoredMerge2(glow, vertical, info.vertical_color, info.vertical_use_ramp, info.vertical_ramp);
		AddColoredMerge2(glow, horizontal, info.horizontal_color, info.horizontal_use_ramp, info.horizontal_ramp);
		AddColoredMerge2(glow, diagonal, info.diagonal_color, info.diagonal_use_ramp, info.diagonal_ramp);
		AddColoredMerge2(glow, highlight, info.highlight_color, info.highlight_use_ramp, info.highlight_ramp);
		AddColoredMerge2(glow, diagonal2, info.diagonal2_color, info.diagonal2_use_ramp, info.diagonal2_ramp);
		for (FloatRGBA &g : glow) {
			g.r = Clamp01(g.r);
			g.g = Clamp01(g.g);
			g.b = Clamp01(g.b);
			g.a = Clamp01(g.a);
		}
	} else {
		AddColoredUnion(glow, vertical, info.vertical_color, scale);
		AddColoredUnion(glow, horizontal, info.horizontal_color, scale);
		AddColoredUnion(glow, diagonal, info.diagonal_color, scale);
		AddColoredUnion(glow, highlight, info.highlight_color, highlight_scale);
		AddColoredUnion(glow, diagonal2, info.diagonal2_color, scale);
		for (FloatRGBA &g : glow) {
			if (g.a > 1.0e-6f) {
				g.r /= g.a;
				g.g /= g.a;
				g.b /= g.a;
			}
		}
	}
	std::vector<FloatRGBA> composed((size_t)work_width * work_height);
	for (A_long y = 0; y < work_height; ++y) {
		for (A_long x = 0; x < work_width; ++x) {
			const size_t idx = (size_t)y * work_width + x;
			const FloatRGBA &src = working_pixels[idx];
			FloatRGBA &out = composed[idx];
			if (info.merge_mode == 2) {
				out = ComposeMerge2Pixel(
					glow[idx], src, (float)info.glow_opacity, (float)info.source_opacity);
			} else {
				out = ComposePremultiplyPixel(
					glow[idx], src, (float)info.glow_opacity, (float)info.source_opacity);
			}
		}
	}
	std::vector<FloatRGBA> glow_full;
	std::vector<FloatRGBA> output_pixels;
	if (use_approximated_input) {
		glow_full = ResizeNearestRGBA(glow, work_width, work_height, w, h);
		output_pixels = ResizeNearestRGBA(composed, work_width, work_height, w, h);
	} else {
		glow_full = std::move(glow);
		output_pixels = std::move(composed);
	}

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const size_t idx = (size_t)y * w + x;
			const FloatRGBA &src = source_pixels[idx];
			const float glow_a = Clamp01(glow_full[idx].a * (float)info.glow_opacity);
			const FloatRGBA glow_normalized = glow_full[idx];
			const FloatRGBA &out = output_pixels[idx];
			KiraKiraDebugDumpPoint(debug, bitdepth, w, h, x, y, src, glow_normalized, glow_a, out);
			// The actual integer-depth outer writers use CVTTSS2SI after
			// clamp and scale for both merge modes.
			*PixelAt<PixelT>(output, x, y) = PixelTraits<PixelT>::WriteAexTruncate(out);
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

static PF_Err ReadRampHandle(PF_InData *in_data, PF_ArbitraryH handle, OLMKiraKiraRampData *out);

static PF_Err ReadRenderInfo(PF_InData *in_data, PF_ParamDef *params[], OLMKiraKiraInfo *info)
{
	AEFX_CLR_STRUCT(*info);
	info->glow_rotation = params[OLMKIRAKIRA_GLOW_ROTATION]->u.fs_d.value;
	info->brightness_gain = params[OLMKIRAKIRA_BRIGHTNESS_GAIN]->u.fs_d.value;
	info->fade_out = params[OLMKIRAKIRA_FADE_OUT]->u.fs_d.value * 0.2;
	info->vertical_length = params[OLMKIRAKIRA_VERTICAL_LENGTH]->u.sd.value;
	info->horizontal_length = params[OLMKIRAKIRA_HORIZONTAL_LENGTH]->u.sd.value;
	info->diagonal_length = params[OLMKIRAKIRA_DIAGONAL_LENGTH]->u.sd.value;
	info->diagonal2_length = params[OLMKIRAKIRA_DIAGONAL2_LENGTH]->u.sd.value;
	info->highlight_radius = params[OLMKIRAKIRA_HIGHLIGHT_RADIUS]->u.sd.value;
	info->glow_opacity = params[OLMKIRAKIRA_GLOW_OPACITY]->u.sd.value / 100.0;
	info->channel = params[OLMKIRAKIRA_CHANNEL]->u.pd.value;
	info->blur_mode = params[OLMKIRAKIRA_BLUR_MODE]->u.pd.value;
	info->merge_mode = params[OLMKIRAKIRA_MERGE_MODE]->u.pd.value;
	info->approximated_input = params[OLMKIRAKIRA_APPROX_INPUT]->u.bd.value;
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
	PF_Err err = ReadRampHandle(in_data, params[OLMKIRAKIRA_VERTICAL_RAMP]->u.arb_d.value, &info->vertical_ramp);
	if (!err) err = ReadRampHandle(in_data, params[OLMKIRAKIRA_HORIZONTAL_RAMP]->u.arb_d.value, &info->horizontal_ramp);
	if (!err) err = ReadRampHandle(in_data, params[OLMKIRAKIRA_DIAGONAL_RAMP]->u.arb_d.value, &info->diagonal_ramp);
	if (!err) err = ReadRampHandle(in_data, params[OLMKIRAKIRA_HIGHLIGHT_RAMP]->u.arb_d.value, &info->highlight_ramp);
	if (!err) err = ReadRampHandle(in_data, params[OLMKIRAKIRA_DIAGONAL2_RAMP]->u.arb_d.value, &info->diagonal2_ramp);
	info->comp_width = params[OLMKIRAKIRA_INPUT]->u.ld.width;
	return err;
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
	ERR(checkout(OLMKIRAKIRA_FADE_OUT, &p)); info->fade_out = p.u.fs_d.value * 0.2; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_VERTICAL_LENGTH, &p)); info->vertical_length = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HORIZONTAL_LENGTH, &p)); info->horizontal_length = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL_LENGTH, &p)); info->diagonal_length = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HIGHLIGHT_RADIUS, &p)); info->highlight_radius = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_GLOW_OPACITY, &p)); info->glow_opacity = p.u.sd.value / 100.0; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_CHANNEL, &p)); info->channel = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_BLUR_MODE, &p)); info->blur_mode = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_MERGE_MODE, &p)); info->merge_mode = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_APPROX_INPUT, &p)); info->approximated_input = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p);
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
	ERR(checkout(OLMKIRAKIRA_VERTICAL_RAMP, &p)); if (!err) err = ReadRampHandle(in_data, p.u.arb_d.value, &info->vertical_ramp); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HORIZONTAL_RAMP, &p)); if (!err) err = ReadRampHandle(in_data, p.u.arb_d.value, &info->horizontal_ramp); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL_RAMP, &p)); if (!err) err = ReadRampHandle(in_data, p.u.arb_d.value, &info->diagonal_ramp); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_HIGHLIGHT_RAMP, &p)); if (!err) err = ReadRampHandle(in_data, p.u.arb_d.value, &info->highlight_ramp); PF_CHECKIN_PARAM(in_data, &p);
	ERR(checkout(OLMKIRAKIRA_DIAGONAL2_RAMP, &p)); if (!err) err = ReadRampHandle(in_data, p.u.arb_d.value, &info->diagonal2_ramp); PF_CHECKIN_PARAM(in_data, &p);
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

static PF_Err GlobalSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02008040;
	out_data->out_flags2 = 0x08001400;

	// Match the Windows plug-in's global AEGP registration. ECW event-surface
	// registration itself is performed by PF_REGISTER_UI in ParamsSetup below.
	static AEGP_PluginID plugin_id = 0;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	return suites.UtilitySuite6()->AEGP_RegisterWithAEGP(
		nullptr, "OLM Kira Kira", &plugin_id);
}

static OLMKiraKiraRampData DefaultRampData()
{
	OLMKiraKiraRampData ramp = {};
	ramp.count = 3;
	ramp.stops[0] = {0.0f, 1.0f, 1.0f, 0.0f, 0.0f};
	ramp.stops[1] = {0.7799999713897705f, 1.0f, 1.0f, 0.6510000228881836f, 0.0f};
	ramp.stops[2] = {1.0f, 1.0f, 1.0f, 1.0f, 1.0f};
	return ramp;
}

static PF_Err NewRampHandle(PF_InData *in_data, const OLMKiraKiraRampData &data, PF_ArbitraryH *out)
{
	if (!in_data || !out) return PF_Err_BAD_CALLBACK_PARAM;
	AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
	PF_Handle handle = handles->host_new_handle(sizeof(data));
	if (!handle) return PF_Err_OUT_OF_MEMORY;
	void *locked = handles->host_lock_handle(handle);
	if (!locked) {
		handles->host_dispose_handle(handle);
		return PF_Err_OUT_OF_MEMORY;
	}
	std::memcpy(locked, &data, sizeof(data));
	handles->host_unlock_handle(handle);
	*out = handle;
	return PF_Err_NONE;
}

static PF_Err ReadRampHandle(PF_InData *in_data, PF_ArbitraryH handle, OLMKiraKiraRampData *out)
{
	if (!in_data || !handle || !out) return PF_Err_BAD_CALLBACK_PARAM;
	AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
	if (handles->host_get_handle_size(handle) < sizeof(*out)) return PF_Err_BAD_CALLBACK_PARAM;
	void *locked = handles->host_lock_handle(handle);
	if (!locked) return PF_Err_BAD_CALLBACK_PARAM;
	std::memcpy(out, locked, sizeof(*out));
	handles->host_unlock_handle(handle);
	if (out->count > 16) return PF_Err_BAD_CALLBACK_PARAM;
	return PF_Err_NONE;
}

static PF_Err RampArbitraryCallback(PF_InData *in_data, PF_ArbParamsExtra *extra)
{
	if (!extra) return PF_Err_BAD_CALLBACK_PARAM;
	PF_Err err = PF_Err_NONE;
	switch (extra->which_function) {
	case PF_Arbitrary_NEW_FUNC:
		return NewRampHandle(in_data, DefaultRampData(), extra->u.new_func_params.arbPH);
	case PF_Arbitrary_DISPOSE_FUNC: {
		AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
		if (extra->u.dispose_func_params.arbH) handles->host_dispose_handle(extra->u.dispose_func_params.arbH);
		extra->u.dispose_func_params.arbH = nullptr;
		return PF_Err_NONE;
	}
	case PF_Arbitrary_COPY_FUNC: {
		OLMKiraKiraRampData ramp = {};
		err = ReadRampHandle(in_data, extra->u.copy_func_params.src_arbH, &ramp);
		return err ? err : NewRampHandle(in_data, ramp, extra->u.copy_func_params.dst_arbPH);
	}
	case PF_Arbitrary_FLAT_SIZE_FUNC:
		*extra->u.flat_size_func_params.flat_data_sizePLu = 0x145;
		return PF_Err_NONE;
	case PF_Arbitrary_FLATTEN_FUNC: {
		if (extra->u.flatten_func_params.buf_sizeLu < 0x145 || !extra->u.flatten_func_params.flat_dataPV)
			return PF_Err_BAD_CALLBACK_PARAM;
		OLMKiraKiraRampData ramp = {};
		err = ReadRampHandle(in_data, extra->u.flatten_func_params.arbH, &ramp);
		if (err) return err;
		unsigned char *flat = static_cast<unsigned char *>(extra->u.flatten_func_params.flat_dataPV);
		std::memset(flat, 0, 0x145);
		flat[0] = 1;
		std::memcpy(flat + 1, &ramp.count, sizeof(ramp.count));
		std::memcpy(flat + 5, ramp.stops, static_cast<size_t>(ramp.count) * sizeof(ramp.stops[0]));
		return PF_Err_NONE;
	}
	case PF_Arbitrary_UNFLATTEN_FUNC: {
		const unsigned char *flat = static_cast<const unsigned char *>(extra->u.unflatten_func_params.flat_dataPV);
		OLMKiraKiraRampData ramp = {};
		size_t count = 0;
		if (!olm::kirakira::parse_merge2_ramp_flat(
				flat, extra->u.unflatten_func_params.buf_sizeLu,
				reinterpret_cast<olm::kirakira::Merge2RampStop *>(ramp.stops), 16, &count))
			return PF_Err_BAD_CALLBACK_PARAM;
		ramp.count = static_cast<A_u_long>(count);
		return NewRampHandle(in_data, ramp, extra->u.unflatten_func_params.arbPH);
	}
	case PF_Arbitrary_INTERP_FUNC: {
		OLMKiraKiraRampData left = {}, right = {}, result = {};
		err = ReadRampHandle(in_data, extra->u.interp_func_params.left_arbH, &left);
		if (!err) err = ReadRampHandle(in_data, extra->u.interp_func_params.right_arbH, &right);
		if (err) return err;
		result.count = static_cast<A_u_long>(olm::kirakira::interpolate_merge2_ramps(
			reinterpret_cast<olm::kirakira::Merge2RampStop *>(result.stops),
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(left.stops), left.count,
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(right.stops), right.count,
			static_cast<float>(extra->u.interp_func_params.tF)));
		return NewRampHandle(in_data, result, extra->u.interp_func_params.interpPH);
	}
	case PF_Arbitrary_COMPARE_FUNC: {
		OLMKiraKiraRampData a = {}, b = {};
		err = ReadRampHandle(in_data, extra->u.compare_func_params.a_arbH, &a);
		if (!err) err = ReadRampHandle(in_data, extra->u.compare_func_params.b_arbH, &b);
		if (err) return err;
		const bool equal = olm::kirakira::equal_merge2_ramps(
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(a.stops), a.count,
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(b.stops), b.count);
		*extra->u.compare_func_params.compareP = equal ? PF_ArbCompare_EQUAL : PF_ArbCompare_NOT_EQUAL;
		return PF_Err_NONE;
	}
	case PF_Arbitrary_PRINT_SIZE_FUNC:
		*extra->u.print_size_func_params.print_sizePLu = 0;
		return PF_Err_NONE;
	case PF_Arbitrary_PRINT_FUNC:
	case PF_Arbitrary_SCAN_FUNC:
		return PF_Err_NONE;
	default:
		return PF_Err_BAD_CALLBACK_PARAM;
	}
}

static PF_Err AddRampParam(PF_InData *in_data, A_short id, A_long disk_id)
{
	// PF_ArbitraryDef::refconPV is opaque to the host and is passed back to
	// PF_Cmd_ARBITRARY_CALLBACKS. The Windows owner uses one stable non-null
	// handler address for all five ramps, so keep the same identity/lifetime
	// contract even though the native callback does not need handler state.
	static const char ramp_handler_refcon = 0;
	PF_ParamDef def;
	AEFX_CLR_STRUCT(def);
	PF_ArbitraryH default_handle = nullptr;
	PF_Err err = NewRampHandle(in_data, DefaultRampData(), &default_handle);
	if (err) return err;
	def.param_type = PF_Param_ARBITRARY_DATA;
	std::strncpy(def.name, "Ramp", sizeof(def.name) - 1);
	def.ui_width = 0x136;
	def.ui_height = 0xaa;
	def.ui_flags = PF_PUI_CONTROL | PF_PUI_DONT_ERASE_CONTROL;
	def.flags = PF_ParamFlag_SUPERVISE | PF_ParamFlag_START_COLLAPSED;
	def.uu.id = disk_id;
	def.u.arb_d.id = id;
	def.u.arb_d.dephault = default_handle;
	def.u.arb_d.value = nullptr;
	def.u.arb_d.refconPV = const_cast<char *>(&ramp_handler_refcon);
	err = PF_ADD_PARAM(in_data, -1, &def);
	if (err) {
		AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
		handles->host_dispose_handle(default_handle);
	}
	return err;
}

static PF_Err RampEvent(PF_InData *in_data, PF_ParamDef *params[], PF_EventExtra *event)
{
	if (!in_data || !params || !event || event->effect_win.area != PF_EA_CONTROL)
		return PF_Err_NONE;
	const A_long index = event->effect_win.index;
	PF_ParamDef *param = params[index];
	if (!param || param->param_type != PF_Param_ARBITRARY_DATA || !param->u.arb_d.value)
		return PF_Err_NONE;
	const PF_Rect &frame = event->effect_win.current_frame;
	const float left = static_cast<float>(frame.left + 10);
	const float width = static_cast<float>(std::max<A_long>(1, std::min<A_long>(192, frame.right - frame.left - 10)));

	if (event->e_type == PF_Event_DRAW) {
		OLMKiraKiraRampData ramp = {};
		PF_Err err = ReadRampHandle(in_data, param->u.arb_d.value, &ramp);
		if (err) return err;
		AEGP_SuiteHandler suites(in_data->pica_basicP);
		DRAWBOT_DrawRef draw_ref = nullptr;
		ERR(suites.EffectCustomUISuite2()->PF_GetDrawingReference(event->contextH, &draw_ref));
		if (err || !draw_ref) return err;
		DRAWBOT_SupplierRef supplier = nullptr;
		DRAWBOT_SurfaceRef surface = nullptr;
		ERR(suites.DrawbotSuiteCurrent()->GetSupplier(draw_ref, &supplier));
		ERR(suites.DrawbotSuiteCurrent()->GetSurface(draw_ref, &surface));
		if (err) return err;
		const olm::kirakira::Merge2RampView view = {
			reinterpret_cast<const olm::kirakira::Merge2RampStop *>(ramp.stops),
			std::min<size_t>(ramp.count, 16)
		};
		const float top = static_cast<float>(frame.top + 5);
		const float height = static_cast<float>(std::max<A_long>(8, std::min<A_long>(50, frame.bottom - frame.top - 5)));
		for (A_long x = 0; x < static_cast<A_long>(width); ++x) {
			const float amount = width > 1.0f ? x / (width - 1.0f) : 0.0f;
			const auto color = olm::kirakira::sample_merge2_ramp(view, amount);
			const DRAWBOT_ColorRGBA rgba = {color.red, color.green, color.blue, 1.0f};
			const DRAWBOT_RectF32 rect = {left + x, top, 1.0f, height};
			ERR(suites.SurfaceSuiteCurrent()->PaintRect(surface, &rgba, &rect));
			if (err) return err;
		}
		for (A_u_long i = 0; i < ramp.count; ++i) {
			const float x = left + Clamp01(ramp.stops[i].position) * width;
			const DRAWBOT_ColorRGBA marker = {1.0f, 1.0f, 1.0f, 1.0f};
			const DRAWBOT_RectF32 rect = {x - 2.0f, top + height + 5.0f, 5.0f, 10.0f};
			ERR(suites.SurfaceSuiteCurrent()->PaintRect(surface, &marker, &rect));
			if (err) return err;
		}
		ERR(suites.SurfaceSuiteCurrent()->Flush(surface));
		event->evt_out_flags |= PF_EO_HANDLED_EVENT;
		return err;
	}

	if (event->e_type == PF_Event_DO_CLICK || event->e_type == PF_Event_DRAG) {
		AEFX_SuiteScoper<PF_HandleSuite1> handles(in_data, kPFHandleSuite, kPFHandleSuiteVersion1);
		OLMKiraKiraRampData *ramp = static_cast<OLMKiraKiraRampData *>(handles->host_lock_handle(param->u.arb_d.value));
		if (!ramp || ramp->count == 0 || ramp->count > 16) return PF_Err_BAD_CALLBACK_PARAM;
		const float normalized = Clamp01((event->u.do_click.screen_point.x - left) / width);
		A_long selected = static_cast<A_long>(event->u.do_click.continue_refcon[0]) - 1;
		const bool edit_color = event->e_type == PF_Event_DO_CLICK && event->u.do_click.num_clicks != 1 &&
			event->u.do_click.screen_point.y >= frame.top + 60 &&
			event->u.do_click.screen_point.y <= frame.top + 70;
		const bool add_stop = event->e_type == PF_Event_DO_CLICK && ramp->count < 16 &&
			event->u.do_click.num_clicks == 1 &&
			event->u.do_click.screen_point.x >= left &&
			event->u.do_click.screen_point.x <= left + width &&
			event->u.do_click.screen_point.y >= frame.top + 5 &&
			event->u.do_click.screen_point.y <= frame.top + 55;
		if (edit_color) {
			const size_t hit = olm::kirakira::hit_merge2_ramp_stop(
				reinterpret_cast<const olm::kirakira::Merge2RampStop *>(ramp->stops), ramp->count,
				normalized, 5.0f / width);
			if (hit < ramp->count) {
				PF_PixelFloat sample = {
					ramp->stops[hit].alpha, ramp->stops[hit].red,
					ramp->stops[hit].green, ramp->stops[hit].blue
				};
				PF_PixelFloat picked = sample;
				AEFX_SuiteScoper<PFAppSuite6> app(in_data, kPFAppSuite, kPFAppSuiteVersion6);
				const PF_Err picker_err = app->PF_AppColorPickerDialog("Color select", &sample, TRUE, &picked);
				size_t picker_selected = hit;
				olm::kirakira::apply_merge2_ramp_color_picker_result(
					reinterpret_cast<olm::kirakira::Merge2RampStop *>(ramp->stops), ramp->count,
					&picker_selected, picker_err, PF_Interrupt_CANCEL,
					picked.alpha, picked.red, picked.green, picked.blue);
				event->u.do_click.continue_refcon[0] = picker_selected < ramp->count
					? static_cast<A_intptr_t>(picker_selected + 1) : 0;
			}
		} else if (add_stop) {
			ramp->count = static_cast<A_u_long>(olm::kirakira::insert_merge2_ramp_stop(
				reinterpret_cast<olm::kirakira::Merge2RampStop *>(ramp->stops), ramp->count,
				normalized));
			event->u.do_click.continue_refcon[0] = 0;
			param->uu.change_flags |= PF_ChangeFlag_CHANGED_VALUE;
		} else if (event->e_type == PF_Event_DO_CLICK || selected < 0 || selected >= static_cast<A_long>(ramp->count)) {
			selected = static_cast<A_long>(olm::kirakira::nearest_merge2_ramp_stop(
				reinterpret_cast<const olm::kirakira::Merge2RampStop *>(ramp->stops), ramp->count, normalized));
			event->u.do_click.continue_refcon[0] = selected + 1;
			event->u.do_click.send_drag = TRUE;
		} else {
			if (event->u.do_click.last_time && event->u.do_click.screen_point.y - (frame.top + 55) >= 21) {
				ramp->count = static_cast<A_u_long>(olm::kirakira::erase_merge2_ramp_stop(
					reinterpret_cast<olm::kirakira::Merge2RampStop *>(ramp->stops), ramp->count,
					static_cast<size_t>(selected)));
				event->u.do_click.continue_refcon[0] = 0;
			} else {
				olm::kirakira::drag_merge2_ramp_stop(
					reinterpret_cast<olm::kirakira::Merge2RampStop *>(ramp->stops), ramp->count,
					static_cast<size_t>(selected), normalized);
			}
			param->uu.change_flags |= PF_ChangeFlag_CHANGED_VALUE;
		}
		param->uu.change_flags |= PF_ChangeFlag_CHANGED_VALUE;
		handles->host_unlock_handle(param->u.arb_d.value);
		event->evt_out_flags |= PF_EO_HANDLED_EVENT | PF_EO_UPDATE_NOW;
		AEFX_SuiteScoper<PFAppSuite6> app(in_data, kPFAppSuite, kPFAppSuiteVersion6);
		app->PF_InvalidateRect(event->contextH, &frame);
		return PF_Err_NONE;
	}
	return PF_Err_NONE;
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
	PF_Err err = PF_Err_NONE;
	OLMKiraKiraInfo info;
	ERR(ReadRenderInfo(in_data, params, &info));
	if (err) return err;
	PF_EffectWorld *input = &params[OLMKIRAKIRA_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	ERR(world_suite->PF_GetPixelFormat(input, &format));
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
	ERR(RenderWorld(input, output, info, bitdepth));
	return err;
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
	}
	return err;
}

#include "OLMKiraKira.h"
#include "AEFX_SuiteHandlerTemplate.h"
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
#include "../../core/kirakira_gaussian.h"
#include "../../core/kirakira_highlight.h"
#include "../../core/kirakira_mode4.h"
#include "../../core/kirakira_warp.h"
#include "../../core/kirakira_merge2.h"

#include <algorithm>
#include <cstdarg>
#include <cstdint>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <vector>

namespace {

static void KiraDiagnosticLog(const char *format, ...)
{
	const char *path = std::getenv("OLMKIRAKIRA_DIAGNOSTIC_LOG");
	if (!path || !*path || !format) return;
	FILE *file = std::fopen(path, "a");
	if (!file) return;
	va_list arguments;
	va_start(arguments, format);
	std::vfprintf(file, format, arguments);
	va_end(arguments);
	std::fputc('\n', file);
	std::fclose(file);
}

static void KiraDiagnosticWorld(const char *label, const PF_EffectWorld *world)
{
	if (!world) {
		KiraDiagnosticLog("world %s null", label ? label : "?");
		return;
	}
	KiraDiagnosticLog(
		"world %s data=%p width=%ld height=%ld rowbytes=%ld origin=%ld,%ld "
		"extent=%ld,%ld,%ld,%ld flags=%lu",
		label ? label : "?", world->data,
		(long)world->width, (long)world->height, (long)world->rowbytes,
		(long)world->origin_x, (long)world->origin_y,
		(long)world->extent_hint.left, (long)world->extent_hint.top,
		(long)world->extent_hint.right, (long)world->extent_hint.bottom,
		(unsigned long)world->world_flags);
}

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
	const size_t row_offset = static_cast<size_t>(y) *
		static_cast<size_t>(world->rowbytes);
	return reinterpret_cast<PixelT *>(
		reinterpret_cast<char *>(world->data) + row_offset) + x;
}

template <typename PixelT>
static const PixelT *PixelAtConst(const PF_EffectWorld *world, A_long x, A_long y)
{
	const size_t row_offset = static_cast<size_t>(y) *
		static_cast<size_t>(world->rowbytes);
	return reinterpret_cast<const PixelT *>(
		reinterpret_cast<const char *>(world->data) + row_offset) + x;
}

template <typename PixelT>
struct PixelTraits;

template <>
struct PixelTraits<PF_Pixel8> {
	static FloatRGBA Read(const PF_Pixel8 &p) {
		// The typed Windows owners materialize a FLOAT32 reciprocal once and
		// multiply each byte lane.  Division is mathematically equivalent but
		// differs by one ULP for a bounded set of byte values.
		constexpr float kByteToFloat = 1.0f / 255.0f;
		return {
			p.red * kByteToFloat,
			p.green * kByteToFloat,
			p.blue * kByteToFloat,
			p.alpha * kByteToFloat
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

static size_t PixelSizeForFormat(PF_PixelFormat format)
{
	switch (format) {
		case PF_PixelFormat_ARGB32:  return sizeof(PF_Pixel8);
		case PF_PixelFormat_ARGB64:  return sizeof(PF_Pixel16);
		case PF_PixelFormat_ARGB128: return sizeof(PF_PixelFloat);
		default: return 0;
	}
}

static short BitDepthForFormat(PF_PixelFormat format)
{
	switch (format) {
		case PF_PixelFormat_ARGB32:  return 8;
		case PF_PixelFormat_ARGB64:  return 16;
		case PF_PixelFormat_ARGB128: return 32;
		default: return 0;
	}
}

static PF_Err GetKiraPixelFormats(
	PF_InData *in_data,
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	PF_PixelFormat *input_format,
	PF_PixelFormat *output_format)
{
	if (!in_data || !input || !output || !input_format || !output_format ||
		!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
		!in_data->pica_basicP->ReleaseSuite) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const void *suite_ptr = nullptr;
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
				err = world_suite->PF_GetPixelFormat(input, input_format);
				if (!err) err = world_suite->PF_GetPixelFormat(output, output_format);
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
}

static bool WorldLayoutIsSafe(const PF_EffectWorld *world, size_t pixel_size)
{
	if (!world || !world->data || pixel_size == 0 ||
		world->width <= 0 || world->height <= 0 || world->rowbytes <= 0) {
		return false;
	}
	const int64_t active_rowbytes =
		static_cast<int64_t>(world->width) * static_cast<int64_t>(pixel_size);
	if (active_rowbytes <= 0 ||
		active_rowbytes > static_cast<int64_t>(world->rowbytes)) {
		return false;
	}
	size_t alignment = 1;
	if (pixel_size == sizeof(PF_PixelFloat)) alignment = alignof(PF_PixelFloat);
	else if (pixel_size == sizeof(PF_Pixel16)) alignment = alignof(PF_Pixel16);
	else if (pixel_size == sizeof(PF_Pixel8)) alignment = alignof(PF_Pixel8);
	if ((reinterpret_cast<uintptr_t>(world->data) % alignment) != 0 ||
		(static_cast<size_t>(world->rowbytes) % alignment) != 0) {
		return false;
	}
	const uint64_t last_row_offset =
		static_cast<uint64_t>(world->height - 1) *
		static_cast<uint64_t>(world->rowbytes);
	return last_row_offset <= UINT64_MAX - static_cast<uint64_t>(active_rowbytes);
}

static PF_Err ValidateWorldPair(
	PF_InData *in_data,
	PF_OutData *out_data,
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	short declared_bitdepth,
	PF_PixelFormat *format_out)
{
	if (!in_data || !out_data || !input || !output || !format_out)
		return PF_Err_BAD_CALLBACK_PARAM;
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	PF_Err err = GetKiraPixelFormats(
		in_data, input, output, &input_format, &output_format);
	if (err) return err;
	if (input_format != output_format) return PF_Err_BAD_CALLBACK_PARAM;
	const size_t pixel_size = PixelSizeForFormat(input_format);
	const short format_bitdepth = BitDepthForFormat(input_format);
	if (!pixel_size || !format_bitdepth ||
		(declared_bitdepth != 0 && declared_bitdepth != format_bitdepth) ||
		input->width != output->width || input->height != output->height ||
		!WorldLayoutIsSafe(input, pixel_size) ||
		!WorldLayoutIsSafe(output, pixel_size)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const uint64_t pixel_count = static_cast<uint64_t>(input->width) *
		static_cast<uint64_t>(input->height);
	if (pixel_count > static_cast<uint64_t>(SIZE_MAX / sizeof(FloatRGBA)))
		return PF_Err_OUT_OF_MEMORY;
	*format_out = input_format;
	return PF_Err_NONE;
}

static std::vector<float> DirectionBoxBlur(
	const std::vector<float> &input,
	A_long width,
	A_long height,
	A_long length,
	A_long dx,
	A_long dy,
	A_long passes)
{
	if (length <= 0) return input;
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
	// Mode 3 and Mode 4 both have recovered, non-identity Length=1 owners.
	// The box-filter modes remain identity at one through DirectionBoxBlur.
	if (length <= 0) return input;
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
		// Complete actual-AEX forward-warp/recurrence/inverse-warp fixtures span
		// public radius endpoints, default/non-power-of-two lengths, canonical
		// and rotated angles, and practical leaves. Sub-minimum leaves remain
		// fail-closed.
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
	// Mode 3's hard public Length range 1..1000 is geometry-general above the
	// bounded minimum leaf; smaller exceptions remain fixture-only. Unsupported tuples fail closed
	// instead of silently substituting the Mode-2 box approximation.
	const bool mode3_admitted =
		olm::kirakira::mode3_gaussian_admitted(rw, rh, length);
	if (blur_mode == 3 && !mode3_admitted) return input;
	if (blur_mode == 3) {
		olm::kirakira::HorizontalGaussian gaussian;
		const bool prepared = length == 1
			? gaussian.prepare_actual_aex_small5_nonfused()
			: gaussian.prepare_actual_aex_nonfused(length);
		if (!prepared ||
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
	PF_Boolean use_ramp,
	const OLMKiraKiraRampData &ramp_data,
	float scale)
{
	const olm::kirakira::Merge2Color fixed = {color.red, color.green, color.blue};
	const olm::kirakira::Merge2RampView ramp = {
		reinterpret_cast<const olm::kirakira::Merge2RampStop *>(ramp_data.stops),
		std::min<size_t>(ramp_data.count, 16)
	};
	const size_t pixels = glow.size();
	for (size_t i = 0; i < pixels; ++i) {
		if (amount[i] <= kFd90RayEpsilon) continue;
		const float alpha = Clamp01(amount[i] * scale);
		const olm::kirakira::Merge2Color selected = use_ramp
			? olm::kirakira::sample_merge2_ramp(ramp, alpha)
			: fixed;
		glow[i].r += alpha * selected.red;
		glow[i].g += alpha * selected.green;
		glow[i].b += alpha * selected.blue;
		glow[i].a = glow[i].a + alpha - glow[i].a * alpha;
	}
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
	// The three typed Windows owners build the direction table as
	// {rotation+90, rotation, rotation+45, rotation+135, 0}.  Although -45
	// describes the same undirected axis, Mode 4's directed recurrence and
	// fixed-point warp rounding make the two representatives bit-distinct.
	std::vector<float> diagonal2 = make_ray(info.diagonal2_length, 135.0 + glow_rotation);
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

	// FUN_18114f4a0 loads Brightness Gain directly from state+0x608 into the
	// trailing argument of both aggregation vtable calls. Natural exported
	// Mode-1 capture confirms ray * Brightness Gain before composition; the
	// historical 0.62 PNG-fit scaffold is not part of the AEX owner path.
	float scale = (float)info.brightness_gain;
	const float highlight_scale = (float)info.brightness_gain;
	if (info.strength_multiplier <= 1.0e-6) {
		scale = 127.0 / 255.0;
	}
	std::vector<FloatRGBA> glow((size_t)work_width * work_height);
	// The exported owner stores the UI Merge mode at state+0x44 for the outer
	// writer, but initializes the aggregation selector at state+0x48 to one.
	// Consequently both public merge choices use FUN_18114fd90 here; only the
	// downstream composition changes with info.merge_mode.
	AddColoredUnion(glow, vertical, info.vertical_color, info.vertical_use_ramp, info.vertical_ramp, scale);
	AddColoredUnion(glow, horizontal, info.horizontal_color, info.horizontal_use_ramp, info.horizontal_ramp, scale);
	AddColoredUnion(glow, diagonal, info.diagonal_color, info.diagonal_use_ramp, info.diagonal_ramp, scale);
	// FUN_18114f4a0 owns four directional slots followed by Highlight.
	// Preserve that addition order because float32 sums are not associative.
	AddColoredUnion(glow, diagonal2, info.diagonal2_color, info.diagonal2_use_ramp, info.diagonal2_ramp, scale);
	AddColoredUnion(glow, highlight, info.highlight_color, info.highlight_use_ramp, info.highlight_ramp, highlight_scale);
	for (FloatRGBA &g : glow) {
		if (g.a > 1.0e-6f) {
			// FUN_18114fd90 computes one float reciprocal and multiplies
			// all RGB lanes in the captured PF32 owner. Keep the proven
			// integer-depth division boundary until those owners are traced.
			if (bitdepth == 32) {
				const float inverse_alpha = 1.0f / g.a;
				g.r *= inverse_alpha;
				g.g *= inverse_alpha;
				g.b *= inverse_alpha;
			} else {
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

static PF_Err CopyColorParam(PF_InData *in_data, PF_ParamDef *param, PF_PixelFloat *out)
{
	if (!in_data || !param || !out) return PF_Err_BAD_CALLBACK_PARAM;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();
	if (!cps || !cps->PF_GetFloatingPointColorFromColorDef)
		return PF_Err_BAD_CALLBACK_PARAM;
	PF_PixelFloat color = {1.0f, 1.0f, 1.0f, 1.0f};
	const PF_Err err = cps->PF_GetFloatingPointColorFromColorDef(
		in_data->effect_ref, param, &color);
	if (err) return err;
	*out = color;
	return PF_Err_NONE;
}

static PF_Err ReadRampHandle(PF_InData *in_data, PF_ArbitraryH handle, OLMKiraKiraRampData *out);

static void KiraDiagnosticInfo(const char *label, const OLMKiraKiraInfo &info)
{
	KiraDiagnosticLog(
		"info %s mode=%ld merge=%ld channel=%ld approx=%d rotation=%.17g gain=%.17g "
		"strength=%.17g fade=%.17g glow_opacity=%.17g source_opacity=%.17g "
		"lengths=%ld,%ld,%ld,%ld highlight=%ld ramps=%d,%d,%d,%d,%d comp_width=%.17g",
		label ? label : "?", (long)info.blur_mode, (long)info.merge_mode,
		(long)info.channel, (int)info.approximated_input,
		(double)info.glow_rotation, (double)info.brightness_gain,
		(double)info.strength_multiplier, (double)info.fade_out,
		(double)info.glow_opacity, (double)info.source_opacity,
		(long)info.vertical_length, (long)info.horizontal_length,
		(long)info.diagonal_length, (long)info.diagonal2_length,
		(long)info.highlight_radius, (int)info.vertical_use_ramp,
		(int)info.horizontal_use_ramp, (int)info.diagonal_use_ramp,
		(int)info.diagonal2_use_ramp, (int)info.highlight_use_ramp,
		(double)info.comp_width);
}

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
	PF_Err err = CopyColorParam(in_data, params[OLMKIRAKIRA_VERTICAL_COLOR], &info->vertical_color);
	if (!err) err = CopyColorParam(in_data, params[OLMKIRAKIRA_HORIZONTAL_COLOR], &info->horizontal_color);
	if (!err) err = CopyColorParam(in_data, params[OLMKIRAKIRA_DIAGONAL_COLOR], &info->diagonal_color);
	if (!err) err = CopyColorParam(in_data, params[OLMKIRAKIRA_HIGHLIGHT_COLOR], &info->highlight_color);
	if (!err) err = CopyColorParam(in_data, params[OLMKIRAKIRA_DIAGONAL2_COLOR], &info->diagonal2_color);
	if (err) return err;
	info->vertical_use_ramp = params[OLMKIRAKIRA_VERTICAL_USE_RAMP]->u.bd.value;
	info->horizontal_use_ramp = params[OLMKIRAKIRA_HORIZONTAL_USE_RAMP]->u.bd.value;
	info->diagonal_use_ramp = params[OLMKIRAKIRA_DIAGONAL_USE_RAMP]->u.bd.value;
	info->highlight_use_ramp = params[OLMKIRAKIRA_HIGHLIGHT_USE_RAMP]->u.bd.value;
	info->diagonal2_use_ramp = params[OLMKIRAKIRA_DIAGONAL2_USE_RAMP]->u.bd.value;
	err = ReadRampHandle(in_data, params[OLMKIRAKIRA_VERTICAL_RAMP]->u.arb_d.value, &info->vertical_ramp);
	if (!err) err = ReadRampHandle(in_data, params[OLMKIRAKIRA_HORIZONTAL_RAMP]->u.arb_d.value, &info->horizontal_ramp);
	if (!err) err = ReadRampHandle(in_data, params[OLMKIRAKIRA_DIAGONAL_RAMP]->u.arb_d.value, &info->diagonal_ramp);
	if (!err) err = ReadRampHandle(in_data, params[OLMKIRAKIRA_HIGHLIGHT_RAMP]->u.arb_d.value, &info->highlight_ramp);
	if (!err) err = ReadRampHandle(in_data, params[OLMKIRAKIRA_DIAGONAL2_RAMP]->u.arb_d.value, &info->diagonal2_ramp);
	info->comp_width = params[OLMKIRAKIRA_INPUT]->u.ld.width;
	return err;
}

static OLMKiraKiraRampData DefaultRampData();

template <typename DecodeT>
static PF_Err CheckoutDecodeSmartParam(
	PF_InData *in_data,
	A_long index,
	DecodeT decode)
{
	PF_ParamDef param;
	AEFX_CLR_STRUCT(param);
	PF_Err err = PF_Err_NONE;
	try {
		err = PF_CHECKOUT_PARAM(in_data, index, in_data->current_time,
			in_data->time_step, in_data->time_scale, &param);
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	if (err) return err;

	PF_Err decode_err = PF_Err_NONE;
	try {
		decode_err = decode(&param);
	} catch (PF_Err &thrown_err) {
		decode_err = thrown_err;
	} catch (const std::bad_alloc &) {
		decode_err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		decode_err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}

	PF_Err checkin_err = PF_Err_NONE;
	try {
		checkin_err = PF_CHECKIN_PARAM(in_data, &param);
	} catch (PF_Err &thrown_err) {
		checkin_err = thrown_err;
	} catch (const std::bad_alloc &) {
		checkin_err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		checkin_err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return decode_err ? decode_err : checkin_err;
}

static PF_Err CheckoutSmartInfo(PF_InData *in_data, OLMKiraKiraInfo *info)
{
	if (!in_data || !info || !in_data->inter.checkout_param ||
		!in_data->inter.checkin_param) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	AEFX_CLR_STRUCT(*info);
	info->vertical_ramp = DefaultRampData();
	info->horizontal_ramp = DefaultRampData();
	info->diagonal_ramp = DefaultRampData();
	info->diagonal2_ramp = DefaultRampData();
	info->highlight_ramp = DefaultRampData();

	// FUN_18114e860 checks parameters in disk-id order. Ramp payloads are
	// checked out only when their immediately preceding use flag is enabled.
#define CHECKOUT_SMART_VALUE(INDEX, BODY) \
	do { \
		const PF_Err checkout_err = CheckoutDecodeSmartParam( \
			in_data, (INDEX), [&](PF_ParamDef *param) -> PF_Err { BODY; return PF_Err_NONE; }); \
		if (checkout_err) return checkout_err; \
	} while (false)
#define CHECKOUT_SMART_DECODE(INDEX, BODY) \
	do { \
		const PF_Err checkout_err = CheckoutDecodeSmartParam( \
			in_data, (INDEX), [&](PF_ParamDef *param) -> PF_Err { BODY; }); \
		if (checkout_err) return checkout_err; \
	} while (false)

	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_GLOW_ROTATION, info->glow_rotation = param->u.fs_d.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_BRIGHTNESS_GAIN, info->brightness_gain = param->u.fs_d.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_STRENGTH_MULTIPLIER, info->strength_multiplier = param->u.sd.value / 100.0);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_FADE_OUT, info->fade_out = param->u.fs_d.value * 0.2);

	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_VERTICAL_LENGTH, info->vertical_length = param->u.sd.value);
	CHECKOUT_SMART_DECODE(OLMKIRAKIRA_VERTICAL_COLOR,
		return CopyColorParam(in_data, param, &info->vertical_color));
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_VERTICAL_USE_RAMP, info->vertical_use_ramp = param->u.bd.value);
	if (info->vertical_use_ramp) {
		CHECKOUT_SMART_DECODE(OLMKIRAKIRA_VERTICAL_RAMP,
			return ReadRampHandle(in_data, param->u.arb_d.value, &info->vertical_ramp));
	}

	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_HORIZONTAL_LENGTH, info->horizontal_length = param->u.sd.value);
	CHECKOUT_SMART_DECODE(OLMKIRAKIRA_HORIZONTAL_COLOR,
		return CopyColorParam(in_data, param, &info->horizontal_color));
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_HORIZONTAL_USE_RAMP, info->horizontal_use_ramp = param->u.bd.value);
	if (info->horizontal_use_ramp) {
		CHECKOUT_SMART_DECODE(OLMKIRAKIRA_HORIZONTAL_RAMP,
			return ReadRampHandle(in_data, param->u.arb_d.value, &info->horizontal_ramp));
	}

	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_DIAGONAL_LENGTH, info->diagonal_length = param->u.sd.value);
	CHECKOUT_SMART_DECODE(OLMKIRAKIRA_DIAGONAL_COLOR,
		return CopyColorParam(in_data, param, &info->diagonal_color));
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_DIAGONAL_USE_RAMP, info->diagonal_use_ramp = param->u.bd.value);
	if (info->diagonal_use_ramp) {
		CHECKOUT_SMART_DECODE(OLMKIRAKIRA_DIAGONAL_RAMP,
			return ReadRampHandle(in_data, param->u.arb_d.value, &info->diagonal_ramp));
	}

	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_DIAGONAL2_LENGTH, info->diagonal2_length = param->u.sd.value);
	CHECKOUT_SMART_DECODE(OLMKIRAKIRA_DIAGONAL2_COLOR,
		return CopyColorParam(in_data, param, &info->diagonal2_color));
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_DIAGONAL2_USE_RAMP, info->diagonal2_use_ramp = param->u.bd.value);
	if (info->diagonal2_use_ramp) {
		CHECKOUT_SMART_DECODE(OLMKIRAKIRA_DIAGONAL2_RAMP,
			return ReadRampHandle(in_data, param->u.arb_d.value, &info->diagonal2_ramp));
	}

	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_HIGHLIGHT_RADIUS, info->highlight_radius = param->u.sd.value);
	CHECKOUT_SMART_DECODE(OLMKIRAKIRA_HIGHLIGHT_COLOR,
		return CopyColorParam(in_data, param, &info->highlight_color));
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_HIGHLIGHT_USE_RAMP, info->highlight_use_ramp = param->u.bd.value);
	if (info->highlight_use_ramp) {
		CHECKOUT_SMART_DECODE(OLMKIRAKIRA_HIGHLIGHT_RAMP,
			return ReadRampHandle(in_data, param->u.arb_d.value, &info->highlight_ramp));
	}

	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_GLOW_OPACITY, info->glow_opacity = param->u.sd.value / 100.0);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_SOURCE_OPACITY, info->source_opacity = param->u.sd.value / 100.0);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_CHANNEL, info->channel = param->u.pd.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_BLUR_MODE, info->blur_mode = param->u.pd.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_MERGE_MODE, info->merge_mode = param->u.pd.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_APPROX_INPUT, info->approximated_input = param->u.bd.value);

#undef CHECKOUT_SMART_DECODE
#undef CHECKOUT_SMART_VALUE
	return PF_Err_NONE;
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

static bool ColorIsClosureWhite(const PF_PixelFloat &color)
{
	return color.alpha == 1.0f && color.red == 1.0f &&
		color.green == 1.0f && color.blue == 1.0f;
}

static bool RampIsClosureDefault(const OLMKiraKiraRampData &ramp)
{
	const OLMKiraKiraRampData expected = DefaultRampData();
	if (ramp.count != expected.count) return false;
	for (A_u_long index = 0; index < expected.count; ++index) {
		const OLMKiraKiraRampStop &actual_stop = ramp.stops[index];
		const OLMKiraKiraRampStop &expected_stop = expected.stops[index];
		if (actual_stop.position != expected_stop.position ||
			actual_stop.alpha != expected_stop.alpha ||
			actual_stop.red != expected_stop.red ||
			actual_stop.green != expected_stop.green ||
			actual_stop.blue != expected_stop.blue) {
			return false;
		}
	}
	return true;
}

enum ClassicClosureSourceFamily {
	ClassicClosureSource_None = 0,
	ClassicClosureSource_SemiTransparentColor,
	ClassicClosureSource_AlphaGradient
};

static ClassicClosureSourceFamily ClassicClosureSourceFamilyForTuple(
	const OLMKiraKiraInfo &info)
{
	// These are the fixed public Classic fixtures closed against the current
	// Windows exported Smart owners.  This is deliberately a tuple map, not a
	// claim that the Cartesian product of the recovered helpers is exact.
	if (info.fade_out != 0.0 || info.glow_opacity != 1.0 ||
		info.channel != 1 || info.approximated_input ||
		info.strength_multiplier != 1.0 || info.source_opacity != 1.0 ||
		info.vertical_length != 0 || info.diagonal_length != 0 ||
		info.vertical_use_ramp || info.diagonal_use_ramp ||
		info.diagonal2_use_ramp) {
		return ClassicClosureSource_None;
	}
	if (!ColorIsClosureWhite(info.vertical_color) ||
		!ColorIsClosureWhite(info.horizontal_color) ||
		!ColorIsClosureWhite(info.diagonal_color) ||
		!ColorIsClosureWhite(info.diagonal2_color) ||
		!ColorIsClosureWhite(info.highlight_color) ||
		!RampIsClosureDefault(info.vertical_ramp) ||
		!RampIsClosureDefault(info.horizontal_ramp) ||
		!RampIsClosureDefault(info.diagonal_ramp) ||
		!RampIsClosureDefault(info.diagonal2_ramp) ||
		!RampIsClosureDefault(info.highlight_ramp)) {
		return ClassicClosureSource_None;
	}

	const bool mode1_horizontal =
		info.blur_mode == 1 && info.merge_mode == 1 &&
		info.brightness_gain == 0.1 &&
		(info.glow_rotation == 0.0 || info.glow_rotation == 1.0) &&
		info.horizontal_length == 7 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 0 &&
		!info.highlight_use_ramp;
	const bool mode1_highlight =
		info.blur_mode == 1 && info.merge_mode == 1 &&
		info.brightness_gain == 1.0 && info.glow_rotation == 0.0 &&
		info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 3 &&
		!info.highlight_use_ramp;
	const bool mode2_horizontal =
		info.blur_mode == 2 && info.merge_mode == 2 &&
		((info.brightness_gain == 0.1 &&
		  (info.glow_rotation == 0.0 || info.glow_rotation == 1.0)) ||
		 (info.brightness_gain == 0.73 && info.glow_rotation == 22.0)) &&
		info.horizontal_length == 7 && info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 0 &&
		!info.highlight_use_ramp;
	const bool mode2_highlight =
		info.blur_mode == 2 && info.merge_mode == 1 &&
		info.brightness_gain == 1.0 && info.glow_rotation == 0.0 &&
		info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 3 &&
		!info.highlight_use_ramp;
	const bool mode3_horizontal =
		info.blur_mode == 3 && info.merge_mode == 1 &&
		info.brightness_gain == 0.1 &&
		(info.glow_rotation == 0.0 || info.glow_rotation == 1.0) &&
		info.horizontal_length == 50 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 0 &&
		!info.highlight_use_ramp;
	const bool mode4_highlight_gradient =
		info.blur_mode == 4 && info.merge_mode == 1 &&
		info.brightness_gain == 1.0 && info.glow_rotation == 0.0 &&
		info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		info.diagonal2_length == 0 && info.highlight_radius == 3 &&
		!info.highlight_use_ramp;
	const bool mode4_declared_family =
		info.blur_mode == 4 && info.merge_mode == 2 &&
		info.brightness_gain == 0.73 && info.glow_rotation == 1.0 &&
		((info.horizontal_length == 5 && info.horizontal_use_ramp &&
		  info.diagonal2_length == 0 && info.highlight_radius == 0 &&
		  !info.highlight_use_ramp) ||
		 (info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		  info.diagonal2_length == 7 && info.highlight_radius == 0 &&
		  !info.highlight_use_ramp) ||
		 (info.horizontal_length == 0 && !info.horizontal_use_ramp &&
		  info.diagonal2_length == 0 && info.highlight_radius == 3 &&
		  info.highlight_use_ramp) ||
		 (info.horizontal_length == 5 && info.horizontal_use_ramp &&
		  info.diagonal2_length == 7 && info.highlight_radius == 3 &&
		  info.highlight_use_ramp));
	if (mode1_highlight || mode2_highlight || mode4_highlight_gradient)
		return ClassicClosureSource_AlphaGradient;
	if (mode1_horizontal || mode2_horizontal || mode3_horizontal ||
		mode4_declared_family)
		return ClassicClosureSource_SemiTransparentColor;
	return ClassicClosureSource_None;
}

static bool IsClassicClosureTuple(const OLMKiraKiraInfo &info)
{
	return ClassicClosureSourceFamilyForTuple(info) != ClassicClosureSource_None;
}

static bool IsGenericBetaFullFrameDimensions(A_long width, A_long height)
{
	// The beta excludes tiny diagnostic leaves. 9x7 is also the minimum used by
	// the geometry-general Mode 3/4 contracts and gives all directional kernels
	// a meaningful border surface. Bound the generic lane to the production
	// range this beta promises: DCI-4K area in either orientation, with neither
	// side exceeding 4096. This also makes every frame-sized allocation and the
	// Mode-3 worst-case Length 300 workload finite before any render allocation.
	constexpr int64_t kMaxGenericPixels = INT64_C(4096) * INT64_C(2160);
	return width >= 9 && height >= 7 && width <= 4096 && height <= 4096 &&
		static_cast<int64_t>(width) * static_cast<int64_t>(height) <=
			kMaxGenericPixels;
}

// Generic beta lane: retain the parameter tuples already closed against the
// Windows owners, but allow their Mode 1-4 algorithms to consume arbitrary
// full-frame source pixels and ordinary host layouts. Keeping this separate
// from the exact closure makes the weaker compatibility claim explicit.
static bool IsGenericBetaMode12Tuple(const OLMKiraKiraInfo &info)
{
	return (info.blur_mode == 1 || info.blur_mode == 2) &&
		ClassicClosureSourceFamilyForTuple(info) != ClassicClosureSource_None;
}

static bool IsGenericBetaMode3HorizontalTuple(const OLMKiraKiraInfo &info)
{
	// Keep the fixed Windows-exported closure at Length 50. The generic lane
	// reuses that tuple's remaining controls while admitting the complete
	// visible UI Length range grounded by the recovered Mode-3 helper chain.
	if (info.blur_mode != 3 || info.horizontal_length < 1 ||
		info.horizontal_length > 300) {
		return false;
	}
	OLMKiraKiraInfo owner_tuple = info;
	owner_tuple.horizontal_length = 50;
	return ClassicClosureSourceFamilyForTuple(owner_tuple) ==
		ClassicClosureSource_SemiTransparentColor;
}

static bool KiraCheckedMultiply(uint64_t left, uint64_t right, uint64_t *out)
{
	if (!out || (right != 0 && left > UINT64_MAX / right)) return false;
	*out = left * right;
	return true;
}

static bool KiraCheckedAdd(uint64_t left, uint64_t right, uint64_t *out)
{
	if (!out || left > UINT64_MAX - right) return false;
	*out = left + right;
	return true;
}

static bool IsGenericBetaMode3BudgetAdmitted(
	const OLMKiraKiraInfo &info,
	A_long width,
	A_long height)
{
	if (!IsGenericBetaMode3HorizontalTuple(info) ||
		!IsGenericBetaFullFrameDimensions(width, height)) {
		return false;
	}
	const double pi = 3.14159265358979323846;
	const double radians = info.glow_rotation * pi / 180.0;
	const double absolute_cosine = std::abs(std::cos(radians));
	const double absolute_sine = std::abs(std::sin(radians));
	const A_long rotated_width =
		AexRotatedExtent(width, height, absolute_cosine, absolute_sine);
	const A_long rotated_height =
		AexRotatedExtent(height, width, absolute_cosine, absolute_sine);
	if (rotated_width <= 0 || rotated_height <= 0) return false;

	uint64_t frame_pixels = 0;
	uint64_t rotated_pixels = 0;
	if (!KiraCheckedMultiply(static_cast<uint64_t>(width),
			static_cast<uint64_t>(height), &frame_pixels) ||
		!KiraCheckedMultiply(static_cast<uint64_t>(rotated_width),
			static_cast<uint64_t>(rotated_height), &rotated_pixels)) {
		return false;
	}
	const uint64_t kernel_taps =
		static_cast<uint64_t>(info.horizontal_length) * 4u + 1u;
	const uint64_t radius =
		static_cast<uint64_t>(info.horizontal_length) * 2u;
	const uint64_t reflect_period =
		static_cast<uint64_t>(rotated_width - 1);
	const uint64_t reflect_fold = std::max<uint64_t>(
		1u, (radius + reflect_period - 1u) / reflect_period);
	uint64_t gaussian_work_units = 0;
	uint64_t folded_gaussian_work_units = 0;
	uint64_t warp_work_units = 0;
	uint64_t outer_work_units = 0;
	uint64_t work_units = 0;
	if (!KiraCheckedMultiply(rotated_pixels, kernel_taps,
			&gaussian_work_units) ||
		!KiraCheckedMultiply(gaussian_work_units, reflect_fold,
			&folded_gaussian_work_units) ||
		!KiraCheckedMultiply(rotated_pixels, 8u, &warp_work_units) ||
		!KiraCheckedMultiply(frame_pixels, 20u, &outer_work_units) ||
		!KiraCheckedAdd(folded_gaussian_work_units, warp_work_units,
			&work_units) ||
		!KiraCheckedAdd(work_units, outer_work_units, &work_units))
		return false;

	uint64_t steady_bytes = 0;
	uint64_t ray_frame_bytes = 0;
	uint64_t ray_rotated_bytes = 0;
	uint64_t ray_peak_bytes = 0;
	uint64_t compose_frame_bytes = 0;
	uint64_t compose_rotated_bytes = 0;
	uint64_t compose_peak_bytes = 0;
	uint64_t kernel_bytes = 0;
	uint64_t peak_bytes = 0;
	if (!KiraCheckedMultiply(frame_pixels, 92u, &steady_bytes) ||
		!KiraCheckedMultiply(frame_pixels, 44u, &ray_frame_bytes) ||
		!KiraCheckedMultiply(rotated_pixels, 12u, &ray_rotated_bytes) ||
		!KiraCheckedAdd(ray_frame_bytes, ray_rotated_bytes, &ray_peak_bytes) ||
		!KiraCheckedMultiply(frame_pixels, 48u, &compose_frame_bytes) ||
		!KiraCheckedMultiply(rotated_pixels, 8u, &compose_rotated_bytes) ||
		!KiraCheckedAdd(compose_frame_bytes, compose_rotated_bytes,
			&compose_peak_bytes) ||
		!KiraCheckedMultiply(kernel_taps, 12u, &kernel_bytes) ||
		!KiraCheckedAdd(std::max({steady_bytes, ray_peak_bytes,
			compose_peak_bytes}), kernel_bytes, &peak_bytes)) {
		return false;
	}

	constexpr uint64_t kMaxPluginOwnedBytes = UINT64_C(1) << 30;
	constexpr uint64_t kMaxMode3WorkUnits = UINT64_C(12000000000);
	return peak_bytes <= kMaxPluginOwnedBytes &&
		work_units <= kMaxMode3WorkUnits;
}

static bool GenericBetaDirectionalRayIsAdmitted(
	A_long width,
	A_long height,
	A_long length,
	double angle_degrees,
	A_long blur_mode)
{
	if (length <= 0) return true;
	const double pi = 3.14159265358979323846;
	const double radians = angle_degrees * pi / 180.0;
	const double absolute_cosine = std::abs(std::cos(radians));
	const double absolute_sine = std::abs(std::sin(radians));
	const A_long rotated_width =
		AexRotatedExtent(width, height, absolute_cosine, absolute_sine);
	const A_long rotated_height =
		AexRotatedExtent(height, width, absolute_cosine, absolute_sine);
	if (blur_mode == 3) {
		return olm::kirakira::mode3_gaussian_admitted(
			rotated_width, rotated_height, length);
	}
	if (blur_mode == 4) {
		return olm::kirakira::mode4_rotated_scalar_admitted(
			rotated_width, rotated_height, length, angle_degrees);
	}
	return false;
}

static bool IsGenericBetaMode34TupleForGeometry(
	const OLMKiraKiraInfo &info,
	A_long width,
	A_long height)
{
	if ((info.blur_mode != 3 && info.blur_mode != 4) ||
		!IsGenericBetaFullFrameDimensions(width, height)) {
		return false;
	}
	const bool tuple_is_admitted = info.blur_mode == 3
		? IsGenericBetaMode3BudgetAdmitted(info, width, height)
		: ClassicClosureSourceFamilyForTuple(info) != ClassicClosureSource_None;
	if (!tuple_is_admitted) return false;
	return GenericBetaDirectionalRayIsAdmitted(
			width, height, info.vertical_length,
			90.0 + info.glow_rotation, info.blur_mode) &&
		GenericBetaDirectionalRayIsAdmitted(
			width, height, info.horizontal_length,
			info.glow_rotation, info.blur_mode) &&
		GenericBetaDirectionalRayIsAdmitted(
			width, height, info.diagonal_length,
			45.0 + info.glow_rotation, info.blur_mode) &&
		GenericBetaDirectionalRayIsAdmitted(
			width, height, info.diagonal2_length,
			135.0 + info.glow_rotation, info.blur_mode);
}

static bool IsGenericBetaTupleForGeometry(
	const OLMKiraKiraInfo &info,
	A_long width,
	A_long height)
{
	return (IsGenericBetaMode12Tuple(info) &&
			IsGenericBetaFullFrameDimensions(width, height)) ||
		IsGenericBetaMode34TupleForGeometry(info, width, height);
}

static bool WorldStorageRangesDoNotOverlap(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output);

static bool IsGenericBetaClassicLayout(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output)
{
	return input && output &&
		IsGenericBetaFullFrameDimensions(input->width, input->height) &&
		input->width == output->width && input->height == output->height &&
		input->origin_x == 0 && input->origin_y == 0 &&
		output->origin_x == 0 && output->origin_y == 0 &&
		WorldStorageRangesDoNotOverlap(input, output);
}

static bool IsMode3Closure32x18Tuple(const OLMKiraKiraInfo &info)
{
	// This is a separate one-fixture admission.  The 5x3 Mode3 family also
	// contains Rotation 1, but only Rotation 0 has a same-source 32x18
	// exported-Smart oracle at all three public pixel depths.
	return ClassicClosureSourceFamilyForTuple(info) ==
			ClassicClosureSource_SemiTransparentColor &&
		info.blur_mode == 3 && info.merge_mode == 1 &&
		info.glow_rotation == 0.0 && info.brightness_gain == 0.1 &&
		info.horizontal_length == 50 && !info.horizontal_use_ramp;
}

static bool IsClassicClosureLayout(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	PF_PixelFormat format)
{
	const size_t pixel_size = PixelSizeForFormat(format);
	if (!pixel_size || input->width != 5 || input->height != 3 ||
		output->width != 5 || output->height != 3 ||
		input->origin_x != 0 || input->origin_y != 0 ||
		output->origin_x != 0 || output->origin_y != 0) {
		return false;
	}
	const int64_t closure_rowbytes =
		5 * static_cast<int64_t>(pixel_size) + 12;
	return input->rowbytes == closure_rowbytes &&
		output->rowbytes == closure_rowbytes &&
		input->extent_hint.left == 0 && input->extent_hint.top == 0 &&
		input->extent_hint.right == 5 && input->extent_hint.bottom == 3 &&
		output->extent_hint.left == 0 && output->extent_hint.top == 0 &&
		output->extent_hint.right == 5 && output->extent_hint.bottom == 3;
}

static bool IsMode3Closure32x18Layout(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	PF_PixelFormat format)
{
	const size_t pixel_size = PixelSizeForFormat(format);
	if (!pixel_size || !input || !output ||
		input->width != 32 || input->height != 18 ||
		output->width != 32 || output->height != 18 ||
		input->origin_x != 0 || input->origin_y != 0 ||
		output->origin_x != 0 || output->origin_y != 0) {
		return false;
	}
	const int64_t closure_rowbytes =
		32 * static_cast<int64_t>(pixel_size) + 12;
	return input->rowbytes == closure_rowbytes &&
		output->rowbytes == closure_rowbytes &&
		input->extent_hint.left == 0 && input->extent_hint.top == 0 &&
		input->extent_hint.right == 32 && input->extent_hint.bottom == 18 &&
		output->extent_hint.left == 0 && output->extent_hint.top == 0 &&
		output->extent_hint.right == 32 && output->extent_hint.bottom == 18;
}

static A_u_short ClosureByteToPF16(A_u_char value)
{
	return static_cast<A_u_short>(std::lround(
		static_cast<double>(value) * 32768.0 / 255.0));
}

static bool ClosureFloatBitsEqual(float actual, float expected)
{
	uint32_t actual_bits = 0;
	uint32_t expected_bits = 0;
	std::memcpy(&actual_bits, &actual, sizeof(actual_bits));
	std::memcpy(&expected_bits, &expected, sizeof(expected_bits));
	return actual_bits == expected_bits;
}

static bool ClassicClosureSourceMatches(
	const PF_EffectWorld *input,
	PF_PixelFormat format,
	ClassicClosureSourceFamily family)
{
	if (!input || family == ClassicClosureSource_None) return false;
	for (A_long y = 0; y < input->height; ++y) {
		for (A_long x = 0; x < input->width; ++x) {
			const A_long index = y * input->width + x;
			const A_u_char red = family == ClassicClosureSource_AlphaGradient ?
				0 : static_cast<A_u_char>(index * 15);
			const A_u_char green = family == ClassicClosureSource_AlphaGradient ?
				0 : static_cast<A_u_char>(index * 11);
			const A_u_char blue = family == ClassicClosureSource_AlphaGradient ?
				0 : static_cast<A_u_char>(index * 7);
			const A_u_char alpha = family == ClassicClosureSource_AlphaGradient ?
				static_cast<A_u_char>(index * 15) :
				static_cast<A_u_char>(64 + index * 11);
			switch (format) {
				case PF_PixelFormat_ARGB32: {
					const PF_Pixel8 &actual = *PixelAtConst<PF_Pixel8>(input, x, y);
					if (actual.alpha != alpha || actual.red != red ||
						actual.green != green || actual.blue != blue) return false;
					break;
				}
				case PF_PixelFormat_ARGB64: {
					const PF_Pixel16 &actual = *PixelAtConst<PF_Pixel16>(input, x, y);
					if (actual.alpha != ClosureByteToPF16(alpha) ||
						actual.red != ClosureByteToPF16(red) ||
						actual.green != ClosureByteToPF16(green) ||
						actual.blue != ClosureByteToPF16(blue)) return false;
					break;
				}
				case PF_PixelFormat_ARGB128: {
					const PF_PixelFloat &actual =
						*PixelAtConst<PF_PixelFloat>(input, x, y);
					if (!ClosureFloatBitsEqual(actual.alpha,
							static_cast<float>(alpha) / 255.0f) ||
						!ClosureFloatBitsEqual(actual.red,
							static_cast<float>(red) / 255.0f) ||
						!ClosureFloatBitsEqual(actual.green,
							static_cast<float>(green) / 255.0f) ||
						!ClosureFloatBitsEqual(actual.blue,
							static_cast<float>(blue) / 255.0f)) return false;
					break;
				}
				default:
					return false;
			}
		}
	}
	return true;
}

static bool GenericBetaInputIsFiniteSDR(
	const PF_EffectWorld *input,
	PF_PixelFormat format)
{
	if (!input) return false;
	if (format == PF_PixelFormat_ARGB32) return true;
	for (A_long y = 0; y < input->height; ++y) {
		for (A_long x = 0; x < input->width; ++x) {
			if (format == PF_PixelFormat_ARGB64) {
				const PF_Pixel16 &pixel = *PixelAtConst<PF_Pixel16>(input, x, y);
				if (pixel.alpha > PF_MAX_CHAN16 || pixel.red > PF_MAX_CHAN16 ||
					pixel.green > PF_MAX_CHAN16 || pixel.blue > PF_MAX_CHAN16) {
					return false;
				}
			} else if (format == PF_PixelFormat_ARGB128) {
				const PF_PixelFloat &pixel =
					*PixelAtConst<PF_PixelFloat>(input, x, y);
				const float lanes[] = {
					pixel.alpha, pixel.red, pixel.green, pixel.blue
				};
				for (float lane : lanes) {
					if (!std::isfinite(lane) || lane < 0.0f || lane > 1.0f)
						return false;
				}
			} else {
				return false;
			}
		}
	}
	return true;
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
	KiraDiagnosticLog("classic enter");
	PF_Err err = PF_Err_NONE;
	if (!in_data || !in_data->pica_basicP || !out_data || !params || !output ||
		!params[OLMKIRAKIRA_INPUT]) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	for (A_long index = 0; index < OLMKIRAKIRA_NUM_PARAMS; ++index) {
		if (!params[index]) return PF_Err_BAD_CALLBACK_PARAM;
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
		IsGenericBetaTupleForGeometry(info, input->width, input->height) &&
		IsGenericBetaClassicLayout(input, output) &&
		GenericBetaInputIsFiniteSDR(input, format);
	KiraDiagnosticLog("classic admission exact=%d generic=%d family=%d",
		(int)exact_closure, (int)generic_beta, (int)source_family);
	if (!exact_closure && !generic_beta) {
		KiraDiagnosticLog("classic reject tuple_layout_source");
		return PF_Err_BAD_CALLBACK_PARAM;
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

static PF_LRect FullSmartClosureRect()
{
	PF_LRect rect = {0, 0, kSmartClosureWidth, kSmartClosureHeight};
	return rect;
}

static bool RectIsFullSmartClosure(const PF_LRect &rect)
{
	return rect.left == 0 && rect.top == 0 &&
		rect.right == kSmartClosureWidth && rect.bottom == kSmartClosureHeight;
}

static bool SmartOutputRequestIsAdmitted(const PF_LRect &rect)
{
	return RectIsFullSmartClosure(rect) ||
		(rect.left == 1 && rect.top == 1 &&
		 rect.right == 4 && rect.bottom == 3) ||
		(rect.left == 0 && rect.top == 0 &&
		 rect.right == kMode3SmartClosureWidth &&
		 rect.bottom == kMode3SmartClosureHeight);
}

static bool RectIsFullMode3SmartClosure(const PF_LRect &rect)
{
	return rect.left == 0 && rect.top == 0 &&
		rect.right == kMode3SmartClosureWidth &&
		rect.bottom == kMode3SmartClosureHeight;
}

static bool GenericBetaRenderDimensions(
	const PF_InData *in_data,
	A_long *width,
	A_long *height)
{
	if (!in_data || !width || !height || in_data->width <= 0 || in_data->height <= 0 ||
		in_data->downsample_x.num <= 0 || in_data->downsample_x.den <= 0 ||
		in_data->downsample_y.num <= 0 || in_data->downsample_y.den <= 0 ||
		in_data->downsample_x.num != in_data->downsample_x.den ||
		in_data->downsample_y.num != in_data->downsample_y.den) {
		return false;
	}
	if (!IsGenericBetaFullFrameDimensions(in_data->width, in_data->height)) {
		return false;
	}
	*width = in_data->width;
	*height = in_data->height;
	return true;
}

static bool WorldHasFullSmartClosureExtent(const PF_EffectWorld *world)
{
	return world && world->extent_hint.left == 0 && world->extent_hint.top == 0 &&
		world->extent_hint.right == kSmartClosureWidth &&
		world->extent_hint.bottom == kSmartClosureHeight;
}

static bool WorldStorageRangesDoNotOverlap(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output)
{
	if (!input || !output || !input->data || !output->data ||
		input->rowbytes <= 0 || output->rowbytes <= 0 ||
		input->height <= 0 || output->height <= 0) {
		return false;
	}
	const uint64_t input_span = static_cast<uint64_t>(input->rowbytes) *
		static_cast<uint64_t>(input->height);
	const uint64_t output_span = static_cast<uint64_t>(output->rowbytes) *
		static_cast<uint64_t>(output->height);
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
	const int64_t expected_rowbytes =
		static_cast<int64_t>(width) *
		static_cast<int64_t>(pixel_size) + 12;
	return pixel_size && input && output &&
		input->width == width && input->height == height &&
		output->width == width && output->height == height &&
		input->origin_x == 0 && input->origin_y == 0 &&
		output->origin_x == 0 && output->origin_y == 0 &&
		input->extent_hint.left == 0 && input->extent_hint.top == 0 &&
		input->extent_hint.right == width && input->extent_hint.bottom == height &&
		output->extent_hint.left == 0 && output->extent_hint.top == 0 &&
		output->extent_hint.right == width && output->extent_hint.bottom == height &&
		input->rowbytes == expected_rowbytes && output->rowbytes == expected_rowbytes &&
		input->world_flags == expected_world_flags &&
		output->world_flags == expected_world_flags &&
		WorldStorageRangesDoNotOverlap(input, output);
}

static bool SmartGenericBetaWorldPairIsFullFrame(
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	A_long width,
	A_long height)
{
	return input && output &&
		IsGenericBetaFullFrameDimensions(width, height) &&
		input->width == width && input->height == height &&
		output->width == width && output->height == height &&
		input->origin_x == 0 && input->origin_y == 0 &&
		output->origin_x == 0 && output->origin_y == 0 &&
		WorldStorageRangesDoNotOverlap(input, output);
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
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const PF_LRect &requested_rect = extra->input->output_request.rect;
	A_long generic_render_width = 0;
	A_long generic_render_height = 0;
	const bool has_generic_render_dimensions = GenericBetaRenderDimensions(
		in_data, &generic_render_width, &generic_render_height);
	const bool request_contains_generic_full_frame =
		has_generic_render_dimensions && requested_rect.left <= 0 &&
		requested_rect.top <= 0 && requested_rect.right >= generic_render_width &&
		requested_rect.bottom >= generic_render_height;
	const bool mode3_32x18_request =
		RectIsFullMode3SmartClosure(requested_rect);
	const bool frame_dimensions_are_known =
		in_data->width > 0 && in_data->height > 0;
	const bool known_frame_is_one_to_one = frame_dimensions_are_known &&
		in_data->downsample_x.num > 0 && in_data->downsample_x.den > 0 &&
		in_data->downsample_y.num > 0 && in_data->downsample_y.den > 0 &&
		in_data->downsample_x.num == in_data->downsample_x.den &&
		in_data->downsample_y.num == in_data->downsample_y.den;
	const bool request_contains_known_full_frame = known_frame_is_one_to_one &&
		requested_rect.left <= 0 && requested_rect.top <= 0 &&
		requested_rect.right >= in_data->width &&
		requested_rect.bottom >= in_data->height;
	// Keep generic ROI/tile requests closed.  The isotropic Highlight branch has
	// finite per-axis halo passes * radius (Mode 1: radius, Modes 2/4: 3*radius).
	// Directional Modes 1/2 use rotated-axis R = passes*max(floor(L/2),
	// L-floor(L/2)-1), and Mode 3 uses R=2L.  Including both bilinear warps, a
	// conservative source halo is Hx=ceil(R*abs(cos(theta))+2*(abs(cos(theta))+
	// abs(sin(theta)))) and the corresponding Hy with sin(theta).  Those modes
	// are finite, but every directional branch constructs its rotated canvas and
	// center from full-frame dimensions.  Mode 4 additionally uses a bidirectional IIR
	// recurrence whose support reaches the row boundary.  A tile-local world
	// therefore changes coordinates and, for Mode 4, cannot have a finite exact
	// halo.  Until SmartRender carries full-comp coordinates and a proved subset
	// admission, only requests containing the complete frame may be normalized.
	// Preserve the historical 5x3 requests. The separate 32x18 owner is only
	// valid for an unknown legacy host geometry or for a proved 1:1 full-frame
	// request; being outside the generic SD-DCI cap must not make dimensions
	// appear unknown and reopen a partial exact tile.
	const bool exact_request_matches_known_frame =
		SmartOutputRequestIsAdmitted(requested_rect) &&
		(!mode3_32x18_request || !frame_dimensions_are_known ||
		 request_contains_known_full_frame);
	if (!exact_request_matches_known_frame &&
		!request_contains_generic_full_frame) {
		KiraDiagnosticLog("pre reject request_not_admitted");
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);

	const bool generic_beta_request =
		!RectIsFullSmartClosure(requested_rect) &&
		request_contains_generic_full_frame;
	const PF_LRect full_rect = generic_beta_request
		? PF_LRect{0, 0, generic_render_width, generic_render_height}
		: (mode3_32x18_request
			? PF_LRect{0, 0, kMode3SmartClosureWidth, kMode3SmartClosureHeight}
			: FullSmartClosureRect());
	req.rect = full_rect;
	req.preserve_rgb_of_zero_alpha = TRUE;
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
	const A_long expected_width = full_rect.right;
	const A_long expected_height = full_rect.bottom;
	const bool exact_checkout_rects_are_full =
		in_result.result_rect.left == 0 && in_result.result_rect.top == 0 &&
		in_result.result_rect.right == expected_width &&
		in_result.result_rect.bottom == expected_height &&
		in_result.max_result_rect.left == 0 &&
		in_result.max_result_rect.top == 0 &&
		in_result.max_result_rect.right == expected_width &&
		in_result.max_result_rect.bottom == expected_height;
	// result_rect/max_result_rect describe content, not storage. Generic
	// arbitrary images may therefore report empty or partial content bounds;
	// ref_width/ref_height and the Smart worlds remain the storage authority.
	if (in_result.ref_width != expected_width ||
		in_result.ref_height != expected_height ||
		(!generic_beta_request && !exact_checkout_rects_are_full)) {
		KiraDiagnosticLog("pre reject checkout_geometry expected=%ldx%ld",
			(long)expected_width, (long)expected_height);
		return PF_Err_BAD_CALLBACK_PARAM;
	}

	PreRenderData *pre = new (std::nothrow) PreRenderData;
	if (!pre) {
		KiraDiagnosticLog("pre reject allocation");
		return PF_Err_OUT_OF_MEMORY;
	}
	pre->comp_width = expected_width;
	pre->comp_height = expected_height;
	pre->generic_full_frame_request = generic_beta_request;
	extra->output->result_rect = full_rect;
	extra->output->max_result_rect = full_rect;
	extra->output->flags |= PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS;
	extra->output->pre_render_data = pre;
	extra->output->delete_pre_render_data_func = DeletePreRenderData;
	KiraDiagnosticLog("pre success dimensions=%ldx%ld generic=%d mode3_32=%d",
		(long)expected_width, (long)expected_height,
		(int)generic_beta_request, (int)mode3_32x18_request);
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
		return PF_Err_BAD_CALLBACK_PARAM;
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
				extra->input->bitdepth, &format);
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
			IsGenericBetaFullFrameDimensions(
				static_cast<A_long>(pre->comp_width),
				static_cast<A_long>(pre->comp_height));
		const bool exact_world_layout =
			(pre_is_classic || pre_is_mode3_32x18) &&
			SmartClosureWorldPairIsSafeForDimensions(
				input_world, output_world, format,
				static_cast<A_long>(pre->comp_width),
				static_cast<A_long>(pre->comp_height));
		const bool generic_world_layout = pre_is_generic_beta &&
			SmartGenericBetaWorldPairIsFullFrame(
				input_world, output_world,
				static_cast<A_long>(pre->comp_width),
				static_cast<A_long>(pre->comp_height));
		KiraDiagnosticLog(
			"smart layout pre_classic=%d pre_mode3_32=%d pre_generic=%d exact=%d generic=%d pre=%gx%g",
			(int)pre_is_classic, (int)pre_is_mode3_32x18,
			(int)pre_is_generic_beta, (int)exact_world_layout,
			(int)generic_world_layout,
			pre ? (double)pre->comp_width : -1.0,
			pre ? (double)pre->comp_height : -1.0);
		if (!err && !exact_world_layout && !generic_world_layout) {
			err = PF_Err_BAD_CALLBACK_PARAM;
			KiraDiagnosticLog("smart reject world_layout");
		}
		OLMKiraKiraInfo info;
		if (!err) err = CheckoutSmartInfo(in_data, &info);
		KiraDiagnosticLog("smart checkout_info error=%d", (int)err);
		if (!err) {
			info.comp_width = pre->comp_width;
			KiraDiagnosticInfo("smart", info);
			const ClassicClosureSourceFamily source_family =
				ClassicClosureSourceFamilyForTuple(info);
			const bool exact_tuple_is_admitted =
				(pre_is_classic && IsClassicClosureTuple(info)) ||
				(pre_is_mode3_32x18 && IsMode3Closure32x18Tuple(info));
			// The exact fixture remains isolated only when source and historical
			// storage layout both match. Safe deviations are generic evidence and
			// must satisfy its SDR, non-overlap, geometry, and budget checks.
			const bool exact_closure = exact_world_layout &&
				exact_tuple_is_admitted &&
				source_family != ClassicClosureSource_None &&
				ClassicClosureSourceMatches(input_world, format, source_family);
			const bool generic_beta = !exact_closure &&
				generic_world_layout && pre_is_generic_beta &&
				IsGenericBetaTupleForGeometry(
					info, input_world->width, input_world->height) &&
				GenericBetaInputIsFiniteSDR(input_world, format);
			KiraDiagnosticLog(
				"smart admission family=%d exact_tuple=%d exact=%d generic=%d",
				(int)source_family, (int)exact_tuple_is_admitted,
				(int)exact_closure, (int)generic_beta);
			if (!exact_closure && !generic_beta) {
				err = PF_Err_BAD_CALLBACK_PARAM;
				KiraDiagnosticLog("smart reject tuple_or_source");
			}
		}
		if (!err) {
			err = RenderWorld(input_world, output_world, info,
				BitDepthForFormat(format));
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

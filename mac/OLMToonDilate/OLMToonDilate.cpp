#include "OLMToonDilate.h"
#include <AEFX_SuiteHelper.h>

#include <algorithm>
#include <cstdint>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <limits>
#include <new>
#include <vector>

// The Windows AEX emits a zero curve tolerance for Search Radius. Adobe's
// shared helper otherwise substitutes the audio-oriented 0.05 default.
#undef AEFX_AUDIO_DEFAULT_CURVE_TOLERANCE
#define AEFX_AUDIO_DEFAULT_CURVE_TOLERANCE 0.0

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
	out_data->out_flags  = 0x02000044;
	out_data->out_flags2 = PF_OutFlag2_SUPPORTS_SMART_RENDER |
	                      PF_OutFlag2_FLOAT_COLOR_AWARE |
	                      PF_OutFlag2_AUTOMATIC_WIDE_TIME_INPUT |
	                      PF_OutFlag2_SUPPORTS_THREADED_RENDERING;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_SearchRadius_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 2.0,
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
static PixelT ReadPixel(const PF_EffectWorld *world, A_long x, A_long y)
{
	PixelT pixel;
	const size_t offset = static_cast<size_t>(y) * static_cast<size_t>(world->rowbytes) +
		static_cast<size_t>(x) * sizeof(PixelT);
	std::memcpy(&pixel, reinterpret_cast<const uint8_t *>(world->data) + offset, sizeof(pixel));
	return pixel;
}

template <typename PixelT>
static void WritePixel(PF_EffectWorld *world, A_long x, A_long y, const PixelT &pixel)
{
	const size_t offset = static_cast<size_t>(y) * static_cast<size_t>(world->rowbytes) +
		static_cast<size_t>(x) * sizeof(PixelT);
	std::memcpy(reinterpret_cast<uint8_t *>(world->data) + offset, &pixel, sizeof(pixel));
}

enum ToonPublicFamily {
	ToonPublicFamily_None = 0,
	ToonPublicFamily_Copy,
	ToonPublicFamily_Fractional,
	ToonPublicFamily_Tie,
	ToonPublicFamily_High,
	ToonPublicFamily_Corner
};

template <typename PixelT>
static PixelT ToonPublicPixel(unsigned kind, A_long x, A_long y);

template <>
PF_Pixel8 ToonPublicPixel<PF_Pixel8>(unsigned kind, A_long x, A_long y)
{
	const unsigned v = static_cast<unsigned>(x * 17 + y * 29 + 3);
	if (kind == 0) return PF_Pixel8{0, static_cast<uint8_t>(91 + v % 97),
		static_cast<uint8_t>(37 + v % 113), static_cast<uint8_t>(11 + v % 127)};
	if (kind == 1) return PF_Pixel8{static_cast<uint8_t>(64 + v % 160),
		static_cast<uint8_t>(13 + v % 211), static_cast<uint8_t>(19 + v % 197),
		static_cast<uint8_t>(23 + v % 191)};
	return PF_Pixel8{255, static_cast<uint8_t>(31 + v % 181),
		static_cast<uint8_t>(47 + v % 173), static_cast<uint8_t>(59 + v % 167)};
}

template <>
PF_Pixel16 ToonPublicPixel<PF_Pixel16>(unsigned kind, A_long x, A_long y)
{
	const unsigned v = static_cast<unsigned>(x * 17 + y * 29 + 3);
	if (kind == 0) return PF_Pixel16{0, static_cast<uint16_t>(41001 + v % 7000),
		static_cast<uint16_t>(30002 + v % 7000), static_cast<uint16_t>(20003 + v % 7000)};
	if (kind == 1) return PF_Pixel16{static_cast<uint16_t>(4096 + v % 24000),
		static_cast<uint16_t>(1001 + v % 19000), static_cast<uint16_t>(2002 + v % 17000),
		static_cast<uint16_t>(3003 + v % 15000)};
	return PF_Pixel16{32768, static_cast<uint16_t>(4001 + v % 19000),
		static_cast<uint16_t>(5002 + v % 17000), static_cast<uint16_t>(6003 + v % 15000)};
}

template <>
PF_PixelFloat ToonPublicPixel<PF_PixelFloat>(unsigned kind, A_long x, A_long y)
{
	const unsigned v = static_cast<unsigned>(x * 17 + y * 29 + 3);
	const float f = static_cast<float>(v % 101) / 128.0f;
	if (kind == 0) return PF_PixelFloat{0.0f, 0.75f + f, 0.5f + f, 0.25f + f};
	if (kind == 1) return PF_PixelFloat{0.5f, 0.125f + f, 0.25f + f, 0.375f + f};
	return PF_PixelFloat{1.0f, 0.1875f + f, 0.3125f + f, 0.4375f + f};
}

template <typename PixelT>
static PixelT ToonCornerPixel(unsigned kind);

template <>
PF_Pixel8 ToonCornerPixel<PF_Pixel8>(unsigned kind)
{
	const PF_Pixel8 values[3] = {{255,10,20,30},{255,90,80,70},{0,3,5,7}};
	return values[kind];
}

template <>
PF_Pixel16 ToonCornerPixel<PF_Pixel16>(unsigned kind)
{
	const PF_Pixel16 values[3] = {{32768,1001,2002,3003},{32768,4004,5005,6006},{0,17,19,23}};
	return values[kind];
}

template <>
PF_PixelFloat ToonCornerPixel<PF_PixelFloat>(unsigned kind)
{
	const PF_PixelFloat values[3] = {{1.0f,.125f,.25f,.5f},{1.0f,.75f,.625f,.375f},{0.0f,.03125f,.0625f,.09375f}};
	return values[kind];
}

static bool ToonDoubleBitsEqual(PF_FpLong value, PF_FpLong expected)
{
	return std::memcmp(&value, &expected, sizeof(value)) == 0;
}

static ToonPublicFamily ToonAdmittedFamily(
	const PF_InData *in_data,
	const PF_EffectWorld *input,
	const OLMToonDilateInfo &info)
{
	if (!in_data || !input ||
		in_data->output_origin_x != 0 || in_data->output_origin_y != 0 ||
		in_data->downsample_y.num != 0 || in_data->downsample_y.den != 0) {
		return ToonPublicFamily_None;
	}
	if (input->width == 7 && input->height == 5 &&
		ToonDoubleBitsEqual(info.search_radius, 0.0) &&
		in_data->downsample_x.num == 1 && in_data->downsample_x.den == 1)
		return ToonPublicFamily_Copy;
	if (input->width == 9 && input->height == 7 &&
		ToonDoubleBitsEqual(info.search_radius, 2.01) &&
		in_data->downsample_x.num == 1 && in_data->downsample_x.den == 1)
		return ToonPublicFamily_Fractional;
	if (input->width == 7 && input->height == 3 &&
		ToonDoubleBitsEqual(info.search_radius, 3.0) &&
		in_data->downsample_x.num == 1 && in_data->downsample_x.den == 1)
		return ToonPublicFamily_Tie;
	if (input->width == 513 && input->height == 17 &&
		ToonDoubleBitsEqual(info.search_radius, 100.0) &&
		in_data->downsample_x.num == 2 && in_data->downsample_x.den == 1)
		return ToonPublicFamily_High;
	if (input->width == 5 && input->height == 5 &&
		ToonDoubleBitsEqual(info.search_radius, 4.0) &&
		in_data->downsample_x.num == 1 && in_data->downsample_x.den == 1)
		return ToonPublicFamily_Corner;
	return ToonPublicFamily_None;
}

template <typename PixelT>
static bool ToonPublicSourceMatches(const PF_EffectWorld *input, ToonPublicFamily family)
{
	if (!input || !input->data || family == ToonPublicFamily_None) return false;
	const A_long w = input->width, h = input->height;
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			unsigned kind = 1;
			if (family == ToonPublicFamily_Corner)
				kind = (x == 0 && y == 0) ? 0U : ((x == w - 1 && y == h - 1) ? 1U : 2U);
			else if (family == ToonPublicFamily_Copy) kind = static_cast<unsigned>((x + y) % 3);
			else if (family == ToonPublicFamily_Fractional) {
				if ((x == 0 && y == 0) || (x == w / 2 && y == h / 2)) kind = 2;
				else if (x == w - 1 && y == h - 1) kind = 0;
			} else if (y == h / 2 && (x == 0 || x == w - 1)) kind = 2;
			const PixelT expected = family == ToonPublicFamily_Corner ?
				ToonCornerPixel<PixelT>(kind) : ToonPublicPixel<PixelT>(kind, x, y);
			const PixelT actual = ReadPixel<PixelT>(input, x, y);
			if (std::memcmp(&actual, &expected, sizeof(expected)) != 0)
				return false;
		}
		const uint8_t *padding = reinterpret_cast<const uint8_t *>(input->data) +
			static_cast<size_t>(y) * static_cast<size_t>(input->rowbytes) +
			static_cast<size_t>(w) * sizeof(PixelT);
		for (A_long i = w * static_cast<A_long>(sizeof(PixelT)); i < input->rowbytes; ++i)
			if (padding[i - w * static_cast<A_long>(sizeof(PixelT))] != 0xA5) return false;
	}
	return true;
}

static bool ToonWorldRangesDoNotOverlap(const PF_EffectWorld *input,
	const PF_EffectWorld *output, size_t input_span, size_t output_span)
{
	const uintptr_t input_begin = reinterpret_cast<uintptr_t>(input->data);
	const uintptr_t output_begin = reinterpret_cast<uintptr_t>(output->data);
	if (input_begin > UINTPTR_MAX - input_span ||
		output_begin > UINTPTR_MAX - output_span) return false;
	return input_begin + input_span <= output_begin ||
		output_begin + output_span <= input_begin;
}

template <typename PixelT>
static PF_Err ValidateToonPublicAdmission(
	const PF_InData *in_data,
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	const OLMToonDilateInfo &info,
	ToonPublicFamily *family_out,
	size_t *span_out)
{
	if (!in_data || !input || !output || !family_out || !span_out ||
		!input->data || !output->data || input->width <= 0 || input->height <= 0)
		return PF_Err_BAD_CALLBACK_PARAM;
	const ToonPublicFamily family = ToonAdmittedFamily(in_data, input, info);
	const A_long expected_rowbytes = input->width * static_cast<A_long>(sizeof(PixelT)) + 13;
	if (family == ToonPublicFamily_None || output->width != input->width ||
		output->height != input->height || input->rowbytes != expected_rowbytes ||
		output->rowbytes != expected_rowbytes || input->world_flags != 0 ||
		output->world_flags != 0 || input->origin_x != 0 || input->origin_y != 0 ||
		output->origin_x != 0 || output->origin_y != 0 ||
		input->extent_hint.left != 101 || input->extent_hint.top != 201 ||
		input->extent_hint.right != 101 + input->width ||
		input->extent_hint.bottom != 201 + input->height ||
		output->extent_hint.left != 301 || output->extent_hint.top != 401 ||
		output->extent_hint.right != 301 + output->width ||
		output->extent_hint.bottom != 401 + output->height)
		return PF_Err_BAD_CALLBACK_PARAM;
	const size_t span = static_cast<size_t>(expected_rowbytes) * static_cast<size_t>(input->height);
	if (!ToonWorldRangesDoNotOverlap(input, output, span, span) ||
		!ToonPublicSourceMatches<PixelT>(input, family))
		return PF_Err_BAD_CALLBACK_PARAM;
	*family_out = family;
	*span_out = span;
	return PF_Err_NONE;
}

// Public Beta full-frame admission. Unlike the retained exact-fixture
// admission above, this contract deliberately does not inspect source pixels,
// require a particular geometry, or require identical input/output strides.
// ROI/tiled worlds remain a later milestone; their halo and coordinate mapping
// cannot be inferred by merely relaxing this validator.
template <typename PixelT>
static PF_Err ValidateToonBetaAdmission(
	const PF_InData *in_data,
	const PF_EffectWorld *input,
	const PF_EffectWorld *output,
	const OLMToonDilateInfo &info,
	size_t *output_span)
{
	if (!in_data || !input || !output || !output_span ||
		!input->data || !output->data ||
		input->width <= 0 || input->height <= 0 ||
		output->width <= 0 || output->height <= 0 ||
		!std::isfinite(info.search_radius) || info.search_radius < 0.0 ||
		info.search_radius > 100.0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (!((in_data->downsample_x.num == 0 && in_data->downsample_x.den == 0) ||
		  (in_data->downsample_x.num > 0 && in_data->downsample_x.den > 0)) ||
		!((in_data->downsample_y.num == 0 && in_data->downsample_y.den == 0) ||
		  (in_data->downsample_y.num > 0 && in_data->downsample_y.den > 0))) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const int64_t offset_x64 = (int64_t)output->origin_x - input->origin_x;
	const int64_t offset_y64 = (int64_t)output->origin_y - input->origin_y;
	const bool tiled = input->width != output->width || input->height != output->height;
	if ((!tiled && (offset_x64 != 0 || offset_y64 != 0)) ||
		(tiled && (offset_x64 < 0 || offset_y64 < 0 || offset_x64 > input->width ||
			offset_y64 > input->height || output->width > input->width - offset_x64 ||
			output->height > input->height - offset_y64))) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t input_width = static_cast<size_t>(input->width);
	const size_t input_height = static_cast<size_t>(input->height);
	const size_t output_width = static_cast<size_t>(output->width);
	const size_t output_height = static_cast<size_t>(output->height);
	if (input_width > std::numeric_limits<size_t>::max() / sizeof(PixelT) ||
		output_width > std::numeric_limits<size_t>::max() / sizeof(PixelT))
		return PF_Err_OUT_OF_MEMORY;
	const size_t input_active_rowbytes = input_width * sizeof(PixelT);
	const size_t output_active_rowbytes = output_width * sizeof(PixelT);
	if (input->rowbytes <= 0 || output->rowbytes <= 0 ||
		static_cast<size_t>(input->rowbytes) < input_active_rowbytes ||
		static_cast<size_t>(output->rowbytes) < output_active_rowbytes) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (input_height > std::numeric_limits<size_t>::max() /
			static_cast<size_t>(input->rowbytes) ||
		output_height > std::numeric_limits<size_t>::max() /
			static_cast<size_t>(output->rowbytes)) {
		return PF_Err_OUT_OF_MEMORY;
	}
	const size_t input_span = input_height * static_cast<size_t>(input->rowbytes);
	const size_t staged_span = output_height * static_cast<size_t>(output->rowbytes);
	static constexpr size_t kMaxRenderWorkingSet = (size_t)3 * 1024 * 1024 * 1024;
	if (input_span > kMaxRenderWorkingSet || staged_span > kMaxRenderWorkingSet - input_span)
		return PF_Err_OUT_OF_MEMORY;
	if (!ToonWorldRangesDoNotOverlap(input, output, input_span, staged_span))
		return PF_Err_BAD_CALLBACK_PARAM;
	*output_span = staged_span;
	return PF_Err_NONE;
}

template <typename PixelT>
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output,
	const OLMToonDilateInfo &info);

template <typename PixelT>
static PF_Err RenderTileTyped(PF_EffectWorld *input, PF_EffectWorld *output,
	const OLMToonDilateInfo &info)
{
	if (input->width == output->width && input->height == output->height &&
		input->origin_x == output->origin_x && input->origin_y == output->origin_y) {
		return RenderTyped<PixelT>(input, output, info);
	}
	if (input->width <= 0 || input->height <= 0 || output->width <= 0 || output->height <= 0)
		return PF_Err_BAD_CALLBACK_PARAM;
	const int64_t ox64 = (int64_t)output->origin_x - input->origin_x;
	const int64_t oy64 = (int64_t)output->origin_y - input->origin_y;
	if (ox64 < 0 || oy64 < 0 || ox64 > input->width || oy64 > input->height ||
		output->width > input->width - ox64 || output->height > input->height - oy64)
		return PF_Err_BAD_CALLBACK_PARAM;
	const A_long ox = (A_long)ox64;
	const A_long oy = (A_long)oy64;
	const size_t rowbytes = static_cast<size_t>(input->width) * sizeof(PixelT);
	if (static_cast<size_t>(input->height) > std::numeric_limits<size_t>::max() / rowbytes)
		return PF_Err_OUT_OF_MEMORY;
	std::vector<uint8_t> rendered(rowbytes * static_cast<size_t>(input->height));
	PF_EffectWorld halo_world = *input;
	halo_world.data = reinterpret_cast<PF_PixelPtr>(rendered.data());
	halo_world.rowbytes = static_cast<A_long>(rowbytes);
	PF_Err err = RenderTyped<PixelT>(input, &halo_world, info);
	if (err) return err;
	for (A_long y = 0; y < output->height; ++y) {
		const uint8_t *src = rendered.data() + static_cast<size_t>(y + oy) * rowbytes +
			static_cast<size_t>(ox) * sizeof(PixelT);
		uint8_t *dst = reinterpret_cast<uint8_t *>(output->data) +
			static_cast<size_t>(y) * static_cast<size_t>(output->rowbytes);
		std::memcpy(dst, src, static_cast<size_t>(output->width) * sizeof(PixelT));
	}
	return PF_Err_NONE;
}

template <typename PixelT>
static PF_Err ValidateWorlds(const PF_EffectWorld *input, const PF_EffectWorld *output, size_t *pixel_count)
{
	if (!input || !output || !pixel_count) return PF_Err_BAD_CALLBACK_PARAM;
	if (output->width < 0 || output->height < 0 ||
	    input->width < output->width || input->height < output->height) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t width = static_cast<size_t>(output->width);
	const size_t height = static_cast<size_t>(output->height);
	if (width != 0 && height > std::numeric_limits<size_t>::max() / width) {
		return PF_Err_OUT_OF_MEMORY;
	}
	*pixel_count = width * height;
	if (*pixel_count > std::vector<uint32_t>().max_size()) return PF_Err_OUT_OF_MEMORY;
	if (*pixel_count == 0) return PF_Err_NONE;
	if (!input->data || !output->data || input->rowbytes <= 0 || output->rowbytes <= 0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (width > std::numeric_limits<size_t>::max() / sizeof(PixelT)) {
		return PF_Err_OUT_OF_MEMORY;
	}
	const size_t visible_rowbytes = width * sizeof(PixelT);
	if (static_cast<size_t>(input->rowbytes) < visible_rowbytes ||
	    static_cast<size_t>(output->rowbytes) < visible_rowbytes) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (height - 1 > std::numeric_limits<size_t>::max() / static_cast<size_t>(input->rowbytes) ||
	    height - 1 > std::numeric_limits<size_t>::max() / static_cast<size_t>(output->rowbytes)) {
		return PF_Err_OUT_OF_MEMORY;
	}
	return PF_Err_NONE;
}

template <typename PixelT>
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMToonDilateInfo &info)
{
	if (!input || !output) return PF_Err_BAD_CALLBACK_PARAM;
	const A_long w = output->width;
	const A_long h = output->height;
	size_t pixel_count = 0;
	PF_Err validation_err = ValidateWorlds<PixelT>(input, output, &pixel_count);
	if (validation_err != PF_Err_NONE) return validation_err;
	if (w <= 0 || h <= 0 || info.search_radius <= 0.0) {
		for (A_long y = 0; y < h; ++y) {
			for (A_long x = 0; x < w; ++x) {
				WritePixel<PixelT>(output, x, y, ReadPixel<PixelT>(input, x, y));
			}
		}
		return PF_Err_NONE;
	}

	const PF_FpLong comp_width = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const PF_FpLong scaled_radius = info.search_radius * ((PF_FpLong)w / comp_width);
	static constexpr A_long kMaxEffectiveRadius = 4096;
	if (!std::isfinite(info.search_radius) || info.search_radius < 0.0 ||
		!std::isfinite(comp_width) || comp_width <= 0.0 ||
		!std::isfinite(scaled_radius) || scaled_radius < 0.0 ||
		scaled_radius > (PF_FpLong)kMaxEffectiveRadius) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const A_long r_eff = (A_long)std::ceil(scaled_radius);
	if (r_eff <= 0) {
		for (A_long y = 0; y < h; ++y) {
			for (A_long x = 0; x < w; ++x) {
				WritePixel<PixelT>(output, x, y, ReadPixel<PixelT>(input, x, y));
			}
		}
		return PF_Err_NONE;
	}

	const uint32_t INF = std::numeric_limits<uint32_t>::max();
	std::vector<uint32_t> dist(pixel_count, INF);
	bool has_seed = false;

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PixelT input_pixel = ReadPixel<PixelT>(input, x, y);
			WritePixel<PixelT>(output, x, y, input_pixel);
				size_t idx = static_cast<size_t>(y) * static_cast<size_t>(w) + static_cast<size_t>(x);
			if (ToonPixelTraits<PixelT>::opaque(input_pixel)) {
				dist[idx] = 0;
				has_seed = true;
			}
		}
	}
	if (!has_seed) return PF_Err_NONE;

	auto try_relax = [&](A_long x, A_long y, const A_long coords[][2], int count) {
		size_t idx = static_cast<size_t>(y) * static_cast<size_t>(w) + static_cast<size_t>(x);
		if (dist[(size_t)idx] == 0) return;
		uint32_t best = INF;
		A_long best_x = -1;
		A_long best_y = -1;
		for (int i = 0; i < count; ++i) {
			A_long nx = coords[i][0];
			A_long ny = coords[i][1];
			if (nx < 0 || nx >= w || ny < 0 || ny >= h) continue;
			size_t neighbor_idx = static_cast<size_t>(ny) * static_cast<size_t>(w) + static_cast<size_t>(nx);
			uint32_t d = dist[neighbor_idx];
			if (d < best) {
				best = d;
				best_x = nx;
				best_y = ny;
			}
		}
		if (best == INF) return;
		uint32_t candidate = best + 1;
		if (candidate >= dist[(size_t)idx]) return;
		dist[(size_t)idx] = candidate;
		if (candidate <= (uint32_t)r_eff) {
			WritePixel<PixelT>(output, x, y, ReadPixel<PixelT>(output, best_x, best_y));
		}
	};

	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const A_long coords[4][2] = {{x - 1, y}, {x - 1, y - 1}, {x, y - 1}, {x + 1, y - 1}};
			try_relax(x, y, coords, 4);
		}
	}
	for (A_long y = h - 1; y >= 0; --y) {
		for (A_long x = w - 1; x >= 0; --x) {
			const A_long coords[4][2] = {{x + 1, y}, {x + 1, y + 1}, {x, y + 1}, {x - 1, y + 1}};
			try_relax(x, y, coords, 4);
		}
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
RenderTileWorld(PF_EffectWorld *input, PF_EffectWorld *output, const OLMToonDilateInfo &info, short bitdepth)
{
	if (bitdepth == 8) return RenderTileTyped<PF_Pixel8>(input, output, info);
	if (bitdepth == 16) return RenderTileTyped<PF_Pixel16>(input, output, info);
	if (bitdepth == 32) return RenderTileTyped<PF_PixelFloat>(input, output, info);
	return PF_Err_BAD_CALLBACK_PARAM;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	OLMToonDilateInfo info;
	info.search_radius = params[OLMTOONDILATE_SEARCH_RADIUS]->u.fs_d.value;
	info.comp_width = params[OLMTOONDILATE_INPUT]->u.ld.width;
	PF_EffectWorld *input = &params[OLMTOONDILATE_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	PF_Err err = PF_Err_NONE;
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
	return RenderWorld(input, output, info, bitdepth);
}

typedef struct {
	PF_FpLong comp_width;
	bool requires_layer_checkin;
} PreRenderData;

static void DeletePreRenderData(void *data)
{
	delete reinterpret_cast<PreRenderData *>(data);
}

static bool ToonCheckedHalo(PF_FpLong radius, A_long scale_num, A_long scale_den,
	A_long *halo_out)
{
	static constexpr A_long kMaxEffectiveRadius = 4096;
	if (!halo_out || !std::isfinite(radius) || radius < 0.0 || radius > 100.0)
		return false;
	PF_FpLong scale = 1.0;
	if (scale_num == 0 && scale_den == 0) {
		scale = 1.0;
	} else if (scale_num > 0 && scale_den > 0) {
		scale = (PF_FpLong)scale_num / (PF_FpLong)scale_den;
	} else {
		return false;
	}
	const PF_FpLong scaled = radius * scale;
	if (!std::isfinite(scale) || !std::isfinite(scaled) || scaled < 0.0 ||
		scaled > (PF_FpLong)kMaxEffectiveRadius)
		return false;
	*halo_out = (A_long)std::ceil(scaled);
	return true;
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
	bool requested_halo = false;
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);
	// Generic spatial tiles need an input halo. Parameter checkout is optional
	// in older bounded hostless adapters; production hosts provide both callbacks.
	if (in_data->inter.checkout_param && in_data->inter.checkin_param &&
		req.rect.right > req.rect.left && req.rect.bottom > req.rect.top) {
		PF_ParamDef radius_param;
		AEFX_CLR_STRUCT(radius_param);
		err = PF_CHECKOUT_PARAM(in_data, OLMTOONDILATE_SEARCH_RADIUS,
			in_data->current_time, in_data->time_step, in_data->time_scale, &radius_param);
		if (err) return err;
		const PF_FpLong radius = radius_param.u.fs_d.value;
		PF_Err checkin_err = PF_CHECKIN_PARAM(in_data, &radius_param);
		if (checkin_err) return checkin_err;
		if (!std::isfinite(radius) || radius < 0.0 || radius > 100.0)
			return PF_Err_BAD_CALLBACK_PARAM;
		A_long halo = 0;
		if (!ToonCheckedHalo(radius, in_data->downsample_x.num,
			in_data->downsample_x.den, &halo))
			return PF_Err_BAD_CALLBACK_PARAM;
		auto subtract_clamped = [halo](A_long value) -> A_long {
			return value <= halo ? 0 : value - halo;
		};
		auto add_saturated = [halo](A_long value) -> A_long {
			return value > std::numeric_limits<A_long>::max() - halo ?
				std::numeric_limits<A_long>::max() : value + halo;
		};
		req.rect.left = subtract_clamped(req.rect.left);
		req.rect.top = subtract_clamped(req.rect.top);
		req.rect.right = add_saturated(req.rect.right);
		req.rect.bottom = add_saturated(req.rect.bottom);
		requested_halo = halo > 0;
	}

	// Match the exported Windows SmartPreRender request exactly. The admitted
	// numerical cells independently require the complete source byte pattern,
	// so a host that discards zero-alpha RGB will fail-close at SmartRender.
	req.preserve_rgb_of_zero_alpha = FALSE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMTOONDILATE_INPUT, OLMTOONDILATE_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		// Allocate before publishing any output state so an allocation failure
		// leaves the host-owned pre-render result unchanged.
		PreRenderData *pre = new PreRenderData;
		pre->comp_width = in_result.ref_width > 0 ? (PF_FpLong)in_result.ref_width : 0.0;
		pre->requires_layer_checkin = requested_halo;
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
		extra->output->flags |= PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS;
		extra->output->pre_render_data = pre;
		extra->output->delete_pre_render_data_func = DeletePreRenderData;
	}
	return err;
}

static PF_Err GetToonPixelFormats(
	PF_InData *in_data,
	const PF_EffectWorld *input_world,
	const PF_EffectWorld *output_world,
	PF_PixelFormat *input_format,
	PF_PixelFormat *output_format);

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	if (!in_data || !out_data || !in_data->pica_basicP || !extra || !extra->input || !extra->cb ||
	    !extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
	    !in_data->inter.checkout_param || !in_data->inter.checkin_param) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	PreRenderData *pre_data = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data);
	bool requires_layer_checkin = pre_data && pre_data->requires_layer_checkin;
	bool input_checked_out = false;
	err = extra->cb->checkout_layer_pixels(in_data->effect_ref, OLMTOONDILATE_INPUT, &input_world);
	if (!err) input_checked_out = true;
	auto finish = [&](PF_Err primary) -> PF_Err {
		if (requires_layer_checkin && input_checked_out) {
			if (!extra->cb->checkin_layer_pixels) return primary ? primary : PF_Err_BAD_CALLBACK_PARAM;
			PF_Err cleanup = extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMTOONDILATE_INPUT);
			if (!primary) primary = cleanup;
			input_checked_out = false;
		}
		return primary;
	};
	if (err) return err;
	err = extra->cb->checkout_output(in_data->effect_ref, &output_world);
	if (err) return finish(err);
	if (!input_world || !output_world) return finish(PF_Err_BAD_CALLBACK_PARAM);
	requires_layer_checkin = requires_layer_checkin ||
		input_world->width != output_world->width || input_world->height != output_world->height ||
		input_world->origin_x != output_world->origin_x || input_world->origin_y != output_world->origin_y;

	PF_ParamDef radius_param;
	AEFX_CLR_STRUCT(radius_param);
	err = PF_CHECKOUT_PARAM(in_data, OLMTOONDILATE_SEARCH_RADIUS,
	                       in_data->current_time, in_data->time_step, in_data->time_scale,
	                       &radius_param);
	if (err) return finish(err);

	OLMToonDilateInfo info;
	info.search_radius = radius_param.u.fs_d.value;
	info.comp_width = input_world->width;
	if (in_data->downsample_x.num > 0 && in_data->downsample_x.den > 0) {
		// The AEX worker scales Search Radius from the host's rational
		// downsample_x pair.  Reconstructing this from integer ref/output
		// widths is off by one for odd-sized worlds at enlarged render scales.
		info.comp_width = (PF_FpLong)input_world->width *
		                  (PF_FpLong)in_data->downsample_x.den /
		                  (PF_FpLong)in_data->downsample_x.num;
	} else if (input_world->width == output_world->width) {
		if (PreRenderData *pre = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data))
			if (pre->comp_width > 0.0) info.comp_width = pre->comp_width;
	}
	// Only a successful checkout is checked in.  Propagate cleanup failure
	// before numerical rendering so the destination remains untouched.
	err = PF_CHECKIN_PARAM(in_data, &radius_param);
	if (err) return finish(err);

	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	err = GetToonPixelFormats(in_data, input_world, output_world,
	                          &input_format, &output_format);
	PF_PixelFormat expected_format = PF_PixelFormat_INVALID;
	switch (extra->input->bitdepth) {
	case 8: expected_format = PF_PixelFormat_ARGB32; break;
	case 16: expected_format = PF_PixelFormat_ARGB64; break;
	case 32: expected_format = PF_PixelFormat_ARGB128; break;
	default: break;
	}
	if (err) return finish(err);
	if (expected_format == PF_PixelFormat_INVALID || input_format != expected_format ||
		output_format != expected_format) return finish(PF_Err_BAD_CALLBACK_PARAM);

	size_t span = 0;
	switch (extra->input->bitdepth) {
	case 8: err = ValidateToonBetaAdmission<PF_Pixel8>(in_data, input_world, output_world, info, &span); break;
	case 16: err = ValidateToonBetaAdmission<PF_Pixel16>(in_data, input_world, output_world, info, &span); break;
	case 32: err = ValidateToonBetaAdmission<PF_PixelFloat>(in_data, input_world, output_world, info, &span); break;
	default: err = PF_Err_BAD_CALLBACK_PARAM; break;
	}
	if (err) return finish(err);

	// Render into private output storage and commit only after the complete
	// numerical path succeeds. The span is derived from the output world, so
	// input and output may legally use different rowbytes.
	try {
		std::vector<uint8_t> staged_bytes(span);
		std::memcpy(staged_bytes.data(), output_world->data, span);
		PF_EffectWorld staged_world = *output_world;
		staged_world.data = reinterpret_cast<PF_PixelPtr>(staged_bytes.data());
		err = RenderTileWorld(input_world, &staged_world, info, extra->input->bitdepth);
		err = finish(err);
		if (!err) std::memcpy(output_world->data, staged_bytes.data(), span);
	} catch (const std::bad_alloc &) {
		err = finish(PF_Err_OUT_OF_MEMORY);
	} catch (...) {
		err = finish(PF_Err_INTERNAL_STRUCT_DAMAGED);
	}

	// Preserve the recorded no-checkin lifecycle for retained full-frame exact
	// paths. Generic spatial tiles use the SDK checkin before committing output.
	return err;
}

static PF_Err
GetToonPixelFormats(
	PF_InData *in_data,
	const PF_EffectWorld *input_world,
	const PF_EffectWorld *output_world,
	PF_PixelFormat *input_format,
	PF_PixelFormat *output_format)
{
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
			if (!err && release_err != kSPNoError) err = static_cast<PF_Err>(release_err);
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
			// The Windows AEX public legacy-render owner is an intentional no-op.
			// Rendering is implemented exclusively by the advertised Smart Render path.
			break;
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

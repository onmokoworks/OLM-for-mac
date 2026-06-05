#include "OLMRadialBlur.h"

#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdio>
#include <map>
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
	PF_ADD_POPUP(GetStringPtr(StrID_BlurType_Param_Name),
	             2, 1, GetStringPtr(StrID_BlurType_Choices),
	             BLUR_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POINT(GetStringPtr(StrID_Center_Param_Name), 960, 540, FALSE,
	             CENTER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_OuterStrength_Param_Name),
	              0, 3000, 0, 3000, 212,
	              OUTER_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_OuterOffsetMode_Param_Name),
	             3, 1, GetStringPtr(StrID_OffsetMode_Choices),
	             OUTER_OFFSET_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_OuterOffset_Param_Name),
	              0, 3000, 0, 3000, 153,
	              OUTER_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_InnerStrength_Param_Name),
	              0, 3000, 0, 3000, 0,
	              INNER_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_RepeatBorder_Param_Name), "", TRUE, 0,
	                REPEAT_BORDER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Ratio_Param_Name),
	                     0.01, 10.0, 0.01, 10.0, 1.0,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     RATIO_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Angle_Param_Name),
	                     -360.0, 360.0, -360.0, 360.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     ANGLE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Quality_Param_Name),
	                     1.0, 50.0, 1.0, 50.0, 1.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     QUALITY_DISK_ID);

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
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_NoiseVariation_Param_Name),
	                     0.0, 100.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     NOISE_VARIATION_DISK_ID);

	out_data->num_params = OLMRADIALBLUR_NUM_PARAMS;
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

using Complex = std::complex<double>;

static A_long NextPowerOfTwo(A_long value)
{
	A_long out = 1;
	while (out < value) out <<= 1;
	return out;
}

static void FFT(std::vector<Complex> &a, bool invert)
{
	const A_long n = (A_long)a.size();
	for (A_long i = 1, j = 0; i < n; ++i) {
		A_long bit = n >> 1;
		for (; j & bit; bit >>= 1) j ^= bit;
		j ^= bit;
		if (i < j) std::swap(a[(size_t)i], a[(size_t)j]);
	}

	for (A_long len = 2; len <= n; len <<= 1) {
		const double angle = (invert ? -2.0 : 2.0) * kPi / (double)len;
		const Complex wlen(std::cos(angle), std::sin(angle));
		for (A_long i = 0; i < n; i += len) {
			Complex w(1.0, 0.0);
			const A_long half = len >> 1;
			for (A_long j = 0; j < half; ++j) {
				Complex u = a[(size_t)(i + j)];
				Complex v = a[(size_t)(i + j + half)] * w;
				a[(size_t)(i + j)] = u + v;
				a[(size_t)(i + j + half)] = u - v;
				w *= wlen;
			}
		}
	}

	if (invert) {
		const double inv_n = 1.0 / (double)n;
		for (Complex &value : a) value *= inv_n;
	}
}

class ForwardConvolver {
public:
	ForwardConvolver(A_long value_count, const std::vector<float> &weights)
		: value_count_(value_count),
		  fft_count_(NextPowerOfTwo(value_count + (A_long)weights.size() - 1)),
		  kernel_fft_((size_t)fft_count_)
	{
		for (size_t i = 0; i < weights.size(); ++i) kernel_fft_[i] = Complex(weights[i], 0.0);
		FFT(kernel_fft_, false);
	}

	void Convolve(const std::vector<double> &values, std::vector<double> &out) const
	{
		std::vector<Complex> spectrum((size_t)fft_count_);
		for (A_long i = 0; i < value_count_; ++i) spectrum[(size_t)i] = Complex(values[(size_t)i], 0.0);
		FFT(spectrum, false);
		for (A_long i = 0; i < fft_count_; ++i) spectrum[(size_t)i] *= kernel_fft_[(size_t)i];
		FFT(spectrum, true);
		out.resize((size_t)value_count_);
		for (A_long i = 0; i < value_count_; ++i) out[(size_t)i] = spectrum[(size_t)i].real();
	}

private:
	A_long value_count_ = 0;
	A_long fft_count_ = 0;
	std::vector<Complex> kernel_fft_;
};

class CircularConvolver {
public:
	CircularConvolver(A_long value_count, const std::vector<float> &weights)
		: value_count_(value_count),
		  repeated_count_(value_count * 3),
		  fft_count_(NextPowerOfTwo(repeated_count_ + (A_long)weights.size() - 1)),
		  kernel_fft_((size_t)fft_count_)
	{
		for (size_t i = 0; i < weights.size(); ++i) kernel_fft_[i] = Complex(weights[i], 0.0);
		FFT(kernel_fft_, false);
	}

	void Convolve(const std::vector<double> &values, std::vector<double> &out) const
	{
		std::vector<Complex> spectrum((size_t)fft_count_);
		for (A_long i = 0; i < repeated_count_; ++i) {
			spectrum[(size_t)i] = Complex(values[(size_t)(i % value_count_)], 0.0);
		}
		FFT(spectrum, false);
		for (A_long i = 0; i < fft_count_; ++i) spectrum[(size_t)i] *= kernel_fft_[(size_t)i];
		FFT(spectrum, true);
		out.resize((size_t)value_count_);
		for (A_long i = 0; i < value_count_; ++i) out[(size_t)i] = spectrum[(size_t)(value_count_ + i)].real();
	}

private:
	A_long value_count_ = 0;
	A_long repeated_count_ = 0;
	A_long fft_count_ = 0;
	std::vector<Complex> kernel_fft_;
};

static float SampleChannel(const FloatImage &image, float x, float y, int channel, bool repeat)
{
	const A_long w = image.width;
	const A_long h = image.height;
	bool valid = true;
	if (repeat) {
		x = ClampFloat(x, 0.0f, (float)(w - 1));
		y = ClampFloat(y, 0.0f, (float)(h - 1));
	} else {
		valid = x >= 0.0f && x <= (float)(w - 1) && y >= 0.0f && y <= (float)(h - 1);
		x = ClampFloat(x, 0.0f, (float)(w - 1));
		y = ClampFloat(y, 0.0f, (float)(h - 1));
	}
	if (!valid) return 0.0f;
	A_long x0 = (A_long)std::floor(x);
	A_long y0 = (A_long)std::floor(y);
	A_long x1 = std::min<A_long>(x0 + 1, w - 1);
	A_long y1 = std::min<A_long>(y0 + 1, h - 1);
	float fx = x - (float)x0;
	float fy = y - (float)y0;
	auto at = [&](A_long px, A_long py) -> float {
		return image.rgba[((size_t)py * w + px) * 4 + channel];
	};
	float top = at(x0, y0) * (1.0f - fx) + at(x1, y0) * fx;
	float bottom = at(x0, y1) * (1.0f - fx) + at(x1, y1) * fx;
	return top * (1.0f - fy) + bottom * fy;
}

static std::vector<float> ZoomGaussianWeights(A_long length)
{
	if (length <= 1) return std::vector<float>{1.0f};
	std::vector<float> weights((size_t)length);
	const double denom = (double)length * (double)length * 2.0 * 0.111111119389534 + 1.0e-5;
	const double inv_denom = 1.0 / denom;
	for (A_long i = 0; i < length; ++i) {
		weights[(size_t)i] = (float)std::exp(-(i * i) * inv_denom);
	}
	return weights;
}

static std::vector<float> RotationGaussianWeights(A_long length)
{
	if (length <= 1) return std::vector<float>{1.0f};
	constexpr A_long table_len = 30000;
	const double denom = (double)table_len * (double)table_len * 2.0 * 0.111111119389534 + 1.0e-5;
	const double inv_denom = 1.0 / denom;
	const A_long idx_scale = table_len / length;
	std::vector<float> weights((size_t)length, 1.0f);
	for (A_long i = 1; i < length; ++i) {
		const A_long table_index = (A_long)((float)i * (float)idx_scale);
		weights[(size_t)i] = (float)std::exp(-(table_index * table_index) * inv_denom);
	}
	return weights;
}

static A_long ZoomEffectiveLength(const OLMRadialBlurInfo &info)
{
	A_long span = info.outer_strength;
	if (info.outer_offset_mode == 2) span = std::max(info.outer_strength, info.outer_offset);
	else if (info.outer_offset_mode == 3) span = info.outer_offset;
	return std::max<A_long>(0, std::min<A_long>(span, 3000));
}

static A_long RotationEffectiveLength(A_long strength, A_long offset_mode, A_long dynamic_offset)
{
	A_long span = strength;
	if (offset_mode == 1) span = strength + dynamic_offset;
	else if (offset_mode == 2) span = std::max(strength, dynamic_offset);
	else if (offset_mode == 3) span = dynamic_offset;
	return std::max<A_long>(0, std::min<A_long>(span - 1, 3000));
}

static A_long DynamicOffsetForRadius(A_long radius_count, A_long offset, A_long radius_index)
{
	if (offset <= 0) return 0;
	return (A_long)((double)((radius_count / 2) * offset) / (double)std::max<A_long>(1, radius_index + 1));
}

static PF_Err RenderZoom8(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info)
{
	if (info.blur_type != 1 || info.inner_strength != 0 ||
	    info.noise_variation != 0.0) {
		CopyWorld<PF_Pixel8>(input, output);
		return PF_Err_NONE;
	}

	const A_long w = output->width;
	const A_long h = output->height;
	FloatImage src;
	src.width = w;
	src.height = h;
	src.rgba.resize((size_t)w * h * 4);
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const PF_Pixel8 *p = PixelAtConst<PF_Pixel8>(input, x, y);
			size_t idx = ((size_t)y * w + x) * 4;
			src.rgba[idx + 0] = (float)p->red / 255.0f;
			src.rgba[idx + 1] = (float)p->green / 255.0f;
			src.rgba[idx + 2] = (float)p->blue / 255.0f;
			src.rgba[idx + 3] = (float)p->alpha / 255.0f;
		}
	}

	const PF_FpLong comp_w = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const PF_FpLong comp_h = info.comp_height > 0.0 ? info.comp_height : (PF_FpLong)h;
	const double cx = info.center_x * ((double)w / comp_w);
	const double cy = info.center_y * ((double)h / comp_h);
	const double ratio = info.ratio > 0.0 ? info.ratio : 1.0;
	const double base_angle = info.angle_deg * kPi / 180.0;
	const double quality = info.quality > 0.0 ? info.quality : 5.0;
	const double step_deg = 1.0 / quality;
	const double step_rad = step_deg * kPi / 180.0;
	const A_long angular_count = (A_long)(360.0 / step_deg);

	const double min_dx = (0.0 <= cx && cx < w) ? 0.0 : std::abs(cx < 0.0 ? cx : cx - w);
	const double min_dy = (0.0 <= cy && cy < h) ? 0.0 : std::abs(cy < 0.0 ? cy : cy - h);
	const double max_dx = (0.0 <= cx && cx < w) ? std::max(cx, (double)w - cx) : (cx < 0.0 ? (double)w - cx : cx);
	const double max_dy = (0.0 <= cy && cy < h) ? std::max(cy, (double)h - cy) : (cy < 0.0 ? (double)h - cy : cy);
	const A_long min_r = std::max<A_long>(0, (A_long)(std::sqrt(min_dx * min_dx + min_dy * min_dy) / ratio) - 2);
	const A_long max_r = (A_long)std::sqrt(max_dx * max_dx + max_dy * max_dy) + 2;
	const A_long radius_count = max_r - min_r + 1;

	FloatImage polar;
	polar.width = radius_count;
	polar.height = angular_count;
	polar.rgba.resize((size_t)angular_count * radius_count * 4);
	const double cos_a = std::cos(base_angle);
	const double sin_a = std::sin(base_angle);
	for (A_long ai = 0; ai < angular_count; ++ai) {
		const double theta = (double)ai * step_rad;
		const double cos_t = std::cos(theta);
		const double sin_t = std::sin(theta);
		for (A_long ri = 0; ri < radius_count; ++ri) {
			const double r = (double)(min_r + ri);
			const double sx0 = r * cos_t;
			const double sy0 = r * sin_t * ratio;
			const float sx = (float)(cx + cos_a * sx0 - sin_a * sy0);
			const float sy = (float)(cy + sin_a * sx0 + cos_a * sy0);
			const size_t dst = ((size_t)ai * radius_count + ri) * 4;
			for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = SampleChannel(src, sx, sy, c, info.repeat_border != FALSE);
		}
	}

	const std::vector<float> weights = ZoomGaussianWeights(ZoomEffectiveLength(info));
	const bool use_fft_convolution = weights.size() > 512;
	FloatImage blurred;
	blurred.width = radius_count;
	blurred.height = angular_count;
	blurred.rgba.assign((size_t)angular_count * radius_count * 4, 0.0f);
	if (!use_fft_convolution) {
		for (A_long ai = 0; ai < angular_count; ++ai) {
			for (A_long ri = 0; ri < radius_count; ++ri) {
				double weighted_rgb[3] = {0.0, 0.0, 0.0};
				double weighted_alpha = 0.0;
				double accum_alpha = 0.0;
				const A_long limit = std::min<A_long>((A_long)weights.size(), ri + 1);
				for (A_long k = 0; k < limit; ++k) {
					const size_t src_idx = ((size_t)ai * radius_count + (ri - k)) * 4;
					const double alpha = polar.rgba[src_idx + 3];
					const double weight = weights[(size_t)k];
					for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * alpha * weight;
					weighted_alpha += alpha * weight;
					accum_alpha += alpha * weight;
				}
				const size_t dst = ((size_t)ai * radius_count + ri) * 4;
				if (weighted_alpha > 1.0e-8) {
					for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = (float)(weighted_rgb[c] / weighted_alpha);
				}
				blurred.rgba[dst + 3] = ClampFloat((float)accum_alpha, 0.0f, 1.0f);
			}
		}
	} else {
		ForwardConvolver convolver(radius_count, weights);
		std::vector<double> values((size_t)radius_count);
		std::vector<double> alpha_conv;
		std::vector<double> rgb_conv[3];
		for (A_long ai = 0; ai < angular_count; ++ai) {
			for (A_long ri = 0; ri < radius_count; ++ri) {
				const size_t src_idx = ((size_t)ai * radius_count + ri) * 4;
				values[(size_t)ri] = polar.rgba[src_idx + 3];
			}
			convolver.Convolve(values, alpha_conv);

			for (int c = 0; c < 3; ++c) {
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t src_idx = ((size_t)ai * radius_count + ri) * 4;
					const double alpha = polar.rgba[src_idx + 3];
					values[(size_t)ri] = polar.rgba[src_idx + c] * alpha;
				}
				convolver.Convolve(values, rgb_conv[c]);
			}

			for (A_long ri = 0; ri < radius_count; ++ri) {
				const size_t dst = ((size_t)ai * radius_count + ri) * 4;
				const double weighted_alpha = alpha_conv[(size_t)ri];
				if (weighted_alpha > 1.0e-8) {
					for (int c = 0; c < 3; ++c) {
						blurred.rgba[dst + c] = (float)(rgb_conv[c][(size_t)ri] / weighted_alpha);
					}
				}
				blurred.rgba[dst + 3] = ClampFloat((float)weighted_alpha, 0.0f, 1.0f);
			}
		}
	}

	const double rgb_quantize_epsilon = use_fft_convolution ? 0.0 : 1.0e-4;
	const double alpha_quantize_epsilon = 1.0e-4;
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const double dx = (double)x - cx;
			const double dy = (double)y - cy;
			const double ex = cos_a * dx + sin_a * dy;
			const double ey = (cos_a * dy - sin_a * dx) / ratio;
			const double radius = std::sqrt(ex * ex + ey * ey);
			double angle = std::atan2(ey, ex);
			if (angle < 0.0) angle += kPi * 2.0;
			const float radius_index = (float)(radius - min_r);
			const float angle_index = (float)(angle / step_rad);
			const A_long xi_raw = (A_long)std::floor(radius_index);
			const A_long yi = (A_long)std::floor(angle_index);
			const float fx = radius_index - (float)xi_raw;
			const float fy = angle_index - (float)yi;
			const A_long xi = std::max<A_long>(0, std::min<A_long>(xi_raw, radius_count - 1));
			const A_long x1 = std::max<A_long>(0, std::min<A_long>(xi_raw + 1, radius_count - 1));
			const A_long y0 = ((yi % angular_count) + angular_count) % angular_count;
			const A_long y1 = (y0 + 1) % angular_count;
			auto sample = [&](A_long px, A_long py, int c) -> float {
				return blurred.rgba[((size_t)py * radius_count + px) * 4 + c];
			};
			const double w00 = (1.0 - fx) * (1.0 - fy);
			const double w10 = fx * (1.0 - fy);
			const double w01 = (1.0 - fx) * fy;
			const double w11 = fx * fy;
			const double a00 = sample(xi, y0, 3) * w00;
			const double a10 = sample(x1, y0, 3) * w10;
			const double a01 = sample(xi, y1, 3) * w01;
			const double a11 = sample(x1, y1, 3) * w11;
			const double alpha = a00 + a10 + a01 + a11;
			PF_Pixel8 *out = PixelAt<PF_Pixel8>(output, x, y);
			double rgb[3] = {0.0, 0.0, 0.0};
			if (alpha > 1.0e-8) {
				for (int c = 0; c < 3; ++c) {
					rgb[c] = (sample(xi, y0, c) * a00 + sample(x1, y0, c) * a10 +
					          sample(xi, y1, c) * a01 + sample(x1, y1, c) * a11) / alpha;
					rgb[c] *= info.brightness_gain;
				}
			}
			out->red   = (A_u_char)ClampFloat((float)std::floor(rgb[0] * 255.0 + rgb_quantize_epsilon), 0.0f, 255.0f);
			out->green = (A_u_char)ClampFloat((float)std::floor(rgb[1] * 255.0 + rgb_quantize_epsilon), 0.0f, 255.0f);
			out->blue  = (A_u_char)ClampFloat((float)std::floor(rgb[2] * 255.0 + rgb_quantize_epsilon), 0.0f, 255.0f);
			out->alpha = (A_u_char)ClampFloat((float)std::floor(alpha * 255.0 + alpha_quantize_epsilon), 0.0f, 255.0f);
		}
	}
	return PF_Err_NONE;
}

static PF_Err RenderRotation8(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info)
{
	if (info.blur_type != 2 || info.inner_strength != 0 ||
	    info.noise_variation != 0.0 || info.size_variation != 0.0) {
		CopyWorld<PF_Pixel8>(input, output);
		return PF_Err_NONE;
	}

	const A_long w = output->width;
	const A_long h = output->height;
	FloatImage src;
	src.width = w;
	src.height = h;
	src.rgba.resize((size_t)w * h * 4);
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

	const PF_FpLong comp_w = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	const PF_FpLong comp_h = info.comp_height > 0.0 ? info.comp_height : (PF_FpLong)h;
	const double cx = info.center_x * ((double)w / comp_w);
	const double cy = info.center_y * ((double)h / comp_h);
	const double ratio = info.ratio > 0.0 ? info.ratio : 1.0;
	const double base_angle = info.angle_deg * kPi / 180.0;
	const double quality = info.quality > 0.0 ? info.quality : 5.0;
	const double step_deg = 1.0 / quality;
	const double step_rad = step_deg * kPi / 180.0;
	const A_long angular_count = (A_long)(360.0 / step_deg);

	const double left = std::max(0.0, -cx);
	const double right = std::max({0.0, cx - (double)w, cx <= (double)w / 2.0 ? (double)w - cx : cx});
	const double top = std::max(0.0, -cy);
	const double bottom = std::max({0.0, cy - (double)h, cy <= (double)h / 2.0 ? (double)h - cy : cy});
	const A_long min_r = std::max<A_long>(0, (A_long)(std::sqrt(left * left + top * top) / ratio) - 2);
	const double max_x = std::max(left, right);
	const double max_y = std::max(top, bottom);
	const A_long max_r = (A_long)std::sqrt(max_x * max_x + max_y * max_y) + 2;
	const A_long radius_count = max_r - min_r + 1;

	FloatImage polar;
	polar.width = angular_count;
	polar.height = radius_count;
	polar.rgba.resize((size_t)radius_count * angular_count * 4);
	const double cos_a = std::cos(base_angle);
	const double sin_a = std::sin(base_angle);
	for (A_long ri = 0; ri < radius_count; ++ri) {
		const double r = (double)(min_r + ri);
		for (A_long ai = 0; ai < angular_count; ++ai) {
			const double theta = (double)ai * step_rad;
			const double sx0 = std::cos(theta) * r;
			const double sy0 = std::sin(theta) * r * ratio;
			const float sx = (float)(cx + cos_a * sx0 - sin_a * sy0);
			const float sy = (float)(cy + sin_a * sx0 + cos_a * sy0);
			const size_t dst = ((size_t)ri * angular_count + ai) * 4;
			for (int c = 0; c < 4; ++c) polar.rgba[dst + c] = SampleChannel(src, sx, sy, c, info.repeat_border != FALSE);
		}
	}

	const bool variable_offset = info.outer_offset != 0;
	const A_long outer_length = RotationEffectiveLength(info.outer_strength, info.outer_offset_mode, 0);
	const std::vector<float> weights = variable_offset ? std::vector<float>{} : RotationGaussianWeights(outer_length);
	FloatImage blurred;
	blurred.width = angular_count;
	blurred.height = radius_count;
	blurred.rgba.assign((size_t)radius_count * angular_count * 4, 0.0f);

	auto scatter_row_small = [&](A_long ri, const std::vector<float> &row_weights) {
		for (A_long ai = 0; ai < angular_count; ++ai) {
			double weighted_rgb[3] = {0.0, 0.0, 0.0};
			double weighted_alpha = 0.0;
			double accum_alpha = 0.0;
			for (size_t k = 0; k < row_weights.size(); ++k) {
				const A_long src_ai = (ai - (A_long)(k % (size_t)angular_count) + angular_count) % angular_count;
				const size_t src_idx = ((size_t)ri * angular_count + src_ai) * 4;
				const double alpha = polar.rgba[src_idx + 3];
				const double contribution = alpha * row_weights[k];
				for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * contribution;
				weighted_alpha += contribution;
				accum_alpha = std::max(accum_alpha, contribution);
			}
			const size_t dst = ((size_t)ri * angular_count + ai) * 4;
			if (weighted_alpha > 1.0e-8) {
				for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = (float)(weighted_rgb[c] / weighted_alpha);
			}
			blurred.rgba[dst + 3] = (float)accum_alpha;
		}
	};

	if (variable_offset) {
		std::map<A_long, std::vector<float>> weight_cache;
		std::map<A_long, CircularConvolver> convolver_cache;
		std::vector<double> values((size_t)angular_count);
		std::vector<double> alpha_conv;
		std::vector<double> rgb_conv[3];
		for (A_long ri = 0; ri < radius_count; ++ri) {
			const A_long dynamic_offset = DynamicOffsetForRadius(radius_count, info.outer_offset, ri);
			const A_long row_length = RotationEffectiveLength(info.outer_strength, info.outer_offset_mode, dynamic_offset);
			auto weight_it = weight_cache.find(row_length);
			if (weight_it == weight_cache.end()) {
				weight_it = weight_cache.emplace(row_length, RotationGaussianWeights(row_length)).first;
			}
			const std::vector<float> &row_weights = weight_it->second;
			if (row_weights.size() < 64) {
				scatter_row_small(ri, row_weights);
				continue;
			}
			auto convolver_it = convolver_cache.find(row_length);
			if (convolver_it == convolver_cache.end()) {
				convolver_it = convolver_cache.emplace(row_length, CircularConvolver(angular_count, row_weights)).first;
			}
			CircularConvolver &convolver = convolver_it->second;
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t src_idx = ((size_t)ri * angular_count + ai) * 4;
				values[(size_t)ai] = polar.rgba[src_idx + 3];
			}
			convolver.Convolve(values, alpha_conv);
			for (int c = 0; c < 3; ++c) {
				for (A_long ai = 0; ai < angular_count; ++ai) {
					const size_t src_idx = ((size_t)ri * angular_count + ai) * 4;
					const double alpha = polar.rgba[src_idx + 3];
					values[(size_t)ai] = polar.rgba[src_idx + c] * alpha;
				}
				convolver.Convolve(values, rgb_conv[c]);
			}
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t dst = ((size_t)ri * angular_count + ai) * 4;
				const double weighted_alpha = alpha_conv[(size_t)ai];
				if (weighted_alpha > 1.0e-8) {
					for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = (float)(rgb_conv[c][(size_t)ai] / weighted_alpha);
				}
				blurred.rgba[dst + 3] = polar.rgba[dst + 3];
			}
		}
	} else if (weights.size() < 64) {
		for (A_long ri = 0; ri < radius_count; ++ri) scatter_row_small(ri, weights);
	} else {
		CircularConvolver convolver(angular_count, weights);
		std::vector<double> values((size_t)angular_count);
		std::vector<double> alpha_conv;
		std::vector<double> rgb_conv[3];
		for (A_long ri = 0; ri < radius_count; ++ri) {
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t src_idx = ((size_t)ri * angular_count + ai) * 4;
				values[(size_t)ai] = polar.rgba[src_idx + 3];
			}
			convolver.Convolve(values, alpha_conv);
			for (int c = 0; c < 3; ++c) {
				for (A_long ai = 0; ai < angular_count; ++ai) {
					const size_t src_idx = ((size_t)ri * angular_count + ai) * 4;
					const double alpha = polar.rgba[src_idx + 3];
					values[(size_t)ai] = polar.rgba[src_idx + c] * alpha;
				}
				convolver.Convolve(values, rgb_conv[c]);
			}
			for (A_long ai = 0; ai < angular_count; ++ai) {
				const size_t dst = ((size_t)ri * angular_count + ai) * 4;
				const double weighted_alpha = alpha_conv[(size_t)ai];
				if (weighted_alpha > 1.0e-8) {
					for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = (float)(rgb_conv[c][(size_t)ai] / weighted_alpha);
				}
				blurred.rgba[dst + 3] = polar.rgba[dst + 3];
			}
		}
	}

	const double alpha_quantize_epsilon = 1.0e-4;
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			const double dx = (double)x - cx;
			const double dy = (double)y - cy;
			const double ex = cos_a * dx + sin_a * dy;
			const double ey = (cos_a * dy - sin_a * dx) / ratio;
			const double radius = std::sqrt(ex * ex + ey * ey);
			double angle = std::atan2(ey, ex);
			if (angle < 0.0) angle += kPi * 2.0;
			const float angle_index = (float)(angle / step_rad);
			const float radius_index = (float)(radius - min_r);
			const A_long xi = (A_long)std::floor(angle_index);
			const A_long yi_raw = (A_long)std::floor(radius_index);
			const float fx = angle_index - (float)xi;
			const float fy = radius_index - (float)yi_raw;
			const A_long x0 = ((xi % angular_count) + angular_count) % angular_count;
			const A_long x1 = (x0 + 1) % angular_count;
			const A_long y0 = std::max<A_long>(0, std::min<A_long>(yi_raw, radius_count - 1));
			const A_long y1 = std::max<A_long>(0, std::min<A_long>(yi_raw + 1, radius_count - 1));
			auto sample = [&](A_long px, A_long py, int c) -> float {
				return blurred.rgba[((size_t)py * angular_count + px) * 4 + c];
			};
			const double w00 = (1.0 - fx) * (1.0 - fy);
			const double w10 = fx * (1.0 - fy);
			const double w01 = (1.0 - fx) * fy;
			const double w11 = fx * fy;
			const double a00 = sample(x0, y0, 3) * w00;
			const double a10 = sample(x1, y0, 3) * w10;
			const double a01 = sample(x0, y1, 3) * w01;
			const double a11 = sample(x1, y1, 3) * w11;
			const double alpha = a00 + a10 + a01 + a11;
			PF_Pixel8 *out = PixelAt<PF_Pixel8>(output, x, y);
			double rgb[3] = {0.0, 0.0, 0.0};
			if (alpha > 1.0e-8) {
				for (int c = 0; c < 3; ++c) {
					rgb[c] = (sample(x0, y0, c) * a00 + sample(x1, y0, c) * a10 +
					          sample(x0, y1, c) * a01 + sample(x1, y1, c) * a11) / alpha;
					rgb[c] *= info.brightness_gain;
				}
			}
			out->red = (A_u_char)ClampFloat((float)std::floor(rgb[0] * 255.0), 0.0f, 255.0f);
			out->green = (A_u_char)ClampFloat((float)std::floor(rgb[1] * 255.0), 0.0f, 255.0f);
			out->blue = (A_u_char)ClampFloat((float)std::floor(rgb[2] * 255.0), 0.0f, 255.0f);
			out->alpha = (A_u_char)ClampFloat((float)std::floor(alpha * 255.0 + alpha_quantize_epsilon), 0.0f, 255.0f);
		}
	}
	return PF_Err_NONE;
}

static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output, const OLMRadialBlurInfo &info, short bitdepth)
{
	if (bitdepth == 8) {
		if (info.blur_type == 2) return RenderRotation8(input, output, info);
		return RenderZoom8(input, output, info);
	}
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

static OLMRadialBlurInfo InfoFromParams(PF_ParamDef *params[], PF_FpLong comp_width, PF_FpLong comp_height)
{
	OLMRadialBlurInfo info;
	info.blur_type = params[OLMRADIALBLUR_BLUR_TYPE]->u.pd.value;
	info.center_x = (PF_FpLong)params[OLMRADIALBLUR_CENTER]->u.td.x_value / 65536.0;
	info.center_y = (PF_FpLong)params[OLMRADIALBLUR_CENTER]->u.td.y_value / 65536.0;
	info.outer_strength = params[OLMRADIALBLUR_OUTER_STRENGTH]->u.sd.value;
	info.outer_offset_mode = params[OLMRADIALBLUR_OUTER_OFFSET_MODE]->u.pd.value;
	info.outer_offset = params[OLMRADIALBLUR_OUTER_OFFSET]->u.sd.value;
	info.inner_strength = params[OLMRADIALBLUR_INNER_STRENGTH]->u.sd.value;
	info.repeat_border = params[OLMRADIALBLUR_REPEAT_BORDER]->u.bd.value;
	info.ratio = params[OLMRADIALBLUR_RATIO]->u.fs_d.value;
	info.angle_deg = params[OLMRADIALBLUR_ANGLE]->u.fs_d.value;
	info.quality = params[OLMRADIALBLUR_QUALITY]->u.fs_d.value;
	info.brightness_gain = params[OLMRADIALBLUR_BRIGHTNESS_GAIN]->u.fs_d.value;
	info.size_variation = params[OLMRADIALBLUR_SIZE_VARIATION]->u.fs_d.value;
	info.noise_variation = params[OLMRADIALBLUR_NOISE_VARIATION]->u.fs_d.value;
	info.comp_width = comp_width;
	info.comp_height = comp_height;
	return info;
}

static PF_Err
Render(PF_InData *, PF_OutData *, PF_ParamDef *params[], PF_LayerDef *output)
{
	OLMRadialBlurInfo info = InfoFromParams(params,
		params[OLMRADIALBLUR_INPUT]->u.ld.width,
		params[OLMRADIALBLUR_INPUT]->u.ld.height);
	short bitdepth = PF_WORLD_IS_DEEP(output) ? 16 : 8;
	return RenderWorld(&params[OLMRADIALBLUR_INPUT]->u.ld, output, info, bitdepth);
}

typedef struct {
	PF_FpLong comp_width;
	PF_FpLong comp_height;
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
		OLMRADIALBLUR_INPUT, OLMRADIALBLUR_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
		PreRenderData *pre = new PreRenderData;
		pre->comp_width = in_result.ref_width > 0 ? (PF_FpLong)in_result.ref_width : 0.0;
		pre->comp_height = in_result.ref_height > 0 ? (PF_FpLong)in_result.ref_height : 0.0;
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
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, OLMRADIALBLUR_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (err || !input_world || !output_world) {
		extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMRADIALBLUR_INPUT);
		return err;
	}

	PF_ParamDef checked[OLMRADIALBLUR_NUM_PARAMS];
	PF_ParamDef *param_ptrs[OLMRADIALBLUR_NUM_PARAMS] = {};
	for (int i = 1; i < OLMRADIALBLUR_NUM_PARAMS; ++i) {
		AEFX_CLR_STRUCT(checked[i]);
		ERR(PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
		                      in_data->time_step, in_data->time_scale, &checked[i]));
		param_ptrs[i] = &checked[i];
	}
	param_ptrs[OLMRADIALBLUR_INPUT] = NULL;

	PF_FpLong comp_w = input_world->width;
	PF_FpLong comp_h = input_world->height;
	if (PreRenderData *pre = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data)) {
		if (pre->comp_width > 0.0) comp_w = pre->comp_width;
		if (pre->comp_height > 0.0) comp_h = pre->comp_height;
	}

	if (!err) {
		OLMRadialBlurInfo info = InfoFromParams(param_ptrs, comp_w, comp_h);
		ERR(RenderWorld(input_world, output_world, info, extra->input->bitdepth));
	}

	for (int i = 1; i < OLMRADIALBLUR_NUM_PARAMS; ++i) {
		PF_CHECKIN_PARAM(in_data, &checked[i]);
	}
	extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMRADIALBLUR_INPUT);
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
		"OLM RadialBlur",
		"OLM RadialBlur",
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

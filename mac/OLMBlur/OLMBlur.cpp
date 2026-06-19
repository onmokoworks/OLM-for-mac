#include "OLMBlur.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>

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
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BlurAmount_Param_Name),
	                     0.05, 1000.0, 5.0, 50.0, 1.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     BLUR_AMOUNT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_BlurSmoothness_Param_Name),
	             1, 100, 1, 100, 1,
	             1, 0, 0,
	             BLUR_SMOOTHNESS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Repeat_Param_Name),
	              1, 10, 1, 10, 2,
	              REPEAT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_BiasDirection_Param_Name),
	             2, 1,
	             GetStringPtr(StrID_BiasDirection_Choices),
	             BIAS_DIRECTION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_Legacy_Param_Name),
	                "", FALSE, 0,
	                LEGACY_DISK_ID);

	out_data->num_params = OLMBLUR_NUM_PARAMS;
	return err;
}

struct BlurParams {
	float blur_amount;
	float blur_smoothness;
	A_long repeat;
	A_long bias_dir;
	A_long legacy;
};

static void blur_1d_horizontal(
	const float *srcRGB, const u_char *srcA,
	float *dstRGB, u_char *dstA,
	A_long w, A_long h, A_long radius, const float *weights)
{
	for (A_long y = 0; y < h; ++y) {
		const float *srow = srcRGB + y * w * 3;
		float *drow = dstRGB + y * w * 3;
		const u_char *sa = srcA + y * w;
		u_char *da = dstA + y * w;
		for (A_long x = 0; x < w; ++x) {
			da[x] = sa[x];
			if (!sa[x]) {
				drow[x*3+0] = srow[x*3+0];
				drow[x*3+1] = srow[x*3+1];
				drow[x*3+2] = srow[x*3+2];
				continue;
			}
			float sumR = 0, sumG = 0, sumB = 0, sumW = 0;
			A_long left = (x < radius) ? x : radius;
			for (A_long k = 0; k <= left; ++k) {
				A_long xi = x - k;
				if (!sa[xi]) break;
				float w_ = weights[k];
				sumW += w_;
				sumR += w_ * srow[xi*3+0];
				sumG += w_ * srow[xi*3+1];
				sumB += w_ * srow[xi*3+2];
			}
			A_long right = (w - 1 - x < radius) ? (w - 1 - x) : radius;
			for (A_long k = 1; k <= right; ++k) {
				A_long xi = x + k;
				if (!sa[xi]) break;
				float w_ = weights[k];
				sumW += w_;
				sumR += w_ * srow[xi*3+0];
				sumG += w_ * srow[xi*3+1];
				sumB += w_ * srow[xi*3+2];
			}
			if (sumW == 0) {
				drow[x*3+0] = drow[x*3+1] = drow[x*3+2] = 0;
			} else {
				float inv = 1.0f / sumW;
				drow[x*3+0] = sumR * inv;
				drow[x*3+1] = sumG * inv;
				drow[x*3+2] = sumB * inv;
			}
		}
	}
}

static void blur_1d_vertical(
	const float *srcRGB, const u_char *srcA,
	float *dstRGB, u_char *dstA,
	A_long w, A_long h, A_long radius, const float *weights)
{
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			A_long idx = y * w + x;
			dstA[idx] = srcA[idx];
			if (!srcA[idx]) {
				dstRGB[idx*3+0] = srcRGB[idx*3+0];
				dstRGB[idx*3+1] = srcRGB[idx*3+1];
				dstRGB[idx*3+2] = srcRGB[idx*3+2];
				continue;
			}
			float sumR = 0, sumG = 0, sumB = 0, sumW = 0;
			A_long up = (y < radius) ? y : radius;
			for (A_long k = 0; k <= up; ++k) {
				A_long yi = y - k;
				A_long i = yi * w + x;
				if (!srcA[i]) break;
				float w_ = weights[k];
				sumW += w_;
				sumR += w_ * srcRGB[i*3+0];
				sumG += w_ * srcRGB[i*3+1];
				sumB += w_ * srcRGB[i*3+2];
			}
			A_long down = (h - 1 - y < radius) ? (h - 1 - y) : radius;
			for (A_long k = 1; k <= down; ++k) {
				A_long yi = y + k;
				A_long i = yi * w + x;
				if (!srcA[i]) break;
				float w_ = weights[k];
				sumW += w_;
				sumR += w_ * srcRGB[i*3+0];
				sumG += w_ * srcRGB[i*3+1];
				sumB += w_ * srcRGB[i*3+2];
			}
			if (sumW == 0) {
				dstRGB[idx*3+0] = dstRGB[idx*3+1] = dstRGB[idx*3+2] = 0;
			} else {
				float inv = 1.0f / sumW;
				dstRGB[idx*3+0] = sumR * inv;
				dstRGB[idx*3+1] = sumG * inv;
				dstRGB[idx*3+2] = sumB * inv;
			}
		}
	}
}

static void legacy_blur_1d_horizontal(
	const float *srcRGB, const u_char *srcA,
	float *dstRGB, u_char *dstA,
	A_long w, A_long h, A_long radius, const float *kernel)
{
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			A_long idx = y * w + x;
			dstA[idx] = srcA[idx];
			if (!srcA[idx]) {
				dstRGB[idx*3+0] = srcRGB[idx*3+0];
				dstRGB[idx*3+1] = srcRGB[idx*3+1];
				dstRGB[idx*3+2] = srcRGB[idx*3+2];
				continue;
			}
			float sumR = 0.0f, sumG = 0.0f, sumB = 0.0f, sumW = 0.0f;
			bool all_same = true;
			bool have_prev = false;
			float prevR = 0.0f, prevG = 0.0f, prevB = 0.0f;
			for (A_long off = -radius; off <= radius; ++off) {
				A_long sx = x + off;
				if (sx <= 0 || sx >= w) continue;
				A_long si = y * w + sx;
				if (!srcA[si]) break;
				float wr = kernel[radius + off];
				sumW += wr;
				sumR += wr * srcRGB[si*3+0];
				sumG += wr * srcRGB[si*3+1];
				sumB += wr * srcRGB[si*3+2];
				float curR = srcRGB[si*3+0];
				float curG = srcRGB[si*3+1];
				float curB = srcRGB[si*3+2];
				if (have_prev && (curR != prevR || curG != prevG || curB != prevB)) {
					all_same = false;
				}
				prevR = curR;
				prevG = curG;
				prevB = curB;
				have_prev = true;
			}
			if (all_same || sumW == 0.0f) {
				dstRGB[idx*3+0] = srcRGB[idx*3+0];
				dstRGB[idx*3+1] = srcRGB[idx*3+1];
				dstRGB[idx*3+2] = srcRGB[idx*3+2];
			} else {
				float inv = 1.0f / sumW;
				dstRGB[idx*3+0] = sumR * inv;
				dstRGB[idx*3+1] = sumG * inv;
				dstRGB[idx*3+2] = sumB * inv;
			}
		}
	}
}

static void legacy_blur_1d_vertical(
	const float *srcRGB, const u_char *srcA,
	float *dstRGB, u_char *dstA,
	A_long w, A_long h, A_long radius, const float *kernel)
{
	for (A_long y = 0; y < h; ++y) {
		for (A_long x = 0; x < w; ++x) {
			A_long idx = y * w + x;
			dstA[idx] = srcA[idx];
			if (!srcA[idx]) {
				dstRGB[idx*3+0] = srcRGB[idx*3+0];
				dstRGB[idx*3+1] = srcRGB[idx*3+1];
				dstRGB[idx*3+2] = srcRGB[idx*3+2];
				continue;
			}
			float sumR = 0.0f, sumG = 0.0f, sumB = 0.0f, sumW = 0.0f;
			bool all_same = true;
			bool have_prev = false;
			float prevR = 0.0f, prevG = 0.0f, prevB = 0.0f;
			for (A_long off = -radius; off <= radius; ++off) {
				A_long sy = y + off;
				if (sy <= 0 || sy >= h) continue;
				A_long si = sy * w + x;
				if (!srcA[si]) break;
				float wr = kernel[radius + off];
				sumW += wr;
				sumR += wr * srcRGB[si*3+0];
				sumG += wr * srcRGB[si*3+1];
				sumB += wr * srcRGB[si*3+2];
				float curR = srcRGB[si*3+0];
				float curG = srcRGB[si*3+1];
				float curB = srcRGB[si*3+2];
				if (have_prev && (curR != prevR || curG != prevG || curB != prevB)) {
					all_same = false;
				}
				prevR = curR;
				prevG = curG;
				prevB = curB;
				have_prev = true;
			}
			if (all_same || sumW == 0.0f) {
				dstRGB[idx*3+0] = srcRGB[idx*3+0];
				dstRGB[idx*3+1] = srcRGB[idx*3+1];
				dstRGB[idx*3+2] = srcRGB[idx*3+2];
			} else {
				float inv = 1.0f / sumW;
				dstRGB[idx*3+0] = sumR * inv;
				dstRGB[idx*3+1] = sumG * inv;
				dstRGB[idx*3+2] = sumB * inv;
			}
		}
	}
}

template <typename P>
static void load_input(const PF_EffectWorld *src, float *rgb, u_char *alpha, float scale);

template <>
void load_input<PF_Pixel8>(const PF_EffectWorld *src, float *rgb, u_char *alpha, float /*scale*/)
{
	A_long w = src->width, h = src->height;
	A_long rb = src->rowbytes;
	for (A_long y = 0; y < h; ++y) {
		const PF_Pixel8 *row = (const PF_Pixel8*)((const char*)src->data + y * rb);
		for (A_long x = 0; x < w; ++x) {
			rgb[(y*w + x)*3+0] = (float)row[x].red;
			rgb[(y*w + x)*3+1] = (float)row[x].green;
			rgb[(y*w + x)*3+2] = (float)row[x].blue;
			alpha[y*w + x] = row[x].alpha ? 1 : 0;
		}
	}
}

template <>
void load_input<PF_Pixel16>(const PF_EffectWorld *src, float *rgb, u_char *alpha, float /*scale*/)
{
	A_long w = src->width, h = src->height;
	A_long rb = src->rowbytes;
	for (A_long y = 0; y < h; ++y) {
		const PF_Pixel16 *row = (const PF_Pixel16*)((const char*)src->data + y * rb);
		for (A_long x = 0; x < w; ++x) {
			rgb[(y*w + x)*3+0] = (float)row[x].red;
			rgb[(y*w + x)*3+1] = (float)row[x].green;
			rgb[(y*w + x)*3+2] = (float)row[x].blue;
			alpha[y*w + x] = row[x].alpha ? 1 : 0;
		}
	}
}

template <>
void load_input<PF_PixelFloat>(const PF_EffectWorld *src, float *rgb, u_char *alpha, float /*scale*/)
{
	A_long w = src->width, h = src->height;
	A_long rb = src->rowbytes;
	for (A_long y = 0; y < h; ++y) {
		const PF_PixelFloat *row = (const PF_PixelFloat*)((const char*)src->data + y * rb);
		for (A_long x = 0; x < w; ++x) {
			rgb[(y*w + x)*3+0] = row[x].red;
			rgb[(y*w + x)*3+1] = row[x].green;
			rgb[(y*w + x)*3+2] = row[x].blue;
			alpha[y*w + x] = (row[x].alpha > 0.0f) ? 1 : 0;
		}
	}
}

static inline float round_blur_value(float v, A_long legacy)
{
	return legacy ? floorf(v + 0.5f) : nearbyintf(v);
}

static void store8(PF_EffectWorld *dst, const float *rgb, A_long legacy)
{
	A_long w = dst->width, h = dst->height;
	A_long rb = dst->rowbytes;
	for (A_long y = 0; y < h; ++y) {
		PF_Pixel8 *row = (PF_Pixel8*)((char*)dst->data + y * rb);
		for (A_long x = 0; x < w; ++x) {
			float r = round_blur_value(rgb[(y*w + x)*3+0], legacy);
			float g = round_blur_value(rgb[(y*w + x)*3+1], legacy);
			float b = round_blur_value(rgb[(y*w + x)*3+2], legacy);
			if (r < 0) r = 0; if (r > 255) r = 255;
			if (g < 0) g = 0; if (g > 255) g = 255;
			if (b < 0) b = 0; if (b > 255) b = 255;
			row[x].red   = (u_char)r;
			row[x].green = (u_char)g;
			row[x].blue  = (u_char)b;
		}
	}
}

static void store16(PF_EffectWorld *dst, const float *rgb, A_long legacy)
{
	A_long w = dst->width, h = dst->height;
	A_long rb = dst->rowbytes;
	for (A_long y = 0; y < h; ++y) {
		PF_Pixel16 *row = (PF_Pixel16*)((char*)dst->data + y * rb);
		for (A_long x = 0; x < w; ++x) {
			float r = round_blur_value(rgb[(y*w + x)*3+0], legacy);
			float g = round_blur_value(rgb[(y*w + x)*3+1], legacy);
			float b = round_blur_value(rgb[(y*w + x)*3+2], legacy);
			if (r < 0) r = 0; if (r > 32768) r = 32768;
			if (g < 0) g = 0; if (g > 32768) g = 32768;
			if (b < 0) b = 0; if (b > 32768) b = 32768;
			row[x].red   = (u_short)r;
			row[x].green = (u_short)g;
			row[x].blue  = (u_short)b;
		}
	}
}

static void storeFloat(PF_EffectWorld *dst, const float *rgb)
{
	A_long w = dst->width, h = dst->height;
	A_long rb = dst->rowbytes;
	for (A_long y = 0; y < h; ++y) {
		PF_PixelFloat *row = (PF_PixelFloat*)((char*)dst->data + y * rb);
		for (A_long x = 0; x < w; ++x) {
			row[x].red   = rgb[(y*w + x)*3+0];
			row[x].green = rgb[(y*w + x)*3+1];
			row[x].blue  = rgb[(y*w + x)*3+2];
		}
	}
}

static PF_Err
BlurRender(PF_InData *in_data, PF_EffectWorld *input, PF_EffectWorld *output,
           short bpc, const BlurParams *bp)
{
	PF_Err err = PF_Err_NONE;
	A_long w = input->width, h = input->height;
	if (w <= 0 || h <= 0) return err;

	float blur_amount = bp->blur_amount;
	blur_amount *= ((float)in_data->downsample_x.num / (float)in_data->downsample_x.den);
	if (blur_amount <= 0) {
		return PF_COPY(input, output, NULL, NULL);
	}

	size_t npix = (size_t)w * h;
	float *buf1 = (float*)malloc(npix * 3 * sizeof(float));
	float *buf2 = (float*)malloc(npix * 3 * sizeof(float));
	u_char *alpha1 = (u_char*)malloc(npix);
	u_char *alpha2 = (u_char*)malloc(npix);
	if (!buf1 || !buf2 || !alpha1 || !alpha2) {
		free(buf1); free(buf2); free(alpha1); free(alpha2);
		return PF_Err_OUT_OF_MEMORY;
	}

	if (bpc == 8)       load_input<PF_Pixel8>(input, buf1, alpha1, 1.0f);
	else if (bpc == 16) load_input<PF_Pixel16>(input, buf1, alpha1, 1.0f);
	else                load_input<PF_PixelFloat>(input, buf1, alpha1, 1.0f);

	A_long max_radius = (A_long)blur_amount + 2;
	float *weights = (float*)malloc((max_radius * 2 + 1) * sizeof(float));
	if (!weights) {
		free(buf1); free(buf2); free(alpha1); free(alpha2);
		return PF_Err_OUT_OF_MEMORY;
	}

	if (bp->legacy) {
		A_long radius = (A_long)blur_amount;
		if (radius > 0) {
			float smoothness = bp->blur_smoothness;
			if (smoothness <= 0.0f) smoothness = 1.0f;
			float sigma_base = ((blur_amount * smoothness) / 100.0f) * (blur_amount / 3.0f);
			for (A_long iter = 1; iter <= bp->repeat; ++iter) {
				float sigma = sigma_base / (float)iter;
				if (sigma <= 0.0f) break;
				float denom = 2.0f * sigma * sigma;
				weights[radius] = 1.0f;
				for (A_long k = 1; k <= radius; ++k) {
					float v = expf(-(float)(k*k) / denom);
					weights[radius - k] = v;
					weights[radius + k] = v;
				}
				if (bp->bias_dir == BIAS_DIR_VERTICAL) {
					legacy_blur_1d_horizontal(buf1, alpha1, buf2, alpha2, w, h, radius, weights);
					legacy_blur_1d_vertical  (buf2, alpha2, buf1, alpha1, w, h, radius, weights);
				} else if (bp->bias_dir == BIAS_DIR_HORIZONTAL) {
					legacy_blur_1d_vertical  (buf1, alpha1, buf2, alpha2, w, h, radius, weights);
					legacy_blur_1d_horizontal(buf2, alpha2, buf1, alpha1, w, h, radius, weights);
				}
			}
		}
	} else {
		float decay = 1.0f;
		if (bp->repeat > 1) decay = powf(3.0f / blur_amount, 1.0f / (float)(bp->repeat - 1));

		for (A_long iter = 0; iter < bp->repeat; ++iter) {
			double radius_d = (double)blur_amount * pow((double)decay, (double)iter);
			A_long radius = (A_long)radius_d;
			if (radius == 0) break;
			float sigma = (float)radius_d / 3.0f;
			float denom = 2.0f * sigma * sigma;
			for (A_long k = 0; k <= radius; ++k) {
				weights[k] = expf(-(float)(k*k) / denom);
			}

			if (bp->bias_dir == BIAS_DIR_VERTICAL) {
				blur_1d_horizontal(buf1, alpha1, buf2, alpha2, w, h, radius, weights);
				blur_1d_vertical  (buf2, alpha2, buf1, alpha1, w, h, radius, weights);
			} else if (bp->bias_dir == BIAS_DIR_HORIZONTAL) {
				blur_1d_vertical  (buf1, alpha1, buf2, alpha2, w, h, radius, weights);
				blur_1d_horizontal(buf2, alpha2, buf1, alpha1, w, h, radius, weights);
			}
		}
	}
	free(weights);

	if (bpc == 8)       store8(output, buf1, bp->legacy);
	else if (bpc == 16) store16(output, buf1, bp->legacy);
	else                storeFloat(output, buf1);

	free(buf1); free(buf2); free(alpha1); free(alpha2);
	return err;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	BlurParams bp;
	AEFX_CLR_STRUCT(bp);
	bp.blur_amount = (float)params[OLMBLUR_BLUR_AMOUNT]->u.fs_d.value;
	bp.blur_smoothness = (float)params[OLMBLUR_BLUR_SMOOTHNESS]->u.fd.value / 65536.0f;
	bp.repeat      = params[OLMBLUR_REPEAT]->u.sd.value;
	bp.bias_dir    = params[OLMBLUR_BIAS_DIRECTION]->u.pd.value;
	bp.legacy      = params[OLMBLUR_LEGACY]->u.bd.value;

	PF_EffectWorld *input = &params[OLMBLUR_INPUT]->u.ld;
	short bpc = PF_WORLD_IS_DEEP(output) ? 16 : 8;

	ERR(PF_COPY(input, output, NULL, NULL));
	ERR(BlurRender(in_data, input, output, bpc, &bp));
	return err;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMBLUR_INPUT, OLMBLUR_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		extra->output->result_rect     = in_result.result_rect;
		extra->output->max_result_rect = in_result.max_result_rect;
		extra->output->solid = FALSE;
		extra->output->pre_render_data = NULL;
		extra->output->flags = 0;
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, OLMBLUR_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (err || !input_world || !output_world) {
		extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMBLUR_INPUT);
		return err;
	}

	BlurParams bp;
	AEFX_CLR_STRUCT(bp);

	PF_ParamDef p;
	AEFX_CLR_STRUCT(p);
	ERR(PF_CHECKOUT_PARAM(in_data, OLMBLUR_BLUR_AMOUNT, in_data->current_time,
	                      in_data->time_step, in_data->time_scale, &p));
	if (!err) { bp.blur_amount = (float)p.u.fs_d.value; PF_CHECKIN_PARAM(in_data, &p); }

	AEFX_CLR_STRUCT(p);
	ERR(PF_CHECKOUT_PARAM(in_data, OLMBLUR_BLUR_SMOOTHNESS, in_data->current_time,
	                      in_data->time_step, in_data->time_scale, &p));
	if (!err) { bp.blur_smoothness = (float)p.u.fd.value / 65536.0f; PF_CHECKIN_PARAM(in_data, &p); }

	AEFX_CLR_STRUCT(p);
	ERR(PF_CHECKOUT_PARAM(in_data, OLMBLUR_REPEAT, in_data->current_time,
	                      in_data->time_step, in_data->time_scale, &p));
	if (!err) { bp.repeat = p.u.sd.value; PF_CHECKIN_PARAM(in_data, &p); }

	AEFX_CLR_STRUCT(p);
	ERR(PF_CHECKOUT_PARAM(in_data, OLMBLUR_BIAS_DIRECTION, in_data->current_time,
	                      in_data->time_step, in_data->time_scale, &p));
	if (!err) { bp.bias_dir = p.u.pd.value; PF_CHECKIN_PARAM(in_data, &p); }

	AEFX_CLR_STRUCT(p);
	ERR(PF_CHECKOUT_PARAM(in_data, OLMBLUR_LEGACY, in_data->current_time,
	                      in_data->time_step, in_data->time_scale, &p));
	if (!err) { bp.legacy = p.u.bd.value; PF_CHECKIN_PARAM(in_data, &p); }

	short bpc = extra->input->bitdepth;
	ERR(PF_COPY(input_world, output_world, NULL, NULL));
	ERR(BlurRender(in_data, input_world, output_world, bpc, &bp));

	extra->cb->checkin_layer_pixels(in_data->effect_ref, OLMBLUR_INPUT);
	return err;
}

extern "C" DllExport
PF_Err PluginDataEntryFunction2(
	PF_PluginDataPtr  inPtr,
	PF_PluginDataCB2  inPluginDataCallBackPtr,
	SPBasicSuite     *inSPBasicSuitePtr,
	const char       *inHostName,
	const char       *inHostVersion)
{
	PF_Err result = PF_Err_INVALID_CALLBACK;
	result = PF_REGISTER_EFFECT_EXT2(
		inPtr, inPluginDataCallBackPtr,
		"OLM Blur",
		"OLM OLM Blur",
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

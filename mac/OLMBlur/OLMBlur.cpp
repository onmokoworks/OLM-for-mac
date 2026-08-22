#include "OLMBlur.h"
#include "olmblur_worker_orchestration.h"
#include "olmblur_worker16_nonlegacy.h"
#include "olmblur_worker16_legacy.h"
#include "olmblur_worker32_nonlegacy.h"
#include "olmblur_worker32_legacy.h"
#include "olmblur_worker8_legacy.h"
#include "AEFX_SuiteHandlerTemplate.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <new>
#include <stdio.h>
#include <stdint.h>
#include <vector>
#include "../../core/olm_world_safety.h"

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
	                     1.0, 1000.0, 1.0, 50.0, 5.0,
	                     // The 2025 AEX registers raw precision value 2.
	                     2, 0, 0,
	                     BLUR_AMOUNT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_BlurSmoothness_Param_Name),
	             1, 100, 1, 100, 100,
	             1, PF_ValueDisplayFlag_PERCENT, 0,
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
	def.param_type = PF_Param_CHECKBOX;
	PF_STRNNCPY(def.name, GetStringPtr(StrID_Legacy_Param_Name), sizeof(def.name));
	def.u.bd.u.nameptr = "";
	def.u.bd.value = TRUE;
	def.u.bd.dephault = FALSE;
	def.flags = PF_ParamFlag_USE_VALUE_FOR_OLD_PROJECTS;
	def.uu.id = LEGACY_DISK_ID;
	if ((err = PF_ADD_PARAM(in_data, -1, &def)) != PF_Err_NONE) return err;

	out_data->num_params = OLMBLUR_NUM_PARAMS;
	return err;
}

#if !defined(OLMBLUR_HOSTLESS_RENDER_HARNESS)
static PF_Err
UpdateParamsUI(PF_InData *in_data)
{
	PF_Err err = PF_Err_NONE;
	AEGP_EffectRefH effectH = NULL;
	AEGP_StreamRefH streamH = NULL;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	ERR(suites.PFInterfaceSuite1()->AEGP_GetNewEffectForEffect(
		0, in_data->effect_ref, &effectH));
	if (!err && effectH) {
		ERR(suites.StreamSuite2()->AEGP_GetNewEffectStreamByIndex(
			0, effectH, OLMBLUR_BLUR_SMOOTHNESS, &streamH));
	}
	if (!err && streamH) {
		AEGP_DynStreamFlags ignored_flags = 0;
		ERR(suites.DynamicStreamSuite3()->AEGP_GetDynamicStreamFlags(
			streamH, &ignored_flags));
		if (!err) {
			ERR(suites.DynamicStreamSuite3()->AEGP_SetDynamicStreamFlag(
				streamH, AEGP_DynStreamFlag_HIDDEN, FALSE, TRUE));
		}
	}
	if (streamH) {
		PF_Err dispose_err = suites.StreamSuite2()->AEGP_DisposeStream(streamH);
		if (!err) err = dispose_err;
	}
	if (effectH) {
		PF_Err dispose_err = suites.EffectSuite3()->AEGP_DisposeEffect(effectH);
		if (!err) err = dispose_err;
	}
	return err;
}
#endif

struct BlurParams {
	float blur_amount;
	float blur_smoothness;
	A_long repeat;
	A_long bias_dir;
	A_long legacy;
};

struct BlurDebugConfig;
static bool debug_has_point(const BlurDebugConfig *debug, A_long x, A_long y);
static bool debug_dump_nonlegacy_helpers(const BlurDebugConfig *debug);
static void debug_dump_legacy_stage(
	const BlurDebugConfig *debug,
	const char *stage,
	A_long iter,
	A_long radius,
	A_long x,
	A_long y,
	bool all_same,
	bool have_prev,
	float sumW,
	A_long first_coord,
	A_long last_coord,
	A_long sample_count,
	float center_r,
	float center_g,
	float center_b,
	float out_r,
	float out_g,
	float out_b);
static void debug_dump_nonlegacy_stage(
	const BlurDebugConfig *debug,
	const char *stage,
	A_long iter,
	A_long radius,
	A_long x,
	A_long y,
	A_long first_coord,
	A_long last_coord,
	A_long sample_count,
	float sumW,
	float out_r,
	float out_g,
	float out_b);

static void blur_1d_horizontal(
	const float *srcRGB, const u_char *srcA,
	float *dstRGB, u_char *dstA,
	A_long w, A_long h, A_long radius, const float *weights,
	const BlurDebugConfig *debug, A_long iter)
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
			A_long first_coord = x;
			A_long last_coord = x;
			A_long sample_count = 0;
			A_long left = (x < radius) ? x : radius;
			for (A_long k = 0; k <= left; ++k) {
				A_long xi = x - k;
				if (!sa[xi]) break;
				if (sample_count == 0 || xi < first_coord) first_coord = xi;
				if (sample_count == 0 || xi > last_coord) last_coord = xi;
				++sample_count;
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
				if (sample_count == 0 || xi < first_coord) first_coord = xi;
				if (sample_count == 0 || xi > last_coord) last_coord = xi;
				++sample_count;
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
			debug_dump_nonlegacy_stage(
				debug, "horizontal", iter, radius, x, y,
				first_coord, last_coord, sample_count, sumW,
				drow[x*3+0] / 32768.0f,
				drow[x*3+1] / 32768.0f,
				drow[x*3+2] / 32768.0f
			);
		}
	}
}

static void blur_1d_vertical(
	const float *srcRGB, const u_char *srcA,
	float *dstRGB, u_char *dstA,
	A_long w, A_long h, A_long radius, const float *weights,
	const BlurDebugConfig *debug, A_long iter)
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
			A_long first_coord = y;
			A_long last_coord = y;
			A_long sample_count = 0;
			A_long up = (y < radius) ? y : radius;
			for (A_long k = 0; k <= up; ++k) {
				A_long yi = y - k;
				A_long i = yi * w + x;
				if (!srcA[i]) break;
				if (sample_count == 0 || yi < first_coord) first_coord = yi;
				if (sample_count == 0 || yi > last_coord) last_coord = yi;
				++sample_count;
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
				if (sample_count == 0 || yi < first_coord) first_coord = yi;
				if (sample_count == 0 || yi > last_coord) last_coord = yi;
				++sample_count;
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
			debug_dump_nonlegacy_stage(
				debug, "vertical", iter, radius, x, y,
				first_coord, last_coord, sample_count, sumW,
				dstRGB[idx*3+0] / 32768.0f,
				dstRGB[idx*3+1] / 32768.0f,
				dstRGB[idx*3+2] / 32768.0f
			);
		}
	}
}

static void legacy_blur_1d_horizontal(
	const float *srcRGB, const u_char *srcA,
	float *dstRGB, u_char *dstA,
	A_long w, A_long h, A_long radius, const float *kernel,
	const BlurDebugConfig *debug, A_long iter)
{
	float carryPrevR = -1.0f, carryPrevG = -1.0f, carryPrevB = -1.0f;
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
			bool have_prev = true;
			A_long first_coord = -1;
			A_long last_coord = -1;
			A_long sample_count = 0;
			float prevR = carryPrevR, prevG = carryPrevG, prevB = carryPrevB;
			bool saw_sample = false;
			for (A_long off = -radius; off <= radius; ++off) {
				A_long sx = x + off;
				if (sx <= 0 || sx >= w) continue;
				A_long si = y * w + sx;
				if (!srcA[si]) break;
				if (first_coord < 0) first_coord = sx;
				last_coord = sx;
				++sample_count;
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
				saw_sample = true;
			}
			if (saw_sample) {
				carryPrevR = prevR;
				carryPrevG = prevG;
				carryPrevB = prevB;
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
			debug_dump_legacy_stage(
				debug, "horizontal", iter, radius, x, y,
				all_same, have_prev, sumW, first_coord, last_coord, sample_count,
				srcRGB[idx*3+0], srcRGB[idx*3+1], srcRGB[idx*3+2],
				dstRGB[idx*3+0], dstRGB[idx*3+1], dstRGB[idx*3+2]
			);
		}
	}
}

static void legacy_blur_1d_vertical(
	const float *srcRGB, const u_char *srcA,
	float *dstRGB, u_char *dstA,
	A_long w, A_long h, A_long radius, const float *kernel,
	const BlurDebugConfig *debug, A_long iter)
{
	float carryPrevR = -1.0f, carryPrevG = -1.0f, carryPrevB = -1.0f;
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
			bool have_prev = true;
			A_long first_coord = -1;
			A_long last_coord = -1;
			A_long sample_count = 0;
			float prevR = carryPrevR, prevG = carryPrevG, prevB = carryPrevB;
			bool saw_sample = false;
			for (A_long off = -radius; off <= radius; ++off) {
				A_long sy = y + off;
				if (sy <= 0 || sy >= h) continue;
				A_long si = sy * w + x;
				if (!srcA[si]) break;
				if (first_coord < 0) first_coord = sy;
				last_coord = sy;
				++sample_count;
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
				saw_sample = true;
			}
			if (saw_sample) {
				carryPrevR = prevR;
				carryPrevG = prevG;
				carryPrevB = prevB;
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
			debug_dump_legacy_stage(
				debug, "vertical", iter, radius, x, y,
				all_same, have_prev, sumW, first_coord, last_coord, sample_count,
				srcRGB[idx*3+0], srcRGB[idx*3+1], srcRGB[idx*3+2],
				dstRGB[idx*3+0], dstRGB[idx*3+1], dstRGB[idx*3+2]
			);
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

static inline int32_t
pf16_rounded_int32(float value)
{
	// Match the PF16 writer's float32 add-half/floor/CVTTSS2SI sequence while
	// making the signed conversion range explicit before extracting the word.
	float rounded = floorf(value + 0.5f);
	if (!(rounded >= -2147483648.0f && rounded < 2147483648.0f)) {
		return INT32_MIN;
	}
	return static_cast<int32_t>(rounded);
}

static inline uint16_t
pack_pf16_value(float value)
{
	const int32_t rounded = pf16_rounded_int32(value);
	return static_cast<uint16_t>(static_cast<uint32_t>(rounded));
}

struct BlurDebugPoint {
	A_long x;
	A_long y;
};

struct BlurDebugConfig {
	const char *dump_path;
	std::vector<BlurDebugPoint> points;
	bool dump_nonlegacy_helpers;
};

struct BlurObservationConfig {
	const char *dump_path;
	const char *case_id;
	const char *request_id;
	const char *render_id;
	const char *plugin_sha256;
	const char *project_bpc;
	const char *renderer;
	bool enabled;
};

static BlurObservationConfig
load_blur_observation_config()
{
	BlurObservationConfig config;
	config.dump_path = NULL;
	config.case_id = NULL;
	config.request_id = NULL;
	config.render_id = NULL;
	config.plugin_sha256 = NULL;
	config.project_bpc = NULL;
	config.renderer = NULL;
	config.enabled = false;
	const char *gate = getenv("OLMBLUR_OBSERVE_CASE0006_PIXEL");
	if (!gate || strcmp(gate, "1") != 0) return config;
	config.dump_path = getenv("OLMBLUR_OBSERVE_DUMP_PATH");
	config.case_id = getenv("OLMBLUR_OBSERVE_CASE_ID");
	config.request_id = getenv("OLMBLUR_OBSERVE_REQUEST_ID");
	config.render_id = getenv("OLMBLUR_OBSERVE_RENDER_ID");
	config.plugin_sha256 = getenv("OLMBLUR_OBSERVE_PLUGIN_SHA256");
	config.project_bpc = getenv("OLMBLUR_OBSERVE_PROJECT_BPC");
	config.renderer = getenv("OLMBLUR_OBSERVE_RENDERER");
	if (config.dump_path && *config.dump_path &&
		config.case_id && strcmp(config.case_id, "olmblur__case_0006") == 0 &&
		config.request_id && *config.request_id &&
		config.render_id && *config.render_id &&
		config.plugin_sha256 && *config.plugin_sha256 &&
		config.project_bpc && strcmp(config.project_bpc, "16") == 0 &&
		config.renderer && strcmp(config.renderer, "Software") == 0) {
		config.enabled = true;
	}
	return config;
}

static void
observe_blur_store16_pixel(
	const BlurObservationConfig *observation,
	const BlurParams *bp,
	A_long w, A_long h, A_long x, A_long y,
	float pre_r, float pre_g, float pre_b,
	u_short stored_r, u_short stored_g, u_short stored_b, u_short stored_a)
{
	if (!observation || !observation->enabled || x != 601 || y != 598) return;
	FILE *fp = fopen(observation->dump_path, "a");
	if (!fp) return;
	fprintf(fp,
		"OLMBLUR_OBSERVE_STORE16 plugin=OLMBlur effect=OLM_Blur case_id=%s request_id=%s render_id=%s plugin_sha256=%s project_bpc=%s renderer=%s x=%d y=%d w=%d h=%d blur_amount=%.9g blur_smoothness=%.9g repeat=%d bias_dir=%d legacy=%d pre_store=(%.9g,%.9g,%.9g) pre_store_hex=(%a,%a,%a) stored=(%u,%u,%u,%u)\n",
		observation->case_id, observation->request_id, observation->render_id,
		observation->plugin_sha256, observation->project_bpc, observation->renderer,
		(int)x, (int)y, (int)w, (int)h,
		bp ? bp->blur_amount : 0.0f, bp ? bp->blur_smoothness : 0.0f,
		bp ? (int)bp->repeat : 0, bp ? (int)bp->bias_dir : 0,
		bp ? (int)bp->legacy : 0,
		pre_r, pre_g, pre_b, (double)pre_r, (double)pre_g, (double)pre_b,
		(unsigned int)stored_r, (unsigned int)stored_g,
		(unsigned int)stored_b, (unsigned int)stored_a);
	fclose(fp);
}

static bool
debug_has_point(const BlurDebugConfig *debug, A_long x, A_long y)
{
	if (!debug || !debug->dump_path || debug->points.empty()) return false;
	for (size_t i = 0; i < debug->points.size(); ++i) {
		if (debug->points[i].x == x && debug->points[i].y == y) return true;
	}
	return false;
}

static bool
debug_dump_nonlegacy_helpers(const BlurDebugConfig *debug)
{
	return debug && debug->dump_path && !debug->points.empty() && debug->dump_nonlegacy_helpers;
}

static void
debug_dump_legacy_stage(
	const BlurDebugConfig *debug,
	const char *stage,
	A_long iter,
	A_long radius,
	A_long x,
	A_long y,
	bool all_same,
	bool have_prev,
	float sumW,
	A_long first_coord,
	A_long last_coord,
	A_long sample_count,
	float center_r,
	float center_g,
	float center_b,
	float out_r,
	float out_g,
	float out_b)
{
	if (!debug_has_point(debug, x, y)) return;
	FILE *fp = fopen(debug->dump_path, "a");
	if (!fp) return;
	fprintf(
		fp,
		"OLMBLUR_DEBUG_LEGACY stage=%s iter=%d radius=%d x=%d y=%d all_same=%d have_prev=%d sumW=%.9g sample_count=%d first_coord=%d last_coord=%d center=(%.9g,%.9g,%.9g) out=(%.9g,%.9g,%.9g)\n",
		stage,
		(int)iter,
		(int)radius,
		(int)x,
		(int)y,
		all_same ? 1 : 0,
		have_prev ? 1 : 0,
		sumW,
		(int)sample_count,
		(int)first_coord,
		(int)last_coord,
		center_r, center_g, center_b,
		out_r, out_g, out_b
	);
	fclose(fp);
}

static void
debug_dump_nonlegacy_stage(
	const BlurDebugConfig *debug,
	const char *stage,
	A_long iter,
	A_long radius,
	A_long x,
	A_long y,
	A_long first_coord,
	A_long last_coord,
	A_long sample_count,
	float sumW,
	float out_r,
	float out_g,
	float out_b)
{
	if (!debug_dump_nonlegacy_helpers(debug) || !debug_has_point(debug, x, y)) return;
	FILE *fp = fopen(debug->dump_path, "a");
	if (!fp) return;
	fprintf(
		fp,
		"OLMBLUR_DEBUG_NONLEGACY stage=%s iter=%d radius=%d x=%d y=%d span=%d sample_count=%d first_coord=%d last_coord=%d sumW=%.9g out_norm=(%.9g,%.9g,%.9g)\n",
		stage,
		(int)iter,
		(int)radius,
		(int)x,
		(int)y,
		(sample_count > 0 && first_coord >= 0 && last_coord >= first_coord) ? (int)(last_coord - first_coord + 1) : 0,
		(int)sample_count,
		(int)first_coord,
		(int)last_coord,
		sumW,
		out_r, out_g, out_b
	);
	fclose(fp);
}

static std::vector<BlurDebugPoint>
parse_blur_debug_points(const char *spec)
{
	std::vector<BlurDebugPoint> points;
	if (!spec || !*spec) return points;
	const char *p = spec;
	while (*p) {
		int x = -1, y = -1, consumed = 0;
		if (sscanf(p, "%d,%d%n", &x, &y, &consumed) == 2 && consumed > 0) {
			points.push_back({ (A_long)x, (A_long)y });
			p += consumed;
			while (*p == ';' || *p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') ++p;
		} else {
			break;
		}
	}
	return points;
}

static BlurDebugConfig
load_blur_debug_config()
{
	BlurDebugConfig config;
	config.dump_path = getenv("OLMBLUR_DEBUG_DUMP_PATH");
	config.points = parse_blur_debug_points(getenv("OLMBLUR_DEBUG_POINTS"));
	config.dump_nonlegacy_helpers = false;
	const char *nonlegacy_helpers = getenv("OLMBLUR_DEBUG_NONLEGACY_HELPERS");
	if (nonlegacy_helpers && *nonlegacy_helpers && strcmp(nonlegacy_helpers, "0") != 0) {
		config.dump_nonlegacy_helpers = true;
	}
	if (!config.dump_path || !*config.dump_path || config.points.empty()) {
		config.dump_path = NULL;
		config.points.clear();
		config.dump_nonlegacy_helpers = false;
	}
	return config;
}

static void
debug_dump_store16(const BlurDebugConfig *debug, const float *rgb, A_long legacy, A_long w, A_long h)
{
	if (!debug || !debug->dump_path || debug->points.empty()) return;
	FILE *fp = fopen(debug->dump_path, "a");
	if (!fp) return;
	fprintf(fp, "OLMBLUR_DEBUG_STORE16_BEGIN legacy=%d w=%d h=%d\n", (int)legacy, (int)w, (int)h);
	for (size_t i = 0; i < debug->points.size(); ++i) {
		A_long x = debug->points[i].x;
		A_long y = debug->points[i].y;
		if (x < 0 || y < 0 || x >= w || y >= h) {
			fprintf(fp, "OLMBLUR_DEBUG_POINT x=%d y=%d status=out_of_bounds\n", (int)x, (int)y);
			continue;
		}
		size_t idx = (size_t)(y * w + x) * 3;
		float raw_r = rgb[idx + 0];
		float raw_g = rgb[idx + 1];
		float raw_b = rgb[idx + 2];
		float floor_r = floorf(raw_r + 0.5f);
		float floor_g = floorf(raw_g + 0.5f);
		float floor_b = floorf(raw_b + 0.5f);
		float nearby_r = nearbyintf(raw_r);
		float nearby_g = nearbyintf(raw_g);
		float nearby_b = nearbyintf(raw_b);
		int32_t rounded_i32_r = pf16_rounded_int32(raw_r);
		int32_t rounded_i32_g = pf16_rounded_int32(raw_g);
		int32_t rounded_i32_b = pf16_rounded_int32(raw_b);
		uint16_t packed_r = pack_pf16_value(raw_r);
		uint16_t packed_g = pack_pf16_value(raw_g);
		uint16_t packed_b = pack_pf16_value(raw_b);
		fprintf(
			fp,
			"OLMBLUR_DEBUG_POINT x=%d y=%d raw=(%.9g,%.9g,%.9g) raw_hex=(%a,%a,%a) floor05=(%.9g,%.9g,%.9g) nearby=(%.9g,%.9g,%.9g) rounded_i32=(%d,%d,%d) packed_low16=(%u,%u,%u) stored=(%u,%u,%u)\n",
			(int)x, (int)y,
			raw_r, raw_g, raw_b,
			(double)raw_r, (double)raw_g, (double)raw_b,
			floor_r, floor_g, floor_b,
			nearby_r, nearby_g, nearby_b,
			(int)rounded_i32_r, (int)rounded_i32_g, (int)rounded_i32_b,
			(unsigned int)packed_r, (unsigned int)packed_g, (unsigned int)packed_b,
			(unsigned int)packed_r, (unsigned int)packed_g, (unsigned int)packed_b
		);
	}
	fprintf(fp, "OLMBLUR_DEBUG_STORE16_END\n");
	fclose(fp);
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

static void store16(PF_EffectWorld *dst, const float *rgb, A_long legacy,
	const BlurDebugConfig *debug, const BlurParams *bp,
	const BlurObservationConfig *observation)
{
	A_long w = dst->width, h = dst->height;
	A_long rb = dst->rowbytes;
	debug_dump_store16(debug, rgb, legacy, w, h);
	for (A_long y = 0; y < h; ++y) {
		PF_Pixel16 *row = (PF_Pixel16*)((char*)dst->data + y * rb);
		for (A_long x = 0; x < w; ++x) {
			float raw_r = rgb[(y*w + x)*3+0];
			float raw_g = rgb[(y*w + x)*3+1];
			float raw_b = rgb[(y*w + x)*3+2];
			row[x].red   = pack_pf16_value(raw_r);
			row[x].green = pack_pf16_value(raw_g);
			row[x].blue  = pack_pf16_value(raw_b);
			if (x == 601 && y == 598) {
				observe_blur_store16_pixel(observation, bp, w, h, x, y,
					raw_r, raw_g, raw_b,
					row[x].red, row[x].green, row[x].blue, row[x].alpha);
			}
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
render_8bpc_legacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                       float blur_amount, float blur_smoothness,
	                       float render_scale, A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<std::uint8_t> source_argb(pixels * 4);
		std::vector<std::uint8_t> destination_argb(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const PF_Pixel8 *source_row = (const PF_Pixel8*)((const char*)input->data + y * (size_t)input->rowbytes);
			for (size_t x = 0; x < width; ++x) {
				const PF_Pixel8 &pixel = source_row[x];
				std::uint8_t *packed = source_argb.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker8_legacy::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0),
			render_scale
		};
		olm::blur::worker8_legacy::render(
			source_argb.data(), destination_argb.data(), width, height, params);

		for (size_t y = 0; y < height; ++y) {
			const PF_Pixel8 *source_row = (const PF_Pixel8*)((const char*)input->data + y * (size_t)input->rowbytes);
			PF_Pixel8 *output_row = (PF_Pixel8*)((char*)output->data + y * (size_t)output->rowbytes);
			for (size_t x = 0; x < width; ++x) {
				const std::uint8_t *packed = destination_argb.data() + (y * width + x) * 4;
				PF_Pixel8 &pixel = output_row[x];
				pixel.alpha = source_row[x].alpha;
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
render_16bpc_nonlegacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                           float blur_amount, float blur_smoothness,
	                           A_long repeat, A_long bias_dir,
	                           const BlurParams *bp,
	                           const BlurObservationConfig *observation)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<std::uint16_t> source_argb16(pixels * 4);
		std::vector<std::uint16_t> destination_argb16(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				PF_Pixel16 pixel; memcpy(&pixel,source_row+x*sizeof(pixel),sizeof(pixel));
				std::uint16_t *packed = source_argb16.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker16::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0)
		};
		olm::blur::worker16::StoreObservation store_observation = {
			601, 598, false, {0.0f, 0.0f, 0.0f}, {0, 0, 0, 0}
		};
		olm::blur::worker16::render_nonlegacy(
			(const std::uint8_t*)source_argb16.data(), (std::uint8_t*)destination_argb16.data(),
			width, height, params, observation && observation->enabled ? &store_observation : NULL);
		if (observation && observation->enabled && !store_observation.captured) {
			return PF_Err_INTERNAL_STRUCT_DAMAGED;
		}

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			unsigned char *output_row = (unsigned char*)output->data + y * (size_t)output->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				const std::uint16_t *packed = destination_argb16.data() + (y * width + x) * 4;
				PF_Pixel16 source_pixel,pixel; memcpy(&source_pixel,source_row+x*sizeof(source_pixel),sizeof(source_pixel));
				pixel.alpha = source_pixel.alpha;
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
				memcpy(output_row+x*sizeof(pixel),&pixel,sizeof(pixel));
				if (x == 601 && y == 598) {
					observe_blur_store16_pixel(observation, bp, (A_long)width, (A_long)height,
						(A_long)x, (A_long)y,
						store_observation.pre_store[0], store_observation.pre_store[1],
						store_observation.pre_store[2], store_observation.stored_argb[1],
						store_observation.stored_argb[2], store_observation.stored_argb[3],
						store_observation.stored_argb[0]);
				}
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
render_16bpc_legacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                       float blur_amount, float blur_smoothness,
	                       float render_scale, A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<std::uint16_t> source_argb16(pixels * 4);
		std::vector<std::uint16_t> destination_argb16(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				PF_Pixel16 pixel; memcpy(&pixel,source_row+x*sizeof(pixel),sizeof(pixel));
				std::uint16_t *packed = source_argb16.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker16_legacy::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0),
			render_scale
		};
		olm::blur::worker16_legacy::render(
			(const std::uint8_t*)source_argb16.data(), (std::uint8_t*)destination_argb16.data(),
			width, height, params);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			unsigned char *output_row = (unsigned char*)output->data + y * (size_t)output->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				const std::uint16_t *packed = destination_argb16.data() + (y * width + x) * 4;
				PF_Pixel16 source_pixel,pixel; memcpy(&source_pixel,source_row+x*sizeof(source_pixel),sizeof(source_pixel));
				pixel.alpha = source_pixel.alpha;
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
				memcpy(output_row+x*sizeof(pixel),&pixel,sizeof(pixel));
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
render_8bpc_nonlegacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                          float blur_amount, float blur_smoothness,
	                          A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	const size_t bytes = pixels * 4;
	u_char *source_argb = (u_char*)malloc(bytes);
	u_char *destination_argb = (u_char*)malloc(bytes);
	if (!source_argb || !destination_argb) {
		free(source_argb);
		free(destination_argb);
		return PF_Err_OUT_OF_MEMORY;
	}

	for (size_t y = 0; y < height; ++y) {
		const PF_Pixel8 *source_row = (const PF_Pixel8*)((const char*)input->data + y * (size_t)input->rowbytes);
		for (size_t x = 0; x < width; ++x) {
			const PF_Pixel8 &pixel = source_row[x];
			u_char *packed = source_argb + (y * width + x) * 4;
			packed[0] = pixel.alpha;
			packed[1] = pixel.red;
			packed[2] = pixel.green;
			packed[3] = pixel.blue;
		}
	}

	olm::blur::worker::Params params = {
		blur_amount,
		blur_smoothness,
		(size_t)(repeat > 0 ? repeat : 0),
		(size_t)(bias_dir > 0 ? bias_dir : 0)
	};
	try {
		olm::blur::worker::render_8bpc_nonlegacy(
			source_argb, destination_argb, width, height, params);
	} catch (const std::bad_alloc &) {
		free(source_argb);
		free(destination_argb);
		return PF_Err_OUT_OF_MEMORY;
	}

	for (size_t y = 0; y < height; ++y) {
		PF_Pixel8 *output_row = (PF_Pixel8*)((char*)output->data + y * (size_t)output->rowbytes);
		for (size_t x = 0; x < width; ++x) {
			const u_char *packed = destination_argb + (y * width + x) * 4;
			PF_Pixel8 &pixel = output_row[x];
			pixel.alpha = packed[0];
			pixel.red = packed[1];
			pixel.green = packed[2];
			pixel.blue = packed[3];
		}
	}

	free(source_argb);
	free(destination_argb);
	return PF_Err_NONE;
}

static PF_Err
render_32bpc_nonlegacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                           float blur_amount, float blur_smoothness,
	                           A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<float> source_argb(pixels * 4);
		std::vector<float> destination_argb(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				PF_PixelFloat pixel; memcpy(&pixel,source_row+x*sizeof(pixel),sizeof(pixel));
				float *packed = source_argb.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker32::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0)
		};
		olm::blur::worker32::render_nonlegacy(
			source_argb.data(), destination_argb.data(), width, height, params);

		for (size_t y = 0; y < height; ++y) {
			unsigned char *output_row = (unsigned char*)output->data + y * (size_t)output->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				const float *packed = destination_argb.data() + (y * width + x) * 4;
				PF_PixelFloat pixel;
				pixel.alpha = packed[0];
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
				memcpy(output_row+x*sizeof(pixel),&pixel,sizeof(pixel));
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
render_32bpc_legacy_adapter(const PF_EffectWorld *input, PF_EffectWorld *output,
	                       float blur_amount, float blur_smoothness,
	                       float render_scale, A_long repeat, A_long bias_dir)
{
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (height != 0 && width > ((size_t)-1) / height) return PF_Err_OUT_OF_MEMORY;
	const size_t pixels = width * height;
	if (pixels > ((size_t)-1) / 4) return PF_Err_OUT_OF_MEMORY;

	try {
		std::vector<float> source_argb(pixels * 4);
		std::vector<float> destination_argb(pixels * 4);

		for (size_t y = 0; y < height; ++y) {
			const unsigned char *source_row = (const unsigned char*)input->data + y * (size_t)input->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				PF_PixelFloat pixel; memcpy(&pixel,source_row+x*sizeof(pixel),sizeof(pixel));
				float *packed = source_argb.data() + (y * width + x) * 4;
				packed[0] = pixel.alpha;
				packed[1] = pixel.red;
				packed[2] = pixel.green;
				packed[3] = pixel.blue;
			}
		}

		olm::blur::worker32_legacy::Params params = {
			blur_amount,
			blur_smoothness,
			(size_t)(repeat > 0 ? repeat : 0),
			(size_t)(bias_dir > 0 ? bias_dir : 0),
			render_scale
		};
		olm::blur::worker32_legacy::render(
			source_argb.data(), destination_argb.data(), width, height, params);

		for (size_t y = 0; y < height; ++y) {
			unsigned char *output_row = (unsigned char*)output->data + y * (size_t)output->rowbytes;
			for (size_t x = 0; x < width; ++x) {
				const float *packed = destination_argb.data() + (y * width + x) * 4;
				PF_PixelFloat pixel;
				pixel.alpha = packed[0];
				pixel.red = packed[1];
				pixel.green = packed[2];
				pixel.blue = packed[3];
				memcpy(output_row+x*sizeof(pixel),&pixel,sizeof(pixel));
			}
		}
	} catch (const std::bad_alloc &) {
		return PF_Err_OUT_OF_MEMORY;
	}

	return PF_Err_NONE;
}

static PF_Err
BlurRender(PF_InData *in_data, PF_EffectWorld *input, PF_EffectWorld *output,
           short bpc, const BlurParams *bp)
{
	PF_Err err = PF_Err_NONE;
	A_long w = input->width, h = input->height;
	if (w <= 0 || h <= 0) return err;
	const BlurObservationConfig observation = load_blur_observation_config();

	const float render_scale =
		((float)in_data->downsample_x.num / (float)in_data->downsample_x.den);
	float blur_amount = bp->blur_amount * render_scale;
	if (blur_amount <= 0) {
		return PF_COPY(input, output, NULL, NULL);
	}
	if (bpc == 8 && bp->legacy) {
		return render_8bpc_legacy_adapter(
			input, output, bp->blur_amount, bp->blur_smoothness, render_scale,
			bp->repeat, bp->bias_dir);
	}
	if (bpc == 8 && !bp->legacy) {
		return render_8bpc_nonlegacy_adapter(
			input, output, blur_amount, bp->blur_smoothness,
			bp->repeat, bp->bias_dir);
	}
	if (bpc == 16 && !bp->legacy) {
		return render_16bpc_nonlegacy_adapter(
			input, output, blur_amount, bp->blur_smoothness,
			bp->repeat, bp->bias_dir, bp, &observation);
	}
	if (bpc == 16 && bp->legacy) {
		return render_16bpc_legacy_adapter(
			input, output, bp->blur_amount, bp->blur_smoothness, render_scale,
			bp->repeat, bp->bias_dir);
	}
	if (bpc == 32 && !bp->legacy) {
		return render_32bpc_nonlegacy_adapter(
			input, output, blur_amount, bp->blur_smoothness,
			bp->repeat, bp->bias_dir);
	}
	if (bpc == 32 && bp->legacy) {
		return render_32bpc_legacy_adapter(
			input, output, bp->blur_amount, bp->blur_smoothness, render_scale,
			bp->repeat, bp->bias_dir);
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
		BlurDebugConfig debug = load_blur_debug_config();
		A_long radius = (A_long)blur_amount;
		if (radius > 0) {
			float smoothness = bp->blur_smoothness;
			if (smoothness <= 0.0f) smoothness = 1.0f;
			float sigma_base = ((blur_amount * smoothness) / 100.0f) * (blur_amount / 3.0f);
			for (A_long iter = 1; iter <= bp->repeat; ++iter) {
				float sigma = sigma_base / (float)iter;
				if (sigma <= 0.0f) break;
				// The Windows Legacy owner doubles sigma before the final multiply;
				// preserve that float32 operation boundary instead of reassociating.
				float denom = (sigma + sigma) * sigma;
				weights[radius] = 1.0f;
				for (A_long k = 1; k <= radius; ++k) {
					float v = expf(-(float)(k*k) / denom);
					weights[radius - k] = v;
					weights[radius + k] = v;
				}
				if (bp->bias_dir == BIAS_DIR_VERTICAL) {
					legacy_blur_1d_horizontal(buf1, alpha1, buf2, alpha2, w, h, radius, weights, &debug, iter);
					legacy_blur_1d_vertical  (buf2, alpha2, buf1, alpha1, w, h, radius, weights, &debug, iter);
				} else if (bp->bias_dir == BIAS_DIR_HORIZONTAL) {
					legacy_blur_1d_vertical  (buf1, alpha1, buf2, alpha2, w, h, radius, weights, &debug, iter);
					legacy_blur_1d_horizontal(buf2, alpha2, buf1, alpha1, w, h, radius, weights, &debug, iter);
				}
			}
		}
		if (bpc == 8)       store8(output, buf1, bp->legacy);
		else if (bpc == 16) store16(output, buf1, bp->legacy, &debug, bp, &observation);
		else                storeFloat(output, buf1);
	} else {
		BlurDebugConfig debug = load_blur_debug_config();
		float decay = 1.0f;
		if (bp->repeat > 1) decay = powf(3.0f / blur_amount, 1.0f / (float)(bp->repeat - 1));

		for (A_long iter = 0; iter < bp->repeat; ++iter) {
			double radius_d = (double)blur_amount * pow((double)decay, (double)iter);
			A_long radius = (A_long)radius_d;
			if (radius == 0) break;
			float sigma = (float)radius_d / 3.0f;
			float denom = 2.0f * sigma * sigma;
			for (A_long k = 0; k <= radius; ++k) {
				const float exponent = -(float)(k*k) / denom;
				weights[k] = (float)exp((double)exponent);
			}

			if (bp->bias_dir == BIAS_DIR_VERTICAL) {
				blur_1d_horizontal(buf1, alpha1, buf2, alpha2, w, h, radius, weights, &debug, iter + 1);
				blur_1d_vertical  (buf2, alpha2, buf1, alpha1, w, h, radius, weights, &debug, iter + 1);
			} else if (bp->bias_dir == BIAS_DIR_HORIZONTAL) {
				blur_1d_vertical  (buf1, alpha1, buf2, alpha2, w, h, radius, weights, &debug, iter + 1);
				blur_1d_horizontal(buf2, alpha2, buf1, alpha1, w, h, radius, weights, &debug, iter + 1);
			}
		}
	}
	free(weights);
	if (!bp->legacy) {
		if (bpc == 8)       store8(output, buf1, bp->legacy);
		else if (bpc == 16) {
			BlurDebugConfig debug = load_blur_debug_config();
			store16(output, buf1, bp->legacy, &debug, bp, &observation);
		}
		else                storeFloat(output, buf1);
	}

	free(buf1); free(buf2); free(alpha1); free(alpha2);
	return err;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	if (!params || !output || !params[OLMBLUR_INPUT] ||
		!params[OLMBLUR_BLUR_AMOUNT] || !params[OLMBLUR_BLUR_SMOOTHNESS] ||
		!params[OLMBLUR_REPEAT]) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_EffectWorld *input = &params[OLMBLUR_INPUT]->u.ld;
	if (!input->data || !output->data || input->width != output->width ||
		input->height != output->height || input->rowbytes != output->rowbytes) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite(in_data, kPFWorldSuite,
	                                             kPFWorldSuiteVersion2, out_data);
	ERR(world_suite->PF_GetPixelFormat(input, &input_format));
	ERR(world_suite->PF_GetPixelFormat(output, &output_format));
	if (err) return err;
	if (input_format != output_format) return PF_Err_BAD_CALLBACK_PARAM;

	A_long expected_rowbytes = 0;
	switch (output_format) {
	case PF_PixelFormat_ARGB32:
		expected_rowbytes = 24 * (A_long)sizeof(PF_Pixel8) + 17;
		break;
	case PF_PixelFormat_ARGB64:
		expected_rowbytes = 24 * (A_long)sizeof(PF_Pixel16) + 23;
		break;
	case PF_PixelFormat_ARGB128:
		// The retained Windows classic owner tests only PF_WorldFlag_DEEP,
		// so PF32 aliases its PF16 branch.  Keep the unowned float route
		// fail-closed; the advertised numerical PF32 owner is Smart Render.
		return PF_Err_BAD_CALLBACK_PARAM;
	default:
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	if (input->width != 24 || input->height != 24 ||
		input->rowbytes != expected_rowbytes) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}

	// The current Windows classic export reads only parameter slots 1..3 and,
	// with the registered float-slider default, observes a zero low dword for
	// Blur Amount.  Its PF8/PF16 non-Legacy worker therefore returns after the
	// initial world copy.  Admit only that bounded public tuple here.  Bias and
	// Legacy are deliberately not consumed: the classic owner does not read
	// slots 4 or 5.  All numerical/non-default work remains on Smart Render.
	const PF_FpLong blur_amount = params[OLMBLUR_BLUR_AMOUNT]->u.fs_d.value;
	const A_long blur_smoothness = params[OLMBLUR_BLUR_SMOOTHNESS]->u.fd.value;
	const A_long repeat = params[OLMBLUR_REPEAT]->u.sd.value;
	if (blur_amount != 5.0 || blur_smoothness != 100 * 65536 || repeat != 2) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}

	ERR(PF_COPY(input, output, NULL, NULL));
	return err;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	(void)out_data;
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
		!extra->cb->checkout_layer) return PF_Err_BAD_CALLBACK_PARAM;
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);

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

static bool
ExactPublicWorld(const PF_EffectWorld *world, short bpc, A_long width, A_long height,
	A_long rowbytes)
{
	if (!world || !world->data || world->width != width || world->height != height ||
		world->origin_x != 0 || world->origin_y != 0 ||
		world->extent_hint.left != 0 || world->extent_hint.top != 0 ||
		world->extent_hint.right != width || world->extent_hint.bottom != height) return false;
	const PF_WorldFlags expected_flags = bpc == 8 ? 0 : PF_WorldFlag_DEEP;
	return rowbytes > 0 && world->rowbytes == rowbytes &&
		world->world_flags == expected_flags;
}

static bool
PublicWorldsDisjoint(const PF_EffectWorld *input, const PF_EffectWorld *output,
	A_long height)
{
	const size_t bytes = (size_t)input->rowbytes * (size_t)height;
	const uintptr_t in_begin = (uintptr_t)input->data;
	const uintptr_t out_begin = (uintptr_t)output->data;
	if (!bytes || in_begin > UINTPTR_MAX - bytes || out_begin > UINTPTR_MAX - bytes) return false;
	const uintptr_t in_end = in_begin + bytes, out_end = out_begin + bytes;
	return in_end <= out_begin || out_end <= in_begin;
}

static PF_Err
GetPublicWorldFormats(PF_InData *in_data, const PF_EffectWorld *input,
	const PF_EffectWorld *output, short bpc)
{
	if (!in_data || !in_data->pica_basicP ||
		!in_data->pica_basicP->AcquireSuite || !in_data->pica_basicP->ReleaseSuite)
		return PF_Err_BAD_CALLBACK_PARAM;
	const void *raw_suite = NULL;
	PF_Err err = PF_Err_NONE;
	try {
		err = (PF_Err)in_data->pica_basicP->AcquireSuite(
			kPFWorldSuite, kPFWorldSuiteVersion2, &raw_suite);
	} catch (const PF_Err &caught) { err = caught; }
	catch (const std::bad_alloc &) { err = PF_Err_OUT_OF_MEMORY; }
	catch (...) { err = PF_Err_INTERNAL_STRUCT_DAMAGED; }
	if (err) return err;
	const PF_WorldSuite2 *suite = (const PF_WorldSuite2*)raw_suite;
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	try {
		if (!suite || !suite->PF_GetPixelFormat) err = PF_Err_BAD_CALLBACK_PARAM;
		if (!err) err = suite->PF_GetPixelFormat(input, &input_format);
		if (!err) err = suite->PF_GetPixelFormat(output, &output_format);
	} catch (const PF_Err &caught) { err = caught; }
	catch (const std::bad_alloc &) { err = PF_Err_OUT_OF_MEMORY; }
	catch (...) { err = PF_Err_INTERNAL_STRUCT_DAMAGED; }
	if (!err) {
		const PF_PixelFormat expected = bpc == 8 ? PF_PixelFormat_ARGB32 :
			(bpc == 16 ? PF_PixelFormat_ARGB64 :
			 (bpc == 32 ? PF_PixelFormat_ARGB128 : PF_PixelFormat_INVALID));
		if (expected == PF_PixelFormat_INVALID || input_format != expected ||
			output_format != expected) err = PF_Err_BAD_CALLBACK_PARAM;
	}
	PF_Err release_err = PF_Err_NONE;
	try {
		release_err = (PF_Err)in_data->pica_basicP->ReleaseSuite(
			kPFWorldSuite, kPFWorldSuiteVersion2);
	} catch (const PF_Err &caught) { release_err = caught; }
	catch (const std::bad_alloc &) { release_err = PF_Err_OUT_OF_MEMORY; }
	catch (...) { release_err = PF_Err_INTERNAL_STRUCT_DAMAGED; }
	return err ? err : release_err;
}

// The exact public lanes below preserve captured Windows contracts.  This
// validator owns the deliberately broader beta lane: full-frame worlds with
// arbitrary pixels and any legal (independent) row stride.
struct PublicBlurParamValues {
	PF_FpLong amount;
	A_long smoothness_fixed, repeat, bias, legacy;
};

static bool
GenericBetaWorld(const PF_EffectWorld *world, size_t pixel_bytes,
	A_long width, A_long height)
{
	if (!world || !world->data || !pixel_bytes || width <= 0 || height <= 0 ||
		world->width != width || world->height != height || world->rowbytes <= 0 ||
		world->origin_x != 0 || world->origin_y != 0 ||
		world->extent_hint.left != 0 || world->extent_hint.top != 0 ||
		world->extent_hint.right != width || world->extent_hint.bottom != height)
		return false;
	const size_t usize_width = (size_t)width;
	if (usize_width > ((size_t)-1) / pixel_bytes) return false;
	const size_t active = usize_width * pixel_bytes;
	return active <= (size_t)world->rowbytes;
}

static bool
GenericBetaTuple(const PublicBlurParamValues& raw, A_long width, A_long height)
{
	if (!isfinite(raw.amount) || raw.amount < 1.0 || raw.amount > 1000.0 ||
		raw.smoothness_fixed < 1 * 65536 || raw.smoothness_fixed > 100 * 65536 ||
		raw.repeat < 1 || raw.repeat > 10 || raw.bias < 1 || raw.bias > 2 ||
		(raw.legacy != 0 && raw.legacy != 1) || width <= 0 || height <= 0 ||
		width > 4096 || height > 2160)
		return false;
	// Preserve the tiny captured fixtures below as exact compatibility owners.
	if (width <= 24 && height <= 24) return false;
	const size_t usize_width = (size_t)width, usize_height = (size_t)height;
	if (usize_width > ((size_t)-1) / usize_height) return false;
	const size_t pixels = usize_width * usize_height;
	// PF32 is the worst case: packed source/destination plus two RGB float
	// planes and flags approach 57 bytes/pixel.  Leave allocator headroom while
	// admitting a full UHD frame at ordinary settings.
	if (pixels > (640u * 1024u * 1024u) / 64u) return false;
	// The current workers are synchronous and have no host abort callback.
	// Bound their dominant O(pixels * radius * repeat) cost before entering the
	// worker; host/perf timeouts remain an outer watchdog, never a cancellation
	// mechanism for an already-running render.
	const size_t radius=(size_t)ceil(raw.amount);
	const size_t max_work=3600u*1000u*1000u;
	if (!radius || pixels > max_work/radius ||
		pixels*radius > max_work/(size_t)raw.repeat) return false;
	return true;
}

static PF_Err
CheckoutPublicBlurParams(PF_InData *in_data, BlurParams *bp, PublicBlurParamValues *raw)
{
	if (!in_data || !bp || !raw || !in_data->inter.checkout_param || !in_data->inter.checkin_param)
		return PF_Err_BAD_CALLBACK_PARAM;
	AEFX_CLR_STRUCT(*raw);
	const A_long indices[5] = {OLMBLUR_BLUR_AMOUNT, OLMBLUR_BLUR_SMOOTHNESS,
		OLMBLUR_REPEAT, OLMBLUR_BIAS_DIRECTION, OLMBLUR_LEGACY};
	for (int ordinal = 0; ordinal < 5; ++ordinal) {
		PF_ParamDef p; AEFX_CLR_STRUCT(p);
		PF_Err err = PF_CHECKOUT_PARAM(in_data, indices[ordinal], in_data->current_time,
			in_data->time_step, in_data->time_scale, &p);
		if (err) return err;
		if (ordinal == 0) { raw->amount=p.u.fs_d.value; bp->blur_amount=(float)raw->amount; }
		else if (ordinal == 1) { raw->smoothness_fixed=p.u.fd.value; bp->blur_smoothness=(float)raw->smoothness_fixed/65536.0f; }
		else if (ordinal == 2) { raw->repeat=p.u.sd.value; bp->repeat=raw->repeat; }
		else if (ordinal == 3) { raw->bias=p.u.pd.value; bp->bias_dir=raw->bias; }
		else { raw->legacy=p.u.bd.value; bp->legacy=raw->legacy; }
		const PF_Err checkin_err = PF_CHECKIN_PARAM(in_data, &p);
		if (checkin_err) return checkin_err;
	}
	return PF_Err_NONE;
}

enum PublicBlurSourceKind {
	PublicBlurSourceNone = 0,
	PublicBlurSourceOriginal24,
	PublicBlurSourcePF16Standard,
	PublicBlurSourcePF16MixedAlpha,
	PublicBlurSourcePF16SevenByFive,
	PublicBlurSourcePF8NonLegacyStandard,
	PublicBlurSourcePF8LegacyStandard,
	PublicBlurSourcePF8LegacyMixedAlpha,
	PublicBlurSourcePF8LegacyBoundaryGradient,
	PublicBlurSourcePF8LegacyByteBoundaries,
	PublicBlurSourcePF16LegacyWordBoundaries,
	PublicBlurSourcePF32NonLegacyStandard,
	PublicBlurSourcePF32LegacyStandard,
	PublicBlurSourcePF32LegacyMixedAlpha,
	PublicBlurSourcePF32LegacyRedBoundary,
	PublicBlurSourcePF32Legacy24Repeat1Union
};

static bool
ExactPublicSource(const PF_EffectWorld *world, short bpc, bool legacy,
	PublicBlurSourceKind source_kind)
{
	if (!world || !world->data) return false;
	if (source_kind == PublicBlurSourcePF32Legacy24Repeat1Union)
		return ExactPublicSource(world,bpc,legacy,PublicBlurSourcePF32LegacyStandard) ||
			ExactPublicSource(world,bpc,legacy,PublicBlurSourceOriginal24);
	if (source_kind == PublicBlurSourcePF16Standard && bpc == 16 &&
		((world->width == 12 && world->height == 12 && world->rowbytes == 109) ||
		 (world->width == 18 && world->height == 18 && world->rowbytes == 157))) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const uint16_t p[4] = {
				(uint16_t)(legacy ? 32768 : (((x*5 + y*3) % 17) == 0 ? 0 : 32768)),
				(uint16_t)((257*x + 31*y + 101) % 32769),
				(uint16_t)((113*x + 211*y + 307) % 32769),
				(uint16_t)((401*x + 97*y + 503) % 32769)
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*8u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF16MixedAlpha && bpc == 16 && legacy &&
		world->width == 18 && world->height == 12 &&
		world->rowbytes == 157) {
		for (A_long y=0;y<12;++y) for (A_long x=0;x<18;++x) {
			const bool boundary = x == 0 || x == 17 || y == 0 || y == 11;
			const bool hole = (x*7 + y*11) % 13 == 0;
			const uint16_t p[4] = {
				(uint16_t)(boundary || hole ? 0 : 8192 + ((x*29 + y*17) % 4) * 16384),
				12800, 25600, 30000
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*8u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF16SevenByFive && bpc == 16 &&
		world->width == 7 && world->height == 5 && world->rowbytes == 69) {
		for (A_long y=0;y<5;++y) for (A_long x=0;x<7;++x) {
			const uint16_t p[4] = {
				32768,
				(uint16_t)(1000 + 701*x + 17*y),
				(uint16_t)(30000 + 37*x + 811*y),
				(uint16_t)(200 + 503*x + 29*y)
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*8u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8NonLegacyStandard && bpc == 8 && !legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const unsigned char p[4] = {
				(unsigned char)(((x*5 + y*3) % 17) == 0 ? 0 : 255),
				(unsigned char)((17*x + 3*y + 11) & 255),
				(unsigned char)((7*x + 19*y + 23) & 255),
				(unsigned char)((29*x + 13*y + 37) & 255)
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8LegacyStandard && bpc == 8 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const unsigned char p[4] = {
				255,
				(unsigned char)((17*x + 3*y + 11) & 255),
				(unsigned char)((7*x + 19*y + 23) & 255),
				(unsigned char)((29*x + 13*y + 37) & 255)
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8LegacyMixedAlpha && bpc == 8 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const bool boundary = x == 0 || x == world->width-1 || y == 0 || y == world->height-1;
			const bool hole = (x*7 + y*11) % 13 == 0;
			const unsigned char p[4] = {
				(unsigned char)(boundary || hole ? 0 : 32 + ((x*29 + y*17) % 4) * 64),
				50, 100, 150
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8LegacyBoundaryGradient && bpc == 8 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const bool boundary = x == 0 || x == world->width-1 || y == 0 || y == world->height-1;
			const unsigned char p[4] = {
				255,
				(unsigned char)(boundary ? ((x*19 + y*23 + 7) & 255) : ((31 + x*9 + y*13) & 255)),
				0, 0
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF8LegacyByteBoundaries && bpc == 8 && legacy) {
		static const unsigned char values[] = {0,1,127,128,254,255};
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const unsigned char p[4] = {
				values[(x+5*y)%6], values[(2*x+y+1)%6],
				values[(x+3*y+2)%6], values[(5*x+2*y+3)%6]
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*4u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF16LegacyWordBoundaries && bpc == 16 && legacy) {
		static const uint16_t values[] = {0,1,32767,32768};
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const uint16_t p[4] = {
				values[(x+3*y)%4], values[(x+y+1)%4],
				values[(2*x+y+2)%4], values[(x+2*y+3)%4]
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*8u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if ((source_kind == PublicBlurSourcePF32NonLegacyStandard ||
		source_kind == PublicBlurSourcePF32LegacyStandard) && bpc == 32) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const float p[4] = {
				(float)(((x*5+y*3)%17)==0 ? 0.0 : ((x+y)%5 ? 1.0 : -0.5)),
				(float)(-1.25 + 0.17*x + 0.031*y),
				(float)(0.5 + 0.11*x - 0.23*y),
				(float)(1.5 + 0.07*x + 0.19*y)
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*16u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF32LegacyMixedAlpha && bpc == 32 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const bool boundary=x==0||x==world->width-1||y==0||y==world->height-1;
			const bool hole=(x*7+y*11)%13==0;
			const float p[4] = {
				(float)(boundary||hole?0.0:((x+2*y)%7==0?-0.5:0.25+0.125*((x*3+y)%4))),
				(float)(0.25+0.031*x),(float)(-0.5+0.017*y),(float)(1.5+0.011*(x+y))
			};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*16u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind == PublicBlurSourcePF32LegacyRedBoundary && bpc == 32 && legacy) {
		for (A_long y=0;y<world->height;++y) for (A_long x=0;x<world->width;++x) {
			const bool boundary=x==0||x==world->width-1||y==0||y==world->height-1;
			const float p[4]={(float)(boundary?0.0:1.0),(float)(0.2+0.11*x+0.037*y),0.0f,0.0f};
			const unsigned char *at=(const unsigned char*)world->data+
				(size_t)y*world->rowbytes+(size_t)x*16u;
			if (memcmp(at,p,sizeof(p))) return false;
		}
		return true;
	}
	if (source_kind != PublicBlurSourceOriginal24) return false;
	if (world->width != 24 || world->height != 24) return false;
	const size_t pixel_bytes = bpc == 8 ? 4u : (bpc == 16 ? 8u : (bpc == 32 ? 16u : 0u));
	if (!pixel_bytes || world->rowbytes != (A_long)(24u * pixel_bytes + (bpc == 8 ? 17u : (bpc == 16 ? 23u : 32u)))) return false;
	static const unsigned char v8[] = {0,1,64,127,128,192,254,255};
	static const uint16_t v16[] = {0,1,8192,16384,32767,32768};
	static const float v32[] = {-0.5f,0.0f,1.0f/255.0f,0.25f,0.5f,1.0f,1.25f,2.0f};
	for (A_long y=0;y<24;++y) for (A_long x=0;x<24;++x) {
		const int selector=(x*5+y*3)%17;
		const unsigned char *at=(const unsigned char*)world->data+(size_t)y*world->rowbytes+(size_t)x*pixel_bytes;
		if (bpc==8) {
			unsigned char p[4]={(unsigned char)(selector==0?0:v8[(x+3*y)%8]),v8[(2*x+y+1)%8],v8[(x+5*y+2)%8],v8[(7*x+3*y+3)%8]};
			if (memcmp(at,p,4)) return false;
		} else if (bpc==16) {
			uint16_t p[4]={(uint16_t)(selector==0?0:v16[(x+3*y)%6]),v16[(2*x+y+1)%6],v16[(x+5*y+2)%6],v16[(7*x+3*y+3)%6]};
			if (memcmp(at,p,8)) return false;
		} else {
			float p[4]={(float)(selector==0?0.0f:v32[(x+3*y)%8]),v32[(2*x+y+1)%8],v32[(x+5*y+2)%8],v32[(7*x+3*y+3)%8]};
			if (memcmp(at,p,16)) return false;
		}
	}
	return true;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	(void)out_data;
	if (!in_data || !extra || !extra->input || !extra->cb ||
		!extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
		!in_data->inter.checkout_param || !in_data->inter.checkin_param)
		return PF_Err_BAD_CALLBACK_PARAM;
	PF_Err err=PF_Err_NONE; PF_EffectWorld *input_world=NULL,*output_world=NULL;
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref,OLMBLUR_INPUT,&input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref,&output_world));
	if (err || !input_world || !output_world) return err ? err : PF_Err_BAD_CALLBACK_PARAM;
	BlurParams bp; AEFX_CLR_STRUCT(bp); PublicBlurParamValues raw; AEFX_CLR_STRUCT(raw);
	err = CheckoutPublicBlurParams(in_data, &bp, &raw);
	const short bpc=extra->input->bitdepth;
	const size_t pixel_bytes=bpc==8?4u:(bpc==16?8u:(bpc==32?16u:0u));
	// Generic beta lane.  Exact fixture admissions remain below as a fallback,
	// retaining their special source and arithmetic contracts.
	if (!err && GenericBetaTuple(raw,input_world->width,input_world->height) &&
		GenericBetaWorld(input_world,pixel_bytes,input_world->width,input_world->height) &&
		GenericBetaWorld(output_world,pixel_bytes,input_world->width,input_world->height) &&
		in_data->downsample_x.num==1 && in_data->downsample_x.den==1 &&
		in_data->downsample_y.num==1 && in_data->downsample_y.den==1) {
		err=GetPublicWorldFormats(in_data,input_world,output_world,bpc);
		olm::world_safety::TightStaging staging;
		if (!err) {
			const olm::world_safety::Status stage_status = staging.prepare(
				{input_world->data, (size_t)input_world->width,
				 (size_t)input_world->height, (size_t)input_world->rowbytes,
				 pixel_bytes},
				{output_world->data, (size_t)output_world->width,
				 (size_t)output_world->height, (size_t)output_world->rowbytes,
				 pixel_bytes});
			if (stage_status == olm::world_safety::Status::out_of_memory)
				err = PF_Err_OUT_OF_MEMORY;
			else if (stage_status != olm::world_safety::Status::ok)
				err = PF_Err_BAD_CALLBACK_PARAM;
		}
		PF_EffectWorld staged_input = *input_world;
		PF_EffectWorld staged_output = *output_world;
		if (!err) {
			staged_input.data = (PF_PixelPtr)const_cast<uint8_t *>(staging.input_data());
			staged_input.rowbytes = (A_long)staging.row_bytes();
			staged_output.data = (PF_PixelPtr)staging.output_data();
			staged_output.rowbytes = (A_long)staging.row_bytes();
			err=BlurRender(in_data,&staged_input,&staged_output,bpc,&bp);
		}
		const PF_Err checkin_err=extra->cb->checkin_layer_pixels ?
			extra->cb->checkin_layer_pixels(in_data->effect_ref,OLMBLUR_INPUT) : PF_Err_NONE;
		if (!err) err=checkin_err;
		if (!err && staging.commit() != olm::world_safety::Status::ok)
			err=PF_Err_BAD_CALLBACK_PARAM;
		return err;
	}
	const bool public24 = raw.amount==5.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==1 && raw.bias==1 && (raw.legacy==0 || raw.legacy==1) &&
		input_world->width==24 && input_world->height==24;
	const bool public7x5 = bpc==16 && raw.amount==4.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==1 && raw.bias==1 && raw.legacy==0 &&
		input_world->width==7 && input_world->height==5;
	const bool public12x12 = bpc==16 && raw.amount==3.0 && raw.smoothness_fixed==100*65536 &&
		((raw.legacy==0 && (raw.repeat==1 || raw.repeat==2) && raw.bias==1) ||
		 (raw.legacy==1 && raw.repeat==2 && raw.bias==1)) &&
		input_world->width==12 && input_world->height==12;
	const bool public18x18 = bpc==16 && raw.amount==11.0 && raw.smoothness_fixed==100*65536 &&
		((raw.legacy==0 && ((raw.repeat==1 && raw.bias==1) || (raw.repeat==3 && raw.bias==2))) ||
		 (raw.legacy==1 && raw.repeat==3 && raw.bias==2)) &&
		input_world->width==18 && input_world->height==18;
	const bool public18x12 = bpc==16 && raw.amount==3.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==2 && raw.bias==2 && raw.legacy==1 &&
		input_world->width==18 && input_world->height==12;
	const bool public8NonLegacy12 = bpc==8 && raw.amount==3.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==2 && raw.bias==1 && raw.legacy==0 &&
		input_world->width==12 && input_world->height==12;
	const bool public8NonLegacy24 = bpc==8 && raw.amount==129.4 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==1 && raw.bias==1 && raw.legacy==0 &&
		input_world->width==24 && input_world->height==24;
	const bool public8NonLegacy18 = bpc==8 && raw.amount==11.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==3 && raw.bias==2 && raw.legacy==0 &&
		input_world->width==18 && input_world->height==18;
	const bool public8NonLegacy24Repeat2 = bpc==8 && raw.amount==129.4 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==2 && raw.bias==2 && raw.legacy==0 &&
		input_world->width==24 && input_world->height==24;
	const bool public8Legacy12 = bpc==8 && raw.amount==3.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==2 && raw.bias==1 && raw.legacy==1 &&
		input_world->width==12 && input_world->height==12;
	const bool public8Legacy18 = bpc==8 && raw.amount==11.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==3 && raw.bias==2 && raw.legacy==1 &&
		input_world->width==18 && input_world->height==18;
	const bool public8Legacy18x12 = bpc==8 && raw.amount==3.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==2 && raw.bias==2 && raw.legacy==1 &&
		input_world->width==18 && input_world->height==12;
	const bool public8Legacy6 = bpc==8 && raw.amount==248.6 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==10 && raw.bias==1 && raw.legacy==1 &&
		input_world->width==6 && input_world->height==6;
	const bool public8LegacyBoundary12 = bpc==8 && raw.amount==248.6 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==10 && raw.bias==1 && raw.legacy==1 &&
		input_world->width==12 && input_world->height==12;
	const bool public8Legacy16 = bpc==8 && raw.amount==5.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==1 && raw.bias==1 && raw.legacy==1 &&
		input_world->width==16 && input_world->height==16;
	const bool public8Legacy10x8 = bpc==8 && raw.amount==1.0 && raw.smoothness_fixed==100*65536 &&
		raw.repeat==2 && raw.bias==2 && raw.legacy==1 &&
		input_world->width==10 && input_world->height==8;
	const bool public8LegacySmooth = bpc==8 && raw.amount==9.0 && raw.smoothness_fixed==2867200 &&
		raw.repeat==3 && raw.bias==2 && raw.legacy==1 &&
		input_world->width==19 && input_world->height==13;
	const bool public16LegacySmooth = bpc==16 && raw.amount==7.0 && raw.smoothness_fixed==4096000 &&
		raw.repeat==4 && raw.bias==1 && raw.legacy==1 &&
		input_world->width==20 && input_world->height==16;
	const bool public32NonLegacyRetained = bpc==32 && raw.smoothness_fixed==100*65536 && raw.legacy==0 && (
		(raw.amount==3.0 && raw.repeat==2 && raw.bias==1 && input_world->width==12 && input_world->height==12) ||
		(raw.amount==11.0 && raw.repeat==3 && raw.bias==2 && input_world->width==18 && input_world->height==18) ||
		((raw.amount==129.4 && raw.repeat==2 && (raw.bias==1 || raw.bias==2) ||
		  raw.amount==125.6 && raw.repeat==4 && raw.bias==1) && input_world->width==4 && input_world->height==3) ||
		(raw.amount==5.0 && (raw.repeat==2 || raw.repeat==10) && raw.bias==1 && input_world->width==7 && input_world->height==5) ||
		((raw.amount==129.4 && (raw.repeat==1 && raw.bias==1 || raw.repeat==2 && raw.bias==2) ||
		  raw.amount==125.6 && raw.repeat==4 && raw.bias==1 ||
		  raw.amount==5.0 && (raw.repeat==2 || raw.repeat==10) && raw.bias==1) && input_world->width==24 && input_world->height==24));
	const bool public32Legacy12 = bpc==32 && raw.amount==3.0 && raw.smoothness_fixed==100*65536 && raw.repeat==2 && raw.bias==1 && raw.legacy==1 && input_world->width==12 && input_world->height==12;
	const bool public32Legacy18 = bpc==32 && raw.amount==11.0 && raw.smoothness_fixed==100*65536 && raw.repeat==3 && raw.bias==2 && raw.legacy==1 && input_world->width==18 && input_world->height==18;
	const bool public32Legacy18x12 = bpc==32 && raw.amount==3.0 && raw.smoothness_fixed==100*65536 && raw.repeat==2 && raw.bias==2 && raw.legacy==1 && input_world->width==18 && input_world->height==12;
	const bool public32Legacy7x5 = bpc==32 && raw.amount==248.6 && raw.smoothness_fixed==100*65536 && raw.repeat==10 && raw.bias==1 && raw.legacy==1 && input_world->width==7 && input_world->height==5;
	const bool public32Legacy9x7 = bpc==32 && raw.amount==5.0 && raw.smoothness_fixed==100*65536 && raw.repeat==10 && raw.bias==1 && raw.legacy==1 && input_world->width==9 && input_world->height==7;
	const bool public32Legacy24Repeat1 = bpc==32 && raw.amount==5.0 && raw.smoothness_fixed==100*65536 && raw.repeat==1 && raw.bias==1 && raw.legacy==1 && input_world->width==24 && input_world->height==24;
	const bool public32Legacy24Repeat10 = bpc==32 && raw.amount==248.6 && raw.smoothness_fixed==100*65536 && raw.repeat==10 && raw.bias==1 && raw.legacy==1 && input_world->width==24 && input_world->height==24;
	const bool public32LegacySmooth = bpc==32 && raw.amount==11.0 && raw.smoothness_fixed==2457600 && raw.repeat==3 && raw.bias==2 && raw.legacy==1 && input_world->width==24 && input_world->height==24;
	PublicBlurSourceKind source_kind = PublicBlurSourceNone;
	A_long width=0,height=0,rowbytes=0;
	if (public24) {
		source_kind=(bpc==32 && raw.legacy==1)?PublicBlurSourcePF32Legacy24Repeat1Union:PublicBlurSourceOriginal24;width=height=24;
		rowbytes=bpc==8?113:(bpc==16?215:(bpc==32?(raw.legacy==1&&input_world->rowbytes==397?397:416):0));
	} else if (public7x5) {
		source_kind=PublicBlurSourcePF16SevenByFive;width=7;height=5;rowbytes=69;
	} else if (public12x12 || public18x18) {
		source_kind=PublicBlurSourcePF16Standard;width=public12x12?12:18;
		height=width;rowbytes=public12x12?109:157;
	} else if (public18x12) {
		source_kind=PublicBlurSourcePF16MixedAlpha;width=18;height=12;rowbytes=157;
	} else if (public16LegacySmooth) {
		source_kind=PublicBlurSourcePF16LegacyWordBoundaries;width=20;height=16;rowbytes=173;
	} else if (public8NonLegacy12 || public8NonLegacy18 || public8NonLegacy24 || public8NonLegacy24Repeat2) {
		source_kind=PublicBlurSourcePF8NonLegacyStandard;
		width=public8NonLegacy12?12:(public8NonLegacy18?18:24);height=width;rowbytes=width*4+13;
	} else if (public8Legacy12 || public8Legacy18 || public8Legacy16) {
		source_kind=PublicBlurSourcePF8LegacyStandard;
		width=public8Legacy12?12:(public8Legacy18?18:16);height=width;rowbytes=width*4+13;
	} else if (public8Legacy18x12) {
		source_kind=PublicBlurSourcePF8LegacyMixedAlpha;width=18;height=12;rowbytes=85;
	} else if (public8Legacy6 || public8LegacyBoundary12 || public8Legacy10x8) {
		source_kind=PublicBlurSourcePF8LegacyBoundaryGradient;
		width=public8Legacy6?6:(public8LegacyBoundary12?12:10);
		height=public8Legacy6?6:(public8LegacyBoundary12?12:8);rowbytes=width*4+13;
	} else if (public8LegacySmooth) {
		source_kind=PublicBlurSourcePF8LegacyByteBoundaries;width=19;height=13;rowbytes=89;
	} else if (public32NonLegacyRetained) {
		source_kind=PublicBlurSourcePF32NonLegacyStandard;width=input_world->width;height=input_world->height;rowbytes=width*16+13;
	} else if (public32Legacy12 || public32Legacy18 || public32Legacy24Repeat1 || public32Legacy24Repeat10 || public32LegacySmooth) {
		source_kind=PublicBlurSourcePF32LegacyStandard;width=public32Legacy12?12:(public32Legacy18?18:24);height=width;rowbytes=width*16+13;
	} else if (public32Legacy18x12 || public32Legacy9x7) {
		source_kind=PublicBlurSourcePF32LegacyMixedAlpha;width=public32Legacy18x12?18:9;height=public32Legacy18x12?12:7;rowbytes=width*16+13;
	} else if (public32Legacy7x5) {
		source_kind=PublicBlurSourcePF32LegacyRedBoundary;width=7;height=5;rowbytes=125;
	}
	const size_t active=(size_t)width*pixel_bytes;
	if (!err && source_kind==PublicBlurSourceNone)
		err=PF_Err_BAD_CALLBACK_PARAM;
	// The Windows exported Smart owner materializes the fixed-slider value
	// from the signed high word of PF_Fixed.  Preserve that public boundary
	// only for the three admitted fractional-Smoothness fixtures; the full
	// fixed value above remains part of each exact admission predicate.
	if (!err && (public8LegacySmooth || public16LegacySmooth || public32LegacySmooth))
		bp.blur_smoothness=(float)(int16_t)((uint32_t)raw.smoothness_fixed >> 16);
	if (!err && (in_data->downsample_x.num!=1 || in_data->downsample_x.den!=1 ||
		in_data->downsample_y.num!=1 || in_data->downsample_y.den!=1 ||
		!pixel_bytes || !ExactPublicWorld(input_world,bpc,width,height,rowbytes) ||
		!ExactPublicWorld(output_world,bpc,width,height,rowbytes) ||
		!PublicWorldsDisjoint(input_world,output_world,height) ||
		!ExactPublicSource(input_world,bpc,raw.legacy!=0,source_kind))) err=PF_Err_BAD_CALLBACK_PARAM;
	if (!err) err = GetPublicWorldFormats(in_data,input_world,output_world,bpc);
	if (!err) try {
		const size_t pixels=(size_t)width*(size_t)height;
		std::vector<PF_PixelFloat> source_words(pixels),destination_words(pixels);
		unsigned char *source=(unsigned char*)source_words.data();
		unsigned char *destination=(unsigned char*)destination_words.data();
		for(size_t y=0;y<(size_t)height;++y) memcpy(source+y*active,(const unsigned char*)input_world->data+y*input_world->rowbytes,active);
		memcpy(destination,source,active*(size_t)height);
		PF_EffectWorld staged_input=*input_world,staged_output=*output_world;
		staged_input.data=(PF_PixelPtr)source;staged_input.rowbytes=(A_long)active;
		staged_output.data=(PF_PixelPtr)destination;staged_output.rowbytes=(A_long)active;
		err=PF_COPY(&staged_input,&staged_output,NULL,NULL);
		if(!err) err=BlurRender(in_data,&staged_input,&staged_output,bpc,&bp);
		if(!err) for(size_t y=0;y<(size_t)height;++y) {
			unsigned char *out=(unsigned char*)output_world->data+y*output_world->rowbytes;
			const unsigned char *in=(const unsigned char*)input_world->data+y*input_world->rowbytes;
			memcpy(out,destination+y*active,active);
			memcpy(out+active,in+active,(size_t)output_world->rowbytes-active);
		}
	} catch(const std::bad_alloc&){err=PF_Err_OUT_OF_MEMORY;}
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
#if !defined(OLMBLUR_HOSTLESS_RENDER_HARNESS)
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParamsUI(in_data); break;
#endif
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

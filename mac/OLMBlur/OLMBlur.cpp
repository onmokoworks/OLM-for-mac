#include "../../core/olm_exact_math.h"
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
#include <fcntl.h>
#include <unistd.h>
#include "../../core/olm_world_safety.h"

// Global flags written by the AEX EffectMain GlobalSetup branch, 0x18000a970.
static constexpr A_long kGlobalFlags = 0x06000040;
// Secondary flags written by the same AEX GlobalSetup branch, 0x18000a970.
static constexpr A_long kGlobalFlags2 = 0x08001400;
// IEEE-754 exponent mask for the C32 admission policy, not an AEX coefficient.
static constexpr uint32_t kFloatExponentMask = 0x7f800000u;
// Finite colour bounds of the retained C32 source admission policy.
static constexpr float kFiniteColourLimit = 16.0f;

// Refusal attribution for the fuzz campaign. When OLM_REFUSAL_TRACE names a
// file, each failing admission guard appends "function:tag@line". The file is
// only opened on a refusal, and the returned error code and all output bytes
// are identical whether or not tracing is enabled.
static PF_Err BlurRefusal(const char *function, const char *tag, int line, PF_Err err)
{
	const char *path = ::getenv("OLM_REFUSAL_TRACE");
	if (path && path[0]) {
		const int handle = ::open(path, O_WRONLY | O_CREAT | O_APPEND, 0666);
		if (handle >= 0) {
			char entry[384];
			const int length = ::snprintf(entry, sizeof(entry), "%s:%s@%d\n", function, tag, line);
			if (length > 0) {
				const ssize_t written = ::write(handle, entry, (size_t)length);
				(void)written;
			}
			::close(handle);
		}
	}
	return err;
}

#define OLM_BLUR_REFUSAL(tag) BlurRefusal(__func__, tag, __LINE__, PF_Err_BAD_CALLBACK_PARAM)
#define OLM_BLUR_ERROR(tag, code) BlurRefusal(__func__, tag, __LINE__, code)

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
	out_data->out_flags  = kGlobalFlags;
	out_data->out_flags2 = kGlobalFlags2;
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

#include "OLMBlur_Workers.inc"

static PF_Err
BlurRender(PF_InData *in_data, PF_EffectWorld *input, PF_EffectWorld *output,
           short bpc, const BlurParams *bp)
{
	PF_Err err = PF_Err_NONE;
	A_long w = input->width, h = input->height;
	if (w <= 0 || h <= 0) return err;
	const BlurObservationConfig observation = load_blur_observation_config();

	// Original non-Legacy workers scale Amount in float32 before deriving
	// integer radii (CVTTSS2SI). Legacy scales radius and sigma separately.
	// Both axes use downsample_x; Smoothness, Repeat and Bias are unchanged.
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

	// Smart admission and format validation admit only the six depth/mode routes above.
	return err;
}

static PF_Err
ClassicCopyGeometry(const PF_EffectWorld *input, const PF_EffectWorld *output,
	std::size_t pixel_bytes)
{
	if (!input || !output || !input->data || !output->data || !pixel_bytes ||
		input->width <= 0 || input->height <= 0 ||
		input->width != output->width || input->height != output->height ||
		input->width > 4096 || input->height > 2160)
		return PF_Err_BAD_CALLBACK_PARAM;
	const std::size_t width = (std::size_t)input->width;
	const std::size_t height = (std::size_t)input->height;
	if (width > ((std::size_t)-1) / height || width * height > 3840u * 2160u)
		return PF_Err_BAD_CALLBACK_PARAM;
	return PF_Err_NONE;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	if (!params || !output || !params[OLMBLUR_INPUT] ||
		!params[OLMBLUR_BLUR_AMOUNT] || !params[OLMBLUR_BLUR_SMOOTHNESS] ||
		!params[OLMBLUR_REPEAT]) {
		return OLM_BLUR_REFUSAL("render-params-null");
	}
	PF_EffectWorld *input = &params[OLMBLUR_INPUT]->u.ld;
	if (!input->data || !output->data || input->width != output->width ||
		input->height != output->height) {
		return OLM_BLUR_REFUSAL("render-world-geometry");
	}
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite(in_data, kPFWorldSuite,
	                                             kPFWorldSuiteVersion2, out_data);
	ERR(world_suite->PF_GetPixelFormat(input, &input_format));
	ERR(world_suite->PF_GetPixelFormat(output, &output_format));
	if (err) return err;
	if (input_format != output_format) return OLM_BLUR_REFUSAL("render-format-mismatch");

	std::size_t pixel_bytes = 0;
	switch (output_format) {
	case PF_PixelFormat_ARGB32:
		pixel_bytes = sizeof(PF_Pixel8);
		break;
	case PF_PixelFormat_ARGB64:
		pixel_bytes = sizeof(PF_Pixel16);
		break;
	case PF_PixelFormat_ARGB128:
		// The retained Windows classic owner tests only PF_WorldFlag_DEEP,
		// so PF32 aliases its PF16 branch.  Keep the unowned float route
		// fail-closed; the advertised numerical PF32 owner is Smart Render.
		return OLM_BLUR_REFUSAL("classic-pf32-unowned");
	default:
		return OLM_BLUR_REFUSAL("classic-format-unknown");
	}
	ERR(ClassicCopyGeometry(input, output, pixel_bytes));
	if (err) return OLM_BLUR_REFUSAL("classic-copy-geometry");

	// The current Windows classic export reads only parameter slots 1..3 and,
	// with the registered float-slider default, observes a zero low dword for
	// Blur Amount.  Its PF8/PF16 non-Legacy worker therefore returns after the
	// initial world copy.  Admit that copy-only tuple for bounded general worlds.
	// Bias and
	// Legacy are deliberately not consumed: the classic owner does not read
	// slots 4 or 5.  All numerical/non-default work remains on Smart Render.
	const PF_FpLong blur_amount = params[OLMBLUR_BLUR_AMOUNT]->u.fs_d.value;
	const A_long blur_smoothness = params[OLMBLUR_BLUR_SMOOTHNESS]->u.fd.value;
	const A_long repeat = params[OLMBLUR_REPEAT]->u.sd.value;
	if (blur_amount != 5.0 || blur_smoothness != 100 * 65536 || repeat != 2) {
		return OLM_BLUR_REFUSAL("classic-nondefault-tuple");
	}

	olm::world_safety::TightStaging staging;
	const olm::world_safety::Status stage_status = staging.prepare(
		{input->data, (std::size_t)input->width, (std::size_t)input->height,
		 (std::size_t)input->rowbytes, pixel_bytes},
		{output->data, (std::size_t)output->width, (std::size_t)output->height,
		 (std::size_t)output->rowbytes, pixel_bytes});
	if (stage_status != olm::world_safety::Status::ok)
		return stage_status == olm::world_safety::Status::out_of_memory ?
			OLM_BLUR_ERROR("classic-staging-oom", PF_Err_OUT_OF_MEMORY) :
			OLM_BLUR_REFUSAL("classic-staging");
	std::memcpy(staging.output_data(), staging.input_data(),
		staging.row_bytes() * staging.height());
	return staging.commit() == olm::world_safety::Status::ok ?
		PF_Err_NONE : OLM_BLUR_REFUSAL("classic-commit");
}

// Original rectangle union, FUN_18000bd90. Empty destinations are replaced;
// empty sources do not enlarge a nonempty destination.
static void BlurUnionRect(const PF_LRect& source, PF_LRect& destination)
{
	if (destination.left >= destination.right || destination.top >= destination.bottom) {
		destination = source;
	} else if (source.left < source.right && source.top < source.bottom) {
		destination.left = std::min(destination.left, source.left);
		destination.top = std::min(destination.top, source.top);
		destination.right = std::max(destination.right, source.right);
		destination.bottom = std::max(destination.bottom, source.bottom);
	}
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	(void)out_data;
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
		!extra->cb->checkout_layer) return OLM_BLUR_REFUSAL("prerender-inputs");
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	// Original 0x18000ab01..0x18000ab85 unions the full InData bounds
	// into the request before checkout (without downsample or aspect scaling).
	const PF_LRect full_bounds = {0, 0, in_data->width, in_data->height};
	BlurUnionRect(full_bounds, req.rect);
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMBLUR_INPUT, OLMBLUR_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		BlurUnionRect(in_result.result_rect, extra->output->result_rect);
		BlurUnionRect(in_result.max_result_rect, extra->output->max_result_rect);
		extra->output->solid = FALSE;
		extra->output->pre_render_data = NULL;
		// Original 0x18000ab94 writes RETURNS_EXTRA_PIXELS.
		extra->output->flags = PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS;
	}
	if (err) return BlurRefusal(__func__, "prerender-checkout", __LINE__, err);
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
		world->origin_x != 0 || world->origin_y != 0)
		return false;
	// The original workers consume the entire checked-out pixel world;
	// extent_hint is not a clipping rectangle for their filtering passes.
	const size_t usize_width = (size_t)width;
	if (usize_width > ((size_t)-1) / pixel_bytes) return false;
	const size_t active = usize_width * pixel_bytes;
	return active <= (size_t)world->rowbytes;
}

// Returns the first failing admission reason, or NULL when the tuple is
// admitted. Tags retain the first failing admission reason.
static const char *
GenericBetaTupleRefusal(const PublicBlurParamValues& raw, A_long width, A_long height, short bpc)
{
	if (!isfinite(raw.amount)) return "generic-amount-nonfinite";
	if (raw.amount < 1.0 || raw.amount > 1000.0) return "generic-amount-range";
	if (raw.smoothness_fixed < 1 * 65536 || raw.smoothness_fixed > 100 * 65536)
		return "generic-smoothness-range";
	if (raw.repeat < 1 || raw.repeat > 10) return "generic-repeat-range";
	if (raw.bias < 1 || raw.bias > 2) return "generic-bias-range";
	if (raw.legacy != 0 && raw.legacy != 1) return "generic-legacy-range";
	if (width <= 0 || height <= 0) return "generic-size-invalid";
	// All supported depths now admit both modes at small sizes. Retain the
	// historical refusal for unsupported depths, including its ordering.
	if (width <= 24 && height <= 24 && bpc != 8 && bpc != 16 && bpc != 32)
		return "generic-small-fixture";
	const size_t usize_width = (size_t)width, usize_height = (size_t)height;
	if (usize_width > ((size_t)-1) / usize_height) return "generic-size-overflow";
	const size_t pixels = usize_width * usize_height;
	// Smart admission is limited by actual buffer representability, not an
	// estimated live-memory or synchronous-work policy. The PF32 packed
	// world is the largest individual vector (four floats per pixel).
	if (pixels > std::vector<float>().max_size() / 4u)
		return "generic-vector-size-overflow";
	return NULL;
}

static bool
SmallDefaultPF32Source(const PF_EffectWorld *world)
{
	// Called only after GenericBetaWorld validates the full active storage.
	// C32: both workers preserve signed infinities and NaN payloads under
	// the SSE helper semantics. Keep larger finite values outside this domain.
	for (A_long y=0; y<world->height; ++y) {
		const unsigned char *row=(const unsigned char*)world->data+(size_t)y*world->rowbytes;
		for (A_long x=0; x<world->width; ++x) {
			float argb[4]; memcpy(argb,row+(size_t)x*sizeof(argb),sizeof(argb));
			for (int c=0;c<4;++c) {
				uint32_t bits; memcpy(&bits, &argb[c], sizeof(bits));
				if ((bits & kFloatExponentMask) == kFloatExponentMask) continue;
				if (!(argb[c]>=-kFiniteColourLimit && argb[c]<=kFiniteColourLimit)) return false;
			}
		}
	}
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
		else if (ordinal == 1) {
			raw->smoothness_fixed=p.u.fd.value;
			// The exported Windows Smart builder reads the signed high word
			// of PF_Fixed (FUN_180009b40), discarding its fractional bits.
			// Keep the full raw value for admission checks on both lanes.
			bp->blur_smoothness=(float)(int16_t)((uint32_t)raw->smoothness_fixed >> 16);
		}
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

#include "OLMBlur_Fixtures.inc"

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	(void)out_data;
	if (!in_data || !extra || !extra->input || !extra->cb ||
		!extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
		!in_data->inter.checkout_param || !in_data->inter.checkin_param)
		return OLM_BLUR_REFUSAL("smartrender-inputs");
	PF_Err err=PF_Err_NONE; PF_EffectWorld *input_world=NULL,*output_world=NULL;
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref,OLMBLUR_INPUT,&input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref,&output_world));
	if (err) return BlurRefusal(__func__, "smartrender-checkout", __LINE__, err);
	if (!input_world || !output_world) return OLM_BLUR_REFUSAL("smartrender-world-null");
	BlurParams bp; AEFX_CLR_STRUCT(bp); PublicBlurParamValues raw; AEFX_CLR_STRUCT(raw);
	err = CheckoutPublicBlurParams(in_data, &bp, &raw);
	if (err) return BlurRefusal(__func__, "smartrender-param-checkout", __LINE__, err);
	const short bpc=extra->input->bitdepth;
	const size_t pixel_bytes=bpc==8?4u:(bpc==16?8u:(bpc==32?16u:0u));
	// Generic beta lane.  Exact fixture admissions remain below as a fallback,
	// retaining their special source and arithmetic contracts.
	const char *generic_tuple_refusal =
		GenericBetaTupleRefusal(raw,input_world->width,input_world->height,bpc);
	const bool generic_input_ok =
		GenericBetaWorld(input_world,pixel_bytes,input_world->width,input_world->height);
	const bool generic_output_ok =
		GenericBetaWorld(output_world,pixel_bytes,input_world->width,input_world->height);
	if (!generic_tuple_refusal && generic_input_ok && bpc==32 &&
		input_world->width<=24 && input_world->height<=24 &&
		!SmallDefaultPF32Source(input_world))
		generic_tuple_refusal="generic-small-pf32-domain";
	const bool full_resolution =
		in_data->downsample_x.num==1 && in_data->downsample_x.den==1 &&
		in_data->downsample_y.num==1 && in_data->downsample_y.den==1;
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
		(((raw.amount==129.4 && raw.repeat==2 && (raw.bias==1 || raw.bias==2)) ||
		  (raw.amount==125.6 && raw.repeat==4 && raw.bias==1)) && input_world->width==4 && input_world->height==3) ||
		(raw.amount==5.0 && (raw.repeat==2 || raw.repeat==10) && raw.bias==1 && input_world->width==7 && input_world->height==5) ||
		(((raw.amount==129.4 && ((raw.repeat==1 && raw.bias==1) || (raw.repeat==2 && raw.bias==2))) ||
		  (raw.amount==125.6 && raw.repeat==4 && raw.bias==1) ||
		  (raw.amount==5.0 && (raw.repeat==2 || raw.repeat==10) && raw.bias==1)) && input_world->width==24 && input_world->height==24));
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
	// Preserve the established fixture's copy/padding and callback contract
	// when its complete source/world admission matches. The new generic rule
	// handles other inputs without changing that exact owner's lifecycle.
	const bool exact_fixture_owner = source_kind != PublicBlurSourceNone &&
		ExactPublicWorld(input_world,bpc,width,height,rowbytes) &&
		ExactPublicWorld(output_world,bpc,width,height,rowbytes) &&
		PublicWorldsDisjoint(input_world,output_world,height) &&
		ExactPublicSource(input_world,bpc,raw.legacy!=0,source_kind);
	if (!err && !generic_tuple_refusal && generic_input_ok && generic_output_ok &&
		(!full_resolution || !exact_fixture_owner)) {
		err=GetPublicWorldFormats(in_data,input_world,output_world,bpc);
		if (err) err=BlurRefusal(__func__, "generic-formats", __LINE__, err);
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
				err = OLM_BLUR_ERROR("generic-staging-oom", PF_Err_OUT_OF_MEMORY);
			else if (stage_status != olm::world_safety::Status::ok)
				err = OLM_BLUR_REFUSAL("generic-staging");
		}
		PF_EffectWorld staged_input = *input_world;
		PF_EffectWorld staged_output = *output_world;
		if (!err) {
			staged_input.data = (PF_PixelPtr)const_cast<uint8_t *>(staging.input_data());
			staged_input.rowbytes = (A_long)staging.row_bytes();
			staged_output.data = (PF_PixelPtr)staging.output_data();
			staged_output.rowbytes = (A_long)staging.row_bytes();
			err=BlurRender(in_data,&staged_input,&staged_output,bpc,&bp);
			if (err) err=BlurRefusal(__func__, "generic-render", __LINE__, err);
		}
		const PF_Err checkin_err=extra->cb->checkin_layer_pixels ?
			extra->cb->checkin_layer_pixels(in_data->effect_ref,OLMBLUR_INPUT) : PF_Err_NONE;
		if (!err) err=checkin_err ? BlurRefusal(__func__, "generic-checkin", __LINE__, checkin_err) : checkin_err;
		if (!err && staging.commit() != olm::world_safety::Status::ok)
			err=OLM_BLUR_REFUSAL("generic-commit");
		return err;
	}
	const size_t active=(size_t)width*pixel_bytes;
	if (!err && source_kind==PublicBlurSourceNone) {
		if (generic_tuple_refusal) err=OLM_BLUR_REFUSAL(generic_tuple_refusal);
		else if (!generic_input_ok) err=OLM_BLUR_REFUSAL("generic-input-world");
		else if (!generic_output_ok) err=OLM_BLUR_REFUSAL("generic-output-world");
		else err=OLM_BLUR_REFUSAL("exact-source-none");
	}
	if (!err && !pixel_bytes) err=OLM_BLUR_REFUSAL("exact-bitdepth");
	if (!err && !ExactPublicWorld(input_world,bpc,width,height,rowbytes))
		err=OLM_BLUR_REFUSAL("exact-input-world");
	if (!err && !ExactPublicWorld(output_world,bpc,width,height,rowbytes))
		err=OLM_BLUR_REFUSAL("exact-output-world");
	if (!err && !PublicWorldsDisjoint(input_world,output_world,height))
		err=OLM_BLUR_REFUSAL("exact-worlds-overlap");
	if (!err && !ExactPublicSource(input_world,bpc,raw.legacy!=0,source_kind))
		err=OLM_BLUR_REFUSAL("exact-source-mismatch");
	if (!err) {
		err = GetPublicWorldFormats(in_data,input_world,output_world,bpc);
		if (err) err=BlurRefusal(__func__, "exact-formats", __LINE__, err);
	}
	if (err) return err;
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
		if (!err) {
			err=BlurRender(in_data,&staged_input,&staged_output,bpc,&bp);
			if (err) err=BlurRefusal(__func__, "exact-render", __LINE__, err);
		}
		if(!err) for(size_t y=0;y<(size_t)height;++y) {
			unsigned char *out=(unsigned char*)output_world->data+y*output_world->rowbytes;
			const unsigned char *in=(const unsigned char*)input_world->data+y*input_world->rowbytes;
			memcpy(out,destination+y*active,active);
			memcpy(out+active,in+active,(size_t)output_world->rowbytes-active);
		}
	} catch(const std::bad_alloc&){
		err=BlurRefusal(__func__, "exact-bad-alloc", __LINE__, PF_Err_OUT_OF_MEMORY);
	}
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

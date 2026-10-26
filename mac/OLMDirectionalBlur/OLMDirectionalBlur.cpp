#include "OLMDirectionalBlur.h"

#include <AEFX_SuiteHandlerTemplate.h>

#include "../../core/dblur_frontonly.h"
#include "../../core/dblur_generic_budget.h"
#include "../../core/dblur_gaussian.h"
#include "../../core/olm_sha256_rows.h"
#include "../../core/olm_world_safety.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <exception>
#include <limits>
#include <memory>
#include <cstdlib>
#include <cerrno>
#include <fcntl.h>
#include <unistd.h>
#include <vector>

// Optional diagnostic attribution, following OLM_RADIAL_REFUSAL. Keep the
// original PF_Err, output and errno even when opening/writing the trace fails.
static PF_Err DirectionalRefusal(const char *function, const char *tag, int line, PF_Err err)
{
    const int saved_errno = errno;
    const char *path = std::getenv("OLM_REFUSAL_TRACE");
    if (path && path[0]) {
        const int handle = ::open(path, O_WRONLY | O_CREAT | O_APPEND, 0666);
        if (handle >= 0) {
            char entry[384];
            const int length = std::snprintf(entry, sizeof(entry), "%s:%s@%d\n", function, tag, line);
            if (length > 0 && static_cast<std::size_t>(length) < sizeof(entry)) {
                const ssize_t written = ::write(handle, entry, static_cast<std::size_t>(length));
                (void)written;
            }
            ::close(handle);
        }
    }
    errno = saved_errno;
    return err;
}
#define OLM_DIRECTIONAL_REFUSAL(tag) DirectionalRefusal(__func__, tag, __LINE__, PF_Err_BAD_CALLBACK_PARAM)

static PF_Err DirectionalCoreError(const char *function, int line, int result)
{
    const int saved_errno = errno;
    char tag[64];
    std::snprintf(tag, sizeof(tag), "core-result-%d", result);
    const PF_Err err = DirectionalRefusal(function, tag, line,
        result == -5 ? PF_Err_OUT_OF_MEMORY : PF_Err_INTERNAL_STRUCT_DAMAGED);
    errno = saved_errno;
    return err;
}
#define OLM_DIRECTIONAL_CORE_ERROR(result) DirectionalCoreError(__func__, __LINE__, result)


// Legacy host scale uses full-precision pi; core angle builder keeps its AEX literal.
static constexpr PF_FpLong kPi = 3.141592653589793238462643383279502884;
#if !defined(OLM_DBLUR_TEST_SEAM)
static AEGP_PluginID g_aegp_plugin_id = 0;
#endif

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
GlobalSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x06000040;
	out_data->out_flags2 = 0x08001408;
#if !defined(OLM_DBLUR_TEST_SEAM)
	// Source-included parameter-layout probes have no host suite table. A real
	// AE GLOBAL_SETUP always supplies one; register there, as the AEX does.
	if (!in_data || !in_data->pica_basicP) return PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	return suites.UtilitySuite6()->AEGP_RegisterWithAEGP(
		nullptr, "OLMDirectionalBlur", &g_aegp_plugin_id);
#else
	return PF_Err_NONE;
#endif
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_ANGLE(GetStringPtr(StrID_Angle_Param_Name), 0.0, ANGLE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_BrightnessGain_Param_Name),
	                     0.0, 10.0, 0.0, 2.0, 1.0,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     BRIGHTNESS_GAIN_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_SizeVariation_Param_Name),
	             0.0, 100.0, 0.0, 100.0, 0.0,
	             PF_Precision_TENTHS, PF_ValueDisplayFlag_PERCENT, 0,
	             SIZE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_FrontBlurParams_Param_Name), FRONT_PARAMS_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_FrontStrength_Param_Name),
	              0, 4000, 0, 4000, 0,
	              FRONT_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_FrontAlphaFade_Param_Name),
	              0, 100, 0, 100, 0,
	              FRONT_ALPHA_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_FrontSharpTail_Param_Name),
	             0.0, 100.0, 0.0, 100.0, 0.0,
	             PF_Precision_TENTHS, PF_ValueDisplayFlag_PERCENT, 0,
	             FRONT_SHARP_TAIL_DISK_ID);

	PF_END_TOPIC(FRONT_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_BackBlurParams_Param_Name), BACK_PARAMS_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_BackStrength_Param_Name),
	              0, 4000, 0, 4000, 0,
	              BACK_STRENGTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_BackAlphaFade_Param_Name),
	              0, 100, 0, 100, 0,
	              BACK_ALPHA_FADE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_BackSharpTail_Param_Name),
	             0.0, 100.0, 0.0, 100.0, 0.0,
	             PF_Precision_TENTHS, PF_ValueDisplayFlag_PERCENT, 0,
	             BACK_SHARP_TAIL_DISK_ID);

	PF_END_TOPIC(BACK_BLANK_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_NoiseParams_Param_Name), NOISE_PARAMS_LABEL_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FIXED(GetStringPtr(StrID_NoiseVariation_Param_Name),
	             0.0, 100.0, 0.0, 100.0, 0.0,
	             PF_Precision_TENTHS, PF_ValueDisplayFlag_PERCENT, 0,
	             NOISE_VARIATION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_NoiseType_Param_Name),
	             2, 1, GetStringPtr(StrID_NoiseType_Choices),
	             NOISE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_LAYER(GetStringPtr(StrID_NoiseLayer_Param_Name), PF_LayerDefault_NONE, NOISE_LAYER_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Seed_Param_Name),
	              1, 1000, 1, 1000, 1,
	              SEED_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_ANGLE(GetStringPtr(StrID_NoiseOffset_Param_Name), 0.0, NOISE_OFFSET_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Thickness_Param_Name),
	                     1.0, 100.0, 1.0, 100.0, 10.0,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     THICKNESS_DISK_ID);

	PF_END_TOPIC(NOISE_BLANK_DISK_ID);

	out_data->num_params = OLMDIRECTIONALBLUR_NUM_PARAMS;
	return err;
}

#if !defined(OLM_DBLUR_TEST_SEAM)
static PF_Err
UpdateParamsUI(PF_InData *in_data)
{
	if (!in_data) return OLM_DIRECTIONAL_REFUSAL("ui-in-data");
	PF_Err err = PF_Err_NONE;
	PF_ParamDef noise_type_param;
	AEFX_CLR_STRUCT(noise_type_param);
	ERR(PF_CHECKOUT_PARAM(in_data, OLMDIRECTIONALBLUR_NOISE_TYPE,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&noise_type_param));
	if (err) return err;
	const A_Boolean layer_mode = noise_type_param.u.pd.value == 3 ? TRUE : FALSE;
	PF_CHECKIN_PARAM(in_data, &noise_type_param);

	AEFX_SuiteScoper<AEGP_PFInterfaceSuite1> pf_interface(
		in_data, kAEGPPFInterfaceSuite, kAEGPPFInterfaceSuiteVersion1);
	AEFX_SuiteScoper<AEGP_StreamSuite6> streams(
		in_data, kAEGPStreamSuite, kAEGPStreamSuiteVersion6);
	AEFX_SuiteScoper<AEGP_DynamicStreamSuite4> dynamic_streams(
		in_data, kAEGPDynamicStreamSuite, kAEGPDynamicStreamSuiteVersion4);
	AEFX_SuiteScoper<AEGP_EffectSuite5> effects(
		in_data, kAEGPEffectSuite, kAEGPEffectSuiteVersion5);

	AEGP_EffectRefH effect = nullptr;
	ERR(pf_interface->AEGP_GetNewEffectForEffect(
		g_aegp_plugin_id, in_data->effect_ref, &effect));
	if (!err && effect) {
		const struct {
			PF_ParamIndex index;
			A_Boolean hidden;
		} controls[] = {
			{OLMDIRECTIONALBLUR_NOISE_LAYER,
			 static_cast<A_Boolean>(layer_mode ? FALSE : TRUE)},
			{OLMDIRECTIONALBLUR_SEED, layer_mode},
			{OLMDIRECTIONALBLUR_NOISE_OFFSET, layer_mode},
			{OLMDIRECTIONALBLUR_THICKNESS, layer_mode},
		};
		for (const auto &control : controls) {
			AEGP_StreamRefH stream = nullptr;
			ERR(streams->AEGP_GetNewEffectStreamByIndex(
				g_aegp_plugin_id, effect, control.index, &stream));
			if (!err && stream) {
				AEGP_DynStreamFlags ignored_flags = 0;
				ERR(dynamic_streams->AEGP_GetDynamicStreamFlags(stream, &ignored_flags));
				ERR(dynamic_streams->AEGP_SetDynamicStreamFlag(
					stream, AEGP_DynStreamFlag_HIDDEN, FALSE, control.hidden));
			}
			if (stream) {
				const PF_Err dispose_err = streams->AEGP_DisposeStream(stream);
				if (!err) err = dispose_err;
			}
			if (err) break;
		}
	}
	if (effect) {
		const PF_Err dispose_err = effects->AEGP_DisposeEffect(effect);
		if (!err) err = dispose_err;
	}
	return err;
}
#endif

template <typename PixelT>
static PixelT *PixelAt(PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<PixelT *>(reinterpret_cast<std::uint8_t *>(world->data) +
		static_cast<std::size_t>(y) * static_cast<std::size_t>(world->rowbytes)) + x;
}

template <typename PixelT>
static const PixelT *PixelAtConst(const PF_EffectWorld *world, A_long x, A_long y)
{
	return reinterpret_cast<const PixelT *>(reinterpret_cast<const std::uint8_t *>(world->data) +
		static_cast<std::size_t>(y) * static_cast<std::size_t>(world->rowbytes)) + x;
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

#include "OLMDirectionalBlur_admission.inc"

#include "OLMDirectionalBlur_kernels.inc"

#include "OLMDirectionalBlur_dispatch.inc"

#include "OLMDirectionalBlur_host.inc"

#if defined(OLM_DBLUR_TEST_SEAM)
#include "tests/TestEntry.inc"
#endif

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
		"OLM DirectionalBlur",
		"OLM Directional Blur",
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
#if !defined(OLM_DBLUR_TEST_SEAM)
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParamsUI(in_data);
			break;
#endif
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
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return err;
}

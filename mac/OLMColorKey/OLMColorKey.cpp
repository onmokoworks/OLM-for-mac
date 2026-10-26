#include "../../core/olm_exact_math.h"
#include "OLMColorKey.h"
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
#include "../DynamicControls.h"
#endif
#include "../../core/x86_float.h"
#include "../../core/olm_parallel.h"
#include "AEFX_SuiteHandlerTemplate.h"
// Optional refusal attribution; errors and output bytes are unchanged.
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#if !defined(AE_OS_WIN)
#include <fcntl.h>
#include <unistd.h>
#endif
#include "Diagnostics.inc"
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
	// Original 2025 AEX PiPL and GLOBAL_SETUP; see F18 route/flag audit.
	out_data->out_flags  = 0x02000440;
	out_data->out_flags2 = PF_OutFlag2_SUPPORTS_SMART_RENDER |
	                      PF_OutFlag2_FLOAT_COLOR_AWARE |
	                      PF_OutFlag2_SUPPORTS_THREADED_RENDERING;
	return PF_Err_NONE;
}

template <typename T>
static T ClampValue(T value, T lo, T hi)
{
	return std::max(lo, std::min(value, hi));
}

static void MakeIndexedName(char *dst, size_t dst_size, const char *base, int index)
{
	std::snprintf(dst, dst_size, "%s %d", base, index);
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_ColorKeep_Param_Name), "", FALSE, 0,
	                COLOR_KEEP_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Threshold_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
	                     THRESHOLD_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_ThresholdGroup_Param_Name),
	             THRESHOLD_GROUP_START_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_Premultiplied_Param_Name), "", FALSE, 0,
	                PREMULTIPLIED_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_ColorSpace_Param_Name),
	             6, 1, GetStringPtr(StrID_ColorSpace_Choices),
	             COLOR_SPACE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_ForceLowerPrecision_Param_Name),
	             3, 1, GetStringPtr(StrID_ForceLowerPrecision_Choices),
	             FORCE_LOWER_PRECISION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_PerColor_Param_Name), "", FALSE, 0,
	                PER_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_PerComponent_Param_Name), "", FALSE, 0,
	                PER_COMPONENT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdR_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
	                     THRESHOLD_R_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdG_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
	                     THRESHOLD_G_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_ThresholdB_Param_Name),
	                     0.0, 1.0, 0.0, 1.0, 0.0,
	                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
	                     THRESHOLD_B_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(THRESHOLD_GROUP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_EdgeThinGroup_Param_Name),
	             EDGE_THIN_GROUP_START_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Amount_Param_Name),
	              -4000, 4000, -100, 100, 0,
	              EDGE_THIN_AMOUNT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_DistanceType_Param_Name),
	             3, 1, GetStringPtr(StrID_DistanceType_Choices),
	             EDGE_THIN_DISTANCE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(EDGE_THIN_GROUP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_TOPIC(GetStringPtr(StrID_EdgeBlurGroup_Param_Name),
	             EDGE_BLUR_GROUP_START_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_Amount_Param_Name),
	                     0.0, 4000.0, 0.0, 100.0, 0.0,
	                     PF_Precision_TENTHS, 0, 0,
	                     EDGE_BLUR_AMOUNT_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_DistanceType_Param_Name),
	             3, 1, GetStringPtr(StrID_DistanceType_Choices),
	             EDGE_BLUR_DISTANCE_TYPE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_EdgeBlurDirection_Param_Name),
	             3, 2, GetStringPtr(StrID_EdgeBlurDirection_Choices),
	             EDGE_BLUR_DIRECTION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_END_TOPIC(EDGE_BLUR_GROUP_END_DISK_ID);

	AEFX_CLR_STRUCT(def);
	def.flags = PF_ParamFlag_SUPERVISE;
	PF_ADD_SLIDER(GetStringPtr(StrID_NumberOfColors_Param_Name),
	              0, OLMCOLORKEY_MAX_COLORS, 0, 30, 1,
	              NUMBER_OF_COLORS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_EnableReplace_Param_Name), "", FALSE, PF_ParamFlag_SUPERVISE,
	                ENABLE_REPLACE_DISK_ID);

	for (int i = 0; i < OLMCOLORKEY_MAX_COLORS; ++i) {
		char name[128];
		int display_index = i + 1;

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_UseColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_CHECKBOX(name, "", FALSE, 0,
		                USE_COLOR_DISK_ID_FIRST + i * 3);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_UseReplaceColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_CHECKBOX(name, "", FALSE, 0,
		                USE_REPLACE_DISK_ID_FIRST + i * 3);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_Color_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		def.flags = PF_ParamFlag_COLLAPSE_TWIRLY;
		PF_ADD_COLOR(name, 0, 0, 0, COLOR_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ReplaceColor_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		def.flags = PF_ParamFlag_COLLAPSE_TWIRLY;
		PF_ADD_COLOR(name, 0, 0, 0, REPLACE_COLOR_DISK_ID_FIRST + i * 3);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdIndexed_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
		                     THRESHOLD_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdR_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
		                     THRESHOLD_R_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdG_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
		                     THRESHOLD_G_DISK_ID_FIRST + i * 5);

		MakeIndexedName(name, sizeof(name), GetStringPtr(StrID_ThresholdB_Param_Name), display_index);
		AEFX_CLR_STRUCT(def);
		PF_ADD_FLOAT_SLIDERX(name, 0.0, 1.0, 0.0, 1.0, 0.0,
		                     PF_Precision_TEN_THOUSANDTHS, 0, PF_ParamFlag_COLLAPSE_TWIRLY,
		                     THRESHOLD_B_DISK_ID_FIRST + i * 5);
	}

	out_data->num_params = OLMCOLORKEY_NUM_PARAMS;
	return err;
}

#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
static PF_Err
UpdateParameterUI(PF_InData *in_data, PF_ParamDef *params[])
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ParamUtilsSuite3 *param_utils = suites.ParamUtilsSuite3();

	auto set_enabled = [&](A_long index, bool enabled) {
		if (err != PF_Err_NONE) return;
		PF_ParamDef copy = *params[index];
		if (enabled)
			copy.ui_flags &= ~PF_PUI_DISABLED;
		else
			copy.ui_flags |= PF_PUI_DISABLED;
		err = param_utils->PF_UpdateParamUI(in_data->effect_ref, index, &copy);
	};

	const bool per_color = params[OLMCOLORKEY_PER_COLOR]->u.bd.value != FALSE;
	const bool per_component = params[OLMCOLORKEY_PER_COMPONENT]->u.bd.value != FALSE;
	const bool replace_enabled = params[OLMCOLORKEY_ENABLE_REPLACE]->u.bd.value != FALSE;
	const A_long color_count = ClampValue<A_long>(
		params[OLMCOLORKEY_NUMBER_OF_COLORS]->u.sd.value, 0, OLMCOLORKEY_MAX_COLORS);

	set_enabled(OLMCOLORKEY_THRESHOLD, !per_color && !per_component);
    auto set_hidden = [&](A_long index, bool hidden) {
        if (!err) err = OLMSetHidden(in_data, index, hidden);
    };
    set_hidden(OLMCOLORKEY_THRESHOLD_R, !(per_component && !per_color));
    set_hidden(OLMCOLORKEY_THRESHOLD_G, !(per_component && !per_color));
    set_hidden(OLMCOLORKEY_THRESHOLD_B, !(per_component && !per_color));
    for (int i = 0; i < OLMCOLORKEY_MAX_COLORS; ++i) {
        const bool active = i < color_count;
        const A_long first = OLMCOLORKEY_COLOR_FIRST + i * COLOR_PARAM_STRIDE;
        const bool use = params[first + COLOR_OFFSET_USE_COLOR]->u.bd.value != FALSE;
        const bool replace = params[first + COLOR_OFFSET_USE_REPLACE]->u.bd.value != FALSE;
        set_enabled(first + COLOR_OFFSET_COLOR, use);
        set_hidden(first + COLOR_OFFSET_COLOR, !active);
        set_hidden(first + COLOR_OFFSET_USE_COLOR, !active);
        set_hidden(first + COLOR_OFFSET_USE_REPLACE, !(active && replace_enabled));
        set_enabled(first + COLOR_OFFSET_USE_REPLACE, use);
        set_hidden(first + COLOR_OFFSET_REPLACE_COLOR, !(active && replace_enabled && replace));
        set_enabled(first + COLOR_OFFSET_REPLACE_COLOR, use);
        set_hidden(first + COLOR_OFFSET_THRESHOLD, !(active && per_color && !per_component));
        set_hidden(first + COLOR_OFFSET_THRESHOLD_R, !(active && per_color && per_component));
        set_hidden(first + COLOR_OFFSET_THRESHOLD_G, !(active && per_color && per_component));
        set_hidden(first + COLOR_OFFSET_THRESHOLD_B, !(active && per_color && per_component));
    }

	return err;
}
#endif

#include "Parameters.inc"
#include "Distance.inc"
#include "ColorMath.inc"
#include "AdmissionFixtures.inc"
#include "BlurMath.inc"
#include "Pixels.inc"
#include "Kernel.inc"
#include "Render.inc"
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
		"OLM Color Key",
		"OLM Color Key",
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
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = UpdateParameterUI(in_data, params); break;
#endif
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, (PF_PreRenderExtra*)extra); break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, (PF_SmartRenderExtra*)extra); break;
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = (PF_Err)4;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	return err;
}

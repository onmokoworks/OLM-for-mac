#include "ColorKeep.h"
#include <math.h>

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
		"%s v%d.%d%d\r%s",
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
	out_data->out_flags  = 0x02000040;
	out_data->out_flags2 = 0x08001400;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_EnabledColorNum_Param_Name),
	              1, COLORKEEP_MAX_COLORS,
	              1, COLORKEEP_MAX_COLORS,
	              COLORKEEP_MAX_COLORS,
	              ENABLED_COLOR_NUM_DISK_ID);

	for (int i = 0; i < COLORKEEP_MAX_COLORS; ++i) {
		AEFX_CLR_STRUCT(def);
		PF_ADD_COLOR(GetStringPtr(StrID_Color_Param_Name),
		             PF_MAX_CHAN8, PF_MAX_CHAN8, PF_MAX_CHAN8,
		             COLOR_DISK_ID_FIRST + i);
	}

	out_data->num_params = COLORKEEP_NUM_PARAMS;
	return err;
}

static PF_Err
SetColorsEnabled(PF_InData *in_data, PF_ParamDef *params[])
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ParamUtilsSuite3 *pu = suites.ParamUtilsSuite3();

	A_long enabledCount = params[COLORKEEP_ENABLED_COLOR_NUM]->u.sd.value;
	if (enabledCount < 1) enabledCount = 1;
	if (enabledCount > COLORKEEP_MAX_COLORS) enabledCount = COLORKEEP_MAX_COLORS;

	for (int i = 0; i < COLORKEEP_MAX_COLORS; ++i) {
		A_long paramIndex = COLORKEEP_COLOR_FIRST + i;
		PF_ParamDef paramCopy = *params[paramIndex];
		if (i < enabledCount)
			paramCopy.ui_flags &= ~PF_PUI_DISABLED;
		else
			paramCopy.ui_flags |= PF_PUI_DISABLED;
		ERR(pu->PF_UpdateParamUI(in_data->effect_ref, paramIndex, &paramCopy));
	}
	return err;
}

static PF_Err
CheckoutInfo(PF_InData *in_data, PF_ParamDef *params[], ColorKeepInfo *info)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();

	info->count = params[COLORKEEP_ENABLED_COLOR_NUM]->u.sd.value;
	if (info->count < 0) info->count = 0;
	if (info->count > COLORKEEP_MAX_COLORS) info->count = COLORKEEP_MAX_COLORS;

	for (A_long i = 0; i < info->count; ++i) {
		PF_ParamDef *cp = params[COLORKEEP_COLOR_FIRST + i];
		info->colors8[i] = cp->u.cd.value;
		PF_PixelFloat fp = {0};
		ERR(cps->PF_GetFloatingPointColorFromColorDef(
			in_data->effect_ref, cp, &fp));
		info->colors[i] = fp;
	}
	return err;
}

static PF_FpLong g_floatEps = 1.0e-4;

static inline u_char ftob(PF_FpLong f)
{
	return (u_char)((int)((f + (0.5 / 255.0)) * 255.0));
}

static inline u_short ftow(PF_FpLong f)
{
	return (u_short)((int)((f + (0.5 / 32768.0)) * 32768.0));
}

static PF_Err
ColorKeep8Func(void *refcon, A_long xL, A_long yL, PF_Pixel8 *inP, PF_Pixel8 *outP)
{
	ColorKeepInfo *info = (ColorKeepInfo*)refcon;
	bool match = false;
	for (A_long i = 0; i < info->count; ++i) {
		const PF_Pixel8 &c = info->colors8[i];
		if (inP->red == c.red && inP->green == c.green && inP->blue == c.blue) {
			match = true; break;
		}
	}
	outP->red = inP->red; outP->green = inP->green; outP->blue = inP->blue;
	outP->alpha = match ? inP->alpha : 0;
	return PF_Err_NONE;
}

static PF_Err
ColorKeep16Func(void *refcon, A_long xL, A_long yL, PF_Pixel16 *inP, PF_Pixel16 *outP)
{
	ColorKeepInfo *info = (ColorKeepInfo*)refcon;
	bool match = false;
	const PF_FpLong tol16 = 0.5 / 255.0;
	PF_FpLong inR = (PF_FpLong)inP->red   / PF_MAX_CHAN16;
	PF_FpLong inG = (PF_FpLong)inP->green / PF_MAX_CHAN16;
	PF_FpLong inB = (PF_FpLong)inP->blue  / PF_MAX_CHAN16;
	for (A_long i = 0; i < info->count; ++i) {
		const PF_Pixel8 &c = info->colors8[i];
		PF_FpLong cr = (PF_FpLong)c.red   / 255.0;
		PF_FpLong cg = (PF_FpLong)c.green / 255.0;
		PF_FpLong cb = (PF_FpLong)c.blue  / 255.0;
		if (fabs(inR - cr) <= tol16 && fabs(inG - cg) <= tol16 && fabs(inB - cb) <= tol16) {
			match = true; break;
		}
	}
	outP->red = inP->red; outP->green = inP->green; outP->blue = inP->blue;
	outP->alpha = match ? inP->alpha : 0;
	return PF_Err_NONE;
}

static PF_Err
ColorKeepFloatFunc(void *refcon, A_long xL, A_long yL, PF_PixelFloat *inP, PF_PixelFloat *outP)
{
	ColorKeepInfo *info = (ColorKeepInfo*)refcon;
	bool match = false;
	const float tolF = 0.5f / 255.0f;
	for (A_long i = 0; i < info->count; ++i) {
		const PF_Pixel8 &c = info->colors8[i];
		float cr = (float)c.red   / 255.0f;
		float cg = (float)c.green / 255.0f;
		float cb = (float)c.blue  / 255.0f;
		if (fabsf(inP->red - cr) <= tolF && fabsf(inP->green - cg) <= tolF && fabsf(inP->blue - cb) <= tolF) {
			match = true; break;
		}
	}
	outP->red = inP->red; outP->green = inP->green; outP->blue = inP->blue;
	outP->alpha = match ? inP->alpha : 0.0f;
	return PF_Err_NONE;
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	ColorKeepInfo info;
	AEFX_CLR_STRUCT(info);

	ERR(CheckoutInfo(in_data, params, &info));
	if (err) return err;

	A_long linesL = output->height;

	if (PF_WORLD_IS_DEEP(output)) {
		ERR(suites.Iterate16Suite2()->iterate(
			in_data, 0, linesL,
			&params[COLORKEEP_INPUT]->u.ld,
			NULL, (void*)&info, ColorKeep16Func, output));
	} else {
		ERR(suites.Iterate8Suite2()->iterate(
			in_data, 0, linesL,
			&params[COLORKEEP_INPUT]->u.ld,
			NULL, (void*)&info, ColorKeep8Func, output));
	}
	return err;
}

typedef struct {
	ColorKeepInfo info;
} PreRenderData;

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	req.preserve_rgb_of_zero_alpha = FALSE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		COLORKEEP_INPUT, COLORKEEP_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
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
	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, COLORKEEP_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));
	if (err || !input_world || !output_world) {
		extra->cb->checkin_layer_pixels(in_data->effect_ref, COLORKEEP_INPUT);
		return err;
	}

	ColorKeepInfo info;
	AEFX_CLR_STRUCT(info);

	PF_ParamDef   enabledParam;
	AEFX_CLR_STRUCT(enabledParam);
	ERR(PF_CHECKOUT_PARAM(in_data, COLORKEEP_ENABLED_COLOR_NUM,
	                      in_data->current_time, in_data->time_step, in_data->time_scale,
	                      &enabledParam));
	info.count = enabledParam.u.sd.value;
	if (info.count < 0) info.count = 0;
	if (info.count > COLORKEEP_MAX_COLORS) info.count = COLORKEEP_MAX_COLORS;
	PF_CHECKIN_PARAM(in_data, &enabledParam);

	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();
	for (A_long i = 0; i < info.count && !err; ++i) {
		PF_ParamDef cp;
		AEFX_CLR_STRUCT(cp);
		ERR(PF_CHECKOUT_PARAM(in_data, COLORKEEP_COLOR_FIRST + i,
		                      in_data->current_time, in_data->time_step, in_data->time_scale,
		                      &cp));
		if (!err) {
			PF_PixelFloat fp = {0};
			ERR(cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref, &cp, &fp));
			info.colors8[i] = cp.u.cd.value;
			info.colors[i] = fp;
			PF_CHECKIN_PARAM(in_data, &cp);
		}
	}

	A_long linesL = output_world->height;
	short bpc = extra->input->bitdepth;

	if (bpc == 8) {
		ERR(suites.Iterate8Suite2()->iterate(
			in_data, 0, linesL, input_world, NULL, (void*)&info,
			ColorKeep8Func, output_world));
	} else if (bpc == 16) {
		ERR(suites.Iterate16Suite2()->iterate(
			in_data, 0, linesL, input_world, NULL, (void*)&info,
			ColorKeep16Func, output_world));
	} else if (bpc == 32) {
		ERR(suites.IterateFloatSuite2()->iterate(
			in_data, 0, linesL, input_world, NULL, (void*)&info,
			ColorKeepFloatFunc, output_world));
	}

	extra->cb->checkin_layer_pixels(in_data->effect_ref, COLORKEEP_INPUT);
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
		"Color Keep",
		"OLM Color Keep",
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
		case PF_Cmd_USER_CHANGED_PARAM:
			err = SetColorsEnabled(in_data, params); break;
		case PF_Cmd_UPDATE_PARAMS_UI:
			err = SetColorsEnabled(in_data, params); break;
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

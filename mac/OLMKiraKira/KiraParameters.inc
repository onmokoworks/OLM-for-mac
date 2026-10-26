// Included by OLMKiraKira.cpp inside its anonymous namespace.
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

// FUN_18114e860 uses CVTDQ2PS/MULSS with float constant 0x3c23d70a
// for Strength and both Opacity controls. Keep unresolved color/resize/Gaussian
// pipelines outside this recovery until their upstream boundaries are closed.
// Original builder 18114e860: FLOAT32 getter followed by MULSS 0.2f.
static PF_FpLong ReadScalarFade(PF_FpLong value, const OLMKiraKiraInfo &info)
{
    return UsesRecoveredSeedPipeline(info) ? (PF_FpLong)((float)value * 0.2f) : value * 0.2;
}

static PF_FpLong ReadRecoveredPercent(A_long value, const OLMKiraKiraInfo &info)
{
	if (UsesRecoveredSeedPipeline(info)) return (float)value * 0.01f;
	return value / 100.0;
}

static PF_Err ReadRenderInfo(PF_InData *in_data, PF_ParamDef *params[], OLMKiraKiraInfo *info)
{
	AEFX_CLR_STRUCT(*info);
	info->glow_rotation = params[OLMKIRAKIRA_GLOW_ROTATION]->u.fs_d.value;
	info->brightness_gain = params[OLMKIRAKIRA_BRIGHTNESS_GAIN]->u.fs_d.value;
	info->vertical_length = params[OLMKIRAKIRA_VERTICAL_LENGTH]->u.sd.value;
	info->horizontal_length = params[OLMKIRAKIRA_HORIZONTAL_LENGTH]->u.sd.value;
	info->diagonal_length = params[OLMKIRAKIRA_DIAGONAL_LENGTH]->u.sd.value;
	info->diagonal2_length = params[OLMKIRAKIRA_DIAGONAL2_LENGTH]->u.sd.value;
	info->highlight_radius = params[OLMKIRAKIRA_HIGHLIGHT_RADIUS]->u.sd.value;
	info->channel = params[OLMKIRAKIRA_CHANNEL]->u.pd.value;
	info->blur_mode = params[OLMKIRAKIRA_BLUR_MODE]->u.pd.value;
	info->merge_mode = params[OLMKIRAKIRA_MERGE_MODE]->u.pd.value;
	info->approximated_input = params[OLMKIRAKIRA_APPROX_INPUT]->u.bd.value;
	info->fade_out = ReadScalarFade(params[OLMKIRAKIRA_FADE_OUT]->u.fs_d.value, *info);
	info->strength_multiplier = ReadRecoveredPercent(params[OLMKIRAKIRA_STRENGTH_MULTIPLIER]->u.sd.value, *info);
	info->glow_opacity = ReadRecoveredPercent(params[OLMKIRAKIRA_GLOW_OPACITY]->u.sd.value, *info);
	info->source_opacity = ReadRecoveredPercent(params[OLMKIRAKIRA_SOURCE_OPACITY]->u.sd.value, *info);
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
	A_long raw_strength = 0;
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_STRENGTH_MULTIPLIER, raw_strength = param->u.sd.value);
	PF_FpLong raw_fade = 0.0;
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_FADE_OUT, raw_fade = param->u.fs_d.value);

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

	A_long raw_glow_opacity = 0;
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_GLOW_OPACITY, raw_glow_opacity = param->u.sd.value);
	A_long raw_source_opacity = 0;
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_SOURCE_OPACITY, raw_source_opacity = param->u.sd.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_CHANNEL, info->channel = param->u.pd.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_BLUR_MODE, info->blur_mode = param->u.pd.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_MERGE_MODE, info->merge_mode = param->u.pd.value);
	CHECKOUT_SMART_VALUE(OLMKIRAKIRA_APPROX_INPUT, info->approximated_input = param->u.bd.value);

	info->fade_out = ReadScalarFade(raw_fade, *info);
	info->strength_multiplier = ReadRecoveredPercent(raw_strength, *info);
	info->glow_opacity = ReadRecoveredPercent(raw_glow_opacity, *info);
	info->source_opacity = ReadRecoveredPercent(raw_source_opacity, *info);
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

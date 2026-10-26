// Included by OLMColorKey.cpp; preserves the single translation unit.
static A_long ColorParamIndex(int i, int offset)
{
	return OLMCOLORKEY_COLOR_FIRST + i * COLOR_PARAM_STRIDE + offset;
}

static PF_Err AcquireColorParamSuite(PF_InData *in_data,
	                                 PF_ColorParamSuite1 **suite,
	                                 bool *needs_release)
{
	if (!in_data || !suite || !needs_release) return OLM_COLORKEY_REFUSAL("color-suite-inputs");
	*suite = NULL;
	*needs_release = false;
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	*suite = suites.ColorParamSuite1();
	return *suite && (*suite)->PF_GetFloatingPointColorFromColorDef
	    ? PF_Err_NONE : OLM_COLORKEY_REFUSAL("color-suite-callback");
#else
	if (!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
	    !in_data->pica_basicP->ReleaseSuite) return OLM_COLORKEY_REFUSAL("color-suite-basic");
	const void *raw_suite = NULL;
	const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
	    kPFColorParamSuite, kPFColorParamSuiteVersion1, &raw_suite);
	if (acquire_err) return (PF_Err)acquire_err;
	*needs_release = true;
	if (!raw_suite) return OLM_COLORKEY_REFUSAL("color-suite-null");
	*suite = (PF_ColorParamSuite1 *)raw_suite;
	return (*suite)->PF_GetFloatingPointColorFromColorDef
	    ? PF_Err_NONE : OLM_COLORKEY_REFUSAL("color-suite-callback");
#endif
}

static PF_Err ReleaseColorParamSuite(PF_InData *in_data, bool needs_release)
{
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	(void)in_data;
	(void)needs_release;
	return PF_Err_NONE;
#else
	if (!needs_release) return PF_Err_NONE;
	if (!in_data || !in_data->pica_basicP || !in_data->pica_basicP->ReleaseSuite)
		return OLM_COLORKEY_REFUSAL("color-suite-release");
	return (PF_Err)in_data->pica_basicP->ReleaseSuite(
	    kPFColorParamSuite, kPFColorParamSuiteVersion1);
#endif
}

static PF_Err
CheckoutInfo(PF_InData *in_data, PF_ParamDef *params[], OLMColorKeyInfo *info)
{
	if (!in_data || !params || !info) return OLM_COLORKEY_REFUSAL("checkout-inputs");
	const A_long required[] = {
		OLMCOLORKEY_COLOR_KEEP, OLMCOLORKEY_THRESHOLD, OLMCOLORKEY_PREMULTIPLIED,
		OLMCOLORKEY_COLOR_SPACE, OLMCOLORKEY_FORCE_LOWER_PRECISION,
		OLMCOLORKEY_PER_COLOR, OLMCOLORKEY_PER_COMPONENT,
		OLMCOLORKEY_THRESHOLD_R, OLMCOLORKEY_THRESHOLD_G, OLMCOLORKEY_THRESHOLD_B,
		OLMCOLORKEY_EDGE_THIN_AMOUNT, OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE,
		OLMCOLORKEY_EDGE_BLUR_AMOUNT, OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE,
		OLMCOLORKEY_EDGE_BLUR_DIRECTION, OLMCOLORKEY_NUMBER_OF_COLORS,
		OLMCOLORKEY_ENABLE_REPLACE,
	};
	for (size_t i = 0; i < sizeof(required) / sizeof(required[0]); ++i) {
		if (!params[required[i]]) return OLM_COLORKEY_REFUSAL("param-null");
	}
	AEFX_CLR_STRUCT(*info);
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	info->distance_step_x = static_cast<float>(in_data->downsample_x.den);
	info->distance_step_y = static_cast<float>(in_data->downsample_y.den);
#endif
	info->color_keep = params[OLMCOLORKEY_COLOR_KEEP]->u.bd.value;
	info->threshold = params[OLMCOLORKEY_THRESHOLD]->u.fs_d.value;
	info->premultiplied = params[OLMCOLORKEY_PREMULTIPLIED]->u.bd.value;
	info->color_space = params[OLMCOLORKEY_COLOR_SPACE]->u.pd.value;
	info->force_lower_precision = params[OLMCOLORKEY_FORCE_LOWER_PRECISION]->u.pd.value;
	info->per_color = params[OLMCOLORKEY_PER_COLOR]->u.bd.value;
	info->per_component = params[OLMCOLORKEY_PER_COMPONENT]->u.bd.value;
	info->threshold_r = params[OLMCOLORKEY_THRESHOLD_R]->u.fs_d.value;
	info->threshold_g = params[OLMCOLORKEY_THRESHOLD_G]->u.fs_d.value;
	info->threshold_b = params[OLMCOLORKEY_THRESHOLD_B]->u.fs_d.value;
	info->edge_thin_amount = params[OLMCOLORKEY_EDGE_THIN_AMOUNT]->u.sd.value;
	info->edge_thin_distance_type = params[OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE]->u.pd.value;
	info->edge_blur_amount = static_cast<float>(params[OLMCOLORKEY_EDGE_BLUR_AMOUNT]->u.fs_d.value);
	info->edge_blur_distance_type = params[OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE]->u.pd.value;
	// Values materialized by the public AE parameter surface use the native
	// owner lane.  Keep that provenance distinct from declared-record worker
	// fixtures, whose captured integer distance planes use different units.
	info->edge_blur_direction = params[OLMCOLORKEY_EDGE_BLUR_DIRECTION]->u.pd.value + 100;
	info->number_of_colors = params[OLMCOLORKEY_NUMBER_OF_COLORS]->u.sd.value;
	info->enable_replace = params[OLMCOLORKEY_ENABLE_REPLACE]->u.bd.value;
	if (info->number_of_colors < 0 || info->number_of_colors > OLMCOLORKEY_MAX_COLORS)
		return OLM_COLORKEY_REFUSAL("color-count");
	for (A_long i = 0; i < info->number_of_colors; ++i) {
		for (int offset = 0; offset < COLOR_PARAM_STRIDE; ++offset) {
			if (!params[ColorParamIndex(i, offset)]) return OLM_COLORKEY_REFUSAL("palette-null");
		}
	}

	PF_ColorParamSuite1 *cps = NULL;
	bool release_suite = false;
	PF_Err err = AcquireColorParamSuite(in_data, &cps, &release_suite);
	std::exception_ptr thrown;
	try {
		for (A_long i = 0; i < info->number_of_colors && !err; ++i) {
			PF_ParamDef *cp = params[ColorParamIndex(i, COLOR_OFFSET_COLOR)];
			info->colors8[i] = cp->u.cd.value;
			PF_PixelFloat fp = {0};
			err = cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref, cp, &fp);
			if (!err) info->colors[i] = fp;
			info->thresholds[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD)]->u.fs_d.value;
			info->thresholds_r[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_R)]->u.fs_d.value;
			info->thresholds_g[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_G)]->u.fs_d.value;
			info->thresholds_b[i] = params[ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_B)]->u.fs_d.value;
			info->use_color[i] = params[ColorParamIndex(i, COLOR_OFFSET_USE_COLOR)]->u.bd.value;
			info->use_replace_color[i] = params[ColorParamIndex(i, COLOR_OFFSET_USE_REPLACE)]->u.bd.value;
			PF_ParamDef *rp = params[ColorParamIndex(i, COLOR_OFFSET_REPLACE_COLOR)];
			PF_PixelFloat rep = {0};
			if (!err) err = cps->PF_GetFloatingPointColorFromColorDef(
			    in_data->effect_ref, rp, &rep);
			if (!err) info->replace_colors[i] = rep;
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	try {
		const PF_Err release_err = ReleaseColorParamSuite(in_data, release_suite);
		if (!err && !thrown && release_err) err = release_err;
	} catch (...) {
		if (!thrown) thrown = std::current_exception();
	}
	if (thrown) std::rethrow_exception(thrown);
	return err;
}

static PF_Err
CheckoutSmartInfo(PF_InData *in_data, OLMColorKeyInfo *info)
{
	if (!in_data || !info) return OLM_COLORKEY_REFUSAL("smart-checkout-inputs");
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	if (!in_data->inter.checkout_param || !in_data->inter.checkin_param)
		return OLM_COLORKEY_REFUSAL("smart-checkout-callback");
#endif
	AEFX_CLR_STRUCT(*info);
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	info->distance_step_x = static_cast<float>(in_data->downsample_x.den);
	info->distance_step_y = static_cast<float>(in_data->downsample_y.den);
#endif
	PF_ColorParamSuite1 *cps = NULL;
	bool release_suite = false;
	PF_Err err = AcquireColorParamSuite(in_data, &cps, &release_suite);
	std::exception_ptr thrown;
	try {
		auto fetch = [&](A_long index, auto consume) -> PF_Err {
			PF_ParamDef p;
			AEFX_CLR_STRUCT(p);
			PF_Err local_err = PF_CHECKOUT_PARAM(
			    in_data, index, in_data->current_time,
			    in_data->time_step, in_data->time_scale, &p);
			if (local_err) return local_err;
			std::exception_ptr consume_thrown;
			try { local_err = consume(p); }
			catch (...) { consume_thrown = std::current_exception(); }
			PF_Err checkin_err = PF_Err_NONE;
			try {
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
				PF_CHECKIN_PARAM(in_data, &p);
#else
				checkin_err = PF_CHECKIN_PARAM(in_data, &p);
#endif
			} catch (...) {
				if (!consume_thrown) consume_thrown = std::current_exception();
			}
			if (consume_thrown) std::rethrow_exception(consume_thrown);
			return local_err ? local_err : checkin_err;
		};
		auto get = [&](A_long index, auto consume) {
			if (!err) err = fetch(index, consume);
		};
		get(OLMCOLORKEY_COLOR_KEEP, [&](const PF_ParamDef &p){ info->color_keep = p.u.bd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_THRESHOLD, [&](const PF_ParamDef &p){ info->threshold = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_PREMULTIPLIED, [&](const PF_ParamDef &p){ info->premultiplied = p.u.bd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_COLOR_SPACE, [&](const PF_ParamDef &p){ info->color_space = p.u.pd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_FORCE_LOWER_PRECISION, [&](const PF_ParamDef &p){ info->force_lower_precision = p.u.pd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_PER_COLOR, [&](const PF_ParamDef &p){ info->per_color = p.u.bd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_PER_COMPONENT, [&](const PF_ParamDef &p){ info->per_component = p.u.bd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_THRESHOLD_R, [&](const PF_ParamDef &p){ info->threshold_r = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_THRESHOLD_G, [&](const PF_ParamDef &p){ info->threshold_g = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_THRESHOLD_B, [&](const PF_ParamDef &p){ info->threshold_b = p.u.fs_d.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_THIN_AMOUNT, [&](const PF_ParamDef &p){ info->edge_thin_amount = p.u.sd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_THIN_DISTANCE_TYPE, [&](const PF_ParamDef &p){ info->edge_thin_distance_type = p.u.pd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_BLUR_AMOUNT, [&](const PF_ParamDef &p){ info->edge_blur_amount = static_cast<float>(p.u.fs_d.value); return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_BLUR_DISTANCE_TYPE, [&](const PF_ParamDef &p){ info->edge_blur_distance_type = p.u.pd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_EDGE_BLUR_DIRECTION, [&](const PF_ParamDef &p){ info->edge_blur_direction = p.u.pd.value + 100; return PF_Err_NONE; });
		get(OLMCOLORKEY_NUMBER_OF_COLORS, [&](const PF_ParamDef &p){ info->number_of_colors = p.u.sd.value; return PF_Err_NONE; });
		get(OLMCOLORKEY_ENABLE_REPLACE, [&](const PF_ParamDef &p){ info->enable_replace = p.u.bd.value; return PF_Err_NONE; });
		if (!err && (info->number_of_colors < 0 ||
		             info->number_of_colors > OLMCOLORKEY_MAX_COLORS))
			err = OLM_COLORKEY_REFUSAL("color-count");
		for (A_long i = 0; i < info->number_of_colors && !err; ++i) {
			get(ColorParamIndex(i, COLOR_OFFSET_COLOR), [&](const PF_ParamDef &p){
				info->colors8[i] = p.u.cd.value;
				PF_PixelFloat value = {0};
				const PF_Err color_err = cps->PF_GetFloatingPointColorFromColorDef(
				    in_data->effect_ref, const_cast<PF_ParamDef *>(&p), &value);
				if (!color_err) info->colors[i] = value;
				return color_err;
			});
			get(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD), [&](const PF_ParamDef &p){ info->thresholds[i] = p.u.fs_d.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_R), [&](const PF_ParamDef &p){ info->thresholds_r[i] = p.u.fs_d.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_G), [&](const PF_ParamDef &p){ info->thresholds_g[i] = p.u.fs_d.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_THRESHOLD_B), [&](const PF_ParamDef &p){ info->thresholds_b[i] = p.u.fs_d.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_USE_COLOR), [&](const PF_ParamDef &p){ info->use_color[i] = p.u.bd.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_USE_REPLACE), [&](const PF_ParamDef &p){ info->use_replace_color[i] = p.u.bd.value; return PF_Err_NONE; });
			get(ColorParamIndex(i, COLOR_OFFSET_REPLACE_COLOR), [&](const PF_ParamDef &p){
				PF_PixelFloat value = {0};
				const PF_Err color_err = cps->PF_GetFloatingPointColorFromColorDef(
				    in_data->effect_ref, const_cast<PF_ParamDef *>(&p), &value);
				if (!color_err) info->replace_colors[i] = value;
				return color_err;
			});
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	try {
		const PF_Err release_err = ReleaseColorParamSuite(in_data, release_suite);
		if (!err && !thrown && release_err) err = release_err;
	} catch (...) {
		if (!thrown) thrown = std::current_exception();
	}
	if (thrown) std::rethrow_exception(thrown);
	return err;
}


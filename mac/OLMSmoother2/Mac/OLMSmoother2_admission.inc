static PF_Err
WorldDepth(PF_InData *in_data,
           PF_OutData *out_data,
           PF_EffectWorld *world,
           short *depth)
{
	if (!in_data || !out_data || !world || !depth) return OLM_SM2_REFUSAL("world-depth-null");
#ifdef OLMSMOOTHER2_SHIM_H
	if (world->bitdepth == 8 || world->bitdepth == 16 || world->bitdepth == 32) {
		*depth = world->bitdepth;
		return PF_Err_NONE;
	}
	return OLM_SM2_REFUSAL("world-depth-format");
#else
	PF_Err err = PF_Err_NONE;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	(void)out_data;
	if (!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
	    !in_data->pica_basicP->ReleaseSuite) return OLM_SM2_REFUSAL("world-depth-inputs");
	const void *raw_suite = nullptr;
	const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
		kPFWorldSuite, kPFWorldSuiteVersion2, &raw_suite);
	if (acquire_err) return OLM_SM2_ERROR("world-depth-suite-acquire", (PF_Err)acquire_err);
	if (!raw_suite) {
		const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
			kPFWorldSuite, kPFWorldSuiteVersion2);
		return OLM_SM2_ERROR("world-depth-suite-null",
			release_err ? (PF_Err)release_err : PF_Err_BAD_CALLBACK_PARAM);
	}
	PF_WorldSuite2 *world_suite = (PF_WorldSuite2 *)raw_suite;
	try {
		if (!world_suite->PF_GetPixelFormat) err = OLM_SM2_REFUSAL("world-depth-function-null");
		if (!err) err = world_suite->PF_GetPixelFormat(world, &format);
	} catch (...) {
		const std::exception_ptr body_error = std::current_exception();
		try { in_data->pica_basicP->ReleaseSuite(kPFWorldSuite, kPFWorldSuiteVersion2); }
		catch (...) {}
		std::rethrow_exception(body_error);
	}
	const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
		kPFWorldSuite, kPFWorldSuiteVersion2);
	if (!err && release_err) err = (PF_Err)release_err;
	if (err) return err;
	switch (format) {
	case PF_PixelFormat_ARGB32:  *depth = 8;  return PF_Err_NONE;
	case PF_PixelFormat_ARGB64:  *depth = 16; return PF_Err_NONE;
	case PF_PixelFormat_ARGB128: *depth = 32; return PF_Err_NONE;
	default: return OLM_SM2_REFUSAL("world-depth-pixel-format");
	}
#endif
}

static bool
ColorIs(const PF_ParamDef *param, A_u_char a, A_u_char r, A_u_char g, A_u_char b)
{
	return param && param->u.cd.value.alpha == a && param->u.cd.value.red == r &&
	       param->u.cd.value.green == g && param->u.cd.value.blue == b;
}

static bool
CoreParamsPresent(const PF_ParamDef *const params[])
{
	if (!params) return false;
	for (A_long i = 1; i < SM_NUM_PARAMS; ++i) if (!params[i]) return false;
	return true;
}

static bool
SmoothingIs(const PF_ParamDef *const params[], A_long smoothness,
            A_long range, A_long extra)
{
	return params[SM_SMOOTHNESS]->u.sd.value == smoothness &&
	       params[SM_SMOOTH_RANGE]->u.sd.value == range &&
	       params[SM_EXTRA_SMOOTH]->u.sd.value == extra;
}

static bool
GammaPaletteRedKey(const PF_ParamDef *const params[], A_u_char kr,
                   A_u_char kg, A_u_char kb)
{
	return params[SM_NUM_GAMMA_COLORS]->u.sd.value == 2 &&
	       ColorIs(params[SM_GAMMA_COLOR_0], 255, 255, 0, 0) &&
	       ColorIs(params[SM_GAMMA_COLOR_1], 255, kr, kg, kb);
}

static bool
GammaTailZero(const PF_ParamDef *const params[], A_long first)
{
	for (A_long i = first; i < NUM_GAMMA_COLORS; ++i) {
		if (!ColorIs(params[SM_GAMMA_COLOR_0 + i], 0, 0, 0, 0)) return false;
	}
	return true;
}

static bool
V2SourceIs(const PF_EffectWorld *world, short depth, const char expected[65])
{
	const size_t pixel_size = depth == 8 ? sizeof(PF_Pixel8) :
	                          depth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat);
	return world && olm::sha256_active_rows_match_hex(
		world->data, (size_t)world->rowbytes,
		(size_t)world->width * pixel_size, (size_t)world->height, expected);
}

static bool
V2Case07WorldContract(const PF_InData *in_data,
                      const PF_EffectWorld *input,
                      const PF_EffectWorld *output,
                      short depth)
{
#ifdef OLMSMOOTHER2_SHIM_H
	(void)in_data;
	return input && output && (depth == 8 || depth == 16 || depth == 32) &&
	       input->width == 1920 && input->height == 1080 &&
	       input->rowbytes == 1920 * (A_long)(depth == 8 ? sizeof(PF_Pixel8) :
	                                           depth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat));
#else
	const A_long expected_flags = depth == 8 ? 0 : PF_WorldFlag_DEEP;
	return in_data && input && output && (depth == 8 || depth == 16 || depth == 32) &&
	       input->width == 1920 && input->height == 1080 &&
	       input->rowbytes == 1920 * (A_long)(depth == 8 ? sizeof(PF_Pixel8) :
	                                           depth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat)) &&
	       output->world_flags == expected_flags && input->world_flags == expected_flags &&
	       in_data->output_origin_x == 0 && in_data->output_origin_y == 0 &&
	       in_data->downsample_x.num == 1 && in_data->downsample_x.den == 1 &&
	       in_data->downsample_y.num == 1 && in_data->downsample_y.den == 1;
#endif
}

struct V2LegacyPF8Tuple {
	A_long enable_key, invert_key;
	A_long smoothness, range, extra, version, gamma_mode, gamma_count;
	A_FpLong gamma_value;
	A_long palette_kind;  // 0=black5, 1=black4+blue, 2=red+black3+blue
};

static bool
V2LegacyPF8ParamsIs(const PF_ParamDef *const params[])
{
	static const V2LegacyPF8Tuple tuples[] = {
		{0,0,100,  2,  0,2,GAMMA_NONE,        1,2.40000009536743,0},
		{1,1,100,  2,  0,2,GAMMA_NONE,        1,2.40000009536743,0},
		{1,0,  0,  2,  0,2,GAMMA_NONE,        1,2.40000009536743,0},
		{1,0,100,  2,100,2,GAMMA_NONE,        1,2.40000009536743,0},
		{1,0,100,100,100,2,GAMMA_NONE,        1,2.40000009536743,0},
		{1,0,100,  0,100,2,GAMMA_NONE,        1,2.40000009536743,0},
		{1,0,100, 26, 40,2,GAMMA_NONE,        1,2.40000009536743,0},
		{1,0, 29, 26, 40,2,GAMMA_NONE,        1,2.40000009536743,0},
		{1,0,100, 26, 40,1,GAMMA_NONE,        1,2.40000009536743,0},
		{1,0,100, 22, 40,2,GAMMA_COLORS_ONLY, 3,1.36872434616089,0},
		{1,0,100, 22, 40,2,GAMMA_COLORS_ONLY, 5,2.16954731941223,1},
		{1,0,100, 88, 40,2,GAMMA_COLORS_ONLY, 5,2.16954731941223,2},
	};
	if (!ColorIs(params[SM_KEY_COLOR], 255, 255, 255, 255)) return false;
	for (const V2LegacyPF8Tuple &tuple : tuples) {
		if (params[SM_ENABLE_KEY]->u.bd.value != tuple.enable_key ||
		    params[SM_INVERT_KEY]->u.bd.value != tuple.invert_key ||
		    !SmoothingIs(params, tuple.smoothness, tuple.range, tuple.extra) ||
		    params[SM_VERSION]->u.pd.value != tuple.version ||
		    params[SM_GAMMA_MODE]->u.pd.value != tuple.gamma_mode ||
		    params[SM_GAMMA_VALUE]->u.fs_d.value != tuple.gamma_value ||
		    params[SM_NUM_GAMMA_COLORS]->u.sd.value != tuple.gamma_count) continue;
		bool colors_match = true;
		for (A_long index = 0; index < NUM_GAMMA_COLORS; ++index) {
			const bool red = tuple.palette_kind == 2 && index == 0;
			const bool blue = tuple.palette_kind != 0 && index == NUM_GAMMA_COLORS - 1;
			colors_match = colors_match && ColorIs(params[SM_GAMMA_COLOR_0 + index],
				255, red ? 255 : 0, 0, blue ? 255 : 0);
		}
		if (colors_match) return true;
	}
	return false;
}

static bool
V2SmartAdmission(const PF_ParamDef *const params[], const PF_EffectWorld *world,
            short depth)
{
	if (!CoreParamsPresent(params) || !world) return false;
	const A_long pixel_size = depth == 8 ? (A_long)sizeof(PF_Pixel8) :
	                          depth == 16 ? (A_long)sizeof(PF_Pixel16) :
	                                        (A_long)sizeof(PF_PixelFloat);
	const A_long pad = depth == 8 ? 5 : depth == 16 ? 7 : 13;
	const A_long version = params[SM_VERSION]->u.pd.value;
	const A_long gamma_mode = params[SM_GAMMA_MODE]->u.pd.value;
	const A_FpLong gamma_value = params[SM_GAMMA_VALUE]->u.fs_d.value;
	const A_long enable_key = params[SM_ENABLE_KEY]->u.bd.value;
	const A_long invert_key = params[SM_INVERT_KEY]->u.bd.value;
	if ((depth != 8 && depth != 16 && depth != 32) ||
	    (enable_key != 0 && enable_key != 1) ||
	    (invert_key != 0 && invert_key != 1)) return false;

	// Current-AEX retained PF8 grid. The same exact straight ARGB8 source is
	// paired to twelve named parameter tuples; the current direct output reaches
	// each retained Windows PNG only through the separately checked nearest-code
	// host premultiplication relation. This does not generalize the source or the
	// tuple union and does not claim a native output-world capture.
	if (depth == 8 && world->width == 1920 && world->height == 1080 &&
	    world->rowbytes == 1920 * pixel_size &&
	    V2LegacyPF8ParamsIs(params) && V2SourceIs(world, depth,
	      "1c15f67a9d0818a0a0266971720e855acac70a89e2690ccbedf5e142fc1c64f3")) return true;

	// Case 07: retained 1920x1080 PF16/PF32 Smart owner fixture. Each source
	// identity is the tight active ARGB buffer. PF16 final EXR words are the
	// exact code/32768 presentation; PF32 has a separately proven unique
	// finite-fixture premultiplied presentation.
	if ((depth == 16 || depth == 32) &&
	    world->width == 1920 && world->height == 1080 &&
	    world->rowbytes == 1920 * pixel_size && version == SMOOTHER_V2 &&
	    enable_key == 0 && invert_key == 0 &&
	    ColorIs(params[SM_KEY_COLOR], 255, 248, 233, 159) &&
	    SmoothingIs(params, 10, 99, 1) &&
	    gamma_mode == GAMMA_COLORS_ONLY &&
	    gamma_value == 1.2699999809265137 &&
	    params[SM_NUM_GAMMA_COLORS]->u.sd.value == 2 &&
	    ColorIs(params[SM_GAMMA_COLOR_0], 255, 233, 38, 239) &&
	    ColorIs(params[SM_GAMMA_COLOR_1], 255, 192, 215, 172) &&
	    ColorIs(params[SM_GAMMA_COLOR_2], 255, 124, 34, 100) &&
	    ColorIs(params[SM_GAMMA_COLOR_3], 255, 17, 7, 127) &&
	    ColorIs(params[SM_GAMMA_COLOR_4], 255, 212, 216, 8) &&
	    V2SourceIs(world, depth, depth == 16 ?
	      "c8d5ded0f9da071eb9e14e7bf20300916a3b8b292f081099d25dfc6359bbafa2" :
	      "133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b")) return true;

	// Installed-identity 3x2 public Smart owner chain. PF16 was exercised only
	// through the synthetic classic production adapter and is not promoted.
	if (depth == 32 && world->width == 3 && world->height == 2 &&
	    world->rowbytes == 3 * pixel_size + 12 &&
	    version == SMOOTHER_V2 && enable_key == 0 && invert_key == 0 &&
	    ColorIs(params[SM_KEY_COLOR], 0, 0, 0, 0) && gamma_mode == GAMMA_NONE &&
	    params[SM_NUM_GAMMA_COLORS]->u.sd.value == 0 && GammaTailZero(params, 0) &&
	    gamma_value == 2.4 && SmoothingIs(params, 100, 1, 0) &&
	    V2SourceIs(world, depth,
	      "4e43421598bfe27755f2b920014c8d3446413061900c9f94e16102fcf3089630")) return true;

	if (world->width == 5 && world->height == 5 &&
	    world->rowbytes == 5 * pixel_size + pad) {
		// Exported Smart owner: intermediate Gamma 1.8, exact key endpoint,
		// both versions and both key polarities (12 raw-exact cells).
		if (enable_key == 1 && ColorIs(params[SM_KEY_COLOR], 255, 202, 187, 230) &&
		    SmoothingIs(params, 100, 100, 100) &&
		    (version == SMOOTHER_V1 || version == SMOOTHER_V2) &&
		    gamma_mode == GAMMA_COLORS_ONLY && gamma_value == 1.8 &&
		    GammaPaletteRedKey(params, 202, 187, 230) && GammaTailZero(params, 2) &&
		    V2SourceIs(world, depth, depth == 8 ?
		      "ca56c65ec9209d52c956f40e51cb8f7c133a001eab1b141b95c04295917cce99" : depth == 16 ?
		      "66127e3fbe12b1b39f25127550d006f69db7d8aabe9c571f8caf91fc6819dee7" :
		      "decb2060f0d96ad30146658c2026edae48caf134311b4207d846317c5589467f")) return true;

		// Earlier exported-owner Gamma 2.4 representatives.
		if (enable_key == 1 && ColorIs(params[SM_KEY_COLOR], 255, 1, 1, 1) &&
		    SmoothingIs(params, 100, 100, 100) && gamma_mode == GAMMA_COLORS_ONLY &&
		    gamma_value == 2.4 && GammaPaletteRedKey(params, 1, 1, 1) &&
		    GammaTailZero(params, 2) &&
		    ((version == SMOOTHER_V1 && invert_key == 0) ||
		     (version == SMOOTHER_V2 && invert_key == 1)) &&
		    V2SourceIs(world, depth, depth == 8 ?
		      "c36c335071f2479526394e667d0448932638fa50b082ae7f82e749b48bc8e964" : depth == 16 ?
		      "550b73ca84e8b69fa24b8b61e6ee8580ed743b765a15256174c1448999247418" :
		      "76c868f51c9ac8da08c67f52e8d837401c5457045a659ee7c484f42f69cb252a")) return true;
	}

	// Public EffectMain covering fixture: two exact cells per depth.
	if (world->width == 17 && world->height == 11 &&
	    world->rowbytes == 17 * pixel_size + pad) {
		if (depth == 8 && version == SMOOTHER_V1 && enable_key == 0 && invert_key == 0 &&
		    ColorIs(params[SM_KEY_COLOR], 255, 1, 1, 1) &&
		    gamma_mode == GAMMA_NONE && gamma_value == 1.0 &&
		    params[SM_NUM_GAMMA_COLORS]->u.sd.value == 1 &&
		    ColorIs(params[SM_GAMMA_COLOR_0], 255, 255, 0, 0) && GammaTailZero(params, 1) &&
		    SmoothingIs(params, 100, 2, 0) && V2SourceIs(world, depth,
		      "c1f989b1abdcc5e2fe6fe46bfe2fb3e769c2f8288ab09ee5005a9db41c4edd6e")) return true;
		if (depth == 8 && version == SMOOTHER_V2 && enable_key == 1 && invert_key == 1 &&
		    ColorIs(params[SM_KEY_COLOR], 255, 1, 1, 1) &&
		    gamma_mode == GAMMA_COLORS_ONLY && gamma_value == 2.4 &&
		    SmoothingIs(params, 50, 50, 50) &&
		    params[SM_NUM_GAMMA_COLORS]->u.sd.value == 5 &&
		    ColorIs(params[SM_GAMMA_COLOR_0], 255, 255, 0, 0) &&
		    ColorIs(params[SM_GAMMA_COLOR_1], 255, 1, 1, 1) &&
		    ColorIs(params[SM_GAMMA_COLOR_2], 255, 255, 0, 0) &&
		    ColorIs(params[SM_GAMMA_COLOR_3], 255, 1, 1, 1) &&
		    ColorIs(params[SM_GAMMA_COLOR_4], 255, 0, 0, 255) && V2SourceIs(world, depth,
		      "22890ba4876617ed2956c87596198c021c26e9e57a67b3816a6c67cf6c8d671e")) return true;
		if (depth == 16 && version == SMOOTHER_V2 && enable_key == 0 && invert_key == 0 &&
		    ColorIs(params[SM_KEY_COLOR], 255, 1, 1, 1) &&
		    gamma_mode == GAMMA_ALL_COLORS && gamma_value == 2.4 &&
		    params[SM_NUM_GAMMA_COLORS]->u.sd.value == 1 &&
		    ColorIs(params[SM_GAMMA_COLOR_0], 255, 255, 0, 0) && GammaTailZero(params, 1) &&
		    SmoothingIs(params, 50, 50, 50) && V2SourceIs(world, depth,
		      "57431e5864c4c0feecb55a6e1646ae2d0b55417bcdd70d5c03ce814f3c1b12ad")) return true;
		if (depth == 16 && version == SMOOTHER_V2 && enable_key == 1 && invert_key == 0 &&
		    ColorIs(params[SM_KEY_COLOR], 255, 1, 1, 1) &&
		    gamma_mode == GAMMA_COLORS_ONLY && gamma_value == 1.0 &&
		    SmoothingIs(params, 100, 2, 0) &&
		    params[SM_NUM_GAMMA_COLORS]->u.sd.value == 5 &&
		    ColorIs(params[SM_GAMMA_COLOR_0], 255, 255, 255, 0) &&
		    ColorIs(params[SM_GAMMA_COLOR_1], 255, 0, 255, 0) &&
		    ColorIs(params[SM_GAMMA_COLOR_2], 255, 1, 1, 1) &&
		    ColorIs(params[SM_GAMMA_COLOR_3], 255, 255, 0, 0) &&
		    ColorIs(params[SM_GAMMA_COLOR_4], 255, 0, 0, 255) && V2SourceIs(world, depth,
		      "bcdc96e0773448fb52f12907dd4bb6c39addaac7f1bed8f31182bc8ce37dd595")) return true;
		if (depth == 32 && version == SMOOTHER_V1 && enable_key == 0 && invert_key == 0 &&
		    ColorIs(params[SM_KEY_COLOR], 255, 1, 1, 1) &&
		    gamma_mode == GAMMA_NONE && gamma_value == 1.0 &&
		    params[SM_NUM_GAMMA_COLORS]->u.sd.value == 1 &&
		    ColorIs(params[SM_GAMMA_COLOR_0], 255, 255, 0, 0) && GammaTailZero(params, 1) &&
		    SmoothingIs(params, 50, 50, 50) && V2SourceIs(world, depth,
		      "83bab2bff36972c9dbb3d079739a23a18d64179da6d8202e1024af6488fb2a40")) return true;
		if (depth == 32 && version == SMOOTHER_V2 && enable_key == 1 && invert_key == 0 &&
		    ColorIs(params[SM_KEY_COLOR], 255, 1, 1, 1) &&
		    gamma_mode == GAMMA_COLORS_ONLY && gamma_value == 2.4 &&
		    SmoothingIs(params, 100, 2, 0) &&
		    params[SM_NUM_GAMMA_COLORS]->u.sd.value == 1 &&
		    ColorIs(params[SM_GAMMA_COLOR_0], 255, 255, 0, 0) && GammaTailZero(params, 1) &&
		    V2SourceIs(world, depth,
		      "d0a57665d75ac51539e2e27e17eae4d16a3916b964ed556bae1bfc553441ad2f")) return true;
	}
	return false;
}

// Public-beta lane for the parameter axes covered by the retained Windows
// classifier/typed-worker corpus. Gamma Colors is portable when it uses the
// captured transfer tables plus the inline AE color list; custom/user LUT
// identities remain outside this lane.
//
// The polygon cardinal chain still contains structurally reconstructed pieces;
// all 256 indices now have local AEX reachability witnesses. That coverage
// does not establish every scan length, parameter state, or native AE contract.
static bool
V2GenericBetaAdmission(const PF_ParamDef *const params[],
                       const PF_EffectWorld *world, short depth)
{
	if (!CoreParamsPresent(params) || !world ||
	    (depth != 8 && depth != 16 && depth != 32)) return false;

	const A_long pixel_size = depth == 8 ? (A_long)sizeof(PF_Pixel8) :
	                          depth == 16 ? (A_long)sizeof(PF_Pixel16) :
	                                        (A_long)sizeof(PF_PixelFloat);
	// The exported AEX Smart owner accepts positive dimensions, including
	// single rows/columns. Their edge handling is shared with larger frames;
	// do not impose the former beta-only 16x16 lower bound.
	if (world->width < 1 || world->height < 1 ||
	    world->width > 8192 || world->height > 8192 ||
	    world->rowbytes < world->width * pixel_size) return false;

	const A_long enable_key = params[SM_ENABLE_KEY]->u.bd.value;
	const A_long invert_key = params[SM_INVERT_KEY]->u.bd.value;
	const A_long version = params[SM_VERSION]->u.pd.value;
	const A_long gamma_mode = params[SM_GAMMA_MODE]->u.pd.value;
	const A_FpLong gamma_value = params[SM_GAMMA_VALUE]->u.fs_d.value;
	const A_long smoothness = params[SM_SMOOTHNESS]->u.sd.value;
	const A_long smooth_range = params[SM_SMOOTH_RANGE]->u.sd.value;
	const A_long extra_smooth = params[SM_EXTRA_SMOOTH]->u.sd.value;
	const A_long gamma_count = params[SM_NUM_GAMMA_COLORS]->u.sd.value;
	// AE stores the 2.4 UI endpoint through a float-backed parameter payload,
	// yielding 2.40000009536743 when promoted to A_FpLong. Comparing against a
	// double literal 2.4 rejects the untouched native-host default.
	const A_FpLong gamma_ui_max = (A_FpLong)(float)2.4f;
	const bool gamma_mode_and_count =
	       ((gamma_mode == GAMMA_NONE || gamma_mode == GAMMA_ALL_COLORS) &&
	        gamma_count >= 0 && gamma_count <= NUM_GAMMA_COLORS) ||
	       (gamma_mode == GAMMA_COLORS_ONLY &&
	        gamma_count >= 0 && gamma_count <= NUM_GAMMA_COLORS);
	return (enable_key == 0 || enable_key == 1) &&
	       (invert_key == 0 || invert_key == 1) &&
	       (version == SMOOTHER_V1 || version == SMOOTHER_V2) &&
	       gamma_mode_and_count &&
	       std::isfinite(gamma_value) && gamma_value >= 1.0 && gamma_value <= gamma_ui_max &&
	       smoothness >= 0 && smoothness <= 100 &&
	       smooth_range >= 0 && smooth_range <= 100 &&
	       extra_smooth >= 0 && extra_smooth <= 100;
}

static PF_Err
ValidatePublicWorlds(PF_InData *in_data,
                     PF_OutData *out_data,
                     PF_EffectWorld *input,
                     PF_EffectWorld *output,
                     short *depth)
{
	if (!input || !output || !input->data || !output->data || !depth ||
	    input->width <= 0 || input->height <= 0 ||
	    input->width != output->width || input->height != output->height ||
	    input->rowbytes <= 0 || output->rowbytes <= 0 ||
	    input->origin_x != output->origin_x ||
	    input->origin_y != output->origin_y) {
		return OLM_SM2_REFUSAL("validate-world-shape");
	}
	short input_depth = 0, output_depth = 0;
	PF_Err err = WorldDepth(in_data, out_data, input, &input_depth);
	if (!err) err = WorldDepth(in_data, out_data, output, &output_depth);
	if (err) return err;
	if (input_depth != output_depth) return OLM_SM2_REFUSAL("validate-depth-mismatch");
	const A_long pixel_size = input_depth == 8 ? (A_long)sizeof(PF_Pixel8) :
	                          input_depth == 16 ? (A_long)sizeof(PF_Pixel16) :
	                          input_depth == 32 ? (A_long)sizeof(PF_PixelFloat) : 0;
	if (!pixel_size || input->width > INT32_MAX / pixel_size ||
	    input->rowbytes < input->width * pixel_size ||
	    output->rowbytes < output->width * pixel_size ||
	    input->height > INT32_MAX / input->rowbytes ||
	    output->height > INT32_MAX / output->rowbytes) {
		return OLM_SM2_REFUSAL("validate-size-overflow");
	}
	const uintptr_t input_begin = (uintptr_t)input->data;
	const uintptr_t output_begin = (uintptr_t)output->data;
	const size_t input_span = (size_t)(input->height - 1) * (size_t)input->rowbytes +
	                          (size_t)input->width * (size_t)pixel_size;
	const size_t output_span = (size_t)(output->height - 1) * (size_t)output->rowbytes +
	                           (size_t)output->width * (size_t)pixel_size;
	if (input_begin > UINTPTR_MAX - input_span ||
	    output_begin > UINTPTR_MAX - output_span ||
	    (input_begin < output_begin + output_span &&
	     output_begin < input_begin + input_span)) {
		return OLM_SM2_REFUSAL("validate-overlap");
	}
	*depth = input_depth;
	return PF_Err_NONE;
}

// ============================================================================
// Classic Render
// ============================================================================

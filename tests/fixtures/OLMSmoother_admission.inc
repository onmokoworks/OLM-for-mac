// Historical source-bound admission fixtures, retained for digest audits only.
// Production PF8/PF16 admission superseded these branches before C02.
static bool
ColorIs(const PF_ParamDef *param, A_u_char a, A_u_char r, A_u_char g, A_u_char b)
{
	return param && param->u.cd.value.alpha == a && param->u.cd.value.red == r &&
	       param->u.cd.value.green == g && param->u.cd.value.blue == b;
}

static bool
V1SourceIs(const PF_EffectWorld *world, short depth, const char expected[65])
{
	const size_t pixel_size = depth == 8 ? sizeof(PF_Pixel8) : sizeof(PF_Pixel16);
	return world && olm::sha256_active_rows_match_hex(
		world->data, (size_t)world->rowbytes,
		(size_t)world->width * pixel_size, (size_t)world->height, expected);
}

static bool
V1ClassicAdmission(const PF_ParamDef *const params[], const PF_EffectWorld *world, short depth)
{
	if (!params || !world || !params[SM_USE_KEY] || !params[SM_KEY_COLOR] ||
	    !params[SM_TOLERANCE]) return false;
	const A_long use_key = params[SM_USE_KEY]->u.bd.value;
	const A_long tolerance = params[SM_TOLERANCE]->u.sd.value;
	if (use_key != 0 && use_key != 1) return false;
	if (tolerance < 0 || tolerance > 255) return false;

	// Public beta lane: both the typed key-mask pass and the interpolation kernel
	// are geometry- and source-independent. Open PF8/PF16 for either key polarity;
	// the retained tuples below remain as an auditable record of the Windows
	// witnesses that established the keyed behavior.
	if (depth == 8 || depth == 16) return true;

	// Canonical full-frame public PF8 closure.
	if (depth == 8 && world->width == 960 && world->height == 540 &&
	    world->rowbytes == 960 * (A_long)sizeof(PF_Pixel8) && use_key == 0 &&
	    tolerance == 6 && ColorIs(params[SM_KEY_COLOR], 255, 255, 255, 255) &&
	    V1SourceIs(world, depth,
	      "d0851831db13ec2452b9ac20245f8d308d09dad1cf32984b91d4fb950d5945cd")) {
		return true;
	}

	// Three independent exported-owner 7x5 fixture families cover both typed
	// lanes, both key polarities, five public tolerance values, padding, and
	// colored/fractional-alpha sources.
	if ((depth == 8 || depth == 16) && world->width == 7 && world->height == 5 &&
	    world->rowbytes == 7 * (depth == 8 ? (A_long)sizeof(PF_Pixel8)
	                                      : (A_long)sizeof(PF_Pixel16)) + 8 &&
	    ColorIs(params[SM_KEY_COLOR], 255, 202, 187, 230)) {
		const bool checker = V1SourceIs(world, depth, depth == 8 ?
		  "86bbf709af011be19543e165d3e636283f29d4d7189101718ce9aabb9295a56b" :
		  "63676c82d06b6b7a5542ec04aa6d9aa903f23eda582121cf287cd2dc9ade006c");
		const bool colored = V1SourceIs(world, depth, depth == 8 ?
		  "460efe22ab70b9f168464df2c5ee2c924e556d09afd8d8ddcdc58328ad71b1ce" :
		  "9d0ab1b7cdcea3d5edc62aa4adbfae9d9e107639b5514ef265cd91d0e7d06fe0");
		const bool ramp = V1SourceIs(world, depth, depth == 8 ?
		  "59c23331927b5c90bbad8bb5e8e0c7742e93e1cc38cf6600e94665b1e3b9cf98" :
		  "1941a4ca2263d87a0021232df8ffae13babc399e2669128d78602bbf1da8821b");
		const bool practical_control = depth == 16 && V1SourceIs(world, depth,
		  "9b17bb75ab3f845aa49b61025160322a75cb592918dda3b5effb367b2ebd6e5b");
		if (checker && (tolerance == 0 || tolerance == 1 || tolerance == 6 ||
		                tolerance == 127 || tolerance == 255)) return true;
		if (colored && (tolerance == 0 || tolerance == 6 ||
		                tolerance == 127 || tolerance == 255)) return true;
		if (ramp && (tolerance == 0 || tolerance == 1 || tolerance == 6 ||
		             tolerance == 127 || tolerance == 255)) return true;
		if (practical_control && (tolerance == 6 || tolerance == 127)) return true;
	}

	// Practical PF16 owner closure and the earlier complete 5x3 Color Key
	// session. Keep these cells explicit instead of generalizing geometry.
	if (depth == 16 && world->width == 64 && world->height == 36 &&
	    world->rowbytes == 64 * (A_long)sizeof(PF_Pixel16) + 32 &&
	    ColorIs(params[SM_KEY_COLOR], 255, 202, 187, 230) &&
	    (tolerance == 6 || tolerance == 127) &&
	    V1SourceIs(world, depth,
	      "6487e12e6f63fb72ef6f0726064e9e7bfe9f472c76885c2ae0c4be628c887f83")) {
		return true;
	}
	if (depth == 16 && world->width == 5 && world->height == 3 &&
	    world->rowbytes == 48 && use_key == 1 && tolerance == 6 &&
	    ColorIs(params[SM_KEY_COLOR], 255, 202, 187, 230) &&
	    (V1SourceIs(world, depth,
	       "79a69ffb49caaf0d95b72096a51871c42b3e69203c033466f63c74b10757f001") ||
	     V1SourceIs(world, depth,
	       "18df1e2648e8a4f25f633f90143c61c5b58fd7e00bfd3bd02013c65947122749"))) {
		return true;
	}
	return false;
}

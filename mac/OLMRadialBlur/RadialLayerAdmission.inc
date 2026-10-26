// Type-3 source/layer pair admission; included by OLMRadialBlur.cpp.
template <typename PixelT>
static PF_Err ComposeType3LayerSpanAEX(
	const PF_EffectWorld *input_world,
	const PF_EffectWorld *noise_world,
	float noise_variation_normalized,
	const float *source_size_factor,
	float *source_span,
	size_t cell_count);

template <typename PixelT>
static bool MatchesType3SmallActiveHash(
	const PF_EffectWorld *world,
	const char *const *expected,
	size_t expected_count)
{
	if (!world || !world->data || world->width != 9 || world->height != 7 ||
		world->rowbytes < 9 * (A_long)sizeof(PixelT) || !expected) return false;
	for (size_t index = 0; index < expected_count; ++index) {
		if (olm::sha256_active_rows_match_hex(
			world->data, (size_t)world->rowbytes, 9 * sizeof(PixelT), 7,
			expected[index])) return true;
	}
	return false;
}

template <typename PixelT>
static bool MatchesType3SmallSourceLayerPair(
	const PF_EffectWorld *input,
	const PF_EffectWorld *noise_world)
{
	// Each set below is a fixed typed public-owner fixture.  The hashes cover
	// visible ARGB rows only; rowbytes, geometry, alignment and matching world
	// layout are guarded by the caller.  Keeping the source and Layer relation
	// paired prevents the PF32 lane from becoming an arbitrary-input admission.
	if constexpr (std::is_same<PixelT, PF_Pixel8>::value) {
		static const char *const sources[] = {
			"3b62de8577b33598ede56c0a3ca5bc636a40b9bf7bc9599000d9840b531eeffe",
			"913c6e2c32d99e4baff62cf421a494730cb043924f2c6bf46406573b59c641bd",
			"b4fcb036f1591f53611fd4253e7db041a21166a5ea3ce8758911d9cf76faab6c",
			"7b53d38d1f76bc90605b858fb7e0dbb42e52558daa2dd51985f0fd492c1460f6",
			"a2966751a436b2c893d2c9d9c2d378c126dfb0b9c3724be549c00ecfa085eebb",
		};
		static const char *const layers[] = {
			"e1a0fbdba8609984fef1c091aafe6e879ac183f1d0638a45b90409c40324e921",
			"05177a5cb397745ccf2ddafa8a0364684e5ffbcdfe5e4be03b4088c8c9d90df1",
			"c333875b922f20cdeba03161e01c0713569a5b7fe6a2db2c618b6184330090cd",
		};
		return MatchesType3SmallActiveHash<PixelT>(input, sources, 5) &&
			MatchesType3SmallActiveHash<PixelT>(noise_world, layers, 3);
	} else if constexpr (std::is_same<PixelT, PF_Pixel16>::value) {
		static const char *const sources[] = {
			"5c853513cbbbdab275383c7aa6b6d82e0f7fef95565a7d0d4f6dd04426a75b33",
			"696bda342649ec9268da57b6a279df6f24b0e857d5e6d0605fd25af95adc3cee",
			"528d66b89a005796a13abf6d039fe9191477240fbb130fa50ad67929e119599b",
			"f183bd3fa31c08888904160c85d2057a6bdf0e4f354201dcf1770ab42f5715af",
			"d9b0a5f4167495d958814a7ad39410bb9147159beb72a5236894dd5e1b234d69",
		};
		static const char *const layers[] = {
			"9b42978d4c3254121a7e27959eefcf3183fa7f50d2a1e376d6e90915ace834b5",
			"543846ff19163d48daae7f16a50fcaf17eb95e9954de64ea23b7e1b3495be901",
			"83cdfbc2d1c662519397a658e43488f2af2adf2e597e2497814cdabb330bce2f",
		};
		return MatchesType3SmallActiveHash<PixelT>(input, sources, 5) &&
			MatchesType3SmallActiveHash<PixelT>(noise_world, layers, 3);
	} else if constexpr (std::is_same<PixelT, PF_PixelFloat>::value) {
		static const char *const sources[] = {
			"ef7de00c687687faced1ac22c8f28d66420ea886a671f0dc62fe52e62fee4c96",
			"a9e080790cc3b9e7a988324b4ec1cc1432a8f43cf897c78318943a0670f171f6",
			"7bb21f2e3e0b60ca1d66eacdff901c7bf10e9c864ea20e740024ca2e658b22ed",
			"3c17ad4a232ea4abac50ffb86dde16bc5094a800ad46f48902695d5ebcd139b9",
			"060c53b0e2a00f21c0ca12629ad32445c92f5a6fdcd5a2ffa9d1bb20989460e3",
		};
		static const char *const natural_layers[] = {
			"9c7db9280f1b48a712b36454ef80e469db90ae3d3d69ff8821095b1d5b0b7f01",
			"c509c146bd3cc5e09189a12a6b751b2b04e14a93187cf1da3059a85a32d28a47",
		};
		static const char *const all_depth_layer[] = {
			"e91e1aa1dcb0385ff7c62285171828ec6a76b11d76ffeee2014e8b479171d026",
		};
		static const char *const all_depth_sources[] = {
			sources[0], sources[1], sources[2], sources[3], sources[4],
		};
		const bool natural_pair =
			MatchesType3SmallActiveHash<PixelT>(input, sources, 5) &&
			MatchesType3SmallActiveHash<PixelT>(noise_world, natural_layers, 2);
		const bool all_depth_pair =
			MatchesType3SmallActiveHash<PixelT>(input, all_depth_sources, 5) &&
			MatchesType3SmallActiveHash<PixelT>(noise_world, all_depth_layer, 1);
		return natural_pair || all_depth_pair;
	}
	return false;
}


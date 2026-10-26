// Included by OLMColorKey.cpp; preserves the single translation unit.
static PF_Err
RenderWorldDirect(PF_EffectWorld *input, PF_EffectWorld *output,
	              const OLMColorKeyInfo &info, short bitdepth,
                  A_long classify_width = -1, A_long classify_height = -1)
{
	if (bitdepth == 8) {
		return RenderTyped<PF_Pixel8>(input, output, info, classify_width, classify_height);
	} else if (bitdepth == 16) {
		return RenderTyped<PF_Pixel16>(input, output, info, classify_width, classify_height);
	} else if (bitdepth == 32) {
		return RenderTyped<PF_PixelFloat>(input, output, info, classify_width, classify_height);
	}
	return OLM_COLORKEY_REFUSAL("render-bitdepth");
}

static bool CheckedPayloadBytes(const PF_EffectWorld *world, size_t *bytes)
{
	if (!world || !bytes || world->rowbytes <= 0 || world->height <= 0) return false;
	const size_t rowbytes = (size_t)world->rowbytes;
	const size_t height = (size_t)world->height;
	if (height > std::numeric_limits<size_t>::max() / rowbytes) return false;
	*bytes = rowbytes * height;
	return true;
}

static bool DisjointPayloads(const PF_EffectWorld *input, const PF_EffectWorld *output)
{
	size_t input_bytes = 0, output_bytes = 0;
	if (!input || !output || !input->data || !output->data ||
	    !CheckedPayloadBytes(input, &input_bytes) ||
	    !CheckedPayloadBytes(output, &output_bytes)) return false;
	const uintptr_t input_begin = reinterpret_cast<uintptr_t>(input->data);
	const uintptr_t output_begin = reinterpret_cast<uintptr_t>(output->data);
	if (input_begin > std::numeric_limits<uintptr_t>::max() - input_bytes ||
	    output_begin > std::numeric_limits<uintptr_t>::max() - output_bytes) return false;
	const uintptr_t input_end = input_begin + input_bytes;
	const uintptr_t output_end = output_begin + output_bytes;
	return input_end <= output_begin || output_end <= input_begin;
}

template <typename PixelT>
static bool IsPublicAdmission(const PF_EffectWorld *input,
	                          const PF_EffectWorld *output,
	                          const OLMColorKeyInfo &info)
{
	const size_t pixel_bytes = sizeof(PixelT);
	const bool pixel_local =
	    info.edge_thin_amount == 0.0 && info.edge_blur_amount == 0.0;
	if (!input || !output || !input->data || !output->data ||
	    input->width <= 0 || input->height <= 0 ||
	    output->width <= 0 || output->height <= 0 ||
	    (size_t)input->width > std::numeric_limits<size_t>::max() / pixel_bytes ||
	    (size_t)output->width > std::numeric_limits<size_t>::max() / pixel_bytes ||
	    (size_t)input->height > std::numeric_limits<size_t>::max() /
	        (size_t)input->width ||
	    (size_t)input->width * (size_t)input->height >
	        std::numeric_limits<size_t>::max() / sizeof(int) ||
	    (size_t)output->height > std::numeric_limits<size_t>::max() /
	        (size_t)output->width ||
	    (size_t)output->width * (size_t)output->height >
	        std::numeric_limits<size_t>::max() / sizeof(int) ||
	    input->rowbytes <= 0 || output->rowbytes <= 0 ||
	    (size_t)input->rowbytes < (size_t)input->width * pixel_bytes ||
	    (size_t)output->rowbytes < (size_t)output->width * pixel_bytes ||
	    !DisjointPayloads(input, output)) return false;
	if (pixel_local) {
		const int64_t input_left = WorldOriginX(input);
		const int64_t input_top = WorldOriginY(input);
		const int64_t input_right = input_left + input->width;
		const int64_t input_bottom = input_top + input->height;
		const int64_t output_left = WorldOriginX(output);
		const int64_t output_top = WorldOriginY(output);
		const int64_t output_right = output_left + output->width;
		const int64_t output_bottom = output_top + output->height;
		return output_left >= input_left && output_top >= input_top &&
		       output_right <= input_right && output_bottom <= input_bottom;
	}
	if (input->width != output->width || input->height != output->height)
		return false;
#ifndef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	if (input->extent_hint.left != 0 || input->extent_hint.top != 0 ||
	    input->extent_hint.right != input->width ||
	    input->extent_hint.bottom != input->height ||
	    output->extent_hint.left != 0 || output->extent_hint.top != 0 ||
	    output->extent_hint.right != output->width ||
	    output->extent_hint.bottom != output->height ||
	    input->origin_x != 0 || input->origin_y != 0 ||
	    output->origin_x != 0 || output->origin_y != 0) return false;
#endif
	// Pixel-local keying and replacement do not depend on a captured source or
	// geometry. Admit arbitrary full-frame worlds when no neighborhood operation
	// is requested.
	// Edge Thin's distance transforms operate only on the generated matte and
	// are geometry-independent. Promote the visible UI range while keeping Edge
	// Blur's captured geometry/curve quirks on the bounded lane below.
	if (info.edge_blur_amount == 0.0 &&
	    info.edge_thin_amount >= -4000.0 && info.edge_thin_amount <= 4000.0 &&
	    info.edge_thin_distance_type >= 1 && info.edge_thin_distance_type <= 3) {
		return true;
	}
	if (IsGenericEdgeBlurTuple(info)) return true;
	if (IsGenericEdgeCompositionTuple(info)) return true;
	if ((size_t)input->rowbytes != (size_t)input->width * pixel_bytes + 8 ||
	    (size_t)output->rowbytes != (size_t)output->width * pixel_bytes + 8) return false;
	if (IsBoundedLab76NativeTuple<PixelT>(input, output, info)) return true;
	if (input->width == 11 && input->height == 7 &&
	    IsBoundedToggleInfo(info) && IsBoundedToggleSource<PixelT>(input))
		return true;
	return IsBoundedEdgeInfo(info, input->width, input->height) &&
	       IsBoundedEdgeSource<PixelT>(input);
}

static bool BoundedInDataGeometry(const PF_InData *in_data, bool require_zero_origin)
{
	if (!in_data) return false;
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	return true;
#else
	return (!require_zero_origin ||
	        (in_data->output_origin_x == 0 && in_data->output_origin_y == 0)) &&
	       in_data->downsample_x.num > 0 &&
	       in_data->downsample_x.den >= static_cast<A_u_long>(in_data->downsample_x.num) &&
	       in_data->downsample_y.num > 0 &&
	       in_data->downsample_y.den >= static_cast<A_u_long>(in_data->downsample_y.num);
#endif
}

struct ColorKeyPreparedRender {
	std::vector<std::uint8_t> input_storage;
	std::vector<std::uint8_t> output_storage;
	PF_EffectWorld input_world;
	PF_EffectWorld output_world;
	size_t active_row_bytes;
};

static PF_Err
PrepareRenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
	               const OLMColorKeyInfo &info, short bitdepth,
	               ColorKeyPreparedRender *prepared)
{
	if (!prepared) return OLM_COLORKEY_REFUSAL("prepared-null");
	A_long pixel_bytes = 0;
	bool admitted = false;
	if (bitdepth == 8) {
		pixel_bytes = (A_long)sizeof(PF_Pixel8);
		admitted = IsPublicAdmission<PF_Pixel8>(input, output, info);
	} else if (bitdepth == 16) {
		pixel_bytes = (A_long)sizeof(PF_Pixel16);
		admitted = IsPublicAdmission<PF_Pixel16>(input, output, info);
	} else if (bitdepth == 32) {
		pixel_bytes = (A_long)sizeof(PF_PixelFloat);
		admitted = IsPublicAdmission<PF_PixelFloat>(input, output, info);
	} else {
		return OLM_COLORKEY_REFUSAL("prepared-bitdepth");
	}
	if (!admitted) return OLM_COLORKEY_REFUSAL("public-admission");

	size_t input_bytes = 0, output_bytes = 0;
	if (!CheckedPayloadBytes(input, &input_bytes) ||
	    !CheckedPayloadBytes(output, &output_bytes)) return OLM_COLORKEY_REFUSAL("prepared-span");
	prepared->input_storage.resize(input_bytes);
	prepared->output_storage.assign(output_bytes, 0);
	prepared->active_row_bytes = (size_t)output->width * (size_t)pixel_bytes;
	for (A_long y = 0; y < input->height; ++y) {
		std::memcpy(prepared->input_storage.data() + (size_t)y * (size_t)input->rowbytes,
		            reinterpret_cast<const std::uint8_t *>(input->data) +
		                (size_t)y * (size_t)input->rowbytes,
		            (size_t)input->rowbytes);
	}
	prepared->input_world = *input;
	prepared->output_world = *output;
	prepared->input_world.data = reinterpret_cast<PF_PixelPtr>(prepared->input_storage.data());
	prepared->output_world.data = reinterpret_cast<PF_PixelPtr>(prepared->output_storage.data());
	return RenderWorldDirect(&prepared->input_world, &prepared->output_world, info, bitdepth);
}

// The original Smart workers (0x9000/0x94b0/0x9960) allocate their
// neighborhood worlds at input size. Iterate uses local coordinates and the
// output extent; 0x113c0/0x113f0/0x11420 address rows without world origins.
// Keep this contract separate from the historical Classic ROI path.
static PF_Err
PrepareSmartRenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
                        const OLMColorKeyInfo &info, short bitdepth,
                        ColorKeyPreparedRender *prepared)
{
    if (!input || !output || !DisjointPayloads(input, output) ||
        output->width <= 0 || output->height <= 0 ||
        output->width > input->width || output->height > input->height)
        return OLM_COLORKEY_REFUSAL("smart-world-dimensions");
    const A_long pixel_bytes = bitdepth == 8 ? sizeof(PF_Pixel8) :
        bitdepth == 16 ? sizeof(PF_Pixel16) : sizeof(PF_PixelFloat);
    if (output->rowbytes <= 0 ||
        (size_t)output->rowbytes < (size_t)output->width * pixel_bytes)
        return OLM_COLORKEY_REFUSAL("smart-output-stride");
    PF_EffectWorld local_input = *input;
    PF_EffectWorld local_output = *output;
#if !defined(OLMCOLORKEY_HOSTLESS_RENDER_HARNESS) || defined(OLMCOLORKEY_HOSTLESS_WORLD_HAS_ORIGIN)
    local_input.origin_x = local_input.origin_y = 0;
    local_output.origin_x = local_output.origin_y = 0;
#endif
    local_input.extent_hint = {0, 0, input->width, input->height};
    local_output.width = input->width;
    local_output.height = input->height;
    local_output.rowbytes = input->rowbytes;
    local_output.extent_hint = local_input.extent_hint;
    size_t size = 0;
    if (!CheckedPayloadBytes(&local_input, &size))
        return OLM_COLORKEY_REFUSAL("smart-input-span");
    // A full-size destination prevents the original raw neighborhood writer
    // from overrunning a negotiated output. Only delivered rows are committed.
    std::vector<std::uint8_t> storage(size, 0);
    local_output.data = reinterpret_cast<PF_PixelPtr>(storage.data());
    bool admitted = bitdepth == 8 ? IsPublicAdmission<PF_Pixel8>(&local_input, &local_output, info) :
        bitdepth == 16 ? IsPublicAdmission<PF_Pixel16>(&local_input, &local_output, info) :
        bitdepth == 32 && IsPublicAdmission<PF_PixelFloat>(&local_input, &local_output, info);
    if (!admitted) return OLM_COLORKEY_REFUSAL("smart-public-admission");
    prepared->input_storage.resize(size);
    std::memcpy(prepared->input_storage.data(), input->data, size);
    prepared->output_storage = std::move(storage);
    prepared->input_world = local_input;
    prepared->output_world = local_output;
    prepared->input_world.data = reinterpret_cast<PF_PixelPtr>(prepared->input_storage.data());
    prepared->output_world.data = reinterpret_cast<PF_PixelPtr>(prepared->output_storage.data());
    prepared->active_row_bytes = (size_t)output->width * pixel_bytes;
    return RenderWorldDirect(&prepared->input_world, &prepared->output_world,
                             info, bitdepth, output->width, output->height);
}

static void CommitPreparedRender(const ColorKeyPreparedRender &prepared,
	                             PF_EffectWorld *output)
{
	for (A_long y = 0; y < output->height; ++y) {
		std::memcpy(reinterpret_cast<std::uint8_t *>(output->data) +
		                (size_t)y * (size_t)output->rowbytes,
		            prepared.output_storage.data() +
		                (size_t)y * (size_t)prepared.output_world.rowbytes,
		            prepared.active_row_bytes);
	}
}

static PF_Err
RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output,
	        const OLMColorKeyInfo &info, short bitdepth)
{
	ColorKeyPreparedRender prepared;
	const PF_Err err = PrepareRenderWorld(input, output, info, bitdepth, &prepared);
	if (err) return err;
	CommitPreparedRender(prepared, output);
	return PF_Err_NONE;
}

static PF_Err GetWorldDepths(PF_InData *in_data,
	                         PF_EffectWorld *input,
	                         PF_EffectWorld *output,
	                         short *depth)
{
	if (!in_data || !input || !output || !depth) return OLM_COLORKEY_REFUSAL("depth-inputs");
	PF_PixelFormat input_format = PF_PixelFormat_INVALID;
	PF_PixelFormat output_format = PF_PixelFormat_INVALID;
#ifdef OLMCOLORKEY_HOSTLESS_RENDER_HARNESS
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite(
	    in_data, kPFWorldSuite, kPFWorldSuiteVersion2, NULL);
	PF_Err err = world_suite->PF_GetPixelFormat(input, &input_format);
	if (!err) err = world_suite->PF_GetPixelFormat(output, &output_format);
#else
	if (!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
	    !in_data->pica_basicP->ReleaseSuite) return OLM_COLORKEY_REFUSAL("world-suite-basic");
	const void *raw_suite = NULL;
	const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
	    kPFWorldSuite, kPFWorldSuiteVersion2, &raw_suite);
	if (acquire_err) return (PF_Err)acquire_err;
	PF_Err err = PF_Err_NONE;
	std::exception_ptr thrown;
	try {
		if (!raw_suite) err = OLM_COLORKEY_REFUSAL("world-suite-null");
		PF_WorldSuite2 *world_suite = (PF_WorldSuite2 *)raw_suite;
		if (!err && !world_suite->PF_GetPixelFormat) err = OLM_COLORKEY_REFUSAL("world-suite-callback");
		if (!err) err = world_suite->PF_GetPixelFormat(input, &input_format);
		if (!err) err = world_suite->PF_GetPixelFormat(output, &output_format);
	} catch (...) {
		thrown = std::current_exception();
	}
	try {
		const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
		    kPFWorldSuite, kPFWorldSuiteVersion2);
		if (!err && !thrown && release_err) err = (PF_Err)release_err;
	} catch (...) {
		if (!thrown) thrown = std::current_exception();
	}
	if (thrown) std::rethrow_exception(thrown);
#endif
	if (err || input_format != output_format) return err ? err : OLM_COLORKEY_REFUSAL("world-format-mismatch");
	switch (input_format) {
	case PF_PixelFormat_ARGB32: *depth = 8; return PF_Err_NONE;
	case PF_PixelFormat_ARGB64: *depth = 16; return PF_Err_NONE;
	case PF_PixelFormat_ARGB128: *depth = 32; return PF_Err_NONE;
	default: return OLM_COLORKEY_REFUSAL("world-bitdepth");
	}
}

static bool ClassicWorldsMatch(const PF_EffectWorld *input,
	                           const PF_EffectWorld *output,
	                           PF_PixelFormat input_format,
	                           PF_PixelFormat output_format)
{
	if (!input || !output || !input->data || !output->data ||
	    input_format != output_format ||
	    input->width <= 0 || input->height <= 0 ||
	    input->width != output->width || input->height != output->height ||
	    input->rowbytes <= 0 || output->rowbytes <= 0) {
		return false;
	}
	A_long pixel_bytes = 0;
	switch (input_format) {
	case PF_PixelFormat_ARGB32: pixel_bytes = (A_long)sizeof(PF_Pixel8); break;
	case PF_PixelFormat_ARGB64: pixel_bytes = (A_long)sizeof(PF_Pixel16); break;
	case PF_PixelFormat_ARGB128: pixel_bytes = (A_long)sizeof(PF_PixelFloat); break;
	default: return false;
	}
	return input->rowbytes == input->width * pixel_bytes + 8 &&
	       output->rowbytes == output->width * pixel_bytes + 8 &&
	       DisjointPayloads(input, output);
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	if (!in_data || !out_data || !params || !params[OLMCOLORKEY_INPUT] || !output) {
		return OLM_COLORKEY_REFUSAL("render-inputs");
	}
	PF_Err err = PF_Err_NONE;
	OLMColorKeyInfo info;
	ERR(CheckoutInfo(in_data, params, &info));
	if (err) return err;
	if (!BoundedInDataGeometry(
	        in_data, info.edge_thin_amount != 0.0 || info.edge_blur_amount != 0.0))
		return OLM_COLORKEY_REFUSAL("render-geometry");
	PF_EffectWorld *input = &params[OLMCOLORKEY_INPUT]->u.ld;
	short bitdepth = 0;
	(void)out_data;
	ERR(GetWorldDepths(in_data, input, output, &bitdepth));
	if (err) return err;
	ERR(RenderWorld(&params[OLMCOLORKEY_INPUT]->u.ld, output, info, bitdepth));
	return err;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
	    !extra->cb->checkout_layer || !BoundedInDataGeometry(in_data, false))
		return OLM_COLORKEY_REFUSAL("prerender-inputs");
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;
	AEFX_CLR_STRUCT(in_result);

	req.preserve_rgb_of_zero_alpha = FALSE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMCOLORKEY_INPUT, OLMCOLORKEY_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));

	if (!err) {
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
	}
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *, PF_SmartRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->cb ||
	    !extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
	    !extra->cb->checkin_layer_pixels || !BoundedInDataGeometry(in_data, false))
		return OLM_COLORKEY_REFUSAL("smartrender-inputs");
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	bool layer_checked_out = false;
	std::exception_ptr thrown;
	ColorKeyPreparedRender prepared;
	bool prepared_ok = false;
	try {
		err = extra->cb->checkout_layer_pixels(
		    in_data->effect_ref, OLMCOLORKEY_INPUT, &input_world);
		layer_checked_out = err == PF_Err_NONE;
#if !defined(AE_OS_WIN)
		if (!err && input_world) {
			err = CapturePixelFloatEntryIfRequested(input_world, extra->input->bitdepth);
		}
#endif
		if (!err && !input_world) err = OLM_COLORKEY_REFUSAL("smart-input-null");
		if (!err) err = extra->cb->checkout_output(in_data->effect_ref, &output_world);
		if (!err && !output_world) err = OLM_COLORKEY_REFUSAL("smart-output-null");
		short world_depth = 0;
		if (!err) err = GetWorldDepths(in_data, input_world, output_world, &world_depth);
		if (!err && world_depth != extra->input->bitdepth) err = OLM_COLORKEY_REFUSAL("smart-depth");
		OLMColorKeyInfo info;
		if (!err) err = CheckoutSmartInfo(in_data, &info);
		if (!err) {
			err = PrepareSmartRenderWorld(input_world, output_world, info,
			                         extra->input->bitdepth, &prepared);
			prepared_ok = err == PF_Err_NONE;
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	if (layer_checked_out) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
			    in_data->effect_ref, OLMCOLORKEY_INPUT);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!thrown) thrown = std::current_exception();
		}
	}
	if (thrown) std::rethrow_exception(thrown);
	if (!err && prepared_ok) CommitPreparedRender(prepared, output_world);
	return err;
}


// Included in OLMDirectionalBlur.cpp; preserve translation-unit order.
constexpr std::uint32_t kFixedWholeSign = 0x8000u; // AEX 0x180006c50: high-word signed bit.
constexpr int kFixedWholeModulus = 0x10000; // AEX 0x180006c50: sign-extend the 16-bit whole part.

static PF_FpLong WindowsFixedWholeNumber(PF_Fixed value)
{
	// FUN_180006c50 reads the signed word at PF_ParamDef+0x3a.
	// Preserve the upper 16 bits, including negative fractional angles;
	// signed division by 65536 would instead truncate them toward zero.
	const std::uint32_t whole = static_cast<std::uint32_t>(value) >> 16;
	return static_cast<PF_FpLong>(whole >= kFixedWholeSign
		? static_cast<std::int32_t>(whole) - kFixedWholeModulus
		: static_cast<std::int32_t>(whole));
}

static OLMDirectionalBlurInfo InfoFromParams(PF_ParamDef *params[], PF_FpLong render_scale_x, PF_FpLong render_scale_y)
{
	OLMDirectionalBlurInfo info;
	info.angle_deg = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_ANGLE]->u.ad.value);
	info.brightness_gain = params[OLMDIRECTIONALBLUR_BRIGHTNESS_GAIN]->u.fs_d.value;
	info.size_variation = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_SIZE_VARIATION]->u.fd.value);
	info.front_strength = params[OLMDIRECTIONALBLUR_FRONT_STRENGTH]->u.sd.value;
	info.front_alpha_fade = params[OLMDIRECTIONALBLUR_FRONT_ALPHA_FADE]->u.sd.value;
	info.front_sharp_tail = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_FRONT_SHARP_TAIL]->u.fd.value);
	info.back_strength = params[OLMDIRECTIONALBLUR_BACK_STRENGTH]->u.sd.value;
	info.back_alpha_fade = params[OLMDIRECTIONALBLUR_BACK_ALPHA_FADE]->u.sd.value;
	info.back_sharp_tail = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_BACK_SHARP_TAIL]->u.fd.value);
	info.noise_variation = WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_NOISE_VARIATION]->u.fd.value);
	info.noise_type = params[OLMDIRECTIONALBLUR_NOISE_TYPE]->u.pd.value;
	info.noise_layer = params[OLMDIRECTIONALBLUR_NOISE_LAYER]->u.ld.dephault;
	info.seed = params[OLMDIRECTIONALBLUR_SEED]->u.sd.value;
	info.noise_offset = static_cast<A_long>(WindowsFixedWholeNumber(params[OLMDIRECTIONALBLUR_NOISE_OFFSET]->u.ad.value));
	info.thickness = params[OLMDIRECTIONALBLUR_THICKNESS]->u.fs_d.value;
	// AEX 0x180003d39..0x180003db8 (also PF16/PF32): pixel distances
	// use the horizontal FLOAT32 ratio, irrespective of angle or Y ratio.
	// Materialize once here so every core and its budget see sampled units.
	if (render_scale_x > 0.0 && render_scale_x <= 1.0 &&
		render_scale_y > 0.0 && render_scale_y <= 1.0) {
		const float scale = static_cast<float>(render_scale_x);
		info.front_strength = static_cast<A_long>(static_cast<float>(info.front_strength) * scale);
		info.front_alpha_fade = static_cast<A_long>(static_cast<float>(info.front_alpha_fade) * scale);
		info.back_strength = static_cast<A_long>(static_cast<float>(info.back_strength) * scale);
		info.back_alpha_fade = static_cast<A_long>(static_cast<float>(info.back_alpha_fade) * scale);
		info.thickness = static_cast<float>(info.thickness) * scale;
		info.render_scale_x = info.render_scale_y = 1.0;
	} else {
		info.render_scale_x = render_scale_x;
		info.render_scale_y = render_scale_y;
	}
	return info;
}

static void RenderScaleFromInData(PF_InData *in_data, PF_FpLong &scale_x, PF_FpLong &scale_y)
{
	scale_x = 1.0;
	scale_y = 1.0;
	if (in_data) {
		if (in_data->downsample_x.den != 0) {
			scale_x = static_cast<float>(in_data->downsample_x.num) / static_cast<float>(in_data->downsample_x.den);
		}
		if (in_data->downsample_y.den != 0) {
			scale_y = static_cast<float>(in_data->downsample_y.num) / static_cast<float>(in_data->downsample_y.den);
		}
	}
}

static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_FpLong scale_x, scale_y;
	RenderScaleFromInData(in_data, scale_x, scale_y);
	OLMDirectionalBlurInfo info = InfoFromParams(params, scale_x, scale_y);
	PF_EffectWorld *input = &params[OLMDIRECTIONALBLUR_INPUT]->u.ld;
	PF_PixelFormat format = PF_PixelFormat_INVALID;
	AEFX_SuiteScoper<PF_WorldSuite2> world_suite = AEFX_SuiteScoper<PF_WorldSuite2>(
		in_data, kPFWorldSuite, kPFWorldSuiteVersion2, out_data);
	PF_Err err = world_suite->PF_GetPixelFormat(input, &format);
	if (err) return err;

	short bitdepth = 0;
	switch (format) {
	case PF_PixelFormat_ARGB32:
		bitdepth = 8;
		break;
	case PF_PixelFormat_ARGB64:
		bitdepth = 16;
		break;
	case PF_PixelFormat_ARGB128:
		bitdepth = 32;
		break;
	default:
		return OLM_DIRECTIONAL_REFUSAL("classic-format");
	}
	PF_EffectWorld *noise_layer = params[OLMDIRECTIONALBLUR_NOISE_LAYER]
		? &params[OLMDIRECTIONALBLUR_NOISE_LAYER]->u.ld : NULL;
	info = DirectionalDeepLayerInfo(info, input, noise_layer, bitdepth);
	if (bitdepth != 8 && info.noise_variation > 0.0 && info.noise_type == 3) {
		PF_PixelFormat layer_format = PF_PixelFormat_INVALID;
		if (!noise_layer || !noise_layer->data) return OLM_DIRECTIONAL_REFUSAL("classic-layer-missing");
		err = world_suite->PF_GetPixelFormat(noise_layer, &layer_format);
		if (err) return err;
		if (layer_format != format) return OLM_DIRECTIONAL_REFUSAL("classic-layer-format");
	}
	return RenderWorld(input, output, noise_layer, info, bitdepth);
}

typedef struct {
	PF_FpLong render_scale_x;
	PF_FpLong render_scale_y;
	A_long full_width;
	A_long full_height;
	bool request_contains_full_frame;
} PreRenderData;

static void DeletePreRenderData(void *data)
{
	delete reinterpret_cast<PreRenderData *>(data);
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *, PF_PreRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->output || !extra->cb ||
		!extra->cb->checkout_layer) {
		return OLM_DIRECTIONAL_REFUSAL("prerender-callbacks");
	}
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;
	PF_CheckoutResult noise_result = {};

	A_long full_width = 0, full_height = 0;
	bool request_contains_full_frame = false;
#if !defined(OLM_DBLUR_TEST_SEAM)
	if (in_data->width > 0 && in_data->height > 0) {
		// PF_InData dimensions are unsampled; requests/worlds are sampled.
		// Use integer ceiling for the host's sampled layer bounds.
		const auto sampled_size = [](A_long size, const PF_RationalScale &scale) -> A_long {
			if (scale.num <= 0 || scale.den == 0 ||
				static_cast<A_u_long>(scale.num) > scale.den) return size;
			return static_cast<A_long>((static_cast<std::int64_t>(size) * scale.num +
				scale.den - 1) / scale.den);
		};
		full_width = sampled_size(in_data->width, in_data->downsample_x);
		full_height = sampled_size(in_data->height, in_data->downsample_y);
		// AEX SmartPreRender forwards the request unchanged; checkout owns
		// the returned result/max rectangles independently of input storage.
		request_contains_full_frame = true;
	}
#endif
	req.preserve_rgb_of_zero_alpha = TRUE;
	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		OLMDIRECTIONALBLUR_INPUT, OLMDIRECTIONALBLUR_INPUT, &req, in_data->current_time,
		in_data->time_step, in_data->time_scale, &in_result));
	// `None` is the actual AEX default for Noise Layer. AE reports that optional
	// layer as unavailable during pre-render; that must not abort modes which do
	// not consume it. A selected layer still contributes its requested extent.
	PF_Err noise_err = PF_Err_BAD_CALLBACK_PARAM;
	if (!err) {
		noise_err = extra->cb->checkout_layer(in_data->effect_ref,
			OLMDIRECTIONALBLUR_NOISE_LAYER, OLMDIRECTIONALBLUR_NOISE_LAYER, &req,
			in_data->current_time, in_data->time_step, in_data->time_scale,
			&noise_result);
	}

	if (!err) {
		std::unique_ptr<PreRenderData> pre(new PreRenderData);
			RenderScaleFromInData(in_data, pre->render_scale_x, pre->render_scale_y);
			pre->full_width = full_width;
			pre->full_height = full_height;
			pre->request_contains_full_frame = request_contains_full_frame;
		UnionLRect(&in_result.result_rect, &extra->output->result_rect);
		UnionLRect(&in_result.max_result_rect, &extra->output->max_result_rect);
		if (noise_err == PF_Err_NONE) {
			UnionLRect(&noise_result.result_rect, &extra->output->result_rect);
			UnionLRect(&noise_result.max_result_rect, &extra->output->max_result_rect);
		}
		extra->output->pre_render_data = pre.release();
		extra->output->delete_pre_render_data_func = DeletePreRenderData;
	}
	return err;
}

static PF_Err CheckinDirectionalParam(PF_InData *in_data, PF_ParamDef *param)
{
	return PF_CHECKIN_PARAM(in_data, param);
}

static bool DirectionalActiveRowBytes(short bitdepth, A_long width, std::size_t *bytes)
{
	if (!bytes || width <= 0) return false;
	std::size_t pixel_bytes = 0;
	switch (bitdepth) {
	case 8: pixel_bytes = sizeof(PF_Pixel8); break;
	case 16: pixel_bytes = sizeof(PF_Pixel16); break;
	case 32: pixel_bytes = sizeof(PF_PixelFloat); break;
	default: return false;
	}
	const std::size_t w = static_cast<std::size_t>(width);
	if (w > std::numeric_limits<std::size_t>::max() / pixel_bytes) return false;
	*bytes = w * pixel_bytes;
	return true;
}

static PF_Err
GetDirectionalPixelFormats(PF_InData *in_data,
	const PF_EffectWorld *input_world,
	const PF_EffectWorld *output_world,
	PF_PixelFormat *input_format,
	PF_PixelFormat *output_format)
{
#if defined(OLM_DBLUR_TEST_SEAM)
	(void)in_data;
	if (!input_world || !output_world || !input_format || !output_format) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	// The oldest source-included Smart harness owns a reduced PF_EffectWorld
	// with a test-only bitdepth member.  Real-SDK direct-core harnesses use the
	// actual PF_EffectWorld, which deliberately has no such member.  Keep this
	// compatibility path compile-time bounded to the reduced harness ABI; real
	// public builds never define OLM_DBLUR_TEST_SEAM and always use WorldSuite2.
	*input_format = DirectionalTestPixelFormat(input_world, 0);
	*output_format = DirectionalTestPixelFormat(output_world, 0);
	return (*input_format == PF_PixelFormat_INVALID ||
		*output_format == PF_PixelFormat_INVALID) ? PF_Err_BAD_CALLBACK_PARAM : PF_Err_NONE;
#else
	if (!in_data || !input_world || !output_world || !input_format || !output_format ||
		!in_data->pica_basicP || !in_data->pica_basicP->AcquireSuite ||
		!in_data->pica_basicP->ReleaseSuite) {
		return OLM_DIRECTIONAL_REFUSAL("worldsuite-arguments");
	}
	const void *suite_ptr = NULL;
	PF_Err err = PF_Err_NONE;
	bool acquired = false;
	try {
		const SPErr acquire_err = in_data->pica_basicP->AcquireSuite(
			kPFWorldSuite, kPFWorldSuiteVersion2, &suite_ptr);
		if (acquire_err != kSPNoError) {
			err = static_cast<PF_Err>(acquire_err);
		} else {
			acquired = true;
			const PF_WorldSuite2 *world_suite =
				reinterpret_cast<const PF_WorldSuite2 *>(suite_ptr);
			if (!world_suite || !world_suite->PF_GetPixelFormat) {
				err = OLM_DIRECTIONAL_REFUSAL("worldsuite-callback");
			} else {
				err = world_suite->PF_GetPixelFormat(input_world, input_format);
				if (!err) err = world_suite->PF_GetPixelFormat(output_world, output_format);
			}
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	} catch (const std::bad_alloc &) {
		err = PF_Err_OUT_OF_MEMORY;
	} catch (...) {
		err = PF_Err_INTERNAL_STRUCT_DAMAGED;
	}
	if (acquired) {
		try {
			const SPErr release_err = in_data->pica_basicP->ReleaseSuite(
				kPFWorldSuite, kPFWorldSuiteVersion2);
			if (!err && release_err != kSPNoError) {
				err = static_cast<PF_Err>(release_err);
			}
		} catch (PF_Err &cleanup_err) {
			if (!err) err = cleanup_err;
		} catch (const std::bad_alloc &) {
			if (!err) err = PF_Err_OUT_OF_MEMORY;
		} catch (...) {
			if (!err) err = PF_Err_INTERNAL_STRUCT_DAMAGED;
		}
	}
	return err;
#endif
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *, PF_SmartRenderExtra *extra)
{
	if (!in_data || !extra || !extra->input || !extra->cb ||
		!extra->cb->checkout_layer_pixels || !extra->cb->checkout_output ||
		!extra->cb->checkin_layer_pixels
#if !defined(OLM_DBLUR_TEST_SEAM)
		|| !in_data->inter.checkout_param || !in_data->inter.checkin_param
#endif
	) {
		return OLM_DIRECTIONAL_REFUSAL("smart-callbacks");
	}
	PF_Err err = PF_Err_NONE;
	PF_EffectWorld *input_world  = NULL;
	PF_EffectWorld *noise_world  = NULL;
	PF_EffectWorld *output_world = NULL;
	bool input_checked_out = false;
	bool noise_checked_out = false;
	PF_ParamDef checked[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
	bool param_checked_out[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
	PF_ParamDef *param_ptrs[OLMDIRECTIONALBLUR_NUM_PARAMS] = {};
	std::vector<std::uint8_t> staged_output;
	PF_EffectWorld staged_world = {};
	std::size_t active_row_bytes = 0;
	bool render_complete = false;
	std::exception_ptr thrown;
	try {
		err = extra->cb->checkout_layer_pixels(
			in_data->effect_ref, OLMDIRECTIONALBLUR_INPUT, &input_world);
		input_checked_out = err == PF_Err_NONE;
		if (!err && !input_world) err = OLM_DIRECTIONAL_REFUSAL("smart-input-missing");
		if (!err) {
			const PF_Err noise_err = extra->cb->checkout_layer_pixels(
				in_data->effect_ref, OLMDIRECTIONALBLUR_NOISE_LAYER, &noise_world);
			noise_checked_out = noise_err == PF_Err_NONE;
			if (!noise_checked_out) noise_world = NULL;
		}
		if (!err) err = extra->cb->checkout_output(in_data->effect_ref, &output_world);
		if (!err && !output_world) err = OLM_DIRECTIONAL_REFUSAL("smart-output-missing");
		if (!err && (!DisjointPayloads(input_world, output_world, extra->input->bitdepth / 8 * 4) ||
			(extra->input->bitdepth == 8 && noise_world &&
                (!DisjointPayloads(input_world, noise_world, extra->input->bitdepth / 8 * 4) ||
                 !DisjointPayloads(output_world, noise_world, extra->input->bitdepth / 8 * 4))))) {
			err = OLM_DIRECTIONAL_REFUSAL("smart-overlapping-worlds");
		}
		if (!err) {
			PF_PixelFormat input_format = PF_PixelFormat_INVALID;
			PF_PixelFormat output_format = PF_PixelFormat_INVALID;
			err = GetDirectionalPixelFormats(in_data, input_world, output_world,
				&input_format, &output_format);
			const short depth = extra->input->bitdepth;
			const PF_PixelFormat expected_format = depth == 8 ? PF_PixelFormat_ARGB32 :
				(depth == 16 ? PF_PixelFormat_ARGB64 :
				 (depth == 32 ? PF_PixelFormat_ARGB128 : PF_PixelFormat_INVALID));
			if (!err && (expected_format == PF_PixelFormat_INVALID ||
				input_format != expected_format || output_format != expected_format ||
				input_format != output_format)) {
				err = OLM_DIRECTIONAL_REFUSAL("smart-format");
			}
		}
		for (int i = 1; i < OLMDIRECTIONALBLUR_NUM_PARAMS && !err; ++i) {
			AEFX_CLR_STRUCT(checked[i]);
			err = PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
				in_data->time_step, in_data->time_scale, &checked[i]);
			if (!err) {
				param_checked_out[i] = true;
				param_ptrs[i] = &checked[i];
			}
		}
		if (!err) {
			PF_FpLong render_scale_x, render_scale_y;
			RenderScaleFromInData(in_data, render_scale_x, render_scale_y);
			PreRenderData *pre = reinterpret_cast<PreRenderData *>(extra->input->pre_render_data);
			if (pre) {
				if (pre->render_scale_x > 0.0) render_scale_x = pre->render_scale_x;
				if (pre->render_scale_y > 0.0) render_scale_y = pre->render_scale_y;
			}
			OLMDirectionalBlurInfo info = InfoFromParams(
				param_ptrs, render_scale_x, render_scale_y);
            info = DirectionalDeepLayerInfo(info, input_world, noise_world,
                extra->input->bitdepth);
			// The AEX copy and Iterate writers use world-local coordinates. Keep
			// the full input-sized workspace, then publish the negotiated output's
			// local rows. An ROI origin does not translate the worker's samples.
			PF_EffectWorld workspace = *output_world;
			std::vector<std::uint8_t> workspace_storage;
			PF_EffectWorld *render_world = output_world;
			std::size_t render_row_bytes = 0;
			if (!DirectionalActiveRowBytes(extra->input->bitdepth, output_world->width,
			                              &active_row_bytes) ||
			    active_row_bytes > static_cast<std::size_t>(output_world->rowbytes)) {
				err = OLM_DIRECTIONAL_REFUSAL("smart-output-span");
			}
			if (!err && (output_world->width != input_world->width ||
			             output_world->height != input_world->height)) {
				std::uintptr_t begin = 0, end = 0;
				std::size_t input_row_bytes = 0;
				if (!DirectionalActiveRowBytes(extra->input->bitdepth, input_world->width,
				                              &input_row_bytes) ||
				    input_row_bytes > static_cast<std::size_t>(input_world->rowbytes) ||
				    output_world->width > input_world->width ||
				    output_world->height > input_world->height ||
				    !PayloadSpan(input_world, &begin, &end, extra->input->bitdepth / 8 * 4)) {
					err = OLM_DIRECTIONAL_REFUSAL("smart-workspace-span");
				} else {
					workspace = *input_world;
					workspace_storage.assign(end - begin, 0);
					workspace.data = reinterpret_cast<PF_PixelPtr>(workspace_storage.data());
					render_world = &workspace;
				}
			}
			if ((extra->input->bitdepth == 16 || extra->input->bitdepth == 32) &&
				info.noise_variation > 0.0 && info.noise_type == 3) {
				PF_PixelFormat source_format = PF_PixelFormat_INVALID;
				PF_PixelFormat layer_format = PF_PixelFormat_INVALID;
				const bool safe = extra->input->bitdepth == 16
					? GenericDeepLayerWorldSafe<PF_Pixel16>(input_world, render_world, noise_world, info)
					: GenericDeepLayerWorldSafe<PF_PixelFloat>(input_world, render_world, noise_world, info);
				if (!safe) err = OLM_DIRECTIONAL_REFUSAL("smart-layer-world");
				else {
					err = GetDirectionalPixelFormats(in_data, input_world, noise_world,
						&source_format, &layer_format);
					if (!err && source_format != layer_format) err = OLM_DIRECTIONAL_REFUSAL("smart-layer-format");
				}
			}
			std::uintptr_t output_begin = 0, output_end = 0;
			if (!PayloadSpan(render_world, &output_begin, &output_end, extra->input->bitdepth / 8 * 4) ||
				!DirectionalActiveRowBytes(extra->input->bitdepth, render_world->width,
				                           &render_row_bytes) ||
				render_row_bytes > static_cast<std::size_t>(render_world->rowbytes)) {
				err = OLM_DIRECTIONAL_REFUSAL("smart-output-span");
			}
			const bool retained_exact = IsRetainedNeutralExact(
				input_world, render_world, info, extra->input->bitdepth);
			const bool pf8_feature_fallback = extra->input->bitdepth == 8 &&
                IsGenericDeepFeatureShape(info) &&
                !CanUseExact8(input_world, render_world, noise_world, info);
			const bool generic_features = pf8_feature_fallback ||
				((extra->input->bitdepth == 16 || extra->input->bitdepth == 32) &&
				IsGenericDeepFeatureShape(info));
			const bool generic_shape = !retained_exact &&
				(IsGenericNeutralShape(info) || generic_features);
			int effective_front_strength = 0, effective_back_strength = 0;
			if (!err && generic_shape) {
				const auto strength_info = generic_features ? NeutralStrengthView(info) : info;
				const bool parameters_safe = GenericEffectiveStrengths(
					strength_info, generic_features || extra->input->bitdepth != 8, &effective_front_strength,
					&effective_back_strength, generic_features);
				const bool worlds_safe = extra->input->bitdepth == 8
					? (pf8_feature_fallback
                        ? CanUsePF8FeatureFallback(input_world, render_world, info, output_end - output_begin, true)
                        : CanUseGenericNeutral8(input_world, render_world, info, true))
					: (extra->input->bitdepth == 16
						? GenericDeepWorldsSafe<PF_Pixel16>(input_world, render_world, strength_info, generic_features, true)
						: (extra->input->bitdepth == 32 &&
							GenericDeepWorldsSafe<PF_PixelFloat>(input_world, render_world, strength_info, generic_features, true)));
				olm::dblur::generic::RenderEstimate smart_estimate = {};
				bool estimate_safe = generic_features
					? GenericDeepFeatureEstimate(info, input_world->width, input_world->height,
						pf8_feature_fallback ? 16 : extra->input->bitdepth,
                        output_end - output_begin, &smart_estimate, 1.0, true)
					: olm::dblur::generic::EstimateRender(input_world->width, input_world->height,
						extra->input->bitdepth, effective_front_strength, effective_back_strength,
						output_end - output_begin, &smart_estimate, false, true);
                if (parameters_safe && worlds_safe && estimate_safe && generic_features &&
                    (extra->input->bitdepth == 16 || extra->input->bitdepth == 32) &&
                    info.noise_variation > 0.0 && info.noise_type == 3) {
                    double layer_bound = std::numeric_limits<double>::infinity();
                    const bool bound_safe = extra->input->bitdepth == 16
                        ? GenericDeepLayerCoefficientBound<PF_Pixel16>(noise_world, info, &layer_bound)
                        : GenericPF32LayerCoefficientBound(noise_world, info, &layer_bound);
                    estimate_safe = bound_safe &&
                        GenericDeepFeatureEstimate(info, input_world->width, input_world->height,
                            extra->input->bitdepth, output_end - output_begin, &smart_estimate, layer_bound, true);
                }
				// AEX 0x180004a20 derives its planes from the checked-out input,
				// not PF_InData's layer dimensions. F53's 40x30 layer / 20x15
				// checkout witnesses also cover nonzero checkout origins. The
				// input-sized workspace and world/budget checks above suffice;
				// requiring a full-layer world rejects valid cropped checkouts.
				if (!parameters_safe || !worlds_safe || !estimate_safe) {
					err = OLM_DIRECTIONAL_REFUSAL("smart-generic-world-or-budget");
				}
			}
			if (!err) {
				staged_output.assign(output_end - output_begin, 0);
				staged_world = *render_world;
				staged_world.data = reinterpret_cast<PF_PixelPtr>(staged_output.data());
				PF_EffectWorld sampled_input = *input_world;
				if (render_world == &workspace) {
					// Both AEX unpack and pack Iterate calls receive the output's
					// local extent. Pixels outside that area never enter the plane,
					// whose dimensions still derive from the checked-out input.
					for (A_long y = 0; y < output_world->height; ++y)
						std::memcpy(workspace_storage.data() + static_cast<std::size_t>(y) * input_world->rowbytes,
							reinterpret_cast<const std::uint8_t *>(input_world->data) +
							static_cast<std::size_t>(y) * input_world->rowbytes, active_row_bytes);
					sampled_input.data = reinterpret_cast<PF_PixelPtr>(workspace_storage.data());
				}
				err = RenderWorld(&sampled_input, &staged_world, noise_world, info,
				                  extra->input->bitdepth, nullptr, true);
				render_complete = err == PF_Err_NONE;
			}
		}
	} catch (...) {
		thrown = std::current_exception();
	}
	for (int i = 1; i < OLMDIRECTIONALBLUR_NUM_PARAMS; ++i) {
		if (!param_checked_out[i]) continue;
		try {
			const PF_Err checkin_err = CheckinDirectionalParam(in_data, &checked[i]);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (input_checked_out) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
				in_data->effect_ref, OLMDIRECTIONALBLUR_INPUT);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (noise_checked_out) {
		try {
			const PF_Err checkin_err = extra->cb->checkin_layer_pixels(
				in_data->effect_ref, OLMDIRECTIONALBLUR_NOISE_LAYER);
			if (!err && !thrown && checkin_err) err = checkin_err;
		} catch (...) {
			if (!err && !thrown) thrown = std::current_exception();
		}
	}
	if (thrown) std::rethrow_exception(thrown);
	if (!err && render_complete) {
		for (A_long y = 0; y < output_world->height; ++y) {
			std::memcpy(reinterpret_cast<std::uint8_t *>(output_world->data) +
					static_cast<std::size_t>(y) * output_world->rowbytes,
				staged_output.data() + static_cast<std::size_t>(y) * staged_world.rowbytes,
				active_row_bytes);
		}
	}
	return err;
}

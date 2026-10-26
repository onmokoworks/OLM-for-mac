static bool IsGenericNeutral8Parameters(const OLMDirectionalBlurInfo &info)
{
	int ignored_front = 0, ignored_back = 0;
	return GenericEffectiveStrengths(info, false, &ignored_front, &ignored_back);
}

static bool DirectionalGenericWorldIsFullFrame(const PF_EffectWorld *world,
	                                            A_long width, A_long height)
{
	return world && width > 0 && height > 0 && world->width == width &&
		world->height == height && DirectionalWorldHasZeroOrigin(world, 0);
}

static bool DirectionalNormalizeFullFrameRequest(const PF_RenderRequest &requested,
	                                              A_long width, A_long height,
	                                              PF_RenderRequest *normalized)
{
#if defined(OLM_DBLUR_TEST_SEAM) && !defined(OLM_DBLUR_TEST_FULL_RENDER_REQUEST)
	(void)requested; (void)width; (void)height; (void)normalized;
	return false;
#else
	if (!normalized || width <= 0 || height <= 0) return false;
	const bool contains = requested.rect.left <= 0 && requested.rect.top <= 0 &&
		requested.rect.right >= width && requested.rect.bottom >= height;
	*normalized = requested;
	if (contains) normalized->rect = PF_LRect{0, 0, width, height};
	normalized->preserve_rgb_of_zero_alpha = TRUE;
	return contains;
#endif
}

// Source-included harness entry points; OLM_DBLUR_TEST_SEAM only.
struct OLMDirectionalBlurGenericEstimate {
	std::uint64_t source_pixels;
	std::uint64_t work_width;
	std::uint64_t work_height;
	std::uint64_t work_pixels;
	std::uint64_t core_workspace_bytes;
	std::uint64_t wrapper_bytes;
	std::uint64_t weight_bytes;
	std::uint64_t smart_staging_bytes;
	std::uint64_t plugin_owned_live_bytes;
	std::uint64_t operation_units;
};

// Test-only transparent view of the exact production estimator.  Tests do not
// duplicate the geometry, live-allocation, or rowdriver-work arithmetic.
extern "C" int OLMDirectionalBlurTestGenericEstimate(
	A_long width,
	A_long height,
	short bitdepth,
	A_long effective_strength,
	std::size_t smart_staging_bytes,
	OLMDirectionalBlurGenericEstimate *result)
{
	if (!result) return 0;
	olm::dblur::generic::RenderEstimate estimate = {};
	if (!olm::dblur::generic::EstimateRender(
		width, height, bitdepth, static_cast<int>(effective_strength),
		smart_staging_bytes, &estimate)) {
		*result = {};
		return 0;
	}
	result->source_pixels = estimate.source_pixels;
	result->work_width = static_cast<std::uint64_t>(estimate.work.width);
	result->work_height = static_cast<std::uint64_t>(estimate.work.height);
	result->work_pixels = estimate.work.pixels;
	result->core_workspace_bytes = estimate.core_workspace_bytes;
	result->wrapper_bytes = estimate.wrapper_bytes;
	result->weight_bytes = estimate.weight_bytes;
	result->smart_staging_bytes = estimate.smart_staging_bytes;
	result->plugin_owned_live_bytes = estimate.plugin_owned_live_bytes;
	result->operation_units = estimate.operation_units;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEstimateSides(
	A_long width,
	A_long height,
	short bitdepth,
	A_long effective_front_strength,
	A_long effective_back_strength,
	std::size_t smart_staging_bytes,
	OLMDirectionalBlurGenericEstimate *result)
{
	if (!result) return 0;
	olm::dblur::generic::RenderEstimate estimate = {};
	if (!olm::dblur::generic::EstimateRender(
		width, height, bitdepth, static_cast<int>(effective_front_strength),
		static_cast<int>(effective_back_strength), smart_staging_bytes, &estimate)) {
		*result = {};
		return 0;
	}
	result->source_pixels = estimate.source_pixels;
	result->work_width = static_cast<std::uint64_t>(estimate.work.width);
	result->work_height = static_cast<std::uint64_t>(estimate.work.height);
	result->work_pixels = estimate.work.pixels;
	result->core_workspace_bytes = estimate.core_workspace_bytes;
	result->wrapper_bytes = estimate.wrapper_bytes;
	result->weight_bytes = estimate.weight_bytes;
	result->smart_staging_bytes = estimate.smart_staging_bytes;
	result->plugin_owned_live_bytes = estimate.plugin_owned_live_bytes;
	result->operation_units = estimate.operation_units;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEffectiveStrength(
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *effective_strength)
{
	int front = 0, back = 0;
	if (!info || !effective_strength ||
		(bitdepth != 8 && bitdepth != 16 && bitdepth != 32) ||
		!GenericEffectiveStrengths(*info, bitdepth != 8, &front, &back) ||
		(front > 0 && back > 0)) {
		return 0;
	}
	*effective_strength = front > 0 ? front : back;
	return 1;
}

extern "C" int OLMDirectionalBlurTestGenericEffectiveStrengths(
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *effective_front_strength,
	int *effective_back_strength)
{
	return info && (bitdepth == 8 || bitdepth == 16 || bitdepth == 32) &&
		GenericEffectiveStrengths(*info, bitdepth != 8,
			effective_front_strength, effective_back_strength) ? 1 : 0;
}

// Test-only entrypoint: keep the boundary probe on the production dispatcher.
extern "C" PF_Err OLMDirectionalBlurTestRenderWorld(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *used_exact_front_only8)
{
	if (!info || !used_exact_front_only8) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	*used_exact_front_only8 =
		bitdepth == 8 && CanUseExact8(input, output, nullptr, *info) ? 1 : 0;
	return RenderWorld(input, output, nullptr, *info, bitdepth);
}

extern "C" PF_Err OLMDirectionalBlurTestRenderWorldRoute(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *observed_route)
{
	if (!info || !observed_route) return PF_Err_BAD_CALLBACK_PARAM;
	return RenderWorld(input, output, nullptr, *info, bitdepth, observed_route);
}

extern "C" PF_Err OLMDirectionalBlurTestRenderWorldWithNoise(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	PF_EffectWorld *noise_layer,
	const OLMDirectionalBlurInfo *info,
	short bitdepth,
	int *used_exact8)
{
	if (!info || !used_exact8) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	*used_exact8 = bitdepth == 8 &&
		CanUseExact8(input, output, noise_layer, *info) ? 1 : 0;
	return RenderWorld(input, output, noise_layer, *info, bitdepth);
}

extern "C" int OLMDirectionalBlurTestNormalizeFullFrameRequest(
	const PF_RenderRequest *requested, A_long width, A_long height,
	PF_RenderRequest *normalized)
{
	return requested && DirectionalNormalizeFullFrameRequest(
		*requested, width, height, normalized) ? 1 : 0;
}

extern "C" int OLMDirectionalBlurTestGenericWorldIsFullFrame(
	const PF_EffectWorld *world, A_long width, A_long height)
{
	return DirectionalGenericWorldIsFullFrame(world, width, height) ? 1 : 0;
}

extern "C" int OLMDirectionalBlurTestGenericSmartFramePolicy(
	const PF_RenderRequest *request, const PF_EffectWorld *input,
	const PF_EffectWorld *output, const OLMDirectionalBlurInfo *info,
	short bitdepth, A_long width, A_long height)
{
	if (!request || !info) return 0;
	PF_RenderRequest normalized = {};
	const bool retained_exact = IsRetainedNeutralExact(input, output, *info, bitdepth);
	const bool generic = !retained_exact &&
		(bitdepth == 8 ? (IsGenericNeutral8Parameters(*info) ||
            (!CanUseExact8(input, output, nullptr, *info) &&
                CanUsePF8FeatureFallback(input, output, *info)))
			: ((bitdepth == 16 || bitdepth == 32) &&
               (IsGenericNeutralDeepParameters(*info) || IsGenericDeepFeatureShape(*info))));
	return generic && DirectionalNormalizeFullFrameRequest(
		*request, width, height, &normalized) &&
		DirectionalGenericWorldIsFullFrame(input, width, height) &&
		DirectionalGenericWorldIsFullFrame(output, width, height) ? 1 : 0;
}

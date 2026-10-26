// Test-only public render and capture entry points; included by OLMRadialBlur.cpp.
#if defined(OLM_RADIALBLUR_TEST_SEAM)
extern "C" PF_Err OLMRadialBlurTestRenderWorld(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	short bitdepth)
{
	if (!input || !output || !info) return PF_Err_BAD_CALLBACK_PARAM;
	return RenderWorld(input, output, *info, bitdepth);
}

extern "C" PF_Err OLMRadialBlurTestRenderWorldWithNoiseLayer(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	PF_EffectWorld *noise_world,
	const OLMRadialBlurInfo *info,
	short bitdepth)
{
	if (!input || !output || !info) return PF_Err_BAD_CALLBACK_PARAM;
	return RenderWorld(input, output, noise_world, *info, bitdepth);
}

extern "C" PF_Err OLMRadialBlurTestRenderRotation8AndCapture(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	RadialBlurTestRotationCapture *capture)
{
	if (!input || !output || !info || !capture || g_rotation_test_capture) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	g_rotation_test_capture = capture;
	const PF_Err err = RenderRotationTyped<PF_Pixel8>(input, output, *info);
	g_rotation_test_capture = nullptr;
	return err;
}

extern "C" PF_Err OLMRadialBlurTestRenderFloatAndCapturePolarPlanes(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	float *pre_blur_polar_rgba,
	float *post_blur_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *polar_width,
	A_long *polar_height)
{
	if (!input || !output || !info || !pre_blur_polar_rgba || !post_blur_polar_rgba || !written_floats ||
	    !polar_width || !polar_height) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	RadialBlurTestPolarCapture capture;
	capture.pre_blur_rgba = pre_blur_polar_rgba;
	capture.post_blur_rgba = post_blur_polar_rgba;
	capture.capacity_floats = capacity_floats;
	const PF_Err err = RenderZoomTyped<PF_PixelFloat>(input, output, *info, &capture);
	*written_floats = capture.written_floats;
	*polar_width = capture.width;
	*polar_height = capture.height;
	return err;
}

extern "C" PF_Err OLMRadialBlurTestRenderFloatAndCapturePolarPlanesWithEligibility(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	float *pre_blur_polar_rgba,
	float *post_blur_polar_rgba,
	A_u_char *eligibility,
	size_t capacity_floats,
	size_t capacity_cells,
	size_t *written_floats,
	size_t *written_cells,
	A_long *polar_width,
	A_long *polar_height)
{
	if (!input || !output || !info || !pre_blur_polar_rgba || !post_blur_polar_rgba ||
	    !eligibility || !written_floats || !written_cells || !polar_width || !polar_height) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	RadialBlurTestPolarCapture capture;
	capture.pre_blur_rgba = pre_blur_polar_rgba;
	capture.post_blur_rgba = post_blur_polar_rgba;
	capture.eligibility = eligibility;
	capture.capacity_floats = capacity_floats;
	capture.capacity_cells = capacity_cells;
	const PF_Err err = RenderZoomTyped<PF_PixelFloat>(input, output, *info, &capture);
	*written_floats = capture.written_floats;
	*written_cells = capture.written_cells;
	*polar_width = capture.width;
	*polar_height = capture.height;
	return err;
}

extern "C" PF_Err OLMRadialBlurTestRenderFloatAndCaptureOuterOnlyInputs(
	PF_EffectWorld *input,
	PF_EffectWorld *output,
	const OLMRadialBlurInfo *info,
	float *pre_blur_polar_rgba,
	float *post_blur_polar_rgba,
	A_u_char *eligibility,
	float *span_plane,
	float *source_scalar_plane,
	size_t capacity_floats,
	size_t capacity_cells,
	size_t *written_floats,
	size_t *written_cells,
	A_long *polar_width,
	A_long *polar_height)
{
	if (!input || !output || !info || !pre_blur_polar_rgba || !post_blur_polar_rgba ||
	    !eligibility || !span_plane || !source_scalar_plane || !written_floats ||
	    !written_cells || !polar_width || !polar_height) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	RadialBlurTestPolarCapture capture;
	capture.pre_blur_rgba = pre_blur_polar_rgba;
	capture.post_blur_rgba = post_blur_polar_rgba;
	capture.eligibility = eligibility;
	capture.span_plane = span_plane;
	capture.source_scalar_plane = source_scalar_plane;
	capture.capacity_floats = capacity_floats;
	capture.capacity_cells = capacity_cells;
	const PF_Err err = RenderZoomTyped<PF_PixelFloat>(input, output, *info, &capture);
	*written_floats = capture.written_floats;
	*written_cells = capture.written_cells;
	*polar_width = capture.width;
	*polar_height = capture.height;
	return err;
}

extern "C" PF_Err OLMRadialBlurTestRunFloatWorker(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_Boolean *used_fft_convolution)
{
	if (!pre_blur_polar_rgba || !info || !normalized_polar_rgba || !written_floats ||
	    !used_fft_convolution || polar_width <= 0 || polar_height <= 0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t required_floats = (size_t)polar_width * polar_height * 4;
	if (capacity_floats < required_floats) return PF_Err_BAD_CALLBACK_PARAM;
	FloatImage polar;
	polar.width = polar_width;
	polar.height = polar_height;
	polar.rgba.assign(pre_blur_polar_rgba, pre_blur_polar_rgba + required_floats);
	bool used_fft = false;
	const FloatImage blurred = BuildZoomBlurredPolar(
		polar, *info, LoadRadialBlurDebugConfig(), &used_fft);
	if (blurred.rgba.size() != required_floats) return PF_Err_BAD_CALLBACK_PARAM;
	std::memcpy(normalized_polar_rgba, blurred.rgba.data(), required_floats * sizeof(float));
	*written_floats = required_floats;
	*used_fft_convolution = used_fft ? TRUE : FALSE;
	return PF_Err_NONE;
}

extern "C" PF_Err OLMRadialBlurTestRunAEXWorkerCandidate(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info) return PF_Err_BAD_CALLBACK_PARAM;
	return RunZoomAEXWorkerCandidate<false>(
		pre_blur_polar_rgba, polar_width, polar_height, info,
		ZoomGaussianWeights(ZoomEffectiveLength(*info)), normalized_polar_rgba,
		capacity_floats, written_floats, weight_count);
}

extern "C" PF_Err OLMRadialBlurTestRunAEXWorkerCandidate2(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info) return PF_Err_BAD_CALLBACK_PARAM;
	return RunZoomAEXWorkerCandidate<false>(
		pre_blur_polar_rgba, polar_width, polar_height, info,
		ZoomGaussianWeightsAEXScalarCandidate(ZoomEffectiveLength(*info)),
		normalized_polar_rgba, capacity_floats, written_floats, weight_count);
}

extern "C" PF_Err OLMRadialBlurTestRunAEXWorkerCandidate3(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info) return PF_Err_BAD_CALLBACK_PARAM;
	return RunZoomAEXWorkerCandidate<true>(
		pre_blur_polar_rgba, polar_width, polar_height, info,
		ZoomGaussianWeightsAEXScalarCandidate(ZoomEffectiveLength(*info)),
		normalized_polar_rgba, capacity_floats, written_floats, weight_count);
}

extern "C" PF_Err OLMRadialBlurTestRunAEXWorkerCandidate4(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	const float *exact_weights,
	A_long exact_weight_count,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info || !exact_weights || exact_weight_count != ZoomEffectiveLength(*info)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const std::vector<float> weights(exact_weights, exact_weights + exact_weight_count);
	return RunZoomAEXWorkerCandidate<true>(
		pre_blur_polar_rgba, polar_width, polar_height, info, weights,
		normalized_polar_rgba, capacity_floats, written_floats, weight_count);
}

extern "C" PF_Err OLMRadialBlurTestRunCandidate5DirectionMaskDiagnostic(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	const float *exact_weights,
	A_long exact_weight_count,
	const A_u_char *source_eligibility,
	size_t eligibility_count,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!info || !exact_weights || !source_eligibility ||
	    exact_weight_count != ZoomEffectiveLength(*info)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const std::vector<float> weights(exact_weights, exact_weights + exact_weight_count);
	return RunZoomAEXWorkerCandidate<true>(
		pre_blur_polar_rgba, polar_width, polar_height, info, weights,
		normalized_polar_rgba, capacity_floats, written_floats, weight_count,
		source_eligibility, eligibility_count);
}

extern "C" PF_Err OLMRadialBlurTestRunCandidate6ScalarPlaneDiagnostic(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	const float *exact_weights,
	A_long exact_weight_count,
	const A_u_char *source_eligibility,
	size_t eligibility_count,
	const float *span_plane,
	const float *source_scalar_plane,
	size_t scalar_plane_count,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count)
{
	if (!pre_blur_polar_rgba || !info || !exact_weights || !source_eligibility ||
	    !span_plane || !source_scalar_plane || !normalized_polar_rgba || !written_floats ||
	    !weight_count || polar_width <= 0 || polar_height <= 0 || info->inner_strength != 0 ||
	    info->inner_offset != 0 || exact_weight_count != ZoomEffectiveLength(*info)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t required_cells = (size_t)polar_width * polar_height;
	const size_t required_floats = required_cells * 4;
	if (eligibility_count != required_cells || scalar_plane_count != required_cells ||
	    capacity_floats < required_floats) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	FloatImage polar;
	polar.width = polar_width;
	polar.height = polar_height;
	polar.rgba.assign(pre_blur_polar_rgba, pre_blur_polar_rgba + required_floats);
	const std::vector<float> weights(exact_weights, exact_weights + exact_weight_count);
	const FloatImage normalized = BuildZoomCandidate6ScalarPlaneDiagnostic(
		polar, weights, source_eligibility, span_plane, source_scalar_plane,
		info->outer_strength);
	if (normalized.rgba.size() != required_floats) return PF_Err_BAD_CALLBACK_PARAM;
	std::memcpy(normalized_polar_rgba, normalized.rgba.data(), required_floats * sizeof(float));
	*written_floats = required_floats;
	*weight_count = exact_weight_count;
	return PF_Err_NONE;
}
#endif


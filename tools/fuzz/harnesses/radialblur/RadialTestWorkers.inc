// Test-only worker alternatives and capture declarations; included by OLMRadialBlur.cpp.
#if defined(OLM_RADIALBLUR_TEST_SEAM)
static std::vector<float> ZoomGaussianWeightsAEXScalarCandidate(A_long length)
{
	if (length <= 1) return std::vector<float>{1.0f};
	const float length_f = (float)length;
	float denom = RadialF32Mul(length_f, length_f);
	denom = RadialF32Mul(denom, 0.111111119389534f);
	denom = RadialF32Add(denom, denom);
	denom = (float)((double)denom + 1.0e-5);
	const float inv_denom = RadialF32Div(1.0f, denom);
	std::vector<float> weights((size_t)length);
	for (A_long i = 0; i < length; ++i) {
		const int square = (int)i * (int)i;
		const float exponent = RadialF32Mul((float)-square, inv_denom);
		weights[(size_t)i] = ucrt_expf(exponent, UCRT_FMA);
	}
	return weights;
}

template <bool UseAEXMultiplyOrder>
static FloatImage BuildZoomAEXWorkerCandidate(
	const FloatImage &polar,
	const std::vector<float> &weights,
	const A_u_char *source_eligibility = nullptr)
{
	const A_long radius_count = polar.width;
	const A_long angular_count = polar.height;
	FloatImage normalized;
	normalized.width = radius_count;
	normalized.height = angular_count;
	normalized.rgba.assign((size_t)angular_count * radius_count * 4, 0.0f);
	std::vector<float> accum_alpha((size_t)angular_count * radius_count, 0.0f);
	std::vector<float> max_alpha((size_t)angular_count * radius_count, 0.0f);
	std::atomic<A_long> next_row(0);
	const unsigned hardware_threads = std::thread::hardware_concurrency();
	const A_long thread_count = std::max<A_long>(
		1, std::min<A_long>(angular_count, hardware_threads ? (A_long)hardware_threads : 1));
	std::vector<std::thread> threads;
	threads.reserve((size_t)thread_count);
	for (A_long thread_index = 0; thread_index < thread_count; ++thread_index) {
		threads.emplace_back([&]() {
			for (;;) {
				const A_long ai = next_row.fetch_add(1, std::memory_order_relaxed);
				if (ai >= angular_count) break;
				const size_t row_cell = (size_t)ai * radius_count;
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float alpha = polar.rgba[rgba + 3];
					for (int c = 0; c < 3; ++c) {
						normalized.rgba[rgba + c] = RadialF32Mul(polar.rgba[rgba + c], alpha);
					}
					accum_alpha[cell] = alpha;
					max_alpha[cell] = alpha;
				}

				for (A_long source_ri = 0; source_ri < radius_count; ++source_ri) {
					const size_t source_cell = row_cell + source_ri;
					if (source_eligibility && source_eligibility[source_cell] == 0) continue;
					const size_t source_rgba = source_cell * 4;
					const float alpha = polar.rgba[source_rgba + 3];
					const A_long limit = std::min<A_long>(
						(A_long)weights.size(), radius_count - source_ri);
					for (A_long k = 1; k < limit; ++k) {
						const float weight = weights[(size_t)k];
						const float alpha_weight = RadialF32Mul(alpha, weight);
						const size_t destination_cell = source_cell + k;
						const size_t destination_rgba = destination_cell * 4;
						for (int c = 0; c < 3; ++c) {
							float contribution = 0.0f;
							if constexpr (UseAEXMultiplyOrder) {
								contribution = RadialF32Mul(alpha_weight, polar.rgba[source_rgba + c]);
							} else {
								const float premultiplied = RadialF32Mul(polar.rgba[source_rgba + c], alpha);
								contribution = RadialF32Mul(premultiplied, weight);
							}
							normalized.rgba[destination_rgba + c] = RadialF32Add(
								normalized.rgba[destination_rgba + c], contribution);
						}
						accum_alpha[destination_cell] = RadialF32Add(
							accum_alpha[destination_cell], alpha_weight);
						if (max_alpha[destination_cell] < alpha_weight) {
							max_alpha[destination_cell] = alpha_weight;
						}
					}
				}

				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float denominator = accum_alpha[cell];
					if (denominator == 0.0f) {
						for (int c = 0; c < 3; ++c) normalized.rgba[rgba + c] = 0.0f;
					} else {
						for (int c = 0; c < 3; ++c) {
							normalized.rgba[rgba + c] = RadialF32Div(normalized.rgba[rgba + c], denominator);
						}
					}
					normalized.rgba[rgba + 3] = max_alpha[cell];
				}
			}
		});
	}
	for (std::thread &thread : threads) thread.join();
	return normalized;
}

static FloatImage BuildZoomCandidate6ScalarPlaneDiagnostic(
	const FloatImage &polar,
	const std::vector<float> &weights,
	const A_u_char *source_eligibility,
	const float *span_plane,
	const float *source_scalar_plane,
	A_long outer_strength)
{
	const A_long radius_count = polar.width;
	const A_long angular_count = polar.height;
	FloatImage normalized;
	normalized.width = radius_count;
	normalized.height = angular_count;
	normalized.rgba.assign((size_t)angular_count * radius_count * 4, 0.0f);
	std::vector<float> accum_alpha((size_t)angular_count * radius_count, 0.0f);
	std::vector<float> max_alpha((size_t)angular_count * radius_count, 0.0f);
	std::atomic<A_long> next_row(0);
	const unsigned hardware_threads = std::thread::hardware_concurrency();
	const A_long thread_count = std::max<A_long>(
		1, std::min<A_long>(angular_count, hardware_threads ? (A_long)hardware_threads : 1));
	std::vector<std::thread> threads;
	threads.reserve((size_t)thread_count);
	for (A_long thread_index = 0; thread_index < thread_count; ++thread_index) {
		threads.emplace_back([&]() {
			for (;;) {
				const A_long ai = next_row.fetch_add(1, std::memory_order_relaxed);
				if (ai >= angular_count) break;
				const size_t row_cell = (size_t)ai * radius_count;
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float source_scalar = source_scalar_plane[cell];
					for (int c = 0; c < 3; ++c) {
						normalized.rgba[rgba + c] = RadialF32Mul(
							polar.rgba[rgba + c], source_scalar);
					}
					accum_alpha[cell] = source_scalar;
					max_alpha[cell] = source_scalar;
				}

				for (A_long source_ri = 0; source_ri < radius_count; ++source_ri) {
					const size_t source_cell = row_cell + source_ri;
					const float source_scalar = source_scalar_plane[source_cell];
					const float span = span_plane[source_cell];
					if (source_eligibility[source_cell] == 0 || source_scalar == 0.0f || span == 0.0f) {
						continue;
					}
					const A_long strength_limit = (A_long)RadialF32Mul((float)outer_strength, span);
					const A_long limit = std::min<A_long>(radius_count - source_ri, strength_limit);
					const float inverse_span = RadialF32Div(1.0f, span);
					const size_t source_rgba = source_cell * 4;
					for (A_long k = 1; k < limit; ++k) {
						const A_long table_index = (A_long)RadialF32Mul((float)k, inverse_span);
						if (table_index < 0 || table_index >= (A_long)weights.size()) continue;
						const float alpha_weight = RadialF32Mul(
							source_scalar, weights[(size_t)table_index]);
						const size_t destination_cell = source_cell + k;
						const size_t destination_rgba = destination_cell * 4;
						for (int c = 0; c < 3; ++c) {
							const float contribution = RadialF32Mul(
								alpha_weight, polar.rgba[source_rgba + c]);
							normalized.rgba[destination_rgba + c] = RadialF32Add(
								normalized.rgba[destination_rgba + c], contribution);
						}
						accum_alpha[destination_cell] = RadialF32Add(
							accum_alpha[destination_cell], alpha_weight);
						if (max_alpha[destination_cell] < alpha_weight) {
							max_alpha[destination_cell] = alpha_weight;
						}
					}
				}

				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float denominator = accum_alpha[cell];
					if (denominator == 0.0f) {
						for (int c = 0; c < 3; ++c) normalized.rgba[rgba + c] = 0.0f;
					} else {
						for (int c = 0; c < 3; ++c) {
							normalized.rgba[rgba + c] = RadialF32Div(
								normalized.rgba[rgba + c], denominator);
						}
					}
					normalized.rgba[rgba + 3] = max_alpha[cell];
				}
			}
		});
	}
	for (std::thread &thread : threads) thread.join();
	return normalized;
}

template <bool UseAEXMultiplyOrder>
static PF_Err RunZoomAEXWorkerCandidate(
	const float *pre_blur_polar_rgba,
	A_long polar_width,
	A_long polar_height,
	const OLMRadialBlurInfo *info,
	const std::vector<float> &weights,
	float *normalized_polar_rgba,
	size_t capacity_floats,
	size_t *written_floats,
	A_long *weight_count,
	const A_u_char *source_eligibility = nullptr,
	size_t eligibility_count = 0)
{
	if (!pre_blur_polar_rgba || !info || !normalized_polar_rgba || !written_floats ||
	    !weight_count || polar_width <= 0 || polar_height <= 0 || info->inner_strength != 0 ||
	    info->outer_edge_fade != 0) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	const size_t required_floats = (size_t)polar_width * polar_height * 4;
	const size_t required_cells = (size_t)polar_width * polar_height;
	if (capacity_floats < required_floats || weights.empty() ||
	    (source_eligibility && eligibility_count != required_cells) ||
	    (!source_eligibility && eligibility_count != 0)) {
		return PF_Err_BAD_CALLBACK_PARAM;
	}
	FloatImage polar;
	polar.width = polar_width;
	polar.height = polar_height;
	polar.rgba.assign(pre_blur_polar_rgba, pre_blur_polar_rgba + required_floats);
	const FloatImage normalized = BuildZoomAEXWorkerCandidate<UseAEXMultiplyOrder>(
		polar, weights, source_eligibility);
	if (normalized.rgba.size() != required_floats) return PF_Err_BAD_CALLBACK_PARAM;
	std::memcpy(normalized_polar_rgba, normalized.rgba.data(), required_floats * sizeof(float));
	*written_floats = required_floats;
	*weight_count = (A_long)weights.size();
	return PF_Err_NONE;
}

struct RadialBlurTestPolarCapture {
	float *pre_blur_rgba = nullptr;
	float *post_blur_rgba = nullptr;
	A_u_char *eligibility = nullptr;
	float *span_plane = nullptr;
	float *source_scalar_plane = nullptr;
	size_t capacity_floats = 0;
	size_t capacity_cells = 0;
	size_t written_floats = 0;
	size_t written_cells = 0;
	A_long width = 0;
	A_long height = 0;
};

struct RadialBlurTestRotationCapture {
	float *polar_rgba = nullptr;
	A_u_char *eligibility = nullptr;
	float *source_scalar = nullptr;
	float *source_span = nullptr;
	float *prepass_alpha = nullptr;
	float *accum_rgba = nullptr;
	float *max_alpha = nullptr;
	float *normalized_rgba = nullptr;
	float *final_rgba = nullptr;
	float *final_coordinates = nullptr;
	size_t capacity_cells = 0;
	size_t capacity_output_pixels = 0;
	size_t written_cells = 0;
	A_long width = 0;
	A_long height = 0;
	// Bounded case_0010 inverse/PF8 writer witnesses, ordered as
	// (1612,6), (1614,6).  The RGBA float arrays retain the native sampler
	// return and the post-gain/upper-clamp arguments passed to the ARGB packer.
	float inverse_coordinates[4] = {0.0f, 0.0f, 0.0f, 0.0f};
	float inverse_rgba[8] = {0.0f};
	float packer_rgba[8] = {0.0f};
	A_u_char packed_argb[8] = {0};
	A_u_char inverse_witness_mask = 0;
	float residual_coordinates[6] = {0.0f};
	float residual_angle_raw[3] = {0.0f};
	float residual_rgba[12] = {0.0f};
	A_u_char residual_witness_mask = 0;
};

static RadialBlurTestRotationCapture *g_rotation_test_capture = nullptr;
#endif


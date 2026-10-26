// Zoom convolution and AEX scatter/normalize kernels; included by OLMRadialBlur.cpp.
static FloatImage BuildZoomBlurredPolar(
	const FloatImage &polar,
	const OLMRadialBlurInfo &info,
	const RadialBlurDebugConfig &debug,
	bool *used_fft_convolution)
{
	const A_long radius_count = polar.width;
	const A_long angular_count = polar.height;
	const std::vector<float> weights = ZoomGaussianWeights(ZoomEffectiveLength(info));
	const bool use_fft_convolution = weights.size() > 512 && !debug.force_scalar_producer;
	if (used_fft_convolution) *used_fft_convolution = use_fft_convolution;
	FloatImage blurred;
	blurred.width = radius_count;
	blurred.height = angular_count;
	blurred.rgba.assign((size_t)angular_count * radius_count * 4, 0.0f);
	if (!use_fft_convolution) {
		for (A_long ai = 0; ai < angular_count; ++ai) {
			for (A_long ri = 0; ri < radius_count; ++ri) {
				double accum_w_double = 0.0;
				float accum_w_float = 0.0f;
				float weighted_rgb[3] = {0.0f, 0.0f, 0.0f};
				float weighted_alpha = 0.0f;
				float accum_alpha = 0.0f;
				const A_long limit = std::min<A_long>((A_long)weights.size(), ri + 1);
				for (A_long k = 0; k < limit; ++k) {
					const size_t src_idx = ((size_t)ai * radius_count + (ri - k)) * 4;
					const float alpha = polar.rgba[src_idx + 3];
					const float weight = weights[(size_t)k];
					if (debug.force_scalar_producer) {
						const float alpha_weight = RadialF32Mul(alpha, weight);
						for (int c = 0; c < 3; ++c) {
							weighted_rgb[c] = RadialF32Add(
								weighted_rgb[c],
								RadialF32Mul(polar.rgba[src_idx + c], alpha_weight));
						}
						weighted_alpha = RadialF32Add(weighted_alpha, alpha_weight);
						accum_alpha = RadialF32Add(accum_alpha, alpha_weight);
						accum_w_float = RadialF32Add(accum_w_float, weight);
					} else {
						for (int c = 0; c < 3; ++c) weighted_rgb[c] += polar.rgba[src_idx + c] * alpha * weight;
						weighted_alpha += alpha * weight;
						accum_alpha += alpha * weight;
						accum_w_double += (double)weight;
					}
				}
				const size_t dst = ((size_t)ai * radius_count + ri) * 4;
				if (weighted_alpha > 1.0e-8f) {
					for (int c = 0; c < 3; ++c) blurred.rgba[dst + c] = weighted_rgb[c] / weighted_alpha;
				}
				const float weight_sum = debug.force_scalar_producer ? accum_w_float : (float)accum_w_double;
				blurred.rgba[dst + 3] = ClampFloat(accum_alpha / weight_sum, 0.0f, 1.0f);
			}
		}
	} else {
		ForwardConvolver convolver(radius_count, weights);
		std::vector<double> values((size_t)radius_count);
		std::vector<double> alpha_conv;
		std::vector<double> rgb_conv[3];
		std::vector<double> weight_sum_conv;
		std::vector<double> ones((size_t)radius_count, 1.0);
		convolver.Convolve(ones, weight_sum_conv);

		for (A_long ai = 0; ai < angular_count; ++ai) {
			for (A_long ri = 0; ri < radius_count; ++ri) {
				const size_t src_idx = ((size_t)ai * radius_count + ri) * 4;
				values[(size_t)ri] = polar.rgba[src_idx + 3];
			}
			convolver.Convolve(values, alpha_conv);

			for (int c = 0; c < 3; ++c) {
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t src_idx = ((size_t)ai * radius_count + ri) * 4;
					const double alpha = polar.rgba[src_idx + 3];
					values[(size_t)ri] = polar.rgba[src_idx + c] * alpha;
				}
				convolver.Convolve(values, rgb_conv[c]);
			}

			for (A_long ri = 0; ri < radius_count; ++ri) {
				const size_t dst = ((size_t)ai * radius_count + ri) * 4;
				const double weighted_alpha = alpha_conv[(size_t)ri];
				if (weighted_alpha > 1.0e-8) {
					for (int c = 0; c < 3; ++c) {
						blurred.rgba[dst + c] = (float)(rgb_conv[c][(size_t)ri] / weighted_alpha);
					}
				}
				blurred.rgba[dst + 3] = ClampFloat((float)(weighted_alpha / weight_sum_conv[(size_t)ri]), 0.0f, 1.0f);
			}
		}
	}
	return blurred;
}

static FloatImage BuildZoomAEXOuterOnlyPolar(
	const FloatImage &polar,
	const std::vector<float> &weights,
	const std::vector<A_u_char> &eligibility,
	const std::vector<float> &span_plane,
	const std::vector<float> &source_scalar_plane,
	A_long outer_strength,
	const std::vector<float> *inner_weights = nullptr,
	A_long inner_strength = 0,
	const std::vector<float> *outer_fade_weights = nullptr,
	A_long outer_fade_span = 0,
	const std::vector<float> *inner_fade_weights = nullptr,
	A_long inner_fade_span = 0,
	bool preserve_noise_zero_seed = false,
	bool use_fade_factor_plane = false,
	const std::vector<float> *fade_factor_plane = nullptr)
{
	const A_long radius_count = polar.width;
	const A_long angular_count = polar.height;
	FloatImage normalized;
	normalized.width = radius_count;
	normalized.height = angular_count;
	const size_t cell_count = (size_t)angular_count * radius_count;
	normalized.rgba.assign(cell_count * 4, 0.0f);
	std::vector<float> accum_alpha(cell_count, 0.0f);
	std::vector<float> max_alpha(cell_count, 0.0f);
	std::atomic<A_long> next_row(0);
	const unsigned hardware_threads = std::thread::hardware_concurrency();
	const A_long thread_count = std::max<A_long>(
		1, std::min<A_long>(32, std::min<A_long>(angular_count,
			hardware_threads ? (A_long)hardware_threads : 1)));
	// Allocate every worker-owned buffer before launching any thread.  A
	// bad_alloc is then propagated through the public render exception boundary
	// rather than escaping a worker and terminating the host process.
	std::vector<std::vector<float> > worker_source_scalar(
		(size_t)thread_count, std::vector<float>((size_t)radius_count));
	std::vector<std::thread> threads;
	threads.reserve((size_t)thread_count);
	try {
	for (A_long thread_index = 0; thread_index < thread_count; ++thread_index) {
		threads.emplace_back([&, thread_index]() {
			std::vector<float> &faded_source_scalar = worker_source_scalar[(size_t)thread_index];
			for (;;) {
				const A_long ai = next_row.fetch_add(1, std::memory_order_relaxed);
				if (ai >= angular_count) break;
				const size_t row_cell = (size_t)ai * radius_count;
				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					// B150 receives the size-factor plane (+0x48), while the later
					// strength scatter consumes the noise-composed span plane.  The
					// SV0 fade tuples have a size factor of exactly one even where a
					// noise-composed scatter span falls below one.  The bounded Size x
					// Edge fixture instead carries the sampled component factor here.
					// C46: an explicit size plane also owns the no-fade prepass.
					const float factor = fade_factor_plane ? (*fade_factor_plane)[cell] : (outer_fade_span > 0 || inner_fade_span > 0)
						? (use_fade_factor_plane
							? (fade_factor_plane ? (*fade_factor_plane)[cell] : span_plane[cell])
							: 1.0f)
						: span_plane[cell];
					float source_scalar = source_scalar_plane[cell];
					// B25A/B26B: UCOMISS + JZ clears all channels on unordered.
					const bool zero_seed = polar.rgba[rgba + 3] == 0.0f ||
						std::isnan(polar.rgba[rgba + 3]) || std::isnan(factor) ||
						(factor == 0.0f && !preserve_noise_zero_seed);
					if (zero_seed ||
						((outer_fade_span > 0 || inner_fade_span > 0) &&
						(polar.rgba[rgba + 3] == 0.0f || source_scalar == 0.0f))) {
						source_scalar = 0.0f;
					} else if (outer_fade_span > 0 || inner_fade_span > 0) {
						float weighted_alpha = polar.rgba[rgba + 3];
						float weight_sum = 1.0f;
						const float inverse_factor = RadialF32Div(1.0f, factor);
						const A_long outer_limit = std::min<A_long>(ri,
							(A_long)RadialF32Mul((float)outer_fade_span, factor));
						for (A_long k = 1; outer_fade_weights && k < outer_limit; ++k) {
							const A_long table_index = (A_long)RadialF32Mul((float)k, inverse_factor);
							const float weight = (*outer_fade_weights)[(size_t)table_index];
							weighted_alpha = RadialF32Add(weighted_alpha, RadialF32Mul(
								weight, polar.rgba[(cell - (size_t)k) * 4 + 3]));
							weight_sum = RadialF32Add(weight_sum, weight);
						}
						const A_long inner_limit = std::min<A_long>(radius_count - ri,
							(A_long)RadialF32Mul((float)inner_fade_span, factor));
						for (A_long k = 1; inner_fade_weights && k < inner_limit; ++k) {
							const A_long table_index = (A_long)RadialF32Mul((float)k, inverse_factor);
							const float weight = (*inner_fade_weights)[(size_t)table_index];
							weighted_alpha = RadialF32Add(weighted_alpha, RadialF32Mul(
								weight, polar.rgba[(cell + (size_t)k) * 4 + 3]));
							weight_sum = RadialF32Add(weight_sum, weight);
						}
						source_scalar = RadialF32Div(weighted_alpha, weight_sum);
					}
					faded_source_scalar[(size_t)ri] = source_scalar;
					for (int c = 0; c < 3; ++c) {
						normalized.rgba[rgba + c] = zero_seed ? 0.0f
							: RadialF32Mul(source_scalar, polar.rgba[rgba + c]);
					}
					accum_alpha[cell] = source_scalar;
					max_alpha[cell] = source_scalar;
				}

				for (A_long source_ri = 0; source_ri < radius_count; ++source_ri) {
					const size_t source_cell = row_cell + source_ri;
					const float source_scalar = faded_source_scalar[(size_t)source_ri];
					const float span = span_plane[source_cell];
					if (eligibility[source_cell] == 0 || source_scalar == 0.0f ||
						std::isnan(source_scalar) || span == 0.0f || std::isnan(span)) continue;
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
								contribution, normalized.rgba[destination_rgba + c]);
						}
						accum_alpha[destination_cell] = RadialF32Add(
							alpha_weight, accum_alpha[destination_cell]);
						if (max_alpha[destination_cell] < alpha_weight) {
							max_alpha[destination_cell] = alpha_weight;
						}
					}
					if (inner_weights && inner_strength > 0) {
						const A_long inner_strength_limit = (A_long)RadialF32Mul((float)inner_strength, span);
						// The AEX reserves radius cell zero for the center sample.  Inner
						// propagation stops at radius one rather than writing into cell zero.
						const A_long inner_limit = std::min<A_long>(source_ri, inner_strength_limit);
						for (A_long k = 1; k < inner_limit; ++k) {
							const A_long table_index = (A_long)RadialF32Mul((float)k, inverse_span);
							if (table_index < 0 || table_index >= (A_long)inner_weights->size()) continue;
							const float alpha_weight = RadialF32Mul(
								source_scalar, (*inner_weights)[(size_t)table_index]);
							const size_t destination_cell = source_cell - k;
							const size_t destination_rgba = destination_cell * 4;
							for (int c = 0; c < 3; ++c) {
								const float contribution = RadialF32Mul(
									alpha_weight, polar.rgba[source_rgba + c]);
								normalized.rgba[destination_rgba + c] = RadialF32Add(
									contribution, normalized.rgba[destination_rgba + c]);
							}
							accum_alpha[destination_cell] = RadialF32Add(
								alpha_weight, accum_alpha[destination_cell]);
							if (max_alpha[destination_cell] < alpha_weight) {
								max_alpha[destination_cell] = alpha_weight;
							}
						}
					}
				}

				for (A_long ri = 0; ri < radius_count; ++ri) {
					const size_t cell = row_cell + ri;
					const size_t rgba = cell * 4;
					const float denominator = accum_alpha[cell];
					if (max_alpha[cell] == 0.0f || std::isnan(max_alpha[cell])) {
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
	} catch (...) {
		for (std::thread &thread : threads) if (thread.joinable()) thread.join();
		throw;
	}
	for (std::thread &thread : threads) thread.join();
	return normalized;
}


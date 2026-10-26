// Included by OLMKiraKira.cpp inside its anonymous namespace.
template <typename PixelT>
static PF_Err RenderTyped(PF_EffectWorld *input, PF_EffectWorld *output, const OLMKiraKiraInfo &info, short bitdepth, float smart_scale = 0.0f)
{
	const A_long w = smart_scale > 0.0f ? input->width : output->width;
	const A_long h = smart_scale > 0.0f ? input->height : output->height;
	if (w <= 0 || h <= 0 || input->width != w || input->height != h ||
		output->width > w || output->height > h) return PF_Err_BAD_CALLBACK_PARAM;
	const KiraKiraDebugConfig debug = LoadKiraKiraDebugConfig();

	const PF_FpLong comp_width = info.comp_width > 0.0 ? info.comp_width : (PF_FpLong)w;
	// Typed AEX owners (18114ccac..18114cd6c) use DIVSS on X num/den,
	// then MULSS and CVTTSS2SI. Preserve the historical Classic path.
	const double render_scale_ratio = smart_scale > 0.0f ? smart_scale :
		(comp_width > 0.0 ? (double)w / comp_width : 1.0);
	const bool use_approximated_input = info.approximated_input && render_scale_ratio > 0.5;
	const A_long work_w = use_approximated_input ? std::max<A_long>(1, w / 2) : w;
	const A_long work_h = use_approximated_input ? std::max<A_long>(1, h / 2) : h;
	const double length_scale = use_approximated_input
		? render_scale_ratio * 0.5
		: render_scale_ratio;
	auto scaled_len = [&](A_long value) -> A_long {
		if (smart_scale > 0.0f)
			return std::max<A_long>(0, (A_long)((float)value * (float)length_scale));
		return std::max<A_long>(0, (A_long)((double)value * length_scale));
	};

	const std::vector<FloatRGBA> source_pixels = ReadPixels<PixelT>(input);
	const std::vector<FloatRGBA> working_pixels = use_approximated_input
		? (UsesRecoveredApproximation(info)
			? ResizeLinearRGBA(source_pixels, w, h, work_w, work_h)
			: ResizeNearestRGBA(source_pixels, w, h, work_w, work_h))
		: source_pixels;
	const A_long work_width = work_w;
	const A_long work_height = work_h;
	std::vector<float> seed = MakeSeed(working_pixels, work_width, work_height, info);
	const A_long passes = BlurModePasses(info.blur_mode);
	const double glow_rotation = info.glow_rotation;
	const bool color_owner = UsesRecoveredColorPipeline(info);
    const std::vector<float> zero_ray(seed.size(), 0.0f);
	auto make_ray = [&](A_long raw_len, double angle) -> std::vector<float> {
		const A_long len = scaled_len(raw_len);
		if (raw_len <= 0 || len <= 0) return zero_ray;
		if (color_owner) {
            std::vector<float> result(seed.size()), plane((size_t)work_width*work_height);
            for (int c=0; c<4; ++c) {
                for (size_t i=0; i<plane.size(); ++i) plane[i]=seed[i*4+c];
                const auto ray=RotatedAxisBoxBlur(plane,work_width,work_height,len,angle,passes,info.blur_mode,true,true,false);
                for (size_t i=0; i<plane.size(); ++i) result[i*4+c]=ray[i];
            }
            return result;
        }
        return RotatedAxisBoxBlur(seed, work_width, work_height, len, angle, passes, info.blur_mode,
			(info.channel == 1 || info.channel == 2 || info.channel == 4) &&
				(info.strength_multiplier == 1.0 || UsesRecoveredSeedPipeline(info)),
			UsesRecoveredSeedPipeline(info));
	};
	std::vector<float> vertical = make_ray(info.vertical_length, 90.0 + glow_rotation);
	std::vector<float> horizontal = make_ray(info.horizontal_length, glow_rotation);
	std::vector<float> diagonal = make_ray(info.diagonal_length, 45.0 + glow_rotation);
	// The three typed Windows owners build the direction table as
	// {rotation+90, rotation, rotation+45, rotation+135, 0}.  Although -45
	// describes the same undirected axis, Mode 4's directed recurrence and
	// fixed-point warp rounding make the two representatives bit-distinct.
	std::vector<float> diagonal2 = make_ray(info.diagonal2_length, 135.0 + glow_rotation);
	std::vector<float> highlight = zero_ray;
	const A_long highlight_radius = scaled_len(info.highlight_radius);
	if (highlight_radius > 0 &&
		(info.blur_mode == 1 || info.blur_mode == 2 || info.blur_mode == 4)) {
		// The actual Mode-4 Highlight branch shares Mode 2's three isotropic
		// box-filter calls.  It does not use the directional Mode-4 recurrence.
		const A_long highlight_passes = info.blur_mode == 1 ? 1 : 3;
		if (color_owner) {
            highlight.resize(seed.size());
            std::vector<float> plane((size_t)work_width*work_height);
            for (int c=0; c<4; ++c) {
                for (size_t i=0; i<plane.size(); ++i) plane[i]=seed[i*4+c];
                const auto ray=olm::kirakira::highlight_isotropic_box_blur(plane,work_width,work_height,highlight_radius*2+1,highlight_passes,false);
                for (size_t i=0; i<plane.size(); ++i) highlight[i*4+c]=ray[i];
            }
        } else {
            highlight = olm::kirakira::highlight_isotropic_box_blur(
                seed, work_width, work_height, highlight_radius * 2 + 1, highlight_passes);
        }
	}

    if (highlight_radius > 0 && info.blur_mode == 3) {
        if (color_owner) {
            std::vector<float> plane((size_t)work_width * work_height);
            for (int c = 0; c < 4; ++c) {
                for (size_t i = 0; i < plane.size(); ++i) plane[i] = seed[i*4+c];
                const auto ray = olm::kirakira::highlight_gaussian(
                    plane, work_width, work_height, highlight_radius);
                for (size_t i = 0; i < plane.size(); ++i) highlight[i*4+c] = ray[i];
            }
        } else {
            highlight = olm::kirakira::highlight_gaussian(
                seed, work_width, work_height, highlight_radius);
        }
    }

	// FUN_18114f4a0 loads Brightness Gain directly from state+0x608 into the
	// trailing argument of both aggregation vtable calls. Natural exported
	// Mode-1 capture confirms ray * Brightness Gain before composition; the
	// historical 0.62 PNG-fit scaffold is not part of the AEX owner path.
	float scale = (float)info.brightness_gain;
	const float highlight_scale = (float)info.brightness_gain;
	if (info.strength_multiplier <= 1.0e-6 && !UsesRecoveredSeedPipeline(info)) {
		scale = 127.0 / 255.0;
	}
	std::vector<FloatRGBA> glow((size_t)work_width * work_height);
	// The exported owner stores the UI Merge mode at state+0x44 for the outer
	// writer, but initializes the aggregation selector at state+0x48 to one.
	// Consequently both public merge choices use FUN_18114fd90 here; only the
	// downstream composition changes with info.merge_mode.
    if (color_owner) {
        const std::vector<float>* rays[]={&vertical,&horizontal,&diagonal,&diagonal2,&highlight};
        for (size_t i=0; i<glow.size(); ++i) {
            auto &g=glow[i];
            // Original helper returns Length even for normalized Gaussian rays.
            // The color aggregator consumes that divisor independently, using
            // the scaled helper lengths when rendering approximated input.
            float norms[5] = {(float)scaled_len(info.vertical_length),(float)scaled_len(info.horizontal_length),
                (float)scaled_len(info.diagonal_length),(float)scaled_len(info.diagonal2_length),
                (float)((highlight_radius*2+1)*(highlight_radius*2+1))};
            if (info.blur_mode == 2) {
                for (int c=0;c<4;++c) norms[c]=norms[c]*norms[c]*norms[c];
                norms[4]=norms[4]*norms[4]; norms[4]=norms[4]*norms[4];
            }
            int ray_index=0;
            for (const auto *ray:rays) {
                const float divisor=norms[ray_index++];
                const float norm=divisor == 0.0f ? 0.0f : 1.0f/divisor;
                const float alpha=(*ray)[i*4+3];
                // Original 18114f152 COMISD / JBE skips unordered alpha too.
                // Finite source extremes can overflow into NaN in the filters.
                if (!((double)alpha > 0.001)) continue;
                const float inv=1.0f/alpha;
                const float a=Clamp01(alpha*norm);
                g.r = inv*(*ray)[i*4]*a*scale+g.r;
                g.g = inv*(*ray)[i*4+1]*a*scale+g.g;
                g.b = inv*(*ray)[i*4+2]*a*scale+g.b;
                g.a = a+g.a;
            }
            if (g.a>0.0f) {
                g.a=Clamp01(g.a);
                const float inv=1.0f/g.a;
                g.r=inv*g.r; g.g=inv*g.g; g.b=inv*g.b;
            }
        }
    } else {
    AddColoredUnion(glow, vertical, info.vertical_color, info.vertical_use_ramp, info.vertical_ramp, scale);
	AddColoredUnion(glow, horizontal, info.horizontal_color, info.horizontal_use_ramp, info.horizontal_ramp, scale);
	AddColoredUnion(glow, diagonal, info.diagonal_color, info.diagonal_use_ramp, info.diagonal_ramp, scale);
	// FUN_18114f4a0 owns four directional slots followed by Highlight.
	// Preserve that addition order because float32 sums are not associative.
	AddColoredUnion(glow, diagonal2, info.diagonal2_color, info.diagonal2_use_ramp, info.diagonal2_ramp, scale);
	AddColoredUnion(glow, highlight, info.highlight_color, info.highlight_use_ramp, info.highlight_ramp, highlight_scale);
	for (FloatRGBA &g : glow) {
		if (g.a > 1.0e-6f) {
			// FUN_18114fd90 uses one reciprocal and three multiplies.
			// F09 proves PF16/32; C04 proves unit-exponent PF8 Alpha. C07
			// closes the remaining scalar Alpha box seed operations, allowing
			// the same original normalization for non-unit strengths too.
			// C13 pairs it through the directional Gaussian pipeline as well.
			// Other PF8 seed branches retain their unresolved boundary.
			if (bitdepth != 8 ||
				(info.channel == 1 && info.strength_multiplier == 1.0) ||
				UsesRecoveredSeedPipeline(info)) {
				const float inverse_alpha = 1.0f / g.a;
				g.r *= inverse_alpha;
				g.g *= inverse_alpha;
				g.b *= inverse_alpha;
			} else {
				g.r /= g.a;
				g.g /= g.a;
				g.b /= g.a;
			}
		}
	}
	}
	std::vector<FloatRGBA> composed((size_t)work_width * work_height);
	for (A_long y = 0; y < work_height; ++y) {
		for (A_long x = 0; x < work_width; ++x) {
			const size_t idx = (size_t)y * work_width + x;
			const FloatRGBA &src = working_pixels[idx];
			FloatRGBA &out = composed[idx];
			if (info.merge_mode == 2) {
				out = ComposeMerge2Pixel(
					glow[idx], src, (float)info.glow_opacity, (float)info.source_opacity);
			} else {
				out = ComposePremultiplyPixel(
					glow[idx], src, (float)info.glow_opacity, (float)info.source_opacity);
			}
		}
	}
	std::vector<FloatRGBA> glow_full;
	std::vector<FloatRGBA> output_pixels;
	if (use_approximated_input && UsesRecoveredApproximation(info)) {
		glow_full = ResizeLinearRGBA(glow, work_width, work_height, w, h);
		output_pixels.resize((size_t)w*h);
		for (size_t i=0; i<output_pixels.size(); ++i) {
			output_pixels[i] = info.merge_mode == 2
				? ComposeMerge2Pixel(glow_full[i], source_pixels[i], (float)info.glow_opacity, (float)info.source_opacity)
				: ComposePremultiplyPixel(glow_full[i], source_pixels[i], (float)info.glow_opacity, (float)info.source_opacity);
		}
	} else if (use_approximated_input) {
		glow_full = ResizeNearestRGBA(glow, work_width, work_height, w, h);
		output_pixels = ResizeNearestRGBA(composed, work_width, work_height, w, h);
		if (HasZeroRays(info)) {
			// Original typed owners resize glow, then compose with the original
			// full-resolution source. With all rays disabled, 18114f4a0 leaves
			// every glow lane zero; neither resize can affect that invariant.
			// Active-ray IPP interpolation remains a separate proof boundary.
			for (size_t i = 0; i < output_pixels.size(); ++i) {
				output_pixels[i] = info.merge_mode == 2
					? ComposeMerge2Pixel(glow_full[i], source_pixels[i], (float)info.glow_opacity, (float)info.source_opacity)
					: ComposePremultiplyPixel(glow_full[i], source_pixels[i], (float)info.glow_opacity, (float)info.source_opacity);
			}
		}
	} else {
		glow_full = std::move(glow);
		output_pixels = std::move(composed);
	}

	// Original outer writers ignore output origin: the negotiated output takes
	// the top-left prefix of each full-source row, not an origin-shifted crop.
	for (A_long y = 0; y < output->height; ++y) {
		for (A_long x = 0; x < output->width; ++x) {
			const size_t idx = (size_t)y * w + x;
			const FloatRGBA &src = source_pixels[idx];
			const float glow_a = Clamp01(glow_full[idx].a * (float)info.glow_opacity);
			const FloatRGBA glow_normalized = glow_full[idx];
			const FloatRGBA &out = output_pixels[idx];
			KiraKiraDebugDumpPoint(debug, bitdepth, w, h, x, y, src, glow_normalized, glow_a, out);
			// The actual integer-depth outer writers use CVTTSS2SI after
			// clamp and scale for both merge modes.
			StoreWorldPixel<PixelT>(output, x, y, PixelTraits<PixelT>::WriteAexTruncate(out));
		}
	}
	return PF_Err_NONE;
}

static PF_Err RenderWorld(PF_EffectWorld *input, PF_EffectWorld *output, const OLMKiraKiraInfo &info, short bitdepth, float smart_scale = 0.0f)
{
	if (bitdepth == 8) return RenderTyped<PF_Pixel8>(input, output, info, bitdepth, smart_scale);
	if (bitdepth == 16) return RenderTyped<PF_Pixel16>(input, output, info, bitdepth, smart_scale);
	if (bitdepth == 32) return RenderTyped<PF_PixelFloat>(input, output, info, bitdepth, smart_scale);
	return PF_Err_BAD_CALLBACK_PARAM;
}

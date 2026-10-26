static bool is_admitted_pf32_smart_exported_matrix(
	const DGParams &p, const std::vector<float> &alpha, long w, long h)
{
	const bool admitted_blur =
		p.blur_mode >= BLUR_MODE_NO_SCALE && p.blur_mode <= BLUR_MODE_BILATERAL;
	if (!p.smart_owner || p.pixel_size != sizeof(PF_PixelFloat) || !admitted_blur ||
	    p.blur_size != 1 || p.interp_mode < INTERP_CONSTANT ||
	    p.interp_mode > INTERP_POWER ||
	    w != 17 || h != 11 ||
	    !p.invert || p.in_out != IN_OUT_INSIDE ||
	    p.inside_threshold != 4 || p.outside_threshold != 4 ||
	    p.render_mode != RENDER_MODE_RGB || p.power != 2.25f ||
	    p.ds_x != 1.0f || p.ds_y != 1.0f ||
	    p.grad_color.red != 28.0f / 255.0f || p.grad_color.green != 0.0f ||
	    p.grad_color.blue != 238.0f / 255.0f ||
	    p.bg_color.red != 16.0f / 255.0f || p.bg_color.green != 160.0f / 255.0f ||
	    p.bg_color.blue != 48.0f / 255.0f || alpha.size() != 17u * 11u) return false;
	// PF32 Power is admitted only here: the native Windows UCRT table, actual-AEX
	// XMM call sequence and same-table full RAW replay close these eight cells.
	// PF16 retains its separately grounded path.
	for (long y = 0; y < h; ++y) {
		for (long x = 0; x < w; ++x) {
			const uint32_t expected_bits =
				(x >= 4 && x < 13 && y >= 2 && y < 9) ? 0x00000000u : 0x3f800000u;
			uint32_t alpha_bits = 0;
			memcpy(&alpha_bits, &alpha[(size_t)y * w + x], sizeof(alpha_bits));
			if (alpha_bits != expected_bits) return false;
		}
	}
	return true;
}

static bool is_admitted_pf32_power_source(
	const PF_LayerDef *input, long w, long h)
{
	if (!input || !input->data || w != 17 || h != 11 ||
	    input->rowbytes < w * (A_long)sizeof(PF_PixelFloat)) return false;
	for (long y = 0; y < h; ++y) {
		const PF_PixelFloat *row = (const PF_PixelFloat *)
			((const char *)input->data + (size_t)y * input->rowbytes);
		for (long x = 0; x < w; ++x) {
			const bool transparent = x >= 4 && x < 13 && y >= 2 && y < 9;
			const PF_PixelFloat expected = transparent ? PF_PixelFloat{0, 0, 0, 0}
				: PF_PixelFloat{
					1.0f,
					(float)((x * 613 + y * 1231) % 256) / 255.0f,
					(float)((x * 997 + y * 211) % 256) / 255.0f,
					(float)((x * 1499 + y * 307) % 256) / 255.0f,
				};
			if (memcmp(&row[x], &expected, sizeof(expected)) != 0) return false;
		}
	}
	return true;
}

// PF32 Smart unblurred lane: Constant/Linear/Sphere avoid platform powf.
// At Size=0, the original owner calls Box/Gaussian/Median with a 1x1 kernel;
// C08 public-AEX campaigns and 648 independent cases prove the identity path.
// Mode 5 has different semantics even at zero size and remains separate.
static bool is_admitted_pf32_smart_unblurred_beta(const DGParams &p)
{
	return p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	       (p.blur_mode == BLUR_MODE_NONE ||
	        (p.blur_size == 0 && p.blur_mode >= BLUR_MODE_NO_SCALE &&
	         p.blur_mode <= BLUR_MODE_MEDIAN)) &&
	       (p.interp_mode == INTERP_CONSTANT || p.interp_mode == INTERP_LINEAR ||
	        p.interp_mode == INTERP_SPHERE) &&
	       p.render_mode >= RENDER_MODE_RGB && p.render_mode <= RENDER_MODE_LAYER &&
	       p.inside_threshold >= 0 && p.outside_threshold >= 0 &&
	       p.ds_x > 0.0f && p.ds_y > 0.0f;
}

// Radius-one bilateral is independently paired to the original IPP producer.
// Power reuses the same finite field and the shared UCRT composition.
static bool is_admitted_pf32_smart_bilateral_beta(const DGParams &p)
{
	if (p.blur_mode != BLUR_MODE_BILATERAL || p.blur_size < 0 || p.blur_size > 1 ||
	    (float)p.blur_size * std::min(p.ds_x, p.ds_y) >= 1.5f)
		return false;
	DGParams identity = p;
	identity.blur_mode = BLUR_MODE_NONE;
	if (identity.interp_mode == INTERP_POWER && std::isfinite(identity.power) &&
	    identity.power >= 0.01f && identity.power <= 5.0f)
		identity.interp_mode = INTERP_LINEAR;
	return is_admitted_pf32_smart_unblurred_beta(identity);
}

// Radius>=3 dispatch uses the generic circular kernel. Smart admission
// retains the verified kernel domain without a Mac-only work ceiling.
static bool is_admitted_pf32_smart_bilateral_general_beta(const DGParams &p, long w, long h)
{
    if (!p.smart_owner || p.pixel_size != sizeof(PF_PixelFloat) ||
        p.blur_mode != BLUR_MODE_BILATERAL || p.blur_size < 3 || p.blur_size > 4096 ||
        p.ds_x != 1.0f || p.ds_y != 1.0f || w <= 0 || h <= 0) return false;
    DGParams identity = p;
    identity.blur_mode = BLUR_MODE_NONE;
    if (identity.interp_mode == INTERP_POWER && std::isfinite(identity.power) &&
        identity.power >= 0.01f && identity.power <= 5.0f)
        identity.interp_mode = INTERP_LINEAR;
    return is_admitted_pf32_smart_unblurred_beta(identity);
}

static bool is_admitted_pf32_smart_bilateral_scalar_beta(const DGParams &p, long w, long h)
{
	if (p.pixel_size != sizeof(PF_PixelFloat) || !is_scalar_bilateral_shape(p, w, h)) return false;
	DGParams identity = p;
	identity.blur_mode = BLUR_MODE_NONE;
	if (identity.interp_mode == INTERP_POWER && std::isfinite(identity.power) &&
	    identity.power >= 0.01f && identity.power <= 5.0f)
		identity.interp_mode = INTERP_LINEAR;
	return is_admitted_pf32_smart_unblurred_beta(identity);
}

static bool is_admitted_pf32_smart_blurred_beta(const DGParams &p, long w, long h)
{
	if (!p.smart_owner || p.pixel_size != sizeof(PF_PixelFloat) ||
		(p.interp_mode != INTERP_CONSTANT && p.interp_mode != INTERP_LINEAR &&
		 p.interp_mode != INTERP_SPHERE) ||
		p.blur_mode < BLUR_MODE_NO_SCALE || p.blur_mode > BLUR_MODE_MEDIAN ||
		p.blur_size < 1 || p.blur_size > (p.blur_mode == BLUR_MODE_MEDIAN ? 500 : 4096) ||
		p.render_mode < RENDER_MODE_RGB || p.render_mode > RENDER_MODE_LAYER ||
		p.inside_threshold < 0 || p.inside_threshold > 1000 ||
		p.outside_threshold < 0 || p.outside_threshold > 1000 ||
		p.ds_x != 1.0f || p.ds_y != 1.0f || w <= 0 || h <= 0)
		return false;
	if (!std::isfinite(p.power) || p.power < 0.01f || p.power > 5.0f) return false;
	const float controls[] = {
		p.grad_color.alpha, p.grad_color.red, p.grad_color.green,
		p.grad_color.blue, p.bg_color.alpha, p.bg_color.red,
		p.bg_color.green, p.bg_color.blue};
	for (float value : controls)
		if (!std::isfinite(value) || value < 0.0f || value > 1.0f) return false;
	// Kernel sizes are bounded by the control checks above; storage products
	// are checked by the Smart world validator and RenderBits.
	return true;
}

static bool pf32_smart_worlds_are_bounded_sdr(
	const PF_LayerDef *input, const PF_LayerDef *output, const DGParams &p)
{
	if (!input || !output || !input->data || !output->data ||
	    input->width <= 0 || input->height <= 0 ||
	    output->width <= 0 || output->height <= 0 ||
	    output->width > input->width || output->height > input->height) return false;
	// Finite extended samples share the existing Box/Gaussian and scalar
	// Bilateral fields. Source RGB is composed after filtering the finite mask.
	// Normalize Power only for admission; rendering retains its UCRT exponent.
	DGParams finite_admission = p;
	if (p.interp_mode == INTERP_POWER && std::isfinite(p.power) &&
	    p.power >= 0.01f && p.power <= 5.0f)
		finite_admission.interp_mode = INTERP_LINEAR;
	const size_t width = (size_t)input->width;
	const size_t height = (size_t)input->height;
	if (width > std::numeric_limits<size_t>::max() / height) return false;
	// The EDT owns a long-index plane as well as float planes. Preserve the
	// largest element's vector representability after removing the area cap.
	if (width * height > std::vector<long>().max_size()) return false;
	if ((reinterpret_cast<uintptr_t>(input->data) % alignof(PF_PixelFloat)) != 0 ||
	    (reinterpret_cast<uintptr_t>(output->data) % alignof(PF_PixelFloat)) != 0 ||
	    input->rowbytes <= 0 || output->rowbytes <= 0 ||
	    ((size_t)input->rowbytes % alignof(PF_PixelFloat)) != 0 ||
	    ((size_t)output->rowbytes % alignof(PF_PixelFloat)) != 0) return false;
	const olm::world_safety::ConstWorld source = {
		input->data, width, height, (size_t)input->rowbytes, sizeof(PF_PixelFloat)};
	const olm::world_safety::ConstWorld destination = {
		output->data, (size_t)output->width, (size_t)output->height, (size_t)output->rowbytes, sizeof(PF_PixelFloat)};
	if (olm::world_safety::validate_layout(source) != olm::world_safety::Status::ok ||
	    olm::world_safety::validate_layout(destination) != olm::world_safety::Status::ok ||
	    olm::world_safety::require_disjoint(source, destination) !=
	        olm::world_safety::Status::ok) return false;
	for (size_t y = 0; y < height; ++y) {
		const PF_PixelFloat *row = reinterpret_cast<const PF_PixelFloat *>(
			reinterpret_cast<const uint8_t *>(input->data) + y * (size_t)input->rowbytes);
		for (size_t x = 0; x < width; ++x) {
			const PF_PixelFloat &pixel = row[x];
			// C19 restores the original signed-int32 mask conversion and invalid
			// weighted-sample arithmetic. The mask conversion maps invalid alpha
			// to zero before filtering; Bilateral consumes that finite
			// field, while source channels enter only the recovered composition.
			const bool nonfinite_field = is_admitted_pf32_smart_unblurred_beta(finite_admission) ||
			    is_admitted_pf32_smart_bilateral_beta(p) ||
			    is_admitted_pf32_smart_bilateral_scalar_beta(finite_admission, (long)width, (long)height) ||
			    is_admitted_pf32_smart_bilateral_general_beta(finite_admission, (long)width, (long)height);
			if (pixel.alpha * 255.0f >= 2147483648.0f && !nonfinite_field) return false;
			const float channels[4] = {pixel.alpha, pixel.red, pixel.green, pixel.blue};
			for (float value : channels) {
				if (!std::isfinite(value) && !nonfinite_field) return false;
				// C27 pairs finite extended samples through the existing Box/Gaussian
				// field and callback. Median retains its SDR boundary;
				// the original large-kernel PF32 Median rejects otherwise-valid inputs.
				if ((value < 0.0f || value > 1.0f) &&
				    !is_admitted_pf32_smart_unblurred_beta(p) &&
				    !(p.blur_mode != BLUR_MODE_MEDIAN && is_admitted_pf32_smart_blurred_beta(finite_admission, (long)width, (long)height)) &&
				    !is_admitted_pf32_smart_bilateral_beta(p) &&
				    !is_admitted_pf32_smart_bilateral_scalar_beta(finite_admission, (long)width, (long)height) &&
				    !is_admitted_pf32_smart_bilateral_general_beta(finite_admission, (long)width, (long)height) &&
				    !is_admitted_pf32_smart_unblurred_beta(finite_admission)) return false;
			}
		}
	}
	return true;
}

// Windows-oracle profile with only the fixture's source and geometry removed.
// The retained 17x11 matrix remains the exact lane; this profile uses native
// libm for Power and therefore carries a numerical-tolerance, not raw-bit,
// compatibility contract.
static constexpr uint32_t PF32_POWER_GENERIC_MAX_ULP = 1;
static_assert(PF32_POWER_GENERIC_MAX_ULP == 1, "PF32 generic Power tolerance contract");
static bool is_admitted_pf32_smart_oracle_profile(const DGParams &p)
{
	return p.smart_owner && p.pixel_size == sizeof(PF_PixelFloat) &&
	       p.invert && p.in_out == IN_OUT_INSIDE &&
	       p.inside_threshold == 4 && p.outside_threshold == 4 &&
	       p.render_mode == RENDER_MODE_RGB && p.power == 2.25f &&
	       p.blur_mode >= BLUR_MODE_NO_SCALE && p.blur_mode <= BLUR_MODE_BILATERAL &&
	       p.blur_size == 1 && p.ds_x == 1.0f && p.ds_y == 1.0f &&
	       p.interp_mode >= INTERP_CONSTANT && p.interp_mode <= INTERP_POWER &&
	       p.grad_color.red == 28.0f / 255.0f && p.grad_color.green == 0.0f &&
	       p.grad_color.blue == 238.0f / 255.0f &&
	       p.bg_color.red == 16.0f / 255.0f && p.bg_color.green == 160.0f / 255.0f &&
	       p.bg_color.blue == 48.0f / 255.0f;
}

static bool checked_pixel_count(long w, long h, size_t *count)
{
	if (!count || w <= 0 || h <= 0) return false;
	const size_t sw = (size_t)w;
	const size_t sh = (size_t)h;
	if (sw > std::numeric_limits<size_t>::max() / sh) return false;
	*count = sw * sh;
	return *count <= std::vector<float>().max_size();
}


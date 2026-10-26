// Included by OLMColorKey.cpp; preserves the single translation unit.
template <typename PixelT>
struct OLMCKPixelTraits;

template <>
struct OLMCKPixelTraits<PF_Pixel8> {
	static float max_chan() { return 255.0f; }
	static float native_key_epsilon() { return 0.5f / 255.0f; }
	static bool is_16bpc() { return false; }
	static bool is_32bpc() { return false; }
	// FUN_180011450 normalizes source bytes by FLOAT32 inverse multiplication.
	static float r(const PF_Pixel8 &p) { return (float)p.red * 0.003921568859368563f; }
	static float g(const PF_Pixel8 &p) { return (float)p.green * 0.003921568859368563f; }
	static float b(const PF_Pixel8 &p) { return (float)p.blue * 0.003921568859368563f; }
	static float a(const PF_Pixel8 &p) { return (float)p.alpha * 0.003921568859368563f; }
	static void zero(PF_Pixel8 &p) { p.alpha = p.red = p.green = p.blue = 0; }
	static void zero_alpha(PF_Pixel8 &p) { p.alpha = 0; }
	static void replace_rgb(PF_Pixel8 &p, const PF_PixelFloat &rep)
	{
		p.red = (A_u_char)ClampValue<int>((int)(rep.red * 255.0f), 0, 255);
		p.green = (A_u_char)ClampValue<int>((int)(rep.green * 255.0f), 0, 255);
		p.blue = (A_u_char)ClampValue<int>((int)(rep.blue * 255.0f), 0, 255);
	}
	static void scale(PF_Pixel8 &dst, const PF_Pixel8 &src, float weight)
	{
		dst.red = (A_u_char)ClampValue<int>((int)((float)src.red * weight + 0.5f), 0, 255);
		dst.green = (A_u_char)ClampValue<int>((int)((float)src.green * weight + 0.5f), 0, 255);
		dst.blue = (A_u_char)ClampValue<int>((int)((float)src.blue * weight + 0.5f), 0, 255);
		dst.alpha = (A_u_char)ClampValue<int>((int)((float)src.alpha * weight + 0.5f), 0, 255);
	}
	static void scale_alpha_only(PF_Pixel8 &dst, float weight)
	{
		dst.alpha = (A_u_char)ClampValue<int>((int)((float)dst.alpha * weight + 0.5f), 0, 255);
	}
	static void scale_alpha_public(PF_Pixel8 &dst, float weight)
	{
		dst.alpha = (A_u_char)ClampValue<int>(
		    (int)std::ceil((float)dst.alpha * weight), 0, 255);
	}
	static void restore_alpha(PF_Pixel8 &dst, const PF_Pixel8 &src) { dst.alpha = src.alpha; }
	static void scale_alpha_unbounded(PF_Pixel8 &dst, float weight) { dst.alpha = (A_u_char)(NativeBlurInt32((float)dst.alpha * weight)); }
};

template <>
struct OLMCKPixelTraits<PF_Pixel16> {
	static float max_chan() { return (float)PF_MAX_CHAN16; }
	static float native_key_epsilon() { return 1.0f / 65536.0f; }
	static bool is_16bpc() { return true; }
	static bool is_32bpc() { return false; }
	static float r(const PF_Pixel16 &p) { return (float)p.red / max_chan(); }
	static float g(const PF_Pixel16 &p) { return (float)p.green / max_chan(); }
	static float b(const PF_Pixel16 &p) { return (float)p.blue / max_chan(); }
	static float a(const PF_Pixel16 &p) { return (float)p.alpha / max_chan(); }
	static void zero(PF_Pixel16 &p) { p.alpha = p.red = p.green = p.blue = 0; }
	static void zero_alpha(PF_Pixel16 &p) { p.alpha = 0; }
	static void replace_rgb(PF_Pixel16 &p, const PF_PixelFloat &rep)
	{
		int maxv = (int)PF_MAX_CHAN16;
		p.red = (A_u_short)ClampValue<int>((int)(rep.red * (float)maxv), 0, maxv);
		p.green = (A_u_short)ClampValue<int>((int)(rep.green * (float)maxv), 0, maxv);
		p.blue = (A_u_short)ClampValue<int>((int)(rep.blue * (float)maxv), 0, maxv);
	}
	static void scale(PF_Pixel16 &dst, const PF_Pixel16 &src, float weight)
	{
		int maxv = (int)PF_MAX_CHAN16;
		dst.red = (A_u_short)ClampValue<int>((int)((float)src.red * weight), 0, maxv);
		dst.green = (A_u_short)ClampValue<int>((int)((float)src.green * weight), 0, maxv);
		dst.blue = (A_u_short)ClampValue<int>((int)((float)src.blue * weight), 0, maxv);
		dst.alpha = (A_u_short)ClampValue<int>((int)((float)src.alpha * weight), 0, maxv);
	}
	static void scale_alpha_only(PF_Pixel16 &dst, float weight)
	{
		int maxv = (int)PF_MAX_CHAN16;
		dst.alpha = (A_u_short)ClampValue<int>((int)((float)dst.alpha * weight), 0, maxv);
	}
	static void scale_alpha_public(PF_Pixel16 &dst, float weight)
	{
		int maxv = (int)PF_MAX_CHAN16;
		dst.alpha = (A_u_short)ClampValue<int>(
		    (int)std::ceil((float)dst.alpha * weight), 0, maxv);
	}
	static void restore_alpha(PF_Pixel16 &dst, const PF_Pixel16 &src) { dst.alpha = src.alpha; }
	static void scale_alpha_unbounded(PF_Pixel16 &dst, float weight) { dst.alpha = (A_u_short)(NativeBlurInt32((float)dst.alpha * weight)); }
};

template <>
struct OLMCKPixelTraits<PF_PixelFloat> {
	static float max_chan() { return 1.0f; }
	static float native_key_epsilon() { return 1.0e-6f; }
	static bool is_16bpc() { return false; }
	static bool is_32bpc() { return true; }
	static float r(const PF_PixelFloat &p) { return p.red; }
	static float g(const PF_PixelFloat &p) { return p.green; }
	static float b(const PF_PixelFloat &p) { return p.blue; }
	static float a(const PF_PixelFloat &p) { return p.alpha; }
	static void zero(PF_PixelFloat &p) { p.alpha = p.red = p.green = p.blue = 0.0f; }
	static void zero_alpha(PF_PixelFloat &p) { p.alpha = 0.0f; }
	static void replace_rgb(PF_PixelFloat &p, const PF_PixelFloat &rep)
	{
		p.red = rep.red;
		p.green = rep.green;
		p.blue = rep.blue;
	}
	static void scale(PF_PixelFloat &dst, const PF_PixelFloat &src, float weight)
	{
		dst.red = olm::x86_float::mul(src.red, weight);
		dst.green = olm::x86_float::mul(src.green, weight);
		dst.blue = olm::x86_float::mul(src.blue, weight);
		dst.alpha = olm::x86_float::mul(src.alpha, weight);
	}
	static void scale_alpha_only(PF_PixelFloat &dst, float weight)
	{
		dst.alpha = olm::x86_float::mul(dst.alpha, weight);
	}
	static void scale_alpha_public(PF_PixelFloat &dst, float weight) { scale_alpha_only(dst, weight); }
	static void restore_alpha(PF_PixelFloat &dst, const PF_PixelFloat &src) { dst.alpha = src.alpha; }
	static void scale_alpha_unbounded(PF_PixelFloat &dst, float weight) { dst.alpha = olm::x86_float::mul(dst.alpha, weight); }
};

// World rowbytes is a byte stride, not a guarantee of PixelT alignment.
// Copy through aligned values so odd padding is valid at every depth.
template <typename PixelT>
static PixelT ReadPixel(const PF_EffectWorld *world, A_long x, A_long y)
{
	PixelT pixel;
	std::memcpy(&pixel, reinterpret_cast<const std::uint8_t *>(world->data) +
	    (size_t)y * (size_t)world->rowbytes + (size_t)x * sizeof(PixelT), sizeof(pixel));
	return pixel;
}

template <typename PixelT>
static void WritePixel(PF_EffectWorld *world, A_long x, A_long y, const PixelT &pixel)
{
	std::memcpy(reinterpret_cast<std::uint8_t *>(world->data) +
	    (size_t)y * (size_t)world->rowbytes + (size_t)x * sizeof(PixelT), &pixel, sizeof(pixel));
}

static A_long WorldOriginX(const PF_EffectWorld *world)
{
#if defined(OLMCOLORKEY_HOSTLESS_RENDER_HARNESS) && \
    !defined(OLMCOLORKEY_HOSTLESS_WORLD_HAS_ORIGIN)
	(void)world;
	return 0;
#else
	return world->origin_x;
#endif
}

static A_long WorldOriginY(const PF_EffectWorld *world)
{
#if defined(OLMCOLORKEY_HOSTLESS_RENDER_HARNESS) && \
    !defined(OLMCOLORKEY_HOSTLESS_WORLD_HAS_ORIGIN)
	(void)world;
	return 0;
#else
	return world->origin_y;
#endif
}

// Before 5602e329 each visited key was converted in place for every pixel.
static inline void LabKeyReference(float (&key)[3])
{
    RGBToPluginLab76(key, key);
}

static inline void LabKeyFast(float (&key)[3], float (&cached)[3], bool &ready)
{
    if (!ready) {
        RGBToPluginLab76(key, key);
        std::memcpy(cached, key, sizeof(key));
        ready = true;
    } else {
        std::memcpy(key, cached, sizeof(key));
    }
}


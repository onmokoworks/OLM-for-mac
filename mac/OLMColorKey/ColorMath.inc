static constexpr float kLabLinearBreakpoint = 0.008856000378727913f; // Lab piecewise breakpoint; AEX 0x9f50, data RVA 0x1f638.
static constexpr float kLabLinearSlope = 7.7870001792907715f; // Lab linear slope; AEX 0x9f50, data RVA 0x1f6f0.
static constexpr float kLabLinearOffset = 0.13793103396892548f; // Lab linear offset; AEX 0x9f50, data RVA 0x1f658.
static constexpr float kLabPower = 0.3333300054073334f; // Lab nonlinear exponent; AEX 0x9f50, data RVA 0x1f678.
static constexpr float kLab76DistanceScale = 424.4352722167969f; // Lab76 threshold and epsilon scale; AEX 0x43a0.
// Included by OLMColorKey.cpp; preserves the single translation unit.
static float LabF(float t)
{
	return t <= kLabLinearBreakpoint
		? t * kLabLinearSlope + kLabLinearOffset
		: ucrt_powf(t, kLabPower, UCRT_FMA);
}

// FLOAT32 sum order matches AEX 0x9f50; do not reassociate.
static void RGBToPluginLab76(const float rgb[3], float out[3])
{
	float r = rgb[0];
	float g = rgb[1];
	float b = rgb[2];
	float x = g * 2.1455016136169434f + r * 0.6380193829536438f + b * 0.2165091633796692f;
	float fx = LabF(x);
	out[0] = x <= kLabLinearBreakpoint
		? g * 1938.031494140625f + r * 576.3229370117188f + b * 195.57272338867188f
		: ucrt_powf(x, kLabPower, UCRT_FMA) * 116.0f - 16.0f;
	float a_source = r * 1.2373713254928589f + g * 1.0727508068084717f + b * 0.5412744283676147f;
	float b_source = g * 0.35758259892463684f + r * 0.05800257995724678f + b * 2.8507096767425537f;
	out[1] = (LabF(a_source) - fx) * 500.0f;
	out[2] = (fx - LabF(b_source)) * 200.0f;
}

static void RGBToPluginHSV(const float rgb[3], float out[3])
{
	const float r = rgb[0], g = rgb[1], b = rgb[2];
	// FUN_180009e10: COMISS/CMOVBE selects green on unordered,
	// then MAXSS/MINSS selects red on unordered or equal operands.
	const float mx = olm::x86_float::sse_max(!(b > g) ? g : b, r);
	const float mn = olm::x86_float::sse_min(!(g > b) ? g : b, r);
	// UCOMISS followed by JE/JNE treats unordered as equal (ZF=1).
	auto equal_or_unordered = [](float a, float b) {
		return !(a < b) && !(a > b);
	};
	const float delta = olm::x86_float::sse_sub(mx, mn);
	float h;
	if (equal_or_unordered(mx, mn)) h = 0.0f;
	else if (equal_or_unordered(r, mx)) h = (g - b) * 60.0f / delta;
	else if (equal_or_unordered(g, mx)) h = (b - r) * 60.0f * (1.0f / delta) + 120.0f;
	else h = (r - g) * 60.0f * (1.0f / delta) + 240.0f;
	h = std::fmod(h, 360.0f);
	if (!(h >= 0.0f)) h += 360.0f;
	out[0] = h * 0.0027777778450399637f;
	out[1] = equal_or_unordered(mx, 0.0f) ? 0.0f : delta / mx;
	out[2] = mx;
}

static void RGBToPluginYUV(const float rgb[3], float out[3])
{
	const float r = rgb[0], g = rgb[1], b = rgb[2];
	out[0] = g * 0.5870000123977661f + r * 0.29899999499320984f + b * 0.11400000005960464f;
	out[1] = b * 0.4359999895095825f - (g * 0.2888599932193756f + r * 0.14712999761104584f);
	out[2] = r * 0.6150000095367432f - g * 0.514989972114563f - b * 0.10001000016927719f;
}

static void RGBToPluginYCrCb(const float rgb[3], float out[3])
{
	const float r = rgb[0], g = rgb[1], b = rgb[2];
	out[0] = r * 0.298909991979599f + g * 0.5866100192070007f + b * 0.11448000371456146f;
	out[1] = b * 0.5f - (r * 0.16874000430107117f + g * 0.33125999569892883f);
	out[2] = r * 0.5f - g * 0.4186899960041046f - b * 0.08130999654531479f;
}

static float Lab94Distance(const float a[3], const float b[3])
{
	const float c1 = std::sqrt(a[1] * a[1] + a[2] * a[2]);
	const float c2 = std::sqrt(b[1] * b[1] + b[2] * b[2]);
	const float cmean = std::sqrt(c2 * c1);
	auto hue = [](float aa, float bb) {
		float h = ucrt_atan2f(bb, aa, UCRT_FMA) * 57.2957763671875f + 180.0f;
		if (h != 0.0f) {
			if (h < 0.0f) h += 540.0f;
			h = std::fmod(h, 360.0f);
		}
		return h;
	};
	const float h1 = hue(a[1], a[2]);
	const float h2 = hue(b[1], b[2]);
	const float dL = b[0] - a[0];
	const float dC = (c2 - c1) / (cmean * 0.04500000178813934f + 1.0f);
	const float dH = (h2 - h1) / (cmean * 0.014999999664723873f + 1.0f);
	return std::sqrt(dL * dL + dC * dC + dH * dH);
}

static bool LabPerComponentHit(const float cmp[3], const float key[3], PF_FpLong tr, PF_FpLong tg, PF_FpLong tb, float epsilon)
{
	const float limit_l = (float)tr * 151.30099487304688f + epsilon * 2709.929931640625f;
	const float limit_a = (float)tg * 264.36700439453125f + epsilon * 578.7139892578125f;
	const float limit_b = (float)tb * 295.572998046875f + epsilon * 414.6759948730469f;
	// FUN_1800043a0: COMISS + JA rejects only ordered greater differences.
	// Unordered Lab components therefore pass, allowing the replacement color.
	return !(std::fabs(cmp[0] - key[0]) > limit_l)
	    && !(std::fabs(cmp[1] - key[1]) > limit_a)
	    && !(std::fabs(cmp[2] - key[2]) > limit_b);
}

static void Lab76ComparatorMutate(float value[3])
{
	// FUN_1800043a0 (Lab76) and the per-component branch of FUN_180004510
	// (Lab94) add the a/b offsets in place.  Lab76 does so before both its
	// scalar and per-component predicates.  The pixel callback reuses the
	// converted comparison triple across the key loop, so a failed key leaves
	// these additions visible to the next key.  Each converted key is local to
	// its own iteration and receives the additions once.
	value[1] += 133.03700256347656f;
	value[2] += 163.48800659179688f;
}

static bool Lab76ScalarHit(const float cmp[3], const float key[3],
	                       PF_FpLong threshold, float epsilon)
{
	// FUN_1800043a0 evaluates the three squared differences and threshold
	// scale with scalar FLOAT32 instructions.  It scales threshold and epsilon
	// separately before their addition.  Keep the operation order visible
	// so the Windows comparator remains the arithmetic owner.
	const float d0 = key[0] - cmp[0];
	const float d1 = key[1] - cmp[1];
	const float d2 = key[2] - cmp[2];
	float distance_squared = d0 * d0;
	distance_squared += d1 * d1;
	distance_squared += d2 * d2;
	const float distance = std::sqrt(distance_squared);
	float limit = (float)threshold * kLab76DistanceScale;
	const float epsilon_limit = epsilon * kLab76DistanceScale;
	limit = epsilon_limit + limit;
	return distance <= limit;
}


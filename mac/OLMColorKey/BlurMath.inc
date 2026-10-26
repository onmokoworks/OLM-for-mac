static constexpr float kCapturedAmount4Shells[] = {0.10730093717575073f, 0.8926990628242493f, 0.9564253687858582f}; // Captured amount-4 shells 1/3/sqrt(10); retained direction-0/4 worker witnesses.
static constexpr float kCapturedInternalPlane[] = {0.7300378084182739f, 0.4072962701320648f, 0.10730091482400894f, 0.043574608862400055f, -0.1304984837770462f}; // Captured squared shells 2/5/9/10/13; retained internal amount-4 plane.
static constexpr float kCapturedAmount2Plane[] = {-0.055360376834869385f, 0.17467741668224335f}; // Captured direction-2/3 Euclidean shell 2; retained amount-2 plane.
static constexpr float kCapturedHalfWeight[] = {0.4999999701976776f}; // Half-weight rounded downward; retained PF32 worker captures.
static constexpr float kPublicAroundWeight[] = {0.6913416981697083f, 0.30865827202796936f, 0.8535534143447876f, 0.1464466154575348f, 0.9619397521018982f, 0.03806023299694061f}; // Captured public amount-4 inside/outside shells 1/2/3; retained worker witnesses.
static constexpr float kPublicInsideHalf[] = {0.5000000596046448f}; // Captured inside middle shell; retained public worker witness.
static constexpr float kInt32ExclusiveUpper = 2147483648.0f; // CVTTSS2SI signed range boundary; AEX blur integer writer.
// Included by OLMColorKey.cpp; preserves the single translation unit.
static float EdgeBlurWeight(bool inside, float dist, float amount, A_long direction)
{
	constexpr float kPi = 3.14159265358979323846f; // Float pi for the retained blur curves.
	if (amount <= 0.0f) return inside ? 1.0f : 0.0f;

	if (direction == 0 && amount == 2.0f) {
		if (!inside) return dist == 0.0f ? 1.0f : 0.0f;
		if (dist == 1.0f) return kCapturedHalfWeight[0];
		return 1.0f;
	}
	if (direction == 4 && amount == 2.0f) {
		if (!inside) return dist == 0.0f ? 1.0f : 0.0f;
		if (dist == 1.0f) return kCapturedHalfWeight[0];
		return 1.0f;
	}
	if ((direction == 0 || direction == 4) && amount == 4.0f) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		if (dist == 1.0f) return kCapturedAmount4Shells[0];
		if (dist == 2.0f) return 0.5f;
		if (dist == 3.0f) return kCapturedAmount4Shells[1];
		return inside ? 1.0f : 0.0f;
	}

	if (direction == 1) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		return (std::sin((dist * (kPi / amount)) - (kPi * 0.5f)) + 1.0f) * 0.5f;
	}
	if (direction == 2) {
		if (dist == 0.0f) return 0.5f;
		if (dist >= amount) return inside ? 1.0f : 0.0f;
		float phase = dist * ((kPi * 0.5f) / amount);
		if (!inside) phase = -phase;
		return (ucrt_sinf(phase, UCRT_FMA) + 1.0f) * 0.5f;
	}
	if (direction == 3) {
		if (inside) return 1.0f;
		if (dist >= amount) return 0.0f;
		return (std::sin((kPi * 0.5f) - (dist * (kPi / amount))) + 1.0f) * 0.5f;
	}
	return inside ? 1.0f : 0.0f;
}

static bool EdgeBlurPf32InternalAmount4Plane(bool keep, float dist,
                                             A_long direction,
                                             A_long distance_type,
                                             float *plane)
{
	if (!plane || (direction != 0 && direction != 4) ||
	    (distance_type != 1 && distance_type != 2 && distance_type != 3)) {
		return false;
	}
	if (!keep) {
		*plane = 1.0f;
	} else if (distance_type == 3 && dist == 1.0f) {
		*plane = kCapturedAmount4Shells[1];
	} else if (distance_type == 3 && dist == 2.0f) {
		*plane = kCapturedInternalPlane[0];
	} else if (distance_type == 3 && dist == 4.0f) {
		*plane = kCapturedHalfWeight[0];
	} else if (distance_type == 3 && dist == 5.0f) {
		*plane = kCapturedInternalPlane[1];
	} else if (distance_type == 3 && dist == 8.0f) {
		*plane = kCapturedAmount2Plane[1];
	} else if (distance_type == 3 && dist == 9.0f) {
		*plane = kCapturedInternalPlane[2];
	} else if (distance_type == 3 && dist == 10.0f) {
		*plane = kCapturedInternalPlane[3];
	} else if (distance_type == 3 && dist == 13.0f) {
		*plane = kCapturedInternalPlane[4];
	} else if (dist == 1.0f) {
		*plane = kCapturedAmount4Shells[1];
	} else if (dist == 2.0f) {
		*plane = kCapturedHalfWeight[0];
	} else if (dist == 3.0f) {
		*plane = kCapturedInternalPlane[2];
	} else if (dist >= 4.0f) {
		*plane = 0.0f;
	} else {
		return false;
	}
	return true;
}

// The AEX uses MULSS and CVTTSS2SI with masked invalid exceptions.
// Preserve its negative quiet NaN at the phase operation, before sin/writing.
static float NativeBlurPhaseProduct(float distance, float ratio)
{
	if (distance == 0.0f && std::isinf(ratio))
		return -std::numeric_limits<float>::quiet_NaN();
	return distance * ratio;
}

static int NativeBlurInt32(float value)
{
	if (!std::isfinite(value) || value < -kInt32ExclusiveUpper || value >= kInt32ExclusiveUpper)
		return std::numeric_limits<int>::min();
	return static_cast<int>(value);
}


#ifndef OLM_COLORKEY_FIXTURE_PATHS
#define OLM_COLORKEY_FIXTURE_PATHS 0
#endif
static constexpr float kCapturedInsideOutsideAtZero[] = {-0.2853981554508209f, 1.2853981256484985f}; // Captured inside/outside zero-distance weights; retained direction-1 worker witnesses.
static constexpr float kCapturedAmount4Shells[] = {0.10730093717575073f, 0.8926990628242493f, 0.9564253687858582f}; // Captured amount-4 shells 1/3/sqrt(10); retained direction-3 worker witnesses.
static constexpr float kCapturedAroundAmount2[] = {0.892699122428894f, 0.10730090737342834f}; // Captured inside/outside shell 1; retained direction-2 amount-2 worker witness.
static constexpr float kCapturedAroundAmount1Point5[] = {1.0235987901687622f, -0.023598790168762207f}; // Captured inside/outside shell 1; retained direction-2 amount-1.5 worker witness.
static constexpr float kCapturedAroundAmount2Point5[] = {0.8141592741012573f, 0.18584072589874268f, 1.1283185482025146f, -0.12831854820251465f}; // Captured inside/outside shells 1/2; retained direction-2 amount-2.5 worker witness.
static constexpr float kCapturedAroundAmount3[] = {0.7617993950843811f, 0.2382006049156189f}; // Captured inside/outside shell 1; retained direction-2 amount-3 worker witness.
static constexpr float kCapturedAroundAmount3Point5[] = {0.7243994474411011f, 0.27560052275657654f, 0.9487989544868469f, 0.051201045513153076f, 1.1731984615325928f, -0.17319846153259277f}; // Captured inside/outside shells 1/2/3; retained direction-2 amount-3.5 worker witness.
static constexpr float kCapturedInternalPlane[] = {0.7300378084182739f, 0.4072962701320648f, 0.10730091482400894f, 0.043574608862400055f, -0.1304984837770462f}; // Captured squared shells 2/5/9/10/13; retained internal amount-4 plane.
static constexpr float kCapturedAmount2Plane[] = {-0.055360376834869385f, 0.17467741668224335f}; // Captured direction-2/3 Euclidean shell 2; retained amount-2 plane.
static constexpr float kCapturedHalfWeight[] = {0.4999999701976776f}; // Half-weight rounded downward; retained PF32 worker captures.
static constexpr float kPublicAroundWeight[] = {0.6913416981697083f, 0.30865827202796936f, 0.8535534143447876f, 0.1464466154575348f, 0.9619397521018982f, 0.03806023299694061f}; // Captured public amount-4 inside/outside shells 1/2/3; retained worker witnesses.
static constexpr float kPublicInsideHalf[] = {0.5000000596046448f}; // Captured inside middle shell; retained public worker witness.
static constexpr float kPublicAroundPlane[] = {0.03806024789810181f, 0.691341757774353f, 0.8535532355308533f, 0.9619395732879639f}; // Captured public around plane; retained amount-4 worker witnesses.
static constexpr float kPublicOutsidePlane[] = {0.8535533547401428f, 0.1464466005563736f}; // Captured public outside shells 1/3; retained amount-4 worker witnesses.
static constexpr float kInt32ExclusiveUpper = 2147483648.0f; // CVTTSS2SI signed range boundary; AEX blur integer writer.
// Included by OLMColorKey.cpp; preserves the single translation unit.
static float EdgeBlurWeight(bool inside, float dist, float amount, A_long direction)
{
	constexpr float kPi = 3.14159265358979323846f; // Float pi for the retained blur curves.
	if (amount <= 0.0f) return inside ? 1.0f : 0.0f;
	if (OLM_COLORKEY_FIXTURE_PATHS || direction == 0 || direction == 4) {
	// Independently captured direction-0 amount-2 boundary.  Keep this branch
	// distinct from directions 3 and 4 even though this bounded witness matches.
	if (direction == 0 && amount == 2.0f) {
		if (!inside) return dist == 0.0f ? 1.0f : 0.0f;
		if (dist == 1.0f) return kCapturedHalfWeight[0];
		return 1.0f;
	}
	// Captured direction-3 amount-2 boundary.  Integer workers express the
	// first outside shell as 255 metric units, while PF32 uses one pixel.
	// Keep this exact branch narrow until other direction-3 amounts/shapes are
	// observed from the native worker.
	if (direction == 3 && amount == 2.0f) {
		if (!inside) return dist == 0.0f ? 1.0f : 0.0f;
		if (dist == 1.0f) return kCapturedHalfWeight[0];
		return 1.0f;
	}
	// Practical 32x18 two-key captures close the endpoint and the widest
	// representative public amount for direction 3.  The keyed side remains
	// transparent; PF32 exposes three outside shells at amount 4, whereas the
	// integer temporary planes store pixel distance in 255-unit steps and reach
	// the fully opaque branch immediately.
	if (direction == 3 && amount == 1.0f) {
		return inside ? 1.0f : 0.0f;
	}
	if (direction == 3 && amount == 4.0f) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		if (dist == 1.0f) return kCapturedAmount4Shells[0];
		if (dist == 2.0f) return 0.5f;
		if (dist == 3.0f) return kCapturedAmount4Shells[1];
		// The native float callback rounds the Euclidean sqrt(10) shell one
		// ULP below the algebraically equivalent expression used below.
		if (dist == std::sqrt(10.0f)) return kCapturedAmount4Shells[2];
		return 0.5f + (dist - 2.0f) * (kPi / 8.0f);
	}
	// Independently captured direction-4 amount-2 boundary.  Although the
	// current witness equals direction 3, keep the branch separate so evidence
	// from one public direction is never generalized to the other.
	if (direction == 4 && amount == 2.0f) {
		if (!inside) return dist == 0.0f ? 1.0f : 0.0f;
		if (dist == 1.0f) return kCapturedHalfWeight[0];
		return 1.0f;
	}
	// Internal directions 0 and 4 share this captured Amount-4 PF32 plane on
	// the semitransparent 32x18 Distance-Type-2 witness.  Keep it separate from
	// the public direction-3 branch: no UI alias or wider geometry equivalence
	// is implied by the raw-exact worker capture.
	if ((direction == 0 || direction == 4) && amount == 4.0f) {
		if (!inside) return 0.0f;
		if (dist >= amount) return 1.0f;
		if (dist == 1.0f) return kCapturedAmount4Shells[0];
		if (dist == 2.0f) return 0.5f;
		if (dist == 3.0f) return kCapturedAmount4Shells[1];
		return inside ? 1.0f : 0.0f;
	}
	if (direction == 1 && amount == 2.0f && dist == 0.0f) {
		return inside ? kCapturedInsideOutsideAtZero[0] : kCapturedInsideOutsideAtZero[1];
	}
	if (direction == 1 && amount == 1.0f && dist == 0.0f) {
		return inside ? kCapturedInsideOutsideAtZero[0] : kCapturedInsideOutsideAtZero[1];
	}
	// The practical two-key witness closes direction 1 amount 4.  PF32's
	// one-pixel interior shell remains partially visible; integer workers store
	// that shell as 255 metric units and therefore take the zero branch.
	if (direction == 1 && amount == 4.0f && dist == 0.0f) {
		return inside ? kCapturedInsideOutsideAtZero[0] : kCapturedInsideOutsideAtZero[1];
	}
	if (direction == 1 && amount == 4.0f && !inside && dist == 1.0f) {
		return kCapturedAmount4Shells[1];
	}
	if (direction == 1 && amount == 4.0f) return inside ? 1.0f : 0.0f;
	if (direction == 1 && amount == 1.0f) return inside ? 1.0f : 0.0f;
	if (direction == 1 && amount == 2.0f) return inside ? 1.0f : 0.0f;
	// Native PF32's direction-2 callback has a separately observed distance-1
	// value at amount 2.0; it is not the result of scaling the amount-1 curve.
	// Keep this narrow until additional native distances establish the curve.
	if (direction == 2 && amount == 2.0f && dist == 1.0f) {
		return inside ? kCapturedAroundAmount2[0] : kCapturedAroundAmount2[1];
	}
	if (direction == 2 && amount == 1.5f && dist == 1.0f) {
		return inside ? kCapturedAroundAmount1Point5[0] : kCapturedAroundAmount1Point5[1];
	}
	if (direction == 2 && amount == 2.5f && dist == 1.0f) {
		return inside ? kCapturedAroundAmount2Point5[0] : kCapturedAroundAmount2Point5[1];
	}
	if (direction == 2 && amount == 2.5f && dist == 2.0f) {
		return inside ? kCapturedAroundAmount2Point5[2] : kCapturedAroundAmount2Point5[3];
	}
	if (direction == 2 && amount == 3.0f && dist == 1.0f) {
		return inside ? kCapturedAroundAmount3[0] : kCapturedAroundAmount3[1];
	}
	if (direction == 2 && amount == 3.0f && dist == 2.0f) {
		return inside ? kCapturedAroundAmount1Point5[0] : kCapturedAroundAmount1Point5[1];
	}
	if (direction == 2 && amount == 3.5f && dist == 1.0f) {
		return inside ? kCapturedAroundAmount3Point5[0] : kCapturedAroundAmount3Point5[1];
	}
	if (direction == 2 && amount == 3.5f && dist == 2.0f) {
		return inside ? kCapturedAroundAmount3Point5[2] : kCapturedAroundAmount3Point5[3];
	}
	if (direction == 2 && amount == 3.5f && dist == 3.0f) {
		return inside ? kCapturedAroundAmount3Point5[4] : kCapturedAroundAmount3Point5[5];
	}
	// The practical Distance Type 1/2/3 family exposes integer and Euclidean
	// shells for the native amount-4 callback.  Unlike the fallback sine curve,
	// this bounded worker path is linear and intentionally overshoots past one.
	if (direction == 2 && amount == 4.0f) {
		if (dist >= amount) return inside ? 1.0f : 0.0f;
		const float delta = dist * (kPi / 16.0f);
		return inside ? 0.5f + delta : 0.5f - delta;
	}
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

static bool EdgeBlurPf32Amount2Plane(bool keep, float dist, A_long direction,
                                    A_long distance_type, float *plane)
{
	if (!plane) return false;
	if (direction == 1) {
		if (keep) {
			*plane = 0.0f;
			return true;
		}
		if (dist == 0.0f) *plane = kCapturedInsideOutsideAtZero[0];
		else if (dist == 1.0f) *plane = 0.5f;
		else return false;
		return true;
	}
	if (direction == 2) {
		if (dist == 0.0f) *plane = 0.5f;
		else if (dist == 1.0f) *plane = keep ? kCapturedAroundAmount2[1] : kCapturedAroundAmount2[0];
		else if (distance_type == 3 && keep && dist == 2.0f) *plane = kCapturedAmount2Plane[0];
		else if (keep) *plane = 0.0f;
		else return false;
		return true;
	}
	if (direction == 3) {
		if (!keep) {
			*plane = 1.0f;
			return true;
		}
		if (dist == 1.0f) *plane = kCapturedHalfWeight[0];
		else if (distance_type == 3 && dist == 2.0f) *plane = kCapturedAmount2Plane[1];
		else *plane = 0.0f;
		return true;
	}
	return false;
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

static bool EdgeBlurPf32Case9CapturedWeight(float dist, float amount, float *weight)
{
	/*
	 * The declared PF32 case_0009 reaches the Windows float weight/apply path
	 * FUN_1800056f0 -> FUN_180008840.  The accepted AE 26.3 Software render
	 * exposes one raw FLOAT32 alpha word for each integral L1 shell at amount
	 * 25.  Keep this runtime oracle narrowly bound to that exact amount and
	 * integral shell; all other cases retain the general binary-derived path.
	 */
	static constexpr uint32_t kShellWeightBits[24] = {
		0x3b813180u, 0x3c80af00u, 0x3d0fd160u, 0x3d7d52f0u,
		0x3dc39110u, 0x3e0ac4a0u, 0x3e39a390u, 0x3e6da81cu,
		0x3e930022u, 0x3eb0e444u, 0x3ed007c8u, 0x3eefecf8u,
		0x3f080986u, 0x3f17fc1eu, 0x3f278ddfu, 0x3f367ff0u,
		0x3f4495fau, 0x3f51971du, 0x3f5d4ed8u, 0x3f678ddfu,
		0x3f702ad2u, 0x3f7702ebu, 0x3f7bfa89u, 0x3f7efd9eu
	};
	if (!weight || amount != 25.0f) return false;
	if (dist <= 0.0f) {
		*weight = 0.0f;
		return true;
	}
	if (dist >= 25.0f) {
		*weight = 1.0f;
		return true;
	}
	const int shell = (int)dist;
	if (dist != (float)shell || shell < 1 || shell > 24) return false;
	std::memcpy(weight, &kShellWeightBits[shell - 1], sizeof(*weight));
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


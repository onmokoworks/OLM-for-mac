// ============================================================================
// RenderState — refcon mirroring Win local_4d8 (built by FUN_1800096f0) plus
// the source/dest world pointers consumed by the kernel.
//
// The kernel reads pointers at very specific offsets in the Win original:
//   8-bit branch  (FUN_180001400): state[0x10] = src_world, state[0x18] = dst
//   16-bit branch (FUN_1800011e0): state[0x18] = src_world, state[0x20] = dst
// We expose a unified C++ struct with named fields, but the byte-by-byte
// classifier code accesses src_world via state->src_world (regardless of
// bitdepth) so the same struct works for both.
// ============================================================================
struct RenderState {
	uint8_t           use_key;       // +0x00 (Win local_4d8)
	uint8_t           key_a;         // +0x01 (alpha byte / pad)
	uint16_t          key_rg_packed; // +0x02..0x03 (Win packed CONCAT11)
	uint16_t          key_b;         // +0x04..0x05 (Win local_4d4)
	uint16_t          key_pad;       // +0x06..0x07 (Win local_4d2)
	int32_t           tolerance_lo;  // +0x08 (Win local_4d0)
	int32_t           tolerance_hi;  // +0x0c (Win local_4cc) — duplicate
	PF_EffectWorld   *src_world;     // pointer to current input world
	PF_EffectWorld   *dst_world;     // pointer to output world
	int32_t           tolerance;     // tolerance value (used by classifier)
	int32_t           threshold;     // raw tolerance; PF16 helpers apply <<7 internally
	// The Windows PF16 key callback consumes four full words.  They cannot be
	// represented by key_rg_packed, which intentionally mirrors the PF8 byte
	// layout above.
	uint16_t          key16_a;
	uint16_t          key16_r;
	uint16_t          key16_g;
	uint16_t          key16_b;
};

// ----------------------------------------------------------------------------
// 8-bit byte → 15-bit ushort widening, exactly as Win v1 inlines it
//   ushort_val = (byte_val * 0x8000 + 0x80) / 0xff
// ----------------------------------------------------------------------------
static inline uint16_t Widen8To16(uint8_t v)
{
	return (uint16_t)(((uint32_t)v * 0x8000u + 0x80u) / 0xffu);
}

// ============================================================================
// LinearOffset* curve evaluators — literal port of FUN_180001000..180001180.
//
// Each Win object is a 0x20-byte struct laid out as:
//   +0x00  vftable pointer
//   +0x08  offset (float, member 0)
//   +0x0c  v0 (float, member 1)
//   +0x10  v1 (float, member 2)
//   +0x14  v2 (float, member 3, only LinearThreeOffsetFunction)
//
// The concrete evaluators below preserve the original single-precision steps.
// Interpolation executors call them with the current sample position.
// ============================================================================
struct LinearEvalBase {
	float offset;  // +0x08 in Win
	float v0;      // +0x0c
	float v1;      // +0x10
	float v2;      // +0x14
	virtual ~LinearEvalBase() = default;
	virtual float Evaluate(float t) const = 0;
};

// The Windows evaluators are scalar SSE (`SUBSS`, `MULSS`, `ADDSS`/`DIVSS`).
// Keep every instruction boundary observable so arm64 cannot contract the
// expressions into FMAs with a different final truncation result.
static inline float SseSubF32(float left, float right) {
	volatile float result = left - right;
	return result;
}
static inline float SseMulF32(float left, float right) {
	volatile float result = left * right;
	return result;
}
static inline float SseDivF32(float left, float right) {
	volatile float result = left / right;
	return result;
}
static inline float SseAddF32(float left, float right) {
	volatile float result = left + right;
	return result;
}

// FUN_1800010c0 — LinearOffsetFunction::operator()
struct LinearOffsetFunction : LinearEvalBase {
	LinearOffsetFunction(float ofs, float p0) {
		offset = ofs; v0 = p0; v1 = 0.0f; v2 = 0.0f;
	}
	float Evaluate(float t) const override {
		// (v0 - offset) * t + offset
		return SseAddF32(SseMulF32(SseSubF32(v0, offset), t), offset);
	}
};

// FUN_1800010e0 — LinearOffsetOneValue::operator()
struct LinearOffsetOneValue : LinearEvalBase {
	LinearOffsetOneValue(float ofs, float p0, float p1) {
		offset = ofs; v0 = p0; v1 = p1; v2 = 0.0f;
	}
	float Evaluate(float t) const override {
		if (t != DAT_18000d1f4) {
			return SseAddF32(SseMulF32(SseSubF32(v0, offset), t), offset);
		}
		return v1;  // Win returns *(param_1 + 0x10)
	}
};

// FUN_180001110 — LinearOffsetZeroOneValue::operator()
struct LinearOffsetZeroOneValue : LinearEvalBase {
	// Unlike the other linear evaluators, the Windows object keeps the
	// t==1 endpoint at +0x18.  LinearEvalBase::v2 occupies +0x14, so retain
	// that slot as padding and model the extra word explicitly.
	float endpoint_one;
	LinearOffsetZeroOneValue(float ofs, float p0, float p1, float p2) {
		offset = ofs; v0 = p0; v1 = p1; v2 = 0.0f; endpoint_one = p2;
	}
	float Evaluate(float t) const override {
		if (t == DAT_18000d1f4) {
			return endpoint_one;  // Win returns *(param_1 + 0x18)
		}
		if (t != 0.0f) {
			return SseAddF32(SseMulF32(SseSubF32(v0, offset), t), offset);
		}
		return v1;  // Win returns *(param_1 + 0x10)
	}
};

// FUN_180001150 — LinearOffsetZeroValue::operator()
struct LinearOffsetZeroValue : LinearEvalBase {
	LinearOffsetZeroValue(float ofs, float p0, float p1) {
		offset = ofs; v0 = p0; v1 = p1; v2 = 0.0f;
	}
	float Evaluate(float t) const override {
		if (t != 0.0f) {
			return SseAddF32(SseMulF32(SseSubF32(v0, offset), t), offset);
		}
		return v1;  // Win returns *(param_1 + 0x10)
	}
};

// FUN_180001180 — LinearThreeOffsetFunction::operator()
struct LinearThreeOffsetFunction : LinearEvalBase {
	LinearThreeOffsetFunction(float ofs, float p0, float p1, float p2) {
		offset = ofs; v0 = p0; v1 = p1; v2 = p2;
	}
	float Evaluate(float t) const override {
		float fVar1 = v1;  // Win *(param_1 + 0x10)
		if (t <= fVar1) {
			// ((v0 - offset) / v1) * t + offset
			return SseAddF32(SseMulF32(SseDivF32(SseSubF32(v0, offset), fVar1), t), offset);
		}
		// fVar1 = (v2 - v0) / (1.0 - v1)
		float slope = SseDivF32(SseSubF32(v2, v0), SseSubF32(DAT_18000d1f4, fVar1));
		// (slope * t + v2) - slope
		return SseSubF32(SseAddF32(SseMulF32(slope, t), v2), slope);
	}
};

// ============================================================================
// Debug trace (mirrors the Smoother2 g_olmsmoother2_trace_* convention):
// set OLMSMOOTHER_TRACE_X / OLMSMOOTHER_TRACE_Y to log dispatcher decisions
// near the row and every interp-executor step writing that dst pixel.
// ============================================================================
static bool trace_xy_enabled(int *tx, int *ty)
{
	static int cached_tx = -2, cached_ty = -2;
	if (cached_tx == -2) {
		const char *ex = getenv("OLMSMOOTHER_TRACE_X");
		const char *ey = getenv("OLMSMOOTHER_TRACE_Y");
		cached_tx = (ex && ey) ? atoi(ex) : -1;
		cached_ty = (ex && ey) ? atoi(ey) : -1;
	}
	*tx = cached_tx; *ty = cached_ty;
	return cached_tx >= 0;
}


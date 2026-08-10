// OLMSmoother_port.cpp — macOS 1:1 port of the Windows OLMSmoother.aex (v1).
//
// Current status: Stage 2 kernel port is in place for 8/16-bpc paths.
// Foundational primitives, scanline callbacks, and the main per-pixel kernel
// were ported from the Win disasm. Specifically:
//
//   - DAT_18000d1f0..d270 float/int constants                   (literal)
//   - DAT_18000f000..f0f0 3x3 direction/index tables            (literal)
//   - 5 LinearOffset* curve evaluators (functor classes)        (literal)
//   - FUN_180001620 / 180001a90  color blend (16/8)             (literal)
//   - FUN_180001ed0 / 180002060  alpha blend (16/8)             (literal)
//   - FUN_1800021f0 / 180002430  color compare (16/8)           (literal)
//   - FUN_180003ff0 / 180004220  9-neighbor extractor (16/8)    (literal, world+0x18 / +0x10)
//   - FUN_180001400 / 1800011e0  render entry chain             (suite-wrapped)
//   - FUN_1800096f0              dispatcher                     (literal control flow)
//
//   - FUN_180006a90 / 180008060  classifier                     (literal)
//   - FUN_180002740 / 1800033d0  sub-handler                    (literal)
//   - FUN_180004450 / 1800047f0  alt-handler                    (literal)
//   - FUN_180004b80 / 180005570  main interp kernel             (literal)
//   - FUN_180005f60 / 180006270  interp executor                (literal)
//   - FUN_180009960 / 180009e30  edge walker                    (literal)
//
// Remaining work:
//   - broader byte-perfect verification against Win reference renders
//   - 32-bpc float behavior currently passes through; Win v1 has no float path

#include "OLMSmoother.h"
#include "AEFX_SuiteHandlerTemplate.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>

// ============================================================================
// DAT_* constants — verified against Ghidra binary read + decomp cross-check.
// Layout at .rdata 18000d1f0..18000d270.
// ============================================================================
static const float DAT_18000d1f0  = 0.5f;          // K_HALF
static const float DAT_18000d1f4  = 1.0f;          // K_ONE
static const float DAT_18000d250  = 1.0f / 32768.0f; // K_USHORT_DIV
static const float _DAT_18000d254 = 0.11f;         // BT.601 luma B
static const float _DAT_18000d258 = 0.30f;         // BT.601 luma R
static const float _DAT_18000d25c = 0.59f;         // BT.601 luma G
static const float DAT_18000d260  = 4.0f;          // (unused in this stage)
static const float DAT_18000d264  = 8.0f;          // (unused in this stage)
static const float DAT_18000d268  = 255.0f;        // K_BYTE_MAX
static const float DAT_18000d26c  = 32768.0f;      // K_USHORT_MAX
static const uint32_t DAT_18000d270 = 0x7FFFFFFFu; // ABS_MASK (sign clear)

// ----------------------------------------------------------------------------
// 3x3 direction/index tables @ 18000f000..18000f0f0.
// Each table has nine entries, including center slot 4.  The original arrays
// are 0x28 bytes apart: 9 int32 values followed by one padding int32.
// Values below are read directly from the pinned 2025 Windows AEX
// (SHA-256 6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82).
// DAT_18000f000  : direction "rev" #0
// DAT_18000f028  : direction "rev" #1
// DAT_18000f050  : direction "rev" #2
// DAT_18000f078  : direction "rev" #3
// DAT_18000f0a0  : direction pair-id
// DAT_18000f0c8  : DX (column delta -1/0/+1)
// DAT_18000f0f0  : DY (row delta    -1/0/+1)
// ----------------------------------------------------------------------------
static const int32_t DAT_18000f000[9] = { 6, 3, 0, 7, 4, 1, 8, 5, 2 };
static const int32_t DAT_18000f028[9] = { 2, 5, 8, 1, 4, 7, 0, 3, 6 };
static const int32_t DAT_18000f050[9] = { 3, 0, 1, 6, 4, 2, 7, 8, 5 };
static const int32_t DAT_18000f078[9] = { 1, 2, 5, 0, 4, 8, 3, 6, 7 };
static const int32_t DAT_18000f0a0[9] = { 8, 7, 6, 5, 4, 3, 2, 1, 0 };
static const int32_t DAT_18000f0c8[9] = { -1, 0, 1, -1, 0, 1, -1, 0, 1 };
static const int32_t DAT_18000f0f0[9] = { -1,-1,-1,  0, 0, 0,  1, 1, 1 };

// ============================================================================
// Plugin lifecycle commands
// ============================================================================
static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_SPRINTF(out_data->return_msg, "%s\n%s",
	           GetStringPtr(StrID_Name),
	           GetStringPtr(StrID_Description));
	return PF_Err_NONE;
}

static PF_Err
GlobalSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000040;
	out_data->out_flags2 = 0x08000000;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_UseKey_Param_Name),
	                "", FALSE, 0, USE_KEY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_Key_Param_Name),
	             0xFF, 0xFF, 0xFF,
	             KEY_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Tolerance_Param_Name),
	              0, 255, 0, 6, 6,
	              TOLERANCE_DISK_ID);

	out_data->num_params = SM_NUM_PARAMS;
	return err;
}

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
// On Mac we use plain C++ classes with a virtual operator()(void) returning
// float. Win calls the evaluator via:
//   weight = (*((code**)*evaluator))(evaluator);
// which on x64 is a virtual fn-ptr deref + tail call passing self as arg. Our
// virtual dispatch matches that semantically (no arg needed; "param_2" in the
// decomp refers to a separate parameter the kernel passes as 0..1 weight, not
// captured here — the LinearOffset eval ignores that input in this stage).
//
// However, looking at the eval bodies (FUN_1800010c0..180001180), all 5 take a
// `float param_2` argument and return a float. So we model them as objects
// with an operator()(float t) method and an evaluator-arg-only sentinel call
// for FUN_180005f60's `(*((code**)*puVar5))(puVar5)` that fetches `t` from a
// pre-stored slot. Stage 4 (when FUN_180005f60 is ported) decides the exact
// invocation pattern — for now these classes are present but unused.
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

// ============================================================================
// FUN_180001620 — 16-bit color blend (literal).
// Reads 9-neighbor pointer table at param_1+0x10..0x30 (rel offsets -0x10..0x10
// from the do-loop's puVar14), reads center pixel at param_1+0x20 (puVar14[2]
// = state->src_world+slot 4 = center, but here Win uses param_1+0x20 which is
// the pre-fetched center pixel pointer stashed by the caller).
// ============================================================================
//
// param_1 layout in Win (FUN_180001620 callsite is FUN_180004450 / kernel):
//   +0x10  9-neighbor pointer 0 (NW)
//   +0x18  pointer 1 (N)
//   +0x20  pointer 2 (NE) — also serves as "center pixel pointer" via param_1+0x20
//   +0x28  pointer 3 (W)
//   +0x30  pointer 4 (C)
//   ...
//
// Wait — re-reading: the loop uses puVar14[-2], puVar14[-1], *puVar14 with
// puVar14 starting at param_1+0x10 (= ptr index 0,1,2) then advancing by 3 on
// each iteration. Iteration 1: indices 0,1,2. Iteration 2: indices 3,4,5.
// Iteration 3: indices 6,7,8. So the loop sweeps all 9 neighbors with the
// `iVar12 != 4`, `!= 3`, `!= 2` skip filters meaning skip-center (index 4) on
// iteration 2's first slot, skip-W (index 3) on iter 2's center, skip-N
// (index 2) on iter 1's last slot... Actually no: iVar12 starts at 0 and gets
// +=3 each outer iter. With 3 inner branches, the skip happens when iVar12
// matches certain values. iVar12 == 4 never happens (it's 0,3,6). But the code
// reads `iVar12 != 4` — let me re-check… Actually re-reading more carefully:
//
// Iteration 1: iVar12=0. Branch1 needs iVar12!=4 (true→take). Branch2 needs
//   iVar12!=3 (true→take). Branch3 needs iVar12!=2 (true→take).
// Iteration 2: iVar12=3 (after +=3). Branch1: !=4 true. Branch2: !=3 FALSE
//   (SKIP). Branch3: !=2 true. iVar12 incremented to 6.
// Iteration 3: iVar12=6. Branch1: !=4 true. Branch2: !=3 true. Branch3: !=2
//   true.
//
// So the skipped slot is "iter 2 branch 2" = puVar14[-1] in iter 2 = (param_1
// +0x10) + 3*8 - 8 = param_1+0x20. That's index 4 = center pixel. Good — the
// loop accumulates 8 neighbors and skips center.
//
// param_3 controls "extra weight" applied to the center pixel (param_1+0x20):
//   param_3 == 5 → add 8 copies of center (final dir==4 blend)
//   param_3 == 2 → add 2 copies of center (alt-handler call)
//   param_3 == 1 → add 1 copy of center
//   param_3 < 1  → no extra
//
// Output: param_2 (pointer to ushort[4] = BGRA at the target pixel).
// ============================================================================
static void
ColorBlend16(uint64_t *param_1, uint16_t *param_2, int param_3)
{
	uint16_t uVar1, uVar2, uVar3, uVar5;
	uint16_t *puVar4;
	uint32_t uVar6, uVar7, uVar8, uVar11, uVar13;
	int iVar9 = 0;
	int iVar12 = 0;
	uint64_t *puVar14 = param_1 + 2;  // param_1 + 0x10 (param_1 is uint64_t*)
	float fVar15, fVar16, fVar17, fVar18, fVar19, fVar20, fVar21, fVar22, fVar23;

	fVar18 = 0.0f;
	fVar19 = 0.0f;
	fVar20 = 0.0f;
	fVar21 = 0.0f;
	fVar22 = 0.0f;

	do {
		puVar4 = (uint16_t*)puVar14[-2];
		if ((puVar4 != nullptr) && (iVar12 != 4)) {
			fVar18 = fVar18 + DAT_18000d1f4;
			fVar19 = fVar19 + (float)*puVar4;
			fVar16 = (float)*puVar4 * DAT_18000d250;
			fVar20 = fVar20 + (float)puVar4[1] * fVar16;
			fVar21 = fVar21 + (float)puVar4[3] * fVar16;
			fVar22 = fVar22 + (float)puVar4[2] * fVar16;
		}
		puVar4 = (uint16_t*)puVar14[-1];
		if ((puVar4 != nullptr) && (iVar12 != 3)) {
			fVar18 = fVar18 + DAT_18000d1f4;
			fVar19 = fVar19 + (float)*puVar4;
			fVar16 = (float)*puVar4 * DAT_18000d250;
			fVar20 = fVar20 + (float)puVar4[1] * fVar16;
			fVar21 = fVar21 + (float)puVar4[3] * fVar16;
			fVar22 = fVar22 + (float)puVar4[2] * fVar16;
		}
		puVar4 = (uint16_t*)*puVar14;
		if ((puVar4 != nullptr) && (iVar12 != 2)) {
			fVar18 = fVar18 + DAT_18000d1f4;
			fVar19 = fVar19 + (float)*puVar4;
			fVar16 = (float)*puVar4 * DAT_18000d250;
			fVar20 = fVar20 + (float)puVar4[1] * fVar16;
			fVar21 = fVar21 + (float)puVar4[3] * fVar16;
			fVar22 = fVar22 + (float)puVar4[2] * fVar16;
		}
		iVar12 = iVar12 + 3;
		puVar14 = puVar14 + 3;
	} while (iVar12 < 9);

	// param_3 = extra-center-weight count
	if (param_3 < 8) {
		if (param_3 < 1) goto LAB_18000198e;
		puVar4 = *(uint16_t**)((uint8_t*)param_1 + 0x20);
		uVar5 = *puVar4;
		uVar1 = puVar4[1];
		uVar2 = puVar4[3];
		uVar3 = puVar4[2];
	} else {
		puVar4 = *(uint16_t**)((uint8_t*)param_1 + 0x20);
		uVar5 = *puVar4;
		uVar1 = puVar4[1];
		uVar2 = puVar4[3];
		uVar3 = puVar4[2];
		fVar23 = (float)uVar5;
		uint32_t uVar6_outer = ((uint32_t)(param_3 - 8) >> 3) + 1;
		uint64_t uVar10 = (uint64_t)uVar6_outer;
		iVar9 = (int)(uVar6_outer * 8);
		fVar16 = fVar23 * DAT_18000d250;
		fVar15 = (float)uVar1 * fVar16;
		fVar17 = (float)uVar2 * fVar16;
		fVar16 = (float)uVar3 * fVar16;
		do {
			fVar18 = fVar18 + DAT_18000d1f4 + DAT_18000d1f4 + DAT_18000d1f4 + DAT_18000d1f4 +
			         DAT_18000d1f4 + DAT_18000d1f4 + DAT_18000d1f4 + DAT_18000d1f4;
			fVar19 = fVar23 + fVar19 + fVar23 + fVar23 + fVar23 + fVar23 + fVar23 + fVar23 + fVar23;
			fVar20 = fVar15 + fVar20 + fVar15 + fVar15 + fVar15 + fVar15 + fVar15 + fVar15 + fVar15;
			fVar21 = fVar17 + fVar21 + fVar17 + fVar17 + fVar17 + fVar17 + fVar17 + fVar17 + fVar17;
			fVar22 = fVar16 + fVar22 + fVar16 + fVar16 + fVar16 + fVar16 + fVar16 + fVar16 + fVar16;
			uVar10 = uVar10 - 1;
		} while (uVar10 != 0);
		if (param_3 <= iVar9) goto LAB_18000198e;
	}
	{
		fVar16 = (float)uVar5 * DAT_18000d250;
		uint64_t uVar10 = (uint64_t)(uint32_t)(param_3 - iVar9);
		do {
			fVar19 = fVar19 + (float)uVar5;
			fVar20 = fVar20 + (float)uVar1 * fVar16;
			fVar21 = fVar21 + (float)uVar2 * fVar16;
			fVar22 = fVar22 + (float)uVar3 * fVar16;
			fVar18 = fVar18 + DAT_18000d1f4;
			uVar10 = uVar10 - 1;
		} while (uVar10 != 0);
	}
LAB_18000198e:
	if (fVar18 <= 0.0f) {
		uVar6 = (uint32_t)*param_2;
		uVar7 = (uint32_t)param_2[1];
		uVar13 = (uint32_t)param_2[3];
		uVar11 = (uint32_t)param_2[2];
	} else {
		uVar6 = (uint32_t)(fVar19 / fVar18);
		uVar7 = (uint32_t)(fVar20 / fVar18);
		uVar13 = (uint32_t)(fVar21 / fVar18);
		uVar11 = (uint32_t)(fVar22 / fVar18);
	}
	fVar18 = (float)(uVar6 & 0xffff) * DAT_18000d250;
	uVar8 = (uint32_t)((float)(uVar7 & 0xffff) / fVar18);
	uVar11 = (uint32_t)((float)(uVar11 & 0xffff) / fVar18);
	uVar7 = (uint32_t)((float)(uVar13 & 0xffff) / fVar18);
	uVar5 = (uint16_t)uVar7;
	if (0x8000 < (uVar7 & 0xffff)) uVar5 = 0x8000;
	param_2[3] = uVar5;
	uVar5 = (uint16_t)uVar8;
	if (0x8000 < (uVar8 & 0xffff)) uVar5 = 0x8000;
	param_2[1] = uVar5;
	uVar5 = (uint16_t)uVar11;
	if (0x8000 < (uVar11 & 0xffff)) uVar5 = 0x8000;
	param_2[2] = uVar5;
	uVar5 = (uint16_t)uVar6;
	if (0x8000 < (uVar6 & 0xffff)) uVar5 = 0x8000;
	*param_2 = uVar5;
}

// ============================================================================
// FUN_180001a90 — 8-bit color blend (literal twin of ColorBlend16).
// ============================================================================
static void
ColorBlend8(uint64_t *param_1, uint8_t *param_2, int param_3)
{
	uint8_t bVar1, bVar2, bVar3, bVar4;
	uint8_t *pbVar5;
	uint32_t uVar6, uVar9, uVar11, uVar12;
	int iVar7 = 0;
	int iVar10 = 0;
	uint64_t *puVar13 = param_1 + 2;
	float fVar14, fVar15, fVar16, fVar17, fVar18, fVar19, fVar20, fVar21, fVar22, fVar23;

	fVar17 = DAT_18000d268;
	fVar18 = 0.0f;
	fVar19 = 0.0f;
	fVar20 = 0.0f;
	fVar21 = 0.0f;
	fVar22 = 0.0f;

	do {
		pbVar5 = (uint8_t*)puVar13[-2];
		if ((pbVar5 != nullptr) && (iVar10 != 4)) {
			fVar18 = fVar18 + DAT_18000d1f4;
			fVar19 = fVar19 + (float)*pbVar5;
			fVar15 = (float)*pbVar5 / DAT_18000d268;
			fVar20 = fVar20 + (float)pbVar5[1] * fVar15;
			fVar21 = fVar21 + (float)pbVar5[3] * fVar15;
			fVar22 = fVar22 + (float)pbVar5[2] * fVar15;
		}
		pbVar5 = (uint8_t*)puVar13[-1];
		if ((pbVar5 != nullptr) && (iVar10 != 3)) {
			fVar18 = fVar18 + DAT_18000d1f4;
			fVar19 = fVar19 + (float)*pbVar5;
			fVar15 = (float)*pbVar5 / DAT_18000d268;
			fVar20 = fVar20 + (float)pbVar5[1] * fVar15;
			fVar21 = fVar21 + (float)pbVar5[3] * fVar15;
			fVar22 = fVar22 + (float)pbVar5[2] * fVar15;
		}
		pbVar5 = (uint8_t*)*puVar13;
		if ((pbVar5 != nullptr) && (iVar10 != 2)) {
			fVar18 = fVar18 + DAT_18000d1f4;
			fVar19 = fVar19 + (float)*pbVar5;
			fVar15 = (float)*pbVar5 / DAT_18000d268;
			fVar20 = fVar20 + (float)pbVar5[1] * fVar15;
			fVar21 = fVar21 + (float)pbVar5[3] * fVar15;
			fVar22 = fVar22 + (float)pbVar5[2] * fVar15;
		}
		iVar10 = iVar10 + 3;
		puVar13 = puVar13 + 3;
	} while (iVar10 < 9);

	if (param_3 < 8) {
		if (param_3 < 1) goto LAB_180001dfe;
		pbVar5 = *(uint8_t**)((uint8_t*)param_1 + 0x20);
		bVar1 = *pbVar5;
		bVar2 = pbVar5[1];
		bVar3 = pbVar5[3];
		bVar4 = pbVar5[2];
	} else {
		pbVar5 = *(uint8_t**)((uint8_t*)param_1 + 0x20);
		bVar1 = *pbVar5;
		bVar2 = pbVar5[1];
		bVar3 = pbVar5[3];
		bVar4 = pbVar5[2];
		fVar23 = (float)bVar1;
		uVar6 = ((uint32_t)(param_3 - 8) >> 3) + 1;
		uint64_t uVar8 = (uint64_t)uVar6;
		fVar15 = fVar23 / DAT_18000d268;
		iVar7 = (int)(uVar6 * 8);
		fVar14 = (float)bVar2 * fVar15;
		fVar16 = (float)bVar3 * fVar15;
		fVar15 = (float)bVar4 * fVar15;
		do {
			fVar18 = fVar18 + DAT_18000d1f4 + DAT_18000d1f4 + DAT_18000d1f4 + DAT_18000d1f4 +
			         DAT_18000d1f4 + DAT_18000d1f4 + DAT_18000d1f4 + DAT_18000d1f4;
			fVar19 = fVar23 + fVar19 + fVar23 + fVar23 + fVar23 + fVar23 + fVar23 + fVar23 + fVar23;
			fVar20 = fVar14 + fVar20 + fVar14 + fVar14 + fVar14 + fVar14 + fVar14 + fVar14 + fVar14;
			fVar21 = fVar16 + fVar21 + fVar16 + fVar16 + fVar16 + fVar16 + fVar16 + fVar16 + fVar16;
			fVar22 = fVar15 + fVar22 + fVar15 + fVar15 + fVar15 + fVar15 + fVar15 + fVar15 + fVar15;
			uVar8 = uVar8 - 1;
		} while (uVar8 != 0);
		if (param_3 <= iVar7) goto LAB_180001dfe;
	}
	{
		fVar15 = (float)bVar1 / DAT_18000d268;
		uint64_t uVar8 = (uint64_t)(uint32_t)(param_3 - iVar7);
		do {
			fVar19 = fVar19 + (float)bVar1;
			fVar20 = fVar20 + (float)bVar2 * fVar15;
			fVar21 = fVar21 + (float)bVar3 * fVar15;
			fVar22 = fVar22 + (float)bVar4 * fVar15;
			fVar18 = fVar18 + DAT_18000d1f4;
			uVar8 = uVar8 - 1;
		} while (uVar8 != 0);
	}
LAB_180001dfe:
	if (fVar18 <= 0.0f) {
		uVar9  = (uint32_t)*param_2;
		uVar6  = (uint32_t)param_2[1];
		uVar11 = (uint32_t)param_2[3];
		uVar12 = (uint32_t)param_2[2];
	} else {
		uVar9  = (uint32_t)(fVar19 / fVar18);
		uVar6  = (uint32_t)(fVar20 / fVar18);
		uVar11 = (uint32_t)(fVar21 / fVar18);
		uVar12 = (uint32_t)(fVar22 / fVar18);
	}
	*param_2 = (uint8_t)uVar9;
	fVar17 = (float)(uVar9 & 0xff) / fVar17;
	param_2[1] = (uint8_t)(int)((float)(uVar6  & 0xff) / fVar17);
	param_2[3] = (uint8_t)(int)((float)(uVar11 & 0xff) / fVar17);
	param_2[2] = (uint8_t)(int)((float)(uVar12 & 0xff) / fVar17);
}

// ============================================================================
// FUN_180001ed0 — 16-bit alpha blend (literal). Premultiplied lerp.
// ============================================================================
static void
AlphaBlend16(const uint16_t *param_1, float param_2,
             const uint16_t *param_3, float param_4,
             uint16_t *param_5)
{
	float fVar1 = DAT_18000d26c;
	float fVar6 = (float)*param_3;
	float fVar7 = (float)*param_1;
	// The Windows worker emits distinct MULSS/MULSS/ADDSS operations.  Keep
	// those binary32 rounding points on Apple Silicon instead of allowing an
	// FMA contraction across the alpha sum.
	volatile float alpha_first = fVar7 * param_2;
	volatile float alpha_second = fVar6 * param_4;
	volatile float alpha_sum = alpha_first + alpha_second;
	float fVar3 = alpha_sum;
	float fVar5 = fVar3;
	if (DAT_18000d26c < fVar3) fVar5 = DAT_18000d26c;
	if (fVar3 < 0.0f) fVar5 = 0.0f;

	auto weighted_channel = [](uint16_t first, float first_weight, float first_alpha,
	                           uint16_t second, float second_weight, float second_alpha,
	                           float divisor) -> float {
		volatile float first_product = (float)first * first_weight;
		first_product = first_product * first_alpha;
		volatile float second_product = (float)second * second_weight;
		second_product = second_product * second_alpha;
		volatile float sum = first_product + second_product;
		return sum / divisor;
	};
	float fVar4 = weighted_channel(param_1[1], param_2, fVar7,
	                               param_3[1], param_4, fVar6, fVar5);
	float fVar2 = weighted_channel(param_1[2], param_2, fVar7,
	                               param_3[2], param_4, fVar6, fVar5);
	fVar6 = weighted_channel(param_1[3], param_2, fVar7,
	                         param_3[3], param_4, fVar6, fVar5);

	fVar3 = fVar6;
	if (DAT_18000d26c < fVar6) fVar3 = DAT_18000d26c;
	if (fVar6 < 0.0f) fVar3 = 0.0f;
	param_5[3] = (int16_t)(int)fVar3;

	fVar3 = fVar4;
	if (fVar1 < fVar4) fVar3 = fVar1;
	if (fVar4 < 0.0f) fVar3 = 0.0f;
	param_5[1] = (int16_t)(int)fVar3;

	fVar3 = fVar2;
	if (fVar1 < fVar2) fVar3 = fVar1;
	if (fVar2 < 0.0f) fVar3 = 0.0f;
	param_5[2] = (int16_t)(int)fVar3;

	*param_5 = (int16_t)(int)fVar5;
}

// ============================================================================
// FUN_180002060 — 8-bit alpha blend (literal twin of AlphaBlend16).
// ============================================================================
static void
AlphaBlend8(const uint8_t *param_1, float param_2,
            const uint8_t *param_3, float param_4,
            uint8_t *param_5)
{
	float fVar1 = DAT_18000d268;
	float fVar6 = (float)*param_3;
	float fVar7 = (float)*param_1;
	volatile float alpha_first = fVar7 * param_2;
	volatile float alpha_second = fVar6 * param_4;
	volatile float alpha_sum = alpha_first + alpha_second;
	float fVar3 = alpha_sum;
	float fVar5 = fVar3;
	if (DAT_18000d268 < fVar3) fVar5 = DAT_18000d268;
	if (fVar3 < 0.0f) fVar5 = 0.0f;

	// FUN_180002060 uses a separate MULSS for every product and ADDSS for the
	// sum.  In particular it never contracts the final multiply/add into an
	// FMA.  Apple Silicon otherwise contracts this expression and crosses an
	// integer truncation boundary for a small set of PF8 pixels.  Volatile
	// temporaries retain the actual AEX's binary32 rounding points.
	auto weighted_channel = [](uint8_t first, float first_weight, float first_alpha,
	                           uint8_t second, float second_weight, float second_alpha,
	                           float divisor) -> float {
		volatile float first_product = (float)first * first_weight;
		first_product = first_product * first_alpha;
		volatile float second_product = (float)second * second_weight;
		second_product = second_product * second_alpha;
		volatile float sum = first_product + second_product;
		return sum / divisor;
	};
	float fVar4 = weighted_channel(param_1[1], param_2, fVar7,
	                               param_3[1], param_4, fVar6, fVar5);
	float fVar2 = weighted_channel(param_1[2], param_2, fVar7,
	                               param_3[2], param_4, fVar6, fVar5);
	fVar6 = weighted_channel(param_1[3], param_2, fVar7,
	                         param_3[3], param_4, fVar6, fVar5);

	float fVar3b = fVar6;
	if (DAT_18000d268 < fVar6) fVar3b = DAT_18000d268;
	if (fVar6 < 0.0f) fVar3b = 0.0f;
	param_5[3] = (uint8_t)(int)fVar3b;

	fVar3 = fVar4;
	if (fVar1 < fVar4) fVar3 = fVar1;
	if (fVar4 < 0.0f) fVar3 = 0.0f;
	param_5[1] = (uint8_t)(int)fVar3;

	fVar3 = fVar2;
	if (fVar1 < fVar2) fVar3 = fVar1;
	if (fVar2 < 0.0f) fVar3 = 0.0f;
	param_5[2] = (uint8_t)(int)fVar3;

	*param_5 = (uint8_t)(int)fVar5;
}

// ============================================================================
// FUN_1800021f0 — 16-bit color compare (literal). BT.601 luma + abs chroma /4.
// ============================================================================
static int32_t
ColorCompare16(const uint16_t *param_1, const uint16_t *param_2)
{
	if ((param_1 != nullptr) && (param_2 != nullptr) &&
	    ((param_1[1] != param_2[1]) ||
	     ((param_1[3] != param_2[3]) || (param_1[2] != param_2[2]) ||
	      (*param_1 != *param_2)))) {
		uint32_t uVar3 = (uint32_t)*param_1 - (uint32_t)*param_2;
		float fVar5 = SseMulF32((float)*param_1, DAT_18000d250);
		uint32_t uVar4 = (uint32_t)((int32_t)uVar3 >> 31);
		float fVar6 = SseMulF32((float)*param_2, DAT_18000d250);
		float p1r=SseMulF32((float)param_1[1],fVar5), p1g=SseMulF32((float)param_1[2],fVar5), p1b=SseMulF32((float)param_1[3],fVar5);
		float p2r=SseMulF32((float)param_2[1],fVar6), p2g=SseMulF32((float)param_2[2],fVar6), p2b=SseMulF32((float)param_2[3],fVar6);
		float l1=SseAddF32(SseAddF32(SseMulF32(p1r,_DAT_18000d258),SseMulF32(p1g,_DAT_18000d25c)),SseMulF32(p1b,_DAT_18000d254));
		float l2=SseAddF32(SseAddF32(SseMulF32(p2r,_DAT_18000d258),SseMulF32(p2g,_DAT_18000d25c)),SseMulF32(p2b,_DAT_18000d254));
		float _X=SseSubF32(l1,l2);
		float diff_a=SseSubF32(p1r,p2r), diff_b=SseSubF32(p1b,p2b), diff_c=SseSubF32(p1g,p2g);
		uint32_t a_bits = (*reinterpret_cast<uint32_t*>(&diff_a)) & DAT_18000d270;
		uint32_t b_bits = (*reinterpret_cast<uint32_t*>(&diff_b)) & DAT_18000d270;
		uint32_t c_bits = (*reinterpret_cast<uint32_t*>(&diff_c)) & DAT_18000d270;
		float fa = *reinterpret_cast<float*>(&a_bits);
		float fb = *reinterpret_cast<float*>(&b_bits);
		float fc = *reinterpret_cast<float*>(&c_bits);
		float metric=SseAddF32((float)(int32_t)((uVar3^uVar4)-uVar4),fa);
		metric=SseAddF32(metric,fb); metric=SseAddF32(metric,fc);
		int32_t iVar1=(int32_t)metric;
		iVar1 = (int32_t)(((uint32_t)(iVar1 >> 31) & 3u) + (uint32_t)iVar1) >> 2;
		if (iVar1 == 0) iVar1 = 1;

		float fVar5x;
		// The PE imports at 0x18000c424/0x18000c41e truncate the signed luma
		// delta toward zero (the old decompiler labels had floor/ceil swapped).
		if (_X <= 0.0f) fVar5x = ceilf(_X);
		else            fVar5x = floorf(_X);
		uint32_t uVar3x = (uint32_t)(int32_t)fVar5x;
		int32_t iVar2 = (int32_t)((uVar3x ^ (uint32_t)((int32_t)uVar3x >> 31)) -
		                          (uint32_t)((int32_t)uVar3x >> 31));
		if (iVar1 < iVar2) iVar1 = iVar2;
		if ((int32_t)uVar3x < 1) iVar1 = -iVar1;
		return iVar1;
	}
	return 0;
}

// ============================================================================
// FUN_180002430 — 8-bit color compare (literal twin).
// ============================================================================
static int32_t
ColorCompare8(const uint8_t *param_1, const uint8_t *param_2)
{
	if ((param_1 != nullptr) && (param_2 != nullptr) &&
	    ((param_1[1] != param_2[1]) ||
	     ((param_1[3] != param_2[3]) || (param_1[2] != param_2[2]) ||
	      (*param_1 != *param_2)))) {
		uint32_t uVar3 = (uint32_t)*param_1 - (uint32_t)*param_2;
		float fVar5 = SseDivF32((float)*param_1, DAT_18000d268);
		uint32_t uVar4 = (uint32_t)((int32_t)uVar3 >> 31);
		float fVar6 = SseDivF32((float)*param_2, DAT_18000d268);
		float p1r=SseMulF32((float)param_1[1],fVar5), p1g=SseMulF32((float)param_1[2],fVar5), p1b=SseMulF32((float)param_1[3],fVar5);
		float p2r=SseMulF32((float)param_2[1],fVar6), p2g=SseMulF32((float)param_2[2],fVar6), p2b=SseMulF32((float)param_2[3],fVar6);
		float l1=SseAddF32(SseAddF32(SseMulF32(p1r,_DAT_18000d258),SseMulF32(p1g,_DAT_18000d25c)),SseMulF32(p1b,_DAT_18000d254));
		float l2=SseAddF32(SseAddF32(SseMulF32(p2r,_DAT_18000d258),SseMulF32(p2g,_DAT_18000d25c)),SseMulF32(p2b,_DAT_18000d254));
		float _X=SseSubF32(l1,l2);
		float diff_a=SseSubF32(p1r,p2r), diff_b=SseSubF32(p1b,p2b), diff_c=SseSubF32(p1g,p2g);
		uint32_t a_bits = (*reinterpret_cast<uint32_t*>(&diff_a)) & DAT_18000d270;
		uint32_t b_bits = (*reinterpret_cast<uint32_t*>(&diff_b)) & DAT_18000d270;
		uint32_t c_bits = (*reinterpret_cast<uint32_t*>(&diff_c)) & DAT_18000d270;
		float fa = *reinterpret_cast<float*>(&a_bits);
		float fb = *reinterpret_cast<float*>(&b_bits);
		float fc = *reinterpret_cast<float*>(&c_bits);
		float metric=SseAddF32((float)(int32_t)((uVar3^uVar4)-uVar4),fa);
		metric=SseAddF32(metric,fb); metric=SseAddF32(metric,fc);
		int32_t iVar1=(int32_t)metric;
		iVar1 = (int32_t)(((uint32_t)(iVar1 >> 31) & 3u) + (uint32_t)iVar1) >> 2;
		if (iVar1 == 0) iVar1 = 1;

		float fVar5x;
		if (_X <= 0.0f) fVar5x = ceilf(_X);
		else            fVar5x = floorf(_X);
		uint32_t uVar3x = (uint32_t)(int32_t)fVar5x;
		int32_t iVar2 = (int32_t)((uVar3x ^ (uint32_t)((int32_t)uVar3x >> 31)) -
		                          (uint32_t)((int32_t)uVar3x >> 31));
		if (iVar1 < iVar2) iVar1 = iVar2;
		if ((int32_t)uVar3x < 1) iVar1 = -iVar1;
		return iVar1;
	}
	return 0;
}

// ============================================================================
// FUN_180003ff0 — 16-bit 9-neighbor pointer extractor (literal).
// Fills param_4[0..8] with pointers to NW, N, NE, W, C, E, SW, S, SE pixels of
// the source EffectWorld at (param_1=col, param_2=row). Out-of-bounds slots
// receive nullptr. Source world is at *(param_3 + 0x18). Stride = 8 bytes/px.
// ============================================================================
static void
NeighborExtract16(int param_1, int param_2, RenderState *state, uintptr_t *param_4)
{
	int64_t lVar4 = 0;
	int iVar7 = param_2 - 1;
	int iVar5 = param_1 - 1;
	PF_EffectWorld *world = state->src_world;
	int W = world->width;
	int H = world->height;
	int RB = world->rowbytes;
	uint8_t *base = (uint8_t*)world->data;

	auto px = [&](int x, int y) -> uintptr_t {
		if (x < 0 || x >= W || y < 0 || y >= H) return 0;
		return (uintptr_t)(base + (int64_t)(y * RB) + (int64_t)x * 8);
	};

	param_4[0] = px(iVar5, iVar7);
	param_4[1] = px(param_1, iVar7);
	param_4[2] = px(param_1 + 1, iVar7);
	param_4[3] = px(iVar5, param_2);
	param_4[4] = px(param_1, param_2);
	param_4[5] = px(param_1 + 1, param_2);
	param_4[6] = px(iVar5, param_2 + 1);
	param_4[7] = px(param_1, param_2 + 1);
	param_4[8] = px(param_1 + 1, param_2 + 1);
	(void)lVar4;
}

// ============================================================================
// FUN_180004220 — 8-bit 9-neighbor pointer extractor (literal twin).
// Source world is at *(param_3 + 0x10). Stride = 4 bytes/px.
// ============================================================================
static void
NeighborExtract8(int param_1, int param_2, RenderState *state, uintptr_t *param_4)
{
	int iVar7 = param_2 - 1;
	int iVar5 = param_1 - 1;
	PF_EffectWorld *world = state->src_world;
	int W = world->width;
	int H = world->height;
	int RB = world->rowbytes;
	uint8_t *base = (uint8_t*)world->data;

	auto px = [&](int x, int y) -> uintptr_t {
		if (x < 0 || x >= W || y < 0 || y >= H) return 0;
		return (uintptr_t)(base + (int64_t)(y * RB) + (int64_t)x * 4);
	};

	param_4[0] = px(iVar5, iVar7);
	param_4[1] = px(param_1, iVar7);
	param_4[2] = px(param_1 + 1, iVar7);
	param_4[3] = px(iVar5, param_2);
	param_4[4] = px(param_1, param_2);
	param_4[5] = px(param_1 + 1, param_2);
	param_4[6] = px(iVar5, param_2 + 1);
	param_4[7] = px(param_1, param_2 + 1);
	param_4[8] = px(param_1 + 1, param_2 + 1);
}

// ============================================================================
// Forward declarations for kernel/handler/walker functions ported below.
// ============================================================================
static int32_t Classifier16(RenderState *state, uint32_t x, uint32_t y,
                            const uintptr_t *neigh, uint32_t dir);
static int32_t Classifier16Exact(RenderState *state, uint32_t x, uint32_t y,
                                 const uintptr_t *neigh, uint32_t dir);
static int32_t Classifier8 (RenderState *state, uint32_t x, uint32_t y,
                            const uintptr_t *neigh, uint32_t dir);
static uint16_t* EdgeWalker16(RenderState *state, int x, int y, int dir1, uint32_t dir2,
                              int *out_x, int *out_y, int threshold);
static uint16_t* EdgeWalker16Exact(RenderState *state, int x, int y, int dir1, uint32_t dir2,
                                   int *out_x, int *out_y, int threshold);
static uint8_t*  EdgeWalker8 (RenderState *state, int x, int y, int dir1, uint32_t dir2,
                              int *out_x, int *out_y, int threshold);
static uint8_t*  EdgeWalker8Exact(RenderState *state, int x, int y, int dir1, uint32_t dir2,
                                  int *out_x, int *out_y, int threshold);
static void SubHandler16(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
                         uint32_t *o6, uint8_t *o7, uint8_t *o8,
                         uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
                         uint32_t *o13, uint32_t *o14);
static void SubHandler16Exact(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
                              uint32_t *o6, uint8_t *o7, uint8_t *o8,
                              uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
                              uint32_t *o13, uint32_t *o14);
static void SubHandler8 (RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
                         uint32_t *o6, uint8_t *o7, uint8_t *o8,
                         uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
                         uint32_t *o13, uint32_t *o14);
static void AltHandler16(RenderState *state, uintptr_t *neigh, int x, int y, uint32_t dir, int scan_type);
static void AltHandler8 (RenderState *state, uintptr_t *neigh, int x, int y, uint32_t dir, int scan_type);
static void MainInterpKernel16(RenderState *state, uintptr_t *neigh,
                               int p3, int p4, int p5, int p6, char p7, char p8,
                               int p9, int p10, int p11, int p12, int p13, int p14);
static void MainInterpKernel8 (RenderState *state, uintptr_t *neigh,
                               int p3, int p4, int p5, int p6, char p7, char p8,
                               int p9, int p10, int p11, int p12, int p13, int p14);
static void InterpExecutor16(RenderState *state, int dir, int p3, int p4,
                             const uint16_t *param_5, int p6, int p7,
                             const uint16_t *param_8, LinearEvalBase *evaluator,
                             char p10, int p11);
static void InterpExecutor8 (RenderState *state, int dir, int p3, int p4,
                             const uint8_t *param_5, int p6, int p7,
                             const uint8_t *param_8, LinearEvalBase *evaluator,
                             char p10, int p11);
#ifdef OLMSMOOTHER_TEST_HOOKS
using InterpExecutor16TestHook = void (*)(RenderState*, int, int, int,
                                         const uint16_t*, int, int,
                                         const uint16_t*, LinearEvalBase*, char, int);
static InterpExecutor16TestHook g_interp_executor16_test_hook = nullptr;
using InterpExecutor8TestHook = void (*)(RenderState*, int, int, int,
                                        const uint8_t*, int, int,
                                        const uint8_t*, LinearEvalBase*, char, int);
static InterpExecutor8TestHook g_interp_executor8_test_hook = nullptr;
#endif

// ============================================================================
// FUN_180006570 / FUN_180006710 — direction dispatchers (literal control flow).
//
// Param_6 (scan_type from classifier) selects the path:
//   0 → return immediately
//   1 → sub-handler → main kernel (if displacement is non-zero)
//   2,3 → alt-handler
//   4 → ColorBlend with weight=5 at center pixel
// ============================================================================
static void
DispatchDirection16(RenderState *state, uintptr_t *neigh,
                    uint32_t x, uint32_t y, uint32_t dir, int32_t scan_type)
{
	if (scan_type == 0) return;
	if (scan_type == 1) {
		uint32_t local_c;        // *param_6 — output kernel mode
		uint8_t  local_28;       // *param_7
		uint8_t  local_28_b;     // *param_8 (in Win, param_8 = (undefined1*)&param_6 alias)
		uint32_t local_1c, local_18, local_20, local_24, local_10, local_14;
		SubHandler16(state, neigh, x, y, dir,
		             &local_c, &local_28, &local_28_b,
		             &local_1c, &local_20, &local_18, &local_24, &local_10, &local_14);
		if ((local_1c != local_18) || (local_20 != local_24)) {
			MainInterpKernel16(state, neigh, (int)x, (int)y, (int)dir,
			                   (int)local_c, (char)local_28, (char)local_28_b,
			                   (int)local_1c, (int)local_20, (int)local_18, (int)local_24,
			                   (int)local_10, (int)local_14);
		}
		return;
	}
	if (scan_type - 2u < 2u) {
		AltHandler16(state, neigh, (int)x, (int)y, dir, scan_type);
	}
	if (scan_type == 4) {
		PF_EffectWorld *dst = state->dst_world;
		uint16_t *target = nullptr;
		if (((int)x >= 0) && ((int)x < dst->width) && ((int)y >= 0) && ((int)y < dst->height)) {
			target = (uint16_t*)((uint8_t*)dst->data + (int64_t)((int)y * dst->rowbytes) +
			                     (int64_t)(int)x * 8);
		}
		ColorBlend16((uint64_t*)neigh, target, 5);
	}
}

static void
DispatchDirection8(RenderState *state, uintptr_t *neigh,
                   uint32_t x, uint32_t y, uint32_t dir, int32_t scan_type)
{
	if (scan_type == 0) return;
	if (scan_type == 1) {
		uint32_t local_c;
		uint8_t  local_28;
		uint8_t  local_28_b;
		uint32_t local_1c, local_18, local_20, local_24, local_10, local_14;
		SubHandler8(state, neigh, x, y, dir,
		            &local_c, &local_28, &local_28_b,
		            &local_1c, &local_20, &local_18, &local_24, &local_10, &local_14);
		if ((local_1c != local_18) || (local_20 != local_24)) {
			{
				int tx, ty;
				if (trace_xy_enabled(&tx, &ty) &&
				    (int)y >= ty - 2 && (int)y <= ty + 2) {
					fprintf(stderr,
					        "[disp8] center=(%u,%u) dir=%u case=%u p7=%d p8=%d "
					        "p9=(%d,%d) p11=(%d,%d) p13=(%d,%d)\n",
					        x, y, dir, local_c, (int)local_28, (int)local_28_b,
					        (int)local_1c, (int)local_20, (int)local_18, (int)local_24,
					        (int)local_10, (int)local_14);
				}
			}
			MainInterpKernel8(state, neigh, (int)x, (int)y, (int)dir,
			                  (int)local_c, (char)local_28, (char)local_28_b,
			                  (int)local_1c, (int)local_20, (int)local_18, (int)local_24,
			                  (int)local_10, (int)local_14);
		}
		return;
	}
	if (scan_type - 2u < 2u) {
		AltHandler8(state, neigh, (int)x, (int)y, dir, scan_type);
	}
	if (scan_type == 4) {
		PF_EffectWorld *dst = state->dst_world;
		uint8_t *target = nullptr;
		if (((int)x >= 0) && ((int)x < dst->width) && ((int)y >= 0) && ((int)y < dst->height)) {
			target = (uint8_t*)dst->data + (int64_t)((int)y * dst->rowbytes) + (int64_t)(int)x * 4;
		}
		ColorBlend8((uint64_t*)neigh, target, 5);
	}
}

// ============================================================================
// FUN_180006a90 — Classifier16 (literal port).
// Takes neighbor pointer array (param_4) + direction index (param_5).
// Returns scan_type ∈ {0, 1, 2, 3, 4}.
// state field: tolerance_hi (state+0xc).
// ============================================================================
static int32_t
Classifier16(RenderState *state, uint32_t x, uint32_t y,
             const uintptr_t *param_4, uint32_t param_5)
{
	return Classifier16Exact(state, x, y, param_4, param_5);

	uint16_t uVar1;
	int iVar2, iVar3;
	const uint16_t *puVar4, *puVar5, *puVar11, *puVar12, *puVar18;
	bool bVar6;
	char cVar7, cVar19;
	int iVar8, iVar9, iVar16, iVar23;
	int64_t lVar10, lVar22;
	uint32_t uVar13, uVar14, uVar15, uVar17, uVar20;
	int32_t uVar21;
	uint32_t local_res8;

	puVar4 = (const uint16_t*)param_4[4];
	iVar23 = state->tolerance_hi;
	lVar22 = (int64_t)(int)param_5;
	puVar12 = (const uint16_t*)param_4[lVar22];
	iVar8 = ColorCompare16(puVar4, puVar12);
	if (iVar23 * -0x80 <= iVar8) {
		return 0;
	}
	puVar11 = (const uint16_t*)param_4[6];
	bVar6 = true;

	if (iVar23 == 0) {
		// All-equal early-out chain (Win lines 3160-3220)
		const uint16_t *cur;
		auto eq4 = [](const uint16_t *a, const uint16_t *b) {
			return (a[1] == b[1]) && (a[3] == b[3]) && (a[2] == b[2]) && (*a == *b);
		};
		// Try idx=6, then 8, 2, 0, 3, 5, 1, 7
		const int try_idx[] = {6, 8, 2, 0, 3, 5, 1, 7};
		bool matched = false;
		for (int ti = 0; ti < 8; ++ti) {
			if (puVar4 == nullptr) break;
			cur = (const uint16_t*)param_4[try_idx[ti]];
			if (cur == nullptr) continue;
			if (eq4(puVar4, cur)) { matched = true; break; }
		}
		if (matched) {
			bVar6 = false;
		}
	} else {
		// Tolerance-allowed early-out chain (Win lines 3224-3300)
		auto cmp_within = [&](const uint16_t *a, const uint16_t *b) -> bool {
			if (!a || !b) return false;
			int iVar = iVar23 << 7;
			uint32_t d, s;
			d = (uint32_t)a[1] - (uint32_t)b[1]; s = (int32_t)d >> 31;
			if ((int32_t)((d ^ s) - s) > iVar) return false;
			d = (uint32_t)a[3] - (uint32_t)b[3]; s = (int32_t)d >> 31;
			if ((int32_t)((d ^ s) - s) > iVar) return false;
			d = (uint32_t)a[2] - (uint32_t)b[2]; s = (int32_t)d >> 31;
			if ((int32_t)((d ^ s) - s) > iVar) return false;
			d = (uint32_t)*a   - (uint32_t)*b;   s = (int32_t)d >> 31;
			if ((int32_t)((d ^ s) - s) > iVar) return false;
			return true;
		};
		const int try_idx[] = {6, 8, 2, 0, 3, 5, 1, 7};
		bool matched = false;
		for (int ti = 0; ti < 8; ++ti) {
			const uint16_t *cur = (const uint16_t*)param_4[try_idx[ti]];
			if (cmp_within(puVar4, cur)) { matched = true; break; }
		}
		if (matched) bVar6 = false;
	}
	if (!bVar6) {
		// LAB_1800070a6 — fall through to no-edge return path eventually
		// We still need to compute LAB_1800070a9 logic for direction-specific.
	}

	// LAB_1800070a9: directional analysis ----------------------------------
	iVar8 = DAT_18000f050[lVar22];
	iVar9 = DAT_18000f028[lVar22];
	uVar21 = bVar6 ? 4 : 1;
	lVar10 = (int64_t)DAT_18000f0a0[lVar22];
	iVar2 = DAT_18000f050[lVar10];
	iVar3 = DAT_18000f078[lVar10];
	puVar11 = (const uint16_t*)param_4[DAT_18000f000[lVar22]];

	auto cmp_le = [&](const uint16_t *a, const uint16_t *b) -> bool {
		if (!a || !b) return false;
		if (iVar23 == 0) return (a[1]==b[1]) && (a[3]==b[3]) && (a[2]==b[2]) && (*a==*b);
		int iVar = iVar23 << 7;
		uint32_t d, s;
		d = (uint32_t)a[1] - (uint32_t)b[1]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar) return false;
		d = (uint32_t)a[3] - (uint32_t)b[3]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar) return false;
		d = (uint32_t)a[2] - (uint32_t)b[2]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar) return false;
		d = (uint32_t)*a   - (uint32_t)*b;   s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar) return false;
		return true;
	};

	// Compute pre-direction state. Following Win FUN_180006a90 lines 3312-3408.
	puVar18 = (const uint16_t*)param_4[iVar9];
	puVar12 = (const uint16_t*)param_4[iVar8];
	cVar19 = '\0';
	cVar7 = '\0';

	if (iVar23 != 0) {
		// Branch where tolerance > 0 (Win main path)
		if (puVar4 && puVar11 && cmp_le(puVar4, puVar11)) {
			// The second comparison is the selected direction pixel against
			// reverse-table-2.  Do not overwrite puVar18 with puVar12's slot:
			// that aliases both operands, makes the test unconditionally true,
			// and incorrectly suppresses the PF16 interpolation path.
			const uint16_t *direction_pix = (const uint16_t*)param_4[param_5];
			if (cmp_le(direction_pix, puVar12)) {
				// LAB_1800074f2 — full forward-strong-match path
				// Fall through to LAB_1800074f2 logic below
				goto LAB_1800074f2_16;
			}
		}
		// LAB_1800073cf and below — try iVar9 direction
		puVar18 = (const uint16_t*)param_4[iVar9];
		if (cmp_le(puVar4, puVar18)) {
			const uint16_t *p5_pix = (const uint16_t*)param_4[DAT_18000f078[(int64_t)param_5]];
			if (cmp_le(puVar12, p5_pix)) {
				goto LAB_1800074e7_16;
			}
			puVar12 = (const uint16_t*)param_4[DAT_18000f050[(int64_t)param_5]];
		} else {
			puVar12 = (const uint16_t*)param_4[DAT_18000f050[(int64_t)param_5]];
		}
		// LAB_180007db2
		if (cmp_le(puVar4, puVar12)) cVar19 = '\x01';
		puVar12 = (const uint16_t*)param_4[DAT_18000f078[(int64_t)param_5]];
	} else {
		// Tolerance == 0 path (exact equality)
		if (puVar4 && puVar11 && (puVar4[1]==puVar11[1]) && (puVar4[3]==puVar11[3]) &&
		    (puVar4[2]==puVar11[2]) && (*puVar4==*puVar11)) {
			puVar18 = (const uint16_t*)param_4[iVar8];
			if (cmp_le(puVar12, puVar18)) {
				goto LAB_1800074f2_16;
			}
		}
		// Fallthrough: try other dirs
		puVar18 = (const uint16_t*)param_4[iVar9];
		if (cmp_le(puVar4, puVar18)) {
			const uint16_t *p5_pix = (const uint16_t*)param_4[DAT_18000f078[(int64_t)param_5]];
			if (cmp_le(puVar12, p5_pix)) {
				goto LAB_1800074e7_16;
			}
			puVar12 = (const uint16_t*)param_4[DAT_18000f050[(int64_t)param_5]];
		} else {
			puVar12 = (const uint16_t*)param_4[DAT_18000f050[(int64_t)param_5]];
		}
		if (cmp_le(puVar4, puVar12)) cVar19 = '\x01';
		puVar12 = (const uint16_t*)param_4[DAT_18000f078[(int64_t)param_5]];
	}

	if (cmp_le(puVar4, puVar12)) {
		cVar7 = '\x01';
		goto LAB_180007ec1_16;
	}
	cVar7 = '\0';
LAB_180007ec1_16:
	if (cVar7 == cVar19) {
		return uVar21;
	}
	// Strict re-check of puVar11/puVar18 with tolerance
	if (!cmp_le(puVar4, puVar11)) return uVar21;
	if (!cmp_le(puVar4, puVar18)) return uVar21;
	return 0;

LAB_1800074e7_16:
	if (puVar11 == nullptr) return 0;
LAB_1800074f2_16:
	uVar21 = 0;
	puVar18 = (const uint16_t*)param_4[iVar9];
	if (puVar18 == nullptr) return 0;
	if (puVar12 == nullptr) return 0;
	if (puVar4  == nullptr) goto LAB_1800078b3_16;

	// Two-side validation: forward dir, back dir
	if (cmp_le(puVar4, puVar11)) {
		const uint16_t *pE = (const uint16_t*)param_4[DAT_18000f078[(int64_t)param_5]];
		if (cmp_le(puVar4, pE)) {
			iVar9 = ColorCompare16((const uint16_t*)param_4[iVar8], puVar4);
			if (iVar9 > iVar23 * 0x80) {
				uVar21 = 2;
			}
			goto LAB_1800078b3_16;
		}
	}
	// Try opposing direction
	if (!cmp_le(puVar4, puVar18)) goto LAB_1800078b3_16;
	{
		const uint16_t *pS = (const uint16_t*)param_4[DAT_18000f050[(int64_t)param_5]];
		if (!cmp_le(puVar4, pS)) goto LAB_1800078b3_16;
	}
	{
		int iVar = ColorCompare16((const uint16_t*)param_4[DAT_18000f078[(int64_t)param_5]], puVar4);
		if (iVar > iVar23 * 0x80) uVar21 = 2;
	}

LAB_1800078b3_16:
	puVar12 = (const uint16_t*)param_4[lVar10];
	if (puVar12 == nullptr) return uVar21;
	if (puVar4  == nullptr) return uVar21;

	if (!cmp_le(puVar4, puVar11)) return uVar21;

	{
		const uint16_t *p3 = (const uint16_t*)param_4[iVar3];
		if (puVar4 == nullptr) return uVar21;
		if (!cmp_le(puVar4, p3)) return uVar21;
		if (!cmp_le(puVar4, puVar12)) return uVar21;
	}

	iVar9 = iVar23 * 0x80;
	iVar8 = ColorCompare16(puVar18, puVar4);
	if (iVar8 <= iVar9) return uVar21;

	uVar1 = puVar18[1];
	uVar15 = (uint32_t)uVar1;
	puVar4 = (const uint16_t*)param_4[param_5];
	if (puVar4 == nullptr) return uVar21;
	if (iVar23 == 0) {
		if (uVar1 != puVar4[1]) return uVar21;
		uVar13 = (uint32_t)puVar18[3];
		if (puVar18[3] != puVar4[3]) return uVar21;
		uVar20 = (uint32_t)puVar18[2];
		if (puVar18[2] != puVar4[2]) return uVar21;
		uVar17 = (uint32_t)*puVar18;
		if (*puVar18 != *puVar4) return uVar21;
	} else {
		uint32_t d, s;
		d = uVar15 - puVar4[1]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		uVar13 = (uint32_t)puVar18[3];
		d = uVar13 - puVar4[3]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		uVar20 = (uint32_t)puVar18[2];
		d = uVar20 - puVar4[2]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		uVar17 = (uint32_t)*puVar18;
		d = uVar17 - *puVar4; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
	}

	puVar4 = (const uint16_t*)param_4[DAT_18000f050[(int64_t)param_5]];
	if (puVar4 == nullptr) return uVar21;
	if (iVar23 == 0) {
		if (uVar1 != puVar4[1]) return uVar21;
		if ((uint16_t)uVar13 != puVar4[3]) return uVar21;
		if ((uint16_t)uVar20 != puVar4[2]) return uVar21;
		if ((uint16_t)uVar17 != *puVar4) return uVar21;
		puVar4 = (const uint16_t*)param_4[iVar2];
		if (puVar4 == nullptr) return uVar21;
		if (uVar1 != puVar4[1]) return uVar21;
		if ((uint16_t)uVar13 != puVar4[3]) return uVar21;
		if ((uint16_t)uVar20 != puVar4[2]) return uVar21;
		if ((uint16_t)uVar17 != *puVar4) return uVar21;
	} else {
		uint32_t d, s;
		d = uVar15 - puVar4[1]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		d = uVar13 - puVar4[3]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		d = uVar20 - puVar4[2]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		d = uVar17 - *puVar4; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;

		puVar4 = (const uint16_t*)param_4[iVar2];
		if (puVar4 == nullptr) return uVar21;
		d = uVar15 - puVar4[1]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		d = uVar13 - puVar4[3]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		d = uVar20 - puVar4[2]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
		d = uVar17 - *puVar4; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar9) return uVar21;
	}
	(void)iVar16; (void)uVar14; (void)local_res8; (void)puVar5;
	return 3;
}

// Portable direct translation of the validated 0x1800087f0..0x18000946e CFG.
// Registers are integer carriers only; pixel pointers remain native pointers.
struct Classifier8TailRegs {
	uint64_t rax=0,rbx=0,rcx=0,rdx=0,rsi=0,rdi=0,rbp=0,rsp=0;
	uint64_t r8=0,r9=0,r10=0,r11=0,r12=0,r13=0,r14=0,r15=0;
};
struct Classifier8TailMemory {
	static constexpr uint64_t kModule=0x180000000ull, kStack=0x700000000000ull;
	uint8_t stack[0x180]{}; bool zf=false,sf=false,of=false;
	template<class T> T raw(uint64_t a) const { T v{}; memcpy(&v,(const void*)(uintptr_t)a,sizeof(v));return v; }
	uint8_t read8(uint64_t a) const { if(a>=kStack&&a<kStack+sizeof(stack))return stack[a-kStack]; return raw<uint8_t>(a); }
	uint32_t read32(uint64_t a) const {
		if(a>=kStack&&a+4<=kStack+sizeof(stack)){uint32_t v;memcpy(&v,stack+a-kStack,4);return v;}
		if(a>=kModule+0xf000&&a<kModule+0xf0c4){
			const uint64_t o=a-kModule; const int32_t *p=nullptr; uint64_t base=0;
			if(o>=0xf000&&o<0xf024){p=DAT_18000f000;base=0xf000;}
			else if(o>=0xf028&&o<0xf04c){p=DAT_18000f028;base=0xf028;}
			else if(o>=0xf050&&o<0xf074){p=DAT_18000f050;base=0xf050;}
			else if(o>=0xf078&&o<0xf09c){p=DAT_18000f078;base=0xf078;}
			else if(o>=0xf0a0&&o<0xf0c4){p=DAT_18000f0a0;base=0xf0a0;}
			if(p)return uint32_t(p[(o-base)/4]);
		}
		return raw<uint32_t>(a);
	}
	uint64_t read64(uint64_t a) const { if(a>=kStack&&a+8<=kStack+sizeof(stack)){uint64_t v;memcpy(&v,stack+a-kStack,8);return v;} return raw<uint64_t>(a); }
	void write8(uint64_t a,uint8_t v){if(a>=kStack&&a<kStack+sizeof(stack))stack[a-kStack]=v;else memcpy((void*)(uintptr_t)a,&v,1);}
	void write32(uint64_t a,uint32_t v){if(a>=kStack&&a+4<=kStack+sizeof(stack))memcpy(stack+a-kStack,&v,4);else memcpy((void*)(uintptr_t)a,&v,4);}
	void write64(uint64_t a,uint64_t v){if(a>=kStack&&a+8<=kStack+sizeof(stack))memcpy(stack+a-kStack,&v,8);else memcpy((void*)(uintptr_t)a,&v,8);}
	uint64_t subflags(uint64_t a,uint64_t b,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);a&=mask;b&=mask;uint64_t r=(a-b)&mask;zf=r==0;sf=(r>>(w-1))&1;of=(((a^b)&(a^r))>>(w-1))&1;return r;}
	void logicflags(uint64_t r,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);r&=mask;zf=r==0;sf=(r>>(w-1))&1;of=false;}
};

static int32_t Classifier8Tail(RenderState *state,const uintptr_t *param_4,uint32_t param_5,uint8_t flag_a,uint8_t flag_b)
{
	Classifier8TailRegs R; Classifier8TailMemory M; uint64_t T=0;
	const int64_t opposite=DAT_18000f0a0[param_5];
	R.rbx=param_4[4]; R.r14=(uintptr_t)param_4; R.r13=param_4[param_5]; R.r15=param_4[DAT_18000f000[param_5]];
	R.r8=Classifier8TailMemory::kModule; R.r9=Classifier8TailMemory::kStack+0x100+flag_a; R.r10=DAT_18000f078[param_5]; R.r12=DAT_18000f028[param_5];
	R.r11=Classifier8TailMemory::kStack+0x100+flag_b; R.rsi=uint32_t(DAT_18000f050[param_5]); R.rdi=uint32_t(state->tolerance_lo); R.rbp=flag_a?4:1;
	R.rax=uint32_t(DAT_18000f000[param_5]); R.rcx=uint32_t(DAT_18000f050[opposite]); R.rsp=Classifier8TailMemory::kStack;
	auto put=[&](size_t o,const auto &v){memcpy(M.stack+o,&v,sizeof(v));};
	int32_t tol=state->tolerance_lo; uint64_t opp=opposite, i2=DAT_18000f050[opposite], dir=param_5, zero=0;
	uint64_t i3=DAT_18000f078[opposite], initial=DAT_18000f050[param_5];
	put(0x20,i3);put(0x28,opp);put(0x30,zero);put(0x70,initial);put(0x78,zero);put(0x88,i2);put(0x90,dir);
#include "OLMSmoother_classifier8_tail.generated.inc"
}

// ============================================================================
// FUN_180008060 — Classifier8 (literal twin of Classifier16).
// state field: tolerance_lo (state+0x8).
// ============================================================================
static int32_t
Classifier8(RenderState *state, uint32_t /*x*/, uint32_t /*y*/,
            const uintptr_t *param_4, uint32_t param_5)
{
	uint8_t uVar1;
	int iVar2, iVar3;
	const uint8_t *puVar4, *puVar11, *puVar12, *puVar18;
	bool bVar6;
	char cVar7, cVar19;
	int iVar8, iVar9, iVar23;
	int64_t lVar10, lVar22;
	uint32_t uVar13, uVar15, uVar17, uVar20;
	int32_t uVar21;

	puVar4 = (const uint8_t*)param_4[4];
	iVar23 = state->tolerance_lo;
	lVar22 = (int64_t)(int)param_5;
	puVar12 = (const uint8_t*)param_4[lVar22];
	iVar8 = ColorCompare8(puVar4, puVar12);
	if (-iVar23 <= iVar8) {
		return 0;
	}
	puVar11 = (const uint8_t*)param_4[6];
	bVar6 = true;

	auto eq4_8 = [](const uint8_t *a, const uint8_t *b) {
		return (a[1] == b[1]) && (a[3] == b[3]) && (a[2] == b[2]) && (*a == *b);
	};
	auto cmp_le_8 = [&](const uint8_t *a, const uint8_t *b) -> bool {
		if (!a || !b) return false;
		if (iVar23 == 0) return eq4_8(a, b);
		uint32_t d, s;
		d = (uint32_t)a[1] - (uint32_t)b[1]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)a[3] - (uint32_t)b[3]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)a[2] - (uint32_t)b[2]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)*a   - (uint32_t)*b;   s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar23) return false;
		return true;
	};

	const int try_idx[] = {6, 8, 2, 0, 3, 5, 1, 7};
	bool matched = false;
	for (int ti = 0; ti < 8; ++ti) {
		const uint8_t *cur = (const uint8_t*)param_4[try_idx[ti]];
		if (iVar23 == 0) {
			if (puVar4 && cur && eq4_8(puVar4, cur)) { matched = true; break; }
		} else {
			if (cmp_le_8(puVar4, cur)) { matched = true; break; }
		}
	}
	if (matched) bVar6 = false;

	iVar8 = DAT_18000f050[lVar22];
	iVar9 = DAT_18000f028[lVar22];
	uVar21 = bVar6 ? 4 : 1;
	lVar10 = (int64_t)DAT_18000f0a0[lVar22];
	iVar2 = DAT_18000f050[lVar10];
	iVar3 = DAT_18000f078[lVar10];
	puVar11 = (const uint8_t*)param_4[DAT_18000f000[lVar22]];

	puVar18 = (const uint8_t*)param_4[iVar9];
	puVar12 = (const uint8_t*)param_4[iVar8];
	cVar19 = '\0';
	cVar7 = '\0';

	if (puVar4 && puVar11 && cmp_le_8(puVar4, puVar11)) {
		const uint8_t *direction_pix = (const uint8_t*)param_4[param_5];
		if (cmp_le_8(direction_pix, puVar12)) {
			goto LAB_1800074f2_8;
		}
	}
	puVar18 = (const uint8_t*)param_4[iVar9];
	if (cmp_le_8(puVar4, puVar18)) {
		const uint8_t *p5_pix = (const uint8_t*)param_4[DAT_18000f078[(int64_t)param_5]];
		if (cmp_le_8(puVar12, p5_pix)) {
			goto LAB_1800074e7_8;
		}
		puVar12 = (const uint8_t*)param_4[DAT_18000f050[(int64_t)param_5]];
	} else {
		puVar12 = (const uint8_t*)param_4[DAT_18000f050[(int64_t)param_5]];
	}
	if (cmp_le_8(puVar4, puVar12)) cVar19 = '\x01';
	puVar12 = (const uint8_t*)param_4[DAT_18000f078[(int64_t)param_5]];

	if (cmp_le_8(puVar4, puVar12)) {
		cVar7 = '\x01';
		goto LAB_180007ec1_8;
	}
	cVar7 = '\0';
LAB_180007ec1_8:
	if (cVar7 == cVar19) goto LAB_1800078b3_8;
	if (!cmp_le_8(puVar4, puVar11)) goto LAB_1800078b3_8;
	if (!cmp_le_8(puVar4, puVar18)) goto LAB_1800078b3_8;
	goto LAB_1800078b3_8;

LAB_1800074e7_8:
	if (puVar11 == nullptr) goto LAB_1800078b3_8;
LAB_1800074f2_8:
	uVar21 = 0;
	puVar18 = (const uint8_t*)param_4[iVar9];
	if (puVar18 == nullptr) goto LAB_1800078b3_8;
	if (puVar12 == nullptr) goto LAB_1800078b3_8;
	if (puVar4  == nullptr) goto LAB_1800078b3_8;

	if (cmp_le_8(puVar4, puVar11)) {
		const uint8_t *pE = (const uint8_t*)param_4[DAT_18000f078[(int64_t)param_5]];
		if (cmp_le_8(puVar4, pE)) {
			iVar9 = ColorCompare8((const uint8_t*)param_4[iVar8], puVar4);
			if (iVar9 > iVar23) {
				uVar21 = 2;
			}
			goto LAB_1800078b3_8;
		}
	}
	if (!cmp_le_8(puVar4, puVar18)) goto LAB_1800078b3_8;
	{
		const uint8_t *pS = (const uint8_t*)param_4[DAT_18000f050[(int64_t)param_5]];
		if (!cmp_le_8(puVar4, pS)) goto LAB_1800078b3_8;
	}
	{
		int iVar = ColorCompare8((const uint8_t*)param_4[DAT_18000f078[(int64_t)param_5]], puVar4);
		if (iVar > iVar23) uVar21 = 2;
	}

LAB_1800078b3_8:
	return Classifier8Tail(state,param_4,param_5,(uint8_t)bVar6,(uint8_t)cVar19);
}

// ============================================================================
// FUN_180009960 — EdgeWalker16 (literal port).
// Walks a chain of equal-color pixels along (dir1) starting at (x,y), updating
// (*out_x, *out_y). Returns: param_5 if walked, 1 if right-side blocked, 2 if
// both blocked. Reads from state->src_world (state+0x18).
// ============================================================================
static uint16_t*
EdgeWalker16(RenderState *state, int x, int y, int dir1, uint32_t dir2,
             int *out_x, int *out_y, int threshold)
{
	return EdgeWalker16Exact(state, x, y, dir1, dir2, out_x, out_y, threshold);

	uint16_t *result = nullptr;
	int dy_dir1 = DAT_18000f0f0[dir1];
	int dx_dir1 = DAT_18000f0c8[dir1];
	*out_x = x;
	*out_y = y;
	int iVar9 = dx_dir1 + x;
	int iVar10 = dy_dir1 + y;

	PF_EffectWorld *world = state->src_world;
	int W = world->width, H = world->height, RB = world->rowbytes;
	uint8_t *base = (uint8_t*)world->data;

	auto pix = [&](int px, int py) -> uint16_t* {
		if (px < 0 || px >= W || py < 0 || py >= H) return nullptr;
		return (uint16_t*)(base + (int64_t)(py * RB) + (int64_t)px * 8);
	};

	uint16_t *puVar13 = pix(x, y);
	uint16_t *puVar12 = pix(iVar9, iVar10);

	int iVar1 = DAT_18000f0f0[(int)dir2];
	int iVar2 = DAT_18000f0c8[(int)dir2];

	auto cmp_le = [&](const uint16_t *a, const uint16_t *b) -> bool {
		if (!a || !b) return false;
		if (threshold == 0) {
			return (a[1]==b[1]) && (a[3]==b[3]) && (a[2]==b[2]) && (*a==*b);
		}
		int iVar = threshold << 7;
		if (iVar < 0) return false;
		uint32_t d, s;
		d = (uint32_t)a[1] - (uint32_t)b[1]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar) return false;
		d = (uint32_t)a[3] - (uint32_t)b[3]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar) return false;
		d = (uint32_t)a[2] - (uint32_t)b[2]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar) return false;
		d = (uint32_t)*a   - (uint32_t)*b;   s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > iVar) return false;
		return true;
	};

	bool bVar15 = (puVar13 != nullptr);
	bool bVar16 = (puVar12 != nullptr);
	if (threshold != 0) {
		bVar15 = bVar15 && (-1 < (threshold << 7));
		bVar16 = bVar16 && (-1 < (threshold << 7));
	}
	bool bVar5 = cmp_le(puVar13, puVar12);

	bool bVar17 = !bVar15;
	if (!bVar17) {
		while (true) {
			if (!bVar16 || bVar5) break;
			*out_x += iVar2;
			iVar10 += iVar1;
			*out_y += iVar1;
			iVar9 += iVar2;
			uint16_t *puVar11 = pix(*out_x, *out_y);
			uint16_t *puVar6  = pix(iVar9, iVar10);
			bVar15 = cmp_le(puVar13, puVar11);
			bVar16 = cmp_le(puVar12, puVar6);
			bVar5  = cmp_le(puVar11, puVar6);
			puVar13 = puVar11;
			puVar12 = puVar6;
			if (!bVar15) break;
		}
		bVar17 = !bVar15;
	}

	if (!bVar17) result = (uint16_t*)(uintptr_t)dir2;
	if (!bVar16) result = (uint16_t*)(uintptr_t)1;
	if (!bVar15 && !bVar16) result = (uint16_t*)(uintptr_t)2;

	*out_x -= iVar2;
	*out_y -= iVar1;
	return result;
}

static uint8_t*
EdgeWalker8Legacy(RenderState *state, int x, int y, int dir1, uint32_t dir2,
            int *out_x, int *out_y, int threshold)
{
	uint8_t *result = nullptr;
	int dy_dir1 = DAT_18000f0f0[dir1];
	int dx_dir1 = DAT_18000f0c8[dir1];
	*out_x = x;
	*out_y = y;
	int iVar9 = dx_dir1 + x;
	int iVar10 = dy_dir1 + y;

	PF_EffectWorld *world = state->src_world;
	int W = world->width, H = world->height, RB = world->rowbytes;
	uint8_t *base = (uint8_t*)world->data;

	auto pix = [&](int px, int py) -> uint8_t* {
		if (px < 0 || px >= W || py < 0 || py >= H) return nullptr;
		return base + (int64_t)(py * RB) + (int64_t)px * 4;
	};

	uint8_t *pbVar13 = pix(x, y);
	uint8_t *pbVar12 = pix(iVar9, iVar10);

	int iVar1 = DAT_18000f0f0[(int)dir2];
	int iVar2 = DAT_18000f0c8[(int)dir2];

	auto cmp_le = [&](const uint8_t *a, const uint8_t *b) -> bool {
		if (!a || !b) return false;
		if (threshold == 0) {
			return (a[1]==b[1]) && (a[3]==b[3]) && (a[2]==b[2]) && (*a==*b);
		}
		uint32_t d, s;
		d = (uint32_t)a[1] - (uint32_t)b[1]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > threshold) return false;
		d = (uint32_t)a[3] - (uint32_t)b[3]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > threshold) return false;
		d = (uint32_t)a[2] - (uint32_t)b[2]; s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > threshold) return false;
		d = (uint32_t)*a   - (uint32_t)*b;   s = (int32_t)d >> 31;
		if ((int32_t)((d ^ s) - s) > threshold) return false;
		return true;
	};

	bool bVar15 = (pbVar13 != nullptr);
	bool bVar16 = (pbVar12 != nullptr);
	if (threshold != 0) {
		bVar15 = bVar15 && (-1 < threshold);
		bVar16 = bVar16 && (-1 < threshold);
	}
	bool bVar6 = cmp_le(pbVar13, pbVar12);

	bool bVar17 = !bVar15;
	if (!bVar17) {
		while (true) {
			if (!bVar16 || bVar6) break;
			*out_x += iVar2;
			iVar10 += iVar1;
			*out_y += iVar1;
			iVar9 += iVar2;
			uint8_t *pbVar11 = pix(*out_x, *out_y);
			uint8_t *pbVar7  = pix(iVar9, iVar10);
			bVar15 = cmp_le(pbVar13, pbVar11);
			bVar16 = cmp_le(pbVar12, pbVar7);
			bVar6  = cmp_le(pbVar11, pbVar7);
			pbVar13 = pbVar11;
			pbVar12 = pbVar7;
			if (!bVar15) break;
		}
		bVar17 = !bVar15;
	}

	if (!bVar17) result = (uint8_t*)(uintptr_t)dir2;
	if (!bVar16) result = (uint8_t*)(uintptr_t)1;
	if (!bVar15 && !bVar16) result = (uint8_t*)(uintptr_t)2;

	*out_x -= iVar2;
	*out_y -= iVar1;
	{
		int tx, ty;
		if (trace_xy_enabled(&tx, &ty) && y >= ty - 2 && y <= ty + 2) {
			fprintf(stderr,
			        "[walk8] start=(%d,%d) dir1=%d dir2=%u thr=%d -> out=(%d,%d) res=%d\n",
			        x, y, dir1, dir2, threshold, *out_x, *out_y,
			        (int)(intptr_t)result);
		}
	}
	return result;
}

static uint8_t*
EdgeWalker8(RenderState *state, int x, int y, int dir1, uint32_t dir2,
            int *out_x, int *out_y, int threshold)
{
	return EdgeWalker8Exact(state,x,y,dir1,dir2,out_x,out_y,threshold);
}

// ============================================================================
// FUN_180004450 — AltHandler16 (literal port). Used for scan_type 2 and 3.
// Reads neighbor pointers from the dispatcher's neigh array (param_2).
// State field: tolerance_hi (state+0xc) for 16-bit comparisons.
// dst_world at state+0x20.
// ============================================================================
static void
AltHandler16(RenderState *state, uintptr_t *neigh, int x, int y, uint32_t dir, int scan_type)
{
	int iVar3 = state->tolerance_hi;
	int64_t lVar4 = (int64_t)(int)dir;
	uint32_t local_b8 = DAT_18000f028[lVar4];
	int iVar10 = DAT_18000f0c8[lVar4] + x;
	int iVar8 = DAT_18000f0f0[lVar4] + y;
	uint32_t local_c0 = DAT_18000f0a0[lVar4];
	uint16_t *target_pix = nullptr;
	uint16_t *center_pix = nullptr;

	int local_c4, local_c8;
	int iVar7, iVar9;
	uint16_t blend_buf[4];
	uintptr_t local_a8[10];
	uintptr_t *neigh_use = neigh;

	if (scan_type == 3) {
		EdgeWalker16(state, x, y, dir, DAT_18000f000[lVar4], &local_c4, &local_c8, iVar3);
		uint32_t u; int dlx, dly;
		dlx = local_c4 - x; u = dlx >> 31; dlx = (dlx ^ u) - u;
		dly = local_c8 - y; u = dly >> 31; dly = (dly ^ u) - u;
		iVar8 = (dly + 1 <= dlx + 1) ? dlx : dly;

		EdgeWalker16(state, x, y, local_b8, local_c0, &local_c4, &local_c8, iVar3);
		dlx = local_c4 - x; u = dlx >> 31; dlx = (dlx ^ u) - u;
		dly = local_c8 - y; u = dly >> 31; dly = (dly ^ u) - u;
		iVar3 = (dly + 1 <= dlx + 1) ? dlx : dly;

		if (((unsigned)(iVar8 - 1) > 1u) || (iVar3 + 1 < 2)) {
			if ((unsigned)(iVar3 - 1) > 1u) return;
			if (iVar8 + 1 < 2) return;
		}
		PF_EffectWorld *dst = state->dst_world;
		if ((x >= 0) && (x < dst->width) && (y >= 0) && (y < dst->height)) {
			target_pix = (uint16_t*)((uint8_t*)dst->data + (int64_t)(y * dst->rowbytes) + (int64_t)x * 8);
		}
		center_pix = *(uint16_t**)((uint8_t*)neigh + 0x20);
		ColorBlend16((uint64_t*)neigh, (uint16_t*)blend_buf, 2);
		// Reorganize to local_c0 layout: blend_buf is the 4 result components written by ColorBlend16
		// to a temp buffer. Win uses (ushort *)&local_c0 as the param_2 buffer (4 ushorts at offset 0).
		if (!target_pix || !center_pix ||
		    (target_pix[1] != center_pix[1]) || (target_pix[3] != center_pix[3]) ||
		    (target_pix[2] != center_pix[2])) {
			AlphaBlend16(blend_buf, DAT_18000d1f0, target_pix, DAT_18000d1f0, target_pix);
			return;
		}
		uint16_t uVar2 = *center_pix;
		if (*target_pix == uVar2) {
			*target_pix    = blend_buf[0];
			target_pix[3]  = blend_buf[3];
			target_pix[2]  = blend_buf[2];
			target_pix[1]  = blend_buf[1];
			return;
		}
		AlphaBlend16(blend_buf, DAT_18000d1f0, target_pix, DAT_18000d1f0, target_pix);
		return;
	}
	if (scan_type != 2) return;

	EdgeWalker16(state, iVar10, iVar8, DAT_18000f000[lVar4], dir, &local_c4, &local_c8, iVar3);
	{
		uint32_t u; int dlx, dly;
		dly = local_c8 - iVar8; u = dly >> 31; dly = (dly ^ u) - u;
		dlx = local_c4 - iVar10; u = dlx >> 31; dlx = (dlx ^ u) - u;
		iVar7 = (dlx + 1 <= dly + 1) ? dly : dlx;
	}
	EdgeWalker16(state, iVar10, iVar8, local_c0, local_b8, &local_c4, &local_c8, iVar3);
	{
		uint32_t u; int dlx, dly;
		dly = local_c8 - iVar8; u = dly >> 31; dly = (dly ^ u) - u;
		dlx = local_c4 - iVar10; u = dlx >> 31; dlx = (dlx ^ u) - u;
		iVar3 = (dlx + 1 <= dly + 1) ? dly : dlx;
		(void)iVar9;
	}
	if (((unsigned)(iVar7 - 1) > 1u) || (iVar3 + 1 < 2)) {
		if ((unsigned)(iVar3 - 1) > 1u) return;
		if (iVar7 + 1 < 2) return;
	}
	NeighborExtract16(iVar10, iVar8, state, local_a8);
	neigh_use = local_a8;
	PF_EffectWorld *dst = state->dst_world;
	if ((iVar10 >= 0) && (iVar10 < dst->width) && (iVar8 >= 0) && (iVar8 < dst->height)) {
		target_pix = (uint16_t*)((uint8_t*)dst->data + (int64_t)(iVar8 * dst->rowbytes) + (int64_t)iVar10 * 8);
	}
	ColorBlend16((uint64_t*)neigh_use, (uint16_t*)blend_buf, 2);
	center_pix = (uint16_t*)local_a8[4];
	if (!target_pix || !center_pix ||
	    (target_pix[1] != center_pix[1]) || (target_pix[3] != center_pix[3]) ||
	    (target_pix[2] != center_pix[2])) {
		AlphaBlend16(blend_buf, DAT_18000d1f0, target_pix, DAT_18000d1f0, target_pix);
		return;
	}
	uint16_t uVar2 = *center_pix;
	if (*target_pix == uVar2) {
		*target_pix    = blend_buf[0];
		target_pix[3]  = blend_buf[3];
		target_pix[2]  = blend_buf[2];
		target_pix[1]  = blend_buf[1];
		return;
	}
	AlphaBlend16(blend_buf, DAT_18000d1f0, target_pix, DAT_18000d1f0, target_pix);
}

static void
AltHandler8(RenderState *state, uintptr_t *neigh, int x, int y, uint32_t dir, int scan_type)
{
	int iVar3 = state->tolerance_lo;
	int64_t lVar4 = (int64_t)(int)dir;
	uint32_t local_b0 = DAT_18000f028[lVar4];
	int iVar10 = DAT_18000f0c8[lVar4] + x;
	int iVar8 = DAT_18000f0f0[lVar4] + y;
	uint32_t local_ac = DAT_18000f0a0[lVar4];
	uint8_t *target_pix = nullptr;
	uint8_t *center_pix = nullptr;
	int local_b8, local_b4;
	int iVar7;
	uint8_t blend_buf[4];
	uintptr_t local_a8[10];
	uintptr_t *neigh_use = neigh;

	if (scan_type == 3) {
		EdgeWalker8(state, x, y, dir, DAT_18000f000[lVar4], &local_b8, &local_b4, iVar3);
		uint32_t u; int dlx, dly;
		dlx = local_b8 - x; u = dlx >> 31; dlx = (dlx ^ u) - u;
		dly = local_b4 - y; u = dly >> 31; dly = (dly ^ u) - u;
		iVar8 = (dly + 1 <= dlx + 1) ? dlx : dly;
		EdgeWalker8(state, x, y, local_b0, local_ac, &local_b8, &local_b4, iVar3);
		dlx = local_b8 - x; u = dlx >> 31; dlx = (dlx ^ u) - u;
		dly = local_b4 - y; u = dly >> 31; dly = (dly ^ u) - u;
		iVar3 = (dly + 1 <= dlx + 1) ? dlx : dly;
		if (((unsigned)(iVar8 - 1) > 1u) || (iVar3 + 1 < 2)) {
			if ((unsigned)(iVar3 - 1) > 1u) return;
			if (iVar8 + 1 < 2) return;
		}
		PF_EffectWorld *dst = state->dst_world;
		if ((x >= 0) && (x < dst->width) && (y >= 0) && (y < dst->height)) {
			target_pix = (uint8_t*)dst->data + (int64_t)(y * dst->rowbytes) + (int64_t)x * 4;
		}
		center_pix = *(uint8_t**)((uint8_t*)neigh + 0x20);
		ColorBlend8((uint64_t*)neigh, blend_buf, 2);
		if (!target_pix || !center_pix ||
		    (target_pix[1] != center_pix[1]) || (target_pix[3] != center_pix[3]) ||
		    (target_pix[2] != center_pix[2])) {
			AlphaBlend8(blend_buf, DAT_18000d1f0, target_pix, DAT_18000d1f0, target_pix);
			return;
		}
		if (*target_pix == *center_pix) {
			*target_pix    = blend_buf[0];
			target_pix[3]  = blend_buf[3];
			target_pix[2]  = blend_buf[2];
			target_pix[1]  = blend_buf[1];
			return;
		}
		AlphaBlend8(blend_buf, DAT_18000d1f0, target_pix, DAT_18000d1f0, target_pix);
		return;
	}
	if (scan_type != 2) return;

	EdgeWalker8(state, iVar10, iVar8, DAT_18000f000[lVar4], dir, &local_b8, &local_b4, iVar3);
	{
		uint32_t u; int dlx, dly;
		dly = local_b4 - iVar8; u = dly >> 31; dly = (dly ^ u) - u;
		dlx = local_b8 - iVar10; u = dlx >> 31; dlx = (dlx ^ u) - u;
		iVar7 = (dlx + 1 <= dly + 1) ? dly : dlx;
	}
	EdgeWalker8(state, iVar10, iVar8, local_ac, local_b0, &local_b8, &local_b4, iVar3);
	{
		uint32_t u; int dlx, dly;
		dly = local_b4 - iVar8; u = dly >> 31; dly = (dly ^ u) - u;
		dlx = local_b8 - iVar10; u = dlx >> 31; dlx = (dlx ^ u) - u;
		iVar3 = (dlx + 1 <= dly + 1) ? dly : dlx;
	}
	if (((unsigned)(iVar7 - 1) > 1u) || (iVar3 + 1 < 2)) {
		if ((unsigned)(iVar3 - 1) > 1u) return;
		if (iVar7 + 1 < 2) return;
	}
	NeighborExtract8(iVar10, iVar8, state, local_a8);
	neigh_use = local_a8;
	PF_EffectWorld *dst = state->dst_world;
	if ((iVar10 >= 0) && (iVar10 < dst->width) && (iVar8 >= 0) && (iVar8 < dst->height)) {
		target_pix = (uint8_t*)dst->data + (int64_t)(iVar8 * dst->rowbytes) + (int64_t)iVar10 * 4;
	}
	ColorBlend8((uint64_t*)neigh_use, blend_buf, 2);
	center_pix = (uint8_t*)local_a8[4];
	if (!target_pix || !center_pix ||
	    (target_pix[1] != center_pix[1]) || (target_pix[3] != center_pix[3]) ||
	    (target_pix[2] != center_pix[2])) {
		AlphaBlend8(blend_buf, DAT_18000d1f0, target_pix, DAT_18000d1f0, target_pix);
		return;
	}
	if (*target_pix == *center_pix) {
		*target_pix    = blend_buf[0];
		target_pix[3]  = blend_buf[3];
		target_pix[2]  = blend_buf[2];
		target_pix[1]  = blend_buf[1];
		return;
	}
	AlphaBlend8(blend_buf, DAT_18000d1f0, target_pix, DAT_18000d1f0, target_pix);
}

// ============================================================================
// SubHandler16 — literal port of FUN_180002740 (~430 lines).
//
// Inputs:
//   state    = param_1   (RenderState*)
//   neigh    = param_2   (uintptr_t[10] neighbor pointer table)
//   x, y     = param_3, param_4
//   dir      = param_5
// Outputs:
//   *o6  = kernel mode (0,1,2,3)
//   *o7  = flag-A
//   *o8  = flag-B
//   *o9, *o10  = "edge1" displacement (x,y)  — Win param_9, param_10
//   *o11,*o12  = "edge2" displacement (x,y)  — Win param_11, param_12
//   *o13,*o14  = "edge3" displacement (x,y)  — Win param_13, param_14
// ============================================================================
static void
SubHandler16(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
             uint32_t *o6, uint8_t *o7, uint8_t *o8,
             uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
             uint32_t *o13, uint32_t *o14)
{
	SubHandler16Exact(state, neigh, x, y, dir,
	                  o6, o7, o8, o9, o10, o11, o12, o13, o14);
	return;

	const uint16_t *puVar1;   // dir DAT_18000f050 pixel
	const uint16_t *puVar2;   // center pixel (neigh+0x20 = param_2[4])
	const uint16_t *puVar3;   // dir DAT_18000f078 pixel
	const uint16_t *puVar4;   // pixel at direction param_5
	uint32_t *puVar5;
	bool bVar6, bVar7;
	uint32_t uVar8, uVar9;
	int iVar10, iVar11, iVar12;
	const uint16_t *puVar13;  // dir DAT_18000f000 pixel
	const uint16_t *puVar14;  // dir DAT_18000f028 pixel
	int64_t lVar15;
	uint32_t uVar16, uVar19, uVar20, uVar21, uVar22;
	int iVar17, iVar18, iVar24, iVar25;

	uint32_t *puVar23 = o14;
	*o9 = x; *o10 = y;
	*o11 = x; *o12 = y;
	*o13 = x; *o14 = y;
	*o7 = 0;
	*o8 = 0;
	iVar17 = state->threshold;       // *(param_1+0x10) — Win threshold field
	int tol_hi = state->tolerance_hi;  // param_14._0_4_ = *(param_1+0xc)
	lVar15 = (int64_t)(int)dir;
	iVar18 = tol_hi << 7;
	iVar24 = DAT_18000f000[lVar15];
	uVar8 = (uint32_t)((int)DAT_18000f0c8[lVar15] + (int)x);
	iVar11 = DAT_18000f028[lVar15];
	puVar13 = (const uint16_t*)neigh[iVar24];
	uVar9 = (uint32_t)((int)DAT_18000f0f0[lVar15] + (int)y);
	puVar14 = (const uint16_t*)neigh[iVar11];
	uint32_t uVar16_pair = (uint32_t)DAT_18000f0a0[lVar15];
	puVar1 = (const uint16_t*)neigh[DAT_18000f050[lVar15]];
	puVar2 = *(const uint16_t**)((uint8_t*)neigh + 0x20);
	puVar3 = (const uint16_t*)neigh[DAT_18000f078[lVar15]];
	puVar4 = (const uint16_t*)neigh[lVar15];
	uint32_t local_res18_0 = x;
	uint32_t local_res20   = y;
	// param_5 / param_8 / param_9 / param_10 / param_13 are also used as
	// stack-aliased temp slots. We use plain locals.
	uint32_t loc_param5 = 0;     // == param_5 used as int holder
	uint32_t loc_param8 = 0;     // == param_8 lower 32-bits
	uint32_t loc_param9 = 0;     // == param_9 lower 32-bits
	uint32_t loc_param10 = 0;    // == param_10 lower 32-bits
	uint32_t loc_param13 = 0;    // == param_13 lower 32-bits

	iVar10 = ColorCompare16(puVar1, puVar2);
	puVar5 = o9;
	if (iVar18 < iVar10) {
		iVar10 = ColorCompare16(puVar3, puVar2);
		puVar5 = o9;
		if (iVar18 < iVar10) {
			iVar10 = ColorCompare16(puVar13, puVar2);
			puVar5 = o9;
			if (iVar18 < iVar10) {
				iVar10 = ColorCompare16(puVar14, puVar2);
				puVar5 = o9;
				uint32_t uVar21 = local_res20;
				uint32_t uVar19 = local_res18_0;
				if (iVar18 < iVar10) {
					*o9  = local_res18_0;
					*o10 = local_res20;
					int wa_x = (int)local_res18_0, wa_y = (int)local_res20;
					int wb_x = (int)uVar19,       wb_y = (int)uVar21;
					EdgeWalker16(state, (int)local_res18_0, (int)local_res20,
					             iVar24, uVar16_pair, &wa_x, &wa_y, iVar17);
					EdgeWalker16(state, (int)uVar19, (int)uVar21,
					             iVar11, uVar16_pair, &wb_x, &wb_y, iVar17);
					// We treat the EdgeWalker return as "non-zero/zero" via wb_x/wb_y vs original.
					// Actually Win uses the function's return value cast to int. EdgeWalker returns
					// nullptr/dir2/1/2 via int cast.
					// We need to capture those. Do it again with return values:
					int wa_x2 = (int)local_res18_0, wa_y2 = (int)local_res20;
					int wb_x2 = (int)uVar19,        wb_y2 = (int)uVar21;
					uint16_t *rwa = EdgeWalker16(state, (int)local_res18_0, (int)local_res20,
					                              iVar24, uVar16_pair, &wa_x2, &wa_y2, iVar17);
					uint16_t *rwb = EdgeWalker16(state, (int)uVar19, (int)uVar21,
					                              iVar11, uVar16_pair, &wb_x2, &wb_y2, iVar17);
					int param_5_val = wb_x2;
					int param_8_val = wb_y2;
					int local_res18_v = wa_x2;
					int local_res20_v = wa_y2;

					uVar8 = (uint32_t)((param_5_val - (int)uVar19) >> 31);
					*o13 = uVar19;
					*puVar23 = uVar21;
					iVar17 = (int)((param_5_val - (int)uVar19) ^ uVar8) - (int)uVar8;
					uVar8 = (uint32_t)((local_res18_v - (int)uVar19) >> 31);
					iVar24 = (int)((local_res18_v - (int)uVar19) ^ uVar8) - (int)uVar8;
					uVar8 = (uint32_t)local_res18_v;
					if (iVar17 < iVar24) {
						uVar8 = (uint32_t)param_5_val;
					}
					*o11 = uVar8;
					uVar8 = (uint32_t)((param_8_val - (int)uVar21) >> 31);
					iVar10 = (int)((param_8_val - (int)uVar21) ^ uVar8) - (int)uVar8;
					uVar8 = (uint32_t)((local_res20_v - (int)uVar21) >> 31);
					iVar11 = (int)((local_res20_v - (int)uVar21) ^ uVar8) - (int)uVar8;
					uVar8 = (uint32_t)local_res20_v;
					if (iVar10 < iVar11) {
						uVar8 = (uint32_t)param_8_val;
					}
					*o12 = uVar8;
					if ((rwa == nullptr) && (rwb == nullptr)) {
						*o6 = 0;
					} else {
						*o6 = 1;
						if (iVar24 < iVar17) {
							*o11 = (uint32_t)param_5_val;
							*o13 = (uint32_t)local_res18_v;
						} else {
							*o11 = (uint32_t)local_res18_v;
							*o13 = (uint32_t)param_5_val;
						}
						if (iVar11 < iVar10) {
							*o12 = (uint32_t)param_8_val;
							*puVar23 = (uint32_t)local_res20_v;
						} else {
							*o12 = (uint32_t)local_res20_v;
							*puVar23 = (uint32_t)param_8_val;
						}
						uint32_t uVar8b = (uint32_t)((int)DAT_18000f0c8[(int64_t)(int)uVar16_pair] + (int)*o13);
						PF_EffectWorld *src = state->src_world;
						if ((((int)uVar8b > 0) && ((int)uVar8b < src->width))) {
							uint32_t uVar16b = (uint32_t)((int)DAT_18000f0f0[(int64_t)(int)uVar16_pair] + (int)*puVar23);
							if (((int)uVar16b > 0) && ((int)uVar16b < src->height)) {
								*o13 = uVar8b;
								*puVar23 = uVar16b;
							}
						}
					}
					uint32_t a = (*o11 - *puVar5);
					uint32_t s = (uint32_t)((int)a >> 31);
					a = (a ^ s) - s;
					uint32_t b = (*o12 - *o10);
					uint32_t s2 = (uint32_t)((int)b >> 31);
					b = (b ^ s2) - s2;
					if ((int)b < (int)a) b = a;
					if ((b & 1u) != 0) return;
					*o7 = 1;
					return;
				}
				// fallthrough to LAB after the all-greater chain (4 ColorCompares passed but 4th failed)
				// Actually if !iVar18 < iVar10 means we go to the bottom path:
			}
		}
	}
	// LAB_180002b03 (post 4-cmp chain): set *o6 = 2, set displacement to (uVar8, uVar9).
	loc_param9 = uVar9;
	*o6 = 2;
	*puVar5 = uVar8;
	*o10 = uVar9;
	loc_param13 = uVar8;
	bool entered_b6f = false;

	auto cmp_within_le = [&](const uint16_t *a, const uint16_t *b) -> bool {
		if (!a || !b) return false;
		if (tol_hi == 0) {
			return (a[1]==b[1]) && (a[3]==b[3]) && (a[2]==b[2]) && (*a==*b);
		}
		uint32_t d, s;
		d = (uint32_t)a[1] - (uint32_t)b[1]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar18) return false;
		d = (uint32_t)a[3] - (uint32_t)b[3]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar18) return false;
		d = (uint32_t)a[2] - (uint32_t)b[2]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar18) return false;
		d = (uint32_t)*a   - (uint32_t)*b;   s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar18) return false;
		return true;
	};

	if (puVar2 == nullptr) goto LAB_180002b5c;
	if (cmp_within_le(puVar2, puVar1)) {
		// Win checks: if puVar1 NULL -> goto LAB_180002b5c; otherwise within tolerance -> proceed
		entered_b6f = true;
		int wa_x = (int)uVar8, wa_y = (int)uVar9;
		EdgeWalker16(state, uVar8, uVar9, iVar24, dir, &wa_x, &wa_y, iVar17);
		*puVar5 = (uint32_t)wa_x;
		*o10    = (uint32_t)wa_y;
		goto AFTER_FIRST_WALK;
	}

LAB_180002b5c:
	{
		int iVar10b = ColorCompare16(puVar2, puVar1);
		puVar23 = o10;
		if (iVar18 < iVar10b) {
			int wa_x = (int)uVar8, wa_y = (int)uVar9;
			EdgeWalker16(state, uVar8, uVar9, iVar24, dir, &wa_x, &wa_y, iVar17);
			*puVar5 = (uint32_t)wa_x;
			*o10    = (uint32_t)wa_y;
			entered_b6f = true;
			goto AFTER_FIRST_WALK;
		}
	}
	// Try LAB_180002da0 (puVar3 direction)
	{
		bool ok_iv9 = false;
		if (puVar2 == nullptr) {
			int iVar10c = ColorCompare16(puVar2, puVar3);
			if (iVar18 < iVar10c) ok_iv9 = true;
		} else {
			ok_iv9 = cmp_within_le(puVar2, puVar3) ? false : true;
		}
		if (ok_iv9) {
			int wb_x = (int)uVar8, wb_y = (int)uVar9;
			EdgeWalker16(state, uVar8, uVar9, iVar11, dir, &wb_x, &wb_y, iVar17);
			*puVar5 = (uint32_t)wb_x;
			*o10    = (uint32_t)wb_y;
		}
	}
	goto AFTER_NO_FIRST_WALK;

AFTER_FIRST_WALK:
	{
		// Try second walk in iVar11 direction with similar gating against puVar3.
		bool do_iv11 = false;
		if (puVar2 == nullptr) {
			int iVar10d = ColorCompare16(puVar2, puVar3);
			if (iVar18 < iVar10d) do_iv11 = true;
		} else {
			do_iv11 = !cmp_within_le(puVar2, puVar3);
		}
		if (do_iv11) {
			int p13_x = (int)loc_param13, p13_y = (int)loc_param9;
			EdgeWalker16(state, uVar8, uVar9, iVar11, dir, &p13_x, &p13_y, iVar17);
			loc_param13 = (uint32_t)p13_x;
			loc_param9  = (uint32_t)p13_y;
		}
		uint32_t uVar21d = local_res18_0 - *puVar5;
		uint32_t uVar19d = local_res18_0 - loc_param13;
		uint32_t uVar20d = local_res20  - loc_param9;
		uint32_t uVar22d = local_res20  - *puVar23;
		auto absi = [](uint32_t v) -> int {
			uint32_t s = (uint32_t)((int)v >> 31);
			return (int)((v ^ s) - s);
		};
		if (absi(uVar19d) <= absi(uVar20d)) uVar19d = uVar20d;
		if (absi(uVar21d) <= absi(uVar22d)) uVar21d = uVar22d;
		if (absi(uVar21d) < absi(uVar19d)) {
			*puVar5  = loc_param13;
			*puVar23 = loc_param9;
		}
	}

AFTER_NO_FIRST_WALK:
	{
		// Decision tree LAB_180002f88 / LAB_180003012 / LAB_180003117 etc.
		bool went_LAB_180003117 = false;
		bool stayed_default = (*puVar5 == uVar8) && (*puVar23 == uVar9);
		bool reached_LAB_18000302c_or_LAB_1800030d3 = false;
		bool jump_180003012 = false;

		if (stayed_default) {
			if (puVar2 != nullptr) {
				bool match = false;
				if (cmp_within_le(puVar2, puVar13) && cmp_within_le(puVar2, puVar14)) {
					match = true;
				}
				if (match) {
					*o6 = 3;
					// fall through into LAB_180002f88 → LAB_180003012/302c chain
					goto LAB_180002f88_label_post3;
				}
				goto LAB_180002f9b_label;
			}
			jump_180003012 = true;
		} else {
LAB_180002f88_label_post3:
			if (puVar2 == nullptr) { jump_180003012 = true; goto AFTER_LAB_180003012; }
			if (tol_hi == 0) {
				if (puVar13 == nullptr) { jump_180003012 = true; goto AFTER_LAB_180003012; }
LAB_180002f9b_label:
				if (!cmp_within_le(puVar2, puVar13)) {
					jump_180003012 = true;
					goto AFTER_LAB_180003012;
				}
				// reached LAB_18000302c
				reached_LAB_18000302c_or_LAB_1800030d3 = true;
			} else {
				if (puVar13 == nullptr) { jump_180003012 = true; goto AFTER_LAB_180003012; }
				if (!cmp_within_le(puVar2, puVar13)) {
					jump_180003012 = true;
					goto AFTER_LAB_180003012;
				}
				// LAB_180003080: check puVar14
				if (cmp_within_le(puVar2, puVar14)) {
					went_LAB_180003117 = true;
					goto AFTER_LAB_180003012;
				}
				// fall to LAB_1800030d3
				goto LAB_1800030d3_label;
			}
		}

AFTER_LAB_180003012:
		if (jump_180003012) {
			int iVar10e = ColorCompare16(puVar2, puVar13);
			if (iVar18 < iVar10e) {
				// LAB_18000302c
				if (puVar2 != nullptr) {
					if (tol_hi != 0) goto LAB_180003080_label;
					if (puVar14 != nullptr) {
						if ((puVar2[1]==puVar14[1]) && (puVar2[3]==puVar14[3]) &&
						    (puVar2[2]==puVar14[2]) && (*puVar2==*puVar14)) {
							*o8 = 1;
							return;
						}
					}
				}
				goto LAB_1800030d3_label;
			}
		}
		if (reached_LAB_18000302c_or_LAB_1800030d3) {
			// LAB_18000302c
			if (puVar2 != nullptr) {
				if (tol_hi != 0) goto LAB_180003080_label;
				if (puVar14 != nullptr) {
					if ((puVar2[1]==puVar14[1]) && (puVar2[3]==puVar14[3]) &&
					    (puVar2[2]==puVar14[2]) && (*puVar2==*puVar14)) {
						*o8 = 1;
						return;
					}
				}
			}
			goto LAB_1800030d3_label;
		}

LAB_180003080_label:
		if ((puVar14 != nullptr) && cmp_within_le(puVar2, puVar14)) {
			went_LAB_180003117 = true;
			goto LAB_180003117_check;
		}

LAB_1800030d3_label:
		{
			int iVar10f = ColorCompare16(puVar2, puVar14);
			if (iVar18 < iVar10f) {
				went_LAB_180003117 = true;
				goto LAB_180003117_check;
			}
		}
		// fall through to iVar25/iVar12 path
		{
			int iVar10g = (int)tol_hi;
			int iVar25g = iVar10g * -0x80;
			int iVar12g = ColorCompare16(puVar13, puVar4);
			if (iVar12g < iVar25g) {
				int iVar12h = ColorCompare16(puVar14, puVar4);
				if (iVar12h < iVar25g) {
					*o8 = 1;
					return;
				}
			}
		}
		// continue into final EdgeWalker pair + bVar6/bVar7 logic

LAB_180003117_check:
		if (went_LAB_180003117) {
			*o8 = 1;
			return;
		}

		// Final EdgeWalker pair on (local_res18_0, local_res20)
		{
		int p10_x = (int)local_res18_0, p10_y = (int)local_res20;
		EdgeWalker16(state, local_res18_0, local_res20, iVar11, uVar16_pair,
		             &p10_x, &p10_y, iVar17);
		int p5_x  = (int)local_res18_0, p5_y  = (int)local_res20;
		EdgeWalker16(state, local_res18_0, local_res20, iVar24, uVar16_pair,
		             &p5_x, &p5_y, iVar17);
		loc_param10 = (uint32_t)p10_x;
		loc_param9  = (uint32_t)p10_y;
		loc_param5  = (uint32_t)p5_x;
		// Win FUN_180002740 (decomp 1126) writes walk B's out_y into
		// local_res18[0]; keep the original x for the distance terms.
		uint32_t saved_x = local_res18_0;
		local_res18_0 = (uint32_t)p5_y;  // walk B end y

		bool bVar6 = false, bVar7 = false;
		if (tol_hi == 0) {
			if (puVar2 != nullptr && puVar13 != nullptr &&
			    (puVar2[1]==puVar13[1]) && (puVar2[3]==puVar13[3]) &&
			    (puVar2[2]==puVar13[2]) && (*puVar2==*puVar13)) {
				bVar6 = true;
			}
			if (puVar2 != nullptr && puVar14 != nullptr &&
			    (puVar2[1]==puVar14[1]) && (puVar2[3]==puVar14[3]) &&
			    (puVar2[2]==puVar14[2]) && (*puVar2==*puVar14)) {
				bVar7 = true;
			}
		} else {
			bVar6 = (puVar2 && puVar13 && cmp_within_le(puVar2, puVar13));
			bVar7 = (puVar2 && puVar14 && cmp_within_le(puVar2, puVar14));
		}

		if (bVar6) {
			if (bVar7) return;
			*o11 = loc_param10;
			local_res18_0 = loc_param9;
		} else if (bVar7) {
			*o11 = loc_param5;
			// *o12 = local_res18_0 (= walk B end y) below, per decomp 1204/1206
		} else {
			uint32_t a = saved_x    - loc_param5;     // x - B.x (decomp 1182)
			uint32_t b = local_res20 - local_res18_0; // y - B.y (decomp 1183)
			auto absi = [](uint32_t v) -> int {
				uint32_t s = (uint32_t)((int)v >> 31);
				return (int)((v ^ s) - s);
			};
			uint32_t c = saved_x    - loc_param10;    // x - A.x
			uint32_t d = local_res20 - loc_param9;    // y - A.y
			*o11 = loc_param5;
			*o12 = local_res18_0;
			if (absi(c) <= absi(d)) c = d;
			if (absi(a) <= absi(b)) a = b;
			if (absi(a) <= absi(c)) return;
			*o11 = loc_param10;
			*o12 = loc_param9;
			return;
		}
		*o12 = local_res18_0;
		return;
		}
	}
}

// ============================================================================
// SubHandler8 — literal port of FUN_1800033d0 (~430 lines).
// Same shape as SubHandler16 except 8-bit pixels and tolerance_lo (state+0x8)
// without the <<7 shift; src_world is at state+0x10 in Win.
// ============================================================================
struct SubHandler8Regs {
	uint64_t rax=0,rbx=0,rcx=0,rdx=0,rsi=0,rdi=0,rbp=0,rsp=0;
	uint64_t r8=0,r9=0,r10=0,r11=0,r12=0,r13=0,r14=0,r15=0;
};
struct SubHandler8Memory {
	static constexpr uint64_t kModule=0x180000000ull, kStack=0x700000000000ull;
	uint8_t stack[0x1000]{}; bool zf=false,sf=false,of=false; PF_EffectWorld *world=nullptr;
	RenderState *state=nullptr; bool pf16=false;
	template<class T> T raw(uint64_t a) const { T v{}; memcpy(&v,(const void*)(uintptr_t)a,sizeof(v));return v; }
	bool is_stack(uint64_t a,size_t n=1) const { return a>=kStack&&a+n<=kStack+sizeof(stack); }
	void *ptr(uint64_t a) { return is_stack(a)?(void*)(stack+a-kStack):(void*)(uintptr_t)a; }
	uint8_t read8(uint64_t a) const { if(is_stack(a))return stack[a-kStack]; return raw<uint8_t>(a); }
	uint16_t read16(uint64_t a) const { if(is_stack(a,2)){uint16_t v;memcpy(&v,stack+a-kStack,2);return v;} return raw<uint16_t>(a); }
	uint32_t read32(uint64_t a) const {
		if(is_stack(a,4)){uint32_t v;memcpy(&v,stack+a-kStack,4);return v;}
		if(state&&a==(uintptr_t)state+8)return uint32_t(state->tolerance_lo);
		if(state&&a==(uintptr_t)state+0xc)return uint32_t(state->tolerance_hi);
		if(state&&pf16&&a==(uintptr_t)state+0x10)return uint32_t(state->threshold);
		if(world&&(a==(uintptr_t)world+4||a==(uintptr_t)world+0x24))return uint32_t(world->width);
		if(world&&(a==(uintptr_t)world+8||a==(uintptr_t)world+0x28))return uint32_t(world->height);
		if(world&&(a==(uintptr_t)world+0xc||a==(uintptr_t)world+0x20))return uint32_t(world->rowbytes);
		if(a>=kModule+0xf000&&a<kModule+0xf114){
			const uint64_t o=a-kModule; const int32_t *p=nullptr; uint64_t base=0;
			if(o>=0xf000&&o<0xf024){p=DAT_18000f000;base=0xf000;}
			else if(o>=0xf028&&o<0xf04c){p=DAT_18000f028;base=0xf028;}
			else if(o>=0xf050&&o<0xf074){p=DAT_18000f050;base=0xf050;}
			else if(o>=0xf078&&o<0xf09c){p=DAT_18000f078;base=0xf078;}
			else if(o>=0xf0a0&&o<0xf0c4){p=DAT_18000f0a0;base=0xf0a0;}
			else if(o>=0xf0c8&&o<0xf0ec){p=DAT_18000f0c8;base=0xf0c8;}
			else if(o>=0xf0f0&&o<0xf114){p=DAT_18000f0f0;base=0xf0f0;}
			if(p)return uint32_t(p[(o-base)/4]);
		}
		return raw<uint32_t>(a);
	}
	uint64_t read64(uint64_t a) const { if(is_stack(a,8)){uint64_t v;memcpy(&v,stack+a-kStack,8);return v;} if(state&&a==(uintptr_t)state+(pf16?0x18:0x10))return (uintptr_t)world; if(world&&(a==(uintptr_t)world+0x10||a==(uintptr_t)world+0x18))return (uintptr_t)world->data; return raw<uint64_t>(a); }
	void write8(uint64_t a,uint8_t v){if(is_stack(a))stack[a-kStack]=v;else memcpy((void*)(uintptr_t)a,&v,1);}
	void write16(uint64_t a,uint16_t v){if(is_stack(a,2))memcpy(stack+a-kStack,&v,2);else memcpy((void*)(uintptr_t)a,&v,2);}
	void write32(uint64_t a,uint32_t v){if(is_stack(a,4))memcpy(stack+a-kStack,&v,4);else memcpy((void*)(uintptr_t)a,&v,4);}
	void write64(uint64_t a,uint64_t v){if(is_stack(a,8))memcpy(stack+a-kStack,&v,8);else memcpy((void*)(uintptr_t)a,&v,8);}
	uint64_t subflags(uint64_t a,uint64_t b,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);a&=mask;b&=mask;uint64_t r=(a-b)&mask;zf=r==0;sf=(r>>(w-1))&1;of=(((a^b)&(a^r))>>(w-1))&1;return r;}
	uint64_t addflags(uint64_t a,uint64_t b,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);a&=mask;b&=mask;uint64_t r=(a+b)&mask;zf=r==0;sf=(r>>(w-1))&1;of=((~(a^b)&(a^r))>>(w-1))&1;return r;}
	void logicflags(uint64_t r,int w){const uint64_t mask=w==64?~0ull:((1ull<<w)-1);r&=mask;zf=r==0;sf=(r>>(w-1))&1;of=false;}
};

static int32_t
Classifier16Exact(RenderState *state, uint32_t x, uint32_t y,
                  const uintptr_t *neigh, uint32_t dir)
{
	SubHandler8Regs R; SubHandler8Memory M; uint64_t T=0;
	M.state=state; M.world=state->src_world; M.pf16=true;
	R.rcx=(uintptr_t)state; R.rdx=x; R.r8=y; R.r9=(uintptr_t)neigh;
	R.rsp=SubHandler8Memory::kStack+0x800;
	M.write64(R.rsp,0xdeadbeefdeadbeefull);
	M.write64(R.rsp+0x28,dir);
#include "OLMSmoother_classifier16.generated.inc"
}

static uint16_t*
EdgeWalker16Exact(RenderState *state, int x, int y, int dir1, uint32_t dir2,
                  int *out_x, int *out_y, int threshold)
{
	SubHandler8Regs R; SubHandler8Memory M; uint64_t T=0;
	M.state=state; M.world=state->src_world; M.pf16=true;
	R.rcx=(uintptr_t)state; R.rdx=uint32_t(x); R.r8=uint32_t(y); R.r9=uint32_t(dir1);
	R.rsp=SubHandler8Memory::kStack+0x800; M.write64(R.rsp,0xdeadbeefdeadbeefull);
	const uint64_t args[]={dir2,(uintptr_t)out_x,(uintptr_t)out_y,uint32_t(threshold)};
	for(size_t i=0;i<sizeof(args)/sizeof(args[0]);++i)M.write64(R.rsp+0x28+i*8,args[i]);
#include "OLMSmoother_edgewalker16.generated.inc"
}

static void
SubHandler16Exact(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
                  uint32_t *o6, uint8_t *o7, uint8_t *o8,
                  uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
                  uint32_t *o13, uint32_t *o14)
{
	SubHandler8Regs R; SubHandler8Memory M; uint64_t T=0;
	M.state=state; M.world=state->src_world; M.pf16=true;
	R.rcx=(uintptr_t)state; R.rdx=(uintptr_t)neigh; R.r8=x; R.r9=y;
	R.rsp=SubHandler8Memory::kStack+0x800; M.write64(R.rsp,0xdeadbeefdeadbeefull);
	const uint64_t args[]={dir,(uintptr_t)o6,(uintptr_t)o7,(uintptr_t)o8,(uintptr_t)o9,
		(uintptr_t)o10,(uintptr_t)o11,(uintptr_t)o12,(uintptr_t)o13,(uintptr_t)o14};
	for(size_t i=0;i<sizeof(args)/sizeof(args[0]);++i)M.write64(R.rsp+0x28+i*8,args[i]);
#include "OLMSmoother_subhandler16.generated.inc"
}

static uint8_t*
EdgeWalker8Exact(RenderState *state, int x, int y, int dir1, uint32_t dir2,
                 int *out_x, int *out_y, int threshold)
{
	SubHandler8Regs R; SubHandler8Memory M; uint64_t T=0; M.state=state; M.world=state->src_world;
	R.rcx=(uintptr_t)state; R.rdx=uint32_t(x); R.r8=uint32_t(y); R.r9=uint32_t(dir1);
	R.rsp=SubHandler8Memory::kStack+0x800; M.write64(R.rsp,0xdeadbeefdeadbeefull);
	const uint64_t args[]={dir2,(uintptr_t)out_x,(uintptr_t)out_y,uint32_t(threshold)};
	for(size_t i=0;i<sizeof(args)/sizeof(args[0]);++i)M.write64(R.rsp+0x28+i*8,args[i]);
#include "OLMSmoother_edgewalker8.generated.inc"
}

static void
SubHandler8Exact(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
                 uint32_t *o6, uint8_t *o7, uint8_t *o8,
                 uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
                 uint32_t *o13, uint32_t *o14)
{
	SubHandler8Regs R; SubHandler8Memory M; uint64_t T=0; M.state=state; M.world=state->src_world;
	R.rcx=(uintptr_t)state; R.rdx=(uintptr_t)neigh; R.r8=x; R.r9=y;
	R.rsp=SubHandler8Memory::kStack+0x800;
	M.write64(R.rsp,0xdeadbeefdeadbeefull);
	const uint64_t args[]={dir,(uintptr_t)o6,(uintptr_t)o7,(uintptr_t)o8,(uintptr_t)o9,
		(uintptr_t)o10,(uintptr_t)o11,(uintptr_t)o12,(uintptr_t)o13,(uintptr_t)o14};
	for(size_t i=0;i<sizeof(args)/sizeof(args[0]);++i)M.write64(R.rsp+0x28+i*8,args[i]);
#include "OLMSmoother_subhandler8.generated.inc"
}

static void
SubHandler8(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
            uint32_t *o6, uint8_t *o7, uint8_t *o8,
            uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
            uint32_t *o13, uint32_t *o14)
{
	SubHandler8Exact(state,neigh,x,y,dir,o6,o7,o8,o9,o10,o11,o12,o13,o14);
}

static void
SubHandler8Legacy(RenderState *state, uintptr_t *neigh, uint32_t x, uint32_t y, uint32_t dir,
            uint32_t *o6, uint8_t *o7, uint8_t *o8,
            uint32_t *o9, uint32_t *o10, uint32_t *o11, uint32_t *o12,
            uint32_t *o13, uint32_t *o14)
{
	const uint8_t *pbVar1, *pbVar2, *pbVar3, *pbVar4;
	uint32_t *puVar5;
	int iVar10, iVar11, iVar12;
	const uint8_t *pbVar13, *pbVar14;
	int64_t lVar15;
	uint32_t uVar9, uVar16, uVar17, uVar18, uVar19, uVar20;
	int iVar21, iVar23;

	uint32_t *puVar22 = o14;
	*o9 = x; *o10 = y;
	*o11 = x; *o12 = y;
	*o13 = x; *o14 = y;
	*o7 = 0;
	*o8 = 0;
	iVar21 = state->threshold;       // *(param_1+0xc)
	iVar23 = state->tolerance_lo;    // *(param_1+0x8)
	lVar15 = (int64_t)(int)dir;
	pbVar13 = *(const uint8_t**)((uint8_t*)neigh + 0x20);
	uint32_t uVar9_init = (uint32_t)((int)DAT_18000f0c8[lVar15] + (int)x);
	uVar9 = uVar9_init;
	iVar11 = DAT_18000f028[lVar15];
	uint32_t param14_dy = (uint32_t)((int)DAT_18000f0f0[lVar15] + (int)y);
	iVar12 = DAT_18000f000[lVar15];
	pbVar14 = (const uint8_t*)neigh[iVar11];
	uVar16 = (uint32_t)DAT_18000f0a0[lVar15];
	pbVar1 = (const uint8_t*)neigh[iVar12];
	pbVar2 = (const uint8_t*)neigh[DAT_18000f050[lVar15]];
	pbVar3 = (const uint8_t*)neigh[DAT_18000f078[lVar15]];
	pbVar4 = (const uint8_t*)neigh[lVar15];
	uint32_t local_res18_0 = x;
	uint32_t local_res20_0 = y;
	uint32_t loc_param5 = 0, loc_param9 = 0, loc_param10 = 0, loc_param13 = 0;

	auto cmp_le_8 = [&](const uint8_t *a, const uint8_t *b) -> bool {
		if (!a || !b) return false;
		if (iVar23 == 0) {
			return (a[1]==b[1]) && (a[3]==b[3]) && (a[2]==b[2]) && (*a==*b);
		}
		uint32_t d, s;
		d = (uint32_t)a[1] - (uint32_t)b[1]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)a[3] - (uint32_t)b[3]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)a[2] - (uint32_t)b[2]; s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar23) return false;
		d = (uint32_t)*a   - (uint32_t)*b;   s = (uint32_t)((int)d >> 31);
		if ((int)((d ^ s) - s) > iVar23) return false;
		return true;
	};

	iVar10 = ColorCompare8(pbVar2, pbVar13);
	puVar5 = o9;
	if (iVar23 < iVar10) {
		iVar10 = ColorCompare8(pbVar3, pbVar13);
		puVar5 = o9;
		if (iVar23 < iVar10) {
			iVar10 = ColorCompare8(pbVar1, pbVar13);
			puVar5 = o9;
			if (iVar23 < iVar10) {
				iVar10 = ColorCompare8(pbVar14, pbVar13);
				puVar5 = o9;
				uint32_t uVar17b = local_res20_0;
				uint32_t uVar18b = local_res18_0;
				if (iVar23 < iVar10) {
					*o9  = local_res18_0;
					*o10 = local_res20_0;
					int wa_x = (int)local_res18_0, wa_y = (int)local_res20_0;
					int wb_x = (int)uVar18b,       wb_y = (int)uVar17b;
					uint8_t *rwa = EdgeWalker8(state, (int)local_res18_0, (int)local_res20_0,
					                            iVar12, uVar16, &wa_x, &wa_y, iVar21);
					uint8_t *rwb = EdgeWalker8(state, (int)uVar18b, (int)uVar17b,
					                            iVar11, uVar16, &wb_x, &wb_y, iVar21);
					int param_5_val = wb_x;
					int param_10_val = wb_y;

					uint32_t uVar9c = (uint32_t)((param_5_val - (int)uVar18b) >> 31);
					*o13 = uVar18b;
					*puVar22 = uVar17b;
					iVar23 = (int)((param_5_val - (int)uVar18b) ^ uVar9c) - (int)uVar9c;
					uVar9c = (uint32_t)((wa_x - (int)uVar18b) >> 31);
					iVar21 = (int)((wa_x - (int)uVar18b) ^ uVar9c) - (int)uVar9c;
					uVar9c = (uint32_t)wa_x;
					if (iVar23 < iVar21) uVar9c = (uint32_t)param_5_val;
					*o11 = uVar9c;
					uVar9c = (uint32_t)((param_10_val - (int)uVar17b) >> 31);
					iVar11 = (int)((param_10_val - (int)uVar17b) ^ uVar9c) - (int)uVar9c;
					uVar9c = (uint32_t)((wa_y - (int)uVar17b) >> 31);
					iVar12 = (int)((wa_y - (int)uVar17b) ^ uVar9c) - (int)uVar9c;
					uVar9c = (uint32_t)wa_y;
					if (iVar11 < iVar12) uVar9c = (uint32_t)param_10_val;
					*o12 = uVar9c;
					if ((rwa == nullptr) && (rwb == nullptr)) {
						*o6 = 0;
					} else {
						*o6 = 1;
						if (iVar21 < iVar23) {
							*o11 = (uint32_t)param_5_val;
							*o13 = (uint32_t)wa_x;
						} else {
							*o11 = (uint32_t)wa_x;
							*o13 = (uint32_t)param_5_val;
						}
						if (iVar12 < iVar11) {
							*o12 = (uint32_t)param_10_val;
							*puVar22 = (uint32_t)wa_y;
						} else {
							*o12 = (uint32_t)wa_y;
							*puVar22 = (uint32_t)param_10_val;
						}
						uint32_t uVar9d = (uint32_t)((int)DAT_18000f0c8[(int64_t)(int)uVar16] + (int)*o13);
						PF_EffectWorld *src = state->src_world;
						if (((int)uVar9d > 0) && ((int)uVar9d < src->width)) {
							uint32_t uVar16d = (uint32_t)((int)DAT_18000f0f0[(int64_t)(int)uVar16] + (int)*puVar22);
							if (((int)uVar16d > 0) && ((int)uVar16d < src->height)) {
								*o13 = uVar9d;
								*puVar22 = uVar16d;
							}
						}
					}
					uint32_t a = (*o11 - *puVar5);
					uint32_t s = (uint32_t)((int)a >> 31);
					a = (a ^ s) - s;
					uint32_t b = (*o12 - *o10);
					uint32_t s2 = (uint32_t)((int)b >> 31);
					b = (b ^ s2) - s2;
					if ((int)b < (int)a) b = a;
					if ((b & 1u) != 0) return;
					*o7 = 1;
					return;
				}
			}
		}
	}

	*o6 = 2;
	*puVar5 = uVar9;
	*o10 = param14_dy;
	loc_param13 = uVar9;
	loc_param9  = param14_dy;
	bool entered_b6f = false;

	if (pbVar13 == nullptr) goto LAB_8_180003a;
	if (cmp_le_8(pbVar13, pbVar2)) {
		entered_b6f = true;
		int wa_x = (int)uVar9, wa_y = (int)param14_dy;
		EdgeWalker8(state, uVar9, param14_dy, iVar12, dir, &wa_x, &wa_y, iVar21);
		*puVar5 = (uint32_t)wa_x;
		*o10    = (uint32_t)wa_y;
		goto AFTER_FIRST_WALK_8;
	}

LAB_8_180003a:
	{
		int iVar10b = ColorCompare8(pbVar13, pbVar2);
		if (iVar23 < iVar10b) {
			int wa_x = (int)uVar9, wa_y = (int)param14_dy;
			EdgeWalker8(state, uVar9, param14_dy, iVar12, dir, &wa_x, &wa_y, iVar21);
			*puVar5 = (uint32_t)wa_x;
			*o10    = (uint32_t)wa_y;
			entered_b6f = true;
			goto AFTER_FIRST_WALK_8;
		}
	}
	{
		bool ok_iv9 = false;
		if (pbVar13 == nullptr) {
			int iVar10c = ColorCompare8(pbVar13, pbVar3);
			if (iVar23 < iVar10c) ok_iv9 = true;
		} else {
			ok_iv9 = !cmp_le_8(pbVar13, pbVar3);
		}
		if (ok_iv9) {
			int wb_x = (int)uVar9, wb_y = (int)param14_dy;
			EdgeWalker8(state, uVar9, param14_dy, iVar11, dir, &wb_x, &wb_y, iVar21);
			*puVar5 = (uint32_t)wb_x;
			*o10    = (uint32_t)wb_y;
		}
	}
	goto AFTER_NO_FIRST_WALK_8;

AFTER_FIRST_WALK_8:
	{
		bool do_iv11 = false;
		if (pbVar13 == nullptr) {
			int iVar10d = ColorCompare8(pbVar13, pbVar3);
			if (iVar23 < iVar10d) do_iv11 = true;
		} else {
			do_iv11 = !cmp_le_8(pbVar13, pbVar3);
		}
		if (do_iv11) {
			int p13_x = (int)loc_param13, p13_y = (int)loc_param9;
			EdgeWalker8(state, uVar9, param14_dy, iVar11, dir, &p13_x, &p13_y, iVar21);
			loc_param13 = (uint32_t)p13_x;
			loc_param9  = (uint32_t)p13_y;
		}
		uint32_t a = local_res18_0 - *puVar5;
		uint32_t b = local_res18_0 - loc_param13;
		uint32_t c = local_res20_0 - loc_param9;
		uint32_t d = local_res20_0 - *o10;
		auto absi = [](uint32_t v) -> int {
			uint32_t s = (uint32_t)((int)v >> 31);
			return (int)((v ^ s) - s);
		};
		if (absi(b) <= absi(c)) b = c;
		if (absi(a) <= absi(d)) a = d;
		if (absi(a) < absi(b)) {
			*puVar5 = loc_param13;
			*o10    = loc_param9;
		}
	}

AFTER_NO_FIRST_WALK_8:
	{
		bool went_LAB_180003d46 = false;
		bool stayed_default = (*puVar5 == uVar9) && (*o10 == param14_dy);
		bool jump_180003c5c = false;

		if (stayed_default) {
			if (pbVar13 != nullptr) {
				bool match = false;
				if (cmp_le_8(pbVar13, pbVar1) && cmp_le_8(pbVar13, pbVar14)) {
					match = true;
				}
				if (match) {
					*o6 = 3;
					goto LAB_180003bdb_8;
				}
				goto LAB_180003be9_8;
			}
			jump_180003c5c = true;
		} else {
LAB_180003bdb_8:
			if (pbVar13 == nullptr) { jump_180003c5c = true; goto AFTER_180003c5c_8; }
			if (iVar23 == 0) {
				if (pbVar1 == nullptr) { jump_180003c5c = true; goto AFTER_180003c5c_8; }
LAB_180003be9_8:
				if (!cmp_le_8(pbVar13, pbVar1)) {
					jump_180003c5c = true;
					goto AFTER_180003c5c_8;
				}
				// LAB_180003c6f
				if (pbVar13 != nullptr) {
					if (iVar23 != 0) goto LAB_180003cba_8;
					if (pbVar14 != nullptr &&
					    (pbVar13[1]==pbVar14[1]) && (pbVar13[3]==pbVar14[3]) &&
					    (pbVar13[2]==pbVar14[2]) && (*pbVar13==*pbVar14)) {
						*o8 = 1;
						return;
					}
				}
				goto LAB_180003d0d_8;
			} else {
				if (pbVar1 == nullptr) { jump_180003c5c = true; goto AFTER_180003c5c_8; }
				if (!cmp_le_8(pbVar13, pbVar1)) {
					jump_180003c5c = true;
					goto AFTER_180003c5c_8;
				}
LAB_180003cba_8:
				if (pbVar14 != nullptr && cmp_le_8(pbVar13, pbVar14)) {
					went_LAB_180003d46 = true;
					goto AFTER_180003c5c_8;
				}
				goto LAB_180003d0d_8;
			}
		}

AFTER_180003c5c_8:
		if (jump_180003c5c) {
			int iVar10e = ColorCompare8(pbVar13, pbVar1);
			if (iVar23 < iVar10e) {
				if (pbVar13 != nullptr) {
					if (iVar23 != 0) goto LAB_180003cba_2_8;
					if (pbVar14 != nullptr &&
					    (pbVar13[1]==pbVar14[1]) && (pbVar13[3]==pbVar14[3]) &&
					    (pbVar13[2]==pbVar14[2]) && (*pbVar13==*pbVar14)) {
						*o8 = 1;
						return;
					}
				}
				goto LAB_180003d0d_8;
LAB_180003cba_2_8:
				if (pbVar14 != nullptr && cmp_le_8(pbVar13, pbVar14)) {
					went_LAB_180003d46 = true;
					goto AFTER_180003c5c_8_after;
				}
			}
		}
AFTER_180003c5c_8_after:

LAB_180003d0d_8:
		if (!went_LAB_180003d46) {
			int iVar10f = ColorCompare8(pbVar13, pbVar14);
			if (iVar23 < iVar10f) went_LAB_180003d46 = true;
		}
		if (!went_LAB_180003d46) {
			int iVar10g = ColorCompare8(pbVar1, pbVar4);
			if (iVar10g < -iVar23) {
				int iVar10h = ColorCompare8(pbVar14, pbVar4);
				if (iVar10h < -iVar23) {
					*o8 = 1;
					return;
				}
			}
		}
		if (went_LAB_180003d46) {
			*o8 = 1;
			return;
		}

		// Final walks
		uint32_t uVar18 = local_res20_0;
		uint32_t uVar9b = local_res18_0;
		int p10_x = (int)local_res18_0, p10_y = (int)local_res20_0;
		int p9_x  = (int)local_res18_0, p9_y  = (int)local_res20_0;
		EdgeWalker8(state, local_res18_0, local_res20_0, iVar11, uVar16, &p10_x, &p10_y, iVar21);
		int rl_x = (int)uVar9b, rl_y = (int)uVar18;
		int p5_x = (int)local_res18_0, p5_y = (int)local_res20_0;
		EdgeWalker8(state, uVar9b, uVar18, iVar12, uVar16, &rl_x, &p5_x, iVar21);
		(void)rl_y;
		loc_param10 = (uint32_t)p10_x;
		loc_param9  = (uint32_t)p10_y;
		// In Win FUN_1800033d0 (decomp 1565) the second EdgeWalker writes out_x
		// into local_res20[0] and out_y into param_5; every later use of
		// local_res20[0] (decomp 1621/1624/1643) therefore reads walk B's end X,
		// not the original y.
		uint32_t local_res20_after = (uint32_t)rl_x;  // walk B end x
		loc_param5 = (uint32_t)p5_x;                  // walk B end y

		bool bVar6 = false, bVar7 = false;
		if (iVar23 == 0) {
			if (pbVar13 != nullptr && pbVar1 != nullptr &&
			    (pbVar13[1]==pbVar1[1]) && (pbVar13[3]==pbVar1[3]) &&
			    (pbVar13[2]==pbVar1[2]) && (*pbVar13==*pbVar1)) bVar6 = true;
			if (pbVar13 != nullptr && pbVar14 != nullptr &&
			    (pbVar13[1]==pbVar14[1]) && (pbVar13[3]==pbVar14[3]) &&
			    (pbVar13[2]==pbVar14[2]) && (*pbVar13==*pbVar14)) bVar7 = true;
		} else {
			bVar6 = (pbVar13 && pbVar1  && cmp_le_8(pbVar13, pbVar1));
			bVar7 = (pbVar13 && pbVar14 && cmp_le_8(pbVar13, pbVar14));
		}

		if (bVar6) {
			if (bVar7) return;
			*o11 = loc_param10;
			loc_param5 = loc_param9;
		} else if (bVar7) {
			*o11 = local_res20_after;  // Win *param_11 = local_res20[0] = walk B end x
		} else {
			uint32_t a = uVar9b - local_res20_after;  // x - B.x (decomp 1621)
			uint32_t b = uVar18 - loc_param5;         // y - B.y
			uint32_t c = uVar9b - loc_param10;        // x - A.x
			uint32_t d = uVar18 - loc_param9;         // y - A.y
			*o11 = local_res20_after;
			*o12 = loc_param5;
			auto absi = [](uint32_t v) -> int {
				uint32_t s = (uint32_t)((int)v >> 31);
				return (int)((v ^ s) - s);
			};
			if (absi(c) <= absi(d)) c = d;
			if (absi(a) <= absi(b)) a = b;
			if (absi(a) <= absi(c)) return;
			*o11 = loc_param10;
			*o12 = loc_param9;
			return;
		}
		*o12 = loc_param5;
		return;
	}
}

// ============================================================================
// MainInterpKernel16 — literal port of FUN_180004b80 (~285 lines).
//
// param_1 = state, param_2 = neigh, param_3..param_14 are forwarded directly
// from SubHandler outputs (kernel mode, scan, displacements...).
// Build curve evaluator on the stack via placement new of LinearEval* class
// (Win uses raw vtable in stack slot; we use C++ virtual class which has the
// same effect — eval() reads `t` argument).
// ============================================================================
static void
MainInterpKernel16(RenderState *state, uintptr_t *neigh,
                   int param_3, int param_4, int param_5, int param_6,
                   char param_7, char param_8,
                   int param_9, int param_10, int param_11, int param_12,
                   int param_13, int param_14)
{
	const uint16_t *puVar1;
	bool bVar3 = false;
	uint32_t uVar4, uVar11, uVar12, uVar13, uVar16;
	int iVar6, iVar7, iVar8, iVar9, iVar10, iVar17, iVar18;
	const uint16_t *puVar14, *puVar15;
	float fVar19, fVar20, fVar21, fVar22, fVar23, fVar24;
	int local_174, local_170, local_148, local_144, local_140;
	uint32_t local_13c;
	int local_138, local_134, local_130;

	int64_t local_158_0 = (int64_t)param_5;
	// Storage for two curve evaluator objects, large enough for any subclass.
	alignas(16) uint8_t curve_158_buf[64];
	alignas(16) uint8_t curve_120_buf[64];
	LinearEvalBase *curve_158 = nullptr;
	LinearEvalBase *curve_120 = nullptr;
	uintptr_t local_f8[10];
	(void)curve_158_buf; (void)curve_120_buf;

	fVar23 = DAT_18000d264;
	fVar19 = DAT_18000d1f4;
	fVar22 = DAT_18000d1f0;

	local_13c = (uint32_t)((param_13 - param_11) >> 31);
	local_13c = (uint32_t)((param_13 - param_11) ^ (int)local_13c) - local_13c;
	uVar11    = (uint32_t)((param_14 - param_12) >> 31);
	uVar11    = (uint32_t)((param_14 - param_12) ^ (int)uVar11) - uVar11;
	if ((int)(local_13c + 1) <= (int)(uVar11 + 1)) local_13c = uVar11;
	uVar16 = local_13c + 1;
	uVar12 = (uint32_t)((param_9 - param_13) >> 31);
	uVar12 = (uint32_t)((param_9 - param_13) ^ (int)uVar12) - uVar12;
	uVar11 = (uint32_t)((param_10 - param_14) >> 31);
	uVar11 = (uint32_t)((param_10 - param_14) ^ (int)uVar11) - uVar11;
	if ((int)uVar11 < (int)uVar12) uVar11 = uVar12;
	uVar12 = (uint32_t)((param_11 - param_9) >> 31);
	iVar6 = (int)((param_11 - param_9) ^ (int)uVar12) - (int)uVar12;
	uVar12 = (uint32_t)((param_12 - param_10) >> 31);
	local_138 = (int)((param_12 - param_10) ^ (int)uVar12) - (int)uVar12;
	if (local_138 < iVar6) local_138 = iVar6;
	local_138 = local_138 + 1;
	puVar15 = *(const uint16_t**)((uint8_t*)neigh + 0x20);
	puVar14 = (const uint16_t*)neigh[local_158_0];
	puVar1  = (const uint16_t*)neigh[DAT_18000f000[local_158_0]];
	iVar6  = param_9  - (param_9  - param_3) / 2;
	iVar17 = param_10 - (param_10 - param_4) / 2;
	if ((uVar16 == uVar11 + 1) && (param_6 == 2)) {
		bVar3 = true;
		iVar7 = ((param_3 - param_13) % 2) + ((param_3 - param_13) / 2);
		iVar8 = ((param_4 - param_14) % 2) + ((param_4 - param_14) / 2);
		local_170 = (param_3 - param_11) / 2;
		local_174 = (param_4 - param_12) / 2;
	} else {
		local_170 = (param_3 - param_11) / 2 + (param_3 - param_11) % 2;
		local_174 = (param_4 - param_12) / 2 + (param_4 - param_12) % 2;
		if (param_6 == 1) {
			iVar8 = (iVar6 - param_13) / 2 + param_13;
			uVar12 = (uint32_t)((iVar6 - param_13) & 0x80000001);
			if ((int)uVar12 < 0) {
				uVar12 = (uint32_t)(((int)uVar12 - 1) | (int)0xfffffffe) + 1;
			}
			iVar7 = (int)uVar12 + iVar8;
			iVar9 = (iVar17 - param_14) / 2 + param_14;
			uVar12 = (uint32_t)((iVar17 - param_14) & 0x80000001);
			if ((int)uVar12 < 0) {
				uVar12 = (uint32_t)(((int)uVar12 - 1) | (int)0xfffffffe) + 1;
			}
			iVar18 = (int)uVar12 + iVar9;
			if (iVar7 == param_3) iVar7 = iVar8;
			if (iVar18 == param_4) iVar18 = iVar9;
			goto LAB_180004e0a_16;
		}
		iVar7 = (param_3 - param_13) / 2 + (param_3 - param_13) % 2;
		iVar8 = (param_4 - param_14) / 2 + (param_4 - param_14) % 2;
	}
	iVar7  = param_13 + iVar7;
	iVar18 = param_14 + iVar8;
LAB_180004e0a_16:
	uVar12 = (uint32_t)((local_170 + param_11) - iVar6);
	uVar13 = (uint32_t)((int)uVar12 >> 31);
	uVar4  = (uint32_t)((local_174 + param_12) - iVar17);
	iVar9  = (int)(uVar12 ^ uVar13) - (int)uVar13;
	uVar12 = (uint32_t)((int)uVar4 >> 31);
	iVar8  = (int)(uVar4 ^ uVar12) - (int)uVar12;
	if (iVar8 < iVar9) iVar8 = iVar9;
	iVar8 = iVar8 + 1;
	uVar12 = (uint32_t)(iVar7 - (local_170 + param_11));
	uVar4  = (uint32_t)((int)uVar12 >> 31);
	iVar9  = (int)(uVar12 ^ uVar4) - (int)uVar4;
	uVar12 = (uint32_t)(iVar18 - (local_174 + param_12));
	uVar4  = (uint32_t)((int)uVar12 >> 31);
	local_140 = (int)(uVar12 ^ uVar4) - (int)uVar4;
	if (local_140 < iVar9) local_140 = iVar9;
	local_148 = local_140 + 1;
	local_130 = DAT_18000f0c8[local_158_0] + iVar7;
	local_134 = DAT_18000f0f0[local_158_0] + iVar18;
	uVar12 = (uint32_t)((local_170 + param_11) - param_3);
	uVar13 = (uint32_t)((int)uVar12 >> 31);
	uVar4  = (uint32_t)((local_174 + param_12) - param_4);
	iVar10 = (int)(uVar12 ^ uVar13) - (int)uVar13;
	uVar12 = (uint32_t)((int)uVar4 >> 31);
	iVar9  = (int)(uVar4 ^ uVar12) - (int)uVar12;
	if (iVar9 < iVar10) iVar9 = iVar10;
	local_144 = param_3;

	if (param_6 == 0) {
		iVar9 = ColorCompare16(puVar15, puVar1);
		if ((iVar9 < 0) && (iVar9 = ColorCompare16(puVar15, puVar1), iVar9 < 0)) {
			iVar9 = ColorCompare16(puVar1, puVar14);
			if (iVar9 < 0) puVar14 = puVar1;
			iVar9 = ColorCompare16(puVar1, puVar14);
			if (iVar9 < 0) puVar14 = puVar1;
		}
		fVar22 = DAT_18000d1f4;
		fVar23 = (float)iVar8 + (float)iVar8;
		fVar19 = DAT_18000d1f4 / fVar23;
		curve_158 = new (curve_158_buf) LinearOffsetFunction(fVar19, DAT_18000d1f4 - fVar19);
		fVar23 = fVar23 - fVar22;
		fVar19 = fVar22 / fVar23;
		curve_120 = new (curve_120_buf) LinearOffsetZeroValue(
			fVar19, fVar22 - fVar19, fVar22 / (fVar23 * DAT_18000d260 - DAT_18000d1f0));
		LinearEvalBase *plVar5 = curve_120;
		if (param_7 != '\0') plVar5 = curve_158;
		InterpExecutor16(state, param_5, local_170 + param_11, local_174 + param_12,
		                 puVar15, iVar6, iVar17, puVar14, plVar5, '\x01', iVar8);
	} else if (param_6 == 1) {
		iVar9 = ColorCompare16(puVar15, puVar1);
		if ((iVar9 < 0) && (iVar9 = ColorCompare16(puVar15, puVar1), iVar9 < 0)) {
			iVar9 = ColorCompare16(puVar1, puVar14);
			if (iVar9 < 0) puVar14 = puVar1;
			iVar9 = ColorCompare16(puVar1, puVar14);
			if (iVar9 < 0) puVar14 = puVar1;
		}
		curve_120 = new (curve_120_buf) LinearThreeOffsetFunction(
			DAT_18000d1f4 / (float)(iVar8 * 4),
			((float)local_148 * DAT_18000d1f0) / (float)iVar8,
			(float)local_148 / (float)iVar8,
			DAT_18000d1f4 - DAT_18000d1f4 / (float)(iVar8 * 2));
		if (iVar8 == 1) {
			uint16_t *puVar15_dst = nullptr;
			PF_EffectWorld *dst = state->dst_world;
			if ((local_144 >= 0) && (local_144 < dst->width) &&
			    (param_4 >= 0) && (param_4 < dst->height)) {
				puVar15_dst = (uint16_t*)((uint8_t*)dst->data + (int64_t)(param_4 * dst->rowbytes) +
				                          (int64_t)local_144 * 8);
			}
			ColorBlend16((uint64_t*)neigh, puVar15_dst, 1);
		} else {
			InterpExecutor16(state, param_5, local_170 + param_11, local_174 + param_12,
			                 puVar15, iVar6, iVar17, puVar14, curve_120, '\x01', iVar8);
		}
	} else if (param_6 == 2) {
		if (bVar3) {
			fVar22 = (float)local_140 / ((float)(int)uVar16 - DAT_18000d1f0);
			if ((local_13c & 1u) == 0) {
				fVar19 = ((float)local_138 + (float)local_138) - DAT_18000d1f4;
			} else {
				fVar19 = (float)(iVar8 * 2 + -1) * DAT_18000d264;
			}
			curve_120 = new (curve_120_buf) LinearOffsetZeroOneValue(
				DAT_18000d1f0 - fVar22, fVar22 + DAT_18000d1f0,
				DAT_18000d1f4 / fVar19, DAT_18000d1f4 - DAT_18000d1f4 / fVar19);
			InterpExecutor16(state, param_5, local_170 + param_11, local_174 + param_12,
			                 puVar15, iVar6, iVar17, puVar14, curve_120, '\x01', iVar9);
		} else {
			if (0 < (int)uVar16) {
				fVar21 = (float)(int)uVar16;
				fVar24 = DAT_18000d1f4 / (fVar21 * DAT_18000d264);
				fVar20 = DAT_18000d1f4 / (fVar21 + fVar21);
				fVar21 = DAT_18000d1f0 - fVar20;
				curve_158 = new (curve_158_buf) LinearOffsetFunction(fVar20, fVar21);
				if (fVar21 <= fVar24) fVar21 = fVar24;
				curve_120 = new (curve_120_buf) LinearOffsetZeroValue(0.0f, fVar21, fVar24);
				uVar16 = uVar16 & 0x80000001u;
				if ((int)uVar16 < 0) {
					uVar16 = (uint32_t)(((int)uVar16 - 1) | (int)0xfffffffe) + 1;
				}
				if (param_8 == '\0') {
					LinearEvalBase *plVar5 = curve_158;
					if (uVar16 == 1) plVar5 = curve_120;
					InterpExecutor16(state, param_5, local_170 + param_11, local_174 + param_12,
					                 puVar15, iVar7, iVar18, puVar14, plVar5, '\x01', iVar9);
				}
			}
			if (0 < (int)uVar11) {
				fVar20 = (float)(int)uVar11;
				fVar21 = fVar19 / (fVar20 + fVar20);
				fVar22 = fVar21 + fVar22;
				curve_158 = new (curve_158_buf) LinearOffsetFunction(fVar22, fVar19 - fVar21);
				fVar23 = fVar19 - fVar19 / (fVar20 * fVar23);
				if (fVar23 <= fVar22) fVar22 = fVar23;
				curve_120 = new (curve_120_buf) LinearOffsetOneValue(fVar22, fVar19, fVar23);
				uVar11 = uVar11 & 0x80000001u;
				if ((int)uVar11 < 0) {
					uVar11 = (uint32_t)(((int)uVar11 - 1) | (int)0xfffffffe) + 1;
				}
				LinearEvalBase *plVar5 = curve_158;
				if (uVar11 == 1) plVar5 = curve_120;
				InterpExecutor16(state, param_5, local_130, local_134,
				                 puVar15, iVar6, iVar17, puVar14, plVar5, '\x01', -1);
			}
		}
	} else if (param_6 == 3) {
		uint16_t *puVar15_dst = nullptr;
		PF_EffectWorld *dst = state->dst_world;
		int iVar17b = DAT_18000f0f0[local_158_0] + param_4;
		int iVar6b  = DAT_18000f0c8[local_158_0] + param_3;
		if ((iVar6b >= 0) && (iVar6b < dst->width) &&
		    (iVar17b >= 0) && (iVar17b < dst->height)) {
			puVar15_dst = (uint16_t*)((uint8_t*)dst->data + (int64_t)(iVar17b * dst->rowbytes) +
			                          (int64_t)iVar6b * 8);
		}
		NeighborExtract16(iVar6b, iVar17b, state, local_f8);
		ColorBlend16((uint64_t*)local_f8, puVar15_dst, 4);
	}
}

// ============================================================================
// MainInterpKernel8 — literal port of FUN_180005570 (twin of MainInterpKernel16)
// ============================================================================
static void
MainInterpKernel8(RenderState *state, uintptr_t *neigh,
                  int param_3, int param_4, int param_5, int param_6,
                  char param_7, char param_8,
                  int param_9, int param_10, int param_11, int param_12,
                  int param_13, int param_14)
{
	const uint8_t *pbVar1;
	bool bVar3 = false;
	uint32_t uVar4, uVar11, uVar12, uVar13, uVar16;
	int iVar6, iVar7, iVar8, iVar9, iVar10, iVar17, iVar18;
	const uint8_t *pbVar14, *pbVar15;
	float fVar19, fVar20, fVar21, fVar22, fVar23, fVar24;
	int local_174, local_170, local_148, local_144, local_140;
	uint32_t local_13c;
	int local_138, local_134, local_130;

	int64_t local_158_0 = (int64_t)param_5;
	alignas(16) uint8_t curve_158_buf[64];
	alignas(16) uint8_t curve_120_buf[64];
	LinearEvalBase *curve_158 = nullptr;
	LinearEvalBase *curve_120 = nullptr;
	uintptr_t local_f8[10];
	(void)curve_158_buf; (void)curve_120_buf;

	fVar23 = DAT_18000d264;
	fVar19 = DAT_18000d1f4;
	fVar22 = DAT_18000d1f0;

	local_13c = (uint32_t)((param_13 - param_11) >> 31);
	local_13c = (uint32_t)((param_13 - param_11) ^ (int)local_13c) - local_13c;
	uVar11    = (uint32_t)((param_14 - param_12) >> 31);
	uVar11    = (uint32_t)((param_14 - param_12) ^ (int)uVar11) - uVar11;
	if ((int)(local_13c + 1) <= (int)(uVar11 + 1)) local_13c = uVar11;
	uVar16 = local_13c + 1;
	uVar12 = (uint32_t)((param_9 - param_13) >> 31);
	uVar12 = (uint32_t)((param_9 - param_13) ^ (int)uVar12) - uVar12;
	uVar11 = (uint32_t)((param_10 - param_14) >> 31);
	uVar11 = (uint32_t)((param_10 - param_14) ^ (int)uVar11) - uVar11;
	if ((int)uVar11 < (int)uVar12) uVar11 = uVar12;
	uVar12 = (uint32_t)((param_11 - param_9) >> 31);
	iVar6 = (int)((param_11 - param_9) ^ (int)uVar12) - (int)uVar12;
	uVar12 = (uint32_t)((param_12 - param_10) >> 31);
	local_138 = (int)((param_12 - param_10) ^ (int)uVar12) - (int)uVar12;
	if (local_138 < iVar6) local_138 = iVar6;
	local_138 = local_138 + 1;
	pbVar15 = *(const uint8_t**)((uint8_t*)neigh + 0x20);
	pbVar14 = (const uint8_t*)neigh[local_158_0];
	pbVar1  = (const uint8_t*)neigh[DAT_18000f000[local_158_0]];
	iVar6  = param_9  - (param_9  - param_3) / 2;
	iVar17 = param_10 - (param_10 - param_4) / 2;
	if ((uVar16 == uVar11 + 1) && (param_6 == 2)) {
		bVar3 = true;
		iVar7 = ((param_3 - param_13) % 2) + ((param_3 - param_13) / 2);
		iVar8 = ((param_4 - param_14) % 2) + ((param_4 - param_14) / 2);
		local_170 = (param_3 - param_11) / 2;
		local_174 = (param_4 - param_12) / 2;
	} else {
		local_170 = (param_3 - param_11) / 2 + (param_3 - param_11) % 2;
		local_174 = (param_4 - param_12) / 2 + (param_4 - param_12) % 2;
		if (param_6 == 1) {
			iVar8 = (iVar6 - param_13) / 2 + param_13;
			// Same signed remainder as the x64 sign-correction sequence, without
			// the decompiler form's signed-overflow UB on negative even deltas.
			iVar7 = (iVar6 - param_13) % 2 + iVar8;
			iVar9 = (iVar17 - param_14) / 2 + param_14;
			iVar18 = (iVar17 - param_14) % 2 + iVar9;
			if (iVar7 == param_3) iVar7 = iVar8;
			if (iVar18 == param_4) iVar18 = iVar9;
			goto LAB_1800057fa_8;
		}
		iVar7 = (param_3 - param_13) / 2 + (param_3 - param_13) % 2;
		iVar8 = (param_4 - param_14) / 2 + (param_4 - param_14) % 2;
	}
	iVar7  = param_13 + iVar7;
	iVar18 = param_14 + iVar8;
LAB_1800057fa_8:
	uVar12 = (uint32_t)((local_170 + param_11) - iVar6);
	uVar13 = (uint32_t)((int)uVar12 >> 31);
	uVar4  = (uint32_t)((local_174 + param_12) - iVar17);
	iVar9  = (int)(uVar12 ^ uVar13) - (int)uVar13;
	uVar12 = (uint32_t)((int)uVar4 >> 31);
	iVar8  = (int)(uVar4 ^ uVar12) - (int)uVar12;
	if (iVar8 < iVar9) iVar8 = iVar9;
	iVar8 = iVar8 + 1;
	uVar12 = (uint32_t)(iVar7 - (local_170 + param_11));
	uVar4  = (uint32_t)((int)uVar12 >> 31);
	iVar9  = (int)(uVar12 ^ uVar4) - (int)uVar4;
	uVar12 = (uint32_t)(iVar18 - (local_174 + param_12));
	uVar4  = (uint32_t)((int)uVar12 >> 31);
	local_140 = (int)(uVar12 ^ uVar4) - (int)uVar4;
	if (local_140 < iVar9) local_140 = iVar9;
	local_148 = local_140 + 1;
	local_130 = DAT_18000f0c8[local_158_0] + iVar7;
	local_134 = DAT_18000f0f0[local_158_0] + iVar18;
	uVar12 = (uint32_t)((local_170 + param_11) - param_3);
	uVar13 = (uint32_t)((int)uVar12 >> 31);
	uVar4  = (uint32_t)((local_174 + param_12) - param_4);
	iVar10 = (int)(uVar12 ^ uVar13) - (int)uVar13;
	uVar12 = (uint32_t)((int)uVar4 >> 31);
	iVar9  = (int)(uVar4 ^ uVar12) - (int)uVar12;
	if (iVar9 < iVar10) iVar9 = iVar10;
	local_144 = param_3;

	if (param_6 == 0) {
		iVar9 = ColorCompare8(pbVar15, pbVar1);
		if ((iVar9 < 0) && (iVar9 = ColorCompare8(pbVar15, pbVar1), iVar9 < 0)) {
			iVar9 = ColorCompare8(pbVar1, pbVar14);
			if (iVar9 < 0) pbVar14 = pbVar1;
			iVar9 = ColorCompare8(pbVar1, pbVar14);
			if (iVar9 < 0) pbVar14 = pbVar1;
		}
		fVar22 = DAT_18000d1f4;
		fVar23 = (float)iVar8 + (float)iVar8;
		fVar19 = DAT_18000d1f4 / fVar23;
		curve_158 = new (curve_158_buf) LinearOffsetFunction(fVar19, DAT_18000d1f4 - fVar19);
		fVar23 = fVar23 - fVar22;
		fVar19 = fVar22 / fVar23;
		curve_120 = new (curve_120_buf) LinearOffsetZeroValue(
			fVar19, fVar22 - fVar19, fVar22 / (fVar23 * DAT_18000d260 - DAT_18000d1f0));
		LinearEvalBase *plVar5 = curve_120;
		if (param_7 != '\0') plVar5 = curve_158;
		InterpExecutor8(state, param_5, local_170 + param_11, local_174 + param_12,
		                pbVar15, iVar6, iVar17, pbVar14, plVar5, '\x01', iVar8);
	} else if (param_6 == 1) {
		iVar9 = ColorCompare8(pbVar15, pbVar1);
		if ((iVar9 < 0) && (iVar9 = ColorCompare8(pbVar15, pbVar1), iVar9 < 0)) {
			iVar9 = ColorCompare8(pbVar1, pbVar14);
			if (iVar9 < 0) pbVar14 = pbVar1;
			iVar9 = ColorCompare8(pbVar1, pbVar14);
			if (iVar9 < 0) pbVar14 = pbVar1;
		}
		curve_120 = new (curve_120_buf) LinearThreeOffsetFunction(
			DAT_18000d1f4 / (float)(iVar8 * 4),
			((float)local_148 * DAT_18000d1f0) / (float)iVar8,
			(float)local_148 / (float)iVar8,
			DAT_18000d1f4 - DAT_18000d1f4 / (float)(iVar8 * 2));
		if (iVar8 == 1) {
			uint8_t *pbVar15_dst = nullptr;
			PF_EffectWorld *dst = state->dst_world;
			if ((local_144 >= 0) && (local_144 < dst->width) &&
			    (param_4 >= 0) && (param_4 < dst->height)) {
				pbVar15_dst = (uint8_t*)dst->data + (int64_t)(param_4 * dst->rowbytes) +
				              (int64_t)local_144 * 4;
			}
			ColorBlend8((uint64_t*)neigh, pbVar15_dst, 1);
		} else {
			InterpExecutor8(state, param_5, local_170 + param_11, local_174 + param_12,
			                pbVar15, iVar6, iVar17, pbVar14, curve_120, '\x01', iVar8);
		}
	} else if (param_6 == 2) {
		if (bVar3) {
			fVar22 = (float)local_140 / ((float)(int)uVar16 - DAT_18000d1f0);
			if ((local_13c & 1u) == 0) {
				fVar19 = ((float)local_138 + (float)local_138) - DAT_18000d1f4;
			} else {
				fVar19 = (float)(iVar8 * 2 + -1) * DAT_18000d264;
			}
			curve_120 = new (curve_120_buf) LinearOffsetZeroOneValue(
				DAT_18000d1f0 - fVar22, fVar22 + DAT_18000d1f0,
				DAT_18000d1f4 / fVar19, DAT_18000d1f4 - DAT_18000d1f4 / fVar19);
			InterpExecutor8(state, param_5, local_170 + param_11, local_174 + param_12,
			                pbVar15, iVar6, iVar17, pbVar14, curve_120, '\x01', iVar9);
		} else {
			if (0 < (int)uVar16) {
				fVar21 = (float)(int)uVar16;
				fVar24 = DAT_18000d1f4 / (fVar21 * DAT_18000d264);
				fVar20 = DAT_18000d1f4 / (fVar21 + fVar21);
				fVar21 = DAT_18000d1f0 - fVar20;
				curve_158 = new (curve_158_buf) LinearOffsetFunction(fVar20, fVar21);
				if (fVar21 <= fVar24) fVar21 = fVar24;
				curve_120 = new (curve_120_buf) LinearOffsetZeroValue(0.0f, fVar21, fVar24);
				uVar16 = uVar16 & 0x80000001u;
				if ((int)uVar16 < 0) {
					uVar16 = (uint32_t)(((int)uVar16 - 1) | (int)0xfffffffe) + 1;
				}
				if (param_8 == '\0') {
					LinearEvalBase *plVar5 = curve_158;
					if (uVar16 == 1) plVar5 = curve_120;
					InterpExecutor8(state, param_5, local_170 + param_11, local_174 + param_12,
					                pbVar15, iVar7, iVar18, pbVar14, plVar5, '\x01', iVar9);
				}
			}
			if (0 < (int)uVar11) {
				fVar20 = (float)(int)uVar11;
				fVar21 = fVar19 / (fVar20 + fVar20);
				fVar22 = fVar21 + fVar22;
				curve_158 = new (curve_158_buf) LinearOffsetFunction(fVar22, fVar19 - fVar21);
				fVar23 = fVar19 - fVar19 / (fVar20 * fVar23);
				if (fVar23 <= fVar22) fVar22 = fVar23;
				curve_120 = new (curve_120_buf) LinearOffsetOneValue(fVar22, fVar19, fVar23);
				uVar11 = uVar11 & 0x80000001u;
				if ((int)uVar11 < 0) {
					uVar11 = (uint32_t)(((int)uVar11 - 1) | (int)0xfffffffe) + 1;
				}
				LinearEvalBase *plVar5 = curve_158;
				if (uVar11 == 1) plVar5 = curve_120;
				InterpExecutor8(state, param_5, local_130, local_134,
				                pbVar15, iVar6, iVar17, pbVar14, plVar5, '\x01', -1);
			}
		}
	} else if (param_6 == 3) {
		uint8_t *pbVar15_dst = nullptr;
		PF_EffectWorld *dst = state->dst_world;
		int iVar17b = DAT_18000f0f0[local_158_0] + param_4;
		int iVar6b  = DAT_18000f0c8[local_158_0] + param_3;
		if ((iVar6b >= 0) && (iVar6b < dst->width) &&
		    (iVar17b >= 0) && (iVar17b < dst->height)) {
			pbVar15_dst = (uint8_t*)dst->data + (int64_t)(iVar17b * dst->rowbytes) +
			              (int64_t)iVar6b * 4;
		}
		NeighborExtract8(iVar6b, iVar17b, state, local_f8);
		ColorBlend8((uint64_t*)local_f8, pbVar15_dst, 4);
	}
}

// ============================================================================
// InterpExecutor16 — literal port of FUN_180005f60.
//
// Loop body (Win disasm 0x180006090):
//   for (i = 0; i <= iVar16; ++i) {
//     t = (iVar16 > 0) ? (float)i / (float)iVar16 : 0.0f;       // implicit XMM1
//     weight = curve.eval(t);  // virtual call, returns float
//     weight = clamp(weight, 0, 1);
//     ... blend using weight
//   }
// param_5 = "color A", param_8 = "color B" (start-end pixels for blending).
// ============================================================================
static void
InterpExecutor16(RenderState *state, int param_2, int param_3, int param_4,
                 const uint16_t *param_5, int param_6, int param_7,
                 const uint16_t *param_8, LinearEvalBase *evaluator,
                 char param_10, int param_11)
{
#ifdef OLMSMOOTHER_TEST_HOOKS
	if (g_interp_executor16_test_hook != nullptr) {
		g_interp_executor16_test_hook(state,param_2,param_3,param_4,param_5,
		                              param_6,param_7,param_8,evaluator,param_10,param_11);
		return;
	}
#endif
	int iVar7  = param_11;
	char cVar6 = param_10;
	float fVar4 = DAT_18000d1f4;
	float fVar3 = DAT_18000d1f0;

	uint16_t local_68[4];
	uint16_t param_5_arr[4];
	uint16_t param_8_arr[4];
	local_68[0] = param_5[0]; local_68[1] = param_5[1];
	local_68[2] = param_5[2]; local_68[3] = param_5[3];
	param_5_arr[0] = param_8[0]; param_5_arr[1] = param_8[1];
	param_5_arr[2] = param_8[2]; param_5_arr[3] = param_8[3];

	uint32_t uVar14;
	uVar14 = (uint32_t)((param_4 - param_7) >> 31);
	int iVar16 = (int)((param_4 - param_7) ^ (int)uVar14) - (int)uVar14;
	uVar14 = (uint32_t)((param_3 - param_6) >> 31);
	int iVar12 = (int)((param_3 - param_6) ^ (int)uVar14) - (int)uVar14;
	int dx_step = DAT_18000f0c8[(int64_t)param_2];
	int dy_step = DAT_18000f0f0[(int64_t)param_2];
	if (iVar16 < iVar12) iVar16 = iVar12;
	int iVar12_loop = 0;

	if (-1 < iVar16) {
		do {
			float t;
			if (iVar16 > 0) {
				t = (float)iVar12_loop / (float)iVar16;
			} else {
				t = 0.0f;
			}
			float fVar19 = evaluator->Evaluate(t);
			float fVar2 = fVar4;
			if (fVar19 <= fVar4) fVar2 = fVar19;
			fVar19 = 0.0f;
			if (0.0f <= fVar2) fVar19 = fVar2;
			uint16_t *puVar17 = nullptr;
			uint16_t *ppuVar15 = nullptr;
			PF_EffectWorld *src = state->src_world;
			if (!((param_3 < 0) || (src->width <= param_3) ||
			      (param_4 < 0) || (src->height <= param_4))) {
				puVar17 = (uint16_t*)((uint8_t*)src->data + (int64_t)(param_4 * src->rowbytes) +
				                      (int64_t)param_3 * 8);
			}
			if (puVar17 != nullptr || param_3 >= 0) {
				PF_EffectWorld *dst = state->dst_world;
				if ((param_3 < dst->width) && (-1 < param_4) && (param_4 < dst->height)) {
					ppuVar15 = (uint16_t*)((uint8_t*)dst->data + (int64_t)(param_4 * dst->rowbytes) +
					                       (int64_t)param_3 * 8);
				}
			}
			uint16_t uVar8 = param_5_arr[0];
			uint16_t uVar9 = param_5_arr[1];
			uint16_t uVar10 = param_5_arr[2];
			uint16_t uVar11 = param_5_arr[3];
			if (cVar6 != '\0' && puVar17 != nullptr) {
				uVar8 = puVar17[0];
				uVar9 = puVar17[1];
				uVar10 = puVar17[2];
				uVar11 = puVar17[3];
				if (iVar12_loop <= iVar7) {
					uVar8 = param_5_arr[0];
					uVar9 = param_5_arr[1];
					uVar10 = param_5_arr[2];
					uVar11 = param_5_arr[3];
					local_68[0] = puVar17[0];
					local_68[1] = puVar17[1];
					local_68[2] = puVar17[2];
					local_68[3] = puVar17[3];
				}
			}
			param_5_arr[0] = uVar8; param_5_arr[1] = uVar9;
			param_5_arr[2] = uVar10; param_5_arr[3] = uVar11;
			if ((fVar4 < fVar19) || (fVar19 < 0.0f)) fVar19 = 0.0f;

			bool dst_eq_src = (ppuVar15 != nullptr && puVar17 != nullptr &&
			                   ppuVar15[1] == puVar17[1] &&
			                   ppuVar15[3] == puVar17[3] &&
			                   ppuVar15[2] == puVar17[2] &&
			                   ppuVar15[0] == puVar17[0]);
			if (!dst_eq_src) {
				AlphaBlend16(local_68, fVar4 - fVar19, param_5_arr, fVar19, param_8_arr);
				AlphaBlend16(param_8_arr, fVar3, ppuVar15 ? ppuVar15 : param_8_arr, fVar3, ppuVar15);
			} else {
				AlphaBlend16(local_68, fVar4 - fVar19, param_5_arr, fVar19, ppuVar15);
			}
			param_3 += dx_step;
			iVar12_loop++;
			param_4 += dy_step;
		} while (iVar12_loop <= iVar16);
	}
}

// ============================================================================
// InterpExecutor8 — literal port of FUN_180006270 (twin of InterpExecutor16).
// ============================================================================
static void
InterpExecutor8(RenderState *state, int param_2, int param_3, int param_4,
                const uint8_t *param_5, int param_6, int param_7,
                const uint8_t *param_8, LinearEvalBase *evaluator,
                char param_10, int param_11)
{
#ifdef OLMSMOOTHER_TEST_HOOKS
	if (g_interp_executor8_test_hook != nullptr) {
		g_interp_executor8_test_hook(state, param_2, param_3, param_4,
		                            param_5, param_6, param_7, param_8,
		                            evaluator, param_10, param_11);
		return;
	}
#endif
	int trace_x, trace_y;
	const bool tracing = trace_xy_enabled(&trace_x, &trace_y);
	const int start_x = param_3, start_y = param_4;
	int iVar8  = param_11;
	char cVar7 = param_10;
	float fVar5 = DAT_18000d1f4;
	float fVar4 = DAT_18000d1f0;

	uint8_t local_res18[4];
	uint8_t local_res10[4];
	uint8_t param_7_arr[4];
	local_res18[0] = param_5[0]; local_res18[1] = param_5[1];
	local_res18[2] = param_5[2]; local_res18[3] = param_5[3];
	local_res10[0] = param_8[0]; local_res10[1] = param_8[1];
	local_res10[2] = param_8[2]; local_res10[3] = param_8[3];

	uint32_t uVar14;
	uVar14 = (uint32_t)((param_4 - param_7) >> 31);
	int iVar16 = (int)((param_4 - param_7) ^ (int)uVar14) - (int)uVar14;
	uVar14 = (uint32_t)((param_3 - param_6) >> 31);
	int iVar13 = (int)((param_3 - param_6) ^ (int)uVar14) - (int)uVar14;
	int iVar1 = DAT_18000f0c8[(int64_t)param_2];
	int local_res20 = DAT_18000f0f0[(int64_t)param_2];
	if (iVar16 < iVar13) iVar16 = iVar13;
	int iVar13_loop = 0;

	if (-1 < iVar16) {
		do {
			float t;
			if (iVar16 > 0) {
				t = (float)iVar13_loop / (float)iVar16;
			} else {
				t = 0.0f;
			}
			float fVar19 = evaluator->Evaluate(t);
			if (tracing && param_3 == trace_x && param_4 == trace_y) {
				fprintf(stderr,
				        "[exec8] dir=%d start=(%d,%d) end_hint=(%d,%d) i=%d/%d t=%.6f eval=%.6f "
				        "iVar8=%d cVar7=%d src5=[%u,%u,%u,%u] src8=[%u,%u,%u,%u] "
				        "curve{ofs=%.6f v0=%.6f v1=%.6f v2=%.6f}\n",
				        param_2, start_x, start_y, param_6, param_7,
				        iVar13_loop, iVar16, t, fVar19, iVar8, (int)cVar7,
				        param_5[0], param_5[1], param_5[2], param_5[3],
				        param_8[0], param_8[1], param_8[2], param_8[3],
				        evaluator->offset, evaluator->v0, evaluator->v1, evaluator->v2);
			}
			float fVar3 = fVar5;
			if (fVar19 <= fVar5) fVar3 = fVar19;
			fVar19 = 0.0f;
			if (0.0f <= fVar3) fVar19 = fVar3;
			uint8_t *pbVar17 = nullptr;
			uint8_t *pbVar15 = nullptr;
			PF_EffectWorld *src = state->src_world;
			if (!((param_3 < 0) || (src->width <= param_3) ||
			      (param_4 < 0) || (src->height <= param_4))) {
				pbVar17 = (uint8_t*)src->data + (int64_t)(param_4 * src->rowbytes) +
				          (int64_t)param_3 * 4;
			}
			if (pbVar17 != nullptr || param_3 >= 0) {
				PF_EffectWorld *dst = state->dst_world;
				if ((param_3 < dst->width) && (-1 < param_4) && (param_4 < dst->height)) {
					pbVar15 = (uint8_t*)dst->data + (int64_t)(param_4 * dst->rowbytes) +
					          (int64_t)param_3 * 4;
				}
			}
			uint8_t bVar9 = local_res10[0], bVar10 = local_res10[1];
			uint8_t bVar11 = local_res10[2], bVar12 = local_res10[3];
			if (cVar7 != '\0' && pbVar17 != nullptr) {
				bVar9 = pbVar17[0]; bVar10 = pbVar17[1];
				bVar11 = pbVar17[2]; bVar12 = pbVar17[3];
				if (iVar13_loop <= iVar8) {
					bVar9 = local_res10[0]; bVar10 = local_res10[1];
					bVar11 = local_res10[2]; bVar12 = local_res10[3];
					local_res18[0] = pbVar17[0]; local_res18[1] = pbVar17[1];
					local_res18[2] = pbVar17[2]; local_res18[3] = pbVar17[3];
				}
			}
			local_res10[0] = bVar9; local_res10[1] = bVar10;
			local_res10[2] = bVar11; local_res10[3] = bVar12;
			if ((fVar5 < fVar19) || (fVar19 < 0.0f)) fVar19 = 0.0f;

			bool dst_eq_src = (pbVar15 != nullptr && pbVar17 != nullptr &&
			                   pbVar15[1] == pbVar17[1] &&
			                   pbVar15[3] == pbVar17[3] &&
			                   pbVar15[2] == pbVar17[2] &&
			                   pbVar15[0] == pbVar17[0]);
			if (!dst_eq_src) {
				AlphaBlend8(local_res18, fVar5 - fVar19, local_res10, fVar19, param_7_arr);
				AlphaBlend8(param_7_arr, fVar4, pbVar15 ? pbVar15 : param_7_arr, fVar4, pbVar15);
			} else {
				AlphaBlend8(local_res18, fVar5 - fVar19, local_res10, fVar19, pbVar15);
			}
			param_3 += iVar1;
			iVar13_loop++;
			param_4 += local_res20;
		} while (iVar13_loop <= iVar16);
	}
}

// ============================================================================
// Per-pixel scanline callbacks — match the structure of FUN_180009470 (16-bit)
// and FUN_1800095b0 (8-bit) literally:
//   1. Build 9-neighbor pointer table (FUN_180003ff0 / 180004220)
//   2. For each direction in {5, 3, 1, 7}: classify, then dispatch
//   3. Return success
// Since Classifier* returns 0 in this stage, no work is done and outP==inP.
// ============================================================================
static PF_Err
ScanlinePixel16_Main(void *refconV, A_long x, A_long y,
                     PF_Pixel16 *inP, PF_Pixel16 *outP)
{
	RenderState *state = (RenderState*)refconV;
	uintptr_t neigh[10];
	(void)inP; (void)outP;  // pre-copied in RenderEntryChain; kernel writes to dst_world.

	NeighborExtract16((int)x, (int)y, state, neigh);

	int32_t st;
	st = Classifier16(state, (uint32_t)x, (uint32_t)y, neigh, 5);
	DispatchDirection16(state, neigh, (uint32_t)x, (uint32_t)y, 5, st);
	st = Classifier16(state, (uint32_t)x, (uint32_t)y, neigh, 3);
	DispatchDirection16(state, neigh, (uint32_t)x, (uint32_t)y, 3, st);
	st = Classifier16(state, (uint32_t)x, (uint32_t)y, neigh, 1);
	DispatchDirection16(state, neigh, (uint32_t)x, (uint32_t)y, 1, st);
	st = Classifier16(state, (uint32_t)x, (uint32_t)y, neigh, 7);
	DispatchDirection16(state, neigh, (uint32_t)x, (uint32_t)y, 7, st);
	return PF_Err_NONE;
}

static PF_Err
ScanlinePixel8_Main(void *refconV, A_long x, A_long y,
                    PF_Pixel8 *inP, PF_Pixel8 *outP)
{
	RenderState *state = (RenderState*)refconV;
	uintptr_t neigh[10];
	(void)inP; (void)outP;

	NeighborExtract8((int)x, (int)y, state, neigh);

	int tx, ty;
	const bool tr = trace_xy_enabled(&tx, &ty) && (int)x == tx && (int)y == ty;
	int32_t st;
	st = Classifier8(state, (uint32_t)x, (uint32_t)y, neigh, 5);
	if (tr) fprintf(stderr, "[cls8] (%d,%d) dir=5 scan_type=%d\n", (int)x, (int)y, st);
	DispatchDirection8(state, neigh, (uint32_t)x, (uint32_t)y, 5, st);
	st = Classifier8(state, (uint32_t)x, (uint32_t)y, neigh, 3);
	if (tr) fprintf(stderr, "[cls8] (%d,%d) dir=3 scan_type=%d\n", (int)x, (int)y, st);
	DispatchDirection8(state, neigh, (uint32_t)x, (uint32_t)y, 3, st);
	st = Classifier8(state, (uint32_t)x, (uint32_t)y, neigh, 1);
	if (tr) fprintf(stderr, "[cls8] (%d,%d) dir=1 scan_type=%d\n", (int)x, (int)y, st);
	DispatchDirection8(state, neigh, (uint32_t)x, (uint32_t)y, 1, st);
	st = Classifier8(state, (uint32_t)x, (uint32_t)y, neigh, 7);
	if (tr) fprintf(stderr, "[cls8] (%d,%d) dir=7 scan_type=%d\n", (int)x, (int)y, st);
	DispatchDirection8(state, neigh, (uint32_t)x, (uint32_t)y, 7, st);
	return PF_Err_NONE;
}

// LAB_1800026e0 — PF8 key-mask callback. The temporary destination world is
// pre-copied from the source; this callback changes only an exact ARGB key
// match, replacing it with the same RGB and alpha zero.
static PF_Err
ScanlinePixel8_KeyMask(void *refconV, A_long /*x*/, A_long /*y*/,
                       PF_Pixel8 *inP, PF_Pixel8 *outP)
{
	RenderState *state = (RenderState*)refconV;
	const uint8_t key_r = (uint8_t)(state->key_rg_packed & 0xffu);
	const uint8_t key_g = (uint8_t)(state->key_rg_packed >> 8);
	const uint8_t key_b = (uint8_t)state->key_b;
	if (inP != nullptr && outP != nullptr &&
	    inP->alpha == state->key_a && inP->red == key_r &&
	    inP->green == key_g && inP->blue == key_b) {
		outP->alpha = 0;
		outP->red = key_r;
		outP->green = key_g;
		outP->blue = key_b;
	}
	return PF_Err_NONE;
}

static PF_Err
ScanlinePixel16_KeyMask(void *refconV, A_long /*x*/, A_long /*y*/,
                        PF_Pixel16 *inP, PF_Pixel16 *outP)
{
	RenderState *state = (RenderState*)refconV;
	if (inP != nullptr && outP != nullptr &&
	    inP->alpha == state->key16_a && inP->red == state->key16_r &&
	    inP->green == state->key16_g && inP->blue == state->key16_b) {
		outP->alpha = 0;
		outP->red = state->key16_r;
		outP->green = state->key16_g;
		outP->blue = state->key16_b;
	}
	return PF_Err_NONE;
}

// 32-bit float — no Win analogue.
static PF_Err
ScanlinePixelFloat_Main(void *refconV, A_long /*x*/, A_long /*y*/,
                        PF_PixelFloat *inP, PF_PixelFloat *outP)
{
	(void)refconV;
	*outP = *inP;
	return PF_Err_NONE;
}

static PF_Err
ScanlinePixelFloat_KeyMask(void *refconV, A_long /*x*/, A_long /*y*/,
                           PF_PixelFloat *inP, PF_PixelFloat *outP)
{
	(void)refconV;
	*outP = *inP;
	return PF_Err_NONE;
}

// ============================================================================
// Render entry chain — FUN_180001400 (8-bit) / FUN_1800011e0 (16-bit) literal port
// using PF_Iterate{8,16,Float} Suite. State->src_world / dst_world get set
// before each pass so the kernel-side neighbor extractor can read from them.
// ============================================================================
template <typename PixelT, typename SuiteT>
static PF_Err
RenderEntryChain(PF_InData       *in_data,
                 const char      *suite_name,
                 int32_t          suite_version,
                 PF_EffectWorld  *input,
                 PF_EffectWorld  *output,
                 RenderState     *state,
                 PF_Err         (*main_pix_fn)(void*, A_long, A_long, PixelT*, PixelT*),
                 PF_Err         (*mask_pix_fn)(void*, A_long, A_long, PixelT*, PixelT*))
{
	PF_Err err = PF_Err_NONE;
	A_long height = output->extent_hint.bottom - output->extent_hint.top;

	AEFX_SuiteScoper<SuiteT> iterate_suite =
		AEFX_SuiteScoper<SuiteT>(in_data, suite_name, suite_version);

	PF_EffectWorld *pass_input = input;
	PF_EffectWorld key_world{};
	void *key_world_data = nullptr;
	state->src_world = pass_input;
	state->dst_world = output;

	// Windows allocates and pre-copies a temporary integer world before invoking
	// LAB_1800026e0 (PF8) or LAB_180002670 (PF16). PF32 has no native analogue.
	if (state->use_key &&
	    (sizeof(PixelT) == sizeof(PF_Pixel8) || sizeof(PixelT) == sizeof(PF_Pixel16))) {
		const A_long rows = input->height;
		const A_long rowbytes = input->rowbytes;
		if (rows > 0 && rowbytes > 0) {
			const size_t bytes = (size_t)rows * (size_t)rowbytes;
			key_world_data = malloc(bytes);
			if (key_world_data == nullptr) return (PF_Err)4; // PF_Err_OUT_OF_MEMORY
			memcpy(key_world_data, input->data, bytes);
			key_world = *input;
			key_world.data = static_cast<decltype(key_world.data)>(key_world_data);
			state->src_world = input;
			state->dst_world = &key_world;
			err = iterate_suite->iterate(in_data, 0, height, input,
			                             &output->extent_hint, state,
			                             mask_pix_fn, &key_world);
			if (!err) pass_input = &key_world;
		}
	}

	// 2nd pass — main interp kernel.
	if (!err) {
		state->src_world = pass_input;
		state->dst_world = output;
		// Pre-copy input → output so kernel writes (which may target neighboring
		// pixels) survive subsequent iterate steps. The callback writes outP=inP
		// for any non-classified pixel; for classified pixels the kernel writes
		// directly into output world (state->dst_world).
		{
			A_long copy_h = pass_input->height;
			if (output->height < copy_h) copy_h = output->height;
			A_long row_bytes = pass_input->width * (int)sizeof(PixelT);
			if (output->rowbytes < pass_input->rowbytes) {
				row_bytes = (output->rowbytes < row_bytes) ? output->rowbytes : row_bytes;
			} else if (pass_input->rowbytes < row_bytes) {
				row_bytes = pass_input->rowbytes;
			}
			for (A_long row = 0; row < copy_h; ++row) {
				memcpy((uint8_t*)output->data + (int64_t)row * output->rowbytes,
				       (uint8_t*)pass_input->data + (int64_t)row * pass_input->rowbytes,
				       (size_t)row_bytes);
			}
		}
		err = iterate_suite->iterate(in_data,
		                             0,
		                             height,
		                             pass_input,
		                             &output->extent_hint,
		                             state,
		                             main_pix_fn,
		                             output);
	}

	free(key_world_data);
	return err;
}

// ----------------------------------------------------------------------------
// Build the RenderState — Win FUN_1800096f0 local_4d8 setup.
// ----------------------------------------------------------------------------
static void
BuildRenderState(PF_ParamDef *params[], short bitdepth, RenderState *state)
{
	memset(state, 0, sizeof(*state));
	state->use_key   = (uint8_t)(params[SM_USE_KEY]->u.bd.value != 0);
	state->tolerance = params[SM_TOLERANCE]->u.sd.value;
	// Both Classifier{16,8} read RAW tolerance from these fields and apply
	// `<<7` internally for 16-bit. Mirror Win local_4d0/local_4cc layout: both
	// fields hold the raw tolerance value.
	state->tolerance_lo = state->tolerance;
	state->tolerance_hi = state->tolerance;

	uint8_t a = params[SM_KEY_COLOR]->u.cd.value.alpha;
	uint8_t r = params[SM_KEY_COLOR]->u.cd.value.red;
	uint8_t g = params[SM_KEY_COLOR]->u.cd.value.green;
	uint8_t b = params[SM_KEY_COLOR]->u.cd.value.blue;

	if (bitdepth >= 16) {
		// Win widens the 8-bit color components to 15-bit at 16-bit depth.
		state->key_a         = a;
		state->key16_a       = Widen8To16(a);
		state->key16_r       = Widen8To16(r);
		state->key16_g       = Widen8To16(g);
		state->key16_b       = Widen8To16(b);
		state->threshold     = state->tolerance;
	} else {
		state->key_a         = a;
		state->key_rg_packed = (uint16_t)((g << 8) | r);
		state->key_b         = (uint16_t)b;
		state->threshold     = state->tolerance;
	}
	state->src_world = nullptr;
	state->dst_world = nullptr;
}

// ============================================================================
// Render dispatcher — Win FUN_1800096f0.
// ============================================================================
static PF_Err
DispatchRender(PF_InData       *in_data,
               PF_ParamDef     *params[],
               PF_EffectWorld  *input,
               PF_EffectWorld  *output,
               short            bitdepth)
{
	RenderState state;
	BuildRenderState(params, bitdepth, &state);

	if (bitdepth == 8) {
		return RenderEntryChain<PF_Pixel8, PF_Iterate8Suite1>(
			in_data,
			kPFIterate8Suite, kPFIterate8SuiteVersion1,
			input, output, &state,
			ScanlinePixel8_Main, ScanlinePixel8_KeyMask);
	} else if (bitdepth == 16) {
		return RenderEntryChain<PF_Pixel16, PF_Iterate16Suite1>(
			in_data,
			kPFIterate16Suite, kPFIterate16SuiteVersion1,
			input, output, &state,
			ScanlinePixel16_Main, ScanlinePixel16_KeyMask);
	} else {
		return RenderEntryChain<PF_PixelFloat, PF_IterateFloatSuite1>(
			in_data,
			kPFIterateFloatSuite, kPFIterateFloatSuiteVersion1,
			input, output, &state,
			ScanlinePixelFloat_Main, ScanlinePixelFloat_KeyMask);
	}
}

// ============================================================================
// Classic Render
// ============================================================================
static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_LayerDef *input = &params[SM_INPUT]->u.ld;
	short bitdepth = PF_WORLD_IS_DEEP(input) ? 16 : 8;
	return DispatchRender(in_data, params, input, output, bitdepth);
}

// ============================================================================
// SmartRender / SmartPreRender
// ============================================================================
static void UnionLRect_inline(const PF_LRect *src, PF_LRect *dst) {
	if (dst->left == dst->right || dst->top == dst->bottom) { *dst = *src; return; }
	if (src->left == src->right || src->top == src->bottom) return;
	if (src->left   < dst->left)   dst->left   = src->left;
	if (src->top    < dst->top)    dst->top    = src->top;
	if (src->right  > dst->right)  dst->right  = src->right;
	if (src->bottom > dst->bottom) dst->bottom = src->bottom;
}

static PF_Err
SmartPreRender(PF_InData *in_data, PF_OutData *out_data, PF_PreRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	PF_RenderRequest req = extra->input->output_request;
	PF_CheckoutResult in_result;

	ERR(extra->cb->checkout_layer(in_data->effect_ref,
		SM_INPUT, SM_INPUT, &req,
		in_data->current_time, in_data->time_step, in_data->time_scale,
		&in_result));

	UnionLRect_inline(&in_result.result_rect,     &extra->output->result_rect);
	UnionLRect_inline(&in_result.max_result_rect, &extra->output->max_result_rect);
	return err;
}

static PF_Err
SmartRender(PF_InData *in_data, PF_OutData *out_data, PF_SmartRenderExtra *extra)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	PF_EffectWorld *input_world  = nullptr;
	PF_EffectWorld *output_world = nullptr;

	ERR(extra->cb->checkout_layer_pixels(in_data->effect_ref, SM_INPUT, &input_world));
	ERR(extra->cb->checkout_output(in_data->effect_ref, &output_world));

	PF_ParamDef param_list[SM_NUM_PARAMS];
	AEFX_CLR_STRUCT(param_list[0]);
	for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
		AEFX_CLR_STRUCT(param_list[i]);
		ERR(PF_CHECKOUT_PARAM(in_data, i, in_data->current_time,
		                      in_data->time_step, in_data->time_scale,
		                      &param_list[i]));
	}

	PF_ParamDef *params[SM_NUM_PARAMS];
	for (A_long i = 0; i < SM_NUM_PARAMS; ++i) params[i] = &param_list[i];

	if (!err && input_world && output_world) {
		param_list[0].u.ld = *input_world;
		err = DispatchRender(in_data, params, input_world, output_world,
		                     extra->input->bitdepth);
	}

	for (A_long i = 1; i < SM_NUM_PARAMS; ++i) {
		PF_CHECKIN_PARAM(in_data, &param_list[i]);
	}
	return err;
}

// ============================================================================
// Entry point
// ============================================================================
extern "C" DllExport
PF_Err EffectMain(PF_Cmd cmd, PF_InData *in_data, PF_OutData *out_data,
                  PF_ParamDef *params[], PF_LayerDef *output, void *extra)
{
	PF_Err err = PF_Err_NONE;
	try {
		switch (cmd) {
		case PF_Cmd_ABOUT:
			err = About(in_data, out_data, params, output);
			break;
		case PF_Cmd_GLOBAL_SETUP:
			err = GlobalSetup(in_data, out_data, params, output);
			break;
		case PF_Cmd_PARAMS_SETUP:
			err = ParamsSetup(in_data, out_data, params, output);
			break;
		case PF_Cmd_RENDER:
			err = Render(in_data, out_data, params, output);
			break;
		case PF_Cmd_SMART_PRE_RENDER:
			err = SmartPreRender(in_data, out_data, (PF_PreRenderExtra *)extra);
			break;
		case PF_Cmd_SMART_RENDER:
			err = SmartRender(in_data, out_data, (PF_SmartRenderExtra *)extra);
			break;
		}
	} catch (PF_Err &thrown_err) {
		err = thrown_err;
	}
	return err;
}

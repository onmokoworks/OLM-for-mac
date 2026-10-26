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
	// Bound the integer offset before forming a native pointer; a+n can wrap.
	bool is_stack(uint64_t a,size_t n=1) const { return a>=kStack&&n<=sizeof(stack)&&a-kStack<=sizeof(stack)-n; }
	uint8_t read8(uint64_t a) const { if(is_stack(a))return stack[a-kStack]; return raw<uint8_t>(a); }
	uint32_t read32(uint64_t a) const {
		if(is_stack(a,4)){uint32_t v;memcpy(&v,stack+(a-kStack),4);return v;}
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
	uint64_t read64(uint64_t a) const { if(is_stack(a,8)){uint64_t v;memcpy(&v,stack+(a-kStack),8);return v;} return raw<uint64_t>(a); }
	void write8(uint64_t a,uint8_t v){if(is_stack(a))stack[a-kStack]=v;else memcpy((void*)(uintptr_t)a,&v,1);}
	void write32(uint64_t a,uint32_t v){if(is_stack(a,4))memcpy(stack+(a-kStack),&v,4);else memcpy((void*)(uintptr_t)a,&v,4);}
	void write64(uint64_t a,uint64_t v){if(is_stack(a,8))memcpy(stack+(a-kStack),&v,8);else memcpy((void*)(uintptr_t)a,&v,8);}
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


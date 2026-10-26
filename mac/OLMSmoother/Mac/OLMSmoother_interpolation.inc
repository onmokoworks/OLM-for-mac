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


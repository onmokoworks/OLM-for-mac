// FUN_180001620: blend eight neighbors, then add the requested center weight.
// The pointer table contains nine pixels; the middle branch of the second
// iteration skips index 4. param_3 selects the additional center contribution.
// Keep the accumulation order and intermediate float widths from the AEX.
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
		// The PE jump at 0x18000c41e targets IAT 0x18000d0d0 (ceilf),
		// and 0x18000c424 targets 0x18000d0c8 (floorf): round away from zero.
		// The old diagnostic host left these imports unimplemented, making
		// the following CVTTSS2SI appear to truncate the unrounded delta.
		if (_X <= 0.0f) fVar5x = floorf(_X);
		else            fVar5x = ceilf(_X);
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
		if (_X <= 0.0f) fVar5x = floorf(_X);
		else            fVar5x = ceilf(_X);
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


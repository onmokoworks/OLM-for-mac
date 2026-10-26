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


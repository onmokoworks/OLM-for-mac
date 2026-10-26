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


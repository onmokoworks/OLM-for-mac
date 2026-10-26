// --- Boost helper: f3c = (f3c+f3c)^2 * DAT_180022694 (=0.5f) applied to last appended vertex ---
static inline void win_boost_last(SmootherPolygon &poly) {
	if (poly.count > 0) {
		float &wref = poly.samples[poly.count - 1].w;
		float v = wref + wref;
		wref = v * v * K_HALF;
	}
}

// FUN_18000f8f0 — β dispatcher.  Switch key = p2[2] + (p2[5]*5 - 1) * 2.
static void win_disp_f8f0(SmootherPolygon &poly, int *p2) {
	int k = p2[2] + (p2[5] * 5 - 1) * 2;
	switch (k) {
		case 0: case 6: case 0x14: case 0x1a: case 0x1e: case 0x24: case 0x50: case 0x56:
			win_leaf_f450(poly, p2); return;
		case 1: case 7: case 0x1b: case 0x1f: case 0x25: case 0x33: case 0x39: case 0x57:
			win_leaf_ead0(poly, p2); return;
		case 4: case 0x18: case 0x22: case 0x36: case 0x54:
			win_leaf_f740(poly, p2); return;
		case 8: case 9: case 0xc: case 0xf: case 0x44: case 0x45: case 0x48: case 0x4b:
			win_leaf_f310(poly, p2); return;
		case 10: case 0x10: case 0x46: case 0x4c:
			if (win_leaf_f1d0(poly, p2, K_ONE)) win_boost_last(poly);
			if (win_leaf_f090(poly, p2, K_ONE)) win_boost_last(poly);
			return;
		case 0xb: case 0x47:
			win_leaf_ead0(poly, p2);
			win_leaf_f090(poly, p2, K_ONE);
			return;
		case 0xd: case 0x49:
			win_leaf_f090(poly, p2, K_ONE);
			return;
		case 0xe: case 0x4a:
			win_leaf_f740(poly, p2);
			win_leaf_f090(poly, p2, K_ONE);
			return;
		case 0x11: case 0x4d:
			win_leaf_ead0(poly, p2);
			win_leaf_f310(poly, p2);
			return;
		case 0x26: case 0x2a: case 0x2b: case 0x58: case 0x59:
		case 0x5c: case 0x5d: case 0x5f:
			win_leaf_e4b0(poly, p2); return;
		case 0x28: case 0x2e:
			win_leaf_f1d0(poly, p2, K_ONE);
			win_leaf_e4b0(poly, p2); return;
		case 0x29: case 0x2f: case 0x5b: case 0x61:
			win_leaf_ead0(poly, p2);
			win_leaf_e4b0(poly, p2); return;
		case 0x2c: case 0x5e:
			win_leaf_f740(poly, p2);
			win_leaf_e4b0(poly, p2); return;
		case 0x32: case 0x38:
			win_leaf_f1d0(poly, p2, K_ONE);
			return;
		case 0x3c: case 0x42:
			win_leaf_f1d0(poly, p2, K_ONE);
			win_leaf_f590(poly, p2); return;
		case 0x3a: case 0x3b: case 0x3e: case 0x3f: case 0x41:
			win_leaf_f590(poly, p2); return;
		case 0x3d: case 0x43:
			win_leaf_ead0(poly, p2);
			win_leaf_f590(poly, p2); return;
		case 0x40:
			win_leaf_f740(poly, p2);
			win_leaf_f590(poly, p2); return;
		case 0x5a: case 0x60:
			win_leaf_f450(poly, p2);
			win_leaf_e4b0(poly, p2); return;
		default: return;
	}
}

// FUN_18000fef0 — γ dispatcher.  Switch key = p2[2] - 1 + p2[5]*10.
static void win_disp_fef0(SmootherPolygon &poly, int *p2) {
	int k = p2[2] - 1 + p2[5] * 10;
	switch (k) {
		case 0: case 6: case 10: case 0x10: case 0x28: case 0x2e: case 0x46: case 0x4c:
			win_leaf_f4f0(poly, p2); return;
		case 3: case 8: case 0x12: case 0x2b: case 0x30: case 0x35: case 0x3a: case 0x4e:
			win_leaf_edb0(poly, p2); return;
		case 5: case 0xf: case 0x2d: case 0x37: case 0x4b:
			win_leaf_f820(poly, p2); return;
		case 0x14: case 0x1a: case 0x50: case 0x56:
			if (win_leaf_f270(poly, p2, K_ONE)) win_boost_last(poly);
			if (win_leaf_f130(poly, p2, K_ONE)) win_boost_last(poly);
			return;
		case 0x17: case 0x53:
			win_leaf_edb0(poly, p2);
			win_leaf_f130(poly, p2, K_ONE); return;
		case 0x18: case 0x54:
			win_leaf_f130(poly, p2, K_ONE); return;
		case 0x19: case 0x55:
			win_leaf_f820(poly, p2);
			win_leaf_f130(poly, p2, K_ONE); return;
		case 0x1c: case 0x58:
			win_leaf_edb0(poly, p2);
			win_leaf_f3b0(poly, p2); return;
		case 0x13: case 0x15: case 0x16: case 0x1b: case 0x4f: case 0x51: case 0x52: case 0x57:
			win_leaf_f3b0(poly, p2); return;
		case 0x1d: case 0x20: case 0x22: case 0x59: case 0x5b: case 0x5c: case 0x5e: case 0x61:
			win_leaf_e7c0(poly, p2); return;
		case 0x1e: case 0x24:
			win_leaf_f270(poly, p2, K_ONE);
			win_leaf_e7c0(poly, p2); return;
		case 0x21: case 0x26: case 0x5d: case 0x62:
			win_leaf_edb0(poly, p2);
			win_leaf_e7c0(poly, p2); return;
		case 0x23: case 0x5f:
			win_leaf_f820(poly, p2);
			win_leaf_e7c0(poly, p2); return;
		case 0x32: case 0x38:
			win_leaf_f270(poly, p2, K_ONE); return;
		case 0x3c: case 0x42:
			win_leaf_f270(poly, p2, K_ONE);
			win_leaf_f670(poly, p2); return;
		case 0x3b: case 0x3d: case 0x3e: case 0x40: case 0x43:
			win_leaf_f670(poly, p2); return;
		case 0x3f: case 0x44:
			win_leaf_edb0(poly, p2);
			win_leaf_f670(poly, p2); return;
		case 0x41:
			win_leaf_f820(poly, p2);
			win_leaf_f670(poly, p2); return;
		case 0x5a: case 0x60:
			win_leaf_f4f0(poly, p2);
			win_leaf_e7c0(poly, p2); return;
		default: return;
	}
}

// FUN_1800101e0 — δ dispatcher.  Switch key = (p2[2] - 1) + p2[5]*10.
static void win_disp_101e0(SmootherPolygon &poly, int *p2) {
	int k = (p2[2] - 1) + p2[5] * 10;
	switch (k) {
		case 0: case 6: case 10: case 0x10: case 0x28: case 0x2e: case 0x46: case 0x4c:
			win_leaf_f540(poly, p2); return;
		case 3: case 8: case 0x12: case 0x2b: case 0x30: case 0x35: case 0x3a: case 0x4e:
			win_leaf_ef20(poly, p2); return;
		case 5: case 0xf: case 0x2d: case 0x37: case 0x4b:
			win_leaf_f890(poly, p2); return;
		case 0x14: case 0x1a: case 0x50: case 0x56:
			if (win_leaf_f2c0(poly, p2, K_ONE)) win_boost_last(poly);
			if (win_leaf_f180(poly, p2, K_ONE)) win_boost_last(poly);
			return;
		case 0x17: case 0x53:
			win_leaf_ef20(poly, p2);
			win_leaf_f180(poly, p2, K_ONE); return;
		case 0x18: case 0x54:
			win_leaf_f180(poly, p2, K_ONE); return;
		case 0x19: case 0x55:
			win_leaf_f890(poly, p2);
			win_leaf_f180(poly, p2, K_ONE); return;
		case 0x1c: case 0x58:
			win_leaf_ef20(poly, p2);
			win_leaf_f400(poly, p2); return;
		case 0x13: case 0x15: case 0x16: case 0x1b: case 0x4f: case 0x51: case 0x52: case 0x57:
			win_leaf_f400(poly, p2); return;
		case 0x1d: case 0x20: case 0x22: case 0x59: case 0x5b: case 0x5c: case 0x5e: case 0x61:
			win_leaf_e950(poly, p2); return;
		case 0x1e: case 0x24:
			win_leaf_f2c0(poly, p2, K_ONE);
			win_leaf_e950(poly, p2); return;
		case 0x21: case 0x26: case 0x5d: case 0x62:
			win_leaf_ef20(poly, p2);
			win_leaf_e950(poly, p2); return;
		case 0x23: case 0x5f:
			win_leaf_f890(poly, p2);
			win_leaf_e950(poly, p2); return;
		case 0x32: case 0x38:
			win_leaf_f2c0(poly, p2, K_ONE); return;
		case 0x3c: case 0x42:
			win_leaf_f2c0(poly, p2, K_ONE);
			win_leaf_f6e0(poly, p2); return;
		case 0x3b: case 0x3d: case 0x3e: case 0x40: case 0x43:
			win_leaf_f6e0(poly, p2); return;
		case 0x3f: case 0x44:
			win_leaf_ef20(poly, p2);
			win_leaf_f6e0(poly, p2); return;
		case 0x41:
			win_leaf_f890(poly, p2);
			win_leaf_f6e0(poly, p2); return;
		case 0x5a: case 0x60:
			win_leaf_f540(poly, p2);
			win_leaf_e950(poly, p2); return;
		default: return;
	}
}

// FUN_1800106b0 — 9時 cardinal entry: cee0 + d6a0, dispatch via f8f0 (β).
static void win_cardinal_9(SmootherPolygon &poly) {
	if (poly.cur_x == 0) return;
	GridDesc g = grid_of(poly);
	int center[2] = { poly.cur_x, poly.cur_y };
	int s1[3]; scan_cee0(s1, &g, center);
	int s2[3]; scan_d6a0(s2, &g, center);
	int desc[6] = { s1[0], s1[1], s1[2], s2[0], s2[1], s2[2] };
	win_disp_f8f0(poly, desc);
}

// FUN_180010760 — 6時 cardinal entry: d3b0 + da50, dispatch via fef0 (γ).
static void win_cardinal_6(SmootherPolygon &poly) {
	if (poly.cur_x == poly.cplane_w - 1) return;
	GridDesc g = grid_of(poly);
	int center[2] = { poly.cur_x, poly.cur_y };
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		// These are the exact two columns consumed by d3b0/da50. Keeping the
		// dump at the cardinal boundary makes endpoint differences explainable
		// without changing class-plane or polygon behavior.
		for (int yy = poly.cur_y - 2; yy <= poly.cur_y + 3; ++yy) {
			std::fprintf(stderr,
			             "trace cardinal6 cplane y=%d x=%d bytes=%u,%u,%u,%u x1=%d bytes=%u,%u,%u,%u\n",
			             yy,
			             poly.cur_x,
			             (unsigned)cp_b(&g, poly.cur_x, yy, 0),
			             (unsigned)cp_b(&g, poly.cur_x, yy, 1),
			             (unsigned)cp_b(&g, poly.cur_x, yy, 2),
			             (unsigned)cp_b(&g, poly.cur_x, yy, 3),
			             poly.cur_x + 1,
			             (unsigned)cp_b(&g, poly.cur_x + 1, yy, 0),
			             (unsigned)cp_b(&g, poly.cur_x + 1, yy, 1),
			             (unsigned)cp_b(&g, poly.cur_x + 1, yy, 2),
			             (unsigned)cp_b(&g, poly.cur_x + 1, yy, 3));
		}
	}
	int s1[3]; scan_d3b0(s1, &g, center);
	int s2[3]; scan_da50(s2, &g, center);
	int desc[6] = { s1[0], s1[1], s1[2], s2[0], s2[1], s2[2] };
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		int k = (desc[2] - 1) + desc[5] * 10;
		std::fprintf(stderr,
		             "trace cardinal6 desc=(%d,%d,%d,%d,%d,%d) key=%d count_before=%d\n",
		             desc[0], desc[1], desc[2], desc[3], desc[4], desc[5], k, poly.count);
	}
	win_disp_fef0(poly, desc);
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr, "trace cardinal6 count_after=%d\n", poly.count);
	}
}

// FUN_180010820 — 3時 cardinal entry: d520 + dbd0, dispatch via 1800101e0 (δ).
static void win_cardinal_3(SmootherPolygon &poly) {
	if (poly.cur_y == 0) return;
	GridDesc g = grid_of(poly);
	int center[2] = { poly.cur_x, poly.cur_y };
	int s1[3]; scan_d520(s1, &g, center);
	int s2[3]; scan_dbd0(s2, &g, center);
	int desc[6] = { s1[0], s1[1], s1[2], s2[0], s2[1], s2[2] };
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		int k = (desc[2] - 1) + desc[5] * 10;
		std::fprintf(stderr,
		             "trace cardinal3 desc=(%d,%d,%d,%d,%d,%d) key=%d\n",
		             desc[0], desc[1], desc[2], desc[3], desc[4], desc[5], k);
	}
	if (g_olmsmoother2_idx18_key_hist_enabled && g_olmsmoother2_current_switch_idx == 0x18) {
		int k = (desc[2] - 1) + desc[5] * 10;
		if (k >= 0 && k < 128) ++g_olmsmoother2_idx18_cardinal3_key_hist[k];
	}
	win_disp_101e0(poly, desc);
}

// Polygon builder — Win has a 256-case switch calling 21 helpers via an 8-bit
// classifier index built from a 2×2 cell + 4 neighbor alphas.  This port now
// uses the Win polygon struct + the 4 corner helpers (literal), and a
// run-length-aware trapezoid sampler for cardinals (structural approximation
// of FUN_1800105f0 chain).
static void build_polygon(SmootherPolygon &poly,
                          const FPlane &plane_in,
                          int x, int y,
                          const SMParams &p)
{
	// Initialize the Win-layout header — class plane triple mirrors
	// Win polygon +0x18..+0x28 (see OLMSmoother2_cardinal_chain.c.txt).
	poly.plane         = &plane_in;
	poly.cplane_base   = p.class_plane;       // 4 bytes/pixel [A,R,G,B]
	poly.cplane_w      = p.w;
	poly.cplane_h      = p.h;
	poly.cplane_stride = p.w * 4;             // tight-packed byte stride
	poly._pad_2c       = 0;
	poly.cur_x         = x;
	poly.cur_y         = y;
	poly.smoothness_n  = (float)p.smoothness_raw   / 100.0f;  // DAT_180022dd0
	poly.extra_n       = (float)p.extra_smooth_raw / 100.0f;
	poly.count         = 0;
	poly.preserve_pf32_scalar_rounding = p.pf32_runtime;

	// Zero smoothness → pass-through (matches FUN_18000c280 early-out).
	if (poly.smoothness_n == 0.0f) return;

	const int w = p.w;
	const int h = p.h;
	const float STEP = 0.125f;  // DAT_180022dd4

	const uint8_t *cp = p.class_plane;
	if (!cp) return;

	// --- LITERAL port of FUN_18000c280's switch index builder ---
	// Center pixel [A,R,G,B] at (x,y).  Out-of-bounds reads return 0.
	auto cb = [&](int cx, int cy, int bi) -> uint8_t {
		if (cx < 0 || cx >= w || cy < 0 || cy >= h) return 0;
		return cp[((size_t)cy * w + cx) * 4 + bi];
	};
	uint8_t c_A = cb(x, y, 0);
	uint8_t c_R = cb(x, y, 1);
	uint8_t c_G = cb(x, y, 2);
	uint8_t c_B = cb(x, y, 3);

	// East neighbor A=0 bit (uVar9 in Win).
	// Win reads `*(lVar8 + 4 + x*4)` = pixel(x+1, y) byte 0 (A byte).
	int eR0 = (x < w - 1) ? ((cb(x + 1, y, 0) == 0) ? 1 : 0) : 1;

	// Below-row probes (bVar15/16, uVar7).
	// Win addressing (after lVar13 := (y+1)*stride):
	//   bVar15 = byte at (y+1)*stride + base + x*4 - 1  -> pixel(x-1, y+1) byte 3 (B)  [SW]
	//   bVar16 = byte at (y+1)*stride + base + x*4 + 1  -> pixel(x,   y+1) byte 1 (R)  [South!]
	//   uVar7  = byte at (y+1)*stride + base + x*4 + 6  -> pixel(x+1, y+1) byte 2 (G)  [SE]
	bool bSW = false, bSE = false;
	int uVar7 = 1;
	if (y < h - 1) {
		if (x > 0)     bSW = cb(x - 1, y + 1, 3) != 0;     // B-byte SW
		if (g_olmsmoother2_cplane_read_diag_mode == 1) {
			bSE = cb(x, y + 1, 2) != 0;
			if (x < w - 1) uVar7 = (cb(x + 1, y + 1, 1) == 0) ? 1 : 0;
		} else if (g_olmsmoother2_cplane_read_diag_mode == 2) {
			bSE = cb(x, y + 1, 0) != 0;
			if (x < w - 1) uVar7 = (cb(x + 1, y + 1, 1) == 0) ? 1 : 0;
		} else {
			bSE = cb(x, y + 1, 1) != 0;                         // R-byte South (NOT SE)
			if (x < w - 1) uVar7 = (cb(x + 1, y + 1, 2) == 0) ? 1 : 0; // G-byte SE
		}
	}

	int iVar3 = bSW ? 0 : 2;
	int iVar4 = (c_B == 0) ? 4 : 0;
	int iVar11 = (c_R == 0) ? 2 : 0;
	int iVar10 = (c_A == 0) ? 8 : 0;
	int iGbit = (c_G == 0) ? 1 : 0;

	int idx = (iVar3 + eR0 + (((bSE ? 0 : 1) + uVar7 * 2) * 4)) * 0x10 +
	          iVar4 + iGbit + iVar11 + iVar10;
	const bool trace_this_pixel =
	    (x == g_olmsmoother2_trace_x && y == g_olmsmoother2_trace_y);
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace build_polygon x=%d y=%d idx=%d c=%02x%02x%02x%02x eR0=%d bSW=%d bSE=%d uVar7=%d bits=%d,%d,%d,%d,%d\n",
		             x, y, idx, c_A, c_R, c_G, c_B, eR0, bSW ? 1 : 0, bSE ? 1 : 0, uVar7,
		             iVar3, iVar4, iVar11, iVar10, iGbit);
		for (int yy = y - 1; yy <= y + 1; ++yy) {
			for (int xx = x - 1; xx <= x + 1; ++xx) {
				if (xx < 0 || xx >= w || yy < 0 || yy >= h) continue;
				const FPix px = fplane_fetch(plane_in, xx, yy, w, h);
				std::fprintf(stderr,
				             "trace neighborhood sample (%d,%d)=%.8f,%.8f,%.8f,%.8f class=%02x%02x%02x%02x\n",
				             xx, yy, px.r, px.g, px.b, px.a,
				             cb(xx, yy, 0), cb(xx, yy, 1), cb(xx, yy, 2), cb(xx, yy, 3));
			}
		}
	}
	if (g_olmsmoother2_index_hist_enabled && idx >= 0 && idx < 256) {
		++g_olmsmoother2_index_hist[idx];
	}
	if (idx == g_olmsmoother2_skip_index_diag) {
		return;
	}

	// --- 222-case dispatch (literal port of FUN_18000c280 switch body) ---
	float step = STEP; (void)step;
	g_olmsmoother2_current_switch_idx = idx;
	switch (idx) {
	case 0:
		if (g_olmsmoother2_idx0_diag_mode != 1) {
			float idx0_step = STEP;
			if (g_olmsmoother2_idx0_diag_mode == 2) idx0_step *= 0.5f;
			else if (g_olmsmoother2_idx0_diag_mode == 3) idx0_step *= 0.25f;
			else if (g_olmsmoother2_idx0_diag_mode == 4) idx0_step *= 2.0f;
			win_FUN_1800134c0_NW(poly, idx0_step);
			win_FUN_180013570_NE(poly, idx0_step);
			win_FUN_180012ce0_SE(poly, idx0_step);
			win_FUN_180012c20_SW(poly, idx0_step);
		}
		break;
	case 1:
		win_FUN_1800122e0(poly);
		win_FUN_180012ce0_SE(poly, STEP);
		win_FUN_180011d80(poly);
		break;
	case 2: case 0x40: case 0x42: case 0x43: case 0x45: case 0x46: case 0x47:
	case 0x62: case 0x66: case 0xa2: case 0xc2: case 0xc3: case 0xe2:
		// Win: goto caseD_2 (cardinal_9) → falls out of if-block →
		// caseD_4a (cardinal_6) → break.  Two calls, not one.
		win_cardinal_9(poly);
		win_cardinal_6(poly);
		break;
	case 3: case 0x83:
		win_FUN_180011d80(poly);
		win_cardinal_6(poly);
		break;
	case 4:
		win_FUN_1800115a0(poly);
		win_FUN_180012c20_SW(poly, STEP);
		win_FUN_180011030(poly);
		break;
	case 5: case 7: case 0x27: case 0x87: case 0xa7:
		win_FUN_180011d80(poly);
		win_FUN_180011030(poly);
		break;
	case 6: case 0x26:
		win_FUN_180011030(poly);
		win_cardinal_9(poly);
		break;
	case 0x52: case 0x53: case 0x56: case 0x57: case 0x72: case 0x76:
	case 0xa6: case 0xc5: case 0xc6: case 199: case 0xd2: case 0xd3:
	case 0xd6: case 0xd7: case 0xe6: case 0xf2: case 0xf6:
		win_cardinal_9(poly);
		break;
	case 8: case 0x10: case 0x18: case 0x19: case 0x1c:
	case 0x31: case 0x38: case 0x39: case 0x3c:
	case 0x8c: case 0x98: case 0x99: case 0x9c:
		if (idx != 0x18 || g_olmsmoother2_idx18_diag_mode != 1) {
			win_cardinal_3(poly);
		}
		if (idx != 0x18 || g_olmsmoother2_idx18_diag_mode != 2) {
			win_cardinal_12(poly);
		}
		break;
	case 9: case 0x89:
		win_FUN_1800122e0(poly);
		win_cardinal_12(poly);
		break;
	case 0x1a: case 0x1b: case 0x1d: case 0x1e: case 0x1f:
	case 0x35: case 0x3a: case 0x3b: case 0x3d: case 0x3e: case 0x3f:
	case 0x8d: case 0x9a: case 0x9b: case 0x9d: case 0x9e: case 0x9f:
		win_cardinal_12(poly);
		break;
	case 10: case 0x8a:
		// Win FUN_18000c280: local_150 = local_150 * DAT_180022694 (= 0.5f),
		// then falls through to case 0xb.  local_150 is poly.smoothness_n.
		poly.smoothness_n *= 0.5f;
		[[fallthrough]];
	case 0xb: case 0x8b:
		win_FUN_180012f60(poly);
		break;
	case 0xc: {
		bool r = win_FUN_180011300(poly);
		(void)r;
		if (!r) win_cardinal_12(poly);
		win_cardinal_3(poly);
	} break;
	case 0xd: case 0xe: case 0xf: case 0x8e: case 0x8f:
		win_FUN_180011300(poly);
		win_cardinal_12(poly);
		win_FUN_18000cc70_normalize(poly);
		break;
	case 0x11: {
		bool r = win_FUN_180012040(poly);
		if (!r) win_cardinal_12(poly);
		win_cardinal_3(poly);
	} break;
	case 0x12: case 0x32:
		// Win FUN_18000c280: local_150 *= DAT_180022694 (0.5f), then falls
		// through to case 0x16.
		poly.smoothness_n *= 0.5f;
		[[fallthrough]];
	case 0x16: case 0x36:
		win_FUN_180012da0(poly);
		break;
	case 0x13: case 0x15: case 0x17: case 0x33: case 0x37:
		win_FUN_180012040(poly);
		win_cardinal_12(poly);
		win_FUN_18000cc70_normalize(poly);
		break;
	case 0x14: case 0x34:
		win_FUN_1800115a0(poly);
		win_cardinal_12(poly);
		break;
	case 0x20:
		win_FUN_1800115a0(poly);
		win_FUN_180013570_NE(poly, STEP);
		win_FUN_180011030(poly);
		break;
	case 0x21: case 0x29: case 0x2d: case 0xa9: case 0xad:
		win_FUN_1800122e0(poly);
		win_FUN_180011030(poly);
		break;
	case 0x22: {
		bool r = win_FUN_180011300(poly) != 0;
		(void)r;
		if (r) win_cardinal_9(poly); else { win_cardinal_6(poly); win_cardinal_9(poly); }
	} break;
	case 0x23: case 0x2a: case 0x2b: case 0xaa: case 0xab:
		win_FUN_180011300(poly);
		win_cardinal_6(poly);
		win_FUN_18000cc70_normalize(poly);
		break;
	case 0x24:
		win_FUN_1800115a0(poly);
		win_FUN_180011030(poly);
		break;
	case 0x2e: case 0x2f: case 0xae: case 0xaf:
		win_FUN_180011030(poly);
		break;
	case 0x25: case 0x85: case 0xa1: case 0xa4: case 0xa5:
		win_FUN_1800115a0(poly);
		win_FUN_180011030(poly);
		win_FUN_1800122e0(poly);
		win_FUN_180011d80(poly);
		break;
	case 0x81:
		win_FUN_1800122e0(poly);
		win_FUN_180011d80(poly);
		break;
	case 0x28: case 0x2c:
		win_cardinal_3(poly);
		win_FUN_180011030(poly);
		break;
	case 0x30: {
		long r = win_FUN_1800119a0(poly);
		if (r == 0) win_cardinal_3(poly);
		win_cardinal_12(poly);
	} break;
	case 0x41: {
		bool r = win_FUN_1800125c0(poly);
		if (!r) { win_cardinal_6(poly); win_cardinal_9(poly); }
		else    { win_cardinal_9(poly); }
	} break;
	case 0x44: {
		long r = win_FUN_1800119a0(poly);
		if (r == 0) win_cardinal_9(poly);
		win_cardinal_6(poly);
	} break;
	case 0x48: case 0x4c:
		// Win FUN_18000c280: local_150 *= DAT_180022694 (0.5f), then falls
		// through to case 0x68.
		poly.smoothness_n *= 0.5f;
		[[fallthrough]];
	case 0x68: case 0x6c:
		win_FUN_1800132f0(poly);
		break;
	case 0x49: case 0x4d: case 0x61: case 0x69: case 0x6d:
		win_FUN_1800125c0(poly);
		win_cardinal_6(poly);
		win_FUN_18000cc70_normalize(poly);
		break;
	case 0x4a: case 0x4b: case 0x4e: case 0x4f: case 99: case 0x65:
	case 0x67: case 0x6a: case 0x6b: case 0x6e: case 0x6f:
	case 0xa3: case 0xca: case 0xcb: case 0xe3: case 0xea: case 0xeb:
		win_cardinal_6(poly);
		break;
	case 0x50: case 0x51:
		// Win FUN_18000c280: local_150 *= DAT_180022694 (0.5f), then falls
		// through to case 0xd0.
		poly.smoothness_n *= 0.5f;
		[[fallthrough]];
	case 0xd0: case 0xd1:
		win_FUN_180013140(poly);
		break;
	case 0x54: case 0x55: case 0xc4: case 0xd4: case 0xd5:
		win_FUN_1800119a0(poly);
		win_cardinal_9(poly);
		win_FUN_18000cc70_normalize(poly);
		break;
	case 0x58: case 0x59: case 0x5c: case 0x78: case 0x79: case 0x7c:
	case 0xac: case 0xb1: case 0xb8: case 0xb9: case 0xbc:
	case 0xd8: case 0xd9: case 0xdc: case 0xf8: case 0xf9: case 0xfc:
		win_cardinal_3(poly);
		break;
	case 0x60: case 100:
		win_FUN_1800115a0(poly);
		win_cardinal_6(poly);
		break;
	case 0x70: case 0x71: case 0xb0: case 0xf0: case 0xf1:
		win_FUN_1800119a0(poly);
		win_cardinal_3(poly);
		win_FUN_18000cc70_normalize(poly);
		break;
	case 0x74: case 0x75: case 0xf4: case 0xf5:
		win_FUN_1800115a0(poly);
		break;
	case 0x80:
		win_FUN_1800122e0(poly);
		win_FUN_1800134c0_NW(poly, STEP);
		win_FUN_180011d80(poly);
		break;
	case 0x82: {
		bool r = win_FUN_180012040(poly);
		if (!r) win_cardinal_9(poly);
		win_cardinal_6(poly);
	} break;
	case 0x84: case 0x94: case 0x95: case 0xb4: case 0xb5:
		win_FUN_1800115a0(poly);
		win_FUN_180011d80(poly);
		break;
	case 0x86: case 0x92: case 0x96: case 0xb2: case 0xb6:
		win_FUN_180012040(poly);
		win_cardinal_9(poly);
		win_FUN_18000cc70_normalize(poly);
		break;
	case 0x88: {
		bool r = win_FUN_1800125c0(poly);
		if (!r) win_cardinal_3(poly);
		win_cardinal_12(poly);
	} break;
	case 0x90: case 0x91:
		win_cardinal_3(poly);
		win_FUN_180011d80(poly);
		break;
	case 0x93: case 0x97: case 0xb3: case 0xb7:
		win_FUN_180011d80(poly);
		break;
	case 0xa0: case 0xe0: case 0xe1: case 0xe4: case 0xe5:
		win_FUN_1800115a0(poly);
		win_FUN_1800122e0(poly);
		break;
	case 0xc9: case 0xcd: case 0xe9: case 0xed:
		win_FUN_1800122e0(poly);
		break;
	case 0xa8: case 200: case 0xcc: case 0xe8: case 0xec:
		win_FUN_1800125c0(poly);
		win_cardinal_3(poly);
		win_FUN_18000cc70_normalize(poly);
		break;
	case 0xc0: case 0xc1:
		win_cardinal_9(poly);
		win_FUN_1800122e0(poly);
		break;
	default:
		break;
	}
	if (trace_this_pixel) {
		std::fprintf(stderr, "trace build_polygon_done x=%d y=%d idx=%d count=%d\n",
		             x, y, idx, poly.count);
		for (int i = 0; i < poly.count && i < 16; ++i) {
			const PolyVertex &v = poly.samples[i];
			std::fprintf(stderr,
			             "trace sample[%d] rgba=(%.8g,%.8g,%.8g,%.8g) w=%.8g\n",
			             i, v.r, v.g, v.b, v.a, v.w);
		}
	}
	g_olmsmoother2_current_switch_idx = -1;
}

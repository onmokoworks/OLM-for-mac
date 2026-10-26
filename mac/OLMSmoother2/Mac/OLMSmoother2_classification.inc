// ============================================================================
// LITERAL Win cardinal chain — 12時 entry (FUN_1800105f0 → FUN_18000fbf0 → 8 leaves).
// Class plane layout: 4 bytes per pixel [A, R, G, B] (Win u8 RGBA byte order).
// Scanners read byte[0] and byte[1] directly from the plane stride.
// ============================================================================

// Win FUN_180013630 — trapezoid attenuation applied at scan endpoints.
static inline float win_FUN_180013630_trapezoid(float p1, int p2_i, float p3) {
	if (p1 == 0.0f || p3 == 0.0f) return 0.0f;
	float f1 = (float)p2_i;
	if (!(f1 < p1)) return 0.0f;
	float f2 = (1.0f - f1 / p1) * p3;
	if (p1 < f1 + 1.0f) {
		return (p1 - f1) * f2 * 0.5f;
	}
	float fnext = (f1 + 1.0f) / p1;
	return ((1.0f - fnext) * p3 + f2) * 0.5f;
}

// Tiny grid-descriptor adapter: scanners receive {base_ptr, wh_packed, stride}
// exactly as Win's on-stack 3-longlong block.  We mirror the layout.
struct GridDesc {
	const uint8_t *base;          // byte 0..7
	int32_t  w, h;                // byte 8..15 (wh packed)
	int32_t  stride;              // byte 16..19
	int32_t  _pad;                // byte 20..23
};

static inline GridDesc grid_of(const SmootherPolygon &poly) {
	return { poly.cplane_base, poly.cplane_w, poly.cplane_h, poly.cplane_stride, 0 };
}

// FUN_180010550 — classifier. Index = p1 + p3*2 + p2*4.
// The idx=7 target reads p4 (R9B) and p5 (stack arg); scanner call sites set
// both, even though Ghidra's decompiler often recovers only the first 3 args.
// Jumptable targets resolved by capstone (see cardinal_chain.c.txt).
static inline int win_FUN_180010550(int p1, int p2, int p3, int p4 = 0, int p5 = 0) {
	int idx = (p1 & 1) | ((p3 & 1) << 1) | ((p2 & 1) << 2);
	switch (idx) {
		case 0: case 1: return 0;
		case 2: return 1;
		case 3: return 4;
		case 4: return 2;
		case 5: return 3;
		case 6: return 5;
		case 7: {
			switch ((p4 & 1) | ((p5 & 1) << 1)) {
				case 0: return 6;
				case 1: return 7;
				case 2: return 8;
				case 3: return 9;
			}
		}
		default: return 6;
	}
}

// --- scanners — literal ports reading 4-byte [A,R,G,B] plane ---

static inline uint8_t cp_b(const GridDesc *g, int x, int y, int bi) {
	if (x < 0 || x >= g->w || y < 0 || y >= g->h) return 0;
	return g->base[y * g->stride + x * 4 + bi];
}

// Forward declarations for the 6 classifier scanners (defined later, called by leaves above).
static void scan_d0d0(int out[3], const GridDesc *g, const int in[2]);
static void scan_d3b0(int out[3], const GridDesc *g, const int in[2]);
static void scan_d520(int out[3], const GridDesc *g, const int in[2]);
static void scan_d6a0(int out[3], const GridDesc *g, const int in[2]);
static void scan_da50(int out[3], const GridDesc *g, const int in[2]);
static void scan_dbd0(int out[3], const GridDesc *g, const int in[2]);

// Replaces sc_d230 above with a clean form (matches Win FUN_18000d230):
// Scan LEFT on row yp=y+1 while (R@(i,yp)!=0) && (A@(i,yp)==0) && (A@(i,y)==0).
// Win back-up (`uVar7 += 1`) ONLY fires when the while-condition fails (R==0).
// On x<1 break (after dec to 0), Win does NOT back up — class probes read at x=0.
static void scan_d230(int out[3], const GridDesc *g, const int in[2]) {
	int x = in[0]; int y = in[1]; int yp = y + 1;
	if (x < 0 || x >= g->w || yp < 0 || yp >= g->h) {
		out[0] = x; out[1] = yp; out[2] = 0; return;
	}
	int i = x;
	if (x > 0) {
		bool exited_via_R0 = false;
		while (true) {
			if (cp_b(g, i, yp, 1) == 0) { exited_via_R0 = true; break; }
			if (cp_b(g, i, yp, 0) != 0) break;
			if (cp_b(g, i, y,  0) != 0) break;
			i--;
			if (i < 1) break;
		}
		if (exited_via_R0) i++;
	}
	// Win class probes (FUN_18000d230):
	//   p1 (CL_arg): R@(i-1, yp)  byte 1
	//   p2 (DL_arg): A@(i,  y)    byte 0  (uses original y, not yp)
	//   p3 (R8_arg): A@(i,  yp)   byte 0
	bool p1 = (i > 0) && cp_b(g, i - 1, yp, 1) != 0;   // R@(i-1, yp)
	bool p2 = cp_b(g, i, y,  0) != 0;                   // A@(i,  y)
	bool p3 = cp_b(g, i, yp, 0) != 0;                   // A@(i, yp)
	bool p4 = cp_b(g, i, yp, 2) != 0;                   // G@(i, yp)
	bool p5 = (i > 0) && cp_b(g, i - 1, yp, 3) != 0;    // B@(i-1, yp)
	out[0] = i; out[1] = y; out[2] = win_FUN_180010550(p1, p2, p3, p4, p5);
}

// FUN_18000d800 — scan RIGHT on row yp=y+1 while (A@(i,yp)!=0) && (R@(i,yp)==0) && (A@(i,y)==0).
// Sign flipped: Win d800 starts `iVar8 = iVar8 + 1` and walks right.
// While: *pcVar5 !=0 (A@i,yp!=0)... no that contradicts. Re-read:
//   while { if (pcVar5[1]=='\0' || *pcVar5 !=0 || pcVar5[prev_row]!=0) break; ... }
//   i.e. walks while R@(i,yp)!=0 && A@(i,yp)==0 && A@(i,y)==0.  Same as d230 but right-walking.
static void scan_d800(int out[3], const GridDesc *g, const int in[2]) {
	int x = in[0]; int y = in[1]; int yp = y + 1;
	if (x < 0 || x >= g->w || yp < 0 || yp >= g->h) {
		out[0] = x; out[1] = yp; out[2] = 0; return;
	}
	int i = x + 1;
	if (i < g->w - 1) {
		while (cp_b(g, i, yp, 1) != 0) {
			if (cp_b(g, i, yp, 0) != 0) break;
			if (cp_b(g, i, y,  0) != 0) break;
			i++;
			if (i >= g->w - 1) break;
		}
	}
	int j = i - 1;
	// Win class probes (FUN_18000d800):
	//   cVar4 = R@(i, yp)  byte 1 (Win uses >>8 of full 4-byte word)
	//   bVar11 = A@(i, yp) byte 0
	//   bVar10 = A@(i, y)  byte 0  (uses original y, not y-1)
	bool p1 = cp_b(g, i, yp, 1) != 0;   // R@(i, yp)
	bool p2 = cp_b(g, i, yp, 0) != 0;   // A@(i, yp)
	bool p3 = cp_b(g, i, y,  0) != 0;   // A@(i, y)
	bool p4 = cp_b(g, i, yp, 2) != 0;   // G@(i, yp)
	bool p5 = (i > 0) && cp_b(g, i - 1, yp, 3) != 0; // B@(i-1, yp)
	out[0] = j; out[1] = y; out[2] = win_FUN_180010550(p1, p2, p3, p4, p5);
}

// --- emit helpers (Win e3a0 / e290 / e430 / e320) ---
// Each computes trapezoid weight and appends ONE vertex at the appropriate
// perpendicular offset from the run endpoints.

// e3a0 — NORTH emit (y-1 of scan origin row).
// Win:  trap((p2[4]-p2[1]+1)*scale_m*smoothness_n, cur_y-p2[1], scale_h*DAT_180022694)
// where DAT_180022694 = 0.5f (verified from binary).
static bool win_e3a0(SmootherPolygon &poly, const int *p2, float scale_m, float scale_h) {
	float trap_width = (float)(p2[4] - p2[1] + 1) * scale_m * poly.smoothness_n;
	int trap_pos = poly.cur_y - p2[1];
	float trap_edge = scale_h * K_HALF;
	float f = win_FUN_180013630_trapezoid(trap_width, trap_pos, trap_edge);
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace e3a0 p2=(%d,%d,%d,%d,%d,%d) scale_m=%.8g scale_h=%.8g trap=(%.8g,%d,%.8g) weight=%.8g\n",
		             p2[0], p2[1], p2[2], p2[3], p2[4], p2[5],
		             scale_m, scale_h, trap_width, trap_pos, trap_edge, f);
	}
	if (f == 0.0f) return false;
	win_FUN_1800104d0_append(poly, p2[0], p2[1] - 1, f);
	return true;
}

// e290 — SOUTH emit.
static bool win_e290(SmootherPolygon &poly, const int *p2, float scale_m, float scale_h) {
	float f = win_FUN_180013630_trapezoid(
		(float)(p2[4] - p2[1] + 1) * scale_m * poly.smoothness_n,
		p2[4] - poly.cur_y,
		scale_h * K_HALF);
	if (f == 0.0f) return false;
	win_FUN_1800104d0_append(poly, p2[3], p2[4] + 1, f);
	return true;
}

// e430 — WEST emit.
static bool win_e430(SmootherPolygon &poly, const int *p2, float scale_m, float scale_h) {
	float f = win_FUN_180013630_trapezoid(
		(float)(p2[3] - p2[0] + 1) * scale_m * poly.smoothness_n,
		poly.cur_x - p2[0],
		scale_h * K_HALF);
	if (f == 0.0f) return false;
	win_FUN_1800104d0_append(poly, p2[0] - 1, p2[1], f);
	return true;
}

// e320 — EAST emit.
static bool win_e320(SmootherPolygon &poly, const int *p2, float scale_m, float scale_h) {
	float f = win_FUN_180013630_trapezoid(
		(float)(p2[3] - p2[0] + 1) * scale_m * poly.smoothness_n,
		p2[3] - poly.cur_x,
		scale_h * K_HALF);
	if (f == 0.0f) return false;
	win_FUN_1800104d0_append(poly, p2[3] + 1, p2[4], f);
	return true;
}

// --- predicates ---
// FUN_18000e0e0 (12時 / α): predicate at (p2[0], p2[1]).
//   if (p2[1] == 0) return 4;
//   bit2 (×4): A@(x,   y-1)   byte 0  (Win: ((y-1)*stride + x*4 + 0))
//   bit1 (×2): R@(x-1, y)     byte 1  (Win: y*stride + x*4 - 3 = (x-1, y, byte 1))
//   bit0 (×1): R@(x,   y)     byte 1  (Win: y*stride + x*4 + 1)
static int win_e0e0(const SmootherPolygon &poly, const int *p2) {
	if (p2[1] == 0) return 4;
	const uint8_t *base = poly.cplane_base;
	int stride = poly.cplane_stride;
	int y = p2[1];
	int x = p2[0];
	bool above = (x >= 0 && x < poly.cplane_w) && base[(y - 1) * stride + x * 4 + 0] != 0;
	bool left  = (x - 1 >= 0) && base[y * stride + (x - 1) * 4 + 1] != 0;
	bool self  = (x >= 0 && x < poly.cplane_w) && base[y * stride + x * 4 + 1] != 0;
	return (above ? 4 : 0) | (left ? 2 : 0) | (self ? 1 : 0);
}

// FUN_18000dea0 (12時 opposite): predicate at (p2[3]=x', p2[4]=y').
//   Win uses lVar1 = x'*4 + 4 (i.e., addresses keyed off x'+1).
//   bit2 (×4): A@(x'+1, y'-1) byte 0  (Win: (y'-1)*stride + (x'+1)*4 + 0)
//   bit0 (×1): R@(x',   y')   byte 1  (Win: y'*stride + x'*4 + 1)
//   bit1 (×2): R@(x'+1, y')   byte 1  (Win: y'*stride + (x'+1)*4 + 1)
static int win_dea0(const SmootherPolygon &poly, const int *p2) {
	int y = p2[4]; int x = p2[3];
	if (y == 0) return 4;
	const uint8_t *base = poly.cplane_base;
	int stride = poly.cplane_stride;
	bool above = (x + 1 >= 0 && x + 1 < poly.cplane_w) && base[(y - 1) * stride + (x + 1) * 4 + 0] != 0;
	bool self  = (x >= 0 && x < poly.cplane_w) && base[y * stride + x * 4 + 1] != 0;
	bool right = (x + 1 < poly.cplane_w) && base[y * stride + (x + 1) * 4 + 1] != 0;
	return (above ? 4 : 0) | (right ? 2 : 0) | (self ? 1 : 0);
}

// --- 8 leaves for the 12時 dispatcher (FUN_18000fbf0) ---
// Constants used in leaf bodies.
// DAT_180022dd8 (extra_smooth multiplier) = 0.2f in Win binary (verified 2026-04-27).
// Note: name preserves the suffix of the original symbol ("dd8" — NOT 0.25 ddc).
static constexpr float K_DD8 = 0.2f;

// FUN_18000f4a0 — predicate=e0e0; if class==4, no-op; else e430(extra*0.5+0.5, 1.0).
// Win:  e430(p, p2, extra * DAT_180022694 + DAT_180022694, DAT_1800226a0)
//     = e430(p, p2, extra * 0.5 + 0.5, 1.0).
static bool win_leaf_f4a0(SmootherPolygon &poly, const int *p2) {
	int c = win_e0e0(poly, p2);
	if (c == 4) return false;
	return win_e430(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}

// FUN_18000ec40 — pred=e0e0; valid c ∈ {1,3,7} (Win: (c-1)&~6 == 0 && c != 5).
// First scan = dbd0 (right-walk on row y from p2[0..1]) → run-end x.
// Chase scan (when c ∈ {3,7}) = d230 walking up-left from (x-1, y).
// Win wscale init = DAT_1800226a0 (1.0); per-iter while-cond sets it to fVar3 (0.5)
// before bounds check, then 1.0 after scan when class==1 (else 0.5).
static bool win_leaf_ec40(SmootherPolygon &poly, const int *p2) {
	int c = win_e0e0(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3];
	scan_dbd0(s, &g, p2);          // Win first scan: FUN_18000dbd0
	int span_end = s[0];
	int total = p2[3] - p2[0] + 1;
	int cur_span = span_end - p2[0];
	float fmul   = poly.extra_n * K_DD8 + K_HALF;
	float wscale_h = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[0];
		int y = p2[1];
		while (true) {
			int px = x - 1;
			int py = y;
			// Win sets fVar11 = fVar3 (=K_HALF) inside the while-condition,
			// so bounds-fail leaves wscale_h at K_HALF.
			wscale_h = K_HALF;
			if (px < 0 || px >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3];
			int in2[2] = { px, py };
			scan_d230(s2, &g, in2);
			wscale_h = K_ONE;
			if (s2[2] == 1) break;
			wscale_h = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 4) break;
		}
	}
	float span_len = (float)(cur_span + 1) * fmul / (float)total;
	return win_e430(poly, p2, span_len, wscale_h);
}

// FUN_18000f7b0 — pred=e0e0, class-dependent scale, e430.
// Win disasm 0x18000f7b0: c=2→scale=1.0, c=3→0.5, c=6→1.0, c=7→0.5; c∈{0,1,4,5}→no emit.
static bool win_leaf_f7b0(SmootherPolygon &poly, const int *p2) {
	int c = win_e0e0(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e430(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}

// FUN_18000f360 — pred=dea0; class!=4 → e320(extra*0.5+0.5, 1.0).
static bool win_leaf_f360(SmootherPolygon &poly, const int *p2) {
	int c = win_dea0(poly, p2);
	if (c == 4) return false;
	return win_e320(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}

// FUN_18000f220 — pred=e0e0; class!=4 → e430(extra*K_DD8+0.5, p3).
static bool win_leaf_f220(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_e0e0(poly, p2);
	if (c == 4) return false;
	return win_e430(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}

// FUN_18000f0e0 — pred=dea0; class!=4 → e320(extra*K_DD8+0.5, p3).
static bool win_leaf_f0e0(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_dea0(poly, p2);
	if (c == 4) return false;
	return win_e320(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}

// FUN_18000f600 — pred=dea0; class-dependent scale, e320.
// Win disasm 0x18000f600: c∈{2,6}→1.0, c∈{3,7}→0.5, c∈{0,1,4,5}→no emit.
static bool win_leaf_f600(SmootherPolygon &poly, const int *p2) {
	int c = win_dea0(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e320(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}

// FUN_18000e640 — pred=dea0; valid c ∈ {1,3,7}.
// First scan = d520 (left-walk on row p2[4] from p2[3..4]) → walked-x.
// Chase scan (when c ∈ {3,7}) = d800 walking right-down from (x+1, y).
static bool win_leaf_e640(SmootherPolygon &poly, const int *p2) {
	int c = win_dea0(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3];
	int in0[2] = { p2[3], p2[4] };
	scan_d520(s, &g, in0);          // Win first scan: FUN_18000d520(p2+3)
	int span_end = s[0];
	int cur_span = p2[3] - span_end;
	int total = p2[3] - p2[0] + 1;
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wscale_h = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[3]; int y = p2[4];
		while (true) {
			int px = x + 1;
			int py = y;
			wscale_h = K_HALF;
			if (px < 0 || px >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3];
			int in3[2] = { px, py };
			scan_d800(s2, &g, in3);
			wscale_h = K_ONE;
			if (s2[2] == 2) break;
			wscale_h = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 3) break;
		}
	}
	float span_len = (float)(cur_span + 1) * fmul / (float)total;
	return win_e320(poly, p2, span_len, wscale_h);
}

// FUN_18000fbf0 — 12時 emitter dispatcher.  Switch key = p2[2] + (p2[5]*5 - 1) * 2.
static void win_disp_fbf0(SmootherPolygon &poly, int *p2) {
	int k = p2[2] + (p2[5] * 5 - 1) * 2;
	bool after = false; (void)after;
	switch (k) {
		case 0: case 6: case 0x14: case 0x1a: case 0x1e: case 0x24: case 0x50: case 0x56:
			win_leaf_f4a0(poly, p2); return;
		case 1: case 7: case 0x1b: case 0x1f: case 0x25: case 0x33: case 0x39: case 0x57:
			win_leaf_ec40(poly, p2); return;
		case 4: case 0x18: case 0x22: case 0x36: case 0x54:
			win_leaf_f7b0(poly, p2); return;
		case 8: case 9: case 0xc: case 0xf: case 0x44: case 0x45: case 0x48: case 0x4b:
			win_leaf_f360(poly, p2); return;
		case 10: case 0x10: case 0x46: case 0x4c: {
			if (win_leaf_f220(poly, p2, K_ONE)) {
				// Boost: f3c = (f3c+f3c)^2 * DAT_180022694 (=0.5f).
				if (poly.count > 0) {
					float &wref = poly.samples[poly.count - 1].w;
					float v = wref + wref;
					wref = v * v * K_HALF;
				}
			}
			if (win_leaf_f0e0(poly, p2, K_ONE)) {
				if (poly.count > 0) {
					float &wref = poly.samples[poly.count - 1].w;
					float v = wref + wref;
					wref = v * v * K_HALF;
				}
			}
			return;
		}
		case 0xb: case 0x47:
			win_leaf_ec40(poly, p2);
			win_leaf_f0e0(poly, p2, K_ONE);
			return;
		case 0xd: case 0x49:
			win_leaf_f0e0(poly, p2, K_ONE);
			return;
		case 0xe: case 0x4a:
			win_leaf_f7b0(poly, p2);
			win_leaf_f0e0(poly, p2, K_ONE);
			return;
		case 0x11: case 0x4d:
			win_leaf_ec40(poly, p2);
			win_leaf_f360(poly, p2);
			return;
		case 0x26: case 0x2a: case 0x2b: case 0x58: case 0x59:
		case 0x5c: case 0x5d: case 0x5f:
			win_leaf_e640(poly, p2);  // fallthrough end
			return;
		case 0x28: case 0x2e:
			win_leaf_f220(poly, p2, K_ONE);
			win_leaf_e640(poly, p2);
			return;
		case 0x29: case 0x2f: case 0x5b: case 0x61:
			win_leaf_ec40(poly, p2);
			win_leaf_e640(poly, p2);
			return;
		case 0x2c: case 0x5e:
			win_leaf_f7b0(poly, p2);
			win_leaf_e640(poly, p2);
			return;
		case 0x32: case 0x38:
			win_leaf_f220(poly, p2, K_ONE);
			return;
		case 0x3c: case 0x42:
			win_leaf_f220(poly, p2, K_ONE);
			win_leaf_f600(poly, p2);
			return;
		case 0x3a: case 0x3b: case 0x3e: case 0x3f: case 0x41:
			win_leaf_f600(poly, p2);
			return;
		case 0x3d: case 0x43:
			win_leaf_ec40(poly, p2);
			win_leaf_f600(poly, p2);
			return;
		case 0x40:
			win_leaf_f7b0(poly, p2);
			win_leaf_f600(poly, p2);
			return;
		case 0x5a: case 0x60:
			win_leaf_f4a0(poly, p2);
			win_leaf_e640(poly, p2);
			return;
		default: return;
	}
}

// FUN_1800105f0 — 12時 cardinal entry.  Sets up scan descriptor + dispatches.
static void win_cardinal_12(SmootherPolygon &poly) {
	// Guard: cur_y != bound_y - 1 (not at bottom row).
	if (poly.cur_y == poly.cplane_h - 1) return;
	GridDesc g1 = grid_of(poly);
	GridDesc g2 = grid_of(poly);
	int center[2] = { poly.cur_x, poly.cur_y };
	int sL[3]; scan_d230(sL, &g1, center);
	int sR[3]; scan_d800(sR, &g2, center);
	// Descriptor layout: { xL, yL, clsL, xR, yR, clsR }
	int desc[6] = { sL[0], sL[1], sL[2], sR[0], sR[1], sR[2] };
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		int k = desc[2] + (desc[5] * 5 - 1) * 2;
		std::fprintf(stderr,
		             "trace cardinal12 desc=(%d,%d,%d,%d,%d,%d) key=%d\n",
		             desc[0], desc[1], desc[2], desc[3], desc[4], desc[5], k);
	}
	if (g_olmsmoother2_idx18_key_hist_enabled && g_olmsmoother2_current_switch_idx == 0x18) {
		int k = desc[2] + (desc[5] * 5 - 1) * 2;
		if (k >= 0 && k < 128) ++g_olmsmoother2_idx18_cardinal12_key_hist[k];
	}
	win_disp_fbf0(poly, desc);
}


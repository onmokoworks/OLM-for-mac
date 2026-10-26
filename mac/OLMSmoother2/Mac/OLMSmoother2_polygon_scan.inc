// ============================================================================
// Task #17 — 222-case dispatcher (FUN_18000c280) + 12 mid-helpers + 3 missing
// cardinals.  The 12 mid-helpers fire conditional edge/corner emits based on
// run-length classification of the 8-neighborhood.  The sibling cardinal
// entries (3時/6時/9時) now have their own dispatcher families instead of
// forwarding through the 12時 dispatcher.  The remaining no-key residual is
// therefore tracked as scanner/leaf fidelity around hot dispatch keys, not as
// a missing cardinal-family placeholder.
// ============================================================================

// Win DAT aliases local to this port block.  Using distinct names to avoid
// collision with the K_HALF macro and the earlier W_IN_W = 1.0f constant.
static constexpr float W_STEP  = 0.125f; // DAT_180022dd4
static constexpr float W_OUT_W = 0.4f;   // DAT_180022de8
static constexpr float W_IN_W  = 0.2f;   // DAT_180022dd8

// Read the 4-byte pixel [A,R,G,B] at (x, y) in the class plane.  Returns 0
// outside bounds.  Matches Win scanner reads of param_2[3].
static inline uint32_t cpl_read32(const GridDesc *g, int x, int y) {
	if (!g->base || x < 0 || x >= g->w || y < 0 || y >= g->h) return 0;
	const uint8_t *p = g->base + (size_t)y * g->stride + (size_t)x * 4;
	return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
	       ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

// --- 6 secondary scanners — LITERAL diagonal walkers, 1:1 ports of Win
//     FUN_180010{8d0,9d0,ad0,bd0,d20,e40}.  Each writes (end_x, end_y) to out[].
//     Direction summary (verified vs Ghidra decompilation):
//       108d0: down-left  (dx=-1, dy=+1).  Initial probe: byte0 at (x,   y+1).
//       109d0: down-right (dx=+1, dy=+1).  Initial probe: byte0 at (x+1, y+1).
//       10ad0: down-right (dx=+1, dy=+1).  Initial probe: byte0 at (x+1, y  ).
//       10bd0: up-left    (dx=-1, dy=-1).  Initial probes: byte2 at (x, y+1)==0 && (x, y)==0.
//       10d20: up-left    (dx=-1, dy=-1).  Initial probes: byte2 at (x, y  )==0 && (x, y-1)==0.
//       10e40: up-right   (dx=+1, dy=-1).  Initial probes: byte3 at (x, y+1)==0 && (x, y  )==0.
//     Per-iteration probes are byte 1 (R) and byte 3 (or byte 2 in -d0 / -bd0 / -d20 variants),
//     plus a side-probe one row "back" along the dy axis. See Win decomp for exact bytes.

// FUN_1800108d0 — down-left diagonal walk.
static void scan_108d0(int out[2], const GridDesc *g, const int in[2]) {
	int x = in[0], y = in[1];
	int y1 = y + 1;
	if (y1 < g->h) {
		int lim = (g->h - y1) - 1;
		int steps = (lim < x) ? lim : x;
		if (steps != 0) {
			if (cp_b(g, x, y1, 0) != 0) {
				int cx = x, cy = y1;
				int hits = 0;
				for (int i = 0; i < steps; ++i) {
					int nx = cx - 1;
					int ny = cy + 1;
					// byte1 at (nx, ny) != 0, byte3 at (nx, ny) == 0,
					// byte3 at (nx, ny-1) (row-back, same col) == 0.
					if (cp_b(g, nx, ny, 1) == 0) break;
					if (cp_b(g, nx, ny, 3) != 0) break;
					if (cp_b(g, nx, ny - 1, 3) != 0) break;
					cx = nx;
					cy = ny;
					if (cp_b(g, nx, ny, 0) == 0) break;
					if (++hits >= steps) break;
				}
				out[0] = cx;
				out[1] = cy - 1;
				return;
			}
		}
	}
	out[0] = x;
	out[1] = y;
}

// FUN_1800109d0 — down-right diagonal walk.
static void scan_109d0(int out[2], const GridDesc *g, const int in[2]) {
	int x = in[0], y = in[1];
	int y1 = y + 1;
	if (y1 < g->h) {
		int lim_h = g->h - y1;
		int lim_w = g->w - x;        // (int)param_2[1] - uVar9
		// Win first selects min(height-y-1, width-x), then iterates
		// `selected - 1` times.  Subtracting one before the min as well
		// shortens long down-right runs by one cell (notably checker/diagonal
		// geometry at the top edge).
		int steps = (lim_h <= lim_w - 1) ? lim_h : lim_w;
		if (steps != 1) {
			if (cp_b(g, x + 1, y1, 0) != 0) {
				int cx = x, cy = y1;
				int hits = 0;
				int budget = steps - 1;
				for (int i = 0; i < budget; ++i) {
					int nx = cx + 1;
					int ny = cy + 1;
					// byte1 at (nx, ny) != 0, byte2 at (nx, ny) == 0,
					// byte2 at (nx, ny-1) == 0.
					if (cp_b(g, nx, ny, 1) == 0) break;
					if (cp_b(g, nx, ny, 2) != 0) break;
					if (cp_b(g, nx, ny - 1, 2) != 0) break;
					cx = nx;
					cy = ny;
					// look-ahead: byte0 at (nx+1, ny).
					if (cp_b(g, nx + 1, ny, 0) == 0) break;
					if (++hits >= budget) break;
				}
				out[0] = cx;
				out[1] = cy - 1;
				return;
			}
		}
	}
	out[0] = x;
	out[1] = y;
}

// FUN_180010ad0 — down-right diagonal walk (no leading y+1<h gate).
static void scan_10ad0(int out[2], const GridDesc *g, const int in[2]) {
	int x = in[0], y = in[1];
	int lim_w = g->w - x;            // (int)param_2[1] - uVar8
	int lim_h = g->h - y;            // h - uVar11
	// Same selected-limit shape as FUN_1800109d0: choose height when it is
	// <= width-1, otherwise retain width, and subtract one only in the loop.
	int steps = (lim_h <= lim_w - 1) ? lim_h : lim_w;
	if (steps != 1) {
		if (cp_b(g, x + 1, y, 0) != 0) {
			int cx = x, cy = y;
			int hits = 0;
			int budget = steps - 1;
			for (int i = 0; i < budget; ++i) {
				int nx = cx + 1;
				int ny = cy + 1;
				if (cp_b(g, nx, ny, 1) == 0) break;
				if (cp_b(g, nx, ny, 2) != 0) break;
				if (cp_b(g, nx, ny - 1, 2) != 0) break;
				cx = nx;
				cy = ny;
				if (cp_b(g, nx + 1, ny, 0) == 0) break;
				if (++hits >= budget) break;
			}
			out[0] = cx;
			out[1] = cy;
			return;
		}
	}
	out[0] = x;
	out[1] = y;
}

// FUN_180010bd0 — step-shape walk: outer probes at (x, y+1) and (x, y);
// per-iter probes at (cx-1, cy) where cy steps y, y-1, y-2... (cx=x, x-1, x-2...).
// Net direction: up-left.  Side-look uses the previous probe row (cy-1).
static void scan_10bd0(int out[2], const GridDesc *g, const int in[2]) {
	int x = in[0], y = in[1];
	int y1 = y + 1;
	if (y1 < g->h) {
		int steps = (y1 < x) ? y1 : x;
		if (steps != 0) {
			// Both probes must be 0: byte2 at (x, y+1) and byte2 at (x, y).
			if (cp_b(g, x, y1, 2) == 0 && cp_b(g, x, y, 2) == 0) {
				int cx = x;
				int probe_y = y;        // = "uVar8" snapshot at iter top
				int hits = 0;
				for (int i = 0; i < steps; ++i) {
					int nx = cx - 1;
					// Top-break: byte1 at (nx, probe_y) ==0 OR byte0 at (cx, probe_y) ==0
					if (cp_b(g, nx, probe_y, 1) == 0 || cp_b(g, cx, probe_y, 0) == 0) {
						// recovery: uVar8 += 1 → probe_y+1; uVar9 = uVar11 = pre_x = cx
						out[0] = cx;
						out[1] = (probe_y + 1) - 1;  // = probe_y
						return;
					}
					// byte2 at (nx, probe_y) != 0 → goto: uVar9=nx, uVar8-1=probe_y-1
					if (cp_b(g, nx, probe_y, 2) != 0) {
						out[0] = nx;
						out[1] = probe_y - 1;
						return;
					}
					// next probe row = probe_y - 1; bounds-checked byte2 read.
					int side_y = probe_y - 1;
					if (cp_b(g, nx, side_y, 2) != 0) {
						out[0] = nx;
						out[1] = probe_y - 1;
						return;
					}
					// Successful iter: advance.
					cx = nx;
					probe_y = side_y;     // mirrors uVar12 = uVar8 - 1
					if (++hits >= steps) {
						// Loop condition fails before re-entering; uVar8 retains
						// previous iter-top value, but we just assigned probe_y
						// to side_y in our model.  Win's uVar8-1 = (previous probe_y)-1
						// = (current probe_y+1)-1 = current probe_y.
						out[0] = cx;
						out[1] = probe_y;
						return;
					}
				}
				// Unreachable: loop exits via one of the returns above.
				out[0] = cx;
				out[1] = probe_y;
				return;
			}
		}
	}
	out[0] = x;
	out[1] = y;
}

// FUN_180010d20 — pure diagonal up-left walk (cx, cy) → (cx-1, cy-1).
// Outer probes: byte2 at (x, y) and (x, y-1) both ==0.
static void scan_10d20(int out[2], const GridDesc *g, const int in[2]) {
	int x = in[0], y = in[1];
	int steps = (y < x) ? y : x;
	if (steps != 0) {
		if (cp_b(g, x, y, 2) == 0 && cp_b(g, x, y - 1, 2) == 0) {
			int cx = x;
			int probe_y = y - 1;        // uVar5 init before loop = y-1
			int pre_x = x;               // uVar10 init = x
			int hits = 0;
			for (int i = 0; i < steps; ++i) {
				int row = probe_y;       // uVar11 = uVar5
				int col_pre = pre_x;     // uVar5 = uVar10  (saved pre_x)
				int nx = col_pre - 1;    // uVar9 = uVar5 - 1
				pre_x = nx;              // uVar10 = nx
				// Top-break: byte1 at (nx, row) ==0 OR byte0 at (col_pre, row) ==0
				if (cp_b(g, nx, row, 1) == 0 || cp_b(g, col_pre, row, 0) == 0) {
					// recovery: uVar11 += 1; uVar9 = uVar5 = col_pre
					out[0] = col_pre;
					out[1] = row + 1;
					return;
				}
				// byte2 at (nx, row) != 0 → out=(nx, row)
				if (cp_b(g, nx, row, 2) != 0) {
					out[0] = nx;
					out[1] = row;
					return;
				}
				int side_y = row - 1;       // uVar5 = uVar11 - 1
				// byte2 at (nx, side_y) (bounds-zero) != 0 OR limit → out=(nx, row)
				if (cp_b(g, nx, side_y, 2) != 0) {
					out[0] = nx;
					out[1] = row;
					return;
				}
				if (++hits >= steps) {
					out[0] = nx;
					out[1] = row;
					return;
				}
				cx = nx;
				probe_y = side_y;
			}
			// Loop body never executed (steps <= 0).  Win leaves uVar11/uVar9 at
			// initial (y, x) since the inner-condition's third clause `0 < uVar7`
			// short-circuits AND skips both the while and the recovery.
			out[0] = x;
			out[1] = y;
			return;
		}
	}
	out[0] = x;
	out[1] = y;
}

// FUN_180010e40 — step-shape walk: outer probes at (x, y+1), (x, y);
// per-iter probes at (cx+1, probe_y) where probe_y steps y, y-1, y-2... (cx=x, x+1, x+2...).
// Net direction: up-right.  Side-look at (probe col, probe_y - 1).
static void scan_10e40(int out[2], const GridDesc *g, const int in[2]) {
	int x = in[0], y = in[1];
	int y1 = y + 1;
	if (y1 < g->h) {
		int lim_w = (g->w - x) - 1;        // (cols - x) - 1
		int steps = (y1 < lim_w) ? y1 : lim_w;
		if (steps != 0) {
			// Both probes must be 0: byte3 at (x, y+1) and (x, y).
			if (cp_b(g, x, y1, 3) == 0 && cp_b(g, x, y, 3) == 0) {
				int cx = x;
				int probe_y = y;       // iVar7 snapshot
				int hits = 0;
				for (int i = 0; i < steps; ++i) {
					int nx = cx + 1;
					// Break: byte0 at (nx, probe_y) ==0 OR byte1 at (nx, probe_y) ==0
					if (cp_b(g, nx, probe_y, 0) == 0 || cp_b(g, nx, probe_y, 1) == 0) {
						// recovery: iVar7 += 1; uVar10 = uVar9 = cx
						out[0] = cx;
						out[1] = (probe_y + 1) - 1;  // = probe_y
						return;
					}
					// byte3 at (nx, probe_y) !=0 OR byte3 at (nx, probe_y-1) !=0 OR limit
					// → goto LAB_180010f12: out=(nx, probe_y - 1)
					if (cp_b(g, nx, probe_y, 3) != 0) {
						out[0] = nx;
						out[1] = probe_y - 1;
						return;
					}
					int side_y = probe_y - 1;
					if (cp_b(g, nx, side_y, 3) != 0) {
						out[0] = nx;
						out[1] = probe_y - 1;
						return;
					}
					if (++hits >= steps) {
						out[0] = nx;
						out[1] = probe_y - 1;
						return;
					}
					cx = nx;
					probe_y = side_y;
				}
				// No iterations executed (steps <= 0).  Win returns iVar7-1 = y+1-1 = y.
				out[0] = cx;
				out[1] = probe_y;
				return;
			}
		}
	}
	out[0] = x;
	out[1] = y;
}

// --- 7 classifier scanners — literal ports of Win FUN_18000{d0d0,d3b0,d520,d6a0,da50,dbd0}.
// Each returns { x_end, y_end, class_mask } from FUN_180010550(p1, p2, p3) on the stop pixels.

// FUN_18000d0d0 — walk UP col x while A@(x,iy)!=0 && R@(x,iy)==0 && R@(x-1,iy)==0.  Returns (x, walked_y).
// Win back-up (`INC R10D`) ONLY fires when the while-condition fails (A==0).
// On y<1 break (after dec to 0), Win does NOT back up — class probes read at y=0.
static void scan_d0d0(int out[3], const GridDesc *g, const int in[2]) {
	int x = in[0], y0 = in[1];
	if (x < 0 || x >= g->w || y0 < 0 || y0 >= g->h) {
		out[0] = x; out[1] = y0; out[2] = 0; return;
	}
	int y = y0;
	if (y0 > 0) {
		bool exited_via_A0 = false;
		while (true) {
			if (cp_b(g, x, y, 0) == 0) { exited_via_A0 = true; break; }  // A==0
			if (cp_b(g, x, y, 1) != 0) break;            // R@(x,y)!=0 → stop
			if (x > 0 && cp_b(g, x - 1, y, 1) != 0) break; // R@(x-1,y)!=0 → stop
			y--;
			if (y < 1) break;
		}
		if (exited_via_A0) y++;
	}
	bool p1 = (y > 0) && cp_b(g, x,     y - 1, 0) != 0;  // A@(x,   y-1)
	bool p2 = cp_b(g, x,     y, 1) != 0;                  // R@(x,   y)
	bool p3 = (x > 0) && cp_b(g, x - 1, y, 1) != 0;       // R@(x-1, y)
	bool p4 = (x > 0) && cp_b(g, x - 1, y, 3) != 0;      // B@(x-1, y)
	bool p5 = cp_b(g, x,     y, 2) != 0;                  // G@(x,   y)
	out[0] = x; out[1] = y; out[2] = win_FUN_180010550(p1, p2, p3, p4, p5);
}

// FUN_18000d3b0 — walk UP col x+1 while A@(x+1,iy)!=0 && R@(x+1,iy)==0 && R@(x,iy)==0.
// Returns (x_unchanged, walked_y).  Class probes at (x+1, walked_y-1)A, (x+1, walked_y)R, (x, walked_y)R.
static void scan_d3b0(int out[3], const GridDesc *g, const int in[2]) {
	int x = in[0], y0 = in[1];
	int xp1 = x + 1;
	if (xp1 < 0 || xp1 >= g->w || y0 < 0 || y0 >= g->h) {
		out[0] = xp1; out[1] = y0; out[2] = 0; return;
	}
	int y = y0;
	if (y0 > 0) {
		bool exited_via_A0 = false;
		while (true) {
			if (cp_b(g, xp1, y, 0) == 0) { exited_via_A0 = true; break; }
			if (cp_b(g, xp1, y, 1) != 0) break;
			if (cp_b(g, x,   y, 1) != 0) break;
			y--;
			if (y < 1) break;
		}
		if (exited_via_A0) y++;
	}
	bool p1 = (y > 0) && cp_b(g, xp1, y - 1, 0) != 0;
	bool p2 = cp_b(g, xp1, y, 1) != 0;
	bool p3 = cp_b(g, x,   y, 1) != 0;
	bool p4 = cp_b(g, x,   y, 3) != 0;
	bool p5 = cp_b(g, xp1, y, 2) != 0;
	out[0] = x; out[1] = y; out[2] = win_FUN_180010550(p1, p2, p3, p4, p5);
}

// FUN_18000d520 — walk LEFT row y while R@(ix,y)!=0 && A@(ix,y)==0 && A@(ix,y-1)==0.
// Returns (walked_x, y).  Class: (R@(x-1,y), A@(x,y-1), A@(x,y)).
static void scan_d520(int out[3], const GridDesc *g, const int in[2]) {
	int x0 = in[0], y = in[1];
	if (x0 < 0 || x0 >= g->w || y < 0 || y >= g->h) {
		out[0] = x0; out[1] = y; out[2] = 0; return;
	}
	int x = x0;
	if (x0 > 0) {
		bool exited_via_R0 = false;
		while (true) {
			if (cp_b(g, x, y, 1) == 0) { exited_via_R0 = true; break; }  // R@(x,y)==0
			if (cp_b(g, x, y, 0) != 0) break;             // A@(x,y)!=0
			if (y > 0 && cp_b(g, x, y - 1, 0) != 0) break;// A@(x,y-1)!=0
			x--;
			if (x < 1) break;
		}
		if (exited_via_R0) x++;
	}
	bool p1 = (x > 0) && cp_b(g, x - 1, y,     1) != 0;
	bool p2 = (y > 0) && cp_b(g, x,     y - 1, 0) != 0;
	bool p3 = cp_b(g, x, y, 0) != 0;
	bool p4 = cp_b(g, x, y, 2) != 0;
	bool p5 = (x > 0) && cp_b(g, x - 1, y, 3) != 0;
	out[0] = x; out[1] = y; out[2] = win_FUN_180010550(p1, p2, p3, p4, p5);
}

// FUN_18000d6a0 — walk DOWN col x starting at y+1 while A@(x,iy)!=0 && R@(x,iy)==0 && R@(x-1,iy)==0.
// iVar7 is incremented past the run; iVar8 = iVar7 - 1 = last walked.
// Class probes at iVar7 (one past end): (A@(x,iVar7), R@(x-1,iVar7), R@(x,iVar7)).
// Returns (x, iVar8 = walked_y - 1).
static void scan_d6a0(int out[3], const GridDesc *g, const int in[2]) {
	int x = in[0], y0 = in[1];
	if (x < 0 || x >= g->w || y0 < 0 || y0 >= g->h) {
		out[0] = x; out[1] = y0; out[2] = 0; return;
	}
	int y = y0 + 1;
	int hMax = g->h - 1;
	while (y < hMax) {
		if (cp_b(g, x, y, 0) == 0) break;             // A==0
		if (cp_b(g, x, y, 1) != 0) break;             // R!=0
		if (x > 0 && cp_b(g, x - 1, y, 1) != 0) break;// R@(x-1)!=0
		y++;
	}
	int iVar8 = y - 1;
	int cls = 0;
	if (iVar8 < hMax) {
		bool p1 = cp_b(g, x, y, 0) != 0;                  // A@(x, y)
		bool p2 = (x > 0) && cp_b(g, x - 1, y, 1) != 0;   // R@(x-1, y)
		bool p3 = cp_b(g, x, y, 1) != 0;                  // R@(x, y)
		bool p4 = (x > 0) && cp_b(g, x - 1, y, 3) != 0;   // B@(x-1, y)
		bool p5 = cp_b(g, x, y, 2) != 0;                  // G@(x, y)
		cls = win_FUN_180010550(p1, p2, p3, p4, p5);
	}
	out[0] = x; out[1] = iVar8; out[2] = cls;
}

// FUN_18000da50 — walk DOWN col x+1 starting at y+1.  Same break-conditions but at col x+1.
// Class: (A@(x+1, iVar9), R@(x, iVar9), R@(x+1, iVar9)).
// Returns (x, iVar10 = iVar9 - 1).
static void scan_da50(int out[3], const GridDesc *g, const int in[2]) {
	int x = in[0], y0 = in[1];
	int xp1 = x + 1;
	if (xp1 < 0 || xp1 >= g->w || y0 < 0 || y0 >= g->h) {
		out[0] = xp1; out[1] = y0; out[2] = 0; return;
	}
	int y = y0 + 1;
	int hMax = g->h - 1;
	while (y < hMax) {
		if (cp_b(g, xp1, y, 0) == 0) break;
		if (cp_b(g, xp1, y, 1) != 0) break;
		if (cp_b(g, x,   y, 1) != 0) break;
		y++;
	}
	int iVar10 = y - 1;
	int cls = 0;
	if (iVar10 < hMax) {
		bool p1 = cp_b(g, xp1, y, 0) != 0;
		bool p2 = cp_b(g, x,   y, 1) != 0;
		bool p3 = cp_b(g, xp1, y, 1) != 0;
		bool p4 = cp_b(g, x,   y, 3) != 0;
		bool p5 = cp_b(g, xp1, y, 2) != 0;
		cls = win_FUN_180010550(p1, p2, p3, p4, p5);
	}
	out[0] = x; out[1] = iVar10; out[2] = cls;
}

// FUN_18000dbd0 — walk RIGHT row y starting at x+1 while R@(ix,y)!=0 && A@(ix,y)==0 && A@(ix,y-1)==0.
// iVar8 is incremented past the run; iVar9 = iVar8 - 1.
// Class probes at iVar8 (one past end): (R@(iVar8, y), A@(iVar8, y), A@(iVar8, y-1)).
// Returns (iVar9 = walked_x - 1, y).
static void scan_dbd0(int out[3], const GridDesc *g, const int in[2]) {
	int x0 = in[0], y = in[1];
	if (x0 < 0 || x0 >= g->w || y < 0 || y >= g->h) {
		out[0] = x0; out[1] = y; out[2] = 0; return;
	}
	int x = x0 + 1;
	int wMax = g->w - 1;
	while (x < wMax) {
		if (cp_b(g, x, y, 1) == 0) break;                 // R==0 → stop
		if (cp_b(g, x, y, 0) != 0) break;                 // A!=0 → stop
		if (y > 0 && cp_b(g, x, y - 1, 0) != 0) break;    // A@(x,y-1)!=0
		x++;
	}
	int iVar9 = x - 1;
	int cls = 0;
	if (iVar9 < wMax) {
		bool p1 = cp_b(g, x, y, 1) != 0;                  // R@(x, y)
		bool p2 = cp_b(g, x, y, 0) != 0;                  // A@(x, y)
		bool p3 = (y > 0) && cp_b(g, x, y - 1, 0) != 0;   // A@(x, y-1)
		bool p4 = cp_b(g, x, y, 2) != 0;                  // G@(x, y)
		bool p5 = (x > 0) && cp_b(g, x - 1, y, 3) != 0;   // B@(x-1, y)
		cls = win_FUN_180010550(p1, p2, p3, p4, p5);
	}
	out[0] = iVar9; out[1] = y; out[2] = cls;
}


// ---------------------------------------------------------------------------
// LITERAL PORTS of FUN_180013700 / FUN_180013bc0 / FUN_180012850.
// These compute anti-aliased coverage of a line / trapezoid against scanline
// band [scan_y+0.5 .. scan_y+1.5] (two halves) and feed two coverage floats
// into out[0..1].  out[1] later becomes vertex.w (+0x50 slot in Win).
// ---------------------------------------------------------------------------

// Mimic Win's "(int)x adjusted by sign mask" floor — for negative non-integer
// x: subtract 1 from the truncated result.  Equivalent to floorf, but kept
// literal so we faithfully follow the binary's branches.
static inline int win_floor_int(float x) {
	int t = (int)x;
	if (x < 0.0f) {
		// Win does:  iVar2 - (uint)((float)(int)(float)(x ^ NEG_Z) < (float)(x ^ NEG_Z));
		// i.e. subtract 1 iff trunc(|x|) != |x| (i.e. x has a fractional part).
		union { float f; uint32_t u; } u; u.f = x;
		u.u ^= K_NEGZ;
		float ax = u.f;
		int   ai = (int)ax;
		t -= ((float)ai < ax) ? 1 : 0;
	}
	return t;
}

static inline float win_pf32_mul_add(float a, float b, float c)
{
	volatile float product = a * b;
	return product + c;
}

static inline float win_pf32_mul_sub(float a, float b, float c)
{
	volatile float product = a * b;
	return product - c;
}

static inline float win_pf32_sub_mul(float c, float a, float b)
{
	volatile float product = a * b;
	return c - product;
}

// FUN_180013700 — line vs scanline band coverage rasterizer.
//   param_2 = (x0,y0), param_3 = (x1,y1), param_4 = scan_y (int).
//   Returns two coverage floats in out[0]/out[1] (top/bottom half).
static float *win_FUN_180013700(float *out, const float *p2, const float *p3,
                                int scan_y, bool preserve_pf32_scalar_rounding)
{
	float y0  = p2[1];
	float dy  = p3[1] - y0;
	float x0  = p2[0];
	float dx  = p3[0] - x0;
	if (dy == 0.0f || dx == 0.0f) {
		out[0] = 0.0f; out[1] = 0.0f; return out;
	}
	float scanLo = (float)scan_y + K_ONE;          // = scan_y + 1
	float scanHi = scanLo + K_ONE;                 // = scan_y + 2
	// x-intercepts at scanLo / scanHi
	float xAtLo  = ((scanLo - y0) * dx) / dy + x0;
	float yAtX_Lo = ((scanLo - x0) * dy) / dx + y0;     // y where line meets x = scanLo
	float xAtHi  = ((scanHi - y0) * dx) / dy + x0;
	float yAtX_Hi = ((scanHi - x0) * dy) / dx + y0;
	float yAtX_Mid = (((scanLo - K_ONE) - y0) * dx) / dy + x0;  // x at scan_y+0
	(void)yAtX_Mid; // alias for fVar9 below
	float fVar9  = (((scanLo - K_ONE) - y0) * dx) / dy + x0; // alias

	// cVar4 from yAtX_Lo - scanLo
	float t8 = yAtX_Lo - scanLo;
	int it = win_floor_int(t8);
	int cVar4;
	if (it < -1)        cVar4 = 3;
	else if (it == -1)  cVar4 = 2;
	else                cVar4 = (it == 0) ? 1 : 0;

	// cVar5 from yAtX_Hi - scanLo.  Win asm at 180013892:  CMP R8D,-2 ; JLE skip
	// → boundary is "it2 > -2" (== "it2 >= -1") to enter inner dispatch; for
	// it2 == -2, cVar5 stays at 3.  Previous code used `it2 >= -2`, which
	// produced cVar5 = 0 instead of 3 at the -2 boundary, causing AA imprecision
	// for lines whose y-extension at scanHi sits exactly two pixels above scanLo.
	float t6 = yAtX_Hi - scanLo;
	int it2 = win_floor_int(t6);
	int cVar5 = 3;
	if (it2 > -2) {
		if (it2 == -1)      cVar5 = 2;
		else                cVar5 = (it2 == 0) ? 1 : 0;
	}

	// fractional parts of yAtX_Lo, yAtX_Hi
	int iL = win_floor_int(yAtX_Lo);
	int iH = win_floor_int(yAtX_Hi);
	float fracL = yAtX_Lo - (float)iL;
	float fracH = yAtX_Hi - (float)iH;

	float fVar7 = 0.0f, fVar6 = 0.0f;
	float f10 = xAtLo;       // line's x at scanLo
	float f13 = xAtHi;       // line's x at scanHi
	bool  done = false;

	if (cVar4 == 3) {
		if (cVar5 == 2) {
			float product = (scanHi - fVar9) * fracH;
			fVar7 = preserve_pf32_scalar_rounding
			    ? win_pf32_sub_mul(K_ONE, product, K_HALF)
			    : K_ONE - product * K_HALF;
			fVar6 = 0.0f; done = true;
		} else if (cVar5 == 1) {
			fVar7 = preserve_pf32_scalar_rounding
			    ? win_pf32_mul_sub(fVar9 + f10, K_HALF, scanLo)
			    : (fVar9 + f10) * K_HALF - scanLo;
			fVar6 = (scanHi - f10) * fracH * K_HALF;
			done = true;
		} else if (cVar5 == 0) {
			fVar7 = preserve_pf32_scalar_rounding
			    ? win_pf32_mul_sub(fVar9 + f10, K_HALF, scanLo)
			    : (fVar9 + f10) * K_HALF - scanLo;
			fVar6 = preserve_pf32_scalar_rounding
			    ? win_pf32_sub_mul(scanHi, f10 + f13, K_HALF)
			    : scanHi - (f10 + f13) * K_HALF;
			done = true;
		} else {
			// cVar5 == 3 (or other) → fall through to fVar7=1, fVar6=0
			fVar7 = K_ONE; fVar6 = 0.0f; done = true;
		}
	} else if (cVar4 == 2) {
		if (cVar5 == 2) {
			fVar7 = K_ONE - (fracH + fracL) * K_HALF;
			fVar6 = 0.0f; done = true;
		} else if (cVar5 == 1) {
			fVar7 = (f10 - scanLo) * (K_ONE - fracL) * K_HALF;
			fVar6 = (scanHi - f10) * fracH * K_HALF;
			done = true;
		} else if (cVar5 == 0) {
			fVar7 = (f10 - scanLo) * (K_ONE - fracL) * K_HALF;
			fVar6 = scanHi - (f10 + f13) * K_HALF;
			done = true;
		} else {
			// cVar5 == 3 → fall through to LAB_180013b69 via post-else (Win) where
			// fVar12 = (fVar9-scanLo)*fracL_orig and fVar7 = 1.0 - fVar12 * 0.5.
			float product = (fVar9 - scanLo) * fracL;
			fVar7 = preserve_pf32_scalar_rounding
			    ? win_pf32_sub_mul(K_ONE, product, K_HALF)
			    : K_ONE - product * K_HALF;
			fVar6 = 0.0f; done = true;
		}
	} else if (cVar4 == 1) {
		if (cVar5 == 2) {
			fVar7 = (scanHi - f10) * (K_ONE - fracH) * K_HALF;
			fVar6 = (f10 - scanLo) * fracL * K_HALF;
			done = true;
		} else if (cVar5 == 1) {
			fVar7 = 0.0f;
			fVar6 = (fracH + fracL) * K_HALF;
			done = true;
		} else if (cVar5 == 0) {
			fVar7 = 0.0f;
			float product = (f13 - scanLo) * (K_ONE - fracL);
			fVar6 = preserve_pf32_scalar_rounding
			    ? win_pf32_sub_mul(K_ONE, product, K_HALF)
			    : K_ONE - product * K_HALF;
			done = true;
		} else {
			// cVar5 == 3 → fall through path: fVar6 = (f10-scanLo)*fracL*0.5, fVar7=scanHi-(fVar9+f10)*0.5
			fVar6 = (f10 - scanLo) * fracL * K_HALF;
			fVar7 = preserve_pf32_scalar_rounding
			    ? win_pf32_sub_mul(scanHi, fVar9 + f10, K_HALF)
			    : scanHi - (fVar9 + f10) * K_HALF;
			done = true;
		}
	} else {
		// cVar4 == 0
		if (cVar5 == 2) {
			fVar7 = (scanHi - f13) * (K_ONE - fracH) * K_HALF;
			fVar6 = preserve_pf32_scalar_rounding
			    ? win_pf32_mul_sub(f10 + f13, K_HALF, scanLo)
			    : (f10 + f13) * K_HALF - scanLo;
			done = true;
		} else if (cVar5 == 1) {
			fVar7 = 0.0f;
			float product = (scanLo - f13) * (K_ONE - fracH);
			fVar6 = preserve_pf32_scalar_rounding
			    ? win_pf32_sub_mul(K_ONE, product, K_HALF)
			    : K_ONE - product * K_HALF;
			done = true;
		} else if (cVar5 == 0) {
			fVar7 = 0.0f;
			fVar6 = K_ONE; done = true;
		} else {
			// cVar5 == 3 → fall through: fVar6 = (f10+f13)*0.5 - scanLo,  fVar7 = scanHi - (fVar9+f10)*0.5
			fVar6 = preserve_pf32_scalar_rounding
			    ? win_pf32_mul_sub(f10 + f13, K_HALF, scanLo)
			    : (f10 + f13) * K_HALF - scanLo;
			fVar7 = preserve_pf32_scalar_rounding
			    ? win_pf32_sub_mul(scanHi, fVar9 + f10, K_HALF)
			    : scanHi - (fVar9 + f10) * K_HALF;
			done = true;
		}
	}
	(void)done;

	// End-clip: line endpoints prune coverage.
	if (scanLo < x0)  fVar7 = 0.0f;   // Win compares against fVar1 = *param_2
	if (p3[0] < scanHi) fVar6 = 0.0f;
	out[0] = fVar7; out[1] = fVar6;
	return out;
}

// FUN_180013bc0 — trapezoid (two lines A,B) vs scanline band.  Computes the
// x-intercepts of A and B at scanLo/scanHi, clips at lines' crossing point,
// then forwards a cleaned-up 2-point segment to FUN_180013700.
static float *win_FUN_180013bc0(float *out, const float *pA0, const float *pA1,
                                const float *pB0, const float *pB1, int scan_y,
                                bool preserve_pf32_scalar_rounding)
{
	float ax = pA0[0], ay = pA0[1];
	float adx = pA1[0] - ax, ady = pA1[1] - ay;
	float bx = pB0[0], by = pB0[1];
	float bdx = pB1[0] - bx, bdy = pB1[1] - by;

	float scanLo = (float)scan_y + K_ONE;
	float scanHi = scanLo + K_ONE;

	// y-coordinate where lines A and B cross (Win's fVar7).
	float a_term = preserve_pf32_scalar_rounding
	    ? win_pf32_mul_sub(ax / adx, ady, ay)
	    : (ax / adx) * ady - ay;
	float b_term = preserve_pf32_scalar_rounding
	    ? win_pf32_mul_sub(bx / bdx, bdy, by)
	    : (bx / bdx) * bdy - by;
	float crossY = (a_term - b_term) / (ady / adx - bdy / bdx);
	float yLo, yHi;
	yLo = (crossY <= scanLo)
	      ? (preserve_pf32_scalar_rounding
	         ? win_pf32_mul_add((scanLo - bx) / bdx, bdy, by)
	         : ((scanLo - bx) / bdx) * bdy + by)
	      : (preserve_pf32_scalar_rounding
	         ? win_pf32_mul_add((scanLo - ax) / adx, ady, ay)
	         : ((scanLo - ax) / adx) * ady + ay);
	yHi = (crossY <= scanHi)
	      ? (preserve_pf32_scalar_rounding
	         ? win_pf32_mul_add((scanHi - bx) / bdx, bdy, by)
	         : ((scanHi - bx) / bdx) * bdy + by)
	      : (preserve_pf32_scalar_rounding
	         ? win_pf32_mul_add((scanHi - ax) / adx, ady, ay)
	         : ((scanHi - ax) / adx) * ady + ay);

	// Clip endpoints.  Asm at 180013d0e-d56 unconditionally initializes
	//   p2 = (scanLo, yLo), p3 = (scanHi, yHi)
	// then if ax > scanLo overwrites p2 with (ax, ay) AND skips the p3 check;
	// else if scanHi > pB1[0] overwrites p3 with (pB1[0], pB1[1]).
	float p2x = scanLo, p2y = yLo, p3x = scanHi, p3y = yHi;
	if (ax > scanLo) {
		p2x = ax; p2y = ay;
		// p3 stays (scanHi, yHi)
	} else {
		if (scanHi > pB1[0]) {
			p3x = pB1[0]; p3y = pB1[1];
		}
		// else p3 stays (scanHi, yHi)
	}

	float seg2[2] = { p2x, p2y };
	float seg3[2] = { p3x, p3y };
	return win_FUN_180013700(
	    out, seg2, seg3, scan_y, preserve_pf32_scalar_rounding);
}

// FUN_180012850 — 16-case (clsR + clsL*4) switch.  Each case fills a small
// local frame with either 4 floats (line → 13700) or 8 floats (trapezoid →
// 13bc0).  Default = {0,0}.  param_2 = total span length (becomes a base x).
static float *win_FUN_180012850(float *out, int span_total, int scan_y,
                                int clsL, int clsR,
                                bool preserve_pf32_scalar_rounding)
{
	float fVar1 = (float)span_total;
	float L[8] = {0,0,0,0,0,0,0,0};
	int key = clsR + clsL * 4;
	bool useTrap = false;
	switch (key) {
	case 0:
		L[6] = fVar1 + K_HALF;
		L[7] = fVar1 + 0.0f;
		L[5] = K_ONE;
		L[4] = K_W15;
		break;
	case 1:
		L[6] = fVar1 + K_ONE;
		L[5] = K_ONE;
		L[4] = K_W15;
		L[7] = fVar1 + 0.0f;
		break;
	case 2:
		L[7] = fVar1 + K_HALF;
		L[0] = K_W15;
		L[6] = fVar1 + K_ONE;
		L[4] = K_ONE;
		L[5] = 0.0f;
		L[1] = K_ONE;
		L[3] = L[6];
		L[2] = fVar1 + K_W20;
		useTrap = true;
		break;
	case 3:
		L[7] = fVar1 + K_ONE;
		L[0] = K_W15;
		L[6] = fVar1 + K_ONE;
		L[4] = K_ONE;
		L[5] = 0.0f;
		L[1] = K_ONE;
		L[3] = L[6];
		L[2] = fVar1 + K_W20;
		useTrap = true;
		break;
	case 4:
		L[6] = fVar1 + K_HALF;
		L[7] = fVar1 + 0.0f;
		L[5] = K_ONE;
		L[4] = K_ONE;
		break;
	case 5:
		L[6] = fVar1 + K_ONE;
		L[7] = fVar1 + 0.0f;
		L[5] = K_ONE;
		L[4] = K_ONE;
		break;
	case 6:
		L[0] = K_ONE;
		L[7] = fVar1 + K_HALF;
		L[6] = fVar1 + K_ONE;
		L[4] = K_ONE;
		L[5] = 0.0f;
		L[1] = K_ONE;
		L[3] = L[6];
		L[2] = fVar1 + K_W20;
		useTrap = true;
		break;
	case 7:
		L[0] = K_ONE;
		L[7] = fVar1 + K_ONE;
		L[6] = fVar1 + K_ONE;
		L[4] = K_ONE;
		L[5] = 0.0f;
		L[1] = K_ONE;
		L[3] = L[6];
		L[2] = fVar1 + K_W20;
		useTrap = true;
		break;
	case 8:
		// Win swaps the pointer order: 13bc0(out, L+6, L+4, L+2, L+0, scan)
		L[2] = 0.0f; L[3] = 0.0f;
		L[6] = K_ONE; L[7] = 0.5f;
		L[5] = fVar1 + K_ONE;
		L[4] = fVar1 + K_ONE;
		L[1] = fVar1 + 0.0f;
		L[0] = fVar1 + K_HALF;
		win_FUN_180013bc0(
		    out, &L[6], &L[4], &L[2], &L[0], scan_y,
		    preserve_pf32_scalar_rounding);
		return out;
	case 9:
		L[1] = K_HALF;
		L[0] = K_ONE;
		L[6] = fVar1 + K_ONE;
		L[3] = L[6];
		L[2] = L[6];
		L[7] = fVar1 + 0.0f;
		L[4] = 0.0f;
		L[5] = 0.0f;
		useTrap = true;
		break;
	case 10:
		L[5] = K_HALF;
		L[6] = fVar1 + K_ONE;
		L[7] = fVar1 + K_HALF;
		L[4] = K_ONE;
		break;
	case 0xb:
		L[7] = fVar1 + K_ONE;
		L[5] = K_HALF;
		L[6] = L[7];
		L[4] = K_ONE;
		break;
	case 0xc:
		L[0] = K_ONE;
		L[1] = 0.0f;
		L[6] = fVar1 + K_HALF;
		L[3] = fVar1 + K_ONE;
		L[2] = fVar1 + K_ONE;
		L[7] = fVar1 + 0.0f;
		L[4] = 0.0f;
		L[5] = 0.0f;
		useTrap = true;
		break;
	case 0xd:
		L[0] = K_ONE;
		L[1] = 0.0f;
		L[6] = fVar1 + K_ONE;
		L[3] = L[6];
		L[2] = L[6];
		L[7] = fVar1 + 0.0f;
		L[4] = 0.0f;
		L[5] = 0.0f;
		useTrap = true;
		break;
	case 0xe:
		L[5] = 0.0f;
		L[6] = fVar1 + K_ONE;
		L[7] = fVar1 + K_HALF;
		L[4] = K_ONE;
		break;
	case 0xf:
		L[7] = fVar1 + K_ONE;
		L[5] = 0.0f;
		L[6] = L[7];
		L[4] = K_ONE;
		break;
	default:
		out[0] = 0.0f; out[1] = 0.0f;
		return out;
	}
	if (useTrap) {
		win_FUN_180013bc0(
		    out, &L[0], &L[2], &L[4], &L[6], scan_y,
		    preserve_pf32_scalar_rounding);
	} else {
		win_FUN_180013700(
		    out, &L[4], &L[6], scan_y, preserve_pf32_scalar_rounding);
	}
	return out;
}

// Wrapper preserving the existing call signature used by append_weighted.
//   span_len           → mapped to "span_total" (Win param_2)
//   offset_from_center → Win param_3 (= cx - L_x or R_x - cx); used by 13700/13bc0
//                        to compute the trapezoid X coordinate where the weight
//                        is sampled.  Previous port discarded this → wrong
//                        weights at every call site that uses append_weighted.
//   case_key           → split into clsL = key>>2, clsR = key & 3.
static inline void win_weight_pair(float *out_ab, int span_len, int offset_from_center,
                                   int case_key, bool preserve_pf32_scalar_rounding)
{
	int clsL = (case_key >> 2) & 3;
	int clsR = case_key & 3;
	win_FUN_180012850(
	    out_ab, span_len, offset_from_center, clsL, clsR,
	    preserve_pf32_scalar_rounding);
}


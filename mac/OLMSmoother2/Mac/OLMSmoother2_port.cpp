// OLMSmoother2.cpp — macOS literal port of the Windows OLMSmoother2.aex pipeline.
// Session B: frame-level setup (copy/unpremul/key/invert/gamma-encode) +
//            5-stage per-pixel pipeline + inverse-gamma output.
//            FUN_18000c280 (polygon builder) is stubbed to count=0, so the
//            orchestrator falls through to the "no blur" branch and writes
//            the center sample straight out.  Expected behavior: pass-through
//            (modulo gamma encode/decode roundtrip when gamma mode is on).

#include "OLMSmoother2.h"
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cstdio>

// ============================================================================
// Constants read directly from the Windows binary (see DAT_180022xxx).
// Session B uses only a subset; the rest are kept for future sessions.
// Marked with (void) refs at the end of the translation unit to avoid
// -Wunused-const-variable complaints, but declared here for clarity.
// ============================================================================
namespace k_olm {
constexpr float  HALF        = 0.5f;      // DAT_180022694
constexpr float  ONE         = 1.0f;      // DAT_1800226a0
constexpr float  W_15        = 1.5f;      // DAT_180022de0
constexpr float  W_20        = 2.0f;      // DAT_180022de4
constexpr float  W_QUARTER   = 0.25f;     // DAT_180022ddc
constexpr uint32_t NEG_ZERO  = 0x80000000u; // DAT_180022df0 (sign mask)
constexpr float  V255        = 255.0f;    // DAT_180022700
constexpr float  INV255      = 1.0f / 255.0f; // DAT_180022690
constexpr float  V32768      = 32768.0f;  // DAT_180022704
constexpr uint32_t ABSMASK   = 0x7FFFFFFFu; // DAT_180022710
constexpr float  COLOR_TOL   = 0.001960922f; // DAT_18002268c (3B008081h)

// sRGB piecewise constants (doubles, matching the Win literal bit patterns)
constexpr double SRGB_BREAK   = 0.00313066844250060782; // DAT_180022698
constexpr double SRGB_BOUND   = 0.04045;                // DAT_1800226a8
constexpr double SRGB_INVSCALE= 1.0 / 12.92;            // DAT_1800226c0
constexpr double SRGB_INV24   = 1.0 / 2.4;              // DAT_1800226c8
constexpr double SRGB_INV1055 = 1.0 / 1.055;            // DAT_1800226d0
constexpr double SRGB_ONE     = 1.0;                    // DAT_1800226d8
constexpr double SRGB_1055    = 1.055;                  // DAT_1800226e0
constexpr double SRGB_24      = 2.4;                    // DAT_1800226e8
constexpr double SRGB_1292    = 12.92;                  // DAT_1800226f8
constexpr double SRGB_OFFSET2 = 0.055;                  // DAT_1800226b8
}

// Short aliases used below
#define K_HALF      k_olm::HALF
#define K_ONE       k_olm::ONE
#define K_W15       k_olm::W_15
#define K_W20       k_olm::W_20
#define K_W025      k_olm::W_QUARTER
#define K_NEGZ      k_olm::NEG_ZERO
#define K_255       k_olm::V255
#define K_INV255    k_olm::INV255
#define K_32768     k_olm::V32768
#define K_ABSMASK   k_olm::ABSMASK
#define K_COLOR_TOL k_olm::COLOR_TOL
#define S_BREAK     k_olm::SRGB_BREAK
#define S_BOUND     k_olm::SRGB_BOUND
#define S_INVSCALE  k_olm::SRGB_INVSCALE
#define S_INV24     k_olm::SRGB_INV24
#define S_INV1055   k_olm::SRGB_INV1055
#define S_ONE       k_olm::SRGB_ONE
#define S_1055      k_olm::SRGB_1055
#define S_24        k_olm::SRGB_24
#define S_1292      k_olm::SRGB_1292
#define S_OFFSET2   k_olm::SRGB_OFFSET2

// CLI-only diagnostic hook. Keep default 0 for the AE plug-in path.
// 0=normal, 1=suppress idx=0 four-corner dispatch, 2=half weight, 3=quarter weight,
// 4=double weight.
static int g_olmsmoother2_idx0_diag_mode = 0;
// CLI-only source/class plane split diagnostic.
// 0=post setup for both, 1=sample pre-setup, 2=class pre-setup,
// 3=sample pre-gamma, 4=class pre-gamma.
static int g_olmsmoother2_plane_split_diag_mode = 0;
static int g_olmsmoother2_skip_index_diag = -1;
static int g_olmsmoother2_idx18_diag_mode = 0;
// CLI-only class-plane read diagnostic for the below-row c280 probes.
// 0=asm-current, 1=South byte2 / SE byte1, 2=South byte0 / SE byte1.
static int g_olmsmoother2_cplane_read_diag_mode = 0;
// CLI-only class-plane threshold diagnostic.
// 0=normal, 1=force Smooth Range, 2=force 0, 3=force key predicate 1.
static int g_olmsmoother2_class_threshold_diag_mode = 0;
// CLI-only gamma curve diagnostic. -1 keeps the current inferred source.
static int g_olmsmoother2_curve_idx_override = -1;
// CLI-only leaf diagnostic. 0=normal, 1=suppress f270.
static int g_olmsmoother2_leaf_diag_mode = 0;
static bool g_olmsmoother2_index_hist_enabled = false;
static uint64_t g_olmsmoother2_index_hist[256] = {};
static bool g_olmsmoother2_idx18_key_hist_enabled = false;
static int g_olmsmoother2_current_switch_idx = -1;
static uint64_t g_olmsmoother2_idx18_cardinal3_key_hist[128] = {};
static uint64_t g_olmsmoother2_idx18_cardinal12_key_hist[128] = {};
static int g_olmsmoother2_trace_x = -1;
static int g_olmsmoother2_trace_y = -1;
static bool g_olmsmoother2_force_input_premultiply = false;

static void OLMSmoother2ResetIndexHistogram(bool enabled)
{
	g_olmsmoother2_index_hist_enabled = enabled;
	for (uint64_t &count : g_olmsmoother2_index_hist) count = 0;
}

static void OLMSmoother2ResetIdx18KeyHistogram(bool enabled)
{
	g_olmsmoother2_idx18_key_hist_enabled = enabled;
	for (uint64_t &count : g_olmsmoother2_idx18_cardinal3_key_hist) count = 0;
	for (uint64_t &count : g_olmsmoother2_idx18_cardinal12_key_hist) count = 0;
}

static bool OLMSmoother2WriteIndexHistogram(const char *path)
{
	FILE *fp = std::fopen(path, "w");
	if (!fp) return false;
	std::fprintf(fp, "idx,count\n");
	for (int i = 0; i < 256; ++i) {
		if (g_olmsmoother2_index_hist[i] != 0) {
			std::fprintf(fp, "%d,%llu\n", i, (unsigned long long)g_olmsmoother2_index_hist[i]);
		}
	}
	std::fclose(fp);
	return true;
}

static bool OLMSmoother2WriteIdx18KeyHistogram(const char *path)
{
	FILE *fp = std::fopen(path, "w");
	if (!fp) return false;
	std::fprintf(fp, "cardinal,key,count\n");
	for (int i = 0; i < 128; ++i) {
		if (g_olmsmoother2_idx18_cardinal3_key_hist[i] != 0) {
			std::fprintf(fp, "3,%d,%llu\n", i, (unsigned long long)g_olmsmoother2_idx18_cardinal3_key_hist[i]);
		}
		if (g_olmsmoother2_idx18_cardinal12_key_hist[i] != 0) {
			std::fprintf(fp, "12,%d,%llu\n", i, (unsigned long long)g_olmsmoother2_idx18_cardinal12_key_hist[i]);
		}
	}
	std::fclose(fp);
	return true;
}

static void OLMSmoother2SetTracePixel(int x, int y)
{
	g_olmsmoother2_trace_x = x;
	g_olmsmoother2_trace_y = y;
}

static void OLMSmoother2ConfigureTracePixelFromEnvironment()
{
	const char *value = std::getenv("OLMSMOOTHER2_TRACE_PIXEL");
	const char *log_path = std::getenv("OLMSMOOTHER2_TRACE_LOG");
	const char *threshold_diag = std::getenv("OLMSMOOTHER2_CLASS_THRESHOLD_DIAG");
	const char *plane_split_diag = std::getenv("OLMSMOOTHER2_PLANE_SPLIT_DIAG");
	const char *force_input_premultiply = std::getenv("OLMSMOOTHER2_FORCE_INPUT_PREMULTIPLY");
	static char opened_log_path[1024] = {};
	if (log_path && *log_path && std::strcmp(log_path, opened_log_path) != 0) {
		if (std::freopen(log_path, "a", stderr)) {
			std::setvbuf(stderr, nullptr, _IOLBF, 0);
			std::snprintf(opened_log_path, sizeof(opened_log_path), "%s", log_path);
		}
	}
	int x = -1;
	int y = -1;
	char trailing = '\0';
	if (value) {
		if (std::sscanf(value, "%d,%d%c", &x, &y, &trailing) == 2) {
			OLMSmoother2SetTracePixel(x, y);
		} else {
			OLMSmoother2SetTracePixel(-1, -1);
		}
	}
	int mode = 0;
	if (threshold_diag) {
		g_olmsmoother2_class_threshold_diag_mode =
		    std::sscanf(threshold_diag, "%d%c", &mode, &trailing) == 1 && mode >= 0 && mode <= 3 ? mode : 0;
	}
	mode = 0;
	if (plane_split_diag) {
		g_olmsmoother2_plane_split_diag_mode =
		    std::sscanf(plane_split_diag, "%d%c", &mode, &trailing) == 1 && mode >= 0 && mode <= 4 ? mode : 0;
	}
	g_olmsmoother2_force_input_premultiply =
	    force_input_premultiply && std::strcmp(force_input_premultiply, "1") == 0;
}

// ============================================================================
// Plumbing: SMParams (Win struct analog) and pixel helpers
// ============================================================================
struct SMParams {
	// Win mirror fields we read per-pixel (mapped to FUN_180004e10 layout by role)
	int           version;        // *param_8 (1 = v1, else v2)
	bool          enable_key;     // param_8[6] lsbyte
	bool          invert_key;     // param_8[5] lsbyte
	bool          keep_premul;    // (char)((longlong)param_8 + 0x19) — pre-mul output flag
	PF_PixelFloat key_color;      // offset 0x0c (RGBA stored as R,G,B,A floats)
	int           smoothness_raw; // Win +0x28 — slider counts, /100 later
	int           extra_smooth_raw; // Win +0x2c
	int           smooth_range;   // Win +0x24 — radius slider
	int           gamma_mode;     // UI popup: 1=None, 2=Gamma Colors, 3=All Colors
	float         gamma_value;    // Win gamma config +0x30
	int           num_gamma_colors;
	PF_PixelFloat gamma_colors[NUM_GAMMA_COLORS];

	// Runtime scratch
	int32_t       w, h;

	// Win analogue of FUN_180002930's output: 1 byte per pixel, nonzero means
	// "foreground"/"edge source".  Built at frame setup; read by the cardinal
	// scanners in build_polygon.  Stride in bytes is always w (tightly packed).
	const uint8_t *class_plane;
};

// Float-pixel scratch buffer (16 bytes per pixel, RGBA packed order)
struct FPix {
	float r, g, b, a;
};

// Pixel layer descriptor — mirrors the 3-element tuple (ptr, rowbytes_combined, stride_extra) used in Win
struct FPlane {
	FPix*  base;
	size_t rowbytes;   // 16 * w
	size_t _reserved;  // unused; matches Win triple layout
};

// ============================================================================
// Param fetch from AE
// ============================================================================
static PF_Err
FetchParams(PF_InData *in_data, PF_ParamDef *params[], SMParams *p)
{
	PF_Err err = PF_Err_NONE;
	AEGP_SuiteHandler suites(in_data->pica_basicP);

	p->enable_key       = params[SM_ENABLE_KEY]->u.bd.value != 0;
	p->invert_key       = params[SM_INVERT_KEY]->u.bd.value != 0;
	p->smoothness_raw   = params[SM_SMOOTHNESS]->u.sd.value;
	p->extra_smooth_raw = params[SM_EXTRA_SMOOTH]->u.sd.value;
	p->smooth_range     = params[SM_SMOOTH_RANGE]->u.sd.value;
	p->version          = params[SM_VERSION]->u.pd.value;      // 1 or 2
	p->gamma_mode       = params[SM_GAMMA_MODE]->u.pd.value;   // 1/2/3
	p->gamma_value      = (float)params[SM_GAMMA_VALUE]->u.fs_d.value;
	p->num_gamma_colors = params[SM_NUM_GAMMA_COLORS]->u.sd.value;
	// The current Windows AEX leaves param_8+0x19 clear. Its PF8 writer emits
	// straight RGB; AE premultiplies later when exporting the PNG.
	p->keep_premul      = false;

	PF_ColorParamSuite1 *cps = suites.ColorParamSuite1();
	cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
		params[SM_KEY_COLOR], &p->key_color);
	for (int i = 0; i < NUM_GAMMA_COLORS; ++i) {
		cps->PF_GetFloatingPointColorFromColorDef(in_data->effect_ref,
			params[SM_GAMMA_COLOR_0 + i], &p->gamma_colors[i]);
	}
	return err;
}

// ============================================================================
// Pixel load / store for read/write of AE layers (A,R,G,B packed order)
// ============================================================================
template<typename P> static inline void load_rgba(const P *p, float &a, float &r, float &g, float &b);
template<> inline void load_rgba<PF_Pixel8>(const PF_Pixel8 *p, float &a, float &r, float &g, float &b) {
	// FUN_1800024c0: CVTDQ2PS followed by MULSS with DAT_180022690.
	a = (float)p->alpha * K_INV255;
	r = (float)p->red   * K_INV255;
	g = (float)p->green * K_INV255;
	b = (float)p->blue  * K_INV255;
}
template<> inline void load_rgba<PF_Pixel16>(const PF_Pixel16 *p, float &a, float &r, float &g, float &b) {
	a = p->alpha / K_32768; r = p->red / K_32768; g = p->green / K_32768; b = p->blue / K_32768;
}
template<> inline void load_rgba<PF_PixelFloat>(const PF_PixelFloat *p, float &a, float &r, float &g, float &b) {
	a = p->alpha; r = p->red; g = p->green; b = p->blue;
}

// Diagnostic host-boundary adapter. Integer AE worlds premultiply in their
// native code domain before conversion to normalized float; multiplying the
// normalized values directly loses the byte/word rounding witness.
template<typename P>
static inline void diagnostic_premultiply_input(const P *, float &a, float &r, float &g, float &b) {
	r *= a; g *= a; b *= a;
}
template<>
inline void diagnostic_premultiply_input<PF_Pixel8>(const PF_Pixel8 *p, float &, float &r, float &g, float &b) {
	const uint32_t a = p->alpha;
	r = ((uint32_t)p->red   * a + 127u) / 255u / K_255;
	g = ((uint32_t)p->green * a + 127u) / 255u / K_255;
	b = ((uint32_t)p->blue  * a + 127u) / 255u / K_255;
}
template<>
inline void diagnostic_premultiply_input<PF_Pixel16>(const PF_Pixel16 *p, float &, float &r, float &g, float &b) {
	const uint64_t a = p->alpha;
	r = ((uint64_t)p->red   * a + 16384u) / 32768u / K_32768;
	g = ((uint64_t)p->green * a + 16384u) / 32768u / K_32768;
	b = ((uint64_t)p->blue  * a + 16384u) / 32768u / K_32768;
}

static inline u_char  clamp8 (float v) { v = v * K_255   + K_HALF; return v < 0 ? 0 : (v > 255.f   ? (u_char)255    : (u_char )v); }
static inline u_short clamp16(float v) { v = v * K_32768 + K_HALF; return v < 0 ? 0 : (v > 32768.f ? (u_short)32768 : (u_short)v); }

// ============================================================================
// Helpers: absolute difference via sign-bit mask (mirrors Win bit-trick)
// ============================================================================
static inline float fabs_bits(float v) {
	uint32_t u; memcpy(&u, &v, 4); u &= K_ABSMASK;
	float out; memcpy(&out, &u, 4); return out;
}

// ============================================================================
// Frame-level setup functions — LITERAL PORTS.
// The Win functions operate over [y0..y1) × [x0..x1) rectangle on a float4 RGBA
// plane.  We call them once across the whole scratch buffer.
// ============================================================================

// FUN_180002600 — copy source world (float RGBA) into scratch buffer.
// Not directly used here because we read from the templated AE layer into scratch ourselves.
// Preserved as a logical step: the copy is the "load_rgba over all pixels" loop below.

// FUN_180002840 — un-premultiply: if A != 0 and A != 1 then RGB /= A
static void win_FUN_180002840_unpremul(FPix *scratch, int32_t w, int32_t h)
{
	const float one = K_ONE;
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			float a = row[x].a;
			if (a != 0.0f && a != one) {
				float inv = one / a;
				row[x].r *= inv;
				row[x].g *= inv;
				row[x].b *= inv;
			}
		}
	}
}

// FUN_180002930 — palette-filter test (NOT a key-color test).  Win semantics
// confirmed via Ghidra disassembly @ 0x180002930:
//   - Reads list base ptr from SMParams byte offset 0x68 (= setter param_1[0xd])
//     and list count from byte offset 0x60 (= setter param_1[0xc]).
//   - These two slots are populated by FUN_180004e10 when Enable Color Key +
//     Invert Color Key stores a one-entry palette = Color Key.
//     Gamma Correction == COLORS_ONLY uses the separate bb10/a9c0 gamma-color
//     config, not this frame-level alpha filter.
//     For other states the OUTER caller FUN_180002e90 gate
//     `*(longlong *)(param_4 + 0x60) != 0` is FALSE, so this routine is skipped.
//   - For each pixel, walks the active palette list (4 floats per entry, 16 bytes).
//     If any entry's RGB is within K_COLOR_TOL of the pixel RGB, keep alpha;
//     otherwise set alpha=0 (LAB_180002a31: pfVar3[3] = 0.0).
// The single SM_KEY_COLOR param is therefore consumed by this function only in
// the invert-key path; in the non-invert key path it is stored in the scalar
// key slot instead.
static void win_FUN_180002930_palette_filter(FPix *scratch, int32_t w, int32_t h,
                                             const PF_PixelFloat *palette,
                                             int palette_count)
{
	if (palette_count <= 0) return;
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			bool match = false;
			for (int i = 0; i < palette_count; ++i) {
				if (fabs_bits(row[x].r - palette[i].red)   < K_COLOR_TOL &&
				    fabs_bits(row[x].g - palette[i].green) < K_COLOR_TOL &&
				    fabs_bits(row[x].b - palette[i].blue)  < K_COLOR_TOL) {
					match = true;
					break;
				}
			}
			if (!match) row[x].a = 0.0f;
		}
	}
}

// FUN_180002a70 — invert-key: if pixel RGB is within tolerance of the key
// color, force alpha=0 (opposite of key_test).
[[maybe_unused]]
static void win_FUN_180002a70_invert_key(FPix *scratch, int32_t w, int32_t h,
                                         const PF_PixelFloat &key)
{
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			if (fabs_bits(row[x].r - key.red)   >= K_COLOR_TOL ||
			    fabs_bits(row[x].g - key.green) >= K_COLOR_TOL ||
			    fabs_bits(row[x].b - key.blue)  >= K_COLOR_TOL) {
				// not a match — keep alpha
			} else {
				row[x].a = 0.0f;
			}
		}
	}
}

// FUN_180002ba0 — frame-level "gamma encode" call site.  LITERAL INSPECTION
// shows this is actually sRGB DECODE (sRGB-coded input -> linear light):
//   v <= 0           -> 0
//   v >= 1           -> 1
//   v < 0.04045      -> v * (1/12.92)                    [linear branch]
//   else             -> pow(v/1.055 + 0.055/1.055, 2.4) ≈ ((v+0.055)/1.055)^2.4
// This turns inputs into linear space so the smoother math operates on
// linear light; the per-pixel write-back (FUN_180004d70) then re-applies
// sRGB ENCODE for display.  We keep the name "gamma_encode" to match the
// caller naming convention in the mission spec, but document the reality.
static inline float win_srgb_decode_one(float v) {
	double d = (double)v;
	if (d <= 0.0) return 0.0f;
	if (d >= S_ONE) return (float)S_ONE;
	if (d < S_BOUND) return (float)(d * S_INVSCALE);      // v * DAT_1800226c0
	// Ghidra literal: pow(v * (1/1.055) + 0.055/1.055, 2.4)
	const double offset_over_1055 = 0.055 / 1.055;        // DAT_1800226b0 ≈ 0.05213
	return (float)pow(d * S_INV1055 + offset_over_1055, S_24);
}

static void win_FUN_180002ba0_gamma_encode(FPix *scratch, int32_t w, int32_t h,
                                           const SMParams &p)
{
	// For Session B we always take the built-in sRGB branch (param_6 == 0 in Win).
	// The custom-LUT branch (FUN_180004cd0) would honor p.gamma_value explicitly
	// via a user-provided LUT; not wired in this session.
	//
	// agentLL fix (2026-04-28): Win FUN_180002ba0 (decompiled at 0x180002ba0)
	// has NO per-pixel gamma_mode gating in the body — once the outer caller
	// (FUN_180003030, gate "*param_4 != 1") admits the call, EVERY pixel is
	// sRGB-decoded.  The previous Mac body inserted a `gamma_mode ==
	// GAMMA_COLORS_ONLY` color-match early-skip that does not exist in Win,
	// silently bypassing the decode for all pixels not matching a UI palette
	// color (and for ALL pixels when the palette was empty in COLORS_ONLY
	// mode).  This produced a global precision divergence in the AA composite
	// because the smoother math then operated on sRGB-encoded values rather
	// than linear light.  The literal Win body is just: per-pixel branch on
	// `*param_6` (LUT vs built-in sRGB) — nothing else.
	(void)p; // gamma_mode/gamma_colors not consulted in Win body
	for (int32_t y = 0; y < h; ++y) {
		FPix *row = scratch + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			row[x].r = win_srgb_decode_one(row[x].r);
			row[x].g = win_srgb_decode_one(row[x].g);
			row[x].b = win_srgb_decode_one(row[x].b);
		}
	}
}

// ============================================================================
// Per-pixel 5-stage pipeline — structurally-correct marching-squares AA.
// SmootherPolygon — matches the Win FUN_18000c280/FUN_1800104d0 layout.
//
//   poly +0x00 : plane_base, rowbytes, _  (FPlane triple — set from param_2)
//   poly +0x20 : int  bound_x  (image width)
//   poly +0x24 : int  bound_y  (image height)
//   poly +0x30 : int  cur_x    (current output pixel)
//   poly +0x34 : int  cur_y
//   poly +0x38 : float smoothness_norm  (slider / 100)
//   poly +0x3C : float extra_norm       (slider / 100)
//   poly +0x40 : vertex[0..11] = 12 × {R,G,B,A,w}  (20 bytes each)
//   poly +0x130: longlong count
//
// The downstream stages (weight_samples / gamma_decode_premul / composite /
// post_unpremul_gamma) read vertex[i].{r,g,b,a,w} and .count — kept backward
// compatible with the previous `samples[]` name for those callers.
// ============================================================================
struct PolyVertex {
	float r, g, b, a, w;   // 20 bytes — Win vertex layout
};
typedef PolyVertex PolySample;   // backward-compat alias for existing stages

struct SmootherPolygon {
	// --- header (Win offsets 0x00..0x3C) — literal port ---
	const FPlane* plane;          // +0x00 source float plane triple
	const uint8_t* cplane_base;   // +0x18 class plane base (4 bytes/pixel [A,R,G,B])
	int32_t       cplane_w;       // +0x20 class plane width
	int32_t       cplane_h;       // +0x24 class plane height
	int32_t       cplane_stride;  // +0x28 class plane byte stride (= 4*w)
	int32_t       _pad_2c;        // +0x2c (stride high word in Win's longlong)
	int32_t       cur_x;          // +0x30
	int32_t       cur_y;          // +0x34
	float         smoothness_n;   // +0x38  (DAT_180022dd0 = 100.0 denom)
	float         extra_n;        // +0x3C

	// --- vertex buffer (Win +0x40 .. +0x130) ---
	PolyVertex    samples[12];    // kept name 'samples' for downstream stages
	int32_t       count;          // Win uses a longlong; int is enough in port

	// Convenience alias: Win bound_x/bound_y === cplane_w/cplane_h (same data).
	int32_t bound_x() const { return cplane_w; }
	int32_t bound_y() const { return cplane_h; }
};

// CLI-only same-state bridge probe. The AE path leaves this disabled.
struct WriterFrameProbe {
	int x = -1;
	int y = -1;
	const char *json_path = nullptr;
	bool captured = false;
	bool bb10_apply = false;
	bool gamma_enable = false;
	float adaptive_gamma = 0.0f;
	FPix center{};
	FPix after_c0d0{};
	FPix after_ab00{};
	FPix cce0{};
	SmootherPolygon polygon{};
	uint8_t expected[4] = {};
	uint8_t actual[4] = {};
};
static WriterFrameProbe g_olmsmoother2_writer_frame_probe;

static uint32_t olmsmoother2_f32_u32(float value)
{
	uint32_t bits;
	std::memcpy(&bits, &value, sizeof(bits));
	return bits;
}

static void OLMSmoother2SetWriterFrameProbe(int x, int y, const char *json_path)
{
	g_olmsmoother2_writer_frame_probe = WriterFrameProbe{};
	g_olmsmoother2_writer_frame_probe.x = x;
	g_olmsmoother2_writer_frame_probe.y = y;
	g_olmsmoother2_writer_frame_probe.json_path = json_path;
}

// ---- helpers for plane access (NN at integer grid) ----
static inline float fplane_alpha(const FPlane &plane, int x, int y, int w, int h) {
	if (x < 0 || x >= w || y < 0 || y >= h) return 0.0f;
	const size_t stride = plane.rowbytes / sizeof(FPix);
	return plane.base[(size_t)y * stride + (size_t)x].a;
}

static inline FPix fplane_fetch(const FPlane &plane, int x, int y, int w, int h) {
	int xc = x < 0 ? 0 : (x >= w ? w - 1 : x);
	int yc = y < 0 ? 0 : (y >= h ? h - 1 : y);
	const size_t stride = plane.rowbytes / sizeof(FPix);
	return plane.base[(size_t)yc * stride + (size_t)xc];
}

// LITERAL PORT of FUN_1800104d0: append one vertex by reading 16 bytes (RGBA
// float) from the plane at integer grid (gi_x, gi_y), attaching weight `w`.
// No bounds clamp — helpers are responsible for their own guards (matches Win).
static inline void win_FUN_1800104d0_append(SmootherPolygon &poly,
                                            int gi_x, int gi_y, float w)
{
	if (poly.count >= 12) return;
	const FPlane &pl = *poly.plane;
	const size_t stride = pl.rowbytes / sizeof(FPix);
	const FPix &px = pl.base[(size_t)gi_y * stride + (size_t)gi_x];
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace append src=(%d,%d) dst_center=(%d,%d) rgba=(%.8g,%.8g,%.8g,%.8g) w=%.8g before_count=%d\n",
		             gi_x, gi_y, poly.cur_x, poly.cur_y, px.r, px.g, px.b, px.a, w, poly.count);
	}
	// Reverse trace: which cur_x,cur_y is pulling from the trace pixel?
	if (gi_x == g_olmsmoother2_trace_x && gi_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace rev_append src=(%d,%d) from_center=(%d,%d) w=%.8g before_count=%d\n",
		             gi_x, gi_y, poly.cur_x, poly.cur_y, w, poly.count);
	}
	PolyVertex &v = poly.samples[poly.count++];
	v.r = px.r; v.g = px.g; v.b = px.b; v.a = px.a; v.w = w;
}

// LITERAL PORT of FUN_18000cc70: divide every vertex weight by the vertex
// count.  Used at the tail of many 256-case dispatch paths as a normalizer.
static inline void win_FUN_18000cc70_normalize(SmootherPolygon &poly) {
	if (poly.count <= 0) return;
	float inv_n = 1.0f / (float)poly.count;
	for (int i = 0; i < poly.count; ++i) poly.samples[i].w *= inv_n;
}

// --- 4 corner helpers — LITERAL PORTS from Ghidra decomp of Win binary ---
// Each emits 3 vertices arranged as an L at the named corner, with weights
// {0.4, 0.2, 0.4} × poly.smoothness_n × `step` (the caller always passes
// DAT_180022dd4 = 0.125 as step).  Guarded against image-boundary reads.

// FUN_1800134c0 — NW (top-left) corner.
static inline void win_FUN_1800134c0_NW(SmootherPolygon &poly, float step) {
	if (poly.cur_x == 0 || poly.cur_y == 0) return;
	const float bw  = poly.smoothness_n;
	const float w_outer = step * bw * 0.4f;   // DAT_180022de8 = 0.4
	const float w_inner = step * bw * 0.2f;   // DAT_180022dd8 = 0.2
	win_FUN_1800104d0_append(poly, poly.cur_x - 1, poly.cur_y,     w_outer);
	win_FUN_1800104d0_append(poly, poly.cur_x - 1, poly.cur_y - 1, w_inner);
	win_FUN_1800104d0_append(poly, poly.cur_x,     poly.cur_y - 1, w_outer);
}

// FUN_180013570 — NE (top-right) corner.
static inline void win_FUN_180013570_NE(SmootherPolygon &poly, float step) {
	if (poly.cur_x == poly.bound_x() - 1 || poly.cur_y == 0) return;
	const float bw = poly.smoothness_n;
	const float w_outer = step * bw * 0.4f;
	const float w_inner = step * bw * 0.2f;
	win_FUN_1800104d0_append(poly, poly.cur_x,     poly.cur_y - 1, w_outer);
	win_FUN_1800104d0_append(poly, poly.cur_x + 1, poly.cur_y - 1, w_inner);
	win_FUN_1800104d0_append(poly, poly.cur_x + 1, poly.cur_y,     w_outer);
}

// FUN_180012c20 — SW (bottom-left) corner.
static inline void win_FUN_180012c20_SW(SmootherPolygon &poly, float step) {
	if (poly.cur_x == 0 || poly.cur_y == poly.bound_y() - 1) return;
	const float bw = poly.smoothness_n;
	const float w_outer = step * bw * 0.4f;
	const float w_inner = step * bw * 0.2f;
	win_FUN_1800104d0_append(poly, poly.cur_x - 1, poly.cur_y,     w_outer);
	win_FUN_1800104d0_append(poly, poly.cur_x - 1, poly.cur_y + 1, w_inner);
	win_FUN_1800104d0_append(poly, poly.cur_x,     poly.cur_y + 1, w_outer);
}

// FUN_180012ce0 — SE (bottom-right) corner.
static inline void win_FUN_180012ce0_SE(SmootherPolygon &poly, float step) {
	if (poly.cur_x == poly.bound_x() - 1 || poly.cur_y == poly.bound_y() - 1) return;
	const float bw = poly.smoothness_n;
	const float w_outer = step * bw * 0.4f;
	const float w_inner = step * bw * 0.2f;
	win_FUN_1800104d0_append(poly, poly.cur_x,     poly.cur_y + 1, w_outer);
	win_FUN_1800104d0_append(poly, poly.cur_x + 1, poly.cur_y + 1, w_inner);
	win_FUN_1800104d0_append(poly, poly.cur_x + 1, poly.cur_y,     w_outer);
}

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
		int steps = (lim_h <= lim_w - 1) ? lim_h : (lim_w - 1);
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
	int steps = (lim_h <= lim_w - 1) ? lim_h : (lim_w - 1);
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

// FUN_180013700 — line vs scanline band coverage rasterizer.
//   param_2 = (x0,y0), param_3 = (x1,y1), param_4 = scan_y (int).
//   Returns two coverage floats in out[0]/out[1] (top/bottom half).
static float *win_FUN_180013700(float *out, const float *p2, const float *p3, int scan_y)
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
			fVar7 = K_ONE - (scanHi - fVar9) * fracH * K_HALF;
			fVar6 = 0.0f; done = true;
		} else if (cVar5 == 1) {
			fVar7 = (fVar9 + f10) * K_HALF - scanLo;
			fVar6 = (scanHi - f10) * fracH * K_HALF;
			done = true;
		} else if (cVar5 == 0) {
			fVar7 = (fVar9 + f10) * K_HALF - scanLo;
			fVar6 = scanHi - (f10 + f13) * K_HALF;
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
			fVar7 = K_ONE - (fVar9 - scanLo) * fracL * K_HALF;
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
			fVar6 = K_ONE - (f13 - scanLo) * (K_ONE - fracL) * K_HALF;
			done = true;
		} else {
			// cVar5 == 3 → fall through path: fVar6 = (f10-scanLo)*fracL*0.5, fVar7=scanHi-(fVar9+f10)*0.5
			fVar6 = (f10 - scanLo) * fracL * K_HALF;
			fVar7 = scanHi - (fVar9 + f10) * K_HALF;
			done = true;
		}
	} else {
		// cVar4 == 0
		if (cVar5 == 2) {
			fVar7 = (scanHi - f13) * (K_ONE - fracH) * K_HALF;
			fVar6 = (f10 + f13) * K_HALF - scanLo;
			done = true;
		} else if (cVar5 == 1) {
			fVar7 = 0.0f;
			fVar6 = K_ONE - (scanLo - f13) * (K_ONE - fracH) * K_HALF;
			done = true;
		} else if (cVar5 == 0) {
			fVar7 = 0.0f;
			fVar6 = K_ONE; done = true;
		} else {
			// cVar5 == 3 → fall through: fVar6 = (f10+f13)*0.5 - scanLo,  fVar7 = scanHi - (fVar9+f10)*0.5
			fVar6 = (f10 + f13) * K_HALF - scanLo;
			fVar7 = scanHi - (fVar9 + f10) * K_HALF;
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
                                const float *pB0, const float *pB1, int scan_y)
{
	float ax = pA0[0], ay = pA0[1];
	float adx = pA1[0] - ax, ady = pA1[1] - ay;
	float bx = pB0[0], by = pB0[1];
	float bdx = pB1[0] - bx, bdy = pB1[1] - by;

	float scanLo = (float)scan_y + K_ONE;
	float scanHi = scanLo + K_ONE;

	// y-coordinate where lines A and B cross (Win's fVar7).
	float crossY = (((ax / adx) * ady - ay) - ((bx / bdx) * bdy - by)) /
	               (ady / adx - bdy / bdx);
	float yLo, yHi;
	yLo = (crossY <= scanLo)
	      ? (((scanLo - bx) / bdx) * bdy + by)
	      : (((scanLo - ax) / adx) * ady + ay);
	yHi = (crossY <= scanHi)
	      ? (((scanHi - bx) / bdx) * bdy + by)
	      : (((scanHi - ax) / adx) * ady + ay);

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
	return win_FUN_180013700(out, seg2, seg3, scan_y);
}

// FUN_180012850 — 16-case (clsR + clsL*4) switch.  Each case fills a small
// local frame with either 4 floats (line → 13700) or 8 floats (trapezoid →
// 13bc0).  Default = {0,0}.  param_2 = total span length (becomes a base x).
static float *win_FUN_180012850(float *out, int span_total, int scan_y,
                                int clsL, int clsR)
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
		win_FUN_180013bc0(out, &L[6], &L[4], &L[2], &L[0], scan_y);
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
		win_FUN_180013bc0(out, &L[0], &L[2], &L[4], &L[6], scan_y);
	} else {
		win_FUN_180013700(out, &L[4], &L[6], scan_y);
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
                                   int case_key)
{
	int clsL = (case_key >> 2) & 3;
	int clsR = case_key & 3;
	win_FUN_180012850(out_ab, span_len, offset_from_center, clsL, clsR);
}

// ---------------------------------------------------------------------------
// 12 mid-shape helpers — LITERAL ports of FUN_18001{122e0, 11d80, 11030, 115a0,
// 12f60, 11300, 12040, 12da0, 119a0, 125c0, 13140, 132f0}.
//
// Each helper:
//   1. Calls two scanners to bracket a run along one row/column.
//   2. Computes total span_len = (end - start + 1) + offset.
//   3. If span < 4 OR corner-boundary condition → fires the fallback corner
//      helper (FUN_180012c20/ce0/134c0/13570).
//   4. Otherwise classifies two endpoints (0..3) then calls FUN_180012850 to
//      get a 2-float weight, and appends ONE vertex at a side-offset position.
//
// Endpoint classifier (common shape): check 3 pixels around endpoint to form
// a 2-bit index that feeds FUN_180012850.
// ---------------------------------------------------------------------------

// === Pattern P1 — used by FUN_1800122e0 / 11d80 / 12040 / 1800125c0 ===
// L-side gate is A@(L, ry-1); secondary check is G@(L, ry) byte 2; nested
// check is A@(L, ry-2); fall-through uses R@(L-1, ry) byte 1.
static int endpoint_cls_left_P1(const GridDesc *g, int ex, int ry)
{
	if (ex == 0) return 2;
	// gate: ry == 0 OR A@(ex, ry-1) != 0
	bool gate = (ry == 0) || (cp_b(g, ex, ry - 1, 0) != 0);
	if (gate) {
		if (cp_b(g, ex, ry, 2) == 0) {
			if (ry < 2) return 2;
			if (cp_b(g, ex, ry - 2, 0) == 0) return 2;
			return 3;
		}
		return 0;
	}
	return (cp_b(g, ex - 1, ry, 1) != 0) ? 1 : 0;
}

// R-side P1: gate A@(R+1, ry); secondary G@(R+1, ry) byte 2; nested A@(R+1, ry+1) byte 0.
static int endpoint_cls_right_P1(const GridDesc *g, int ex, int ry)
{
	if (ex >= g->w - 1) return 2;
	if (cp_b(g, ex + 1, ry, 0) == 0)
		return (cp_b(g, ex + 1, ry, 1) != 0) ? 1 : 0;
	if (cp_b(g, ex + 1, ry, 2) == 0) {
		if (ry < g->h - 1 && cp_b(g, ex + 1, ry + 1, 0) != 0) return 3;
		return 2;
	}
	return 0;
}

// === Pattern P2 — used by FUN_180011030 / 11300 / 1800115a0 / 1800119a0 ===
// L-side gate is A@(L, ry); secondary check is B@(L-1, ry) byte 3; nested
// check is A@(L, ry+1).
static int endpoint_cls_left_P2(const GridDesc *g, int ex, int ry)
{
	if (ex == 0) return 2;
	if (cp_b(g, ex, ry, 0) == 0)
		return (cp_b(g, ex - 1, ry, 1) != 0) ? 1 : 0;
	if (cp_b(g, ex - 1, ry, 3) != 0) return 0;
	if (ry < g->h - 1 && cp_b(g, ex, ry + 1, 0) != 0) return 3;
	return 2;
}

// R-side P2: gate A@(R+1, ry-1); secondary B@(R, ry) byte 3; nested A@(R+1, ry-2).
static int endpoint_cls_right_P2(const GridDesc *g, int ex, int ry)
{
	if (ex >= g->w - 1) return 2;
	bool gate = (ry == 0) || (cp_b(g, ex + 1, ry - 1, 0) != 0);
	if (gate) {
		if (cp_b(g, ex, ry, 3) != 0) return 0;
		if (ry >= 2 && cp_b(g, ex + 1, ry - 2, 0) != 0) return 3;
		return 2;
	}
	return (cp_b(g, ex + 1, ry, 1) != 0) ? 1 : 0;
}

// Helper emit: append one vertex at (ex, ey) with computed trapezoid weight.
// Bug fix vs prior port:
//   - fscale used `extra_n * 1.0` but Win has `extra_n * DAT_180022ddc(=0.25)`.
//   - 12時 helpers (cy-1 emit) write wp[0] (local_res8) to the +0x50 slot;
//     6時 helpers (cy+1 emit) write wp[1] (local_resc).
//     Verified vs Ghidra @ 0x1800122e0 / 0x1800125c0 / 0x1800115a0 (12時 → wp[0])
//     and 0x180011d80 / 0x180012040 / 0x180011030 / 0x180011300 (6時 → wp[1]).
static inline void append_weighted(SmootherPolygon &poly, int ex, int ey,
                                   int span_len, int ep_offset, int case_key,
                                   int slot = 1)
{
	float wp[2];
	win_weight_pair(wp, span_len, ep_offset, case_key);
	float fscale = poly.extra_n * K_W025 + poly.smoothness_n;
	wp[0] *= fscale; wp[1] *= fscale;
	win_FUN_1800104d0_append(poly, ex, ey, wp[slot]);
}

// FUN_1800122e0 — 12時 side emit, scans current row left/right.
static bool win_FUN_1800122e0(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_10d20(L, &g, in);
	scan_10ad0(R, &g, in);
	int span = cx + 1 + (R[0] - cx) - L[0];
	if (span < 4) {
		if (cx < g.w - 1) {
			uint8_t g_byte = cp_b(&g, cx + 1, cy, 2);
			if (g_byte != 0) return true;
			win_FUN_180013570_NE(poly, W_STEP);
		}
		return true;
	}
	// Win uses iStackX_14 (L's walked y) and iStackX_1c (R's walked y) for the
	// endpoint classification, NOT cy.  Scanners walk diagonally so L[1]/R[1]
	// can differ from cy near image edges.
	int clsL = endpoint_cls_left_P1(&g, L[0], L[1]);
	int clsR = endpoint_cls_right_P1(&g, R[0], R[1]);
	// Win FUN_1800122e0 calls FUN_180012850(.., uVar7=clsR, uVar11=clsL),
	// so the switch index = param_5 + param_4*4 = clsL + clsR*4 (NOT clsL*4+clsR).
	// 12時: vertex weight = wp[0] (local_res8) per Ghidra @0x1800122e0.
	append_weighted(poly, cx, cy - 1, span, R[0] - cx, clsR * 4 + clsL, 0);
	return true;
}

// FUN_180011d80 — 6時 side emit, scans below row.
static bool win_FUN_180011d80(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_10bd0(L, &g, in);
	scan_109d0(R, &g, in);
	int span = cx + 1 + (R[0] - cx) - L[0];
	if (span < 4) {
		if (cy < g.h - 1 && cp_b(&g, cx, cy + 1, 2) != 0) return false;
		(void)span;
		win_FUN_180012c20_SW(poly, W_STEP);
		return true;
	}
	// Win: iStackX_14 = iStackX_14 + 1 (= L_y + 1), used for L-side cls.
	// Same for R via iStackX_1c + 1.
	int clsL = endpoint_cls_left_P1(&g, L[0], L[1] + 1);
	int clsR = endpoint_cls_right_P1(&g, R[0], R[1] + 1);
	// Win FUN_180011d80 calls FUN_180012850(.., uVar13=clsR, uVar9=clsL),
	// so the switch index = param_5 + param_4*4 = clsL + clsR*4 (NOT clsL*4+clsR).
	append_weighted(poly, cx, cy + 1, span, R[0] - cx, clsR * 4 + clsL);
	return true;
}

// FUN_180011030 — 6時 variant (scans below row left/right).
static bool win_FUN_180011030(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_108d0(L, &g, in);
	scan_10e40(R, &g, in);
	int span = (R[0] - cx) + 1 + (cx - L[0]);
	if (span < 4) {
		if (cy < g.h - 1 && cp_b(&g, cx, cy + 1, 3) == 0)
			win_FUN_180012ce0_SE(poly, W_STEP);
		return true;
	}
	// Win: iStackX_14 + 1 / iStackX_1c + 1 (= L_y + 1, R_y + 1).
	int clsL = endpoint_cls_left_P2(&g, L[0], L[1] + 1);
	int clsR = endpoint_cls_right_P2(&g, R[0], R[1] + 1);
	append_weighted(poly, cx, cy + 1, span, cx - L[0], clsL * 4 + clsR);
	return true;
}

// FUN_1800115a0 — 12時 NW-end variant.  LITERAL 1:1 port re-verified vs Ghidra.
//
// Win behavior:
//   L-walk: diagonal SW (x-1, y+1) while R != 0, breaking on B!=0 (curr or prev row),
//     A==0, or hitting limit min(cx, h-1-cy).  Pre-condition: A@(cx,cy)!=0.
//   R-walk: diagonal NE (x+1, y-1) while A!=0 && R!=0, breaking on B!=0 (curr or
//     col-left), or hitting limit min(cy, w-1-cx).  Pre-condition: B@(cx,cy)==0
//     && B@(cx,cy-1)==0.
//   Endpoint classes use L's walked y (uVar17) for left, R's walked y (uVar15)
//     for right — NOT cy.
//   Fallback gate uses B@(cx-1, cy), not G.
static bool win_FUN_1800115a0(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;

	// uVar6 = L's final x; uVar17 = L's final y; uVar18 = R's final x;
	// uVar15 = R's final y.  Initial values when no walking happens.
	int uVar6 = cx;          // L_x
	int uVar17 = cy;         // L_y
	int uVar18 = cx;         // R_x
	int uVar15 = cy;         // R_y

	// --- L-walk: diagonal SW while R-bit holds ---
	{
		int limit = (g.h - cy) - 1;
		if (cx < limit) limit = cx;
		if (limit > 0 && cp_b(&g, cx, cy, 0) != 0) {
			// Win uVar15 (running x), uVar19 (running y stored as ulonglong),
			// uVar17 (y at top), local_res18 (pre-decrement x).
			int it_x = cx;        // uVar15 in Win
			int it_y_stored = cy;  // uVar19 init
			int iVar8 = 0;
			for (;;) {
				int local_res18 = it_x;          // save x before decrement
				int it_y_top = it_y_stored;      // uVar17 = (uint)uVar19
				int new_x = local_res18 - 1;     // uVar15 = local_res18 - 1
				int new_y = it_y_top + 1;        // uVar18 = uVar17 + 1
				it_x = new_x;
				uVar6 = local_res18;             // pre-advance x snapshot
				uVar17 = it_y_top;               // pre-advance y snapshot
				// Outer: R@(new_x, new_y) == 0 → break with pre-advance state
				if (cp_b(&g, new_x, new_y, 1) == 0) break;
				// Inner B-checks: break with pre-advance state
				if (cp_b(&g, new_x, new_y, 3) != 0) break;
				if (cp_b(&g, new_x, new_y - 1, 3) != 0) break;
				// Advance commit: uVar6 = uVar15 (new_x), uVar17 = uVar18 (new_y)
				uVar6 = new_x;
				uVar17 = new_y;
				// A@(new_x, new_y) == 0 → break with NEW state
				if (cp_b(&g, new_x, new_y, 0) == 0) break;
				iVar8++;
				it_y_stored = new_y;             // uVar19 = (ulonglong)uVar18
				if (limit <= iVar8) break;
			}
		}
	}

	// --- R-walk: diagonal NE while A!=0 && R!=0 ---
	{
		int limit = (g.w - cx) - 1;
		if (cy < limit) limit = cy;
		if (limit > 0 && cp_b(&g, cx, cy, 3) == 0 && cp_b(&g, cx, cy - 1, 3) == 0) {
			// Win uVar15 (y), uVar12 (x at top), uVar18 (x advanced), uVar20 (saved x).
			int it_y_in = cy - 1;     // uVar12 init = uVar3 - 1 = cy - 1
			int it_x_in = cx;          // uVar20 init = cx
			int iVar8 = 0;
			for (;;) {
				uVar15 = it_y_in;       // uVar15 = uVar12 (y-coord)
				int it_x = it_x_in;     // uVar12 = (uint)uVar20 (x-coord)
				int new_x = it_x + 1;   // uVar18 = uVar12 + 1
				int new_x_save = new_x;  // uVar20 = (ulonglong)uVar18 (for next iter)
				// --- Outer break: A@(new_x, uVar15)==0 or R@(new_x, uVar15)==0.
				// Post-fixup runs (uVar15 += 1; uVar18 = uVar12 = it_x).
				if (cp_b(&g, new_x, uVar15, 0) == 0) {
					uVar15 = uVar15 + 1; uVar18 = it_x; break;
				}
				if (cp_b(&g, new_x, uVar15, 1) == 0) {
					uVar15 = uVar15 + 1; uVar18 = it_x; break;
				}
				// --- Inner break path (goto LAB_180011759): no fixup.
				// 1) B@(new_x, uVar15) != 0
				if (cp_b(&g, new_x, uVar15, 3) != 0) {
					uVar18 = new_x; break;
				}
				// 2) B@(new_x, uVar15 - 1) != 0
				if (uVar15 >= 1 && cp_b(&g, new_x, uVar15 - 1, 3) != 0) {
					uVar18 = new_x; break;
				}
				// 3) iVar8++, uVar12 = uVar15 - 1; if limit reached → goto LAB.
				iVar8++;
				it_y_in = uVar15 - 1;     // uVar12 = uVar15 - 1
				it_x_in = new_x_save;     // uVar20 = uVar18
				if (limit <= iVar8) {
					uVar18 = new_x; break;
				}
			}
		}
	}

	int span = (uVar18 - cx) + 1 + (cx - uVar6);
	if (span < 4) {
		// Win: if cx > 0 and B@(cx-1, cy) != 0 → return 0; else call FUN_1800134c0.
		if (cx > 0) {
			if (cp_b(&g, cx - 1, cy, 3) != 0) return false;
			win_FUN_1800134c0_NW(poly, W_STEP);
		}
		return true;
	}

	// Endpoint classes — Win uses (uVar6, uVar17) for left, (uVar18, uVar15) for right.
	// Reproduce inline from Ghidra logic.
	int clsL;
	if (uVar6 == 0) {
		clsL = 2;
	} else {
		// A@(uVar6, uVar17)
		if (cp_b(&g, uVar6, uVar17, 0) == 0) {
			// R@(uVar6 - 1, uVar17)
			clsL = (cp_b(&g, uVar6 - 1, uVar17, 1) != 0) ? 1 : 0;
		} else if (cp_b(&g, uVar6 - 1, uVar17, 3) == 0) {
			// B@(uVar6-1, uVar17) == 0 → check A@(uVar6, uVar17+1)
			if (uVar17 >= g.h - 1 || cp_b(&g, uVar6, uVar17 + 1, 0) == 0) {
				clsL = 2;
			} else {
				clsL = 3;
			}
		} else {
			clsL = 0;
		}
	}

	int clsR;
	if (uVar18 == g.w - 1) {
		clsR = 2;
	} else {
		// A@(uVar18+1, uVar15) when uVar15 == 0 OR B@(uVar18+1, uVar15-1) != 0
		bool branch1 = (uVar15 == 0) || cp_b(&g, uVar18 + 1, uVar15 - 1, 0) != 0;
		if (branch1) {
			// B@(uVar18, uVar15) (offset +3)
			if (cp_b(&g, uVar18, uVar15, 3) == 0) {
				// A@(uVar18+1, uVar15-2) check (uVar15 >= 2)
				if (uVar15 >= 2 && cp_b(&g, uVar18 + 1, uVar15 - 2, 0) != 0) {
					clsR = 3;
				} else {
					clsR = 2;
				}
			} else {
				clsR = 0;
			}
		} else {
			// R@(uVar18+1, uVar15) check (offset +5 = (uVar18+1)*4 + 1)
			clsR = (cp_b(&g, uVar18 + 1, uVar15, 1) != 0) ? 1 : 0;
		}
	}

	// 12時: vertex weight = wp[0] (local_res8) per Ghidra @0x1800115a0.
	append_weighted(poly, cx, cy - 1, span, cx - uVar6, clsL * 4 + clsR, 0);
	return true;
}

// FUN_180012f60 — SE corner 3-point emit variant (emits (cx,cy+1)/(cx+1,cy+1)/(cx+1,cy)).
static void win_FUN_180012f60(SmootherPolygon &poly) {
	int cy = poly.cur_y, cx = poly.cur_x;
	if (cy == poly.cplane_h - 1 || cx == poly.cplane_w - 1) return;
	GridDesc g = grid_of(poly);
	int in[2] = { cx, cy };
	int L[3], R[3];
	scan_d230(L, &g, in);
	scan_d3b0(R, &g, in);
	int spanX = (cx - L[0]) + 1;
	int spanY = (cy - R[1]) + 1;
	if ((spanX < 4 || spanY < 4) && (spanX < 2 || spanY < 2 ||
	    cp_b(&g, cx, cy + 1, 3) == 0)) {
		int len = (spanY < spanX) ? (cy - R[1]) : (cx - L[0]);
		// Win FUN_180012f60: fVar10 = DAT_180022694 (= 0.5f);
		//                    if (iVar8 == 2) fVar10 = DAT_180022dd4 (= 0.125f);
		float fscale = (len == 2) ? W_STEP : 0.5f;
		if (cy != poly.cplane_h - 1 && cx != poly.cplane_w - 1) {
			float b = poly.smoothness_n;
			float wo = fscale * b * W_OUT_W;
			float wi = fscale * b * W_IN_W;
			win_FUN_1800104d0_append(poly, cx,     cy + 1, wo);
			win_FUN_1800104d0_append(poly, cx + 1, cy + 1, wi);
			win_FUN_1800104d0_append(poly, cx + 1, cy,     wo);
		}
	}
}

// FUN_180011300 — 6時 variant.  Returns 1 when vertex emitted, 0 otherwise
// (matches Win decomp returning ulonglong as success flag).
static bool win_FUN_180011300(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_108d0(L, &g, in);
	scan_10e40(R, &g, in);
	int span = (R[0] - cx) + 1 + (cx - L[0]);
	if (span < 4) return false;
	// Win: iStackX_1c + 1 / iStackX_24 + 1 (= L_y + 1, R_y + 1).
	int clsL = endpoint_cls_left_P2(&g, L[0], L[1] + 1);
	int clsR = endpoint_cls_right_P2(&g, R[0], R[1] + 1);
	append_weighted(poly, cx, cy + 1, span, cx - L[0], clsL * 4 + clsR);
	return true;
}

// FUN_180012040 — 6時 variant.
static bool win_FUN_180012040(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_10bd0(L, &g, in);
	scan_109d0(R, &g, in);
	int span = cx + 1 + (R[0] - cx) - L[0];
	if (span < 4) return false;
	// Win: iStackX_14 + 1 / iStackX_1c + 1 (= L_y + 1, R_y + 1).
	int clsL = endpoint_cls_left_P1(&g, L[0], L[1] + 1);
	int clsR = endpoint_cls_right_P1(&g, R[0], R[1] + 1);
	// Win FUN_180012040 calls FUN_180012850(.., uVar11=clsR, uVar8=clsL),
	// so the switch index = param_5 + param_4*4 = clsL + clsR*4 (NOT clsL*4+clsR).
	append_weighted(poly, cx, cy + 1, span, R[0] - cx, clsR * 4 + clsL);
	return true;
}

// FUN_180012da0 — SW corner 3-point emit.
static void win_FUN_180012da0(SmootherPolygon &poly) {
	int cx = poly.cur_x, cy = poly.cur_y;
	if (cy == poly.cplane_h - 1 || cx == 0) return;
	GridDesc g = grid_of(poly);
	int in[2] = { cx, cy };
	int L[3], R[3];
	scan_d800(L, &g, in);
	scan_d0d0(R, &g, in);
	int spanX = (L[0] - cx) + 1;
	int spanY = (cy - R[1]) + 1;
	if ((spanX < 4 || spanY < 4) && (spanX < 2 || spanY < 2 ||
	    cp_b(&g, cx, cy + 1, 2) == 0)) {
		int len = (spanY < spanX) ? spanY : spanX;
		// Win FUN_180012da0: fVar8 = DAT_180022694 (= 0.5f);
		//                    if (iVar6 == 3) fVar8 = DAT_180022dd4 (= 0.125f);
		float fscale = (len == 3) ? W_STEP : 0.5f;
		float b = poly.smoothness_n;
		float wo = fscale * b * W_OUT_W;
		float wi = fscale * b * W_IN_W;
		win_FUN_1800104d0_append(poly, cx - 1, cy,     wo);
		win_FUN_1800104d0_append(poly, cx - 1, cy + 1, wi);
		win_FUN_1800104d0_append(poly, cx,     cy + 1, wo);
	}
}

// FUN_1800119a0 — 12時 variant with pre-walking (literal Win port).
//
// Win behavior (verified vs Ghidra decompile @ 0x1800119a0):
//   L-walk: diagonal SW (x-1, y+1) while R != 0, breaking on B != 0 (curr or
//     prev row), A == 0, or hitting limit min(cx, h-1-cy).  Pre-condition:
//     A@(cx, cy) != 0.  Tracks walked y (uVar17) for cls input.
//   R-walk: diagonal NE (x+1, y-1) while A != 0 && R != 0, breaking on B != 0
//     (curr or col-left), or hitting limit min(cy, w-1-cx).  Pre-condition:
//     B@(cx, cy) == 0 && B@(cx, cy-1) == 0.  Tracks walked y (uVar15).
//   Endpoint classes (P2 pattern): cls-L uses (L_x, L_y_walked),
//     cls-R uses (R_x, R_y_walked) — NOT cy.
//   Emits at (cx, cy - 1).  No fallback when span < 4 (returns 0).
//
// agentGG fix: prior Mac port omitted the R-walk entirely and used cy in
// place of walked-y for the endpoint classification.  Both bugs surface as
// faint diagonal lines at 45° tangent points of large circles.
static long win_FUN_1800119a0(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;

	// uVar7 = L's final x; uVar17 = L's final y; uVar18 = R's final x;
	// uVar15 = R's final y.  Initial values when no walking happens.
	int uVar7 = cx;     // L_x
	int uVar17 = cy;    // L_y
	int uVar18 = cx;    // R_x
	int uVar15 = cy;    // R_y

	// --- L-walk: diagonal SW while R-bit holds (matches FUN_1800115a0 L-walk) ---
	{
		int limit = (g.h - cy) - 1;
		if (cx < limit) limit = cx;
		// Win precond: A@(cx, cy) != 0.
		if (limit > 0 && cp_b(&g, cx, cy, 0) != 0) {
			int it_x = cx;        // uVar15 in Win
			int it_y_stored = cy;  // uVar19 init
			int iVar9 = 0;
			for (;;) {
				int local_res10 = it_x;          // save x before decrement
				int it_y_top = it_y_stored;      // uVar17 = (uint)uVar19
				int new_x = local_res10 - 1;     // uVar15 = local_res10 - 1
				int new_y = it_y_top + 1;        // uVar18 = uVar17 + 1
				it_x = new_x;
				uVar7 = local_res10;             // pre-advance x snapshot
				uVar17 = it_y_top;               // pre-advance y snapshot
				// Outer: R@(new_x, new_y) == 0 → break with pre-advance state.
				if (cp_b(&g, new_x, new_y, 1) == 0) break;
				// Inner B-checks: break with pre-advance state.
				if (cp_b(&g, new_x, new_y, 3) != 0) break;
				if (cp_b(&g, new_x, new_y - 1, 3) != 0) break;
				// Advance commit.
				uVar7 = new_x;
				uVar17 = new_y;
				// A@(new_x, new_y) == 0 → break with NEW state.
				if (cp_b(&g, new_x, new_y, 0) == 0) break;
				iVar9++;
				it_y_stored = new_y;
				if (limit <= iVar9) break;
			}
		}
	}

	// --- R-walk: diagonal NE while A != 0 && R != 0 (matches FUN_1800115a0 R-walk) ---
	{
		int limit = (g.w - cx) - 1;
		if (cy < limit) limit = cy;
		// Win precond: B@(cx, cy) == 0 && B@(cx, cy-1) == 0.
		if (limit > 0 && cp_b(&g, cx, cy, 3) == 0 &&
		    (cy == 0 || cp_b(&g, cx, cy - 1, 3) == 0)) {
			int it_y_in = cy - 1;     // uVar6 init = local_res18 - 1 = cy - 1
			int it_x_in = cx;          // uVar16 init = cx
			int iVar9 = 0;
			for (;;) {
				uVar15 = it_y_in;       // uVar15 = uVar6 (y-coord)
				int it_x = it_x_in;     // running x
				int new_x = it_x + 1;   // uVar18 = uVar16 + 1
				// Outer break: A@(new_x, uVar15)==0 or R@(new_x, uVar15)==0.
				// Post-fixup: uVar15 += 1; uVar18 = it_x.
				if (cp_b(&g, new_x, uVar15, 0) == 0) {
					uVar15 = uVar15 + 1; uVar18 = it_x; break;
				}
				if (cp_b(&g, new_x, uVar15, 1) == 0) {
					uVar15 = uVar15 + 1; uVar18 = it_x; break;
				}
				// Inner break (goto LAB_180011b55): no fixup.
				if (cp_b(&g, new_x, uVar15, 3) != 0) {
					uVar18 = new_x; break;
				}
				if (uVar15 >= 1 && cp_b(&g, new_x, uVar15 - 1, 3) != 0) {
					uVar18 = new_x; break;
				}
				iVar9++;
				it_y_in = uVar15 - 1;
				it_x_in = new_x;
				if (limit <= iVar9) {
					uVar18 = new_x; break;
				}
			}
		}
	}

	int span = (uVar18 - cx) + 1 + (cx - uVar7);
	if (span < 4) return 0;

	// Endpoint classes — Win uses (uVar7, uVar17) for L, (uVar18, uVar15) for R.
	// Both follow the P2 pattern (verified vs Ghidra: L gate is A@(L,L_y);
	// R gate is A@(R+1, R_y-1) | (R_y==0)).
	int clsL = endpoint_cls_left_P2(&g, uVar7, uVar17);
	int clsR = endpoint_cls_right_P2(&g, uVar18, uVar15);
	// 12時: vertex weight = wp[0] (local_res8) per Ghidra @0x1800119a0.
	append_weighted(poly, cx, cy - 1, span, cx - uVar7, clsL * 4 + clsR, 0);
	return 1;
}

// FUN_1800125c0 — 12時 variant of 122e0 (same scanners, different trapezoid).
static bool win_FUN_1800125c0(SmootherPolygon &poly) {
	GridDesc g = grid_of(poly);
	int cx = poly.cur_x, cy = poly.cur_y;
	int in[2] = { cx, cy };
	int L[2], R[2];
	scan_10d20(L, &g, in);
	scan_10ad0(R, &g, in);
	int span = cx + 1 + (R[0] - cx) - L[0];
	const bool trace_this_pixel =
	    (cx == g_olmsmoother2_trace_x && cy == g_olmsmoother2_trace_y);
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace 0125c0 pre L=(%d,%d) R=(%d,%d) span=%d\n",
		             L[0], L[1], R[0], R[1], span);
	}
	if (span < 4) return false;
	// Win: iStackX_14 / iStackX_1c (= L_y, R_y, NO +1) for 12時 NW-end variant.
	int clsL = endpoint_cls_left_P1(&g, L[0], L[1]);
	int clsR = endpoint_cls_right_P1(&g, R[0], R[1]);
	if (trace_this_pixel) {
		float wp[2];
		win_weight_pair(wp, span, R[0] - cx, clsR * 4 + clsL);
		float fscale = poly.extra_n * K_W025 + poly.smoothness_n;
		std::fprintf(stderr,
		             "trace 0125c0 emit ex=%d ey=%d offset=%d clsL=%d clsR=%d key=%d raw=(%.8f,%.8f) scaled=(%.8f,%.8f)\n",
		             cx, cy - 1, R[0] - cx, clsL, clsR, clsR * 4 + clsL,
		             wp[0], wp[1], wp[0] * fscale, wp[1] * fscale);
	}
	// Win FUN_1800125c0 calls FUN_180012850(.., uVar11=clsR, uVar8=clsL),
	// so the switch index = param_5 + param_4*4 = clsL + clsR*4 (NOT clsL*4+clsR).
	// 12時: vertex weight = wp[0] (local_res8) per Ghidra @0x1800125c0.
	append_weighted(poly, cx, cy - 1, span, R[0] - cx, clsR * 4 + clsL, 0);
	return true;
}

// FUN_180013140 — NW corner 3-point emit.
static void win_FUN_180013140(SmootherPolygon &poly) {
	int cx = poly.cur_x, cy = poly.cur_y;
	if (cy == poly.cplane_h - 1 || cx == 0) return;
	GridDesc g = grid_of(poly);
	int in[2] = { cx, cy };
	int L[3], R[3];
	scan_dbd0(L, &g, in);
	scan_d6a0(R, &g, in);
	int spanX = (L[0] - cx) + 1;
	int spanY = (R[1] - cy) + 1;
	// Win: byte at stride*cy + cx*4 - 1 = pixel (cx-1, cy) byte index 3 (B).
	if (poly.cur_x == 501 && poly.cur_y == 1055) {
		std::fprintf(stderr, "trace case0004: spanX=%d spanY=%d cp_b=%d\n", spanX, spanY, cp_b(&g, cx - 1, cy, 3));
	}
	if ((spanX < 4 || spanY < 4) && (spanX < 2 || spanY < 2 ||
	    cp_b(&g, cx - 1, cy, 3) == 0)) {
		int len = (spanY < spanX) ? spanY : spanX;
		// Win FUN_180013140: fVar8 = DAT_180022694 (= 0.5f);
		//                    if (iVar6 == 3) fVar8 = DAT_180022dd4 (= 0.125f);
		float fscale = (len == 3) ? W_STEP : 0.5f;
		if (cx != 0 && cy != 0) {
			float b = poly.smoothness_n;
			float wo = fscale * b * W_OUT_W;
			float wi = fscale * b * W_IN_W;
			win_FUN_1800104d0_append(poly, cx - 1, cy,     wo);
			win_FUN_1800104d0_append(poly, cx - 1, cy - 1, wi);
			win_FUN_1800104d0_append(poly, cx,     cy - 1, wo);
		}
	}
}

// FUN_1800132f0 — NE corner 3-point emit (emits (cx,cy-1)/(cx+1,cy-1)/(cx+1,cy)).
static void win_FUN_1800132f0(SmootherPolygon &poly) {
	int cy = poly.cur_y, cx = poly.cur_x;
	if (cy == 0 || cx == poly.cplane_w - 1) return;
	GridDesc g = grid_of(poly);
	int in[2] = { cx, cy };
	int L[3], R[3];
	scan_d520(L, &g, in);
	scan_da50(R, &g, in);
	int spanX = (cx - L[0]) + 1;
	int spanY = (R[1] - cy) + 1;
	// Win: byte at stride*cy + cx*4 + 6 = pixel (cx+1, cy) byte index 2 (G).
	if ((spanX < 4 || spanY < 4) && (spanX < 2 || spanY < 2 ||
	    cp_b(&g, cx + 1, cy, 2) == 0)) {
		int len = (spanY < spanX) ? (R[1] - cy) : (cx - L[0]);
		// Win FUN_1800132f0: fVar10 = DAT_180022694 (= 0.5f);
		//                    if (iVar8 == 2) fVar10 = DAT_180022dd4 (= 0.125f);
		float fscale = (len == 2) ? W_STEP : 0.5f;
		if (cx != poly.cplane_w - 1 && cy != 0) {
			float b = poly.smoothness_n;
			float wo = fscale * b * W_OUT_W;
			float wi = fscale * b * W_IN_W;
			win_FUN_1800104d0_append(poly, cx,     cy - 1, wo);
			win_FUN_1800104d0_append(poly, cx + 1, cy - 1, wi);
			win_FUN_1800104d0_append(poly, cx + 1, cy,     wo);
		}
	}
}

// ============================================================================
// LITERAL Win cardinal chain — 3 sibling directions (β/γ/δ): 9時/6時/3時 entries,
// dispatchers f8f0/fef0/1800101e0, 24 leaves, 6 predicates.
// All ported 1:1 from Ghidra decompile (verified 2026-04-27 session 4).
// ============================================================================

// FUN_18000cee0 — walk UP col x while A@(x,iy)!=0 && R@(x,iy)==0 && R@(x-1,iy)==0.
// Functionally identical to d0d0; Win has both due to inlining.  Returns (x, walked_y).
// Class probes: (A@(x, y-1), R@(x, y), R@(x-1, y)).
static void scan_cee0(int out[3], const GridDesc *g, const int in[2]) {
	int x = in[0], y0 = in[1];
	if (x < 0 || x >= g->w || y0 < 0 || y0 >= g->h) {
		out[0] = x; out[1] = y0; out[2] = 0; return;
	}
	int y = y0;
	if (y0 > 0) {
		while (cp_b(g, x, y, 0) != 0) {                    // A@(x,y)!=0
			if (cp_b(g, x, y, 1) != 0) break;               // R@(x,y)!=0
			if (x > 0 && cp_b(g, x - 1, y, 1) != 0) break;  // R@(x-1,y)!=0
			y--;
			if (y < 1) break;
		}
		if (cp_b(g, x, y, 0) == 0) y++;
	}
	bool p1 = (y > 0) && cp_b(g, x,     y - 1, 0) != 0;     // A@(x, y-1)
	bool p2 = cp_b(g, x,     y, 1) != 0;                     // R@(x, y)
	bool p3 = (x > 0) && cp_b(g, x - 1, y, 1) != 0;          // R@(x-1, y)
	bool p4 = (x > 0) && cp_b(g, x - 1, y, 3) != 0;         // B@(x-1, y)
	bool p5 = cp_b(g, x,     y, 2) != 0;                     // G@(x, y)
	out[0] = x; out[1] = y; out[2] = win_FUN_180010550(p1, p2, p3, p4, p5);
}

// --- 6 sibling predicates (β/γ/δ × 2 endpoints) ---

// FUN_18000e050 (β: right-vertical at p2[0]=x, p2[1]=y).
static int win_e050(const SmootherPolygon &poly, const int *p2) {
	if (p2[0] == poly.cplane_w - 1) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[0], y = p2[1];
	bool b_above_A = (y > 0) && base[(y - 1) * s + (x + 1) * 4 + 0] != 0;
	bool b_self_A  = base[y * s + (x + 1) * 4 + 0] != 0;
	bool b_self_R  = base[y * s + (x + 1) * 4 + 1] != 0;
	return (b_above_A ? 2 : 0) | (b_self_R ? 4 : 0) | (b_self_A ? 1 : 0);
}

// FUN_18000de10 (β2: uses p2[3]=x', p2[4]=y').
static int win_de10(const SmootherPolygon &poly, const int *p2) {
	if (p2[3] == poly.cplane_w - 1) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[3], y = p2[4];
	bool a_y_A      = base[y * s + (x + 1) * 4 + 0] != 0;
	bool a_y1_R     = (y + 1 < poly.cplane_h) && base[(y + 1) * s + (x + 1) * 4 + 1] != 0;
	bool a_y1_A     = (y + 1 < poly.cplane_h) && base[(y + 1) * s + (x + 1) * 4 + 0] != 0;
	return (a_y_A ? 1 : 0) | (a_y1_R ? 4 : 0) | (a_y1_A ? 2 : 0);
}

// FUN_18000e170 (γ: left-vertical at p2[0]=x, p2[1]=y).
static int win_e170(const SmootherPolygon &poly, const int *p2) {
	if (p2[0] == 0) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[0], y = p2[1];
	bool b1 = (y > 0) && base[(y - 1) * s + x * 4 + 0] != 0;     // A@(x, y-1)
	bool b2 = base[y * s + (x - 1) * 4 + 1] != 0;                // R@(x-1, y)
	bool b3 = base[y * s + x * 4 + 0] != 0;                      // A@(x, y)
	int c = (b1 ? 2 : 0) | (b2 ? 4 : 0) | (b3 ? 1 : 0);
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace e170 p2=(%d,%d,%d,%d,%d,%d) bits Axy-1=%d R x-1y=%d Axy=%d -> c=%d\n",
		             p2[0], p2[1], p2[2], p2[3], p2[4], p2[5],
		             b1 ? 1 : 0, b2 ? 1 : 0, b3 ? 1 : 0, c);
	}
	return c;
}

// FUN_18000df30 (γ2: uses p2[3]=x', p2[4]=y').
static int win_df30(const SmootherPolygon &poly, const int *p2) {
	if (p2[3] == 0) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[3], y = p2[4];
	bool b1 = base[y * s + x * 4 + 0] != 0;                                   // A@(x, y)
	bool b2 = (y + 1 < poly.cplane_h) && base[(y + 1) * s + (x - 1) * 4 + 1] != 0;  // R@(x-1, y+1)
	bool b3 = (y + 1 < poly.cplane_h) && base[(y + 1) * s + x * 4 + 0] != 0;  // A@(x, y+1)
	return (b1 ? 1 : 0) | (b2 ? 4 : 0) | (b3 ? 2 : 0);
}

// FUN_18000e200 (δ: bottom-horizontal at p2[0]=x, p2[1]=y).
static int win_e200(const SmootherPolygon &poly, const int *p2) {
	if (p2[1] == poly.cplane_h - 1) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[0], y = p2[1];
	bool b1 = (x > 0) && base[(y + 1) * s + (x - 1) * 4 + 1] != 0;  // R@(x-1, y+1)
	bool b2 = base[(y + 1) * s + x * 4 + 1] != 0;                    // R@(x, y+1)
	bool b3 = base[(y + 1) * s + x * 4 + 0] != 0;                    // A@(x, y+1)
	return (b1 ? 2 : 0) | (b2 ? 1 : 0) | (b3 ? 4 : 0);
}

// FUN_18000dfc0 (δ2: uses p2[3]=x', p2[4]=y').
static int win_dfc0(const SmootherPolygon &poly, const int *p2) {
	if (p2[4] == poly.cplane_h - 1) return 4;
	const uint8_t *base = poly.cplane_base;
	int s = poly.cplane_stride;
	int x = p2[3], y = p2[4];
	bool b1 = (x + 1 < poly.cplane_w) && base[(y + 1) * s + (x + 1) * 4 + 1] != 0;  // R@(x+1, y+1)
	bool b2 = base[(y + 1) * s + x * 4 + 1] != 0;                                    // R@(x, y+1)
	bool b3 = (x + 1 < poly.cplane_w) && base[(y + 1) * s + (x + 1) * 4 + 0] != 0;  // A@(x+1, y+1)
	return (b1 ? 2 : 0) | (b2 ? 1 : 0) | (b3 ? 4 : 0);
}

// --- Direction β leaves (used by FUN_18000f8f0 / 9時 entry) ---
// Templates: pred ∈ {e050, de10}, emit ∈ {e3a0, e290}.

static bool win_leaf_f450(SmootherPolygon &poly, const int *p2) {  // T1: e050 + e3a0
	int c = win_e050(poly, p2);
	if (c == 4) return false;
	return win_e3a0(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_ead0(SmootherPolygon &poly, const int *p2) {  // T2: e050 + da50/cee0 + e3a0
	int c = win_e050(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[0], p2[1] }; scan_da50(s, &g, in0);  // Win first scan: FUN_18000da50
	int span_end_y = s[1];
	int total_y = p2[4] - p2[1];
	int cur_span = span_end_y - p2[1];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	// AEX 0x18000eb56 initializes XMM6 to 1.0; the optional cce0 chase
	// below is the only path that reduces this scale to 0.5.
	float wsh  = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[0], y = p2[1];
		while (true) {
			int py = y - 1;
			wsh = K_HALF;
			if (x < 0 || x >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { x, py }; scan_cee0(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 1) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 4) break;
		}
	}
	float w = (float)(cur_span + 1) * fmul / (float)(total_y + 1);
	return win_e3a0(poly, p2, w, wsh);
}
static bool win_leaf_f740(SmootherPolygon &poly, const int *p2) {  // T3: e050 → e3a0
	// Win 0x18000f740: c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_e050(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e3a0(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_f310(SmootherPolygon &poly, const int *p2) {  // T4: de10 + e290
	int c = win_de10(poly, p2);
	if (c == 4) return false;
	return win_e290(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_f1d0(SmootherPolygon &poly, const int *p2, float p3) {  // T5: e050 + e3a0 (parameterized)
	int c = win_e050(poly, p2);
	if (c == 4) return false;
	return win_e3a0(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f090(SmootherPolygon &poly, const int *p2, float p3) {  // T6: de10 + e290 (parameterized)
	int c = win_de10(poly, p2);
	if (c == 4) return false;
	return win_e290(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f590(SmootherPolygon &poly, const int *p2) {  // T7: de10 → e290
	// Win 0x18000f590: c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_de10(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e290(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_e4b0(SmootherPolygon &poly, const int *p2) {  // T8: de10 + d3b0/d6a0 + e290
	int c = win_de10(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[3], p2[4] }; scan_d3b0(s, &g, in0);
	int span_y = p2[4] - s[1];
	int total = p2[4] - p2[1];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[3], y = p2[4];
		while (true) {
			int py = y + 1;
			wsh = K_HALF;
			if (x < 0 || x >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { x, py }; scan_d6a0(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 2) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 3) break;
		}
	}
	float w = (float)(span_y + 1) * fmul / (float)(total + 1);
	return win_e290(poly, p2, w, wsh);
}

// --- Direction γ leaves (FUN_18000fef0 / 6時 entry) — pred ∈ {e170, df30}, emit ∈ {e3a0, e290} ---
static bool win_leaf_f4f0(SmootherPolygon &poly, const int *p2) {
	int c = win_e170(poly, p2);
	if (c == 4) return false;
	return win_e3a0(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_edb0(SmootherPolygon &poly, const int *p2) {
	int c = win_e170(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[0], p2[1] }; scan_d6a0(s, &g, in0);
	int span = s[1] - p2[1];
	int total = p2[4] - p2[1];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[0], y = p2[1];
		while (true) {
			int py = y - 1;
			wsh = K_HALF;
			if (x < 0 || x >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { x, py }; scan_d3b0(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 2) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 3) break;
		}
	}
	float w = (float)(span + 1) * fmul / (float)(total + 1);
	return win_e3a0(poly, p2, w, wsh);
}
static bool win_leaf_f820(SmootherPolygon &poly, const int *p2) {
	// Win 0x18000f820 (γ T3 e170+e3a0): c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_e170(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e3a0(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_f3b0(SmootherPolygon &poly, const int *p2) {
	int c = win_df30(poly, p2);
	if (c == 4) return false;
	return win_e290(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_f270(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_e170(poly, p2);
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace f270 c=%d p3=%.8g extra_n=%.8g count_before=%d\n",
		             c, p3, poly.extra_n, poly.count);
	}
	if (c == 4) return false;
	if (g_olmsmoother2_leaf_diag_mode == 1) {
		if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
			std::fprintf(stderr, "trace f270 suppressed_by_diag=1 count_after=%d\n", poly.count);
		}
		return false;
	}
	bool emitted = win_e3a0(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
	if (poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y) {
		std::fprintf(stderr,
		             "trace f270 emitted=%d count_after=%d\n",
		             emitted ? 1 : 0, poly.count);
	}
	return emitted;
}
static bool win_leaf_f130(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_df30(poly, p2);
	if (c == 4) return false;
	return win_e290(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f670(SmootherPolygon &poly, const int *p2) {
	// Win 0x18000f670 (γ T7 df30+e290): c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_df30(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e290(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_e7c0(SmootherPolygon &poly, const int *p2) {
	int c = win_df30(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[3], p2[4] }; scan_cee0(s, &g, in0);
	int span = p2[4] - s[1];
	int total = p2[4] - p2[1];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[3], y = p2[4];
		while (true) {
			int py = y + 1;
			wsh = K_HALF;
			if (x < 0 || x >= poly.cplane_w || py < 0 || py >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { x, py }; scan_da50(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 1) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 4) break;
		}
	}
	float w = (float)(span + 1) * fmul / (float)(total + 1);
	return win_e290(poly, p2, w, wsh);
}

// --- Direction δ leaves (FUN_1800101e0 / 3時 entry) — pred ∈ {e200, dfc0}, emit ∈ {e430, e320} ---
static bool win_leaf_f540(SmootherPolygon &poly, const int *p2) {
	int c = win_e200(poly, p2);
	if (c == 4) return false;
	return win_e430(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_ef20(SmootherPolygon &poly, const int *p2) {
	int c = win_e200(poly, p2);
	const bool trace_this_pixel =
	    poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y;
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[0], p2[1] }; scan_d800(s, &g, in0);
	int span = s[0] - p2[0];
	int total = p2[3] - p2[0];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[0], y = p2[1];
		while (true) {
			int px = x - 1;
			wsh = K_HALF;
			if (px < 0 || px >= poly.cplane_w || y < 0 || y >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { px, y }; scan_d520(s2, &g, in2);
			wsh = K_ONE;
			if (trace_this_pixel) {
				std::fprintf(stderr,
				             "trace ef20 chase in=(%d,%d) out=(%d,%d,%d) scale=%.8g\n",
				             px, y, s2[0], s2[1], s2[2], wsh);
			}
			if (s2[2] == 2) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 3) break;
		}
	}
	float w = (float)(span + 1) * fmul / (float)(total + 1);
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace ef20 c=%d d800=(%d,%d,%d) span=%d total=%d fmul=%.8g scale=%.8g weight=%.8g\n",
		             c, s[0], s[1], s[2], span, total, fmul, wsh, w);
	}
	return win_e430(poly, p2, w, wsh);
}
static bool win_leaf_f890(SmootherPolygon &poly, const int *p2) {
	// Win 0x18000f890 (δ T3 e200+e430): c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_e200(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e430(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_f400(SmootherPolygon &poly, const int *p2) {
	int c = win_dfc0(poly, p2);
	if (c == 4) return false;
	return win_e320(poly, p2, poly.extra_n * K_HALF + K_HALF, K_ONE);
}
static bool win_leaf_f2c0(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_e200(poly, p2);
	if (c == 4) return false;
	return win_e430(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f180(SmootherPolygon &poly, const int *p2, float p3) {
	int c = win_dfc0(poly, p2);
	if (c == 4) return false;
	return win_e320(poly, p2, poly.extra_n * K_DD8 + K_HALF, p3);
}
static bool win_leaf_f6e0(SmootherPolygon &poly, const int *p2) {
	// Win 0x18000f6e0 (δ T7 dfc0+e320): c∈{2,6}→1.0, c∈{3,7}→0.5, else no emit.
	int c = win_dfc0(poly, p2);
	float scale;
	if (c == 2 || c == 6) scale = K_ONE;
	else if (c == 3 || c == 7) scale = K_HALF;
	else return false;
	return win_e320(poly, p2, poly.extra_n * K_DD8 + K_HALF, scale);
}
static bool win_leaf_e950(SmootherPolygon &poly, const int *p2) {
	int c = win_dfc0(poly, p2);
	if (((c - 1) & ~6) != 0 || c == 5) return false;
	GridDesc g = grid_of(poly);
	int s[3]; int in0[2] = { p2[3], p2[4] }; scan_d230(s, &g, in0);
	int span = p2[3] - s[0];
	int total = p2[3] - p2[0];
	float fmul = poly.extra_n * K_DD8 + K_HALF;
	float wsh = K_ONE;
	if (((c - 3) & ~4) == 0) {
		int x = p2[3], y = p2[4];
		while (true) {
			int px = x + 1;
			wsh = K_HALF;
			if (px < 0 || px >= poly.cplane_w || y < 0 || y >= poly.cplane_h) break;
			int s2[3]; int in2[2] = { px, y }; scan_dbd0(s2, &g, in2);
			wsh = K_ONE;
			if (s2[2] == 1) break;
			wsh = K_HALF;
			x = s2[0]; y = s2[1];
			if (s2[2] != 4) break;
		}
	}
	float w = (float)(span + 1) * fmul / (float)(total + 1);
	return win_e320(poly, p2, w, wsh);
}

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

// Stage 2: per-sample luminance-diff weight (BT.709).
static inline float luma_bt709(const FPix &px) {
	return 0.2126f * px.r + 0.7152f * px.g + 0.0722f * px.b;
}

static void weight_samples(SmootherPolygon &poly, const FPix &center) {
	float c_lum = luma_bt709(center);
	for (int i = 0; i < poly.count; ++i) {
		PolySample &s = poly.samples[i];
		FPix spx = { s.r, s.g, s.b, s.a };
		float s_lum = luma_bt709(spx);
		float d = s_lum - c_lum;
		if (d < 0) d = -d;
		// Similarity ∈ [0,1]; identical luma → 1, very different → ~0.
		float similarity = 1.0f - d;
		if (similarity < 0.0f) similarity = 0.0f;
		// Samples similar to center get full coverage; very different samples
		// get reduced coverage.  This avoids halos on strong-contrast edges.
		s.w *= (0.5f + 0.5f * similarity);
	}
}

// Stage 3: gamma decode + premultiply.
// Generic pow helper retained for reference / future custom-LUT branches.
__attribute__((unused))
static inline void pow_rgb(FPix &px, float exponent) {
	if (px.r > 0.0f) px.r = powf(px.r, exponent); else px.r = 0.0f;
	if (px.g > 0.0f) px.g = powf(px.g, exponent); else px.g = 0.0f;
	if (px.b > 0.0f) px.b = powf(px.b, exponent); else px.b = 0.0f;
}

// ============================================================================
// FUN_18000bb10 — adaptive gamma value computation (LITERAL PORT).
//
// Win signature (decompiled):
//   float* FUN_18000bb10(float *out_pair,        // [0]=float result, [1]=apply byte
//                        float *gctx,            // gamma config struct (param_5+10)
//                          gctx[0]=input gamma value (float)
//                          gctx[1]=curve_idx (int reinterpreted as float)
//                          (char)gctx[6]=mode byte: 1/2/3 (matches gamma_mode UI)
//                        float *center_rgba,     // 4-float center pixel
//                        ulonglong *poly_pair,   // [0]=count, [1]=ptr to samples
//                        ...)
//
// Mode 1 (passthrough):  out = gctx[0],   apply=1
// Mode 2 (luma adapt):
//   t = (1/N) * sum_i( s.w * luma709(s.rgb) + (1 - s.w) * luma709(center.rgb) )
//   t' = curve(t, curve_idx)            // 6 curves indexed by gctx[1]
//   out = (1 - t') * gctx[0] + t'       // blend toward 1.0
//   apply = 1
// Mode 3 (key-test):     if any sample matches key list, apply=1, out=gctx[0]
//                        else apply=0
// Default:               apply = 0
//
// Curve table (param_2[1] reinterpret_cast<int>):
//   1: pow2-in       t = t*t
//   2: pow2-out      t = 1 - (1-t)^2
//   3: pow3-in       t = t*t*t
//   4: pow3-out      t = 1 - (1-t)^3
//   5: smoothstep    t = (3 - 2t) * t * t
//   6: smootherstep  t = ((6t - 15)*t + 10) * t^3
//
// The constants 3/6/10/15 are DAT_180022dc0/dc4/dc8/dcc respectively.
// Luma weights at DAT_180022db4/db8/dbc are Rec.709 (B=0.0722, R=0.2126, G=0.7152).
// ============================================================================

// Bb10 curve dispatch.  Returns t' given raw t and curve index (1..6).
static inline float win_FUN_18000bb10_curve(float t, int curve_idx) {
	switch (curve_idx) {
	case 1:  return t * t;                                   // pow2-in
	case 2: { float u = K_ONE - t; return K_ONE - u * u; }   // pow2-out
	case 3:  return t * t * t;                               // pow3-in
	case 4: { float u = K_ONE - t; return K_ONE - u * u * u; } // pow3-out
	case 5:  return (3.0f - (t + t)) * t * t;                // smoothstep
	case 6:  return ((t * 6.0f - 15.0f) * t + 10.0f) * (t * t * t); // smootherstep
	default: return t;
	}
}

// Output-path sRGB encoder used by FUN_18000a9c0's gamma-color test.
static inline double win_FUN_180004d70_literal(double v);

// Returns the per-pixel adaptive gamma exponent.  out_apply=true means
// "apply gamma decode/encode for this pixel" (i.e. mode 1, 2, or 3 + match).
// gamma_in is the configured gamma (p.gamma_value); curve_idx selects easing.
static float win_FUN_18000bb10_adaptive_gamma(const FPix &center,
                                              const SmootherPolygon &poly,
                                              const SMParams &p,
                                              int curve_idx,
                                              bool &out_apply)
{
	const int win_gamma_mode =
		(p.gamma_mode == GAMMA_ALL_COLORS)  ? 1 :
		(p.gamma_mode == GAMMA_COLORS_ONLY) ? 3 : 0;
	const float gamma_in = p.gamma_value;

	// Win internal mode 1 — apply to all colors. UI "All Colors" maps here.
	if (win_gamma_mode == 1) {
		out_apply = true;
		return gamma_in;
	}

	// Win internal mode 2 — luma-adaptive blend. The current AE UI does not
	// expose this mode directly, but keep the literal body for completeness.
	if (win_gamma_mode == 2) {
		const float c_lum = luma_bt709(center);
		float sum = 0.0f;
		for (int i = 0; i < poly.count; ++i) {
			const PolyVertex &s = poly.samples[i];
			FPix spx = { s.r, s.g, s.b, s.a };
			float s_lum = luma_bt709(spx);
			sum += s.w * s_lum + (K_ONE - s.w) * c_lum;
		}
		float t = (poly.count > 0) ? (sum / (float)poly.count) : 0.0f;
		t = win_FUN_18000bb10_curve(t, curve_idx);
		out_apply = true;
		return (K_ONE - t) * gamma_in + t;
	}

	// Win internal mode 3 — key-color test against the Gamma Color list.
	// UI "Gamma Colors" maps here. FUN_18000a9c0 compares RGB only using
	// DAT_18002268c; only the zero-valued internal config uses output transfer.
	if (win_gamma_mode == 3 && p.num_gamma_colors > 0) {
		const bool trace_this_pixel =
		    poly.cur_x == g_olmsmoother2_trace_x && poly.cur_y == g_olmsmoother2_trace_y;
		auto matches_gamma_color = [&](float r, float g, float b) -> bool {
			// FUN_18000cce0 receives the setup struct at +8. Its low 32-bit
			// field is the internal version flag: v1=1, v2=0. a9c0 applies the
			// output transfer when that flag is zero, so UI v2 must re-encode.
			if (p.version != SMOOTHER_V1) {
				r = (float)win_FUN_180004d70_literal(r);
				g = (float)win_FUN_180004d70_literal(g);
				b = (float)win_FUN_180004d70_literal(b);
			}
			const int n = std::min(p.num_gamma_colors, NUM_GAMMA_COLORS);
			for (int i = 0; i < n; ++i) {
				const PF_PixelFloat &key = p.gamma_colors[i];
				if (trace_this_pixel) {
					std::fprintf(stderr,
					             "trace a9c0 candidate=(%.8g,%.8g,%.8g) key[%d]=(%.8g,%.8g,%.8g)\n",
					             r, g, b, i, key.red, key.green, key.blue);
				}
				if (fabs_bits(r - key.red)   < K_COLOR_TOL &&
				    fabs_bits(g - key.green) < K_COLOR_TOL &&
				    fabs_bits(b - key.blue)  < K_COLOR_TOL) {
					return true;
				}
			}
			return false;
		};
		bool match = matches_gamma_color(center.r, center.g, center.b);
		for (int i = 0; !match && i < poly.count; ++i) {
			const PolySample &s = poly.samples[i];
			match = matches_gamma_color(s.r, s.g, s.b);
		}
		out_apply = match;
		return gamma_in;
	}
	out_apply = false;
	return gamma_in;
}

// LITERAL port of FUN_18000c0d0:
//   if (apply_byte): pow(rgb, 1/gamma) on center AND each sample
//   if (center.a != 1): center.rgb *= center.a   (premul, unconditional)
//   for each sample: if (s.a != 1): s.rgb *= s.a (premul)
static void gamma_decode_premul(FPix &center, SmootherPolygon &poly,
                                bool gamma_enable, float gamma_value)
{
	if (gamma_enable && gamma_value > 0.0f) {
		double e = 1.0 / (double)gamma_value;
		center.r = (float)pow((double)center.r, e);
		center.g = (float)pow((double)center.g, e);
		center.b = (float)pow((double)center.b, e);
		for (int i = 0; i < poly.count; ++i) {
			poly.samples[i].r = (float)pow((double)poly.samples[i].r, e);
			poly.samples[i].g = (float)pow((double)poly.samples[i].g, e);
			poly.samples[i].b = (float)pow((double)poly.samples[i].b, e);
		}
	}
	if (center.a != 1.0f) {
		center.r *= center.a;
		center.g *= center.a;
		center.b *= center.a;
	}
	for (int i = 0; i < poly.count; ++i) {
		PolySample &s = poly.samples[i];
		if (s.a != 1.0f) { s.r *= s.a; s.g *= s.a; s.b *= s.a; }
	}
}

// Stage 4: accumulate weighted blend.
static void composite(FPix &out, const FPix &center, const SmootherPolygon &poly) {
	if (poly.count == 0) { out = center; return; }
	float W = 0.0f;
	for (int i = 0; i < poly.count; ++i) W += poly.samples[i].w;
	if (W < 0.0f) W = 0.0f;
	if (W > 1.0f) W = 1.0f;
	float blend = 1.0f - W;
	out.r = blend * center.r;
	out.g = blend * center.g;
	out.b = blend * center.b;
	out.a = blend * center.a;
	for (int i = 0; i < poly.count; ++i) {
		const PolySample &s = poly.samples[i];
		out.r += s.w * s.r;
		out.g += s.w * s.g;
		out.b += s.w * s.b;
		out.a += s.w * s.a;
	}
}

// Stage 5: post unpremul + gamma encode + clamp.
// Forward decl — literal definition lives further below in the encoder block.
static inline double win_FUN_180004d70_literal(double v);

// LITERAL port of FUN_18000b120:
//   if (a != 0 && a != 1): rgb /= a       (unpremul)
//   if (apply_byte): pow(rgb, gamma)      (inverse of c0d0's pow)
//   clamp each channel separately to [0,1]
static void post_unpremul_gamma(FPix &px, bool gamma_enable, float gamma_value) {
	float a = px.a;
	if (a != 0.0f && a != 1.0f) {
		// FUN_18000b120 uses three scalar DIVSS instructions. Computing one
		// reciprocal and multiplying shifts the float32 rounding point.
		px.r /= a; px.g /= a; px.b /= a;
	}
	if (gamma_enable && gamma_value > 0.0f) {
		double e = (double)gamma_value;
		px.r = (float)pow((double)px.r, e);
		px.g = (float)pow((double)px.g, e);
		px.b = (float)pow((double)px.b, e);
	}
	if (px.r < 0.0f) px.r = 0.0f; else if (px.r > 1.0f) px.r = 1.0f;
	if (px.g < 0.0f) px.g = 0.0f; else if (px.g > 1.0f) px.g = 1.0f;
	if (px.b < 0.0f) px.b = 0.0f; else if (px.b > 1.0f) px.b = 1.0f;
	if (px.a < 0.0f) px.a = 0.0f; else if (px.a > 1.0f) px.a = 1.0f;
}

// FUN_18000cce0 — per-pixel orchestrator.
static void win_FUN_18000cce0_orchestrate(FPix &out_pixel,
                                          const FPlane &plane_in,
                                          const FPlane & /*plane_out*/,
                                          int x, int y,
                                          const SMParams &p)
{
	const int w = p.w;
	const int h = p.h;

	FPix center = fplane_fetch(plane_in, x, y, w, h);
	SmootherPolygon poly;
	const bool trace_this_pixel =
	    (x == g_olmsmoother2_trace_x && y == g_olmsmoother2_trace_y);
	build_polygon(poly, plane_in, x, y, p);
	if (g_olmsmoother2_writer_frame_probe.json_path &&
	    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
		g_olmsmoother2_writer_frame_probe.center = center;
		g_olmsmoother2_writer_frame_probe.polygon = poly;
	}

	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_entry x=%d y=%d center=%.8f,%.8f,%.8f,%.8f poly_count=%d\n",
		             x, y, center.r, center.g, center.b, center.a, poly.count);
		for (int i = 0; i < poly.count; ++i) {
			const PolySample &s = poly.samples[i];
			std::fprintf(stderr,
			             "trace cce0_poly[%d]=%.8f,%.8f,%.8f,%.8f w=%.8f\n",
			             i, s.r, s.g, s.b, s.a, s.w);
		}
	}

	if (poly.count == 0) {
		out_pixel = center;
		if (g_olmsmoother2_writer_frame_probe.json_path &&
		    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
			g_olmsmoother2_writer_frame_probe.cce0 = out_pixel;
			g_olmsmoother2_writer_frame_probe.captured = true;
		}
		if (trace_this_pixel) {
			std::fprintf(stderr,
			             "trace cce0_exit_passthrough out=%.8f,%.8f,%.8f,%.8f\n",
			             out_pixel.r, out_pixel.g, out_pixel.b, out_pixel.a);
		}
		return;
	}

	// Stage 2: per-sample weight via luminance difference.
	// (Session B heuristic — Win's dispatch doesn't include this.  Disabled
	// until we can verify AA visibility, then re-evaluate.)
	// weight_samples(poly, center);
	(void)&weight_samples;  // silence -Wunused-function

	// Stage 3a: FUN_18000bb10 — compute the per-pixel adaptive gamma exponent.
	// Win passes bb10's float output (gated by an apply byte) into FUN_18000c0d0
	// which performs pow(rgb, 1/gamma).  We mirror that exactly: bb10 picks the
	// effective gamma per pixel (passthrough / luma-blend / key-gated), and the
	// result drives the existing gamma_decode_premul / post_unpremul_gamma pair.
	//
	// curve_idx source is unverified — Win reads it from the gamma config struct
	// at param_5+0x2C.  Conservative mapping: smoothstep (5) when EXTRA_SMOOTH
	// is unused (raw=0), otherwise EXTRA_SMOOTH_RAW % 6 + 1 to span all 6 curves.
	int curve_idx = (p.extra_smooth_raw > 0) ? ((p.extra_smooth_raw % 6) + 1) : 5;
	if (g_olmsmoother2_curve_idx_override >= 0) {
		curve_idx = g_olmsmoother2_curve_idx_override;
	}
	bool bb10_apply = false;
	float adaptive_gamma = win_FUN_18000bb10_adaptive_gamma(
		center, poly, p, curve_idx, bb10_apply);

	bool gamma_enable = bb10_apply && (adaptive_gamma > 0.0f);
	FPix working = center;
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_bb10 apply=%d gamma=%.8f curve=%d\n",
		             bb10_apply ? 1 : 0, adaptive_gamma, curve_idx);
	}
	gamma_decode_premul(working, poly, gamma_enable, adaptive_gamma);
	if (g_olmsmoother2_writer_frame_probe.json_path &&
	    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
		g_olmsmoother2_writer_frame_probe.bb10_apply = bb10_apply;
		g_olmsmoother2_writer_frame_probe.gamma_enable = gamma_enable;
		g_olmsmoother2_writer_frame_probe.adaptive_gamma = adaptive_gamma;
		g_olmsmoother2_writer_frame_probe.after_c0d0 = working;
	}
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_after_c0d0 center=%.8f,%.8f,%.8f,%.8f\n",
		             working.r, working.g, working.b, working.a);
		for (int i = 0; i < poly.count; ++i) {
			const PolySample &s = poly.samples[i];
			std::fprintf(stderr,
			             "trace cce0_after_c0d0_poly[%d]=%.8f,%.8f,%.8f,%.8f w=%.8f\n",
			             i, s.r, s.g, s.b, s.a, s.w);
		}
	}

	// Stage 4: composite.
	FPix accum;
	composite(accum, working, poly);
	if (g_olmsmoother2_writer_frame_probe.json_path &&
	    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
		g_olmsmoother2_writer_frame_probe.after_ab00 = accum;
	}
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_after_ab00 accum=%.8f,%.8f,%.8f,%.8f\n",
		             accum.r, accum.g, accum.b, accum.a);
	}

	// Stage 5: post unpremul + gamma encode + clamp.
	post_unpremul_gamma(accum, gamma_enable, adaptive_gamma);
	if (trace_this_pixel) {
		std::fprintf(stderr,
		             "trace cce0_after_b120 out=%.8f,%.8f,%.8f,%.8f\n",
		             accum.r, accum.g, accum.b, accum.a);
	}

	out_pixel = accum;
	if (g_olmsmoother2_writer_frame_probe.json_path &&
	    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
		g_olmsmoother2_writer_frame_probe.cce0 = out_pixel;
		g_olmsmoother2_writer_frame_probe.captured = true;
	}
}

// ============================================================================
// Output-path sRGB encoder — LITERAL PORT of FUN_180004d70 (sRGB OETF,
// linear -> sRGB) and stub for FUN_180004c30 (user LUT lookup).
// FUN_180002ba0 above does sRGB DECODE at frame start; this one ENCODES at
// write-back, so the net effect is linear-space processing round-tripped
// back to sRGB for display.
// ============================================================================

// FUN_180004d70 bits:
//   v <= 0                   -> 0
//   v >= 1                   -> 1
//   v < 0.003131 (S_BREAK)   -> v * 12.92
//   else                     -> pow(v, 1/2.4) * 1.055 - 0.055
static inline double win_FUN_180004d70_literal(double v)
{
	if (v <= 0.0) return 0.0;
	if (v >= S_ONE) return S_ONE;
	if (v < S_BREAK) return v * S_1292;
	return pow(v, S_INV24) * S_1055 - S_OFFSET2;
}

static void OLMSmoother2WriteWriterFrameProbe(bool apply_inverse_gamma, bool keep_premul)
{
	WriterFrameProbe &probe = g_olmsmoother2_writer_frame_probe;
	if (!probe.json_path || !probe.captured) return;
	FPix px = probe.cce0;
	float r = px.r, g = px.g, b = px.b, a = px.a;
	if (apply_inverse_gamma) {
		r = (float)win_FUN_180004d70_literal((double)r);
		g = (float)win_FUN_180004d70_literal((double)g);
		b = (float)win_FUN_180004d70_literal((double)b);
	}
	if (keep_premul && a != K_ONE) {
		r *= a; g *= a; b *= a;
	}
	probe.expected[0] = clamp8(a);
	probe.expected[1] = clamp8(r);
	probe.expected[2] = clamp8(g);
	probe.expected[3] = clamp8(b);
	FILE *fp = std::fopen(probe.json_path, "w");
	if (!fp) return;
	std::fprintf(fp, "{\"x\":%d,\"y\":%d,\"bb10_apply\":%s,\"gamma_enable\":%s,\"adaptive_gamma\":%.9g,"
	             "\"center_rgba_u32\":[%u,%u,%u,%u],\"after_c0d0_rgba_u32\":[%u,%u,%u,%u],"
	             "\"after_ab00_rgba_u32\":[%u,%u,%u,%u],\"cce0_rgba\":[%.9g,%.9g,%.9g,%.9g],"
	             "\"cce0_rgba_u32\":[%u,%u,%u,%u],\"polygon_count\":%d,\"polygon\":[",
	             probe.x, probe.y, probe.bb10_apply ? "true" : "false",
	             probe.gamma_enable ? "true" : "false", probe.adaptive_gamma,
	             olmsmoother2_f32_u32(probe.center.r), olmsmoother2_f32_u32(probe.center.g),
	             olmsmoother2_f32_u32(probe.center.b), olmsmoother2_f32_u32(probe.center.a),
	             olmsmoother2_f32_u32(probe.after_c0d0.r), olmsmoother2_f32_u32(probe.after_c0d0.g),
	             olmsmoother2_f32_u32(probe.after_c0d0.b), olmsmoother2_f32_u32(probe.after_c0d0.a),
	             olmsmoother2_f32_u32(probe.after_ab00.r), olmsmoother2_f32_u32(probe.after_ab00.g),
	             olmsmoother2_f32_u32(probe.after_ab00.b), olmsmoother2_f32_u32(probe.after_ab00.a),
	             probe.cce0.r, probe.cce0.g, probe.cce0.b, probe.cce0.a,
	             olmsmoother2_f32_u32(probe.cce0.r), olmsmoother2_f32_u32(probe.cce0.g),
	             olmsmoother2_f32_u32(probe.cce0.b), olmsmoother2_f32_u32(probe.cce0.a),
	             probe.polygon.count);
	for (int i = 0; i < probe.polygon.count; ++i) {
		const PolyVertex &v = probe.polygon.samples[i];
		if (i) std::fputc(',', fp);
		std::fprintf(fp, "{\"rgba_u32\":[%u,%u,%u,%u],\"weight_u32\":%u}",
		             olmsmoother2_f32_u32(v.r), olmsmoother2_f32_u32(v.g),
		             olmsmoother2_f32_u32(v.b), olmsmoother2_f32_u32(v.a),
		             olmsmoother2_f32_u32(v.w));
	}
	const bool equal = std::memcmp(probe.expected, probe.actual, sizeof(probe.expected)) == 0;
	std::fprintf(fp, "],\"expected_pf8_argb_memory\":[%u,%u,%u,%u],\"actual_pf8_argb_memory\":[%u,%u,%u,%u],\"invariant\":\"cce0_to_pf8_writer_bytes_equal\",\"writer_bytes_equal\":%s}\n",
	             probe.expected[0], probe.expected[1], probe.expected[2], probe.expected[3],
	             probe.actual[0], probe.actual[1], probe.actual[2], probe.actual[3],
	             equal ? "true" : "false");
	std::fclose(fp);
}

// FUN_180004c30 — LUT-based inverse via linear interpolation over a user LUT.
// We don't have a runtime LUT in Session B (gamma_ctx == null always), so
// this is a placeholder.  __attribute__((unused)) silences -Wunused-function.
__attribute__((unused))
static inline float win_FUN_180004c30_lut(float v) {
	if (v <= 0) return 0.0f;
	if (v >= 1) return 1.0f;
	return v; // identity until LUT infra is added
}

// ============================================================================
// Core render path
// ============================================================================
template<typename P>
static PF_Err
RenderBits(PF_InData *in_data, PF_ParamDef *params[],
           PF_LayerDef *input, PF_LayerDef *output)
{
	PF_Err err = PF_Err_NONE;
	OLMSmoother2ConfigureTracePixelFromEnvironment();

	SMParams p; AEFX_CLR_STRUCT(p);
	ERR(FetchParams(in_data, params, &p));
	if (err) return err;

	const int32_t w = output->width;
	const int32_t h = output->height;
	p.w = w; p.h = h;

	// Allocate float scratch (matches Win FUN_180002600 copy target layout).
	std::vector<FPix> scratch((size_t)w * (size_t)h);

	// Stage: load input AE layer into float scratch (logical equivalent of FUN_180002600 copy).
	for (int32_t y = 0; y < h; ++y) {
		const P *row = (const P *)((char *)input->data + (size_t)y * input->rowbytes);
		FPix   *dst  = scratch.data() + (size_t)y * w;
		for (int32_t x = 0; x < w; ++x) {
			float a, r, g, b;
			load_rgba(&row[x], a, r, g, b);
			if (g_olmsmoother2_force_input_premultiply) {
				diagnostic_premultiply_input(&row[x], a, r, g, b);
			}
			dst[x].r = r; dst[x].g = g; dst[x].b = b; dst[x].a = a;
		}
	}
	const std::vector<FPix> scratch_pre_setup = scratch;

	// FUN_180002e90 gates unpremultiply on byte [render params + 0x18].
	// FUN_180005180 passes setter_base + 8 as the render params pointer, so
	// this is setter byte +0x20. FUN_180004e10 initializes that field to zero
	// and never ties it to Enable Color Key. The current Windows AEX therefore
	// keeps premultiplied 8bpc input here; treating enable_key as this gate
	// changes the class plane and cardinal descriptors in legacy key cases.
	// FUN_180002930 guard (Win FUN_180002e90 @ 0x180002e90):
	//   `*(longlong *)(param_4 + 0x60) != 0`
	// ASM at FUN_180004e10 shows one way to populate this active palette:
	//   - Enable Color Key + Invert Color Key stores the Color Key at the inline
	//     one-entry palette and points +0x68/+0x70 at it.
	// Gamma Correction == COLORS_ONLY stores its list in the separate gamma
	// config at +0x98/+0xe8 and is consumed later by FUN_18000bb10/a9c0, not by
	// this frame-level alpha filter.
	PF_PixelFloat active_palette[NUM_GAMMA_COLORS];
	const PF_PixelFloat *active_palette_ptr = nullptr;
	int active_palette_count = 0;
	if (p.enable_key && p.invert_key) {
		active_palette[0] = p.key_color;
		active_palette_ptr = active_palette;
		active_palette_count = 1;
	}
	if (active_palette_ptr && active_palette_count > 0) {
		win_FUN_180002930_palette_filter(scratch.data(), w, h,
		                                 active_palette_ptr, active_palette_count);
	}
	if (p.enable_key && !p.invert_key) {
		win_FUN_180002a70_invert_key(scratch.data(), w, h, p.key_color);
	}
	const std::vector<FPix> scratch_pre_gamma = scratch;
	// FUN_180002a70 is the non-invert scalar-key path. The asm frame gate is
	// byte [SMParams+0x14], inside the scalar key-color storage written only by
	// FUN_180004e10's non-invert branch; do not wire it to the UI invert boolean.
	// FUN_180002ba0 guard: "*param_4 != 1" — ASM-verified that *param_4 reads
	// SMParams offset +8, which FUN_180004e10 sets to (version_popup == 1) ? 1 : 0.
	// So Win runs sRGB decode whenever version != v1, INDEPENDENT of gamma_mode.
	// FUN_180002ba0 itself has no internal gamma_mode gating — it always decodes.
	// (CC fix: previously gated on gamma_mode != GAMMA_NONE, which skipped the
	// decode in the default v2/None UI state and produced a 1px sRGB-roundtrip
	// ring vs the Win reference.)
	if (p.version != SMOOTHER_V1) {
		win_FUN_180002ba0_gamma_encode(scratch.data(), w, h, p);
	}

	// Build an FPlane alias for the per-pixel orchestrator.
	// Win treats input & output as distinct planes; here the input plane holds
	// the post-frame-setup values and we write into the output plane to avoid
	// in-place feedback.  Allocate an output scratch.
	std::vector<FPix> scratch_out((size_t)w * (size_t)h);

	FPix *sample_base = scratch.data();
	const FPix *class_base = scratch.data();
	if (g_olmsmoother2_plane_split_diag_mode == 1) {
		sample_base = const_cast<FPix *>(scratch_pre_setup.data());
	} else if (g_olmsmoother2_plane_split_diag_mode == 2) {
		class_base = scratch_pre_setup.data();
	} else if (g_olmsmoother2_plane_split_diag_mode == 3) {
		sample_base = const_cast<FPix *>(scratch_pre_gamma.data());
	} else if (g_olmsmoother2_plane_split_diag_mode == 4) {
		class_base = scratch_pre_gamma.data();
	}

	FPlane plane_in  = { sample_base,        (size_t)w * sizeof(FPix), 0 };
	FPlane plane_out = { scratch_out.data(), (size_t)w * sizeof(FPix), 0 };

	// Frame-level u8 class plane — LITERAL port of FUN_18000ac00 / FUN_18000ae10.
	// Per-pixel 4 bytes encoding color-edges to neighbors:
	//   byte[0] = (color_dist(self, LEFT)      >= threshold) ? 0xFF : 0
	//   byte[1] = (color_dist(self, TOP)       >= threshold) ? 0xFF : 0
	//   byte[2] = (color_dist(self, TOP-LEFT)  >= threshold) ? 0xFF : 0
	//   byte[3] = (color_dist(self, TOP-RIGHT) >= threshold) ? 0xFF : 0
	// Win threshold (FUN_18000ae10):
	//   fVar15 = (float)*(int *)(param_5 + 0x1c) / DAT_180022dd0;  // = 100.0
	//   fVar15 = fVar15 + DAT_180022db0;                            // = 0.001
	// Param +0x1c is a single-byte flag (init 0, set to 1 when key_color exists
	// AND invert_key is off — i.e. a single-key list is active).  As an int the
	// upper 3 bytes are zero, so the value is 0 or 1, NOT smoothness.  Threshold
	// is therefore essentially 0.001 (no key) or 0.011 (key on) — a tiny epsilon
	// that lights up the class plane on virtually any visible color edge.
	// Earlier versions of this port used smoothness_raw/100 here, which made the
	// threshold ≥ 0.5 at any non-trivial smoothness — class plane went all-zero,
	// every pixel fell into idx=0xff (default in the 222-case dispatch), poly
	// stayed at count=0, composite returned the center sample, and the effect
	// was bypassed end-to-end.  Restoring the literal Win formula:
	// color_dist (FUN_18000b2b0):
	//   if both alpha == 0 → 0
	//   else max(|dR|, |dG|, |dB|, |dY|) + |dA|, where Y = Rec.709 luma.
	const float WIN_LUMA_R = 0.2126f;  // DAT_180022db8
	const float WIN_LUMA_G = 0.7152f;  // DAT_180022dbc
	const float WIN_LUMA_B = 0.0722f;  // DAT_180022db4
	const float WIN_THRESH_BIAS = 0.001f;  // DAT_180022db0
	auto color_dist = [&](const FPix &a, const FPix &b) -> float {
		if (a.a == 0.0f && b.a == 0.0f) return 0.0f;
		float dr = std::fabs(a.r - b.r);
		float dg = std::fabs(a.g - b.g);
		float db = std::fabs(a.b - b.b);
		float la = a.r * WIN_LUMA_R + a.g * WIN_LUMA_G + a.b * WIN_LUMA_B;
		float lb = b.r * WIN_LUMA_R + b.g * WIN_LUMA_G + b.b * WIN_LUMA_B;
		float dy = std::fabs(la - lb);
		float maxv = std::max(std::max(dr, dg), std::max(db, dy));
		return maxv + std::fabs(a.a - b.a);
	};
	// Class-plane threshold = (float)*(int *)(param_5 + 0x1c) / 100.0 + 0.001.
	// 2026-06-15 grid finding: in the no-key path, the render-time SMParams
	// pointer is the setter struct base + 8 (the setter stores a pointer at +0
	// and the scalar params follow).  Under that shift FUN_18000ae10's
	// render +0x1c read is the setter's +0x24 = SMOOTH RANGE.
	//   - render +0x1c (ae10 threshold)  == setter +0x24 == Smooth Range
	//   - render +0x20 (c280 corner bw)  == setter +0x28 == Smoothness
	//   - render +0x24 (c280 local_14c)  == setter +0x2c == Extra Smooth
	// Confirmed against disasm: FUN_18000ae10 @18000ae72 `MOVD XMM8,[R15+0x1c]`,
	// FUN_18000c280 @18000c2bb `MOVD XMM2,[RAX+0x20]` / @18000c33f `[RAX+0x24]`.
	// The no-key software grid (sm2_no_key_s*_r{1,2,3}) shows the reference
	// smooths FEWER pixels as Smooth Range rises (r1>r2>r3), i.e. a rising
	// threshold = SmoothRange/100 + 0.001.  The earlier "key predicate" reading
	// was the source of the no-key over-firing residual.  The 2026-06-21
	// current-AEX legacy recapture shows the key-enabled path also follows this
	// Smooth Range threshold; the older key-predicate reading is kept as a
	// CLI-only diagnostic.
	const int   smooth_range_field = p.smooth_range;
	const int   key_pred_byte = (p.enable_key && !p.invert_key) ? 1 : 0;
	int class_threshold_field = smooth_range_field;
	if (g_olmsmoother2_class_threshold_diag_mode == 1) {
		class_threshold_field = smooth_range_field;
	} else if (g_olmsmoother2_class_threshold_diag_mode == 2) {
		class_threshold_field = 0;
	} else if (g_olmsmoother2_class_threshold_diag_mode == 3) {
		class_threshold_field = 1;
	}
	const float threshold = (float)class_threshold_field / 100.0f + WIN_THRESH_BIAS;
	if (g_olmsmoother2_trace_x >= 0 && g_olmsmoother2_trace_y >= 0) {
		std::fprintf(stderr,
		             "trace class_threshold mode=%d field=%d threshold=%.8f enable_key=%d invert_key=%d smooth_range=%d key_pred=%d\n",
		             g_olmsmoother2_class_threshold_diag_mode,
		             class_threshold_field,
		             threshold,
		             p.enable_key ? 1 : 0,
		             p.invert_key ? 1 : 0,
		             smooth_range_field,
		             key_pred_byte);
	}

	std::vector<uint8_t> class_plane((size_t)w * (size_t)h * 4, 0);
	auto fpix_at = [&](int xx, int yy) -> const FPix& {
		return class_base[(size_t)yy * w + xx];
	};
	for (int32_t y = 0; y < h; ++y) {
		uint8_t *row = class_plane.data() + (size_t)y * w * 4;
		for (int32_t x = 0; x < w; ++x) {
			const FPix &self = fpix_at(x, y);
			uint8_t b0 = 0, b1 = 0, b2 = 0, b3 = 0;
			// byte[0] = LEFT edge (param_3 >= 1)
			if (x >= 1) {
				b0 = (color_dist(self, fpix_at(x - 1, y)) >= threshold) ? 0xFF : 0;
			}
			if (y >= 1) {
				// byte[1] = TOP edge
				b1 = (color_dist(self, fpix_at(x, y - 1)) >= threshold) ? 0xFF : 0;
				// byte[2] = TOP-LEFT (param_3 >= 1)
				if (x >= 1) {
					b2 = (color_dist(self, fpix_at(x - 1, y - 1)) >= threshold) ? 0xFF : 0;
				}
				// byte[3] = TOP-RIGHT.  Win guard: param_3+1 < (int)param_2[1]+ -1
				// i.e. x + 1 < w - 1, i.e. x < w - 2.
				if (x + 1 < w - 1) {
					b3 = (color_dist(self, fpix_at(x + 1, y - 1)) >= threshold) ? 0xFF : 0;
				}
			}
			row[x * 4 + 0] = b0;
			row[x * 4 + 1] = b1;
			row[x * 4 + 2] = b2;
			row[x * 4 + 3] = b3;
		}
	}
	if (g_olmsmoother2_trace_x >= 0 && g_olmsmoother2_trace_y >= 0) {
		for (int yy = g_olmsmoother2_trace_y - 1; yy <= g_olmsmoother2_trace_y; ++yy) {
			for (int xx = g_olmsmoother2_trace_x - 1; xx <= g_olmsmoother2_trace_x + 1; ++xx) {
				if (xx < 0 || xx >= w || yy < 0 || yy >= h) continue;
				const FPix &self = fpix_at(xx, yy);
				const float left = xx > 0 ? color_dist(self, fpix_at(xx - 1, yy)) : -1.0f;
				const float top = yy > 0 ? color_dist(self, fpix_at(xx, yy - 1)) : -1.0f;
				const float top_left = xx > 0 && yy > 0 ? color_dist(self, fpix_at(xx - 1, yy - 1)) : -1.0f;
				const float top_right = xx + 1 < w - 1 && yy > 0 ? color_dist(self, fpix_at(xx + 1, yy - 1)) : -1.0f;
				const uint8_t *bits = class_plane.data() + ((size_t)yy * w + xx) * 4;
				std::fprintf(stderr,
				             "trace class_metric x=%d y=%d left=%.9g top=%.9g top_left=%.9g top_right=%.9g threshold=%.9g bits=%u,%u,%u,%u\n",
				             xx, yy, left, top, top_left, top_right, threshold,
				             (unsigned)bits[0], (unsigned)bits[1], (unsigned)bits[2], (unsigned)bits[3]);
			}
		}
	}
	p.class_plane = class_plane.data();

	for (int32_t y = 0; y < h; ++y) {
		for (int32_t x = 0; x < w; ++x) {
			FPix out_px;
			win_FUN_18000cce0_orchestrate(out_px, plane_in, plane_out, x, y, p);
			plane_out.base[(size_t)y * w + x] = out_px;
		}
	}

	// Inverse-gamma output path (FUN_1800036e0 inside FUN_180003d90):
	// Win gate is "*param_8 != 1" where param_8 also points at SMParams +8
	// (version-derived flag).  No gamma-LUT (param_9+0x10 == 0) -> sRGB OETF
	// via FUN_180004d70.  Same fix as the input-side decode: the gate is
	// version != v1, NOT gamma_mode != None.
	const bool apply_inverse_gamma = (p.version != SMOOTHER_V1);
	const float one = K_ONE;

	for (int32_t y = 0; y < h; ++y) {
		P *dst = (P *)((char *)output->data + (size_t)y * output->rowbytes);
		for (int32_t x = 0; x < w; ++x) {
			FPix px = plane_out.base[(size_t)y * w + x];
			float r = px.r, g = px.g, b = px.b, a = px.a;

			if (apply_inverse_gamma) {
				// Win branch: param_9 (gamma ctx) + 0x10 LUT ptr == 0 -> FUN_180004d70.
				r = (float)win_FUN_180004d70_literal((double)r);
				g = (float)win_FUN_180004d70_literal((double)g);
				b = (float)win_FUN_180004d70_literal((double)b);
			}

			// Win: if param_8[0x19] != 0 AND a != 1.0 -> RGB *= a  (re-premul)
			if (p.keep_premul && a != one) {
				r *= a;
				g *= a;
				b *= a;
			}

			if (std::is_same<P, PF_Pixel8>::value) {
				PF_Pixel8 *q = (PF_Pixel8 *)&dst[x];
				q->alpha = clamp8(a); q->red = clamp8(r); q->green = clamp8(g); q->blue = clamp8(b);
				if (g_olmsmoother2_writer_frame_probe.json_path &&
				    x == g_olmsmoother2_writer_frame_probe.x && y == g_olmsmoother2_writer_frame_probe.y) {
					g_olmsmoother2_writer_frame_probe.actual[0] = q->alpha;
					g_olmsmoother2_writer_frame_probe.actual[1] = q->red;
					g_olmsmoother2_writer_frame_probe.actual[2] = q->green;
					g_olmsmoother2_writer_frame_probe.actual[3] = q->blue;
				}
			} else if (std::is_same<P, PF_Pixel16>::value) {
				PF_Pixel16 *q = (PF_Pixel16 *)&dst[x];
				q->alpha = clamp16(a); q->red = clamp16(r); q->green = clamp16(g); q->blue = clamp16(b);
			} else {
				// Win FUN_1800036e0 (PF_PixelFloat writer) at 0x1800036e0 writes
				// MOVUPS [RBX], XMM6 (asm 0x1800038ee) with NO clamping on any
				// channel.  R/G/B are already saturated to [0,1] by FUN_180004d70
				// (sRGB OETF clamps internally); the optional `*= a` re-premul can
				// push them outside [0,1] when alpha > 1, but Win still writes the
				// raw value.  Alpha (`local_cc`) is written verbatim from
				// FUN_18000cce0 with no clamp at all.  Match Win byte-for-byte.
				PF_PixelFloat *q = (PF_PixelFloat *)&dst[x];
				q->alpha = a; q->red = r; q->green = g; q->blue = b;
			}
		}
	}
	OLMSmoother2WriteWriterFrameProbe(apply_inverse_gamma, p.keep_premul);

	return err;
}

// ============================================================================
// Lifecycle
// ============================================================================
static PF_Err
About(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	AEGP_SuiteHandler suites(in_data->pica_basicP);
	suites.ANSICallbacksSuite1()->sprintf(out_data->return_msg,
		"%s %d.%d\r%s",
		GetStringPtr(StrID_Name),
		MAJOR_VERSION, MINOR_VERSION,
		"Smooth images.");
	return PF_Err_NONE;
}

static PF_Err
GlobalSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	out_data->my_version = PF_VERSION(MAJOR_VERSION, MINOR_VERSION, BUG_VERSION,
	                                  STAGE_VERSION, BUILD_VERSION);
	out_data->out_flags  = 0x02000440;
	out_data->out_flags2 = 0x08001400;
	return PF_Err_NONE;
}

static PF_Err
ParamsSetup(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *[], PF_LayerDef *)
{
	PF_Err      err = PF_Err_NONE;
	PF_ParamDef def;

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_EnableKey_Param_Name),
	                "", FALSE, 0, ENABLE_KEY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_COLOR(GetStringPtr(StrID_Key_Param_Name),
	             0xFF, 0xFF, 0xFF,
	             KEY_COLOR_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_CHECKBOX(GetStringPtr(StrID_InvertKey_Param_Name),
	                "", FALSE, 0, INVERT_KEY_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_Smoothness_Param_Name),
	              0, 100, 0, 100, 100,
	              SMOOTHNESS_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_ExtraSmooth_Param_Name),
	              0, 100, 0, 100, 0,
	              EXTRA_SMOOTH_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_SmoothRange_Param_Name),
	              0, 255, 0, 255, 2,
	              SMOOTH_RANGE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_Version_Param_Name),
	             2, SMOOTHER_V2,
	             GetStringPtr(StrID_Version_Choices),
	             VERSION_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_POPUP(GetStringPtr(StrID_Gamma_Param_Name),
	             3, GAMMA_NONE,
	             GetStringPtr(StrID_Gamma_Choices),
	             GAMMA_MODE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_FLOAT_SLIDERX(GetStringPtr(StrID_GammaValue_Param_Name),
	                     1.0, 2.4, 1.0, 2.4, 2.4,
	                     PF_Precision_HUNDREDTHS, 0, 0,
	                     GAMMA_VALUE_DISK_ID);

	AEFX_CLR_STRUCT(def);
	PF_ADD_SLIDER(GetStringPtr(StrID_NumGamma_Param_Name),
	              0, NUM_GAMMA_COLORS, 0, NUM_GAMMA_COLORS, 1,
	              NUM_GAMMA_DISK_ID);

	for (int i = 0; i < NUM_GAMMA_COLORS; ++i) {
		AEFX_CLR_STRUCT(def);
		PF_ADD_COLOR(GetStringPtr(StrID_GammaColor_Param_Name),
		             0, 0, 0,
		             GAMMA_COLOR_0_DISK_ID + i);
	}

	out_data->num_params = SM_NUM_PARAMS;
	return err;
}

// ============================================================================
// Classic Render
// ============================================================================
static PF_Err
Render(PF_InData *in_data, PF_OutData *out_data, PF_ParamDef *params[], PF_LayerDef *output)
{
	PF_LayerDef *input = &params[SM_INPUT]->u.ld;
	if (PF_WORLD_IS_DEEP(input)) {
		return RenderBits<PF_Pixel16>(in_data, params, input, output);
	} else {
		return RenderBits<PF_Pixel8>(in_data, params, input, output);
	}
}

// ============================================================================
// SmartRender
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

	UnionLRect_inline(&in_result.result_rect, &extra->output->result_rect);
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
		short depth = extra->input->bitdepth;
		if (depth == 8) {
			err = RenderBits<PF_Pixel8>(in_data, params, input_world, output_world);
		} else if (depth == 16) {
			err = RenderBits<PF_Pixel16>(in_data, params, input_world, output_world);
		} else {
			err = RenderBits<PF_PixelFloat>(in_data, params, input_world, output_world);
		}
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

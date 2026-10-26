// ============================================================================
// Constants read directly from the Windows binary (see DAT_180022xxx).
// Preserve the literal widths and values used by the frame and polygon stages.
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
constexpr float  COLOR_TOL   = 0x1.010102p-9f; // DAT_18002268c (3B008081h)

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
static thread_local int g_olmsmoother2_current_switch_idx = -1;
static uint64_t g_olmsmoother2_idx18_cardinal3_key_hist[128] = {};
static uint64_t g_olmsmoother2_idx18_cardinal12_key_hist[128] = {};
static int g_olmsmoother2_trace_x = -1;
static int g_olmsmoother2_trace_y = -1;
static thread_local bool g_olmsmoother2_force_input_premultiply = false;

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
	bool          pf16_runtime;
	bool          pf32_runtime;

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

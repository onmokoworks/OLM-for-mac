// AE-free shim header for OLMSmoother_port.cpp.
//
// The mac port includes "OLMSmoother.h" expecting the After Effects SDK. This
// shim replaces it with the minimal type/macro surface the port actually
// touches, so the algorithm can be compiled into a standalone CLI with no SDK.
// It is found ahead of the real header purely via the CLI build's -I path.
#pragma once
#ifndef OLMSMOOTHER_SHIM_H
#define OLMSMOOTHER_SHIM_H

#include <cstdint>
#include <cstring>
#include <cstdio>

// --- basic AE scalar types -------------------------------------------------
typedef int32_t  A_long;
typedef uint32_t A_u_long;
typedef int16_t  A_short;
typedef uint16_t A_u_short;
typedef char     A_char;
typedef uint8_t  A_u_char;
typedef char     A_Boolean;
typedef double   A_FpLong;

typedef A_long PF_Err;
enum { PF_Err_NONE = 0 };

typedef void *PF_ProgPtr;

#define DllExport
#ifndef FALSE
#define FALSE 0
#endif
#ifndef TRUE
#define TRUE 1
#endif

// Pinned OLMSmoother v1 eVER tuple from the production header/binary.
#define MAJOR_VERSION 1
#define MINOR_VERSION 2
#define BUG_VERSION 1
#define STAGE_VERSION 0
#define BUILD_VERSION 0

// --- pixels (AE native byte order is Alpha, Red, Green, Blue) ---------------
struct PF_Pixel8  { uint8_t  alpha, red, green, blue; };
struct PF_Pixel16 { uint16_t alpha, red, green, blue; };
struct PF_PixelFloat { float alpha, red, green, blue; };
typedef PF_Pixel8 PF_Pixel;

// --- rects / worlds --------------------------------------------------------
struct PF_LRect { A_long left, top, right, bottom; };
typedef PF_LRect PF_Rect;

struct PF_EffectWorld {
	void   *data;
	A_long  width;
	A_long  height;
	A_long  rowbytes;
	short   bitdepth;
	PF_LRect extent_hint;
};
typedef PF_EffectWorld PF_LayerDef;

#define PF_WORLD_IS_DEEP(W) ((W) != nullptr && (W)->bitdepth == 16)

// --- params ----------------------------------------------------------------
enum {
	SM_INPUT = 0,
	SM_USE_KEY,
	SM_KEY_COLOR,
	SM_TOLERANCE,
	SM_NUM_PARAMS
};
enum {
	USE_KEY_DISK_ID   = 1,
	KEY_COLOR_DISK_ID = 2,
	TOLERANCE_DISK_ID = 3
};

struct PF_BooleanData { A_long value; };
struct PF_SliderData  { A_long value; };
struct PF_ColorData   { PF_Pixel value; };

struct PF_ParamDef {
	union {
		PF_BooleanData bd;
		PF_SliderData  sd;
		PF_ColorData   cd;
		PF_LayerDef    ld;
	} u;
};

// --- in/out data -----------------------------------------------------------
struct PF_InData {
	PF_ProgPtr effect_ref;
	A_long     current_time;
	A_long     time_step;
	A_long     time_scale;
	void      *pica_basicP;
};
struct PF_OutData {
	char     return_msg[256];
	A_u_long my_version;
	A_u_long out_flags;
	A_u_long out_flags2;
	A_long   num_params;
};

// --- command + smart-render scaffolding (used only by uncalled handlers) ---
typedef A_long PF_Cmd;
enum {
	PF_Cmd_ABOUT = 0,
	PF_Cmd_GLOBAL_SETUP,
	PF_Cmd_PARAMS_SETUP,
	PF_Cmd_RENDER,
	PF_Cmd_SMART_PRE_RENDER,
	PF_Cmd_SMART_RENDER
};

struct PF_RenderRequest  { A_long _dummy; };
struct PF_CheckoutResult { PF_LRect result_rect, max_result_rect; };

struct PF_PreRenderCallbacks {
	PF_Err (*checkout_layer)(PF_ProgPtr, A_long, A_long, PF_RenderRequest *,
	                         A_long, A_long, A_long, PF_CheckoutResult *);
};
struct PF_PreRenderInput  { PF_RenderRequest output_request; short bitdepth; };
struct PF_PreRenderOutput { PF_LRect result_rect, max_result_rect; };
struct PF_PreRenderExtra {
	PF_PreRenderInput     *input;
	PF_PreRenderOutput    *output;
	PF_PreRenderCallbacks *cb;
};

struct PF_SmartRenderCallbacks {
	PF_Err (*checkout_layer_pixels)(PF_ProgPtr, A_long, PF_EffectWorld **);
	PF_Err (*checkout_output)(PF_ProgPtr, PF_EffectWorld **);
};
struct PF_SmartRenderInput { short bitdepth; };
struct PF_SmartRenderExtra {
	PF_SmartRenderInput     *input;
	PF_SmartRenderCallbacks *cb;
};

struct AEGP_SuiteHandler { AEGP_SuiteHandler(void *) {} };

// --- macros the port expects from AE_Macros.h / Param_Utils.h --------------
#define PF_VERSION(A, B, C, D, E) \
	((static_cast<A_u_long>(A) << 19) | (static_cast<A_u_long>(B) << 15) | \
	 (static_cast<A_u_long>(C) << 11) | (static_cast<A_u_long>(D) << 9) | \
	 static_cast<A_u_long>(E))
#define AEFX_CLR_STRUCT(S) std::memset(&(S), 0, sizeof(S))
#define PF_SPRINTF std::sprintf
#define ERR(X) do { if (err == PF_Err_NONE) { err = (X); } } while (0)
#ifdef OLMSMOOTHER_CAPTURE_PARAMS
#define PF_ADD_CHECKBOX(NAME, DESC, DEFAULT, FLAGS, DISK_ID) \
    olmsmoother_capture_checkbox((NAME), (DEFAULT), (FLAGS), (DISK_ID))
#define PF_ADD_COLOR(NAME, R, G, B, DISK_ID) \
    olmsmoother_capture_color((NAME), (R), (G), (B), (DISK_ID))
#define PF_ADD_SLIDER(NAME, VALID_MIN, VALID_MAX, SLIDER_MIN, SLIDER_MAX, DEFAULT, DISK_ID) \
    olmsmoother_capture_slider((NAME), (VALID_MIN), (VALID_MAX), (SLIDER_MIN), (SLIDER_MAX), (DEFAULT), (DISK_ID))
#else
#define PF_ADD_CHECKBOX(...) ((void)0)
#define PF_ADD_COLOR(...)    ((void)0)
#define PF_ADD_SLIDER(...)   ((void)0)
#endif
#define PF_CHECKOUT_PARAM(...) (PF_Err_NONE)
#define PF_CHECKIN_PARAM(...)  ((void)0)

// --- strings ---------------------------------------------------------------
enum {
	StrID_Name = 0,
	StrID_Description,
	StrID_UseKey_Param_Name,
	StrID_Key_Param_Name,
	StrID_Tolerance_Param_Name
};
static inline const char *GetStringPtr(int id) {
#ifdef OLMSMOOTHER_CAPTURE_PARAMS
	static const char *const values[] = {"OLM Smoother", "", "Use Color Key", "Color Key", "Do Smooth Range"};
	return (id >= 0 && id < 5) ? values[id] : "";
#else
	(void)id; return "";
#endif
}

// --- iterate suites (concrete fn-ptr typed, backed by the CLI loop) ---------
typedef PF_Err (*PF_Iterate8Fn)(void *, A_long, A_long, PF_Pixel8 *, PF_Pixel8 *);
typedef PF_Err (*PF_Iterate16Fn)(void *, A_long, A_long, PF_Pixel16 *, PF_Pixel16 *);
typedef PF_Err (*PF_IterateFloatFn)(void *, A_long, A_long, PF_PixelFloat *, PF_PixelFloat *);

struct PF_Iterate8Suite1 {
	PF_Err (*iterate)(PF_InData *, A_long, A_long, PF_EffectWorld *,
	                  const PF_LRect *, void *, PF_Iterate8Fn, PF_EffectWorld *);
};
struct PF_Iterate16Suite1 {
	PF_Err (*iterate)(PF_InData *, A_long, A_long, PF_EffectWorld *,
	                  const PF_LRect *, void *, PF_Iterate16Fn, PF_EffectWorld *);
};
struct PF_IterateFloatSuite1 {
	PF_Err (*iterate)(PF_InData *, A_long, A_long, PF_EffectWorld *,
	                  const PF_LRect *, void *, PF_IterateFloatFn, PF_EffectWorld *);
};

#define kPFIterate8Suite        "PF Iterate8 Suite"
#define kPFIterate8SuiteVersion1 1
#define kPFIterate16Suite       "PF iterate16 Suite"
#define kPFIterate16SuiteVersion1 1
#define kPFIterateFloatSuite    "PF IterateFloat Suite"
#define kPFIterateFloatSuiteVersion1 1

#endif // OLMSMOOTHER_SHIM_H

// AE-free shim header for mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp.
#pragma once
#ifndef OLMSMOOTHER2_SHIM_H
#define OLMSMOOTHER2_SHIM_H

#include <cstdint>
#include <cstring>
#include <cstdio>

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
enum { PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS = 1 };

typedef void *PF_ProgPtr;

#define DllExport
#ifndef FALSE
#define FALSE 0
#endif
#ifndef TRUE
#define TRUE 1
#endif

typedef unsigned char  u_char;
typedef unsigned short u_short;
typedef unsigned short u_int16;
typedef unsigned long  u_long;
typedef short int      int16;

struct PF_Pixel8  { uint8_t  alpha, red, green, blue; };
struct PF_Pixel16 { uint16_t alpha, red, green, blue; };
struct PF_PixelFloat { float alpha, red, green, blue; };
typedef PF_Pixel8 PF_Pixel;

struct PF_LRect { A_long left, top, right, bottom; };
typedef PF_LRect PF_Rect;

struct PF_EffectWorld {
	void   *data;
	A_long  width;
	A_long  height;
	A_long  rowbytes;
	short   bitdepth;
	PF_LRect extent_hint;
	A_long  origin_x;
	A_long  origin_y;
};
typedef PF_EffectWorld PF_LayerDef;

#define PF_WORLD_IS_DEEP(W) ((W) && (W)->bitdepth == 16)

#define PF_TABLE_BITS      12
#define PF_TABLE_SZ_16     4096
#define PF_DEEP_COLOR_AWARE 1

#define MAJOR_VERSION 2
#define MINOR_VERSION 1
#define BUG_VERSION   0
#define STAGE_VERSION 0
#define BUILD_VERSION 0

#define NUM_GAMMA_COLORS 5

enum {
	SM_INPUT = 0,
	SM_ENABLE_KEY,
	SM_KEY_COLOR,
	SM_INVERT_KEY,
	SM_SMOOTHNESS,
	SM_EXTRA_SMOOTH,
	SM_SMOOTH_RANGE,
	SM_VERSION,
	SM_GAMMA_MODE,
	SM_GAMMA_VALUE,
	SM_NUM_GAMMA_COLORS,
	SM_GAMMA_COLOR_0,
	SM_GAMMA_COLOR_1,
	SM_GAMMA_COLOR_2,
	SM_GAMMA_COLOR_3,
	SM_GAMMA_COLOR_4,
	SM_NUM_PARAMS
};

enum {
	ENABLE_KEY_DISK_ID      = 1,
	KEY_COLOR_DISK_ID       = 2,
	SMOOTHNESS_DISK_ID      = 3,
	EXTRA_SMOOTH_DISK_ID    = 4,
	SMOOTH_RANGE_DISK_ID    = 5,
	VERSION_DISK_ID         = 6,
	GAMMA_MODE_DISK_ID      = 7,
	GAMMA_VALUE_DISK_ID     = 8,
	NUM_GAMMA_DISK_ID       = 9,
	GAMMA_COLOR_0_DISK_ID   = 10,
	GAMMA_COLOR_1_DISK_ID   = 11,
	GAMMA_COLOR_2_DISK_ID   = 12,
	GAMMA_COLOR_3_DISK_ID   = 13,
	GAMMA_COLOR_4_DISK_ID   = 14,
	INVERT_KEY_DISK_ID      = 15
};

enum {
	SMOOTHER_V1 = 1,
	SMOOTHER_V2 = 2
};

enum {
	GAMMA_NONE         = 1,
	GAMMA_COLORS_ONLY = 2,
	GAMMA_ALL_COLORS  = 3
};

struct PF_BooleanData { A_long value; };
struct PF_SliderData  { A_long value; };
struct PF_PopupData   { A_long value; };
struct PF_FloatSliderData { double value; };
struct PF_ColorData   { PF_Pixel value; };

struct PF_ParamDef {
	union {
		PF_BooleanData bd;
		PF_SliderData  sd;
		PF_PopupData   pd;
		PF_FloatSliderData fs_d;
		PF_ColorData   cd;
		PF_LayerDef    ld;
	} u;
};

struct PF_InData {
	PF_ProgPtr effect_ref;
	A_long     current_time;
	A_long     time_step;
	A_long     time_scale;
	void      *pica_basicP;
	A_long     width;
	A_long     height;
	struct { A_long num, den; } downsample_x;
	struct { A_long num, den; } downsample_y;
};
struct PF_OutData {
	char     return_msg[256];
	A_u_long my_version;
	A_u_long out_flags;
	A_u_long out_flags2;
	A_long   num_params;
};

typedef A_long PF_Cmd;
enum {
	PF_Cmd_ABOUT = 0,
	PF_Cmd_GLOBAL_SETUP,
	PF_Cmd_PARAMS_SETUP,
	PF_Cmd_RENDER,
	PF_Cmd_SMART_PRE_RENDER,
	PF_Cmd_SMART_RENDER
};

struct PF_RenderRequest  { PF_LRect rect; A_long field, channel_mask; char preserve_rgb_of_zero_alpha; };
struct PF_CheckoutResult {
	PF_LRect result_rect, max_result_rect;
	A_long ref_width, ref_height;
};

struct PF_PreRenderCallbacks {
	PF_Err (*checkout_layer)(PF_ProgPtr, A_long, A_long, PF_RenderRequest *,
	                         A_long, A_long, A_long, PF_CheckoutResult *);
};
struct PF_PreRenderInput  { PF_RenderRequest output_request; short bitdepth; };
struct PF_PreRenderOutput {
	PF_LRect result_rect, max_result_rect;
	char solid, reserved;
	short flags;
	void *pre_render_data;
	void (*delete_pre_render_data_func)(void *);
};
struct PF_PreRenderExtra {
	PF_PreRenderInput     *input;
	PF_PreRenderOutput    *output;
	PF_PreRenderCallbacks *cb;
};

struct PF_SmartRenderCallbacks {
	PF_Err (*checkout_layer_pixels)(PF_ProgPtr, A_long, PF_EffectWorld **);
	PF_Err (*checkout_output)(PF_ProgPtr, PF_EffectWorld **);
};
// Keep bitdepth first for the long-standing aggregate initializers used by the
// hostless public-guard harness. SmartRender does not consume output_request.
struct PF_SmartRenderInput { short bitdepth; PF_RenderRequest output_request; void *pre_render_data; };
struct PF_SmartRenderExtra {
	PF_SmartRenderInput     *input;
	PF_SmartRenderCallbacks *cb;
};

struct PF_ColorParamSuite1 {
	PF_Err (*PF_GetFloatingPointColorFromColorDef)(PF_ProgPtr, PF_ParamDef *, PF_PixelFloat *);
};

struct PF_ANSICallbacksSuite1 {
	int (*sprintf)(char *, const char *, ...);
};

static PF_Err cli_get_float_color(PF_ProgPtr, PF_ParamDef *def, PF_PixelFloat *out) {
	out->alpha = def->u.cd.value.alpha / 255.0f;
	out->red   = def->u.cd.value.red   / 255.0f;
	out->green = def->u.cd.value.green / 255.0f;
	out->blue  = def->u.cd.value.blue  / 255.0f;
	return PF_Err_NONE;
}

static PF_ColorParamSuite1 g_color_suite = { &cli_get_float_color };
static PF_ANSICallbacksSuite1 g_ansi_suite = { &std::sprintf };

struct AEGP_SuiteHandler {
	AEGP_SuiteHandler(void *) {}
	PF_ColorParamSuite1 *ColorParamSuite1() { return &g_color_suite; }
	PF_ANSICallbacksSuite1 *ANSICallbacksSuite1() { return &g_ansi_suite; }
};

#define PF_VERSION(A, B, C, D, E) (0u)
#define AEFX_CLR_STRUCT(S) std::memset(&(S), 0, sizeof(S))
#define PF_SPRINTF std::sprintf
#define ERR(X) do { if (err == PF_Err_NONE) { err = (X); } } while (0)
#define FIX_2_FLOAT(X) (X)
#define PF_Precision_HUNDREDTHS 2
#define PF_ADD_CHECKBOX(...)      ((void)0)
#define PF_ADD_COLOR(...)         ((void)0)
#define PF_ADD_SLIDER(...)        ((void)0)
#define PF_ADD_POPUP(...)         ((void)0)
#define PF_ADD_FLOAT_SLIDERX(...) ((void)0)
typedef PF_Err (*CLI_CheckoutParamHook)(A_long, PF_ParamDef *);
typedef void (*CLI_CheckinParamHook)(PF_ParamDef *);
typedef PF_Err (*CLI_CheckinParamErrorHook)(PF_ParamDef *);
static PF_Err cli_default_checkout_param(A_long, PF_ParamDef *) { return PF_Err_NONE; }
static void cli_default_checkin_param(PF_ParamDef *) {}
static CLI_CheckoutParamHook g_cli_checkout_param_hook = &cli_default_checkout_param;
static CLI_CheckinParamHook g_cli_checkin_param_hook = &cli_default_checkin_param;
static CLI_CheckinParamErrorHook g_cli_checkin_param_error_hook = nullptr;
static PF_Err cli_checkin_param_result(PF_ParamDef *param) {
    g_cli_checkin_param_hook(param);
    return g_cli_checkin_param_error_hook ? g_cli_checkin_param_error_hook(param) : PF_Err_NONE;
}
#define PF_CHECKOUT_PARAM(IN,I,T,TS,SCALE,OUT) g_cli_checkout_param_hook((I),(OUT))
#define PF_CHECKIN_PARAM(IN,P) cli_checkin_param_result((P))

enum {
	StrID_Name = 0,
	StrID_Description,
	StrID_EnableKey_Param_Name,
	StrID_Key_Param_Name,
	StrID_InvertKey_Param_Name,
	StrID_Smoothness_Param_Name,
	StrID_ExtraSmooth_Param_Name,
	StrID_SmoothRange_Param_Name,
	StrID_Version_Param_Name,
	StrID_Version_Choices,
	StrID_Gamma_Param_Name,
	StrID_Gamma_Choices,
	StrID_GammaValue_Param_Name,
	StrID_NumGamma_Param_Name,
	StrID_GammaColor_Param_Name
};
static inline const char *GetStringPtr(int) { return ""; }

#endif // OLMSMOOTHER2_SHIM_H

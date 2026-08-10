#pragma once

#include <cstdint>
#include <cstdio>
#include <cstring>

typedef std::int32_t A_long;
typedef std::uint32_t A_u_long;
typedef void *PF_ProgPtr;
typedef A_long PF_Err;
enum { PF_Err_NONE = 0 };
enum { PF_Err_BAD_CALLBACK_PARAM = -1 };
enum { PF_Stage_BETA = 0 };
typedef A_long PF_Cmd;
enum { PF_Cmd_ABOUT = 0, PF_Cmd_GLOBAL_SETUP, PF_Cmd_PARAMS_SETUP,
       PF_Cmd_RENDER, PF_Cmd_SMART_PRE_RENDER, PF_Cmd_SMART_RENDER,
       PF_Cmd_UPDATE_PARAMS_UI };

struct PF_Pixel8 { std::uint8_t alpha, red, green, blue; };
struct PF_Pixel16 { std::uint16_t alpha, red, green, blue; };
struct PF_PixelFloat { float alpha, red, green, blue; };
enum PF_PixelFormat { PF_PixelFormat_INVALID, PF_PixelFormat_ARGB32,
                      PF_PixelFormat_ARGB64, PF_PixelFormat_ARGB128 };
struct PF_LRect { A_long left, top, right, bottom; };
struct PF_EffectWorld {
    void *data;
    A_long width, height, rowbytes;
    short bitdepth;
    PF_LRect extent_hint;
};
typedef PF_EffectWorld PF_LayerDef;

struct PF_BooleanData { A_long value; };
struct PF_SliderData { A_long value; };
struct PF_PopupData { A_long value; };
struct PF_FloatSliderData { double value; };
struct PF_ColorData { PF_Pixel8 value; };
struct PF_ParamDef {
	A_u_long ui_flags;
	A_u_long flags;
    union {
        PF_BooleanData bd;
        PF_SliderData sd;
        PF_PopupData pd;
        PF_FloatSliderData fs_d;
        PF_ColorData cd;
        PF_LayerDef ld;
    } u;
};
struct PF_InData {
    PF_ProgPtr effect_ref;
    A_long current_time, time_step, time_scale;
    struct { A_long num, den; } downsample_x, downsample_y;
    void *pica_basicP;
};
struct PF_OutData { char return_msg[256]; A_u_long my_version, out_flags, out_flags2; A_long num_params; };
struct PF_RenderRequest { A_long _dummy; };
struct PF_CheckoutResult { PF_LRect result_rect, max_result_rect; };
struct PF_PreRenderInput { PF_RenderRequest output_request; short bitdepth; };
struct PF_PreRenderOutput { PF_LRect result_rect, max_result_rect; };
struct PF_PreRenderCallbacks {
    PF_Err (*checkout_layer)(PF_ProgPtr, A_long, A_long, PF_RenderRequest *, A_long, A_long, A_long, PF_CheckoutResult *);
};
struct PF_PreRenderExtra { PF_PreRenderInput *input; PF_PreRenderOutput *output; PF_PreRenderCallbacks *cb; };
struct PF_SmartRenderInput { short bitdepth; };
struct PF_SmartRenderCallbacks {
    PF_Err (*checkout_layer_pixels)(PF_ProgPtr, A_long, PF_EffectWorld **);
    PF_Err (*checkout_output)(PF_ProgPtr, PF_EffectWorld **);
};
struct PF_SmartRenderExtra { PF_SmartRenderInput *input; PF_SmartRenderCallbacks *cb; };

struct PF_WorldSuite2 {
    PF_Err PF_GetPixelFormat(PF_LayerDef *world, PF_PixelFormat *format) {
        *format = world->bitdepth == 8 ? PF_PixelFormat_ARGB32
                 : world->bitdepth == 16 ? PF_PixelFormat_ARGB64 : PF_PixelFormat_ARGB128;
        return PF_Err_NONE;
    }
};
static constexpr const char *kPFWorldSuite = "PF World Suite";
static constexpr A_long kPFWorldSuiteVersion2 = 2;
template <typename SuiteT>
struct AEFX_SuiteScoper {
    SuiteT suite;
    AEFX_SuiteScoper(PF_InData *, const char *, A_long, PF_OutData *) {}
    SuiteT *operator->() { return &suite; }
};

struct PF_ColorParamSuite1 {
    PF_Err (*PF_GetFloatingPointColorFromColorDef)(PF_ProgPtr, PF_ParamDef *, PF_PixelFloat *);
};
struct PF_ANSICallbacksSuite1 { int (*sprintf)(char *, const char *, ...); };
struct PF_ParamUtilsSuite3 {
    PF_Err PF_UpdateParamUI(PF_ProgPtr, A_long, const PF_ParamDef *) { return PF_Err_NONE; }
};
static PF_Err dg_harness_color(PF_ProgPtr, PF_ParamDef *def, PF_PixelFloat *out) {
    out->alpha = def->u.cd.value.alpha / 255.0f;
    out->red = def->u.cd.value.red / 255.0f;
    out->green = def->u.cd.value.green / 255.0f;
    out->blue = def->u.cd.value.blue / 255.0f;
    return PF_Err_NONE;
}
static PF_ColorParamSuite1 dg_harness_color_suite = { &dg_harness_color };
static PF_ANSICallbacksSuite1 dg_harness_ansi_suite = { &std::sprintf };
static PF_ParamUtilsSuite3 dg_harness_param_utils_suite;
struct AEGP_SuiteHandler {
    explicit AEGP_SuiteHandler(void *) {}
    PF_ColorParamSuite1 *ColorParamSuite1() { return &dg_harness_color_suite; }
    PF_ANSICallbacksSuite1 *ANSICallbacksSuite1() { return &dg_harness_ansi_suite; }
    PF_ParamUtilsSuite3 *ParamUtilsSuite3() { return &dg_harness_param_utils_suite; }
};

#define DllExport
#define PF_WORLD_IS_DEEP(W) (0)
#define PF_VERSION(A, B, C, D, E) (0u)
#define AEFX_CLR_STRUCT(S) std::memset(&(S), 0, sizeof(S))
#define ERR(X) do { if (err == PF_Err_NONE) err = (X); } while (0)
#define PF_CHECKOUT_PARAM(...) (PF_Err_NONE)
#define PF_CHECKIN_PARAM(...) ((void)0)
#define PF_ADD_CHECKBOX(...) ((void)0)
#define PF_ADD_COLOR(...) ((void)0)
#define PF_ADD_SLIDER(...) ((void)0)
#define PF_ADD_POPUP(...) ((void)0)
#define PF_ADD_FLOAT_SLIDERX(...) ((void)0)
#define PF_Precision_HUNDREDTHS 2
#define PF_ParamFlag_START_COLLAPSED 0x20
#define PF_PUI_DISABLED 0x20
#define AEFX_ChannelDepthTpl_h

static inline const char *GetStringPtr(int) { return ""; }

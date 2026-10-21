#pragma once

#include <dlfcn.h>

// Included after the source has been compiled with EffectMain renamed. Direct
// typed helpers remain available to the probe, while every subsequent public
// call is forwarded to the current installed Mach-O.
static PF_Err InstalledOLMRadialBlurEffectMain(
    PF_Cmd cmd,
    PF_InData *in_data,
    PF_OutData *out_data,
    PF_ParamDef *params[],
    PF_LayerDef *output,
    void *extra)
{
    using EffectMainFn = PF_Err (*)(
        PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef **, PF_LayerDef *, void *);
    static void *handle = dlopen(
        "/Users/onmk/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/"
        "OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur",
        RTLD_NOW | RTLD_LOCAL);
    static EffectMainFn entry = handle
        ? reinterpret_cast<EffectMainFn>(dlsym(handle, "EffectMain"))
        : nullptr;
    return entry
        ? entry(cmd, in_data, out_data, params, output, extra)
        : PF_Err_BAD_CALLBACK_PARAM;
}

#define EffectMain InstalledOLMRadialBlurEffectMain

#pragma once

#define EffectMain SourceBuiltOLMColorKeyEffectMain
#include "../../mac/OLMColorKey/OLMColorKey.cpp"
#undef EffectMain

#include <cstdlib>
#include <dlfcn.h>
#include <string>

// Forward the real-SDK public-entry probe to the selected installed Mach-O.
static PF_Err InstalledOLMColorKeyEffectMain(
    PF_Cmd cmd,
    PF_InData *in_data,
    PF_OutData *out_data,
    PF_ParamDef *params[],
    PF_LayerDef *output,
    void *extra)
{
    using EffectMainFn = PF_Err (*)(
        PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef **, PF_LayerDef *, void *);
    static void *handle = nullptr;
    static EffectMainFn entry = nullptr;
    if (!entry) {
        const char *path = std::getenv("OLMCOLORKEY_INSTALLED_BINARY");
        static std::string default_path;
        if (!path || !*path) {
            const char *home = std::getenv("HOME");
            if (!home || !*home) return PF_Err_BAD_CALLBACK_PARAM;
            default_path = std::string(home) +
                "/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/"
                "OLMColorKey.plugin/Contents/MacOS/OLMColorKey";
            path = default_path.c_str();
        }
        handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
        if (!handle) return PF_Err_BAD_CALLBACK_PARAM;
        entry = reinterpret_cast<EffectMainFn>(dlsym(handle, "EffectMain"));
        if (!entry) return PF_Err_BAD_CALLBACK_PARAM;
    }
    return entry(cmd, in_data, out_data, params, output, extra);
}

#define EffectMain InstalledOLMColorKeyEffectMain

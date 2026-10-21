// AE-free GLOBAL_SETUP probe of a compiled bundle, never a source-included shim.
#include "AEConfig.h"
#include "AE_Effect.h"
#include "AE_GeneralPlug.h"
#include "SPBasic.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <dlfcn.h>

static A_Err register_plugin(AEGP_GlobalRefcon, const A_char *, AEGP_PluginID *id) {
    *id = 42;
    return 0;
}
static AEGP_UtilitySuite6 utility6{};
static AEGP_UtilitySuite3 utility3{};
static SPErr acquire(const char *name, int32 version, const void **suite) {
    std::fprintf(stderr, "AcquireSuite %s %d\n", name, int(version));
    if (std::strcmp(name, kAEGPUtilitySuite) != 0) return -1;
    if (version == kAEGPUtilitySuiteVersion6) *suite = &utility6;
    else if (version == kAEGPUtilitySuiteVersion3) *suite = &utility3;
    else return -1;
    return 0;
}
static SPErr release(const char *, int32) { return 0; }
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) { std::fprintf(stderr, "%s\n", dlerror()); return 3; }
    using Entry = PF_Err (*)(PF_Cmd, PF_InData *, PF_OutData *, PF_ParamDef **, PF_LayerDef *, void *);
    auto entry = reinterpret_cast<Entry>(dlsym(handle, "EffectMain"));
    if (!entry) return 4;
    utility6.AEGP_RegisterWithAEGP = register_plugin;
    utility3.AEGP_RegisterWithAEGP = register_plugin;
    SPBasicSuite basic{};
    basic.AcquireSuite = acquire;
    basic.ReleaseSuite = release;
    PF_InData in{};
    PF_OutData out;
    std::memset(&out, std::strtoul(argv[2], nullptr, 0), sizeof(out));
    in.pica_basicP = &basic;
    auto error = entry(PF_Cmd_GLOBAL_SETUP, &in, &out, nullptr, nullptr, nullptr);
    std::printf("{\"return_code\":%d,\"my_version\":%u,\"out_flags\":%u,\"out_flags2\":%u}\n",
        int(error), unsigned(out.my_version), unsigned(out.out_flags), unsigned(out.out_flags2));
    return error ? 5 : 0;
}

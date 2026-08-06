#include "Skeleton.h"

namespace {
constexpr PF_Pixel16 kPixels[12] = {
    {32768,32768,32768,32768}, {32768,8192,24576,32768}, {32768,0,0,0}, {32768,32769,32768,32768},
    {32768,32768,32769,32768}, {32768,32768,32768,32769}, {32768,65535,65535,65535}, {32769,32768,32768,32768},
    {65535,8192,24576,32768}, {16384,65535,32769,49152}, {1,32769,1,65535}, {32768,12345,23456,34567},
};

PF_Err render(PF_LayerDef *output) {
    if (!output || !output->data || output->width < 4 || output->height < 3 || !PF_WORLD_IS_DEEP(output)) return PF_Err_BAD_CALLBACK_PARAM;
    for (A_long y = 0; y < output->height; ++y) {
        auto *row = reinterpret_cast<PF_Pixel16 *>(reinterpret_cast<char *>(output->data) + y * output->rowbytes);
        for (A_long x = 0; x < output->width; ++x) row[x] = (x < 4 && y < 3) ? kPixels[y * 4 + x] : PF_Pixel16{0,0,0,0};
    }
    return PF_Err_NONE;
}
}

extern "C" DllExport PF_Err EffectMain(PF_Cmd cmd, PF_InData *, PF_OutData *out, PF_ParamDef *[], PF_LayerDef *output, void *) {
    switch (cmd) {
        case PF_Cmd_GLOBAL_SETUP:
            out->my_version = PF_VERSION(1,0,0,PF_Stage_DEVELOP,0);
            out->out_flags = PF_OutFlag_DEEP_COLOR_AWARE;
            return PF_Err_NONE;
        case PF_Cmd_PARAMS_SETUP:
            out->num_params = 1;
            return PF_Err_NONE;
        case PF_Cmd_RENDER:
            return render(output);
        default:
            return PF_Err_NONE;
    }
}

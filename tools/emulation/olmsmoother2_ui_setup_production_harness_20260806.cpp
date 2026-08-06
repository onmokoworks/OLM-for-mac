#include <cstdio>
#include <cstdint>
#include <cstring>
#include "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"

static uint32_t raw_pixel(const PF_UnionablePixel &pixel) {
    uint32_t value = 0;
    std::memcpy(&value, &pixel, sizeof(value));
    return value;
}

static uint64_t raw_double(PF_FpLong value) {
    uint64_t bits = 0;
    std::memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static PF_Err capture(PF_ProgPtr, PF_ParamIndex, PF_ParamDefPtr def) {
    std::printf("%u\t%u\t%u\t%u\t%s\t", def->uu.id, def->param_type,
                def->flags, def->ui_flags, def->name);
    switch (def->param_type) {
    case PF_Param_CHECKBOX:
        std::printf("%d,%d", def->u.bd.value, def->u.bd.dephault);
        break;
    case PF_Param_COLOR:
        std::printf("%u,%u", raw_pixel(def->u.cd.value), raw_pixel(def->u.cd.dephault));
        break;
    case PF_Param_SLIDER:
        std::printf("%d,%d,%d,%d,%d,%d", def->u.sd.value, def->u.sd.valid_min,
                    def->u.sd.valid_max, def->u.sd.slider_min,
                    def->u.sd.slider_max, def->u.sd.dephault);
        break;
    case PF_Param_POPUP:
        std::printf("%d,%d,%d,%s", def->u.pd.value, def->u.pd.num_choices,
                    def->u.pd.dephault, def->u.pd.u.namesptr);
        break;
    case PF_Param_FLOAT_SLIDER:
        std::printf("%016llx,%016llx,%016llx,%016llx,%016llx,%016llx,%016llx,%d,%d,%u,%016llx,%d,%016llx",
                    (unsigned long long)raw_double(def->u.fs_d.value),
                    (unsigned long long)raw_double(def->u.fs_d.phase),
                    (unsigned long long)raw_double(def->u.fs_d.valid_min),
                    (unsigned long long)raw_double(def->u.fs_d.valid_max),
                    (unsigned long long)raw_double(def->u.fs_d.slider_min),
                    (unsigned long long)raw_double(def->u.fs_d.slider_max),
                    (unsigned long long)raw_double(def->u.fs_d.dephault),
                    def->u.fs_d.precision, def->u.fs_d.display_flags,
                    def->u.fs_d.fs_flags,
                    (unsigned long long)raw_double(def->u.fs_d.curve_tolerance),
                    def->u.fs_d.useExponent,
                    (unsigned long long)raw_double(def->u.fs_d.exponent));
        break;
    default:
        return PF_Err_BAD_CALLBACK_PARAM;
    }
    std::putchar('\n');
    return PF_Err_NONE;
}

int main() {
    PF_InData in{};
    PF_OutData global{}, params{};
    in.inter.add_param = capture;
    int global_error = EffectMain(PF_Cmd_GLOBAL_SETUP, &in, &global, nullptr, nullptr, nullptr);
    int params_error = EffectMain(PF_Cmd_PARAMS_SETUP, &in, &params, nullptr, nullptr, nullptr);
    std::fprintf(stderr, "%d %u %u %u %d %d\n", global_error, global.my_version,
                 global.out_flags, global.out_flags2, params_error, params.num_params);
    return global_error || params_error ? 1 : 0;
}

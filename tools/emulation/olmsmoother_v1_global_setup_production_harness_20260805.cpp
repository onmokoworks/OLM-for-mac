#include <cstdio>
#include <new>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

int main() {
    PF_InData in{};
    PF_OutData out{};
    const PF_Err err = EffectMain(PF_Cmd_GLOBAL_SETUP, &in, &out, nullptr, nullptr, nullptr);
    std::printf("{\"error\":%d,\"my_version\":%u,\"out_flags\":%u,\"out_flags2\":%u}\n",
                static_cast<int>(err), static_cast<unsigned>(out.my_version),
                static_cast<unsigned>(out.out_flags),
                static_cast<unsigned>(out.out_flags2));
    return err == PF_Err_NONE ? 0 : 1;
}

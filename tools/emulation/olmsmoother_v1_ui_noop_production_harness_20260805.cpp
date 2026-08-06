#include <cstdio>
#include <new>
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"
int main(){
 auto bad=[](uintptr_t p){return reinterpret_cast<void*>(p);};
 int u=EffectMain(static_cast<PF_Cmd>(13),reinterpret_cast<PF_InData*>(bad(0x11111111)),reinterpret_cast<PF_OutData*>(bad(0x22222222)),reinterpret_cast<PF_ParamDef**>(bad(0x33333333)),reinterpret_cast<PF_LayerDef*>(bad(0x44444444)),bad(0x55555555));
 int v=EffectMain(static_cast<PF_Cmd>(14),reinterpret_cast<PF_InData*>(bad(0x11111111)),reinterpret_cast<PF_OutData*>(bad(0x22222222)),reinterpret_cast<PF_ParamDef**>(bad(0x33333333)),reinterpret_cast<PF_LayerDef*>(bad(0x44444444)),bad(0x55555555));
 std::printf("{\"user_changed_param\":%d,\"update_params_ui\":%d}\n",u,v);return (u||v)?1:0;
}

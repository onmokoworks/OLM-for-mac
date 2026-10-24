// Synthetic bundle: PreRender has no pixels. SMART_RENDER must not be called.
#include "AE_Effect.h"
extern "C" __attribute__((visibility("default"))) PF_Err EffectMain(
 PF_Cmd cmd,PF_InData*,PF_OutData *out,PF_ParamDef**,PF_LayerDef*,void *extra) {
 if(cmd==PF_Cmd_GLOBAL_SETUP)out->out_flags2=PF_OutFlag2_SUPPORTS_SMART_RENDER;
 if(cmd==PF_Cmd_PARAMS_SETUP)out->num_params=1;
 if(cmd==PF_Cmd_SMART_PRE_RENDER) {
  auto *e=static_cast<PF_PreRenderExtra*>(extra);
  e->output->result_rect={0,0,0,0};e->output->max_result_rect={0,0,11,7};
 }
 return cmd==PF_Cmd_SMART_RENDER?777:0;
}

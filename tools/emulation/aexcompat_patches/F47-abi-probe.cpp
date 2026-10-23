#include "AEConfig.h"
#include "AE_Effect.h"
#include "AE_EffectCB.h"
#include <cstdio>
#include <cstddef>
int main() {
#define S(t) printf(#t " %zu\n", sizeof(t));
#define O(t,f) printf(#t "." #f " %zu\n", offsetof(t,f));
S(PF_InData) S(PF_OutData) S(PF_ParamDef) S(PF_LayerDef) S(PF_InteractCallbacks)
O(PF_InData,utils) O(PF_InData,effect_ref) O(PF_InData,pica_basicP)
O(PF_ParamDef,u) O(PF_LayerDef,data)
}

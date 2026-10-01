#include "../../mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
#include <cstdio>
#include <cstring>
static int calls=0,choices=0,labels=0;
static PF_Err AddParam(PF_ProgPtr,A_long,PF_ParamDef*def) {
 ++calls;
 if(calls==OLMDIRECTIONALBLUR_NOISE_TYPE) {
  if(def->param_type!=PF_Param_POPUP)return PF_Err_BAD_CALLBACK_PARAM;
  choices=def->u.pd.num_choices;
  labels=1;for(const char*p=def->u.pd.u.namesptr;*p;++p)if(*p=='|')++labels;
 }
 return PF_Err_NONE;
}
int main(){PF_InData in{};PF_OutData out{};in.inter.add_param=AddParam;
 PF_Err err=EffectMain(PF_Cmd_PARAMS_SETUP,&in,&out,nullptr,nullptr,nullptr);
 printf("ERROR %d\nCOUNT %d\nCHOICES %d\nLABELS %d\n",int(err),calls,choices,labels);
 return err?1:0;
}

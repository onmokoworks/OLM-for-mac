// Included after the production UI handler, compiled against the real Mac SDK.
#include <iostream>
#include <cstring>
#include <cstdint>
static PF_ParamDef defs[256];
static int hidden[256], effects_live, streams_live;
static AEGP_PFInterfaceSuite1 interface_suite{};
static AEGP_StreamSuite2 streams2{};
static AEGP_StreamSuite6 streams6{};
static AEGP_DynamicStreamSuite3 dynamic3{};
static AEGP_DynamicStreamSuite4 dynamic4{};
static AEGP_EffectSuite3 effects3{};
static AEGP_EffectSuite5 effects5{};
static PF_ParamUtilsSuite3 param_utils{};
static A_Err new_effect(AEGP_PluginID, PF_ProgPtr, AEGP_EffectRefH *out) {
    ++effects_live; *out=reinterpret_cast<AEGP_EffectRefH>(1); return 0;
}
static A_Err new_stream(AEGP_PluginID, AEGP_EffectRefH, PF_ParamIndex slot, AEGP_StreamRefH *out) {
    ++streams_live; *out=reinterpret_cast<AEGP_StreamRefH>(intptr_t(slot+1)); return 0;
}
static A_Err dispose_stream(AEGP_StreamRefH) {--streams_live; return 0;}
static A_Err dispose_effect(AEGP_EffectRefH) {--effects_live; return 0;}
static A_Err get_flags(AEGP_StreamRefH s, AEGP_DynStreamFlags *out) {
    *out=hidden[intptr_t(s)-1] ? AEGP_DynStreamFlag_HIDDEN : 0; return 0;
}
static A_Err set_hidden(AEGP_StreamRefH s, AEGP_DynStreamFlags flag, A_Boolean undo, A_Boolean value) {
    if(flag!=AEGP_DynStreamFlag_HIDDEN || undo) return 99;
    int slot=intptr_t(s)-1; hidden[slot]=bool(value);
    std::cout<<"H "<<slot<<" "<<bool(value)<<"\n"; return 0;
}
static PF_Err update(PF_ProgPtr, PF_ParamIndex slot, const PF_ParamDef *p) {
    // Name and value must not change as a side effect of UI updates.
    if(std::memcmp(p->name,defs[slot].name,sizeof(p->name)) ||
       std::memcmp(&p->u,&defs[slot].u,sizeof(p->u))) return 98;
    defs[slot].ui_flags=p->ui_flags;
    std::cout<<"D "<<slot<<" "<<p->ui_flags<<"\n"; return 0;
}
static PF_Err checkout(PF_ProgPtr, PF_ParamIndex slot, A_long, A_long, A_u_long, PF_ParamDef *p) {
    *p=defs[slot]; return 0;
}
static PF_Err checkin(PF_ProgPtr, PF_ParamDef *) {return 0;}
static SPErr acquire(const char *name, int32_t version, const void **out) {
#define SUITE(n,v,obj) if(!std::strcmp(name,n)&&version==v){*out=&obj;return 0;}
    SUITE(kAEGPPFInterfaceSuite,kAEGPPFInterfaceSuiteVersion1,interface_suite)
    SUITE(kAEGPStreamSuite,kAEGPStreamSuiteVersion2,streams2)
    SUITE(kAEGPStreamSuite,kAEGPStreamSuiteVersion6,streams6)
    SUITE(kAEGPDynamicStreamSuite,kAEGPDynamicStreamSuiteVersion3,dynamic3)
    SUITE(kAEGPDynamicStreamSuite,kAEGPDynamicStreamSuiteVersion4,dynamic4)
    SUITE(kAEGPEffectSuite,kAEGPEffectSuiteVersion3,effects3)
    SUITE(kAEGPEffectSuite,kAEGPEffectSuiteVersion5,effects5)
    SUITE(kPFParamUtilsSuite,kPFParamUtilsSuiteVersion3,param_utils)
#undef SUITE
    std::cerr<<"unsupported "<<name<<" "<<version<<"\n"; return 97;
}
static SPErr release(const char *, int32_t) {return 0;}
int main() {
    interface_suite.AEGP_GetNewEffectForEffect=new_effect;
    streams2.AEGP_GetNewEffectStreamByIndex=new_stream; streams2.AEGP_DisposeStream=dispose_stream;
    streams6.AEGP_GetNewEffectStreamByIndex=new_stream; streams6.AEGP_DisposeStream=dispose_stream;
    dynamic3.AEGP_SetDynamicStreamFlag=set_hidden; dynamic3.AEGP_GetDynamicStreamFlags=get_flags;
    dynamic4.AEGP_SetDynamicStreamFlag=set_hidden; dynamic4.AEGP_GetDynamicStreamFlags=get_flags;
    effects3.AEGP_DisposeEffect=dispose_effect; effects5.AEGP_DisposeEffect=dispose_effect;
    param_utils.PF_UpdateParamUI=update;
    SPBasicSuite basic{}; basic.AcquireSuite=acquire; basic.ReleaseSuite=release;
    PF_InData in{}; in.pica_basicP=&basic; in.current_time=7; in.time_step=1; in.time_scale=24;
    in.inter.checkout_param=checkout; in.inter.checkin_param=checkin;
    PF_ParamDef *params[256]; for(int i=0;i<256;++i) params[i]=&defs[i];
    int n;
    while(std::cin>>n) {
        for(int i=1;i<=n;++i) {
            int type,flags,h; double value;
            std::cin>>type>>flags>>h>>value;
            defs[i]={}; defs[i].param_type=PF_ParamType(type); defs[i].ui_flags=flags; hidden[i]=h;
            std::snprintf(defs[i].name,sizeof(defs[i].name),"sentinel %d",i);
            switch(type) {
                case PF_Param_CHECKBOX: defs[i].u.bd.value=value; break;
                case PF_Param_POPUP: defs[i].u.pd.value=value; break;
                case PF_Param_SLIDER: defs[i].u.sd.value=value; break;
                case PF_Param_FLOAT_SLIDER: defs[i].u.fs_d.value=value; break;
                default: break;
            }
        }
        int err=INVOKE_UI;
        std::cout<<"E "<<err<<" "<<effects_live<<" "<<streams_live<<"\n";
        for(int i=1;i<=n;++i) std::cout<<"S "<<i<<" "<<defs[i].ui_flags<<" "<<hidden[i]<<"\n";
        std::cout<<"END\n";
        if(err || effects_live || streams_live) return 1;
    }
}

// F52 opt-in geometry for source-recompiled hosts. Included AFTER plugin .cpp.
#pragma once
#include <cstdlib>
#include <cstdio>
static void f52_input(PF_InData *in) {
    const char *v=std::getenv("OLM_F52_DOWNSAMPLE");
    if(!v) return;
    int w,h,xn,xd,yn,yd;
    if(std::sscanf(v,"%d,%d,%d,%d,%d,%d",&w,&h,&xn,&xd,&yn,&yd)!=6 ||
       w<=0 || h<=0 || xn<=0 || xd<xn || yn<=0 || yd<yn) std::abort();
    in->width=w; in->height=h;
    in->downsample_x={xn,static_cast<A_u_long>(xd)};
    in->downsample_y={yn,static_cast<A_u_long>(yd)};
}
static PF_Err f52_entry(PF_Cmd cmd,PF_InData *in,PF_OutData *out,PF_ParamDef **params,PF_LayerDef *world,void *extra) {
    f52_input(in);
    return EffectMain(cmd,in,out,params,world,extra);
}
#define EffectMain f52_entry

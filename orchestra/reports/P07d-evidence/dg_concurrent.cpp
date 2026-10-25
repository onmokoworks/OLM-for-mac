#include <thread>
#include <chrono>
#include <cassert>
int main() {
    PF_ParamDef defs[DG_NUM_PARAMS]{}; PF_ParamDef* params[DG_NUM_PARAMS];
    for(int i=0;i<DG_NUM_PARAMS;++i)params[i]=defs+i;
    defs[DG_INVERT].u.bd.value=1;defs[DG_IN_OUT].u.pd.value=IN_OUT_INSIDE;
    defs[DG_INSIDE_THRESHOLD].u.sd.value=4;defs[DG_OUTSIDE_THRESHOLD].u.sd.value=4;
    defs[DG_RENDER_MODE].u.pd.value=RENDER_MODE_RGB;
    defs[DG_GRAD_COLOR].u.cd.value={255,28,0,238};defs[DG_BG_COLOR].u.cd.value={255,16,160,48};
    defs[DG_INTERP_MODE].u.pd.value=INTERP_LINEAR;defs[DG_POWER].u.fs_d.value=2.25;
    defs[DG_BLUR_MODE].u.pd.value=BLUR_MODE_NO_SCALE;defs[DG_BLUR_SIZE].u.sd.value=1;
    for(int side:{128,255,256,512,1080}){
        int w=side==1080?1920:side,h=side;
        std::vector<PF_Pixel8> input(w*h),reference,outputs[4];
        for(int i=0;i<w*h;++i)input[i]={255,(unsigned char)(i%256),(unsigned char)(i%251),(unsigned char)(i%241)};
        for(auto& v:outputs)v.resize(w*h);
        for(int renders:{1,4})for(const char* cap:{"1","2","8"}){
            setenv("OLM_PARALLEL_MAX",cap,1);
            for(int repeat=0;repeat<3;++repeat){
                auto render=[&](int lane){
                    PF_EffectWorld iw{input.data(),w,h,w*4,8,{0,0,w,h}},ow=iw;ow.data=outputs[lane].data();
                    PF_InData in{};in.width=w;in.height=h;in.downsample_x={1,1};in.downsample_y={1,1};
                    assert(RenderBits<PF_Pixel8>(&in,params,&iw,&ow,true)==0);
                };
                auto begin=std::chrono::steady_clock::now();
                if(renders==1)render(0);else{std::thread a(render,0),b(render,1),c(render,2),d(render,3);a.join();b.join();c.join();d.join();}
                double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
                if(reference.empty())reference=outputs[0];
                for(int lane=0;lane<renders;++lane)assert(memcmp(reference.data(),outputs[lane].data(),reference.size()*sizeof(PF_Pixel8))==0);
                printf("%d %d %d %s %d %.9f exact\n",w,h,renders,cap,repeat,seconds);fflush(stdout);
            }
        }
    }
}

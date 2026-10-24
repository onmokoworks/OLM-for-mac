#include <thread>
#include <chrono>
#include <cassert>
int main() {
    constexpr int w=1920,h=1080;
    init_params(kTuples[0]);
    PF_InData in{}; in.pica_basicP=&g_basic;
    PF_ParamDef* params[OLMKIRAKIRA_NUM_PARAMS];
    for(int i=0;i<OLMKIRAKIRA_NUM_PARAMS;++i) params[i]=g_defs+i;
    g_defs[0].u.ld.width=w;
    OLMKiraKiraInfo info{};
    assert(ReadRenderInfo(&in,params,&info)==0);
    info.vertical_length=info.horizontal_length=info.diagonal_length=info.diagonal2_length=100;
    std::vector<PF_Pixel8> input(w*h);
    for(int i=0;i<w*h;++i) input[i]={255,(A_u_char)(i%256),(A_u_char)(i%251),(A_u_char)(i%241)};
    std::vector<PF_Pixel8> outputs[4],reference;
    for(auto& output:outputs) output.resize(w*h);
    auto render=[&](int lane){
        PF_EffectWorld iw{},ow{};iw.width=w;iw.height=h;iw.rowbytes=w*sizeof(PF_Pixel8);iw.data=reinterpret_cast<PF_PixelPtr>(input.data());
        ow=iw;ow.data=reinterpret_cast<PF_PixelPtr>(outputs[lane].data());
        assert(RenderTyped<PF_Pixel8>(&iw,&ow,info,8,1.0f)==0);
    };
    for(const char* tasks:{"1","2","8"}) {
        setenv("OLM_PARALLEL_MAX",tasks,1);
        for(int repeat=0;repeat<3;++repeat) {
            auto begin=std::chrono::steady_clock::now();
            std::thread a(render,0),b(render,1),c(render,2),d(render,3);
            a.join();b.join();c.join();d.join();
            double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
            if(reference.empty()) reference=outputs[0];
            for(auto& output:outputs) assert(memcmp(output.data(),reference.data(),output.size()*sizeof(PF_Pixel8))==0);
            printf("tasks=%s repeat=%d four_renders_seconds=%.9f exact\n",tasks,repeat,elapsed);
        }
    }
}

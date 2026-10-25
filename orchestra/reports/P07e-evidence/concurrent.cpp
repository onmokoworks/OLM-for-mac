#include "production_under_test.cpp"
#include <chrono>
#include <cassert>
#include <thread>
int main() {
    for (int w : {64,128,240}) {
        const int h=w;
        OLMRadialBlurInfo info{};
        info.blur_type=2; info.center_x=w/2.; info.center_y=h/2.;
        info.outer_strength=30; info.inner_strength=10;
        info.outer_edge_fade=15; info.inner_edge_fade=10;
        info.outer_offset_mode=info.inner_offset_mode=1;
        info.repeat_border=TRUE; info.ratio=1; info.quality=5;
        info.brightness_gain=1; info.noise_type=1; info.seed=1; info.thickness=10;
        info.comp_width=w; info.comp_height=h;
        std::vector<PF_Pixel8> input(w*h), outputs[4], reference;
        for(int i=0;i<w*h;++i) input[i]={255,(A_u_char)(i%256),(A_u_char)(i%251),(A_u_char)(i%241)};
        for(auto& output:outputs) output.resize(w*h);
        auto render=[&](int lane) {
            PF_EffectWorld iw{},ow{};
            iw.width=w; iw.height=h; iw.rowbytes=w*sizeof(PF_Pixel8);
            iw.extent_hint={0,0,w,h}; iw.data=reinterpret_cast<PF_PixelPtr>(input.data());
            ow=iw; ow.data=reinterpret_cast<PF_PixelPtr>(outputs[lane].data());
            assert(RenderRotationTyped<PF_Pixel8>(&iw,&ow,info)==0);
        };
        for(const char* tasks:{"1","2","8"}) {
            setenv("OLM_PARALLEL_MAX",tasks,1);
            for (int lanes : {1,4}) for(int repeat=0;repeat<3;++repeat) {
                const auto begin=std::chrono::steady_clock::now();
                if(lanes==1) render(0);
                else { std::thread a(render,0),b(render,1),c(render,2),d(render,3);
                    a.join();b.join();c.join();d.join(); }
                double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
                if(reference.empty()) reference=outputs[0];
                for(int lane=0;lane<lanes;++lane)
                    assert(memcmp(outputs[lane].data(),reference.data(),reference.size()*sizeof(PF_Pixel8))==0);
                printf("size=%d tasks=%s lanes=%d repeat=%d seconds=%.9f exact\n",w,tasks,lanes,repeat,elapsed);
                fflush(stdout);
            }
        }
    }
}

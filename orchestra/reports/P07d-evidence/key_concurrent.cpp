#include <thread>
#include <chrono>
#include <cassert>
int main() {
    OLMColorKeyInfo info{};
    info.color_space=4;info.force_lower_precision=1;info.number_of_colors=24;
    info.distance_step_x=info.distance_step_y=1;
    for(int i=0;i<24;++i){info.use_color[i]=1;info.colors[i]={1.f,i/24.f,(23-i)/24.f,.5f};}
    for(int side:{128,255,256,512,1080}){
        int w=side==1080?1920:side,h=side;
        std::vector<PF_Pixel8> input(w*h),reference,outputs[4];
        for(int i=0;i<w*h;++i)input[i]={255,(A_u_char)(i%256),(A_u_char)(i%251),(A_u_char)(i%241)};
        for(auto& v:outputs)v.resize(w*h);
        for(int renders:{1,4})for(const char* cap:{"1","2","8"}){
            setenv("OLM_PARALLEL_MAX",cap,1);
            for(int repeat=0;repeat<3;++repeat){
                auto render=[&](int lane){PF_EffectWorld iw{},ow{};iw.width=w;iw.height=h;iw.rowbytes=w*sizeof(PF_Pixel8);iw.data=(PF_PixelPtr)input.data();ow=iw;ow.data=(PF_PixelPtr)outputs[lane].data();assert(RenderTyped<PF_Pixel8>(&iw,&ow,info)==0);};
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

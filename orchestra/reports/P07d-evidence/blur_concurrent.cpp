#include "olmblur_worker_orchestration.h"
#include <thread>
#include <chrono>
#include <vector>
#include <cstdio>
#include <cstdlib>
#include <cassert>
int main() {
    const olm::blur::worker::Params params{30,100,3,1};
    for (const int side : {128,255,256,512,1080}) {
        const int w=side==1080?1920:side,h=side;
        std::vector<std::uint8_t> input(w*h*4), reference;
        for (int i=0;i<w*h;++i) {
            input[i*4]=255;input[i*4+1]=i%256;input[i*4+2]=i%251;input[i*4+3]=i%241;
        }
        std::vector<std::uint8_t> output[4];
        for (auto& v:output)v.resize(input.size());
        for (const int renders : {1,4}) for (const char* cap : {"1","2","8"}) {
            setenv("OLM_PARALLEL_MAX",cap,1);
            for (int repeat=0;repeat<3;++repeat) {
                const auto begin=std::chrono::steady_clock::now();
                auto render=[&](int lane){olm::blur::worker::render_8bpc_nonlegacy(input.data(),output[lane].data(),w,h,params);};
                if(renders==1)render(0);
                else {std::thread a(render,0),b(render,1),c(render,2),d(render,3);a.join();b.join();c.join();d.join();}
                const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
                if(reference.empty())reference=output[0];
                for(int i=0;i<renders;++i)assert(output[i]==reference);
                printf("%d %d %d %s %d %.9f exact\n",w,h,renders,cap,repeat,seconds);fflush(stdout);
            }
        }
    }
}

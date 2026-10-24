#include "core/kirakira_warp.h"
#include <chrono>
#include <cstdio>
#include <cstring>
#include <thread>

int main() {
    for (int size : {64,128,192,256,384,512,1080}) {
        std::vector<float> input(size*size);
        for (std::size_t i=0;i<input.size();++i) input[i]=float(i%257)/256;
        std::vector<float> reference;
        for (const char* tasks : {"1","2","8"}) {
            setenv("OLM_PARALLEL_MAX",tasks,1);
            auto start=std::chrono::steady_clock::now();
            std::vector<float> output;
            for (int repeat=0;repeat<20;++repeat)
                output=olm::kirakira::warp_get_rotation_matrix_2d(input,size,size,size,size,size/2.,size/2.,22.);
            auto seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()/20;
            if(reference.empty()) reference=output;
            if(std::memcmp(reference.data(),output.data(),output.size()*sizeof(float))) return 1;
            std::printf("%d %s %.9f exact\n",size,tasks,seconds);
        }
    }
}

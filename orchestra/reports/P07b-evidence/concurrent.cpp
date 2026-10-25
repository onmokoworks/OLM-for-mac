// Include the standard public host to reuse its exact parameter parser/shim.
#define main public_host_main
#include "host.cpp"
#undef main
#include <thread>
#include <atomic>
#include <chrono>
#include <array>
#include <cassert>
int main(int argc, char** argv) {
    if(argc != 5) return 2;
    int w=atoi(argv[1]),h=atoi(argv[2]),repeats=atoi(argv[3]);
    if(!load_parameters(argv[4])) return 3;
    PF_InData in{}; PF_ParamDef* params[SM_NUM_PARAMS];
    for(int i=0;i<SM_NUM_PARAMS;++i) params[i]=definitions+i;
    SMParams p{}; if(FetchParams(&in,params,&p)) return 4;
    std::vector<PF_PixelFloat> input(size_t(w)*h);
    for(size_t i=0;i<input.size();++i) input[i]={1.0f,float(i%31)/31,float(i%67)/67,float(i%127)/127};
    std::array<std::vector<PF_PixelFloat>,4> output;
    for(auto& v:output) v.resize(input.size());
    auto render=[&](int i) {
        PF_LayerDef iw{},ow{}; iw.width=w;iw.height=h;iw.rowbytes=w*sizeof(PF_PixelFloat);iw.data=input.data();iw.bitdepth=32;
        ow=iw;ow.data=output[i].data();PF_InData local{};
        for(int n=0;n<repeats;++n) if(RenderBits<PF_PixelFloat>(&local,nullptr,&iw,&ow,&p)) std::abort();
    };
    auto begin=std::chrono::steady_clock::now();
    render(0);
    double single=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()/repeats;
    auto expected=output[0];
    std::atomic<int> ready{0};std::atomic<bool> go{false};
    std::array<std::thread,4> threads;
    for(int i=0;i<4;++i) threads[i]=std::thread([&,i]{++ready;while(!go.load())std::this_thread::yield();render(i);});
    while(ready.load()!=4) std::this_thread::yield();
    begin=std::chrono::steady_clock::now();go=true;
    for(auto& t:threads)t.join();
    double concurrent=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()/repeats;
    for(auto& v:output) if(memcmp(v.data(),expected.data(),v.size()*sizeof(PF_PixelFloat)))return 5;
    olm::Sha256 hash; hash.update(expected.data(),expected.size()*sizeof(PF_PixelFloat));
    uint8_t digest[32];hash.final(digest);char hex[65];
    for(int i=0;i<32;++i)snprintf(hex+2*i,3,"%02x",digest[i]);
    printf("{\"width\":%d,\"height\":%d,\"single_seconds\":%.9f,\"four_seconds\":%.9f,\"exact\":true,\"sha256\":\"%s\"}\n",w,h,single,concurrent,hex);
}

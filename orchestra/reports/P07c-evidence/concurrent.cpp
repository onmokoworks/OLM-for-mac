#include <thread>
#include <chrono>
#include <cassert>
#include <memory>
static void fill(Fixture &f) {
    for(int y=0;y<f.iw.height;++y)for(int x=0;x<f.iw.width;++x){
        const unsigned v=((x/11+y/7)%3)?255:0;
        if(f.iw.bitdepth==8){PF_Pixel8 p{255,(uint8_t)v,(uint8_t)v,(uint8_t)v};memcpy(f.input.data()+y*f.iw.rowbytes+x*4,&p,4);}
        else {const uint16_t v16=v?32768:0;PF_Pixel16 p{32768,v16,v16,v16};memcpy(f.input.data()+y*f.iw.rowbytes+x*8,&p,8);}
    }
}
static double render(Fixture &f) {
    PF_InData in{};PF_OutData out{};in.time_step=1;in.time_scale=24;
    const auto start=std::chrono::steady_clock::now();
    const auto error=EffectMain(PF_Cmd_RENDER,&in,&out,f.params,&f.ow,nullptr);
    assert(error==0);
    return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
}
int main(){
    for(int depth:{8,16})for(int tolerance:{6,23}) {
        std::vector<std::unique_ptr<Fixture>> frames;
        for(int i=0;i<4;++i){frames.emplace_back(new Fixture(depth,1920,1080,0));fill(*frames.back());frames.back()->defs[SM_TOLERANCE].u.sd.value=tolerance;}
        std::vector<unsigned char> expected;
        for(int repeat=0;repeat<5;++repeat)for(int cap:{1,8}){
            setenv("OLM_PARALLEL_MAX",cap==1?"1":"8",1);
            const auto start=std::chrono::steady_clock::now();
            std::vector<std::thread> tasks;
            for(int i=0;i<4;++i)tasks.emplace_back([&,i]{render(*frames[i]);});
            for(auto &t:tasks)t.join();
            const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
            if(cap==1)expected=frames[0]->output;
            for(auto &f:frames)assert(f->output==expected);
            printf("concurrent depth=%d tolerance=%d cap=%d repeat=%d seconds=%.9f exact=4\n",depth,tolerance,cap,repeat,seconds);fflush(stdout);
        }
    }
    for(int depth:{8,16})for(int size:{64,128,192,256,384,512}){
        Fixture f(depth,size,size,0);fill(f);
        std::vector<unsigned char> expected;
        for(int cap:{1,8}){
            setenv("OLM_PARALLEL_MAX",cap==1?"1":"8",1);
            render(f);double seconds=0;for(int i=0;i<5;++i)seconds+=render(f);
            if(cap==1)expected=f.output;else assert(expected==f.output);
            printf("threshold depth=%d size=%d cap=%d seconds=%.9f\n",depth,size,cap,seconds/5);fflush(stdout);
        }
    }
}

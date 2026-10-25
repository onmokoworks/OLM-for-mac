// Appended to the existing public SDK host by persistence.py.
#include <cassert>
#include <iostream>
int main() {
    PF_InData in{}; in.pica_basicP=&g_basic;
    OLMKiraKiraRampData ramp{};
    unsigned count=0;
    while (std::cin.read(reinterpret_cast<char*>(&ramp),sizeof(ramp))) {
        assert(ramp.count<=16);
        PF_ArbitraryH first=nullptr, second=nullptr, copied=nullptr;
        assert(NewRampHandle(&in,ramp,&first)==0);
        unsigned char flat[0x145]{}, again[0x145]{};
        PF_ArbParamsExtra e{};
        e.which_function=PF_Arbitrary_FLATTEN_FUNC;
        e.u.flatten_func_params.arbH=first;
        e.u.flatten_func_params.buf_sizeLu=sizeof(flat);
        e.u.flatten_func_params.flat_dataPV=flat;
        assert(RampArbitraryCallback(&in,&e)==0 && flat[0]==1);
        assert(!std::memcmp(flat+1,&ramp,4+20*ramp.count));
        for(unsigned i=5+20*ramp.count;i<sizeof(flat);++i) assert(flat[i]==0);
        e={};e.which_function=PF_Arbitrary_UNFLATTEN_FUNC;
        e.u.unflatten_func_params.flat_dataPV=flat;
        e.u.unflatten_func_params.buf_sizeLu=sizeof(flat);
        e.u.unflatten_func_params.arbPH=&second;
        assert(RampArbitraryCallback(&in,&e)==0);
        e={};e.which_function=PF_Arbitrary_COPY_FUNC;
        e.u.copy_func_params.src_arbH=second;e.u.copy_func_params.dst_arbPH=&copied;
        assert(RampArbitraryCallback(&in,&e)==0);
        e={};e.which_function=PF_Arbitrary_FLATTEN_FUNC;
        e.u.flatten_func_params.arbH=copied;e.u.flatten_func_params.buf_sizeLu=sizeof(again);
        e.u.flatten_func_params.flat_dataPV=again;
        assert(RampArbitraryCallback(&in,&e)==0 && !std::memcmp(flat,again,sizeof(flat)));
        for(auto h:{first,second,copied}) {
            e={};e.which_function=PF_Arbitrary_DISPOSE_FUNC;e.u.dispose_func_params.arbH=h;
            assert(RampArbitraryCallback(&in,&e)==0);
        }
        ++count;
    }
    assert(count==34 && g_sizes.empty());
    std::cout << "34 original valid presets: callback flatten/unflatten/copy/flatten byte-identical; zero live handles\n";
}

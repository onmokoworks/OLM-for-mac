#include <cstdio>
#include <new>
#include <string>
#include <vector>

struct CapturedParam { std::string name, kind; int a, b, c, d, value, disk; };
static std::vector<CapturedParam> captured;
static void olmsmoother_capture_checkbox(const char*n,int v,int disk){captured.push_back({n,"checkbox",0,1,0,1,v,disk});}
static void olmsmoother_capture_color(const char*n,int r,int g,int b,int disk){captured.push_back({n,"color",r,g,b,255,0,disk});}
static void olmsmoother_capture_slider(const char*n,int vmin,int vmax,int smin,int smax,int v,int disk){captured.push_back({n,"slider",vmin,vmax,smin,smax,v,disk});}
#define OLMSMOOTHER_CAPTURE_PARAMS 1
#include "../../mac/OLMSmoother/Mac/OLMSmoother_port.cpp"

int main(){
 PF_InData in{}; PF_OutData out{};
 int err=EffectMain(PF_Cmd_PARAMS_SETUP,&in,&out,nullptr,nullptr,nullptr);
 std::printf("{\"error\":%d,\"num_params\":%d,\"parameters\":[",err,(int)out.num_params);
 for(size_t i=0;i<captured.size();++i){auto&p=captured[i];if(i)std::printf(",");
  std::printf("{\"name\":\"%s\",\"kind\":\"%s\",\"a\":%d,\"b\":%d,\"c\":%d,\"d\":%d,\"value\":%d,\"disk_id\":%d}",p.name.c_str(),p.kind.c_str(),p.a,p.b,p.c,p.d,p.value,p.disk);}
 std::puts("]}"); return err?1:0;
}

// F52c standalone bundle transport with explicit negotiated geometry.
#define OLM_F52_BUNDLE_GEOMETRY 1
#include "F47d-native-bridge.cpp"
#include "../../fuzz/harnesses/parameters.hpp"
#include <iostream>

int main(int argc, char **argv) {
 if(argc!=9) { std::fprintf(stderr,"usage: host executable width height depth padding smart declarations parameters\n"); return 2; }
 const int w=std::atoi(argv[2]), h=std::atoi(argv[3]), depth=std::atoi(argv[4]);
 const int pad=std::atoi(argv[5]), smart=std::atoi(argv[6]);
 if(w<1 || h<1 || w>4096 || h>4096 || pad<0 || pad>4096 || (depth!=8 && depth!=16 && depth!=32)) return 2;
 std::ifstream declarations(argv[7]); int count=0;
 if(!(declarations>>count) || count<1 || count>4096) return 2;
 std::vector<PF_ParamDef> defs(count);
 for(auto &d:defs) { int type; if(!(declarations>>type)) return 2; d.param_type=static_cast<PF_ParamType>(type); }
 if(!fuzz_parameters(argv[8],defs.data(),count)) return 2;
 const int packed=w*(depth/8)*4, stride=packed+pad;
 std::vector<unsigned char> input(size_t(stride)*h,0xA5),output_bytes(size_t(stride)*h,0);
 for(int y=0;y<h;++y) if(!std::cin.read(reinterpret_cast<char*>(input.data()+size_t(y)*stride),packed)) return 2;
 if(std::cin.peek()!=EOF) return 2;
 PF_EffectWorld src{},dst{};
 src.width=dst.width=w; src.height=dst.height=h;
 src.rowbytes=stride; dst.rowbytes=stride;
 src.world_flags=dst.world_flags=depth==16?PF_WorldFlag_DEEP:0;
 src.extent_hint=dst.extent_hint={0,0,w,h};
 src.pix_aspect_ratio=dst.pix_aspect_ratio={1,1};
 PF_InData in{};
 in.effect_ref=reinterpret_cast<PF_ProgPtr>(1); in.quality=PF_Quality_HI;
 in.version.major=13; in.version.minor=29; in.appl_id=0x46585443;
 in.num_params=count; in.width=w; in.height=h; in.extent_hint={0,0,w,h};
 in.time_step=in.local_time_step=1; in.time_scale=24; in.total_time=1;
 in.downsample_x=in.downsample_y=in.pixel_aspect_ratio={1,1};
 const int request[]={0,0,w,h};
 int err=f47c_render(argv[1],reinterpret_cast<unsigned char*>(&in),reinterpret_cast<unsigned char*>(defs.data()),
  reinterpret_cast<unsigned char*>(&src),reinterpret_cast<unsigned char*>(&dst),input.data(),output_bytes.data(),depth,request,count,smart);
 std::cout.write(reinterpret_cast<char*>(&err),sizeof(err));
 if(!err && smart && f52_realistic()) {
  std::ifstream rendered(std::getenv("OLM_F52_GEOMETRY_OUTPUT"),std::ios::binary);
  if(!rendered)return 3;
  char chunk[4096];
  while(rendered.read(chunk,sizeof(chunk)) || rendered.gcount())std::cout.write(chunk,rendered.gcount());
  if(rendered.bad())return 3;
 } else {
  for(int y=0;y<h;++y)std::cout.write(reinterpret_cast<char*>(output_bytes.data()+size_t(y)*stride),packed);
 }
 return std::cout?0:3;
}

#include "core/dblur_float.h"
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstdlib>
float f(uint32_t u){float x;std::memcpy(&x,&u,4);return x;}
int main(){
 const uint32_t edge[]={0,0x80000000,1,0x80000001,0x007fffff,0x00800000,0x3f800000,0xbf800000,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00000,0xffc00000,0x7f800001,0xff800001,0x7fffffff,0xffffffff};
 uint64_t count=0; uint32_t rng=20261025;
 auto check=[&](uint32_t a,uint32_t b){
  float x=f(a),y=f(b);
  float old[]={olm::x86_float::sse_add(x,y),olm::x86_float::sse_sub(x,y),olm::x86_float::sse_mul(x,y),olm::x86_float::sse_div(x,y)};
  float now[]={olm::dblur_float::add(x,y),olm::dblur_float::sub(x,y),olm::dblur_float::mul(x,y),olm::dblur_float::div(x,y)};
  for(int op=0;op<4;++op){++count;if(olm::x86_float::bits(old[op])!=olm::x86_float::bits(now[op])){printf("mismatch %08x %08x op %d old %08x new %08x\n",a,b,op,olm::x86_float::bits(old[op]),olm::x86_float::bits(now[op]));exit(1);}}
 };
 for(auto a:edge)for(auto b:edge)check(a,b);
 for(int i=0;i<4000000;++i){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;uint32_t a=rng;rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;check(a,rng);}
 printf("%llu arithmetic comparisons; 0 mismatches\n",count);
}

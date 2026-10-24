#include "core/dblur_rowdriver.h"
#include "core/dblur_rotate.h"
#include <dlfcn.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <cstdint>
static uint32_t rng=2053;
uint32_t word(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
float arbitrary(){uint32_t u=word();float x;memcpy(&x,&u,4);return x;}
void same(const std::vector<float>&a,const std::vector<float>&b,const char*stage,int test){
 for(size_t i=0;i<a.size();++i)if(memcmp(&a[i],&b[i],4)){uint32_t x,y;memcpy(&x,&a[i],4);memcpy(&y,&b[i],4);printf("mismatch %s test=%d word=%zu old=%08x new=%08x\n",stage,test,i,x,y);exit(1);}
}
int main(int argc,char**argv){
 if(argc!=3)return 2;void* a=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);void*b=dlopen(argv[2],RTLD_NOW|RTLD_LOCAL);if(!a||!b){puts(dlerror());return 2;}
 auto sa=(decltype(&olm_dblur_scatter_f32))dlsym(a,"olm_dblur_scatter_f32"), sb=(decltype(sa))dlsym(b,"olm_dblur_scatter_f32");
 for(int test=0;test<10000;++test){
  const int n=65;std::vector<float>s(n*4),x(n*4),y,dx(n),dy,alpha(n),weights(n);
  for(auto&v:s)v=test%2?arbitrary():float(int(word()%2001)-1000)/1000;
  for(auto&v:x)v=arbitrary();for(auto&v:dx)v=arbitrary();for(auto&v:alpha)v=arbitrary();for(auto&v:weights)v=arbitrary();
  // Exercise bounded fast path with finite and exceptional accumulators.
  if(test%3==0){for(auto&v:alpha)v=0.5f;for(auto&v:weights)v=0.25f;}
  y=x;dy=dx;
  sa(32,0,test%2,s.data(),x.data(),dx.data(),alpha.data(),weights.data(),63,n,1);
  sb(32,0,test%2,s.data(),y.data(),dy.data(),alpha.data(),weights.data(),63,n,1);
  same(x,y,"scatter",test);same(dx,dy,"scatter denominator",test);
 }
 auto ra=(decltype(&olm_dblur_rowdriver_f32))dlsym(a,"olm_dblur_rowdriver_f32"),rb=(decltype(ra))dlsym(b,"olm_dblur_rowdriver_f32");
 for(int test=0;test<120;++test){
  int w=17,h=65+test%3;int n=w*h;std::vector<float>s(n*4),x(n*4),y(n*4),dx(n),dy(n),ax(n),ay(n),map(n*4,1),weights(32,0.5f);
  for(auto&v:s)v=test%2?arbitrary():float(int(word()%2001)-1000)/1000;
  ra(0,h,s.data(),x.data(),w,1,1,0,1,0,0,weights.data(),weights.data(),weights.data(),weights.data(),dx.data(),ax.data(),map.data(),15,13,7,5);
  rb(0,h,s.data(),y.data(),w,1,1,0,1,0,0,weights.data(),weights.data(),weights.data(),weights.data(),dy.data(),ay.data(),map.data(),15,13,7,5);
  same(x,y,"parallel rows",test);same(dx,dy,"row denominator",test);same(ax,ay,"row alpha",test);
 }
 for(const char* name:{"olm_dblur_rotate_rgba_f32_trig","olm_dblur_rotate_scalar_f32_trig"}){
  auto fa=(decltype(&olm_dblur_rotate_rgba_f32_trig))dlsym(a,name),fb=(decltype(fa))dlsym(b,name);
  for(int test=0;test<100;++test){int w=33,h=17;std::vector<float>s(w*h*4),x(w*h*4),y;
   for(auto&v:s)v=arbitrary();for(auto&v:x)v=arbitrary();y=x;
   fa(s.data(),x.data(),w,h,test%2?0.6f:1.0f,test%2?0.8f:0.0f);fb(s.data(),y.data(),w,h,test%2?0.6f:1.0f,test%2?0.8f:0.0f);same(x,y,name,test);
  }
 }
 puts("10000 scatter, 120 parallel rowdriver, 200 rotation comparisons; 0 mismatches");
}

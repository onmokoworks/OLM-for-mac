// Read-only large-argument reduction probe; never substitutes a math result.
#define ORACLE_EMBEDDED
#include "oracle.c"
#include "remainder_piby2_f.h"
typedef void (__attribute__((ms_abi)) *reduce_fn)(uint64_t,double*,int*);
int main(int argc,char **argv){
 if(argc!=2)return 2;atexit(report_stubs);load(argv[1]);current="sinf-reduction";
 struct sigaction sa={0};sa.sa_sigaction=fault;sa.sa_flags=SA_SIGINFO;sigaction(SIGSEGV,&sa,0);sigaction(SIGBUS,&sa,0);sigaction(SIGILL,&sa,0);
 _mm_setcsr(0x1f80);
 uint32_t inputs[]={0x4c43326e,0x4d123456,0x7f7fffff,0x6c678b0d};
 puts("input,ucrt_region,amd_region,ucrt_residual,amd_residual");
 for(unsigned i=0;i<sizeof inputs/sizeof inputs[0];i++){
  in_a=inputs[i];float f;memcpy(&f,&in_a,4);double x=f,u=0,r=0;int ur=0,ar=0;uint64_t b;memcpy(&b,&x,8);
  ((reduce_fn)at(0xbafc0,1))(b,&u,&ur);remainder_piby2_f(in_a,&ar,&r);
  printf("%08x,%d,%d,%a,%a\n",in_a,ur,ar,u,r);
 }
 return 0;
}

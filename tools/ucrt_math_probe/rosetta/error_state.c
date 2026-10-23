// Check the stub state contract independently of numerical qualification.
#define ORACLE_EMBEDDED
#include "oracle.c"
int main(int argc,char **argv){
 if(argc!=2)return 2;atexit(report_stubs);
 struct sigaction sa={0};sa.sa_sigaction=fault;sa.sa_flags=SA_SIGINFO;sigaction(SIGSEGV,&sa,0);sigaction(SIGBUS,&sa,0);sigaction(SIGILL,&sa,0);
 const char *names[]={"expf","sinf","cosf","powf","powf"};
 uint32_t a[]={0x42c80000,0x7f800000,0x7f800000,0xbf800000,0};
 uint32_t b[]={0,0,0,0x3f000000,0xbf800000};
 int errors[]={34,33,33,33,34};
 for(int mode=0;mode<2;mode++){
  uint32_t er=load(argv[1]);*(uint32_t*)at(0x13bdf4,4)=3;((setter)export_named(er,"_set_FMA3_enable"))(mode);_mm_setcsr(0x1f80);
  for(int i=0;i<5;i++){
   current=names[i];in_a=a[i];in_b=b[i];void *fn=export_named(er,current);
   last_error=0x12345678;memset(fake_ptd,0,sizeof fake_ptd);
   float x,y,z;memcpy(&x,a+i,4);memcpy(&y,b+i,4);z=i>=3?((binary)fn)(x,y):((unary)fn)(x);
   if(last_error!=0x12345678||u32(fake_ptd+0x20)!=(uint32_t)errors[i])die("last-error/errno state contract");
   uint32_t bits;memcpy(&bits,&z,4);printf("mode=%d %s %08x %08x result=%08x errno=%d last_error=%08x\n",mode,current,a[i],b[i],bits,errors[i],last_error);
  }
 }
 return 0;
}

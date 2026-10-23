// Pinned PE64 leaf loader; deliberately no Windows startup or OS emulation.
#define _DARWIN_C_SOURCE
#include <CommonCrypto/CommonDigest.h>
#include <sys/mman.h>
#include <signal.h>
#include <sys/ucontext.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <xmmintrin.h>
#include <unistd.h>
static uint8_t *base;
static size_t size;
static const char *current;
static uint32_t in_a,in_b;
static uint16_t u16(const void *p){uint16_t v;memcpy(&v,p,2);return v;}
static uint32_t u32(const void *p){uint32_t v;memcpy(&v,p,4);return v;}
static uint64_t u64(const void *p){uint64_t v;memcpy(&v,p,8);return v;}
static void die(const char *s){fprintf(stderr,"loader: %s\n",s);exit(2);}
static void *at(uint32_t r,size_t n){if(r>size||n>size-r)die("RVA out of bounds");return base+r;}
static void fault(int sig,siginfo_t *si,void *context){
 ucontext_t *c=context;
 // Diagnostic only: never turn a fault into a numerical result.
 fprintf(stderr,"FAULT signal=%d function=%s a=%08x b=%08x rip_rva=%llx address=%p\n",sig,current,in_a,in_b,(unsigned long long)(c->uc_mcontext->__ss.__rip-(uintptr_t)base),si->si_addr);
 _exit(128+sig);
}
__attribute__((noreturn)) static void import_abort(const char *name){fprintf(stderr,"IMPORT_ABORT %s function=%s a=%08x b=%08x\n",name,current,in_a,in_b);exit(86);}
static void *export_named(uint32_t r,const char *name){
 uint8_t *d=at(r,40);uint32_t n=u32(d+24);
 for(uint32_t i=0;i<n;i++)if(!strcmp(at(u32(at(u32(d+32)+4*i,4)),1),name)){
  uint32_t ordinal=u16(at(u32(d+36)+2*i,2));return at(u32(at(u32(d+28)+4*ordinal,4)),1);
 }
 die("export not found");return NULL;
}
static uint32_t load(const char *path){
 FILE *f=fopen(path,"rb");if(!f)die("open DLL");fseek(f,0,SEEK_END);long len=ftell(f);rewind(f);
 uint8_t *raw=malloc(len);if(!raw||fread(raw,1,len,f)!=(size_t)len)die("read DLL");fclose(f);
 unsigned char digest[32];CC_SHA256(raw,(CC_LONG)len,digest);char hex[65];for(int i=0;i<32;i++)sprintf(hex+2*i,"%02x",digest[i]);
 if(strcmp(hex,"385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3"))die("DLL SHA256 differs from pinned F27 DLL");
 uint8_t *pe=raw+u32(raw+0x3c),*opt=pe+24;
 if(memcmp(pe,"PE\0\0",4)||u16(pe+4)!=0x8664||u16(opt)!=0x20b)die("not PE64");
 size=u32(opt+56);base=mmap(NULL,size,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);if(base==MAP_FAILED)die("mmap image");
 memcpy(base,raw,u32(opt+60));uint8_t *sec=opt+u16(pe+20);
 for(unsigned i=0;i<u16(pe+6);i++,sec+=40){uint32_t n=u32(sec+16),off=u32(sec+20);if((uint64_t)off+n>(uint64_t)len)die("section file bounds");memcpy(at(u32(sec+12),n),raw+off,n);}
 uint64_t delta=(uintptr_t)base-u64(opt+24);uint32_t rr=u32(opt+112+5*8),rs=u32(opt+116+5*8);
 for(uint32_t pos=0;pos<rs;){uint8_t *b=at(rr+pos,8);uint32_t page=u32(b),n=u32(b+4);if(n<8||n>rs-pos)die("reloc bounds");
  for(uint32_t j=8;j<n;j+=2){uint16_t e=u16(at(rr+pos+j,2));if((e>>12)==10){uint8_t *p=at(page+(e&4095),8);uint64_t v=u64(p)+delta;memcpy(p,&v,8);}else if(e>>12)die("unsupported reloc");}pos+=n;
 }
 // A separate executable thunk for every IAT slot preserves the import name.
 size_t cap=65536,used=0;uint8_t *thunks=mmap(NULL,cap,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANON,-1,0);if(thunks==MAP_FAILED)die("mmap thunks");
 uint32_t ir=u32(opt+112+8);
 for(uint32_t p=ir;ir&&u32(at(p+12,4));p+=20){uint8_t *d=at(p,20);uint32_t lookup=u32(d),iat=u32(d+16);if(!lookup)lookup=iat;
  for(uint32_t i=0;;i++){uint64_t t=u64(at(lookup+i*8,8));if(!t)break;char name[512];
   if(t>>63)snprintf(name,sizeof name,"%s!ordinal-%llu",(char*)at(u32(d+12),1),(unsigned long long)(t&65535));
   else snprintf(name,sizeof name,"%s!%s",(char*)at(u32(d+12),1),(char*)at((uint32_t)t+2,1));
   if(used+32>cap)die("too many imports");uint8_t *s=thunks+used;used+=32;
   s[0]=0x48;s[1]=0xbf;uint64_t v=(uintptr_t)strdup(name);memcpy(s+2,&v,8);s[10]=0x48;s[11]=0xb8;v=(uintptr_t)import_abort;memcpy(s+12,&v,8);s[20]=0xff;s[21]=0xe0;
   v=(uintptr_t)s;memcpy(at(iat+i*8,8),&v,8);
  }
 }
 if(mprotect(thunks,cap,PROT_READ|PROT_EXEC)||mprotect(base,size,PROT_READ|PROT_WRITE|PROT_EXEC))die("mprotect executable image");
 uint32_t er=u32(opt+112);free(raw);return er;
}
typedef float (__attribute__((ms_abi)) *unary)(float);
typedef float (__attribute__((ms_abi)) *binary)(float,float);
typedef int (__attribute__((ms_abi)) *setter)(int);
int main(int argc,char **argv){
 if(argc!=4){fprintf(stderr,"usage: oracle DLL MODE FUNCTION < hex-pairs.txt > hex-results.txt\n");return 2;}
 struct sigaction sa={0};sa.sa_sigaction=fault;sa.sa_flags=SA_SIGINFO;sigaction(SIGSEGV,&sa,0);sigaction(SIGBUS,&sa,0);sigaction(SIGILL,&sa,0);
 uint32_t er=load(argv[1]);current=argv[3];int mode=atoi(argv[2]);if(mode!=0&&mode!=1)die("mode must be 0/1");
 _mm_setcsr(0x1f80);*(uint32_t*)at(0x13bdf4,4)=3;((setter)export_named(er,"_set_FMA3_enable"))(mode);
 if(u32(at(0x13bdf0,4))!=(mode?3:0))die("FMA mask not set");
 void *fn=export_named(er,current);int bin=!strcmp(current,"atan2f")||!strcmp(current,"powf");
 if(strcmp(current,"expf")&&strcmp(current,"sinf")&&strcmp(current,"cosf")&&!bin)die("unsupported function");
 while(scanf("%x %x",&in_a,&in_b)==2){float a,b,z;uint32_t out;memcpy(&a,&in_a,4);memcpy(&b,&in_b,4);z=bin?((binary)fn)(a,b):((unary)fn)(a);memcpy(&out,&z,4);printf("%08x\n",out);fflush(stdout);}
 return ferror(stdin)||ferror(stdout)?2:0;
}

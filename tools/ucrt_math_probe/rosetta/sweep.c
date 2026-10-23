// One process, bounded memory, atomic cumulative checkpoints. No numerical fixes.
#define ORACLE_EMBEDDED
#include "oracle.c"
#include <dlfcn.h>
#include <time.h>
#include <errno.h>
#define KEEP 2000
static const char *engines[]={"ucrt0","ucrt1","apple","amd-off","amd-fma"};
struct witness {uint32_t a,b,x,y;};
struct state {
 char magic[16], function[16];
 uint64_t next, count[10], buckets[10][2][256], hits[3];
 struct witness first[10][KEEP];
};
static struct state st;
static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
static FILE *open_out(const char *dir,const char *name,char *path){snprintf(path,4096,"%s/%s",dir,name);FILE *f=fopen(path,"wb");if(!f)die("open output");return f;}
static void save(const char *dir){
 char path[4096],dest[4096];memcpy(st.hits,stub_hits,sizeof stub_hits);
 FILE *f=open_out(dir,"checkpoint.new",path);
 if(fwrite(&st,sizeof st,1,f)!=1||fflush(f)||fsync(fileno(f))||fclose(f))die("checkpoint write");
 snprintf(dest,sizeof dest,"%s/checkpoint.bin",dir);if(rename(path,dest))die("checkpoint rename");
}
static void summaries(const char *dir){
 char path[4096];FILE *f=open_out(dir,"counts.csv",path);
 fprintf(f,"pair,processed,mismatches\n");int p=0;
 for(int i=0;i<5;i++)for(int j=i+1;j<5;j++,p++)fprintf(f,"%s/%s,%llu,%llu\n",engines[i],engines[j],st.next,st.count[p]);
 fclose(f);f=open_out(dir,"buckets.csv",path);fprintf(f,"pair,argument,biased_exponent,mismatches\n");p=0;
 for(int i=0;i<5;i++)for(int j=i+1;j<5;j++,p++)for(int a=0;a<2;a++)for(int e=0;e<256;e++)
 if(st.buckets[p][a][e])fprintf(f,"%s/%s,%d,%d,%llu\n",engines[i],engines[j],a,e,st.buckets[p][a][e]);
 fclose(f);f=open_out(dir,"first.csv",path);fprintf(f,"pair,a,b,left,right\n");p=0;
 for(int i=0;i<5;i++)for(int j=i+1;j<5;j++,p++)for(uint64_t k=0;k<st.count[p]&&k<KEEP;k++){
 struct witness w=st.first[p][k];fprintf(f,"%s/%s,%08x,%08x,%08x,%08x\n",engines[i],engines[j],w.a,w.b,w.x,w.y);}
 fclose(f);
}
int main(int argc,char **argv){
 if(argc!=8){fprintf(stderr,"usage: sweep DLL FUNCTION AMD-OFF AMD-FMA OUT END CHUNK\n");return 2;}
 current=argv[2];int bin=!strcmp(current,"atan2f")||!strcmp(current,"powf");
 if(!bin&&strcmp(current,"expf")&&strcmp(current,"sinf")&&strcmp(current,"cosf"))die("function");
 uint64_t end=strtoull(argv[6],0,0),chunk=strtoull(argv[7],0,0);if(!chunk||end>(1ULL<<32))die("range");
 char path[4096];snprintf(path,sizeof path,"%s/checkpoint.bin",argv[5]);FILE *f=fopen(path,"rb");
 if(f){if(fread(&st,sizeof st,1,f)!=1||fgetc(f)!=EOF)die("checkpoint size");fclose(f);
 if(strcmp(st.magic,"F27c-sweep-v1")||strcmp(st.function,current))die("checkpoint identity");}
 else {if(errno!=ENOENT)die("checkpoint open");strcpy(st.magic,"F27c-sweep-v1");strcpy(st.function,current);}
 if(st.next>end)die("checkpoint past end");memcpy(stub_hits,st.hits,sizeof stub_hits);atexit(report_stubs);
 struct sigaction sa={0};sa.sa_sigaction=fault;sa.sa_flags=SA_SIGINFO;sigaction(SIGSEGV,&sa,0);sigaction(SIGBUS,&sa,0);sigaction(SIGILL,&sa,0);
 void *fn[5];for(int mode=0;mode<2;mode++){
 uint32_t er=load(argv[1]);*(uint32_t*)at(0x13bdf4,4)=3;((setter)export_named(er,"_set_FMA3_enable"))(mode);
 if(u32(at(0x13bdf0,4))!=(mode?3:0))die("FMA mask");fn[mode]=export_named(er,current);}
 for(int i=2;i<5;i++){
 void *h=dlopen(i==2?"/usr/lib/libSystem.B.dylib":argv[i],RTLD_NOW|RTLD_LOCAL);char sym[64];
 snprintf(sym,sizeof sym,"%s%s",i==2?"":(!strcmp(current,"atan2f")?"amd_ref_":"amd_opt_"),current);
 fn[i]=h?dlsym(h,sym):NULL;if(!fn[i])die("host symbol");}
 _mm_setcsr(0x1f80);struct timespec t0,t1;clock_gettime(CLOCK_MONOTONIC,&t0);uint64_t start=st.next;
 while(st.next<end){uint64_t stop=st.next+chunk;if(stop>end)stop=end;
 for(uint64_t n=st.next;n<stop;n++){
 // Stateless SplitMix64: reproducible random pairs and O(1) restart.
 uint64_t r=mix(n^0xf27cULL);in_a=bin?(uint32_t)r:(uint32_t)n;in_b=bin?(uint32_t)(r>>32):0;
 float a,b,z;memcpy(&a,&in_a,4);memcpy(&b,&in_b,4);uint32_t out[5];
 for(int i=0;i<2;i++){z=bin?((binary)fn[i])(a,b):((unary)fn[i])(a);memcpy(out+i,&z,4);}
 for(int i=2;i<5;i++){z=bin?((float(*)(float,float))fn[i])(a,b):((float(*)(float))fn[i])(a);memcpy(out+i,&z,4);}
 int p=0;for(int i=0;i<5;i++)for(int j=i+1;j<5;j++,p++)if(out[i]!=out[j]){
 uint64_t k=st.count[p]++;st.buckets[p][0][(in_a>>23)&255]++;st.buckets[p][1][(in_b>>23)&255]++;
 if(k<KEEP)st.first[p][k]=(struct witness){in_a,in_b,out[i],out[j]};}
 }
 st.next=stop;save(argv[5]);clock_gettime(CLOCK_MONOTONIC,&t1);
 fprintf(stderr,"PROGRESS %s next=%llu elapsed=%.6f inputs=%llu\n",current,st.next,(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)*1e-9,st.next-start);fflush(stderr);
 }
 summaries(argv[5]);return 0;
}

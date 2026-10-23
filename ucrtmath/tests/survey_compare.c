#define ORACLE_EMBEDDED
#include "../../tools/ucrt_math_probe/rosetta/oracle.c"
#include <dlfcn.h>
typedef double (__attribute__((ms_abi)) *du)(double);
typedef double (__attribute__((ms_abi)) *db)(double,double);
int main(int argc,char **argv){
 if(argc!=6)return 2;void *fn[2],*amd[2];uint8_t *images[2];size_t sizes[2];
 for(int m=0;m<2;m++){uint32_t er=load(argv[1]);images[m]=base;sizes[m]=size;
 *(uint32_t*)at(0x13bdf4,4)=3;((setter)export_named(er,"_set_FMA3_enable"))(m);
 if(u32(at(0x13bdf0,4))!=(m?3:0))die("mode mask");fn[m]=export_named(er,argv[2]);
 void *h=dlopen(argv[3+m],RTLD_NOW|RTLD_LOCAL);if(!h){fprintf(stderr,"%s\n",dlerror());return 2;}
 char symbol[64];snprintf(symbol,sizeof symbol,"amd_opt_%s",argv[2]);amd[m]=dlsym(h,symbol);if(!amd[m])die("AMD symbol");}
 _mm_setcsr(0x1f80);uint64_t count=0,bad[5][5]={{0}},finite[5][5]={{0}},first[5][5][4]={{{0}}},rows[4096][3];size_t n;
 int single=!strcmp(argv[2],"log2f"),binary=!strcmp(argv[2],"pow");
 while((n=fread(rows,1,sizeof rows,stdin))){if(n%24)die("truncated record");n/=24;
 for(size_t i=0;i<n;i++){uint64_t r[5]={0};r[2]=rows[i][2];
 for(int m=0;m<2;m++){base=images[m];size=sizes[m];
 if(single){uint32_t a=rows[i][0],v;float x,z;memcpy(&x,&a,4);z=((unary)fn[m])(x);memcpy(&v,&z,4);r[m]=v;z=((float(*)(float))amd[m])(x);memcpy(&v,&z,4);r[3+m]=v;}
 else {double a,b,z;memcpy(&a,&rows[i][0],8);memcpy(&b,&rows[i][1],8);z=binary?((db)fn[m])(a,b):((du)fn[m])(a);memcpy(&r[m],&z,8);z=binary?((double(*)(double,double))amd[m])(a,b):((double(*)(double))amd[m])(a);memcpy(&r[3+m],&z,8);}}
 for(int a=0;a<5;a++)for(int b=a+1;b<5;b++)if(r[a]!=r[b]){if(!bad[a][b]){first[a][b][0]=rows[i][0];first[a][b][1]=rows[i][1];first[a][b][2]=r[a];first[a][b][3]=r[b];}bad[a][b]++;
 uint64_t mask=single?0x7f800000ULL:0x7ff0000000000000ULL;
 if((rows[i][0]&mask)!=mask && (!binary||(rows[i][1]&mask)!=mask))finite[a][b]++;
 }
 }count+=n;}
 if(ferror(stdin)||count!=strtoull(argv[5],0,0))die("wrong count");
 printf("{\"function\":\"%s\",\"count\":%llu,\"engines\":[\"ucrt0\",\"ucrt1\",\"apple-arm64\",\"amd-off-x86\",\"amd-fma-x86\"],\"pairs\":[",argv[2],count);
 int comma=0;for(int a=0;a<5;a++)for(int b=a+1;b<5;b++)printf("%s{\"a\":%d,\"b\":%d,\"mismatches\":%llu,\"finite_input_mismatches\":%llu,\"first\":[\"%016llx\",\"%016llx\",\"%016llx\",\"%016llx\"]}",comma++?",":"",a,b,bad[a][b],finite[a][b],first[a][b][0],first[a][b][1],first[a][b][2],first[a][b][3]);puts("]}");return 0;
}

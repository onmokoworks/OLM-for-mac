#include "ucrtmath.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint64_t mix(uint64_t z){z+=0x9e3779b97f4a7c15ULL;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}
static double val(uint64_t u){double x;memcpy(&x,&u,8);return x;}
static uint64_t bits(double x){uint64_t u;memcpy(&u,&x,8);return u;}
int main(int argc,char **argv){
 if(argc!=4)return 2;
 double (*fn)(double,ucrt_mode)=!strcmp(argv[1],"sin")?ucrt_sin:!strcmp(argv[1],"cos")?ucrt_cos:!strcmp(argv[1],"exp")?ucrt_exp:NULL;
 if(!fn)return 2;
 uint64_t count=strtoull(argv[3],0,0),rows[4096][3];size_t n=0;
 for(uint64_t i=0;i<count;i++){
  uint64_t a=mix(i^0xf43b);
  if(!strcmp(argv[2],"file")){if(scanf("%llx",(unsigned long long*)&a)!=1)return 2;}
  else if(!strcmp(argv[2],"range")){
   double t=(a>>11)*0x1p-53;
   a=bits(!strcmp(argv[1],"exp")?-745.0+1455.0*t:-64.0+128.0*t);
  }else if(strcmp(argv[2],"random"))return 2;
  rows[n][0]=a;rows[n][1]=bits(fn(val(a),0));rows[n][2]=bits(fn(val(a),1));
  if(++n==4096){if(fwrite(rows,24,n,stdout)!=n)return 2;n=0;}
 }
 if(n&&fwrite(rows,24,n,stdout)!=n)return 2;
 return fflush(stdout)||ferror(stdout)?2:0;
}

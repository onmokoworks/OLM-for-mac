#include "../include/ucrtmath.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint64_t mix(uint64_t z){z+=0x9e3779b97f4a7c15ULL;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}
static double value(uint64_t u){double d;memcpy(&d,&u,8);return d;}
static uint64_t word(double d){uint64_t u;memcpy(&u,&d,8);return u;}
int main(int argc,char **argv){
 if(argc!=3)return 2;
 uint64_t count=strtoull(argv[2],0,0),rows[4096][4];size_t n=0;
 for(uint64_t i=0;i<count;i++){
  uint64_t a=mix(i^0xf28),b=mix(i^0xf28^0x123456789abcdef0ULL);
  if(!strcmp(argv[1],"file")){if(scanf("%llx %llx",&a,&b)!=2)return 2;}
  else if(!strcmp(argv[1],"ranges")){
   a=word((double)(a>>11)*0x1p-53*4);
   b=word((double)(b>>11)*0x1p-53*16-8);
  } else if(strcmp(argv[1],"random"))return 2;
  rows[n][0]=a;rows[n][1]=b;
  for(int m=0;m<2;m++)rows[n][2+m]=word(ucrt_pow(value(a),value(b),m));
  if(++n==4096){if(fwrite(rows,32,n,stdout)!=n)return 2;n=0;}
 }
 if(n&&fwrite(rows,32,n,stdout)!=n)return 2;
 return ferror(stdin)||fflush(stdout)||ferror(stdout)?2:0;
}

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint64_t mix(uint64_t z){z+=0x9e3779b97f4a7c15ULL;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}
int main(int argc,char **argv){
 if(argc!=3 && argc!=4)return 2; uint64_t count=strtoull(argv[2],0,0), rows[4096][3];size_t n=0;
 for(uint64_t i=0;i<count;i++){
 uint64_t a=mix(i^0xf28),b=mix(i^0xf28^0x123456789abcdef0ULL),z;
 if(!strcmp(argv[1],"log2f")){uint32_t u=i,v;float x,y;memcpy(&x,&u,4);y=log2f(x);memcpy(&v,&y,4);a=u;b=0;z=v;}
 else {double x,y,v;
 if(argc==4){
  double t=(double)(a>>11)*0x1p-53, u=(double)(b>>11)*0x1p-53;
  if(!strcmp(argv[1],"sin")||!strcmp(argv[1],"cos")){x=(t*2-1)*0x1.921fb54442d18p+4;y=0;}
  else if(!strcmp(argv[1],"exp")){x=-128*t;y=0;}
  else {x=t*(i%2?1:4);y=i%3?u*16:(double)((int)(i%65)-32)*0.5;}
  if(i<256){static const uint64_t sp[]={0,0x8000000000000000ULL,1,0x0010000000000000ULL,0x3fefffffffffffffULL,0x3ff0000000000000ULL,0x3ff0000000000001ULL,0x7fefffffffffffffULL,0x7ff0000000000000ULL,0xfff0000000000000ULL,0x7ff0000000000001ULL,0x7ff8000000000001ULL,0xfff8000000000001ULL,0xbff0000000000000ULL,0x4000000000000000ULL,0x3fe0000000000000ULL};a=sp[i%16];b=sp[i/16];}
  else {memcpy(&a,&x,8);memcpy(&b,&y,8);}
 }
 memcpy(&x,&a,8);memcpy(&y,&b,8);
 if(!strcmp(argv[1],"sin"))v=sin(x);else if(!strcmp(argv[1],"cos"))v=cos(x);else if(!strcmp(argv[1],"exp"))v=exp(x);else if(!strcmp(argv[1],"pow"))v=pow(x,y);else return 2;
 memcpy(&z,&v,8);}
 rows[n][0]=a;rows[n][1]=b;rows[n][2]=z;
 if(++n==4096){if(fwrite(rows,24,n,stdout)!=n)return 2;n=0;}
 }
 if(n&&fwrite(rows,24,n,stdout)!=n)return 2;return fflush(stdout)||ferror(stdout)?2:0;
}

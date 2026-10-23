#include "ucrtmath.h"
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
static uint32_t bits(float f){uint32_t u;memcpy(&u,&f,4);return u;}
static float val(uint32_t u){float f;memcpy(&f,&u,4);return f;}
static uint64_t mix(uint64_t z){z+=0x9e3779b97f4a7c15ULL;z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}
int main(int argc,char **argv){
 if(argc!=4)return 2;
 const char *fn=argv[1];uint64_t count=strtoull(argv[3],0,0);
 uint32_t rows[4096][4];size_t n=0;uint64_t i=0;
 while(1){uint32_t a,b;
  if(!strcmp(argv[2],"file")){if(scanf("%x %x",&a,&b)!=2)break;}
  else {if(i==count)break;uint64_t r=mix(i^0xf27c);a=(!strcmp(fn,"expf")||!strcmp(fn,"sinf")||!strcmp(fn,"cosf")||!strcmp(fn,"log2f"))?(uint32_t)i:(uint32_t)r;b=!strcmp(fn,"expf")?0:(uint32_t)(r>>32);}
  rows[n][0]=a;rows[n][1]=b;
  for(int m=0;m<2;m++) {float z;
   if(!strcmp(fn,"expf"))z=ucrt_expf(val(a),m);
   else if(!strcmp(fn,"sinf"))z=ucrt_sinf(val(a),m);
   else if(!strcmp(fn,"cosf"))z=ucrt_cosf(val(a),m);
   else if(!strcmp(fn,"log2f"))z=ucrt_log2f(val(a),m);
   else if(!strcmp(fn,"powf"))z=ucrt_powf(val(a),val(b),m);
   else if(!strcmp(fn,"atan2f"))z=ucrt_atan2f(val(a),val(b),m);
   else return 2;
   rows[n][2+m]=bits(z);
  }
  i++;if(++n==4096){if(fwrite(rows,16,n,stdout)!=n)return 2;n=0;}
 }
 if(n&&fwrite(rows,16,n,stdout)!=n)return 2;
 return ferror(stdin)||fflush(stdout)||ferror(stdout)?2:0;
}

// Apple libSystem comparison process, built explicitly for x86_64.
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 if(argc!=2&&argc!=3)return 2;
 char symbol[64];snprintf(symbol,sizeof symbol,"%s%s",argc==3?(!strcmp(argv[1],"atan2f")?"amd_ref_":"amd_opt_"):"",argv[1]);
 void *lib=dlopen(argc==3?argv[2]:"/usr/lib/libSystem.B.dylib",RTLD_NOW);
 void *fn=lib?dlsym(lib,symbol):NULL;if(!fn)return 2;
 int binary=!strcmp(argv[1],"atan2f")||!strcmp(argv[1],"powf");
 if(!binary&&strcmp(argv[1],"expf")&&strcmp(argv[1],"sinf")&&strcmp(argv[1],"cosf"))return 2;
 uint32_t a,b,r;while(scanf("%x %x",&a,&b)==2){float x,y,z;memcpy(&x,&a,4);memcpy(&y,&b,4);z=binary?((float(*)(float,float))fn)(x,y):((float(*)(float))fn)(x);memcpy(&r,&z,4);printf("%08x\n",r);}return 0;
}

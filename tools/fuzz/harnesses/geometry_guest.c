/* Synthetic Windows SDK-ABI fixture, NOT an OLM plugin or output oracle.
 * Offsets: retained aex-abi generated.rs, AE_Effect.h Windows x64 layout.
 * Emits a coordinate pattern to test host allocation/serialization only. */
typedef unsigned char byte;
typedef int i32;
#define I(p,o) (*(i32*)((byte*)(p)+(o)))
#define P(p,o) (*(void**)((byte*)(p)+(o)))
__declspec(dllexport) i32 EffectMain(i32 cmd,void *in,void *out,void *params,void *world,void *extra) {
    if(cmd==1){I(out,400)=1<<10;return 0;}
    if(cmd==4){I(out,48)=1;return 0;}
    if(cmd==23){
        void *pi=P(extra,0),*po=P(extra,8);
        for(int i=0;i<4;++i)I(po,i*4)=I(pi,i*4);
        I(po,16)=-3;I(po,20)=-2;I(po,24)=14;I(po,28)=10;
        return 0;
    }
    if(cmd==24){
        void *cb=P(extra,8),*w=0;
        i32 (*checkout)(void*,void**)=P(cb,16);
        i32 error=checkout(P(in,184),&w);if(error)return error;
        i32 width=I(w,36),height=I(w,40),stride=I(w,32),ox=I(w,104),oy=I(w,108);
        if(width!=17||height!=12||stride!=71||ox!=-3||oy!=-2||I(in,276)!=3||I(in,280)!=2)return 777;
        byte *data=P(w,24);
        for(int y=0;y<height;++y)for(int x=0;x<width;++x){
            byte *p=data+y*stride+x*4;p[0]=255;p[1]=x+ox+32;p[2]=y+oy+32;p[3]=77;
        }
    }
    return 0;
}

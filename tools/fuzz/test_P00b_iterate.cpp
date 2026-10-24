// SDK-host transport regression: rectangle clipping and untouched destination.
#define main p00_host_main
#include "../emulation/aexcompat_patches/P00-host-realism.cpp"
#undef main
#include <cassert>
static PF_Err copy_pixel(void*, A_long, A_long, PF_Pixel* in, PF_Pixel* out) {
 *out=*in; return 0;
}
int main() {
 PF_Pixel src[6]{}; PF_Pixel dst[12]{};
 for(auto &p:src)p.alpha=255;
 PF_EffectWorld a{},b{};
 a.data=src;a.width=3;a.height=2;a.rowbytes=3*sizeof(PF_Pixel);
 b.data=dst;b.width=4;b.height=3;b.rowbytes=4*sizeof(PF_Pixel);
 PF_Rect rect{1,0,4,3}; // left, top, right, bottom
 assert(iterate<PF_Pixel>(nullptr,0,3,&a,&rect,nullptr,copy_pixel,&b)==0);
 for(int y=0;y<3;y++)for(int x=0;x<4;x++)assert(dst[y*4+x].alpha==((y<2&&x>=1&&x<3)?255:0));
 std::memset(dst,0,sizeof(dst));
 assert(iterate<PF_Pixel>(nullptr,0,3,&a,nullptr,nullptr,copy_pixel,&b)==0);
 for(int y=0;y<3;y++)for(int x=0;x<4;x++)assert(dst[y*4+x].alpha==((y<2&&x<3)?255:0));
 return 0;
}

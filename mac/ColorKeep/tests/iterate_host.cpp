// P04d: ordinary-iterate addressing, area and byte-stride contract.
#include "../../../tools/emulation/aexcompat_patches/F47d-native-bridge.cpp"
#include <cassert>

template<class P> static PF_Err copy_pixel(void *ref, A_long, A_long, P *in, P *out) {
 ++*static_cast<int*>(ref);
 std::memcpy(out,in,sizeof(P));
 return 0;
}
template<class P> static void check() {
 const size_t ib=4*sizeof(P)+3, ob=3*sizeof(P)+1;
 std::vector<unsigned char> input(1+ib*3,0), output(1+ob*2,0xa5);
 for(size_t i=0;i<input.size();++i)input[i]=static_cast<unsigned char>(i*17+13);
 PF_EffectWorld src{},dst{};
 src.width=4;src.height=3;src.rowbytes=ib;src.data=(PF_PixelPtr)(input.data()+1);
 dst.width=3;dst.height=2;dst.rowbytes=ob;dst.data=(PF_PixelPtr)(output.data()+1);
 src.origin_x=17;src.origin_y=21;dst.origin_x=2;dst.origin_y=3;
 PF_Rect area{1,0,3,2}; int calls=0;
 assert(iterate<P>(nullptr,0,2,&src,&area,&calls,copy_pixel<P>,&dst)==0);
 assert(calls==4);
 auto expected=std::vector<unsigned char>(output.size(),0xa5);
 for(int y=0;y<2;++y)std::memcpy(expected.data()+1+y*ob+sizeof(P),input.data()+1+y*ib+sizeof(P),2*sizeof(P));
 assert(output==expected);
 area={2,1,2,1};calls=0;
 assert(iterate<P>(nullptr,0,0,&src,&area,&calls,copy_pixel<P>,&dst)==0 && calls==0);
 assert(output==expected);
 area={0,0,4,2};
 assert(iterate<P>(nullptr,0,2,&src,&area,&calls,copy_pixel<P>,&dst)!=0 && calls==0);
 assert(output==expected);
 assert(iterate<P>(nullptr,0,2,&src,nullptr,&calls,copy_pixel<P>,&dst)==0 && calls==6);
 for(int y=0;y<2;++y)std::memcpy(expected.data()+1+y*ob,input.data()+1+y*ib,3*sizeof(P));
 assert(output==expected);
}
int main() { check<PF_Pixel>();check<PF_Pixel16>();check<PF_PixelFloat>(); }

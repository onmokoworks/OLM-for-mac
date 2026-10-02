// Copy preserves arbitrary byte rows; invalid layouts reject atomically.
#include "production_under_test.cpp"
#include <iostream>
int main() {
 unsigned checks=0;
 for(short depth: {8,16,32}) for(int family: {1,2}) {
  size_t ps=depth==8?4:depth==16?8:16;int w=3,h=4;size_t active=w*ps,irb=active+3,orb=active+5;
  std::vector<A_u_char>a(irb*h+2,0xa5),b(orb*h+2,0xee);
  for(int y=0;y<h;++y)for(size_t x=0;x<active;++x)a[1+y*irb+x]=(A_u_char)((x*73+y*131)%256);
  auto original=a;PF_EffectWorld in{},out{};in.data=(PF_PixelPtr)(a.data()+1);in.width=w;in.height=h;in.rowbytes=irb;
  out.data=(PF_PixelPtr)(b.data()+1);out.width=w;out.height=h;out.rowbytes=orb;
  OLMRadialBlurInfo q{};q.blur_type=family;q.noise_type=2;q.comp_width=w;q.comp_height=h;
  q.center_x=-400;q.center_y=700;q.quality=50;q.brightness_gain=10;q.angle_deg=-720;q.ratio=5;q.repeat_border=FALSE;
  if(RenderWorld(&in,&out,nullptr,q,depth))return 1;
  if(a!=original||b.front()!=0xee||b.back()!=0xee)return 2;
  for(int y=0;y<h;++y) {
   if(std::memcmp(a.data()+1+y*irb,b.data()+1+y*orb,active))return 3;
   for(size_t x=active;x<orb;++x)if(b[1+y*orb+x]!=0xee)return 4;
  }++checks;
  // Every invalid layout must reject before any output byte is written.
  for(int state=0;state<13;++state) {
   PF_EffectWorld x=in,z=out;OLMRadialBlurInfo info=q;short bd=depth;bool null_input=false,null_output=false;
   switch(state) {
    case 0:x.rowbytes=active-1;break;case 1:z.rowbytes=active-1;break;
    case 2:x.rowbytes=-1;break;case 3:z.rowbytes=-1;break;
    case 4:z.height=h-1;break;case 5:z.width=w-1;break;
    case 6:x.data=nullptr;break;case 7:z.data=nullptr;break;
    case 8:info.comp_width=w+1;break;case 9:info.comp_height=h+1;break;
    case 10:bd=31;break;case 11:null_input=true;break;case 12:null_output=true;break;
   }
   std::fill(b.begin(),b.end(),0xee);auto previous=b;
   if(RenderWorld(null_input?nullptr:&x,null_output?nullptr:&z,nullptr,info,bd)!=PF_Err_BAD_CALLBACK_PARAM)return 10+state;
   if(b!=previous||a!=original)return 30+state;++checks;
  }
  // The Blur path retains its alignment/SDR contracts when Strength is nonzero.
  std::fill(b.begin(),b.end(),0xee);auto previous=b;q.outer_strength=1;q.repeat_border=TRUE;q.center_x=1;q.center_y=1;
  q.ratio=1;q.angle_deg=0;q.quality=1;q.brightness_gain=1;q.noise_variation=0;
  if(depth!=8&&RenderWorld(&in,&out,nullptr,q,depth)!=PF_Err_BAD_CALLBACK_PARAM)return 60;
  if(depth!=8&&(b!=previous||a!=original))return 61;
 }
 std::cout<<"NOOP_WORLD_CONTRACT "<<checks<<" BYTE_COPY_AND_ATOMIC_REJECTIONS\n";
}

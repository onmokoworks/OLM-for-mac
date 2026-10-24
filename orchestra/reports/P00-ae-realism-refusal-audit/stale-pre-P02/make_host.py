from pathlib import Path
p=Path('tools/emulation/aexcompat_patches/F47d-native-bridge.cpp')
s=p.read_text()
s='// P00 derived F47d suite host. See P00-host-realism.md for limitations.\n'+s
s=s.replace('using Entry =', '#include "../../fuzz/harnesses/parameters.hpp"\n#include <chrono>\nstatic const char *parameter_file;\nstatic bool expand_output;\nusing Entry =')
a=s.index(' if(s->default_ramps && p->param_type')
b=s.index('\n return 0;',a)
s=s[:a]+''' actual=*p;
 if(p->param_type==PF_Param_ARBITRARY_DATA) actual.u.arb_d.value=p->u.arb_d.dephault;
 // AE converts point defaults from percentages into layer-space fixed coordinates.
 if(p->param_type==PF_Param_POINT) {
  actual.u.td.x_value=PF_Fixed(double(p->u.td.x_dephault)*s->src->width/100.0);
  actual.u.td.y_value=PF_Fixed(double(p->u.td.y_dephault)*s->src->height/100.0);
 }
'''+s[b:]
s=s.replace('if(!err && (state.declarations!=count-1 || out.num_params!=count)) err=fail("declaration count");','''if(!err && out.num_params!=state.declarations+1) err=fail("declaration count");
  state.count=in.num_params=out.num_params;
  if(!err && !fuzz_parameters(parameter_file,params.data(),state.count)) err=fail("parameter file");''')
s=s.replace('if(!err && smart) err=call(PF_Cmd_SMART_PRE_RENDER,&pe);','''if(!err && smart) err=call(PF_Cmd_SMART_PRE_RENDER,&pe);
  std::fprintf(stderr,"P00 prerender result=%d,%d,%d,%d max=%d,%d,%d,%d\\n",
   po.result_rect.left,po.result_rect.top,po.result_rect.right,po.result_rect.bottom,
   po.max_result_rect.left,po.max_result_rect.top,po.max_result_rect.right,po.max_result_rect.bottom);
  if(!err && smart && expand_output) {
   const auto r=po.result_rect;
   const int nw=r.right-r.left, nh=r.bottom-r.top;
   if(nw>0 && nh>0 && nw<=8192 && nh<=8192 && (nw>dst.width || nh>dst.height)) {
    dst.width=nw;dst.height=nh;dst.rowbytes=nw*depth/8*4;dst.extent_hint={0,0,nw,nh};
    in.output_origin_x=-r.left;in.output_origin_y=-r.top;
    destination.assign(size_t(dst.rowbytes)*nh+128,0xA7);
    std::fill(destination.begin()+64,destination.end()-64,0);
    dst.data=reinterpret_cast<PF_Pixel*>(destination.data()+64);
   }
  }
  auto render_start=std::chrono::steady_clock::now();''')
s=s.replace('if(po.pre_render_data) {','''auto render_end=std::chrono::steady_clock::now();
  bool nonzero=false;
  for(int y=0;y<dst.height;++y) for(int x=0;x<dst.width*depth/8*4;++x)
   nonzero |= reinterpret_cast<unsigned char*>(dst.data)[size_t(y)*dst.rowbytes+x]!=0;
  std::printf("{\\"error\\":%d,\\"render_seconds\\":%.9f,\\"nonzero\\":%s,\\"output_width\\":%d,\\"output_height\\":%d}\\n",
   err,std::chrono::duration<double>(render_end-render_start).count(),nonzero?"true":"false",int(dst.width),int(dst.height));
  if(po.pre_render_data) {''')
s=s.replace('std::memcpy(dst_pixels,destination.data()+64,dst_size);','// No pixel transport: output sanity and timing are emitted above.')
s+='''
// Arguments: executable fullW fullH depth dsXden dsYden pad extent ROI aspectN aspectD expand params classic
int main(int argc,char **argv) {
 if(argc!=15) return 2;
 int fw=atoi(argv[2]),fh=atoi(argv[3]),depth=atoi(argv[4]),dx=atoi(argv[5]),dy=atoi(argv[6]);
 int pad=atoi(argv[7]),extent=atoi(argv[8]),roi=atoi(argv[9]),an=atoi(argv[10]),ad=atoi(argv[11]);
 expand_output=atoi(argv[12]);parameter_file=argv[13];bool classic=atoi(argv[14]);
 if(fw<1||fw>8192||fh<1||fh>8192||dx<1||dy<1||pad<0||pad>4096||ad<1||an<1||(depth!=8&&depth!=16&&depth!=32)) return 2;
 int w=(fw+dx-1)/dx,h=(fh+dy-1)/dy,bpp=depth/8*4;
 int stride=w*bpp+pad;stride=(stride+bpp-1)/bpp*bpp;
 std::vector<unsigned char> input(size_t(stride)*h,0),output(size_t(stride)*h,0);
 for(int y=0;y<h;++y) for(int x=0;x<w;++x) {
  unsigned char *q=input.data()+size_t(y)*stride+x*bpp;
  for(int c=0;c<4;++c) {
   unsigned v=c==0?255:((x*17+y*29+c*53)%256);
   if(depth==8) q[c]=v;
   else if(depth==16) {unsigned short u=(v*32768u)/255;memcpy(q+c*2,&u,2);}
   else {float f=v/255.0f;memcpy(q+c*4,&f,4);}
  }
 }
 PF_EffectWorld src{},dst{};
 src.width=dst.width=w;src.height=dst.height=h;src.rowbytes=dst.rowbytes=stride;
 src.world_flags=dst.world_flags=depth==8?0:PF_WorldFlag_DEEP;
 src.extent_hint=dst.extent_hint={0,0,w,h};
 if(extent) src.extent_hint={w/4,h/4,w*3/4,h*3/4};
 src.pix_aspect_ratio=dst.pix_aspect_ratio={an,ad};
 PF_InData in{};in.effect_ref=reinterpret_cast<PF_ProgPtr>(1);in.quality=PF_Quality_HI;
 in.version.major=13;in.version.minor=29;in.appl_id=0x46585443;
 in.num_params=512;in.width=fw;in.height=fh;in.extent_hint=src.extent_hint;
 in.time_step=in.local_time_step=1;in.time_scale=24;in.total_time=1;
 in.downsample_x={1,dx};in.downsample_y={1,dy};in.pixel_aspect_ratio={an,ad};
 int request[]={0,0,w,h};if(roi) {request[0]=w/4;request[1]=h/4;request[2]=w*3/4;request[3]=h*3/4;}
 std::vector<PF_ParamDef> defs(512);
 int err=f47c_render(argv[1],reinterpret_cast<unsigned char*>(&in),reinterpret_cast<unsigned char*>(defs.data()),
  reinterpret_cast<unsigned char*>(&src),reinterpret_cast<unsigned char*>(&dst),input.data(),output.data(),depth,request,512,!classic);
 std::fprintf(stderr,"P00 final_error=%d\\n",err);
 return err?1:0;
}
'''
Path('tools/emulation/aexcompat_patches/P00-host-realism.cpp').write_text(s)

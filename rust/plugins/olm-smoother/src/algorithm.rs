//! Checked, host-independent frame owner. Callback traversal is deliberately
//! serial: interpolation may write neighbors that later callbacks read.
use olm_core::{allocate,Budget,Depth,Error,Pixel,Rect,Result,View,ViewMut};
use crate::{generated::*,support::*};
#[derive(Clone, Copy, Debug)]
pub struct Params {pub use_key:bool,pub key:[u8;4],pub tolerance:i32}
impl Default for Params {fn default()->Self{Self{use_key:false,key:[255;4],tolerance:6}}}
pub fn render(input:&View<'_>,output:&mut ViewMut<'_>,p:Params,extent:Rect)->Result<()> {
 let l=input.layout();let o=output.layout();
 if l.depth!=o.depth||l.width!=o.width||l.height!=o.height||l.depth==Depth::F32{return Err(Error::Unsupported);}
 if !(0..=255).contains(&p.tolerance)||l.width>4096||l.height>4096||l.width.checked_mul(l.height).ok_or(Error::Overflow)?>4096*2160{return Err(Error::Geometry);}
 let frame=Rect::from_size(0,0,l.width,l.height)?;
 if !frame.contains(extent){return Err(Error::Bounds);}
 let n=l.width*l.height;let mut budget=Budget::new(4096*2160*16);
 // u64 storage keeps all pointer-reinterpreted samples and curve buffers aligned.
 let bytes=n*l.depth.pixel_bytes();let count=(bytes+7)/8;
 let mut src=allocate(count,0u64,&mut budget)?;let mut dst=allocate(count,0u64,&mut budget)?;
 unsafe {
  for y in 0..l.height {for x in 0..l.width {
   let i=y*l.width+x;
   match input.get(x,y)? {
    Pixel::U8(mut v)=>{if p.use_key && extent.left()<=x as i32&&(x as i32)<extent.right()&&extent.top()<=y as i32&&(y as i32)<extent.bottom()&&v==p.key{v[0]=0;}
      src.as_mut_ptr().cast::<[u8;4]>().add(i).write(v);},
    Pixel::U16(mut v)=>{let key=p.key.map(|v|((v as u32*32768+128)/255) as u16);
      if p.use_key && extent.left()<=x as i32&&(x as i32)<extent.right()&&extent.top()<=y as i32&&(y as i32)<extent.bottom()&&v==key{v[0]=0;}
      src.as_mut_ptr().cast::<[u16;4]>().add(i).write(v);},
    _=>return Err(Error::Unsupported),
   }
  }}
  dst.copy_from_slice(&src);
  let mut sw=World{data:src.as_mut_ptr().cast(),width:l.width as i32,height:l.height as i32,rowbytes:(l.width*l.depth.pixel_bytes()) as i32,..Default::default()};
  let mut dw=World{data:dst.as_mut_ptr().cast(),..sw};
  let mut state=RenderState{src_world:&mut sw,dst_world:&mut dw,tolerance:p.tolerance,tolerance_lo:p.tolerance,tolerance_hi:p.tolerance,threshold:p.tolerance,..Default::default()};
  for y in extent.top()..extent.bottom(){for x in extent.left()..extent.right(){
   if l.depth==Depth::U8 {ScanlinePixel8_Main((&mut state as *mut RenderState).cast(),x,y,std::ptr::null_mut(),std::ptr::null_mut());}
   else {ScanlinePixel16_Main((&mut state as *mut RenderState).cast(),x,y,std::ptr::null_mut(),std::ptr::null_mut());}
  }}
  for y in 0..l.height{for x in 0..l.width{let i=y*l.width+x;
   let px=if l.depth==Depth::U8{Pixel::U8(dst.as_ptr().cast::<[u8;4]>().add(i).read())}else{Pixel::U16(dst.as_ptr().cast::<[u16;4]>().add(i).read())};
   output.set(x,y,px)?;
  }}
 }
 Ok(())
}

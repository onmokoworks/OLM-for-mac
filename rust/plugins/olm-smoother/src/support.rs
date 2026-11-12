//! Host-independent carriers for the literal C++ control-flow translation.
//! Virtual addresses designate local stack storage or immutable direction tables;
//! all pixel pointers designate checked, owned staging buffers.
pub(super) const DAT_18000d1f0: f32 = 0.5;
pub(super) const DAT_18000d1f4: f32 = 1.0;
pub(super) const DAT_18000d250: f32 = 1.0 / 32768.0;
pub(super) const _DAT_18000d254: f32 = 0.11;
pub(super) const _DAT_18000d258: f32 = 0.30;
pub(super) const _DAT_18000d25c: f32 = 0.59;
pub(super) const DAT_18000d260: f32 = 4.0;
pub(super) const DAT_18000d264: f32 = 8.0;
pub(super) const DAT_18000d268: f32 = 255.0;
pub(super) const DAT_18000d26c: f32 = 32768.0;
pub(super) const DAT_18000d270: u32 = 0x7fff_ffff;
pub(super) const DAT_18000f000: [i32;9] = [6,3,0,7,4,1,8,5,2];
pub(super) const DAT_18000f028: [i32;9] = [2,5,8,1,4,7,0,3,6];
pub(super) const DAT_18000f050: [i32;9] = [3,0,1,6,4,2,7,8,5];
pub(super) const DAT_18000f078: [i32;9] = [1,2,5,0,4,8,3,6,7];
pub(super) const DAT_18000f0a0: [i32;9] = [8,7,6,5,4,3,2,1,0];
pub(super) const DAT_18000f0c8: [i32;9] = [-1,0,1,-1,0,1,-1,0,1];
pub(super) const DAT_18000f0f0: [i32;9] = [-1,-1,-1,0,0,0,1,1,1];
pub(super) const PF_Err_NONE: i32 = 0;
pub(super) const KSTACK: u64 = 0x700000000000;
pub(super) const KMODULE: u64 = 0x180000000;
pub(super) use olm_math::x86::{add as SseAddF32,sub as SseSubF32,mul as SseMulF32,div as SseDivF32};

#[repr(C)]
#[derive(Clone, Copy, Default)]
pub(super) struct World {
 pub data: *mut (), pub width:i32, pub height:i32, pub rowbytes:i32,
 // Generated memory carriers address Windows world fields through +0x28.
 // Reserve the complete descriptor span so a synthetic field address cannot
 // alias an adjacent native RenderState and hit its interception first.
 pub padding:[u64;13],
}
#[repr(C)]
#[derive(Clone, Copy, Default)]
pub(super) struct Pixel8 {pub alpha:u8,pub red:u8,pub green:u8,pub blue:u8}
#[repr(C)]
#[derive(Clone, Copy, Default)]
pub(super) struct Pixel16 {pub alpha:u16,pub red:u16,pub green:u16,pub blue:u16}
#[repr(C)]
#[derive(Clone, Copy, Default)]
pub(super) struct RenderState {
 pub use_key:u8,pub key_a:u8,pub key_rg_packed:u16,pub key_b:u16,pub key_pad:u16,
 pub tolerance_lo:i32,pub tolerance_hi:i32,pub src_world:*mut World,pub dst_world:*mut World,
 pub tolerance:i32,pub threshold:i32,pub key16_a:u16,pub key16_r:u16,pub key16_g:u16,pub key16_b:u16,
}
#[derive(Default)]
pub(super) struct Regs {
 pub rax:u64,pub rbx:u64,pub rcx:u64,pub rdx:u64,pub rsi:u64,pub rdi:u64,pub rbp:u64,pub rsp:u64,
 pub r8:u64,pub r9:u64,pub r10:u64,pub r11:u64,pub r12:u64,pub r13:u64,pub r14:u64,pub r15:u64,
}
pub(super) struct Memory {
 pub stack:[u8;4096],pub zf:bool,pub sf:bool,pub of:bool,
 pub world:*mut World,pub state:*mut RenderState,pub pf16:bool,
}
impl Default for Memory {
 fn default()->Self {Self{stack:[0;4096],zf:false,sf:false,of:false,world:std::ptr::null_mut(),state:std::ptr::null_mut(),pf16:false}}
}
impl Memory {
 fn is_stack(&self,a:u64,n:usize)->bool {a>=KSTACK && n<=4096 && a-KSTACK<=4096-n as u64}
 pub unsafe fn ptr(&mut self,a:u64)->*mut () {
  if self.is_stack(a,1){self.stack.as_mut_ptr().add((a-KSTACK) as usize).cast()}else{a as *mut ()}
 }
 unsafe fn raw<T:Copy>(&self,a:u64)->T {
  if self.is_stack(a,std::mem::size_of::<T>()){self.stack.as_ptr().add((a-KSTACK) as usize).cast::<T>().read_unaligned()}
  else{(a as *const T).read_unaligned()}
 }
 pub unsafe fn read8(&self,a:u64)->u8 {self.raw(a)}
 pub unsafe fn read16(&self,a:u64)->u16 {self.raw(a)}
 pub unsafe fn read32(&self,a:u64)->u32 {
  if self.is_stack(a,4){return self.raw(a);}
  if !self.state.is_null(){let s=self.state as u64;
   if a==s+8{return (*self.state).tolerance_lo as u32;}
   if a==s+12{return (*self.state).tolerance_hi as u32;}
   if self.pf16 && a==s+16{return (*self.state).threshold as u32;}
  }
  if !self.world.is_null(){let w=self.world as u64;
   if a==w+4||a==w+0x24{return (*self.world).width as u32;}
   if a==w+8||a==w+0x28{return (*self.world).height as u32;}
   if a==w+12||a==w+0x20{return (*self.world).rowbytes as u32;}
  }
  for (base,table) in [(0xf000,&DAT_18000f000),(0xf028,&DAT_18000f028),(0xf050,&DAT_18000f050),(0xf078,&DAT_18000f078),(0xf0a0,&DAT_18000f0a0),(0xf0c8,&DAT_18000f0c8),(0xf0f0,&DAT_18000f0f0)] {
   if a>=KMODULE+base && a<KMODULE+base+36 {return table[((a-KMODULE-base)/4) as usize] as u32;}
  }
  self.raw(a)
 }
 pub unsafe fn read64(&self,a:u64)->u64 {
  if self.is_stack(a,8){return self.raw(a);}
  if !self.state.is_null() && a==self.state as u64+if self.pf16{0x18}else{0x10}{return self.world as u64;}
  if !self.world.is_null() && (a==self.world as u64+0x10||a==self.world as u64+0x18){return (*self.world).data as u64;}
  self.raw(a)
 }
 unsafe fn write<T:Copy>(&mut self,a:u64,v:T){
  if self.is_stack(a,std::mem::size_of::<T>()){self.stack.as_mut_ptr().add((a-KSTACK) as usize).cast::<T>().write_unaligned(v);}
  else{(a as *mut T).write_unaligned(v);}
 }
 pub unsafe fn write8(&mut self,a:u64,v:u8){self.write(a,v)}
 pub unsafe fn write16(&mut self,a:u64,v:u16){self.write(a,v)}
 pub unsafe fn write32(&mut self,a:u64,v:u32){self.write(a,v)}
 pub unsafe fn write64(&mut self,a:u64,v:u64){self.write(a,v)}
 pub fn subflags(&mut self,mut a:u64,mut b:u64,w:i32)->u64 {
  let mask=if w==64{u64::MAX}else{(1u64<<w)-1};a&=mask;b&=mask;
  let r=a.wrapping_sub(b)&mask;self.zf=r==0;self.sf=(r>>(w-1))&1!=0;self.of=(((a^b)&(a^r))>>(w-1))&1!=0;r
 }
 pub fn addflags(&mut self,mut a:u64,mut b:u64,w:i32)->u64 {
  let mask=if w==64{u64::MAX}else{(1u64<<w)-1};a&=mask;b&=mask;
  let r=a.wrapping_add(b)&mask;self.zf=r==0;self.sf=(r>>(w-1))&1!=0;self.of=(((!(a^b))&(a^r))>>(w-1))&1!=0;r
 }
 pub fn logicflags(&mut self,mut r:u64,w:i32){let mask=if w==64{u64::MAX}else{(1u64<<w)-1};r&=mask;self.zf=r==0;self.sf=(r>>(w-1))&1!=0;self.of=false;}
}
#[repr(C)]
#[derive(Clone, Copy, Default)]
pub(super) struct Eval {kind:u32,pub offset:f32,pub v0:f32,pub v1:f32,pub v2:f32}
impl Eval {
 pub fn new(kind:u32,offset:f32,v0:f32,v1:f32,v2:f32)->Self{Self{kind,offset,v0,v1,v2}}
 pub fn evaluate(&self,t:f32)->f32 {
  match self.kind {
   1 if t==1.0=>self.v1,
   2 if t==1.0=>self.v2,
   2|3 if t==0.0=>self.v1,
   4=>{if t<=self.v1 {SseAddF32(SseMulF32(SseDivF32(SseSubF32(self.v0,self.offset),self.v1),t),self.offset)}
        else {let slope=SseDivF32(SseSubF32(self.v2,self.v0),SseSubF32(1.0,self.v1));SseSubF32(SseAddF32(SseMulF32(slope,t),self.v2),slope)}},
   _=>SseAddF32(SseMulF32(SseSubF32(self.v0,self.offset),t),self.offset),
  }
 }
}

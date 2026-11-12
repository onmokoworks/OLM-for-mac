//! Recorded-context host services for native original-worker replay only.
//! No image algorithm is implemented here; the actual AEX worker does that.
use std::{ffi::{c_void,CStr},ptr,sync::atomic::{AtomicUsize,Ordering}};
#[link(name="kernel32")]
extern "system" { fn LoadLibraryW(path:*const u16)->*mut u8; fn FreeLibrary(p:*mut u8)->i32; }
static BPP:AtomicUsize=AtomicUsize::new(4);
unsafe fn q(p:*const u8,o:usize)->usize {ptr::read_unaligned(p.add(o).cast())}
unsafe fn i(p:*const u8,o:usize)->i32 {ptr::read_unaligned(p.add(o).cast())}
unsafe extern "C" fn new_handle(n:u64)->*mut c_void {
    if n>64*1024*1024 {return ptr::null_mut();}
    Box::into_raw(Box::new(vec![0u8;n as usize])).cast()
}
unsafe extern "C" fn lock(h:*mut c_void)->*mut u8 {(*h.cast::<Vec<u8>>()).as_mut_ptr()}
unsafe extern "C" fn unlock(_: *mut c_void) {}
unsafe extern "C" fn dispose(h:*mut c_void) {drop(Box::from_raw(h.cast::<Vec<u8>>()));}
#[repr(C)] struct Handles {
    new:unsafe extern "C" fn(u64)->*mut c_void,
    lock:unsafe extern "C" fn(*mut c_void)->*mut u8,
    unlock:unsafe extern "C" fn(*mut c_void), dispose:unsafe extern "C" fn(*mut c_void),
}
static HANDLES:Handles=Handles{new:new_handle,lock,unlock,dispose};
unsafe extern "C" fn acquire(name:*const i8,version:i32,out:*mut *const c_void)->i32 {
    if CStr::from_ptr(name).to_bytes()!=b"PF Handle Suite" || version!=2 {return 13;}
    *out=ptr::addr_of!(HANDLES).cast(); 0
}
unsafe extern "C" fn release(_: *const i8,_:i32)->i32 {0}
#[repr(C)] struct Basic {
    acquire:unsafe extern "C" fn(*const i8,i32,*mut *const c_void)->i32,
    release:unsafe extern "C" fn(*const i8,i32)->i32,
}
static BASIC:Basic=Basic{acquire,release};
unsafe extern "C" fn copy_world(_:usize,src:*const u8,dst:*mut u8,_:*const u8)->i32 {
    let (w,h)=(i(src,0x24),i(src,0x28));
    if w<0 || h<0 || w!=i(dst,0x24) || h!=i(dst,0x28) {return 13;}
    let bytes=w as usize*BPP.load(Ordering::Relaxed);
    for y in 0..h as usize {
        ptr::copy((q(src,0x18) as *const u8).add(y*i(src,0x20) as usize),
                  (q(dst,0x18) as *mut u8).add(y*i(dst,0x20) as usize),bytes);
    }
    0
}
#[no_mangle]
pub unsafe extern "C" fn replay_worker(ctx:*mut u8,src:*const u8,dst:*mut u8,radius:*const f32,depth:u32,path:*const u16)->i32 {
    let rva=match depth {8=>0x1a6150,16=>0x1a5a90,32=>0x1a6800,_=>return -1};
    let module=LoadLibraryW(path); if module.is_null() {return -2;}
    BPP.store((depth/8*4) as usize,Ordering::Relaxed);
    let mut util=[0usize;9]; util[8]=copy_world as usize;
    let old_util=q(ctx,0xb0); let old_basic=q(ctx,0x180);
    ptr::write_unaligned(ctx.add(0xb0).cast::<usize>(),util.as_ptr() as usize);
    ptr::write_unaligned(ctx.add(0x180).cast::<usize>(),ptr::addr_of!(BASIC) as usize);
    let worker:unsafe extern "C" fn(*mut u8,usize,*const u8,*mut u8,*const f32)=std::mem::transmute(module.add(rva));
    worker(ctx,0,src,dst,radius);
    ptr::write_unaligned(ctx.add(0xb0).cast::<usize>(),old_util);
    ptr::write_unaligned(ctx.add(0x180).cast::<usize>(),old_basic);
    FreeLibrary(module); 0
}

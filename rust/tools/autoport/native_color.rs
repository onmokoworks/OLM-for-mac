//! Native parameter-parent replay. Host replies are actual recorded suite calls.
use std::{ptr,ffi::{c_void,CStr}};
#[link(name="kernel32")]
extern "system" {fn LoadLibraryW(p:*const u16)->*mut u8;fn FreeLibrary(p:*mut u8)->i32;}
static mut PARAMS:*const u8=ptr::null();
static mut COLORS:*const u8=ptr::null();
static mut SLOTS:[usize;101]=[0;101];
unsafe extern "C" fn checkout(_:usize,slot:i32,_:i32,_:i32,_:u32,out:*mut u8)->i32 {
    if !(1..=101).contains(&slot){return 13;}
    ptr::copy_nonoverlapping(PARAMS.add((slot-1) as usize*176),out,176);
    SLOTS[(slot-1) as usize]=out as usize;0
}
unsafe extern "C" fn checkin(_:usize,_:*mut u8)->i32 {0}
unsafe extern "C" fn color(_:usize,param:*const u8,out:*mut u8)->i32 {
    for k in 1..101 {if SLOTS[k]==param as usize {ptr::copy_nonoverlapping(COLORS.add((k-1)*16),out,16);return 0;}}
    13
}
#[repr(C)] struct Color {get:unsafe extern "C" fn(usize,*const u8,*mut u8)->i32}
static COLOR:Color=Color{get:color};
unsafe extern "C" fn acquire(name:*const i8,version:i32,out:*mut *const c_void)->i32 {
    if CStr::from_ptr(name).to_bytes()!=b"PF ColorParamSuite" || version!=1 {return 13;}
    *out=ptr::addr_of!(COLOR).cast();0
}
unsafe extern "C" fn release(_: *const i8,_:i32)->i32 {0}
#[repr(C)] struct Basic {get:unsafe extern "C" fn(*const i8,i32,*mut *const c_void)->i32,release:unsafe extern "C" fn(*const i8,i32)->i32}
static BASIC:Basic=Basic{get:acquire,release};
#[no_mangle]
pub unsafe extern "C" fn replay_snapshot(indata:*mut u8,world:*mut u8,context:*mut u8,params:*const u8,colors:*const u8,path:*const u16)->i32 {
    PARAMS=params;COLORS=colors;SLOTS=[0;101];
    let module=LoadLibraryW(path);if module.is_null(){return -1;}
    let offsets=[0usize,8,0x180];let values=[checkout as usize,checkin as usize,ptr::addr_of!(BASIC) as usize];
    let mut old=[0usize;3];
    for k in 0..3 {old[k]=ptr::read_unaligned(indata.add(offsets[k]).cast());ptr::write_unaligned(indata.add(offsets[k]).cast(),values[k]);}
    let f:unsafe extern "C" fn(u64,*mut u8,u64,u64,*mut u8,*mut u8)->i32=std::mem::transmute(module.add(0x1a90));
    let result=f(8,indata,0,0,world,context);
    for k in 0..3 {ptr::write_unaligned(indata.add(offsets[k]).cast(),old[k]);}
    FreeLibrary(module);result
}

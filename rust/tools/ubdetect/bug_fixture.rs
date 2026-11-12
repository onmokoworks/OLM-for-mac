//! Test-only wrapper around a separately loaded qualified Rust Smoother.
//! --cfg deliberate_bug changes exactly one output byte after Classic render.
use std::{ffi::c_void, sync::OnceLock};
type Entry = unsafe extern "C" fn(i32,*mut c_void,*mut c_void,*mut c_void,*mut u8,*mut c_void)->i32;
#[link(name="kernel32")]
extern "system" {
    fn LoadLibraryW(path:*const u16)->*mut c_void;
    fn GetProcAddress(module:*mut c_void,name:*const u8)->*mut c_void;
}
static ENTRY: OnceLock<usize> = OnceLock::new();
#[no_mangle]
pub unsafe extern "C" fn EffectMain(cmd:i32,i:*mut c_void,o:*mut c_void,p:*mut c_void,w:*mut u8,e:*mut c_void)->i32 {
    let raw = *ENTRY.get_or_init(|| {
        let path:Vec<u16>=env!("UBDETECT_FORWARD_AEX").encode_utf16().chain(Some(0)).collect();
        let module=LoadLibraryW(path.as_ptr());
        if module.is_null() { return 0; }
        GetProcAddress(module,b"EffectMain\0".as_ptr()) as usize
    });
    if raw==0 { return 1; }
    let entry:Entry=std::mem::transmute(raw);
    let err=entry(cmd,i,o,p,w,e);
    #[cfg(deliberate_bug)]
    if err==0 && cmd==11 && !w.is_null() {
        // Windows x64 PF_EffectWorld.data = +0x18, packed ARGB8 for this test.
        let data=std::ptr::read_unaligned(w.add(0x18) as *const *mut u8);
        if !data.is_null() { *data ^= 1; }
    }
    err
}
#[no_mangle]
pub unsafe extern "C" fn entryPointFunc(cmd:i32,i:*mut c_void,o:*mut c_void,p:*mut c_void,w:*mut u8,e:*mut c_void)->i32 {
    EffectMain(cmd,i,o,p,w,e)
}

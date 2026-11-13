//! Test-only executable accepts the render CLI shape; it is NOT an AE host.
use std::{ffi::c_void, os::windows::ffi::OsStrExt};
#[link(name="kernel32")]
extern "system" {
    fn LoadLibraryW(path: *const u16) -> *mut c_void;
    fn GetProcAddress(module: *mut c_void, name: *const u8) -> *mut c_void;
}
fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args[1] == "--owned-child" {
        std::thread::sleep(std::time::Duration::from_secs(30));
        return;
    }
    let path: Vec<_> = std::ffi::OsStr::new(&args[3]).encode_wide().chain(Some(0)).collect();
    let module = unsafe { LoadLibraryW(path.as_ptr()) };
    assert!(!module.is_null());
    let mixed: unsafe extern "C" fn(u64,f64,u32,f32,u64,*mut u64)->u64 = unsafe {
        std::mem::transmute(GetProcAddress(module, b"mixed\0".as_ptr()))
    };
    let nested: extern "C" fn(u32)->u32 = unsafe { std::mem::transmute(GetProcAddress(module, b"nested\0".as_ptr())) };
    let returned: extern "C" fn(u32,u32)->*mut u8 = unsafe { std::mem::transmute(GetProcAddress(module, b"returned\0".as_ptr())) };
    let mut threads = Vec::new();
    for i in 0..4u64 {
        threads.push(std::thread::spawn(move || {
            for j in 0..3u64 {
                let mut output = 0;
                let result = unsafe { mixed(i*3+j, -2.5, 0xfedcba98, -0.0, 0xfedcba9876543210, &mut output) };
                assert_eq!(result, output);
            }
        }));
    }
    for t in threads { t.join().unwrap(); }
    assert_eq!(nested(3), 7);
    assert!(!returned(16, 250).is_null());
    let request = std::fs::read_to_string(&args[6]).unwrap();
    if request.contains("crash") { std::process::abort(); }
    if request.contains("timeout") { std::thread::sleep(std::time::Duration::from_secs(30)); }
    if request.contains("descendant") {
        let _child = std::process::Command::new(std::env::current_exe().unwrap()).arg("--owned-child").spawn().unwrap();
    }
    std::fs::copy(&args[4], &args[5]).unwrap();
}

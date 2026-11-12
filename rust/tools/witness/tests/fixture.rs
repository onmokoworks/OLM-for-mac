#[link(name = "ucrt")]
extern "C" {
    fn expf(x: f32) -> f32;
    fn powf(x: f32, y: f32) -> f32;
    fn sin(x: f64) -> f64;
}
#[link(name = "kernel32")]
extern "system" {
    fn Sleep(milliseconds: u32);
    fn GetTickCount() -> u32;
}
#[link(name = "witness_provider", kind = "raw-dylib")]
extern "C" {
    fn witness_mixed(a: u64, b: f64, c: f32, d: u64, e: f64, f: u64, g: f32, p: *mut u64) -> f64;
}
#[no_mangle]
pub unsafe extern "C" fn mixed(
    a: u64,
    b: f64,
    c: f32,
    d: u64,
    e: f64,
    f: u64,
    g: f32,
    p: *mut u64,
) -> f64 {
    witness_mixed(a, b, c, d, e, f, g, p)
}
#[no_mangle]
pub unsafe extern "C" fn math(x: f32, y: f32, z: f64) -> f64 {
    let _ = GetTickCount();
    expf(x) as f64 + powf(x, y) as f64 + sin(z)
}
#[repr(C)]
pub struct Blob {
    data: *mut u8,
    len: u64,
}
#[no_mangle]
pub unsafe extern "C" fn blob(b: *mut Blob) -> u64 {
    for i in 0..(*b).len as usize {
        *(*b).data.add(i) = (*(*b).data.add(i)).wrapping_add(1);
    }
    (*b).len
}
#[no_mangle]
pub unsafe extern "C" fn crash() {
    std::arch::asm!("ud2", options(noreturn));
}
#[no_mangle]
pub unsafe extern "C" fn hang() {
    Sleep(30000);
}
#[no_mangle]
pub unsafe extern "C" fn overwrite(p: *mut u8) {
    *p.add(8) = 0;
}

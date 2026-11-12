#[no_mangle]
pub unsafe extern "C" fn witness_mixed(
    a: u64,
    b: f64,
    c: f32,
    d: u64,
    e: f64,
    f: u64,
    g: f32,
    p: *mut u64,
) -> f64 {
    *p = a ^ d ^ f;
    b + c as f64 + e + g as f64
}

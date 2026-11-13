#[link(name="record_provider", kind="raw-dylib")]
extern "C" { fn ippRecordFixture(x: u64) -> u64; }
#[no_mangle]
#[inline(never)]
pub unsafe extern "C" fn mixed(a: u64, b: f64, c: u32, d: f32, e: u64, out: *mut u64) -> u64 {
    let answer = ippRecordFixture(a) ^ b.to_bits() ^ c as u64 ^ d.to_bits() as u64 ^ e;
    *out = answer;
    answer
}
#[no_mangle]
#[inline(never)]
pub extern "C" fn nested(n: u32) -> u32 {
    if n == 0 { return 1; }
    let f = std::hint::black_box(nested as extern "C" fn(u32) -> u32);
    std::hint::black_box(f(n-1)) + n
}
#[no_mangle]
#[inline(never)]
pub extern "C" fn returned(n: u32, seed: u32) -> *mut u8 {
    assert!(n <= 1024);
    let mut data: Vec<u8> = (0..n).map(|i| (seed as u8).wrapping_add(i as u8)).collect();
    let p = data.as_mut_ptr();
    std::mem::forget(data); // fixture allocation lives until owned child exit
    p
}

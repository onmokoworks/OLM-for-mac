//! Witness-only ABI adapter: the production plateau detector, preallocated native vector.
use crate::algorithm::{self, Color, Layout};
unsafe fn detect(
    w: *const u8,
    x: i32,
    y: i32,
    v: *mut u8,
    excluded: *const Color,
    n: i32,
    bpp: usize,
) -> u64 {
    let width = *(w.add(0x24).cast::<i32>());
    let height = *(w.add(0x28).cast::<i32>());
    if x <= 0 || y <= 0 || x >= width - 1 || y >= height - 1 {
        return 0;
    }
    let row = *(w.add(0x20).cast::<i32>()) as usize;
    let data = *(w.add(0x18).cast::<*const u8>());
    let count = *(v.add(0x20).cast::<usize>());
    let colors = *(v.add(0x18).cast::<*mut Color>());
    let mut old = std::slice::from_raw_parts(excluded, n as usize).to_vec();
    old.extend_from_slice(std::slice::from_raw_parts(colors, count));
    let a = Layout {
        width: 3,
        height: 3,
        row_bytes: row,
        bytes_per_pixel: bpp,
        origin: (0, 0),
    };
    let input = std::slice::from_raw_parts(
        data.add((y as usize - 1) * row + (x as usize - 1) * bpp),
        a.span().unwrap(),
    );
    let found = algorithm::detect(input, a, &old, 1).unwrap();
    if let Some(&c) = found.first() {
        *colors.add(count) = c;
        *(v.add(0x20).cast::<usize>()) = count + 1
    }
    0
}
#[no_mangle]
pub unsafe extern "C" fn witness_detect8(
    w: *const u8,
    x: i32,
    y: i32,
    v: *mut u8,
    e: *const Color,
    n: i32,
) -> u64 {
    detect(w, x, y, v, e, n, 4)
}
#[no_mangle]
pub unsafe extern "C" fn witness_detect16(
    w: *const u8,
    x: i32,
    y: i32,
    v: *mut u8,
    e: *const Color,
    n: i32,
) -> u64 {
    detect(w, x, y, v, e, n, 8)
}
#[no_mangle]
pub unsafe extern "C" fn witness_detect32(
    w: *const u8,
    x: i32,
    y: i32,
    v: *mut u8,
    e: *const Color,
    n: i32,
) -> u64 {
    detect(w, x, y, v, e, n, 16)
}

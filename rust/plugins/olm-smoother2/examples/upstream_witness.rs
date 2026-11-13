//! Test-only scalar ABI adapters for the headless native witness.
use olm_smoother2::{class_plane, oklab, types::Pixel};
#[no_mangle]
pub unsafe extern "C" fn to_oklab(out: *mut Pixel, input: *const Pixel) -> *mut Pixel {
    *out = oklab::from_linear(*input);
    out
}
#[no_mangle]
pub unsafe extern "C" fn from_oklab(out: *mut Pixel, input: *const Pixel) -> *mut Pixel {
    *out = oklab::to_linear(*input);
    out
}
#[no_mangle]
pub unsafe extern "C" fn distance(a: *const Pixel, b: *const Pixel, space: i32) -> f32 {
    class_plane::distance_in_space(*a, *b, space + 1)
}
#[repr(C)]
pub struct Plane {
    data: *const Pixel,
    width: i32,
    height: i32,
    stride: i32,
}
#[no_mangle]
pub unsafe extern "C" fn classify(
    out: *mut u8,
    plane: *const Plane,
    x: i32,
    y: i32,
    params: *const u8,
) -> *mut u8 {
    let plane = &*plane;
    let version = *(params.add(4) as *const i32) + 1;
    // Extra fixture-only field beyond the original's config: unscaled UI range.
    let range = *(params.add(0x90) as *const f32);
    assert_eq!(
        (range * 0.01).to_bits(),
        (*(params.add(0x20) as *const f32)).to_bits()
    );
    let get = |xx: i32, yy: i32| {
        *((plane.data as *const u8).offset(yy as isize * plane.stride as isize) as *const Pixel)
            .offset(xx as isize)
    };
    let pixels: Vec<_> = (0..plane.height)
        .flat_map(|yy| (0..plane.width).map(move |xx| get(xx, yy)))
        .collect();
    let map = class_plane::build_with_range(
        &pixels,
        plane.width as usize,
        plane.height as usize,
        range,
        version,
        1,
        &mut olm_core::Budget::new(pixels.len() * 4),
    )
    .unwrap();
    for (n, b) in map[(y * plane.width + x) as usize].iter().enumerate() {
        *out.add(n) = (*b != 0) as u8;
    }
    out
}
#[no_mangle]
pub extern "C" fn cube_root(x: f32) -> f32 {
    oklab::cbrtf(x)
}

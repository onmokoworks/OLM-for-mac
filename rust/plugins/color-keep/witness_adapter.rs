//! Test-only ABI adapter. Uses the production pixel function; never installed.
use color_keep::pixel;
use olm_core::Pixel;

unsafe fn palette<'a>(ctx: *const u8) -> &'a [[f32; 4]] {
    let count = std::ptr::read_unaligned(ctx.add(0x20).cast::<i32>());
    assert!((0..=200).contains(&count));
    std::slice::from_raw_parts(ctx.add(0x24).cast(), count as usize)
}

macro_rules! callback {
    ($name:ident, $ty:ty, $variant:ident) => {
        #[no_mangle]
        pub unsafe extern "C" fn $name(
            ctx: *const u8,
            _x: i32,
            _y: i32,
            input: *const $ty,
            output: *mut $ty,
        ) -> i32 {
            let p = std::ptr::read_unaligned(input.cast::<[$ty; 4]>());
            let Pixel::$variant(result) = pixel(Pixel::$variant(p), palette(ctx)) else {
                unreachable!()
            };
            // The native callback writes alpha only; the caller copies RGB.
            std::ptr::write_unaligned(output, result[0]);
            0
        }
    };
}
callback!(callback8, u8, U8);
callback!(callback16, u16, U16);
callback!(callback32, f32, F32);

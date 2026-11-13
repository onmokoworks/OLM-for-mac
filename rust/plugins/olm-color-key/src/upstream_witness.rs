//! Test-only adapters for the 2026-11-12 pixel-callback ABI. No production export.
//! Context offsets are grounded in RVAs 0xa940/0x2360/0x2f30/0x3b30.
use crate::algorithm::{self, Key, Params};
use olm_core::{Depth, Layout, View, ViewMut};

unsafe fn pixel(context: *const u8, source: *const u8, dest: *mut u8, depth: Depth) -> u64 {
    if context.is_null() || source.is_null() || dest.is_null() {
        return 1;
    }
    let int = |at| std::ptr::read_unaligned(context.add(at).cast::<i32>());
    let float = |at| std::ptr::read_unaligned(context.add(at).cast::<f32>());
    let flag = |at| *context.add(at) != 0;
    let count = int(0x38);
    if !(0..=200).contains(&count) {
        return 1;
    }
    let p = Params {
        keep: true, // Pixel callbacks produce the kept matte; inversion is in their caller.
        replace: flag(0x24) && flag(0x4d),
        premultiplied: flag(0x25),
        space: int(0x30),
        precision: int(0x3c),
        per_component: flag(0x34),
        per_color: flag(0x35),
        threshold: float(0x50),
        components: [float(0x58), float(0x5c), float(0x60)],
        keys: (0..count as usize)
            .map(|n| Key {
                enabled: flag(0x25f4 + n),
                replace: flag(0x26bc + n),
                color: std::array::from_fn(|c| float(0x78 + n * 16 + c * 4)),
                replacement: std::array::from_fn(|c| float(0xcf8 + n * 16 + c * 4)),
                threshold: float(0x1974 + n * 4),
                components: [
                    float(0x1c94 + n * 4),
                    float(0x1fb4 + n * 4),
                    float(0x22d4 + n * 4),
                ],
            })
            .collect(),
        ..Params::default()
    };
    let size = depth.pixel_bytes();
    let layout = Layout {
        width: 1,
        height: 1,
        stride: size,
        origin: (0, 0),
        depth,
    };
    let input = std::slice::from_raw_parts(source, size);
    let output = std::slice::from_raw_parts_mut(dest, size);
    let Ok(input) = View::new(input, layout) else {
        return 1;
    };
    let Ok(mut output) = ViewMut::new(output, layout) else {
        return 1;
    };
    match algorithm::render(&input, &mut output, &p) {
        Ok(()) => 0,
        Err(_) => 1,
    }
}
macro_rules! adapter {
    ($name:ident,$depth:expr) => {
        #[no_mangle]
        pub unsafe extern "C" fn $name(
            context: *const u8,
            _x: usize,
            _y: usize,
            source: *const u8,
            dest: *mut u8,
        ) -> u64 {
            std::panic::catch_unwind(|| pixel(context, source, dest, $depth)).unwrap_or(1)
        }
    };
}
adapter!(olm_ck_witness8, Depth::U8);
adapter!(olm_ck_witness16, Depth::U16);
adapter!(olm_ck_witness32, Depth::F32);

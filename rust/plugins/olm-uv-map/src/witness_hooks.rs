//! Diagnostic-only native ABI bridges; never enabled in a release plug-in.
use super::*;
unsafe fn read<T: Copy>(p: *const u8, offset: usize) -> T {
    std::ptr::read_unaligned(p.add(offset).cast())
}
unsafe fn world<'a>(p: *const u8, bytes: usize) -> (&'a [u8], Layout) {
    let l = Layout {
        width: read::<i32>(p, 0x24) as usize,
        height: read::<i32>(p, 0x28) as usize,
        row_bytes: read::<i32>(p, 0x20) as usize,
        bytes_per_pixel: bytes,
        origin: (0, 0),
    };
    (
        std::slice::from_raw_parts(read::<*const u8>(p, 0x18), l.span().unwrap()),
        l,
    )
}
unsafe fn write_pixel(p: *mut u8, pixel: Pixel, bytes: usize) {
    for c in 0..4 {
        match bytes {
            4 => p.add(c).write(pixel[c] as u8),
            8 => std::ptr::write_unaligned(p.add(c * 2).cast::<u16>(), pixel[c] as u16),
            _ => std::ptr::write_unaligned(p.add(c * 4).cast::<f32>(), pixel[c]),
        }
    }
}
unsafe fn bilinear_bridge(
    w: *const u8,
    x: i32,
    y: i32,
    dx: f32,
    dy: f32,
    out: *mut u8,
    bytes: usize,
) {
    let (data, l) = world(w, bytes);
    let im = Image::decode(data, l).unwrap();
    // Corpus uses binary fractions exactly representable after adding x/y.
    write_pixel(
        out,
        bilinear(&im, x as f32 + dx, y as f32 + dy, bytes),
        bytes,
    );
}
macro_rules! bilinear_export {
    ($name:ident,$bytes:expr) => {
        #[no_mangle]
        pub unsafe extern "C" fn $name(
            w: *const u8,
            x: i32,
            y: i32,
            dx: f32,
            dy: f32,
            out: *mut u8,
        ) {
            bilinear_bridge(w, x, y, dx, dy, out, $bytes)
        }
    };
}
bilinear_export!(uv_bilinear8, 4);
bilinear_export!(uv_bilinear16, 8);
bilinear_export!(uv_bilinear32, 16);

#[no_mangle]
pub unsafe extern "C" fn uv_mipmaps(state: *const u8, texture: *const u8) {
    let depth = read::<i32>(state, 8) as usize;
    let (data, l) = world(texture, depth / 2);
    let levels = mipmaps(&Image::decode(data, l).unwrap(), depth / 2).unwrap();
    let worlds = read::<*const u8>(state, 16);
    for (k, image) in levels.iter().enumerate() {
        let w = worlds.add(k * 0x78);
        let data = read::<*mut u8>(w, 24);
        let stride = read::<i32>(w, 32) as usize;
        for y in 0..image.height {
            for x in 0..image.width {
                write_pixel(
                    data.add(y * stride + x * 16),
                    image.pixels[y * image.width + x],
                    16,
                );
            }
        }
    }
}
unsafe fn pixel_bridge(ctx: *const u8, x: i32, y: i32, out: *mut u8, bytes: usize) -> u64 {
    let (input, l) = world(read::<*const u8>(ctx, 8), bytes);
    let texture = world(ctx.add(0x28), bytes);
    let b = Layout {
        width: 1,
        height: 1,
        row_bytes: bytes,
        bytes_per_pixel: bytes,
        origin: (x, y),
    };
    let params = Params {
        method: read(ctx, 0x24),
        smoothness: read(ctx, 0xa0),
    };
    render(
        input,
        l,
        Some(texture),
        std::slice::from_raw_parts_mut(out, bytes),
        b,
        params,
    )
    .unwrap();
    0
}
macro_rules! pixel_export {
    ($name:ident,$bytes:expr) => {
        #[no_mangle]
        pub unsafe extern "C" fn $name(
            ctx: *const u8,
            x: i32,
            y: i32,
            _input: *const u8,
            out: *mut u8,
        ) -> u64 {
            pixel_bridge(ctx, x, y, out, $bytes)
        }
    };
}
pixel_export!(uv_pixel8, 4);
pixel_export!(uv_pixel16, 8);
pixel_export!(uv_pixel32, 16);

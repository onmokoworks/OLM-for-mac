//! Structured pixel kernels. Integer input bounds make every intermediate finite;
//! ordinary IEEE operations therefore equal the reference SSE wrappers, including
//! operation order. No reassociation, reciprocal approximation or FMA is used.
use super::{kernels, support::*};

#[inline]
fn compare(a: [u16; 4], b: [u16; 4], deep: bool) -> i32 {
    if a == b {
        return 0;
    }
    let alpha = |v: u16| {
        if deep {
            v as f32 * (1.0 / 32768.0)
        } else {
            v as f32 / 255.0
        }
    };
    let aa = alpha(a[0]);
    let ba = alpha(b[0]);
    let ar = a[1] as f32 * aa;
    let ag = a[2] as f32 * aa;
    let ab = a[3] as f32 * aa;
    let br = b[1] as f32 * ba;
    let bg = b[2] as f32 * ba;
    let bb = b[3] as f32 * ba;
    let luma = ((ar * 0.30 + ag * 0.59) + ab * 0.11) - ((br * 0.30 + bg * 0.59) + bb * 0.11);
    let metric = (((a[0] as i32 - b[0] as i32).abs() as f32 + (ar - br).abs()) + (ab - bb).abs())
        + (ag - bg).abs();
    let magnitude = ((metric as i32 / 4).max(1)).max(luma.abs().ceil() as i32);
    if luma > 0.0 {
        magnitude
    } else {
        -magnitude
    }
}

#[inline]
pub(super) unsafe fn ColorCompare8(a: *mut u8, b: *mut u8) -> i32 {
    if a.is_null() || b.is_null() {
        return 0;
    }
    compare(
        a.cast::<[u8; 4]>().read().map(u16::from),
        b.cast::<[u8; 4]>().read().map(u16::from),
        false,
    )
}
#[inline]
pub(super) unsafe fn ColorCompare16(a: *mut u16, b: *mut u16) -> i32 {
    if a.is_null() || b.is_null() {
        return 0;
    }
    compare(
        a.cast::<[u16; 4]>().read(),
        b.cast::<[u16; 4]>().read(),
        true,
    )
}

unsafe fn neighbors(x: i32, y: i32, state: *mut RenderState, out: *mut u64, size: i32) {
    let world = &*(*state).src_world;
    for dy in -1..=1 {
        for dx in -1..=1 {
            let xx = x + dx;
            let yy = y + dy;
            let pointer = if xx >= 0 && xx < world.width && yy >= 0 && yy < world.height {
                world
                    .data
                    .cast::<u8>()
                    .offset((yy * world.rowbytes) as isize + (xx * size) as isize)
                    as u64
            } else {
                0
            };
            out.add(((dy + 1) * 3 + dx + 1) as usize).write(pointer);
        }
    }
}
pub(super) unsafe fn NeighborExtract8(x: i32, y: i32, s: *mut RenderState, n: *mut u64) {
    neighbors(x, y, s, n, 4);
}
pub(super) unsafe fn NeighborExtract16(x: i32, y: i32, s: *mut RenderState, n: *mut u64) {
    neighbors(x, y, s, n, 8);
}

// The first classifier branch rejects most directions. Evaluate it before
// constructing the reference's virtual register file and 4 KiB stack carrier.
pub(super) unsafe fn Classifier16Exact(
    s: *mut RenderState,
    x: u32,
    y: u32,
    n: *mut u64,
    d: u32,
) -> i32 {
    if ColorCompare16(*n.add(4) as *mut u16, *n.add(d as usize) as *mut u16)
        >= -128 * (*s).tolerance_hi
    {
        return 0;
    }
    kernels::Classifier16Slow(s, x, y, n, d)
}

pub(super) unsafe fn Classifier8(
    s: *mut RenderState,
    _x: u32,
    _y: u32,
    n: *mut u64,
    d: u32,
) -> i32 {
    let pixel = |i: usize| *n.add(i) as *mut u8;
    let center = pixel(4);
    let tolerance = (*s).tolerance_lo;
    if ColorCompare8(center, pixel(d as usize)) >= -tolerance {
        return 0;
    }
    let close = |a: *mut u8, b: *mut u8| {
        if a.is_null() || b.is_null() {
            return false;
        }
        (0..4).all(|c| (*a.add(c) as i32 - *b.add(c) as i32).abs() <= tolerance)
    };
    let isolated = ![6, 8, 2, 0, 3, 5, 1, 7]
        .into_iter()
        .any(|i| close(center, pixel(i)));
    let d = d as usize;
    let left = pixel(DAT_18000f000[d] as usize);
    let right = pixel(DAT_18000f028[d] as usize);
    let forward_left = pixel(DAT_18000f050[d] as usize);
    let forward_right = pixel(DAT_18000f078[d] as usize);
    // Both paired branches reach the tail with flag_b still zero. Remaining
    // prefix calculations only modify dead temporaries, not pixels or state.
    let paired = (close(center, left) && close(pixel(d), forward_left))
        || (close(center, right) && close(forward_left, forward_right));
    let flag_b = !paired && close(center, forward_left);
    kernels::Classifier8Tail(s, n, d as u32, isolated as u8, flag_b as u8)
}

pub(super) unsafe fn ScanlinePixel8_Main(
    s: *mut (),
    x: i32,
    y: i32,
    _i: *mut Pixel8,
    _o: *mut Pixel8,
) -> i32 {
    let s = s.cast::<RenderState>();
    let mut n = [0u64; 10];
    NeighborExtract8(x, y, s, n.as_mut_ptr());
    for d in [5, 3, 1, 7] {
        let kind = Classifier8(s, x as u32, y as u32, n.as_mut_ptr(), d);
        kernels::DispatchDirection8(s, n.as_mut_ptr(), x as u32, y as u32, d, kind);
    }
    0
}
pub(super) unsafe fn ScanlinePixel16_Main(
    s: *mut (),
    x: i32,
    y: i32,
    _i: *mut Pixel16,
    _o: *mut Pixel16,
) -> i32 {
    let s = s.cast::<RenderState>();
    let mut n = [0u64; 10];
    NeighborExtract16(x, y, s, n.as_mut_ptr());
    for d in [5, 3, 1, 7] {
        let kind = Classifier16Exact(s, x as u32, y as u32, n.as_mut_ptr(), d);
        kernels::DispatchDirection16(s, n.as_mut_ptr(), x as u32, y as u32, d, kind);
    }
    0
}

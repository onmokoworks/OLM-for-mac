use olm_core::{Depth, Layout};
use olm_toon_dilate::algorithm::{effective_radius, render};
extern "C" {
    fn toon_reference(
        input: *const u8,
        output: *mut u8,
        iw: i32,
        ih: i32,
        istride: i32,
        ow: i32,
        oh: i32,
        ostride: i32,
        depth: i32,
        radius: f64,
        numerator: i32,
        denominator: u32,
    ) -> i32;
}
fn next(s: &mut u64) -> u32 {
    *s ^= *s << 13;
    *s ^= *s >> 7;
    *s ^= *s << 17;
    (*s >> 19) as u32
}
fn case(
    seed: u64,
    depth: Depth,
    w: usize,
    h: usize,
    ow: usize,
    oh: usize,
    radius: f64,
    num: i32,
    den: u32,
) -> Vec<u8> {
    let bpp = depth.pixel_bytes();
    let il = Layout {
        width: w,
        height: h,
        stride: w * bpp + 3,
        depth,
        origin: (27, -16),
    };
    let ol = Layout {
        width: ow,
        height: oh,
        stride: ow * bpp + 7,
        depth,
        origin: (-2, 41),
    };
    let mut input = vec![0x81; il.stride * h];
    let mut state = seed | 1;
    for y in 0..h {
        for x in 0..w {
            let at = y * il.stride + x * bpp;
            for c in 0..bpp {
                input[at + c] = next(&mut state) as u8;
            }
            let n = next(&mut state) as usize;
            match depth {
                Depth::U8 => input[at] = [0, 1, 128, 254, 255][n % 5],
                Depth::U16 => input[at..at + 2].copy_from_slice(
                    &[0u16, 1, 16384, 32767, 32768, 32769, 65535][n % 7].to_ne_bytes(),
                ),
                Depth::F32 => input[at..at + 4].copy_from_slice(
                    &[
                        0u32, 0x80000000, 0x3f000000, 0x3f7fffff, 0x3f800000, 0x3f800001,
                        0xbf800000, 0x7f800000, 0xff800000, 0x7fc01234, 0x7f800123,
                    ][n % 11]
                        .to_ne_bytes(),
                ),
            }
        }
    }
    let original = input.clone();
    let mut expected = vec![0xa9; ol.stride * oh];
    let mut actual = expected.clone();
    unsafe {
        assert_eq!(
            toon_reference(
                input.as_ptr(),
                expected.as_mut_ptr(),
                w as _,
                h as _,
                il.stride as _,
                ow as _,
                oh as _,
                ol.stride as _,
                match depth {
                    Depth::U8 => 8,
                    Depth::U16 => 16,
                    Depth::F32 => 32,
                },
                radius,
                num,
                den
            ),
            0
        );
    }
    render(
        &input,
        il,
        &mut actual,
        ol,
        effective_radius(radius, num, den).unwrap(),
    )
    .unwrap();
    assert_eq!(
        actual, expected,
        "seed={seed}, {depth:?}, {w}x{h}->{ow}x{oh}, radius={radius}, scale={num}/{den}"
    );
    assert_eq!(input, original);
    actual
}
#[test]
fn production_cpp_reference_matrix() {
    let mut count = 0;
    for depth in [Depth::U8, Depth::U16, Depth::F32] {
        for (w, h) in [(1, 1), (1, 9), (9, 1), (2, 2), (5, 3), (7, 5), (31, 19)] {
            for radius in [
                0.0, 0.000001, 0.1, 1.0, 1.00000001, 2.01, 3.0, 4.0, 13.0, 100.0,
            ] {
                for (num, den) in [(0, 0), (1, 1), (1, 2), (1, 4), (2, 3)] {
                    for shape in 0..3 {
                        let (ow, oh) = match shape {
                            0 => (w, h),
                            1 => ((w + 1) / 2, (h + 1) / 2),
                            _ => (w + 2, h + 1),
                        };
                        case(0x12345678 + count, depth, w, h, ow, oh, radius, num, den);
                        count += 1;
                    }
                }
            }
        }
    }
    assert_eq!(count, 3150);
}
#[test]
fn concurrent_frames_are_independent() {
    // Cropped-world raster passes remain serial; independent frames may run
    // concurrently. Compare 1, 2 and 7 scheduling threads on identical jobs.
    let jobs = 42;
    let run = |threads| {
        let mut rows = vec![Vec::<u8>::new(); jobs];
        olm_core::parallel_rows(&mut rows, 1, threads, |i, row| {
            row[0] = case(i as u64 + 37, Depth::F32, 17, 11, 13, 9, 2.01, 1, 2);
        })
        .unwrap();
        rows
    };
    assert_eq!(run(1), run(2));
    assert_eq!(run(1), run(7));
}
#[test]
fn invalid_inputs_do_not_modify_output() {
    for radius in [-1.0, 100.1, f64::NAN, f64::INFINITY] {
        assert!(effective_radius(radius, 1, 1).is_err());
    }
    for (num, den) in [(0, 1), (-1, 1), (1, 0)] {
        assert!(effective_radius(2.0, num, den).is_err());
    }
    assert_eq!(effective_radius(1.00000001, 1, 1).unwrap(), 1);
    assert_eq!(effective_radius(2.01, 1, 2).unwrap(), 2);
    assert_eq!(effective_radius(2.0, 0, 0).unwrap(), 2);
    let l = Layout {
        width: 1,
        height: 1,
        stride: 4,
        depth: Depth::U8,
        origin: (0, 0),
    };
    let mut output = [0x55; 4];
    assert!(render(&[1; 3], l, &mut output, l, 2).is_err());
    assert_eq!(output, [0x55; 4]);
}

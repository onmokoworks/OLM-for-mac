use super::algorithm::{integer_store, render, Params};
use olm_core::{Depth, Layout, View, ViewMut};
unsafe extern "C" {
    fn blur_reference(
        src: *const u8,
        dst: *mut u8,
        w: usize,
        h: usize,
        depth: i32,
        legacy: bool,
        amount: f32,
        smoothness: f32,
        repeat: usize,
        bias: usize,
        scale: f32,
    );
}
fn next(state: &mut u32) -> u32 {
    *state ^= *state << 13;
    *state ^= *state >> 17;
    *state ^= *state << 5;
    *state
}
#[test]
fn six_workers_match_cpp_and_thread_counts() {
    let mut state = 0xb10b2026;
    let special = [
        0u32, 0x80000000, 0x7f800000, 0xff800000, 0x7fc12345, 0xffc23456, 0x7f812345, 1, 0x80000001,
    ];
    let mut count = 0;
    for depth in [Depth::U8, Depth::U16, Depth::F32] {
        for case in 0..144 {
            let (w, h) = [
                (1, 1),
                (3, 7),
                (11, 7),
                (17, 13),
                (31, 19),
                (2, 1),
                (1, 9),
                (7, 6),
            ][case % 8];
            let p = Params {
                amount: [1.0, 2.0, 2.9999998, 5.0, 13.7, 50.0, 127.0, 1000.0][case % 8],
                smoothness: [1.0, 31.0, 100.0][case % 3],
                repeat: [1, 2, 3, 7, 10][case % 5],
                bias: 1 + (case / 2) % 2,
                legacy: case % 2 == 1,
                scale: [1.0, 0.5, 0.25][(case / 3) % 3],
            };
            let size = w * h * depth.pixel_bytes();
            let mut input = vec![0u8; size];
            match depth {
                Depth::U8 => {
                    for b in &mut input {
                        *b = next(&mut state) as u8;
                    }
                }
                Depth::U16 => {
                    for c in input.chunks_exact_mut(2) {
                        c.copy_from_slice(&(next(&mut state) as u16).to_ne_bytes());
                    }
                }
                Depth::F32 => {
                    for (i, c) in input.chunks_exact_mut(4).enumerate() {
                        let bits = if case % 3 == 0 {
                            special[i % special.len()]
                        } else {
                            ((next(&mut state) % 32001) as f32 / 1000.0 - 16.0).to_bits()
                        };
                        c.copy_from_slice(&bits.to_ne_bytes());
                    }
                }
            }
            // Transparent boundaries, including hidden RGB and alpha negative zero.
            for pixel in (0..w * h).step_by(5) {
                let channel = depth.pixel_bytes() / 4;
                input[pixel * channel * 4..pixel * channel * 4 + channel].fill(0);
            }
            let layout = Layout {
                width: w,
                height: h,
                stride: w * depth.pixel_bytes(),
                depth,
                origin: (0, 0),
            };
            let view = View::new(&input, layout).unwrap();
            let mut reference = vec![0u8; size];
            unsafe {
                blur_reference(
                    input.as_ptr(),
                    reference.as_mut_ptr(),
                    w,
                    h,
                    match depth {
                        Depth::U8 => 8,
                        Depth::U16 => 16,
                        Depth::F32 => 32,
                    },
                    p.legacy,
                    p.amount,
                    p.smoothness,
                    p.repeat,
                    p.bias,
                    p.scale,
                );
            }
            for threads in [1, 4] {
                let mut candidate = vec![0u8; size];
                render(
                    &view,
                    &mut ViewMut::new(&mut candidate, layout).unwrap(),
                    &p,
                    threads,
                )
                .unwrap();
                let mut bytes = vec![0xa5; size];
                super::algorithm::render_bytes(&view, &mut bytes, layout, &p, threads).unwrap();
                assert_eq!(
                    bytes, candidate,
                    "byte writer depth={depth:?} case={case} threads={threads}"
                );
                if candidate != reference {
                    let first = candidate
                        .iter()
                        .zip(&reference)
                        .position(|(a, b)| a != b)
                        .unwrap();
                    panic!("depth={depth:?} case={case} params={p:?} threads={threads} first byte={first} actual={:?} expected={:?}", &candidate[first.saturating_sub(8)..(first+16).min(size)], &reference[first.saturating_sub(8)..(first+16).min(size)]);
                }
            }
            count += 1;
        }
    }
    assert_eq!(count, 432);
}
#[test]
fn typed_writers_keep_low_bits() {
    for (v, expected) in [
        (32768.5, 32769),
        (65535.0, 65535),
        (65536.0, 65536),
        (-1.0, -1),
        (f32::NAN, i32::MIN),
        (f32::INFINITY, i32::MIN),
    ] {
        assert_eq!(integer_store(v), expected);
    }
    assert_eq!(integer_store(65536.0) as u16, 0);
    assert_eq!(integer_store(-1.0) as u8, 255);
}
#[test]
fn odd_stride_and_padding_are_preserved() {
    for depth in [Depth::U8, Depth::U16, Depth::F32] {
        let (w, h) = (7, 9);
        let row = w * depth.pixel_bytes();
        let l = Layout {
            width: w,
            height: h,
            stride: row + 3,
            depth,
            origin: (0, 0),
        };
        let mut input = vec![0u8; l.span().unwrap()];
        let mut source = ViewMut::new(&mut input, l).unwrap();
        for y in 0..h {
            for x in 0..w {
                source
                    .set(
                        x,
                        y,
                        match depth {
                            Depth::U8 => olm_core::Pixel::U8([255, x as u8, y as u8, 77]),
                            Depth::U16 => olm_core::Pixel::U16([32768, x as u16, y as u16, 32768]),
                            Depth::F32 => olm_core::Pixel::F32([1.0, x as f32, y as f32, 0.5]),
                        },
                    )
                    .unwrap();
            }
        }
        let o = Layout {
            stride: row + 5,
            ..l
        };
        let mut output = vec![0x5a; o.span().unwrap()];
        render(
            &View::new(&input, l).unwrap(),
            &mut ViewMut::new(&mut output, o).unwrap(),
            &Params::default(),
            4,
        )
        .unwrap();
        for y in 0..h - 1 {
            assert!(output[y * o.stride + row..(y + 1) * o.stride]
                .iter()
                .all(|b| *b == 0x5a));
        }
    }
}

#[test]
fn uniform_legacy_carry_partitions_match_cpp() {
    let mut count = 0;
    for depth in [Depth::U8, Depth::U16, Depth::F32] {
        for case in 0..12 {
            let (w, h) = [(1, 1), (3, 7), (13, 11), (17, 13)][case % 4];
            let layout = Layout {
                width: w,
                height: h,
                stride: w * depth.pixel_bytes(),
                depth,
                origin: (0, 0),
            };
            let size = layout.span().unwrap();
            let mut input = vec![0; size];
            {
                let mut v = ViewMut::new(&mut input, layout).unwrap();
                for y in 0..h {
                    for x in 0..w {
                        let transparent = case / 4 == 1 && (x == w / 2 || y == h / 2);
                        let changed = case / 4 == 2 && x == w / 6 && y == h / 6;
                        let pixel = match depth {
                            Depth::U8 => olm_core::Pixel::U8([
                                if transparent { 0 } else { 255 },
                                if changed { 11 } else { 77 },
                                77,
                                77,
                            ]),
                            Depth::U16 => olm_core::Pixel::U16([
                                if transparent { 0 } else { 32768 },
                                if changed { 11 } else { 65535 },
                                65535,
                                65535,
                            ]),
                            Depth::F32 => olm_core::Pixel::F32([
                                if transparent { 0.0 } else { -1.0 },
                                if changed { 0.5 } else { -1.0 },
                                -1.0,
                                -1.0,
                            ]),
                        };
                        v.set(x, y, pixel).unwrap();
                    }
                }
            }
            for bias in [1, 2] {
                for scale in [1.0, 0.25] {
                    let p = Params {
                        amount: 2.0,
                        smoothness: 37.0,
                        repeat: 7,
                        bias,
                        legacy: true,
                        scale,
                    };
                    let mut reference = vec![0; size];
                    unsafe {
                        blur_reference(
                            input.as_ptr(),
                            reference.as_mut_ptr(),
                            w,
                            h,
                            match depth {
                                Depth::U8 => 8,
                                Depth::U16 => 16,
                                Depth::F32 => 32,
                            },
                            true,
                            p.amount,
                            p.smoothness,
                            p.repeat,
                            p.bias,
                            p.scale,
                        );
                    }
                    for threads in [1, 4] {
                        let mut output = vec![0; size];
                        render(
                            &View::new(&input, layout).unwrap(),
                            &mut ViewMut::new(&mut output, layout).unwrap(),
                            &p,
                            threads,
                        )
                        .unwrap();
                        assert_eq!(
                            output, reference,
                            "uniform carry: {depth:?} case={case} {p:?} threads={threads}"
                        );
                    }
                    count += 1;
                }
            }
        }
    }
    assert_eq!(count, 144);
}

#[test]
fn byte_output_preserves_odd_padding_and_short_final_row() {
    for depth in [Depth::U8, Depth::U16, Depth::F32] {
        let layout = Layout {
            width: 7,
            height: 5,
            stride: 7 * depth.pixel_bytes() + 3,
            depth,
            origin: (0, 0),
        };
        let mut input = vec![0u8; layout.span().unwrap()];
        let mut view = ViewMut::new(&mut input, layout).unwrap();
        for y in 0..5 {
            for x in 0..7 {
                let p = match depth {
                    Depth::U8 => olm_core::Pixel::U8([255, 31, 17, 9]),
                    Depth::U16 => olm_core::Pixel::U16([32768, 32769, 65535, 1]),
                    Depth::F32 => olm_core::Pixel::F32([
                        f32::from_bits(0x80000000),
                        f32::from_bits(0x7fc01234),
                        1.,
                        -0.,
                    ]),
                };
                view.set(x, y, p).unwrap();
            }
        }
        let view = View::new(&input, layout).unwrap();
        let mut expected = vec![0xa5; input.len()];
        render(
            &view,
            &mut ViewMut::new(&mut expected, layout).unwrap(),
            &Params::default(),
            1,
        )
        .unwrap();
        for threads in [1, 4] {
            let mut actual = vec![0xa5; input.len()];
            super::algorithm::render_bytes(&view, &mut actual, layout, &Params::default(), threads)
                .unwrap();
            assert_eq!(actual, expected);
        }
    }
}

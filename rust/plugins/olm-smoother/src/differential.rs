use crate::{
    algorithm::{self, Params},
    generated, hot,
};
use olm_core::{Depth, Layout, Rect, View, ViewMut};

fn next(s: &mut u64) -> u32 {
    *s = s
        .wrapping_mul(6364136223846793005)
        .wrapping_add(1442695040888963407);
    (*s >> 32) as u32
}
fn check(a: [u16; 4], b: [u16; 4]) {
    unsafe {
        let mut a8 = a.map(|v| v as u8);
        let mut b8 = b.map(|v| v as u8);
        assert_eq!(
            hot::ColorCompare8(a8.as_mut_ptr(), b8.as_mut_ptr()),
            generated::ColorCompare8(a8.as_mut_ptr(), b8.as_mut_ptr()),
            "8: {a8:?} {b8:?}"
        );
        let mut a = a;
        let mut b = b;
        assert_eq!(
            hot::ColorCompare16(a.as_mut_ptr(), b.as_mut_ptr()),
            generated::ColorCompare16(a.as_mut_ptr(), b.as_mut_ptr()),
            "16: {a:?} {b:?}"
        );
    }
}
#[test]
fn comparison_exhaustive_channel_pairs_and_random_pixels() {
    // Exhaust all 8-bit channel pairs at representative alpha endpoints, and
    // all 16-bit channel values against endpoints, not just AE nominal white.
    for alpha in [0, 1, 128, 255] {
        for channel in 0..4 {
            for a in 0..256 {
                for b in 0..256 {
                    let mut pa = [alpha, 0, 0, 0];
                    let mut pb = pa;
                    pa[channel] = a;
                    pb[channel] = b;
                    check(pa, pb);
                }
            }
        }
    }
    for channel in 0..4 {
        for a in 0..=65535u16 {
            for b in [0, 1, 32768, 65535] {
                let mut pa = [32768, 0, 0, 0];
                let mut pb = pa;
                pa[channel] = a;
                pb[channel] = b;
                check(pa, pb);
            }
        }
    }
    let mut s = 0xace0123456789;
    for _ in 0..1_000_000 {
        check(
            std::array::from_fn(|_| next(&mut s) as u16),
            std::array::from_fn(|_| next(&mut s) as u16),
        );
    }
    unsafe {
        let mut a = [1u16; 4];
        assert_eq!(hot::ColorCompare16(a.as_mut_ptr(), std::ptr::null_mut()), 0);
        assert_eq!(
            hot::ColorCompare8(std::ptr::null_mut(), a.as_mut_ptr().cast()),
            0
        );
    }
}

#[test]
fn generated_frames_all_tolerances() {
    let mut seed = 0x510071828;
    for depth in [Depth::U8, Depth::U16] {
        for tolerance in 0..256 {
            for pattern in 0..4 {
                let (w, h) = [(1, 1), (3, 7), (17, 9), (31, 19)][pattern];
                let stride = w * depth.pixel_bytes() + 8;
                let layout = Layout {
                    width: w,
                    height: h,
                    stride,
                    depth,
                    origin: (7, -3),
                };
                let mut input = vec![0u8; layout.span().unwrap()];
                let palette: [[u16; 4]; 6] =
                    std::array::from_fn(|_| std::array::from_fn(|_| next(&mut seed) as u16));
                {
                    let mut view = ViewMut::new(&mut input, layout).unwrap();
                    for y in 0..h {
                        for x in 0..w {
                            let p = if pattern == 3 {
                                std::array::from_fn(|_| next(&mut seed) as u16)
                            } else {
                                palette[(x / 3 + y / 2) % 6]
                            };
                            view.set(
                                x,
                                y,
                                if depth == Depth::U8 {
                                    olm_core::Pixel::U8(p.map(|v| v as u8))
                                } else {
                                    olm_core::Pixel::U16(p)
                                },
                            )
                            .unwrap();
                        }
                    }
                }
                let extent = if pattern == 2 {
                    Rect::new(1, 1, w as i32 - 1, h as i32 - 1).unwrap()
                } else {
                    Rect::from_size(0, 0, w, h).unwrap()
                };
                let params = Params {
                    tolerance,
                    use_key: tolerance % 2 == 0,
                    key: palette[0].map(|v| v as u8),
                };
                let view = View::new(&input, layout).unwrap();
                let mut actual = vec![0xab; input.len()];
                let mut expected = actual.clone();
                algorithm::render_impl::<false>(
                    &view,
                    &mut ViewMut::new(&mut actual, layout).unwrap(),
                    params,
                    extent,
                )
                .unwrap();
                algorithm::render_impl::<true>(
                    &view,
                    &mut ViewMut::new(&mut expected, layout).unwrap(),
                    params,
                    extent,
                )
                .unwrap();
                assert_eq!(
                    actual, expected,
                    "{depth:?} tolerance={tolerance} pattern={pattern}"
                );
                let mut raw = vec![0xab; input.len()];
                algorithm::render_bytes(&input, layout, &mut raw, layout, params, extent).unwrap();
                assert_eq!(
                    raw, expected,
                    "byte rows {depth:?} tolerance={tolerance} pattern={pattern}"
                );
            }
        }
    }
}

#[test]
fn classifiers_exhaustive_three_color_neighborhoods() {
    use crate::support::*;
    let mut src8 = [[0u8; 4]; 9];
    let mut src16 = [[0u16; 4]; 9];
    let mut world = World::default();
    let mut state = RenderState {
        src_world: &mut world,
        ..Default::default()
    };
    let mut neighbors = [0u64; 10];
    for tolerance in [0, 6, 255] {
        state.tolerance_lo = tolerance;
        state.tolerance_hi = tolerance;
        for code in 0..3usize.pow(9) {
            let mut digits = code;
            for i in 0..9 {
                src8[i] = [[0, 0, 0, 0], [255, 255, 255, 255], [128, 63, 129, 250]][digits % 3];
                src16[i] = src8[i].map(|v| v as u16 * 128);
                digits /= 3;
            }
            for deep in [false, true] {
                for i in 0..9 {
                    neighbors[i] = if deep {
                        src16[i].as_mut_ptr() as u64
                    } else {
                        src8[i].as_mut_ptr() as u64
                    };
                }
                for d in [1, 3, 5, 7] {
                    unsafe {
                        let actual = if deep {
                            hot::Classifier16Exact(&mut state, 1, 1, neighbors.as_mut_ptr(), d)
                        } else {
                            hot::Classifier8(&mut state, 1, 1, neighbors.as_mut_ptr(), d)
                        };
                        let expected = if deep {
                            generated::Classifier16Exact(
                                &mut state,
                                1,
                                1,
                                neighbors.as_mut_ptr(),
                                d,
                            )
                        } else {
                            generated::Classifier8(&mut state, 1, 1, neighbors.as_mut_ptr(), d)
                        };
                        assert_eq!(
                            actual, expected,
                            "deep={deep} tol={tolerance} pattern={code} dir={d}"
                        );
                    }
                }
            }
        }
    }
}

#[test]
fn parallel_classification_matches_ordered_reference() {
    use crate::algorithm::{self, Params};
    use olm_core::{Depth, Layout, Rect, View, ViewMut};
    for depth in [Depth::U8, Depth::U16] {
        let (w, h) = (257, 193);
        let layout = Layout {
            width: w,
            height: h,
            stride: w * depth.pixel_bytes() + 3,
            depth,
            origin: (-7, 11),
        };
        for (case, tolerance) in [0, 6, 64, 255].into_iter().enumerate() {
            let mut input = vec![0x9a; layout.span().unwrap()];
            let mut seed = 0x12345678u32;
            for y in 0..h {
                for x in 0..w {
                    seed ^= seed << 13;
                    seed ^= seed >> 17;
                    seed ^= seed << 5;
                    let color = match case {
                        0 => [255, if x + y > 190 { 255 } else { 0 }, 0, 0],
                        1 => [[255, 255, 255, 255], [128, 63, 129, 250], [0, 32, 127, 255]]
                            [seed as usize % 3],
                        _ => seed.to_ne_bytes(),
                    };
                    let at = y * layout.stride + x * depth.pixel_bytes();
                    if depth == Depth::U8 {
                        input[at..at + 4].copy_from_slice(&color);
                    } else {
                        for (c, value) in color.into_iter().enumerate() {
                            input[at + 2 * c..at + 2 * c + 2]
                                .copy_from_slice(&(u16::from(value) * 128).to_ne_bytes());
                        }
                    }
                }
            }
            let extent = if case % 2 == 0 {
                Rect::from_size(0, 0, w, h).unwrap()
            } else {
                Rect::new(1, 2, w as i32 - 2, h as i32 - 1).unwrap()
            };
            let params = Params {
                tolerance,
                use_key: true,
                key: [255; 4],
            };
            let view = View::new(&input, layout).unwrap();
            let mut expected = vec![0xab; input.len()];
            algorithm::render_impl::<true>(
                &view,
                &mut ViewMut::new(&mut expected, layout).unwrap(),
                params,
                extent,
            )
            .unwrap();
            for workers in [1, 2, 3, usize::MAX] {
                let mut actual = vec![0xab; input.len()];
                algorithm::render_with_workers(
                    &view,
                    &mut ViewMut::new(&mut actual, layout).unwrap(),
                    params,
                    extent,
                    workers,
                )
                .unwrap();
                assert_eq!(
                    actual, expected,
                    "depth={depth:?} case={case} workers={workers}"
                );
            }
        }
    }
}

#[test]
fn color_blend5_all_neighbor_masks_and_random_full_range() {
    let mut seed = 0x8472931u32;
    for mask in 0..256usize {
        for iteration in 0..256 {
            let mut pixels: [[u16; 4]; 9] = std::array::from_fn(|_| {
                std::array::from_fn(|_| {
                    seed ^= seed << 13;
                    seed ^= seed >> 17;
                    seed ^= seed << 5;
                    seed as u16
                })
            });
            if iteration == 0 {
                for p in &mut pixels {
                    p[0] = 0;
                }
            }
            if iteration == 1 {
                pixels = [[0; 4]; 9];
            }
            if iteration == 2 {
                pixels = [[u16::MAX; 4]; 9];
            }
            let pixels8 = pixels.map(|p| p.map(|v| v as u8));
            for deep in [false, true] {
                let mut n = [0u64; 10];
                for (bit, i) in [0, 1, 2, 3, 5, 6, 7, 8].into_iter().enumerate() {
                    if mask & (1 << bit) != 0 {
                        n[i] = if deep {
                            pixels[i].as_ptr() as u64
                        } else {
                            pixels8[i].as_ptr() as u64
                        };
                    }
                }
                n[4] = if deep {
                    pixels[4].as_ptr() as u64
                } else {
                    pixels8[4].as_ptr() as u64
                };
                unsafe {
                    if deep {
                        let mut expected = [0u16; 4];
                        generated::ColorBlend16(n.as_mut_ptr(), expected.as_mut_ptr(), 5);
                        assert_eq!(
                            hot::color_blend5::<true>(n.as_ptr()),
                            expected,
                            "mask={mask}"
                        );
                    } else {
                        let mut expected = [0u8; 4];
                        generated::ColorBlend8(n.as_mut_ptr(), expected.as_mut_ptr(), 5);
                        assert_eq!(
                            hot::color_blend5::<false>(n.as_ptr()),
                            expected.map(u16::from),
                            "mask={mask}"
                        );
                    }
                }
            }
        }
    }
}

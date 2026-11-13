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

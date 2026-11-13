use crate::{
    algorithm::{render, Params},
    hot::*,
    kernels::*,
};
use olm_core::{Depth, Layout, Rect, View, ViewMut};
use std::ffi::c_void;
extern "C" {
    fn smoother_reference(
        i: *const c_void,
        o: *mut c_void,
        w: i32,
        h: i32,
        deep: i32,
        key_on: i32,
        key: *const u8,
        tol: i32,
        l: i32,
        t: i32,
        r: i32,
        b: i32,
    );
    fn smoother_compare(a: *const c_void, b: *const c_void, deep: i32) -> i32;
    fn smoother_alpha(
        a: *const c_void,
        aw: f32,
        b: *const c_void,
        bw: f32,
        o: *mut c_void,
        deep: i32,
    );
    fn smoother_step(
        i: *mut c_void,
        o: *mut c_void,
        w: i32,
        h: i32,
        deep: i32,
        tol: i32,
        x: i32,
        y: i32,
        dir: i32,
    ) -> i32;
    fn smoother_sub(
        i: *mut c_void,
        w: i32,
        h: i32,
        deep: i32,
        tol: i32,
        x: i32,
        y: i32,
        dir: i32,
        out: *mut u32,
    );
    fn smoother_walk(
        i: *mut c_void,
        w: i32,
        h: i32,
        deep: i32,
        tol: i32,
        x: i32,
        y: i32,
        d1: i32,
        d2: i32,
        ox: *mut i32,
        oy: *mut i32,
    ) -> u64;
}
fn next(s: &mut u64) -> u32 {
    *s = s
        .wrapping_mul(6364136223846793005)
        .wrapping_add(1442695040888963407);
    (*s >> 32) as u32
}
fn bytes(a: &[u64], n: usize) -> &[u8] {
    unsafe { std::slice::from_raw_parts(a.as_ptr().cast(), n) }
}
fn bytes_mut(a: &mut [u64], n: usize) -> &mut [u8] {
    unsafe { std::slice::from_raw_parts_mut(a.as_mut_ptr().cast(), n) }
}
fn frame(case: usize, deep: bool) -> (Vec<u64>, usize, usize, Params) {
    let (w, h): (usize, usize) = [(1, 1), (3, 7), (11, 7), (17, 13), (31, 19)][case % 5];
    let mut seed = 0x632be59bd9b4e019u64.wrapping_add(case as u64);
    let palette: [[u16; 4]; 6] = std::array::from_fn(|i| {
        std::array::from_fn(|c| {
            if c == 0 {
                [0, 1, 32, 128, 255, 255][i] * if deep { 128 } else { 1 }
            } else {
                (next(&mut seed) % if deep { 32769 } else { 256 }) as u16
            }
        })
    });
    let mut src = vec![0u64; (w * h * if deep { 8 } else { 4 }).div_ceil(8)];
    for y in 0..h {
        for x in 0..w {
            let index = match case % 5 {
                0 => (x + y * 2) % 6,
                1 => ((x * 2 + y) / 3) % 6,
                2 => (next(&mut seed) % 6) as usize,
                3 => usize::from(x + y > w / 2),
                _ => usize::from(x * x + y * y > w * w / 2),
            };
            let p = if case % 7 == 0 {
                std::array::from_fn(|_| (next(&mut seed) % if deep { 32769 } else { 256 }) as u16)
            } else {
                palette[index]
            };
            unsafe {
                if deep {
                    src.as_mut_ptr().cast::<[u16; 4]>().add(y * w + x).write(p);
                } else {
                    src.as_mut_ptr()
                        .cast::<[u8; 4]>()
                        .add(y * w + x)
                        .write(p.map(|v| v as u8));
                }
            }
        }
    }
    let key = [255, 255, 255, 255];
    // Explicit exact color-key hits, including alpha equality.
    if case % 3 == 0 {
        for i in (0..w * h).step_by(3) {
            unsafe {
                if deep {
                    src.as_mut_ptr()
                        .cast::<[u16; 4]>()
                        .add(i)
                        .write(key.map(|v| ((v as u32 * 32768 + 128) / 255) as u16));
                } else {
                    src.as_mut_ptr().cast::<[u8; 4]>().add(i).write(key);
                }
            }
        }
    }
    (
        src,
        w,
        h,
        Params {
            use_key: case % 2 == 0,
            key,
            tolerance: [0, 1, 6, 32, 128, 255][case % 6],
        },
    )
}
fn run_rust(src: &[u64], w: usize, h: usize, p: Params, deep: bool, rect: Rect) -> Vec<u64> {
    let n = w * h * if deep { 8 } else { 4 };
    let mut out = vec![0u64; n.div_ceil(8)];
    let l = Layout {
        width: w,
        height: h,
        stride: w * if deep { 8 } else { 4 },
        depth: if deep { Depth::U16 } else { Depth::U8 },
        origin: (0, 0),
    };
    render(
        &View::new(bytes(src, n), l).unwrap(),
        &mut ViewMut::new(bytes_mut(&mut out, n), l).unwrap(),
        p,
        rect,
    )
    .unwrap();
    out
}
#[test]
fn cpp_frames() {
    for deep in [false, true] {
        for case in 0..240 {
            let (src, w, h, p) = frame(case, deep);
            let n = w * h * if deep { 8 } else { 4 };
            let rect = if case % 4 == 0 && w > 3 {
                Rect::new(1, 1, w as i32 - 1, h as i32 - 1).unwrap()
            } else {
                Rect::from_size(0, 0, w, h).unwrap()
            };
            let actual = run_rust(&src, w, h, p, deep, rect);
            let mut expected = vec![0u64; n.div_ceil(8)];
            unsafe {
                smoother_reference(
                    src.as_ptr().cast(),
                    expected.as_mut_ptr().cast(),
                    w as i32,
                    h as i32,
                    deep as i32,
                    p.use_key as i32,
                    p.key.as_ptr(),
                    p.tolerance,
                    rect.left(),
                    rect.top(),
                    rect.right(),
                    rect.bottom(),
                );
            }
            if bytes(&actual, n) != bytes(&expected, n) {
                let pos = bytes(&actual, n)
                    .iter()
                    .zip(bytes(&expected, n))
                    .position(|(a, b)| a != b)
                    .unwrap();
                panic!(
                    "deep={deep} case={case} byte={pos}, Rust={} C++={}",
                    bytes(&actual, n)[pos],
                    bytes(&expected, n)[pos]
                );
            }
        }
    }
}
#[test]
fn cpp_pixel_helpers() {
    let mut s = 0x123456789abcdefu64;
    for deep in [false, true] {
        for _ in 0..8192 {
            let a: [u16; 4] = std::array::from_fn(|_| (next(&mut s) % 32769) as u16);
            let b: [u16; 4] = std::array::from_fn(|_| (next(&mut s) % 32769) as u16);
            let a8 = a.map(|v| v as u8);
            let b8 = b.map(|v| v as u8);
            let aw = (next(&mut s) % 2049) as f32 / 1024.0 - 0.5;
            let bw = (next(&mut s) % 2049) as f32 / 1024.0 - 0.5;
            unsafe {
                let ap = if deep {
                    a.as_ptr().cast()
                } else {
                    a8.as_ptr().cast()
                };
                let bp = if deep {
                    b.as_ptr().cast()
                } else {
                    b8.as_ptr().cast()
                };
                let actual = if deep {
                    ColorCompare16(ap as *mut u16, bp as *mut u16)
                } else {
                    ColorCompare8(ap as *mut u8, bp as *mut u8)
                };
                assert_eq!(actual, smoother_compare(ap, bp, deep as i32));
                let mut actual = 0u64;
                let mut expected = 0u64;
                if deep {
                    AlphaBlend16(
                        ap as *mut u16,
                        aw,
                        bp as *mut u16,
                        bw,
                        (&mut actual as *mut u64).cast(),
                    );
                } else {
                    AlphaBlend8(
                        ap as *mut u8,
                        aw,
                        bp as *mut u8,
                        bw,
                        (&mut actual as *mut u64).cast(),
                    );
                }
                smoother_alpha(
                    ap,
                    aw,
                    bp,
                    bw,
                    (&mut expected as *mut u64).cast(),
                    deep as i32,
                );
                assert_eq!(actual, expected);
            }
        }
    }
}
#[test]
fn scheduling_independence() {
    let work = |case| {
        let (src, w, h, p) = frame(case, true);
        run_rust(&src, w, h, p, true, Rect::from_size(0, 0, w, h).unwrap())
    };
    let expected: Vec<_> = (0..32).map(work).collect();
    for threads in [1, 2, 4] {
        std::thread::scope(|scope| {
            let handles: Vec<_> = (0..threads)
                .map(|lane| {
                    scope.spawn(move || {
                        (lane..32)
                            .step_by(threads)
                            .map(|i| (i, work(i)))
                            .collect::<Vec<_>>()
                    })
                })
                .collect();
            for handle in handles {
                for (i, v) in handle.join().unwrap() {
                    assert_eq!(expected[i], v);
                }
            }
        });
    }
}
#[test]
fn rejection_and_padded_rows() {
    let p = Params::default();
    let l = Layout {
        width: 3,
        height: 3,
        stride: 25,
        depth: Depth::U16,
        origin: (19, -4),
    };
    let input = vec![0u8; l.span().unwrap()];
    let mut output = vec![0xabu8; l.span().unwrap()];
    render(
        &View::new(&input, l).unwrap(),
        &mut ViewMut::new(&mut output, l).unwrap(),
        p,
        Rect::new(0, 0, 3, 3).unwrap(),
    )
    .unwrap();
    assert_eq!(output[24], 0xab);
    assert_eq!(output[49], 0xab);
    let mut output = vec![0xabu8; l.span().unwrap()];
    assert!(render(
        &View::new(&input, l).unwrap(),
        &mut ViewMut::new(&mut output, l).unwrap(),
        Params {
            tolerance: 256,
            ..p
        },
        Rect::new(0, 0, 3, 3).unwrap()
    )
    .is_err());
    assert!(output.iter().all(|&v| v == 0xab));
}
#[test]
fn cpp_steps() {
    use crate::support::*;
    for deep in [false, true] {
        for case in 0..40 {
            let (mut src, w, h, p) = frame(case, deep);
            let mut actual = src.clone();
            let mut expected = src.clone();
            let nbytes = w * h * if deep { 8 } else { 4 };
            let mut sw = World {
                data: src.as_mut_ptr().cast(),
                width: w as i32,
                height: h as i32,
                rowbytes: (w * if deep { 8 } else { 4 }) as i32,
                ..Default::default()
            };
            let mut dw = World {
                data: actual.as_mut_ptr().cast(),
                ..sw
            };
            let mut s = RenderState {
                src_world: &mut sw,
                dst_world: &mut dw,
                tolerance: p.tolerance,
                tolerance_lo: p.tolerance,
                tolerance_hi: p.tolerance,
                threshold: p.tolerance,
                ..Default::default()
            };
            unsafe {
                for y in 0..h {
                    for x in 0..w {
                        for dir in [5, 3, 1, 7] {
                            let mut n = [0u64; 10];
                            let c = if deep {
                                NeighborExtract16(x as i32, y as i32, &mut s, n.as_mut_ptr());
                                Classifier16Exact(&mut s, x as u32, y as u32, n.as_mut_ptr(), dir)
                            } else {
                                NeighborExtract8(x as i32, y as i32, &mut s, n.as_mut_ptr());
                                Classifier8(&mut s, x as u32, y as u32, n.as_mut_ptr(), dir)
                            };
                            let ec = smoother_step(
                                src.as_mut_ptr().cast(),
                                expected.as_mut_ptr().cast(),
                                w as i32,
                                h as i32,
                                deep as i32,
                                p.tolerance,
                                x as i32,
                                y as i32,
                                dir as i32,
                            );
                            assert_eq!(
                                c, ec,
                                "classifier deep={deep} case={case} xy={x},{y} dir={dir}"
                            );
                            if c == 1 {
                                let mut a = [0u32; 9];
                                let mut b = [0u32; 9];
                                let mut aa = 0;
                                let mut ab = 0;
                                let ap = a.as_mut_ptr();
                                if deep {
                                    SubHandler16Exact(
                                        &mut s,
                                        n.as_mut_ptr(),
                                        x as u32,
                                        y as u32,
                                        dir,
                                        ap,
                                        &mut aa,
                                        &mut ab,
                                        ap.add(3),
                                        ap.add(4),
                                        ap.add(5),
                                        ap.add(6),
                                        ap.add(7),
                                        ap.add(8),
                                    );
                                } else {
                                    SubHandler8Exact(
                                        &mut s,
                                        n.as_mut_ptr(),
                                        x as u32,
                                        y as u32,
                                        dir,
                                        ap,
                                        &mut aa,
                                        &mut ab,
                                        ap.add(3),
                                        ap.add(4),
                                        ap.add(5),
                                        ap.add(6),
                                        ap.add(7),
                                        ap.add(8),
                                    );
                                }
                                a[1] = aa as u32;
                                a[2] = ab as u32;
                                smoother_sub(
                                    src.as_mut_ptr().cast(),
                                    w as i32,
                                    h as i32,
                                    deep as i32,
                                    p.tolerance,
                                    x as i32,
                                    y as i32,
                                    dir as i32,
                                    b.as_mut_ptr(),
                                );
                                assert_eq!(
                                    a, b,
                                    "subhandler deep={deep} case={case} xy={x},{y} dir={dir}"
                                );
                            }
                            if deep {
                                DispatchDirection16(
                                    &mut s,
                                    n.as_mut_ptr(),
                                    x as u32,
                                    y as u32,
                                    dir,
                                    c,
                                );
                            } else {
                                DispatchDirection8(
                                    &mut s,
                                    n.as_mut_ptr(),
                                    x as u32,
                                    y as u32,
                                    dir,
                                    c,
                                );
                            }
                            if bytes(&actual, nbytes) != bytes(&expected, nbytes) {
                                let at = bytes(&actual, nbytes)
                                    .iter()
                                    .zip(bytes(&expected, nbytes))
                                    .position(|(a, b)| a != b)
                                    .unwrap();
                                panic!("dispatch deep={deep} case={case} xy={x},{y} dir={dir} type={c} byte={at} actual={} expected={}",bytes(&actual,nbytes)[at],bytes(&expected,nbytes)[at]);
                            }
                        }
                    }
                }
            }
        }
    }
}
#[test]
fn cpp_walkers() {
    use crate::support::*;
    for deep in [false, true] {
        for case in 0..10 {
            let (mut src, w, h, p) = frame(case, deep);
            let mut sw = World {
                data: src.as_mut_ptr().cast(),
                width: w as i32,
                height: h as i32,
                rowbytes: (w * if deep { 8 } else { 4 }) as i32,
                ..Default::default()
            };
            let mut s = RenderState {
                src_world: &mut sw,
                tolerance: p.tolerance,
                tolerance_lo: p.tolerance,
                tolerance_hi: p.tolerance,
                threshold: p.tolerance,
                ..Default::default()
            };
            for y in 0..h {
                for x in 0..w {
                    for d1 in [1, 3, 5, 7] {
                        for d2 in [1, 3, 5, 7] {
                            let (mut ax, mut ay, mut bx, mut by) = (0, 0, 0, 0);
                            unsafe {
                                let b = smoother_walk(
                                    src.as_mut_ptr().cast(),
                                    w as i32,
                                    h as i32,
                                    deep as i32,
                                    p.tolerance,
                                    x as i32,
                                    y as i32,
                                    d1,
                                    d2,
                                    &mut bx,
                                    &mut by,
                                );
                                let a = if deep {
                                    EdgeWalker16Exact(
                                        &mut s,
                                        x as i32,
                                        y as i32,
                                        d1,
                                        d2 as u32,
                                        &mut ax,
                                        &mut ay,
                                        p.tolerance,
                                    ) as u64
                                } else {
                                    EdgeWalker8Exact(
                                        &mut s,
                                        x as i32,
                                        y as i32,
                                        d1,
                                        d2 as u32,
                                        &mut ax,
                                        &mut ay,
                                        p.tolerance,
                                    ) as u64
                                };
                                assert_eq!(
                                    (a, ax, ay),
                                    (b, bx, by),
                                    "walk deep={deep} case={case} xy={x},{y} dirs={d1},{d2}"
                                );
                            }
                        }
                    }
                }
            }
        }
    }
}

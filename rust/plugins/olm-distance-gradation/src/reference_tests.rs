use crate::{
    algorithm::{compose, Params},
    bilateral, field, filters,
};
extern "C" {
    fn dg_field(
        m: *const u8,
        w: i32,
        h: i32,
        rw: i32,
        rh: i32,
        threshold: f32,
        constant: i32,
        maximum: f32,
        out: *mut f32,
    );
    fn dg_filter(m: *mut f32, w: i32, h: i32, mode: i32, rx: i32, ry: i32, scalar: i32);
    fn dg_exp(x: f32, vector: i32) -> f32;
    fn dg_compose(
        src: *const f32,
        aux: f32,
        x: f32,
        controls: *const i32,
        colors: *const f32,
        power: f32,
        out: *mut f32,
    );
}
fn next(s: &mut u64) -> u32 {
    *s = s.wrapping_mul(6364136223846793005).wrapping_add(1);
    (*s >> 32) as u32
}
#[test]
fn native_fma_exp() {
    for pair in include_bytes!("../tests/native-ipp-exp.bin").chunks_exact(8) {
        let x = f32::from_le_bytes(pair[..4].try_into().unwrap());
        let expected = u32::from_le_bytes(pair[4..].try_into().unwrap());
        assert_eq!(bilateral::fma_exp(x).to_bits(), expected, "native exp {x}");
    }
}
#[test]
fn upstream_recorded_fields() {
    // Native 2025 RVA 0x11750f0 inputs/outputs captured during Smart32.
    // Includes long outside distances that exercise native IPP RSQRT/FMA.
    let data = include_bytes!("../tests/upstream-field.bin");
    let mut at = 0;
    while at < data.len() {
        let word = |i| u32::from_le_bytes(data[i..i + 4].try_into().unwrap());
        let (w, h, rw, rh) = (
            word(at) as usize,
            word(at + 4) as usize,
            word(at + 8) as usize,
            word(at + 12) as usize,
        );
        let threshold = word(at + 16) as f32;
        let constant = word(at + 20) == 1;
        let max = f32::from_bits(word(at + 24));
        at += 28;
        let actual = field::normalized(
            &data[at..at + w * h],
            w,
            h,
            rw,
            rh,
            threshold,
            constant,
            max,
        );
        at += w * h;
        for (v, bytes) in actual.iter().zip(data[at..at + w * h * 4].chunks_exact(4)) {
            assert_eq!(v.to_bits(), u32::from_le_bytes(bytes.try_into().unwrap()));
        }
        at += w * h * 4;
    }
}
#[test]
fn upstream_padding_geometry() {
    for factor in [1, 2, 4] {
        let mut p = Params {
            use_padding: true,
            scale_x: (1, factor),
            scale_y: (1, factor),
            ..Default::default()
        };
        assert_eq!(
            crate::algorithm::padding(&p).unwrap(),
            (factor as usize, 1, 1)
        );
        p.in_out = 2;
        p.outside = 7;
        assert_eq!(
            crate::algorithm::padding(&p).unwrap(),
            (7, 7 / factor as usize, 7 / factor as usize)
        );
        p.use_padding = false;
        assert_eq!(crate::algorithm::padding(&p).unwrap(), (0, 0, 0));
    }
}
#[test]
fn upstream_both_uses_masked_copy() {
    use olm_core::{Depth, Layout, View, ViewMut};
    let data = include_bytes!("../tests/upstream-masked-copy.bin");
    let word = |i| u32::from_le_bytes(data[i..i + 4].try_into().unwrap()) as usize;
    let (w, h, ow, oh) = (word(0), word(4), word(8), word(12));
    let layout = |width, height| Layout {
        width,
        height,
        stride: width * 4,
        depth: Depth::U8,
        origin: (0, 0),
    };
    let input = View::new(&data[16..16 + w * h * 4], layout(w, h)).unwrap();
    let mut bytes = vec![0; ow * oh * 4];
    let mut output = ViewMut::new(&mut bytes, layout(ow, oh)).unwrap();
    let p = Params {
        in_out: 3,
        inside: 33,
        outside: 115,
        use_bg: true,
        grad: [180., 149., 240., 226.].map(|v| v / 255.),
        bg: [9., 94., 171., 7.].map(|v| v / 255.),
        interpolation: 4,
        blur_mode: 5,
        blur_size: 12,
        use_padding: true,
        scale_x: (1, 2),
        scale_y: (1, 2),
        ..Default::default()
    };
    crate::algorithm::render(&input, &mut output, &p).unwrap();
    assert_eq!(bytes, &data[16 + w * h * 4..]);
}
#[test]
fn native_fma_filters() {
    let data = include_bytes!("../tests/native-ipp-fma.bin");
    let mut at = 0;
    let mut failures = vec![];
    while at < data.len() {
        let word = |i| u32::from_le_bytes(data[i..i + 4].try_into().unwrap()) as usize;
        let (w, h, r, max) = (word(at), word(at + 4), word(at + 8), word(at + 12));
        at += 16;
        let mut a: Vec<_> = data[at..at + w * h * 4]
            .chunks_exact(4)
            .map(|b| f32::from_le_bytes(b.try_into().unwrap()))
            .collect();
        at += w * h * 4;
        let expected = &data[at..at + w * h * 4];
        at += w * h * 4;
        bilateral::blur_mode(&mut a, w, h, r, false, true);
        let count = a
            .iter()
            .zip(expected.chunks_exact(4))
            .filter(|(a, b)| a.to_bits() != u32::from_le_bytes((*b).try_into().unwrap()))
            .count();
        if count != 0 {
            failures.push(format!("{w}x{h} r{r} max{max}: {count}"));
        }
    }
    assert!(failures.is_empty(), "{}", failures.join("\n"));
}
fn same(a: &[f32], b: &[f32], label: &str) {
    for (i, (a, b)) in a.iter().zip(b).enumerate() {
        assert_eq!(a.to_bits(), b.to_bits(), "{label} sample {i}: {a} vs {b}");
    }
}
#[test]
fn cpp_fields() {
    let mut seed = 123u64;
    for (w, h) in [(1, 1), (3, 7), (11, 7), (17, 11), (31, 19), (97, 61)] {
        for factor in [1, 2, 4] {
            for constant in [false, true] {
                for threshold in [0., 1., 4., 128., 1000.] {
                    for maximum in [1., 255.] {
                        let m: Vec<_> = (0..w * h)
                            .map(|_| (next(&mut seed) % 7 != 0) as u8)
                            .collect();
                        let actual = field::normalized_legacy(
                            &m,
                            w,
                            h,
                            w * factor,
                            h * factor,
                            threshold,
                            constant,
                            maximum,
                        );
                        let mut expected = vec![0.; w * h];
                        unsafe {
                            dg_field(
                                m.as_ptr(),
                                w as i32,
                                h as i32,
                                (w * factor) as i32,
                                (h * factor) as i32,
                                threshold,
                                constant as i32,
                                maximum,
                                expected.as_mut_ptr(),
                            );
                        }
                        same(
                            &actual,
                            &expected,
                            &format!(
                                "field {w}x{h}/{factor} t{threshold} c{constant} max{maximum}"
                            ),
                        );
                    }
                }
            }
        }
    }
}
#[test]
fn cpp_filters() {
    let mut seed = 824u64;
    for (w, h) in [(1, 1), (1, 7), (3, 7), (11, 7), (17, 11), (31, 19)] {
        for mode in 2..=5 {
            for r in [1, 2, 3, 4, 7, 12, 32] {
                for max in [1., 255., 32768.] {
                    let a: Vec<_> = (0..w * h)
                        .map(|_| (next(&mut seed) % 1001) as f32 / 1000. * max)
                        .collect();
                    let mut expected = a.clone();
                    let mut actual = a;
                    unsafe {
                        dg_filter(expected.as_mut_ptr(), w as i32, h as i32, mode, r, r, 0);
                    }
                    match mode {
                        2 => filters::box_blur(
                            &mut actual,
                            w,
                            h,
                            (2 * r + 1) as usize,
                            (2 * r + 1) as usize,
                        ),
                        3 => filters::gaussian(
                            &mut actual,
                            w,
                            h,
                            (2 * r + 1) as usize,
                            (2 * r + 1) as usize,
                        ),
                        4 => filters::median(&mut actual, w, h, (2 * r + 1) as usize),
                        _ => bilateral::blur(&mut actual, w, h, r as usize, false),
                    }
                    same(
                        &actual,
                        &expected,
                        &format!("filter {w}x{h} mode {mode} r{r} max{max}"),
                    );
                }
            }
        }
    }
}
#[test]
fn cpp_exponentials() {
    for i in 0..100001 {
        let x = -25. * i as f32 / 100001.;
        for vector in [0, 1] {
            let actual = if vector == 0 {
                bilateral::scalar_exp(x)
            } else {
                bilateral::vector_exp(x)
            };
            let expected = unsafe { dg_exp(x, vector) };
            assert_eq!(
                actual.to_bits(),
                expected.to_bits(),
                "exp {x} vector{vector}"
            );
        }
    }
}
#[test]
fn cpp_composition() {
    let mut seed = 598u64;
    for depth in [4, 8, 16] {
        for _ in 0..10000 {
            let mut f = || next(&mut seed) as f32 / u32::MAX as f32;
            let src = [f(), f(), f(), f()];
            let aux = f();
            let x = f();
            let grad = [1., f(), f(), f()];
            let bg = [1., f(), f(), f()];
            let power = 0.01 + f() * 4.99;
            let c = [
                depth,
                (next(&mut seed) & 1) as i32,
                (next(&mut seed) % 3 + 1) as i32,
                (next(&mut seed) % 2 + 1) as i32,
                (next(&mut seed) & 1) as i32,
                (next(&mut seed) % 4 + 1) as i32,
                2,
                (next(&mut seed) & 1) as i32,
                0,
            ];
            let p = Params {
                invert: c[1] != 0,
                in_out: c[2],
                render_mode: c[3],
                use_bg: c[4] != 0,
                interpolation: c[5],
                blur_mode: c[6],
                blur_size: c[7] as u32,
                grad,
                bg,
                power,
                ..Params::default()
            };
            let actual = compose(src, aux, x, &p, c[7] != 0, false);
            let mut expected = [0.; 4];
            let colors: Vec<_> = grad.into_iter().chain(bg).collect();
            unsafe {
                dg_compose(
                    src.as_ptr(),
                    aux,
                    x,
                    c.as_ptr(),
                    colors.as_ptr(),
                    power,
                    expected.as_mut_ptr(),
                );
            }
            same(&actual, &expected, "compose");
        }
    }
}
#[test]
fn concurrent_determinism() {
    let m: Vec<_> = (0..97 * 61).map(|i| (i % 13 != 0) as u8).collect();
    let expected = field::normalized(&m, 97, 61, 194, 122, 128., false, 1.);
    std::thread::scope(|s| {
        for _ in 0..4 {
            let m = &m;
            let expected = &expected;
            s.spawn(move || {
                for _ in 0..8 {
                    same(
                        &field::normalized(m, 97, 61, 194, 122, 128., false, 1.),
                        expected,
                        "concurrent field",
                    );
                }
            });
        }
    });
}

#[test]
fn native_gaussian() {
    let data = include_bytes!("../tests/native-gaussian.bin");
    let mut at = 0;
    let mut failures = vec![];
    while at < data.len() {
        let word = |i| u32::from_le_bytes(data[i..i + 4].try_into().unwrap()) as usize;
        let (w, h, n, ny) = (word(at), word(at + 4), word(at + 8), word(at + 12));
        at += 16;
        let mut a: Vec<_> = data[at..at + w * h * 4]
            .chunks_exact(4)
            .map(|b| f32::from_le_bytes(b.try_into().unwrap()))
            .collect();
        at += w * h * 4;
        let expected = &data[at..at + w * h * 4];
        at += w * h * 4;
        filters::gaussian_native(&mut a, w, h, n, ny);
        let count = a
            .iter()
            .zip(expected.chunks_exact(4))
            .filter(|(a, b)| a.to_bits() != u32::from_le_bytes((*b).try_into().unwrap()))
            .count();
        if count != 0 {
            failures.push(format!("{w}x{h} n{n}x{ny}: {count}"));
        }
    }
    assert!(failures.is_empty(), "{}", failures.join("\n"));
}
#[test]
fn native_gaussian_kernels() {
    let data = include_bytes!("../tests/native-gaussian-kernels.bin");
    let mut at = 0;
    let mut failures = vec![];
    while at < data.len() {
        let n = u32::from_le_bytes(data[at..at + 4].try_into().unwrap()) as usize;
        at += 4;
        let expected = &data[at..at + n * 8];
        at += n * 8;
        let a = filters::kernel(n);
        let count = a
            .iter()
            .zip(expected.chunks_exact(8))
            .filter(|(a, b)| {
                a.to_bits() != (f64::from_le_bytes((*b).try_into().unwrap()) as f32).to_bits()
            })
            .count();
        if count != 0 {
            failures.push(format!("kernel {n}: {count}"));
        }
    }
    assert!(failures.is_empty(), "{}", failures.join("\n"));
}

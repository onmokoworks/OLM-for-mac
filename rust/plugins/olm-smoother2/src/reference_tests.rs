use crate::{
    frame, gamma, lut,
    types::{Pixel, Vertex},
};
extern "C" {
    fn sm2_ref_sha(data: *const u8, n: usize, out: *mut u8);
    fn sm2_ref_render(
        pixels: *mut Pixel,
        w: i32,
        h: i32,
        version: i32,
        smooth: i32,
        extra: i32,
        range: i32,
        mode: i32,
        gamma: f32,
        palette: *const Pixel,
        colors: i32,
        key_mode: i32,
        keep: i32,
        out: *mut Pixel,
    );
    fn sm2_ref_polygon(
        pixels: *mut Pixel,
        classes: *const u8,
        w: i32,
        h: i32,
        x: i32,
        y: i32,
        smooth: i32,
        extra: i32,
        out: *mut Vertex,
    ) -> i32;
    fn sm2_ref_leaf(
        id: i32,
        pixels: *mut Pixel,
        classes: *const u8,
        w: i32,
        h: i32,
        x: i32,
        y: i32,
        smooth: f32,
        extra: f32,
        desc: *const i32,
        scale: f32,
        out: *mut Vertex,
        count: *mut i32,
    ) -> i32;
    fn sm2_ref_class_plane(input: *const Pixel, w: i32, h: i32, range: i32, out: *mut u8);
    fn sm2_ref_weights(span: i32, offset: i32, key: i32, scalar: i32, out: *mut f32);
    fn sm2_ref_line(p2: *const f32, p3: *const f32, offset: i32, scalar: i32, out: *mut f32);
    fn sm2_ref_corners(
        pixels: *mut Pixel,
        w: i32,
        h: i32,
        stride: i32,
        x: i32,
        y: i32,
        smooth: f32,
        mask: i32,
        normalize: i32,
        out: *mut Vertex,
    ) -> i32;
    fn sm2_ref_curve(t: f32, index: i32) -> f32;
    fn sm2_ref_encode_literal(v: f64) -> f64;
    fn sm2_ref_adaptive(
        center: *const Pixel,
        samples: *const Vertex,
        n: i32,
        version: i32,
        mode: i32,
        value: f32,
        palette: *const Pixel,
        colors: i32,
        result: *mut f32,
    ) -> i32;
    fn sm2_ref_gamma(
        op: i32,
        center: *mut Pixel,
        samples: *mut Vertex,
        n: i32,
        enable: i32,
        value: f32,
    );
    fn sm2_ref_classify(bits: i32) -> i32;
    fn sm2_ref_trapezoid(width: f32, position: i32, edge: f32) -> f32;
    fn sm2_ref_scan(
        kind: i32,
        bytes: *const u8,
        w: i32,
        h: i32,
        stride: i32,
        x: i32,
        y: i32,
        out: *mut i32,
    );
    fn sm2_ref_load(depth: i32, value: u32, out: *mut Pixel);
    fn sm2_ref_pack(depth: i32, v: f32) -> u32;
    fn sm2_ref_transfer(op: i32, v: f32) -> f32;
    fn sm2_ref_frame(op: i32, pixels: *mut Pixel, n: i32, keys: *const Pixel, count: i32);
}

#[test]
fn source_identity_sha256() {
    let mut rng = Rng(0x51a256);
    for n in (0..257).chain([1024, 8192, 65536]) {
        let input: Vec<u8> = (0..n).map(|_| rng.word() as u8).collect();
        let mut expected = [0; 32];
        unsafe {
            sm2_ref_sha(input.as_ptr(), n, expected.as_mut_ptr());
        }
        assert_eq!(crate::sha256::digest(&input), expected, "length={n}");
    }
}

#[test]
fn stage7_complete_polygons() {
    for seed in [0x7a11, 0x20261114] {
        let mut rng = Rng(seed);
        for (w, h) in [(1, 1), (3, 7), (11, 9), (31, 19)] {
            let mut pixels: Vec<_> = (0..w * h).map(|_| rng.pixel()).collect();
            for case in 0..256 {
                let mut classes: Vec<u8> = (0..w * h * 4).map(|_| (rng.word() & 1) as u8).collect();
                // All 256 index bit patterns at an interior pixel, with random surrounding runs.
                if w > 3 {
                    let x = w / 2;
                    let y = h / 2;
                    for (bit, dx, dy, ch) in [
                        (3, 0, 0, 0),
                        (1, 0, 0, 1),
                        (0, 0, 0, 2),
                        (2, 0, 0, 3),
                        (4, 1, 0, 0),
                        (5, -1, 1, 3),
                        (6, 0, 1, 1),
                        (7, 1, 1, 2),
                    ] {
                        classes[((y + dy) * w * 4 + (x + dx) * 4 + ch) as usize] =
                            if case & (1 << bit) == 0 { 1 } else { 0 };
                    }
                }
                for (x, y) in [
                    (0, 0),
                    (w - 1, 0),
                    (0, h - 1),
                    (w - 1, h - 1),
                    (w / 2, h / 2),
                ] {
                    let smooth = [1, 25, 50, 100][case % 4];
                    let extra = [0, 25, 100][case % 3];
                    let mut natural = vec![0u8; (w * h * 4) as usize];
                    unsafe {
                        sm2_ref_class_plane(
                            pixels.as_ptr(),
                            w,
                            h,
                            (case % 101) as i32,
                            natural.as_mut_ptr(),
                        );
                    }
                    let classes = if w > 3 && x == w / 2 && y == h / 2 {
                        &classes
                    } else {
                        &natural
                    };
                    let mut expected = [Vertex::default(); 12];
                    let n = unsafe {
                        sm2_ref_polygon(
                            pixels.as_mut_ptr(),
                            classes.as_ptr(),
                            w,
                            h,
                            x,
                            y,
                            smooth,
                            extra,
                            expected.as_mut_ptr(),
                        )
                    };
                    let mut p = crate::geometry::State::new(
                        &pixels,
                        classes,
                        w,
                        h,
                        x,
                        y,
                        smooth as f32 / 100.0,
                        extra as f32 / 100.0,
                    )
                    .unwrap();
                    crate::geometry::build(&mut p);
                    let actual = p.vertices().unwrap();
                    assert_eq!(
                        actual.len(),
                        n as usize,
                        "seed={seed:x} size={w}x{h} case={case} xy={x},{y}"
                    );
                    for (i, (a, b)) in actual.iter().zip(expected).enumerate() {
                        same(a.pixel, b.pixel);
                        assert_eq!(
                            a.weight.to_bits(),
                            b.weight.to_bits(),
                            "seed={seed:x} size={w}x{h} case={case} xy={x},{y} vertex={i}"
                        );
                    }
                }
            }
        }
    }
}

#[test]
fn stage8_full_render() {
    use crate::algorithm::{render, Params};
    use gamma::GammaMode;
    for seed in [0x8f00d, 0x20261115] {
        let mut rng = Rng(seed);
        for (w, h) in [(1, 1), (3, 7), (11, 9), (31, 19)] {
            for case in 0..144 {
                let palette: Vec<_> = (0..5).map(|_| rng.pixel()).collect();
                let input: Vec<_> = (0..w * h)
                    .map(|i| {
                        let mut v = if case % 3 == 0 {
                            palette[(i % 5) as usize]
                        } else if case % 3 == 1 {
                            palette[((i / w + i % w) / 3 % 5) as usize]
                        } else {
                            rng.pixel()
                        };
                        if case % 4 == 0 {
                            v.a = 1.0;
                        }
                        if case % 4 == 1 && i % 3 == 0 {
                            v.a = 0.0;
                        }
                        v
                    })
                    .collect();
                let key_mode = case % 3;
                let colors = case % 6;
                let p = Params {
                    version: 1 + case % 2,
                    smoothness: [0, 1, 50, 100][(case / 2 % 4) as usize],
                    extra: [0, 25, 100][(case / 8 % 3) as usize],
                    range: [0, 1, 2, 50, 100][(case / 3 % 5) as usize],
                    gamma_mode: [GammaMode::None, GammaMode::Colors, GammaMode::All]
                        [(case / 4 % 3) as usize],
                    gamma: [0.0, 0.5, 1.0, 2.2, 2.4, 5.0][(case / 6 % 6) as usize],
                    gamma_colors: palette[..colors as usize].to_vec(),
                    key: if key_mode == 0 {
                        None
                    } else {
                        Some((palette[0], key_mode == 2))
                    },
                    keep_premultiplied: case % 2 == 0,
                };
                let mut source = input.clone();
                let mut expected = vec![Pixel::default(); input.len()];
                unsafe {
                    sm2_ref_render(
                        source.as_mut_ptr(),
                        w,
                        h,
                        p.version,
                        p.smoothness,
                        p.extra,
                        p.range,
                        p.gamma_mode as i32,
                        p.gamma,
                        palette.as_ptr(),
                        colors,
                        key_mode,
                        p.keep_premultiplied as i32,
                        expected.as_mut_ptr(),
                    );
                }
                for threads in [1, 3, 7] {
                    let actual = render(
                        &input,
                        w as usize,
                        h as usize,
                        &p,
                        threads,
                        &mut olm_core::Budget::new(input.len() * 36),
                    )
                    .unwrap();
                    for (i, (a, b)) in actual.into_iter().zip(&expected).enumerate() {
                        assert_eq!(
                            a.words(),
                            b.words(),
                            "seed={seed:x} size={w}x{h} case={case} threads={threads} pixel={i}"
                        );
                    }
                }
            }
        }
    }
}

#[test]
fn stage6_directional_leaves() {
    let mut calls = 0;
    for seed in [0x61eaf, 0x20261113] {
        let mut rng = Rng(seed);
        for case in 0..512 {
            let (w, h) = (11, 9);
            let mut pixels: Vec<_> = (0..w * h).map(|_| rng.pixel()).collect();
            let mut classes = vec![0; w * h * 4];
            for (i, b) in classes.iter_mut().enumerate() {
                *b = if case < 16 {
                    if case & (1 << (i % 4)) != 0 {
                        255
                    } else {
                        0
                    }
                } else if rng.word() % 3 == 0 {
                    255
                } else {
                    0
                };
            }
            let desc = [
                2,
                2,
                (rng.word() % 10) as i32,
                8,
                6,
                (rng.word() % 10) as i32,
            ];
            let smooth = [0.0, 0.01, 0.5, 1.0][case % 4];
            let extra = [0.0, 0.25, 1.0][case % 3];
            let scale = [0.0, 0.5, 1.0][case % 3];
            for id in 0..32 {
                let mut expected = [Vertex::default(); 12];
                let mut count = 0;
                let expected_flag = unsafe {
                    sm2_ref_leaf(
                        id,
                        pixels.as_mut_ptr(),
                        classes.as_ptr(),
                        w as i32,
                        h as i32,
                        5,
                        4,
                        smooth,
                        extra,
                        desc.as_ptr(),
                        scale,
                        expected.as_mut_ptr(),
                        &mut count,
                    )
                };
                let mut state = crate::geometry::State::new(
                    &pixels, &classes, w as i32, h as i32, 5, 4, smooth, extra,
                )
                .unwrap();
                let flag = crate::geometry::test_leaf(id as usize, &desc, scale, &mut state);
                assert_eq!(
                    flag as i32, expected_flag,
                    "seed={seed} case={case} leaf={id}"
                );
                let actual = state.vertices().unwrap();
                assert_eq!(actual.len(), count as usize);
                for (a, b) in actual.iter().zip(expected.iter()) {
                    same(a.pixel, b.pixel);
                    assert_eq!(
                        a.weight.to_bits(),
                        b.weight.to_bits(),
                        "seed={seed} case={case} leaf={id}"
                    );
                }
                calls += 1;
            }
        }
    }
    assert_eq!(calls, 32768);
}

#[test]
fn stage5_class_plane() {
    let mut rng = Rng(0x5162c1a55);
    let mut frames = 0;
    for (w, h) in [(1, 1), (1, 7), (7, 1), (3, 7), (11, 9), (31, 19)] {
        for case in 0..48 {
            let mut input: Vec<_> = (0..w * h).map(|_| rng.pixel()).collect();
            for (i, p) in input.iter_mut().enumerate() {
                if case < 8 {
                    *p = frame::load8([
                        if i % 3 == 0 { 0 } else { 255 },
                        (i % 5 * 51) as u8,
                        0,
                        255,
                    ]);
                }
                if case % 8 == 0 {
                    p.r = f32::from_bits(0x7fc12345);
                }
                if case % 8 == 1 {
                    p.g = f32::INFINITY;
                }
            }
            for range in [0, 1, 2, 3, 50, 100] {
                let mut expected = vec![0u8; w * h * 4];
                unsafe {
                    sm2_ref_class_plane(
                        input.as_ptr(),
                        w as i32,
                        h as i32,
                        range,
                        expected.as_mut_ptr(),
                    );
                }
                for threads in [1, 3, 7] {
                    let mut budget = olm_core::Budget::new(w * h * 4);
                    let actual =
                        crate::class_plane::build(&input, w, h, range, threads, &mut budget)
                            .unwrap();
                    assert_eq!(
                        actual.into_iter().flatten().collect::<Vec<_>>(),
                        expected,
                        "size={w}x{h} case={case} range={range}"
                    );
                    assert_eq!(budget.used(), w * h * 4);
                }
                frames += 1;
            }
        }
    }
    assert_eq!(frames, 1728);
    assert!(crate::class_plane::build(
        &[Pixel::default(); 4],
        2,
        2,
        1,
        1,
        &mut olm_core::Budget::new(15)
    )
    .is_err());
}

#[test]
fn stage4_coverage_weights() {
    let mut count = 0;
    for span in 4..=256 {
        for offset in -2..=span + 2 {
            for key in 0..16 {
                let actual = crate::weights::pair(span, offset, key)
                    .unwrap()
                    .map(f32::to_bits);
                for scalar in [0, 1] {
                    let mut expected = [0.0; 2];
                    unsafe {
                        sm2_ref_weights(span, offset, key, scalar, expected.as_mut_ptr());
                    }
                    assert_eq!(
                        actual,
                        expected.map(f32::to_bits),
                        "span={span} offset={offset} key={key} scalar={scalar}"
                    );
                    count += 1;
                }
            }
        }
    }
    assert_eq!(count, 1092960);
    let mut rng = Rng(0x5162c0a);
    for _ in 0..20000 {
        let p2 = [rng.unit() * 32.0 - 8.0, rng.unit() * 32.0 - 8.0];
        let p3 = [rng.unit() * 32.0 - 8.0, rng.unit() * 32.0 - 8.0];
        let offset = (rng.word() % 32) as i32 - 8;
        let actual = crate::weights::line(p2, p3, offset)
            .unwrap()
            .map(f32::to_bits);
        for scalar in [0, 1] {
            let mut expected = [0.0; 2];
            unsafe {
                sm2_ref_line(
                    p2.as_ptr(),
                    p3.as_ptr(),
                    offset,
                    scalar,
                    expected.as_mut_ptr(),
                );
            }
            assert_eq!(
                actual,
                expected.map(f32::to_bits),
                "p2={p2:?} p3={p3:?} offset={offset}"
            );
        }
    }
}

#[test]
fn stage4_corners_and_normalization() {
    use crate::polygon::{Corner::*, Plane, Polygon};
    let mut rng = Rng(0x5162c047);
    for (w, h) in [(1, 1), (1, 7), (7, 1), (3, 7), (11, 9)] {
        let stride = w + 3;
        let mut pixels: Vec<_> = (0..stride * h).map(|_| rng.pixel()).collect();
        for y in 0..h {
            for x in 0..w {
                for mask in 0..16 {
                    for normalize in [0, 1] {
                        let smooth = rng.unit();
                        let mut expected = [Vertex::default(); 12];
                        let n = unsafe {
                            sm2_ref_corners(
                                pixels.as_mut_ptr(),
                                w,
                                h,
                                stride,
                                x,
                                y,
                                smooth,
                                mask,
                                normalize,
                                expected.as_mut_ptr(),
                            )
                        } as usize;
                        let plane =
                            Plane::new(&pixels, w as usize, h as usize, stride as usize).unwrap();
                        let mut polygon = Polygon::new(plane, x, y, smooth).unwrap();
                        for (i, corner) in [Nw, Ne, Sw, Se].into_iter().enumerate() {
                            if mask & (1 << i) != 0 {
                                polygon.corner(corner, 0.125).unwrap();
                            }
                        }
                        if normalize != 0 {
                            polygon.normalize();
                        }
                        assert_eq!(polygon.samples().len(), n);
                        for (a, b) in polygon.samples().iter().zip(expected[..n].iter()) {
                            same(a.pixel, b.pixel);
                            assert_eq!(a.weight.to_bits(), b.weight.to_bits());
                        }
                    }
                }
            }
        }
    }
}

#[test]
fn invalid_geometry_and_polygon_capacity() {
    use crate::polygon::{Plane, Polygon};
    assert!(crate::scan::Grid::new(&[], 1, 1, 4).is_err());
    assert!(crate::scan::Grid::new(&[0; 8], 2, 1, 7).is_err());
    assert!(Plane::new(&[], 1, 1, 1).is_err());
    assert!(Plane::new(&[Pixel::default()], usize::MAX, 2, usize::MAX).is_err());
    let pixels = [Pixel::default(); 4];
    let mut p = Polygon::new(Plane::new(&pixels, 2, 2, 2).unwrap(), 0, 0, 0.5).unwrap();
    assert!(p.append(-1, 0, 1.0).is_err());
    for _ in 0..20 {
        p.append(0, 0, 0.125).unwrap();
    }
    assert_eq!(p.samples().len(), 12);
    assert!(crate::weights::line([f32::NAN, 0.0], [1.0, 1.0], 0).is_err());
}

#[test]
fn stage3_gamma_stages() {
    let mut rng = Rng(0x5162a11);
    for n in 0..=12 {
        for case in 0..512 {
            let mut center = rng.pixel();
            let mut samples: Vec<_> = (0..n)
                .map(|_| Vertex {
                    pixel: rng.pixel(),
                    weight: rng.unit() * 0.2,
                })
                .collect();
            if case % 8 == 0 {
                center.a = 0.0;
            }
            if case % 8 == 1 {
                center.a = 1.0;
            }
            if case % 8 == 2 {
                center.a = -0.25;
            }
            if case % 8 == 3 && n > 0 {
                samples[0].weight = -0.25;
            }
            if case % 8 == 4 && n > 0 {
                samples[0].weight = 1.25;
            }
            let value = [0.0, 0.1, 0.5, 1.0, 2.2, 5.0, 10.0][case % 7];
            let enable = case % 2 == 0;
            for op in 0..4 {
                let mut expected = center;
                let mut es = samples.clone();
                unsafe {
                    sm2_ref_gamma(op, &mut expected, es.as_mut_ptr(), n, enable as i32, value);
                }
                let mut actual = center;
                let mut ss = samples.clone();
                match op {
                    0 => gamma::decode_premultiply(&mut actual, &mut ss, enable, value),
                    1 => actual = gamma::composite(actual, &ss, false),
                    2 => actual = gamma::composite(actual, &ss, true),
                    _ => gamma::post_unpremultiply(&mut actual, enable, value),
                }
                assert_eq!(
                    actual.words(),
                    expected.words(),
                    "case={case} n={n} op={op}"
                );
                for (a, b) in ss.iter().zip(es.iter()) {
                    same(a.pixel, b.pixel);
                    assert_eq!(a.weight.to_bits(), b.weight.to_bits());
                }
            }
        }
    }
}

#[test]
fn stage3_palette_membership() {
    use gamma::GammaMode::*;
    let mut rng = Rng(0x5162c0107);
    for version in [1, 2] {
        for mode in [None, Colors, All] {
            for count in 0..=5 {
                for case in 0..128 {
                    let mut center = rng.pixel();
                    let mut samples: Vec<_> = (0..case % 13)
                        .map(|_| Vertex {
                            pixel: rng.pixel(),
                            weight: rng.unit(),
                        })
                        .collect();
                    let palette: Vec<_> = (0..count).map(|_| rng.pixel()).collect();
                    if count > 0 {
                        let mut p = palette[0];
                        if version == 2 {
                            p.r = lut::decode(p.r);
                            p.g = lut::decode(p.g);
                            p.b = lut::decode(p.b);
                        }
                        if case % 3 == 0 {
                            center = p;
                        } else if case % 3 == 1 && !samples.is_empty() {
                            samples[0].pixel = p;
                        }
                        if case % 11 == 0 {
                            center.r = f32::from_bits(0x7fc12345);
                        }
                    }
                    let mut expected_value = 0.0;
                    let expected = unsafe {
                        sm2_ref_adaptive(
                            &center,
                            samples.as_ptr(),
                            samples.len() as i32,
                            version,
                            mode as i32,
                            2.2,
                            palette.as_ptr(),
                            count,
                            &mut expected_value,
                        )
                    };
                    let (value, apply) =
                        gamma::adaptive(center, &samples, version, mode, 2.2, &palette);
                    assert_eq!(apply, expected != 0);
                    assert_eq!(value.to_bits(), expected_value.to_bits());
                }
            }
        }
    }
}

#[test]
fn stage3_scalar_nonfinite_and_curves() {
    let words = [
        0, 0x80000000, 0x3f800000, 0xbf800000, 0x7f800000, 0xff800000, 0x7fc12345, 0xff812345,
    ];
    for a in words {
        for b in words {
            let center = Pixel {
                r: f32::from_bits(a),
                g: f32::from_bits(b),
                b: f32::from_bits(a),
                a: f32::from_bits(b),
            };
            let samples = vec![Vertex {
                pixel: center,
                weight: 0.5,
            }];
            for op in [0, 2, 3] {
                let (mut expected, mut es) = (center, samples.clone());
                unsafe {
                    sm2_ref_gamma(op, &mut expected, es.as_mut_ptr(), 1, 0, 2.2);
                }
                let (mut actual, mut ss) = (center, samples.clone());
                match op {
                    0 => gamma::decode_premultiply(&mut actual, &mut ss, false, 2.2),
                    2 => actual = gamma::composite(actual, &ss, true),
                    _ => gamma::post_unpremultiply(&mut actual, false, 2.2),
                }
                same(actual, expected);
                same(ss[0].pixel, es[0].pixel);
            }
        }
    }
    let mut rng = Rng(0x5162c);
    for _ in 0..20000 {
        let t = rng.unit() * 2.0 - 0.5;
        for index in 0..8 {
            assert_eq!(
                gamma::curve(t, index).to_bits(),
                unsafe { sm2_ref_curve(t, index) }.to_bits()
            );
        }
        assert_eq!(
            gamma::srgb_encode_literal(t as f64).to_bits(),
            unsafe { sm2_ref_encode_literal(t as f64) }.to_bits()
        );
    }
}

#[test]
fn stage3_thread_count_independence() {
    let mut rng = Rng(0x51627);
    let input: Vec<_> = (0..31 * 19).map(|_| rng.pixel()).collect();
    let key = input[5];
    let run = |threads| {
        let mut out = input.clone();
        olm_core::parallel_rows(&mut out, 31, threads, |_, row| {
            frame::setup(row, 2, Some((key, false)));
            for p in row {
                let mut samples = [Vertex {
                    pixel: *p,
                    weight: 0.125,
                }];
                gamma::decode_premultiply(p, &mut samples, true, 2.2);
                *p = gamma::composite(*p, &samples, true);
                gamma::post_unpremultiply(p, true, 2.2);
            }
        })
        .unwrap();
        out.into_iter().map(Pixel::words).collect::<Vec<_>>()
    };
    let serial = run(1);
    for threads in [2, 3, 7] {
        assert_eq!(serial, run(threads));
    }
}

#[test]
fn stage2_classifiers_and_trapezoids() {
    for bits in 0..32 {
        let b = |i| bits & (1 << i) != 0;
        assert_eq!(
            crate::scan::classify(b(0), b(1), b(2), b(3), b(4)),
            unsafe { sm2_ref_classify(bits) }
        );
    }
    let mut rng = Rng(0x51627a9);
    for i in 0..20000 {
        let width = if i % 7 == 0 {
            (i % 37) as f32
        } else {
            rng.unit() * 100.0
        };
        let edge = rng.unit() * 2.0 - 0.5;
        let position = (rng.word() % 130) as i32 - 10;
        let actual = crate::scan::trapezoid(width, position, edge);
        let expected = unsafe { sm2_ref_trapezoid(width, position, edge) };
        assert_eq!(actual.to_bits(), expected.to_bits());
    }
}

#[test]
fn stage2_all_scanners() {
    use crate::scan::{Axial::*, Diagonal::*, Grid};
    let axial = [D0d0, D230, D3b0, D520, D6a0, D800, Da50, Dbd0];
    let diagonal = [D108d0, D109d0, D10ad0, D10bd0, D10d20, D10e40];
    let mut comparisons = 0;
    for seed in [0x5162, 0x20261112] {
        let mut rng = Rng(seed);
        for (w, h) in [(1, 1), (1, 7), (7, 1), (3, 7), (11, 9), (31, 19)] {
            for pattern in 0..48 {
                let stride = w * 4 + (pattern % 5);
                let mut bytes = vec![0xcd; (stride * h) as usize];
                for y in 0..h {
                    for x in 0..w {
                        for c in 0..4 {
                            let on = if pattern < 16 {
                                pattern & (1 << c) != 0
                            } else if pattern < 24 {
                                (x + y + c + pattern) % 3 == 0
                            } else {
                                rng.word() % 4 == 0
                            };
                            bytes[(y * stride + x * 4 + c) as usize] = if on { 255 } else { 0 };
                        }
                    }
                }
                let grid = Grid::new(&bytes, w, h, stride as usize).unwrap();
                for y in 0..h {
                    for x in 0..w {
                        for (kind, &scan) in axial.iter().enumerate() {
                            let mut expected = [0; 3];
                            unsafe {
                                sm2_ref_scan(
                                    kind as i32,
                                    bytes.as_ptr(),
                                    w,
                                    h,
                                    stride,
                                    x,
                                    y,
                                    expected.as_mut_ptr(),
                                );
                            }
                            assert_eq!(grid.axial(scan,x,y).unwrap(),expected,"seed={seed} size={w}x{h} pattern={pattern} at={x},{y} scan={scan:?}");
                            comparisons += 1;
                        }
                        for (kind, &scan) in diagonal.iter().enumerate() {
                            let mut expected = [0; 2];
                            unsafe {
                                sm2_ref_scan(
                                    kind as i32 + 8,
                                    bytes.as_ptr(),
                                    w,
                                    h,
                                    stride,
                                    x,
                                    y,
                                    expected.as_mut_ptr(),
                                );
                            }
                            assert_eq!(grid.diagonal(scan,x,y).unwrap(),expected,"seed={seed} size={w}x{h} pattern={pattern} at={x},{y} scan={scan:?}");
                            comparisons += 1;
                        }
                    }
                }
            }
        }
    }
    assert_eq!(comparisons, 973056);
}
struct Rng(u64);
impl Rng {
    fn word(&mut self) -> u32 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0 as u32
    }
    fn unit(&mut self) -> f32 {
        (self.word() >> 8) as f32 / 16777216.0
    }
    fn pixel(&mut self) -> Pixel {
        Pixel {
            r: self.unit(),
            g: self.unit(),
            b: self.unit(),
            a: self.unit(),
        }
    }
}
fn same(a: Pixel, b: Pixel) {
    assert_eq!(a.words(), b.words());
}

#[test]
fn stage1_integer_loads_and_packing() {
    for (depth, limit) in [(8, 256), (16, 65536)] {
        for value in 0..limit {
            let p = if depth == 8 {
                frame::load8([value as u8; 4])
            } else {
                frame::load16([value as u16; 4])
            };
            let mut expected = Pixel::default();
            unsafe {
                sm2_ref_load(depth, value, &mut expected);
            }
            same(p, expected);
            let packed = if depth == 8 {
                frame::pack8(p.r) as u32
            } else {
                frame::pack16(p.r) as u32
            };
            assert_eq!(packed, unsafe { sm2_ref_pack(depth, p.r) });
        }
    }
    let mut rng = Rng(0x5162);
    for _ in 0..20000 {
        let v = f32::from_bits(rng.word());
        assert_eq!(frame::pack16(v) as u32, unsafe { sm2_ref_pack(16, v) });
        if v.is_finite() {
            assert_eq!(frame::pack8(v) as u32, unsafe { sm2_ref_pack(8, v) });
        }
    }
}

#[test]
fn stage1_transfers() {
    let mut values = vec![
        0.0,
        -0.0,
        1.0,
        -1.0,
        2.0,
        f32::INFINITY,
        f32::NEG_INFINITY,
        f32::from_bits(0x7fc12345),
    ];
    // Every LUT knot and its immediate binary32 neighbors.
    for i in 0..10000 {
        let v = i as f32 / 9999.0;
        values.extend([
            v,
            f32::from_bits(v.to_bits().wrapping_sub(1)),
            f32::from_bits(v.to_bits() + 1),
        ]);
    }
    let mut rng = Rng(0x5162dec0de);
    values.extend((0..20000).map(|_| rng.unit()));
    for v in values {
        for (op, f) in [
            (0, frame::srgb_decode_literal as fn(f32) -> f32),
            (1, lut::decode),
            (2, lut::encode),
        ] {
            let expected = unsafe { sm2_ref_transfer(op, v) };
            assert_eq!(
                f(v).to_bits(),
                expected.to_bits(),
                "op={op} input={:08x}",
                v.to_bits()
            );
        }
    }
}

#[test]
fn stage1_key_setup_and_unpremultiply() {
    let mut rng = Rng(0x5162f00d);
    for case in 0..512 {
        let keys: Vec<_> = (0..5).map(|_| rng.pixel()).collect();
        let mut input: Vec<_> = (0..37).map(|_| rng.pixel()).collect();
        input[..5].copy_from_slice(&keys);
        input[5].r = f32::from_bits(0x7fc12345);
        input[5].g = keys[0].g;
        input[5].b = keys[0].b;
        input[6].a = 0.0;
        input[7].a = 1.0;
        input[8].a = -0.0;
        input[9] = keys[0];
        input[9].r += crate::types::COLOR_TOL;
        for op in 0..4 {
            let count = if op == 2 { 1 } else { case % 6 };
            let mut expected = input.clone();
            unsafe {
                sm2_ref_frame(
                    op,
                    expected.as_mut_ptr(),
                    expected.len() as i32,
                    keys.as_ptr(),
                    count,
                );
            }
            let mut actual = input.clone();
            match op {
                0 => frame::unpremultiply(&mut actual),
                1 => frame::palette_filter(&mut actual, &keys[..count as usize]),
                2 => frame::scalar_key(&mut actual, keys[0]),
                _ => frame::setup(&mut actual, 2, None),
            }
            for (a, b) in actual.into_iter().zip(expected) {
                same(a, b);
            }
        }
    }
}

#[test]
fn parallel_large_frames_all_versions() {
    use crate::algorithm::{render_with_range, Params};
    use gamma::GammaMode;
    let (w, h) = (257, 193); // Crosses the parallel threshold, with uneven row chunks.
    let mut rng = Rng(0x519223);
    let palette: Vec<_> = (0..6).map(|_| rng.pixel()).collect();
    let input: Vec<_> = (0..w * h)
        .map(|i| {
            if i % 7 == 0 {
                rng.pixel()
            } else {
                palette[(i / w + i % w / 3) % 6]
            }
        })
        .collect();
    for version in 1..=3 {
        for mode in [GammaMode::None, GammaMode::Colors, GammaMode::All] {
            let p = Params {
                version,
                smoothness: 100,
                extra: 75,
                range: 2,
                gamma_mode: mode,
                gamma: 2.4,
                gamma_colors: palette.clone(),
                key: Some((palette[0], version % 2 == 0)),
                keep_premultiplied: true,
            };
            let run = |threads| {
                render_with_range(
                    &input,
                    w,
                    h,
                    &p,
                    2.375,
                    threads,
                    &mut olm_core::Budget::new(w * h * 36),
                )
                .unwrap()
            };
            let expected = run(1);
            for threads in [2, 3, usize::MAX] {
                for (a, b) in run(threads).iter().zip(&expected) {
                    assert_eq!(a.words(), b.words());
                }
            }
        }
    }
}

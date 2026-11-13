use olm_kirakira::{algorithm as a, filters as f, ramp::Ramp, trig};
unsafe extern "C" {
    fn ref_trig(x: f64, out: *mut f32);
    fn ref_filter(
        src: *const f32,
        dst: *mut f32,
        w: i32,
        h: i32,
        len: i32,
        angle: f64,
        kind: i32,
        normalize: i32,
    );
    fn ref_seed(
        src: *const [f32; 4],
        dst: *mut f32,
        n: i32,
        channel: i32,
        strength: f32,
        fade: f32,
    );
    fn ref_compose(
        g: *const [f32; 4],
        s: *const [f32; 4],
        out: *mut [f32; 4],
        go: f32,
        so: f32,
        merge: i32,
    );
    fn ref_resize(src: *const [f32; 4], dst: *mut [f32; 4], sw: i32, sh: i32, dw: i32, dh: i32);
    fn ref_render(
        src: *const [f32; 4],
        dst: *mut [f32; 4],
        w: i32,
        h: i32,
        p: *const f64,
        scale: f32,
    );
}
fn same(a: &[f32], b: &[f32], label: &str) {
    assert_eq!(a.len(), b.len());
    for (i, (a, b)) in a.iter().zip(b).enumerate() {
        assert_eq!(a.to_bits(), b.to_bits(), "{label} sample {i}: {a:?} {b:?}");
    }
}
#[test]
fn embedded_trig_matches_cpp() {
    for x in -20000..20000 {
        let degrees = if x % 2 == 0 {
            x as f64 * 65536.0
        } else {
            x as f64 / 31.0
        };
        let (s, c) = trig::extent_sincos(degrees);
        let mut out = [0.0; 2];
        unsafe {
            ref_trig(degrees, out.as_mut_ptr());
        }
        same(&[s, c], &out, "extent trig");
    }
}
#[test]
fn filters_match_cpp() {
    for (w, h) in [(1, 1), (3, 7), (11, 7), (19, 11)] {
        let src: Vec<f32> = (0..w * h)
            .map(|i| ((i * 7717 + 113) % 65537) as f32 / 65536.0)
            .collect();
        for len in [1, 2, 3, 5, 7, 11, 50] {
            for angle in [0.0, 45.0, 90.0, 135.0, 12345.0 * 65536.0] {
                for kind in 1..=7 {
                    for normalize in [false, true] {
                        if kind == 4 && (w < 5 || h < 3) {
                            continue;
                        }
                        let actual = match kind {
                            1..=4 => f::ray(&src, w, h, len, angle, kind, normalize, true),
                            5 | 6 => f::box_highlight(
                                &src,
                                w,
                                h,
                                len * 2 + 1,
                                if kind == 5 { 1 } else { 3 },
                                normalize,
                            ),
                            _ => f::gaussian_highlight(&src, w, h, len),
                        };
                        let mut expected = vec![0.0; src.len()];
                        unsafe {
                            ref_filter(
                                src.as_ptr(),
                                expected.as_mut_ptr(),
                                w as i32,
                                h as i32,
                                len,
                                angle,
                                kind,
                                normalize as i32,
                            );
                        }
                        same(
                            &actual,
                            &expected,
                            &format!(
                                "{w}x{h} len={len} angle={angle} kind={kind} norm={normalize}"
                            ),
                        );
                    }
                }
            }
        }
    }
}
#[test]
fn seeds_composition_resize_match_cpp() {
    let src: Vec<[f32; 4]> = (0..77)
        .map(|i| std::array::from_fn(|c| ((i * 187 + c * 33) % 256) as f32 / 255.0))
        .collect();
    for channel in 1..=6 {
        for strength in [0.0, 0.01, 0.999, 1.0, 3.7, 10.0] {
            for fade in [0.0, 0.1, 0.2] {
                let p = a::Params {
                    channel,
                    strength: strength as f64,
                    fade: fade as f64,
                    ..Default::default()
                };
                let actual = a::seed(&src, &p);
                let mut expected = vec![0.0; actual.len()];
                unsafe {
                    ref_seed(
                        src.as_ptr(),
                        expected.as_mut_ptr(),
                        77,
                        channel,
                        strength,
                        fade,
                    );
                }
                same(&actual, &expected, "seed");
            }
        }
    }
    for s in &src {
        for g in &src {
            for merge in [1, 2] {
                let actual = a::compose(*g, *s, 0.73, 0.42, merge);
                let mut expected = [0.0; 4];
                unsafe {
                    ref_compose(g, s, &mut expected, 0.73, 0.42, merge);
                }
                same(&actual, &expected, "compose");
            }
        }
    }
    for (dw, dh) in [(1, 1), (5, 3), (9, 9), (25, 17)] {
        let actual = f::resize(&src, 11, 7, dw, dh, true);
        let mut expected = vec![[0.0; 4]; dw * dh];
        unsafe {
            ref_resize(
                src.as_ptr(),
                expected.as_mut_ptr(),
                11,
                7,
                dw as i32,
                dh as i32,
            );
        }
        for (a, b) in actual.iter().zip(&expected) {
            same(a, b, "resize");
        }
    }
}
#[test]
fn ramp_disk_abi() {
    assert_eq!(std::mem::size_of::<Ramp>(), 324);
    for count in 0..=16 {
        let mut r = Ramp {
            count,
            stops: [[0.0; 5]; 16],
        };
        for i in 0..16 {
            r.stops[i] =
                std::array::from_fn(|c| f32::from_bits(0x3f000000 + i as u32 * 31 + c as u32));
        }
        let bytes = r.flatten().unwrap();
        assert_eq!(bytes[0], 1);
        assert!(bytes[5 + count as usize * 20..].iter().all(|v| *v == 0));
        let decoded = Ramp::unflatten(&bytes).unwrap();
        assert!(decoded.equal_active(&r));
        assert_eq!(bytes, decoded.flatten().unwrap());
    }
    assert!(Ramp::unflatten(&[1, 17, 0, 0, 0]).is_none());
}
#[test]
fn concurrent_render_is_deterministic() {
    let src: Vec<[f32; 4]> = (0..77).map(|i| [i as f32 / 77.0, 0.5, 0.2, 0.7]).collect();
    let p = a::Params::default();
    let expected = a::pixels(&src, 11, 7, &p, 1.0).unwrap();
    std::thread::scope(|scope| {
        let mut joins = vec![];
        for _ in 0..4 {
            joins.push(scope.spawn(|| a::pixels(&src, 11, 7, &p, 1.0).unwrap()));
        }
        for j in joins {
            let actual = j.join().unwrap();
            for (a, b) in actual.iter().zip(&expected) {
                same(a, b, "thread count");
            }
        }
    });
}
#[test]
fn full_cpp_pipeline() {
    for (w, h) in [(11, 7), (31, 19)] {
        for channel in 1..=6 {
            for blur in 1..=3 {
                for approximate in [false, true] {
                    let p = a::Params {
                        fused_filters: false,
                        fused_resize: false,
                        channel,
                        blur,
                        approximate,
                        rotation: -17487887.0,
                        gain: 100.0,
                        strength: 10.0,
                        lengths: [0, 50, 1000, 1000, 0],
                        ..Default::default()
                    };
                    let src: Vec<[f32; 4]> = (0..w * h)
                        .map(|i| std::array::from_fn(|c| ((i * 187 + c * 33) % 256) as f32 / 255.0))
                        .collect();
                    let actual = a::pixels(&src, w, h, &p, 1.0).unwrap();
                    let mut expected = vec![[0.0; 4]; src.len()];
                    let params = [
                        channel as f64,
                        blur as f64,
                        1.0,
                        approximate as u8 as f64,
                        p.gain,
                        p.strength,
                        p.fade,
                        p.glow_opacity,
                        p.source_opacity,
                        p.rotation,
                        0.0,
                        50.0,
                        1000.0,
                        1000.0,
                        0.0,
                    ];
                    unsafe {
                        ref_render(
                            src.as_ptr(),
                            expected.as_mut_ptr(),
                            w as i32,
                            h as i32,
                            params.as_ptr(),
                            1.0,
                        );
                    }
                    for (a, b) in actual.iter().zip(&expected) {
                        same(
                            a,
                            b,
                            &format!("render {w} {h} ch{channel} blur{blur} approx{approximate}"),
                        );
                    }
                }
            }
        }
    }
}
#[test]
fn ramp_editor_matches_cpp_events_and_draw_commands() {
    use olm_kirakira::editor::{self as e, Event};
    unsafe extern "C" {
        fn ref_ui(
            r: *mut Ramp,
            s: *mut i32,
            clip: *mut Ramp,
            available: *mut i32,
            rng: *mut u32,
            event: i32,
            x: i32,
            y: i32,
            digest: *mut u64,
        ) -> i32;
    }
    let mut r = Ramp::default();
    let mut expected = r;
    let mut s = e::State::default();
    let mut state = [-1, -1, 0, 0, 0, 0, -1, 0];
    let mut clip = e::Clipboard::default();
    let mut clip_ref = clip.data;
    let mut available = 0;
    let mut rng = 0x810cd;
    let mut rng_ref = rng;
    let mut events = vec![
        (Event::Single, 100, 30),
        (Event::Single, 100, 65),
        (Event::Drag, 160, 75),
        (Event::Release, 160, 75),
        (Event::Multiple, 160, 65),
        (Event::Single, 240, 40),
        (Event::Release, 240, 40),
        (Event::Single, 70, 90),
        (Event::Release, 70, 90),
        (Event::Single, 170, 90),
        (Event::Release, 170, 90),
        (Event::Single, 240, 70),
        (Event::Release, 240, 70),
        (Event::Single, 260, 15),
        (Event::Single, 240, 35),
        (Event::Drag, 240, 53),
        (Event::Release, 240, 35),
    ];
    let mut random = 1234567u32;
    for _ in 0..2000 {
        random = random.wrapping_mul(1664525).wrapping_add(1013904223);
        let x = (random % 330) as i32 - 10;
        let y = ((random >> 9) % 180) as i32 - 10;
        let event = [
            Event::Hover,
            Event::Single,
            Event::Multiple,
            Event::Drag,
            Event::Release,
        ][(random >> 20) as usize % 5];
        events.push((event, x, y));
    }
    for (event, x, y) in events {
        let picked = e::dispatch(&mut r, &mut s, &mut clip, &mut rng, event, x, y);
        let mut hash_ref = 0;
        let picked_ref = unsafe {
            ref_ui(
                &mut expected,
                state.as_mut_ptr(),
                &mut clip_ref,
                &mut available,
                &mut rng_ref,
                event as i32,
                x,
                y,
                &mut hash_ref,
            )
        };
        assert_eq!(picked, picked_ref);
        assert_eq!(r, expected);
        assert_eq!(clip.data, clip_ref);
        assert_eq!(clip.available, available != 0);
        assert_eq!(rng, rng_ref);
        assert_eq!(
            [
                s.selected,
                s.armed,
                s.hover_x,
                s.hover_y,
                s.anchor_y,
                s.menu_open as i32,
                s.preset_row,
                s.scroll
            ],
            state
        );
        let mut hash = 1469598103934665603u64;
        let mut word = |v: u32| {
            hash ^= v as u64;
            hash = hash.wrapping_mul(1099511628211);
        };
        for c in e::draw(&r, &s, clip.available) {
            word(c.kind as u32);
            for f in c.rect.into_iter().chain(c.color.rgba) {
                word(f.to_bits());
            }
            word(c.color.role as u32);
            word(c.color.factor.to_bits());
            word(c.font.to_bits());
            for t in c.text.encode_utf16() {
                word(t as u32);
            }
            word(0);
        }
        assert_eq!(hash, hash_ref, "draw at {x},{y}");
    }
}
#[test]
fn ramp_interpolation_and_legacy_mode4_match_cpp() {
    unsafe extern "C" {
        fn ref_ramp_interp(a: *const Ramp, b: *const Ramp, t: f32, out: *mut Ramp);
        fn ref_legacy(src: *const [f32; 4], dst: *mut [f32; 4], w: i32, h: i32, variant: i32);
    }
    for left in 0..=16 {
        for right in 0..=16 {
            for t in [-0.5, 0.0, 0.37, 0.5, 1.0, 1.5] {
                let mut l = olm_kirakira::editor::preset(left);
                let mut r = olm_kirakira::editor::preset(right + 17);
                l.count = left as u32;
                r.count = right as u32;
                let got = l.interpolate(&r, t);
                let mut expected = Ramp::default();
                unsafe {
                    ref_ramp_interp(&l, &r, t, &mut expected);
                }
                assert_eq!(got, expected);
            }
        }
    }
    for (w, h) in [(11, 7), (19, 13)] {
        for variant in 0..5 {
            let mut p = a::Params {
                fused_filters: false,
                fused_resize: false,
                blur: 4,
                merge: if variant == 0 { 1 } else { 2 },
                gain: if variant == 0 { 1.0 } else { 0.73 },
                rotation: if variant == 0 { 0.0 } else { 1.0 },
                lengths: [0; 5],
                ..Default::default()
            };
            if variant == 1 || variant == 4 {
                p.lengths[1] = 5;
                p.use_ramp[1] = true;
            }
            if variant == 2 || variant == 4 {
                p.lengths[3] = 7;
            }
            if variant == 0 || variant == 3 || variant == 4 {
                p.lengths[4] = 3;
                p.use_ramp[4] = variant != 0;
            }
            let src: Vec<[f32; 4]> = (0..w * h)
                .map(|i| std::array::from_fn(|c| ((i * 187 + c * 33) % 256) as f32 / 255.0))
                .collect();
            let actual = a::pixels(&src, w, h, &p, 1.0).unwrap();
            let mut expected = vec![[0.0; 4]; src.len()];
            unsafe {
                ref_legacy(
                    src.as_ptr(),
                    expected.as_mut_ptr(),
                    w as i32,
                    h as i32,
                    variant,
                );
            }
            for (a, b) in actual.iter().zip(&expected) {
                same(a, b, "legacy mode4");
            }
        }
    }
}

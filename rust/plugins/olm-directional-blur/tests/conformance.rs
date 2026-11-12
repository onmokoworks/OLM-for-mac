use olm_directional_blur::algorithm::{self, Depth, Params};
extern "C" {
    fn reference_render(
        depth: i32,
        input: *const u8,
        output: *mut u8,
        w: i32,
        h: i32,
        f: *const f32,
        n: *const i32,
        layer: *const u8,
    ) -> i32;
    fn reference_gaussian(n: i32, i: i32) -> f32;
}
fn rng(s: &mut u32) -> u32 {
    *s = s.wrapping_mul(1664525).wrapping_add(1013904223);
    *s
}
#[test]
fn gaussian_words() {
    for n in [1, 2, 7, 32, 99, 100, 257, 1000, 4000] {
        for (i, v) in algorithm::gaussian(n).iter().enumerate() {
            assert_eq!(
                v.to_bits(),
                unsafe { reference_gaussian(n, i as i32) }.to_bits()
            );
        }
    }
}
#[test]
fn cpp_full_images_and_thread_independence() {
    let mut seed = 0x12345678;
    let mut cases = 0;
    for k in 0..120 {
        let (w, h) = [(1, 1), (3, 7), (11, 7), (31, 19), (17, 33), (64, 36)][k % 6];
        let p = Params {
            angle: (rng(&mut seed) % 721) as f32 - 360.0,
            gain: (rng(&mut seed) % 1001) as f32 / 100.0,
            size: if k % 3 == 0 {
                0.0
            } else {
                (rng(&mut seed) % 101) as f32
            },
            front: (rng(&mut seed) % 50 + 1) as i32,
            back: (rng(&mut seed) % 50) as i32,
            front_fade: (rng(&mut seed) % 21) as i32,
            back_fade: (rng(&mut seed) % 21) as i32,
            front_tail: (rng(&mut seed) % 101) as f32,
            back_tail: (rng(&mut seed) % 101) as f32,
            noise: if k % 3 == 0 {
                0.0
            } else {
                (rng(&mut seed) % 101) as f32
            },
            noise_type: 1 + (k % 2) as i32,
            seed: rng(&mut seed) % 1000 + 1,
            offset: (rng(&mut seed) % 721) as i32 - 360,
            thickness: (rng(&mut seed) % 100 + 1) as f32 / 4.0,
        };
        let f = [
            p.angle,
            p.gain,
            p.front_tail,
            p.back_tail,
            p.size,
            p.noise,
            p.thickness,
        ];
        let n = [
            p.front,
            p.front_fade,
            p.back,
            p.back_fade,
            p.noise_type,
            p.seed as i32,
            p.offset,
        ];
        let raw: Vec<[u8; 4]> = (0..w * h)
            .map(|_| {
                let a = [0, 1, 32, 128, 255][(rng(&mut seed) % 5) as usize];
                [
                    (rng(&mut seed) >> 24) as u8,
                    (rng(&mut seed) >> 24) as u8,
                    (rng(&mut seed) >> 24) as u8,
                    a,
                ]
            })
            .collect();
        for depth in [Depth::U8, Depth::U16, Depth::F32] {
            let input: Vec<[f32; 4]> = raw
                .iter()
                .map(|p| {
                    p.map(|v| match depth {
                        Depth::U8 | Depth::F32 => v as f32 / 255.0,
                        Depth::U16 => ((v as u32 * 32768 + 127) / 255) as f32 * (1.0 / 32768.0),
                    })
                })
                .collect();
            let result = algorithm::render(&input, w, h, &p, depth, None, 1).unwrap();
            let parallel = algorithm::render(&input, w, h, &p, depth, None, 4).unwrap();
            for (a, b) in result.iter().flatten().zip(parallel.iter().flatten()) {
                assert_eq!(a.to_bits(), b.to_bits(), "threads case {k}");
            }
            unsafe {
                match depth {
                    Depth::U8 => {
                        let mut reference = vec![[0u8; 4]; w * h];
                        assert_eq!(
                            reference_render(
                                8,
                                raw.as_ptr().cast(),
                                reference.as_mut_ptr().cast(),
                                w as i32,
                                h as i32,
                                f.as_ptr(),
                                n.as_ptr(),
                                std::ptr::null()
                            ),
                            0
                        );
                        for (i, (r, v)) in reference.iter().zip(&result).enumerate() {
                            assert_eq!(
                                *r,
                                v.map(|v| olm_math::x86::cvttss2si(v * 255.0) as u8),
                                "u8 case {k} pixel {i}"
                            );
                        }
                    }
                    Depth::U16 => {
                        let src: Vec<[u16; 4]> = input
                            .iter()
                            .map(|v| [v[3], v[0], v[1], v[2]].map(|x| (x * 32768.0) as u16))
                            .collect();
                        let mut reference = vec![[0u16; 4]; w * h];
                        assert_eq!(
                            reference_render(
                                16,
                                src.as_ptr().cast(),
                                reference.as_mut_ptr().cast(),
                                w as i32,
                                h as i32,
                                f.as_ptr(),
                                n.as_ptr(),
                                std::ptr::null()
                            ),
                            0
                        );
                        for (i, (r, v)) in reference.iter().zip(&result).enumerate() {
                            assert_eq!(
                                *r,
                                [v[3], v[0], v[1], v[2]]
                                    .map(|v| olm_math::x86::cvttss2si(v * 32768.0) as u16),
                                "u16 case {k} pixel {i}"
                            );
                        }
                    }
                    Depth::F32 => {
                        let src: Vec<[f32; 4]> =
                            input.iter().map(|v| [v[3], v[0], v[1], v[2]]).collect();
                        let mut reference = vec![[0f32; 4]; w * h];
                        assert_eq!(
                            reference_render(
                                32,
                                src.as_ptr().cast(),
                                reference.as_mut_ptr().cast(),
                                w as i32,
                                h as i32,
                                f.as_ptr(),
                                n.as_ptr(),
                                std::ptr::null()
                            ),
                            0
                        );
                        for (i, (r, v)) in reference.iter().zip(&result).enumerate() {
                            assert_eq!(
                                r.map(f32::to_bits),
                                [v[3], v[0], v[1], v[2]].map(f32::to_bits),
                                "f32 case {k} pixel {i}"
                            );
                        }
                    }
                }
            }
            cases += 1;
        }
    }
    assert_eq!(cases, 360);
}

#[test]
fn layer_and_nonfinite_cpp_words() {
    let (w, h) = (17usize, 11usize);
    let mut state = 7;
    for case in 0..24 {
        let p = Params {
            front: 11,
            back: 7,
            front_fade: if case % 3 == 0 { 0 } else { 4 },
            back_fade: if case % 4 == 0 { 0 } else { 5 },
            front_tail: if case % 2 == 0 { 0.0 } else { 30.0 },
            back_tail: 0.0,
            size: if case % 3 == 0 { 0.0 } else { 25.0 },
            angle: [0.0, 45.0, 168.0, -60.0][case % 4],
            gain: 1.25,
            noise: if case < 12 { 70.0 } else { 0.0 },
            noise_type: 3,
            ..Params::default()
        };
        let mut src: Vec<[f32; 4]> = (0..w * h)
            .map(|_| {
                let a = [0.0, 0.25, 1.0, -0.25][(rng(&mut state) % 4) as usize];
                [a, (rng(&mut state) % 500) as f32 / 255.0 - 0.25, 0.5, 0.9]
            })
            .collect();
        if case >= 12 {
            for i in (0..w * h).step_by(19) {
                src[i][(case - 12) % 4] = [
                    f32::from_bits(0x7fc12345),
                    f32::INFINITY,
                    f32::NEG_INFINITY,
                    -0.0,
                ][case % 4];
            }
        }
        let layer: Vec<[f32; 4]> = (0..w * h).map(|_| [1.0, 0.2, 0.7, 0.9]).collect();
        let input: Vec<_> = src.iter().map(|v| [v[1], v[2], v[3], v[0]]).collect();
        let normalized_layer: Vec<_> = layer.iter().map(|v| [v[1], v[2], v[3], v[0]]).collect();
        let result =
            algorithm::render(&input, w, h, &p, Depth::F32, Some(&normalized_layer), 3).unwrap();
        let mut reference = vec![[0f32; 4]; w * h];
        let f = [
            p.angle,
            p.gain,
            p.front_tail,
            p.back_tail,
            p.size,
            p.noise,
            p.thickness,
        ];
        let n = [
            p.front,
            p.front_fade,
            p.back,
            p.back_fade,
            p.noise_type,
            p.seed as i32,
            p.offset,
        ];
        assert_eq!(
            unsafe {
                reference_render(
                    32,
                    src.as_ptr().cast(),
                    reference.as_mut_ptr().cast(),
                    w as i32,
                    h as i32,
                    f.as_ptr(),
                    n.as_ptr(),
                    layer.as_ptr().cast(),
                )
            },
            0
        );
        for (i, (a, b)) in reference.iter().zip(&result).enumerate() {
            assert_eq!(
                a.map(f32::to_bits),
                [b[3], b[0], b[1], b[2]].map(f32::to_bits),
                "layer/HDR case {case} pixel {i}"
            );
        }
    }
}

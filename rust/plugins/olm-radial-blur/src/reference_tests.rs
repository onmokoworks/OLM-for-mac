use crate::{algorithm, math, noise};
#[path = "../tests/support/offset_witness.rs"]
mod offset_witness;
extern "C" {
    #[cfg(target_arch = "x86_64")]
    fn radial_weights_native(n: i32, out: *mut f32);
    fn radial_trig(x: f32, out: *mut f32);
    fn radial_weights(n: i32, rotation: i32, out: *mut f32);
    fn radial_noise(w: i32, h: i32, size: f32, phase: f32, seed: u32, out: *mut f32) -> i32;
    fn radial_sample(data: *const f32, w: i32, h: i32, x: f32, y: f32, repeat: i32, out: *mut f32);
    fn radial_scalar(data: *const f32, w: i32, h: i32, x: f32, y: f32, repeat: i32) -> f32;
}
#[cfg(target_arch = "x86_64")]
#[test]
#[cfg_attr(
    target_os = "macos",
    ignore = "Capture-machine RCPSS qualification: Intel Mac hardware has a different seed profile; portable golden tests validate the preserved Windows profile"
)]
fn native_reciprocal_profile_and_gaussians() {
    unsafe {
        use std::arch::x86_64::{_mm_cvtss_f32, _mm_rcp_ss, _mm_set_ss};
        let native = |x: f32| _mm_cvtss_f32(_mm_rcp_ss(_mm_set_ss(x))).to_bits();
        // Full significand qualification and exponent-scaling qualification for
        // every public Gaussian length, independent of pixels or expected frames.
        for mantissa in 0..0x800000u32 {
            let x = f32::from_bits(0x3f800000 + mantissa);
            assert_eq!(math::reciprocal_seed(x).to_bits(), native(x));
        }
        for n in 2..=30000 {
            let d = n as f32 * n as f32 * 0.111111119389534f32;
            let d = ((d + d) as f64 + 1.0e-5) as f32;
            assert_eq!(math::reciprocal_seed(d).to_bits(), native(d));
        }
        for n in [1, 2, 3, 4, 5, 20, 43, 63, 99, 100, 499, 2000, 3000] {
            let a = math::fade_weights(n);
            let mut b = vec![0.0; a.len()];
            radial_weights_native(n, b.as_mut_ptr());
            assert_eq!(
                a.iter().map(|v| v.to_bits()).collect::<Vec<_>>(),
                b.iter().map(|v| v.to_bits()).collect::<Vec<_>>()
            );
        }
    }
}
#[cfg(target_arch = "x86_64")]
#[test]
fn reciprocal_seed_diagnostic() {
    unsafe {
        use std::arch::x86_64::{_mm_cvtss_f32, _mm_rcp_ss, _mm_set_ss};
        for n in [20, 43, 63, 100, 2000, 30000] {
            let d = n as f32 * n as f32 * 0.111111119389534f32;
            let d = ((d + d) as f64 + 1.0e-5) as f32;
            let exact = 1.0 / d;
            let seed = _mm_cvtss_f32(_mm_rcp_ss(_mm_set_ss(d)));
            let old = (exact + exact) - (exact * exact) * d;
            let native = (seed + seed) - (seed * seed) * d;
            println!("length={n} denominator={:08x} division={:08x} seed={:08x} cpp_refined={:08x} native_refined={:08x}",d.to_bits(),exact.to_bits(),seed.to_bits(),old.to_bits(),native.to_bits());
        }
    }
}
#[cfg(target_arch = "x86_64")]
#[test]
#[ignore = "Explicit hardware-profile regeneration; writes only owned crate source"]
fn capture_reciprocal_profile() {
    unsafe {
        use std::arch::x86_64::{_mm_cvtss_f32, _mm_rcp_ss, _mm_set_ss};
        let native = |x: f32| _mm_cvtss_f32(_mm_rcp_ss(_mm_set_ss(x))).to_bits();
        let table: Vec<u32> = (0..4096)
            .map(|i| native(f32::from_bits(0x3f800000 + (i << 11))))
            .collect();
        for mantissa in 0..0x800000u32 {
            assert_eq!(
                native(f32::from_bits(0x3f800000 + mantissa)),
                table[(mantissa >> 11) as usize],
                "mantissa={mantissa:08x}"
            );
        }
        let mut text=String::from("// RCPSS mantissa profile, captured from this validation CPU; see VALIDATION.md.\n// Exhaustively checked across all 2^23 normal significands. No image data used.\npub const SEED: [u32; 4096] = [\n");
        for row in table.chunks(8) {
            for word in row {
                text.push_str(&format!("0x{word:08x},"));
            }
            text.push('\n');
        }
        text.push_str("];\n");
        std::fs::write(
            concat!(env!("CARGO_MANIFEST_DIR"), "/src/reciprocal_table.rs"),
            text,
        )
        .unwrap();
    }
}
#[test]
fn cpp_trig_and_tables() {
    unsafe {
        for i in -10000..10000 {
            let x = i as f32 * 0.0007123;
            let mut r = [0.0; 2];
            radial_trig(x, r.as_mut_ptr());
            let (s, c) = math::trig(x);
            assert_eq!([s.to_bits(), c.to_bits()], r.map(f32::to_bits));
        }
        for n in [0, 1, 2, 3, 4, 5, 17, 99, 100, 499, 2000, 3000] {
            for rotation in [false, true] {
                let a = if rotation {
                    math::rotation_weights(n)
                } else {
                    math::fade_weights_seed(n, false)
                };
                let mut b = vec![0.0; a.len()];
                radial_weights(n, rotation as i32, b.as_mut_ptr());
                assert_eq!(
                    a.iter().map(|x| x.to_bits()).collect::<Vec<_>>(),
                    b.iter().map(|x| x.to_bits()).collect::<Vec<_>>(),
                    "n={n} rotation={rotation}"
                );
            }
        }
    }
}
#[test]
fn cpp_noise_and_sampling() {
    unsafe {
        for seed in [1, 2, 999, 1000] {
            for size in [0.25, 1.0, 3.37, 10.0, 100.0] {
                for phase in [-5.5, 0.0, 6.283185] {
                    let (a, nw) = noise::generate(11, 7, size, phase, seed);
                    let mut b = vec![0.0; a.len()];
                    assert_eq!(
                        radial_noise(11, 7, size, phase, seed, b.as_mut_ptr()),
                        nw as i32
                    );
                    assert_eq!(
                        a.iter().map(|x| x.to_bits()).collect::<Vec<_>>(),
                        b.iter().map(|x| x.to_bits()).collect::<Vec<_>>()
                    );
                }
            }
        }
        let src: Vec<[f32; 4]> = (0..21)
            .map(|i| [i as f32 * 0.11, 0.3, -0.2, (i % 5) as f32 * 0.25])
            .collect();
        let mut scalar: Vec<f32> = src.iter().map(|p| p[3]).collect();
        scalar.push(0.0);
        for n in 0..1200 {
            let x = (n % 39) as f32 * 0.27 - 3.0;
            let y = (n % 29) as f32 * 0.23 - 2.0;
            for repeat in [false, true] {
                let (a, valid) = algorithm::sample_rgba(&src, 3, 7, x, y, repeat);
                let mut b = [0.0; 5];
                radial_sample(
                    src.as_ptr().cast(),
                    3,
                    7,
                    x,
                    y,
                    repeat as i32,
                    b.as_mut_ptr(),
                );
                assert_eq!(
                    a.map(f32::to_bits),
                    [b[0], b[1], b[2], b[3]].map(f32::to_bits)
                );
                assert_eq!(valid, b[4] != 0.0);
                assert_eq!(
                    algorithm::sample_scalar(&scalar, 3, 7, x, y, repeat).to_bits(),
                    radial_scalar(scalar.as_ptr(), 3, 7, x, y, repeat as i32).to_bits()
                );
            }
        }
    }
}

#[test]
fn cpp_exceptional_sampler_words() {
    let words = [
        0x00000000, 0x80000000, 0x7f800000, 0xff800000, 0x7fc12345, 0x7f812345, 0xffc54321,
        0x00000001,
    ];
    for word in words {
        for channel in 0..4 {
            let mut src = [[0.25, 0.5, 0.75, 1.0]; 4];
            src[1][channel] = f32::from_bits(word);
            for (x, y) in [(0.0, 0.0), (0.3, 0.7), (-0.25, 0.5), (1.0, 1.0)] {
                for repeat in [false, true] {
                    let (a, valid) = algorithm::sample_rgba(&src, 2, 2, x, y, repeat);
                    let mut b = [0.0; 5];
                    unsafe {
                        radial_sample(
                            src.as_ptr().cast(),
                            2,
                            2,
                            x,
                            y,
                            repeat as i32,
                            b.as_mut_ptr(),
                        );
                    }
                    assert_eq!(
                        a.map(f32::to_bits),
                        [b[0], b[1], b[2], b[3]].map(f32::to_bits)
                    );
                    assert_eq!(valid, b[4] != 0.0);
                }
            }
        }
    }
}
#[test]
fn threads_and_type3() {
    use olm_core::*;
    let l = Layout {
        width: 5,
        height: 3,
        stride: 5 * 4 + 3,
        depth: Depth::U8,
        origin: (0, 0),
    };
    let mut bytes = vec![0; l.span().unwrap()];
    {
        let mut v = ViewMut::new(&mut bytes, l).unwrap();
        for y in 0..3 {
            for x in 0..5 {
                v.set(x, y, Pixel::U8([(x * 37 + y * 29) as u8, 123, 17, 219]))
                    .unwrap();
            }
        }
    }
    let input = View::new(&bytes, l).unwrap();
    for rotation in [false, true] {
        let mut p = algorithm::Params {
            rotation,
            center: [2.5, 1.5],
            strength: [17, 12],
            fade: [3, 5],
            noise: 32.0,
            size: 64.0,
            quality: 1.0,
            ..Default::default()
        };
        let mut a = vec![0; l.span().unwrap()];
        let mut b = a.clone();
        algorithm::render(&p, &input, &mut ViewMut::new(&mut a, l).unwrap(), 1).unwrap();
        algorithm::render(&p, &input, &mut ViewMut::new(&mut b, l).unwrap(), 3).unwrap();
        assert_eq!(a, b);
        p.noise_type = 3;
        let before = b.clone();
        assert_eq!(
            algorithm::render(&p, &input, &mut ViewMut::new(&mut b, l).unwrap(), 1),
            Err(Error::Unsupported)
        );
        assert_eq!(before, b);
    }
}

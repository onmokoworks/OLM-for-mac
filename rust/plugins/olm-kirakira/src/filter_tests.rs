//! Retained pre-optimization warp plus ordered box/reference checks.
use super::*;
fn bits(v: &[f32]) -> Vec<u32> {
    v.iter().map(|v| v.to_bits()).collect()
}
fn input(w: usize, h: usize, special: bool) -> Vec<f32> {
    let mut rng = 0x13417891u32;
    (0..w * h)
        .map(|i| {
            rng ^= rng << 13;
            rng ^= rng >> 17;
            rng ^= rng << 5;
            if special {
                [
                    0.0,
                    -0.0,
                    f32::from_bits(1),
                    f32::MAX,
                    -f32::MAX,
                    f32::INFINITY,
                    f32::NEG_INFINITY,
                    f32::from_bits(0x7fc12345),
                    f32::from_bits(0xffc54321),
                ][i % 9]
            } else {
                (rng as i32 as f32) * (1.0 / 2147483648.0)
            }
        })
        .collect()
}
#[test]
fn warp_preserves_scalar_bits_and_thread_counts() {
    for (w, h) in [(1, 1), (3, 7), (31, 19), (97, 61), (1025, 17)] {
        for special in [false, true] {
            let src = input(w, h, special);
            for angle in [
                -359.7, -135.0, -0.1, 0.0, 22.375, 45.0, 90.0, 135.0, 360.0, 23592960.0,
            ] {
                let expected = warp_scalar(&src, w, h, angle);
                for workers in [1, 4] {
                    assert_eq!(
                        bits(&warp_with_workers(&src, w, h, angle, workers)),
                        bits(&expected),
                        "warp {w}x{h} angle={angle} special={special} workers={workers}"
                    );
                }
            }
        }
    }
}
#[test]
fn box_preserves_four_row_residue_and_thread_counts() {
    for w in [1, 3, 8, 31, 97] {
        for h in [1, 3, 4, 5, 9, 17] {
            for special in [false, true] {
                let src = input(w, h, special);
                for len in [1, 2, 3, 4, 5, 50, 201] {
                    for passes in [0, 1, 3] {
                        for normalize in [false, true] {
                            let expected =
                                box_horizontal_scalar(&src, w, h, len, passes, normalize, true);
                            for workers in [1, 4] {
                                let actual =
                                    box_rows(&src, w, h, len as usize, passes, normalize, workers);
                                assert_eq!(bits(&actual),bits(&expected),
                                    "box {w}x{h} len={len} passes={passes} normalize={normalize} special={special} workers={workers}");
                            }
                        }
                    }
                }
            }
        }
    }
}

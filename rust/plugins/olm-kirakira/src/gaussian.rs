//! Ordered Gaussian taps, parallel only across independent pixels/rows.
//! The scalar special three/five-tap kernels stay in filters.rs.
use crate::filters::reflect;

pub(crate) fn rows(
    src: &[f32],
    w: usize,
    h: usize,
    k: &[f32],
    fused: bool,
    color: bool,
) -> Vec<f32> {
    let workers = if w.saturating_mul(h).saturating_mul(k.len()) >= 1_000_000 {
        std::thread::available_parallelism()
            .map_or(1, usize::from)
            .min(8)
    } else {
        1
    };
    rows_with_workers(src, w, h, k, fused, color, workers)
}

pub(crate) fn rows_with_workers(
    src: &[f32],
    w: usize,
    h: usize,
    k: &[f32],
    fused: bool,
    color: bool,
    workers: usize,
) -> Vec<f32> {
    let mut out = vec![0.0; src.len()];
    let radius = k.len() / 2;
    // Reflection is computed once, including kernels wider than the image.
    let borders: Vec<_> = (0..radius)
        .map(|i| {
            (
                reflect(i as i32 - radius as i32, w as i32),
                reflect((w + i) as i32, w as i32),
            )
        })
        .collect();
    let fused_end = if !fused {
        0
    } else if color {
        w / 2 * 2
    } else {
        w / 8 * 8
    };
    let run = |input: &[f32], output: &mut [f32]| {
        let mut padded = vec![0.0; w + radius * 2];
        for (source, dest) in input.chunks_exact(w).zip(output.chunks_exact_mut(w)) {
            padded[radius..radius + w].copy_from_slice(source);
            for (i, &(left, right)) in borders.iter().enumerate() {
                padded[i] = source[left];
                padded[radius + w + i] = source[right];
            }
            convolve(&padded, dest, k, fused_end);
        }
    };
    let workers = workers.max(1).min(h);
    if workers == 1 {
        run(&src[..w * h], &mut out[..w * h]);
    } else {
        let chunk = h.div_ceil(workers) * w;
        std::thread::scope(|scope| {
            for (input, output) in src[..w * h]
                .chunks(chunk)
                .zip(out[..w * h].chunks_mut(chunk))
            {
                scope.spawn(|| run(input, output));
            }
        });
    }
    out
}

fn convolve(src: &[f32], dst: &mut [f32], k: &[f32], fused_end: usize) {
    convolve_dispatch(src, dst, k, fused_end, true);
}

// An explicit argument lets tests exercise the same fallback that machines
// without AVX2/FMA use, without mutable globals or environment switches.
fn convolve_dispatch(src: &[f32], dst: &mut [f32], k: &[f32], fused_end: usize, _allow_simd: bool) {
    #[cfg(target_arch = "x86_64")]
    if _allow_simd && std::is_x86_feature_detected!("avx2") && std::is_x86_feature_detected!("fma")
    {
        // SAFETY: CPU features checked; padded source has dst.len()+k.len()-1
        // elements, so every unaligned vector load stays inside the slice.
        unsafe { avx(src, dst, k, fused_end) };
        return;
    }
    scalar(src, dst, k, 0, fused_end);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runtime_dispatch_matches_forced_scalar_fallback() {
        let mut rng = 0x93819472u32;
        for w in [1, 2, 5, 7, 8, 9, 31, 32, 33, 97, 1025] {
            for taps in [1, 3, 5, 25, 401, 1201] {
                let k: Vec<_> = (0..taps)
                    .map(|i| (i + 1) as f32 / (taps * taps) as f32)
                    .collect();
                for special in [false, true] {
                    let src: Vec<_> = (0..w + taps - 1)
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
                                f32::from_bits((rng & 0x807fffff) | ((rng % 254 + 1) << 23))
                            }
                        })
                        .collect();
                    for end in [0, w / 8 * 8, w / 2 * 2] {
                        let mut actual = vec![0.0; w];
                        let mut expected = vec![0.0; w];
                        convolve_dispatch(&src, &mut actual, &k, end, true);
                        convolve_dispatch(&src, &mut expected, &k, end, false);
                        let bits = |v: &[f32]| v.iter().map(|f| f.to_bits()).collect::<Vec<_>>();
                        assert_eq!(
                            bits(&actual),
                            bits(&expected),
                            "w={w} taps={taps} end={end} special={special}"
                        );
                    }
                }
            }
        }
    }
}

fn scalar(src: &[f32], dst: &mut [f32], k: &[f32], start: usize, fused_end: usize) {
    for (x, out) in dst.iter_mut().enumerate().skip(start) {
        let mut v = src[x] * k[0];
        for i in 1..k.len() {
            v = if x < fused_end {
                src[x + i].mul_add(k[i], v)
            } else {
                v + src[x + i] * k[i]
            };
        }
        *out = v;
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2,fma")]
unsafe fn avx(src: &[f32], dst: &mut [f32], k: &[f32], fused_end: usize) {
    use std::arch::x86_64::*;
    let mut x = 0;
    // Four independent vectors hide FMA latency without reassociating taps.
    while x + 32 <= fused_end {
        let p = src.as_ptr().add(x);
        let weight = _mm256_set1_ps(k[0]);
        let mut a = _mm256_mul_ps(_mm256_loadu_ps(p), weight);
        let mut b = _mm256_mul_ps(_mm256_loadu_ps(p.add(8)), weight);
        let mut c = _mm256_mul_ps(_mm256_loadu_ps(p.add(16)), weight);
        let mut d = _mm256_mul_ps(_mm256_loadu_ps(p.add(24)), weight);
        for (i, &v) in k.iter().enumerate().skip(1) {
            let weight = _mm256_set1_ps(v);
            a = _mm256_fmadd_ps(_mm256_loadu_ps(p.add(i)), weight, a);
            b = _mm256_fmadd_ps(_mm256_loadu_ps(p.add(i + 8)), weight, b);
            c = _mm256_fmadd_ps(_mm256_loadu_ps(p.add(i + 16)), weight, c);
            d = _mm256_fmadd_ps(_mm256_loadu_ps(p.add(i + 24)), weight, d);
        }
        _mm256_storeu_ps(dst.as_mut_ptr().add(x), a);
        _mm256_storeu_ps(dst.as_mut_ptr().add(x + 8), b);
        _mm256_storeu_ps(dst.as_mut_ptr().add(x + 16), c);
        _mm256_storeu_ps(dst.as_mut_ptr().add(x + 24), d);
        x += 32;
    }
    while x + 8 <= dst.len() {
        if x < fused_end && x + 8 > fused_end {
            break;
        }
        let p = src.as_ptr().add(x);
        let mut v = _mm256_mul_ps(_mm256_loadu_ps(p), _mm256_set1_ps(k[0]));
        for (i, &weight) in k.iter().enumerate().skip(1) {
            let a = _mm256_loadu_ps(p.add(i));
            let b = _mm256_set1_ps(weight);
            v = if x < fused_end {
                _mm256_fmadd_ps(a, b, v)
            } else {
                _mm256_add_ps(v, _mm256_mul_ps(a, b))
            };
        }
        _mm256_storeu_ps(dst.as_mut_ptr().add(x), v);
        x += 8;
    }
    scalar(src, dst, k, x, fused_end);
}

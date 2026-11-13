//! Legacy cvSmooth arithmetic, preserving the original row/column reductions.
use olm_math::{exp, Mode};
pub fn kernel(n: usize) -> Vec<f32> {
    match n {
        1 => return vec![1.],
        3 => return vec![0.25, 0.5, 0.25],
        5 => return vec![1. / 16., 4. / 16., 6. / 16., 4. / 16., 1. / 16.],
        7 => {
            return vec![
                2. / 64.,
                7. / 64.,
                14. / 64.,
                18. / 64.,
                14. / 64.,
                7. / 64.,
                2. / 64.,
            ]
        }
        9 => {
            return vec![
                4. / 256.,
                13. / 256.,
                30. / 256.,
                51. / 256.,
                60. / 256.,
                51. / 256.,
                30. / 256.,
                13. / 256.,
                4. / 256.,
            ]
        }
        _ => (),
    }
    let sigma = n as f64 * 0.15 + 0.35;
    let factor = -0.125 / (sigma * sigma);
    let half = n / 2;
    let mut weights = vec![0.; half];
    let mut sum = 0.;
    for (i, v) in weights.iter_mut().enumerate() {
        let x = 1. - n as f64 + i as f64 * 2.;
        *v = exp(x * x * factor, Mode::Fma);
        sum += *v;
    }
    sum = sum * 2. + 1.;
    let inv = 1. / sum;
    let mut k = vec![0.; n];
    for i in 0..half {
        k[i] = (weights[i] * inv) as f32;
        k[n - i - 1] = k[i];
    }
    k[half] = inv as f32;
    k
}
fn cl(x: isize, n: usize) -> usize {
    x.clamp(0, n as isize - 1) as usize
}
#[cfg(test)]
pub fn gaussian(mat: &mut [f32], w: usize, h: usize, kx: usize, ky: usize) {
    gaussian_mode(mat, w, h, kx, ky, false);
}
// OpenCV 4.5.5 filter.simd.hpp: RowVec_32f/SymmRowSmallVec_32f and
// SymmColumnVec_32f use AVX2 FMA in complete eight-float blocks. Scalar tails
// retain separate multiply/add. Native cvSmooth fixtures cover the boundaries.
pub fn gaussian_native(mat: &mut [f32], w: usize, h: usize, kx: usize, ky: usize) {
    gaussian_mode(mat, w, h, kx, ky, true);
}
fn gaussian_mode(mat: &mut [f32], w: usize, h: usize, kx: usize, ky: usize, native: bool) {
    gaussian_mode_threads(mat, w, h, kx, ky, native, olm_core::row_workers(h, w));
}
fn gaussian_mode_threads(
    mat: &mut [f32],
    w: usize,
    h: usize,
    kx: usize,
    ky: usize,
    native: bool,
    threads: usize,
) {
    #[cfg(feature = "stage-dump")]
    let native = crate::stage_dump::native_mode(native);
    #[cfg(feature = "stage-dump")]
    let capture = crate::stage_dump::begin(mat, w, h, kx, ky, native);
    let a = kernel(kx);
    let b = kernel(ky);
    let mut tmp = vec![0.; w * h];
    olm_core::parallel_rows(&mut tmp, w, threads, |y, row| {
        for x in 0..w {
            let at = |dx: isize| mat[y * w + cl(x as isize + dx, w)];
            let fused = native && x < w / 8 * 8;
            let v = if (w == 1 && !(kx == 3 && ky == 3)) || kx == 1 {
                at(0)
            } else if kx == 3 {
                (at(-1) + at(1)) * 0.25 + at(0) * 0.5
            } else if kx == 5 {
                if fused {
                    (at(-2) + at(2)).mul_add(a[4], at(0).mul_add(a[2], (at(-1) + at(1)) * a[3]))
                } else {
                    (at(0) * a[2] + (at(-1) + at(1)) * a[3]) + (at(-2) + at(2)) * a[4]
                }
            } else {
                let mut v = 0.;
                for i in 0..kx {
                    let sample = at(i as isize - kx as isize / 2);
                    v = if fused {
                        sample.mul_add(a[i], v)
                    } else {
                        v + sample * a[i]
                    };
                }
                v
            };
            row[x] = v;
        }
    })
    .expect("validated Gaussian plane");
    #[cfg(feature = "stage-dump")]
    crate::stage_dump::middle(&mut tmp, &capture);
    for y in 0..h {
        let mut vector_end = 0;
        #[cfg(target_arch = "x86_64")]
        if native
            && std::arch::is_x86_feature_detected!("avx2")
            && std::arch::is_x86_feature_detected!("fma")
        {
            // Geometry and kernel lengths were established by the scalar driver.
            vector_end = unsafe { gaussian_column_avx2(&tmp, mat, w, h, y, kx, ky, &b) };
        }
        for x in vector_end..w {
            let at = |dy: isize| tmp[cl(y as isize + dy, h) * w + x];
            let mut v = at(0);
            if (h != 1 || (kx == 3 && ky == 3)) && ky != 1 {
                if ky == 3 {
                    v = (at(-1) + at(1)) * 0.25 + v * 0.5;
                } else {
                    v *= b[ky / 2];
                    for i in 1..=ky / 2 {
                        let sample = at(-(i as isize)) + at(i as isize);
                        v = if native && x < w / 8 * 8 {
                            sample.mul_add(b[ky / 2 + i], v)
                        } else {
                            v + sample * b[ky / 2 + i]
                        };
                    }
                }
            }
            mat[y * w + x] = v;
        }
    }
    #[cfg(feature = "stage-dump")]
    crate::stage_dump::end(mat, capture);
}
// Same eight-lane FMA boundary as the native column profile; tails stay scalar.
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2,fma")]
unsafe fn gaussian_column_avx2(
    src: &[f32],
    dst: &mut [f32],
    w: usize,
    h: usize,
    y: usize,
    kx: usize,
    ky: usize,
    b: &[f32],
) -> usize {
    use std::arch::x86_64::*;
    let end = w / 8 * 8;
    for x in (0..end).step_by(8) {
        let at = |dy: isize| _mm256_loadu_ps(src.as_ptr().add(cl(y as isize + dy, h) * w + x));
        let mut v = at(0);
        if (h != 1 || (kx == 3 && ky == 3)) && ky != 1 {
            if ky == 3 {
                v = _mm256_add_ps(
                    _mm256_mul_ps(_mm256_add_ps(at(-1), at(1)), _mm256_set1_ps(0.25)),
                    _mm256_mul_ps(v, _mm256_set1_ps(0.5)),
                );
            } else {
                v = _mm256_mul_ps(v, _mm256_set1_ps(b[ky / 2]));
                for i in 1..=ky / 2 {
                    let sample = _mm256_add_ps(at(-(i as isize)), at(i as isize));
                    v = _mm256_fmadd_ps(sample, _mm256_set1_ps(b[ky / 2 + i]), v);
                }
            }
        }
        _mm256_storeu_ps(dst.as_mut_ptr().add(y * w + x), v);
    }
    end
}

pub fn box_blur(mat: &mut [f32], w: usize, h: usize, kx: usize, ky: usize) {
    let area = kx as f64 * ky as f64;
    let rx = kx / 2;
    let ry = ky / 2;
    // Same representability proof as box_sum_is_exact in DistanceFilters.inc.
    let mut quantum = 0i32;
    let mut maximum = 0f64;
    let mut finite = true;
    for &v in mat.iter() {
        if !v.is_finite() {
            finite = false;
            break;
        }
        let a = v.abs();
        if a == 0. {
            continue;
        }
        let exponent = if a.is_normal() {
            ((a.to_bits() >> 23) & 255) as i32 - 126
        } else {
            let b = a * 16777216.;
            ((b.to_bits() >> 23) & 255) as i32 - 150
        };
        quantum = quantum.min(exponent - 24);
        maximum = maximum.max(a as f64);
    }
    let taps = kx.max(ky) as u64 * kx.max(ky) as u64;
    let exact = finite && maximum * 2f64.powi(-quantum) <= ((1u64 << 53) / taps) as f64;
    if !exact {
        let src = mat.to_vec();
        for y in 0..h {
            for x in 0..w {
                let mut sum = 0.;
                for j in 0..ky {
                    for i in 0..kx {
                        sum += src[cl(y as isize + j as isize - ry as isize, h) * w
                            + cl(x as isize + i as isize - rx as isize, w)]
                            as f64;
                    }
                }
                mat[y * w + x] = (sum / area) as f32;
            }
        }
        return;
    }
    let mut rows = vec![0f64; w * h];
    for y in 0..h {
        let src = &mat[y * w..(y + 1) * w];
        let mut sum = src[0] as f64 * rx as f64;
        for x in 0..=rx.min(w - 1) {
            sum += src[x] as f64;
        }
        if rx >= w {
            sum += src[w - 1] as f64 * (rx - w + 1) as f64;
        }
        rows[y * w] = sum;
        for x in 1..w {
            sum -= src[x.saturating_sub(rx + 1)] as f64;
            sum += src[(x + rx).min(w - 1)] as f64;
            rows[y * w + x] = sum;
        }
    }
    for x in 0..w {
        let mut sum = rows[x] * ry as f64;
        for y in 0..=ry.min(h - 1) {
            sum += rows[y * w + x];
        }
        if ry >= h {
            sum += rows[(h - 1) * w + x] * (ry - h + 1) as f64;
        }
        mat[x] = (sum / area) as f32;
        for y in 1..h {
            sum -= rows[y.saturating_sub(ry + 1) * w + x];
            sum += rows[(y + ry).min(h - 1) * w + x];
            mat[y * w + x] = (sum / area) as f32;
        }
    }
}
pub fn median(mat: &mut [f32], w: usize, h: usize, n: usize) {
    if n <= 1 {
        return;
    }
    let src = mat.to_vec();
    let r = n / 2;
    if n * n > src.len() * 4 {
        let mut order: Vec<_> = (0..src.len()).collect();
        order.sort_unstable_by(|&a, &b| src[a].total_cmp(&src[b]));
        let mult = |s: usize, c: usize, len: usize| -> u64 {
            if len == 1 {
                n as u64
            } else if s == 0 {
                (r as isize - c as isize + 1).max(0) as u64
            } else if s == len - 1 {
                (r as isize - (len - 1 - c) as isize + 1).max(0) as u64
            } else {
                (s.abs_diff(c) <= r) as u64
            }
        };
        for y in 0..h {
            for x in 0..w {
                let mut count = 0u64;
                for &i in &order {
                    count += mult(i % w, x, w) * mult(i / w, y, h);
                    if count > (n as u64 * n as u64) / 2 {
                        mat[y * w + x] = src[i];
                        break;
                    }
                }
            }
        }
        return;
    }
    let mut window = vec![0.; n * n];
    for y in 0..h {
        for x in 0..w {
            for j in 0..n {
                for i in 0..n {
                    window[j * n + i] = src[cl(y as isize + j as isize - r as isize, h) * w
                        + cl(x as isize + i as isize - r as isize, w)];
                }
            }
            let (_, mid, _) = window.select_nth_unstable_by(n * n / 2, |a, b| a.total_cmp(b));
            mat[y * w + x] = *mid;
        }
    }
}

// Diagnostic access to the retained historical arithmetic; no default-build item.
#[cfg(feature = "stage-dump")]
pub(crate) fn stage_dump_gaussian_sse(mat: &mut [f32], w: usize, h: usize, kx: usize, ky: usize) {
    gaussian_mode(mat, w, h, kx, ky, false);
}

#[cfg(all(test, target_arch = "x86_64"))]
mod simd_tests {
    use super::*;
    #[test]
    fn column_matches_scalar_bits() {
        if !std::arch::is_x86_feature_detected!("avx2")
            || !std::arch::is_x86_feature_detected!("fma")
        {
            return;
        }
        let mut seed = 0x12345678u32;
        for w in [1, 7, 8, 9, 15, 16, 17, 31, 64, 127] {
            for h in [1, 2, 7, 19] {
                let src: Vec<f32> = (0..w * h)
                    .map(|i| {
                        seed ^= seed << 13;
                        seed ^= seed >> 17;
                        seed ^= seed << 5;
                        match i % 17 {
                            0 => 0.0,
                            1 => -0.0,
                            2 => f32::from_bits(1),
                            3 => f32::MAX,
                            _ => (seed as i32 as f32) * (1.0 / 2147483648.0),
                        }
                    })
                    .collect();
                for ky in [1, 3, 5, 7, 9, 13, 25] {
                    let b = kernel(ky);
                    let mut dst = vec![123.0; w * h];
                    for y in 0..h {
                        let end =
                            unsafe { gaussian_column_avx2(&src, &mut dst, w, h, y, 3, ky, &b) };
                        for x in 0..end {
                            let at = |dy: isize| src[cl(y as isize + dy, h) * w + x];
                            let mut v = at(0);
                            if (h != 1 || ky == 3) && ky != 1 {
                                if ky == 3 {
                                    v = (at(-1) + at(1)) * 0.25 + v * 0.5;
                                } else {
                                    v *= b[ky / 2];
                                    for i in 1..=ky / 2 {
                                        v = (at(-(i as isize)) + at(i as isize))
                                            .mul_add(b[ky / 2 + i], v);
                                    }
                                }
                            }
                            assert_eq!(
                                dst[y * w + x].to_bits(),
                                v.to_bits(),
                                "{w} {h} {ky} {y} {x}"
                            );
                        }
                        assert!(dst[y * w + end..(y + 1) * w].iter().all(|&v| v == 123.0));
                    }
                }
            }
        }
    }
}

#[cfg(test)]
mod parallel_tests {
    use super::*;
    #[test]
    fn gaussian_rows_match_one_and_seven_workers() {
        let (w, h) = (257, 521);
        let source: Vec<f32> = (0..w * h)
            .map(|i| ((i * 7919 % 65536) as f32 - 32768.0) / 32768.0)
            .collect();
        for native in [false, true] {
            for (kx, ky) in [(3, 3), (5, 7), (13, 9)] {
                let mut a = source.clone();
                let mut b = source.clone();
                gaussian_mode_threads(&mut a, w, h, kx, ky, native, 1);
                gaussian_mode_threads(&mut b, w, h, kx, ky, native, 7);
                assert!(a.iter().zip(b).all(|(a, b)| a.to_bits() == b.to_bits()));
            }
        }
    }
}

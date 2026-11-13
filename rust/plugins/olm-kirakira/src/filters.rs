//! Ordered filters from KiraFilters.inc and core/kirakira_*.h.
use olm_math::{self as math, Mode::Fma};
#[cfg(test)]
#[path = "filter_tests.rs"]
mod row_tests;
pub fn reflect(mut x: i32, n: i32) -> usize {
    if n <= 1 {
        return 0;
    }
    // Equivalent to repeated REFLECT_101 folds, without length-dependent loops.
    let period = 2 * (n - 1);
    x %= period;
    if x < 0 {
        x = -x;
    }
    if x >= n {
        x = period - x;
    }
    x as usize
}
pub fn crop(src: &[f32], sw: usize, sh: usize, dw: usize, dh: usize) -> Vec<f32> {
    let mut out = vec![0.0; dw * dh];
    let x0 = (sw as f32 * 0.5) as i32 - dw as i32 / 2;
    let y0 = (sh as f32 * 0.5) as i32 - dh as i32 / 2;
    for y in 0..dh {
        let sy = y as i32 + y0;
        if sy < 0 || sy >= sh as i32 {
            continue;
        }
        for x in 0..dw {
            let sx = x as i32 + x0;
            if sx >= 0 && sx < sw as i32 {
                out[y * dw + x] = src[sy as usize * sw + sx as usize];
            }
        }
    }
    out
}
pub fn warp(src: &[f32], w: usize, h: usize, angle: f64) -> Vec<f32> {
    warp_with_workers(src, w, h, angle, crate::parallel::workers(w * h))
}

fn warp_with_workers(src: &[f32], w: usize, h: usize, angle: f64, workers: usize) -> Vec<f32> {
    // Preserve the retained scalar NaN-payload selection when input is nonfinite.
    if src.iter().any(|v| !v.is_finite()) {
        return warp_scalar(src, w, h, angle);
    }
    let radians = angle * std::f64::consts::PI / 180.0;
    let alpha = math::cos(radians, Fma);
    let beta = math::sin(radians, Fma);
    let cx = w as f64 * 0.5;
    let cy = h as f64 * 0.5;
    let m02 = (1.0 - alpha) * cx - beta * cy;
    let m12 = beta * cx + (1.0 - alpha) * cy;
    let determinant = alpha * alpha + beta * beta;
    let i00 = alpha / determinant;
    let i01 = -beta / determinant;
    let i02 = (beta * m12 - alpha * m02) / determinant;
    let i10 = beta / determinant;
    let i11 = alpha / determinant;
    let i12 = (-beta * m02 - alpha * m12) / determinant;
    let mut out = vec![0.0; w * h];
    let sample = |x: i32, y: i32| {
        if x < 0 || y < 0 || x >= w as i32 || y >= h as i32 {
            0.0
        } else {
            src[y as usize * w + x as usize]
        }
    };
    // Preserve the two multiplications before rounding; factoring 1024 into
    // the coefficient would change rounding at some coordinates.
    let deltas: Vec<_> = (0..w)
        .map(|x| {
            (
                (i00 * x as f64 * 1024.0).round_ties_even() as i32,
                (i10 * x as f64 * 1024.0).round_ties_even() as i32,
            )
        })
        .collect();
    crate::parallel::chunks(&mut out, w.max(1), workers, |start, chunk| {
        for (row, output) in chunk.chunks_mut(w).enumerate() {
            let y = start / w + row;
            let bx = ((i01 * y as f64 + i02) * 1024.0).round_ties_even() as i32 + 16;
            let by = ((i11 * y as f64 + i12) * 1024.0).round_ties_even() as i32 + 16;
            for x in 0..w {
                let xf = (bx + deltas[x].0) >> 5;
                let yf = (by + deltas[x].1) >> 5;
                let x0 = xf >> 5;
                let y0 = yf >> 5;
                let fx = xf & 31;
                let fy = yf & 31;
                let w00 = ((32 - fx) * (32 - fy)) as f32 * (1.0 / 1024.0);
                let w10 = (fx * (32 - fy)) as f32 * (1.0 / 1024.0);
                let w01 = ((32 - fx) * fy) as f32 * (1.0 / 1024.0);
                let w11 = (fx * fy) as f32 * (1.0 / 1024.0);
                let mut v = sample(x0 + 1, y0) * w10;
                v += sample(x0, y0) * w00;
                v += sample(x0, y0 + 1) * w01;
                v += sample(x0 + 1, y0 + 1) * w11;
                output[x] = v;
            }
        }
    });
    out
}
fn warp_scalar(src: &[f32], w: usize, h: usize, angle: f64) -> Vec<f32> {
    let radians = angle * std::f64::consts::PI / 180.0;
    let alpha = math::cos(radians, Fma);
    let beta = math::sin(radians, Fma);
    let cx = w as f64 * 0.5;
    let cy = h as f64 * 0.5;
    let m02 = (1.0 - alpha) * cx - beta * cy;
    let m12 = beta * cx + (1.0 - alpha) * cy;
    let determinant = alpha * alpha + beta * beta;
    let i00 = alpha / determinant;
    let i01 = -beta / determinant;
    let i02 = (beta * m12 - alpha * m02) / determinant;
    let i10 = beta / determinant;
    let i11 = alpha / determinant;
    let i12 = (-beta * m02 - alpha * m12) / determinant;
    let mut out = vec![0.0; w * h];
    let sample = |x: i32, y: i32| {
        if x < 0 || y < 0 || x >= w as i32 || y >= h as i32 {
            0.0
        } else {
            src[y as usize * w + x as usize]
        }
    };
    for y in 0..h {
        let bx = ((i01 * y as f64 + i02) * 1024.0).round_ties_even() as i32 + 16;
        let by = ((i11 * y as f64 + i12) * 1024.0).round_ties_even() as i32 + 16;
        for x in 0..w {
            let xf = (bx + (i00 * x as f64 * 1024.0).round_ties_even() as i32) >> 5;
            let yf = (by + (i10 * x as f64 * 1024.0).round_ties_even() as i32) >> 5;
            let x0 = xf >> 5;
            let y0 = yf >> 5;
            let fx = xf & 31;
            let fy = yf & 31;
            let w00 = ((32 - fx) * (32 - fy)) as f32 * (1.0 / 1024.0);
            let w10 = (fx * (32 - fy)) as f32 * (1.0 / 1024.0);
            let w01 = ((32 - fx) * fy) as f32 * (1.0 / 1024.0);
            let w11 = (fx * fy) as f32 * (1.0 / 1024.0);
            let mut v = sample(x0 + 1, y0) * w10;
            v += sample(x0, y0) * w00;
            v += sample(x0, y0 + 1) * w01;
            v += sample(x0 + 1, y0 + 1) * w11;
            out[y * w + x] = v;
        }
    }
    out
}

pub fn box_horizontal(
    src: &[f32],
    w: usize,
    h: usize,
    len: i32,
    passes: usize,
    normalize: bool,
    recovered: bool,
) -> Vec<f32> {
    if recovered && len > 0 && w > 0 && h > 0 {
        return box_rows(
            src,
            w,
            h,
            len as usize,
            passes,
            normalize,
            crate::parallel::workers(w * h),
        );
    }
    box_horizontal_scalar(src, w, h, len, passes, normalize, recovered)
}

fn box_rows(
    input: &[f32],
    w: usize,
    h: usize,
    len: usize,
    passes: usize,
    normalize: bool,
    workers: usize,
) -> Vec<f32> {
    let indices: Vec<_> = (0..w + len - 1)
        .map(|x| reflect(x as i32 - (len / 2) as i32, w as i32))
        .collect();
    let scale = if normalize { 1.0 / len as f64 } else { 1.0 };
    let mut src = input.to_vec();
    let mut dst = vec![0.0; src.len()];
    for _ in 0..passes {
        // The recovered filter carries rounding residue across groups of four
        // rows. Never split one of these groups between workers.
        crate::parallel::chunks(&mut dst[..w * h], w * 4, workers, |start, chunk| {
            let mut column = vec![0.0f64; w];
            let mut padded = vec![0.0f32; indices.len()];
            for (row, out) in chunk.chunks_mut(w).enumerate() {
                if row % 4 == 0 {
                    column.fill(0.0);
                }
                let source = &src[start + row * w..start + (row + 1) * w];
                for (v, &i) in padded.iter_mut().zip(&indices) {
                    *v = source[i];
                }
                let mut sum = 0.0f64;
                for &v in &padded[..len] {
                    sum += v as f64;
                }
                for x in 0..w {
                    if len == 3 || len == 5 {
                        sum = padded[x] as f64;
                        for &v in &padded[x + 1..x + len] {
                            sum += v as f64;
                        }
                    }
                    let total = column[x] + sum;
                    out[x] = (total * scale) as f32;
                    column[x] = total - sum;
                    if x + 1 < w && len != 3 && len != 5 {
                        sum += padded[x + len] as f64 - padded[x] as f64;
                    }
                }
            }
        });
        std::mem::swap(&mut src, &mut dst);
    }
    src
}

fn box_horizontal_scalar(
    src: &[f32],
    w: usize,
    h: usize,
    len: i32,
    passes: usize,
    normalize: bool,
    recovered: bool,
) -> Vec<f32> {
    let mut src = src.to_vec();
    let left = len / 2;
    let right = len - left - 1;
    for _ in 0..passes {
        let mut dst = vec![0.0; src.len()];
        let mut column = vec![0.0f64; w];
        for y in 0..h {
            if y % 4 == 0 {
                column.fill(0.0);
            }
            let mut sum = 0.0f64;
            for k in -left..=right {
                sum += src[y * w + reflect(k, w as i32)] as f64;
            }
            let scale = if normalize { 1.0 / len as f64 } else { 1.0 };
            for x in 0..w {
                if !recovered || len == 3 || len == 5 {
                    sum = src[y * w + reflect(x as i32 - left, w as i32)] as f64;
                    for k in -left + 1..=right {
                        sum += src[y * w + reflect(x as i32 + k, w as i32)] as f64;
                    }
                }
                if recovered {
                    let total = column[x] + sum;
                    dst[y * w + x] = (total * scale) as f32;
                    column[x] = total - sum;
                } else {
                    dst[y * w + x] = (sum / len as f64) as f32;
                }
                if recovered && x + 1 < w && len != 3 && len != 5 {
                    sum += src[y * w + reflect(x as i32 + right + 1, w as i32)] as f64
                        - src[y * w + reflect(x as i32 - left, w as i32)] as f64;
                }
            }
        }
        src = dst;
    }
    src
}
pub fn box_highlight(
    input: &[f32],
    w: usize,
    h: usize,
    k: i32,
    passes: usize,
    normalize: bool,
) -> Vec<f32> {
    let mut src = input.to_vec();
    if k <= 1 {
        return src;
    }
    let left = k / 2;
    let right = k - left - 1;
    for _ in 0..passes {
        let mut rows = vec![0.0f64; src.len()];
        for y in 0..h {
            let mut sum = 0.0f64;
            for dx in -left..=right {
                sum += src[y * w + reflect(dx, w as i32)] as f64;
            }
            for x in 0..w {
                if k == 3 || k == 5 {
                    sum = src[y * w + reflect(x as i32 - left, w as i32)] as f64;
                    for dx in -left + 1..=right {
                        sum += src[y * w + reflect(x as i32 + dx, w as i32)] as f64;
                    }
                }
                rows[y * w + x] = sum;
                if x + 1 < w && k != 3 && k != 5 {
                    sum += src[y * w + reflect(x as i32 + right + 1, w as i32)] as f64
                        - src[y * w + reflect(x as i32 - left, w as i32)] as f64;
                }
            }
        }
        let mut out = vec![0.0; src.len()];
        let scale = if normalize {
            1.0 / (k as f64 * k as f64)
        } else {
            1.0
        };
        for x in 0..w {
            let mut sum = 0.0f64;
            for dy in -left..right {
                sum += rows[reflect(dy, h as i32) * w + x];
            }
            for y in 0..h {
                let total = sum + rows[reflect(y as i32 + right, h as i32) * w + x];
                out[y * w + x] = (total * scale) as f32;
                sum = total - rows[reflect(y as i32 - left, h as i32) * w + x];
            }
        }
        src = out;
    }
    src
}
fn gaussian_kernel(radius: i32, sigma: f64, highlight: bool) -> Vec<f32> {
    let scale = -0.5 / (sigma * sigma);
    let mut sum = 0.0;
    let weights: Vec<f64> = (-radius..=radius)
        .map(|x| {
            let v = math::exp(
                if highlight {
                    -0.5 * x as f64 * x as f64 / (sigma * sigma)
                } else {
                    x as f64 * x as f64 * scale
                },
                Fma,
            );
            sum += v;
            v
        })
        .collect();
    let kernel = weights.iter().map(|v| (v / sum) as f32).collect();
    if highlight {
        match radius {
            1 => vec![0.25, 0.5, 0.25],
            2 => vec![0.0625, 0.25, 0.375, 0.25, 0.0625],
            3 => vec![
                0.03125, 0.109375, 0.21875, 0.28125, 0.21875, 0.109375, 0.03125,
            ],
            4 => [4.0, 13.0, 30.0, 51.0, 60.0, 51.0, 30.0, 13.0, 4.0]
                .map(|v| v / 256.0)
                .to_vec(),
            _ => kernel,
        }
    } else {
        kernel
    }
}
pub fn gaussian_horizontal(src: &[f32], w: usize, h: usize, len: i32) -> Vec<f32> {
    gaussian_horizontal_profile(src, w, h, len, false, false)
}
pub fn gaussian_horizontal_profile(
    src: &[f32],
    w: usize,
    h: usize,
    len: i32,
    fused: bool,
    color: bool,
) -> Vec<f32> {
    let radius = len * 2;
    let k = gaussian_kernel(radius, len as f64 * 0.5, false);
    gaussian_rows(src, w, h, radius, &k, len == 1, false, fused, color)
}
fn gaussian_rows(
    src: &[f32],
    w: usize,
    h: usize,
    radius: i32,
    k: &[f32],
    small: bool,
    highlight: bool,
    fused: bool,
    color: bool,
) -> Vec<f32> {
    if w > 0 && h > 0 && !(highlight && w == 1) && !(small && radius <= 2) {
        return crate::gaussian::rows(src, w, h, k, fused, color);
    }
    gaussian_rows_scalar(src, w, h, radius, k, small, highlight, fused, color)
}

#[allow(clippy::too_many_arguments)] // Retained reference signature matches gaussian_rows.
fn gaussian_rows_scalar(
    src: &[f32],
    w: usize,
    h: usize,
    radius: i32,
    k: &[f32],
    small: bool,
    highlight: bool,
    fused: bool,
    color: bool,
) -> Vec<f32> {
    let mut out = vec![0.0; src.len()];
    for y in 0..h {
        for x in 0..w {
            if highlight && w == 1 {
                out[y] = src[y];
                continue;
            }
            let at = |dx: i32| src[y * w + reflect(x as i32 + dx, w as i32)];
            // Native opt_AVX2 RowVec_32f at RVA 0x1319472 processes floor(w/8)*8
            // scalar pixels with VFMADD231PS; RowFilter's tail is nonfused. The
            // four-component owner uses its fused component path. C++ baseline
            // tests retain four-lane nonfused ordering via fused=false.
            let vector_width = if fused {
                if color {
                    w / 2 * 2
                } else {
                    w / 8 * 8
                }
            } else {
                w / 4 * 4
            };
            let use_fma = fused && x < vector_width;
            let add = |a: f32, b: f32, c: f32| if use_fma { b.mul_add(c, a) } else { a + b * c };
            let value = if small && radius == 1 {
                add(at(0) * k[1], at(-1) + at(1), k[0])
            } else if small && radius == 2 {
                let pair = at(-1) + at(1);
                let v = if x < vector_width {
                    add(pair * k[1], at(0), k[2])
                } else {
                    add(at(0) * k[2], pair, k[1])
                };
                add(v, at(-2) + at(2), k[0])
            } else {
                let mut v = at(-radius) * k[0];
                for i in 1..k.len() {
                    v = add(v, at(i as i32 - radius), k[i]);
                }
                v
            };
            out[y * w + x] = value;
        }
    }
    out
}
pub fn gaussian_highlight(src: &[f32], w: usize, h: usize, radius: i32) -> Vec<f32> {
    gaussian_highlight_profile(src, w, h, radius, false, false)
}

#[cfg(test)]
mod gaussian_tests {
    use super::*;

    #[test]
    fn ordered_rows_match_scalar_bits_and_thread_counts() {
        let mut rng = 0x82371491u32;
        for w in [
            1, 2, 3, 5, 7, 8, 9, 15, 16, 17, 31, 32, 33, 63, 97, 257, 1023, 1024, 1025,
        ] {
            let h = 9;
            let src: Vec<_> = (0..w * h)
                .map(|i| {
                    rng ^= rng << 13;
                    rng ^= rng >> 17;
                    rng ^= rng << 5;
                    match i % 13 {
                        0 => 0.0,
                        1 => -0.0,
                        2 => f32::from_bits(1),
                        3 => -f32::from_bits(0x007fffff),
                        4 => f32::MAX,
                        5 => -f32::MAX,
                        _ => f32::from_bits((rng & 0x807fffff) | ((rng % 254 + 1) << 23)),
                    }
                })
                .collect();
            for radius in [0, 1, 2, 3, 4, 12, 200, 600] {
                let k = gaussian_kernel(radius, (radius.max(1) as f64) * 0.25, false);
                for fused in [false, true] {
                    for color in [false, true] {
                        let expected = gaussian_rows_scalar(
                            &src, w, h, radius, &k, false, false, fused, color,
                        );
                        for workers in [1, 4] {
                            let actual = crate::gaussian::rows_with_workers(
                                &src, w, h, &k, fused, color, workers,
                            );
                            assert_eq!(actual.iter().map(|v| v.to_bits()).collect::<Vec<_>>(), expected.iter().map(|v| v.to_bits()).collect::<Vec<_>>(), "w={w} radius={radius} fused={fused} color={color} workers={workers}");
                        }
                    }
                }
            }
        }
    }
}
pub fn gaussian_highlight_profile(
    src: &[f32],
    w: usize,
    h: usize,
    radius: i32,
    fused: bool,
    color: bool,
) -> Vec<f32> {
    let k = gaussian_kernel(radius, 0.3 * (radius - 1) as f64 + 0.8, true);
    let rows = gaussian_rows(src, w, h, radius, &k, true, true, fused, color);
    let mut out = vec![0.0; src.len()];
    for y in 0..h {
        for x in 0..w {
            if h == 1 {
                out[x] = rows[x];
                continue;
            }
            let mut v = rows[y * w + x] * k[radius as usize];
            for j in 1..=radius {
                let pair = rows[reflect(y as i32 - j, h as i32) * w + x]
                    + rows[reflect(y as i32 + j, h as i32) * w + x];
                v = if fused && x < if color { w / 2 * 2 } else { w / 8 * 8 } {
                    pair.mul_add(k[(radius + j) as usize], v)
                } else {
                    v + pair * k[(radius + j) as usize]
                };
            }
            out[y * w + x] = v;
        }
    }
    out
}
pub fn mode4(src: &[f32], w: usize, h: usize, radius: i32) -> Vec<f32> {
    let d = radius + 1;
    let pw = radius as f32 / d as f32;
    let sw = radius as f32 / (d * d) as f32;
    let mut dst = vec![0.0; src.len()];
    for y in 0..h {
        let mut a = dst[y * w];
        for x in 1..w {
            a = sw * src[y * w + x - 1] + pw * a;
            dst[y * w + x] = a;
        }
        a = 0.0;
        for x in (0..w.saturating_sub(1)).rev() {
            a = sw * src[y * w + x + 1] + pw * a;
            dst[y * w + x] += a;
        }
    }
    dst
}
pub fn ray(
    src: &[f32],
    w: usize,
    h: usize,
    len: i32,
    angle: f64,
    mode: i32,
    normalize: bool,
    recovered: bool,
) -> Vec<f32> {
    ray_profile(src, w, h, len, angle, mode, normalize, recovered, false)
}
pub fn ray_profile(
    src: &[f32],
    w: usize,
    h: usize,
    len: i32,
    angle: f64,
    mode: i32,
    normalize: bool,
    recovered: bool,
    fused: bool,
) -> Vec<f32> {
    let (s, c) = crate::trig::extent_sincos(angle);
    let rw = crate::trig::extent(w as i32, h as i32, c.abs(), s.abs()) as usize;
    let rh = crate::trig::extent(h as i32, w as i32, c.abs(), s.abs()) as usize;
    let centered = crop(src, w, h, rw, rh);
    let forward = warp(&centered, rw, rh, angle);
    let filtered = match mode {
        3 => gaussian_horizontal_profile(&forward, rw, rh, len, fused, !normalize),
        4 => {
            if rw < 9 || rh < 7 {
                return src.to_vec();
            }
            mode4(&forward, rw, rh, len)
        }
        _ => box_horizontal(
            &forward,
            rw,
            rh,
            len,
            if mode == 1 { 1 } else { 3 },
            normalize,
            recovered,
        ),
    };
    crop(&warp(&filtered, rw, rh, -angle), rw, rh, w, h)
}
pub fn resize(
    src: &[[f32; 4]],
    sw: usize,
    sh: usize,
    dw: usize,
    dh: usize,
    linear: bool,
) -> Vec<[f32; 4]> {
    resize_profile(src, sw, sh, dw, dh, linear, false)
}
pub fn resize_profile(
    src: &[[f32; 4]],
    sw: usize,
    sh: usize,
    dw: usize,
    dh: usize,
    linear: bool,
    fused: bool,
) -> Vec<[f32; 4]> {
    if sw == dw && sh == dh {
        return src.to_vec();
    }
    let mut out = vec![[0.0; 4]; dw * dh];
    let sx = sw as f64 / dw as f64;
    let sy = sh as f64 / dh as f64;
    let blend =
        |a: [f32; 4], b: [f32; 4], t: f32| std::array::from_fn(|c| a[c] + (b[c] - a[c]) * t);
    let inner = |a: [f32; 4], b: [f32; 4], t: f32| {
        if fused {
            std::array::from_fn(|c| (b[c] - a[c]).mul_add(t, a[c]))
        } else {
            blend(a, b, t)
        }
    };
    for y in 0..dh {
        for x in 0..dw {
            if !linear {
                out[y * dw + x] = src[(y * sh / dh) * sw + x * sw / dw];
                continue;
            }
            let cy = (y as f64 + 0.5) * sy - 0.5;
            let cx = (x as f64 + 0.5) * sx - 0.5;
            let mut iy = cy.floor() as i32;
            let mut ix = cx.floor() as i32;
            let yb = iy < 0 || iy >= sh as i32 - 1;
            let xb = ix < 0 || ix >= sw as i32 - 1;
            let mut fy = (cy - iy as f64) as f32;
            let mut fx = (cx - ix as f64) as f32;
            if iy < 0 {
                iy = 0;
                fy = 0.0;
            }
            if iy >= sh as i32 - 1 {
                iy = sh as i32 - 1;
                fy = 0.0;
            }
            if ix < 0 {
                ix = 0;
                fx = 0.0;
            }
            if ix >= sw as i32 - 1 {
                ix = sw as i32 - 1;
                fx = 0.0;
            }
            let y0 = iy as usize;
            let y1 = (y0 + 1).min(sh - 1);
            let x0 = ix as usize;
            let x1 = if xb { x0 } else { x0 + 1 };
            out[y * dw + x] = if yb {
                inner(src[y0 * sw + x0], src[y0 * sw + x1], fx)
            } else if xb {
                inner(src[y0 * sw + x0], src[y1 * sw + x0], fy)
            } else {
                inner(
                    inner(src[y0 * sw + x0], src[y0 * sw + x1], fx),
                    inner(src[y1 * sw + x0], src[y1 * sw + x1], fx),
                    fy,
                )
            };
        }
    }
    out
}

//! Embedded IPP exponential and bilateral reductions.
#![allow(non_upper_case_globals)]
include!("bilateral_table.rs");
include!("bilateral_fma_table.rs");
const kScalarRoundBias: f64 = 6755399441055744.;
const kVectorRoundBias: f32 = 12582912.;
pub fn scalar_exp(x: f32) -> f32 {
    if x.abs() < kScalarExpTiny {
        return 1. + x;
    }
    let scaled = x as f64 * kScalarLog2Scale;
    let biased = kScalarRoundBias + scaled;
    let n = biased.to_bits() as u32 as i32;
    let residual = scaled + (kScalarRoundBias - biased);
    let bits = POWERS[(n as u32 & 255) as usize].wrapping_add(((n >> 8) as i64 as u64) << 52);
    let value = f64::from_bits(bits);
    let quadratic = (kScalarExpQuadratic * residual) * residual;
    let linear = kScalarExpLinear * residual + 1.;
    (value * (linear + quadratic)) as f32
}
pub fn vector_exp(x: f32) -> f32 {
    let scaled = x * kVectorLog2E;
    let biased = scaled + kVectorRoundBias;
    let n = biased - kVectorRoundBias;
    let hi = n * kVectorLn2High;
    let lo = n * kVectorLn2Low;
    let residual = (x - hi) - lo;
    let mut poly = kVectorExpC5 * residual + kVectorExpC4;
    poly = poly * residual + kVectorExpC3;
    poly = poly * residual + kVectorExpC2;
    poly = poly * residual + kVectorExpC1;
    poly = poly * residual + 1.;
    f32::from_bits(poly.to_bits().wrapping_add(biased.to_bits() << 23))
}
fn weight(sample: f32, center: f32, vector: bool) -> f32 {
    let d = sample - center;
    let exponent = if vector {
        (d * d) * -0.5
    } else {
        (-0.5 * d) * d
    };
    if exponent > -25. {
        if vector {
            vector_exp(exponent)
        } else {
            scalar_exp(exponent)
        }
    } else {
        0.
    }
}
#[cfg(test)]
pub fn blur(mat: &mut [f32], w: usize, h: usize, r: usize, scalar: bool) {
    blur_mode(mat, w, h, r, scalar, false);
}
pub fn blur_mode(mat: &mut [f32], w: usize, h: usize, r: usize, scalar: bool, fma: bool) {
    let source = mat.to_vec();
    let at = |x: usize, y: usize, dx: isize, dy: isize| {
        source[(y as isize + dy).clamp(0, h as isize - 1) as usize * w
            + (x as isize + dx).clamp(0, w as isize - 1) as usize]
    };
    if r == 1 && fma {
        let spatial = fma_exp(-0.5);
        for y in 0..h {
            for x in 0..w {
                let c = at(x, y, 0, 0);
                let vector = w >= 16 && h >= 3 && (y == 0 || y == h - 1 || (x > 0 && x < w - 1));
                let v = [
                    at(x, y, -1, 0),
                    at(x, y, 0, -1),
                    at(x, y, 1, 0),
                    at(x, y, 0, 1),
                ];
                let wt = v.map(|v| weight_fma(v, c, vector));
                let (num, den) = if vector {
                    let mut n = v[0] * wt[0];
                    let mut d = wt[0] + wt[1];
                    n = v[1].mul_add(wt[1], n);
                    n = v[2].mul_add(wt[2], n);
                    d = wt[2] + d;
                    n = v[3].mul_add(wt[3], n);
                    d = wt[3] + d;
                    (n, d)
                } else {
                    (
                        wt[0].mul_add(v[0], v[2] * wt[2]) + wt[1].mul_add(v[1], v[3] * wt[3]),
                        (wt[0] + wt[1]) + (wt[2] + wt[3]),
                    )
                };
                mat[y * w + x] = num.mul_add(spatial, c) / den.mul_add(spatial, 1.);
            }
        }
        return;
    }
    if r == 1 {
        let spatial = if fma { fma_exp(-0.5) } else { scalar_exp(-0.5) };
        for y in 0..h {
            for x in 0..w {
                let center = at(x, y, 0, 0);
                let vector = w >= 16 && h >= 3 && (y == 0 || y == h - 1 || (x > 0 && x < w - 1));
                let mut sum = 0.;
                let mut ws = 0.;
                for (dx, dy) in [(-1, 0), (0, -1), (1, 0), (0, 1)] {
                    let v = at(x, y, dx, dy);
                    let wt = if fma {
                        weight_fma(v, center, vector)
                    } else {
                        weight(v, center, vector)
                    };
                    ws += wt;
                    sum += v * wt;
                }
                ws *= spatial;
                sum *= spatial;
                mat[y * w + x] = (sum + center) / (ws + 1.);
            }
        }
        return;
    }
    if r == 2 && fma {
        let taps = [
            [(0, -2), (-2, 0), (2, 0), (0, 2)],
            [(-1, -1), (1, -1), (-1, 1), (1, 1)],
            [(0, -1), (-1, 0), (1, 0), (0, 1)],
        ];
        let spatial = [fma_exp(-2.), fma_exp(-1.), fma_exp(-0.5)];
        for y in 0..h {
            for x in 0..w {
                let c = at(x, y, 0, 0);
                let vector = w >= 16 && h > 4 && (y < 2 || y >= h - 2 || (x >= 2 && x < w - 2));
                let mut nums = [0.; 3];
                let mut dens = [0.; 3];
                for g in 0..3 {
                    let mut v = taps[g].map(|(dx, dy)| at(x, y, dx, dy));
                    let mut wt = v.map(|v| weight_fma(v, c, vector));
                    if vector {
                        if g == 2 {
                            v.swap(0, 1);
                            wt.swap(0, 1);
                        }
                        if g == 0 {
                            v.swap(0, 1);
                            v.swap(1, 2);
                            wt.swap(0, 1);
                            wt.swap(1, 2);
                        }
                        let mut n = v[0] * wt[0];
                        for i in 1..4 {
                            n = v[i].mul_add(wt[i], n);
                        }
                        nums[g] = n;
                    } else {
                        // Scalar AVX pairs R/L and B/T, then fuses spatial groups.
                        nums[g] =
                            wt[1].mul_add(v[1], wt[2] * v[2]) + wt[0].mul_add(v[0], wt[3] * v[3]);
                    }
                    dens[g] = ((wt[0] + wt[1]) + wt[2]) + wt[3];
                }
                let (n, d) = if vector {
                    (
                        nums[1].mul_add(
                            spatial[1],
                            nums[0].mul_add(spatial[0], nums[2] * spatial[2]),
                        ) + c,
                        dens[1].mul_add(
                            spatial[1],
                            dens[0].mul_add(spatial[0], dens[2] * spatial[2]),
                        ) + 1.,
                    )
                } else {
                    (
                        nums[2].mul_add(
                            spatial[2],
                            nums[0].mul_add(spatial[0], nums[1].mul_add(spatial[1], c)),
                        ),
                        dens[2].mul_add(
                            spatial[2],
                            dens[0].mul_add(spatial[0], spatial[1] * dens[1]) + 1.,
                        ),
                    )
                };
                mat[y * w + x] = n / d;
            }
        }
        return;
    }
    if r == 2 {
        let taps = [
            [(0, -2), (-2, 0), (2, 0), (0, 2)],
            [(-1, -1), (1, -1), (-1, 1), (1, 1)],
            [(0, -1), (-1, 0), (1, 0), (0, 1)],
        ];
        let spatial = [scalar_exp(-2.), scalar_exp(-1.), scalar_exp(-0.5)];
        for y in 0..h {
            for x in 0..w {
                let center = at(x, y, 0, 0);
                let vector = w >= 16 && h > 4 && (y < 2 || y >= h - 2 || (x >= 2 && x < w - 2));
                let mut num = [0.; 3];
                let mut den = [0.; 3];
                for g in 0..3 {
                    let mut weights = [0.; 4];
                    let mut products = [0.; 4];
                    for t in 0..4 {
                        let (dx, dy) = taps[g][t];
                        let v = at(x, y, dx, dy);
                        weights[t] = weight(v, center, vector);
                        products[t] = v * weights[t];
                    }
                    if vector && g == 0 {
                        products.swap(0, 1);
                        products.swap(1, 2);
                        weights.swap(0, 1);
                        weights.swap(1, 2);
                    }
                    num[g] = ((products[0] + products[1]) + products[2] + products[3]) * spatial[g];
                    den[g] = ((weights[0] + weights[1]) + weights[2] + weights[3]) * spatial[g];
                }
                let numerator = if vector {
                    center + ((num[2] + num[0]) + num[1])
                } else {
                    (center + (num[0] + num[1])) + num[2]
                };
                let denominator = if vector {
                    ((den[2] + den[0]) + den[1]) + 1.
                } else {
                    ((den[0] + den[1]) + 1.) + den[2]
                };
                mat[y * w + x] = numerator / denominator;
            }
        }
        return;
    }
    let finite = mat.iter().all(|v| v.is_finite());
    let extent = if finite { r.min(7) } else { r } as isize;
    let mut offsets = vec![];
    for y in -extent..=extent {
        for x in -extent..=extent {
            let square = (x * x + y * y) as usize;
            if square > r * r || (finite && square >= 50) {
                continue;
            }
            let e = -0.5 * square as f32;
            offsets.push((
                x,
                y,
                if e > -25. {
                    if fma {
                        fma_exp(e)
                    } else {
                        scalar_exp(e)
                    }
                } else {
                    0.
                },
            ));
        }
    }
    for y in 0..h {
        for x in 0..w {
            let vector = !scalar
                && w >= 16
                && w > 2 * r
                && h > 2 * r
                && (y < r || y >= h - r || (x >= r && x < w - r));
            let center = at(x, y, 0, 0);
            let mut sum = 0.;
            let mut ws = 0.;
            for &(dx, dy, spatial) in &offsets {
                let v = at(x, y, dx, dy);
                let color = if fma {
                    weight_fma(v, center, vector)
                } else {
                    weight(v, center, vector)
                };
                let wt = color * spatial;
                if fma {
                    ws = spatial.mul_add(color, ws);
                    sum = wt.mul_add(v, sum);
                } else {
                    ws += wt;
                    sum += v * wt;
                }
            }
            mat[y * w + x] = sum / ws;
        }
    }
}
const kScalarExpTiny: f32 = f32::from_bits(0x31800000);
const kScalarLog2Scale: f64 = f64::from_bits(0x40771547652b82fe);
const kScalarExpQuadratic: f64 = f64::from_bits(0x3ecebfbdff82c58e);
const kScalarExpLinear: f64 = f64::from_bits(0x3f662e42fefa72c5);
const kVectorLog2E: f32 = f32::from_bits(0x3fb8aa3b);
const kVectorLn2High: f32 = f32::from_bits(0x3f317200);
const kVectorLn2Low: f32 = f32::from_bits(0x35bfbe8e);
const kVectorExpC5: f32 = f32::from_bits(0x3c07d9fe);
const kVectorExpC4: f32 = f32::from_bits(0x3d2b8392);
const kVectorExpC3: f32 = f32::from_bits(0x3e2aacac);
const kVectorExpC2: f32 = f32::from_bits(0x3effff34);
const kVectorExpC1: f32 = f32::from_bits(0x3f7ffffe);

// Native IPP CPU index 4, scalar exp RVA 0x1450f60. All fusions are explicit.
pub fn fma_exp(x: f32) -> f32 {
    let c = |i: usize| f64::from_bits(EXP_DATA[i]);
    if x.abs() < f32::from_bits(0x31800000) {
        return (x as f64 + 1.) as f32;
    }
    let biased = c(33).mul_add(x as f64, c(32));
    let n = biased - c(32);
    let residual = (-n).mul_add(c(34), x as f64);
    let bits = biased.to_bits();
    let value = f64::from_bits(EXP_DATA[(bits & 31) as usize].wrapping_add((bits >> 5) << 52));
    let poly = c(35).mul_add(residual, c(36)).mul_add(residual, c(37));
    (value * residual).mul_add(poly, value) as f32
}
pub fn fma_vector_exp(x: f32) -> f32 {
    let biased = kVectorLog2E.mul_add(x, kVectorRoundBias);
    let n = biased - kVectorRoundBias;
    let residual = (-n).mul_add(kVectorLn2Low, (-kVectorLn2High).mul_add(n, x));
    let poly = kVectorExpC5
        .mul_add(residual, kVectorExpC4)
        .mul_add(residual, kVectorExpC3)
        .mul_add(residual, kVectorExpC2)
        .mul_add(residual, kVectorExpC1)
        .mul_add(residual, 1.);
    f32::from_bits(poly.to_bits().wrapping_add(biased.to_bits() << 23))
}
fn weight_fma(v: f32, c: f32, vector: bool) -> f32 {
    let d = v - c;
    let e = if vector {
        (d * d) * -0.5
    } else {
        (-0.5 * d) * d
    };
    if e > -25. {
        if vector {
            fma_vector_exp(e)
        } else {
            fma_exp(e)
        }
    } else {
        0.
    }
}

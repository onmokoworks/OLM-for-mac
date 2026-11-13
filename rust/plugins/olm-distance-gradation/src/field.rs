//! Meijster EDT and Smart owner resize/normalization, from the shared C++ core.
mod native_rsqrt {
    include!("rsqrt_table.rs");
    pub fn positive_normal(x: f32) -> f32 {
        let bits = x.to_bits();
        let exponent = ((bits >> 23) & 255) as i32;
        let parity = (exponent - 127) & 1;
        let index = parity as usize * 4096 + ((bits & 0x7fffff) >> 11) as usize;
        let adjustment = ((exponent - 127 - parity) / 2) << 23;
        f32::from_bits((RSQRT[index] as i32 - adjustment) as u32)
    }
}
#[cfg(feature = "stage-dump")]
pub fn edt(mask: &[u8], w: usize, h: usize) -> Vec<f32> {
    edt_impl(mask, w, h, true)
}
fn edt_impl(mask: &[u8], w: usize, h: usize, native: bool) -> Vec<f32> {
    edt_with_threads(mask, w, h, native, olm_core::row_workers(h, w))
}
fn edt_with_threads(mask: &[u8], w: usize, h: usize, native: bool, threads: usize) -> Vec<f32> {
    let inf = (w + h) as i64;
    let mut g = vec![0i64; w * h];
    for x in 0..w {
        g[x] = if mask[x] != 0 { inf } else { 0 };
    }
    // Columns are independent: walk contiguous rows while retaining each
    // column's forward/backward recurrence exactly.
    for y in 1..h {
        let (before, after) = g.split_at_mut(y * w);
        let previous = &before[(y - 1) * w..y * w];
        for (x, value) in after[..w].iter_mut().enumerate() {
            *value = if mask[y * w + x] == 0 {
                0
            } else if previous[x] == inf {
                inf
            } else {
                previous[x] + 1
            };
        }
    }
    for y in (0..h - 1).rev() {
        let (before, after) = g.split_at_mut((y + 1) * w);
        for (x, value) in before[y * w..].iter_mut().enumerate() {
            if after[x] != inf && after[x] + 1 < *value {
                *value = after[x] + 1;
            }
        }
    }
    let mut dst = vec![0.; w * h];
    olm_core::parallel_rows(&mut dst, w, threads, |y, output| {
        let mut s = vec![0usize; w];
        let mut t = vec![0i64; w];
        let row = &g[y * w..(y + 1) * w];
        let mut q = 0isize;
        s[0] = 0;
        t[0] = 0;
        let val = |x: i64, i: usize| {
            let d = x - i as i64;
            (d * d + row[i] * row[i]) as f32
        };
        for u in 1..w {
            while q >= 0 && val(t[q as usize], s[q as usize]) > val(t[q as usize], u) {
                q -= 1;
            }
            if q < 0 {
                q = 0;
                s[0] = u;
            } else {
                let i = s[q as usize] as i64;
                let uu = u as i64;
                let sep = 1
                    + (uu * uu - i * i + row[u] * row[u] - row[i as usize] * row[i as usize])
                        / (2 * (uu - i));
                if sep < w as i64 {
                    q += 1;
                    s[q as usize] = u;
                    t[q as usize] = sep;
                }
            }
        }
        for u in (0..w).rev() {
            output[u] = val(u as i64, s[q as usize]);
            if u as i64 == t[q as usize] {
                q -= 1;
            }
        }
        if native {
            // IPP CPU index 4: RVA 0x2f1e20 aligns to eight floats, then
            // processes sixteen at a time. Prefix/tail helper 0x6e4d00 uses
            // the same FMA polynomial and whole-group zero fallback.
            let prefix = ((8 - (y * w) % 8) % 8).min(w);
            let mut x = 0;
            while x < w {
                let n = if x == 0 && prefix != 0 {
                    prefix
                } else {
                    (w - x).min(16)
                };
                let group = &mut output[x..x + n];
                let regular = group.iter().all(|v| *v > 0.);
                for v in group {
                    *v = if regular {
                        let r = native_rsqrt::positive_normal(*v);
                        let product = r * *v;
                        let residual = (-product).mul_add(r, 1.);
                        let scale = 0.375f32.mul_add(residual, 0.5);
                        let correction = r * residual;
                        *v * scale.mul_add(correction, r)
                    } else {
                        v.sqrt()
                    };
                }
                x += n;
            }
            return;
        }
        let mut x = 0;
        while x < w && (y * w + x) % 4 != 0 {
            output[x] = output[x].sqrt();
            x += 1;
        }
        while x + 16 <= w {
            let regular = output[x..x + 16].iter().all(|v| *v > 0.);
            for k in 0..16 {
                let v = output[x + k];
                let root = v.sqrt();
                output[x + k] = if regular {
                    let inv = 1. / root;
                    let prod = v * inv;
                    (inv * prod - 3.) * (prod * -0.5)
                } else {
                    root
                };
            }
            x += 16;
        }
        while x < w {
            output[x] = output[x].sqrt();
            x += 1;
        }
    })
    .expect("validated distance plane");
    dst
}
pub fn normalized(
    mask: &[u8],
    w: usize,
    h: usize,
    rw: usize,
    rh: usize,
    threshold: f32,
    constant: bool,
    max: f32,
) -> Vec<f32> {
    normalized_impl(mask, w, h, rw, rh, threshold, constant, max, false)
}
#[cfg(test)]
pub fn normalized_legacy(
    mask: &[u8],
    w: usize,
    h: usize,
    rw: usize,
    rh: usize,
    threshold: f32,
    constant: bool,
    max: f32,
) -> Vec<f32> {
    normalized_impl(mask, w, h, rw, rh, threshold, constant, max, true)
}
fn normalized_impl(
    mask: &[u8],
    w: usize,
    h: usize,
    rw: usize,
    rh: usize,
    threshold: f32,
    constant: bool,
    max: f32,
    legacy: bool,
) -> Vec<f32> {
    let mut field = if w == rw && h == rh {
        edt_impl(mask, w, h, !legacy)
    } else {
        let mut expanded = vec![0; rw * rh];
        let sx = w as f64 / rw as f64;
        let sy = h as f64 / rh as f64;
        for y in 0..rh {
            for x in 0..rw {
                expanded[y * rw + x] = mask[((y as f64 * sy) as usize).min(h - 1) * w
                    + ((x as f64 * sx) as usize).min(w - 1)];
            }
        }
        let d = edt_impl(&expanded, rw, rh, !legacy);
        let mut f = vec![0.; w * h];
        for y in 0..h {
            let cy = (y as f64 + 0.5) * (rh as f64 / h as f64) - 0.5;
            let iy = if legacy {
                (cy as f32).floor() as isize
            } else {
                cy.floor() as isize
            };
            let fy = if legacy {
                cy as f32 - iy as f32
            } else {
                (cy - iy as f64) as f32
            };
            let y0 = iy.clamp(0, rh as isize - 1) as usize;
            let y1 = (iy + 1).clamp(0, rh as isize - 1) as usize;
            for x in 0..w {
                let cx = (x as f64 + 0.5) * (rw as f64 / w as f64) - 0.5;
                let mut ix = if legacy {
                    (cx as f32).floor() as isize
                } else {
                    cx.floor() as isize
                };
                let mut fx = if legacy {
                    cx as f32 - ix as f32
                } else {
                    (cx - ix as f64) as f32
                };
                if ix < 0 {
                    ix = 0;
                    fx = 0.;
                }
                if ix >= rw as isize - 1 {
                    ix = rw as isize - 1;
                    fx = 0.;
                }
                let xx = ix as usize;
                let x1 = (xx + 1).min(rw - 1);
                // IPP index-4 rows: 0x729e60 / 0x72a040 use delta
                // interpolation, FMA for groups of four, scalar tail otherwise.
                let blend = |a: f32, b: f32, t: f32| {
                    if legacy {
                        a * (1. - t) + b * t
                    } else if x < w / 4 * 4 {
                        (b - a).mul_add(t, a)
                    } else {
                        a + (b - a) * t
                    }
                };
                let a = blend(d[y0 * rw + xx], d[y0 * rw + x1], fx);
                let b = blend(d[y1 * rw + xx], d[y1 * rw + x1], fx);
                f[y * w + x] = blend(a, b, fy);
            }
        }
        f
    };
    if constant {
        for v in &mut field {
            *v = if *v > threshold { max } else { 0. };
        }
    } else {
        // 2026-11-12 RVA 0x11750f0: cvThreshold(TRUNC) uses 0.1
        // for zero threshold, then cvNormalize's upper bound is reduced by
        // observed_max / requested_threshold. Preserve its double arithmetic.
        let th = if legacy {
            threshold.max(1.)
        } else if threshold == 0. {
            0.1
        } else {
            threshold
        };
        let mut raw = 0f32;
        for v in &mut field {
            *v = v.min(th);
            raw = raw.max(*v);
        }
        let scale = if raw > 0. {
            if legacy {
                max / raw
            } else {
                let upper = if raw < threshold {
                    raw as f64 / threshold as f64
                } else {
                    1.
                };
                ((upper * max as f64) / raw as f64) as f32
            }
        } else {
            0.
        };
        for v in &mut field {
            *v *= scale;
        }
    }
    field
}
pub fn pack(v: f32, max: f32) -> f32 {
    (v * max).clamp(0., max).round_ties_even() / max
}

#[cfg(test)]
mod parallel_tests {
    use super::*;
    #[test]
    fn distance_rows_preserve_canonical_groups_across_threads() {
        for (w, h) in [(257, 521), (511, 257)] {
            for kind in 0..3 {
                let mask: Vec<u8> = (0..w * h)
                    .map(|i| match kind {
                        0 => 0,
                        1 => 1,
                        _ => ((i * 7919 + i / w * 17) % 37 > 2) as u8,
                    })
                    .collect();
                for native in [false, true] {
                    let a = edt_with_threads(&mask, w, h, native, 1);
                    let b = edt_with_threads(&mask, w, h, native, 7);
                    assert!(a.iter().zip(b).all(|(a, b)| a.to_bits() == b.to_bits()));
                }
            }
        }
    }
}

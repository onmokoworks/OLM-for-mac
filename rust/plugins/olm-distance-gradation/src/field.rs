//! Meijster EDT and Smart owner resize/normalization, from the shared C++ core.
pub fn edt(mask: &[u8], w: usize, h: usize) -> Vec<f32> {
    let inf = (w + h) as i64;
    let mut g = vec![0i64; w * h];
    for x in 0..w {
        g[x] = if mask[x] != 0 { inf } else { 0 };
        for y in 1..h {
            let i = y * w + x;
            g[i] = if mask[i] == 0 {
                0
            } else if g[i - w] == inf {
                inf
            } else {
                g[i - w] + 1
            };
        }
        for y in (0..h - 1).rev() {
            let i = y * w + x;
            if g[i + w] != inf && g[i + w] + 1 < g[i] {
                g[i] = g[i + w] + 1;
            }
        }
    }
    let mut s = vec![0usize; w];
    let mut t = vec![0i64; w];
    let mut dst = vec![0.; w * h];
    for y in 0..h {
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
            dst[y * w + u] = val(u as i64, s[q as usize]);
            if u as i64 == t[q as usize] {
                q -= 1;
            }
        }
        let mut x = 0;
        while x < w && (y * w + x) % 4 != 0 {
            dst[y * w + x] = dst[y * w + x].sqrt();
            x += 1;
        }
        while x + 16 <= w {
            let regular = dst[y * w + x..y * w + x + 16].iter().all(|v| *v > 0.);
            for k in 0..16 {
                let v = dst[y * w + x + k];
                let root = v.sqrt();
                dst[y * w + x + k] = if regular {
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
            dst[y * w + x] = dst[y * w + x].sqrt();
            x += 1;
        }
    }
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
    let mut field = if w == rw && h == rh {
        edt(mask, w, h)
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
        let d = edt(&expanded, rw, rh);
        let mut f = vec![0.; w * h];
        for y in 0..h {
            let mut fy = ((y as f64 + 0.5) * rh as f64 / h as f64 - 0.5) as f32;
            let iy = fy.floor() as isize;
            fy -= iy as f32;
            let y0 = iy.clamp(0, rh as isize - 1) as usize;
            let y1 = (iy + 1).clamp(0, rh as isize - 1) as usize;
            for x in 0..w {
                let mut fx = ((x as f64 + 0.5) * rw as f64 / w as f64 - 0.5) as f32;
                let mut ix = fx.floor() as isize;
                fx -= ix as f32;
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
                let a = d[y0 * rw + xx] * (1. - fx) + d[y0 * rw + x1] * fx;
                let b = d[y1 * rw + xx] * (1. - fx) + d[y1 * rw + x1] * fx;
                f[y * w + x] = a * (1. - fy) + b * fy;
            }
        }
        f
    };
    if constant {
        for v in &mut field {
            *v = if *v > threshold { max } else { 0. };
        }
    } else {
        let th = threshold.max(1.);
        let mut raw = 0f32;
        for v in &mut field {
            *v = v.min(th);
            raw = raw.max(*v);
        }
        let scale = if raw > 0. { max / raw } else { 0. };
        for v in &mut field {
            *v *= scale;
        }
    }
    field
}
pub fn pack(v: f32, max: f32) -> f32 {
    (v * max).clamp(0., max).round_ties_even() / max
}

//! Distance scan order and single-column behavior from Distance.inc.
pub fn boundary(mask: &[u8], w: usize, h: usize) -> Vec<u8> {
    let mut out = vec![0; w * h];
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            if mask[i] == 0 {
                continue;
            }
            let mut all = true;
            for dy in -1..=1 {
                for dx in -1..=1 {
                    if dx == 0 && dy == 0 {
                        continue;
                    }
                    let xx = (x as isize + dx).clamp(0, w as isize - 1) as usize;
                    let yy = (y as isize + dy).clamp(0, h as isize - 1) as usize;
                    all = all && mask[yy * w + xx] != 0;
                }
            }
            out[i] = (!all) as u8;
        }
    }
    out
}
fn edt(f: &[f32], step: f32) -> Vec<f32> {
    let sites: Vec<_> = (0..f.len()).filter(|&i| f[i] < 5.0e8).collect();
    let mut d = vec![1.0e9; f.len()];
    if sites.is_empty() {
        return d;
    }
    let mut v = vec![0; sites.len()];
    let mut z = vec![0.0; sites.len() + 1];
    let mut k = 0;
    v[0] = sites[0];
    z[0] = -1.0e20;
    z[1] = 1.0e20;
    for &q in &sites[1..] {
        let mut s;
        loop {
            let p = v[k];
            let qf = q as f32;
            let pf = p as f32;
            s = ((f[q] + qf * qf * step * step) - (f[p] + pf * pf * step * step))
                / (2.0 * (qf - pf) * step)
                * (1.0 / step);
            if s > z[k] || k == 0 {
                break;
            }
            k -= 1;
        }
        if s <= z[k] {
            k = 0
        } else {
            k += 1
        }
        v[k] = q;
        z[k] = s;
        z[k + 1] = 1.0e20;
    }
    k = 0;
    for q in 0..f.len() {
        while z[k + 1] < (q as f32) {
            k += 1
        }
        let p = v[k];
        let delta = q as f32 - p as f32;
        d[q] = (delta * delta * step * step) + f[p];
    }
    d
}
pub fn distance(
    mask: &[u8],
    w: usize,
    h: usize,
    kind: i32,
    dx: f32,
    dy: f32,
    initial: Option<&[f32]>,
) -> Vec<f32> {
    if kind == 3 {
        let mut tmp = vec![0.0; w * h];
        for x in 0..w {
            let f: Vec<_> = (0..h)
                .map(|y| if mask[y * w + x] != 0 { 0.0 } else { 1.0e9 })
                .collect();
            let c = edt(&f, dy);
            for y in 0..h {
                tmp[y * w + x] = c[y];
            }
        }
        let mut out = vec![0.0; w * h];
        for y in 0..h {
            let r = edt(&tmp[y * w..(y + 1) * w], dx);
            for x in 0..w {
                out[y * w + x] = r[x].sqrt();
            }
        }
        return out;
    }
    if kind == 1 && w == 1 {
        let mut d = initial
            .filter(|a| a.len() == h)
            .map(|a| a.to_vec())
            .unwrap_or_else(|| vec![0.0; h]);
        d[0] = if mask[0] != 0 { 0.0 } else { 3999.0 };
        fn read(d: &[f32], y: isize) -> f32 {
            if y >= 0 && (y as usize) < d.len() {
                d[y as usize]
            } else {
                0.0
            }
        }
        for y in 1..h {
            let left = if mask[y] != 0 {
                0.0
            } else {
                4000.0f32.min((d[y - 1].min(d[y])) + dy)
            };
            d[y] = if mask[y] != 0 {
                0.0
            } else {
                4000.0f32.min((left + dx).min(d[y - 1].min(read(&d, y as isize - 2)) + dy))
            };
        }
        for y in (0..h - 1).rev() {
            let right = d[y + 1].min(d[y]) + dy;
            d[y] = d[y].min(right);
            let left = d[y + 1].min(read(&d, y as isize + 2)).min(d[y]) + dy;
            d[y] = d[y].min(left.min(right + dx));
        }
        return d;
    }
    let mut d = vec![4000.0f32; w * h];
    for i in 0..w * h {
        if mask[i] != 0 {
            d[i] = 0.0
        }
    }
    if mask[0] == 0 {
        d[0] = 3999.0
    }
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            if x > 0 {
                d[i] = d[i].min(d[i - 1] + dx)
            }
            if y > 0 {
                d[i] = d[i].min(d[i - w] + dy)
            }
            if kind == 1 {
                if x > 0 && y > 0 {
                    d[i] = d[i].min(d[i - w - 1] + dy)
                }
                if x + 1 < w && y > 0 {
                    d[i] = d[i].min(d[i - w + 1] + dy)
                }
            }
        }
    }
    for x in (0..w - 1).rev() {
        let i = (h - 1) * w + x;
        d[i] = d[i].min(d[i + 1] + dx)
    }
    for y in (0..h - 1).rev() {
        let i = y * w + w - 1;
        let below = if kind == 1 {
            d[i + w].min(d[i + w - 1])
        } else {
            d[i + w]
        };
        let mut right = 4000.0f32.min(below + dy);
        d[i] = d[i].min(right);
        for x in (0..w - 1).rev() {
            let i = y * w + x;
            let mut below = d[i + w];
            if kind == 1 {
                below = below.min(d[i + w + 1]);
                if x > 0 {
                    below = below.min(d[i + w - 1]);
                }
            }
            right = 4000.0f32.min((below.min(d[i + 1]) + dy).min(right + dx));
            d[i] = d[i].min(right);
        }
    }
    d
}

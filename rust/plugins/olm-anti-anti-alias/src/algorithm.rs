//! CPU translation of the 2025 AEX; provenance and boundaries in VALIDATION.md.
use crate::generated;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Layout {
    pub width: usize,
    pub height: usize,
    pub row_bytes: usize,
    pub bytes_per_pixel: usize,
    pub origin: (i32, i32),
}
impl Layout {
    pub fn span(self) -> Option<usize> {
        if ![4, 8, 16].contains(&self.bytes_per_pixel) {
            return None;
        }
        let row = self.width.checked_mul(self.bytes_per_pixel)?;
        if self.row_bytes < row {
            return None;
        }
        if self.height == 0 {
            return Some(0);
        }
        self.row_bytes
            .checked_mul(self.height - 1)?
            .checked_add(row)
    }
}

pub type Color = [f32; 4]; // ARGB
#[derive(Clone, Debug, Default)]
pub struct Settings {
    pub colors: Vec<Color>,
    pub automatic: bool,
}

fn allocate<T: Clone>(n: usize, value: T) -> Result<Vec<T>, &'static str> {
    let mut v = Vec::new();
    v.try_reserve_exact(n).map_err(|_| "allocation")?;
    v.resize(n, value);
    Ok(v)
}
fn load(raw: &[u8], bpp: usize) -> Color {
    std::array::from_fn(|c| match bpp {
        4 => raw[c] as f32 / 255.0,
        8 => u16::from_le_bytes(raw[c * 2..c * 2 + 2].try_into().unwrap()) as f32 * (1.0 / 32768.0),
        _ => f32::from_le_bytes(raw[c * 4..c * 4 + 4].try_into().unwrap()),
    })
}
// CVTTSS2SI, then narrowing, rather than Rust's saturating float cast.
fn cvtt(v: f32) -> i32 {
    if !(-2147483648.0..2147483648.0).contains(&v) {
        i32::MIN
    } else {
        v as i32
    }
}
fn store(raw: &mut [u8], c: Color, bpp: usize) {
    for k in 0..4 {
        match bpp {
            4 => raw[k] = cvtt(c[k] * 255.0) as u8,
            8 => {
                raw[k * 2..k * 2 + 2].copy_from_slice(&(cvtt(c[k] * 32768.0) as u16).to_le_bytes())
            }
            _ => raw[k * 4..k * 4 + 4].copy_from_slice(&c[k].to_le_bytes()),
        }
    }
}
fn matches(raw: &[u8], p: Color, bpp: usize) -> bool {
    if bpp == 16 {
        let q = load(raw, bpp);
        return [1, 2, 3, 0]
            .into_iter()
            .all(|k| !((q[k] - p[k]).abs() > 0.0001));
    }
    let scale = if bpp == 4 { 255.0 } else { 32768.0 };
    let half = if bpp == 4 { 0.0019607844 } else { 1.5258789e-5 };
    [1, 2, 3, 0].into_iter().all(|k| {
        let value = cvtt((p[k] + half) * scale);
        if bpp == 4 {
            raw[k] == value as u8
        } else {
            u16::from_le_bytes(raw[k * 2..k * 2 + 2].try_into().unwrap()) == value as u16
        }
    })
}
fn auto_matches(raw: &[u8], p: Color, bpp: usize) -> bool {
    unsafe {
        match bpp {
            4 => generated::autoport_180001740(p[1], p[2], p[3], p[0], raw.as_ptr()) != 0,
            8 => generated::autoport_180001680(p[1], p[2], p[3], p[0], raw.as_ptr()) != 0,
            _ => {
                let q = load(raw, bpp);
                [1, 2, 3, 0]
                    .into_iter()
                    .all(|k| !((q[k] - p[k]).abs() > 0.0002))
            }
        }
    }
}
fn raw_at(input: &[u8], a: Layout, x: usize, y: usize) -> &[u8] {
    let at = y * a.row_bytes + x * a.bytes_per_pixel;
    &input[at..at + a.bytes_per_pixel]
}
/// Row-major 3x3 plateau detector (4830/4d40/5230), excluding existing colors.
pub fn detect(
    input: &[u8],
    a: Layout,
    existing: &[Color],
    limit: usize,
) -> Result<Vec<Color>, &'static str> {
    if a.span().ok_or("layout")? > input.len() {
        return Err("input length");
    }
    let mut found = Vec::new();
    found
        .try_reserve(limit.min(9999))
        .map_err(|_| "allocation")?;
    for y in 1..a.height.saturating_sub(1) {
        for x in 1..a.width.saturating_sub(1) {
            if found.len() >= limit {
                return Ok(found);
            }
            let raw = raw_at(input, a, x, y);
            let p = load(raw, a.bytes_per_pixel);
            if p[0] != 1.0 {
                continue;
            }
            let same = (y - 1..=y + 1).all(|yy| {
                (x - 1..=x + 1).all(|xx| {
                    let q = load(raw_at(input, a, xx, yy), a.bytes_per_pixel);
                    p.iter().zip(q).all(|(v, w)| *v == w)
                })
            });
            if same
                && !existing
                    .iter()
                    .chain(found.iter())
                    .any(|&q| auto_matches(raw, q, a.bytes_per_pixel))
            {
                found.push(p)
            }
        }
    }
    Ok(found)
}
fn squared(a: Color, b: Color) -> f32 {
    let r = a[1] - b[1];
    let g = a[2] - b[2];
    let z = a[3] - b[3];
    (r * r + g * g) + z * z
}
fn nearest(
    p: Color,
    palette: &[Color],
    indices: impl Iterator<Item = usize>,
    unordered: bool,
) -> Option<usize> {
    let mut best = None;
    let mut distance = 99999.9f32;
    for k in indices {
        let d = squared(palette[k], p);
        if if unordered {
            !(distance <= d)
        } else {
            d < distance
        } {
            distance = d;
            best = Some(k)
        }
    }
    best
}
fn pair(p: Color, a: Color, b: Color) -> (f32, bool) {
    let d = [0.0, b[1] - a[1], b[2] - a[2], b[3] - a[3]];
    let len2 = (d[2] * d[2] + d[1] * d[1]) + d[3] * d[3];
    let (mut t, mut da, mut db) = (0.0, 0.0, 0.0);
    let (mut u, mut v) = ([0.0; 4], [0.0; 4]);
    let score = unsafe {
        generated::autoport_18000a630(
            p.as_ptr(),
            &mut t,
            a.as_ptr(),
            b.as_ptr(),
            u.as_mut_ptr(),
            v.as_mut_ptr(),
            &mut da,
            &mut db,
            d.as_ptr(),
            len2,
        )
    };
    (score, db <= da)
}
fn choose_pair(p: Color, palette: &[Color], candidates: &[usize]) -> Option<usize> {
    let mut best = None;
    let mut minimum = 99999.9f32;
    let mut examine = |a: usize, b: usize| {
        let (score, second) = pair(p, palette[a], palette[b]);
        if score < minimum {
            minimum = score;
            best = Some(if second { b } else { a })
        }
    };
    if candidates.len() == 1 {
        for k in 0..palette.len() {
            if k != candidates[0] {
                examine(candidates[0], k)
            }
        }
    } else {
        for (i, &a) in candidates.iter().enumerate() {
            for &b in &candidates[i + 1..] {
                examine(a, b)
            }
        }
    }
    best
}
fn neighbors(
    x: usize,
    y: usize,
    r: usize,
    w: usize,
    h: usize,
) -> impl Iterator<Item = (usize, usize)> {
    (y.saturating_sub(r)..=(y + r).min(h - 1))
        .flat_map(move |yy| (x.saturating_sub(r)..=(x + r).min(w - 1)).map(move |xx| (xx, yy)))
}

/// Pure render with checked spans, input-space neighborhoods, untouched row padding.
pub fn render_with(
    input: &[u8],
    a: Layout,
    output: &mut [u8],
    b: Layout,
    settings: &Settings,
) -> Result<(), &'static str> {
    if a.bytes_per_pixel != b.bytes_per_pixel
        || a.span().ok_or("input layout")? > input.len()
        || b.span().ok_or("output layout")? > output.len()
    {
        return Err("layout mismatch");
    }
    let n = a.width.checked_mul(a.height).ok_or("dimensions")?;
    let mut pixels = allocate(n, [0.0; 4])?;
    for y in 0..a.height {
        for x in 0..a.width {
            pixels[y * a.width + x] = load(raw_at(input, a, x, y), a.bytes_per_pixel)
        }
    }
    let mut palette = settings.colors.clone();
    for c in &mut palette {
        c[0] = 1.0
    }
    if settings.automatic {
        let extra = detect(input, a, &palette, 9999usize.saturating_sub(palette.len()))?;
        palette.extend(extra);
    }
    let bypass = palette.is_empty() || (palette.len() == 1 && palette[0][1..] == [0.0; 3]);
    let mut result = pixels.clone();
    if !bypass {
        let mut first = allocate(n, -1i32)?;
        let mut second = allocate(n, -1i32)?;
        for y in 0..a.height {
            for x in 0..a.width {
                let i = y * a.width + x;
                let p = pixels[i];
                if p[0] == 0.0 {
                    continue;
                }
                if let Some(k) = palette
                    .iter()
                    .position(|&c| matches(raw_at(input, a, x, y), c, a.bytes_per_pixel))
                {
                    result[i] = palette[k];
                    first[i] = k as i32;
                    second[i] = k as i32;
                } else {
                    result[i] = [1.0, 0.0, 0.0, 0.0]
                }
            }
        }
        let mut selected = allocate(palette.len(), false)?;
        let mut candidates = Vec::new();
        candidates
            .try_reserve_exact(palette.len())
            .map_err(|_| "allocation")?;
        for y in 0..a.height {
            for x in 0..a.width {
                let i = y * a.width + x;
                let p = pixels[i];
                if p[0] == 0.0 {
                    result[i] = p;
                    continue;
                }
                if first[i] >= 0 {
                    continue;
                }
                result[i] = p;
                if p[0] != 1.0 {
                    continue;
                }
                for radius in 1..=2 {
                    selected.fill(false);
                    for (xx, yy) in neighbors(x, y, radius, a.width, a.height) {
                        let j = yy * a.width + xx;
                        if first[j] >= 0 {
                            selected[first[j] as usize] = true
                        } else if let Some(k) = nearest(pixels[j], &palette, 0..palette.len(), true)
                        {
                            if squared(p, palette[k]).sqrt() + 0.0001 < 1.0 {
                                selected[k] = true
                            }
                        }
                    }
                    candidates.clear();
                    candidates.extend(
                        selected
                            .iter()
                            .enumerate()
                            .filter_map(|(k, &yes)| yes.then_some(k)),
                    );
                    if let Some(k) = choose_pair(p, &palette, &candidates) {
                        result[i] = palette[k];
                        second[i] = k as i32;
                        break;
                    }
                }
            }
        }
        for y in 0..a.height {
            for x in 0..a.width {
                let i = y * a.width + x;
                let p = pixels[i];
                if p[0] == 1.0 || second[i] >= 0 {
                    continue;
                }
                if p[0] <= 0.5 {
                    result[i] = [0.0, 1.0, 1.0, 1.0];
                    continue;
                }
                selected.fill(false);
                for radius in 1..=4 {
                    for (xx, yy) in neighbors(x, y, radius, a.width, a.height) {
                        let k = second[yy * a.width + xx];
                        if k >= 0 {
                            selected[k as usize] = true
                        }
                    }
                    if selected.iter().any(|&v| v) {
                        break;
                    }
                }
                let indices = selected
                    .iter()
                    .enumerate()
                    .filter_map(|(k, &yes)| yes.then_some(k));
                if let Some(k) = nearest(p, &palette, indices, false) {
                    result[i] = palette[k]
                } else {
                    result[i] = p
                }
            }
        }
    }
    for y in 0..b.height {
        for x in 0..b.width {
            let sx = i64::from(b.origin.0) + x as i64 - i64::from(a.origin.0);
            let sy = i64::from(b.origin.1) + y as i64 - i64::from(a.origin.1);
            let dst = y * b.row_bytes + x * b.bytes_per_pixel;
            let target = &mut output[dst..dst + b.bytes_per_pixel];
            if sx >= 0 && sy >= 0 && (sx as usize) < a.width && (sy as usize) < a.height {
                if bypass {
                    target.copy_from_slice(raw_at(input, a, sx as usize, sy as usize))
                } else {
                    store(
                        target,
                        result[sy as usize * a.width + sx as usize],
                        b.bytes_per_pixel,
                    )
                }
            } else {
                target.fill(0)
            }
        }
    }
    Ok(())
}
pub fn render(input: &[u8], a: Layout, output: &mut [u8], b: Layout) -> Result<(), &'static str> {
    render_with(input, a, output, b, &Settings::default())
}

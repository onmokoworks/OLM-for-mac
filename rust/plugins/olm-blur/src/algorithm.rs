//! Pure CPU translation of core/olmblur_{helper,fullworker_helper,worker*}.cpp.
//! Accumulation order, operand order, six Legacy carry partitions and typed writers
//! are part of the algorithm. Do not normalize integer channels or fuse operations.
use olm_core::{allocate, image_len, Budget, Error, Pixel, Result, View, ViewMut};
use olm_math::{x86, Mode};

#[derive(Clone, Copy, Debug)]
pub struct Params {
    pub amount: f32,
    pub smoothness: f32,
    pub repeat: usize,
    pub bias: usize,
    pub legacy: bool,
    pub scale: f32,
}
impl Default for Params {
    fn default() -> Self {
        Self {
            amount: 5.0,
            smoothness: 100.0,
            repeat: 2,
            bias: 1,
            legacy: false,
            scale: 1.0,
        }
    }
}

/// floorf(value + 0.5), CVTTSS2SI, low byte/word. No nominal white clamp.
pub fn integer_store(value: f32) -> i32 {
    x86::cvttss2si(x86::add(value, 0.5).floor())
}

fn nonlegacy_pass(
    flags: &[u8],
    src: &[[f32; 3]],
    dst: &mut [[f32; 3]],
    weights: &[f32],
    w: usize,
    h: usize,
    vertical: bool,
    threads: usize,
) -> Result<()> {
    let radius = weights.len() - 1;
    olm_core::parallel_rows(dst, w, threads, |y, row| {
        for (x, out) in row.iter_mut().enumerate() {
            let center = y * w + x;
            if flags[center] == 0 {
                *out = src[center];
                continue;
            }
            let (coordinate, dimension, step) = if vertical { (y, h, w) } else { (x, w, 1) };
            let mut sum = 0.0;
            let mut rgb = [0.0; 3];
            let mut add = |index: usize, weight: f32| {
                sum = x86::add(sum, weight);
                for c in 0..3 {
                    rgb[c] = x86::add(rgb[c], x86::mul(weight, src[index][c]));
                }
            };
            for d in 0..=radius.min(coordinate) {
                let index = center - d * step;
                if flags[index] == 0 {
                    break;
                }
                add(index, weights[d]);
            }
            for d in 1..=radius.min(dimension - 1 - coordinate) {
                let index = center + d * step;
                if flags[index] == 0 {
                    break;
                }
                add(index, weights[d]);
            }
            let scale = if sum == 0.0 { 0.0 } else { x86::div(1.0, sum) };
            for c in 0..3 {
                out[c] = x86::mul(scale, rgb[c]);
            }
        }
    })
}

fn legacy_pass(
    flags: &[u8],
    src: &[[f32; 3]],
    dst: &mut [[f32; 3]],
    weights: &[f32],
    w: usize,
    h: usize,
    vertical: bool,
) {
    let radius = weights.len() / 2;
    // Carry belongs to each original partition, not to a row or execution thread.
    for part in 0..6 {
        let dim = if vertical { w } else { h };
        let base = dim / 6;
        let count = if part == 5 { dim - 5 * base } else { base };
        let offset = base * part;
        let mut carry = [-1.0; 3];
        let (rows, cols) = if vertical { (h, count) } else { (count, w) };
        for row in 0..rows {
            for col in 0..cols {
                let (x, y) = if vertical {
                    (offset + col, row)
                } else {
                    (col, offset + row)
                };
                let center = y * w + x;
                if flags[center] == 0 {
                    if !vertical {
                        dst[center] = src[center];
                    }
                    continue;
                }
                let (coordinate, dimension, step) = if vertical { (y, h, w) } else { (x, w, 1) };
                let mut sum = 0.0;
                let mut rgb = [0.0; 3];
                let mut unchanged = true;
                let mut add = |index: usize, weight: f32| {
                    let pixel = src[index];
                    sum = x86::add(sum, weight);
                    for c in 0..3 {
                        rgb[c] = x86::add(rgb[c], x86::mul(pixel[c], weight));
                        if pixel[c] != carry[c] {
                            unchanged = false;
                        }
                    }
                    carry = pixel;
                };
                // AEX excludes coordinate zero, including the center at the border.
                for d in 0..=radius {
                    if coordinate <= d {
                        continue;
                    }
                    let index = center - d * step;
                    if flags[index] == 0 {
                        break;
                    }
                    add(index, weights[radius - d]);
                }
                for d in 1..=radius {
                    if coordinate + d >= dimension {
                        break;
                    }
                    let index = center + d * step;
                    if flags[index] == 0 {
                        break;
                    }
                    add(index, weights[radius + d]);
                }
                let scale = if sum != 0.0 { x86::div(1.0, sum) } else { 1.0 };
                dst[center] = if unchanged {
                    src[center]
                } else {
                    rgb.map(|c| x86::mul(scale, c))
                };
            }
        }
    }
}

/// Full-frame worlds, arbitrary positive strides. Parameters match the Smart
/// builder (Smoothness has already had its fixed-point fraction discarded).
/// Thread count only schedules independent non-Legacy rows; Legacy is serial.
pub fn render(
    input: &View<'_>,
    output: &mut ViewMut<'_>,
    p: &Params,
    threads: usize,
) -> Result<()> {
    let l = input.layout();
    let o = output.layout();
    if l.width != o.width
        || l.height != o.height
        || l.depth != o.depth
        || l.origin != (0, 0)
        || o.origin != (0, 0)
    {
        return Err(Error::Unsupported);
    }
    if !p.amount.is_finite()
        || !(1.0..=1000.0).contains(&p.amount)
        || !(1.0..=100.0).contains(&p.smoothness)
        || !(1..=10).contains(&p.repeat)
        || !(1..=2).contains(&p.bias)
        || !p.scale.is_finite()
        || p.scale <= 0.0
    {
        return Err(Error::Unsupported);
    }
    let (w, h) = (l.width, l.height);
    let n = image_len(w, h)?;
    let mut budget = Budget::new(isize::MAX as usize);
    let mut a = allocate(n, [0.0; 3], &mut budget)?;
    let mut b = allocate(n, [0.0; 3], &mut budget)?;
    let mut flags = allocate(n, 0u8, &mut budget)?;
    for y in 0..h {
        for x in 0..w {
            let argb = match input.get(x, y)? {
                Pixel::U8(v) => v.map(|c| c as f32),
                Pixel::U16(v) => v.map(|c| c as f32),
                Pixel::F32(v) => {
                    if w <= 24
                        && h <= 24
                        && v.iter()
                            .any(|c| c.is_finite() && !(-16.0..=16.0).contains(c))
                    {
                        return Err(Error::Unsupported);
                    }
                    v
                }
            };
            a[y * w + x] = [argb[1], argb[2], argb[3]];
            flags[y * w + x] = (argb[0] != 0.0) as u8;
        }
    }
    let amount = p.amount * p.scale;
    if !amount.is_finite() {
        return Err(Error::Unsupported);
    }
    // Host downsampling is <=1; checked coefficient allocation also handles larger valid rationals.
    if p.legacy {
        let radius = amount as usize;
        let size = radius
            .checked_mul(2)
            .and_then(|v| v.checked_add(1))
            .ok_or(Error::Overflow)?;
        let mut weights = allocate(size, 0.0, &mut budget)?;
        let sigma_base = ((p.amount * p.smoothness) / 100.0) * (p.amount / 3.0) * p.scale;
        for iteration in 1..=p.repeat {
            weights[radius] = 1.0;
            let sigma = sigma_base / iteration as f32;
            let denominator = (sigma + sigma) * sigma;
            for d in 1..=radius {
                let square = d.checked_mul(d).ok_or(Error::Overflow)? as f32;
                let weight = olm_math::expf(-square / denominator, Mode::Fma);
                weights[radius - d] = weight;
                weights[radius + d] = weight;
            }
            legacy_pass(&flags, &a, &mut b, &weights, w, h, p.bias == 2);
            legacy_pass(&flags, &b, &mut a, &weights, w, h, p.bias == 1);
        }
    } else {
        let decay = if p.repeat > 1 {
            olm_math::powf(3.0 / amount, 1.0 / (p.repeat - 1) as f32, Mode::Fma)
        } else {
            1.0
        };
        for iteration in 0..p.repeat {
            let radius_value =
                (amount as f64 * olm_math::pow(decay as f64, iteration as f64, Mode::Fma)) as f32;
            let radius = radius_value as usize;
            if radius == 0 {
                break;
            }
            let size = radius.checked_add(1).ok_or(Error::Overflow)?;
            let mut weight_budget = Budget::new(isize::MAX as usize);
            let mut weights = allocate(size, 0.0, &mut weight_budget)?;
            let sigma = radius_value / 3.0;
            let denominator = (sigma + sigma) * sigma;
            for (k, weight) in weights.iter_mut().enumerate() {
                let square = k.checked_mul(k).ok_or(Error::Overflow)? as f32;
                *weight = olm_math::expf(-square / denominator, Mode::Fma);
            }
            nonlegacy_pass(&flags, &a, &mut b, &weights, w, h, p.bias == 2, threads)?;
            nonlegacy_pass(&flags, &b, &mut a, &weights, w, h, p.bias == 1, threads)?;
        }
    }
    for y in 0..h {
        for x in 0..w {
            let rgb = a[y * w + x];
            let pixel = match input.get(x, y)? {
                Pixel::U8(v) => Pixel::U8([
                    v[0],
                    integer_store(rgb[0]) as u8,
                    integer_store(rgb[1]) as u8,
                    integer_store(rgb[2]) as u8,
                ]),
                Pixel::U16(v) => Pixel::U16([
                    v[0],
                    integer_store(rgb[0]) as u16,
                    integer_store(rgb[1]) as u16,
                    integer_store(rgb[2]) as u16,
                ]),
                Pixel::F32(v) => Pixel::F32([v[0], rgb[0], rgb[1], rgb[2]]),
            };
            output.set(x, y, pixel)?;
        }
    }
    Ok(())
}

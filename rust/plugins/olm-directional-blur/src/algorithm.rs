//! Platform-independent translation of core/dblur_{frontonly,rotate,rowdriver,field,noise}.
//! All transcendental operations use OLM-internal UCRT FMA, never platform libm.
use crate::{noise::Plane, rotate, rowdriver::Driver};
use olm_math::{expf, x86, Mode};
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error {
    Parameters,
    Size,
    Allocation,
    Layer,
}
pub type Result<T> = std::result::Result<T, Error>;
#[derive(Clone, Copy, Debug)]
pub struct Params {
    pub angle: f32,
    pub gain: f32,
    pub size: f32,
    pub front: i32,
    pub front_fade: i32,
    pub front_tail: f32,
    pub back: i32,
    pub back_fade: i32,
    pub back_tail: f32,
    pub noise: f32,
    pub noise_type: i32,
    pub seed: u32,
    pub offset: i32,
    pub thickness: f32,
}
impl Default for Params {
    fn default() -> Self {
        Self {
            angle: 0.0,
            gain: 1.0,
            size: 0.0,
            front: 0,
            front_fade: 0,
            front_tail: 0.0,
            back: 0,
            back_fade: 0,
            back_tail: 0.0,
            noise: 0.0,
            noise_type: 1,
            seed: 1,
            offset: 0,
            thickness: 10.0,
        }
    }
}
impl Params {
    pub fn sampled(mut self, scale: f32) -> Self {
        self.front = (self.front as f32 * scale) as i32;
        self.back = (self.back as f32 * scale) as i32;
        self.front_fade = (self.front_fade as f32 * scale) as i32;
        self.back_fade = (self.back_fade as f32 * scale) as i32;
        self.thickness *= scale;
        self
    }
    pub fn identity(&self) -> bool {
        self.front == 0 && self.back == 0 && self.front_fade == 0 && self.back_fade == 0
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Depth {
    U8,
    U16,
    F32,
}
pub(crate) fn zeros<T: Default + Clone>(n: usize) -> Result<Vec<T>> {
    let mut v = Vec::new();
    v.try_reserve_exact(n).map_err(|_| Error::Allocation)?;
    v.resize(n, T::default());
    Ok(v)
}
pub fn gaussian(count: i32) -> Vec<f32> {
    (0..count)
        .map(|i| {
            let ratio = count as f32 / 3.0;
            let square = ratio * ratio;
            let denominator = (square as f64 + square as f64 + 1.0e-5) as f32;
            expf(-(i * i) as f32 / denominator, Mode::Fma)
        })
        .collect()
}
fn components(image: &[[f32; 4]], w: usize, h: usize) -> Result<(Vec<[f32; 4]>, f32)> {
    let n = w * h;
    let mut map = zeros(n)?;
    let mut visited: Vec<bool> = zeros(n)?;
    let mut pending = Vec::new();
    let mut component = Vec::new();
    pending.try_reserve(n).map_err(|_| Error::Allocation)?;
    component.try_reserve(n).map_err(|_| Error::Allocation)?;
    let mut maximum = 0.0f32;
    for start in 0..n {
        if visited[start] {
            continue;
        }
        visited[start] = true;
        if !(image[start][3] > 0.0) {
            continue;
        }
        pending.clear();
        component.clear();
        pending.push(start);
        let min_y = start / w;
        let mut max_y = 0;
        while let Some(i) = pending.pop() {
            if !(image[i][3] > 0.0) {
                continue;
            }
            component.push(i);
            let x = i % w;
            let y = i / w;
            if y > min_y {
                max_y = max_y.max(y);
            }
            for (j, allowed) in [
                (i.wrapping_sub(1), x > 0),
                (i + 1, x + 1 < w),
                (i.wrapping_sub(w), y > 0),
                (i + w, y + 1 < h),
            ] {
                if allowed && !visited[j] {
                    visited[j] = true;
                    pending.push(j);
                }
            }
        }
        let area = component.len() as f32;
        maximum = maximum.max(area);
        let center = ((min_y + max_y) / 2) as f32;
        let half = max_y as f32 - center;
        for &i in &component {
            map[i] = [area, min_y as f32, center, half];
        }
    }
    Ok((map, maximum))
}
/// Input/output are straight normalized RGBA. Integer depths must be unpacked
/// with division by 255 (U8), multiplication by 1/32768 (U16).
/// Layer pixels are the same normalized RGBA and local geometry as input.
pub fn render(
    input: &[[f32; 4]],
    w: usize,
    h: usize,
    p: &Params,
    depth: Depth,
    layer: Option<&[[f32; 4]]>,
    threads: usize,
) -> Result<Vec<[f32; 4]>> {
    if w == 0 || h == 0 || w.checked_mul(h) != Some(input.len()) {
        return Err(Error::Size);
    }
    if p.identity() {
        return Ok(input.to_vec());
    }
    if !p.angle.is_finite()
        || !p.gain.is_finite()
        || !(0.0..=10.0).contains(&p.gain)
        || ![p.size, p.front_tail, p.back_tail, p.noise]
            .iter()
            .all(|v| v.is_finite() && (0.0..=100.0).contains(v))
        || !(0..=4000).contains(&p.front)
        || !(0..=4000).contains(&p.back)
        || !(0..=100).contains(&p.front_fade)
        || !(0..=100).contains(&p.back_fade)
    {
        return Err(Error::Parameters);
    }
    let diagonal = w
        .checked_mul(w)
        .and_then(|v| h.checked_mul(h).and_then(|b| v.checked_add(b)))
        .filter(|&v| v <= i32::MAX as usize)
        .ok_or(Error::Size)?;
    let half = 2 - ((diagonal as f32).sqrt() * -0.5) as i32;
    let ww = (w as i32 + (half - (w / 2) as i32) * 2) as usize;
    let hh = (h as i32 + (half - (h / 2) as i32) * 2) as usize;
    let n = ww.checked_mul(hh).ok_or(Error::Size)?;
    let ox = ww / 2 - w / 2;
    let oy = hh / 2 - h / 2;
    let mut a: Vec<[f32; 4]> = zeros(n)?;
    let mut b: Vec<[f32; 4]> = zeros(n)?;
    for y in 0..h {
        a[(y + oy) * ww + ox..(y + oy) * ww + ox + w].copy_from_slice(&input[y * w..(y + 1) * w]);
    }
    // Original literal and operation order are part of the numerical contract.
    #[allow(clippy::approx_constant)]
    let angle = (((p.angle as f64 + 90.0) / 180.0) * 3.14159265) as f32;
    rotate::rgba(&a, &mut b, ww, hh, angle);
    a.copy_from_slice(&b);
    let rows = hh / hh.min(32) * hh.min(32);
    if depth != Depth::U8 {
        b[..rows * ww].fill([0.0; 4]);
    }
    let (comp, mut divisor) = if p.size != 0.0 || p.front_tail != 0.0 || p.back_tail != 0.0 {
        components(&a, ww, hh)?
    } else {
        (vec![[1.0, 0.0, 0.0, 1.0]; n], 1.0)
    };
    if depth != Depth::F32 {
        if divisor <= 0.0 {
            divisor = 1.0;
        }
    } else if divisor == 0.0 {
        for y in 0..rows {
            for x in 2..ww {
                if a[y * ww + x][3] != 0.0 && x > p.back_fade as usize {
                    divisor = 1.0;
                    break;
                }
            }
            if divisor != 0.0 {
                break;
            }
        }
    }
    let mut noise = None;
    let mut field = None;
    if p.noise > 0.0 {
        if p.noise_type == 3 {
            let layer = layer.filter(|v| v.len() == w * h).ok_or(Error::Layer)?;
            let mut f = zeros(n)?;
            let mut rotated = zeros(n)?;
            for y in 0..h {
                for x in 0..w {
                    let v = layer[y * w + x];
                    let r = v[0] * v[3];
                    let g = v[1] * v[3];
                    let bl = v[2] * v[3];
                    f[(y + oy) * ww + x + ox] =
                        ((g as f64 * 0.587 + r as f64 * 0.299) + bl as f64 * 0.114) as f32;
                }
            }
            rotate::scalar(&f, &mut rotated, ww, hh, angle);
            field = Some(rotated);
        } else {
            if !(1..=2).contains(&p.noise_type) || !p.thickness.is_finite() || p.thickness <= 0.0 {
                return Err(Error::Parameters);
            }
            noise = Some(Plane::demanded(
                &a,
                ww,
                hh,
                rows,
                p.thickness,
                p.offset as f32 / 36.0,
                p.seed,
                p.noise_type == 1,
            )?);
        }
    }
    let driver = Driver {
        params: p,
        comp: &comp,
        divisor,
        weights: [
            gaussian(p.front),
            gaussian(p.back),
            gaussian(p.front_fade.max(1)),
            gaussian(p.back_fade.max(1)),
        ],
        noise,
        field,
        width: ww,
    };
    let mut den = zeros(n)?;
    let mut valid = zeros(n)?;
    let count = threads.max(1).min(rows);
    let chunk = (rows + count - 1) / count * ww;
    std::thread::scope(|scope| {
        for (i, (((src, dst), d), v)) in a[..rows * ww]
            .chunks(chunk)
            .zip(b[..rows * ww].chunks_mut(chunk))
            .zip(den[..rows * ww].chunks_mut(chunk))
            .zip(valid[..rows * ww].chunks_mut(chunk))
            .enumerate()
        {
            let driver = &driver;
            if count == 1 {
                driver.rows(0, src, dst, d, v);
            } else {
                scope.spawn(move || driver.rows(i * chunk / ww, src, dst, d, v));
            }
        }
    });
    for i in 0..n {
        if den[i] > 0.0 {
            for c in 0..3 {
                b[i][c] /= den[i];
            }
        }
    }
    a.fill([0.0; 4]);
    rotate::rgba(&b, &mut a, ww, hh, -angle);
    let mut out = zeros(w * h)?;
    for y in 0..h {
        for x in 0..w {
            let mut v = a[(y + oy) * ww + x + ox];
            for c in 0..3 {
                v[c] = match depth {
                    Depth::U8 => {
                        let z = v[c] * p.gain;
                        if z < 1.0 {
                            z
                        } else {
                            1.0
                        }
                    }
                    Depth::U16 => {
                        let z = v[c] * p.gain;
                        if 1.0 < z {
                            1.0
                        } else {
                            z
                        }
                    }
                    Depth::F32 => x86::min(x86::mul(p.gain, v[c]), 1.0),
                };
            }
            out[y * w + x] = v;
        }
    }
    Ok(out)
}

//! Pure CPU kernels translated from mac/OLMRadialBlur/Radial*.inc.
use crate::{math::*, noise};
use olm_core::{allocate, Budget, Depth, Error, Pixel, Result, View, ViewMut};

#[derive(Clone, Debug)]
pub struct Params {
    pub rotation: bool,
    pub center: [f64; 2],
    pub strength: [i32; 2],
    pub offset: [i32; 2],
    pub mode: [i32; 2],
    pub fade: [i32; 2],
    pub repeat: bool,
    pub ratio: f64,
    pub angle: f64,
    pub quality: f64,
    pub gain: f64,
    pub size: f64,
    pub noise: f64,
    pub noise_type: i32,
    pub seed: u32,
    pub phase: f32,
    pub thickness: f64,
    pub downsample: f32,
}
impl Default for Params {
    fn default() -> Self {
        Self {
            rotation: false,
            center: [0.0; 2],
            strength: [0; 2],
            offset: [0; 2],
            mode: [1; 2],
            fade: [0; 2],
            repeat: true,
            ratio: 1.0,
            angle: 0.0,
            quality: 5.0,
            gain: 1.0,
            size: 0.0,
            noise: 0.0,
            noise_type: 1,
            seed: 1,
            phase: 0.0,
            thickness: 10.0,
            downsample: 1.0,
        }
    }
}
impl Params {
    pub fn no_op(&self) -> bool {
        self.strength == [0; 2] && self.offset == [0; 2] && self.fade == [0; 2]
    }
    fn validate(&self) -> Result<()> {
        if self.noise_type == 3 {
            return Err(Error::Unsupported);
        }
        let valid = (1..=2).contains(&self.noise_type)
            && (1..=1000).contains(&self.seed)
            && self
                .center
                .iter()
                .all(|&v| v.is_finite() && (-32768.0..32768.0).contains(&v))
            && self.strength.iter().all(|v| (0..=2000).contains(v))
            && self.offset.iter().all(|v| (0..=500).contains(v))
            && self.fade.iter().all(|v| (0..=100).contains(v))
            && self.mode.iter().all(|v| (1..=3).contains(v))
            && (1.0..=5.0).contains(&self.ratio)
            && (1.0..=50.0).contains(&self.quality)
            && (0.0..=10.0).contains(&self.gain)
            && (0.0..=100.0).contains(&self.size)
            && (0.0..=100.0).contains(&self.noise)
            && (1.0..=100.0).contains(&self.thickness)
            && (-32768.0..32768.0).contains(&self.angle)
            && self.phase.is_finite()
            && self.downsample.is_finite()
            && self.downsample > 0.0
            && self.downsample <= 1.0;
        if valid {
            Ok(())
        } else {
            Err(Error::Unsupported)
        }
    }
}

/// Source samples are RGBA floats, preserving the native integer reciprocal.
fn read(p: Pixel) -> [f32; 4] {
    let a = match p {
        Pixel::U8(v) => v.map(|x| mul(x as f32, 1.0 / 255.0)),
        Pixel::U16(v) => v.map(|x| mul(x as f32, 1.0 / 32768.0)),
        Pixel::F32(v) => v,
    };
    [a[1], a[2], a[3], a[0]]
}
fn pack(p: [f32; 4], depth: Depth) -> Pixel {
    let a = [p[3], p[0], p[1], p[2]];
    match depth {
        Depth::U8 => Pixel::U8(a.map(|x| int(mul(x, 255.0)) as u8)),
        Depth::U16 => Pixel::U16(a.map(|x| int(mul(x, 32768.0)) as u16)),
        Depth::F32 => Pixel::F32(a),
    }
}
pub(crate) fn sample_rgba(
    src: &[[f32; 4]],
    w: usize,
    h: usize,
    x: f32,
    y: f32,
    repeat: bool,
) -> ([f32; 4], bool) {
    let xi = int(x);
    let yi = int(y);
    let gate = xi > -2 && xi < w as i32 && yi > -2 && yi < h as i32;
    if !repeat && !gate {
        return ([0.0; 4], false);
    }
    let fx = sub(x, xi as f32);
    let fy = sub(y, yi as f32);
    let weights = [
        mul(sub(1.0, fx), sub(1.0, fy)),
        mul(fx, sub(1.0, fy)),
        mul(sub(1.0, fx), fy),
        mul(fx, fy),
    ];
    let coords = [(xi, yi), (xi + 1, yi), (xi, yi + 1), (xi + 1, yi + 1)];
    let mut out = [0.0; 4];
    let mut weight_sum = 0.0;
    for ((mut px, mut py), weight) in coords.into_iter().zip(weights) {
        if repeat {
            px = px.clamp(0, w as i32 - 1);
            py = py.clamp(0, h as i32 - 1);
        }
        if px < 0 || py < 0 || px >= w as i32 || py >= h as i32 {
            continue;
        }
        let p = src[py as usize * w + px as usize];
        let aw = mul(weight, p[3]);
        out[3] = add(aw, out[3]);
        weight_sum = add(weight_sum, weight);
        for c in 0..3 {
            out[c] = add(mul(aw, p[c]), out[c]);
        }
    }
    if out[3] != 0.0 && !out[3].is_nan() {
        let inverse = div(1.0, out[3]);
        for c in 0..3 {
            out[c] = if c == 2 {
                mul(inverse, out[c])
            } else {
                mul(out[c], inverse)
            };
        }
        if !repeat {
            out[3] = div(out[3], weight_sum);
        }
        (out, gate)
    } else {
        (out, false)
    }
}
pub(crate) fn sample_scalar(src: &[f32], w: usize, h: usize, x: f32, y: f32, repeat: bool) -> f32 {
    let xi = int(x);
    let yi = int(y);
    let fx = sub(x, xi as f32);
    let fy = sub(y, yi as f32);
    let weights = [
        mul(sub(1.0, fx), sub(1.0, fy)),
        mul(sub(1.0, fy), fx),
        mul(sub(1.0, fx), fy),
        mul(fy, fx),
    ];
    let coords = [(xi, yi), (xi + 1, yi), (xi, yi + 1), (xi + 1, yi + 1)];
    let mut result = 0.0;
    let mut ws = 0.0;
    for (tap, ((mut px, mut py), weight)) in coords.into_iter().zip(weights).enumerate() {
        if repeat {
            px = px.clamp(0, w as i32 - 1);
            py = py.clamp(0, h as i32 - 1);
        }
        if px < 0 || py < 0 || px >= w as i32 || py >= h as i32 {
            continue;
        }
        let index = py as usize * w + px as usize + usize::from(repeat && tap % 2 == 1);
        let value = if index < w * h { src[index] } else { 0.0 };
        let term = mul(weight, value);
        result = if repeat && tap == 0 {
            term
        } else {
            add(result, term)
        };
        ws = add(ws, weight);
    }
    if repeat {
        result
    } else if ws != 0.0 {
        div(result, ws)
    } else {
        0.0
    }
}
pub(crate) fn size_factors(src: &[[f32; 4]], w: usize, h: usize, percentage: f32) -> Vec<f32> {
    let count = w * h;
    let sv = mul(percentage, 0.01);
    if sv as f64 <= 0.0001 {
        let mut p = vec![1.0; count + 1];
        p[count] = 0.0;
        return p;
    }
    let mask: Vec<bool> = src.iter().map(|p| !(p[3] <= 0.0)).collect();
    let mut labels = vec![0; count];
    let mut areas = vec![0i32];
    let mut pending = Vec::new();
    for start in 0..count {
        if labels[start] != 0 || !mask[start] {
            continue;
        }
        let label = areas.len();
        labels[start] = label;
        pending.push(start);
        let mut area = 0;
        while let Some(cell) = pending.pop() {
            area += 1;
            let x = cell % w;
            let y = cell / w;
            for (ok, n) in [
                (x > 0, cell.wrapping_sub(1)),
                (x + 1 < w, cell + 1),
                (y > 0, cell.wrapping_sub(w)),
                (y + 1 < h, cell + w),
            ] {
                if ok && labels[n] == 0 && mask[n] {
                    labels[n] = label;
                    pending.push(n);
                }
            }
        }
        areas.push(area);
    }
    for edge in (w - 1..count).step_by(w) {
        if edge + 1 < count && mask[edge] && mask[edge + 1] {
            areas[labels[edge]] += 1;
        }
    }
    let max = *areas.iter().max().unwrap();
    let inverse = if max > 0 { div(1.0, max as f32) } else { 1.0 };
    let mut out = vec![0.0; count + 1];
    for cell in 0..count {
        let mut label = labels[cell];
        if cell > 0 && cell % w == 0 && mask[cell - 1] && mask[cell] {
            label = label.max(labels[cell - 1]);
        }
        out[cell] = add(mul(mul(areas[label] as f32, inverse), sv), sub(1.0, sv));
    }
    out
}
fn resolved(strength: i32, offset: i32, mode: i32, radii: i32, r: i32) -> i32 {
    let dynamic = int(mul(((radii / 2) * offset) as f32, div(1.0, (r + 1) as f32)));
    match mode {
        1 => strength + dynamic,
        2 => strength.max(dynamic),
        3 => dynamic,
        _ => strength,
    }
}

pub fn render(
    p: &Params,
    input: &View<'_>,
    output: &mut ViewMut<'_>,
    threads: usize,
) -> Result<()> {
    let l = input.layout();
    let o = output.layout();
    if l.depth != o.depth {
        return Err(Error::Unsupported);
    }
    let w = l.width;
    let h = l.height;
    let crop_x = o.origin.0 - l.origin.0;
    let crop_y = o.origin.1 - l.origin.1;
    if crop_x < 0 || crop_y < 0 || crop_x as usize + o.width > w || crop_y as usize + o.height > h {
        return Err(Error::Geometry);
    }
    if p.no_op() {
        for y in 0..o.height {
            for x in 0..o.width {
                output.set(x, y, input.get(x + crop_x as usize, y + crop_y as usize)?)?;
            }
        }
        return Ok(());
    }
    // The original/C++ owner returns the input before touching the noise path
    // when all six Strength/Offset/Fade controls are zero.
    p.validate()?;
    let step = div(1.0, p.quality as f32);
    let radians = (step as f64 * RAD) as f32;
    let angular = int(div(360.0, step)) as usize;
    let (min_r, max_r) = radius_bounds(
        w as i32,
        h as i32,
        p.center[0] as f32,
        p.center[1] as f32,
        p.ratio as f32,
    );
    if max_r < min_r {
        return Err(Error::Geometry);
    }
    let radii = (max_r - min_r + 1) as usize;
    let count = angular.checked_mul(radii).ok_or(Error::Overflow)?;
    // Same 1 GiB memory ceiling as the C++ Smart owner, reserving 64 MiB.
    let mut budget = Budget::new((1 << 30) - (64 << 20));
    budget.reserve(count.checked_mul(80).ok_or(Error::Overflow)?)?;
    let mut src = allocate(
        w.checked_mul(h).ok_or(Error::Overflow)?,
        [0.0; 4],
        &mut budget,
    )?;
    for y in 0..h {
        for x in 0..w {
            src[y * w + x] = read(input.get(x, y)?);
        }
    }
    let size_active = mul(p.size as f32, 0.01) as f64 > 0.0001;
    let size = size_factors(&src, w, h, p.size as f32);
    let mut span = size.clone();
    if p.noise != 0.0 {
        let cell = mul(p.thickness as f32, p.downsample);
        let (np, nw) = noise::generate(w, h, cell, p.phase, p.seed);
        let nv = mul(p.noise as f32, 0.01);
        for y in 0..h {
            for x in 0..w {
                let mixed = add(
                    mul(nv, noise::sample(&np, nw, cell, x, y, p.noise_type == 1)),
                    sub(1.0, nv),
                );
                span[y * w + x] = if p.size != 0.0 {
                    mul(mixed, span[y * w + x])
                } else {
                    mixed
                };
            }
        }
    }
    let fixed = ((p.angle * 65536.0) * RAD) as i32;
    let ca = olm_math::cos(fixed as f64, olm_math::Mode::Fma) as f32;
    let sa = olm_math::sin(fixed as f64, olm_math::Mode::Fma) as f32;
    let trig: Vec<_> = (0..angular).map(|a| trig(mul(a as f32, radians))).collect();
    let mut polar = vec![[0.0; 4]; count];
    let mut valid = vec![false; count];
    let mut spans = vec![0.0; count];
    let mut fades = vec![1.0; count];
    for a in 0..angular {
        for r in 0..radii {
            let radius = (min_r + r as i32) as f32;
            let (s, c) = trig[a];
            let sx0 = mul(radius, c);
            let sy0 = if p.rotation {
                mul(mul(radius, p.ratio as f32), s)
            } else {
                mul(radius, mul(s, p.ratio as f32))
            };
            let sx = add(sub(mul(ca, sx0), mul(sa, sy0)), p.center[0] as f32);
            let sy = add(add(mul(sa, sx0), mul(ca, sy0)), p.center[1] as f32);
            let cell = if p.rotation {
                r * angular + a
            } else {
                a * radii + r
            };
            (polar[cell], valid[cell]) = sample_rgba(&src, w, h, sx, sy, p.repeat);
            spans[cell] = sample_scalar(&span, w, h, sx, sy, p.repeat);
            if size_active {
                fades[cell] = sample_scalar(&size, w, h, sx, sy, p.repeat);
            }
        }
    }
    let blurred = if p.rotation {
        rotation(
            p, step, angular, radii, &polar, &valid, &spans, &fades, threads,
        )?
    } else {
        zoom(
            p,
            angular,
            radii,
            &polar,
            &valid,
            &spans,
            if p.size != 0.0 { Some(&fades) } else { None },
            threads,
        )?
    };
    for y in 0..o.height {
        for x in 0..o.width {
            let dx = sub((x + crop_x as usize) as f32, p.center[0] as f32);
            let dy = sub((y + crop_y as usize) as f32, p.center[1] as f32);
            let ex = if p.rotation {
                add(mul(ca, dx), mul(sa, dy))
            } else {
                add(mul(sa, dy), mul(ca, dx))
            };
            let ey = div(sub(mul(ca, dy), mul(sa, dx)), p.ratio as f32);
            let radius = sub(add(mul(ey, ey), mul(ex, ex)).sqrt(), min_r as f32);
            let mut angle = olm_math::atan2f(ey, ex, olm_math::Mode::Fma);
            if angle < 0.0 {
                angle = (angle as f64 + TURN) as f32;
            }
            let mut ai = if p.rotation {
                mul(
                    angle,
                    div(
                        1.0,
                        ((1.0 / (p.quality as f32 as f64)) as f32 as f64 * RAD) as f32,
                    ),
                )
            } else if angle < 0.0 {
                0.0
            } else {
                div(angle, radians)
            };
            if !p.rotation && ai >= angular as f32 {
                ai = sub(ai, angular as f32);
            }
            let (xx, yy) = if p.rotation {
                (ai, radius)
            } else {
                (radius, ai)
            };
            let floor = p.rotation || l.depth == Depth::U8;
            let xi = if floor { int(xx.floor()) } else { int(xx) };
            let yi = if floor { int(yy.floor()) } else { int(yy) };
            let fx = sub(xx, xi as f32);
            let fy = sub(yy, yi as f32);
            let (x0, x1, y0, y1, pw) = if p.rotation {
                (
                    xi.rem_euclid(angular as i32),
                    (xi + 1).rem_euclid(angular as i32),
                    yi.clamp(0, radii as i32 - 1),
                    (yi + 1).clamp(0, radii as i32 - 1),
                    angular,
                )
            } else {
                let a = yi.rem_euclid(angular as i32);
                let b = (a + 1) % angular as i32;
                if l.depth == Depth::U8 {
                    (
                        xi.clamp(0, radii as i32 - 1),
                        (xi + 1).clamp(0, radii as i32 - 1),
                        a,
                        b,
                        radii,
                    )
                } else {
                    (xi, xi + 1, a, b, radii)
                }
            };
            let coords = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)];
            let weights = [
                mul(sub(1.0, fx), sub(1.0, fy)),
                mul(sub(1.0, fy), fx),
                mul(sub(1.0, fx), fy),
                mul(fy, fx),
            ];
            let mut taps = [[0.0; 4]; 4];
            for (i, (tx, ty)) in coords.into_iter().enumerate() {
                let idx = ty as i64 * pw as i64 + tx as i64;
                if idx < 0 || idx >= count as i64 {
                    return Err(Error::Bounds);
                }
                taps[i] = blurred[idx as usize];
            }
            let order = if p.rotation {
                [0, 2, 1, 3]
            } else {
                [0, 1, 2, 3]
            };
            let aw = std::array::from_fn::<_, 4, _>(|i| mul(weights[i], taps[i][3]));
            let mut alpha = 0.0;
            let mut result = [0.0; 4];
            for i in order {
                alpha = add(aw[i], alpha);
                for c in 0..3 {
                    result[c] = add(mul(aw[i], taps[i][c]), result[c]);
                }
            }
            let inverse = if alpha != 0.0 && !alpha.is_nan() {
                div(1.0, alpha)
            } else {
                1.0
            };
            for c in 0..3 {
                let normalized = if c == 2 {
                    mul(inverse, result[c])
                } else {
                    mul(result[c], inverse)
                };
                let gain = mul(normalized, p.gain as f32);
                result[c] = if gain < 1.0 { gain } else { 1.0 };
            }
            result[3] = alpha;
            output.set(x, y, pack(result, l.depth))?;
        }
    }
    Ok(())
}

fn zoom(
    p: &Params,
    angles: usize,
    radii: usize,
    polar: &[[f32; 4]],
    valid: &[bool],
    span: &[f32],
    fade: Option<&[f32]>,
    threads: usize,
) -> Result<Vec<[f32; 4]>> {
    let strength = p.strength.map(|x| int(mul(x as f32, p.downsample)));
    let fade_span = p.fade.map(|x| int(mul(x as f32, p.downsample)));
    let weights = strength.map(fade_weights);
    let fades = fade_span.map(fade_weights);
    let preserve = p.noise != 0.0 && mul(p.size as f32, 0.01) as f64 <= 0.0001;
    let mut out = vec![[0.0; 4]; angles * radii];
    olm_core::parallel_rows(&mut out, radii, threads, |a, row| {
        let base = a * radii;
        let mut alpha = vec![0.0; radii];
        let mut max = vec![0.0; radii];
        let mut source = vec![0.0; radii];
        for r in 0..radii {
            let cell = base + r;
            let color = polar[cell];
            let factor = if let Some(f) = fade {
                f[cell]
            } else if fade_span[0] > 0 || fade_span[1] > 0 {
                1.0
            } else {
                span[cell]
            };
            let zero = color[3] == 0.0
                || color[3].is_nan()
                || factor.is_nan()
                || (factor == 0.0 && !preserve);
            let mut scalar = color[3];
            if zero {
                scalar = 0.0;
            } else if fade_span[0] > 0 || fade_span[1] > 0 {
                let mut sum = color[3];
                let mut ws = 1.0;
                let inverse = div(1.0, factor);
                for d in 0..2 {
                    let limit = (if d == 0 { r } else { radii - r })
                        .min(int(mul(fade_span[d] as f32, factor)).max(0) as usize);
                    for k in 1..limit {
                        let index = int(mul(k as f32, inverse)) as usize;
                        let weight = fades[d][index];
                        let from = if d == 0 { cell - k } else { cell + k };
                        sum = add(sum, mul(weight, polar[from][3]));
                        ws = add(ws, weight);
                    }
                }
                scalar = div(sum, ws);
            }
            source[r] = scalar;
            alpha[r] = scalar;
            max[r] = scalar;
            for c in 0..3 {
                row[r][c] = if zero { 0.0 } else { mul(scalar, color[c]) };
            }
        }
        for r in 0..radii {
            let cell = base + r;
            let scalar = source[r];
            let factor = span[cell];
            if !valid[cell] || scalar == 0.0 || scalar.is_nan() || factor == 0.0 || factor.is_nan()
            {
                continue;
            }
            let inverse = div(1.0, factor);
            for d in 0..2 {
                let limit = (if d == 0 { radii - r } else { r })
                    .min(int(mul(strength[d] as f32, factor)).max(0) as usize);
                for k in 1..limit {
                    let idx = int(mul(k as f32, inverse));
                    if idx < 0 || idx as usize >= weights[d].len() {
                        continue;
                    }
                    let aw = mul(scalar, weights[d][idx as usize]);
                    let to = if d == 0 { r + k } else { r - k };
                    for c in 0..3 {
                        row[to][c] = add(mul(aw, polar[cell][c]), row[to][c]);
                    }
                    alpha[to] = add(aw, alpha[to]);
                    if max[to] < aw {
                        max[to] = aw;
                    }
                }
            }
        }
        for r in 0..radii {
            for c in 0..3 {
                row[r][c] = if max[r] == 0.0 || max[r].is_nan() {
                    0.0
                } else {
                    div(row[r][c], alpha[r])
                };
            }
            row[r][3] = max[r];
        }
    })?;
    Ok(out)
}
fn rotation(
    p: &Params,
    step: f32,
    angles: usize,
    radii: usize,
    polar: &[[f32; 4]],
    valid: &[bool],
    span: &[f32],
    fade: &[f32],
    threads: usize,
) -> Result<Vec<[f32; 4]>> {
    let scale = 0.2 / step as f64;
    let control = |v: i32| ((v as f64 * scale) as i32).max(0);
    let strength = p.strength.map(control);
    let offset = p.offset.map(control);
    let fade_span = p.fade.map(control);
    let weights = fade_span.map(fade_weights);
    let count = angles * radii;
    let mut seed = vec![0.0; count];
    let mut accum = vec![[0.0; 4]; count];
    let mut max = vec![0.0; count];
    let polar_alpha = |i: i64| {
        if i < 0 {
            0.0
        } else if (i as usize) < count {
            polar[i as usize][3]
        } else {
            *span.get(i as usize - count).unwrap_or(&0.0)
        }
    };
    // Prepass reads immutable adjacent rows, then all scatter rows are independent.
    for r in 0..radii {
        for a in 0..angles {
            let cell = r * angles + a;
            let color = polar[cell];
            if color[3] == 0.0 || color[3].is_nan() {
                continue;
            }
            let factor = fade[cell];
            let inverse = div(1.0, factor);
            let mut sum = color[3];
            let mut ws = 1.0;
            for d in 0..2 {
                let limit = int(mul(fade_span[d] as f32, factor));
                let mut pointer = cell as i64 + if d == 0 { -1 } else { 1 };
                let mut pos = a as i32;
                for k in 1..limit {
                    let index = int(mul(k as f32, inverse)) as usize;
                    let weight = weights[d][index];
                    sum = add(sum, mul(polar_alpha(pointer), weight));
                    ws = add(ws, weight);
                    if d == 0 {
                        pos -= 1;
                        if pos < 0 {
                            pos = angles as i32 - 1;
                            pointer = (r * angles + angles - 1) as i64;
                        }
                        pointer -= 1;
                    } else {
                        pos += 1;
                        if pos >= angles as i32 {
                            pos = 0;
                            pointer = (r * angles) as i64;
                        }
                        pointer += 1;
                    }
                }
            }
            if p.size != 0.0 && factor == 0.0 {
                continue;
            }
            let alpha = div(sum, ws);
            seed[cell] = alpha;
            max[cell] = alpha;
            for c in 0..3 {
                accum[cell][c] = mul(alpha, color[c]);
            }
            accum[cell][3] = alpha;
        }
    }
    // Store row-local maxima in the output scratch to avoid cross-row mutation.
    let mut out = vec![[0.0; 4]; count];
    olm_core::parallel_rows(&mut out, angles, threads, |r, row| {
        let base = r * angles;
        let mut data = accum[base..base + angles].to_vec();
        let mut maximum = max[base..base + angles].to_vec();
        let spans: [i32; 2] = std::array::from_fn(|d| {
            resolved(strength[d], offset[d], p.mode[d], radii as i32, r as i32)
        });
        let mut cache = std::collections::BTreeMap::new();
        for a in 0..angles {
            let cell = base + a;
            let alpha = seed[cell];
            let factor = span[cell];
            if !valid[cell] || alpha == 0.0 || alpha.is_nan() || factor == 0.0 || factor.is_nan() {
                continue;
            }
            for d in 0..2 {
                let length = int(mul(spans[d].min(3000) as f32, factor)).max(0);
                if length <= 1 {
                    continue;
                }
                let weights = cache
                    .entry(length)
                    .or_insert_with(|| rotation_weights(length));
                for k in 1..length {
                    let to =
                        (a as i32 + if d == 0 { k } else { -k }).rem_euclid(angles as i32) as usize;
                    let contribution = mul(alpha, weights[k as usize]);
                    for c in 0..3 {
                        data[to][c] = add(mul(contribution, polar[cell][c]), data[to][c]);
                    }
                    data[to][3] = add(contribution, data[to][3]);
                    if maximum[to] <= contribution && contribution != maximum[to] {
                        maximum[to] = contribution;
                    }
                }
            }
        }
        for a in 0..angles {
            for c in 0..3 {
                row[a][c] = if maximum[a] != 0.0 && !maximum[a].is_nan() {
                    div(data[a][c], data[a][3])
                } else {
                    0.0
                };
            }
            row[a][3] = maximum[a];
        }
    })?;
    Ok(out)
}

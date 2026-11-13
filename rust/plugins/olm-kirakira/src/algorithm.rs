//! Platform-independent KiraRender/KiraFilters translation. Internal pixels RGBA.
use crate::{filters as f, ramp::Ramp};
use olm_core::{Depth, Pixel, View, ViewMut};
use olm_math::{self as math, Mode::Fma};
#[derive(Clone, Debug)]
pub struct Params {
    pub fused_filters: bool,
    pub fused_resize: bool,
    pub channel: i32,
    pub blur: i32,
    pub merge: i32,
    pub approximate: bool,
    pub gain: f64,
    pub strength: f64,
    pub fade: f64,
    pub glow_opacity: f64,
    pub source_opacity: f64,
    /// The original consumes raw signed 16.16 angle bits as degrees.
    pub rotation: f64,
    pub lengths: [i32; 5],
    pub colors: [[f32; 3]; 5],
    pub use_ramp: [bool; 5],
    pub ramps: [Ramp; 5],
}
impl Default for Params {
    fn default() -> Self {
        Self {
            fused_filters: true,
            fused_resize: true,
            channel: 1,
            blur: 2,
            merge: 1,
            approximate: false,
            gain: 1.0,
            strength: 1.0,
            fade: 0.0,
            glow_opacity: 1.0,
            source_opacity: 1.0,
            rotation: 0.0,
            lengths: [50, 50, 50, 50, 0],
            colors: [[1.0; 3]; 5],
            use_ramp: [false; 5],
            ramps: [Ramp::default(); 5],
        }
    }
}
pub fn clamp(v: f32) -> f32 {
    if v.is_nan() || v <= 0.0 {
        0.0
    } else if v >= 1.0 {
        1.0
    } else {
        v
    }
}
pub fn compose(g: [f32; 4], s: [f32; 4], go: f32, so: f32, merge: i32) -> [f32; 4] {
    if g[3] + s[3] == 0.0 {
        return [0.0; 4];
    }
    let ga = clamp(g[3] * go);
    let sa = clamp(so * s[3]);
    let sum = sa + ga;
    if merge == 1 && sum == 0.0 {
        return [0.0; 4];
    }
    let mut out = [0.0; 4];
    let inverse = 1.0 / sum;
    for c in 0..3 {
        let v = sa * s[c] + ga * g[c];
        out[c] = clamp(if merge == 2 { v } else { v * inverse });
    }
    out[3] = clamp(sum);
    out
}
impl Params {
    /// Retained C++ generic legacy tuple family. Mode 4 is absent from the
    /// original declared popup range, but old stored parameter values can use it.
    pub fn legacy_admitted(&self, w: usize, h: usize) -> bool {
        if w < 9
            || h < 7
            || self.fade != 0.0
            || self.glow_opacity != 1.0
            || self.channel != 1
            || self.approximate
            || self.strength != 1.0
            || self.source_opacity != 1.0
            || self.lengths[0] != 0
            || self.lengths[2] != 0
            || self.use_ramp[0]
            || self.use_ramp[2]
            || self.use_ramp[3]
            || self.colors != [[1.0; 3]; 5]
            || !self.ramps.iter().all(|r| r.equal_active(&Ramp::default()))
        {
            return false;
        }
        let h = self.lengths[1];
        let d = self.lengths[3];
        let highlight = self.lengths[4];
        let only_h = d == 0 && highlight == 0 && !self.use_ramp[4];
        let only_high =
            h == 0 && !self.use_ramp[1] && d == 0 && highlight == 3 && !self.use_ramp[4];
        match self.blur {
            1 => {
                self.merge == 1
                    && ((self.gain == 0.1
                        && [0.0, 1.0].contains(&self.rotation)
                        && h == 7
                        && !self.use_ramp[1]
                        && only_h)
                        || (self.gain == 1.0 && self.rotation == 0.0 && only_high))
            }
            2 => {
                (self.merge == 2
                    && ((self.gain == 0.1 && [0.0, 1.0].contains(&self.rotation))
                        || (self.gain == 0.73 && self.rotation == 22.0))
                    && h == 7
                    && self.use_ramp[1]
                    && only_h)
                    || (self.merge == 1 && self.gain == 1.0 && self.rotation == 0.0 && only_high)
            }
            3 => {
                self.merge == 1
                    && self.gain == 0.1
                    && [0.0, 1.0].contains(&self.rotation)
                    && (1..=300).contains(&h)
                    && !self.use_ramp[1]
                    && only_h
            }
            4 => {
                (self.merge == 1 && self.gain == 1.0 && self.rotation == 0.0 && only_high)
                    || (self.merge == 2
                        && self.gain == 0.73
                        && self.rotation == 1.0
                        && ((h == 5 && self.use_ramp[1] && only_h)
                            || (h == 0
                                && !self.use_ramp[1]
                                && d == 7
                                && highlight == 0
                                && !self.use_ramp[4])
                            || (h == 0
                                && !self.use_ramp[1]
                                && d == 0
                                && highlight == 3
                                && self.use_ramp[4])
                            || (h == 5
                                && self.use_ramp[1]
                                && d == 7
                                && highlight == 3
                                && self.use_ramp[4])))
            }
            _ => false,
        }
    }
    pub fn color_owner(&self) -> bool {
        (1..=3).contains(&self.blur) && [3, 5, 6].contains(&self.channel)
    }
    pub fn recovered(&self) -> bool {
        (1..=3).contains(&self.blur) && (1..=6).contains(&self.channel)
    }
    pub fn linear(&self) -> bool {
        self.approximate && self.recovered()
    }
    pub fn admitted(&self, w: usize, h: usize) -> bool {
        // Smart admission in KiraAdmission.inc, including the existing custom
        // ramp refusal. Serialization remains supported independently.
        if w == 0 || h == 0 || w > i32::MAX as usize / 4 || h > i32::MAX as usize / 4 {
            return false;
        }
        if self.legacy_admitted(w, h) {
            return true;
        }
        if !self.recovered() || ![1, 2].contains(&self.merge) {
            return false;
        }
        if self.approximate && (w < 4 || h < 4) {
            return false;
        }
        if self.lengths == [0; 5]
            && self.source_opacity == 1.0
            && (0.0..=100.0).contains(&self.glow_opacity)
        {
            return true;
        }
        if !(1.0..=100.0).contains(&self.gain)
            || !(0.0..=10.0).contains(&self.strength)
            || !(0.0..=100.0).contains(&self.glow_opacity)
            || !(0.0..=1.0).contains(&self.source_opacity)
            || !(self.rotation > -2147483648.0 && self.rotation <= 2147483512.0)
        {
            return false;
        }
        if ([2, 4].contains(&self.channel) || (self.approximate && self.channel != 1))
            && !(0.0..=0.2f32 as f64).contains(&self.fade)
        {
            return false;
        }
        for j in 0..5 {
            if self.lengths[j] < 0 || self.lengths[j] > if j == 4 { 500 } else { 1000 } {
                return false;
            }
            if self.lengths[j] == 0 {
                continue;
            }
            if self.use_ramp[j] {
                if !self.ramps[j].equal_active(&Ramp::default()) {
                    return false;
                }
            } else if !self.colors[j].iter().all(|v| (0.0..=1.0).contains(v)) {
                return false;
            }
        }
        true
    }
}
pub fn seed(pixels: &[[f32; 4]], p: &Params) -> Vec<f32> {
    let recovered = p.recovered();
    let color = p.color_owner();
    let mut out = vec![0.0; pixels.len() * if color { 4 } else { 1 }];
    let exponent = if recovered {
        (p.strength as f32).max(0.001) as f64
    } else {
        p.strength.max(1.0e-6)
    };
    let fade = p.fade as f32;
    let pow = |v: f32| {
        if recovered {
            math::powf(v, exponent as f32, Fma)
        } else {
            math::pow(v as f64, exponent, Fma) as f32
        }
    };
    let apply_fade = |v: f32| {
        if v == 0.0 || (recovered && v.is_nan()) {
            return 0.0;
        }
        if fade < v {
            return pow(v);
        }
        let n = v / fade;
        if recovered {
            math::powf(n, 2.0, Fma) * math::powf(fade, exponent as f32, Fma)
        } else {
            n * n * math::pow(fade as f64, exponent, Fma) as f32
        }
    };
    for (i, s) in pixels.iter().enumerate() {
        if color {
            for c in 0..3 {
                out[i * 4 + c] = math::powf(s[c], p.strength as f32 + 1.0, Fma) * s[3];
            }
            out[i * 4 + 3] = s[3];
            continue;
        }
        out[i] = match p.channel {
            1 => pow(s[3]),
            2 => {
                let l = if recovered {
                    (s[1] as f64 * 0.7152 + s[0] as f64 * 0.2126 + s[2] as f64 * 0.0722) as f32
                } else {
                    s[0] * 0.2126 + s[1] * 0.7152 + s[2] * 0.0722
                };
                apply_fade(l) * s[3]
            }
            4 => {
                let gb = if s[1] >= s[2] { s[1] } else { s[2] };
                let m = if s[0] >= gb { s[0] } else { gb };
                apply_fade(m) * s[3]
            }
            _ => pow(s[0]).max(pow(s[1])).max(pow(s[2])) * s[3],
        };
    }
    out
}
pub fn pixels(
    source: &[[f32; 4]],
    w: usize,
    h: usize,
    p: &Params,
    scale: f32,
) -> olm_core::Result<Vec<[f32; 4]>> {
    if source.len() != w.checked_mul(h).ok_or(olm_core::Error::Bounds)? {
        return Err(olm_core::Error::Bounds);
    }
    if !p.admitted(w, h) {
        return Err(olm_core::Error::Unsupported);
    }
    let approx = p.approximate && scale > 0.5;
    let (ww, wh) = if approx {
        (1.max(w / 2), 1.max(h / 2))
    } else {
        (w, h)
    };
    let ls = if approx { scale * 0.5 } else { scale };
    let lengths = p.lengths.map(|v| (v as f32 * ls) as i32);
    let work = if approx {
        f::resize_profile(source, w, h, ww, wh, p.linear(), p.fused_resize)
    } else {
        source.to_vec()
    };
    let seed = seed(&work, p);
    let color = p.color_owner();
    let channels = if color { 4 } else { 1 };
    let n = ww * wh;
    let mut glow = vec![[0.0f32; 4]; n];
    let angles = [90.0, 0.0, 45.0, 135.0, 0.0];
    let mut norms = lengths.map(|v| v as f32);
    norms[4] = ((lengths[4] * 2 + 1) * (lengths[4] * 2 + 1)) as f32;
    if p.blur == 2 {
        for norm in &mut norms[..4] {
            *norm = *norm * *norm * *norm;
        }
        norms[4] *= norms[4];
        norms[4] *= norms[4];
    }
    for j in 0..5 {
        if lengths[j] <= 0 {
            continue;
        }
        let mut ray = vec![0.0; seed.len()];
        for c in 0..channels {
            let plane: Vec<f32> = (0..n).map(|i| seed[i * channels + c]).collect();
            let filtered = if j < 4 {
                f::ray_profile(
                    &plane,
                    ww,
                    wh,
                    lengths[j],
                    p.rotation + angles[j],
                    p.blur,
                    !color,
                    p.recovered(),
                    p.fused_filters,
                )
            } else if p.blur == 3 {
                f::gaussian_highlight_profile(&plane, ww, wh, lengths[j], p.fused_filters, color)
            } else {
                f::box_highlight(
                    &plane,
                    ww,
                    wh,
                    lengths[j] * 2 + 1,
                    if p.blur == 1 { 1 } else { 3 },
                    !color,
                )
            };
            for i in 0..n {
                ray[i * channels + c] = filtered[i];
            }
        }
        for i in 0..n {
            let g = &mut glow[i];
            if color {
                let a = ray[i * 4 + 3];
                if !(a as f64 > 0.001) {
                    continue;
                }
                let inv = 1.0 / a;
                let a1 = clamp(a * if norms[j] == 0.0 { 0.0 } else { 1.0 / norms[j] });
                for c in 0..3 {
                    g[c] = inv * ray[i * 4 + c] * a1 * p.gain as f32 + g[c];
                }
                g[3] = a1 + g[3];
            } else {
                if ray[i] <= 0.001 {
                    continue;
                }
                let a = clamp(ray[i] * p.gain as f32);
                let rgb = if p.use_ramp[j] {
                    p.ramps[j].sample(a)
                } else {
                    p.colors[j]
                };
                for c in 0..3 {
                    g[c] += a * rgb[c];
                }
                g[3] = g[3] + a - g[3] * a;
            }
        }
    }
    for g in &mut glow {
        if g[3] > if color { 0.0 } else { 1.0e-6 } {
            if color {
                g[3] = clamp(g[3]);
            }
            let inverse = 1.0 / g[3];
            for c in 0..3 {
                g[c] *= inverse;
            }
        }
    }
    if approx {
        glow = f::resize_profile(&glow, ww, wh, w, h, p.linear(), p.fused_resize);
    }
    Ok(source
        .iter()
        .zip(glow)
        .map(|(s, g)| {
            compose(
                g,
                *s,
                p.glow_opacity as f32,
                p.source_opacity as f32,
                p.merge,
            )
        })
        .collect())
}
pub fn render(
    input: &View<'_>,
    output: &mut ViewMut<'_>,
    p: &Params,
    scale: f32,
) -> olm_core::Result<()> {
    let a = input.layout();
    let b = output.layout();
    if b.width > a.width || b.height > a.height || a.depth != b.depth {
        return Err(olm_core::Error::Bounds);
    }
    let mut src = Vec::with_capacity(a.width * a.height);
    for y in 0..a.height {
        for x in 0..a.width {
            let argb = match input.get(x, y)? {
                Pixel::U8(v) => v.map(|c| c as f32 * (1.0 / 255.0)),
                Pixel::U16(v) => v.map(|c| c as f32 / 32768.0),
                Pixel::F32(v) => v,
            };
            // KiraAdmission allows arbitrary nonfinite Alpha and box color inputs;
            // Gaussian color/brightness and scalar approximation require finite.
            if a.depth == Depth::U16 && argb.iter().any(|c| *c > 1.0) {
                return Err(olm_core::Error::Unsupported);
            }
            if a.depth == Depth::F32
                && p.channel != 1
                && (p.blur == 3 || (p.approximate && [2, 4].contains(&p.channel)))
                && argb.iter().any(|c| !c.is_finite())
            {
                return Err(olm_core::Error::Unsupported);
            }
            src.push([argb[1], argb[2], argb[3], argb[0]]);
        }
    }
    let dst = pixels(&src, a.width, a.height, p, scale)?;
    for y in 0..b.height {
        for x in 0..b.width {
            let v = dst[y * a.width + x];
            let argb = [v[3], v[0], v[1], v[2]];
            output.set(
                x,
                y,
                match b.depth {
                    Depth::U8 => Pixel::U8(argb.map(|c| (clamp(c) * 255.0) as u8)),
                    Depth::U16 => Pixel::U16(argb.map(|c| (clamp(c) * 32768.0) as u16)),
                    Depth::F32 => Pixel::F32(argb.map(clamp)),
                },
            )?;
        }
    }
    Ok(())
}

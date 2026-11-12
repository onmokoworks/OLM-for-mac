//! Pure stages from gamma_composite.inc. All imported pow calls use UCRT FMA.
use crate::{
    lut,
    types::{Pixel, Vertex, COLOR_TOL},
};
use olm_math::{x86, Mode};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(i32)]
pub enum GammaMode {
    None = 1,
    Colors = 2,
    All = 3,
}

pub fn curve(t: f32, index: i32) -> f32 {
    match index {
        1 => t * t,
        2 => {
            let u = 1.0 - t;
            1.0 - u * u
        }
        3 => t * t * t,
        4 => {
            let u = 1.0 - t;
            1.0 - u * u * u
        }
        5 => (3.0 - (t + t)) * t * t,
        6 => ((t * 6.0 - 15.0) * t + 10.0) * (t * t * t),
        _ => t,
    }
}

/// Public UI mode mapping. The internal luma-adaptive mode has no public mapping.
pub fn adaptive(
    center: Pixel,
    samples: &[Vertex],
    version: i32,
    mode: GammaMode,
    value: f32,
    palette: &[Pixel],
) -> (f32, bool) {
    if mode == GammaMode::All {
        return (value, true);
    }
    if mode != GammaMode::Colors || palette.is_empty() {
        return (value, false);
    }
    let matches = |mut p: Pixel| {
        if version != 1 {
            p.r = lut::encode(p.r);
            p.g = lut::encode(p.g);
            p.b = lut::encode(p.b);
        }
        // Unlike the frame alpha filter, a9c0 rejects unordered components.
        palette.iter().take(5).any(|key| {
            (p.r - key.r).abs() < COLOR_TOL
                && (p.g - key.g).abs() < COLOR_TOL
                && (p.b - key.b).abs() < COLOR_TOL
        })
    };
    (
        value,
        matches(center) || samples.iter().any(|s| matches(s.pixel)),
    )
}

fn power_rgb(p: &mut Pixel, e: f64) {
    p.r = olm_math::pow(p.r as f64, e, Mode::Fma) as f32;
    p.g = olm_math::pow(p.g as f64, e, Mode::Fma) as f32;
    p.b = olm_math::pow(p.b as f64, e, Mode::Fma) as f32;
}
fn premultiply(p: &mut Pixel) {
    if p.a != 1.0 {
        p.r = x86::mul(p.a, p.r);
        p.g = x86::mul(p.a, p.g);
        p.b = x86::mul(p.a, p.b);
    }
}
pub fn decode_premultiply(center: &mut Pixel, samples: &mut [Vertex], enable: bool, value: f32) {
    if enable && value > 0.0 {
        // DIVSS first, followed by float-to-double conversion, not binary64 divide.
        let exponent = (1.0_f32 / value) as f64;
        power_rgb(center, exponent);
        for s in samples.iter_mut() {
            power_rgb(&mut s.pixel, exponent);
        }
    }
    premultiply(center);
    for s in samples {
        premultiply(&mut s.pixel);
    }
}

/// Current C++ orchestration selects `scalar=true` at EVERY depth, including PF8.
/// The false branch retains the older leaf solely for reference comparison.
pub fn composite(center: Pixel, samples: &[Vertex], scalar: bool) -> Pixel {
    if samples.is_empty() {
        return center;
    }
    let mut weight = 0.0;
    for s in samples {
        weight += s.weight;
    }
    if weight < 0.0 {
        weight = 0.0;
    }
    if weight > 1.0 {
        weight = 1.0;
    }
    let blend = 1.0 - weight;
    if scalar {
        let mut out = Pixel {
            r: x86::mul(blend, center.r),
            g: x86::mul(blend, center.g),
            b: x86::mul(blend, center.b),
            a: x86::mul(blend, center.a),
        };
        for s in samples {
            // Original SSE ADDSS destination is the weighted sample.
            out.r = x86::add(x86::mul(s.weight, s.pixel.r), out.r);
            out.g = x86::add(x86::mul(s.weight, s.pixel.g), out.g);
            out.b = x86::add(x86::mul(s.weight, s.pixel.b), out.b);
            out.a = x86::add(x86::mul(s.weight, s.pixel.a), out.a);
        }
        out
    } else {
        let mut out = Pixel {
            r: blend * center.r,
            g: blend * center.g,
            b: blend * center.b,
            a: blend * center.a,
        };
        for s in samples {
            out.r += s.weight * s.pixel.r;
            out.g += s.weight * s.pixel.g;
            out.b += s.weight * s.pixel.b;
            out.a += s.weight * s.pixel.a;
        }
        out
    }
}

pub fn post_unpremultiply(p: &mut Pixel, enable: bool, value: f32) {
    if p.a != 0.0 && p.a != 1.0 {
        p.r = x86::div(p.r, p.a);
        p.g = x86::div(p.g, p.a);
        p.b = x86::div(p.b, p.a);
    }
    if enable && value > 0.0 {
        power_rgb(p, value as f64);
    }
    for c in [&mut p.r, &mut p.g, &mut p.b, &mut p.a] {
        if *c < 0.0 {
            *c = 0.0;
        } else if *c > 1.0 {
            *c = 1.0;
        }
    }
}

pub fn srgb_encode_literal(v: f64) -> f64 {
    if v <= 0.0 {
        return 0.0;
    }
    if v >= 1.0 {
        return 1.0;
    }
    if v < 0.00313066844250060782 {
        return v * 12.92;
    }
    olm_math::pow(v, 1.0 / 2.4, Mode::Fma) * 1.055 - 0.055
}

//! 2026-11-12 AEX RVAs 5520 (linear -> Oklab), 5840 (inverse).
//! UCRT cube root is shared by olm-math; OLM-internal.
use crate::types::Pixel;
pub use olm_math::cbrtf;

pub fn from_linear(p: Pixel) -> Pixel {
    let l = cbrtf(p.g * 0.53633255 + p.r * 0.41222146 + p.b * 0.051445995);
    let m = cbrtf(p.r * 0.2119035 + p.g * 0.6806995 + p.b * 0.10739696);
    let s = cbrtf(p.r * 0.08830246 + p.g * 0.28171885 + p.b * 0.6299787);
    Pixel { r: (l * 0.21045426 + m * 0.7936178) - s * 0.004072047,
        g: (l * 1.9779985 - m * 2.4285922) + s * 0.4505937,
        b: (m * 0.78277177 + l * 0.025904037) - s * 0.80867577, a: p.a }
}

pub fn to_linear(p: Pixel) -> Pixel {
    let l = p.g * 0.39633778 + p.r + p.b * 0.21580376;
    let s = (p.r - p.g * 0.08948418) - p.b * 1.2914855;
    let m = (p.r - p.g * 0.105561346) - p.b * 0.06385417;
    let l = l * l * l;
    let s = s * s * s;
    let m = m * m * m;
    Pixel { r: (l * 4.0767417 - m * 3.3077116) + s * 0.23096994,
        g: (m * 2.6097574 - l * 1.268438) - s * 0.34131938,
        b: s * 1.7076147 - (l * 0.0041960864 + m * 0.7034186), a: p.a }
}


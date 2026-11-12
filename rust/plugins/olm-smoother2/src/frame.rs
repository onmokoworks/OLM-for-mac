//! Translation of OLMSmoother2_frame_setup.inc (pure kernels only).
use crate::{
    lut,
    types::{Pixel, COLOR_TOL},
};

pub fn load8([a, r, g, b]: [u8; 4]) -> Pixel {
    const INV: f32 = 1.0 / 255.0;
    Pixel {
        r: r as f32 * INV,
        g: g as f32 * INV,
        b: b as f32 * INV,
        a: a as f32 * INV,
    }
}
pub fn load16([a, r, g, b]: [u16; 4]) -> Pixel {
    Pixel {
        r: r as f32 / 32768.0,
        g: g as f32 / 32768.0,
        b: b as f32 / 32768.0,
        a: a as f32 / 32768.0,
    }
}

/// Defined for finite channels (the C++ PF8 NaN cast has no portable contract).
pub fn pack8(v: f32) -> u8 {
    let v = v * 255.0 + 0.5;
    if v < 0.0 {
        0
    } else if v > 255.0 {
        255
    } else {
        v as u8
    }
}
/// PF16 uses signed CVTTSS2SI followed by the low word, not saturation at white.
pub fn pack16(v: f32) -> u16 {
    let rounded = v * 32768.0 + 0.5;
    if !rounded.is_finite()
        || rounded as f64 >= 9223372036854775808.0
        || (rounded as f64) < -9223372036854775808.0
    {
        0
    } else {
        (rounded as i64) as u16
    }
}

/// Available as a leaf only: public frame setup does NOT enable this for color key.
pub fn unpremultiply(pixels: &mut [Pixel]) {
    for p in pixels {
        if p.a != 0.0 && p.a != 1.0 {
            let inv = 1.0 / p.a;
            p.r *= inv;
            p.g *= inv;
            p.b *= inv;
        }
    }
}

fn key_match(p: Pixel, key: Pixel) -> bool {
    // Ordered >= rejection means an unordered (NaN) component is accepted.
    !((p.r - key.r).abs() >= COLOR_TOL)
        && !((p.g - key.g).abs() >= COLOR_TOL)
        && !((p.b - key.b).abs() >= COLOR_TOL)
}
pub fn palette_filter(pixels: &mut [Pixel], palette: &[Pixel]) {
    if palette.is_empty() {
        return;
    }
    for p in pixels {
        if !palette.iter().any(|&key| key_match(*p, key)) {
            p.a = 0.0;
        }
    }
}
pub fn scalar_key(pixels: &mut [Pixel], key: Pixel) {
    for p in pixels {
        if key_match(*p, key) {
            p.a = 0.0;
        }
    }
}

pub fn srgb_decode_literal(v: f32) -> f32 {
    let d = v as f64;
    if d <= 0.0 {
        return 0.0;
    }
    if d >= 1.0 {
        return 1.0;
    }
    if d < 0.04045 {
        return (d * (1.0 / 12.92)) as f32;
    }
    olm_math::pow(d * (1.0 / 1.055) + 0.055 / 1.055, 2.4, olm_math::Mode::Fma) as f32
}

/// Public setup order: key alpha filter, then v2 decode for every RGB channel.
/// All current C++ RenderBits depths select the captured runtime decode LUT.
pub fn setup(pixels: &mut [Pixel], version: i32, key: Option<(Pixel, bool)>) {
    if let Some((key, invert)) = key {
        if invert {
            palette_filter(pixels, &[key]);
        } else {
            scalar_key(pixels, key);
        }
    }
    if version != 1 {
        for p in pixels {
            p.r = lut::decode(p.r);
            p.g = lut::decode(p.g);
            p.b = lut::decode(p.b);
        }
    }
}

//! Local extension pending an olm-math `logf` API; not platform libm.
//! Translated from the loaded UCRT logf SSE/FMA bodies, constants in log_tables.
use crate::log_tables::{LEAD, RECIP, TAIL};
use olm_math::Mode;

pub fn logf(x: f32, mode: Mode) -> f32 {
    let bits = x.to_bits();
    let abs = bits & 0x7fffffff;
    if abs > 0x7f800000 {
        return f32::from_bits(bits | 0x400000);
    }
    if abs == 0 {
        return f32::NEG_INFINITY;
    }
    if bits >> 31 != 0 {
        return f32::from_bits(0xffc00000);
    }
    if abs == 0x7f800000 {
        return x;
    }
    let fused = mode == Mode::Fma;
    let mut mantissa = abs & 0x7fffff;
    let mut exponent = ((abs >> 23) as i32 - 127) as f32;
    if abs < 0x800000 {
        let normalized = (f32::from_bits(mantissa | 0x3f800000) - 1.0).to_bits();
        mantissa = normalized & 0x7fffff;
        exponent = ((normalized >> 23) as i32 - 253) as f32;
    }
    if (x - 1.0).abs() < 0.0625 {
        let r = x - 1.0;
        let t = r / (2.0 + r);
        let correction = r * t;
        let u = t + t;
        let square = u * u;
        let cube = u * square;
        let a = f32::from_bits(0x3c4ccccd);
        let b = f32::from_bits(0x3daaaaab);
        let v = if fused {
            square.mul_add(a, b).mul_add(cube, -correction)
        } else {
            ((square * a) + b) * cube - correction
        };
        return r + v;
    }
    let z = f32::from_bits(mantissa | 0x3f000000);
    let index = ((mantissa >> 16) + ((mantissa >> 15) & 1)) as usize;
    let rounded = f32::from_bits(((index as u32) << 16) | 0x3f000000);
    let r = (rounded - z) * f32::from_bits(RECIP[index]);
    let square = r * r;
    let a = f32::from_bits(0x3eaaaaab);
    let hi = f32::from_bits(0x3f317000);
    let lo = f32::from_bits(0x3805fdf4);
    let lead = f32::from_bits(LEAD[index]);
    let tail = f32::from_bits(TAIL[index]);
    if fused {
        let p = a.mul_add(r, 0.5);
        let q = p.mul_add(square, r);
        let low = lo.mul_add(exponent, -q) + tail;
        hi.mul_add(exponent, lead) + low
    } else {
        let p = a * r + 0.5;
        let q = r + p * square;
        let low = (lo * exponent - q) + tail;
        (hi * exponent + lead) + low
    }
}

/// Native validation entry, independent of AE.
#[no_mangle]
pub extern "C" fn uv_logf(x: f32, fma: i32) -> f32 {
    logf(x, if fma == 0 { Mode::NoFma } else { Mode::Fma })
}

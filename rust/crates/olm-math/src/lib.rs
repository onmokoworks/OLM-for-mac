//! Bit-preserving UCRT numerics. OLM-internal; must not be published standalone.
//! Requires round-to-nearest, gradual underflow. No global mode or CPU dispatch.
//! `Mode::Fma` is the lane explicitly used by the Mac pilot sources.

mod cbrtf;
pub use cbrtf::cbrtf;

/// UCRT evaluation lane (not an instruction-set requirement).
#[repr(i32)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Mode {
    NoFma = 0,
    Fma = 1,
}

macro_rules! unary {
    ($name:ident, $raw:ident, $ty:ty) => {
        extern "C" {
            fn $raw(x: $ty, mode: Mode) -> $ty;
        }
        #[doc = "Evaluate the vendored UCRT implementation in the selected lane."]
        pub fn $name(x: $ty, mode: Mode) -> $ty {
            unsafe { $raw(x, mode) }
        }
    };
}
macro_rules! binary {
    ($name:ident, $raw:ident, $ty:ty) => {
        extern "C" {
            fn $raw(x: $ty, y: $ty, mode: Mode) -> $ty;
        }
        #[doc = "Evaluate the vendored UCRT implementation in the selected lane."]
        pub fn $name(x: $ty, y: $ty, mode: Mode) -> $ty {
            unsafe { $raw(x, y, mode) }
        }
    };
}
unary!(sin, ucrt_sin, f64);
unary!(cos, ucrt_cos, f64);
unary!(exp, ucrt_exp, f64);
unary!(sinf, ucrt_sinf, f32);
unary!(cosf, ucrt_cosf, f32);
unary!(log2f, ucrt_log2f, f32);
unary!(expf, ucrt_expf, f32);
binary!(pow, ucrt_pow, f64);
binary!(powf, ucrt_powf, f32);
binary!(atan2f, ucrt_atan2f, f32);

/// Scalar x86 SSE semantics from core/x86_float.h (this header is not x87).
pub mod x86 {
    /// Preserve first NaN operand, quiet its payload; generated invalid is negative.
    pub fn result(r: f32, a: f32, b: f32) -> f32 {
        if a.is_nan() {
            return f32::from_bits(a.to_bits() | 0x00400000);
        }
        if b.is_nan() {
            return f32::from_bits(b.to_bits() | 0x00400000);
        }
        if r.is_nan() {
            f32::from_bits(0xffc00000)
        } else {
            r
        }
    }
    pub fn add(a: f32, b: f32) -> f32 {
        result(a + b, a, b)
    }
    pub fn sub(a: f32, b: f32) -> f32 {
        result(a - b, a, b)
    }
    pub fn mul(a: f32, b: f32) -> f32 {
        result(a * b, a, b)
    }
    pub fn div(a: f32, b: f32) -> f32 {
        result(a / b, a, b)
    }
    pub fn min(a: f32, b: f32) -> f32 {
        if a < b {
            a
        } else {
            b
        }
    }
    pub fn max(a: f32, b: f32) -> f32 {
        if a > b {
            a
        } else {
            b
        }
    }
    /// CVTTSS2SI, including x86 integer-indefinite for nonrepresentable inputs.
    pub fn cvttss2si(x: f32) -> i32 {
        if !x.is_finite() || !(-2147483648.0..2147483648.0).contains(&x) {
            i32::MIN
        } else {
            x as i32
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn special_values() {
        for m in [Mode::NoFma, Mode::Fma] {
            assert_eq!(sinf(-0.0, m).to_bits(), 0x80000000);
            assert_eq!(cosf(0.0, m), 1.0);
            assert_eq!(log2f(0.0, m), f32::NEG_INFINITY);
            assert_eq!(sinf(f32::INFINITY, m).to_bits(), 0xffc00000);
            assert_eq!(exp(f64::NEG_INFINITY, m).to_bits(), 0);
        }
        assert_eq!(x86::mul(0.0, f32::INFINITY).to_bits(), 0xffc00000);
        assert_eq!(x86::min(0.0, -0.0).to_bits(), 0x80000000);
        assert_eq!(
            x86::add(f32::from_bits(0x7f800001), f32::NAN).to_bits(),
            0x7fc00001
        );
    }
}

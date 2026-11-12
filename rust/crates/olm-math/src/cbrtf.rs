//! Bit-exact UCRT cube root. OLM-internal; not publishable standalone.
use crate::x86::{add, div, mul};

/// UCRT 10.0.26100 cbrtf, RVA 54ed0 in the hash-bound local provider.
/// Scalar SSE only: no FMA dispatch, one rational estimate/refinement.
/// Return-bit contract; errno and exception flags are outside this port.
pub fn cbrtf(x: f32) -> f32 {
    let bits = x.to_bits();
    let sign = bits & 0x8000_0000;
    let mut mantissa = bits & 0x7f_ffff;
    let mut exponent = ((bits >> 23) & 255) as i32;
    // UCRT returns the original word, even for signaling NaNs.
    if exponent == 255 || (exponent == 0 && mantissa == 0) { return x; }
    if exponent == 0 {
        let shift = mantissa.leading_zeros() as i32 - 8;
        mantissa = (mantissa << shift) & 0x7f_ffff;
        exponent = 1 - shift;
    }
    exponent -= 126;
    let mut reduction = 0;
    while exponent % 3 != 0 { exponent += 1; reduction += 1; }
    let y = f32::from_bits(mantissa | ((126 - reduction) as u32) << 23);
    let estimate = div(
        add(mul(add(mul(y, f32::from_bits(0x3e79a416)), f32::from_bits(0x3f754413)), y), f32::from_bits(0x3da1a0cf)),
        add(y, f32::from_bits(0x3e8f2a5a)),
    );
    let refined = mul(add(div(mul(y, 1.5), add(div(mul(y, 0.5), estimate), mul(estimate, estimate))), estimate), 0.5);
    // Every finite binary32 cube root is normal; scaling cannot under/overflow.
    let scaled = (refined.to_bits() as i64 + ((exponent / 3) as i64 * (1 << 23))) as u32;
    f32::from_bits(scaled | sign)
}

#[cfg(all(test, target_os = "windows"))]
mod tests {
    #[link(name = "ucrt")]
    extern "C" { #[link_name = "cbrtf"] fn native(x: f32) -> f32; }
    #[test]
    fn ucrt_cbrtf_words() {
        let mut state = 0x20261112u32;
        let check = |word| {
            let x = f32::from_bits(word);
            assert_eq!(super::cbrtf(x).to_bits(), unsafe {native(x)}.to_bits(), "input={word:08x}");
        };
        for _ in 0..1_000_000 {
            state ^= state << 13; state ^= state >> 17; state ^= state << 5;
            check(state);
        }
        for exponent in 0..=255u32 {
            for delta in -32i64..=32 {
                let word = ((exponent << 23) as i64 + delta) as u32;
                check(word); check(word | 0x80000000);
            }
        }
        for word in [0,0x80000000,1,0x7fffff,0x7f800000,0xff800000,0x7f800001,0xff800001,0x7fc01234] {check(word);}
    }
}

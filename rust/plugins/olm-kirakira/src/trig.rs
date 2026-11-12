//! Embedded AEX extent trig, translated from core/olm_exact_math.h.
use crate::trig_tables::{RECONSTRUCTION, REDUCTION};
fn f(x: u32) -> f32 {
    f32::from_bits(x)
}
pub fn sine(x: f32) -> f32 {
    let sign = x.to_bits() & 0x80000000;
    let a = x.abs();
    if a <= 10000.0 {
        let mut n = a * f(0x3ea2f983);
        n += 12582912.0;
        let parity = n.to_bits() << 31;
        n -= 12582912.0;
        let mut r = a - n * f(0x40490000);
        r -= n * f(0x3a7da000);
        r -= n * f(0x34222000);
        r -= n * f(0x2cb4611a);
        let square = r * r;
        r = f(r.to_bits() ^ parity);
        let mut p = f(0x362edef8) * square;
        p += f(0xb94fb7ff);
        p *= square;
        p += f(0x3c088766);
        p *= square;
        p += f(0xbe2aaaa6);
        p = square * p;
        p *= r;
        return f((r + p).to_bits() ^ sign);
    }
    if a.to_bits() & 0x7f800000 == 0x7f800000 {
        return f(if a.to_bits() & 0x7fffff != 0 {
            x.to_bits() | 0x400000
        } else {
            0xffc00000
        });
    }
    let reciprocal = REDUCTION[((a.to_bits() >> 23) & 255) as usize];
    let m = ((a.to_bits() & 0x7fffff) | 0x800000) as u64;
    let (mh, ml) = (m >> 16, m & 0xffff);
    let (ch, cl) = (
        (reciprocal[2] >> 16) as u64,
        (reciprocal[2] & 0xffff) as u64,
    );
    let bottom = mh * ch + ((ml * ch) >> 16) + ((mh * cl) >> 16);
    let product = ((m * reciprocal[0] as u64) << 32)
        .wrapping_add(m * reciprocal[1] as u64)
        .wrapping_add(bottom);
    let (hi, lo) = ((product >> 32) as u32, product as u32);
    let mut top = f((hi >> 9) | (0x3f800000 ^ sign));
    let middle_base = f(0x34000000 ^ sign);
    let mut middle = f(((hi & 0x1ff) << 14) | (lo >> 18) | (0x34000000 ^ sign));
    let bottom_base = f(0x28800000 ^ sign);
    let mut bottom = f(((lo & 0x3ffff) << 5) | (0x28800000 ^ sign));
    let rounded = top + 49152.0;
    let integral = rounded - 49152.0;
    middle -= middle_base;
    bottom -= bottom_base;
    top -= integral;
    let fraction = top + middle;
    top -= fraction;
    middle += top;
    bottom += middle;
    let split = f(fraction.to_bits() & 0xfffff000);
    let residual = fraction - split;
    let high = f(0x40c91000) * split;
    let mut low = f(0x40c91000) * residual;
    low += split * f(0xb795777a);
    let mut tail = f(0x40c90fdb) * bottom;
    tail += residual * f(0xb795777a);
    low += tail;
    let r = low + high;
    let correction = low + (high - r);
    let row = RECONSTRUCTION[(rounded.to_bits() & 255) as usize];
    let (c, s, extra, c_low) = (f(row[0]), f(row[1]), f(row[2]), f(row[3]));
    let square = r * r;
    let mut first = r * c_low;
    let mut second = r * c;
    let sum1 = s + first;
    first += s - sum1;
    let sum2 = sum1 + second;
    second += sum1 - sum2;
    let mut cp = f(0x3d2aaa7c) * square;
    cp += f(0xbf000000);
    cp = square * cp;
    cp = s * cp;
    let mut sp = f(0x3c08885c) * square;
    sp += f(0xbe2aaaab);
    sp *= square;
    sp *= r;
    let derivative = (c + c_low) - r * s;
    sp *= derivative;
    first += second;
    first += sp;
    let mut rest = extra + correction * derivative;
    rest += cp;
    rest += first;
    sum2 + rest
}
pub fn extent_sincos(degrees: f64) -> (f32, f32) {
    let r = (degrees * f64::from_bits(0x3f91df46a2529d39)) as f32;
    let a = r.abs();
    if !(a >= 1.0 / 8192.0) {
        if a.to_bits() > 0x7f800000 {
            return (r, f(a.to_bits() | 0x400000));
        }
        return (r, 1.0 - (a * a) * 0.5);
    }
    (sine(r), sine(a + f(0x3fc90fdb)))
}
pub fn extent(major: i32, minor: i32, ac: f32, asin: f32) -> i32 {
    (major + 4).max(((major as f32 * ac + minor as f32 * asin) + 4.0) as i32)
}

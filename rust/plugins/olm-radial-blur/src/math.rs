//! Embedded AEX polynomials, distinct from the imported UCRT functions.
pub use olm_math::x86::{add, cvttss2si as int, div, mul, sub};
pub const RAD: f64 = 0.017453292500000002;
// Original AEX literal; replacing it with TAU changes output bits.
#[allow(clippy::approx_constant)]
pub const TURN: f64 = 6.2831853;
pub fn sin_hot(x: f32) -> f32 {
    let f = f32::from_bits;
    let absolute = x.abs();
    let quadrant = add(mul(absolute, f(0x3ea2f983)), f(0x4b400000));
    let n = sub(quadrant, f(0x4b400000));
    let mut r = absolute;
    for bits in [0x40490000, 0x3a7da000, 0x34222000, 0x2cb4611a] {
        r = sub(r, mul(f(bits), n));
    }
    let signed = f(r.to_bits() ^ (quadrant.to_bits() << 31));
    let square = mul(r, r);
    let mut p = mul(f(0x362edef8), square);
    for bits in [0xb94fb7ff, 0x3c088766, 0xbe2aaaa6] {
        p = mul(add(p, f(bits)), square);
    }
    p = add(signed, mul(p, signed));
    f(p.to_bits() ^ (x.to_bits() & 0x80000000))
}
pub fn trig(theta: f32) -> (f32, f32) {
    let a = theta.abs();
    if a < f32::from_bits(0x39000000) {
        return (theta, sub(1.0, mul(mul(a, a), 0.5)));
    }
    (sin_hot(theta), sin_hot(add(a, f32::from_bits(0x3fc90fdb))))
}
pub fn gaussian_exp(x: f32) -> f32 {
    const M: [u32; 64] = [
        0x000000, 0x0164d2, 0x02cd87, 0x043a29, 0x05aac3, 0x071f62, 0x08980f, 0x0a14d5, 0x0b95c2,
        0x0d1adf, 0x0ea43a, 0x1031dc, 0x11c3d3, 0x135a2b, 0x14f4f0, 0x16942d, 0x1837f0, 0x19e046,
        0x1b8d3a, 0x1d3eda, 0x1ef532, 0x20b051, 0x227043, 0x243516, 0x25fed7, 0x27cd94, 0x29a15b,
        0x2b7a3a, 0x2d583f, 0x2f3b79, 0x3123f6, 0x3311c4, 0x3504f3, 0x36fd92, 0x38fbaf, 0x3aff5b,
        0x3d08a4, 0x3f179a, 0x412c4d, 0x4346cd, 0x45672a, 0x478d75, 0x49b9be, 0x4bec15, 0x4e248c,
        0x506334, 0x52a81e, 0x54f35b, 0x5744fd, 0x599d16, 0x5bfbb8, 0x5e60f5, 0x60ccdf, 0x633f89,
        0x65b907, 0x68396a, 0x6ac0c7, 0x6d4f30, 0x6fe4ba, 0x728177, 0x75257d, 0x77d0df, 0x7a83b3,
        0x7d3e0c,
    ];
    let scaled = mul(x, 92.33248138427734);
    let low = scaled.floor();
    let fraction = sub(scaled, low);
    let mut n = int(low);
    if fraction > 0.5 || (fraction == 0.5 && n & 1 != 0) {
        n += 1;
    }
    let r = sub(
        sub(x, mul(n as f32, 0.01082611083984375)),
        mul(n as f32, 0.000004313856607041089),
    );
    let p = add(add(add(r, r), 2.0), mul(r, r));
    mul(
        p,
        f32::from_bits((((8064 + n) as u32 >> 6) << 23) | M[(n & 63) as usize]),
    )
}
fn inverse_variance(length: i32) -> (f32, f32) {
    let d = mul(mul(length as f32, length as f32), 0.111111119389534);
    let d = (add(d, d) as f64 + 1.0e-5) as f32;
    (div(1.0, d), d)
}
pub fn fade_weights(length: i32) -> Vec<f32> {
    fade_weights_seed(length, true)
}
// The C++ emulator uses exact division as an RCPPS substitute. Native AEX uses
// the processor estimate. Keep the old seam available to tests, not production.
pub(crate) fn reciprocal_seed(x: f32) -> f32 {
    let word = x.to_bits();
    let exponent = ((word >> 23) & 255) as i32;
    debug_assert!(word >> 31 == 0 && (1..253).contains(&exponent));
    let normalized = crate::reciprocal_table::SEED[((word & 0x7fffff) >> 11) as usize];
    f32::from_bits((normalized as i64 - ((exponent - 127) as i64 * (1 << 23))) as u32)
}
pub(crate) fn fade_weights_seed(length: i32, native: bool) -> Vec<f32> {
    if length <= 1 {
        return vec![1.0];
    }
    let (inv, d) = inverse_variance(length);
    let seed = if native { reciprocal_seed(d) } else { inv };
    let refined = sub(add(seed, seed), mul(mul(seed, seed), d));
    (0..length)
        .map(|i| {
            if i < (length & !3) {
                gaussian_exp(mul(-(i * i) as f32, refined))
            } else {
                olm_math::expf(mul(-(i * i) as f32, inv), olm_math::Mode::Fma)
            }
        })
        .collect()
}
pub fn rotation_weights(length: i32) -> Vec<f32> {
    if length <= 1 {
        return vec![1.0];
    }
    let (inv, _) = inverse_variance(30000);
    let step = 30000 / length;
    let mut weights = vec![1.0; length as usize];
    for i in 1..length {
        let j = int(mul(i as f32, step as f32));
        weights[i as usize] = gaussian_exp(mul(-(j * j) as f32, inv));
    }
    weights
}
pub fn radius_bounds(w: i32, h: i32, cx: f32, cy: f32, ratio: f32) -> (i32, i32) {
    fn axis(n: i32, c: f32) -> (f32, f32) {
        if c < 0.0 {
            (-c, sub(n as f32, c))
        } else if c >= n as f32 {
            (sub(c, n as f32), c)
        } else {
            (
                0.0,
                if c > (n / 2) as f32 {
                    c
                } else {
                    sub(n as f32, c)
                },
            )
        }
    }
    let (nx, fx) = axis(w, cx);
    let (ny, fy) = axis(h, cy);
    let near = int(add(mul(nx, nx), mul(ny, ny)).sqrt());
    let far = int(add(mul(fx, fx), mul(fy, fy)).sqrt());
    ((int(div(near as f32, ratio)) - 2).max(0), far + 2)
}

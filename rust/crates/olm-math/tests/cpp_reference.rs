use olm_math::{self as m, x86, Mode};
extern "C" {
    fn olm_cpp_float(op: i32, x: f32, y: f32, mode: i32) -> f32;
    fn olm_cpp_double(op: i32, x: f64, y: f64, mode: i32) -> f64;
}
#[test]
fn cpp_probe_vectors() {
    let mut seed = 0x1234abcd87654321u64;
    let mut next = || {
        seed ^= seed << 13;
        seed ^= seed >> 7;
        seed ^= seed << 17;
        seed
    };
    for mode in [Mode::NoFma, Mode::Fma] {
        for _ in 0..4096 {
            let a = next();
            let b = next();
            let x = f32::from_bits(a as u32);
            let y = f32::from_bits(b as u32);
            let values = [
                m::sinf(x, mode),
                m::cosf(x, mode),
                m::log2f(x, mode),
                m::expf(x, mode),
                m::atan2f(x, y, mode),
                m::powf(x, y, mode),
                x86::add(x, y),
                x86::sub(x, y),
                x86::mul(x, y),
                x86::div(x, y),
                x86::min(x, y),
                x86::max(x, y),
            ];
            for (op, v) in values.into_iter().enumerate() {
                assert_eq!(
                    v.to_bits(),
                    unsafe { olm_cpp_float(op as i32, x, y, mode as i32) }.to_bits(),
                    "op={op} x={a:x} y={b:x}"
                );
            }
            let x = f64::from_bits(a);
            let y = f64::from_bits(b);
            for (op, v) in [
                m::sin(x, mode),
                m::cos(x, mode),
                m::exp(x, mode),
                m::pow(x, y, mode),
            ]
            .into_iter()
            .enumerate()
            {
                assert_eq!(
                    v.to_bits(),
                    unsafe { olm_cpp_double(op as i32, x, y, mode as i32) }.to_bits()
                );
            }
        }
    }
}

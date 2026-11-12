//! Native UCRT comparisons run in this dedicated test executable: changing the
//! DLL's mode must never race a plug-in render or an unrelated test process.
#![cfg(windows)]
use olm_math::{self as m, Mode};
#[test]
fn native_ucrt_both_modes() {
    unsafe {
        let dll = libloading::Library::new("ucrtbase.dll").unwrap();
        let get: libloading::Symbol<unsafe extern "C" fn() -> i32> =
            dll.get(b"_get_FMA3_enable\0").unwrap();
        let set: libloading::Symbol<unsafe extern "C" fn(i32) -> i32> =
            dll.get(b"_set_FMA3_enable\0").unwrap();
        let initial = get();
        struct Restore<'a>(&'a (dyn Fn(i32)), i32);
        impl Drop for Restore<'_> {
            fn drop(&mut self) {
                (self.0)(self.1)
            }
        }
        let setter = |v| {
            set(v);
        };
        let _restore = Restore(&setter, initial);
        let mut seed = 0x43b0123456789abcu64;
        let mut next = || {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            seed
        };
        let floats: Vec<_> = (0..4096)
            .map(|_| f32::from_bits(next() as u32))
            .chain([
                0.0,
                -0.0,
                1.0,
                -1.0,
                f32::INFINITY,
                f32::NEG_INFINITY,
                f32::from_bits(1),
                f32::from_bits(0x7f800001),
            ])
            .collect();
        let doubles: Vec<_> = (0..4096)
            .map(|_| f64::from_bits(next()))
            .chain([
                0.0,
                -0.0,
                1.0,
                -1.0,
                f64::INFINITY,
                f64::NEG_INFINITY,
                f64::from_bits(1),
                f64::from_bits(0x7ff0000000000001),
            ])
            .collect();
        for mode in [Mode::NoFma, Mode::Fma] {
            set(mode as i32);
            assert_eq!(
                get(),
                mode as i32,
                "native DLL cannot select requested mode"
            );
            for (name, port) in [
                ("sinf", m::sinf as fn(f32, Mode) -> f32),
                ("cosf", m::cosf),
                ("log2f", m::log2f),
                ("expf", m::expf),
            ] {
                let native: libloading::Symbol<unsafe extern "C" fn(f32) -> f32> =
                    dll.get(name.as_bytes()).unwrap();
                for &x in &floats {
                    assert_eq!(
                        port(x, mode).to_bits(),
                        native(x).to_bits(),
                        "{name} {mode:?} x={:08x}",
                        x.to_bits()
                    );
                }
            }
            for (name, port) in [
                ("sin", m::sin as fn(f64, Mode) -> f64),
                ("cos", m::cos),
                ("exp", m::exp),
            ] {
                let native: libloading::Symbol<unsafe extern "C" fn(f64) -> f64> =
                    dll.get(name.as_bytes()).unwrap();
                for &x in &doubles {
                    assert_eq!(
                        port(x, mode).to_bits(),
                        native(x).to_bits(),
                        "{name} {mode:?} x={:016x}",
                        x.to_bits()
                    );
                }
            }
            for (name, port) in [
                ("atan2f", m::atan2f as fn(f32, f32, Mode) -> f32),
                ("powf", m::powf),
            ] {
                let native: libloading::Symbol<unsafe extern "C" fn(f32, f32) -> f32> =
                    dll.get(name.as_bytes()).unwrap();
                for (i, &x) in floats.iter().enumerate() {
                    let y = floats[(i * 13 + 7) % floats.len()];
                    assert_eq!(
                        port(x, y, mode).to_bits(),
                        native(x, y).to_bits(),
                        "{name} {mode:?} x={:08x} y={:08x}",
                        x.to_bits(),
                        y.to_bits()
                    );
                }
            }
            let pow: libloading::Symbol<unsafe extern "C" fn(f64, f64) -> f64> =
                dll.get(b"pow\0").unwrap();
            for (i, &x) in doubles.iter().enumerate() {
                let y = doubles[(i * 13 + 7) % doubles.len()];
                assert_eq!(
                    m::pow(x, y, mode).to_bits(),
                    pow(x, y).to_bits(),
                    "pow {mode:?} x={:016x} y={:016x}",
                    x.to_bits(),
                    y.to_bits()
                );
            }
        }
        eprintln!("native UCRT: 4104 vectors x 10 functions x 2 modes = 82080 raw-word comparisons; initial FMA={initial}");
    }
}

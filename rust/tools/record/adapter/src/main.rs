//! OLM-internal adapter: compile existing production sources unchanged.
//! Includes olm-math/UCRT-derived material; must not be published standalone.
#![allow(dead_code)]
#[rustfmt::skip]
#[allow(clippy::all, unexpected_cfgs)]
#[path = "../../../../plugins/olm-directional-blur/src/algorithm.rs"]
mod algorithm;
#[rustfmt::skip]
#[allow(clippy::all, unexpected_cfgs)]
#[path = "../../../../plugins/olm-directional-blur/src/noise.rs"]
mod noise;
#[rustfmt::skip]
#[allow(clippy::all, unexpected_cfgs)]
#[path = "../../../../plugins/olm-directional-blur/src/rotate.rs"]
mod rotate;
#[rustfmt::skip]
#[allow(clippy::all, unexpected_cfgs)]
#[path = "../../../../plugins/olm-directional-blur/src/rowdriver.rs"]
mod rowdriver;
#[rustfmt::skip]
#[allow(clippy::all, unexpected_cfgs)]
#[path = "../../../../plugins/olm-kirakira/src/trig.rs"]
mod trig;
#[rustfmt::skip]
#[allow(clippy::all, unexpected_cfgs)]
#[path = "../../../../plugins/olm-kirakira/src/trig_tables.rs"]
mod trig_tables;
use serde_json::{json, Value};

fn unhex(s: &str) -> Vec<u8> {
    assert_eq!(s.len() % 2, 0);
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
        .collect()
}
fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}
fn main() {
    let paths: Vec<_> = std::env::args().collect();
    let v: Value = serde_json::from_slice(&std::fs::read(&paths[1]).unwrap()).unwrap();
    let args: Vec<Vec<u8>> = v["args"]
        .as_array()
        .unwrap()
        .iter()
        .map(|x| unhex(x["bits_le"].as_str().unwrap()))
        .collect();
    let u32arg = |i: usize| u32::from_le_bytes(args[i][..4].try_into().unwrap());
    let f32arg = |i: usize| f32::from_bits(u32arg(i));
    let mut buffers: Vec<Vec<u8>> = v["buffers"]
        .as_array()
        .unwrap()
        .iter()
        .map(|x| unhex(x["before_hex"].as_str().unwrap_or("")))
        .collect();
    let mut ret = Vec::new();
    let mut pointer = None;
    let name = v["name"].as_str().unwrap();
    match name {
        "fixture.returned" => {
            let (n, seed) = (u32arg(0) as usize, u32arg(1) as u8);
            assert!(n <= 1024);
            buffers[0] = (0..n).map(|i| seed.wrapping_add(i as u8)).collect();
            pointer = Some("nonnull");
        }
        "directional.gaussian" | "wrong.gaussian" => {
            let n = u32arg(1) as i32;
            assert!((0..=65536).contains(&n));
            let values = algorithm::gaussian(n);
            buffers[0] = values.iter().flat_map(|x| x.to_le_bytes()).collect();
            // Deliberately wrong implementation for the negative control.
            if name == "wrong.gaussian" && !buffers[0].is_empty() {
                buffers[0][0] ^= 1;
            }
        }
        "directional.rotate" => {
            let (w, h) = (u32arg(2) as usize, u32arg(3) as usize);
            assert!(w.checked_mul(h).unwrap() <= 16 * 1024 * 1024);
            let pixels = |b: &[u8]| -> Vec<[f32; 4]> {
                b.chunks_exact(16)
                    .map(|p| {
                        std::array::from_fn(|i| {
                            f32::from_le_bytes(p[i * 4..i * 4 + 4].try_into().unwrap())
                        })
                    })
                    .collect()
            };
            let src = pixels(&buffers[0]);
            let mut dst = pixels(&buffers[1]);
            assert_eq!(src.len(), w * h);
            assert_eq!(dst.len(), w * h);
            rotate::rgba(&src, &mut dst, w, h, f32arg(4));
            buffers[1] = dst.iter().flatten().flat_map(|x| x.to_le_bytes()).collect();
        }
        "kirakira.extent_sincos" => {
            let r = f32arg(0);
            assert!(r.is_finite());
            let factor = f64::from_bits(0x3f91df46a2529d39);
            let degrees = r as f64 / factor;
            // The public translation takes degrees; verify its lowered f32 arg.
            assert_eq!(((degrees * factor) as f32).to_bits(), r.to_bits());
            let (s, c) = trig::extent_sincos(degrees);
            ret.extend(s.to_le_bytes());
            ret.extend(c.to_le_bytes());
        }
        "math.expf" => ret.extend(olm_math::expf(f32arg(0), olm_math::Mode::Fma).to_le_bytes()),
        "math.cosf" => ret.extend(olm_math::cosf(f32arg(0), olm_math::Mode::Fma).to_le_bytes()),
        "math.sinf" => ret.extend(olm_math::sinf(f32arg(0), olm_math::Mode::Fma).to_le_bytes()),
        "math.powf" => {
            ret.extend(olm_math::powf(f32arg(0), f32arg(1), olm_math::Mode::Fma).to_le_bytes())
        }
        _ => panic!("unknown named adapter: {name}"),
    }
    std::fs::write(&paths[2], serde_json::to_vec_pretty(&json!({
        "return_hex":hex(&ret), "return_pointer":pointer, "buffers":buffers.iter().map(|b| hex(b)).collect::<Vec<_>>()
    })).unwrap()).unwrap();
}

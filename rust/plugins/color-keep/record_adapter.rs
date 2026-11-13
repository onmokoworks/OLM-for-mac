//! Test-only recorder adapter using the production pixel API.
use olm_core::Pixel;
use serde_json::{json, Value};

fn unhex(s: &str) -> Vec<u8> {
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
        .collect()
}
fn main() {
    let paths: Vec<_> = std::env::args().collect();
    let v: Value = serde_json::from_slice(&std::fs::read(&paths[1]).unwrap()).unwrap();
    let mut buffers: Vec<Vec<u8>> = v["buffers"]
        .as_array()
        .unwrap()
        .iter()
        .map(|b| unhex(b["before_hex"].as_str().unwrap()))
        .collect();
    let count = i32::from_le_bytes(buffers[0][0x20..0x24].try_into().unwrap());
    assert!((0..=200).contains(&count));
    let colors: Vec<[f32; 4]> = buffers[0][0x24..0x24 + count as usize * 16]
        .chunks_exact(16)
        .map(|c| {
            std::array::from_fn(|i| f32::from_le_bytes(c[i * 4..i * 4 + 4].try_into().unwrap()))
        })
        .collect();
    let p = match v["name"].as_str().unwrap() {
        "color-keep.8" => Pixel::U8(buffers[1][..4].try_into().unwrap()),
        "color-keep.16" => Pixel::U16(std::array::from_fn(|i| {
            u16::from_le_bytes(buffers[1][i * 2..i * 2 + 2].try_into().unwrap())
        })),
        "color-keep.32" => Pixel::F32(std::array::from_fn(|i| {
            f32::from_le_bytes(buffers[1][i * 4..i * 4 + 4].try_into().unwrap())
        })),
        _ => panic!("unknown adapter"),
    };
    let alpha = match color_keep::pixel(p, &colors) {
        Pixel::U8(p) => vec![p[0]],
        Pixel::U16(p) => p[0].to_le_bytes().to_vec(),
        Pixel::F32(p) => p[0].to_le_bytes().to_vec(),
    };
    buffers[2][..alpha.len()].copy_from_slice(&alpha);
    let hexes: Vec<String> = buffers
        .iter()
        .map(|b| b.iter().map(|x| format!("{x:02x}")).collect())
        .collect();
    std::fs::write(
        &paths[2],
        serde_json::to_vec(&json!({
            "return_hex": "00000000", "buffers": hexes
        }))
        .unwrap(),
    )
    .unwrap();
}

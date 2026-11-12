//! Compile the actual translation sources, with no copied/tuned algorithm.
//! OLM-internal: the optional olm-math dependency must not be published standalone.
#![allow(dead_code)]
#[rustfmt::skip]
#[path = "../../../plugins/olm-directional-blur/src/algorithm.rs"]
mod algorithm;
#[rustfmt::skip]
#[path = "../../../plugins/olm-directional-blur/src/noise.rs"]
mod noise;
#[rustfmt::skip]
#[path = "../../../plugins/olm-directional-blur/src/rotate.rs"]
mod rotate;
#[rustfmt::skip]
#[path = "../../../plugins/olm-directional-blur/src/rowdriver.rs"]
mod rowdriver;
#[rustfmt::skip]
#[path = "../../../plugins/olm-kirakira/src/trig.rs"]
mod trig;
#[rustfmt::skip]
#[path = "../../../plugins/olm-kirakira/src/trig_tables.rs"]
mod trig_tables;
use serde::Deserialize;
use serde_json::json;
use std::io::{self, Read};
#[derive(Deserialize)]
struct Input {
    counts: Vec<i32>,
    degrees: Vec<f64>,
}
fn hex(b: &[u8]) -> String {
    b.iter().map(|b| format!("{b:02x}")).collect()
}
fn main() {
    let mut data = String::new();
    io::stdin().read_to_string(&mut data).unwrap();
    let input: Input = serde_json::from_str(&data).unwrap();
    assert!(input.counts.iter().all(|&n| (0..=8192).contains(&n)));
    let gaussian: Vec<_> = input
        .counts
        .iter()
        .map(|&n| {
            hex(&algorithm::gaussian(n)
                .iter()
                .flat_map(|x| x.to_le_bytes())
                .collect::<Vec<_>>())
        })
        .collect();
    let trig:Vec<_> = input.degrees.iter().map(|&d| {
        let (s,c)=trig::extent_sincos(d);
        let radians = (d*f64::from_bits(0x3f91df46a2529d39)) as f32;
        json!({"input_bits":format!("0x{:08x}",radians.to_bits()),"bits_le":hex(&[s.to_le_bytes(),c.to_le_bytes()].concat())})
    }).collect();
    println!("{}", json!({"gaussian":gaussian,"trig":trig}));
}

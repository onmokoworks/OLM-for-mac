//! Bounded 540p kernel profile; no host, rendered files, or persistent helpers.
#[allow(dead_code)]
#[path = "../src/algorithm.rs"]
mod algorithm;
use olm_core::{Depth, Layout};
use std::{hint::black_box, time::Instant};
fn main() {
    let (w, h) = (960, 540);
    for depth in [Depth::U8, Depth::U16, Depth::F32] {
        let n = depth.pixel_bytes();
        let l = Layout {
            width: w,
            height: h,
            stride: w * n,
            depth,
            origin: (0, 0),
        };
        for spacing in [5, 97] {
            let mut input = vec![0u8; l.span().unwrap()];
            for (i, p) in input.chunks_exact_mut(n).enumerate() {
                for (c, v) in p.iter_mut().enumerate() {
                    *v = (i * 71 + c * 37) as u8;
                }
                let opaque = i % spacing == 0;
                match depth {
                    Depth::U8 => p[0] = if opaque { 255 } else { 128 },
                    Depth::U16 => p[..2]
                        .copy_from_slice(&(if opaque { 32768u16 } else { 16384 }).to_ne_bytes()),
                    Depth::F32 => {
                        p[..4].copy_from_slice(&(if opaque { 1f32 } else { 0.5 }).to_ne_bytes())
                    }
                }
            }
            let mut output = vec![0; input.len()];
            for radius in [0, 5, 50] {
                let mut samples = Vec::new();
                for _ in 0..9 {
                    let start = Instant::now();
                    algorithm::render_staged(
                        black_box(&input),
                        l,
                        black_box(&mut output),
                        l,
                        radius,
                    )
                    .unwrap();
                    samples.push(start.elapsed().as_secs_f64() * 1000.0);
                }
                samples.sort_by(f64::total_cmp);
                println!(
                    "{depth:?} spacing={spacing} radius={radius} median_ms={:.4}",
                    samples[4]
                );
            }
        }
    }
}

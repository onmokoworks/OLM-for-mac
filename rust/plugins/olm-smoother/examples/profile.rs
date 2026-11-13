//! Run with --release --features profile; clocks are compiled out normally.
use olm_core::{Depth, Layout, Rect, View, ViewMut};
use olm_smoother::algorithm::{render, Params};
fn main() {
    let (width, height) = (1920, 1080);
    // Optional raw ARGB8 benchmark image (1920x1080, no headers).
    let supplied = std::env::args().nth(1).map(|p| std::fs::read(p).unwrap());
    for depth in [Depth::U8, Depth::U16] {
        let layout = Layout {
            width,
            height,
            stride: width * depth.pixel_bytes(),
            depth,
            origin: (0, 0),
        };
        let mut input = vec![0; layout.span().unwrap()];
        let mut seed = 20261113u32;
        for (i, pixel) in input.chunks_mut(depth.pixel_bytes()).enumerate() {
            for c in 0..4 {
                seed ^= seed << 13;
                seed ^= seed >> 17;
                seed ^= seed << 5;
                let value = supplied
                    .as_ref()
                    .map_or((seed & 255) as u8, |raw| raw[i * 4 + c]);
                if depth == Depth::U8 {
                    pixel[c] = value;
                } else {
                    let normalized = value as f32 * (1.0 / 255.0);
                    let word = (normalized * 32768.0 + 0.5) as u16;
                    pixel[c * 2..c * 2 + 2].copy_from_slice(&word.to_ne_bytes());
                }
            }
        }
        let mut output = vec![0; input.len()];
        for tolerance in [6, 64] {
            for _ in 0..3 {
                eprintln!("{depth:?} tolerance={tolerance}");
                render(
                    &View::new(&input, layout).unwrap(),
                    &mut ViewMut::new(&mut output, layout).unwrap(),
                    Params {
                        tolerance,
                        ..Default::default()
                    },
                    Rect::from_size(0, 0, width, height).unwrap(),
                )
                .unwrap();
            }
        }
        std::hint::black_box(output);
    }
}

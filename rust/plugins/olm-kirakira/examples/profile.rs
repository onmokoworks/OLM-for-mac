//! Bounded release microbenchmark: cargo run --release -p olm-kirakira --example profile
use olm_kirakira::{algorithm, filters};
use std::{hint::black_box, time::Instant};

fn measure<T>(name: &str, mut run: impl FnMut() -> T) {
    for sample in 0..3 {
        let start = Instant::now();
        black_box(run());
        println!(
            "{name} sample={sample} ms={:.3}",
            start.elapsed().as_secs_f64() * 1000.0
        );
    }
}

fn main() {
    let (w, h) = (1920, 1080);
    let src: Vec<f32> = (0..w * h)
        .map(|i| ((i * 7919 % 65521) as f32) / 65521.0)
        .collect();
    measure("gaussian len=100", || {
        filters::gaussian_horizontal_profile(&src, w, h, 100, true, false)
    });
    measure("highlight radius=12", || {
        filters::gaussian_highlight_profile(&src, w, h, 12, true, false)
    });
    let pixels: Vec<_> = src.iter().map(|&v| [v, v * 0.5, v * 0.25, 1.0]).collect();
    let p = algorithm::Params {
        blur: 3,
        lengths: [100, 100, 100, 100, 12],
        ..Default::default()
    };
    measure("heavy pipeline", || {
        algorithm::pixels(&pixels, w, h, &p, 1.0).unwrap()
    });
}

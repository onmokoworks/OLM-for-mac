//! Bounded phase timings, no host required. Run with `cargo run --release
//! -p olm-smoother2 --example smoother2-profile`; arithmetic remains the public pipeline.
use olm_smoother2::{
    algorithm::{self, Params},
    class_plane, frame,
    gamma::GammaMode,
    oklab,
    types::Pixel,
};
use std::{hint::black_box, time::Instant};
fn main() {
    let (w, h) = (1920, 1080);
    let input: Vec<_> = (0..w * h)
        .map(|i| {
            frame::load8([
                255,
                (i % 256) as u8,
                ((i / w) % 256) as u8,
                ((i * 37) % 256) as u8,
            ])
        })
        .collect();
    let threads = std::thread::available_parallelism().map_or(1, usize::from);
    for version in [2, 3] {
        let p = Params {
            version,
            smoothness: 100,
            extra: 0,
            range: 2,
            gamma_mode: GammaMode::None,
            gamma: 2.4,
            gamma_colors: vec![],
            key: None,
            keep_premultiplied: false,
        };
        for _ in 0..3 {
            let mut scratch = input.clone();
            let t = Instant::now();
            frame::setup(&mut scratch, version, None);
            let setup = t.elapsed();
            let t = Instant::now();
            let classes = class_plane::build_with_range(
                &scratch,
                w,
                h,
                2.0,
                version,
                1,
                &mut olm_core::Budget::new(w * h * 4),
            )
            .unwrap();
            black_box(classes);
            let class = t.elapsed();
            let t = Instant::now();
            for px in &scratch {
                black_box(oklab::cbrtf(black_box(px.r)));
                black_box(oklab::cbrtf(black_box(px.g)));
                black_box(oklab::cbrtf(black_box(px.b)));
            }
            let roots = t.elapsed();
            print!("version={version} serial_setup={setup:?} serial_classes={class:?} three_cbrtf={roots:?}");
            for workers in [1, threads] {
                let t = Instant::now();
                let output: Vec<Pixel> = algorithm::render(
                    &input,
                    w,
                    h,
                    &p,
                    workers,
                    &mut olm_core::Budget::new(w * h * 36),
                )
                .unwrap();
                black_box(output);
                print!(" full_{workers}={:?}", t.elapsed());
            }
            println!();
        }
    }
}

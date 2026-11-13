//! Bounded release microbenchmark: cargo run --release -p olm-kirakira --example profile
use olm_core::{Depth, Layout, Pixel, View, ViewMut};
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
    let defaults = algorithm::Params::default();
    // Checked typed-world boundary used by AE; setup/allocation excluded here.
    for depth in [Depth::U8, Depth::U16, Depth::F32] {
        let layout = Layout {
            width: w,
            height: h,
            stride: w * depth.pixel_bytes(),
            depth,
            origin: (0, 0),
        };
        let mut input = vec![0u8; layout.span().unwrap()];
        let mut output = input.clone();
        let mut view = ViewMut::new(&mut input, layout).unwrap();
        for y in 0..h {
            for x in 0..w {
                let v = src[y * w + x];
                view.set(
                    x,
                    y,
                    match depth {
                        Depth::U8 => Pixel::U8([255, (v * 255.0) as u8, 0, 0]),
                        Depth::U16 => Pixel::U16([32768, (v * 32768.0) as u16, 0, 0]),
                        Depth::F32 => Pixel::F32([1.0, v, 0.0, 0.0]),
                    },
                )
                .unwrap();
            }
        }
        let view = View::new(&input, layout).unwrap();
        measure(&format!("typed default {depth:?}"), || {
            algorithm::render(
                &view,
                &mut ViewMut::new(&mut output, layout).unwrap(),
                &defaults,
                1.0,
            )
            .unwrap()
        });
        measure(&format!("checked read/convert {depth:?}"), || {
            let mut values = Vec::with_capacity(w * h);
            for y in 0..h {
                for x in 0..w {
                    values.push(match view.get(x, y).unwrap() {
                        Pixel::U8(v) => v.map(|v| v as f32 * (1.0 / 255.0)),
                        Pixel::U16(v) => v.map(|v| v as f32 / 32768.0),
                        Pixel::F32(v) => v,
                    });
                }
            }
            values
        });
        measure(&format!("checked convert/write {depth:?}"), || {
            let mut view = ViewMut::new(&mut output, layout).unwrap();
            for y in 0..h {
                for x in 0..w {
                    let p = pixels[y * w + x];
                    view.set(
                        x,
                        y,
                        match depth {
                            Depth::U8 => Pixel::U8(p.map(|v| (algorithm::clamp(v) * 255.0) as u8)),
                            Depth::U16 => {
                                Pixel::U16(p.map(|v| (algorithm::clamp(v) * 32768.0) as u16))
                            }
                            Depth::F32 => Pixel::F32(p.map(algorithm::clamp)),
                        },
                    )
                    .unwrap();
                }
            }
        });
    }
    measure("default pipeline", || {
        algorithm::pixels(&pixels, w, h, &defaults, 1.0).unwrap()
    });
    measure("seed", || algorithm::seed(&pixels, &defaults));
    measure("source copy", || pixels.clone());
    measure("compose", || {
        pixels
            .iter()
            .map(|&v| algorithm::compose(v, v, 1.0, 1.0, 1))
            .collect::<Vec<_>>()
    });
    measure("box len=50 passes=3", || {
        filters::box_horizontal(&src, w, h, 50, 3, true, true)
    });
    for angle in [0.0_f64, 45.0, 90.0, 135.0] {
        let (s, c) = olm_kirakira::trig::extent_sincos(angle);
        let rw = olm_kirakira::trig::extent(w as i32, h as i32, c.abs(), s.abs()) as usize;
        let rh = olm_kirakira::trig::extent(h as i32, w as i32, c.abs(), s.abs()) as usize;
        let centered = filters::crop(&src, w, h, rw, rh);
        measure(&format!("warp {angle} {rw}x{rh}"), || {
            filters::warp(&centered, rw, rh, angle)
        });
        measure(&format!("box {angle} {rw}x{rh}"), || {
            filters::box_horizontal(&centered, rw, rh, 50, 3, true, true)
        });
        measure(&format!("ray {angle}"), || {
            filters::ray_profile(&src, w, h, 50, angle, 2, true, true, true)
        });
    }
    let p = algorithm::Params {
        blur: 3,
        lengths: [100, 100, 100, 100, 12],
        ..Default::default()
    };
    measure("heavy pipeline", || {
        algorithm::pixels(&pixels, w, h, &p, 1.0).unwrap()
    });
}

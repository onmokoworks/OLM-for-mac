#[path = "../src/field.rs"]
mod field;
use std::{hint::black_box, time::Instant};
fn measure(name: &str, mut f: impl FnMut()) {
    let mut ts = Vec::new();
    for i in 0..41 {
        let t = Instant::now();
        f();
        if i > 0 {
            ts.push(t.elapsed().as_secs_f64() * 1000.);
        }
    }
    ts.sort_by(f64::total_cmp);
    println!(
        "{name}: median {:.4} min {:.4} ms",
        (ts[19] + ts[20]) / 2.,
        ts[0]
    );
}
fn main() {
    let (w, h) = (960, 540);
    let mask: Vec<u8> = (0..w * h).map(|i| ((i % 5) > 1) as u8).collect();
    measure("field", || {
        black_box(field::normalized(&mask, w, h, w, h, 128., false, 255.));
    });
    let source = field::normalized(&mask, w, h, w, h, 128., false, 255.);
    let mut dst = source.clone();
    measure("8 staging + packing", || {
        for (d, &v) in dst.iter_mut().zip(&source) {
            *d = field::pack(v.clamp(0., 255.).round_ties_even() / 255., 255.);
        }
        black_box(&dst);
    });
    measure("16 packing", || {
        for (d, &v) in dst.iter_mut().zip(&source) {
            *d = field::pack(v, 32768.);
        }
        black_box(&dst);
    });
    use olm_core::{Depth, Layout, Pixel, View};
    for depth in [Depth::U8, Depth::U16] {
        let layout = Layout {
            width: w,
            height: h,
            stride: w * depth.pixel_bytes(),
            depth,
            origin: (0, 0),
        };
        let data = vec![128; layout.span().unwrap()];
        let view = View::new(&data, layout).unwrap();
        let mut mask = vec![0u8; w * h];
        measure(&format!("checked alpha-only {depth:?}"), || {
            for y in 0..h {
                for x in 0..w {
                    let alpha = match view.get(x, y).unwrap() {
                        Pixel::U8(v) => v[0] as f32 / 255.,
                        Pixel::U16(v) => v[0] as f32 / 32768.,
                        _ => unreachable!(),
                    };
                    let scaled = alpha * if depth == Depth::U16 { 256. } else { 255. };
                    mask[y * w + x] = (scaled >= 1.5 && scaled < 2147483648.) as u8;
                }
            }
            black_box(&mask);
        });
        measure(&format!("row mask {depth:?}"), || {
            for y in 0..h {
                for (m, pixel) in mask[y * w..(y + 1) * w]
                    .iter_mut()
                    .zip(view.row(y).unwrap().chunks_exact(depth.pixel_bytes()))
                {
                    *m = if depth == Depth::U8 {
                        (pixel[0] >= 2) as u8
                    } else {
                        (u16::from_ne_bytes([pixel[0], pixel[1]]) >= 192) as u8
                    };
                }
            }
            black_box(&mask);
        });
    }
    for threads in [1, 2, 4, 8, 16] {
        measure(&format!("empty rows {threads}"), || {
            olm_core::parallel_rows(&mut dst, w, threads, |_, row| {
                black_box(row);
            })
            .unwrap();
        });
    }
}

// Pure 32-bpc no-op copy profile; no IO or retained frames.
use std::{hint::black_box, time::Instant};
fn main() {
    let (w, h) = (960usize, 540usize);
    let stride = w * 16;
    let sources = vec![vec![0x5au8; stride * h]; 8];
    let mut outputs = vec![vec![0u8; stride * h]; 8];
    for workers in [0, 1, 2, 4, 8] {
        let mut times = Vec::new();
        for iteration in 0..31 {
            let source = &sources[iteration % 8];
            let output = &mut outputs[iteration % 8];
            let t = Instant::now();
            if workers == 0 {
                for (a, b) in source.chunks(stride).zip(output.chunks_mut(stride)) {
                    b.copy_from_slice(a);
                }
            } else if workers == 1 {
                output.copy_from_slice(&source);
            } else {
                let chunk = h.div_ceil(workers) * stride;
                std::thread::scope(|s| {
                    for (a, b) in source.chunks(chunk).zip(output.chunks_mut(chunk)) {
                        s.spawn(move || b.copy_from_slice(a));
                    }
                });
            }
            times.push(t.elapsed().as_secs_f64() * 1000.);
            black_box(&*output);
        }
        times.remove(0);
        times.sort_by(f64::total_cmp);
        println!("workers={workers} median_ms={:.3}", times[15]);
        assert_eq!(sources, outputs);
    }
}

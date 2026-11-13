use olm_blur::algorithm::{render_bytes, Params};
use olm_core::{Depth, Layout, View};
fn main() {
    let (w, h) = (960, 540);
    let layout = Layout {
        width: w,
        height: h,
        stride: w * 16,
        depth: Depth::F32,
        origin: (0, 0),
    };
    let mut source = vec![0u8; w * h * 16];
    for (i, p) in source.chunks_exact_mut(4).enumerate() {
        p.copy_from_slice(&((i % 251) as f32 / 255.).to_ne_bytes());
    }
    let mut dest = source.clone();
    let p = Params {
        amount: 5.,
        smoothness: 100.,
        repeat: 2,
        bias: 1,
        legacy: false,
        scale: 1.,
    };
    for _ in 0..8 {
        render_bytes(
            &View::new(&source, layout).unwrap(),
            &mut dest,
            layout,
            &p,
            std::thread::available_parallelism().unwrap().get(),
        )
        .unwrap();
        std::hint::black_box(&dest);
    }
}

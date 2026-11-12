use olm_core::{Depth, Rect};
use olm_golden::*;
use olm_smoother::algorithm::{self, Params};
fn main() {
    run("OLMSmoother", &[Depth::U8, Depth::U16], |c, input, out| {
        let p = Params {
            use_key: c.index % 2 == 1,
            key: [255; 4],
            tolerance: [0, 6, 20, 128, 255, 3][c.index % 6],
        };
        c.number(1, p.use_key as u8 as f64);
        c.color(2, p.key);
        c.number(3, p.tolerance);
        algorithm::render(
            input,
            out,
            p,
            Rect::from_size(0, 0, c.width, c.height).unwrap(),
        )
        .unwrap();
    });
}

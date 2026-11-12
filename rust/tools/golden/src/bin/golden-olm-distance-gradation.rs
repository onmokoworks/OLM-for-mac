use olm_distance_gradation::algorithm::{self, Params};
use olm_golden::*;
fn main() {
    run("DistanceGradation", ALL_DEPTHS, |c, input, out| {
        let i = c.index;
        let grad = c.color(7, [255, 255, 32, 0]);
        let bg = c.color(8, [255, 0, 17, 64]);
        let p = Params {
            invert: i % 2 == 1,
            in_out: 1 + (i % 3) as i32,
            inside: 3 + (i % 4) as i32,
            outside: 5,
            render_mode: 1 + (i % 2) as i32,
            use_bg: i % 3 == 1,
            grad,
            bg,
            interpolation: 1 + (i % 4) as i32,
            power: 1.5,
            blur_mode: [1, 2, 3, 5][i % 4],
            blur_size: 4,
            scale_x: (1, c.denominator),
            scale_y: (1, c.denominator),
        };
        for (s, n) in [
            (1, p.invert as u8 as f64),
            (2, p.in_out as f64),
            (3, p.inside as f64),
            (4, p.outside as f64),
            (5, p.render_mode as f64),
            (6, p.use_bg as u8 as f64),
            (9, p.interpolation as f64),
            (10, p.power as f64),
            (11, p.blur_mode as f64),
            (12, p.blur_size as f64),
        ] {
            c.number(s, n);
        }
        algorithm::render(input, out, &p).unwrap();
    });
}

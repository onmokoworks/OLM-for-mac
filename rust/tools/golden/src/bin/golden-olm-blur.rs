use olm_blur::algorithm::{self, Params};
use olm_golden::*;
fn main() {
    run("OLMBlur", ALL_DEPTHS, |c, input, out| {
        let p = Params {
            amount: [1., 5., 12.5][c.index % 3],
            smoothness: [1., 37., 100.][(c.index / 3) % 3],
            repeat: 1 + c.index % 3,
            bias: 1 + c.index % 2,
            legacy: c.index >= 9,
            scale: c.scale(),
        };
        for (s, n) in [
            (1, p.amount as f64),
            (2, p.smoothness as f64),
            (3, p.repeat as f64),
            (4, p.bias as f64),
            (5, p.legacy as u8 as f64),
        ] {
            c.number(s, n);
        }
        algorithm::render(input, out, &p, 1).unwrap();
    });
}

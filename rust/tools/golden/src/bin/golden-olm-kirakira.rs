use olm_golden::*;
use olm_kirakira::algorithm::{self, Params};
fn main() {
    run("OLMKiraKira", ALL_DEPTHS, |c, input, out| {
        let i = c.index;
        let approximate = i % 2 == 1;
        let mut p = Params {
            channel: 1 + (i % 6) as i32,
            blur: 1 + (i / 6) as i32,
            merge: 1 + (i % 2) as i32,
            approximate: approximate && c.scale() > 0.5,
            gain: 1.,
            strength: (125f32 * 0.01f32) as f64,
            fade: (0.25f32 * 0.2f32) as f64,
            glow_opacity: (80f32 * 0.01f32) as f64,
            source_opacity: (75f32 * 0.01f32) as f64,
            rotation: 0.,
            lengths: [3, 5, 2, 4, 1],
            ..Params::default()
        };
        for (s, n) in [
            (1, p.channel as f64),
            (2, p.blur as f64),
            (3, p.merge as f64),
            (4, approximate as u8 as f64),
            (5, 1.),
            (6, 125.),
            (7, 0.25),
            (8, 80.),
            (9, 75.),
        ] {
            c.number(s, n);
        }
        for j in 0..5 {
            c.number(10 + j * 6, p.lengths[j] as f64);
            let v = c.color(
                11 + j * 6,
                if j % 2 == 0 {
                    [255; 4]
                } else {
                    [255, 255, 128, 64]
                },
            );
            p.colors[j] = [v[1], v[2], v[3]];
            c.number(13 + j * 6, 0.);
        }
        c.angle(40, 0.);
        algorithm::render(input, out, &p, c.scale()).unwrap();
    });
}

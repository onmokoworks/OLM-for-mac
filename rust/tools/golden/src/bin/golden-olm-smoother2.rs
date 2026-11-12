use olm_core::{Budget, Depth, Pixel as Stored};
use olm_golden::*;
use olm_smoother2::{
    algorithm::{self, Params},
    frame,
    gamma::GammaMode,
    types::Pixel,
};
fn main() {
    run("OLMSmoother2", ALL_DEPTHS, |c, input, out| {
        let i = c.index;
        let key = i % 3 != 0;
        let invert = i % 3 == 2;
        let gamma = 1 + (i % 3) as i32;
        c.color(2, [255; 4]);
        c.color(11, [255; 4]);
        let p = Params {
            version: 1 + (i % 2) as i32,
            smoothness: [25, 70, 100][i % 3],
            extra: if i >= 9 { 50 } else { 0 },
            range: [0, 2, 20][(i / 3) % 3],
            gamma_mode: match gamma {
                1 => GammaMode::None,
                2 => GammaMode::Colors,
                _ => GammaMode::All,
            },
            gamma: 2.2,
            gamma_colors: vec![Pixel {
                r: 1.,
                g: 1.,
                b: 1.,
                a: 1.,
            }],
            key: if key {
                Some((
                    Pixel {
                        r: 1.,
                        g: 1.,
                        b: 1.,
                        a: 1.,
                    },
                    invert,
                ))
            } else {
                None
            },
            keep_premultiplied: false,
        };
        for (s, n) in [
            (1, key as u8 as f64),
            (3, invert as u8 as f64),
            (4, p.smoothness as f64),
            (5, p.extra as f64),
            (6, p.range as f64),
            (7, p.version as f64),
            (8, gamma as f64),
            (9, 2.2),
            (10, 1.),
        ] {
            c.number(s, n);
        }
        let mut source = Vec::new();
        for y in 0..c.height {
            for x in 0..c.width {
                source.push(match input.get(x, y).unwrap() {
                    Stored::U8(v) => frame::load8(v),
                    Stored::U16(v) => frame::load16(v),
                    Stored::F32([a, r, g, b]) => Pixel { r, g, b, a },
                });
            }
        }
        let result = algorithm::render(
            &source,
            c.width,
            c.height,
            &p,
            1,
            &mut Budget::new(64 * 1024 * 1024),
        )
        .unwrap();
        for (i, p) in result.iter().enumerate() {
            let a = [p.a, p.r, p.g, p.b];
            out.set(
                i % c.width,
                i / c.width,
                match c.depth {
                    Depth::U8 => Stored::U8(a.map(frame::pack8)),
                    Depth::U16 => Stored::U16(a.map(frame::pack16)),
                    Depth::F32 => Stored::F32(a),
                },
            )
            .unwrap();
        }
    });
}

use olm_color_key::algorithm::{self, Key, Params};
use olm_golden::*;
fn main() {
    run("OLMColorKey", ALL_DEPTHS, |c, input, out| {
        let i = c.index;
        let color = c.color(26, [255; 4]);
        let replacement = c.color(27, [255, 255, 0, 0]);
        let mut p = Params {
            keep: i % 2 == 1,
            threshold: 0.25,
            premultiplied: i % 3 == 1,
            space: 1 + (i % 6) as i32,
            precision: 1 + ((i / 6) % 3) as i32,
            per_color: i % 3 == 1,
            per_component: i % 3 == 2,
            components: [0.2, 0.3, 0.4],
            thin: [-2, 0, 2][i % 3],
            thin_distance: 1 + (i % 3) as i32,
            blur: [0., 1.5, 3.][(i / 3) % 3],
            blur_distance: 1 + ((i / 3) % 3) as i32,
            direction: 1 + (i % 3) as i32,
            replace: i >= 9,
            keys: vec![Key {
                enabled: true,
                replace: true,
                color: [color[1], color[2], color[3]],
                replacement: [replacement[1], replacement[2], replacement[3]],
                threshold: 0.35,
                components: [0.1, 0.2, 0.3],
            }],
            step_x: c.denominator as f32,
            step_y: c.denominator as f32,
        };
        if i >= 12 {
            let last = p.keys[0].clone();
            p.keys[0].enabled = false;
            for index in 1..200 {
                let mut key = last.clone();
                key.enabled = index == 199;
                let slot = 24 + index * 8;
                c.number(slot, key.enabled as u8 as f64);
                c.number(slot + 1, 1.);
                c.color(slot + 2, [255; 4]);
                c.color(slot + 3, [255, 255, 0, 0]);
                c.number(slot + 4, 0.35);
                c.number(slot + 5, 0.1);
                c.number(slot + 6, 0.2);
                c.number(slot + 7, 0.3);
                p.keys.push(key);
            }
        }
        for (s, n) in [
            (1, p.keep as u8 as f64),
            (2, 0.25),
            (4, p.premultiplied as u8 as f64),
            (5, p.space as f64),
            (6, p.precision as f64),
            (7, p.per_color as u8 as f64),
            (8, p.per_component as u8 as f64),
            (9, 0.2),
            (10, 0.3),
            (11, 0.4),
            (14, p.thin as f64),
            (15, p.thin_distance as f64),
            (18, p.blur as f64),
            (19, p.blur_distance as f64),
            (20, p.direction as f64),
            (22, p.keys.len() as f64),
            (23, p.replace as u8 as f64),
            (24, p.keys[0].enabled as u8 as f64),
            (25, 1.),
            (28, 0.35),
            (29, 0.1),
            (30, 0.2),
            (31, 0.3),
        ] {
            c.number(s, n);
        }
        algorithm::render_smart(input, out, &p).unwrap();
    });
}

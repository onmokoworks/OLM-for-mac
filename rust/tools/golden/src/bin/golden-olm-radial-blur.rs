use olm_golden::*;
use olm_radial_blur::algorithm::{self, Params};
fn main() {
    run("OLMRadialBlur", ALL_DEPTHS, |c, input, out| {
        let i = c.index;
        c.point(2, [50., 50.]);
        let angle = [0., 15., 45.][i % 3];
        let phase = if i % 2 == 0 { 0.0 } else { 1.0 };
        let p = Params {
            rotation: i % 2 == 1,
            center: [c.width as f64 * 0.5, c.height as f64 * 0.5],
            strength: [8, 4],
            offset: [2, 1],
            mode: [1 + (i % 3) as i32, 1 + ((i / 3) % 3) as i32],
            fade: [5, 3],
            repeat: i % 3 != 0,
            ratio: 1.25,
            angle,
            quality: 2.,
            gain: 1.,
            size: 10.,
            noise: if i < 6 { 0. } else { 20. },
            noise_type: 1 + (i % 2) as i32,
            seed: 11,
            phase: ((phase * 65536.) * 2.663161090079238e-7) as f32,
            thickness: 8.,
            downsample: c.scale(),
        };
        for (s, n) in [
            (1, if p.rotation { 2. } else { 1. }),
            (4, 8.),
            (5, p.mode[0] as f64),
            (6, 2.),
            (7, 5.),
            (10, 4.),
            (11, p.mode[1] as f64),
            (12, 1.),
            (13, 3.),
            (15, p.repeat as u8 as f64),
            (17, 1.25),
            (20, 2.),
            (21, 1.),
            (22, 10.),
            (24, p.noise),
            (25, p.noise_type as f64),
            (27, 11.),
            (29, 8.),
        ] {
            c.number(s, n);
        }
        c.angle(18, angle);
        c.angle(28, phase);
        algorithm::render(&p, input, out, 1).unwrap();
    });
}

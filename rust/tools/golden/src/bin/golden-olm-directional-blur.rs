use olm_core::{Depth, Pixel};
use olm_directional_blur::algorithm::{self, Params};
use olm_golden::*;
fn main() {
    run("OLMDirectionalBlur", ALL_DEPTHS, |c, input, out| {
        let i = c.index;
        let p = Params {
            angle: [0., 45., 90.][i % 3],
            gain: 1.25,
            size: ((i % 3) * 20) as f32,
            front: 8,
            front_fade: if i % 2 == 0 { 4 } else { 0 },
            front_tail: 25.,
            back: if i % 2 == 0 { 0 } else { 8 },
            back_fade: 2,
            back_tail: 50.,
            noise: if i < 6 { 0. } else { 30. },
            noise_type: 1 + (i % 2) as i32,
            seed: 13,
            offset: if i % 2 == 0 { 0 } else { 1 },
            thickness: 8.,
        };
        for (s, n) in [
            (2, p.gain as f64),
            (3, p.size as f64),
            (5, p.front as f64),
            (6, p.front_fade as f64),
            (7, p.front_tail as f64),
            (10, p.back as f64),
            (11, p.back_fade as f64),
            (12, p.back_tail as f64),
            (15, p.noise as f64),
            (16, p.noise_type as f64),
            (18, p.seed as f64),
            (20, p.thickness as f64),
        ] {
            c.number(s, n);
        }
        c.angle(1, p.angle as f64);
        c.angle(19, p.offset as f64);
        let mut source = Vec::new();
        for y in 0..c.height {
            for x in 0..c.width {
                let a = match input.get(x, y).unwrap() {
                    Pixel::U8(v) => v.map(|n| n as f32 / 255.),
                    Pixel::U16(v) => v.map(|n| n as f32 * (1. / 32768.)),
                    Pixel::F32(v) => v,
                };
                source.push([a[1], a[2], a[3], a[0]]);
            }
        }
        let depth = match c.depth {
            Depth::U8 => algorithm::Depth::U8,
            Depth::U16 => algorithm::Depth::U16,
            Depth::F32 => algorithm::Depth::F32,
        };
        let result = algorithm::render(
            &source,
            c.width,
            c.height,
            &p.sampled(c.scale()),
            depth,
            None,
            1,
        )
        .unwrap();
        for (i, v) in result.iter().enumerate() {
            let a = [v[3], v[0], v[1], v[2]];
            out.set(
                i % c.width,
                i / c.width,
                match c.depth {
                    Depth::U8 => Pixel::U8(a.map(|v| olm_math::x86::cvttss2si(v * 255.) as u8)),
                    Depth::U16 => {
                        Pixel::U16(a.map(|v| olm_math::x86::cvttss2si(v * 32768.) as u16))
                    }
                    Depth::F32 => Pixel::F32(a),
                },
            )
            .unwrap();
        }
    });
}

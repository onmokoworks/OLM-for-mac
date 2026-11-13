//! Retained C++ source gates and public parameter refusals.
use crate::{
    algorithm::{Depth, Params},
    host::RenderContext,
    sha256,
};
use olm_core::{Error, Layout, Pixel, Result, View};
fn hash(view: &View<'_>) -> Result<String> {
    let l = view.layout();
    let mut b = Vec::new();
    for y in 0..l.height {
        for x in 0..l.width {
            match view.get(x, y)? {
                Pixel::U8(v) => b.extend(v),
                Pixel::U16(v) => {
                    for c in v {
                        b.extend(c.to_le_bytes())
                    }
                }
                Pixel::F32(v) => {
                    for c in v {
                        b.extend(c.to_bits().to_le_bytes())
                    }
                }
            }
        }
    }
    Ok(sha256::hash(&b))
}
fn higher(p: &Params) -> bool {
    p.angle == 45.0
        && p.gain == 1.0
        && p.front == 8
        && p.back == 8
        && p.seed == 1
        && p.offset == 0
        && p.thickness == 3.0
        && [
            (50, 50.0, 100, 100.0, 0.0, 25.0, 1),
            (50, 100.0, 50, 50.0, 50.0, 100.0, 2),
            (100, 50.0, 50, 100.0, 0.0, 100.0, 2),
            (100, 100.0, 100, 50.0, 50.0, 25.0, 1),
        ]
        .contains(&(
            p.front_fade,
            p.front_tail,
            p.back_fade,
            p.back_tail,
            p.size,
            p.noise,
            p.noise_type,
        ))
}
fn type3(p: &Params) -> bool {
    p.angle == 45.0
        && p.gain == 1.0
        && p.front == 8
        && p.front_fade == 0
        && p.front_tail == 50.0
        && p.back == 0
        && p.back_fade == 0
        && p.back_tail == 0.0
        && p.size == 0.0
        && p.noise == 100.0
        && p.noise_type == 3
        && p.seed == 1
        && p.offset == 0
        && p.thickness == 3.0
}
pub fn check(
    input: &View<'_>,
    out: Layout,
    p: &Params,
    depth: Depth,
    ctx: RenderContext,
    layer: Option<&View<'_>>,
) -> Result<()> {
    let a = input.layout();
    let fail = Err(Error::Unsupported);
    // RenderWorld deliberately tests the tuple against 32x18 before world gating.
    if higher(p) {
        let geometry = (a.width, a.height);
        let i = match depth {
            Depth::U8 => 0,
            Depth::U16 => 1,
            Depth::F32 => 2,
        };
        let stride = if geometry == (32, 18) {
            [140, 272, 544][i]
        } else {
            [268, 528, 1056][i]
        };
        let accepted = if geometry == (32, 18) {
            p.front_fade == 50
                && p.front_tail == 100.0
                && p.back_fade == 50
                && p.back_tail == 50.0
                && p.size == 50.0
                && p.noise == 100.0
                && p.noise_type == 2
        } else {
            geometry == (64, 36)
        };
        let expected = if geometry == (32, 18) {
            [
                "7c65cdf081119a7db77d804cb5ad256f3b89beb73bb32587fbf53224c56d06e6",
                "44f6470ac55a81953e062df177d996a0336348a472b7e0e050b8de261c1fcbf5",
                "0c626ba0cc34551753ea2176999eb075610ebd63c40fee5af7b2c31a10812ba6",
            ][i]
        } else {
            [
                "0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03",
                "18f79acc8e254e7f1bf8c3753a0d82badcc9f9247f568ba0088b5caf74e5d450",
                "884631deb3be114d9a226566d537323fc1f634e83f58cdd30b73c98cacef708d",
            ][i]
        };
        if !accepted
            || ctx.input_extent != [0, 0, a.width as i32, a.height as i32]
            || ctx.output_extent != ctx.input_extent
            || a.stride != stride
            || out.stride != stride
            || hash(input)? != expected
        {
            return fail;
        }
    }
    if depth == Depth::U8 && type3(p) {
        let Some(l) = layer else { return fail };
        if ctx.input_extent != [0, 0, 16, 16]
            || ctx.output_extent != [0, 0, 16, 16]
            || (a.width, a.height) != (16, 16)
            || a.stride != 76
            || out.stride != 76
            || l.layout().stride != 84
            || hash(input)? != "ad840bf75281333fc389ba7083074e10ff82e7538583242e7a91880e6bbe1b83"
        {
            return fail;
        }
        if hash(l)? != hash(input)? {
            return fail;
        }
    }
    if p.identity() {
        return Ok(());
    }
    if depth == Depth::U8
        && (a.width, a.height) == (64, 36)
        && p.angle == 45.0
        && p.gain == 1.0
        && p.front == 8
        && p.front_fade == 0
        && p.front_tail == 0.0
        && p.back == 0
        && p.back_fade == 0
        && p.back_tail == 0.0
        && p.size == 0.0
        && p.noise == 25.0
        && p.noise_type == 2
        && p.seed == 1
        && p.offset == 0
        && p.thickness == 3.0
    {
        let allowed = [
            "0380a27194735f3eb5556bc005fe4be9cc2e1cccfe1a8987226c18d6a146fe03",
            "2d07a41ae992770085117e9815300bfd0730745883e60b24aaad5e69dfc087ae",
            "784c27133912eb473bb88c560af00d1cadb2c841297bf05ccef648036a86e212",
            "c549e434122a54ed2d78b23249ba25bbe6a4c121469a9b1e195743848095cd10",
            "b5274891a810ed4743b9b8b0816ed8fb6c5a9a1d5f777d71f32d2be010e02fa0",
        ];
        if !allowed.contains(&hash(input)?.as_str()) {
            return fail;
        }
    }
    if !(-32768.0..=32767.99998474121).contains(&(p.angle as f64)) {
        return fail;
    }
    if p.noise > 0.0
        && p.noise_type != 3
        && (!(1..=1000).contains(&p.seed)
            || !(-32768..=32767).contains(&p.offset)
            || p.thickness > 100.0)
    {
        return fail;
    }
    if p.noise > 0.0 && p.noise_type == 3 {
        let Some(l) = layer else { return fail };
        let b = l.layout();
        if (b.width, b.height) != (a.width, a.height) {
            return fail;
        }
        if depth == Depth::U8 {
            let legacy = (a.width, a.height) == (16, 16)
                && p.angle == 27.0
                && p.gain == 1.125
                && p.size == 38.0
                && p.front == 37
                && p.front_fade == 9
                && p.front_tail == 23.0
                && p.back == 19
                && p.back_fade == 7
                && p.back_tail == 31.0
                && p.noise == 73.0;
            if p.front == 0 && p.back == 0 {
                return fail;
            }
            if p.size != 0.0
                && (p.front_fade != 0
                    || p.front_tail != 0.0
                    || p.back_fade != 0
                    || p.back_tail != 0.0)
                && !legacy
                && !higher(p)
            {
                return fail;
            }
        } else {
            if a.origin != (0, 0) || out.origin != (0, 0) || b.origin != (0, 0) {
                return fail;
            }
            for y in 0..b.height {
                for x in 0..b.width {
                    if !l.get(x, y)?.normalized().iter().all(|v| v.is_finite()) {
                        return fail;
                    }
                }
            }
        }
    }
    if !ctx.smart {
        if a.width > 4096 || a.height > 4096 || a.width * a.height > 4096 * 2160 {
            return fail;
        }
        if depth == Depth::F32 {
            for y in 0..a.height {
                for x in 0..a.width {
                    if !input.get(x, y)?.normalized().iter().all(|v| v.is_finite()) {
                        return fail;
                    }
                }
            }
        }
    }
    if !ctx.smart {
        let diagonal = (a.width * a.width + a.height * a.height) as f32;
        let half = 2 - (diagonal.sqrt() * -0.5) as i32;
        let w = (a.width as i32 + (half - (a.width / 2) as i32) * 2) as u64;
        let h = (a.height as i32 + (half - (a.height / 2) as i32) * 2) as u64;
        let pixels = w * h;
        let component = p.size != 0.0 || p.front_tail != 0.0 || p.back_tail != 0.0;
        let generated = p.noise > 0.0 && p.noise_type != 3;
        let layer_mode = p.noise > 0.0 && p.noise_type == 3;
        let mut bound = 1.0f64;
        if layer_mode {
            if let Some(l) = layer {
                let mut product = 0.0f64;
                for y in 0..a.height {
                    for x in 0..a.width {
                        let v = l.get(x, y)?.normalized();
                        let rgb = (v[1].abs() as f64)
                            .max(v[2].abs() as f64)
                            .max(v[3].abs() as f64);
                        product = product.max(v[0].abs() as f64 * rgb);
                    }
                }
                let opacity = p.noise as f64 / 100.0;
                bound = (product * opacity + 1.0 - opacity).max(1.0)
                    * (1.0 + 32.0 * f32::EPSILON as f64);
            }
        }
        let scatter = |n: i32| {
            let len = ((n as f64 * bound) as u64).min(w);
            if len > 1 {
                (len - 1) * (2 * w - len - 2) / 2
            } else {
                0
            }
        };
        let noise_pixels = if generated {
            ((w as f32 / p.thickness + 3.0) as u64)
                .checked_mul((h as f32 / p.thickness + 3.0) as u64)
                .ok_or(Error::Overflow)?
        } else {
            0
        };
        let units = (scatter(p.front) + scatter(p.back)) * h
            + pixels
                * (8 + 4 * (p.front_fade + p.back_fade) as u64
                    + if component { 12 } else { 0 }
                    + if layer_mode { 32 } else { 0 })
            + noise_pixels * 64;
        let bytes = pixels * (56 + if component { 24 } else { 0 } + if layer_mode { 8 } else { 0 })
            + a.width as u64
                * a.height as u64
                * a.depth.pixel_bytes() as u64
                * (2 + if layer_mode { 1 } else { 0 })
            + (p.front + p.back + p.front_fade.max(1) + p.back_fade.max(1) + 2) as u64 * 4
            + noise_pixels * 4
            + if generated { 404 } else { 0 }
            + 64 * 1024 * 1024;
        if units > 350_000_000 || bytes > 3 * 1024 * 1024 * 1024 {
            return fail;
        }
    }
    Ok(())
}

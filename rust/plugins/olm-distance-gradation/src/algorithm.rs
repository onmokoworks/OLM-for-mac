//! SmartFX field staging and composition. No AE types or platform math.
use olm_core::{Depth, Error, Pixel, Result, View, ViewMut};
use olm_math::{pow, powf, Mode};
#[derive(Clone, Debug)]
pub struct Params {
    pub invert: bool,
    pub in_out: i32,
    pub inside: i32,
    pub outside: i32,
    pub render_mode: i32,
    pub use_bg: bool,
    pub grad: [f32; 4],
    pub bg: [f32; 4],
    pub interpolation: i32,
    pub power: f32,
    pub blur_mode: i32,
    pub blur_size: u32,
    pub scale_x: (u32, u32),
    pub scale_y: (u32, u32),
}
impl Default for Params {
    fn default() -> Self {
        Self {
            invert: false,
            in_out: 1,
            inside: 128,
            outside: 128,
            render_mode: 1,
            use_bg: false,
            grad: [1., 1., 0., 0.],
            bg: [1., 0., 0., 0.],
            interpolation: 2,
            power: 1.,
            blur_mode: 1,
            blur_size: 0,
            scale_x: (1, 1),
            scale_y: (1, 1),
        }
    }
}
fn weighted(a: f32, b: f32) -> f32 {
    if a.is_infinite() && b == 0. {
        f32::from_bits(0xffc00000)
    } else {
        a * b
    }
}
pub fn compose(
    src: [f32; 4],
    aux: f32,
    mut x: f32,
    p: &Params,
    blurred: bool,
    degenerate: bool,
) -> [f32; 4] {
    if degenerate {
        return if p.use_bg {
            [1., p.bg[1], p.bg[2], p.bg[3]]
        } else {
            [0.; 4]
        };
    }
    let ownership = match p.in_out {
        3 => 1.,
        2 => 1. - src[0],
        _ => src[0],
    };
    if ownership < 0.0001 {
        return [0., x, x, if blurred { aux } else { x }];
    }
    if !p.invert {
        x = 1. - x;
    }
    if p.interpolation == 3 {
        let t = (1. - x) as f64;
        let s = 1. - pow(t, 2., Mode::Fma);
        x = if s < 0. { 0. } else { s.sqrt() as f32 };
    } else if p.interpolation == 4 {
        x = powf(x, p.power, Mode::Fma);
    }
    if p.interpolation == 1 && !blurred {
        x = if x > 0. { 1. } else { 0. };
    }
    let mut alpha = ownership;
    if p.in_out == 2 {
        if alpha < 0. {
            alpha = 0.;
        }
        if alpha > 1. {
            alpha = 1.;
        }
    }
    if p.render_mode == 2 && !p.use_bg {
        return [weighted(alpha, x), src[1], src[2], src[3]];
    }
    let color = if p.render_mode == 1 { p.grad } else { src };
    if p.use_bg {
        let one = 1. - x;
        [
            alpha,
            one * p.bg[1] + weighted(color[1], x),
            one * p.bg[2] + weighted(color[2], x),
            one * p.bg[3] + weighted(color[3], x),
        ]
    } else {
        [weighted(alpha, x), color[1], color[2], color[3]]
    }
}
pub fn render(input: &View<'_>, output: &mut ViewMut<'_>, params: &Params) -> Result<()> {
    let l = input.layout();
    let o = output.layout();
    let (w, h) = (l.width, l.height);
    if w == 0 || h == 0 || o.width > w || o.height > h || o.depth != l.depth {
        return Err(Error::Bounds);
    }
    let mut p = params.clone();
    if p.scale_x.0 == 0 || p.scale_x.1 == 0 || p.scale_y.0 == 0 || p.scale_y.1 == 0 {
        return Err(Error::Unsupported);
    }
    let rw = (w as u32).wrapping_mul(p.scale_x.1) as f32 / p.scale_x.0 as f32;
    let rh = (h as u32).wrapping_mul(p.scale_y.1) as f32 / p.scale_y.0 as f32;
    if !(rw >= 1. && rh >= 1. && rw < 2147483648. && rh < 2147483648.) {
        return Err(Error::Bounds);
    }
    let (rw, rh) = (rw as usize, rh as usize);
    let count = olm_core::image_len(w, h)?;
    olm_core::image_len(rw, rh)?;
    let bx = p.blur_size.wrapping_mul(p.scale_x.0) / p.scale_x.1;
    let by = p.blur_size.wrapping_mul(p.scale_y.0) / p.scale_y.1;
    p.blur_size = bx;
    if l.depth == Depth::F32 && p.interpolation == 4 && p.power == 1. {
        p.interpolation = 2;
    }
    let blurred = p.blur_mode != 1
        && (bx > 0
            || ((p.blur_mode == 2 || p.blur_mode == 3) && by > 0)
            || (l.depth != Depth::U16 && p.blur_mode == 5));
    // Mirror the existing PF32 Smart admission. Large Median Power remains refused.
    if l.depth == Depth::F32 {
        if !(1..=2).contains(&p.render_mode)
            || p.inside < 0
            || p.outside < 0
            || !(1..=5).contains(&p.blur_mode)
            || !(1..=4).contains(&p.interpolation)
        {
            return Err(Error::Unsupported);
        }
        if p.interpolation == 4
            && (!p.power.is_finite()
                || !(0.01..=5.).contains(&p.power)
                || (p.blur_mode == 4 && bx > 2))
        {
            return Err(Error::Unsupported);
        }
        if blurred
            && p.blur_mode != 5
            && (bx > if p.blur_mode == 4 { 500 } else { 4096 }
                || p.inside > 1000
                || p.outside > 1000
                || !p.power.is_finite()
                || !(0.01..=5.).contains(&p.power)
                || p.grad
                    .iter()
                    .chain(p.bg.iter())
                    .any(|v| !v.is_finite() || !(0. ..=1.).contains(v)))
        {
            return Err(Error::Unsupported);
        }
    }
    let mut mask = vec![0u8; count];
    let mut any = false;
    let mut any_not = false;
    for y in 0..h {
        for x in 0..w {
            let src = normalized(input.get(x, y)?);
            if l.depth == Depth::F32 {
                let nonfinite = !blurred || p.blur_mode == 5;
                let extended = nonfinite || p.blur_mode != 4;
                if (!nonfinite && src[0] * 255. >= 2147483648.)
                    || src.iter().any(|v| {
                        (!v.is_finite() && !nonfinite) || ((*v < 0. || *v > 1.) && !extended)
                    })
                {
                    return Err(Error::Unsupported);
                }
            }
            let scaled = src[0] * if l.depth == Depth::U16 { 256. } else { 255. };
            let owns = scaled >= 1.5 && scaled < 2147483648.;
            mask[y * w + x] = owns as u8;
            any |= owns;
            any_not |= !owns;
        }
    }
    let degenerate = !any || !any_not;
    let scaled8 = l.depth == Depth::U8 && blurred;
    let staged8 = l.depth == Depth::U8 && !blurred;
    let max = if l.depth == Depth::U8 { 255. } else { 1. };
    let make = |m: &[u8], threshold: i32| {
        let mut f =
            crate::field::normalized(m, w, h, rw, rh, threshold as f32, p.interpolation == 1, max);
        if staged8 {
            for v in &mut f {
                *v = v.clamp(0., 255.).round_ties_even() / 255.;
            }
        }
        f
    };
    let mut field = match p.in_out {
        1 => {
            if !any_not {
                vec![if p.invert { 0. } else { 1. }; count]
            } else {
                make(&mask, p.inside)
            }
        }
        2 => {
            let m: Vec<_> = mask.iter().map(|v| 1 - v).collect();
            make(&m, p.outside)
        }
        3 => {
            let mut a = make(&mask, p.inside);
            let m: Vec<_> = mask.iter().map(|v| 1 - v).collect();
            let b = make(&m, p.outside);
            for (a, b) in a.iter_mut().zip(b) {
                *a = a.max(b);
            }
            a
        }
        _ => vec![0.; count],
    };
    if p.interpolation == 1 && blurred {
        let max = if scaled8 { 255. } else { 1. };
        for v in &mut field {
            *v = if *v >= max { max } else { 0. };
        }
    }
    let mut aux = if blurred { field.clone() } else { vec![] };
    if blurred {
        let r = if p.blur_mode == 5 { bx.max(1) } else { bx } as usize;
        let kx = 2 * r + 1;
        let ky = 2 * by as usize + 1;
        if kx > 1 || ky > 1 {
            match p.blur_mode {
                2 => crate::filters::box_blur(&mut field, w, h, kx, ky),
                3 => crate::filters::gaussian_native(&mut field, w, h, kx, ky),
                4 => crate::filters::median(&mut field, w, h, kx),
                5 => {
                    if l.depth == Depth::U16 {
                        for v in &mut field {
                            *v *= 32768.;
                        }
                    }
                    let scalar = l.depth != Depth::U16
                        && r >= if l.depth == Depth::F32 { 2 } else { 3 }
                        && r <= if l.depth == Depth::F32 { 4096 } else { 32 }
                        && (r == 2 || w <= 2 * r || h <= 2 * r);
                    crate::bilateral::blur_mode(&mut field, w, h, r, scalar, true);
                    if l.depth == Depth::U16 {
                        for v in &mut field {
                            *v /= 32768.;
                        }
                    }
                }
                _ => (),
            }
        }
    }
    for f in [&mut field, &mut aux] {
        match l.depth {
            Depth::U16 => {
                for v in f.iter_mut() {
                    *v = crate::field::pack(*v, 32768.);
                }
            }
            Depth::U8 => {
                for v in f.iter_mut() {
                    *v = if scaled8 {
                        v.clamp(0., 255.).round_ties_even() / 255.
                    } else {
                        crate::field::pack(*v, 255.)
                    };
                }
            }
            _ => (),
        }
    }
    for y in 0..o.height {
        for x in 0..o.width {
            let i = y * o.width + x;
            let src = normalized(input.get(x, y)?);
            let v = compose(
                src,
                if blurred { aux[i] } else { 0. },
                field[i],
                &p,
                blurred,
                degenerate,
            );
            let pixel = match l.depth {
                Depth::U8 => Pixel::U8(v.map(|v| (v * 255.).clamp(0., 255.) as u8)),
                Depth::U16 => Pixel::U16(v.map(|v| olm_math::x86::cvttss2si(v * 32768.) as u16)),
                Depth::F32 => Pixel::F32(v),
            };
            output.set(x, y, pixel)?;
        }
    }
    Ok(())
}

fn normalized(p: Pixel) -> [f32; 4] {
    match p {
        Pixel::U8(v) => v.map(|x| x as f32 / 255.),
        Pixel::U16(v) => v.map(|x| x as f32 / 32768.),
        Pixel::F32(v) => v,
    }
}

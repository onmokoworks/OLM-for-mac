//! ColorKeep pixel algorithm translated from mac/ColorKeep/ColorKeep.cpp.
use olm_core::{Pixel, View, ViewMut};

/// Palette colors are host float ARGB, including alpha. RGB survives rejection.
pub fn pixel(p: Pixel, palette: &[[f32; 4]]) -> Pixel {
    let hit = palette.iter().any(|c| match p {
        Pixel::U8(v) => (0..4).all(|i| {
            v[i] == (olm_math::x86::cvttss2si((c[i] + f32::from_bits(0x3b008081)) * 255.0) as u8)
        }),
        Pixel::U16(v) => (0..4).all(|i| {
            v[i] == (olm_math::x86::cvttss2si((c[i] + f32::from_bits(0x37800000)) * 32768.0) as u16)
        }),
        Pixel::F32(v) => (0..4).all(|i| !((v[i] - c[i]).abs() > 1.0e-4f32)),
    });
    if hit {
        p
    } else {
        p.with_alpha(0.0)
    }
}
pub fn render(
    input: &View<'_>,
    output: &mut ViewMut<'_>,
    palette: &[[f32; 4]],
) -> olm_core::Result<()> {
    if palette.len() > 100 {
        return Err(olm_core::Error::Unsupported);
    }
    let l = output.layout();
    if !input.layout().rect()?.contains(l.rect()?) {
        return Err(olm_core::Error::Bounds);
    }
    for y in 0..l.height {
        for x in 0..l.width {
            let p = input.get_global(
                (l.origin.0 as i64 + x as i64) as i32,
                (l.origin.1 as i64 + y as i64) as i32,
            )?;
            output.set(x, y, pixel(p, palette))?;
        }
    }
    Ok(())
}
#[cfg(any(target_os = "windows", target_os = "macos"))]
mod ae {
    use olm_ae::{Effect, Kind, Param, RenderContext, Value};
    pub struct Plugin;
    impl Effect for Plugin {
        const NAME: &'static str = "Color Keep";
        const MATCH_NAME: &'static str = "OLM Color Keep";
        const VERSION: u32 = 526336;
        const FLAGS: u32 = 0x02000040;
        fn params() -> Vec<Param> {
            let mut p = vec![Param {
                id: 1,
                name: "Enabled Color Num".into(),
                flags: 64,
                kind: Kind::Integer {
                    min: 0,
                    max: 100,
                    slider_min: 0,
                    slider_max: 100,
                    default: 1,
                },
            }];
            for i in 0..100 {
                p.push(Param {
                    id: 2 + i,
                    name: "Color".into(),
                    flags: 0,
                    kind: Kind::Color,
                });
            }
            p
        }
        fn render(
            v: &[Value],
            ctx: RenderContext,
            input: &super::View<'_>,
            out: &mut super::ViewMut<'_>,
        ) -> olm_core::Result<()> {
            let n = (v[0].number as usize).min(100);
            let colors: Vec<_> = v[1..=n].iter().map(|v| v.color).collect();
            if ctx.smart {
                let l = out.layout();
                let r = ctx
                    .output_extent
                    .intersection(olm_core::Rect::from_size(0, 0, l.width, l.height)?);
                for y in r.top()..r.bottom() {
                    for x in r.left()..r.right() {
                        out.set(
                            x as usize,
                            y as usize,
                            super::pixel(input.get(x as usize, y as usize)?, &colors),
                        )?;
                    }
                }
                Ok(())
            } else {
                super::render(input, out, &colors)
            }
        }
    }
    olm_ae::export_effect!(Plugin, entryPointFunc);
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn alpha_is_part_of_key() {
        let p = Pixel::U8([128, 255, 0, 0]);
        assert_eq!(pixel(p, &[[1.0, 1.0, 0.0, 0.0]]), Pixel::U8([0, 255, 0, 0]));
        assert_eq!(pixel(p, &[[128.0 / 255.0, 1.0, 0.0, 0.0]]), p);
    }
    #[test]
    fn unordered_falls_through() {
        let p = Pixel::F32([0.5, f32::NAN, 0.0, 0.0]);
        assert_eq!(pixel(p, &[[0.5, 1.0, 0.0, 0.0]]).alpha(), 0.5);
    }
}

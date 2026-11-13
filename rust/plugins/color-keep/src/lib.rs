//! ColorKeep 1.1.0, translated from the 2026-11-12 Windows CPU release.
use olm_core::{Pixel, View, ViewMut};

/// Palette colors are host float ARGB; only RGB participates in matching.
/// New 2025 callbacks: RVAs 0x15c0 / 0x1690 / 0x1780 (8/16/32 bpc).
/// Conversion helpers 0x7080 / 0x70f0 multiply in binary32; 0x7160 copies.
/// COMISS/JA rejects strictly greater differences, accepting unordered values.
/// The original copies the input world first, then writes only output alpha.
pub fn pixel(p: Pixel, palette: &[[f32; 4]]) -> Pixel {
    let normalized = match p {
        Pixel::U8(v) => v.map(|x| x as f32 * f32::from_bits(0x3b808081)),
        Pixel::U16(v) => v.map(|x| x as f32 * f32::from_bits(0x38000000)),
        Pixel::F32(v) => v,
    };
    let hit = palette
        .iter()
        .any(|c| (1..4).all(|i| !((c[i] - normalized[i]).abs() > 1.0e-4f32)));
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
    if palette.len() > 200 {
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
        const NAME: &'static str = "OLM Color Keep";
        const MATCH_NAME: &'static str = "OLM Color Keep";
        const VERSION: u32 = 557056;
        const FLAGS: u32 = 0x02000040;
        fn params() -> Vec<Param> {
            let mut p = vec![Param {
                id: 1,
                name: "Enabled Color Num".into(),
                flags: 64,
                kind: Kind::Integer {
                    min: 0,
                    max: 200,
                    slider_min: 0,
                    slider_max: 200,
                    default: 1,
                },
            }];
            for i in 0..200 {
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
            let n = (v[0].number as usize).min(200);
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
    olm_ae::export_effect!(Plugin, entry_point);
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn alpha_is_not_part_of_key() {
        let p = Pixel::U8([128, 255, 0, 0]);
        assert_eq!(pixel(p, &[[1.0, 1.0, 0.0, 0.0]]), p);
        assert_eq!(pixel(p, &[[128.0 / 255.0, 1.0, 0.0, 0.0]]), p);
    }
    #[test]
    fn normalized_integer_thresholds() {
        // PF16 admits a three-word difference, but rejects four words.
        let p = Pixel::U16([1234, 16384, 0, 0]);
        assert_eq!(pixel(p, &[[1.0, 16387.0 / 32768.0, 0.0, 0.0]]), p);
        assert_eq!(
            pixel(p, &[[1.0, 16388.0 / 32768.0, 0.0, 0.0]]),
            p.with_alpha(0.0)
        );
        // PF8 no longer rounds an arbitrary float palette to a byte key.
        let p = Pixel::U8([123, 128, 0, 0]);
        let r = 128.0 * f32::from_bits(0x3b808081);
        assert_eq!(pixel(p, &[[0.0, r + 0.00005, 0.0, 0.0]]), p);
        assert_eq!(pixel(p, &[[0.0, r + 0.0002, 0.0, 0.0]]), p.with_alpha(0.0));
    }
    #[test]
    fn last_palette_entry_and_empty_palette() {
        let p = Pixel::F32([0.5, 1.0, 0.0, 0.0]);
        let mut colors = [[1.0, 0.0, 0.0, 0.0]; 200];
        colors[199] = [0.0, 1.0, 0.0, 0.0];
        assert_eq!(pixel(p, &colors), p);
        assert_eq!(pixel(p, &colors[..199]), p.with_alpha(0.0));
        assert_eq!(pixel(p, &[]), p.with_alpha(0.0));
    }
    #[test]
    fn unordered_falls_through() {
        let p = Pixel::F32([0.5, f32::NAN, 0.0, 0.0]);
        assert_eq!(pixel(p, &[[0.5, 1.0, 0.0, 0.0]]).alpha(), 0.5);
    }
}

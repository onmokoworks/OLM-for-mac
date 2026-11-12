//! AE parameter surface and adapter.
use crate::algorithm::{Key, Params};
use olm_ae::{Effect, Kind, Param, RenderContext, Value};
struct Plugin;
fn param(id: i32, name: &str, flags: i32, kind: Kind) -> Param {
    Param {
        id,
        name: name.into(),
        flags,
        kind,
    }
}
fn float(id: i32, name: &str) -> Param {
    param(
        id,
        name,
        32,
        Kind::Float {
            min: 0.0,
            max: 1.0,
            slider_min: 0.0,
            slider_max: 1.0,
            default: 0.0,
            precision: 4,
        },
    )
}
fn check(id: i32, name: &str) -> Param {
    param(id, name, 0, Kind::Checkbox(false))
}
fn popup(id: i32, name: &str, choices: &str, default: i16) -> Param {
    param(
        id,
        name,
        0,
        Kind::Popup {
            choices: choices.into(),
            default,
        },
    )
}
impl Effect for Plugin {
    const NAME: &'static str = "OLM Color Key";
    const VERSION: u32 = 1148928;
    const FLAGS: u32 = 0x02000440;
    const PRESERVE_ZERO_ALPHA_RGB: Option<bool> = Some(false);
    fn params() -> Vec<Param> {
        let mut p = vec![
            check(1, "Color Keep"),
            float(2, "Threshold"),
            param(3, "Threshold Parameters", 0, Kind::GroupStart),
            check(4, "Premultiplied Color"),
            popup(5, "Color Space", "RGB|HSV|Lab76|Lab94|YUV|YCrCb", 1),
            popup(0x20a, "Force Lower Precision", "Full|16bit|8bit", 1),
            check(6, "Per Color"),
            check(7, "Per Component"),
            float(8, "Threshold(R,H,L,Y,Y)"),
            float(9, "Threshold(G,S,a,U,Cr)"),
            float(10, "Threshold(B,V,b,V,Cb)"),
            param(11, "", 0, Kind::GroupEnd),
            param(12, "Edge Thin", 0, Kind::GroupStart),
            param(
                13,
                "Amount",
                0,
                Kind::Integer {
                    min: -4000,
                    max: 4000,
                    slider_min: -100,
                    slider_max: 100,
                    default: 0,
                },
            ),
            popup(14, "Distance Type", "Box|Approximate|Euclidean", 1),
            param(20, "", 0, Kind::GroupEnd),
            param(16, "Edge Blur", 0, Kind::GroupStart),
            param(
                17,
                "Amount",
                0,
                Kind::Float {
                    min: 0.0,
                    max: 4000.0,
                    slider_min: 0.0,
                    slider_max: 100.0,
                    default: 0.0,
                    precision: 1,
                },
            ),
            popup(18, "Distance Type", "Box|Approximate|Euclidean", 1),
            popup(19, "Direction", "Inside | Around | Outside", 2),
            param(16, "", 0, Kind::GroupEnd),
            param(
                21,
                "Number of Colors",
                64,
                Kind::Integer {
                    min: 0,
                    max: 25,
                    slider_min: 0,
                    slider_max: 30,
                    default: 1,
                },
            ),
            param(0x20b, "Enable Replace", 64, Kind::Checkbox(false)),
        ];
        for i in 0..25 {
            let n = i + 1;
            p.push(check(0x20c + i * 3, &format!("Use Color {n}")));
            p.push(check(0x20d + i * 3, &format!("Use Replace Color {n}")));
            p.push(param(0x16 + i * 5, &format!("Color {n}"), 32, Kind::Color));
            p.push(param(
                0x20e + i * 3,
                &format!("Replace Color {n}"),
                32,
                Kind::Color,
            ));
            for (j, name) in [
                "Threshold",
                "Threshold(R,H,L,Y,Y)",
                "Threshold(G,S,a,U,Cr)",
                "Threshold(B,V,b,V,Cb)",
            ]
            .iter()
            .enumerate()
            {
                p.push(float(0x17 + i * 5 + j as i32, &format!("{name} {n}")));
            }
        }
        p
    }
    fn render(
        v: &[Value],
        ctx: RenderContext,
        input: &olm_core::View<'_>,
        out: &mut olm_core::ViewMut<'_>,
    ) -> olm_core::Result<()> {
        let at = |slot: usize| v[slot - 1].number;
        let yes = |slot| at(slot) != 0.0;
        let mut p = Params {
            keep: yes(1),
            threshold: at(2) as f32,
            premultiplied: yes(4),
            space: at(5) as i32,
            precision: at(6) as i32,
            per_color: yes(7),
            per_component: yes(8),
            components: [at(9) as f32, at(10) as f32, at(11) as f32],
            thin: at(14) as i32,
            thin_distance: at(15) as i32,
            blur: at(18) as f32,
            blur_distance: at(19) as i32,
            direction: at(20) as i32,
            replace: yes(23),
            keys: vec![],
            step_x: ctx.downsample_x.denominator as f32,
            step_y: ctx.downsample_y.denominator as f32,
        };
        let n = at(22) as usize;
        if n > 25 {
            return Err(olm_core::Error::Unsupported);
        }
        for i in 0..n {
            let s = 24 + i * 8;
            let c = v[s + 1].color;
            let r = v[s + 2].color;
            p.keys.push(Key {
                enabled: yes(s),
                replace: yes(s + 1),
                color: [c[1], c[2], c[3]],
                replacement: [r[1], r[2], r[3]],
                threshold: at(s + 4) as f32,
                components: [at(s + 5) as f32, at(s + 6) as f32, at(s + 7) as f32],
            });
        }
        if ctx.smart {
            crate::algorithm::render_smart(input, out, &p)
        } else {
            crate::algorithm::render(input, out, &p)
        }
    }
}
olm_ae::export_effect!(Plugin, entry_point);

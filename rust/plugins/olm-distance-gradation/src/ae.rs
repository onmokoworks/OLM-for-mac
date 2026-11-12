use crate::algorithm::{render, Params};
use olm_ae::{sys::*, Effect, Kind, Param, RenderContext, Value};
#[path = "shared_candidates.rs"]
mod shared_candidates;
#[path = "ui.rs"]
mod ui;
pub struct Plugin;
fn param(id: i32, name: &str, flags: i32, kind: Kind) -> Param {
    Param {
        id,
        name: name.into(),
        flags,
        kind,
    }
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
    const NAME: &'static str = "Distance Gradation";
    const MATCH_NAME: &'static str = "OLM Distance Gradation";
    const VERSION: u32 = 266752;
    const FLAGS: u32 = 0x06000040;
    fn params() -> Vec<Param> {
        vec![
            param(1, "Invert", 0, Kind::Checkbox(false)),
            popup(2, "In/Out", "Inside|Outside|Both", 0),
            param(
                3,
                "Inside Threshold",
                0,
                Kind::Integer {
                    min: 0,
                    max: 1000,
                    slider_min: 0,
                    slider_max: 512,
                    default: 128,
                },
            ),
            param(
                4,
                "Outside Threshold",
                0,
                Kind::Integer {
                    min: 0,
                    max: 1000,
                    slider_min: 0,
                    slider_max: 512,
                    default: 128,
                },
            ),
            popup(5, "Render Mode", "RGB|Layer", 1),
            param(6, "Use Background Color", 0, Kind::Checkbox(false)),
            param(7, "Gradation Color", 0, Kind::Color),
            param(8, "BG Color ", 0, Kind::Color),
            popup(9, "Interpolation Mode", "Constant|Linear|Sphere|Power", 2),
            param(
                10,
                "Power",
                32,
                Kind::Float {
                    min: 0.01,
                    max: 5.,
                    slider_min: 0.01,
                    slider_max: 5.,
                    default: 1.,
                    precision: 2,
                },
            ),
            popup(11, "Blur Mode", "No Blur|Blur No Scale|Blur", 1),
            param(
                12,
                "Blur Size",
                32,
                Kind::Integer {
                    min: 0,
                    max: 4096,
                    slider_min: 0,
                    slider_max: 500,
                    default: 0,
                },
            ),
        ]
    }
    fn render(
        v: &[Value],
        ctx: RenderContext,
        input: &olm_core::View<'_>,
        out: &mut olm_core::ViewMut<'_>,
    ) -> olm_core::Result<()> {
        // Classic is not dispatched by AE for this SmartFX effect.
        if !ctx.smart {
            return Err(olm_core::Error::Unsupported);
        }
        let at = |i: usize| v[i - 1].number;
        render(
            input,
            out,
            &Params {
                invert: at(1) != 0.,
                in_out: at(2) as i32,
                inside: at(3) as i32,
                outside: at(4) as i32,
                render_mode: at(5) as i32,
                use_bg: at(6) != 0.,
                grad: v[6].color,
                bg: v[7].color,
                interpolation: at(9) as i32,
                power: at(10) as f32,
                blur_mode: at(11) as i32,
                blur_size: at(12) as u32,
                scale_x: (
                    ctx.downsample_x.numerator as u32,
                    ctx.downsample_x.denominator,
                ),
                scale_y: (
                    ctx.downsample_y.numerator as u32,
                    ctx.downsample_y.denominator,
                ),
            },
        )
    }
}
#[no_mangle]
pub unsafe extern "C" fn EffectMain(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut std::ffi::c_void,
) -> PF_Err {
    if cmd == PF_Cmd_UPDATE_PARAMS_UI {
        return std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let Some(input) = i.as_ref() else {
                return olm_ae::BAD;
            };
            ui::update(input).err().unwrap_or(0)
        }))
        .unwrap_or(olm_ae::BAD);
    }
    if cmd == PF_Cmd_PARAMS_SETUP {
        return std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let (Some(i), Some(o)) = (i.as_ref(), o.as_mut()) else {
                return olm_ae::BAD;
            };
            shared_candidates::setup::<Plugin>(i, o).err().unwrap_or(0)
        }))
        .unwrap_or(olm_ae::BAD);
    }
    olm_ae::entry::<Plugin>(cmd, i, o, p, w, e)
}
#[cfg(target_os = "windows")]
#[no_mangle]
pub unsafe extern "C" fn entryPointFunc(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut std::ffi::c_void,
) -> PF_Err {
    EffectMain(cmd, i, o, p, w, e)
}
#[cfg(target_os = "macos")]
#[no_mangle]
pub unsafe extern "C" fn PluginDataEntryFunction2(
    p: PF_PluginDataPtr,
    cb: PF_PluginDataCB2,
    _basic: *const SPBasicSuite,
    _host: *const std::ffi::c_char,
    _version: *const std::ffi::c_char,
) -> PF_Err {
    let Some(cb) = cb else {
        return olm_ae::BAD;
    };
    cb(
        p,
        c"Distance Gradation".as_ptr().cast(),
        c"OLM Distance Gradation".as_ptr().cast(),
        b"OLM Plug-ins\0".as_ptr(),
        b"EffectMain\0".as_ptr(),
        i32::from_be_bytes(*b"eFKT"),
        13,
        28,
        0,
        b"https://olm.co.jp/\0".as_ptr(),
    )
}

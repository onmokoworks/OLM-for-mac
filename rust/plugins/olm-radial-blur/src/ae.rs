use crate::{
    algorithm::{self, Params},
    glue::*,
};
use olm_core::{View, ViewMut};
pub struct Plugin;
fn param(id: i32, name: &str, flags: i32, ui_flags: i32, kind: Kind) -> Param {
    Param {
        id,
        name: name.into(),
        flags,
        ui_flags,
        kind,
    }
}
fn popup(id: i32, name: &str, choices: &str) -> Param {
    param(
        id,
        name,
        0x62,
        0,
        Kind::Popup {
            choices: choices.into(),
            default: 1,
        },
    )
}
fn integer(id: i32, name: &str, min: i32, max: i32, default: i32) -> Param {
    param(
        id,
        name,
        1,
        0x40,
        Kind::Integer {
            min,
            max,
            slider_min: min,
            slider_max: max,
            default,
        },
    )
}
fn float(
    id: i32,
    name: &str,
    min: f32,
    max: f32,
    slider_max: f32,
    default: f32,
    precision: i16,
) -> Param {
    param(
        id,
        name,
        0x40,
        0,
        Kind::Float {
            min,
            max,
            slider_min: min,
            slider_max,
            default,
            precision,
        },
    )
}
fn start(id: i32, name: &str) -> Param {
    param(id, name, 0x20, 0, Kind::GroupStart)
}
fn end(id: i32) -> Param {
    param(id, "", 0, 0, Kind::GroupEnd)
}
impl Effect for Plugin {
    const NAME: &'static str = "OLM RadialBlur";
    const VERSION: u32 = 622592;
    const FLAGS: u32 = 0x06008040;
    const FLAGS2: u32 = 0x08001408;
    fn params() -> Vec<Param> {
        vec![
            popup(1, "Blur Type", "Zoom | Rotation"),
            param(2, "Center", 0x60, 0, Kind::Point),
            start(3, "Outer Blur"),
            integer(4, "Strength", 0, 2000, 0),
            popup(28, "Offset Mode", "Add | Max | Override"),
            integer(29, "Offset", 0, 500, 0),
            integer(5, "Edge Fade", 0, 100, 0),
            end(6),
            start(7, "Inner Blur"),
            integer(8, "Strength", 0, 2000, 0),
            popup(30, "Offset Mode", "Add | Max | Override"),
            integer(31, "Offset", 0, 500, 0),
            integer(9, "Edge Fade", 0, 100, 0),
            end(10),
            param(26, "Repeat Border", 0x62, 0, Kind::Checkbox(true)),
            start(11, "Ellipse"),
            float(12, "Ratio", 1.0, 5.0, 5.0, 1.0, 2),
            param(13, "Angle", 0x60, 0, Kind::Angle),
            end(14),
            float(15, "Quality", 1.0, 50.0, 50.0, 5.0, 2),
            float(16, "Brightness Gain", 0.0, 10.0, 2.0, 1.0, 1),
            float(17, "Size Variation", 0.0, 100.0, 100.0, 0.0, 1),
            start(18, "Noise Parameters"),
            float(19, "Noise Variation", 0.0, 100.0, 100.0, 0.0, 1),
            popup(20, "Noise Type", "Smooth | Block | Layer"),
            param(21, "Noise Layer", 0x62, 0, Kind::Layer),
            integer(22, "Seed", 1, 1000, 1),
            param(23, "Offset", 0x60, 0, Kind::Angle),
            float(24, "Thickness", 1.0, 100.0, 100.0, 10.0, 2),
            end(25),
        ]
    }
    const COPY_VALUES: &'static [usize] = &[3, 5, 6, 9, 11, 12];
    fn render(
        v: &[Value],
        ctx: RenderContext,
        input: &View<'_>,
        output: &mut ViewMut<'_>,
    ) -> olm_core::Result<()> {
        let n = |slot: usize| v[slot - 1].number;
        let scale = crate::math::div(
            ctx.downsample_x.numerator as f32,
            ctx.downsample_x.denominator as f32,
        );
        let origin = input.layout().origin;
        let p = Params {
            rotation: n(1) == 2.0,
            center: [
                (v[1].point[0] / ctx.downsample_x.scale() - origin.0 as f64) * scale as f64,
                (v[1].point[1] / ctx.downsample_y.scale() - origin.1 as f64) * scale as f64,
            ],
            strength: [n(4) as i32, n(10) as i32],
            offset: [n(6) as i32, n(12) as i32],
            mode: [n(5) as i32, n(11) as i32],
            fade: [n(7) as i32, n(13) as i32],
            repeat: n(15) != 0.0,
            ratio: n(17),
            angle: n(18),
            quality: n(20),
            gain: n(21),
            size: n(22),
            noise: n(24),
            noise_type: n(25) as i32,
            seed: n(27) as u32,
            phase: ((n(28) * 65536.0) * 2.663161090079238e-7) as f32,
            thickness: n(29),
            downsample: scale,
        };
        algorithm::render(
            &p,
            input,
            output,
            render_threads(input.layout().width, input.layout().height),
        )
    }
}
#[no_mangle]
pub unsafe extern "C" fn EffectMain(
    cmd: sys::PF_Cmd,
    i: *mut sys::PF_InData,
    o: *mut sys::PF_OutData,
    p: sys::PF_ParamList,
    w: *mut sys::PF_LayerDef,
    e: *mut std::ffi::c_void,
) -> sys::PF_Err {
    crate::glue::entry::<Plugin>(cmd, i, o, p, w, e)
}
#[cfg(target_os = "windows")]
#[no_mangle]
pub unsafe extern "C" fn entry_point(
    cmd: sys::PF_Cmd,
    i: *mut sys::PF_InData,
    o: *mut sys::PF_OutData,
    p: sys::PF_ParamList,
    w: *mut sys::PF_LayerDef,
    e: *mut std::ffi::c_void,
) -> sys::PF_Err {
    EffectMain(cmd, i, o, p, w, e)
}
#[cfg(target_os = "macos")]
#[no_mangle]
pub unsafe extern "C" fn PluginDataEntryFunction2(
    p: sys::PF_PluginDataPtr,
    cb: sys::PF_PluginDataCB2,
    _: *const sys::SPBasicSuite,
    _: *const std::ffi::c_char,
    _: *const std::ffi::c_char,
) -> sys::PF_Err {
    let Some(cb) = cb else { return BAD };
    cb(
        p,
        b"OLM RadialBlur\0".as_ptr(),
        b"OLM RadialBlur\0".as_ptr(),
        b"OLM Plug-ins\0".as_ptr(),
        b"EffectMain\0".as_ptr(),
        i32::from_be_bytes(*b"eFKT"),
        13,
        28,
        0,
        b"https://olm.co.jp/\0".as_ptr(),
    )
}

// Small worlds do not amortize row-worker startup. No process-global pool/state.
fn render_threads(width: usize, height: usize) -> usize {
    if width.saturating_mul(height) < 65536 {
        1
    } else {
        std::thread::available_parallelism().map_or(1, usize::from)
    }
}

//! Parameter inventory and SmartFX adapter. No host types enter the algorithm.
#![allow(non_snake_case)]
use crate::{
    algorithm::{self, Params},
    frame,
    gamma::GammaMode,
    types::Pixel,
};
use olm_ae::{sys::*, Effect, Kind, Param, RenderContext, Value, BAD};
use std::{
    ffi::{c_void, CString},
    ptr,
};
struct Plugin;
fn param(id: i32, name: &str, flags: i32, kind: Kind) -> Param {
    Param {
        id,
        name: name.into(),
        flags,
        kind,
    }
}
fn slider(id: i32, name: &str, max: i32, default: i32, flags: i32) -> Param {
    param(
        id,
        name,
        flags,
        Kind::Integer {
            min: 0,
            max,
            slider_min: 0,
            slider_max: max,
            default,
        },
    )
}
impl Effect for Plugin {
    const NAME: &'static str = "OLM Smoother v2";
    const VERSION: u32 = 1114112;
    const FLAGS: u32 = 0x02000440;
    const PRESERVE_ZERO_ALPHA_RGB: Option<bool> = Some(true);
    fn params() -> Vec<Param> {
        let mut p = vec![
            param(1, "Enable Color Key", 0, Kind::Checkbox(false)),
            param(2, "Color Key", 0, Kind::Color),
            param(15, "Invert Color Key", 0, Kind::Checkbox(false)),
            slider(3, "Smoothness", 100, 100, 0),
            slider(4, "Extra Smooth", 100, 0, 0),
            param(
                5,
                "Smooth Range",
                0,
                Kind::Float {
                    min: 0.0,
                    max: 100.0,
                    slider_min: 0.0,
                    slider_max: 100.0,
                    default: 2.0,
                    precision: 1,
                },
            ),
            param(
                6,
                "Smoother Version",
                64,
                Kind::Popup {
                    choices: "v1 (sRGB)|v2 (Linear)|v2 (Oklab)".into(),
                    default: 2,
                },
            ),
            param(
                7,
                "Gamma Correction",
                64,
                Kind::Popup {
                    choices: "None|Gamma Colors|All Colors".into(),
                    default: 1,
                },
            ),
            param(
                8,
                "Gamma Value",
                0,
                Kind::Float {
                    min: 1.0,
                    max: 2.4,
                    slider_min: 1.0,
                    slider_max: 2.4,
                    default: 2.4,
                    precision: 2,
                },
            ),
            slider(9, "Number of Gamma Colors", 5, 1, 64),
        ];
        for i in 0..5 {
            p.push(param(10 + i, "Gamma Color", 0, Kind::Color));
        }
        p
    }
    fn render(
        v: &[Value],
        ctx: RenderContext,
        input: &olm_core::View<'_>,
        output: &mut olm_core::ViewMut<'_>,
    ) -> olm_core::Result<()> {
        use olm_core::{Depth, Error, Pixel as Stored};
        let a = input.layout();
        let b = output.layout();
        if !ctx.smart
            || a.width != b.width
            || a.height != b.height
            || a.origin != b.origin
            || a.depth != b.depth
            || a.width > 8192
            || a.height > 8192
            || a.stride.checked_mul(a.height).ok_or(Error::Overflow)? > i32::MAX as usize
            || b.stride.checked_mul(b.height).ok_or(Error::Overflow)? > i32::MAX as usize
        {
            return Err(Error::Unsupported);
        }
        let at = |slot: usize| v[slot - 1].number;
        for (slot, min, max) in [
            (1, 0.0, 1.0),
            (3, 0.0, 1.0),
            (4, 0.0, 100.0),
            (5, 0.0, 100.0),
            (6, 0.0, 100.0),
            (7, 1.0, 3.0),
            (8, 1.0, 3.0),
            (9, 1.0, 2.4f32 as f64),
            (10, 0.0, 5.0),
        ] {
            if !at(slot).is_finite() || at(slot) < min || at(slot) > max {
                return Err(Error::Unsupported);
            }
        }
        let color = |slot: usize| {
            let [a, r, g, b] = v[slot - 1].color;
            Pixel { r, g, b, a }
        };
        let p = Params {
            version: at(7) as i32,
            smoothness: at(4) as i32,
            extra: at(5) as i32,
            range: at(6) as i32,
            gamma_mode: match at(8) as i32 {
                1 => GammaMode::None,
                2 => GammaMode::Colors,
                _ => GammaMode::All,
            },
            gamma: at(9) as f32,
            gamma_colors: (0..at(10) as usize).map(|i| color(11 + i)).collect(),
            key: if at(1) != 0.0 {
                Some((color(2), at(3) != 0.0))
            } else {
                None
            },
            keep_premultiplied: false,
        };
        let n = olm_core::image_len(a.width, a.height)?;
        let mut budget = olm_core::Budget::new(n.checked_mul(52).ok_or(Error::Overflow)?);
        let mut pixels = olm_core::allocate(n, Pixel::default(), &mut budget)?;
        for y in 0..a.height {
            for x in 0..a.width {
                pixels[y * a.width + x] = match input.get(x, y)? {
                    Stored::U8(v) => frame::load8(v),
                    Stored::U16(v) => frame::load16(v),
                    Stored::F32([a, r, g, b]) => Pixel { r, g, b, a },
                };
            }
        }
        let result = algorithm::render_with_range(
            &pixels,
            a.width,
            a.height,
            &p,
            at(6) as f32,
            std::thread::available_parallelism().map_or(1, usize::from),
            &mut budget,
        )?;
        for y in 0..a.height {
            for x in 0..a.width {
                let p = result[y * a.width + x];
                let argb = [p.a, p.r, p.g, p.b];
                output.set(
                    x,
                    y,
                    match a.depth {
                        Depth::U8 => Stored::U8(argb.map(frame::pack8)),
                        Depth::U16 => Stored::U16(argb.map(frame::pack16)),
                        Depth::F32 => Stored::F32(argb),
                    },
                )?;
            }
        }
        Ok(())
    }
}

// Local parameter setup is needed because the shared Kind::Color defaults to black.
include!("ae_setup.rs");
#[path = "ae_boundary.rs"]
mod boundary;
#[path = "dynamic.rs"]
mod dynamic;

#[no_mangle]
pub unsafe extern "C" fn EffectMain(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut c_void,
) -> PF_Err {
    if cmd == PF_Cmd_RENDER {
        return BAD;
    }
    if cmd == PF_Cmd_PARAMS_SETUP {
        return std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let i = i.as_ref().ok_or(BAD)?;
            let o = o.as_mut().ok_or(BAD)?;
            setup::<Plugin>(i, o)
        }))
        .unwrap_or(Err(BAD))
        .err()
        .unwrap_or(0);
    }
    if cmd == PF_Cmd_UPDATE_PARAMS_UI {
        return std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| dynamic::update(i, p)))
            .unwrap_or(Err(BAD))
            .err()
            .unwrap_or(0);
    }
    boundary::entry::<Plugin>(cmd, i, o, p, w, e)
}
#[no_mangle]
pub unsafe extern "C" fn entry_point(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut c_void,
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
        return BAD;
    };
    cb(
        p,
        c"OLM Smoother v2".as_ptr().cast(),
        c"OLM Smoother v2".as_ptr().cast(),
        b"OLM Plug-ins\0".as_ptr(),
        b"EffectMain\0".as_ptr(),
        i32::from_be_bytes(*b"eFKT"),
        13,
        28,
        0,
        b"https://olm.co.jp/\0".as_ptr(),
    )
}

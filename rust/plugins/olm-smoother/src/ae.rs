use crate::algorithm::{self, Params};
use olm_ae::{sys::*, Effect, Kind, Param, RenderContext, Value};
use std::ffi::c_void;
struct Plugin;
impl Effect for Plugin {
    const NAME: &'static str = "OLM Smoother";
    const VERSION: u32 = 591872;
    const FLAGS: u32 = 0x02000040;
    const FLAGS2: u32 = 0x08000000;
    fn params() -> Vec<Param> {
        vec![
            Param {
                id: 1,
                name: "Use Color Key".into(),
                flags: 0,
                kind: Kind::Checkbox(false),
            },
            Param {
                id: 2,
                name: "Color Key".into(),
                flags: 0,
                kind: Kind::Color,
            },
            // Native original inventory: UI maximum 255 (the C++ declaration says 6).
            Param {
                id: 3,
                name: "Do Smooth Range".into(),
                flags: 0,
                kind: Kind::Integer {
                    min: 0,
                    max: 255,
                    slider_min: 0,
                    slider_max: 255,
                    default: 6,
                },
            },
        ]
    }
    fn render(
        v: &[Value],
        ctx: RenderContext,
        i: &olm_core::View<'_>,
        o: &mut olm_core::ViewMut<'_>,
    ) -> olm_core::Result<()> {
        if ctx.smart || v.len() != 3 || !(v[0].number == 0.0 || v[0].number == 1.0) {
            return Err(olm_core::Error::Unsupported);
        }
        algorithm::render(
            i,
            o,
            Params {
                use_key: v[0].number != 0.0,
                key: v[1].color8,
                tolerance: v[2].number as i32,
            },
            ctx.output_extent,
        )
    }
}
// Local setup is necessary because the shared Color kind has a black default.
// Keep the original white default without changing the shared parameter API.
unsafe fn setup(i: *mut PF_InData, o: *mut PF_OutData) -> PF_Err {
    let (Some(i), Some(o)) = (i.as_ref(), o.as_mut()) else {
        return olm_ae::BAD;
    };
    let Some(add) = i.inter.add_param else {
        return olm_ae::BAD;
    };
    for spec in Plugin::params() {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.uu.id = spec.id;
        for (a, b) in p.name.iter_mut().zip(spec.name.bytes()) {
            *a = b as _;
        }
        match spec.kind {
            Kind::Checkbox(_) => {
                p.param_type = PF_Param_CHECKBOX;
                p.u.bd.u.nameptr = c"".as_ptr();
            }
            Kind::Color => {
                p.param_type = PF_Param_COLOR;
                p.u.cd.value = PF_Pixel {
                    alpha: 255,
                    red: 255,
                    green: 255,
                    blue: 255,
                };
                p.u.cd.dephault = p.u.cd.value;
            }
            Kind::Integer {
                min,
                max,
                slider_min,
                slider_max,
                default,
            } => {
                p.param_type = PF_Param_SLIDER;
                p.u.sd = PF_SliderDef {
                    value: default,
                    dephault: default,
                    valid_min: min,
                    valid_max: max,
                    slider_min,
                    slider_max,
                    ..std::mem::zeroed()
                };
            }
            _ => return olm_ae::BAD,
        }
        let err = add(i.effect_ref, -1, &mut p);
        if err != 0 {
            return err;
        }
    }
    o.num_params = 4;
    0
}
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
        return crate::byte_boundary::render(i, o, p, w);
    }
    if cmd == PF_Cmd_PARAMS_SETUP {
        return std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| setup(i, o)))
            .unwrap_or(olm_ae::BAD);
    }
    if cmd == PF_Cmd_SMART_PRE_RENDER || cmd == PF_Cmd_SMART_RENDER {
        return olm_ae::BAD;
    }
    olm_ae::entry::<Plugin>(cmd, i, o, p, w, e)
}
#[no_mangle]
pub unsafe extern "C" fn entryPointFunc(
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
    let Some(cb) = cb else { return olm_ae::BAD };
    cb(
        p,
        b"OLM Smoother\0".as_ptr(),
        b"OLM Smoother\0".as_ptr(),
        b"OLM Plug-ins\0".as_ptr(),
        b"EffectMain\0".as_ptr(),
        i32::from_be_bytes(*b"eFKT"),
        13,
        28,
        0,
        b"https://olm.co.jp/\0".as_ptr(),
    )
}

use crate::adapter::{self, Effect, Param, RenderContext, Value};
use crate::algorithm::Params;
use olm_ae::sys::*;
pub struct Plugin;
impl Effect for Plugin {
    const NAME: &'static str = "OLM Kira Kira";
    const MATCH_NAME: &'static str = "OLM OLM Kira Kira";
    const VERSION: u32 = 1638400;
    const FLAGS: u32 = 0x02008040;
    fn params() -> Vec<Param> {
        crate::params::declarations()
    }
    fn render(
        v: &[Value],
        ctx: RenderContext,
        input: &olm_core::View<'_>,
        out: &mut olm_core::ViewMut<'_>,
    ) -> olm_core::Result<()> {
        let number = |slot: usize| v[slot - 1].number;
        let scale = ctx.downsample_x.numerator as f32 / ctx.downsample_x.denominator as f32;
        let mut p = Params {
            channel: number(1) as i32,
            blur: number(2) as i32,
            merge: number(3) as i32,
            approximate: number(4) != 0.0 && scale > 0.5,
            gain: number(5),
            strength: ((number(6) as i32 as f32) * 0.01f32) as f64,
            fade: ((number(7) as f32) * 0.2f32) as f64,
            glow_opacity: ((number(8) as i32 as f32) * 0.01f32) as f64,
            source_opacity: ((number(9) as i32 as f32) * 0.01f32) as f64,
            rotation: number(40),
            ..Params::default()
        };
        for j in 0..5 {
            let s = 10 + j * 6;
            p.lengths[j] = number(s) as i32;
            let c = v[s].color;
            p.colors[j] = [c[1], c[2], c[3]];
            p.use_ramp[j] = number(s + 3) != 0.0;
            p.ramps[j] = v[s + 3].ramp;
        }
        crate::algorithm::render(input, out, &p, scale)
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
    adapter::entry::<Plugin>(cmd, i, o, p, w, e)
}
#[cfg(target_os = "macos")]
#[no_mangle]
pub unsafe extern "C" fn PluginDataEntryFunction2(
    p: PF_PluginDataPtr,
    cb: PF_PluginDataCB2,
    _: *const SPBasicSuite,
    _: *const std::ffi::c_char,
    _: *const std::ffi::c_char,
) -> PF_Err {
    let Some(cb) = cb else {
        return adapter::BAD;
    };
    cb(
        p,
        c"OLM Kira Kira".as_ptr().cast(),
        c"OLM OLM Kira Kira".as_ptr().cast(),
        b"OLM Plug-ins\0".as_ptr(),
        b"EffectMain\0".as_ptr(),
        i32::from_be_bytes(*b"eFKT"),
        13,
        28,
        0,
        b"https://olm.co.jp/\0".as_ptr(),
    )
}

#[cfg(target_os = "windows")]
#[no_mangle]
pub unsafe extern "C" fn entry_point(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut std::ffi::c_void,
) -> PF_Err {
    EffectMain(cmd, i, o, p, w, e)
}

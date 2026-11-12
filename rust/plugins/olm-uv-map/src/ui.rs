//! 180004080: Smoothness is enabled exactly when interpolation is Trilinear.
use after_effects_sys::*;
pub unsafe fn handle(
    cmd: PF_Cmd,
    i: &PF_InData,
    _params: PF_ParamList,
    _extra: *mut std::ffi::c_void,
) -> crate::ae::Result<()> {
    use crate::ae::{check, BAD};
    if cmd != PF_Cmd_UPDATE_PARAMS_UI && cmd != PF_Cmd_USER_CHANGED_PARAM {
        return Ok(());
    }
    let checkout = i.inter.checkout_param.ok_or(BAD)?;
    let checkin = i.inter.checkin_param.ok_or(BAD)?;
    let mut method = std::mem::zeroed();
    check(checkout(
        i.effect_ref,
        2,
        i.current_time,
        i.time_step,
        i.time_scale,
        &mut method,
    ))?;
    let enabled = method.u.pd.value == 3;
    check(checkin(i.effect_ref, &mut method))?;
    let mut smooth = std::mem::zeroed();
    check(checkout(
        i.effect_ref,
        3,
        i.current_time,
        i.time_step,
        i.time_scale,
        &mut smooth,
    ))?;
    let result = (|| {
        smooth.ui_flags = if enabled { 0 } else { PF_PUI_DISABLED as _ };
        let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
        let release = basic.ReleaseSuite.ok_or(BAD)?;
        let mut raw = std::ptr::null();
        check(basic.AcquireSuite.ok_or(BAD)?(
            kPFParamUtilsSuite.as_ptr().cast(),
            3,
            &mut raw,
        ))?;
        let result = (|| {
            let suite = (raw as *const PF_ParamUtilsSuite3).as_ref().ok_or(BAD)?;
            check(suite.PF_UpdateParamUI.ok_or(BAD)?(i.effect_ref, 3, &smooth))
        })();
        let clean = check(release(kPFParamUtilsSuite.as_ptr().cast(), 3));
        result?;
        clean
    })();
    let clean = check(checkin(i.effect_ref, &mut smooth));
    result?;
    clean
}

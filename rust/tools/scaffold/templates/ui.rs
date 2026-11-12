//! TODO: implement original dynamic UI, drawing, hit testing and user-change logic.
//! PARAMS_SETUP preserves declarations, not subsequent state transitions.
use after_effects_sys::*;
pub unsafe fn handle(
    _cmd: PF_Cmd,
    _i: &PF_InData,
    _params: PF_ParamList,
    _extra: *mut std::ffi::c_void,
) -> crate::ae::Result<()> {
    Ok(())
}

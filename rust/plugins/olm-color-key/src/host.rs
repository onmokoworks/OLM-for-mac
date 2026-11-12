//! Crate-local declaration labels and UI dispatch; shared render glue is unchanged.
#![allow(non_upper_case_globals, non_snake_case)]
use super::Plugin;
use olm_ae::{sys::*, Result, BAD};
use std::{cell::Cell, ffi::c_void};

#[path = "ui.rs"]
mod ui;

type Add = unsafe extern "C" fn(PF_ProgPtr, i32, *mut PF_ParamDef) -> PF_Err;
thread_local! { static ADD: Cell<Option<Add>> = const { Cell::new(None) }; }
struct RestoreAdd(Option<Add>);
impl Drop for RestoreAdd {
    fn drop(&mut self) {
        ADD.set(self.0);
    }
}
unsafe extern "C" fn add(refcon: PF_ProgPtr, index: i32, p: *mut PF_ParamDef) -> PF_Err {
    let Some(p) = p.as_mut() else { return BAD };
    if p.param_type == PF_Param_CHECKBOX {
        let name = std::ffi::CStr::from_ptr(p.name.as_ptr()).to_bytes();
        p.u.bd.u.nameptr = if name.starts_with(b"Use Replace Color ") {
            c"Use Replace Color".as_ptr()
        } else if name.starts_with(b"Use Color ") {
            c"Use Color".as_ptr()
        } else {
            p.name.as_ptr()
        };
    }
    match ADD.get() {
        Some(f) => f(refcon, index, p),
        None => BAD,
    }
}

unsafe fn dispatch(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut c_void,
) -> PF_Err {
    if cmd == PF_Cmd_GLOBAL_SETUP {
        let error = olm_ae::entry::<Plugin>(cmd, i, o, p, w, e);
        if error != 0 {
            return error;
        }
        return ui::register(i).err().unwrap_or(0);
    }
    if cmd == PF_Cmd_PARAMS_SETUP {
        let Some(input) = i.as_ref() else { return BAD };
        let Some(callback) = input.inter.add_param else {
            return BAD;
        };
        let mut input = *input;
        let _restore = RestoreAdd(ADD.replace(Some(callback)));
        input.inter.add_param = Some(add);
        return olm_ae::entry::<Plugin>(cmd, &mut input, o, p, w, e);
    }
    if cmd == PF_Cmd_UPDATE_PARAMS_UI {
        return std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| ui::update(i, p)))
            .unwrap_or(Err(BAD))
            .err()
            .unwrap_or(0);
    }
    olm_ae::entry::<Plugin>(cmd, i, o, p, w, e)
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
    dispatch(cmd, i, o, p, w, e)
}
#[cfg(target_os = "windows")]
#[no_mangle]
pub unsafe extern "C" fn entry_point(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut c_void,
) -> PF_Err {
    dispatch(cmd, i, o, p, w, e)
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
    let Some(cb) = cb else { return BAD };
    cb(
        p,
        c"OLM Color Key".as_ptr().cast(),
        c"OLM Color Key".as_ptr().cast(),
        b"OLM Plug-ins\0".as_ptr(),
        b"EffectMain\0".as_ptr(),
        i32::from_be_bytes(*b"eFKT"),
        13,
        28,
        0,
        b"https://olm.co.jp/\0".as_ptr(),
    )
}

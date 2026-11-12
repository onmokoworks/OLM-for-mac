//! C++ UpdateParamsUI port. Host resources remain balanced on callback errors.
use olm_ae::{sys::*, BAD};
type Result<T> = std::result::Result<T, PF_Err>;
fn check(e: PF_Err) -> Result<()> {
    if e == 0 {
        Ok(())
    } else {
        Err(e)
    }
}
struct Checked<'a> {
    input: &'a PF_InData,
    value: PF_ParamDef,
}
impl Drop for Checked<'_> {
    fn drop(&mut self) {
        unsafe {
            if let Some(f) = self.input.inter.checkin_param {
                f(self.input.effect_ref, &mut self.value);
            }
        }
    }
}
unsafe fn checkout(input: &PF_InData, slot: i32) -> Result<Checked<'_>> {
    input.inter.checkin_param.ok_or(BAD)?;
    let mut p = std::mem::zeroed();
    check(input.inter.checkout_param.ok_or(BAD)?(
        input.effect_ref,
        slot,
        input.current_time,
        input.time_step,
        input.time_scale,
        &mut p,
    ))?;
    Ok(Checked { input, value: p })
}
struct Suite<'a> {
    basic: &'a SPBasicSuite,
    ptr: *const PF_ParamUtilsSuite3,
}
impl Drop for Suite<'_> {
    fn drop(&mut self) {
        unsafe {
            if let Some(f) = self.basic.ReleaseSuite {
                f(kPFParamUtilsSuite.as_ptr().cast(), 3);
            }
        }
    }
}
unsafe fn enabled(input: &PF_InData, slot: i32, disabled: bool) -> Result<()> {
    let mut p = checkout(input, slot)?;
    p.value.ui_flags = if disabled { PF_PUI_DISABLED as _ } else { 0 };
    let basic = input.pica_basicP.as_ref().ok_or(BAD)?;
    basic.ReleaseSuite.ok_or(BAD)?;
    let mut raw = std::ptr::null();
    check(
        basic.AcquireSuite.ok_or(BAD)?(kPFParamUtilsSuite.as_ptr().cast(), 3, &mut raw) as PF_Err,
    )?;
    let suite = Suite {
        basic,
        ptr: raw.cast(),
    };
    let update = suite.ptr.as_ref().ok_or(BAD)?.PF_UpdateParamUI.ok_or(BAD)?;
    check(update(input.effect_ref, slot, &p.value))
}
unsafe fn popup(input: &PF_InData, slot: i32) -> Result<i32> {
    Ok(checkout(input, slot)?.value.u.pd.value as i32)
}
pub unsafe fn update(input: &PF_InData) -> Result<()> {
    let interpolation = popup(input, 9)?;
    enabled(input, 10, interpolation != 4)?;
    let in_out = popup(input, 2)?;
    enabled(input, 4, in_out == 1)?;
    enabled(input, 3, in_out == 2)?;
    let render = popup(input, 5)?;
    let background = checkout(input, 6)?.value.u.bd.value != 0;
    enabled(input, 7, render != 1)?;
    enabled(input, 8, !background)?;
    let blur = popup(input, 11)?;
    enabled(input, 12, blur == 1)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::RefCell;
    #[derive(Default)]
    struct State {
        values: [i32; 13],
        updates: Vec<(i32, i32)>,
        checked: i32,
        returned: i32,
        acquired: i32,
        released: i32,
        fail_slot: i32,
    }
    thread_local! {static STATE:RefCell<State>=RefCell::new(State::default());}
    unsafe extern "C" fn get(
        _: PF_ProgPtr,
        slot: PF_ParamIndex,
        _: A_long,
        _: A_long,
        _: A_u_long,
        p: *mut PF_ParamDef,
    ) -> PF_Err {
        STATE.with(|s| {
            let mut s = s.borrow_mut();
            s.checked += 1;
            (*p).ui_flags = 0x7fff;
            if slot == 6 {
                (*p).u.bd.value = s.values[slot as usize] as _;
            } else {
                (*p).u.pd.value = s.values[slot as usize] as _;
            }
        });
        0
    }
    unsafe extern "C" fn put(_: PF_ProgPtr, _: *mut PF_ParamDef) -> PF_Err {
        STATE.with(|s| s.borrow_mut().returned += 1);
        0
    }
    unsafe extern "C" fn set(_: PF_ProgPtr, slot: PF_ParamIndex, p: *const PF_ParamDef) -> PF_Err {
        STATE.with(|s| {
            let mut s = s.borrow_mut();
            s.updates.push((slot, (*p).ui_flags));
            if s.fail_slot == slot {
                77
            } else {
                0
            }
        })
    }
    static SUITE: PF_ParamUtilsSuite3 = {
        let mut s: PF_ParamUtilsSuite3 = unsafe { std::mem::zeroed() };
        s.PF_UpdateParamUI = Some(set);
        s
    };
    unsafe extern "C" fn acquire(
        _: *const std::ffi::c_char,
        version: i32,
        raw: *mut *const std::ffi::c_void,
    ) -> SPErr {
        assert_eq!(version, 3);
        *raw = (&SUITE as *const PF_ParamUtilsSuite3).cast();
        STATE.with(|s| s.borrow_mut().acquired += 1);
        0
    }
    unsafe extern "C" fn release(_: *const std::ffi::c_char, version: i32) -> SPErr {
        assert_eq!(version, 3);
        STATE.with(|s| s.borrow_mut().released += 1);
        0
    }
    #[test]
    fn ui_callbacks_and_error_cleanup() {
        unsafe {
            let mut basic: SPBasicSuite = std::mem::zeroed();
            basic.AcquireSuite = Some(acquire);
            basic.ReleaseSuite = Some(release);
            let mut input: PF_InData = std::mem::zeroed();
            input.pica_basicP = &mut basic;
            input.inter.checkout_param = Some(get);
            input.inter.checkin_param = Some(put);
            for (values, expected) in [
                (
                    [0, 0, 1, 0, 0, 1, 0, 0, 0, 2, 0, 1, 0],
                    vec![(10, 32), (4, 32), (3, 0), (7, 0), (8, 32), (12, 32)],
                ),
                (
                    [0, 0, 2, 0, 0, 2, 1, 0, 0, 4, 0, 5, 0],
                    vec![(10, 0), (4, 0), (3, 32), (7, 32), (8, 0), (12, 0)],
                ),
            ] {
                STATE.with(|s| {
                    *s.borrow_mut() = State {
                        values,
                        ..State::default()
                    }
                });
                assert_eq!(update(&input), Ok(()));
                STATE.with(|s| {
                    let s = s.borrow();
                    assert_eq!(s.updates, expected);
                    assert_eq!(
                        (s.checked, s.returned, s.acquired, s.released),
                        (11, 11, 6, 6)
                    );
                });
            }
            STATE.with(|s| {
                *s.borrow_mut() = State {
                    fail_slot: 4,
                    ..State::default()
                }
            });
            assert_eq!(update(&input), Err(77));
            STATE.with(|s| {
                let s = s.borrow();
                assert_eq!(
                    (s.checked, s.returned, s.acquired, s.released),
                    (4, 4, 2, 2)
                );
            });
        }
    }
}

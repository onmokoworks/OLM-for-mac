//! UI-only stream visibility and disabled controls, from mac/DynamicControls.h.
use crate::glue::{sys::*, Result, BAD};
use std::{ffi::c_void, ptr};
struct Suite<'a, T> {
    basic: &'a SPBasicSuite,
    name: *const i8,
    version: i32,
    raw: *const T,
}
impl<'a, T> Suite<'a, T> {
    unsafe fn new(i: &'a PF_InData, name: &[u8], version: i32) -> Result<Self> {
        let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
        let mut raw: *const c_void = ptr::null();
        basic.ReleaseSuite.ok_or(BAD)?;
        let err = basic.AcquireSuite.ok_or(BAD)?(name.as_ptr().cast(), version, &mut raw);
        if err != 0 {
            return Err(err as _);
        }
        let guard = Self {
            basic,
            name: name.as_ptr().cast(),
            version,
            raw: raw.cast(),
        };
        if guard.raw.is_null() {
            return Err(BAD);
        }
        Ok(guard)
    }
}
impl<T> Drop for Suite<'_, T> {
    fn drop(&mut self) {
        unsafe {
            if let Some(f) = self.basic.ReleaseSuite {
                f(self.name, self.version);
            }
        }
    }
}
fn check(err: i32) -> Result<()> {
    if err == 0 {
        Ok(())
    } else {
        Err(err)
    }
}
unsafe fn hidden(i: &PF_InData, slot: i32, hidden: bool) -> Result<()> {
    let pf = Suite::<AEGP_PFInterfaceSuite1>::new(
        i,
        kAEGPPFInterfaceSuite,
        kAEGPPFInterfaceSuiteVersion1 as _,
    )?;
    let stream =
        Suite::<AEGP_StreamSuite2>::new(i, kAEGPStreamSuite, kAEGPStreamSuiteVersion2 as _)?;
    let dynamic = Suite::<AEGP_DynamicStreamSuite3>::new(
        i,
        kAEGPDynamicStreamSuite,
        kAEGPDynamicStreamSuiteVersion3 as _,
    )?;
    let effect =
        Suite::<AEGP_EffectSuite3>::new(i, kAEGPEffectSuite, kAEGPEffectSuiteVersion3 as _)?;
    let dispose_stream = (*stream.raw).AEGP_DisposeStream.ok_or(BAD)?;
    let dispose_effect = (*effect.raw).AEGP_DisposeEffect.ok_or(BAD)?;
    let mut e = ptr::null_mut();
    let mut s = ptr::null_mut();
    let result = (|| {
        check((*pf.raw).AEGP_GetNewEffectForEffect.ok_or(BAD)?(
            0,
            i.effect_ref,
            &mut e,
        ))?;
        check((*stream.raw).AEGP_GetNewEffectStreamByIndex.ok_or(BAD)?(
            0, e, slot, &mut s,
        ))?;
        check((*dynamic.raw).AEGP_SetDynamicStreamFlag.ok_or(BAD)?(
            s,
            AEGP_DynStreamFlag_HIDDEN as _,
            0,
            hidden as _,
        ))
    })();
    let a = if !s.is_null() {
        check(dispose_stream(s))
    } else {
        Ok(())
    };
    let b = if !e.is_null() {
        check(dispose_effect(e))
    } else {
        Ok(())
    };
    result.and(a).and(b)
}
pub unsafe fn update(i: &PF_InData, params: PF_ParamList) -> Result<()> {
    if params.is_null() {
        return Ok(());
    }
    let get = |n: usize| (*params.add(n)).as_ref().ok_or(BAD);
    let layer = get(25)?.u.pd.value == 3;
    for (slot, hide) in [(26, !layer), (27, layer), (28, layer), (29, layer)] {
        hidden(i, slot, hide)?;
    }
    let rotation = get(1)?.u.pd.value == 2;
    let outer = rotation && get(5)?.u.pd.value == 3;
    let inner = rotation && get(11)?.u.pd.value == 3;
    let suite =
        Suite::<PF_ParamUtilsSuite3>::new(i, kPFParamUtilsSuite, kPFParamUtilsSuiteVersion3 as _)?;
    let update = (*suite.raw).PF_UpdateParamUI.ok_or(BAD)?;
    for (slot, disabled) in [
        (4, outer),
        (6, !rotation),
        (5, !rotation),
        (10, inner),
        (12, !rotation),
        (11, !rotation),
    ] {
        let mut p = *get(slot)?;
        if disabled {
            p.ui_flags |= PF_PUI_DISABLED as i32;
        } else {
            p.ui_flags &= !(PF_PUI_DISABLED as i32);
        }
        check(update(i.effect_ref, slot as i32, &mut p))?;
    }
    Ok(())
}

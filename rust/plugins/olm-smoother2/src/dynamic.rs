//! UI-only translation of DynamicControls.h, retaining suite/ref ownership.
use super::*;
type Result<T> = olm_ae::Result<T>;
fn check(e: PF_Err) -> Result<()> {
    if e == 0 {
        Ok(())
    } else {
        Err(e)
    }
}
unsafe fn suite<T, F, R>(i: &PF_InData, name: &[u8], version: i32, f: F) -> Result<R>
where
    F: FnOnce(&T) -> Result<R>,
{
    let b = i.pica_basicP.as_ref().ok_or(BAD)?;
    let acquire = b.AcquireSuite.ok_or(BAD)?;
    let release = b.ReleaseSuite.ok_or(BAD)?;
    let mut raw = ptr::null();
    check(acquire(name.as_ptr().cast(), version, &mut raw) as PF_Err)?;
    let result = match (raw as *const T).as_ref() {
        Some(s) => f(s),
        None => Err(BAD),
    };
    let freed = check(release(name.as_ptr().cast(), version) as PF_Err);
    let value = result?;
    freed?;
    Ok(value)
}
unsafe fn hidden(i: &PF_InData, index: i32, hide: bool) -> Result<()> {
    let mut effect = ptr::null_mut();
    let mut stream = ptr::null_mut();
    let result = (|| {
        suite::<AEGP_PFInterfaceSuite1, _, _>(i, kAEGPPFInterfaceSuite, 1, |s| {
            check(s.AEGP_GetNewEffectForEffect.ok_or(BAD)?(
                0,
                i.effect_ref,
                &mut effect,
            ))
        })?;
        suite::<AEGP_StreamSuite2, _, _>(i, kAEGPStreamSuite, 2, |s| {
            check(s.AEGP_GetNewEffectStreamByIndex.ok_or(BAD)?(
                0,
                effect,
                index,
                &mut stream,
            ))
        })?;
        suite::<AEGP_DynamicStreamSuite3, _, _>(i, kAEGPDynamicStreamSuite, 3, |s| {
            check(s.AEGP_SetDynamicStreamFlag.ok_or(BAD)?(
                stream,
                AEGP_DynStreamFlag_HIDDEN as _,
                0,
                hide as _,
            ))
        })
    })();
    let dispose_stream = if stream.is_null() {
        Ok(())
    } else {
        suite::<AEGP_StreamSuite2, _, _>(i, kAEGPStreamSuite, 2, |s| {
            check(s.AEGP_DisposeStream.ok_or(BAD)?(stream))
        })
    };
    let dispose_effect = if effect.is_null() {
        Ok(())
    } else {
        suite::<AEGP_EffectSuite3, _, _>(i, kAEGPEffectSuite, 3, |s| {
            check(s.AEGP_DisposeEffect.ok_or(BAD)?(effect))
        })
    };
    result?;
    dispose_stream?;
    dispose_effect
}
pub(super) unsafe fn update(i: *mut PF_InData, params: PF_ParamList) -> Result<()> {
    let i = i.as_ref().ok_or(BAD)?;
    if params.is_null() {
        return Err(BAD);
    }
    let at = |n: usize| (*params.add(n)).as_ref().ok_or(BAD);
    let key = at(1)?.u.bd.value != 0;
    let mode = at(8)?.u.pd.value;
    let count = at(10)?.u.sd.value;
    let oklab = at(7)?.u.pd.value == 3;
    for (slot, disabled) in [
        (2, !key),
        (3, !key),
        (8, oklab),
        (9, oklab || mode == 1),
        (10, oklab || mode != 2),
    ] {
        let mut p = *at(slot)?;
        if disabled {
            p.ui_flags |= PF_PUI_DISABLED;
        } else {
            p.ui_flags &= !(PF_PUI_DISABLED);
        }
        suite::<PF_ParamUtilsSuite3, _, _>(i, kPFParamUtilsSuite, 3, |s| {
            check(s.PF_UpdateParamUI.ok_or(BAD)?(
                i.effect_ref,
                slot as i32,
                &p,
            ))
        })?;
    }
    for n in 0..5 {
        hidden(i, 11 + n, !(!oklab && mode == 2 && n < count))?;
    }
    Ok(())
}

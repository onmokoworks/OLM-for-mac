//! Visibility/enabled rules from upstream 2025 RVA 0x1d90.
//! Acquire suites/effect once per update; never scan the disk-ID map per control.
use super::*;
use crate::algorithm::MAX_COLORS;
use std::{
    ptr,
    sync::atomic::{AtomicI32, Ordering},
};

static PLUGIN_ID: AtomicI32 = AtomicI32::new(0);
#[cfg(test)]
#[path = "ui_tests.rs"]
mod tests;
fn check(e: PF_Err) -> Result<()> {
    if e == 0 {
        Ok(())
    } else {
        Err(e)
    }
}
struct Suite<'a, T> {
    basic: &'a SPBasicSuite,
    name: &'static [u8],
    version: i32,
    raw: *const T,
}
impl<'a, T> Suite<'a, T> {
    unsafe fn get(i: &'a PF_InData, name: &'static [u8], version: i32) -> Result<Self> {
        let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
        basic.ReleaseSuite.ok_or(BAD)?;
        let mut raw = ptr::null();
        check(basic.AcquireSuite.ok_or(BAD)?(
            name.as_ptr().cast(),
            version,
            &mut raw,
        ))?;
        let suite = Self {
            basic,
            name,
            version,
            raw: raw.cast(),
        };
        if raw.is_null() {
            return Err(BAD);
        }
        Ok(suite)
    }
    unsafe fn value(&self) -> &T {
        &*self.raw
    }
}
impl<T> Drop for Suite<'_, T> {
    fn drop(&mut self) {
        unsafe {
            if let Some(release) = self.basic.ReleaseSuite {
                release(self.name.as_ptr().cast(), self.version);
            }
        }
    }
}
pub(super) unsafe fn register(i: *mut PF_InData) -> Result<()> {
    let i = i.as_ref().ok_or(BAD)?;
    let utility =
        Suite::<AEGP_UtilitySuite6>::get(i, kAEGPUtilitySuite, kAEGPUtilitySuiteVersion6 as i32)?;
    let mut id = 0;
    check(utility.value().AEGP_RegisterWithAEGP.ok_or(BAD)?(
        ptr::null_mut(),
        c"OLM Color Key".as_ptr(),
        &mut id,
    ))?;
    PLUGIN_ID.store(id, Ordering::Relaxed);
    Ok(())
}

pub(super) unsafe fn update(input: *mut PF_InData, params: PF_ParamList) -> Result<()> {
    let i = input.as_ref().ok_or(BAD)?;
    if params.is_null() {
        return Err(BAD);
    }
    let at = |slot: usize| (*params.add(slot)).as_ref().ok_or(BAD);
    let per_color = at(7)?.u.bd.value != 0;
    let per_component = at(8)?.u.bd.value != 0;
    let replace = at(23)?.u.bd.value != 0;
    let count = at(22)?.u.sd.value;
    if !(0..=MAX_COLORS as i32).contains(&count) {
        return Err(BAD);
    }
    let utils = Suite::<PF_ParamUtilsSuite3>::get(i, kPFParamUtilsSuite, 3)?;
    let interface = Suite::<AEGP_PFInterfaceSuite1>::get(i, kAEGPPFInterfaceSuite, 1)?;
    let streams =
        Suite::<AEGP_StreamSuite6>::get(i, kAEGPStreamSuite, kAEGPStreamSuiteVersion6 as i32)?;
    let dynamic = Suite::<AEGP_DynamicStreamSuite4>::get(
        i,
        kAEGPDynamicStreamSuite,
        kAEGPDynamicStreamSuiteVersion4 as i32,
    )?;
    let effects =
        Suite::<AEGP_EffectSuite5>::get(i, kAEGPEffectSuite, kAEGPEffectSuiteVersion5 as i32)?;
    let dispose_effect = effects.value().AEGP_DisposeEffect.ok_or(BAD)?;
    let dispose_stream = streams.value().AEGP_DisposeStream.ok_or(BAD)?;
    let new_stream = streams.value().AEGP_GetNewEffectStreamByIndex.ok_or(BAD)?;
    let set_hidden = dynamic.value().AEGP_SetDynamicStreamFlag.ok_or(BAD)?;
    let update = utils.value().PF_UpdateParamUI.ok_or(BAD)?;
    let id = PLUGIN_ID.load(Ordering::Relaxed);
    let mut effect = ptr::null_mut();
    check(interface.value().AEGP_GetNewEffectForEffect.ok_or(BAD)?(
        id,
        i.effect_ref,
        &mut effect,
    ))?;
    if effect.is_null() {
        return Err(BAD);
    }
    let result = (|| -> Result<()> {
        let enabled = |slot: usize, enable: bool| -> Result<()> {
            let mut p = *at(slot)?;
            if enable {
                p.ui_flags &= !(PF_PUI_DISABLED as i32);
            } else {
                p.ui_flags |= PF_PUI_DISABLED as i32;
            }
            check(update(i.effect_ref, slot as i32, &p))
        };
        let visible = |slot: usize, show: bool| -> Result<()> {
            let mut stream = ptr::null_mut();
            check(new_stream(id, effect, slot as i32, &mut stream))?;
            if stream.is_null() {
                return Err(BAD);
            }
            let result = check(set_hidden(
                stream,
                AEGP_DynStreamFlag_HIDDEN as _,
                0,
                (!show) as _,
            ));
            let disposed = check(dispose_stream(stream));
            result?;
            disposed
        };
        enabled(2, !per_color && !per_component)?;
        for slot in 9..=11 {
            visible(slot, per_component && !per_color)?;
        }
        for n in 0..MAX_COLORS {
            let s = 24 + 8 * n;
            let active = n < count as usize;
            let use_color = at(s)?.u.bd.value != 0;
            let use_replace = at(s + 1)?.u.bd.value != 0;
            enabled(s + 2, use_color)?;
            visible(s + 2, active)?;
            visible(s, active)?;
            visible(s + 1, active && replace)?;
            enabled(s + 1, use_color)?;
            visible(s + 3, active && replace && use_replace)?;
            enabled(s + 3, use_color)?;
            visible(s + 4, active && per_color && !per_component)?;
            for slot in s + 5..=s + 7 {
                visible(slot, active && per_color && per_component)?;
            }
        }
        Ok(())
    })();
    let disposed = check(dispose_effect(effect));
    result?;
    disposed
}

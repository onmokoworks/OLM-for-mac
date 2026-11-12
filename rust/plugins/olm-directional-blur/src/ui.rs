//! AEGP registration and dynamic controls, translated from the Mac adapter.
use crate::host::{sys::*, Result, BAD};
use std::{
    ptr,
    sync::atomic::{AtomicI32, Ordering},
};
static PLUGIN_ID: AtomicI32 = AtomicI32::new(0);
fn check(e: i32) -> Result<()> {
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
    unsafe fn get(i: &'a PF_InData, name: &'static [u8], version: u32) -> Result<Self> {
        let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
        basic.ReleaseSuite.ok_or(BAD)?;
        let mut raw = ptr::null();
        check(basic.AcquireSuite.ok_or(BAD)?(
            name.as_ptr().cast(),
            version as i32,
            &mut raw,
        ))?;
        let s = Self {
            basic,
            name,
            version: version as i32,
            raw: raw.cast(),
        };
        if s.raw.is_null() {
            return Err(BAD);
        }
        Ok(s)
    }
    unsafe fn value(&self) -> &T {
        &*self.raw
    }
}
impl<T> Drop for Suite<'_, T> {
    fn drop(&mut self) {
        unsafe {
            if let Some(f) = self.basic.ReleaseSuite {
                f(self.name.as_ptr().cast(), self.version);
            }
        }
    }
}
pub unsafe fn register(i: &PF_InData) -> Result<()> {
    if i.pica_basicP.is_null() {
        return Ok(());
    }
    let s = Suite::<AEGP_UtilitySuite6>::get(i, kAEGPUtilitySuite, kAEGPUtilitySuiteVersion6)?;
    let mut id = 0;
    check(s.value().AEGP_RegisterWithAEGP.ok_or(BAD)?(
        ptr::null_mut(),
        b"OLMDirectionalBlur\0".as_ptr().cast(),
        &mut id,
    ))?;
    PLUGIN_ID.store(id, Ordering::Relaxed);
    Ok(())
}
pub unsafe fn update(i: &PF_InData) -> Result<()> {
    let mut param = std::mem::zeroed();
    let checkin = i.inter.checkin_param.ok_or(BAD)?;
    check(i.inter.checkout_param.ok_or(BAD)?(
        i.effect_ref,
        16,
        i.current_time,
        i.time_step,
        i.time_scale,
        &mut param,
    ))?;
    let layer = param.u.pd.value == 3;
    check(checkin(i.effect_ref, &mut param))?;
    let pf = Suite::<AEGP_PFInterfaceSuite1>::get(
        i,
        kAEGPPFInterfaceSuite,
        kAEGPPFInterfaceSuiteVersion1,
    )?;
    let streams = Suite::<AEGP_StreamSuite6>::get(i, kAEGPStreamSuite, kAEGPStreamSuiteVersion6)?;
    let dynamic = Suite::<AEGP_DynamicStreamSuite4>::get(
        i,
        kAEGPDynamicStreamSuite,
        kAEGPDynamicStreamSuiteVersion4,
    )?;
    let effects = Suite::<AEGP_EffectSuite5>::get(i, kAEGPEffectSuite, kAEGPEffectSuiteVersion5)?;
    let dispose_effect = effects.value().AEGP_DisposeEffect.ok_or(BAD)?;
    let dispose_stream = streams.value().AEGP_DisposeStream.ok_or(BAD)?;
    let id = PLUGIN_ID.load(Ordering::Relaxed);
    let mut effect = ptr::null_mut();
    check(pf.value().AEGP_GetNewEffectForEffect.ok_or(BAD)?(
        id,
        i.effect_ref,
        &mut effect,
    ))?;
    if effect.is_null() {
        return Ok(());
    }
    let result = (|| -> Result<()> {
        for (index, hidden) in [(17, !layer), (18, layer), (19, layer), (20, layer)] {
            let mut stream = ptr::null_mut();
            check(streams.value().AEGP_GetNewEffectStreamByIndex.ok_or(BAD)?(
                id,
                effect,
                index,
                &mut stream,
            ))?;
            if stream.is_null() {
                continue;
            }
            let changed = (|| -> Result<()> {
                let mut flags = 0;
                check(dynamic.value().AEGP_GetDynamicStreamFlags.ok_or(BAD)?(
                    stream, &mut flags,
                ))?;
                check(dynamic.value().AEGP_SetDynamicStreamFlag.ok_or(BAD)?(
                    stream,
                    AEGP_DynStreamFlag_HIDDEN as _,
                    0,
                    hidden as _,
                ))
            })();
            let cleaned = check(dispose_stream(stream));
            changed?;
            cleaned?;
        }
        Ok(())
    })();
    let cleaned = check(dispose_effect(effect));
    result?;
    cleaned
}

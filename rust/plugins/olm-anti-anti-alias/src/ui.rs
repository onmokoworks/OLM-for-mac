//! AEGP-backed original buttons and dynamic palette visibility (5b00/6710/6be0).
#![allow(non_upper_case_globals)]
use crate::{
    ae::{check, checkout, snapshot, Result, BAD},
    algorithm, palette,
};
use after_effects_sys::*;
use std::{ffi::c_void, ops::Deref, ptr};
struct Suite<'a, T> {
    basic: &'a SPBasicSuite,
    name: &'static [u8],
    version: i32,
    raw: *const T,
}
impl<'a, T> Suite<'a, T> {
    unsafe fn new(i: &'a PF_InData, name: &'static [u8], version: i32) -> Result<Self> {
        let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
        basic.ReleaseSuite.ok_or(BAD)?;
        let mut raw = ptr::null();
        check(basic.AcquireSuite.ok_or(BAD)?(name.as_ptr().cast(), version, &mut raw) as _)?;
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
}
impl<T> Deref for Suite<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &*self.raw }
    }
}
impl<T> Drop for Suite<'_, T> {
    fn drop(&mut self) {
        unsafe {
            (self.basic.ReleaseSuite.unwrap())(self.name.as_ptr().cast(), self.version);
        }
    }
}
struct Handle<H: Copy> {
    h: H,
    dispose: unsafe extern "C" fn(H) -> A_Err,
    live: bool,
}
impl<H: Copy> Handle<H> {
    fn new(h: H, dispose: unsafe extern "C" fn(H) -> A_Err) -> Self {
        Self {
            h,
            dispose,
            live: true,
        }
    }
    unsafe fn finish(mut self) -> Result<()> {
        self.live = false;
        check((self.dispose)(self.h) as _)
    }
}
impl<H: Copy> Drop for Handle<H> {
    fn drop(&mut self) {
        if self.live {
            unsafe {
                (self.dispose)(self.h);
            }
        }
    }
}
unsafe fn stream(
    s: &AEGP_StreamSuite3,
    e: AEGP_EffectRefH,
    index: i32,
) -> Result<Handle<AEGP_StreamRefH>> {
    let dispose = s.AEGP_DisposeStream.ok_or(BAD)?;
    let mut h = ptr::null_mut();
    check(s.AEGP_GetNewEffectStreamByIndex.ok_or(BAD)?(0, e, index, &mut h) as _)?;
    Ok(Handle::new(h, dispose))
}
unsafe fn set(
    s: &AEGP_StreamSuite3,
    e: AEGP_EffectRefH,
    index: i32,
    value: AEGP_StreamVal2,
) -> Result<()> {
    let h = stream(s, e, index)?;
    let mut v = AEGP_StreamValue2 {
        streamH: h.h,
        val: value,
    };
    check(s.AEGP_SetStreamValue.ok_or(BAD)?(0, h.h, &mut v) as _)?;
    h.finish()
}
fn color(c: algorithm::Color) -> AEGP_StreamVal2 {
    AEGP_StreamVal2 {
        color: AEGP_ColorVal {
            alphaF: c[0] as _,
            redF: c[1] as _,
            greenF: c[2] as _,
            blueF: c[3] as _,
        },
    }
}
unsafe fn visibility(i: &PF_InData, s: &AEGP_StreamSuite3, e: AEGP_EffectRefH) -> Result<()> {
    let mut count = std::mem::zeroed();
    checkout(i, 1, &mut count)?;
    let n = count.u.sd.value;
    check(i.inter.checkin_param.ok_or(BAD)?(i.effect_ref, &mut count))?;
    let dynamic = Suite::<AEGP_DynamicStreamSuite3>::new(i, b"AEGP Dynamic Stream Suite\0", 3)?;
    let set = dynamic.AEGP_SetDynamicStreamFlag.ok_or(BAD)?;
    for k in 0..100 {
        let h = stream(s, e, k + 7)?;
        check(set(h.h, 2, 0, (k >= n) as _) as _)?;
        h.finish()?;
    }
    Ok(())
}
unsafe fn detect_and_write(
    i: &PF_InData,
    s: &AEGP_StreamSuite3,
    e: AEGP_EffectRefH,
    init: bool,
) -> Result<()> {
    let options =
        Suite::<AEGP_LayerRenderOptionsSuite2>::new(i, b"AEGP Layer Render Options Suite\0", 2)?;
    let render = Suite::<AEGP_RenderSuite5>::new(i, b"AEGP Render Suite\0", 8)?;
    let world = Suite::<AEGP_WorldSuite3>::new(i, b"AEGP World Suite\0", 3)?;
    let pixel = Suite::<PF_WorldSuite2>::new(i, kPFWorldSuite, 2)?;
    let dispose = options.AEGP_Dispose.ok_or(BAD)?;
    let checkin = render.AEGP_CheckinFrame.ok_or(BAD)?;
    let mut oh = ptr::null_mut();
    check(options.AEGP_NewFromUpstreamOfEffect.ok_or(BAD)?(0, e, &mut oh) as _)?;
    let oh = Handle::new(oh, dispose);
    check(options.AEGP_SetDownsampleFactor.ok_or(BAD)?(oh.h, 1, 1) as _)?;
    let mut receipt = ptr::null_mut();
    check(render.AEGP_RenderAndCheckoutLayerFrame.ok_or(BAD)?(
        oh.h,
        None,
        ptr::null_mut(),
        &mut receipt,
    ) as _)?;
    let receipt = Handle::new(receipt, checkin);
    let mut wh = ptr::null_mut();
    check(render.AEGP_GetReceiptWorld.ok_or(BAD)?(receipt.h, &mut wh) as _)?;
    let mut w: PF_EffectWorld = std::mem::zeroed();
    check(world.AEGP_FillOutPFEffectWorld.ok_or(BAD)?(wh, &mut w) as _)?;
    let mut format = 0;
    check(pixel.PF_GetPixelFormat.ok_or(BAD)?(&w, &mut format))?;
    let bpp = match format {
        PF_PixelFormat_ARGB32 => 4,
        PF_PixelFormat_ARGB64 => 8,
        PF_PixelFormat_ARGB128 => 16,
        _ => return Err(BAD),
    };
    if w.width < 0 || w.height < 0 || w.rowbytes < 0 || w.data.is_null() {
        return Err(BAD);
    }
    let layout = algorithm::Layout {
        width: w.width as _,
        height: w.height as _,
        row_bytes: w.rowbytes as _,
        bytes_per_pixel: bpp,
        origin: (w.origin_x, w.origin_y),
    };
    let span = layout
        .span()
        .filter(|&n| n <= isize::MAX as usize)
        .ok_or(BAD)?;
    let active = snapshot(i)?.colors;
    let (count, edits) = palette::additions(
        std::slice::from_raw_parts(w.data.cast(), span),
        layout,
        &active,
        init,
    )
    .map_err(|_| BAD)?;
    if count > active.len() {
        set(
            s,
            e,
            1,
            AEGP_StreamVal2 {
                one_d: count as f64,
            },
        )?
    }
    for (slot, c) in edits {
        set(s, e, slot as i32 + 7, color(c))?
    }
    receipt.finish()?;
    oh.finish()
}
pub unsafe fn handle(
    cmd: PF_Cmd,
    i: &PF_InData,
    _params: PF_ParamList,
    extra: *mut c_void,
) -> Result<()> {
    let button = if cmd == PF_Cmd_USER_CHANGED_PARAM {
        (extra as *const PF_UserChangedParamExtra)
            .as_ref()
            .ok_or(BAD)?
            .param_index
    } else {
        0
    };
    if cmd != PF_Cmd_UPDATE_PARAMS_UI && !(3..=5).contains(&button) {
        return Ok(());
    }
    let interface = Suite::<AEGP_PFInterfaceSuite1>::new(i, b"AEGP PF Interface Suite\0", 1)?;
    let effects = Suite::<AEGP_EffectSuite1>::new(i, b"AEGP Effect Suite\0", 1)?;
    let streams = Suite::<AEGP_StreamSuite3>::new(i, b"AEGP Stream Suite\0", 8)?;
    let dispose = effects.AEGP_DisposeEffect.ok_or(BAD)?;
    let mut e = ptr::null_mut();
    check(interface.AEGP_GetNewEffectForEffect.ok_or(BAD)?(0, i.effect_ref, &mut e) as _)?;
    let e = Handle::new(e, dispose);
    if cmd == PF_Cmd_UPDATE_PARAMS_UI {
        visibility(i, &streams, e.h)?
    } else {
        if button == 3 || button == 5 {
            for k in 0..100 {
                set(&streams, e.h, k + 7, color([0.0; 4]))?
            }
        }
        if button != 5 {
            detect_and_write(i, &streams, e.h, button == 3)?
        }
    }
    e.finish()
}
#[cfg(test)]
#[path = "ui_tests.rs"]
mod tests;

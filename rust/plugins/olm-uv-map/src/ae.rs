//! UV Map CPU SmartFX adapter. Secondary layers use PF checkout_param like the original.
#![allow(non_upper_case_globals, non_snake_case)]
use crate::{
    algorithm::{self, Layout},
    params,
};
use after_effects_sys::*;
use std::{ffi::c_void, ptr};
pub type Result<T> = std::result::Result<T, PF_Err>;
pub const BAD: PF_Err = PF_Err_BAD_CALLBACK_PARAM as _;
pub fn check(e: PF_Err) -> Result<()> {
    if e == 0 {
        Ok(())
    } else {
        Err(e)
    }
}

unsafe fn world_depth(
    i: &PF_InData,
    a: *const PF_LayerDef,
    b: *const PF_LayerDef,
) -> Result<usize> {
    let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
    let release = basic.ReleaseSuite.ok_or(BAD)?;
    let mut raw = ptr::null();
    check(basic.AcquireSuite.ok_or(BAD)?(kPFWorldSuite.as_ptr().cast(), 2, &mut raw) as _)?;
    let result = (|| {
        let suite = (raw as *const PF_WorldSuite2).as_ref().ok_or(BAD)?;
        let get = suite.PF_GetPixelFormat.ok_or(BAD)?;
        let (mut x, mut y) = (0, 0);
        check(get(a, &mut x))?;
        check(get(b, &mut y))?;
        if x != y {
            return Err(BAD);
        }
        match x {
            PF_PixelFormat_ARGB32 => Ok(8),
            PF_PixelFormat_ARGB64 => Ok(16),
            PF_PixelFormat_ARGB128 => Ok(32),
            _ => Err(BAD),
        }
    })();
    let cleanup = check(release(kPFWorldSuite.as_ptr().cast(), 2) as _);
    let d = result?;
    cleanup?;
    Ok(d)
}
fn supported(depth: usize) -> bool {
    match depth {
        8 => true,
        16 => params::FLAGS & (1 << 25) != 0,
        32 => params::FLAGS2 & (1 << 12) != 0,
        _ => false,
    }
}
fn layout(w: &PF_LayerDef, depth: usize) -> Result<Layout> {
    if w.width < 0 || w.height < 0 || w.rowbytes < 0 || w.data.is_null() {
        return Err(BAD);
    }
    Ok(Layout {
        width: w.width as _,
        height: w.height as _,
        row_bytes: w.rowbytes as _,
        bytes_per_pixel: depth / 2,
        origin: (w.origin_x, w.origin_y),
    })
}
unsafe fn render(
    i: &PF_InData,
    input: *const PF_LayerDef,
    output: *mut PF_LayerDef,
    expected: Option<usize>,
    texture: Option<&PF_LayerDef>,
    params: algorithm::Params,
) -> Result<()> {
    let a = input.as_ref().ok_or(BAD)?;
    let b = output.as_ref().ok_or(BAD)?;
    let depth = world_depth(i, input, output)?;
    if !supported(depth) || expected.is_some_and(|d| d != depth) {
        return Err(BAD);
    }
    let mut la = layout(a, depth)?;
    let mut lb = layout(b, depth)?;
    // 180003be0 passes output.extent_hint to the plain Iterate suite.
    // That walk uses local x/y on both worlds, not output origin offsets.
    la.origin = (0, 0);
    let left = b.extent_hint.left.max(0) as usize;
    let top = b.extent_hint.top.max(0) as usize;
    let right = (b.extent_hint.right.max(0) as usize)
        .min(la.width)
        .min(lb.width);
    let bottom = (b.extent_hint.bottom.max(0) as usize)
        .min(la.height)
        .min(lb.height);
    if right <= left || bottom <= top {
        return Ok(());
    }
    let offset = top
        .checked_mul(lb.row_bytes)
        .and_then(|v| v.checked_add(left * lb.bytes_per_pixel))
        .ok_or(BAD)?;
    lb.width = right - left;
    lb.height = bottom - top;
    lb.origin = (left as i32, top as i32);
    let na = la.span().ok_or(BAD)?;
    let nb = lb.span().ok_or(BAD)?;
    if na > isize::MAX as usize || nb > isize::MAX as usize {
        return Err(BAD);
    }
    let pa = a.data as usize;
    let pb = (b.data as usize).checked_add(offset).ok_or(BAD)?;
    let ea = pa.checked_add(na).ok_or(BAD)?;
    let eb = pb.checked_add(nb).ok_or(BAD)?;
    if pa < eb && pb < ea {
        return Err(BAD);
    }
    let tex = if let Some(t) = texture.filter(|t| !t.data.is_null() && t.width > 0 && t.height > 0)
    {
        if world_depth(i, input, t)? != depth {
            return Err(BAD);
        }
        let lt = layout(t, depth)?;
        let nt = lt.span().ok_or(BAD)?;
        if nt > isize::MAX as usize {
            return Err(BAD);
        }
        let pt = t.data as usize;
        let et = pt.checked_add(nt).ok_or(BAD)?;
        if pt < eb && pb < et {
            return Err(BAD);
        }
        Some((std::slice::from_raw_parts(t.data.cast(), nt), lt))
    } else {
        None
    };
    algorithm::render(
        std::slice::from_raw_parts(a.data.cast(), na),
        la,
        tex,
        std::slice::from_raw_parts_mut((pb as *mut u8).cast(), nb),
        lb,
        params,
    )
    .map_err(|_| BAD)
}
struct Pixels<'a> {
    i: &'a PF_InData,
    cb: &'a PF_SmartRenderCallbacks,
    active: bool,
}
impl Pixels<'_> {
    unsafe fn finish(&mut self) -> Result<()> {
        self.active = false;
        check(self.cb.checkin_layer_pixels.ok_or(BAD)?(
            self.i.effect_ref,
            0,
        ))
    }
}
impl Drop for Pixels<'_> {
    fn drop(&mut self) {
        if self.active {
            unsafe {
                let _ = self.finish();
            }
        }
    }
}
struct ParamCheckout<'a> {
    i: &'a PF_InData,
    value: Box<PF_ParamDef>,
    active: bool,
}
impl<'a> ParamCheckout<'a> {
    unsafe fn new(i: &'a PF_InData, slot: i32) -> Result<Self> {
        i.inter.checkin_param.ok_or(BAD)?;
        let mut value = Box::new(std::mem::zeroed());
        check(i.inter.checkout_param.ok_or(BAD)?(
            i.effect_ref,
            slot,
            i.current_time,
            i.time_step,
            i.time_scale,
            &mut *value,
        ))?;
        Ok(Self {
            i,
            value,
            active: true,
        })
    }
    unsafe fn finish(&mut self) -> Result<()> {
        self.active = false;
        check(self.i.inter.checkin_param.ok_or(BAD)?(
            self.i.effect_ref,
            &mut *self.value,
        ))
    }
}
impl Drop for ParamCheckout<'_> {
    fn drop(&mut self) {
        if self.active {
            unsafe {
                let _ = self.finish();
            }
        }
    }
}
pub unsafe fn entry(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    extra: *mut c_void,
) -> PF_Err {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| -> Result<()> {
        let i = i.as_ref().ok_or(BAD)?;
        let o = o.as_mut().ok_or(BAD)?;
        match cmd {
            PF_Cmd_GLOBAL_SETUP => {
                o.my_version = params::VERSION;
                o.out_flags = params::FLAGS as _;
                o.out_flags2 = params::FLAGS2 as _;
            }
            PF_Cmd_PARAMS_SETUP => params::setup(i, o)?,
            PF_Cmd_UPDATE_PARAMS_UI | PF_Cmd_USER_CHANGED_PARAM | PF_Cmd_EVENT => {
                crate::ui::handle(cmd, i, p, extra)?
            }
            PF_Cmd_ARBITRARY_CALLBACK => crate::arbitrary::callback(
                i,
                (extra as *mut PF_ArbParamsExtra).as_mut().ok_or(BAD)?,
            )?,
            PF_Cmd_RENDER => {
                if params::FLAGS2 & (1 << 10) != 0 || p.is_null() {
                    return Err(BAD);
                }
                let input = (*p).as_ref().ok_or(BAD)?;
                let depth = world_depth(i, &input.u.ld, w)?;
                if depth == 32 {
                    return Err(BAD);
                }
                render(
                    i,
                    &input.u.ld,
                    w,
                    Some(depth),
                    None,
                    algorithm::Params::default(),
                )?;
            }
            PF_Cmd_SMART_PRE_RENDER => {
                if params::FLAGS2 & (1 << 10) == 0 {
                    return Err(BAD);
                }
                let e = (extra as *mut PF_PreRenderExtra).as_mut().ok_or(BAD)?;
                let ei = e.input.as_ref().ok_or(BAD)?;
                let eo = e.output.as_mut().ok_or(BAD)?;
                let cb = e.cb.as_ref().ok_or(BAD)?;
                let req = ei.output_request;
                // Original requests the primary UV world unchanged.

                let mut r = std::mem::zeroed();
                check(cb.checkout_layer.ok_or(BAD)?(
                    i.effect_ref,
                    0,
                    0,
                    &req,
                    i.current_time,
                    i.time_step,
                    i.time_scale,
                    &mut r,
                ))?;
                eo.result_rect = r.result_rect;
                eo.max_result_rect = r.max_result_rect;
            }
            PF_Cmd_SMART_RENDER => {
                if params::FLAGS2 & (1 << 10) == 0 {
                    return Err(BAD);
                }
                let e = (extra as *mut PF_SmartRenderExtra).as_ref().ok_or(BAD)?;
                let ei = e.input.as_ref().ok_or(BAD)?;
                let cb = e.cb.as_ref().ok_or(BAD)?;
                if !supported(ei.bitdepth as usize) {
                    return Err(BAD);
                }
                cb.checkin_layer_pixels.ok_or(BAD)?;
                let mut input = ptr::null_mut();
                check(cb.checkout_layer_pixels.ok_or(BAD)?(
                    i.effect_ref,
                    0,
                    &mut input,
                ))?;
                let mut guard = Pixels {
                    i,
                    cb,
                    active: true,
                };
                let mut output = ptr::null_mut();
                check(cb.checkout_output.ok_or(BAD)?(i.effect_ref, &mut output))?;
                let mut texture = ParamCheckout::new(i, 1)?;
                let mut method = ParamCheckout::new(i, 2)?;
                let mut smooth = ParamCheckout::new(i, 3)?;
                let parameters = algorithm::Params {
                    method: method.value.u.pd.value,
                    smoothness: smooth.value.u.fs_d.value as f32,
                };
                let result = render(
                    i,
                    input,
                    output,
                    Some(ei.bitdepth as usize),
                    Some(&texture.value.u.ld),
                    parameters,
                );
                let a = smooth.finish();
                let b = method.finish();
                let c = texture.finish();
                result?;
                a?;
                b?;
                c?;
                guard.finish()?;
            }
            _ => {}
        }
        Ok(())
    }))
    .unwrap_or(Err(BAD))
    .err()
    .unwrap_or(0)
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
    entry(cmd, i, o, p, w, e)
}
// The generator appends the exact Windows PiPL entry alias, if different.

#[export_name = "entryPointFunc"]
pub unsafe extern "C" fn original_entry_alias(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut c_void,
) -> PF_Err {
    entry(cmd, i, o, p, w, e)
}

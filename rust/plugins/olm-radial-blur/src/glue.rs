//! Crate-local extension of the pilot AE boundary for Point, Angle and Layer.
//! Host pointers and checkout lifetimes stay here; no shared source is changed.
#![allow(non_upper_case_globals)] // Adobe SDK selector names are ABI constants.
pub use olm_ae::sys;
use olm_core::{Depth, Layout, View, ViewMut};
use std::{
    ffi::{c_void, CString},
    ptr,
};
use sys::*;
pub type Result<T> = std::result::Result<T, PF_Err>;
pub const BAD: PF_Err = PF_Err_BAD_CALLBACK_PARAM as PF_Err;
fn check(e: PF_Err) -> Result<()> {
    if e == 0 {
        Ok(())
    } else {
        Err(e)
    }
}

#[derive(Clone, Debug)]
pub enum Kind {
    Integer {
        min: i32,
        max: i32,
        slider_min: i32,
        slider_max: i32,
        default: i32,
    },
    Float {
        min: f32,
        max: f32,
        slider_min: f32,
        slider_max: f32,
        default: f32,
        precision: i16,
    },
    Checkbox(bool),
    Popup {
        choices: String,
        default: i16,
    },
    Point,
    Angle,
    Layer,
    GroupStart,
    GroupEnd,
}
/// Exact ordered parameter declaration. IDs are saved-project disk IDs, not slots.
#[derive(Clone, Debug)]
pub struct Param {
    pub id: i32,
    pub name: String,
    pub flags: i32,
    pub ui_flags: i32,
    pub kind: Kind,
}
#[derive(Clone, Copy, Debug)]
pub struct Value {
    pub number: f64,
    pub point: [f64; 2],
}
pub use olm_ae::{Downsample, RenderContext};
/// Stateless plug-in contract. Parameters exclude input slot zero; values match
/// this order. All render state must be local to preserve concurrent renders.
pub trait Effect {
    const NAME: &'static str;
    const VERSION: u32;
    const FLAGS: u32;
    const FLAGS2: u32 = 0x08001400;
    /// None preserves the host request; Some matches an explicit original override.
    const PRESERVE_ZERO_ALPHA_RGB: Option<bool> = None;
    fn params() -> Vec<Param>;
    /// Full-size byte-copy shortcut; host retains stride and checkout ownership.
    fn copy_only(_values: &[Value], _ctx: RenderContext) -> bool {
        false
    }
    fn render(
        values: &[Value],
        ctx: RenderContext,
        input: &View<'_>,
        output: &mut ViewMut<'_>,
    ) -> olm_core::Result<()>;
}

unsafe fn setup<E: Effect>(i: &PF_InData, o: &mut PF_OutData) -> Result<()> {
    let add = i.inter.add_param.ok_or(BAD)?;
    let specs = E::params();
    for s in &specs {
        let mut p: PF_ParamDef = std::mem::zeroed();
        p.uu.id = s.id;
        p.flags = s.flags;
        p.ui_flags = s.ui_flags;
        for (a, b) in p.name.iter_mut().take(31).zip(s.name.bytes()) {
            *a = b as _;
        }
        let mut text = None;
        match &s.kind {
            Kind::Integer {
                min,
                max,
                slider_min,
                slider_max,
                default,
            } => {
                p.param_type = PF_Param_SLIDER;
                p.u.sd = PF_SliderDef {
                    value: *default,
                    dephault: *default,
                    valid_min: *min,
                    valid_max: *max,
                    slider_min: *slider_min,
                    slider_max: *slider_max,
                    ..std::mem::zeroed()
                };
            }
            Kind::Float {
                min,
                max,
                slider_min,
                slider_max,
                default,
                precision,
            } => {
                p.param_type = PF_Param_FLOAT_SLIDER;
                p.u.fs_d = PF_FloatSliderDef {
                    value: *default as f64,
                    dephault: *default,
                    valid_min: *min,
                    valid_max: *max,
                    slider_min: *slider_min,
                    slider_max: *slider_max,
                    precision: *precision,
                    ..std::mem::zeroed()
                };
            }
            Kind::Checkbox(v) => {
                p.param_type = PF_Param_CHECKBOX;
                p.u.bd.value = *v as _;
                p.u.bd.dephault = *v as _;
                p.u.bd.u.nameptr = c"".as_ptr();
            }
            Kind::Popup { choices, default } => {
                p.param_type = PF_Param_POPUP;
                text = Some(CString::new(choices.as_bytes()).map_err(|_| BAD)?);
                p.u.pd.num_choices = choices.split('|').count() as _;
                p.u.pd.value = *default as _;
                p.u.pd.dephault = *default;
                p.u.pd.u.namesptr = text.as_ref().unwrap().as_ptr();
            }
            Kind::Point => {
                p.param_type = PF_Param_POINT;
                p.u.td.x_value = 50 * 65536;
                p.u.td.y_value = 50 * 65536;
                p.u.td.x_dephault = 50 * 65536;
                p.u.td.y_dephault = 50 * 65536;
            }
            Kind::Angle => {
                p.param_type = PF_Param_ANGLE;
            }
            Kind::Layer => {
                p.param_type = PF_Param_LAYER;
                p.u.ld.dephault = 0;
            }
            Kind::GroupStart => p.param_type = PF_Param_GROUP_START,
            Kind::GroupEnd => p.param_type = PF_Param_GROUP_END,
        }
        check(add(i.effect_ref, -1, &mut p))?;
        drop(text);
    }
    o.num_params = specs.len() as i32 + 1;
    Ok(())
}

struct CheckedParam<'a> {
    i: &'a PF_InData,
    p: Box<PF_ParamDef>,
    active: bool,
}
impl CheckedParam<'_> {
    unsafe fn finish(&mut self) -> Result<()> {
        self.active = false;
        check(self.i.inter.checkin_param.ok_or(BAD)?(
            self.i.effect_ref,
            &mut *self.p,
        ))
    }
}
impl Drop for CheckedParam<'_> {
    fn drop(&mut self) {
        if self.active {
            unsafe {
                let _ = self.finish();
            }
        }
    }
}
unsafe fn values<E: Effect>(
    i: &PF_InData,
    params: PF_ParamList,
    smart: bool,
) -> Result<Vec<Value>> {
    let specs = E::params();
    let mut out = Vec::with_capacity(specs.len());
    for (n, s) in specs.iter().enumerate() {
        let mut checked = None;
        // Topics carry no stream and must not be checked out in SmartRender.
        if matches!(s.kind, Kind::GroupStart | Kind::GroupEnd | Kind::Layer) {
            out.push(Value {
                number: 0.0,
                point: [0.0; 2],
            });
            continue;
        }
        let p = if smart {
            let checkout = i.inter.checkout_param.ok_or(BAD)?;
            i.inter.checkin_param.ok_or(BAD)?;
            // The host owns this address until checkin, including moves of the guard.
            let mut p = Box::new(std::mem::zeroed());
            check(checkout(
                i.effect_ref,
                (n + 1) as _,
                i.current_time,
                i.time_step,
                i.time_scale,
                &mut *p,
            ))?;
            checked = Some(CheckedParam { i, p, active: true });
            &*checked.as_ref().unwrap().p
        } else {
            if params.is_null() {
                return Err(BAD);
            }
            (*params.add(n + 1)).as_ref().ok_or(BAD)?
        };
        let mut v = Value {
            number: 0.0,
            point: [0.0; 2],
        };
        match s.kind {
            Kind::Point => {
                v.point = [
                    p.u.td.x_value as f64 / 65536.0,
                    p.u.td.y_value as f64 / 65536.0,
                ]
            }
            Kind::Angle => v.number = p.u.ad.value as f64 / 65536.0,
            Kind::Integer { .. } => v.number = p.u.sd.value as f64,
            Kind::Float { .. } => v.number = p.u.fs_d.value,
            Kind::Checkbox(_) => v.number = p.u.bd.value as f64,
            Kind::Popup { .. } => v.number = p.u.pd.value as f64,
            _ => {}
        }
        out.push(v);
        if let Some(c) = &mut checked {
            c.finish()?;
        }
    }
    Ok(out)
}

unsafe fn world_layout(w: &PF_LayerDef, depth: Depth) -> Result<Layout> {
    if w.width <= 0 || w.height <= 0 || w.rowbytes <= 0 || w.data.is_null() {
        return Err(BAD);
    }
    let l = Layout {
        width: w.width as _,
        height: w.height as _,
        stride: w.rowbytes as _,
        depth,
        origin: (w.origin_x, w.origin_y),
    };
    l.span().map_err(|_| BAD)?;
    Ok(l)
}
unsafe fn world_depth(
    i: &PF_InData,
    a: *const PF_LayerDef,
    b: *const PF_LayerDef,
) -> Result<Depth> {
    let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
    let acquire = basic.AcquireSuite.ok_or(BAD)?;
    let release = basic.ReleaseSuite.ok_or(BAD)?;
    let mut raw = ptr::null();
    check(acquire(kPFWorldSuite.as_ptr().cast(), 2, &mut raw) as PF_Err)?;
    let result = (|| {
        let s = (raw as *const PF_WorldSuite2).as_ref().ok_or(BAD)?;
        let f = s.PF_GetPixelFormat.ok_or(BAD)?;
        let mut af = 0;
        let mut bf = 0;
        check(f(a, &mut af))?;
        check(f(b, &mut bf))?;
        if af != bf {
            return Err(BAD);
        }
        match af {
            PF_PixelFormat_ARGB32 => Ok(Depth::U8),
            PF_PixelFormat_ARGB64 => Ok(Depth::U16),
            PF_PixelFormat_ARGB128 => Ok(Depth::F32),
            _ => Err(BAD),
        }
    })();
    let freed = check(release(kPFWorldSuite.as_ptr().cast(), 2) as PF_Err);
    let d = result?;
    freed?;
    Ok(d)
}
unsafe fn render<E: Effect>(
    i: &PF_InData,
    params: PF_ParamList,
    input: *const PF_LayerDef,
    output: *mut PF_LayerDef,
    depth: Depth,
    smart: bool,
) -> Result<()> {
    let a = input.as_ref().ok_or(BAD)?;
    let b = output.as_ref().ok_or(BAD)?;
    if world_depth(i, input, output)? != depth {
        return Err(BAD);
    }
    let la = world_layout(a, depth)?;
    let lb = world_layout(b, depth)?;
    let na = la.span().map_err(|_| BAD)?;
    let nb = lb.span().map_err(|_| BAD)?;
    let pa = a.data as usize;
    let pb = b.data as usize;
    let ea = pa.checked_add(na).ok_or(BAD)?;
    let eb = pb.checked_add(nb).ok_or(BAD)?;
    if pa < eb && pb < ea {
        return Err(BAD);
    }
    let extent = b.extent_hint;
    let ctx = RenderContext {
        downsample_x: Downsample::new(i.downsample_x.num, i.downsample_x.den)?,
        downsample_y: Downsample::new(i.downsample_y.num, i.downsample_y.den)?,
        smart,
        output_extent: olm_core::Rect::new(
            extent.left as i32,
            extent.top as i32,
            extent.right as i32,
            extent.bottom as i32,
        )
        .map_err(|_| BAD)?,
    };
    let v = values::<E>(i, params, smart)?;
    let input = View::new(std::slice::from_raw_parts(a.data.cast(), na), la).map_err(|_| BAD)?;
    let destination = std::slice::from_raw_parts_mut(b.data.cast::<u8>(), nb);
    if la.width == lb.width
        && la.height == lb.height
        && la.origin == lb.origin
        && E::copy_only(&v, ctx)
    {
        copy_rows(
            std::slice::from_raw_parts(a.data.cast::<u8>(), na),
            la,
            destination,
            lb,
        );
        Ok(())
    } else if E::copy_only(&v, ctx) {
        // Match the original host copy's resampling for a smaller Smart output.
        host_copy(i, a, output)
    } else {
        let mut output = ViewMut::new(destination, lb).map_err(|_| BAD)?;
        E::render(&v, ctx, &input, &mut output).map_err(|_| BAD)
    }
}

struct CheckedPixels<'a> {
    i: &'a PF_InData,
    cb: &'a PF_SmartRenderCallbacks,
    active: bool,
}
impl CheckedPixels<'_> {
    unsafe fn finish(&mut self) -> Result<()> {
        self.active = false;
        check(self.cb.checkin_layer_pixels.ok_or(BAD)?(
            self.i.effect_ref,
            0,
        ))
    }
}
impl Drop for CheckedPixels<'_> {
    fn drop(&mut self) {
        if self.active {
            unsafe {
                let _ = self.finish();
            }
        }
    }
}
/// AE C ABI entry; caller must supply the valid pointers required by its selector.
/// Panics are contained and all successful checkouts have scope-bound checkin.
pub unsafe fn entry<E: Effect>(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    params: PF_ParamList,
    output: *mut PF_LayerDef,
    extra: *mut c_void,
) -> PF_Err {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| -> Result<()> {
        let i = i.as_ref().ok_or(BAD)?;
        let o = o.as_mut().ok_or(BAD)?;
        match cmd {
            PF_Cmd_GLOBAL_SETUP => {
                o.my_version = E::VERSION;
                o.out_flags = E::FLAGS as _;
                o.out_flags2 = E::FLAGS2 as _;
            }
            PF_Cmd_PARAMS_SETUP => setup::<E>(i, o)?,
            PF_Cmd_UPDATE_PARAMS_UI => crate::ui::update(i, params)?,
            PF_Cmd_RENDER => {
                if params.is_null() {
                    return Err(BAD);
                }
                let p = (*params).as_ref().ok_or(BAD)?;
                let d = world_depth(i, &p.u.ld, output)?;
                if d == Depth::F32 {
                    return Err(BAD);
                }
                render::<E>(i, params, &p.u.ld, output, d, false)?;
            }
            PF_Cmd_SMART_PRE_RENDER => {
                let e = (extra as *mut PF_PreRenderExtra).as_mut().ok_or(BAD)?;
                let ei = e.input.as_ref().ok_or(BAD)?;
                let eo = e.output.as_mut().ok_or(BAD)?;
                let cb = e.cb.as_ref().ok_or(BAD)?;
                let mut req = ei.output_request;
                // Radial neighborhoods require the complete input world.
                req.rect = PF_LRect {
                    left: 0,
                    top: 0,
                    right: i.width,
                    bottom: i.height,
                };
                if let Some(preserve) = E::PRESERVE_ZERO_ALPHA_RGB {
                    req.preserve_rgb_of_zero_alpha = preserve as _;
                }
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
                let requested = ei.output_request.rect;
                if requested.left > r.result_rect.left
                    || requested.top > r.result_rect.top
                    || requested.right < r.result_rect.right
                    || requested.bottom < r.result_rect.bottom
                {
                    // The original no-op preserves the requested output dimensions;
                    // its PF_COPY then scales the complete checked-out input into them.
                    let v = values::<E>(i, params, true)?;
                    let ctx = RenderContext {
                        downsample_x: Downsample::new(i.downsample_x.num, i.downsample_x.den)?,
                        downsample_y: Downsample::new(i.downsample_y.num, i.downsample_y.den)?,
                        smart: true,
                        output_extent: olm_core::Rect::new(
                            requested.left,
                            requested.top,
                            requested.right,
                            requested.bottom,
                        )
                        .map_err(|_| BAD)?,
                    };
                    if E::copy_only(&v, ctx) {
                        eo.result_rect.left = requested.left.max(r.result_rect.left);
                        eo.result_rect.top = requested.top.max(r.result_rect.top);
                        eo.result_rect.right = requested.right.min(r.result_rect.right);
                        eo.result_rect.bottom = requested.bottom.min(r.result_rect.bottom);
                    }
                }
            }
            PF_Cmd_SMART_RENDER => {
                let e = (extra as *mut PF_SmartRenderExtra).as_ref().ok_or(BAD)?;
                let ei = e.input.as_ref().ok_or(BAD)?;
                let cb = e.cb.as_ref().ok_or(BAD)?;
                let depth = match ei.bitdepth {
                    8 => Depth::U8,
                    16 => Depth::U16,
                    32 => Depth::F32,
                    _ => return Err(BAD),
                };
                cb.checkin_layer_pixels.ok_or(BAD)?;
                let mut input = ptr::null_mut();
                check(cb.checkout_layer_pixels.ok_or(BAD)?(
                    i.effect_ref,
                    0,
                    &mut input,
                ))?;
                let mut guard = CheckedPixels {
                    i,
                    cb,
                    active: true,
                };
                let mut output = ptr::null_mut();
                check(cb.checkout_output.ok_or(BAD)?(i.effect_ref, &mut output))?;
                render::<E>(i, params, input, output, depth, true)?;
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

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};
    static CHECKINS: AtomicUsize = AtomicUsize::new(0);
    unsafe extern "C" fn checkout(_: PF_ProgPtr, _: i32, p: *mut *mut PF_EffectWorld) -> PF_Err {
        *p = ptr::null_mut();
        0
    }
    unsafe extern "C" fn failure(_: PF_ProgPtr, _: *mut *mut PF_EffectWorld) -> PF_Err {
        42
    }
    unsafe extern "C" fn checkin(_: PF_ProgPtr, _: i32) -> PF_Err {
        CHECKINS.fetch_add(1, Ordering::SeqCst);
        43
    }
    #[test]
    fn failed_output_checkout_balances_input_once() {
        unsafe {
            CHECKINS.store(0, Ordering::SeqCst);
            let mut i: PF_InData = std::mem::zeroed();
            let mut o = std::mem::zeroed();
            let mut input: PF_SmartRenderInput = std::mem::zeroed();
            input.bitdepth = 32;
            let mut cb = PF_SmartRenderCallbacks {
                checkout_layer_pixels: Some(checkout),
                checkout_output: Some(failure),
                checkin_layer_pixels: Some(checkin),
            };
            let mut extra = PF_SmartRenderExtra {
                input: &mut input,
                cb: &mut cb,
            };
            assert_eq!(
                entry::<crate::ae::Plugin>(
                    PF_Cmd_SMART_RENDER,
                    &mut i,
                    &mut o,
                    ptr::null_mut(),
                    ptr::null_mut(),
                    (&mut extra as *mut PF_SmartRenderExtra).cast()
                ),
                42
            );
            assert_eq!(CHECKINS.load(Ordering::SeqCst), 1);
            let mut guard = CheckedPixels {
                i: &i,
                cb: &cb,
                active: true,
            };
            assert_eq!(guard.finish(), Err(43));
            drop(guard);
            assert_eq!(CHECKINS.load(Ordering::SeqCst), 2);
        }
    }
}

// Original typed copy writes active pixels only, preserving destination padding.
fn copy_rows(source: &[u8], input: Layout, destination: &mut [u8], output: Layout) {
    let active = output.width * output.depth.pixel_bytes();
    for y in 0..output.height {
        destination[y * output.stride..y * output.stride + active]
            .copy_from_slice(&source[y * input.stride..y * input.stride + active]);
    }
}

#[cfg(test)]
mod copy_tests {
    use super::*;
    #[test]
    fn active_rows_preserve_every_bit_and_padding() {
        for depth in [Depth::U8, Depth::U16, Depth::F32] {
            let active = 7 * depth.pixel_bytes();
            let input = Layout {
                width: 7,
                height: 3,
                stride: active + 5,
                depth,
                origin: (0, 0),
            };
            let output = Layout {
                stride: active + 9,
                ..input
            };
            let source: Vec<u8> = (0..input.span().unwrap())
                .map(|i| (i * 73 + 19) as u8)
                .collect();
            let mut actual = vec![0xa5; output.span().unwrap()];
            let mut expected = actual.clone();
            let view = View::new(&source, input).unwrap();
            let mut out = ViewMut::new(&mut expected, output).unwrap();
            for y in 0..input.height {
                for x in 0..input.width {
                    out.set(x, y, view.get(x, y).unwrap()).unwrap();
                }
            }
            copy_rows(&source, input, &mut actual, output);
            assert_eq!(actual, expected);
        }
    }
}

unsafe fn host_copy(i: &PF_InData, input: &PF_LayerDef, output: *mut PF_LayerDef) -> Result<()> {
    // PF_COPY uses the legacy utility callback, whose resampling differs from
    // WorldTransformSuite::copy in the captured host. Match the original route.
    let copy = i.utils.as_ref().ok_or(BAD)?.copy.ok_or(BAD)?;
    check(copy(
        i.effect_ref,
        input as *const _ as *mut _,
        output,
        ptr::null_mut(),
        ptr::null_mut(),
    ))
}

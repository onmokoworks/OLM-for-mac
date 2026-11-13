//! Shared AE entry boundary. Algorithms receive only owned parameter values and
//! checked byte views. All host pointers and checkout lifetimes stay here.
#![allow(non_upper_case_globals)] // Adobe SDK selector names are ABI constants.
pub use after_effects;
#[cfg(not(target_os = "macos"))]
pub use after_effects::sys;
#[cfg(target_os = "macos")]
#[path = "macos_sys.rs"]
pub mod sys;
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
    Color,
    Popup {
        choices: String,
        default: i16,
    },
    GroupStart,
    GroupEnd,
}
/// Exact ordered parameter declaration. IDs are saved-project disk IDs, not slots.
#[derive(Clone, Debug)]
pub struct Param {
    pub id: i32,
    pub name: String,
    pub flags: i32,
    pub kind: Kind,
}
#[derive(Clone, Copy, Debug)]
pub struct Value {
    pub number: f64,
    pub color: [f32; 4],
    pub color8: [u8; 4],
}
/// Positive rational host downsample; ColorKey distances use denominator only.
#[derive(Clone, Copy, Debug)]
pub struct Downsample {
    pub numerator: i32,
    pub denominator: u32,
}
impl Downsample {
    pub fn new(numerator: i32, denominator: u32) -> Result<Self> {
        if numerator <= 0 || denominator == 0 {
            Err(BAD)
        } else {
            Ok(Self {
                numerator,
                denominator,
            })
        }
    }
    pub fn scale(self) -> f64 {
        self.numerator as f64 / self.denominator as f64
    }
    /// AE's checked integer floor for source dimensions at preview resolution.
    pub fn dimension(self, full: usize) -> Result<usize> {
        let scaled =
            full.checked_mul(self.numerator as usize).ok_or(BAD)? / (self.denominator as usize);
        if scaled == 0 {
            Err(BAD)
        } else {
            Ok(scaled)
        }
    }
}
#[derive(Clone, Copy, Debug)]
pub struct RenderContext {
    pub downsample_x: Downsample,
    pub downsample_y: Downsample,
    pub smart: bool,
    pub output_extent: olm_core::Rect,
}
/// Stateless plug-in contract. Parameters exclude input slot zero; values match
/// this order. All render state must be local to preserve concurrent renders.
pub trait Effect {
    const NAME: &'static str;
    const MATCH_NAME: &'static str = Self::NAME;
    const VERSION: u32;
    const FLAGS: u32;
    const FLAGS2: u32 = 0x08001400;
    /// None preserves the host request; Some matches an explicit original override.
    const PRESERVE_ZERO_ALPHA_RGB: Option<bool> = None;
    fn params() -> Vec<Param>;
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
            Kind::Color => {
                p.param_type = PF_Param_COLOR;
                p.u.cd.value.alpha = 255;
                p.u.cd.dephault.alpha = 255;
            }
            Kind::Popup { choices, default } => {
                p.param_type = PF_Param_POPUP;
                text = Some(CString::new(choices.as_bytes()).map_err(|_| BAD)?);
                p.u.pd.num_choices = choices.split('|').count() as _;
                p.u.pd.value = *default as _;
                p.u.pd.dephault = *default;
                p.u.pd.u.namesptr = text.as_ref().unwrap().as_ptr();
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
struct ColorSuite<'a> {
    i: &'a PF_InData,
    p: *const PF_ColorParamSuite1,
}
impl Drop for ColorSuite<'_> {
    fn drop(&mut self) {
        unsafe {
            if let Some(f) = (*self.i.pica_basicP).ReleaseSuite {
                f(kPFColorParamSuite.as_ptr().cast(), 1);
            }
        }
    }
}
unsafe fn values<E: Effect>(
    i: &PF_InData,
    params: PF_ParamList,
    smart: bool,
) -> Result<Vec<Value>> {
    let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
    let acquire = basic.AcquireSuite.ok_or(BAD)?;
    basic.ReleaseSuite.ok_or(BAD)?;
    let mut raw = ptr::null();
    check(acquire(kPFColorParamSuite.as_ptr().cast(), 1, &mut raw) as PF_Err)?;
    let suite = ColorSuite { i, p: raw.cast() };
    let color = (*suite.p.as_ref().ok_or(BAD)?)
        .PF_GetFloatingPointColorFromColorDef
        .ok_or(BAD)?;
    let specs = E::params();
    let mut out = Vec::with_capacity(specs.len());
    for (n, s) in specs.iter().enumerate() {
        let mut checked = None;
        // Topics carry no stream and must not be checked out in SmartRender.
        if matches!(s.kind, Kind::GroupStart | Kind::GroupEnd) {
            out.push(Value {
                number: 0.0,
                color: [0.0; 4],
                color8: [0; 4],
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
            color: [0.0; 4],
            color8: [0; 4],
        };
        match s.kind {
            Kind::Integer { .. } => v.number = p.u.sd.value as f64,
            Kind::Float { .. } => v.number = p.u.fs_d.value,
            Kind::Checkbox(_) => v.number = p.u.bd.value as f64,
            Kind::Popup { .. } => v.number = p.u.pd.value as f64,
            Kind::Color => {
                let mut c = std::mem::zeroed();
                check(color(i.effect_ref, p, &mut c))?;
                v.color = [c.alpha, c.red, c.green, c.blue];
                let c = p.u.cd.value;
                v.color8 = [c.alpha, c.red, c.green, c.blue];
            }
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
    let mut output =
        ViewMut::new(std::slice::from_raw_parts_mut(b.data.cast(), nb), lb).map_err(|_| BAD)?;
    E::render(&v, ctx, &input, &mut output).map_err(|_| BAD)
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

/// Emit the standard exported entry without adding mutable global state.
#[macro_export]
macro_rules! export_effect {
    ($effect:ty,$entry:ident) => {
        $crate::export_effect!($effect);
        #[cfg(target_os = "windows")]
        #[no_mangle]
        pub unsafe extern "C" fn $entry(
            cmd: $crate::sys::PF_Cmd,
            i: *mut $crate::sys::PF_InData,
            o: *mut $crate::sys::PF_OutData,
            p: $crate::sys::PF_ParamList,
            w: *mut $crate::sys::PF_LayerDef,
            e: *mut std::ffi::c_void,
        ) -> $crate::sys::PF_Err {
            $crate::entry::<$effect>(cmd, i, o, p, w, e)
        }
    };
    ($effect:ty) => {
        #[no_mangle]
        pub unsafe extern "C" fn EffectMain(
            cmd: $crate::sys::PF_Cmd,
            i: *mut $crate::sys::PF_InData,
            o: *mut $crate::sys::PF_OutData,
            p: $crate::sys::PF_ParamList,
            w: *mut $crate::sys::PF_LayerDef,
            e: *mut std::ffi::c_void,
        ) -> $crate::sys::PF_Err {
            $crate::entry::<$effect>(cmd, i, o, p, w, e)
        }
        #[cfg(target_os = "macos")]
        #[no_mangle]
        pub unsafe extern "C" fn PluginDataEntryFunction2(
            p: $crate::sys::PF_PluginDataPtr,
            cb: $crate::sys::PF_PluginDataCB2,
            _basic: *const $crate::sys::SPBasicSuite,
            _host: *const std::ffi::c_char,
            _version: *const std::ffi::c_char,
        ) -> $crate::sys::PF_Err {
            let Some(cb) = cb else { return $crate::BAD };
            let name = std::ffi::CString::new(<$effect as $crate::Effect>::NAME).unwrap();
            let matched = std::ffi::CString::new(<$effect as $crate::Effect>::MATCH_NAME).unwrap();
            cb(
                p,
                name.as_ptr().cast(),
                matched.as_ptr().cast(),
                b"OLM Plug-ins\0".as_ptr(),
                b"EffectMain\0".as_ptr(),
                i32::from_be_bytes(*b"eFKT"),
                13,
                28,
                0,
                b"https://olm.co.jp/\0".as_ptr(),
            )
        }
    };
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
    unsafe extern "C" fn output_failure(_: PF_ProgPtr, _: *mut *mut PF_EffectWorld) -> PF_Err {
        42
    }
    unsafe extern "C" fn checkin(_: PF_ProgPtr, _: i32) -> PF_Err {
        CHECKINS.fetch_add(1, Ordering::SeqCst);
        43
    }
    thread_local! { static PARAM_ADDRESS: std::cell::Cell<usize> = const { std::cell::Cell::new(0) }; }
    unsafe extern "C" fn param_checkin(_: PF_ProgPtr, p: *mut PF_ParamDef) -> PF_Err {
        PARAM_ADDRESS.with(|a| if a.replace(0) == p as usize { 0 } else { BAD })
    }
    #[test]
    fn moved_parameter_guard_retains_checkout_address() {
        unsafe {
            let mut i: PF_InData = std::mem::zeroed();
            i.inter.checkin_param = Some(param_checkin);
            let mut p = Box::new(std::mem::zeroed());
            PARAM_ADDRESS.with(|a| a.set((&mut *p as *mut PF_ParamDef) as usize));
            let guard = CheckedParam { i: &i, p, active: true };
            // Exercise a move into and out of another allocation, as in held checkouts.
            let mut guards = vec![guard];
            let mut moved = std::hint::black_box(guards.pop().unwrap());
            moved.finish().unwrap();
        }
    }
    struct Dummy;
    impl Effect for Dummy {
        const NAME: &'static str = "test";
        const VERSION: u32 = 0;
        const FLAGS: u32 = 0;
        fn params() -> Vec<Param> {
            vec![]
        }
        fn render(
            _: &[Value],
            _: RenderContext,
            _: &View<'_>,
            _: &mut ViewMut<'_>,
        ) -> olm_core::Result<()> {
            Ok(())
        }
    }
    #[test]
    fn failed_checkout_still_checks_in_once() {
        unsafe {
            CHECKINS.store(0, Ordering::SeqCst);
            let mut i: PF_InData = std::mem::zeroed();
            let mut o = std::mem::zeroed();
            let mut input: PF_SmartRenderInput = std::mem::zeroed();
            input.bitdepth = 8;
            let mut cb = PF_SmartRenderCallbacks {
                checkout_layer_pixels: Some(checkout),
                checkout_output: Some(output_failure),
                checkin_layer_pixels: Some(checkin),
            };
            let mut extra = PF_SmartRenderExtra {
                input: &mut input,
                cb: &mut cb,
            };
            assert_eq!(
                entry::<Dummy>(
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
    #[test]
    fn downsample_overflow() {
        assert!(Downsample::new(0, 1).is_err());
        assert!(Downsample::new(1, 0).is_err());
        assert_eq!(Downsample::new(1, 4).unwrap().dimension(13).unwrap(), 3);
        assert!(Downsample::new(2, 1)
            .unwrap()
            .dimension(usize::MAX)
            .is_err());
    }
}

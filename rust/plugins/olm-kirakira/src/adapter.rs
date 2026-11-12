//! Shared AE entry boundary. Algorithms receive only owned parameter values and
//! checked byte views. All host pointers and checkout lifetimes stay here.
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
    Color,
    Popup {
        choices: String,
        count: i16,
        default: i16,
    },
    Angle,
    Ramp,
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
    pub ramp: crate::ramp::Ramp,
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
                p.u.cd.value = PF_Pixel {
                    alpha: 255,
                    red: 255,
                    green: 255,
                    blue: 255,
                };
                p.u.cd.dephault = p.u.cd.value;
            }
            Kind::Popup {
                choices,
                count,
                default,
            } => {
                p.param_type = PF_Param_POPUP;
                text = Some(CString::new(choices.as_bytes()).map_err(|_| BAD)?);
                p.u.pd.num_choices = *count;
                p.u.pd.value = *default as _;
                p.u.pd.dephault = *default;
                p.u.pd.u.namesptr = text.as_ref().unwrap().as_ptr();
            }
            Kind::Angle => {
                p.param_type = PF_Param_ANGLE;
            }
            Kind::Ramp => {
                p.param_type = PF_Param_ARBITRARY_DATA;
                p.ui_width = 310;
                p.ui_height = 170;
                p.ui_flags = PF_PUI_CONTROL | PF_PUI_DONT_ERASE_CONTROL;
                p.u.arb_d.id = s.id as _;
                p.u.arb_d.refconPV = &RAMP_REFCON as *const u8 as *mut c_void;
                p.u.arb_d.dephault = new_ramp(i, &crate::ramp::Ramp::default())?;
            }
            Kind::GroupStart => p.param_type = PF_Param_GROUP_START,
            Kind::GroupEnd => p.param_type = PF_Param_GROUP_END,
        }
        let error = add(i.effect_ref, -1, &mut p);
        if error != 0 && matches!(s.kind, Kind::Ramp) {
            let suite = handles(i)?;
            (*suite.s).host_dispose_handle.ok_or(BAD)?(p.u.arb_d.dephault);
        }
        check(error)?;
        drop(text);
    }
    let mut ui: PF_CustomUIInfo = std::mem::zeroed();
    ui.events = PF_CustomEFlag_EFFECT;
    check(i.inter.register_ui.ok_or(BAD)?(i.effect_ref, &mut ui))?;
    o.num_params = specs.len() as i32 + 1;
    Ok(())
}

struct CheckedParam<'a> {
    i: &'a PF_InData,
    p: PF_ParamDef,
    active: bool,
}
impl CheckedParam<'_> {
    unsafe fn finish(&mut self) -> Result<()> {
        self.active = false;
        check(self.i.inter.checkin_param.ok_or(BAD)?(
            self.i.effect_ref,
            &mut self.p,
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
                ramp: crate::ramp::Ramp::default(),
            });
            continue;
        }
        let p = if smart {
            let checkout = i.inter.checkout_param.ok_or(BAD)?;
            i.inter.checkin_param.ok_or(BAD)?;
            let mut p = std::mem::zeroed();
            check(checkout(
                i.effect_ref,
                (n + 1) as _,
                i.current_time,
                i.time_step,
                i.time_scale,
                &mut p,
            ))?;
            checked = Some(CheckedParam { i, p, active: true });
            &checked.as_ref().unwrap().p
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
            ramp: crate::ramp::Ramp::default(),
        };
        match s.kind {
            Kind::Angle => v.number = p.u.ad.value as f64,
            Kind::Ramp => v.ramp = read_ramp(i, p.u.arb_d.value)?,
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
            PF_Cmd_UPDATE_PARAMS_UI => crate::ae_ui::update(i, params)?,
            PF_Cmd_EVENT => crate::ae_ui::event(
                i,
                params,
                (extra as *mut PF_EventExtra).as_mut().ok_or(BAD)?,
            )?,
            PF_Cmd_SEQUENCE_SETDOWN => crate::ae_ui::clear(i, false)?,
            PF_Cmd_GLOBAL_SETDOWN => crate::ae_ui::clear(i, true)?,
            PF_Cmd_ARBITRARY_CALLBACK => {
                arbitrary(i, (extra as *mut PF_ArbParamsExtra).as_mut().ok_or(BAD)?)?
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
                union_rect(r.result_rect, &mut eo.result_rect);
                union_rect(r.max_result_rect, &mut eo.max_result_rect);
                eo.flags |= PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS as i16;
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

// Local extension of olm-ae: host handles and arbitrary parameter lifecycle.
static RAMP_REFCON: u8 = 0;
struct Handles<'a> {
    i: &'a PF_InData,
    s: *const PF_HandleSuite1,
}
impl Drop for Handles<'_> {
    fn drop(&mut self) {
        unsafe {
            if let Some(release) = (*self.i.pica_basicP).ReleaseSuite {
                release(kPFHandleSuite.as_ptr().cast(), kPFHandleSuiteVersion1 as _);
            }
        }
    }
}
unsafe fn handles(i: &PF_InData) -> Result<Handles<'_>> {
    let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
    basic.ReleaseSuite.ok_or(BAD)?;
    let mut raw = ptr::null();
    check(basic.AcquireSuite.ok_or(BAD)?(
        kPFHandleSuite.as_ptr().cast(),
        kPFHandleSuiteVersion1 as _,
        &mut raw,
    ) as PF_Err)?;
    let h = Handles { i, s: raw.cast() };
    h.s.as_ref().ok_or(BAD)?;
    Ok(h)
}
unsafe fn new_ramp(i: &PF_InData, r: &crate::ramp::Ramp) -> Result<PF_ArbitraryH> {
    let suite = handles(i)?;
    let s = &*suite.s;
    let new = s.host_new_handle.ok_or(BAD)?;
    let lock = s.host_lock_handle.ok_or(BAD)?;
    let unlock = s.host_unlock_handle.ok_or(BAD)?;
    let dispose = s.host_dispose_handle.ok_or(BAD)?;
    let h = new(324);
    if h.is_null() {
        return Err(PF_Err_OUT_OF_MEMORY as _);
    }
    let p = lock(h);
    if p.is_null() {
        dispose(h);
        return Err(PF_Err_OUT_OF_MEMORY as _);
    }
    ptr::copy_nonoverlapping(r as *const _ as *const u8, p.cast(), 324);
    unlock(h);
    Ok(h)
}
pub(crate) unsafe fn read_ramp(i: &PF_InData, h: PF_ArbitraryH) -> Result<crate::ramp::Ramp> {
    if h.is_null() {
        return Err(BAD);
    }
    let suite = handles(i)?;
    let s = &*suite.s;
    if s.host_get_handle_size.ok_or(BAD)?(h) < 324 {
        return Err(BAD);
    }
    let unlock = s.host_unlock_handle.ok_or(BAD)?;
    let p = s.host_lock_handle.ok_or(BAD)?(h);
    if p.is_null() {
        return Err(BAD);
    }
    let r = ptr::read_unaligned(p.cast::<crate::ramp::Ramp>());
    unlock(h);
    if r.count > 16 {
        return Err(BAD);
    }
    Ok(r)
}
unsafe fn arbitrary(i: &PF_InData, e: &mut PF_ArbParamsExtra) -> Result<()> {
    use crate::ramp::Ramp;
    match e.which_function {
        PF_Arbitrary_NEW_FUNC => {
            *e.u.new_func_params.arbPH.as_mut().ok_or(BAD)? = new_ramp(i, &Ramp::default())?;
        }
        PF_Arbitrary_DISPOSE_FUNC => {
            let suite = handles(i)?;
            let h = e.u.dispose_func_params.arbH;
            if !h.is_null() {
                (*suite.s).host_dispose_handle.ok_or(BAD)?(h);
            }
            e.u.dispose_func_params.arbH = ptr::null_mut();
        }
        PF_Arbitrary_COPY_FUNC => {
            let a = e.u.copy_func_params;
            let r = read_ramp(i, a.src_arbH)?;
            *a.dst_arbPH.as_mut().ok_or(BAD)? = new_ramp(i, &r)?;
        }
        PF_Arbitrary_FLAT_SIZE_FUNC => {
            *e.u.flat_size_func_params
                .flat_data_sizePLu
                .as_mut()
                .ok_or(BAD)? = 325;
        }
        PF_Arbitrary_FLATTEN_FUNC => {
            let a = e.u.flatten_func_params;
            if a.buf_sizeLu < 325 || a.flat_dataPV.is_null() {
                return Err(BAD);
            }
            let flat = read_ramp(i, a.arbH)?.flatten().ok_or(BAD)?;
            ptr::copy_nonoverlapping(flat.as_ptr(), a.flat_dataPV.cast(), 325);
        }
        PF_Arbitrary_UNFLATTEN_FUNC => {
            let a = e.u.unflatten_func_params;
            if a.flat_dataPV.is_null() {
                return Err(BAD);
            }
            let r = Ramp::unflatten(std::slice::from_raw_parts(
                a.flat_dataPV.cast(),
                a.buf_sizeLu as usize,
            ))
            .ok_or(BAD)?;
            *a.arbPH.as_mut().ok_or(BAD)? = new_ramp(i, &r)?;
        }
        PF_Arbitrary_INTERP_FUNC => {
            let a = e.u.interp_func_params;
            let r =
                read_ramp(i, a.left_arbH)?.interpolate(&read_ramp(i, a.right_arbH)?, a.tF as f32);
            *a.interpPH.as_mut().ok_or(BAD)? = new_ramp(i, &r)?;
        }
        PF_Arbitrary_COMPARE_FUNC => {
            let a = e.u.compare_func_params;
            let same = read_ramp(i, a.a_arbH)?.equal_active(&read_ramp(i, a.b_arbH)?);
            *a.compareP.as_mut().ok_or(BAD)? = if same {
                PF_ArbCompare_EQUAL
            } else {
                PF_ArbCompare_NOT_EQUAL
            };
        }
        PF_Arbitrary_PRINT_SIZE_FUNC => {
            *e.u.print_size_func_params
                .print_sizePLu
                .as_mut()
                .ok_or(BAD)? = 0;
        }
        PF_Arbitrary_PRINT_FUNC | PF_Arbitrary_SCAN_FUNC => {}
        _ => return Err(BAD),
    }
    Ok(())
}

pub(crate) unsafe fn write_ramp(
    i: &PF_InData,
    h: PF_ArbitraryH,
    r: &crate::ramp::Ramp,
) -> Result<()> {
    if h.is_null() || r.count > 16 {
        return Err(BAD);
    }
    let suite = handles(i)?;
    let s = &*suite.s;
    if s.host_get_handle_size.ok_or(BAD)?(h) < 324 {
        return Err(BAD);
    }
    let unlock = s.host_unlock_handle.ok_or(BAD)?;
    let p = s.host_lock_handle.ok_or(BAD)?(h);
    if p.is_null() {
        return Err(BAD);
    }
    ptr::copy_nonoverlapping(r as *const _ as *const u8, p.cast(), 324);
    unlock(h);
    Ok(())
}

fn union_rect(src: PF_LRect, dst: &mut PF_LRect) {
    if dst.left >= dst.right || dst.top >= dst.bottom {
        *dst = src;
    } else if src.left < src.right && src.top < src.bottom {
        dst.left = dst.left.min(src.left);
        dst.top = dst.top.min(src.top);
        dst.right = dst.right.max(src.right);
        dst.bottom = dst.bottom.max(src.bottom);
    }
}

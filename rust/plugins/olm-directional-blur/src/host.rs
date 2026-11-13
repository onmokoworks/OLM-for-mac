//! Crate-local extension of the pilot AE entry boundary. Algorithms receive only owned parameter values and
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
    Angle,
    Fixed,
    Layer,
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
    pub layer: Option<PF_LayerDef>,
}
/// Positive rational host downsample; DirectionalBlur uses the horizontal f32 ratio.
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
}
#[derive(Clone, Copy, Debug)]
pub struct RenderContext {
    pub downsample_x: Downsample,
    pub downsample_y: Downsample,
    pub smart: bool,
    pub input_extent: [i32; 4],
    pub output_extent: [i32; 4],
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
    unsafe fn global_setup(_: &PF_InData) -> Result<()> {
        Ok(())
    }
    unsafe fn update_ui(_: &PF_InData) -> Result<()> {
        Ok(())
    }
    /// Full-size byte-copy shortcut; host retains stride and checkout ownership.
    const COPY_INTEGER_SLOTS: &'static [i32] = &[];
    fn copy_lengths(_values: &[i32], _ctx: RenderContext) -> bool {
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
        for (a, b) in p.name.iter_mut().take(31).zip(s.name.bytes()) {
            *a = b as _;
        }
        let mut text = None;
        match &s.kind {
            Kind::Angle => {
                p.param_type = PF_Param_ANGLE;
            }
            Kind::Fixed => {
                p.param_type = PF_Param_FIX_SLIDER;
                p.u.fd.valid_min = 0;
                p.u.fd.valid_max = 100 * 65536;
                p.u.fd.slider_min = 0;
                p.u.fd.slider_max = 100 * 65536;
                p.u.fd.precision = 1;
                p.u.fd.display_flags = PF_ValueDisplayFlag_PERCENT as _;
            }
            Kind::Layer => {
                p.param_type = PF_Param_LAYER;
                p.u.ld.dephault = PF_LayerDefault_NONE as _;
            }

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
            Kind::Popup { choices, default } => {
                p.param_type = PF_Param_POPUP;
                text = Some(CString::new(choices.as_bytes()).map_err(|_| BAD)?);
                p.u.pd.num_choices = 2;
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
unsafe fn values<'a, E: Effect>(
    i: &'a PF_InData,
    params: PF_ParamList,
    smart: bool,
) -> Result<(Vec<Value>, Vec<CheckedParam<'a>>)> {
    let specs = E::params();
    let mut out: Vec<Value> = Vec::with_capacity(specs.len());
    let mut guards = Vec::new();
    for (n, s) in specs.iter().enumerate() {
        let mut checked = None;
        // Topics carry no stream and must not be checked out in SmartRender.
        if matches!(s.kind, Kind::GroupStart | Kind::GroupEnd)
            || (matches!(s.kind, Kind::Layer) && (out[15].number != 3.0 || out[14].number <= 0.0))
        {
            out.push(Value {
                number: 0.0,
                layer: None,
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
            layer: None,
        };
        match s.kind {
            Kind::Angle => v.number = (p.u.ad.value >> 16) as f64,
            Kind::Fixed => v.number = (p.u.fd.value >> 16) as f64,
            Kind::Layer => v.layer = Some(p.u.ld),
            Kind::Integer { .. } => v.number = p.u.sd.value as f64,
            Kind::Float { .. } => v.number = p.u.fs_d.value,
            Kind::Popup { .. } => v.number = p.u.pd.value as f64,
            _ => {}
        }
        out.push(v);
        if let Some(c) = checked {
            guards.push(c);
        }
    }
    Ok((out, guards))
}

// Only integer controls needed to establish no-op. Each SDK record remains at
// one stack address from checkout through checkin; no parameter Vec/Box/strings.
unsafe fn probe_copy<E: Effect>(
    i: &PF_InData,
    params: PF_ParamList,
    smart: bool,
    ctx: RenderContext,
) -> Result<bool> {
    if E::COPY_INTEGER_SLOTS.len() != 4 {
        return Ok(false);
    }
    let mut lengths = [0; 4];
    for (value, &slot) in lengths.iter_mut().zip(E::COPY_INTEGER_SLOTS) {
        if smart {
            let checkout = i.inter.checkout_param.ok_or(BAD)?;
            let checkin = i.inter.checkin_param.ok_or(BAD)?;
            let mut parameter: PF_ParamDef = std::mem::zeroed();
            check(checkout(
                i.effect_ref,
                slot,
                i.current_time,
                i.time_step,
                i.time_scale,
                &mut parameter,
            ))?;
            *value = parameter.u.sd.value;
            // No fallible operation or allocation between successful checkout and checkin.
            check(checkin(i.effect_ref, &mut parameter))?;
        } else {
            if params.is_null() || slot < 1 {
                return Err(BAD);
            }
            *value = (*params.add(slot as usize)).as_ref().ok_or(BAD)?.u.sd.value;
        }
    }
    Ok(E::copy_lengths(&lengths, ctx))
}

pub(crate) unsafe fn world_layout(w: &PF_LayerDef, depth: Depth) -> Result<Layout> {
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
) -> Result<Option<(Vec<u8>, Layout)>> {
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
    let ctx = RenderContext {
        downsample_x: Downsample::new(i.downsample_x.num, i.downsample_x.den)?,
        downsample_y: Downsample::new(i.downsample_y.num, i.downsample_y.den)?,
        smart,
        input_extent: [
            a.extent_hint.left,
            a.extent_hint.top,
            a.extent_hint.right,
            a.extent_hint.bottom,
        ],
        output_extent: [
            b.extent_hint.left,
            b.extent_hint.top,
            b.extent_hint.right,
            b.extent_hint.bottom,
        ],
    };
    if probe_copy::<E>(i, params, smart, ctx)? {
        // The original calls PF_UtilCallbacks::copy with null rectangles. For
        // packed full worlds this is exactly an active-byte copy. Preserve
        // host-defined padding/crop/origin behavior by using its callback otherwise.
        let full_input = [0, 0, la.width as i32, la.height as i32];
        let full_output = [0, 0, lb.width as i32, lb.height as i32];
        let active = la.width * depth.pixel_bytes();
        if la.width == lb.width
            && la.height == lb.height
            && la.origin == lb.origin
            && la.stride == active
            && lb.stride == active
            && ctx.input_extent == full_input
            && ctx.output_extent == full_output
        {
            copy_rows(
                std::slice::from_raw_parts(a.data.cast::<u8>(), na),
                la,
                std::slice::from_raw_parts_mut(b.data.cast::<u8>(), nb),
                lb,
            );
        } else {
            host_copy(i, a, output)?;
        }
        return Ok(None);
    }
    let (v, mut guards) = values::<E>(i, params, smart)?;
    for value in &v {
        if let Some(layer) = &value.layer {
            if !layer.data.is_null() {
                let ll = world_layout(layer, depth)?;
                let ln = ll.span().map_err(|_| BAD)?;
                let lp = layer.data as usize;
                let le = lp.checked_add(ln).ok_or(BAD)?;
                if pb < le && lp < eb {
                    return Err(BAD);
                }
                if depth != Depth::U8 && layer.width == a.width && layer.height == a.height {
                    world_depth(i, input, layer)?;
                }
            }
        }
    }

    let input = View::new(std::slice::from_raw_parts(a.data.cast(), na), la).map_err(|_| BAD)?;
    // Active kernels retain transactional publication on checkin failures.
    let mut storage = vec![0u8; nb];
    let mut staged = ViewMut::new(&mut storage, lb).map_err(|_| BAD)?;
    E::render(&v, ctx, &input, &mut staged).map_err(|_| BAD)?;
    for g in &mut guards {
        g.finish()?;
    }
    Ok(Some((storage, lb)))
}

unsafe fn publish(data: &[u8], layout: Layout, output: *mut PF_LayerDef) {
    for y in 0..layout.height {
        std::ptr::copy_nonoverlapping(
            data.as_ptr().add(y * layout.stride),
            (*output).data.cast::<u8>().add(y * layout.stride),
            layout.width * layout.depth.pixel_bytes(),
        );
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
                E::global_setup(i)?;
            }
            PF_Cmd_PARAMS_SETUP => setup::<E>(i, o)?,
            PF_Cmd_UPDATE_PARAMS_UI => E::update_ui(i)?,
            PF_Cmd_RENDER => {
                if params.is_null() {
                    return Err(BAD);
                }
                let p = (*params).as_ref().ok_or(BAD)?;
                let d = world_depth(i, &p.u.ld, output)?;
                if d == Depth::F32 {
                    return Err(BAD);
                }
                if let Some((storage, layout)) = render::<E>(i, params, &p.u.ld, output, d, false)?
                {
                    publish(&storage, layout, output);
                }
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
                let staged = render::<E>(i, params, input, output, depth, true)?;
                guard.finish()?;
                if let Some((storage, layout)) = staged {
                    publish(&storage, layout, output);
                }
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
    unsafe extern "C" fn output_failure(_: PF_ProgPtr, _: *mut *mut PF_EffectWorld) -> PF_Err {
        42
    }
    unsafe extern "C" fn checkin(_: PF_ProgPtr, _: i32) -> PF_Err {
        CHECKINS.fetch_add(1, Ordering::SeqCst);
        43
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
    }
}

// Original typed copy writes active pixels only, preserving destination padding.
fn copy_rows(source: &[u8], input: Layout, destination: &mut [u8], output: Layout) {
    let active = output.width * output.depth.pixel_bytes();
    if input.stride == active && output.stride == active {
        let size = active * output.height;
        destination[..size].copy_from_slice(&source[..size]);
        return;
    }
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
            for padding in [0, 5] {
                let active = 7 * depth.pixel_bytes();
                let input = Layout {
                    width: 7,
                    height: 3,
                    stride: active + padding,
                    depth,
                    origin: (0, 0),
                };
                let output = Layout {
                    stride: active + if padding == 0 { 0 } else { 9 },
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

#[cfg(test)]
mod probe_tests {
    use super::*;
    struct State {
        slots: Vec<i32>,
        checked_in: usize,
        address: usize,
        fail_checkout: i32,
        fail_checkin: usize,
    }
    unsafe extern "C" fn checkout(
        effect: PF_ProgPtr,
        slot: i32,
        _: i32,
        _: i32,
        _: u32,
        parameter: *mut PF_ParamDef,
    ) -> PF_Err {
        let state = &mut *(effect as *mut State);
        state.slots.push(slot);
        if slot == state.fail_checkout {
            return 41;
        }
        state.address = parameter as usize;
        (*parameter).u.sd.value = 0;
        0
    }
    unsafe extern "C" fn checkin(effect: PF_ProgPtr, parameter: *mut PF_ParamDef) -> PF_Err {
        let state = &mut *(effect as *mut State);
        assert_eq!(state.address, parameter as usize);
        state.checked_in += 1;
        if state.checked_in == state.fail_checkin {
            42
        } else {
            0
        }
    }
    struct Probe;
    impl Effect for Probe {
        const NAME: &'static str = "probe";
        const VERSION: u32 = 0;
        const FLAGS: u32 = 0;
        const COPY_INTEGER_SLOTS: &'static [i32] = &[5, 6, 10, 11];
        fn params() -> Vec<Param> {
            panic!("no-op probe must not allocate metadata")
        }
        fn copy_lengths(v: &[i32], _: RenderContext) -> bool {
            v == [0, 0, 0, 0]
        }
        fn render(
            _: &[Value],
            _: RenderContext,
            _: &View<'_>,
            _: &mut ViewMut<'_>,
        ) -> olm_core::Result<()> {
            unreachable!()
        }
    }
    #[test]
    fn probe_preserves_checkout_address_and_failure_checkins() {
        for (fail_checkout, fail_checkin, want, checks) in
            [(0, 0, Ok(true), 4), (10, 0, Err(41), 2), (0, 2, Err(42), 2)]
        {
            let mut state = State {
                slots: vec![],
                checked_in: 0,
                address: 0,
                fail_checkout,
                fail_checkin,
            };
            unsafe {
                let mut i: PF_InData = std::mem::zeroed();
                i.effect_ref = (&mut state as *mut State).cast();
                i.inter.checkout_param = Some(checkout);
                i.inter.checkin_param = Some(checkin);
                let ctx = RenderContext {
                    downsample_x: Downsample::new(1, 1).unwrap(),
                    downsample_y: Downsample::new(1, 1).unwrap(),
                    smart: true,
                    input_extent: [0; 4],
                    output_extent: [0; 4],
                };
                assert_eq!(probe_copy::<Probe>(&i, ptr::null_mut(), true, ctx), want);
            }
            assert_eq!(state.checked_in, checks);
            assert_eq!(state.slots, &[5, 6, 10, 11][..state.slots.len()]);
        }
    }
}

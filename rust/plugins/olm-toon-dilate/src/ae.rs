//! Local adapter preserves ToonDilate's no-op Classic selector, optional pixel
//! checkin lifecycle, zero downsample fallback, and extra-pixels pre-render flag.
#![allow(non_upper_case_globals)]
use crate::algorithm;
use olm_ae::{sys::*, Effect, Kind, Param, BAD};
use olm_core::{allocate, Budget, Depth, Error, Layout};
use std::{ffi::c_void, ptr};
type Result<T> = std::result::Result<T, PF_Err>;

struct Toon;
impl Effect for Toon {
    const NAME: &'static str = "OLM Toon Dilate";
    const MATCH_NAME: &'static str = "ADBE OLMToonDilate";
    const VERSION: u32 = 0x88800;
    const FLAGS: u32 = 0x02000044;
    const FLAGS2: u32 = 0x08021400;
    fn params() -> Vec<Param> {
        vec![Param {
            id: 1,
            name: "Search Radius".into(),
            flags: 0,
            kind: Kind::Float {
                min: 0.0,
                max: 100.0,
                slider_min: 0.0,
                slider_max: 100.0,
                default: 2.0,
                precision: 1,
            },
        }]
    }
    fn render(
        _: &[olm_ae::Value],
        _: olm_ae::RenderContext,
        _: &olm_core::View<'_>,
        _: &mut olm_core::ViewMut<'_>,
    ) -> olm_core::Result<()> {
        Err(Error::Unsupported)
    }
}
fn check(e: PF_Err) -> Result<()> {
    if e == 0 {
        Ok(())
    } else {
        Err(e)
    }
}
fn core_error(e: Error) -> PF_Err {
    match e {
        Error::Allocation | Error::Overflow => PF_Err_OUT_OF_MEMORY as _,
        _ => BAD,
    }
}
fn union(a: PF_LRect, b: PF_LRect) -> PF_LRect {
    if a.left == a.right || a.top == a.bottom {
        return b;
    }
    if b.left == b.right || b.top == b.bottom {
        return a;
    }
    PF_LRect {
        left: a.left.min(b.left),
        top: a.top.min(b.top),
        right: a.right.max(b.right),
        bottom: a.bottom.max(b.bottom),
    }
}
unsafe fn pre_render(i: &PF_InData, extra: *mut c_void) -> Result<()> {
    let e = (extra as *mut PF_PreRenderExtra).as_mut().ok_or(BAD)?;
    let ei = e.input.as_ref().ok_or(BAD)?;
    let eo = e.output.as_mut().ok_or(BAD)?;
    let cb = e.cb.as_ref().ok_or(BAD)?;
    let mut request = ei.output_request;
    request.preserve_rgb_of_zero_alpha = 0;
    let mut r = std::mem::zeroed();
    check(cb.checkout_layer.ok_or(BAD)?(
        i.effect_ref,
        0,
        0,
        &request,
        i.current_time,
        i.time_step,
        i.time_scale,
        &mut r,
    ))?;
    eo.result_rect = union(eo.result_rect, r.result_rect);
    eo.max_result_rect = union(eo.max_result_rect, r.max_result_rect);
    eo.flags |= PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS as i16;
    // C++ stores ref_width but its SmartRender never consumes it. No allocation
    // or pre_render_data is needed for the identical numerical contract.
    Ok(())
}
fn layout(w: &PF_LayerDef, depth: Depth) -> Result<Layout> {
    if w.width <= 0 || w.height <= 0 || w.rowbytes <= 0 || w.data.is_null() {
        return Err(BAD);
    }
    // Origins are deliberately ignored by the original worker.
    let l = Layout {
        width: w.width as _,
        height: w.height as _,
        stride: w.rowbytes as _,
        depth,
        origin: (0, 0),
    };
    l.span().map_err(core_error)?;
    Ok(l)
}
unsafe fn formats(
    i: &PF_InData,
    a: *const PF_LayerDef,
    b: *const PF_LayerDef,
    expected: PF_PixelFormat,
) -> Result<()> {
    let basic = i.pica_basicP.as_ref().ok_or(BAD)?;
    let acquire = basic.AcquireSuite.ok_or(BAD)?;
    let release = basic.ReleaseSuite.ok_or(BAD)?;
    let mut raw = ptr::null();
    check(acquire(kPFWorldSuite.as_ptr().cast(), 2, &mut raw) as _)?;
    let result = (|| {
        let s = (raw as *const PF_WorldSuite2).as_ref().ok_or(BAD)?;
        let get = s.PF_GetPixelFormat.ok_or(BAD)?;
        let (mut af, mut bf) = (0, 0);
        check(get(a, &mut af))?;
        check(get(b, &mut bf))?;
        if af != expected || bf != expected {
            Err(BAD)
        } else {
            Ok(())
        }
    })();
    let cleanup = check(release(kPFWorldSuite.as_ptr().cast(), 2) as _);
    result.and(cleanup)
}
unsafe fn smart_render(i: &PF_InData, extra: *mut c_void) -> Result<()> {
    i.pica_basicP.as_ref().ok_or(BAD)?;
    let checkout_param = i.inter.checkout_param.ok_or(BAD)?;
    let checkin_param = i.inter.checkin_param.ok_or(BAD)?;
    let e = (extra as *const PF_SmartRenderExtra).as_ref().ok_or(BAD)?;
    let ei = e.input.as_ref().ok_or(BAD)?;
    let cb = e.cb.as_ref().ok_or(BAD)?;
    let checkout = cb.checkout_layer_pixels.ok_or(BAD)?;
    let output_checkout = cb.checkout_output.ok_or(BAD)?;
    let mut input = ptr::null_mut();
    check(checkout(i.effect_ref, 0, &mut input))?;
    let mut output = ptr::null_mut();
    check(output_checkout(i.effect_ref, &mut output))?;
    let a = input.as_ref().ok_or(BAD)?;
    let b = output.as_ref().ok_or(BAD)?;
    let needs_checkin = a.width != b.width
        || a.height != b.height
        || a.origin_x != b.origin_x
        || a.origin_y != b.origin_y;
    let result = (|| -> Result<(Vec<u8>, usize)> {
        let mut param = std::mem::zeroed();
        check(checkout_param(
            i.effect_ref,
            1,
            i.current_time,
            i.time_step,
            i.time_scale,
            &mut param,
        ))?;
        let radius = param.u.fs_d.value;
        check(checkin_param(i.effect_ref, &mut param))?;
        let (depth, expected) = match ei.bitdepth {
            8 => (Depth::U8, PF_PixelFormat_ARGB32),
            16 => (Depth::U16, PF_PixelFormat_ARGB64),
            32 => (Depth::F32, PF_PixelFormat_ARGB128),
            _ => return Err(BAD),
        };
        formats(i, input, output, expected)?;
        let il = layout(a, depth)?;
        let ol = layout(b, depth)?;
        let ni = il.span().map_err(core_error)?;
        let no = ol.span().map_err(core_error)?;
        let pa = a.data as usize;
        let pb = b.data as usize;
        if pa < pb.checked_add(no).ok_or(BAD)? && pb < pa.checked_add(ni).ok_or(BAD)? {
            return Err(BAD);
        }
        // Both axes must be valid even though only X scales the radius.
        algorithm::effective_radius(0.0, i.downsample_y.num, i.downsample_y.den)
            .map_err(core_error)?;
        let r = algorithm::effective_radius(radius, i.downsample_x.num, i.downsample_x.den)
            .map_err(core_error)?;
        let mut staged =
            allocate(no, 0u8, &mut Budget::new(isize::MAX as usize)).map_err(core_error)?;
        staged.copy_from_slice(std::slice::from_raw_parts(b.data.cast(), no));
        algorithm::render_staged(
            std::slice::from_raw_parts(a.data.cast(), ni),
            il,
            &mut staged,
            ol,
            r,
        )
        .map_err(core_error)?;
        Ok((staged, no))
    })();
    let cleanup = if needs_checkin {
        cb.checkin_layer_pixels
            .ok_or(BAD)
            .and_then(|f| check(f(i.effect_ref, 0)))
    } else {
        Ok(())
    };
    let (staged, no) = result?;
    cleanup?;
    ptr::copy_nonoverlapping(staged.as_ptr(), b.data.cast(), no);
    Ok(())
}
unsafe fn entry(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut c_void,
) -> PF_Err {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| -> Result<()> {
        match cmd {
            PF_Cmd_PARAMS_SETUP => {
                let input = i.as_ref().ok_or(BAD)?;
                let mut ui: PF_CustomUIInfo = std::mem::zeroed();
                // Original AEX inspection registers EFFECT (4) before adding
                // Search Radius. The Mac source and shared pilot omit this.
                ui.events = PF_CustomEFlag_EFFECT as _;
                check(input.inter.register_ui.ok_or(BAD)?(
                    input.effect_ref,
                    &mut ui,
                ))?;
                check(olm_ae::entry::<Toon>(cmd, i, o, p, w, e))
            }
            PF_Cmd_RENDER => Ok(()), // Public Windows and C++ Classic owners do nothing.
            PF_Cmd_SMART_PRE_RENDER => pre_render(i.as_ref().ok_or(BAD)?, e),
            PF_Cmd_SMART_RENDER => {
                o.as_ref().ok_or(BAD)?;
                smart_render(i.as_ref().ok_or(BAD)?, e)
            }
            _ => check(olm_ae::entry::<Toon>(cmd, i, o, p, w, e)),
        }
    }))
    .unwrap_or(Err(PF_Err_INTERNAL_STRUCT_DAMAGED as _))
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
#[cfg(target_os = "windows")]
#[no_mangle]
pub unsafe extern "C" fn entry_point(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut c_void,
) -> PF_Err {
    entry(cmd, i, o, p, w, e)
}
#[cfg(target_os = "macos")]
#[no_mangle]
pub unsafe extern "C" fn PluginDataEntryFunction2(
    p: PF_PluginDataPtr,
    cb: PF_PluginDataCB2,
    _: *const SPBasicSuite,
    _: *const std::ffi::c_char,
    _: *const std::ffi::c_char,
) -> PF_Err {
    let Some(cb) = cb else {
        return BAD;
    };
    cb(
        p,
        c"OLM Toon Dilate".as_ptr().cast(),
        c"ADBE OLMToonDilate".as_ptr().cast(),
        c"OLM Plug-ins".as_ptr().cast(),
        c"EffectMain".as_ptr().cast(),
        i32::from_be_bytes(*b"eFKT"),
        13,
        28,
        0,
        c"https://olm.co.jp/".as_ptr().cast(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::cell::RefCell;
    #[derive(Default)]
    struct Host {
        input: usize,
        output: usize,
        suite: usize,
        format: PF_PixelFormat,
        radius: f64,
        param_in: usize,
        pixels_in: usize,
        param_error: PF_Err,
        pixel_error: PF_Err,
        output_error: PF_Err,
        releases: usize,
        pre_error: PF_Err,
    }
    thread_local! { static HOST: RefCell<Host> = RefCell::new(Host::default()); }
    unsafe extern "C" fn pixels(_: PF_ProgPtr, _: i32, p: *mut *mut PF_EffectWorld) -> PF_Err {
        HOST.with(|h| *p = h.borrow().input as _);
        0
    }
    unsafe extern "C" fn output(_: PF_ProgPtr, p: *mut *mut PF_EffectWorld) -> PF_Err {
        HOST.with(|h| {
            let h = h.borrow();
            *p = h.output as _;
            h.output_error
        })
    }
    unsafe extern "C" fn pixel_in(_: PF_ProgPtr, _: i32) -> PF_Err {
        HOST.with(|h| {
            let mut h = h.borrow_mut();
            h.pixels_in += 1;
            h.pixel_error
        })
    }
    unsafe extern "C" fn param(
        _: PF_ProgPtr,
        slot: i32,
        _: i32,
        _: i32,
        _: u32,
        p: *mut PF_ParamDef,
    ) -> PF_Err {
        assert_eq!(slot, 1);
        HOST.with(|h| (*p).u.fs_d.value = h.borrow().radius);
        0
    }
    unsafe extern "C" fn param_in(_: PF_ProgPtr, _: *mut PF_ParamDef) -> PF_Err {
        HOST.with(|h| {
            let mut h = h.borrow_mut();
            h.param_in += 1;
            h.param_error
        })
    }
    unsafe extern "C" fn acquire(_: *const std::ffi::c_char, _: i32, p: *mut *const c_void) -> i32 {
        HOST.with(|h| *p = h.borrow().suite as _);
        0
    }
    unsafe extern "C" fn release(_: *const std::ffi::c_char, _: i32) -> i32 {
        HOST.with(|h| h.borrow_mut().releases += 1);
        0
    }
    unsafe extern "C" fn format(_: *const PF_EffectWorld, p: *mut PF_PixelFormat) -> PF_Err {
        HOST.with(|h| *p = h.borrow().format);
        0
    }
    unsafe fn smart_fixture(
        depth: i16,
        cropped: bool,
        optional: bool,
        configure: impl FnOnce(&mut Host),
    ) -> (PF_Err, Vec<u8>, Vec<u8>) {
        let (bpp, fmt) = match depth {
            8 => (4, PF_PixelFormat_ARGB32),
            16 => (8, PF_PixelFormat_ARGB64),
            _ => (16, PF_PixelFormat_ARGB128),
        };
        let mut src = vec![0u8; bpp * 3 + 3];
        let seed: Vec<u8> = match depth {
            8 => vec![255, 21, 43, 65],
            16 => [32768u16, 21, 43, 65]
                .into_iter()
                .flat_map(u16::to_ne_bytes)
                .collect(),
            _ => [1.0f32, -0.0, 4.25, -2.0]
                .into_iter()
                .flat_map(f32::to_ne_bytes)
                .collect(),
        };
        src[..bpp].copy_from_slice(&seed);
        let mut dst = vec![0x9b; bpp * 3 + 7];
        let before = dst.clone();
        let mut a: PF_LayerDef = std::mem::zeroed();
        a.data = src.as_mut_ptr().cast();
        a.width = 3;
        a.height = 1;
        a.rowbytes = src.len() as _;
        let mut b: PF_LayerDef = std::mem::zeroed();
        b.data = dst.as_mut_ptr().cast();
        b.width = if cropped { 2 } else { 3 };
        b.height = 1;
        b.rowbytes = dst.len() as _;
        let mut suite: PF_WorldSuite2 = std::mem::zeroed();
        suite.PF_GetPixelFormat = Some(format);
        HOST.with(|h| {
            let mut host = Host {
                input: &mut a as *mut _ as usize,
                output: &mut b as *mut _ as usize,
                suite: &mut suite as *mut _ as usize,
                format: fmt,
                radius: 2.0,
                ..Default::default()
            };
            configure(&mut host);
            *h.borrow_mut() = host;
        });
        let mut basic: SPBasicSuite = std::mem::zeroed();
        basic.AcquireSuite = Some(acquire);
        basic.ReleaseSuite = Some(release);
        let mut i: PF_InData = std::mem::zeroed();
        i.pica_basicP = &mut basic;
        i.inter.checkout_param = Some(param);
        i.inter.checkin_param = Some(param_in);
        // (0,0) downsample must retain the C++ fallback.
        let mut o = std::mem::zeroed();
        let mut si: PF_SmartRenderInput = std::mem::zeroed();
        si.bitdepth = depth;
        let mut cb = PF_SmartRenderCallbacks {
            checkout_layer_pixels: Some(pixels),
            checkout_output: Some(output),
            checkin_layer_pixels: if optional { Some(pixel_in) } else { None },
        };
        let mut e = PF_SmartRenderExtra {
            input: &mut si,
            cb: &mut cb,
        };
        let err = EffectMain(
            PF_Cmd_SMART_RENDER,
            &mut i,
            &mut o,
            ptr::null_mut(),
            ptr::null_mut(),
            (&mut e as *mut PF_SmartRenderExtra).cast(),
        );
        if err == 0 {
            for x in 0..b.width as usize {
                assert_eq!(&dst[x * bpp..(x + 1) * bpp], seed);
            }
            assert_eq!(
                &dst[b.width as usize * bpp..],
                &before[b.width as usize * bpp..]
            );
        }
        assert_eq!(&src[..bpp], seed);
        (err, dst, before)
    }
    #[test]
    fn smart_lifecycle_and_atomic_commit() {
        unsafe {
            for depth in [8, 16, 32] {
                assert_eq!(smart_fixture(depth, false, false, |_| {}).0, 0);
                HOST.with(|h| {
                    let h = h.borrow();
                    assert_eq!((h.param_in, h.pixels_in, h.releases), (1, 0, 1));
                });
                assert_eq!(smart_fixture(depth, true, true, |_| {}).0, 0);
                HOST.with(|h| assert_eq!(h.borrow().pixels_in, 1));
                for failure in 0..5 {
                    let (err, dst, before) = smart_fixture(depth, true, true, |h| match failure {
                        0 => h.param_error = 41,
                        1 => h.pixel_error = 42,
                        2 => h.radius = f64::NAN,
                        3 => h.format = 0,
                        _ => h.output_error = 43,
                    });
                    assert_ne!(err, 0);
                    assert_eq!(dst, before);
                    HOST.with(|h| {
                        assert_eq!(h.borrow().pixels_in, if failure == 4 { 0 } else { 1 })
                    });
                }
                let (err, dst, before) = smart_fixture(depth, true, false, |_| {});
                assert_eq!(err, BAD);
                assert_eq!(dst, before);
            }
        }
    }
    unsafe extern "C" fn layer(
        _: PF_ProgPtr,
        _: i32,
        _: i32,
        req: *const PF_RenderRequest,
        _: i32,
        _: i32,
        _: u32,
        result: *mut PF_CheckoutResult,
    ) -> PF_Err {
        assert_eq!((*req).preserve_rgb_of_zero_alpha, 0);
        assert_eq!((*req).rect.left, 2);
        (*result).result_rect = PF_LRect {
            left: 1,
            top: 2,
            right: 8,
            bottom: 9,
        };
        (*result).max_result_rect = PF_LRect {
            left: 0,
            top: 0,
            right: 10,
            bottom: 10,
        };
        HOST.with(|h| h.borrow().pre_error)
    }
    #[test]
    fn prerender_preserves_request_and_unions_rectangles() {
        unsafe {
            for error in [0, 27] {
                HOST.with(|h| {
                    *h.borrow_mut() = Host {
                        pre_error: error,
                        ..Default::default()
                    }
                });
                let mut i: PF_InData = std::mem::zeroed();
                let mut o = std::mem::zeroed();
                let mut pi: PF_PreRenderInput = std::mem::zeroed();
                pi.output_request.rect.left = 2;
                pi.output_request.preserve_rgb_of_zero_alpha = 1;
                let mut po: PF_PreRenderOutput = std::mem::zeroed();
                po.result_rect = PF_LRect {
                    left: 3,
                    top: 3,
                    right: 12,
                    bottom: 12,
                };
                let mut cb: PF_PreRenderCallbacks = std::mem::zeroed();
                cb.checkout_layer = Some(layer);
                let mut extra = PF_PreRenderExtra {
                    input: &mut pi,
                    output: &mut po,
                    cb: &mut cb,
                };
                assert_eq!(
                    EffectMain(
                        PF_Cmd_SMART_PRE_RENDER,
                        &mut i,
                        &mut o,
                        ptr::null_mut(),
                        ptr::null_mut(),
                        (&mut extra as *mut PF_PreRenderExtra).cast()
                    ),
                    error
                );
                assert_eq!(po.result_rect.left, if error == 0 { 1 } else { 3 });
                assert_eq!(po.result_rect.right, 12);
                assert_eq!(
                    po.flags & PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS as i16,
                    if error == 0 { 1 } else { 0 }
                );
                assert_eq!(pi.output_request.preserve_rgb_of_zero_alpha, 1);
            }
        }
    }
    #[test]
    fn classic_is_noop() {
        unsafe {
            assert_eq!(
                EffectMain(
                    PF_Cmd_RENDER,
                    ptr::null_mut(),
                    ptr::null_mut(),
                    ptr::null_mut(),
                    ptr::null_mut(),
                    ptr::null_mut()
                ),
                0
            );
        }
    }
    unsafe extern "C" fn register_ui(_: PF_ProgPtr, ui: *mut PF_CustomUIInfo) -> PF_Err {
        assert_eq!((*ui).events, PF_CustomEFlag_EFFECT as PF_CustomEventFlags);
        assert_eq!((*ui).comp_ui_width, 0);
        assert_eq!((*ui).layer_ui_height, 0);
        HOST.with(|h| h.borrow_mut().pixels_in += 1);
        0
    }
    unsafe extern "C" fn add_param(_: PF_ProgPtr, slot: i32, p: *mut PF_ParamDef) -> PF_Err {
        HOST.with(|h| assert_eq!(h.borrow().pixels_in, 1));
        assert_eq!(slot, -1);
        assert_eq!((*p).uu.id, 1);
        assert_eq!((*p).param_type, PF_Param_FLOAT_SLIDER);
        assert_eq!((*p).flags, 0);
        assert_eq!((*p).ui_flags, 0);
        let f = (*p).u.fs_d;
        assert_eq!((f.value, f.dephault), (2.0, 2.0));
        assert_eq!(
            (f.valid_min, f.valid_max, f.slider_min, f.slider_max),
            (0.0, 100.0, 0.0, 100.0)
        );
        assert_eq!(f.precision, 1);
        assert_eq!(f.curve_tolerance, 0.0);
        0
    }
    #[test]
    fn original_parameter_registration() {
        unsafe {
            HOST.with(|h| *h.borrow_mut() = Host::default());
            let mut i: PF_InData = std::mem::zeroed();
            let mut o: PF_OutData = std::mem::zeroed();
            i.inter.register_ui = Some(register_ui);
            i.inter.add_param = Some(add_param);
            assert_eq!(
                EffectMain(
                    PF_Cmd_PARAMS_SETUP,
                    &mut i,
                    &mut o,
                    ptr::null_mut(),
                    ptr::null_mut(),
                    ptr::null_mut()
                ),
                0
            );
            assert_eq!(o.num_params, 2);
        }
    }
}

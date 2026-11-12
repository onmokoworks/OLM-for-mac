//! Local pilot boundary: retained-fixture admission and transactional output.
#![allow(non_upper_case_globals)]
use super::*;
use olm_core::{Depth,Layout,View,ViewMut};
use olm_ae::Downsample;
type Result<T> = olm_ae::Result<T>;
fn check(e:PF_Err)->Result<()>{if e==0{Ok(())}else{Err(e)}}
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
    active:bool,
}
impl ColorSuite<'_>{
    unsafe fn finish(&mut self)->Result<()>{self.active=false;check((*self.i.pica_basicP).ReleaseSuite.ok_or(BAD)?(kPFColorParamSuite.as_ptr().cast(),1) as PF_Err)}
}
impl Drop for ColorSuite<'_> {
    fn drop(&mut self) {
        unsafe {
            if self.active {let _=self.finish();}
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
    let mut suite = ColorSuite { i, p: raw.cast(),active:true };
    let color = (*suite.p.as_ref().ok_or(BAD)?)
        .PF_GetFloatingPointColorFromColorDef
        .ok_or(BAD)?;
    let specs = E::params();
    let mut out:Vec<Value> = Vec::with_capacity(specs.len());
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
        };
        match s.kind {
            Kind::Integer { .. } => v.number = p.u.sd.value as f64,
            Kind::Float { .. } => v.number = p.u.fs_d.value,
            Kind::Checkbox(_) => v.number = p.u.bd.value as f64,
            Kind::Popup { .. } => v.number = p.u.pd.value as f64,
            Kind::Color => {
                let mut c = std::mem::zeroed();
                // Original reads suite floats only for enabled key/active gamma colors.
                if (n==1 && out[0].number!=0.0) || (n>=10 && out[7].number==2.0 && n-10<(out[9].number as usize).min(5)) {
                    check(color(i.effect_ref, p, &mut c))?;
                }
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
    suite.finish()?;
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
    // Caller validates host-owned worlds before replacing output storage.
    // PF_GetPixelFormat may reject a stack copy of a host world.
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
    if crate::admission::retained(&v, a, depth)? {
        let flags=if depth==Depth::U8{0}else{PF_WorldFlag_DEEP as i32};
        if a.rowbytes as usize!=la.width*depth.pixel_bytes() || a.world_flags!=flags || b.world_flags!=flags || i.output_origin_x!=0 || i.output_origin_y!=0 || i.downsample_x.num!=1 || i.downsample_x.den!=1 || i.downsample_y.num!=1 || i.downsample_y.den!=1{return Err(BAD);}
    }
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
pub(super) unsafe fn entry<E: Effect>(
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
                if world_depth(i,input,output)?!=depth{return Err(BAD);}
                let original=output.as_ref().ok_or(BAD)?;
                let layout=world_layout(original,depth)?;
                let il=world_layout(input.as_ref().ok_or(BAD)?,depth)?;
                if il.width!=layout.width || il.height!=layout.height || il.origin!=layout.origin || il.width>8192 || il.height>8192 || il.stride.checked_mul(il.height).ok_or(BAD)?>i32::MAX as usize || layout.stride.checked_mul(layout.height).ok_or(BAD)?>i32::MAX as usize{return Err(BAD);}
                let ib=(*input).data as usize;let ob=original.data as usize;
                let ie=ib.checked_add(il.span().map_err(|_|BAD)?).ok_or(BAD)?;
                let oe=ob.checked_add(layout.span().map_err(|_|BAD)?).ok_or(BAD)?;
                if ib<oe && ob<ie{return Err(BAD);}
                let len=layout.span().map_err(|_|BAD)?;
                let mut staged=Vec::new();staged.try_reserve_exact(len).map_err(|_|BAD)?;staged.resize(len,0u8);
                let mut staged_world=*original;staged_world.data=staged.as_mut_ptr().cast();
                // Keep the caller's padding; publish active rows only after checkout cleanup succeeds.
                render::<E>(i, params, input, &mut staged_world, depth, true)?;
                guard.finish()?;
                for y in 0..layout.height {
                    ptr::copy_nonoverlapping(staged.as_ptr().add(y*layout.stride),(original.data as *mut u8).add(y*layout.stride),layout.width*depth.pixel_bytes());
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
        assert_eq!(Downsample::new(1, 4).unwrap().dimension(13).unwrap(), 3);
        assert!(Downsample::new(2, 1)
            .unwrap()
            .dimension(usize::MAX)
            .is_err());
    }

    struct Host {
        input:PF_EffectWorld,output:PF_EffectWorld,input_bytes:[u8;4],output_bytes:[u8;4],
        world_suite:PF_WorldSuite2,color_suite:PF_ColorParamSuite1,
        checkin_error:PF_Err,checkins:usize,acquires:usize,releases:usize,formats:usize,
    }
    thread_local!{static HOST:std::cell::Cell<*mut Host>=const{std::cell::Cell::new(ptr::null_mut())};}
    unsafe extern "C" fn host_acquire(name:*const std::ffi::c_char,_version:i32,out:*mut *const c_void)->i32{
        HOST.with(|cell|{let h=&mut *cell.get();h.acquires+=1;
            *out=if std::ffi::CStr::from_ptr(name).to_bytes_with_nul()==kPFWorldSuite{(&h.world_suite as *const PF_WorldSuite2).cast()}else{(&h.color_suite as *const PF_ColorParamSuite1).cast()};0
        })
    }
    unsafe extern "C" fn host_release(_name:*const std::ffi::c_char,_version:i32)->i32{HOST.with(|cell|{(*cell.get()).releases+=1;});0}
    unsafe extern "C" fn host_format(world:*const PF_EffectWorld,out:*mut PF_PixelFormat)->PF_Err{
        HOST.with(|cell|{let h=&mut *cell.get();h.formats+=1;
            if !std::ptr::eq(world,&h.input) && !std::ptr::eq(world,&h.output){return 44;}
            *out=PF_PixelFormat_ARGB32;0
        })
    }
    unsafe extern "C" fn host_color(_:PF_ProgPtr,_:*const PF_ParamDef,_:*mut PF_PixelFloat)->PF_Err{45}
    unsafe extern "C" fn host_input(effect:PF_ProgPtr,_:i32,out:*mut *mut PF_EffectWorld)->PF_Err{*out=&mut (*(effect as *mut Host)).input;0}
    unsafe extern "C" fn host_output(effect:PF_ProgPtr,out:*mut *mut PF_EffectWorld)->PF_Err{*out=&mut (*(effect as *mut Host)).output;0}
    unsafe extern "C" fn host_checkin(effect:PF_ProgPtr,_:i32)->PF_Err{let h=&mut *(effect as *mut Host);h.checkins+=1;h.checkin_error}
    struct Paint;
    impl Effect for Paint {
        const NAME:&'static str="test";const VERSION:u32=0;const FLAGS:u32=0;
        fn params()->Vec<Param>{vec![]}
        fn render(_:&[Value],_:RenderContext,_:&View<'_>,out:&mut ViewMut<'_>)->olm_core::Result<()>{out.set(0,0,olm_core::Pixel::U8([255,11,22,33]))}
    }
    #[test]
    fn host_world_validation_and_transactional_publication(){unsafe{
        for late_error in [0,43] {
            let mut h:Box<Host>=Box::new(std::mem::zeroed());h.checkin_error=late_error;
            h.input_bytes=[255,1,2,3];h.output_bytes=[7;4];
            h.input.width=1;h.input.height=1;h.input.rowbytes=4;h.input.data=h.input_bytes.as_mut_ptr().cast();
            h.output=h.input;h.output.data=h.output_bytes.as_mut_ptr().cast();
            h.world_suite.PF_GetPixelFormat=Some(host_format);h.color_suite.PF_GetFloatingPointColorFromColorDef=Some(host_color);
            HOST.with(|cell|cell.set(&mut *h));
            let mut basic:SPBasicSuite=std::mem::zeroed();basic.AcquireSuite=Some(host_acquire);basic.ReleaseSuite=Some(host_release);
            let mut i:PF_InData=std::mem::zeroed();i.effect_ref=(&mut *h as *mut Host).cast();i.pica_basicP=&mut basic;
            i.downsample_x.num=1;i.downsample_x.den=1;i.downsample_y=i.downsample_x;
            let mut o=std::mem::zeroed();let mut input:PF_SmartRenderInput=std::mem::zeroed();input.bitdepth=8;
            let mut cb=PF_SmartRenderCallbacks{checkout_layer_pixels:Some(host_input),checkout_output:Some(host_output),checkin_layer_pixels:Some(host_checkin)};
            let mut extra=PF_SmartRenderExtra{input:&mut input,cb:&mut cb};
            let error=entry::<Paint>(PF_Cmd_SMART_RENDER,&mut i,&mut o,ptr::null_mut(),ptr::null_mut(),(&mut extra as *mut PF_SmartRenderExtra).cast());
            assert_eq!(error,late_error);assert_eq!(h.checkins,1);assert_eq!(h.formats,2);assert_eq!(h.acquires,h.releases);
            assert_eq!(h.output_bytes,if late_error==0{[255,11,22,33]}else{[7;4]});assert_eq!(h.input_bytes,[255,1,2,3]);
            HOST.with(|cell|cell.set(ptr::null_mut()));
        }
    }}
}

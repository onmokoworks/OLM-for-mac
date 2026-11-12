//! AE Drawbot adapter. Host suites/objects are released on every return path.
#![allow(non_upper_case_globals)]
use crate::{
    adapter::{read_ramp, write_ramp, Result, BAD},
    editor as ed,
};
use olm_ae::sys::*;
use std::{
    collections::HashMap,
    ffi::c_void,
    ptr,
    sync::{LazyLock, Mutex},
};
struct Suite<'a, T> {
    basic: &'a SPBasicSuite,
    name: &'static [u8],
    version: i32,
    p: *const T,
}
impl<T> std::ops::Deref for Suite<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        unsafe { &*self.p }
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
unsafe fn suite<'a, T>(
    i: &'a PF_InData,
    name: &'static [u8],
    version: u32,
) -> Result<Suite<'a, T>> {
    let b = i.pica_basicP.as_ref().ok_or(BAD)?;
    b.ReleaseSuite.ok_or(BAD)?;
    let mut p: *const c_void = ptr::null();
    ok(b.AcquireSuite.ok_or(BAD)?(
        name.as_ptr().cast(),
        version as _,
        &mut p,
    ))?;
    let guard = Suite {
        basic: b,
        name,
        version: version as _,
        p: p.cast(),
    };
    if p.is_null() {
        return Err(BAD);
    }
    Ok(guard)
}
fn ok(e: i32) -> Result<()> {
    if e == 0 {
        Ok(())
    } else {
        Err(e)
    }
}
struct Object<'a> {
    release: unsafe extern "C" fn(DRAWBOT_ObjectRef) -> SPErr,
    p: DRAWBOT_ObjectRef,
    _life: std::marker::PhantomData<&'a ()>,
}
impl Object<'_> {
    fn new(s: &DRAWBOT_SupplierSuite1) -> Result<Object<'_>> {
        Ok(Object {
            release: s.ReleaseObject.ok_or(BAD)?,
            p: ptr::null_mut(),
            _life: std::marker::PhantomData,
        })
    }
}
impl Drop for Object<'_> {
    fn drop(&mut self) {
        unsafe {
            if !self.p.is_null() {
                (self.release)(self.p);
            }
        }
    }
}
unsafe fn draw(i: &PF_InData, e: &PF_EventExtra, commands: &[ed::Command]) -> Result<()> {
    let ui = suite::<PF_EffectCustomUISuite2>(
        i,
        kPFEffectCustomUISuite,
        kPFEffectCustomUISuiteVersion2,
    )?;
    let mut drawing = ptr::null_mut();
    ok(ui.PF_GetDrawingReference.ok_or(BAD)?(
        e.contextH,
        &mut drawing,
    ))?;
    if drawing.is_null() {
        return Ok(());
    }
    let d =
        suite::<DRAWBOT_DrawbotSuite1>(i, kDRAWBOT_DrawSuite, kDRAWBOT_DrawSuite_VersionCurrent)?;
    let mut supplier = ptr::null_mut();
    let mut surface = ptr::null_mut();
    ok(d.GetSupplier.ok_or(BAD)?(drawing, &mut supplier))?;
    ok(d.GetSurface.ok_or(BAD)?(drawing, &mut surface))?;
    let sup = suite::<DRAWBOT_SupplierSuite1>(
        i,
        kDRAWBOT_SupplierSuite,
        kDRAWBOT_SupplierSuite_VersionCurrent,
    )?;
    let surf = suite::<DRAWBOT_SurfaceSuite2>(
        i,
        kDRAWBOT_SurfaceSuite,
        kDRAWBOT_SurfaceSuite_VersionCurrent,
    )?;
    let path_suite =
        suite::<DRAWBOT_PathSuite1>(i, kDRAWBOT_PathSuite, kDRAWBOT_PathSuite_VersionCurrent)?;
    let app = suite::<PFAppSuite6>(i, kPFAppSuite, kPFAppSuiteVersion6)?;
    let ox = e.effect_win.current_frame.left as f32;
    let oy = e.effect_win.current_frame.top as f32;
    let mut shared = Object::new(&sup)?;
    let mut theme = HashMap::<i32, [f32; 4]>::new();
    for c in commands {
        let mut rgba = c.color.rgba;
        if c.color.role != 0 {
            rgba = *theme.get(&c.color.role).ok_or(BAD)?;
            for v in &mut rgba[..3] {
                *v *= c.color.factor;
            }
        }
        let color = DRAWBOT_ColorRGBA {
            red: rgba[0],
            green: rgba[1],
            blue: rgba[2],
            alpha: rgba[3],
        };
        let [x, y, w, h] = c.rect;
        let r = DRAWBOT_RectF32 {
            left: x + ox,
            top: y + oy,
            width: w,
            height: h,
        };
        // Declaration order gives the reference brush/font/pen/path cleanup order.
        let mut path = Object::new(&sup)?;
        let mut pen = Object::new(&sup)?;
        let mut font = Object::new(&sup)?;
        let mut brush = Object::new(&sup)?;
        use ed::Kind::*;
        match c.kind {
            Theme => {
                let mut value: PF_App_Color = std::mem::zeroed();
                ok(app.PF_AppGetColor.ok_or(BAD)?(x as _, &mut value))?;
                let scale = f32::from_bits(0x37800080);
                theme.insert(
                    x as i32,
                    [
                        value.red as f32 * scale,
                        value.green as f32 * scale,
                        value.blue as f32 * scale,
                        1.0,
                    ],
                );
            }
            Pen => {
                ok(sup.NewPen.ok_or(BAD)?(
                    supplier,
                    &color,
                    1.0,
                    (&mut shared.p as *mut DRAWBOT_ObjectRef).cast(),
                ))?;
            }
            ReleasePen => {
                if !shared.p.is_null() {
                    let handle = std::mem::replace(&mut shared.p, ptr::null_mut());
                    ok((shared.release)(handle))?;
                }
            }
            Antialias => ok(surf.SetAntiAliasPolicy.ok_or(BAD)?(surface, 0))?,
            Fill => ok(surf.PaintRect.ok_or(BAD)?(surface, &color, &r))?,
            Ticks | Frame | Line => {
                ok(sup.NewPath.ok_or(BAD)?(
                    supplier,
                    (&mut path.p as *mut DRAWBOT_ObjectRef).cast(),
                ))?;
                let p = path.p.cast();
                if matches!(c.kind, Frame) {
                    ok(path_suite.MoveTo.ok_or(BAD)?(p, r.left + ox, r.top + oy))?;
                    ok(path_suite.AddRect.ok_or(BAD)?(p, &r))?;
                } else {
                    ok(path_suite.MoveTo.ok_or(BAD)?(p, r.left, r.top))?;
                    ok(path_suite.LineTo.ok_or(BAD)?(
                        p,
                        r.left + if matches!(c.kind, Ticks) { 0.0 } else { w },
                        r.top + if matches!(c.kind, Ticks) { 5.0 } else { h },
                    ))?;
                    if matches!(c.kind, Ticks) {
                        ok(path_suite.MoveTo.ok_or(BAD)?(p, r.left, r.top + h))?;
                        ok(path_suite.LineTo.ok_or(BAD)?(p, r.left, r.top + h - 5.0))?;
                    }
                }
                let pen_ref = if matches!(c.kind, Ticks) {
                    shared.p.cast()
                } else {
                    ok(sup.NewPen.ok_or(BAD)?(
                        supplier,
                        &color,
                        1.0,
                        (&mut pen.p as *mut DRAWBOT_ObjectRef).cast(),
                    ))?;
                    pen.p.cast()
                };
                ok(surf.StrokePath.ok_or(BAD)?(surface, pen_ref, p))?;
            }
            Text => {
                ok(sup.NewDefaultFont.ok_or(BAD)?(
                    supplier,
                    c.font,
                    (&mut font.p as *mut DRAWBOT_ObjectRef).cast(),
                ))?;
                ok(sup.NewBrush.ok_or(BAD)?(
                    supplier,
                    &color,
                    (&mut brush.p as *mut DRAWBOT_ObjectRef).cast(),
                ))?;
                let text: Vec<u16> = c.text.encode_utf16().chain(Some(0)).collect();
                let origin = DRAWBOT_PointF32 {
                    x: r.left,
                    y: r.top,
                };
                ok(surf.DrawString.ok_or(BAD)?(
                    surface,
                    brush.p.cast(),
                    font.p.cast(),
                    text.as_ptr(),
                    &origin,
                    1,
                    1,
                    w,
                ))?;
            }
        }
    }
    Ok(())
}
#[derive(Default)]
struct Instance {
    clip: ed::Clipboard,
    ramps: HashMap<i32, ed::State>,
}
struct Instances {
    items: HashMap<usize, Instance>,
    rng: u32,
}
static STATE: LazyLock<Mutex<Instances>> = LazyLock::new(|| {
    Mutex::new(Instances {
        items: HashMap::new(),
        rng: 0x000810cd,
    })
});
pub fn clear(i: &PF_InData, all: bool) -> Result<()> {
    let mut s = STATE.lock().map_err(|_| BAD)?;
    if all {
        s.items.clear();
    } else {
        s.items.remove(&(i.effect_ref as usize));
    }
    Ok(())
}
pub unsafe fn update(i: &PF_InData, params: PF_ParamList) -> Result<()> {
    if params.is_null() {
        return Err(BAD);
    }
    let s = suite::<PF_ParamUtilsSuite3>(i, kPFParamUtilsSuite, kPFParamUtilsSuiteVersion3)?;
    for u in [13usize, 19, 25, 31, 37] {
        let ramp = (*params.add(u)).as_ref().ok_or(BAD)?.u.bd.value != 0;
        for slot in [u - 2, u + 1] {
            let mut def = *(*params.add(slot)).as_ref().ok_or(BAD)?;
            if if slot == u - 2 { ramp } else { !ramp } {
                def.ui_flags |= PF_PUI_DISABLED;
            } else {
                def.ui_flags &= !PF_PUI_DISABLED;
            }
            ok(s.PF_UpdateParamUI.ok_or(BAD)?(
                i.effect_ref,
                slot as _,
                &def,
            ))?;
        }
    }
    Ok(())
}
pub unsafe fn event(i: &PF_InData, params: PF_ParamList, e: &mut PF_EventExtra) -> Result<()> {
    if params.is_null() || e.effect_win.area != PF_EA_CONTROL {
        return Ok(());
    }
    let index = e.effect_win.index;
    if ![14, 20, 26, 32, 38].contains(&index) {
        return Ok(());
    }
    let param = (*params.add(index as usize)).as_mut().ok_or(BAD)?;
    if param.param_type != PF_Param_ARBITRARY_DATA || param.u.arb_d.value.is_null() {
        return Ok(());
    }
    if ![
        PF_Event_DRAW,
        PF_Event_DO_CLICK,
        PF_Event_DRAG,
        PF_Event_ADJUST_CURSOR,
    ]
    .contains(&e.e_type)
    {
        return Ok(());
    }
    let mut ramp = read_ramp(i, param.u.arb_d.value)?;
    let app = suite::<PFAppSuite6>(i, kPFAppSuite, kPFAppSuiteVersion6)?;
    let key = i.effect_ref as usize;
    let frame = e.effect_win.current_frame;
    if e.e_type == PF_Event_DRAW {
        let commands = {
            let mut g = STATE.lock().map_err(|_| BAD)?;
            let instance = g.items.entry(key).or_default();
            let s = instance.ramps.entry(index).or_default();
            s.hover_x -= frame.left as i32;
            s.hover_y -= frame.top as i32;
            ed::draw(&ramp, s, instance.clip.available)
        };
        return draw(i, e, &commands);
    }
    let point = if e.e_type == PF_Event_ADJUST_CURSOR {
        e.u.adjust_cursor.screen_point
    } else {
        e.u.do_click.screen_point
    };
    let event = if e.e_type == PF_Event_DO_CLICK {
        e.u.do_click.send_drag = 1;
        if e.u.do_click.num_clicks == 1 {
            ed::Event::Single
        } else {
            ed::Event::Multiple
        }
    } else if e.e_type == PF_Event_DRAG {
        if e.u.do_click.last_time != 0 {
            ed::Event::Release
        } else {
            ed::Event::Drag
        }
    } else {
        ed::Event::Hover
    };
    let picker = {
        let mut g = STATE.lock().map_err(|_| BAD)?;
        let Instances { items, rng } = &mut *g;
        let instance = items.entry(key).or_default();
        let state = instance.ramps.entry(index).or_default();
        ed::dispatch(
            &mut ramp,
            state,
            &mut instance.clip,
            rng,
            event,
            point.h as i32 - frame.left as i32,
            point.v as i32 - frame.top as i32,
        )
    };
    if picker >= 0 {
        let s = ramp.stops[picker as usize];
        let sample = PF_PixelFloat {
            alpha: s[1],
            red: s[2],
            green: s[3],
            blue: s[4],
        };
        let mut picked = sample;
        let error = app.PF_AppColorPickerDialog.ok_or(BAD)?(
            c"Color select".as_ptr(),
            &sample,
            1,
            &mut picked,
        );
        let mut g = STATE.lock().map_err(|_| BAD)?;
        let state = g
            .items
            .entry(key)
            .or_default()
            .ramps
            .entry(index)
            .or_default();
        ed::picker(
            &mut ramp,
            state,
            picker,
            error == PF_Interrupt_CANCEL as PF_Err,
            ed::Color {
                rgba: [picked.red, picked.green, picked.blue, picked.alpha],
                ..Default::default()
            },
        );
    }
    if event != ed::Event::Hover {
        write_ramp(i, param.u.arb_d.value, &ramp)?;
        ok(app.PF_InvalidateRect.ok_or(BAD)?(e.contextH, &frame))?;
    }
    param.uu.change_flags |= PF_ChangeFlag_CHANGED_VALUE;
    e.evt_out_flags |= PF_EO_HANDLED_EVENT | PF_EO_UPDATE_NOW;
    Ok(())
}

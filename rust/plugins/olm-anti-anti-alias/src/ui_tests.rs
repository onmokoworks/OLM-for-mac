//! Simulated AE suite tests; this does not claim native AE project round trips.
use super::*;
use std::{cell::RefCell, collections::HashMap, ffi::CStr};
struct Host {
    count: i32,
    colors: [[f32; 4]; 100],
    pixels: Vec<u8>,
    suites: HashMap<String, Vec<usize>>,
    handles: i32,
    params: i32,
    hidden: Vec<(i32, bool)>,
    fail_write: bool,
}
impl Default for Host {
    fn default() -> Self {
        Self {
            count: 0,
            colors: [[1., 0., 0., 0.]; 100],
            pixels: vec![255, 255, 0, 0].repeat(9),
            suites: HashMap::new(),
            handles: 0,
            params: 0,
            hidden: vec![],
            fail_write: false,
        }
    }
}
thread_local! {static HOST:RefCell<Host>=RefCell::new(Host::default());}
fn host<R>(f: impl FnOnce(&mut Host) -> R) -> R {
    HOST.with(|h| f(&mut h.borrow_mut()))
}
unsafe extern "C" fn effect(_: i32, _: PF_ProgPtr, p: *mut AEGP_EffectRefH) -> A_Err {
    *p = 1usize as _;
    host(|h| h.handles += 1);
    0
}
unsafe extern "C" fn dispose_effect(_: AEGP_EffectRefH) -> A_Err {
    host(|h| h.handles -= 1);
    0
}
unsafe extern "C" fn new_stream(
    _: i32,
    _: AEGP_EffectRefH,
    k: i32,
    p: *mut AEGP_StreamRefH,
) -> A_Err {
    *p = (k as usize + 1) as _;
    host(|h| h.handles += 1);
    0
}
unsafe extern "C" fn dispose_stream(_: AEGP_StreamRefH) -> A_Err {
    host(|h| h.handles -= 1);
    0
}
unsafe extern "C" fn write(_: i32, s: AEGP_StreamRefH, v: *mut AEGP_StreamValue2) -> A_Err {
    host(|h| {
        if h.fail_write {
            return 7;
        }
        let k = s as usize - 1;
        if k == 1 {
            h.count = (*v).val.one_d as i32
        } else {
            let c = (*v).val.color;
            h.colors[k - 7] = [c.alphaF as _, c.redF as _, c.greenF as _, c.blueF as _]
        }
        0
    })
}
unsafe extern "C" fn hide(
    s: AEGP_StreamRefH,
    _: AEGP_DynStreamFlags,
    _: A_Boolean,
    b: A_Boolean,
) -> A_Err {
    host(|h| h.hidden.push((s as i32 - 8, b != 0)));
    0
}
unsafe extern "C" fn options(
    _: i32,
    _: AEGP_EffectRefH,
    p: *mut AEGP_LayerRenderOptionsH,
) -> A_Err {
    *p = 1usize as _;
    host(|h| h.handles += 1);
    0
}
unsafe extern "C" fn dispose_options(_: AEGP_LayerRenderOptionsH) -> A_Err {
    host(|h| h.handles -= 1);
    0
}
unsafe extern "C" fn downsample(_: AEGP_LayerRenderOptionsH, x: A_short, y: A_short) -> A_Err {
    if (x, y) == (1, 1) {
        0
    } else {
        7
    }
}
unsafe extern "C" fn frame(
    _: AEGP_LayerRenderOptionsH,
    _: AEGP_RenderSuiteCheckForCancel,
    _: AEGP_CancelRefcon,
    p: *mut AEGP_FrameReceiptH,
) -> A_Err {
    *p = 1usize as _;
    host(|h| h.handles += 1);
    0
}
unsafe extern "C" fn checkin_frame(_: AEGP_FrameReceiptH) -> A_Err {
    host(|h| h.handles -= 1);
    0
}
unsafe extern "C" fn receipt_world(_: AEGP_FrameReceiptH, p: *mut AEGP_WorldH) -> A_Err {
    *p = 1usize as _;
    0
}
unsafe extern "C" fn world(_: AEGP_WorldH, w: *mut PF_EffectWorld) -> A_Err {
    (*w).width = 3;
    (*w).height = 3;
    (*w).rowbytes = 12;
    (*w).data = host(|h| h.pixels.as_mut_ptr().cast());
    0
}
unsafe extern "C" fn format(_: *const PF_EffectWorld, p: *mut PF_PixelFormat) -> PF_Err {
    *p = PF_PixelFormat_ARGB32;
    0
}
unsafe extern "C" fn checkout_param(
    _: PF_ProgPtr,
    k: i32,
    _: i32,
    _: i32,
    _: u32,
    p: *mut PF_ParamDef,
) -> PF_Err {
    *p = std::mem::zeroed();
    host(|h| {
        h.params += 1;
        match k {
            1 => (*p).u.sd.value = h.count,
            2 => (*p).u.bd.value = 0,
            _ => {
                let c = h.colors[k as usize - 7];
                (*p).u.cd.value = PF_Pixel {
                    alpha: (c[0] * 255.) as _,
                    red: (c[1] * 255.) as _,
                    green: (c[2] * 255.) as _,
                    blue: (c[3] * 255.) as _,
                }
            }
        }
    });
    0
}
unsafe extern "C" fn checkin_param(_: PF_ProgPtr, _: *mut PF_ParamDef) -> PF_Err {
    host(|h| h.params -= 1);
    0
}
unsafe extern "C" fn float_color(
    _: PF_ProgPtr,
    p: *const PF_ParamDef,
    c: *mut PF_PixelFloat,
) -> PF_Err {
    let x = (*p).u.cd.value;
    *c = PF_PixelFloat {
        alpha: x.alpha as f32 / 255.,
        red: x.red as f32 / 255.,
        green: x.green as f32 / 255.,
        blue: x.blue as f32 / 255.,
    };
    0
}
unsafe extern "C" fn acquire(
    name: *const std::ffi::c_char,
    _: i32,
    out: *mut *const c_void,
) -> SPErr {
    let name = CStr::from_ptr(name).to_str().unwrap();
    macro_rules! suite {($t:ty,$($f:ident:$v:expr),*)=>{{let mut s:Box<$t>=Box::new(std::mem::zeroed());$(s.$f=Some($v);)* Box::into_raw(s) as *const c_void}}}
    let s = match name {
        "AEGP PF Interface Suite" => {
            suite!(AEGP_PFInterfaceSuite1,AEGP_GetNewEffectForEffect:effect)
        }
        "AEGP Effect Suite" => suite!(AEGP_EffectSuite1,AEGP_DisposeEffect:dispose_effect),
        "AEGP Stream Suite" => {
            suite!(AEGP_StreamSuite3,AEGP_GetNewEffectStreamByIndex:new_stream,AEGP_DisposeStream:dispose_stream,AEGP_SetStreamValue:write)
        }
        "AEGP Dynamic Stream Suite" => {
            suite!(AEGP_DynamicStreamSuite3,AEGP_SetDynamicStreamFlag:hide)
        }
        "AEGP Layer Render Options Suite" => {
            suite!(AEGP_LayerRenderOptionsSuite2,AEGP_NewFromUpstreamOfEffect:options,AEGP_Dispose:dispose_options,AEGP_SetDownsampleFactor:downsample)
        }
        "AEGP Render Suite" => {
            suite!(AEGP_RenderSuite5,AEGP_RenderAndCheckoutLayerFrame:frame,AEGP_CheckinFrame:checkin_frame,AEGP_GetReceiptWorld:receipt_world)
        }
        "AEGP World Suite" => suite!(AEGP_WorldSuite3,AEGP_FillOutPFEffectWorld:world),
        "PF World Suite" => suite!(PF_WorldSuite2,PF_GetPixelFormat:format),
        "PF ColorParamSuite" => {
            suite!(PF_ColorParamSuite1,PF_GetFloatingPointColorFromColorDef:float_color)
        }
        _ => return 7,
    };
    *out = s;
    host(|h| {
        h.suites
            .entry(name.to_owned())
            .or_default()
            .push(s as usize)
    });
    0
}
unsafe extern "C" fn release(name: *const std::ffi::c_char, _: i32) -> SPErr {
    let name = CStr::from_ptr(name).to_str().unwrap();
    let p = host(|h| h.suites.get_mut(name).unwrap().pop().unwrap());
    macro_rules! free {
        ($t:ty) => {
            drop(Box::from_raw(p as *mut $t))
        };
    }
    match name {
        "AEGP PF Interface Suite" => free!(AEGP_PFInterfaceSuite1),
        "AEGP Effect Suite" => free!(AEGP_EffectSuite1),
        "AEGP Stream Suite" => free!(AEGP_StreamSuite3),
        "AEGP Dynamic Stream Suite" => free!(AEGP_DynamicStreamSuite3),
        "AEGP Layer Render Options Suite" => free!(AEGP_LayerRenderOptionsSuite2),
        "AEGP Render Suite" => free!(AEGP_RenderSuite5),
        "AEGP World Suite" => free!(AEGP_WorldSuite3),
        "PF World Suite" => free!(PF_WorldSuite2),
        "PF ColorParamSuite" => free!(PF_ColorParamSuite1),
        _ => return 7,
    };
    0
}
unsafe fn call(button: i32) -> Result<()> {
    let mut basic: SPBasicSuite = std::mem::zeroed();
    basic.AcquireSuite = Some(acquire);
    basic.ReleaseSuite = Some(release);
    let mut i: PF_InData = std::mem::zeroed();
    i.pica_basicP = &mut basic;
    i.inter.checkout_param = Some(checkout_param);
    i.inter.checkin_param = Some(checkin_param);
    let mut extra: PF_UserChangedParamExtra = std::mem::zeroed();
    extra.param_index = button;
    let r = handle(
        if button == 0 {
            PF_Cmd_UPDATE_PARAMS_UI
        } else {
            PF_Cmd_USER_CHANGED_PARAM
        },
        &i,
        ptr::null_mut(),
        (&mut extra as *mut PF_UserChangedParamExtra).cast(),
    );
    host(|h| {
        assert_eq!(h.handles, 0);
        assert_eq!(h.params, 0);
        assert!(h.suites.values().all(|x| x.is_empty()));
    });
    r
}
#[test]
fn buttons_persist_in_regular_streams_and_clear_keeps_count() {
    unsafe {
        host(|h| *h = Host::default());
        call(3).unwrap();
        host(|h| {
            assert_eq!(h.count, 1);
            assert_eq!(h.colors[0], [1., 1., 0., 0.]);
        });
        call(4).unwrap();
        host(|h| assert_eq!(h.count, 1));
        call(5).unwrap();
        host(|h| {
            assert_eq!(h.count, 1);
            assert!(h.colors.iter().all(|&c| c == [0.; 4]));
        });
    }
}
#[test]
fn update_visibility_follows_count() {
    unsafe {
        host(|h| {
            *h = Host::default();
            h.count = 3
        });
        call(0).unwrap();
        host(|h| {
            assert_eq!(h.hidden.len(), 100);
            for &(k, hidden) in &h.hidden {
                assert_eq!(hidden, k >= 3)
            }
        });
    }
}
#[test]
fn failed_stream_edit_releases_every_handle_and_suite() {
    unsafe {
        host(|h| {
            *h = Host::default();
            h.fail_write = true
        });
        assert_eq!(call(4), Err(7));
    }
}

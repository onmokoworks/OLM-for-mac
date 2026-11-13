use super::*;
use std::{cell::RefCell, collections::BTreeMap, ffi::CStr};
#[derive(Default)]
struct Host {
    suites: BTreeMap<String, usize>,
    enabled: BTreeMap<usize, bool>,
    visible: BTreeMap<usize, bool>,
    effects: i32,
    streams: i32,
    fail: usize,
}
thread_local! { static HOST:RefCell<Host> = RefCell::new(Host::default()); }
fn host<T>(f: impl FnOnce(&mut Host) -> T) -> T {
    HOST.with(|h| f(&mut h.borrow_mut()))
}
unsafe extern "C" fn effect(_: AEGP_PluginID, _: PF_ProgPtr, out: *mut AEGP_EffectRefH) -> A_Err {
    *out = 1usize as _;
    host(|h| h.effects += 1);
    0
}
unsafe extern "C" fn drop_effect(_: AEGP_EffectRefH) -> A_Err {
    host(|h| h.effects -= 1);
    0
}
unsafe extern "C" fn stream(
    _: AEGP_PluginID,
    _: AEGP_EffectRefH,
    slot: i32,
    out: *mut AEGP_StreamRefH,
) -> A_Err {
    *out = (slot as usize + 1) as _;
    host(|h| h.streams += 1);
    0
}
unsafe extern "C" fn drop_stream(_: AEGP_StreamRefH) -> A_Err {
    host(|h| h.streams -= 1);
    0
}
unsafe extern "C" fn hidden(
    stream: AEGP_StreamRefH,
    flag: AEGP_DynStreamFlags,
    _: A_Boolean,
    value: A_Boolean,
) -> A_Err {
    assert_eq!(flag, AEGP_DynStreamFlag_HIDDEN as AEGP_DynStreamFlags);
    let slot = stream as usize - 1;
    host(|h| {
        h.visible.insert(slot, value == 0);
        if h.fail == slot {
            17
        } else {
            0
        }
    })
}
unsafe extern "C" fn enabled(_: PF_ProgPtr, slot: i32, p: *const PF_ParamDef) -> PF_Err {
    assert_eq!((*p).ui_flags & 0x100, 0x100);
    host(|h| {
        h.enabled
            .insert(slot as usize, (*p).ui_flags & PF_PUI_DISABLED as i32 == 0)
    });
    0
}
unsafe extern "C" fn acquire(
    name: *const std::ffi::c_char,
    version: i32,
    out: *mut *const c_void,
) -> SPErr {
    let name = CStr::from_ptr(name).to_str().unwrap();
    macro_rules! suite {($t:ty,$version:expr,$($field:ident:$f:ident),*)=>{{
        assert_eq!(version,$version as i32);let mut s:Box<$t>=Box::new(std::mem::zeroed());
        $(s.$field=Some($f);)* Box::into_raw(s) as *const c_void
    }}}
    *out = match name {
        "PF Param Utils Suite" => suite!(PF_ParamUtilsSuite3,3,PF_UpdateParamUI:enabled),
        "AEGP PF Interface Suite" => {
            suite!(AEGP_PFInterfaceSuite1,1,AEGP_GetNewEffectForEffect:effect)
        }
        "AEGP Stream Suite" => {
            suite!(AEGP_StreamSuite6,kAEGPStreamSuiteVersion6,AEGP_GetNewEffectStreamByIndex:stream,AEGP_DisposeStream:drop_stream)
        }
        "AEGP Dynamic Stream Suite" => {
            suite!(AEGP_DynamicStreamSuite4,kAEGPDynamicStreamSuiteVersion4,AEGP_SetDynamicStreamFlag:hidden)
        }
        "AEGP Effect Suite" => {
            suite!(AEGP_EffectSuite5,kAEGPEffectSuiteVersion5,AEGP_DisposeEffect:drop_effect)
        }
        _ => return 7,
    };
    host(|h| h.suites.insert(name.into(), *out as usize));
    0
}
unsafe extern "C" fn release(name: *const std::ffi::c_char, _: i32) -> SPErr {
    let name = CStr::from_ptr(name).to_str().unwrap();
    let p = host(|h| h.suites.remove(name).unwrap());
    match name {
        "PF Param Utils Suite" => drop(Box::from_raw(p as *mut PF_ParamUtilsSuite3)),
        "AEGP PF Interface Suite" => drop(Box::from_raw(p as *mut AEGP_PFInterfaceSuite1)),
        "AEGP Stream Suite" => drop(Box::from_raw(p as *mut AEGP_StreamSuite6)),
        "AEGP Dynamic Stream Suite" => drop(Box::from_raw(p as *mut AEGP_DynamicStreamSuite4)),
        "AEGP Effect Suite" => drop(Box::from_raw(p as *mut AEGP_EffectSuite5)),
        _ => panic!("unknown suite"),
    };
    0
}
#[test]
fn all_palette_ui_states_and_error_cleanup() {
    unsafe {
        let mut basic: SPBasicSuite = std::mem::zeroed();
        basic.AcquireSuite = Some(acquire);
        basic.ReleaseSuite = Some(release);
        let mut input: PF_InData = std::mem::zeroed();
        input.pica_basicP = &mut basic;
        let mut params: Vec<PF_ParamDef> = vec![std::mem::zeroed(); 1624];
        for p in &mut params {
            p.ui_flags = 0x100;
        }
        for n in 0..200 {
            params[24 + n * 8].u.bd.value = (n % 2) as _;
            params[25 + n * 8].u.bd.value = (n % 3 == 0) as _;
        }
        let mut pointers: Vec<_> = params.iter_mut().map(|p| p as *mut _).collect();
        for count in [0, 26, 100, 101, 200] {
            for bits in 0..8 {
                host(|h| *h = Host::default());
                let pc = bits & 1 != 0;
                let component = bits & 2 != 0;
                let replace = bits & 4 != 0;
                params[7].u.bd.value = pc as _;
                params[8].u.bd.value = component as _;
                params[23].u.bd.value = replace as _;
                params[22].u.sd.value = count;
                assert_eq!(update(&mut input, pointers.as_mut_ptr()), Ok(()));
                host(|h| {
                    assert!(h.suites.is_empty());
                    assert_eq!((h.effects, h.streams), (0, 0));
                    assert_eq!(h.enabled.len(), 601);
                    assert_eq!(h.visible.len(), 1603);
                    assert_eq!(h.enabled[&2], !pc && !component);
                    for slot in 9..=11 {
                        assert_eq!(h.visible[&slot], component && !pc);
                    }
                    for n in 0..200 {
                        let s = 24 + n * 8;
                        let active = n < count as usize;
                        for slot in [s + 1, s + 2, s + 3] {
                            assert_eq!(h.enabled[&slot], n % 2 != 0);
                        }
                        let visible = [
                            active,
                            active && replace,
                            active,
                            active && replace && n % 3 == 0,
                            active && pc && !component,
                            active && pc && component,
                            active && pc && component,
                            active && pc && component,
                        ];
                        for (j, value) in visible.into_iter().enumerate() {
                            assert_eq!(h.visible[&(s + j)], value);
                        }
                    }
                });
                assert!(params.iter().all(|p| p.ui_flags == 0x100));
            }
        }
        host(|h| {
            *h = Host::default();
            h.fail = 1619;
        });
        assert_eq!(update(&mut input, pointers.as_mut_ptr()), Err(17));
        host(|h| {
            assert!(h.suites.is_empty());
            assert_eq!((h.effects, h.streams), (0, 0));
        });
    }
}

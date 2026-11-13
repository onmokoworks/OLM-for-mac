//! Explicit native ABI test; no AE, installation, binary patching or original copy.
#![cfg(windows)]
use olm_ae::sys::*;
use olm_kirakira::ramp::Ramp;
use std::{
    collections::HashMap,
    ffi::{c_char, c_void, CStr},
    ptr,
    sync::{LazyLock, Mutex},
};
type Entry = unsafe extern "C" fn(
    PF_Cmd,
    *mut PF_InData,
    *mut PF_OutData,
    PF_ParamList,
    *mut PF_LayerDef,
    *mut c_void,
) -> PF_Err;
#[link(name = "kernel32")]
unsafe extern "system" {
    fn LoadLibraryW(p: *const u16) -> *mut c_void;
    fn GetProcAddress(m: *mut c_void, n: *const u8) -> *mut c_void;
}
static HANDLES: LazyLock<Mutex<HashMap<usize, usize>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));
static ARBS: Mutex<Vec<(i16, usize, usize)>> = Mutex::new(Vec::new());
unsafe extern "C" fn new_handle(size: A_HandleSize) -> PF_Handle {
    let data = std::alloc::alloc_zeroed(
        std::alloc::Layout::from_size_align(size as usize + 64, 16).unwrap(),
    );
    ptr::write_bytes(data.add(size as usize), 0xaa, 64);
    let h = Box::into_raw(Box::new(data));
    HANDLES.lock().unwrap().insert(h as usize, size as usize);
    h.cast()
}
unsafe extern "C" fn lock(h: PF_Handle) -> *mut c_void {
    if h.is_null() {
        return ptr::null_mut();
    }
    (*h).cast()
}
unsafe extern "C" fn unlock(_: PF_Handle) {}
unsafe extern "C" fn dispose(h: PF_Handle) {
    if h.is_null() {
        return;
    }
    let size = HANDLES
        .lock()
        .unwrap()
        .remove(&(h as usize))
        .expect("owned handle");
    assert!(
        std::slice::from_raw_parts((*h as *const u8).add(size), 64)
            .iter()
            .all(|&v| v == 0xaa),
        "overrun size {size}"
    );
    std::alloc::dealloc(
        (*h).cast(),
        std::alloc::Layout::from_size_align(size + 64, 16).unwrap(),
    );
    drop(Box::from_raw(h));
}
unsafe extern "C" fn size(h: PF_Handle) -> A_HandleSize {
    *HANDLES.lock().unwrap().get(&(h as usize)).unwrap() as _
}
static HS: PF_HandleSuite1 = PF_HandleSuite1 {
    host_new_handle: Some(new_handle),
    host_lock_handle: Some(lock),
    host_unlock_handle: Some(unlock),
    host_dispose_handle: Some(dispose),
    host_get_handle_size: Some(size),
    host_resize_handle: None,
};
unsafe extern "C" fn aegp_register(
    _: AEGP_GlobalRefcon,
    _: *const A_char,
    p: *mut AEGP_PluginID,
) -> A_Err {
    *p = 1;
    0
}
static mut UTILITY: Option<AEGP_UtilitySuite6> = None;
unsafe extern "C" fn acquire(name: *const c_char, version: i32, out: *mut *const c_void) -> SPErr {
    if CStr::from_ptr(name).to_bytes() == b"PF Handle Suite" && version == 2 {
        *out = (&HS as *const PF_HandleSuite1).cast();
        0
    } else if CStr::from_ptr(name).to_bytes() == b"AEGP Utility Suite" {
        let mut u: AEGP_UtilitySuite6 = std::mem::zeroed();
        u.AEGP_RegisterWithAEGP = Some(aegp_register);
        UTILITY = Some(u);
        *out = std::ptr::addr_of!(UTILITY)
            .as_ref()
            .unwrap()
            .as_ref()
            .unwrap() as *const AEGP_UtilitySuite6 as _;
        0
    } else {
        eprintln!("unsupported suite {:?} v{version}", CStr::from_ptr(name));
        -1
    }
}
unsafe extern "C" fn release(_: *const c_char, _: i32) -> SPErr {
    0
}
unsafe extern "C" fn add(_: PF_ProgPtr, _: i32, p: *mut PF_ParamDef) -> PF_Err {
    let p = &*p;
    if p.param_type == PF_Param_ARBITRARY_DATA {
        let a = p.u.arb_d;
        ARBS.lock()
            .unwrap()
            .push((a.id, a.refconPV as usize, a.dephault as usize));
    }
    0
}
unsafe extern "C" fn strcpy(dst: *mut c_char, src: *const c_char) -> *mut c_char {
    ptr::copy_nonoverlapping(src, dst, CStr::from_ptr(src).to_bytes_with_nul().len());
    dst
}
unsafe extern "C" fn register(_: PF_ProgPtr, _: *mut PF_CustomUIInfo) -> PF_Err {
    0
}
unsafe fn invoke(entry: Entry, i: &mut PF_InData, e: &mut PF_ArbParamsExtra) {
    let mut o: PF_OutData = std::mem::zeroed();
    o.global_data = i.global_data;
    assert_eq!(
        entry(
            PF_Cmd_ARBITRARY_CALLBACK,
            i,
            &mut o,
            ptr::null_mut(),
            ptr::null_mut(),
            (e as *mut PF_ArbParamsExtra).cast()
        ),
        0
    );
}
#[test]
#[ignore = "requires OLM_KIRA_ORIGINAL absolute path; loads original only for arbitrary callbacks"]
fn original_flatten_unflatten_copy_abi() {
    unsafe {
        let path = std::env::var("OLM_KIRA_ORIGINAL").expect("original path");
        let wide: Vec<u16> = path.encode_utf16().chain(Some(0)).collect();
        let module = LoadLibraryW(wide.as_ptr());
        assert!(!module.is_null());
        let raw = GetProcAddress(module, b"entry_point\0".as_ptr());
        assert!(!raw.is_null());
        let entry: Entry = std::mem::transmute(raw);
        let mut basic: SPBasicSuite = std::mem::zeroed();
        basic.AcquireSuite = Some(acquire);
        basic.ReleaseSuite = Some(release);
        let mut i: PF_InData = std::mem::zeroed();
        let mut o = std::mem::zeroed();
        i.pica_basicP = &mut basic;
        let mut utils: _PF_UtilCallbacks = std::mem::zeroed();
        utils.host_new_handle = Some(new_handle);
        utils.host_lock_handle = Some(lock);
        utils.host_unlock_handle = Some(unlock);
        utils.host_dispose_handle = Some(dispose);
        utils.host_get_handle_size = Some(size);
        utils.ansi.strcpy = Some(strcpy);
        i.utils = &mut utils;
        i.inter.add_param = Some(add);
        i.inter.register_ui = Some(register);
        eprintln!("global setup");
        assert_eq!(
            entry(
                PF_Cmd_GLOBAL_SETUP,
                &mut i,
                &mut o,
                ptr::null_mut(),
                ptr::null_mut(),
                ptr::null_mut()
            ),
            0
        );
        i.global_data = o.global_data;
        eprintln!(
            "params setup global={:p} out={:p}",
            i.global_data, o.global_data
        );
        assert_eq!(
            entry(
                PF_Cmd_PARAMS_SETUP,
                &mut i,
                &mut o,
                ptr::null_mut(),
                ptr::null_mut(),
                ptr::null_mut()
            ),
            0
        );
        eprintln!("arbitrary callbacks");
        let arbs = ARBS.lock().unwrap().clone();
        assert_eq!(arbs.len(), 5);
        for &(id, refcon, default) in &arbs {
            let mut e: PF_ArbParamsExtra = std::mem::zeroed();
            e.id = id;
            let mut flat = [0xccu8; 325];
            e.which_function = PF_Arbitrary_FLATTEN_FUNC;
            e.u.flatten_func_params.refconPV = refcon as _;
            e.u.flatten_func_params.arbH = default as _;
            e.u.flatten_func_params.buf_sizeLu = 325;
            e.u.flatten_func_params.flat_dataPV = flat.as_mut_ptr().cast();
            invoke(entry, &mut i, &mut e);
            assert_eq!(
                flat[..65],
                Ramp::default().flatten().unwrap()[..65],
                "original default active bytes id{id}"
            );
            let mut cases = Vec::new();
            for count in 0..=16 {
                let mut r = Ramp {
                    count,
                    stops: [[0.0; 5]; 16],
                };
                for x in 0..count as usize {
                    r.stops[x] = [x as f32 / 16.0, 0.5, x as f32 / 17.0, 0.25, 0.75];
                }
                cases.push(r);
            }
            cases.extend((0..34).map(olm_kirakira::editor::preset));
            let mut declared_size = 0;
            e.which_function = PF_Arbitrary_FLAT_SIZE_FUNC;
            e.u.flat_size_func_params.refconPV = refcon as _;
            e.u.flat_size_func_params.arbH = default as _;
            e.u.flat_size_func_params.flat_data_sizePLu = &mut declared_size;
            invoke(entry, &mut i, &mut e);
            assert_eq!(declared_size, 325);
            for r in cases {
                let count = r.count;
                let bytes = r.flatten().unwrap();
                let mut h = ptr::null_mut();
                e.which_function = PF_Arbitrary_UNFLATTEN_FUNC;
                e.u.unflatten_func_params.refconPV = refcon as _;
                e.u.unflatten_func_params.buf_sizeLu = 325;
                e.u.unflatten_func_params.flat_dataPV = bytes.as_ptr().cast();
                e.u.unflatten_func_params.arbPH = &mut h;
                invoke(entry, &mut i, &mut e);
                let mut copied = ptr::null_mut();
                e.which_function = PF_Arbitrary_COPY_FUNC;
                e.u.copy_func_params.refconPV = refcon as _;
                e.u.copy_func_params.src_arbH = h;
                e.u.copy_func_params.dst_arbPH = &mut copied;
                invoke(entry, &mut i, &mut e);
                e.which_function = PF_Arbitrary_FLATTEN_FUNC;
                e.u.flatten_func_params.refconPV = refcon as _;
                e.u.flatten_func_params.arbH = copied;
                e.u.flatten_func_params.buf_sizeLu = 325;
                e.u.flatten_func_params.flat_dataPV = flat.as_mut_ptr().cast();
                invoke(entry, &mut i, &mut e);
                assert_eq!(
                    flat[..5 + count as usize * 20],
                    bytes[..5 + count as usize * 20],
                    "custom ramp count{count} id{id}"
                );
                for handle in [h, copied] {
                    e.which_function = PF_Arbitrary_DISPOSE_FUNC;
                    e.u.dispose_func_params.refconPV = refcon as _;
                    e.u.dispose_func_params.arbH = handle;
                    invoke(entry, &mut i, &mut e);
                }
            }
            e.which_function = PF_Arbitrary_DISPOSE_FUNC;
            e.u.dispose_func_params.refconPV = refcon as _;
            e.u.dispose_func_params.arbH = default as _;
            invoke(entry, &mut i, &mut e);
        }
        // This deliberately minimal host tests arbitrary callbacks, not the
        // original's global shutdown (which expects the full AE cache/UI host).
        // Dispose every remaining mock-host handle and retain the DLL until the
        // isolated test process exits; the OS releases its runtime allocations.
        let remaining: Vec<usize> = HANDLES.lock().unwrap().keys().copied().collect();
        for h in remaining {
            dispose(h as PF_Handle);
        }
        assert!(HANDLES.lock().unwrap().is_empty());
        eprintln!("5 original defaults + 255 custom/preset UNFLATTEN/COPY/FLATTEN: active flattened bytes identical (325-byte envelope); no live handles");
    }
}

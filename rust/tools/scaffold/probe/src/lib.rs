//! Inspection-only proxy. Runs inside the oracle-owned AEXCompat worker, never AE.
#![allow(non_upper_case_globals, non_snake_case)]
use after_effects_sys::*;
use serde_json::{json, Value};
use std::{
    cell::RefCell,
    ffi::{c_void, CStr, CString},
    ptr,
    sync::OnceLock,
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
extern "system" {
    fn LoadLibraryW(p: *const u16) -> *mut c_void;
    fn GetProcAddress(m: *mut c_void, n: *const i8) -> *mut c_void;
}
static ENTRY: OnceLock<Entry> = OnceLock::new();
#[derive(Default)]
struct Capture {
    params: Vec<Value>,
    arbs: Vec<(usize, PF_ArbitraryDef)>,
    events: i32,
    add: Option<unsafe extern "C" fn(PF_ProgPtr, i32, *mut PF_ParamDef) -> PF_Err>,
    register: Option<unsafe extern "C" fn(PF_ProgPtr, *mut PF_CustomUIInfo) -> PF_Err>,
}
thread_local! { static CAP:RefCell<Capture> = RefCell::new(Capture::default()); }
unsafe fn text(p: *const i8) -> Vec<u8> {
    if p.is_null() {
        vec![]
    } else {
        CStr::from_ptr(p).to_bytes().to_vec()
    }
}
unsafe extern "C" fn add(r: PF_ProgPtr, index: i32, p: *mut PF_ParamDef) -> PF_Err {
    let p0 = &*p;
    let mut fields = serde_json::Map::new();
    macro_rules! fields {($($path:ident $(.$tail:ident)*),* $(,)?)=>{$(fields.insert(stringify!($path $(.$tail)*).replace(' ',""),json!(p0.$path $(.$tail)*));)*};}
    macro_rules! bits32 {($($path:ident $(.$tail:ident)*),* $(,)?)=>{$(fields.insert(stringify!($path $(.$tail)*).replace(' ',""),json!({"f32_bits":p0.$path $(.$tail)*.to_bits()}));)*};}
    macro_rules! bits64 {($($path:ident $(.$tail:ident)*),* $(,)?)=>{$(fields.insert(stringify!($path $(.$tail)*).replace(' ',""),json!({"f64_bits":p0.$path $(.$tail)*.to_bits()}));)*};}
    fields!(uu.id, ui_flags, ui_width, ui_height, param_type, flags);
    let mut label = None;
    let mut supported = true;
    match p0.param_type {
        PF_Param_SLIDER => {
            fields!(
                u.sd.value,
                u.sd.valid_min,
                u.sd.valid_max,
                u.sd.slider_min,
                u.sd.slider_max,
                u.sd.dephault
            );
        }
        PF_Param_FIX_SLIDER => {
            fields!(
                u.fd.value,
                u.fd.valid_min,
                u.fd.valid_max,
                u.fd.slider_min,
                u.fd.slider_max,
                u.fd.dephault,
                u.fd.precision,
                u.fd.display_flags
            );
        }
        PF_Param_FLOAT_SLIDER => {
            bits64!(u.fs_d.value, u.fs_d.phase);
            bits32!(
                u.fs_d.valid_min,
                u.fs_d.valid_max,
                u.fs_d.slider_min,
                u.fs_d.slider_max,
                u.fs_d.dephault,
                u.fs_d.curve_tolerance,
                u.fs_d.exponent
            );
            fields!(
                u.fs_d.precision,
                u.fs_d.display_flags,
                u.fs_d.fs_flags,
                u.fs_d.useExponent
            );
        }
        PF_Param_ANGLE => {
            fields!(u.ad.value, u.ad.dephault, u.ad.valid_min, u.ad.valid_max);
        }
        PF_Param_CHECKBOX => {
            fields!(u.bd.value, u.bd.dephault);
            label = Some(("u.bd.u.nameptr", text(p0.u.bd.u.nameptr)));
        }
        PF_Param_POPUP => {
            fields!(u.pd.value, u.pd.dephault, u.pd.num_choices);
            label = Some(("u.pd.u.namesptr", text(p0.u.pd.u.namesptr)));
        }
        PF_Param_COLOR => {
            fields!(
                u.cd.value.alpha,
                u.cd.value.red,
                u.cd.value.green,
                u.cd.value.blue,
                u.cd.dephault.alpha,
                u.cd.dephault.red,
                u.cd.dephault.green,
                u.cd.dephault.blue
            );
        }
        PF_Param_POINT => {
            fields!(
                u.td.x_value,
                u.td.y_value,
                u.td.x_dephault,
                u.td.y_dephault,
                u.td.restrict_bounds
            );
        }
        PF_Param_LAYER => {
            fields!(u.ld.dephault);
        }
        PF_Param_ARBITRARY_DATA => {
            fields!(u.arb_d.id);
        }
        PF_Param_GROUP_START | PF_Param_GROUP_END => {}
        _ => supported = false,
    }
    // Fixed-size descriptions are byte strings too, not locale-decoded text.
    let arrays: Vec<(&str, Vec<i8>)> = match p0.param_type {
        PF_Param_SLIDER => vec![
            ("u.sd.value_str", p0.u.sd.value_str.to_vec()),
            ("u.sd.value_desc", p0.u.sd.value_desc.to_vec()),
        ],
        PF_Param_FIX_SLIDER => vec![
            ("u.fd.value_str", p0.u.fd.value_str.to_vec()),
            ("u.fd.value_desc", p0.u.fd.value_desc.to_vec()),
        ],
        PF_Param_FLOAT_SLIDER => vec![("u.fs_d.value_desc", p0.u.fs_d.value_desc.to_vec())],
        _ => vec![],
    };
    let f=CAP.with(|c| {let mut c=c.borrow_mut();let slot=c.params.len()+1;
        if p0.param_type==PF_Param_ARBITRARY_DATA {c.arbs.push((slot,p0.u.arb_d));}
        c.params.push(json!({"slot":slot,"add_index":index,"fields":fields,"name":p0.name.to_vec(),"label":label,"arrays":arrays,"supported":supported}));c.add.unwrap()});
    f(r, index, p)
}
unsafe extern "C" fn register(r: PF_ProgPtr, ui: *mut PF_CustomUIInfo) -> PF_Err {
    let f = CAP.with(|c| {
        let mut c = c.borrow_mut();
        c.events = (*ui).events as _;
        c.register.unwrap()
    });
    f(r, ui)
}
unsafe fn original() -> Entry {
    *ENTRY.get_or_init(|| {
        let path = std::env::var("OLM_SCAFFOLD_ORIGINAL").expect("original");
        let wide: Vec<u16> = path.encode_utf16().chain(Some(0)).collect();
        let m = LoadLibraryW(wide.as_ptr());
        assert!(!m.is_null(), "LoadLibraryW failed");
        let symbol = CString::new(std::env::var("OLM_SCAFFOLD_ENTRY").expect("entry")).unwrap();
        let raw = GetProcAddress(m, symbol.as_ptr());
        assert!(!raw.is_null(), "entry absent");
        std::mem::transmute(raw)
    })
}
unsafe fn invoke(
    cmd: PF_Cmd,
    i: *mut PF_InData,
    o: *mut PF_OutData,
    p: PF_ParamList,
    w: *mut PF_LayerDef,
    e: *mut c_void,
) -> PF_Err {
    let entry = original();
    if cmd != PF_Cmd_PARAMS_SETUP {
        return entry(cmd, i, o, p, w, e);
    }
    let old = (*i).inter;
    CAP.with(|c| {
        *c.borrow_mut() = Capture {
            add: old.add_param,
            register: old.register_ui,
            ..Capture::default()
        }
    });
    (*i).inter.add_param = Some(add);
    (*i).inter.register_ui = Some(register);
    let err = entry(cmd, i, o, p, w, e);
    (*i).inter = old;
    if err != 0 {
        return err;
    }
    let arbs = CAP.with(|c| c.borrow().arbs.clone());
    for (slot, a) in arbs {
        let mut extra: PF_ArbParamsExtra = std::mem::zeroed();
        extra.id = a.id;
        let mut size = 0;
        extra.which_function = PF_Arbitrary_FLAT_SIZE_FUNC;
        extra.u.flat_size_func_params.refconPV = a.refconPV;
        extra.u.flat_size_func_params.arbH = a.dephault;
        extra.u.flat_size_func_params.flat_data_sizePLu = &mut size;
        let size_err = entry(
            PF_Cmd_ARBITRARY_CALLBACK,
            i,
            o,
            ptr::null_mut(),
            ptr::null_mut(),
            (&mut extra as *mut PF_ArbParamsExtra).cast(),
        );
        let mut bytes: Vec<u8> = vec![];
        let mut flat_err = -1;
        if size_err == 0 && size <= 16 * 1024 * 1024 {
            bytes.resize(size as usize, 0);
            extra.which_function = PF_Arbitrary_FLATTEN_FUNC;
            extra.u.flatten_func_params.refconPV = a.refconPV;
            extra.u.flatten_func_params.arbH = a.dephault;
            extra.u.flatten_func_params.buf_sizeLu = size;
            extra.u.flatten_func_params.flat_dataPV = bytes.as_mut_ptr().cast();
            flat_err = entry(
                PF_Cmd_ARBITRARY_CALLBACK,
                i,
                o,
                ptr::null_mut(),
                ptr::null_mut(),
                (&mut extra as *mut PF_ArbParamsExtra).cast(),
            );
        }
        CAP.with(|c| {
            c.borrow_mut().params[slot - 1]["arbitrary"] =
                json!({"size_error":size_err,"flatten_error":flat_err,"default_flat":bytes});
        });
    }
    let doc=CAP.with(|c|{let c=c.borrow();json!({"schema_version":1,"params":c.params,"custom_ui_events":c.events,"version":(*o).my_version,"flags":(*o).out_flags,"flags2":(*o).out_flags2,"num_params":(*o).num_params})});
    let path = std::env::var("OLM_SCAFFOLD_CAPTURE").expect("capture");
    std::fs::write(path, serde_json::to_vec_pretty(&doc).unwrap()).expect("write capture");
    0
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
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| invoke(cmd, i, o, p, w, e)))
        .unwrap_or(PF_Err_BAD_CALLBACK_PARAM as _)
}

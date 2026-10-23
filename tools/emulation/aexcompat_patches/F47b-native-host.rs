//! Native C-ABI lifecycle boundary. Not a render/session backend.
//! Buffers use shared aex-abi constants, verified against the Mac SDK before build.
use aex_abi::x86_64_windows as abi;
use aex_guest_worker::backend::GuestParam;
use serde_json::{Value, json};
use std::{
    cell::RefCell,
    ffi::{CStr, c_char, c_void},
    ptr,
};

type Entry =
    unsafe extern "C" fn(i32, *mut u8, *mut u8, *mut c_void, *mut c_void, *mut c_void) -> i32;
#[repr(C, align(8))]
struct Buffer<const N: usize>([u8; N]);
#[derive(Default)]
struct State {
    parameters: Vec<GuestParam>,
    suites: Vec<Value>,
}
thread_local! { static STATE: RefCell<Option<State>> = const { RefCell::new(None) }; }
fn u32_at(b: &[u8], offset: usize) -> u32 {
    u32::from_ne_bytes(b[offset..offset + 4].try_into().unwrap())
}
fn put32(b: &mut [u8], offset: usize, value: u32) {
    b[offset..offset + 4].copy_from_slice(&value.to_ne_bytes());
}
fn put64(b: &mut [u8], offset: usize, value: u64) {
    b[offset..offset + 8].copy_from_slice(&value.to_ne_bytes());
}
unsafe extern "C" fn add_param(_: *mut c_void, index: i32, definition: *const u8) -> i32 {
    if definition.is_null() {
        return 516;
    }
    // Reuse the emulated host's parameter representation. Pointer-bearing union
    // fields are valid only while the owning bundle remains loaded; this probe
    // serializes scalar metadata and never dereferences those fields.
    let bytes = unsafe { std::slice::from_raw_parts(definition, abi::PF_PARAM_DEF_SIZE) };
    let name = &bytes[abi::PARAM_NAME_OFFSET..abi::PARAM_NAME_OFFSET + abi::PARAM_NAME_SIZE];
    let end = name.iter().position(|&x| x == 0).unwrap_or(name.len());
    STATE.with(|state| {
        let mut state = state.borrow_mut();
        let Some(state) = state.as_mut() else {
            return 516;
        };
        state.parameters.push(GuestParam {
            index,
            param_type: u32_at(bytes, abi::PARAM_PARAM_TYPE_OFFSET) as i32,
            name: String::from_utf8_lossy(&name[..end]).into_owned(),
            bytes: bytes.to_vec(),
        });
        0
    })
}
unsafe extern "C" fn abort(_: *mut c_void) -> i32 {
    0
}
unsafe extern "C" fn progress(_: *mut c_void, _: i32, _: i32) -> i32 {
    0
}
unsafe extern "C" fn acquire(name: *const c_char, version: i32, suite: *mut *const c_void) -> i32 {
    if !suite.is_null() {
        unsafe {
            *suite = ptr::null();
        }
    }
    if name.is_null() {
        return -1;
    }
    let name = unsafe { CStr::from_ptr(name) }.to_string_lossy();
    eprintln!("native AcquireSuite name={name:?} version={version} supported=false");
    STATE.with(|state| {
        if let Some(state) = state.borrow_mut().as_mut() {
            state
                .suites
                .push(json!({"name":name,"version":version,"supported":false}));
        }
    });
    // kSPSuiteNotFoundError from SPErrorCodes.h (four-character SPErr).
    0x53214664
}
unsafe extern "C" fn release(_: *const c_char, _: i32) -> i32 {
    0x53214664
}
struct Scope;
impl Drop for Scope {
    fn drop(&mut self) {
        STATE.with(|s| {
            s.borrow_mut().take();
        });
    }
}

pub unsafe fn setup(pointer: *mut c_void) -> Result<Value, String> {
    if STATE.with(|s| s.borrow().is_some()) {
        return Err("nested native host invocation".into());
    }
    STATE.with(|s| *s.borrow_mut() = Some(State::default()));
    let _scope = Scope;
    let entry: Entry = unsafe { std::mem::transmute(pointer) };
    let mut input = Buffer([0u8; abi::PF_IN_DATA_SIZE]);
    let mut output = Buffer([0u8; abi::PF_OUT_DATA_SIZE]);
    let mut utils = Buffer([0u8; abi::PF_UTIL_CALLBACKS_SIZE]);
    let mut basic = [0usize; 8];
    basic[0] = acquire as *const () as usize;
    basic[1] = release as *const () as usize;
    for (offset, address) in [
        (abi::INTER_ADD_PARAM_OFFSET, add_param as *const () as usize),
        (abi::INTER_ABORT_OFFSET, abort as *const () as usize),
        (abi::INTER_PROGRESS_OFFSET, progress as *const () as usize),
    ] {
        put64(&mut input.0, offset, address as u64);
    }
    put64(
        &mut input.0,
        abi::IN_UTILS_OFFSET,
        utils.0.as_mut_ptr() as u64,
    );
    put64(
        &mut input.0,
        abi::IN_PICA_BASICP_OFFSET,
        basic.as_ptr() as u64,
    );
    put64(&mut input.0, abi::IN_EFFECT_REF_OFFSET, 1);
    // Match ClassicHost::from_engine_with_effect's setup inputs.
    for (offset, value) in [
        (abi::IN_QUALITY_OFFSET, 1),
        (abi::IN_VERSION_OFFSET, 13 | (29 << 16)),
        (abi::IN_APPL_ID_OFFSET, 0x4658_5443),
        (abi::IN_NUM_PARAMS_OFFSET, 1),
        (abi::IN_TIME_STEP_OFFSET, 1),
        (abi::IN_LOCAL_TIME_STEP_OFFSET, 1),
        (abi::IN_TIME_SCALE_OFFSET, 1),
    ] {
        put32(&mut input.0, offset, value);
    }
    for offset in [
        abi::IN_DOWNSAMPLE_X_OFFSET,
        abi::IN_DOWNSAMPLE_Y_OFFSET,
        abi::IN_PIXEL_ASPECT_RATIO_OFFSET,
    ] {
        put32(&mut input.0, offset, 1);
        put32(&mut input.0, offset + 4, 1);
    }
    let mut selectors = Vec::new();
    let mut call = |cmd: usize, name: &str| {
        let error = unsafe {
            entry(
                cmd as i32,
                input.0.as_mut_ptr(),
                output.0.as_mut_ptr(),
                ptr::null_mut(),
                ptr::null_mut(),
                ptr::null_mut(),
            )
        };
        selectors.push(json!({"selector":name,"error":error}));
        // Propagate global/sequence handles exactly as ClassicHost does.
        for (src, dst) in [
            (abi::OUT_GLOBAL_DATA_OFFSET, abi::IN_GLOBAL_DATA_OFFSET),
            (abi::OUT_SEQUENCE_DATA_OFFSET, abi::IN_SEQUENCE_DATA_OFFSET),
        ] {
            input.0[dst..dst + 8].copy_from_slice(&output.0[src..src + 8]);
        }
        if cmd == abi::PF_CMD_PARAMS_SETUP {
            put32(
                &mut input.0,
                abi::IN_NUM_PARAMS_OFFSET,
                u32_at(&output.0, abi::OUT_NUM_PARAMS_OFFSET),
            );
        }
        error
    };
    let global = call(abi::PF_CMD_GLOBAL_SETUP, "GLOBAL_SETUP");
    let mut setup_ok = false;
    if global == 0 {
        let params = call(abi::PF_CMD_PARAMS_SETUP, "PARAMS_SETUP");
        if params == 0 {
            let sequence = call(abi::PF_CMD_SEQUENCE_SETUP, "SEQUENCE_SETUP");
            if sequence == 0 {
                setup_ok = true;
                if call(abi::PF_CMD_SEQUENCE_SETDOWN, "SEQUENCE_SETDOWN") != 0 {
                    setup_ok = false;
                }
            }
        }
        if call(abi::PF_CMD_GLOBAL_SETDOWN, "GLOBAL_SETDOWN") != 0 {
            setup_ok = false;
        }
    }
    let (parameters, suites) = STATE.with(|s| {
        let mut s = s.borrow_mut();
        let s = s.as_mut().unwrap();
        (
            std::mem::take(&mut s.parameters),
            std::mem::take(&mut s.suites),
        )
    });
    let parameters: Vec<Value> = parameters
        .iter()
        .enumerate()
        .map(|(offset, p)| {
            json!({
                "slot": offset+1, "index":p.index, "param_type":p.param_type, "name":p.name,
                "disk_id":u32_at(&p.bytes, abi::PARAM_UU_OFFSET),
                "flags":u32_at(&p.bytes, abi::PARAM_FLAGS_OFFSET)
            })
        })
        .collect();
    Ok(json!({"setup_ok":setup_ok, "selectors_executed":selectors,
        "advertised_num_params":u32_at(&output.0, abi::OUT_NUM_PARAMS_OFFSET),
        "out_flags":u32_at(&output.0, abi::OUT_OUT_FLAGS_OFFSET),
        "out_flags2":u32_at(&output.0, abi::OUT_OUT_FLAGS2_OFFSET),
        "parameters":parameters, "acquire_suite_calls":suites,
        "render_supported":false, "session_supported":false}))
}

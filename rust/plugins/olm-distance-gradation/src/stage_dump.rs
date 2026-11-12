//! OLM-internal, opt-in native witness ABI. Never installed or used by AE.
//! Calls the production filters; witness owns and dumps the raw float buffers.

/// Replay Gaussian stages with distinct initialized width * height float buffers.
/// native=0 reproduces the documented historical SSE arithmetic; native=1 uses
/// production AVX/FMA semantics. fault_index=-1 disables one-ULP injection.
#[no_mangle]
pub unsafe extern "C" fn olm_stage_gaussian_v1(
    src: *const f32,
    dst: *mut f32,
    width: u32,
    height: u32,
    kx: u32,
    ky: u32,
    native: u32,
    fault_index: i64,
) -> i32 {
    let n = (width as usize).checked_mul(height as usize).unwrap_or(0);
    if n == 0
        || n > 1_048_576
        || src.is_null()
        || dst.is_null()
        || src == dst
        || kx == 0
        || ky == 0
        || kx > 8193
        || ky > 8193
        || kx % 2 == 0
        || ky % 2 == 0
        || native > 1
        || fault_index < -1
        || fault_index >= n as i64
    {
        return -1;
    }
    let source = std::slice::from_raw_parts(src, n);
    let destination = std::slice::from_raw_parts_mut(dst, n);
    destination.copy_from_slice(source);
    if native == 1 {
        crate::filters::gaussian_native(
            destination,
            width as usize,
            height as usize,
            kx as usize,
            ky as usize,
        );
    } else {
        crate::filters::stage_dump_gaussian_sse(
            destination,
            width as usize,
            height as usize,
            kx as usize,
            ky as usize,
        );
    }
    if fault_index >= 0 {
        let value = &mut destination[fault_index as usize];
        if !value.is_finite() || *value < 0.0 || value.to_bits() == 0x7f7fffff {
            return -2;
        }
        *value = f32::from_bits(value.to_bits() + 1);
    }
    0
}

// Actual render-path capture. This entire module is feature-gated. One owned
// harness process handles one render; the ordinal also distinguishes repeats.
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
static CAPTURE_INDEX: AtomicUsize = AtomicUsize::new(0);

pub(crate) fn native_mode(default: bool) -> bool {
    if std::env::var("OLM_STAGE_HISTORICAL_SSE").as_deref() == Ok("1") {
        false
    } else {
        default
    }
}
fn dump(path: &std::path::Path, name: &str, values: &[f32]) {
    let bytes: Vec<u8> = values
        .iter()
        .flat_map(|v| v.to_bits().to_le_bytes())
        .collect();
    std::fs::write(path.join(name), bytes).expect("stage-dump write failed");
}
pub(crate) fn begin(
    input: &[f32],
    w: usize,
    h: usize,
    kx: usize,
    ky: usize,
    native: bool,
) -> Option<PathBuf> {
    let root = std::env::var_os("OLM_STAGE_DUMP_DIR")?;
    let ordinal = CAPTURE_INDEX.fetch_add(1, Ordering::SeqCst);
    let path = PathBuf::from(root).join(format!("gaussian-{}-{}", std::process::id(), ordinal));
    std::fs::create_dir(&path).expect("stage-dump directory must be new");
    dump(&path, "input.bin", input);
    std::fs::write(path.join("stage.json"), format!(
        "{{\"plugin\":\"distance\",\"width\":{w},\"height\":{h},\"kx\":{kx},\"ky\":{ky},\"native\":{native},\"ordinal\":{ordinal}}}\n"
    )).expect("stage-dump metadata failed");
    Some(path)
}
pub(crate) fn middle(values: &mut [f32], capture: &Option<PathBuf>) {
    if let Some(path) = capture {
        if let Ok(index) = std::env::var("OLM_STAGE_FAULT_INDEX") {
            let index: usize = index.parse().expect("invalid stage fault index");
            let value = &mut values[index];
            assert!(value.is_finite() && *value >= 0.0 && value.to_bits() < 0x7f7fffff);
            *value = f32::from_bits(value.to_bits() + 1);
        }
        dump(path, "middle.bin", values);
    }
}
pub(crate) fn end(values: &[f32], capture: Option<PathBuf>) {
    if let Some(path) = capture {
        dump(&path, "output.bin", values);
    }
}

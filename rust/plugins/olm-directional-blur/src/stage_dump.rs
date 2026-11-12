//! OLM-internal, opt-in native witness ABI. Never installed or used by AE.
//! Buffers are dumped by the witness child, not by the production renderer.

/// Replay the production rotate stage. All pointers must address distinct,
/// initialized, 16-byte-aligned buffers of width * height RGBA float pixels.
/// fault_index = -1 disables injection; otherwise increment one positive finite
/// float by one ULP *before* it is consumed by the following stage.
#[no_mangle]
pub unsafe extern "C" fn olm_stage_rotate_v1(
    src: *const [f32; 4],
    dst: *mut [f32; 4],
    width: u32,
    height: u32,
    angle: f32,
    fault_index: i64,
) -> i32 {
    let n = (width as usize).checked_mul(height as usize).unwrap_or(0);
    if n == 0
        || n > 1_048_576
        || src.is_null()
        || dst.is_null()
        || src == dst
        || !angle.is_finite()
        || fault_index < -1
        || fault_index >= (n * 4) as i64
    {
        return -1;
    }
    let source = std::slice::from_raw_parts(src, n);
    let destination = std::slice::from_raw_parts_mut(dst, n);
    crate::rotate::rgba(source, destination, width as usize, height as usize, angle);
    if fault_index >= 0 {
        let i = fault_index as usize;
        let value = &mut destination[i / 4][i % 4];
        if !value.is_finite() || *value < 0.0 || value.to_bits() == 0x7f7fffff {
            return -2;
        }
        *value = f32::from_bits(value.to_bits() + 1);
    }
    0
}

use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
static CAPTURE_INDEX: AtomicUsize = AtomicUsize::new(0);
fn dump(path: &std::path::Path, name: &str, values: &[[f32; 4]]) {
    let bytes: Vec<u8> = values
        .iter()
        .flatten()
        .flat_map(|v| v.to_bits().to_le_bytes())
        .collect();
    std::fs::write(path.join(name), bytes).expect("stage-dump write failed");
}
pub(crate) fn begin(
    src: &[[f32; 4]],
    dst: &[[f32; 4]],
    w: usize,
    h: usize,
    angle: f32,
) -> Option<(PathBuf, usize)> {
    let root = std::env::var_os("OLM_STAGE_DUMP_DIR")?;
    let ordinal = CAPTURE_INDEX.fetch_add(1, Ordering::SeqCst);
    let path = PathBuf::from(root).join(format!("rotate-{}-{}", std::process::id(), ordinal));
    std::fs::create_dir(&path).expect("stage-dump directory must be new");
    dump(&path, "input.bin", src);
    dump(&path, "initial.bin", dst);
    std::fs::write(path.join("stage.json"), format!(
        "{{\"plugin\":\"directional\",\"width\":{w},\"height\":{h},\"angle_bits\":{},\"ordinal\":{ordinal}}}\n", angle.to_bits()
    )).expect("stage-dump metadata failed");
    Some((path, ordinal))
}
pub(crate) fn end(dst: &mut [[f32; 4]], capture: Option<(PathBuf, usize)>) {
    if let Some((path, ordinal)) = capture {
        if ordinal == 0 {
            if let Ok(index) = std::env::var("OLM_STAGE_FAULT_INDEX") {
                let i: usize = index.parse().expect("invalid stage fault index");
                let value = &mut dst[i / 4][i % 4];
                assert!(value.is_finite() && *value >= 0.0 && value.to_bits() < 0x7f7fffff);
                *value = f32::from_bits(value.to_bits() + 1);
            }
        }
        dump(&path, "output.bin", dst);
    }
}

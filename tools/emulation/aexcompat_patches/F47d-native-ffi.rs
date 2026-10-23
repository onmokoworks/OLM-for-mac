//! The sole unsafe Rust boundary. C++ receives length-checked SDK snapshots.
use std::ffi::{CString, c_char};
use aex_abi::x86_64_windows as abi;
unsafe extern "C" {
    fn f47c_render(path: *const c_char, input: *const u8, parameters: *mut u8,
        source: *mut u8, destination: *mut u8, source_pixels: *mut u8,
        destination_pixels: *mut u8, depth: i16, request: *const i32, count: i32, smart: i32) -> i32;
}
pub fn render(path: &str, input: &[u8], params: &mut [u8], src: &mut [u8], dst: &mut [u8],
    src_pixels: &mut [u8], dst_pixels: &mut [u8], depth: i16, request: &[i32;4], smart: bool) -> Result<i32,String> {
    if input.len()!=abi::PF_IN_DATA_SIZE || params.is_empty() || params.len()%abi::PF_PARAM_DEF_SIZE!=0 ||
        src.len()!=abi::PF_LAYER_DEF_SIZE || dst.len()!=abi::PF_LAYER_DEF_SIZE {
        return Err("native ABI snapshot size mismatch".into());
    }
    let path = CString::new(path).map_err(|_| "NUL in bundle path")?;
    Ok(unsafe { f47c_render(path.as_ptr(),input.as_ptr(),params.as_mut_ptr(),src.as_mut_ptr(),
        dst.as_mut_ptr(),src_pixels.as_mut_ptr(),dst_pixels.as_mut_ptr(),depth,request.as_ptr(), (params.len()/abi::PF_PARAM_DEF_SIZE) as i32, smart as i32) })
}

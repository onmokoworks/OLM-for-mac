//! Returned-allocation shim called by the unmodified witness host.
//! Reuses witness's public ABI bridge; no second native calling convention.
#![allow(dead_code)]
#[rustfmt::skip]
#[path = "../../../witness/src/abi.rs"]
mod abi;
#[rustfmt::skip]
#[path = "../../../witness/src/windows.rs"]
mod windows;
use std::{ffi::OsString, os::windows::ffi::OsStringExt, path::PathBuf};

// abi.rs also contains the unused IAT thunk. No thunk is installed here; fail
// closed if it were ever called instead of silently fabricating a trace result.
#[no_mangle]
pub extern "C" fn witness_trace_dispatch() -> ! {
    std::process::abort()
}

/// # Safety
/// All pointers are witness-owned valid allocations described by record.py.
/// The original's returned allocation must remain readable after return.
#[no_mangle]
pub unsafe extern "C" fn record_returned(
    module: *const u16,
    rva: u64,
    slots: *const u64,
    output: *mut u8,
    size: u64,
    meta: *mut u64,
) -> i32 {
    if size > 256 * 1024 * 1024 {
        return 1;
    }
    let mut n = 0;
    while n < 32768 && *module.add(n) != 0 {
        n += 1;
    }
    if n == 32768 {
        return 2;
    }
    let path = PathBuf::from(OsString::from_wide(std::slice::from_raw_parts(module, n)));
    let Ok(base) = windows::load(&path) else {
        return 3;
    };
    let mut call = abi::Call::new(base + rva as usize);
    call.slots
        .copy_from_slice(std::slice::from_raw_parts(slots, 32));
    let result = call.run();
    *meta = result.rax;
    *meta.add(1) = match *meta.add(3) {
        0 => (result.rax == 0) as u64,
        1 => (result.rax != 0) as u64,
        2 => (result.rax == *meta.add(2)) as u64,
        _ => return 4,
    };
    if size != 0 {
        if result.rax == 0 {
            return 5;
        }
        std::ptr::copy_nonoverlapping(result.rax as *const u8, output, size as usize);
    }
    0
}

use std::{
    ffi::{c_void, CString},
    os::windows::ffi::OsStrExt,
    path::Path,
};
pub type Handle = *mut c_void;
#[link(name = "kernel32")]
extern "system" {
    pub fn LoadLibraryExW(path: *const u16, file: Handle, flags: u32) -> Handle;
    pub fn GetProcAddress(module: Handle, name: *const u8) -> *mut c_void;
    pub fn VirtualAlloc(address: Handle, size: usize, kind: u32, protection: u32) -> Handle;
    pub fn VirtualProtect(address: Handle, size: usize, protection: u32, old: *mut u32) -> i32;
    pub fn FlushInstructionCache(process: Handle, address: Handle, size: usize) -> i32;
    pub fn GetCurrentProcess() -> Handle;
    pub fn IsProcessInJob(process: Handle, job: Handle, result: *mut i32) -> i32;
    pub fn SetErrorMode(mode: u32) -> u32;
    pub fn GetLastError() -> u32;
    pub fn SetLastError(value: u32);
    pub fn GetModuleFileNameW(module: Handle, buffer: *mut u16, size: u32) -> u32;
    pub fn GetModuleHandleExW(flags: u32, address: *const u16, module: *mut Handle) -> i32;
    pub fn GetCurrentThreadId() -> u32;
}
pub fn error() -> String {
    std::io::Error::last_os_error().to_string()
}
pub unsafe fn load(path: &Path) -> Result<usize, String> {
    let wide: Vec<_> = path.as_os_str().encode_wide().chain(Some(0)).collect();
    // DLL directory + System32/default directories; never change the process CWD.
    let h = LoadLibraryExW(wide.as_ptr(), std::ptr::null_mut(), 0x100 | 0x1000);
    if h.is_null() {
        Err(error())
    } else {
        Ok(h as usize)
    }
}
pub unsafe fn proc(module: usize, name: &str) -> Result<usize, String> {
    let name = CString::new(name).map_err(|e| e.to_string())?;
    let p = GetProcAddress(module as Handle, name.as_ptr().cast());
    if p.is_null() {
        Err(error())
    } else {
        Ok(p as usize)
    }
}
pub unsafe fn module_path(module: usize) -> String {
    let mut path = [0u16; 32768];
    let n = GetModuleFileNameW(module as Handle, path.as_mut_ptr(), path.len() as u32);
    String::from_utf16_lossy(&path[..n as usize])
}
pub unsafe fn provider(address: usize) -> Result<(String, Option<i32>), String> {
    let mut module = std::ptr::null_mut();
    if GetModuleHandleExW(6, address as *const u16, &mut module) == 0 {
        return Err(error());
    }
    let fma = proc(module as usize, "_get_FMA3_enable").ok().map(|p| {
        let get: unsafe extern "C" fn() -> i32 = std::mem::transmute(p);
        get()
    });
    Ok((module_path(module as usize), fma))
}
pub unsafe fn executable(code: &[u8]) -> Result<usize, String> {
    let p = VirtualAlloc(std::ptr::null_mut(), code.len(), 0x3000, 4);
    if p.is_null() {
        return Err(error());
    }
    std::ptr::copy_nonoverlapping(code.as_ptr(), p.cast(), code.len());
    let mut old = 0;
    if VirtualProtect(p, code.len(), 0x20, &mut old) == 0
        || FlushInstructionCache(GetCurrentProcess(), p, code.len()) == 0
    {
        return Err(error());
    }
    // Child-lifetime allocation. Never writable and executable simultaneously.
    Ok(p as usize)
}

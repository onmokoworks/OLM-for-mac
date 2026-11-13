//! Opaque flattened-byte lifecycle, NOT the original arbitrary-data semantics.
//! TODO: semantic comparison, interpolation, print/scan, editing and validation.
//! Host handles hold a length prefix followed by exact flattened bytes.
#![allow(non_upper_case_globals)]
use crate::ae::{check, Result, BAD};
use after_effects_sys::*;
use std::ptr;
#[cfg(test)]
#[path = "arbitrary_tests.rs"]
mod tests;
const LIMIT: usize = 16 * 1024 * 1024;
struct Handles<'a> {
    i: &'a PF_InData,
    s: *const PF_HandleSuite1,
}
impl Drop for Handles<'_> {
    fn drop(&mut self) {
        unsafe {
            if let Some(f) = (*self.i.pica_basicP).ReleaseSuite {
                f(kPFHandleSuite.as_ptr().cast(), kPFHandleSuiteVersion1 as _);
            }
        }
    }
}
unsafe fn handles(i: &PF_InData) -> Result<Handles<'_>> {
    let b = i.pica_basicP.as_ref().ok_or(BAD)?;
    b.ReleaseSuite.ok_or(BAD)?;
    let mut raw = ptr::null();
    check(b.AcquireSuite.ok_or(BAD)?(
        kPFHandleSuite.as_ptr().cast(),
        kPFHandleSuiteVersion1 as _,
        &mut raw,
    ) as _)?;
    let h = Handles { i, s: raw.cast() };
    h.s.as_ref().ok_or(BAD)?;
    Ok(h)
}
pub unsafe fn new(i: &PF_InData, flat: &[u8]) -> Result<PF_ArbitraryH> {
    if flat.len() > LIMIT {
        return Err(BAD);
    }
    let h = handles(i)?;
    let s = &*h.s;
    let lock = s.host_lock_handle.ok_or(BAD)?;
    let unlock = s.host_unlock_handle.ok_or(BAD)?;
    let free = s.host_dispose_handle.ok_or(BAD)?;
    let handle = s.host_new_handle.ok_or(BAD)?((flat.len() + 4) as _);
    if handle.is_null() {
        return Err(PF_Err_OUT_OF_MEMORY as _);
    }
    let data = lock(handle).cast::<u8>();
    if data.is_null() {
        free(handle);
        return Err(BAD);
    }
    ptr::copy_nonoverlapping((flat.len() as u32).to_le_bytes().as_ptr(), data, 4);
    ptr::copy_nonoverlapping(flat.as_ptr(), data.add(4), flat.len());
    unlock(handle);
    Ok(handle)
}
unsafe fn read(i: &PF_InData, handle: PF_ArbitraryH) -> Result<Vec<u8>> {
    if handle.is_null() {
        return Err(BAD);
    }
    let h = handles(i)?;
    let s = &*h.s;
    let size = s.host_get_handle_size.ok_or(BAD)?(handle) as usize;
    if !(4..=LIMIT + 4).contains(&size) {
        return Err(BAD);
    }
    let unlock = s.host_unlock_handle.ok_or(BAD)?;
    let data = s.host_lock_handle.ok_or(BAD)?(handle).cast::<u8>();
    if data.is_null() {
        return Err(BAD);
    }
    let len = u32::from_le_bytes(std::slice::from_raw_parts(data, 4).try_into().unwrap()) as usize;
    let result = if len == size - 4 {
        Ok(std::slice::from_raw_parts(data.add(4), len).to_vec())
    } else {
        Err(BAD)
    };
    unlock(handle);
    result
}
pub unsafe fn dispose(i: &PF_InData, handle: PF_ArbitraryH) -> Result<()> {
    if !handle.is_null() {
        let h = handles(i)?;
        (*h.s).host_dispose_handle.ok_or(BAD)?(handle);
    }
    Ok(())
}
pub unsafe fn callback(i: &PF_InData, e: &mut PF_ArbParamsExtra) -> Result<()> {
    match e.which_function {
        PF_Arbitrary_NEW_FUNC => {
            *e.u.new_func_params.arbPH.as_mut().ok_or(BAD)? =
                new(i, crate::params::arbitrary_default(e.id).ok_or(BAD)?)?;
        }
        PF_Arbitrary_DISPOSE_FUNC => dispose(i, e.u.dispose_func_params.arbH)?,
        PF_Arbitrary_COPY_FUNC => {
            let a = e.u.copy_func_params;
            *a.dst_arbPH.as_mut().ok_or(BAD)? = new(i, &read(i, a.src_arbH)?)?;
        }
        PF_Arbitrary_FLAT_SIZE_FUNC => {
            let a = e.u.flat_size_func_params;
            *a.flat_data_sizePLu.as_mut().ok_or(BAD)? = read(i, a.arbH)?.len() as _;
        }
        PF_Arbitrary_FLATTEN_FUNC => {
            let a = e.u.flatten_func_params;
            let bytes = read(i, a.arbH)?;
            if a.flat_dataPV.is_null() || (a.buf_sizeLu as usize) < bytes.len() {
                return Err(BAD);
            }
            ptr::copy_nonoverlapping(bytes.as_ptr(), a.flat_dataPV.cast(), bytes.len());
        }
        PF_Arbitrary_UNFLATTEN_FUNC => {
            let a = e.u.unflatten_func_params;
            if a.buf_sizeLu as usize > LIMIT || (a.flat_dataPV.is_null() && a.buf_sizeLu != 0) {
                return Err(BAD);
            }
            let bytes = if a.buf_sizeLu == 0 {
                &[]
            } else {
                std::slice::from_raw_parts(a.flat_dataPV.cast(), a.buf_sizeLu as usize)
            };
            *a.arbPH.as_mut().ok_or(BAD)? = new(i, bytes)?;
        }
        PF_Arbitrary_COMPARE_FUNC => {
            let a = e.u.compare_func_params;
            *a.compareP.as_mut().ok_or(BAD)? = if read(i, a.a_arbH)? == read(i, a.b_arbH)? {
                PF_ArbCompare_EQUAL
            } else {
                PF_ArbCompare_NOT_EQUAL
            };
        }
        PF_Arbitrary_INTERP_FUNC => {
            let a = e.u.interp_func_params;
            let left = read(i, a.left_arbH)?;
            let right = read(i, a.right_arbH)?;
            // Never invent interpolation of an unknown format. Exact endpoints only.
            let selected = if a.tF == 0.0 || left == right {
                left
            } else if a.tF == 1.0 {
                right
            } else {
                return Err(BAD);
            };
            *a.interpPH.as_mut().ok_or(BAD)? = new(i, &selected)?;
        }
        _ => return Err(BAD),
    }
    Ok(())
}

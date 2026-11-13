//! Tests the opaque lifecycle without AE or an original binary.
use super::*;
use std::{
    collections::HashMap,
    ffi::{c_char, c_void},
    sync::{
        atomic::{AtomicI32, Ordering},
        LazyLock, Mutex,
    },
};
static MEMORY: LazyLock<Mutex<HashMap<usize, Box<[u8]>>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));
static SUITES: AtomicI32 = AtomicI32::new(0);
unsafe extern "C" fn alloc(size: A_HandleSize) -> PF_Handle {
    let mut bytes = vec![0; size as usize].into_boxed_slice();
    let h = Box::into_raw(Box::new(bytes.as_mut_ptr()));
    MEMORY.lock().unwrap().insert(h as usize, bytes);
    h.cast()
}
unsafe extern "C" fn lock(h: PF_Handle) -> *mut c_void {
    (*h).cast()
}
unsafe extern "C" fn unlock(_: PF_Handle) {}
unsafe extern "C" fn free(h: PF_Handle) {
    MEMORY.lock().unwrap().remove(&(h as usize)).unwrap();
    drop(Box::from_raw(h));
}
unsafe extern "C" fn size(h: PF_Handle) -> A_HandleSize {
    MEMORY.lock().unwrap()[&(h as usize)].len() as _
}
static HANDLES: PF_HandleSuite1 = PF_HandleSuite1 {
    host_new_handle: Some(alloc),
    host_lock_handle: Some(lock),
    host_unlock_handle: Some(unlock),
    host_dispose_handle: Some(free),
    host_get_handle_size: Some(size),
    host_resize_handle: None,
};
unsafe extern "C" fn acquire(_: *const c_char, _: i32, out: *mut *const c_void) -> SPErr {
    SUITES.fetch_add(1, Ordering::SeqCst);
    *out = (&HANDLES as *const PF_HandleSuite1).cast();
    0
}
unsafe extern "C" fn release(_: *const c_char, _: i32) -> SPErr {
    SUITES.fetch_sub(1, Ordering::SeqCst);
    0
}

#[test]
fn opaque_callback_roundtrip_copy_compare_and_refusal() {
    unsafe {
        let mut basic: SPBasicSuite = std::mem::zeroed();
        basic.AcquireSuite = Some(acquire);
        basic.ReleaseSuite = Some(release);
        let mut i: PF_InData = std::mem::zeroed();
        i.pica_basicP = &mut basic;
        for bytes in [
            vec![],
            vec![0, 255, 128, 7],
            (0..325).map(|x| (x * 73) as u8).collect(),
        ] {
            let mut e: PF_ArbParamsExtra = std::mem::zeroed();
            let mut h = ptr::null_mut();
            e.which_function = PF_Arbitrary_UNFLATTEN_FUNC;
            e.u.unflatten_func_params.buf_sizeLu = bytes.len() as _;
            e.u.unflatten_func_params.flat_dataPV = bytes.as_ptr().cast();
            e.u.unflatten_func_params.arbPH = &mut h;
            callback(&i, &mut e).unwrap();
            assert_eq!(read(&i, h).unwrap(), bytes);
            let mut copied = ptr::null_mut();
            e.which_function = PF_Arbitrary_COPY_FUNC;
            e.u.copy_func_params.src_arbH = h;
            e.u.copy_func_params.dst_arbPH = &mut copied;
            callback(&i, &mut e).unwrap();
            let mut n = 999;
            e.which_function = PF_Arbitrary_FLAT_SIZE_FUNC;
            e.u.flat_size_func_params.arbH = copied;
            e.u.flat_size_func_params.flat_data_sizePLu = &mut n;
            callback(&i, &mut e).unwrap();
            assert_eq!(n as usize, bytes.len());
            let mut flat = vec![0xAA; bytes.len() + 8];
            e.which_function = PF_Arbitrary_FLATTEN_FUNC;
            e.u.flatten_func_params.arbH = copied;
            e.u.flatten_func_params.buf_sizeLu = bytes.len() as _;
            e.u.flatten_func_params.flat_dataPV = flat.as_mut_ptr().cast();
            callback(&i, &mut e).unwrap();
            assert_eq!(&flat[..bytes.len()], bytes);
            assert_eq!(&flat[bytes.len()..], &[0xAA; 8]);
            let mut comparison = PF_ArbCompare_NOT_EQUAL;
            e.which_function = PF_Arbitrary_COMPARE_FUNC;
            e.u.compare_func_params.a_arbH = h;
            e.u.compare_func_params.b_arbH = copied;
            e.u.compare_func_params.compareP = &mut comparison;
            callback(&i, &mut e).unwrap();
            assert_eq!(comparison, PF_ArbCompare_EQUAL);
            let different = new(&i, &[34, 7]).unwrap();
            let mut interpolated = ptr::null_mut();
            e.which_function = PF_Arbitrary_INTERP_FUNC;
            e.u.interp_func_params.left_arbH = h;
            e.u.interp_func_params.right_arbH = different;
            e.u.interp_func_params.tF = 0.5;
            e.u.interp_func_params.interpPH = &mut interpolated;
            assert_eq!(callback(&i, &mut e), Err(BAD));
            assert!(interpolated.is_null());
            e.u.interp_func_params.tF = 0.0;
            callback(&i, &mut e).unwrap();
            assert_eq!(read(&i, interpolated).unwrap(), bytes);
            for handle in [h, copied, different, interpolated] {
                e.which_function = PF_Arbitrary_DISPOSE_FUNC;
                e.u.dispose_func_params.arbH = handle;
                callback(&i, &mut e).unwrap();
            }
        }
        assert_eq!(SUITES.load(Ordering::SeqCst), 0);
        assert!(MEMORY.lock().unwrap().is_empty());
    }
}

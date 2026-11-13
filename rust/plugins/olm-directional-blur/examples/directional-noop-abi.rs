use olm_ae::sys::{PF_InData, PF_UtilCallbacks};
fn main() {
    let utils = std::mem::offset_of!(PF_InData, utils);
    let effect = std::mem::offset_of!(PF_InData, effect_ref);
    let copy = std::mem::offset_of!(PF_UtilCallbacks, copy);
    println!("PF_InData.utils={utils:#x} effect_ref={effect:#x} PF_UtilCallbacks.copy={copy:#x}");
    #[cfg(all(target_os = "windows", target_pointer_width = "64"))]
    assert_eq!((utils, effect, copy), (0xb0, 0xb8, 0x40));
}

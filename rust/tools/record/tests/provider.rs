//! Synthetic IPP-shaped import, not Intel IPP evidence.
#[no_mangle]
pub extern "C" fn ippRecordFixture(x: u64) -> u64 { x.wrapping_add(17) }

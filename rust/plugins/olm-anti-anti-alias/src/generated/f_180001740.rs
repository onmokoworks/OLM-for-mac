#[no_mangle]
pub unsafe extern "C" fn autoport_180001740(r: f32, g: f32, b: f32, a: f32, p: *const u8) -> u8 {
    let dr = (core::ptr::read_unaligned(p.add(1)) as f32) - r * 255.0_f32;
    if f32::from_bits(dr.to_bits() & 0x7fff_ffff) > 0.051_f32 {
        return 0;
    }
    let dg = (core::ptr::read_unaligned(p.add(2)) as f32) - g * 255.0_f32;
    if f32::from_bits(dg.to_bits() & 0x7fff_ffff) > 0.051_f32 {
        return 0;
    }
    let db = (core::ptr::read_unaligned(p.add(3)) as f32) - b * 255.0_f32;
    if f32::from_bits(db.to_bits() & 0x7fff_ffff) > 0.051_f32 {
        return 0;
    }
    let da = (core::ptr::read_unaligned(p) as f32) - a * 255.0_f32;
    if f32::from_bits(da.to_bits() & 0x7fff_ffff) > 0.051_f32 {
        return 0;
    }
    1
}

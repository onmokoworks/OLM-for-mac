#[inline]
fn matches_channel(value: u16, target: f32) -> bool {
    let scaled = target * 32768.0_f32;
    let difference = (value as f32) - scaled;
    let magnitude = f32::from_bits(difference.to_bits() & 0x7fff_ffff);
    !(magnitude > 6.5536_f32)
}

#[no_mangle]
pub unsafe extern "C" fn autoport_180001680(r: f32, g: f32, b: f32, a: f32, p: *const u8) -> u8 {
    let red = core::ptr::read_unaligned(p.add(2).cast::<u16>());
    if !matches_channel(red, r) {
        return 0;
    }
    let green = core::ptr::read_unaligned(p.add(4).cast::<u16>());
    if !matches_channel(green, g) {
        return 0;
    }
    let blue = core::ptr::read_unaligned(p.add(6).cast::<u16>());
    if !matches_channel(blue, b) {
        return 0;
    }
    let alpha = core::ptr::read_unaligned(p.cast::<u16>());
    matches_channel(alpha, a) as u8
}

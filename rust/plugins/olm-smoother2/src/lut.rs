//! Captured Windows LUT bytes, parsed from the authoritative C++ headers at build time.
static DECODE: &[u8; 40000] = include_bytes!(concat!(env!("OUT_DIR"), "/decode.bin"));
static ENCODE: &[u8; 40000] = include_bytes!(concat!(env!("OUT_DIR"), "/encode.bin"));

fn interpolate(table: &[u8; 40000], v: f32) -> f32 {
    if !(v > 0.0) {
        return 0.0;
    }
    if v >= 1.0 {
        return 1.0;
    }
    let scaled = v as f64 * 9999.0;
    let index = scaled as usize;
    let fraction = scaled - index as f64;
    let at = index * 4;
    let lower = f32::from_le_bytes(table[at..at + 4].try_into().unwrap());
    let upper = f32::from_le_bytes(table[at + 4..at + 8].try_into().unwrap());
    let upper_term = upper as f64 * fraction;
    let lower_term = lower as f64 * (1.0 - fraction);
    (upper_term + lower_term) as f32
}

pub fn decode(v: f32) -> f32 {
    interpolate(DECODE, v)
}
pub fn encode(v: f32) -> f32 {
    interpolate(ENCODE, v)
}

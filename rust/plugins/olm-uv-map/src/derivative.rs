#[inline]
fn abs_bits(x: f32) -> f32 {
    f32::from_bits(x.to_bits() & 0x7fff_ffff)
}

#[no_mangle]
pub unsafe extern "C" fn autoport_180004780(
    input: *const f32,
    min_u: *mut f32,
    max_u: *mut f32,
    min_v: *mut f32,
    max_v: *mut f32,
) {
    let center_u = *input;
    let left_u = abs_bits(*input.add(4) - center_u);
    let right_u = abs_bits(*input.add(8) - center_u);
    let down_u = abs_bits(*input.add(16) - center_u);
    let center_v = *input.add(1);
    let up_u = abs_bits(*input.add(12) - center_u);
    let left_v = abs_bits(*input.add(5) - center_v);
    let right_v = abs_bits(*input.add(9) - center_v);
    let up_v = abs_bits(*input.add(13) - center_v);
    let down_v = abs_bits(*input.add(17) - center_v);

    if 0.0 < *input.add(7) {
        if *max_u <= left_u && left_u != *max_u {
            *max_u = left_u;
        }
        if *max_v <= left_v && left_v != *max_v {
            *max_v = left_v;
        }
    }
    if 0.0 < *input.add(11) {
        if *max_u <= right_u && right_u != *max_u {
            *max_u = right_u;
        }
        if *max_v <= right_v && right_v != *max_v {
            *max_v = right_v;
        }
    }
    if 0.0 < *input.add(15) {
        if *max_u <= up_u && up_u != *max_u {
            *max_u = up_u;
        }
        if *max_v <= up_v && up_v != *max_v {
            *max_v = up_v;
        }
    }
    if 0.0 < *input.add(19) {
        if *max_u <= down_u && down_u != *max_u {
            *max_u = down_u;
        }
        if *max_v <= down_v && down_v != *max_v {
            *max_v = down_v;
        }
    }

    *min_u = *max_u;
    *min_v = *max_v;

    if 0.0 < *input.add(7) {
        if 0.0 < left_u && left_u < *min_u {
            *min_u = left_u;
        }
        if 0.0 < left_v && left_v < *min_v {
            *min_v = left_v;
        }
    }
    if 0.0 < *input.add(11) {
        if 0.0 < right_u && right_u < *min_u {
            *min_u = right_u;
        }
        if 0.0 < right_v && right_v < *min_v {
            *min_v = right_v;
        }
    }
    if 0.0 < *input.add(15) {
        if 0.0 < up_u && up_u < *min_u {
            *min_u = up_u;
        }
        if 0.0 < up_v && up_v < *min_v {
            *min_v = up_v;
        }
    }
    if 0.0 < *input.add(19) {
        if 0.0 < down_u && down_u < *min_u {
            *min_u = down_u;
        }
        if 0.0 < down_v && down_v < *min_v {
            *min_v = down_v;
        }
    }
}

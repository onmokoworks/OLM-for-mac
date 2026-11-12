#[inline(always)]
unsafe fn load_f32(p: *const f32, byte_offset: usize) -> f32 {
    unsafe { core::ptr::read_unaligned(p.cast::<u8>().add(byte_offset).cast::<f32>()) }
}

#[inline(always)]
unsafe fn store_f32(p: *mut f32, byte_offset: usize, x: f32) {
    unsafe { core::ptr::write_unaligned(p.cast::<u8>().add(byte_offset).cast::<f32>(), x) }
}

#[inline(always)]
fn clamp_channel(x: f32) -> f32 {
    if x < 0.0_f32 {
        0.0_f32
    } else if 1.0_f32 < x {
        1.0_f32
    } else {
        x
    }
}

#[inline(always)]
unsafe fn copy_argb(src: *const f32, dst: *mut f32) {
    unsafe {
        let upper = core::ptr::read_unaligned(src.cast::<u8>().add(8).cast::<u64>());
        let lower = core::ptr::read_unaligned(src.cast::<u64>());
        core::ptr::write_unaligned(dst.cast::<u64>(), lower);
        core::ptr::write_unaligned(dst.cast::<u8>().add(8).cast::<u64>(), upper);
    }
}

#[inline(always)]
unsafe fn rgb_distance(x: *const f32, y: *const f32) -> f32 {
    unsafe {
        let blue = load_f32(x, 12) - load_f32(y, 12);
        let red = load_f32(x, 4) - load_f32(y, 4);
        let green = load_f32(x, 8) - load_f32(y, 8);
        let rr = red * red;
        let gg = green * green;
        let bb = blue * blue;
        let rg = rr + gg;
        let squared = rg + bb;
        squared.sqrt()
    }
}

#[no_mangle]
pub unsafe extern "C" fn autoport_18000a630(
    p: *const f32,
    t: *mut f32,
    a: *const f32,
    b: *const f32,
    u: *mut f32,
    v: *mut f32,
    da: *mut f32,
    db: *mut f32,
    d: *const f32,
    len2: f32,
) -> f32 {
    unsafe {
        let distance_a = rgb_distance(p, a);
        store_f32(da, 0, distance_a + 0.0001_f32);
        let distance_b = rgb_distance(p, b);
        store_f32(db, 0, distance_b + 0.0001_f32);

        let green_term = (load_f32(p, 8) - load_f32(a, 8)) * load_f32(d, 8);
        let red_term = (load_f32(p, 4) - load_f32(a, 4)) * load_f32(d, 4);
        let gr = green_term + red_term;
        let blue_term = (load_f32(p, 12) - load_f32(a, 12)) * load_f32(d, 12);
        let numerator = gr + blue_term;
        let q = numerator / len2;

        if q >= 1.0_f32 {
            copy_argb(p, v);
            copy_argb(a, u);
            store_f32(t, 0, 1.0_f32);
            return load_f32(db, 0);
        }
        if q <= 0.0_f32 {
            copy_argb(b, v);
            copy_argb(p, u);
            store_f32(t, 0, 0.0_f32);
            return load_f32(da, 0);
        }

        let red_product = load_f32(d, 4) * q;
        let ur = clamp_channel(load_f32(p, 4) - red_product);
        store_f32(u, 4, ur);

        let green_product = q * load_f32(d, 8);
        let ug = clamp_channel(load_f32(p, 8) - green_product);
        store_f32(u, 8, ug);

        let blue_product = q * load_f32(d, 12);
        let ub = clamp_channel(load_f32(p, 12) - blue_product);
        store_f32(u, 12, ub);

        let complement = 1.0_f32 - q;
        let red_product = complement * ur;
        let vr = clamp_channel((load_f32(p, 4) - red_product) / q);
        store_f32(v, 4, vr);

        let green_product = complement * load_f32(u, 8);
        let vg = clamp_channel((load_f32(p, 8) - green_product) / q);
        store_f32(v, 8, vg);

        let blue_product = complement * load_f32(u, 12);
        let vb = clamp_channel((load_f32(p, 12) - blue_product) / q);
        store_f32(v, 12, vb);

        store_f32(t, 0, q);
        let distance_u = rgb_distance(u, a);
        let distance_v = rgb_distance(v, b);
        let padded_u = distance_u + 0.0001_f32;
        let padded_v = distance_v + 0.0001_f32;
        padded_u + padded_v
    }
}

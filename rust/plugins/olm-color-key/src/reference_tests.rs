extern "C" {
    fn olm_ck_cpp_color(space: i32, input: *const f32, output: *mut f32);
    fn olm_ck_cpp_distance(
        input: *const u8,
        w: i32,
        h: i32,
        kind: i32,
        dx: f32,
        dy: f32,
        output: *mut f32,
    );
    fn olm_ck_cpp_boundary(input: *const u8, w: i32, h: i32, output: *mut u8);
}
#[test]
fn cpp_color_math() {
    let mut seed = 0x53a01234u32;
    let mut next = || {
        seed ^= seed << 13;
        seed ^= seed >> 17;
        seed ^= seed << 5;
        seed
    };
    for space in 1..=6 {
        for _ in 0..4096 {
            let rgb = std::array::from_fn(|_| (next() as f64 / u32::MAX as f64 * 4.0 - 1.0) as f32);
            let mut expected = [0.0; 3];
            unsafe {
                olm_ck_cpp_color(space, rgb.as_ptr(), expected.as_mut_ptr());
            }
            let actual = crate::color::convert(rgb, space);
            assert_eq!(
                actual.map(f32::to_bits),
                expected.map(f32::to_bits),
                "space={space} rgb={rgb:?}"
            );
        }
    }
}
#[test]
fn cpp_distance_scans() {
    let mut seed = 0x66f01234u32;
    let mut next = || {
        seed ^= seed << 13;
        seed ^= seed >> 17;
        seed ^= seed << 5;
        seed
    };
    for (w, h) in [(1, 1), (1, 17), (19, 1), (3, 7), (11, 7), (31, 19)] {
        for (dx, dy) in [(1.0, 1.0), (2.0, 4.0), (4.0, 2.0)] {
            for _ in 0..12 {
                let mask: Vec<_> = (0..w * h).map(|_| (next() % 7 == 0) as u8).collect();
                let mut boundary = vec![0; w * h];
                unsafe {
                    olm_ck_cpp_boundary(mask.as_ptr(), w as i32, h as i32, boundary.as_mut_ptr());
                }
                assert_eq!(crate::distance::boundary(&mask, w, h), boundary);
                for kind in 1..=3 {
                    let mut expected = vec![0.0; w * h];
                    unsafe {
                        olm_ck_cpp_distance(
                            mask.as_ptr(),
                            w as i32,
                            h as i32,
                            kind,
                            dx,
                            dy,
                            expected.as_mut_ptr(),
                        );
                    }
                    let actual = crate::distance::distance(&mask, w, h, kind, dx, dy, None);
                    assert_eq!(
                        actual.iter().map(|v| v.to_bits()).collect::<Vec<_>>(),
                        expected.iter().map(|v| v.to_bits()).collect::<Vec<_>>(),
                        "{w}x{h} kind={kind} step={dx},{dy}"
                    );
                }
            }
        }
    }
}

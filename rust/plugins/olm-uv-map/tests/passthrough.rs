use olm_uv_map::algorithm::{render, Layout, Params};
#[test]
fn absent_texture_clears_active_pixels_and_keeps_padding() {
    for bytes in [4, 8, 16] {
        let l = Layout {
            width: 3,
            height: 2,
            row_bytes: 4 * bytes,
            bytes_per_pixel: bytes,
            origin: (0, 0),
        };
        let input = vec![0; 8 * bytes];
        let mut output = vec![0xa5; 8 * bytes];
        render(&input, l, None, &mut output, l, Params::default()).unwrap();
        for y in 0..2 {
            assert!(output[y * 4 * bytes..y * 4 * bytes + 3 * bytes]
                .iter()
                .all(|x| *x == 0));
            assert!(output[y * 4 * bytes + 3 * bytes..(y + 1) * 4 * bytes]
                .iter()
                .all(|x| *x == 0xa5));
        }
    }
}
#[test]
fn nearest_uses_texture_dimensions_and_inverts_v() {
    let uv = [255, 255, 255, 0, 255, 0, 0, 0];
    let tex = [255, 1, 2, 3, 128, 4, 5, 6, 64, 7, 8, 9];
    let a = Layout {
        width: 2,
        height: 1,
        row_bytes: 8,
        bytes_per_pixel: 4,
        origin: (0, 0),
    };
    let t = Layout {
        width: 3,
        height: 1,
        row_bytes: 12,
        ..a
    };
    let mut out = [0; 8];
    render(
        &uv,
        a,
        Some((&tex, t)),
        &mut out,
        a,
        Params {
            method: 1,
            smoothness: 0.5,
        },
    )
    .unwrap();
    assert_eq!(out, [64, 7, 8, 9, 255, 1, 2, 3]);
}

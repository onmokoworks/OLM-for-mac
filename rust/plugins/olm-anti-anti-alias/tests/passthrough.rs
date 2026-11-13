use olm_anti_anti_alias::algorithm::{render, Layout};
#[test]
fn preserves_bits_crop_and_padding_all_depths() {
    for bytes in [4, 8, 16] {
        let a = Layout {
            width: 3,
            height: 2,
            row_bytes: 3 * bytes + 7,
            bytes_per_pixel: bytes,
            origin: (-1, 5),
        };
        let b = Layout {
            width: 2,
            height: 2,
            row_bytes: 2 * bytes + 5,
            bytes_per_pixel: bytes,
            origin: (0, 5),
        };
        let input: Vec<u8> = (0..a.span().unwrap())
            .map(|x| x.wrapping_mul(73) as u8)
            .collect();
        let mut output = vec![0xAA; b.row_bytes * b.height];
        render(&input, a, &mut output, b).unwrap();
        for y in 0..2 {
            assert_eq!(
                &output[y * b.row_bytes..y * b.row_bytes + 2 * bytes],
                &input[y * a.row_bytes + bytes..y * a.row_bytes + 3 * bytes]
            );
            assert!(output[y * b.row_bytes + 2 * bytes..(y + 1) * b.row_bytes]
                .iter()
                .all(|x| *x == 0xAA));
        }
    }
}
#[test]
fn rejects_invalid_span_before_writing() {
    let a = Layout {
        width: usize::MAX,
        height: 2,
        row_bytes: 16,
        bytes_per_pixel: 16,
        origin: (0, 0),
    };
    let mut out = [0xAA; 16];
    assert!(render(&[], a, &mut out, a).is_err());
    assert_eq!(out, [0xAA; 16]);
}

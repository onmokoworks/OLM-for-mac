use olm_uv_map::algorithm::{render, Layout, Params};
#[test]
fn m1_d8() {
    let a = Layout {
        width: 3,
        height: 7,
        row_bytes: 12,
        bytes_per_pixel: 4,
        origin: (0, 0),
    };
    let t = Layout {
        width: 1,
        height: 1,
        row_bytes: 4,
        ..a
    };
    let mut output = vec![0; 84];
    render(
        include_bytes!("golden/m1-d8-uv.bin"),
        a,
        Some((include_bytes!("golden/m1-d8-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 1,
            smoothness: 0.0f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m1-d8-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}
#[test]
fn m2_d8() {
    let a = Layout {
        width: 31,
        height: 19,
        row_bytes: 124,
        bytes_per_pixel: 4,
        origin: (0, 0),
    };
    let t = Layout {
        width: 1,
        height: 5,
        row_bytes: 4,
        ..a
    };
    let mut output = vec![0; 2356];
    render(
        include_bytes!("golden/m2-d8-uv.bin"),
        a,
        Some((include_bytes!("golden/m2-d8-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 2,
            smoothness: 0.5f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m2-d8-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}
#[test]
fn m3_d8() {
    let a = Layout {
        width: 11,
        height: 7,
        row_bytes: 44,
        bytes_per_pixel: 4,
        origin: (0, 0),
    };
    let t = Layout {
        width: 2,
        height: 1,
        row_bytes: 8,
        ..a
    };
    let mut output = vec![0; 308];
    render(
        include_bytes!("golden/m3-d8-uv.bin"),
        a,
        Some((include_bytes!("golden/m3-d8-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 3,
            smoothness: 1.0f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m3-d8-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}
#[test]
fn m1_d16() {
    let a = Layout {
        width: 3,
        height: 7,
        row_bytes: 24,
        bytes_per_pixel: 8,
        origin: (0, 0),
    };
    let t = Layout {
        width: 1,
        height: 1,
        row_bytes: 8,
        ..a
    };
    let mut output = vec![0; 168];
    render(
        include_bytes!("golden/m1-d16-uv.bin"),
        a,
        Some((include_bytes!("golden/m1-d16-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 1,
            smoothness: 0.0f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m1-d16-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}
#[test]
fn m2_d16() {
    let a = Layout {
        width: 31,
        height: 19,
        row_bytes: 248,
        bytes_per_pixel: 8,
        origin: (0, 0),
    };
    let t = Layout {
        width: 1,
        height: 5,
        row_bytes: 8,
        ..a
    };
    let mut output = vec![0; 4712];
    render(
        include_bytes!("golden/m2-d16-uv.bin"),
        a,
        Some((include_bytes!("golden/m2-d16-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 2,
            smoothness: 0.5f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m2-d16-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}
#[test]
fn m3_d16() {
    let a = Layout {
        width: 11,
        height: 7,
        row_bytes: 88,
        bytes_per_pixel: 8,
        origin: (0, 0),
    };
    let t = Layout {
        width: 2,
        height: 1,
        row_bytes: 16,
        ..a
    };
    let mut output = vec![0; 616];
    render(
        include_bytes!("golden/m3-d16-uv.bin"),
        a,
        Some((include_bytes!("golden/m3-d16-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 3,
            smoothness: 1.0f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m3-d16-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}
#[test]
fn m1_d32() {
    let a = Layout {
        width: 3,
        height: 7,
        row_bytes: 48,
        bytes_per_pixel: 16,
        origin: (0, 0),
    };
    let t = Layout {
        width: 1,
        height: 1,
        row_bytes: 16,
        ..a
    };
    let mut output = vec![0; 336];
    render(
        include_bytes!("golden/m1-d32-uv.bin"),
        a,
        Some((include_bytes!("golden/m1-d32-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 1,
            smoothness: 0.0f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m1-d32-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}
#[test]
fn m2_d32() {
    let a = Layout {
        width: 31,
        height: 19,
        row_bytes: 496,
        bytes_per_pixel: 16,
        origin: (0, 0),
    };
    let t = Layout {
        width: 1,
        height: 5,
        row_bytes: 16,
        ..a
    };
    let mut output = vec![0; 9424];
    render(
        include_bytes!("golden/m2-d32-uv.bin"),
        a,
        Some((include_bytes!("golden/m2-d32-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 2,
            smoothness: 0.5f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m2-d32-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}
#[test]
fn m3_d32() {
    let a = Layout {
        width: 11,
        height: 7,
        row_bytes: 176,
        bytes_per_pixel: 16,
        origin: (0, 0),
    };
    let t = Layout {
        width: 2,
        height: 1,
        row_bytes: 32,
        ..a
    };
    let mut output = vec![0; 1232];
    render(
        include_bytes!("golden/m3-d32-uv.bin"),
        a,
        Some((include_bytes!("golden/m3-d32-texture.bin"), t)),
        &mut output,
        a,
        Params {
            method: 3,
            smoothness: 1.0f32,
        },
    )
    .unwrap();
    let expected = include_bytes!("golden/m3-d32-expected.bin");
    assert_eq!(output.len(), expected.len());
    assert!(
        output.iter().zip(expected).all(|(a, b)| a == b),
        "first differing byte: {:?}",
        output.iter().zip(expected).position(|(a, b)| a != b)
    );
}

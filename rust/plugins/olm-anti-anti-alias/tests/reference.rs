//! Contract tests grounded in the manual and native selector/pixel routines.
use olm_anti_anti_alias::{
    algorithm::{detect, render_with, Layout, Settings},
    palette,
};
fn layout() -> Layout {
    Layout {
        width: 9,
        height: 3,
        row_bytes: 36,
        bytes_per_pixel: 4,
        origin: (0, 0),
    }
}
fn stripes() -> Vec<u8> {
    (0..3)
        .flat_map(|_| {
            (0..9).flat_map(|x| match x / 3 {
                0 => [255, 255, 0, 0],
                1 => [255, 0, 255, 0],
                _ => [255, 0, 0, 255],
            })
        })
        .collect()
}
#[test]
fn detects_three_plateaus_in_row_order_and_excludes_existing() {
    let found = detect(&stripes(), layout(), &[], 100).unwrap();
    assert_eq!(
        found,
        [[1., 1., 0., 0.], [1., 0., 1., 0.], [1., 0., 0., 1.]]
    );
    assert_eq!(
        detect(&stripes(), layout(), &found[..1], 1).unwrap(),
        [found[1]]
    );
    let mut nonopaque = stripes();
    for p in nonopaque.chunks_mut(4) {
        p[0] = 254
    }
    assert!(detect(&nonopaque, layout(), &[], 100).unwrap().is_empty());
}
#[test]
fn add_retains_first_active_black_and_fills_other_black_slots() {
    let active = [[1., 1., 0., 0.], [1., 0., 0., 0.], [1., 0., 0., 0.]];
    let (count, edits) = palette::additions(&stripes(), layout(), &active, false).unwrap();
    assert_eq!(count, 4);
    assert_eq!(edits, [(2, [1., 0., 1., 0.]), (3, [1., 0., 0., 1.])]);
}
#[test]
fn init_replaces_from_first_slot_without_decreasing_saved_count() {
    let (count, edits) = palette::additions(&stripes(), layout(), &[[0.; 4]; 7], true).unwrap();
    assert_eq!(count, 7);
    assert_eq!(edits.len(), 3);
    assert_eq!(edits[0].0, 0);
}
#[test]
fn automatic_render_does_not_mutate_saved_palette() {
    let settings = Settings {
        colors: vec![],
        automatic: true,
    };
    let mut output = vec![0; 108];
    render_with(&stripes(), layout(), &mut output, layout(), &settings).unwrap();
    assert_eq!(output, stripes());
    assert!(settings.colors.is_empty());
}
#[test]
fn partial_alpha_threshold_outputs_transparent_white() {
    let a = Layout {
        width: 3,
        height: 1,
        row_bytes: 12,
        bytes_per_pixel: 4,
        origin: (0, 0),
    };
    let input = [0, 4, 5, 6, 127, 4, 5, 6, 128, 4, 5, 6];
    let mut out = [0; 12];
    render_with(
        &input,
        a,
        &mut out,
        a,
        &Settings {
            colors: vec![[1., 1., 0., 0.], [1., 0., 1., 0.]],
            automatic: false,
        },
    )
    .unwrap();
    assert_eq!(&out[..8], &[0, 255, 255, 255, 0, 255, 255, 255]);
    assert_eq!(&out[8..], &input[8..]);
}

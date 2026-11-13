use crate::{algorithm, noise};
use olm_core::*;
#[path = "offset_witness_data.rs"]
mod data;

#[test]
fn smart32_negative_offset_cpp_and_pixel_support() {
    let phase = ((-318.36653167426726_f64 * 65536.0).round() * 2.663161090079238e-7) as f32;
    let mut underread_cells = Vec::new();
    for degrees in [-318.36653167426726_f64, 0.0, 1.0] {
        let offset = ((degrees * 65536.0).round() * 2.663161090079238e-7) as f32;
        noise::probe::TRACE.with(|v| *v.borrow_mut() = Some(Vec::new()));
        let (rust, width) = noise::generate(3, 7, 0.25, offset, 595);
        let indices = noise::probe::TRACE.with(|v| v.borrow_mut().take().unwrap());
        let mut cpp = vec![0.0; rust.len()];
        assert_eq!(
            unsafe { super::radial_noise(3, 7, 0.25, offset, 595, cpp.as_mut_ptr()) },
            width as i32
        );
        assert_eq!(
            rust.iter().map(|v| v.to_bits()).collect::<Vec<_>>(),
            cpp.iter().map(|v| v.to_bits()).collect::<Vec<_>>()
        );
        let cells: Vec<_> = indices
            .chunks_exact(2)
            .enumerate()
            .filter(|(_, v)| v.iter().any(|i| !(0..101).contains(i)))
            .map(|(i, v)| (i, v[0], v[1]))
            .collect();
        if degrees < 0.0 {
            underread_cells = cells;
        } else {
            assert!(cells.is_empty());
        }
    }
    assert!(!underread_cells.is_empty());
    let (plane, width) = noise::generate(3, 7, 0.25, phase, 595);
    let mut source_support = [false; 21];
    for fill in [-1.0, 1.0] {
        noise::probe::FILL.with(|v| v.set(fill));
        let (changed, _) = noise::generate(3, 7, 0.25, phase, 595);
        noise::probe::FILL.with(|v| v.set(0.0));
        for (i, affected) in source_support.iter_mut().enumerate() {
            *affected |= noise::sample(&plane, width, 0.25, i % 3, i / 3, true).to_bits()
                != noise::sample(&changed, width, 0.25, i % 3, i / 3, true).to_bits();
        }
    }
    let source_pixels: Vec<_> = (0..21).filter(|i| source_support[*i]).collect();
    assert_eq!(source_pixels, [18, 19]);
    println!("underread_sensitive_source_pixels={source_pixels:?}");
    let layout = Layout {
        width: 3,
        height: 7,
        stride: 48,
        depth: Depth::F32,
        origin: (0, 0),
    };
    let mut input = vec![0; layout.span().unwrap()];
    for (i, p) in data::INPUT.iter().enumerate() {
        ViewMut::new(&mut input, layout)
            .unwrap()
            .set(
                (i % 3) as _,
                (i / 3) as _,
                Pixel::F32([p[3], p[0], p[1], p[2]].map(|v| v as f32 * (1.0 / 255.0))),
            )
            .unwrap();
    }
    let params = algorithm::Params {
        rotation: true,
        center: [
            (-1.1078088915675215_f64 / 100.0 * 3.0 * 65536.0).round() / 65536.0,
            (2.7040483976804683_f64 / 100.0 * 7.0 * 65536.0).round() / 65536.0,
        ],
        strength: [0, 936],
        offset: [220, 500],
        mode: [1, 1],
        fade: [0, 100],
        repeat: true,
        ratio: 5.0,
        angle: (-201.29544059748778_f64 * 65536.0).round() / 65536.0,
        quality: 50.0,
        gain: 7.68382588089265,
        size: 0.0,
        noise: 60.100821069658025,
        noise_type: 1,
        seed: 595,
        phase,
        thickness: 1.0,
        downsample: 0.25,
    };
    let render = |fill| {
        noise::probe::FILL.with(|v| v.set(fill));
        let mut output = vec![0; layout.span().unwrap()];
        algorithm::render(
            &params,
            &View::new(&input, layout).unwrap(),
            &mut ViewMut::new(&mut output, layout).unwrap(),
            1,
        )
        .unwrap();
        noise::probe::FILL.with(|v| v.set(0.0));
        (0..21)
            .map(|i| {
                match View::new(&output, layout)
                    .unwrap()
                    .get(i % 3, i / 3)
                    .unwrap()
                {
                    Pixel::F32(v) => [v[1], v[2], v[3], v[0]].map(f32::to_bits),
                    _ => unreachable!(),
                }
            })
            .collect::<Vec<_>>()
    };
    let baseline = render(0.0);
    assert_eq!(
        baseline,
        data::EXPECTED,
        "Pure Smart32 must match the frozen integrated DLL"
    );
    let mut support = vec![false; 21];
    for fill in [-1.0, 1.0] {
        let changed = render(fill);
        for i in 0..21 {
            support[i] |= changed[i] != baseline[i];
        }
    }
    for i in data::MISMATCH_PIXELS {
        assert!(
            support[i],
            "mismatch outside under-read sensitivity support: {i}"
        );
    }
    let affected: Vec<_> = (0..21).filter(|i| support[*i]).collect();
    println!("phase_bits={:08x}; underread_cells={:?}; underread_sensitive_output_pixels={:?}; observed_mismatch_pixels={:?}",phase.to_bits(),underread_cells,affected,data::MISMATCH_PIXELS);
}

//! Seeded, host-free render cases. Each binary links exactly one plug-in rlib:
//! linking all ten together would collide on their exported AE entry symbols.
use olm_core::{Depth, Layout, Pixel, View, ViewMut};
use std::{collections::BTreeMap, fs, path::PathBuf};

#[path = "../../../plugins/olm-directional-blur/src/sha256.rs"]
mod sha256;

pub struct Case {
    pub index: usize,
    pub width: usize,
    pub height: usize,
    pub denominator: u32,
    pub depth: Depth,
    assignments: Vec<String>,
}
impl Case {
    pub fn scale(&self) -> f32 {
        1.0 / self.denominator as f32
    }
    pub fn number(&mut self, slot: usize, value: impl Into<f64>) {
        self.assignments
            .push(format!("{{\"slot\":{slot},\"value\":{}}}", value.into()));
    }
    pub fn color(&mut self, slot: usize, argb: [u8; 4]) -> [f32; 4] {
        self.assignments
            .push(format!("{{\"slot\":{slot},\"color\":{:?}}}", argb));
        argb.map(|x| x as f32 / 255.0)
    }
    pub fn point(&mut self, slot: usize, percent: [f64; 2]) {
        self.assignments
            .push(format!("{{\"slot\":{slot},\"components\":{:?}}}", percent));
    }
    pub fn angle(&mut self, slot: usize, degrees: f64) {
        self.assignments
            .push(format!("{{\"slot\":{slot},\"components\":[{degrees}]}}"));
    }
}

/// Integer-only xorshift32 input generator: same bytes on all targets.
fn rgba(seed: u32, w: usize, h: usize) -> Vec<u8> {
    let mut state = seed;
    let mut bytes = Vec::with_capacity(w * h * 4);
    for i in 0..w * h {
        state ^= state << 13;
        state ^= state >> 17;
        state ^= state << 5;
        let mut p = [
            (state >> 8) as u8,
            (state >> 16) as u8,
            state as u8,
            [0, 1, 32, 128, 254, 255][i % 6],
        ];
        // Exact palette hits, contours, and transparent nonblack RGB.
        if i % 7 == 0 {
            p = [255, 255, 255, 255];
        }
        if i % 11 == 0 {
            p = [0, 0, 0, 255];
        }
        bytes.extend(p);
    }
    bytes
}

pub fn run(name: &str, depths: &[Depth], render: fn(&mut Case, &View<'_>, &mut ViewMut<'_>)) {
    assert!(
        cfg!(target_endian = "little"),
        "golden byte contract is little-endian"
    );
    let args: Vec<_> = std::env::args().skip(1).collect();
    let export = match args.as_slice() {
        [] => None,
        [flag, dir] if flag == "--export" => Some(PathBuf::from(dir)),
        _ => panic!("usage: {name} [--export NEW_DIRECTORY]"),
    };
    if let Some(dir) = &export {
        fs::create_dir(dir).expect("use a fresh export directory");
    }
    let golden = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("golden.json");
    let expected = if export.is_none() {
        // golden.json is intentionally a flat string-to-string map with no escapes.
        let text = fs::read_to_string(golden).expect("verified golden.json required");
        let tokens: Vec<_> = text.split('"').skip(1).step_by(2).collect();
        assert_eq!(tokens.len() % 2, 0);
        tokens
            .chunks_exact(2)
            .map(|p| (p[0].to_owned(), p[1].to_owned()))
            .collect::<BTreeMap<_, _>>()
    } else {
        BTreeMap::new()
    };
    let mut records = Vec::new();
    let mut count = 0;
    for index in 0..18 {
        for &depth in depths {
            let (width, height) = [(9, 7), (11, 9), (17, 9)][index % 3];
            let denominator = [1, 2, 4][(index / 3) % 3];
            let mut case = Case {
                index,
                width,
                height,
                denominator,
                depth,
                assignments: vec![],
            };
            let bpc = match depth {
                Depth::U8 => 8,
                Depth::U16 => 16,
                Depth::F32 => 32,
            };
            let id = format!("{name}-{index:02}-{bpc}");
            let seed = 0x4f4c4d01u32.wrapping_add(index as u32 * 7919);
            let source = rgba(seed, width, height);
            let layout = Layout {
                width,
                height,
                stride: width * depth.pixel_bytes(),
                depth,
                origin: (0, 0),
            };
            let mut input = vec![0; layout.span().unwrap()];
            let mut output = vec![0; input.len()];
            {
                let mut world = ViewMut::new(&mut input, layout).unwrap();
                for (i, p) in source.chunks_exact(4).enumerate() {
                    let a = [p[3], p[0], p[1], p[2]];
                    let pixel = match depth {
                        Depth::U8 => Pixel::U8(a),
                        // Experimental PNG routes materialize worlds in
                        // minihost/src/render_pixel_transport.cpp using the
                        // rounded binary32 reciprocal, not integer scaling.
                        Depth::U16 => Pixel::U16(a.map(|v| {
                            (v as f32 * (1.0f32 / 255.0) * 32768.0 + 0.5) as u16
                        })),
                        Depth::F32 => Pixel::F32(a.map(|v| v as f32 * (1.0f32 / 255.0))),
                    };
                    world.set(i % width, i / width, pixel).unwrap();
                }
            }
            render(
                &mut case,
                &View::new(&input, layout).unwrap(),
                &mut ViewMut::new(&mut output, layout).unwrap(),
            );
            // Canonical RGBA native words, matching AEXCompat's typed sidecars.
            let word = depth.pixel_bytes() / 4;
            let canonical: Vec<u8> = output
                .chunks_exact(word * 4)
                .flat_map(|p| {
                    [1, 2, 3, 0]
                        .into_iter()
                        .flat_map(move |c| p[c * word..(c + 1) * word].iter().copied())
                })
                .collect();
            let hash = sha256::hash(&canonical);
            if let Some(dir) = &export {
                fs::write(dir.join(format!("{id}.rgba")), &source).unwrap();
                fs::write(dir.join(format!("{id}.raw")), &canonical).unwrap();
                records.push(format!("{{\"id\":\"{id}\",\"width\":{width},\"height\":{height},\"depth\":{bpc},\"denominator\":{denominator},\"seed\":{seed},\"assignments\":[{}],\"sha256\":\"{hash}\"}}", case.assignments.join(",")));
            } else {
                assert_eq!(
                    expected.get(&id),
                    Some(&hash),
                    "{id}: output differs from Windows original-verified golden"
                );
            }
            count += 1;
        }
    }
    if let Some(dir) = export {
        fs::write(
            dir.join("cases.json"),
            format!("[\n{}\n]\n", records.join(",\n")),
        )
        .unwrap();
    } else {
        assert_eq!(
            expected
                .keys()
                .filter(|k| k.starts_with(&format!("{name}-")))
                .count(),
            count,
            "stale/extra golden cases"
        );
    }
    println!(
        "{name}: {count} cases {}",
        if args.is_empty() {
            "match original-verified golden"
        } else {
            "exported (NOT yet oracle-verified)"
        }
    );
}

pub const ALL_DEPTHS: &[Depth] = &[Depth::U8, Depth::U16, Depth::F32];

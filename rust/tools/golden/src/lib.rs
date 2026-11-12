//! Seeded, host-free render cases. Each binary links exactly one plug-in rlib:
//! linking multiple plug-ins together would collide on their exported AE entry symbols.
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
    layers: Vec<(usize, usize, usize, Vec<u8>)>,
}
impl Case {
    /// Add a reproducible secondary PNG and return its depth-promoted ARGB bytes.
    pub fn layer(&mut self, slot: usize, width: usize, height: usize) -> Vec<u8> {
        let source = rgba(0x554d0001 + self.index as u32 * 7919, width, height);
        self.assignments.push(format!(
            "{{\"slot\":{slot},\"layer\":\"layer-{slot}.png\"}}"
        ));
        let bytes = promote(&source, self.depth);
        self.layers.push((slot, width, height, source));
        bytes
    }
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
    let read_map = |file: &str| {
        if export.is_some() {
            return BTreeMap::new();
        }
        // Both files are generated flat string-to-SHA256 maps with no escapes.
        let text = fs::read_to_string(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(file))
            .expect("original-verified golden and exclusion manifests required");
        let tokens: Vec<_> = text.split('"').skip(1).step_by(2).collect();
        assert_eq!(tokens.len() % 2, 0);
        let mut map = BTreeMap::new();
        for pair in tokens.chunks_exact(2) {
            assert_eq!(pair[1].len(), 64);
            assert!(pair[1].bytes().all(|b| b.is_ascii_hexdigit()));
            assert!(
                map.insert(pair[0].to_owned(), pair[1].to_owned()).is_none(),
                "duplicate case"
            );
        }
        map
    };
    let expected = read_map("golden.json");
    let exclusions = read_map("exclusions.json");
    assert!(expected.keys().all(|k| !exclusions.contains_key(k)));
    if export.is_none() {
        assert_eq!(expected.len() + exclusions.len(), 630);
    }
    let mut records = Vec::new();
    let mut count = 0;
    let mut excluded = 0;
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
                layers: vec![],
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
                        Depth::U16 => Pixel::U16(
                            a.map(|v| (v as f32 * (1.0f32 / 255.0) * 32768.0 + 0.5) as u16),
                        ),
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
            let mut identity = format!(
                "{id}/{width}/{height}/{denominator}/{}",
                case.assignments.join(",")
            )
            .into_bytes();
            identity.extend_from_slice(&input);
            for (slot, w, h, source) in &case.layers {
                identity.extend_from_slice(format!("/{slot}/{w}/{h}/").as_bytes());
                identity.extend_from_slice(source);
            }
            let fingerprint = sha256::hash(&identity);
            if let Some(dir) = &export {
                fs::write(dir.join(format!("{id}.rgba")), &source).unwrap();
                fs::write(dir.join(format!("{id}.raw")), &canonical).unwrap();
                let layers: Vec<_> = case
                    .layers
                    .iter()
                    .map(|(slot, w, h, source)| {
                        let file = format!("{id}-layer-{slot}.rgba");
                        fs::write(dir.join(&file), source).unwrap();
                        format!(
                            "{{\"slot\":{slot},\"width\":{w},\"height\":{h},\"file\":\"{file}\"}}"
                        )
                    })
                    .collect();
                let layers = layers.join(",");
                records.push(format!("{{\"id\":\"{id}\",\"width\":{width},\"height\":{height},\"depth\":{bpc},\"denominator\":{denominator},\"seed\":{seed},\"assignments\":[{}],\"sha256\":\"{hash}\",\"fingerprint\":\"{fingerprint}\",\"layers\":[{layers}]}}", case.assignments.join(",")));
            } else if let Some(bound) = exclusions.get(&id) {
                assert_eq!(
                    bound, &fingerprint,
                    "{id}: changed input/params invalidate original-defect exclusion"
                );
                excluded += 1;
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
            count - excluded,
            "stale/extra golden cases"
        );
        assert_eq!(
            exclusions
                .keys()
                .filter(|k| k.starts_with(&format!("{name}-")))
                .count(),
            excluded
        );
    }
    println!(
        "{name}: {} cases {}; {excluded} original-nondeterministic cases excluded",
        count - excluded,
        if args.is_empty() {
            "match original-verified golden"
        } else {
            "exported (NOT yet oracle-verified)"
        }
    );
}

pub const ALL_DEPTHS: &[Depth] = &[Depth::U8, Depth::U16, Depth::F32];

/// Canonical PNG promotion used by AEXCompat, packed native ARGB.
pub fn promote(source: &[u8], depth: Depth) -> Vec<u8> {
    source
        .chunks_exact(4)
        .flat_map(|p| {
            [p[3], p[0], p[1], p[2]]
                .into_iter()
                .flat_map(|v| match depth {
                    Depth::U8 => vec![v],
                    Depth::U16 => ((v as f32 * (1.0f32 / 255.0) * 32768.0 + 0.5) as u16)
                        .to_le_bytes()
                        .to_vec(),
                    Depth::F32 => (v as f32 * (1.0f32 / 255.0)).to_le_bytes().to_vec(),
                })
        })
        .collect()
}
pub fn native_bytes(input: &View<'_>) -> Vec<u8> {
    let l = input.layout();
    (0..l.height)
        .flat_map(|y| {
            (0..l.width).flat_map(move |x| match input.get(x, y).unwrap() {
                Pixel::U8(p) => p.to_vec(),
                Pixel::U16(p) => p.into_iter().flat_map(u16::to_le_bytes).collect(),
                Pixel::F32(p) => p.into_iter().flat_map(f32::to_le_bytes).collect(),
            })
        })
        .collect()
}
pub fn write_native(bytes: &[u8], out: &mut ViewMut<'_>) {
    let l = out.layout();
    for (i, p) in bytes.chunks_exact(l.depth.pixel_bytes()).enumerate() {
        let pixel = match l.depth {
            Depth::U8 => Pixel::U8(p.try_into().unwrap()),
            Depth::U16 => Pixel::U16(std::array::from_fn(|c| {
                u16::from_le_bytes(p[c * 2..c * 2 + 2].try_into().unwrap())
            })),
            Depth::F32 => Pixel::F32(std::array::from_fn(|c| {
                f32::from_le_bytes(p[c * 4..c * 4 + 4].try_into().unwrap())
            })),
        };
        out.set(i % l.width, i / l.width, pixel).unwrap();
    }
}

use olm_anti_anti_alias::algorithm::{self, Layout, Settings};
use olm_golden::*;
fn main() {
    run("OLMAntiAntiAlias", ALL_DEPTHS, |c, input, out| {
        let count = [0, 1, 3, 25, 100, 2][c.index % 6];
        c.number(1, count as f64);
        c.number(2, (c.index % 2) as f64);
        let colors = (0..count)
            .map(|i| c.color(7 + i, [[255, 0, 0, 0], [255; 4], [255, 255, 0, 0]][i % 3]))
            .collect();
        let settings = Settings {
            colors,
            automatic: c.index % 2 == 1,
        };
        let bpp = c.depth.pixel_bytes();
        let l = Layout {
            width: c.width,
            height: c.height,
            row_bytes: c.width * bpp,
            bytes_per_pixel: bpp,
            origin: (0, 0),
        };
        let bytes = native_bytes(input);
        let mut result = vec![0; bytes.len()];
        algorithm::render_with(&bytes, l, &mut result, l, &settings).unwrap();
        write_native(&result, out);
    });
}

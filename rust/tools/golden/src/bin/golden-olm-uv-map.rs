use olm_golden::*;
use olm_uv_map::algorithm::{self, Layout, Params};
fn main() {
    run("OLMUVMap", ALL_DEPTHS, |c, input, out| {
        let (tw, th) = [(17, 9), (1, 5), (8, 16)][(c.index / 3) % 3];
        let texture = c.layer(1, tw, th);
        let params = Params {
            method: 1 + (c.index % 3) as i32,
            smoothness: [0.0, 0.5, 1.0][(c.index / 3) % 3],
        };
        c.number(2, params.method as f64);
        c.number(3, params.smoothness as f64);
        let bpp = c.depth.pixel_bytes();
        let l = Layout {
            width: c.width,
            height: c.height,
            row_bytes: c.width * bpp,
            bytes_per_pixel: bpp,
            origin: (0, 0),
        };
        let t = Layout {
            width: tw,
            height: th,
            row_bytes: tw * bpp,
            ..l
        };
        let bytes = native_bytes(input);
        let mut result = vec![0; bytes.len()];
        algorithm::render(&bytes, l, Some((&texture, t)), &mut result, l, params).unwrap();
        write_native(&result, out);
    });
}

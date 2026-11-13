//! Pure full-frame pipeline. Input/output are RGBA float values before typed packing.
use crate::{
    class_plane, frame,
    gamma::{self, GammaMode},
    geometry, lut,
    types::Pixel,
};
use olm_core::{Budget, Error, Result};

#[derive(Clone, Debug)]
pub struct Params {
    pub version: i32,
    pub smoothness: i32,
    pub extra: i32,
    pub range: i32,
    pub gamma_mode: GammaMode,
    pub gamma: f32,
    pub gamma_colors: Vec<Pixel>,
    pub key: Option<(Pixel, bool)>,
    pub keep_premultiplied: bool,
}

pub fn render(
    input: &[Pixel],
    width: usize,
    height: usize,
    p: &Params,
    threads: usize,
    budget: &mut Budget,
) -> Result<Vec<Pixel>> {
    render_with_range(input, width, height, p, p.range as f32, threads, budget)
}

/// Fractional Smooth Range in UI units; integer API retained for existing callers.
pub fn render_with_range(
    input: &[Pixel],
    width: usize,
    height: usize,
    p: &Params,
    range: f32,
    threads: usize,
    budget: &mut Budget,
) -> Result<Vec<Pixel>> {
    let n = olm_core::image_len(width, height)?;
    if input.len() != n || width > i32::MAX as usize || height > i32::MAX as usize {
        return Err(Error::Bounds);
    }
    if threads == 0 {
        return Err(Error::Geometry);
    }
    let mut scratch = olm_core::allocate(n, Pixel::default(), budget)?;
    crate::rows::parallel_rows(&mut scratch, width, threads, |y, row| {
        row.copy_from_slice(&input[y * width..(y + 1) * width]);
        frame::setup(row, p.version, p.key);
    })?;
    let classes =
        class_plane::build_with_range(&scratch, width, height, range, p.version, threads, budget)?;
    let bytes = classes.as_flattened();
    let mut output = olm_core::allocate(n, Pixel::default(), budget)?;
    let failed = std::sync::atomic::AtomicBool::new(false);
    crate::rows::parallel_rows(&mut output, width, threads, |y, row| {
        for (x, dst) in row.iter_mut().enumerate() {
            let mut center = scratch[y * width + x];
            let mut polygon = match geometry::State::new(
                &scratch,
                bytes,
                width as i32,
                height as i32,
                x as i32,
                y as i32,
                p.smoothness as f32 / 100.0,
                p.extra as f32 / 100.0,
            ) {
                Ok(v) => v,
                Err(_) => {
                    failed.store(true, std::sync::atomic::Ordering::Relaxed);
                    continue;
                }
            };
            geometry::build(&mut polygon);
            let vertices = match polygon.vertices() {
                Ok(v) => v,
                Err(_) => {
                    failed.store(true, std::sync::atomic::Ordering::Relaxed);
                    continue;
                }
            };
            if !vertices.is_empty() {
                let mut samples = [crate::types::Vertex::default(); 12];
                let samples = &mut samples[..vertices.len()];
                samples.copy_from_slice(vertices);
                let (value, apply) = if p.version == 3 {
                    (p.gamma, false)
                } else {
                    gamma::adaptive(
                        center,
                        samples,
                        p.version,
                        p.gamma_mode,
                        p.gamma,
                        &p.gamma_colors,
                    )
                };
                let enable = p.version != 3 && apply && value > 0.0;
                gamma::decode_premultiply(&mut center, samples, enable, value);
                center = gamma::composite(center, samples, true);
                gamma::post_unpremultiply_unclamped(&mut center, enable, value);
            }
            if p.version == 3 {
                center = crate::oklab::to_linear(center);
            }
            if p.version != 1 {
                center.r = lut::encode(center.r);
                center.g = lut::encode(center.g);
                center.b = lut::encode(center.b);
            }
            for c in [&mut center.r, &mut center.g, &mut center.b, &mut center.a] {
                if !(*c >= 0.0) {
                    *c = 0.0;
                } else if *c >= 1.0 {
                    *c = 1.0;
                }
            }
            if p.keep_premultiplied && center.a != 1.0 {
                center.r *= center.a;
                center.g *= center.a;
                center.b *= center.a;
            }
            *dst = center;
        }
    })?;
    if failed.load(std::sync::atomic::Ordering::Relaxed) {
        return Err(Error::Bounds);
    }
    Ok(output)
}

//! ac00/ae10 class-plane stage from RenderBits, before polygon construction.
use crate::types::Pixel;
use olm_core::{Budget, Error, Result};

pub fn distance(a: Pixel, b: Pixel) -> f32 {
    if a.a == 0.0 && b.a == 0.0 {
        return 0.0;
    }
    let dr = (a.r - b.r).abs();
    let dg = (a.g - b.g).abs();
    let db = (a.b - b.b).abs();
    let la = a.r * 0.2126 + a.g * 0.7152 + a.b * 0.0722;
    let lb = b.r * 0.2126 + b.g * 0.7152 + b.b * 0.0722;
    let dy = (la - lb).abs();
    // COMISS/CMOVBE followed by MAXSS: unordered selection is not f32::max.
    let mut max = if dg > dr { dg } else { dr };
    max = if db > max { db } else { max };
    max = if max > dy { max } else { dy };
    max + (a.a - b.a).abs()
}

/// Input is complete, immutable, tightly packed RGBA float scratch.
/// Output bytes are [left,top,top-left,top-right], each zero or 255.
pub fn build(
    input: &[Pixel],
    width: usize,
    height: usize,
    smooth_range: i32,
    threads: usize,
    budget: &mut Budget,
) -> Result<Vec<[u8; 4]>> {
    let n = olm_core::image_len(width, height)?;
    if width >= i32::MAX as usize || height >= i32::MAX as usize || threads == 0 {
        return Err(Error::Geometry);
    }
    if input.len() != n {
        return Err(Error::Bounds);
    }
    let mut output = olm_core::allocate(n, [0; 4], budget)?;
    let threshold = smooth_range as f32 / 100.0 + 0.001;
    olm_core::parallel_rows(&mut output, width, threads, |y, row| {
        for (x, out) in row.iter_mut().enumerate() {
            let p = input[y * width + x];
            let edge = |xx, yy| {
                if distance(p, input[yy * width + xx]) >= threshold {
                    255
                } else {
                    0
                }
            };
            if x >= 1 {
                out[0] = edge(x - 1, y);
            }
            if y >= 1 {
                out[1] = edge(x, y - 1);
                if x >= 1 {
                    out[2] = edge(x - 1, y - 1);
                }
                // Deliberately excludes the penultimate column, as in the AEX.
                if x + 1 < width - 1 {
                    out[3] = edge(x + 1, y - 1);
                }
            }
        }
    })?;
    Ok(output)
}

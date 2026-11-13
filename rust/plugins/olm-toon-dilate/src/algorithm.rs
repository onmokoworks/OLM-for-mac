//! Translation of mac/OLMToonDilate/OLMToonDilate.cpp RenderTyped (Smart).
//! Distances span the input. Pixel reads/writes are output-local, including
//! smaller output worlds; a winning neighbor outside the output is a no-op.
use olm_core::{allocate, image_len, Budget, Depth, Error, Layout, Result};

pub fn effective_radius(radius: f64, numerator: i32, denominator: u32) -> Result<u32> {
    if !radius.is_finite() || !(0.0..=100.0).contains(&radius) {
        return Err(Error::Geometry);
    }
    let scale = match (numerator, denominator) {
        (0, 0) => 1.0f32,
        (n, d) if n > 0 && d > 0 => n as f32 / d as f32,
        _ => return Err(Error::Geometry),
    };
    // CVTDQ2PS / DIVSS / MULSS, followed by promotion and double ceil.
    let scaled = (radius as f32 * scale) as f64;
    let rounded = scaled.ceil();
    if !scaled.is_finite() || rounded > i32::MAX as f64 {
        return Err(Error::Geometry);
    }
    Ok(rounded as u32)
}

fn seed(p: &[u8], depth: Depth) -> bool {
    match depth {
        Depth::U8 => p[0] == 255,
        Depth::U16 => u16::from_ne_bytes(p[..2].try_into().unwrap()) == 32768,
        Depth::F32 => {
            let a = f32::from_ne_bytes(p[..4].try_into().unwrap());
            a == 1.0 || a.is_nan()
        }
    }
}

/// Stages output and commits only on success. Padding and pixels outside input
/// coverage remain untouched. Origins do not offset accesses in the AEX worker.
pub fn render(input: &[u8], il: Layout, output: &mut [u8], ol: Layout, radius: u32) -> Result<()> {
    let no = ol.span()?;
    if output.len() < no {
        return Err(Error::Bounds);
    }
    let mut staged = allocate(no, 0u8, &mut Budget::new(isize::MAX as usize))?;
    staged.copy_from_slice(&output[..no]);
    render_staged(input, il, &mut staged, ol, radius)?;
    output[..no].copy_from_slice(&staged);
    Ok(())
}

/// The AE adapter already owns a transaction buffer until pixel checkin succeeds.
pub(crate) fn render_staged(
    input: &[u8],
    il: Layout,
    output: &mut [u8],
    ol: Layout,
    radius: u32,
) -> Result<()> {
    let ni = il.span()?;
    let no = ol.span()?;
    if input.len() < ni || output.len() < no || il.depth != ol.depth {
        return Err(Error::Bounds);
    }
    if radius > i32::MAX as u32 {
        return Err(Error::Geometry);
    }
    let mut budget = Budget::new(isize::MAX as usize);
    let staged = &mut output[..no];
    let w = il.width;
    let h = il.height;
    let pixel_bytes = il.depth.pixel_bytes();
    let mut dist = if radius > 0 {
        allocate(image_len(w, h)?, u32::MAX, &mut budget)?
    } else {
        Vec::new()
    };
    let mut has_seed = false;
    let copy_bytes = w.min(ol.width) * pixel_bytes;
    for y in 0..h.min(ol.height) {
        staged[y * ol.stride..y * ol.stride + copy_bytes]
            .copy_from_slice(&input[y * il.stride..y * il.stride + copy_bytes]);
    }
    if radius > 0 {
        olm_core::parallel_rows_auto(&mut dist, w, |y, row| {
            for (d, p) in row.iter_mut().zip(
                input[y * il.stride..y * il.stride + w * pixel_bytes].chunks_exact(pixel_bytes),
            ) {
                if seed(p, il.depth) {
                    *d = 0;
                }
            }
        })?;
        has_seed = dist.contains(&0);
    }
    if has_seed {
        // These passes have cross-pixel dependencies and must remain serial.
        for backward in [false, true] {
            let offsets = if backward {
                [(1, 0), (1, 1), (0, 1), (-1, 1)]
            } else {
                [(-1, 0), (-1, -1), (0, -1), (1, -1)]
            };
            for row in 0..h {
                let y = if backward { h - 1 - row } else { row };
                for col in 0..w {
                    let x = if backward { w - 1 - col } else { col };
                    let idx = y * w + x;
                    if dist[idx] == 0 {
                        continue;
                    }
                    let mut best = u32::MAX;
                    let mut winner = (0, 0);
                    for (dx, dy) in offsets {
                        let nx = x as i64 + dx;
                        let ny = y as i64 + dy;
                        if nx < 0 || ny < 0 || nx >= w as i64 || ny >= h as i64 {
                            continue;
                        }
                        let (nx, ny) = (nx as usize, ny as usize);
                        let d = dist[ny * w + nx];
                        if d < best {
                            best = d;
                            winner = (nx, ny);
                        }
                    }
                    if best == u32::MAX {
                        continue;
                    }
                    let candidate = best + 1;
                    if candidate >= dist[idx] {
                        continue;
                    }
                    dist[idx] = candidate;
                    let (nx, ny) = winner;
                    if candidate <= radius
                        && nx < ol.width
                        && ny < ol.height
                        && x < ol.width
                        && y < ol.height
                    {
                        let src = ny * ol.stride + nx * pixel_bytes;
                        let dst = y * ol.stride + x * pixel_bytes;
                        staged.copy_within(src..src + pixel_bytes, dst);
                    }
                }
            }
        }
    }
    Ok(())
}

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

fn seed<const PIXEL_BYTES: usize>(p: &[u8]) -> bool {
    match PIXEL_BYTES {
        4 => p[0] == 255,
        8 => u16::from_ne_bytes(p[..2].try_into().unwrap()) == 32768,
        _ => {
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
    match il.depth {
        Depth::U8 => render_staged_depth::<4>(input, il, output, ol, radius),
        Depth::U16 => render_staged_depth::<8>(input, il, output, ol, radius),
        Depth::F32 => render_staged_depth::<16>(input, il, output, ol, radius),
    }
}

// Fixed pixel widths let the ordered propagation copy use inline loads/stores
// instead of a variable-length memmove for every winning neighbor.
fn render_staged_depth<const PIXEL_BYTES: usize>(
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
    let pixel_bytes = PIXEL_BYTES;
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
                if seed::<PIXEL_BYTES>(p) {
                    *d = 0;
                }
            }
        })?;
        has_seed = dist.contains(&0);
    }
    if has_seed {
        propagate::<PIXEL_BYTES, false>(&mut dist, staged, w, h, ol, radius);
        propagate::<PIXEL_BYTES, true>(&mut dist, staged, w, h, ol, radius);
    }
    Ok(())
}

// Split the current and adjacent distance rows once. This preserves the ordered
// recurrence while avoiding full-plane coordinate arithmetic for every neighbor.
fn propagate<const PIXEL_BYTES: usize, const BACKWARD: bool>(
    dist: &mut [u32],
    staged: &mut [u8],
    w: usize,
    h: usize,
    ol: Layout,
    radius: u32,
) {
    let direction = if BACKWARD { 1isize } else { -1 };
    for step in 0..h {
        let y = if BACKWARD { h - 1 - step } else { step };
        let (row, adjacent): (&mut [u32], Option<&[u32]>) = if BACKWARD {
            let (head, tail) = dist.split_at_mut((y + 1) * w);
            (&mut head[y * w..], tail.get(..w))
        } else {
            let (head, tail) = dist.split_at_mut(y * w);
            let previous = if y == 0 {
                None
            } else {
                Some(&head[(y - 1) * w..])
            };
            (&mut tail[..w], previous)
        };
        for col in 0..w {
            let x = if BACKWARD { w - 1 - col } else { col };
            if row[x] == 0 {
                continue;
            }
            let mut best = u32::MAX;
            let mut winner = (0, 0);
            for (dx, other_row) in [
                (direction, false),
                (direction, true),
                (0, true),
                (-direction, true),
            ] {
                let nx = x as isize + dx;
                if nx < 0 || nx >= w as isize {
                    continue;
                }
                let nx = nx as usize;
                let (d, ny) = if other_row {
                    let Some(neighbor) = adjacent else {
                        continue;
                    };
                    (neighbor[nx], if BACKWARD { y + 1 } else { y - 1 })
                } else {
                    (row[nx], y)
                };
                if d < best {
                    best = d;
                    winner = (nx, ny);
                }
            }
            if best == u32::MAX {
                continue;
            }
            let candidate = best + 1;
            if candidate >= row[x] {
                continue;
            }
            row[x] = candidate;
            let (nx, ny) = winner;
            if candidate <= radius
                && nx < ol.width
                && ny < ol.height
                && x < ol.width
                && y < ol.height
            {
                let src = ny * ol.stride + nx * PIXEL_BYTES;
                let dst = y * ol.stride + x * PIXEL_BYTES;
                staged.copy_within(src..src + PIXEL_BYTES, dst);
            }
        }
    }
}

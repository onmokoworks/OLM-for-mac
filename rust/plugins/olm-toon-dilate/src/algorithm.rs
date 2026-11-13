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
    if radius > 0 && il.width == ol.width && il.height == ol.height {
        let minimum_rows = 128usize.max((radius as usize).saturating_mul(4));
        let workers = std::thread::available_parallelism()
            .map_or(1, usize::from)
            .min(il.height.div_ceil(minimum_rows));
        return render_bands::<PIXEL_BYTES>(input, il, output, ol, radius, workers);
    }
    render_reference::<PIXEL_BYTES>(input, il, output, ol, radius)
}

fn render_reference<const PIXEL_BYTES: usize>(
    input: &[u8],
    il: Layout,
    output: &mut [u8],
    ol: Layout,
    radius: u32,
) -> Result<()> {
    let no = ol.span()?;
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

// Only distances <= radius can cause a color write. Each predecessor reduces
// distance by one and changes y by at most one. Thus an interior pixel's color
// and strict-tie decisions depend only on seeds/paths inside its radius halo.
// Keeping both original raster orders inside overlapping bands preserves those
// paths. Outside-radius distances can be saturated to INF: they cannot win a
// visible write or block a shorter path. Cropped worlds retain the reference
// because their out-of-output copies are deliberately no-ops.
fn render_bands<const N: usize>(
    input: &[u8],
    il: Layout,
    output: &mut [u8],
    ol: Layout,
    radius: u32,
    workers: usize,
) -> Result<()> {
    let rows = il.height.div_ceil(workers.max(1).min(il.height));
    let chunk = rows.checked_mul(ol.stride).ok_or(Error::Overflow)?;
    let span = ol.span()?;
    if workers == 1 {
        return band::<N>(input, il, &mut output[..span], ol, 0, il.height, radius);
    }
    std::thread::scope(|scope| {
        let mut handles = Vec::new();
        for (i, bytes) in output[..span].chunks_mut(chunk).enumerate() {
            let start = i * rows;
            let end = (start + rows).min(il.height);
            handles.push(scope.spawn(move || band::<N>(input, il, bytes, ol, start, end, radius)));
        }
        for handle in handles {
            handle.join().expect("band worker panicked")?;
        }
        Ok(())
    })
}

fn band<const N: usize>(
    input: &[u8],
    il: Layout,
    output: &mut [u8],
    ol: Layout,
    start: usize,
    end: usize,
    radius: u32,
) -> Result<()> {
    let top = start.saturating_sub(radius as usize);
    let bottom = end.saturating_add(radius as usize).min(il.height);
    let w = il.width;
    let h = bottom - top;
    let stride = w.checked_add(2).ok_or(Error::Overflow)?;
    let count = stride
        .checked_mul(h.checked_add(2).ok_or(Error::Overflow)?)
        .ok_or(Error::Overflow)?;
    let mut budget = Budget::new(isize::MAX as usize);
    let mut dist = allocate(count, u32::MAX, &mut budget)?;
    let mut pixels = allocate(count, [0u8; N], &mut budget)?;
    for y in 0..h {
        let at = (y + 1) * stride + 1;
        let src = &input[(top + y) * il.stride..(top + y) * il.stride + w * N];
        for ((d, p), s) in dist[at..at + w]
            .iter_mut()
            .zip(&mut pixels[at..at + w])
            .zip(src.chunks_exact(N))
        {
            p.copy_from_slice(s);
            if seed::<N>(p) {
                *d = 0;
            }
        }
    }
    scan::<N, false>(&mut dist, &mut pixels, stride, w, h, radius);
    scan::<N, true>(&mut dist, &mut pixels, stride, w, h, radius);
    for y in start..end {
        let at = (y - top + 1) * stride + 1;
        let dst = &mut output[(y - start) * ol.stride..(y - start) * ol.stride + w * N];
        for (d, p) in dst.chunks_exact_mut(N).zip(&pixels[at..at + w]) {
            d.copy_from_slice(p);
        }
    }
    Ok(())
}

// Sentinel rows/columns remove edge branches. The checked allocation and loop
// ranges prove all five indices are inside both arrays, even at image corners.
// Copies use [u8; N] (alignment 1) and preserve arbitrary float payload bits.
fn scan<const N: usize, const BACK: bool>(
    dist: &mut [u32],
    pixels: &mut [[u8; N]],
    stride: usize,
    w: usize,
    h: usize,
    radius: u32,
) {
    for step in 0..h {
        let y = if BACK { h - step } else { step + 1 };
        for col in 0..w {
            let x = if BACK { w - col } else { col + 1 };
            let i = y * stride + x;
            unsafe {
                let current = *dist.get_unchecked(i);
                // A non-seed's best possible distance is 1. Equal candidates
                // never replace it, so the backward pass can skip it entirely.
                if current <= u32::from(BACK) {
                    continue;
                }
                let a = if BACK { i + 1 } else { i - 1 };
                let b = if BACK { i + stride + 1 } else { i - stride - 1 };
                let c = if BACK { i + stride } else { i - stride };
                let d = if BACK { i + stride - 1 } else { i - stride + 1 };
                let mut best = *dist.get_unchecked(a);
                let mut winner = a;
                for j in [b, c, d] {
                    let v = *dist.get_unchecked(j);
                    if v < best {
                        best = v;
                        winner = j;
                    }
                }
                if best >= radius {
                    continue;
                }
                let candidate = best + 1;
                if candidate < current {
                    *dist.get_unchecked_mut(i) = candidate;
                    *pixels.get_unchecked_mut(i) = *pixels.get_unchecked(winner);
                }
            }
        }
    }
}

#[cfg(test)]
mod band_tests {
    use super::*;
    #[test]
    fn exhaustive_masks_preserve_order_across_every_band_boundary() {
        let (w, h) = (3, 4);
        let l = Layout {
            width: w,
            height: h,
            stride: w * 4 + 3,
            depth: Depth::U8,
            origin: (-7, 11),
        };
        for mask in 0..1u32 << (w * h) {
            let mut input = vec![0xA5; l.span().unwrap()];
            for y in 0..h {
                for x in 0..w {
                    let i = y * w + x;
                    let at = y * l.stride + x * 4;
                    input[at..at + 4].copy_from_slice(&[
                        if mask & (1 << i) != 0 { 255 } else { 0 },
                        i as u8,
                        (i * 71) as u8,
                        0,
                    ]);
                }
            }
            for radius in [1, 2, 3, 5] {
                let mut expected = vec![0x97; input.len()];
                render_reference::<4>(&input, l, &mut expected, l, radius).unwrap();
                for rows in [1, 2, 3, 4] {
                    let mut output = vec![0x97; input.len()];
                    for start in (0..h).step_by(rows) {
                        let end = (start + rows).min(h);
                        let stop = if end == h {
                            output.len()
                        } else {
                            end * l.stride
                        };
                        band::<4>(
                            &input,
                            l,
                            &mut output[start * l.stride..stop],
                            l,
                            start,
                            end,
                            radius,
                        )
                        .unwrap();
                    }
                    assert_eq!(expected, output, "mask={mask} radius={radius} rows={rows}");
                }
            }
        }
    }
    fn random_depth<const N: usize>(depth: Depth) {
        let (w, h) = (257, 259);
        let l = Layout {
            width: w,
            height: h,
            stride: w * N + 3,
            depth,
            origin: (-11, 9),
        };
        for spacing in [1, 5, 97, 65537, usize::MAX] {
            let mut input = vec![0xC7; l.span().unwrap()];
            let mut state = 0x71712345u32;
            for y in 0..h {
                for x in 0..w {
                    let i = y * w + x;
                    let at = y * l.stride + x * N;
                    for b in &mut input[at..at + N] {
                        state ^= state << 13;
                        state ^= state >> 17;
                        state ^= state << 5;
                        *b = state as u8;
                    }
                    let hit = spacing != usize::MAX && i % spacing == 0;
                    match depth {
                        Depth::U8 => input[at] = if hit { 255 } else { 128 },
                        Depth::U16 => input[at..at + 2]
                            .copy_from_slice(&(if hit { 32768u16 } else { 65535 }).to_ne_bytes()),
                        Depth::F32 => input[at..at + 4].copy_from_slice(
                            &(if hit {
                                if i % 2 == 0 {
                                    0x7f800123u32
                                } else {
                                    1f32.to_bits()
                                }
                            } else {
                                (-0.0f32).to_bits()
                            })
                            .to_ne_bytes(),
                        ),
                    }
                }
            }
            for radius in [1, 2, 5, 50, 100, 400] {
                let mut expected = vec![0x97; input.len()];
                render_reference::<N>(&input, l, &mut expected, l, radius).unwrap();
                for workers in [1, 2, 7] {
                    let mut output = vec![0x97; input.len()];
                    render_bands::<N>(&input, l, &mut output, l, radius, workers).unwrap();
                    assert_eq!(
                        expected, output,
                        "{depth:?} spacing={spacing} radius={radius} workers={workers}"
                    );
                }
            }
        }
    }
    #[test]
    fn padded_payloads_and_sparse_seeds_match_one_two_seven_workers() {
        random_depth::<4>(Depth::U8);
        random_depth::<8>(Depth::U16);
        random_depth::<16>(Depth::F32);
    }
}

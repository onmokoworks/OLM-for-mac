//! Pure CPU translation of core/olmblur_{helper,fullworker_helper,worker*}.cpp.
//! Accumulation order, operand order, six Legacy carry partitions and typed writers
//! are part of the algorithm. Do not normalize integer channels or fuse operations.
use olm_core::{allocate, image_len, Budget, Error, Pixel, Result, View, ViewMut};
use olm_math::{x86, Mode};

#[derive(Clone, Copy, Debug)]
pub struct Params {
    pub amount: f32,
    pub smoothness: f32,
    pub repeat: usize,
    pub bias: usize,
    pub legacy: bool,
    pub scale: f32,
}
impl Default for Params {
    fn default() -> Self {
        Self {
            amount: 5.0,
            smoothness: 100.0,
            repeat: 2,
            bias: 1,
            legacy: false,
            scale: 1.0,
        }
    }
}

/// floorf(value + 0.5), CVTTSS2SI, low byte/word. No nominal white clamp.
pub fn integer_store(value: f32) -> i32 {
    x86::cvttss2si(x86::add(value, 0.5).floor())
}

fn nonlegacy_pass<const FINITE: bool>(
    flags: &[u8],
    src: &[[f32; 3]],
    dst: &mut [[f32; 3]],
    weights: &[f32],
    w: usize,
    h: usize,
    vertical: bool,
    threads: usize,
) -> Result<()> {
    let radius = weights.len() - 1;
    olm_core::parallel_rows(dst, w, threads, |y, row| {
        #[cfg(not(target_arch = "x86_64"))]
        let prefix = 0;
        #[cfg(target_arch = "x86_64")]
        let prefix = if FINITE && weights.len() <= 6 && std::is_x86_feature_detected!("sse2") {
            // Four independent output pixels; taps stay in scalar order per lane.
            unsafe { finite_row_sse2(flags, src, row, weights, w, h, y, vertical) }
        } else {
            0
        };
        for (x, out) in row.iter_mut().enumerate().skip(prefix) {
            let center = y * w + x;
            if flags[center] == 0 {
                *out = src[center];
                continue;
            }
            let (coordinate, dimension, step) = if vertical { (y, h, w) } else { (x, w, 1) };
            let mut sum = 0.0;
            let mut rgb = [0.0; 3];
            let mut add = |index: usize, weight: f32| {
                sum = ordered_add::<FINITE>(sum, weight);
                for c in 0..3 {
                    rgb[c] =
                        ordered_add::<FINITE>(rgb[c], ordered_mul::<FINITE>(weight, src[index][c]));
                }
            };
            for d in 0..=radius.min(coordinate) {
                let index = center - d * step;
                if flags[index] == 0 {
                    break;
                }
                add(index, weights[d]);
            }
            for d in 1..=radius.min(dimension - 1 - coordinate) {
                let index = center + d * step;
                if flags[index] == 0 {
                    break;
                }
                add(index, weights[d]);
            }
            let scale = if sum == 0.0 { 0.0 } else { x86::div(1.0, sum) };
            for c in 0..3 {
                out[c] = ordered_mul::<FINITE>(scale, rgb[c]);
            }
        }
    })
}

fn legacy_pass<const FINITE: bool>(
    flags: &[u8],
    src: &[[f32; 3]],
    dst: &mut [[f32; 3]],
    weights: &[f32],
    w: usize,
    h: usize,
    vertical: bool,
) {
    let radius = weights.len() / 2;
    // Carry belongs to each original partition, not to a row or execution thread.
    for part in 0..6 {
        let dim = if vertical { w } else { h };
        let base = dim / 6;
        let count = if part == 5 { dim - 5 * base } else { base };
        let offset = base * part;
        let mut carry = [-1.0; 3];
        let (rows, cols) = if vertical { (h, count) } else { (count, w) };
        for row in 0..rows {
            for col in 0..cols {
                let (x, y) = if vertical {
                    (offset + col, row)
                } else {
                    (col, offset + row)
                };
                let center = y * w + x;
                if flags[center] == 0 {
                    if !vertical {
                        dst[center] = src[center];
                    }
                    continue;
                }
                let (coordinate, dimension, step) = if vertical { (y, h, w) } else { (x, w, 1) };
                let mut sum = 0.0;
                let mut rgb = [0.0; 3];
                let mut unchanged = true;
                let mut add = |index: usize, weight: f32| {
                    let pixel = src[index];
                    sum = ordered_add::<FINITE>(sum, weight);
                    for c in 0..3 {
                        rgb[c] =
                            ordered_add::<FINITE>(rgb[c], ordered_mul::<FINITE>(pixel[c], weight));
                        if pixel[c] != carry[c] {
                            unchanged = false;
                        }
                    }
                    carry = pixel;
                };
                // AEX excludes coordinate zero, including the center at the border.
                for d in 0..=radius {
                    if coordinate <= d {
                        continue;
                    }
                    let index = center - d * step;
                    if flags[index] == 0 {
                        break;
                    }
                    add(index, weights[radius - d]);
                }
                for d in 1..=radius {
                    if coordinate + d >= dimension {
                        break;
                    }
                    let index = center + d * step;
                    if flags[index] == 0 {
                        break;
                    }
                    add(index, weights[radius + d]);
                }
                let scale = if sum != 0.0 { x86::div(1.0, sum) } else { 1.0 };
                dst[center] = if unchanged {
                    src[center]
                } else {
                    rgb.map(|c| ordered_mul::<FINITE>(scale, c))
                };
            }
        }
    }
}

/// Full-frame worlds, arbitrary positive strides. Parameters match the Smart
/// builder (Smoothness has already had its fixed-point fraction discarded).
/// Thread count only schedules independent non-Legacy rows; Legacy is serial.
pub fn render(
    input: &View<'_>,
    output: &mut ViewMut<'_>,
    p: &Params,
    threads: usize,
) -> Result<()> {
    render_impl(input, output.layout(), p, threads, |a| {
        let (w, h) = (input.layout().width, input.layout().height);
        for y in 0..h {
            for x in 0..w {
                output.set(x, y, output_pixel(input.get(x, y)?, a[y * w + x]))?;
            }
        }
        Ok(())
    })
}

fn output_pixel(pixel: Pixel, rgb: [f32; 3]) -> Pixel {
    match pixel {
        Pixel::U8(v) => Pixel::U8([
            v[0],
            integer_store(rgb[0]) as u8,
            integer_store(rgb[1]) as u8,
            integer_store(rgb[2]) as u8,
        ]),
        Pixel::U16(v) => Pixel::U16([
            v[0],
            integer_store(rgb[0]) as u16,
            integer_store(rgb[1]) as u16,
            integer_store(rgb[2]) as u16,
        ]),
        Pixel::F32(v) => Pixel::F32([v[0], rgb[0], rgb[1], rgb[2]]),
    }
}

/// Crate-local host byte boundary: checked once, disjoint rows, padding untouched.
pub fn render_bytes(
    input: &View<'_>,
    output: &mut [u8],
    layout: olm_core::Layout,
    p: &Params,
    threads: usize,
) -> Result<()> {
    let span = layout.span()?;
    if output.len() < span {
        return Err(Error::Bounds);
    }
    render_impl(input, layout, p, threads, |a| {
        let workers = threads
            .max(1)
            .min(layout.height)
            .min(std::thread::available_parallelism().map_or(1, usize::from));
        let rows = layout.height.div_ceil(workers);
        let chunk = rows.checked_mul(layout.stride).ok_or(Error::Overflow)?;
        std::thread::scope(|scope| {
            for (part, bytes) in output[..span].chunks_mut(chunk).enumerate() {
                let mut work = move || {
                    for (row, bytes) in bytes.chunks_mut(layout.stride).enumerate() {
                        let y = part * rows + row;
                        for (x, pixel) in bytes[..layout.width * layout.depth.pixel_bytes()]
                            .chunks_exact_mut(layout.depth.pixel_bytes())
                            .enumerate()
                        {
                            let value = output_pixel(
                                input.get(x, y).expect("validated input coordinates"),
                                a[y * layout.width + x],
                            );
                            match value {
                                Pixel::U8(v) => pixel.copy_from_slice(&v),
                                Pixel::U16(v) => {
                                    for (dst, c) in pixel.chunks_exact_mut(2).zip(v) {
                                        dst.copy_from_slice(&c.to_ne_bytes());
                                    }
                                }
                                Pixel::F32(v) => {
                                    for (dst, c) in pixel.chunks_exact_mut(4).zip(v) {
                                        dst.copy_from_slice(&c.to_ne_bytes());
                                    }
                                }
                            }
                        }
                    }
                };
                if workers == 1 {
                    work();
                } else {
                    scope.spawn(work);
                }
            }
        });
        Ok(())
    })
}

fn render_impl(
    input: &View<'_>,
    o: olm_core::Layout,
    p: &Params,
    threads: usize,
    publish: impl FnOnce(&[[f32; 3]]) -> Result<()>,
) -> Result<()> {
    let l = input.layout();
    if l.width != o.width
        || l.height != o.height
        || l.depth != o.depth
        || l.origin != (0, 0)
        || o.origin != (0, 0)
    {
        return Err(Error::Unsupported);
    }
    if !p.amount.is_finite()
        || !(1.0..=1000.0).contains(&p.amount)
        || !(1.0..=100.0).contains(&p.smoothness)
        || !(1..=10).contains(&p.repeat)
        || !(1..=2).contains(&p.bias)
        || !p.scale.is_finite()
        || p.scale <= 0.0
    {
        return Err(Error::Unsupported);
    }
    let (w, h) = (l.width, l.height);
    let n = image_len(w, h)?;
    #[cfg(feature = "profile")]
    let clock = std::time::Instant::now();
    let mut budget = Budget::new(isize::MAX as usize);
    let mut a = allocate(n, [0.0; 3], &mut budget)?;
    let mut b = allocate(n, [0.0; 3], &mut budget)?;
    let mut flags = allocate(n, 0u8, &mut budget)?;
    let stage = |first_row: usize, pixels: &mut [[f32; 3]], mask: &mut [u8]| -> Result<bool> {
        let mut bounded = true;
        for (row, (pixels, mask)) in pixels.chunks_mut(w).zip(mask.chunks_mut(w)).enumerate() {
            let y = first_row + row;
            for x in 0..w {
                let argb = match input.get(x, y)? {
                    Pixel::U8(v) => v.map(|c| c as f32),
                    Pixel::U16(v) => v.map(|c| c as f32),
                    Pixel::F32(v) => {
                        if w <= 24
                            && h <= 24
                            && v.iter()
                                .any(|c| c.is_finite() && !(-16.0..=16.0).contains(c))
                        {
                            return Err(Error::Unsupported);
                        }
                        bounded =
                            bounded && v[1..].iter().all(|c| c.is_finite() && c.abs() <= 1.0e10);
                        v
                    }
                };
                pixels[x] = [argb[1], argb[2], argb[3]];
                mask[x] = (argb[0] != 0.0) as u8;
            }
        }
        Ok(bounded)
    };
    let finite = if threads > 1 && h > 1 {
        let workers = threads
            .min(h)
            .min(std::thread::available_parallelism().map_or(1, usize::from));
        let chunk = h.div_ceil(workers) * w;
        std::thread::scope(|scope| -> Result<bool> {
            let mut handles = Vec::new();
            for (part, (pixels, mask)) in
                a.chunks_mut(chunk).zip(flags.chunks_mut(chunk)).enumerate()
            {
                let stage = &stage;
                handles.push(scope.spawn(move || stage(part * (chunk / w), pixels, mask)));
            }
            let mut bounded = true;
            for handle in handles {
                bounded &= handle.join().expect("staging worker panicked")?;
            }
            Ok(bounded)
        })?
    } else {
        stage(0, &mut a, &mut flags)?
    };
    // Bounded inputs permit the fast path, but Legacy border normalization can
    // overflow a subnormal reciprocal and generate NaNs in later passes.
    // Non-x86 fast arithmetic repairs those results with SSE NaN semantics.
    #[cfg(feature = "profile")]
    let staged_at = clock.elapsed();
    let amount = p.amount * p.scale;
    if !amount.is_finite() {
        return Err(Error::Unsupported);
    }
    // Host downsampling is <=1; checked coefficient allocation also handles larger valid rationals.
    if p.legacy {
        let radius = amount as usize;
        let size = radius
            .checked_mul(2)
            .and_then(|v| v.checked_add(1))
            .ok_or(Error::Overflow)?;
        let mut weights = allocate(size, 0.0, &mut budget)?;
        let sigma_base = ((p.amount * p.smoothness) / 100.0) * (p.amount / 3.0) * p.scale;
        for iteration in 1..=p.repeat {
            weights[radius] = 1.0;
            let sigma = sigma_base / iteration as f32;
            let denominator = (sigma + sigma) * sigma;
            for d in 1..=radius {
                let square = d.checked_mul(d).ok_or(Error::Overflow)? as f32;
                let weight = olm_math::expf(-square / denominator, Mode::Fma);
                weights[radius - d] = weight;
                weights[radius + d] = weight;
            }
            if finite {
                legacy_pass::<true>(&flags, &a, &mut b, &weights, w, h, p.bias == 2);
                legacy_pass::<true>(&flags, &b, &mut a, &weights, w, h, p.bias == 1);
            } else {
                legacy_pass::<false>(&flags, &a, &mut b, &weights, w, h, p.bias == 2);
                legacy_pass::<false>(&flags, &b, &mut a, &weights, w, h, p.bias == 1);
            }
        }
    } else {
        let decay = if p.repeat > 1 {
            olm_math::powf(3.0 / amount, 1.0 / (p.repeat - 1) as f32, Mode::Fma)
        } else {
            1.0
        };
        for iteration in 0..p.repeat {
            let radius_value =
                (amount as f64 * olm_math::pow(decay as f64, iteration as f64, Mode::Fma)) as f32;
            let radius = radius_value as usize;
            if radius == 0 {
                break;
            }
            let size = radius.checked_add(1).ok_or(Error::Overflow)?;
            let mut weight_budget = Budget::new(isize::MAX as usize);
            let mut weights = allocate(size, 0.0, &mut weight_budget)?;
            let sigma = radius_value / 3.0;
            let denominator = (sigma + sigma) * sigma;
            for (k, weight) in weights.iter_mut().enumerate() {
                let square = k.checked_mul(k).ok_or(Error::Overflow)? as f32;
                *weight = olm_math::expf(-square / denominator, Mode::Fma);
            }
            if finite {
                nonlegacy_pass::<true>(&flags, &a, &mut b, &weights, w, h, p.bias == 2, threads)?;
                nonlegacy_pass::<true>(&flags, &b, &mut a, &weights, w, h, p.bias == 1, threads)?;
            } else {
                nonlegacy_pass::<false>(&flags, &a, &mut b, &weights, w, h, p.bias == 2, threads)?;
                nonlegacy_pass::<false>(&flags, &b, &mut a, &weights, w, h, p.bias == 1, threads)?;
            }
        }
    }
    #[cfg(feature = "profile")]
    let filtered_at = clock.elapsed();
    publish(&a)?;
    #[cfg(feature = "profile")]
    eprintln!(
        "stage_ms={:.3} filter_ms={:.3} output_ms={:.3}",
        staged_at.as_secs_f64() * 1000.,
        (filtered_at - staged_at).as_secs_f64() * 1000.,
        (clock.elapsed() - filtered_at).as_secs_f64() * 1000.
    );
    Ok(())
}

#[inline(always)]
fn ordered_add<const FINITE: bool>(a: f32, b: f32) -> f32 {
    if FINITE {
        let result = a + b;
        #[cfg(not(target_arch = "x86_64"))]
        let result = finite_result(result, a, b);
        result
    } else {
        x86::add(a, b)
    }
}
#[inline(always)]
fn ordered_mul<const FINITE: bool>(a: f32, b: f32) -> f32 {
    if FINITE {
        let result = a * b;
        #[cfg(not(target_arch = "x86_64"))]
        let result = finite_result(result, a, b);
        result
    } else {
        x86::mul(a, b)
    }
}

// Only exceptional results need operand inspection. Reuse the shared first-NaN
// quieting/default-invalid policy; never canonicalize copied input pixels.
#[cfg(any(test, not(target_arch = "x86_64")))]
#[inline(always)]
fn finite_result(result: f32, a: f32, b: f32) -> f32 {
    if result.is_nan() {
        x86::result(result, a, b)
    } else {
        result
    }
}

#[cfg(test)]
mod nan_tests {
    use super::*;

    #[test]
    fn generated_and_propagated_nan_bits_match_sse() {
        let inf = std::hint::black_box(f32::INFINITY);
        for (a, b, result) in [
            (0.0, inf, 0.0 * inf),
            (inf, -inf, inf - inf),
            (0.0, 0.0, std::hint::black_box(0.0f32) / 0.0),
        ] {
            assert_eq!(finite_result(result, a, b).to_bits(), 0xffc00000);
        }
        assert_eq!(ordered_mul::<true>(0.0, inf).to_bits(), 0xffc00000);
        assert_eq!(ordered_add::<true>(inf, -inf).to_bits(), 0xffc00000);
        for bits in [0x7f801234, 0xff801234, 0x7fc05678, 0xffc05678] {
            let a = f32::from_bits(bits);
            let b = f32::from_bits(0x7fc09876);
            // Model a host choosing the wrong operand/sign, even on x86 CI.
            assert_eq!(finite_result(b, a, b).to_bits(), bits | 0x00400000);
            assert_eq!(finite_result(b, 1.0, a).to_bits(), bits | 0x00400000);
            assert_eq!(ordered_mul::<false>(a, b).to_bits(), bits | 0x00400000);
        }
        assert_eq!(finite_result(-0.0, -0.0, 1.0).to_bits(), 0x80000000);
    }

    #[test]
    fn legacy_subnormal_normalization_generates_negative_nan() {
        // Border excludes the center: one tiny weighted tap yields an infinite
        // reciprocal. Zero RGB times that reciprocal must use SSE default NaN.
        let src = [[0.0; 3]; 2];
        let mut dst = src;
        legacy_pass::<true>(
            &[1, 1],
            &src,
            &mut dst,
            &[f32::from_bits(1), 1.0, f32::from_bits(1)],
            2,
            1,
            false,
        );
        assert_eq!(dst[0].map(f32::to_bits), [0xffc00000; 3]);
    }
}

/// Bounded finite RGB only. SSE2 is mandatory on x86-64; dispatch still checks it.
/// Each vector lane is one output pixel, never a partial reduction of a pixel.
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "sse2")]
unsafe fn finite_row_sse2(
    flags: &[u8],
    src: &[[f32; 3]],
    row: &mut [[f32; 3]],
    weights: &[f32],
    w: usize,
    h: usize,
    y: usize,
    vertical: bool,
) -> usize {
    use std::arch::x86_64::*;
    let end = w / 4 * 4;
    let step = if vertical { w } else { 1 };
    for x in (0..end).step_by(4) {
        let centers = std::array::from_fn::<_, 4, _>(|lane| y * w + x + lane);
        let enabled = centers.map(|i| flags[i] != 0);
        let mut sums = _mm_setzero_ps();
        let mut rgb = [_mm_setzero_ps(); 3];
        for forward in [false, true] {
            let mut active = enabled;
            for (d, &weight) in weights.iter().enumerate().skip(usize::from(forward)) {
                let mut values = [[0.0f32; 4]; 3];
                let mut ws = [0.0f32; 4];
                for lane in 0..4 {
                    let coordinate = if vertical { y } else { x + lane };
                    let dimension = if vertical { h } else { w };
                    active[lane] &= if forward {
                        d < dimension - coordinate
                    } else {
                        d <= coordinate
                    };
                    if active[lane] {
                        let index = if forward {
                            centers[lane] + d * step
                        } else {
                            centers[lane] - d * step
                        };
                        active[lane] = flags[index] != 0;
                        if active[lane] {
                            ws[lane] = weight;
                            for c in 0..3 {
                                values[c][lane] = src[index][c];
                            }
                        }
                    }
                }
                if !active.iter().any(|&v| v) {
                    break;
                }
                let weight = _mm_loadu_ps(ws.as_ptr());
                sums = _mm_add_ps(sums, weight);
                for c in 0..3 {
                    rgb[c] =
                        _mm_add_ps(rgb[c], _mm_mul_ps(weight, _mm_loadu_ps(values[c].as_ptr())));
                }
            }
        }
        let nonzero = _mm_cmpneq_ps(sums, _mm_setzero_ps());
        let scale = _mm_and_ps(nonzero, _mm_div_ps(_mm_set1_ps(1.0), sums));
        let mut channels = [[0.0f32; 4]; 3];
        for c in 0..3 {
            _mm_storeu_ps(channels[c].as_mut_ptr(), _mm_mul_ps(scale, rgb[c]));
        }
        for lane in 0..4 {
            row[x + lane] = if enabled[lane] {
                std::array::from_fn(|c| channels[c][lane])
            } else {
                src[centers[lane]]
            };
        }
    }
    end
}

#[cfg(all(test, target_arch = "x86_64"))]
mod simd_tests {
    use super::*;
    #[test]
    fn four_pixels_equal_scalar_order() {
        let mut state = 0x13b17u32;
        for w in [4, 5, 17, 64] {
            for h in [1, 7, 33] {
                let mut flags = vec![1; w * h];
                let mut source = vec![[0.0; 3]; w * h];
                for (i, rgb) in source.iter_mut().enumerate() {
                    for value in rgb.iter_mut() {
                        state ^= state << 13;
                        state ^= state >> 17;
                        state ^= state << 5;
                        *value = ((state as i32) as f32) * 0.125;
                    }
                    if i % 7 == 0 {
                        *rgb = [f32::from_bits(1), -0.0, -f32::from_bits(1)];
                    }
                    if i % 5 == 0 {
                        flags[i] = 0;
                    }
                }
                for vertical in [false, true] {
                    for radius in [1, 4, 19, 127] {
                        let weights: Vec<_> = (0..=radius).map(|i| 1.0 / (i + 1) as f32).collect();
                        let mut scalar = vec![[0.0; 3]; w * h];
                        let mut vector = scalar.clone();
                        nonlegacy_pass::<false>(
                            &flags,
                            &source,
                            &mut scalar,
                            &weights,
                            w,
                            h,
                            vertical,
                            1,
                        )
                        .unwrap();
                        nonlegacy_pass::<true>(
                            &flags,
                            &source,
                            &mut vector,
                            &weights,
                            w,
                            h,
                            vertical,
                            3,
                        )
                        .unwrap();
                        assert_eq!(
                            scalar
                                .iter()
                                .map(|v| v.map(f32::to_bits))
                                .collect::<Vec<_>>(),
                            vector
                                .iter()
                                .map(|v| v.map(f32::to_bits))
                                .collect::<Vec<_>>()
                        );
                    }
                }
            }
        }
    }
}

//! Checked, host-independent frame owner. Callback traversal is deliberately
//! serial: interpolation may write neighbors that later callbacks read.
use crate::{hot::*, support::*};
use olm_core::{allocate, Budget, Depth, Error, Layout, Pixel, Rect, Result, View, ViewMut};
#[derive(Clone, Copy, Debug)]
pub struct Params {
    pub use_key: bool,
    pub key: [u8; 4],
    pub tolerance: i32,
}
impl Default for Params {
    fn default() -> Self {
        Self {
            use_key: false,
            key: [255; 4],
            tolerance: 6,
        }
    }
}
pub fn render(input: &View<'_>, output: &mut ViewMut<'_>, p: Params, extent: Rect) -> Result<()> {
    render_impl::<false>(input, output, p, extent)
}
pub(super) fn render_impl<const REFERENCE: bool>(
    input: &View<'_>,
    output: &mut ViewMut<'_>,
    p: Params,
    extent: Rect,
) -> Result<()> {
    render_workers::<REFERENCE>(input, output, p, extent, usize::MAX)
}

/// Explicit worker limit for deterministic validation and phase profiling.
pub fn render_with_workers(
    input: &View<'_>,
    output: &mut ViewMut<'_>,
    p: Params,
    extent: Rect,
    workers: usize,
) -> Result<()> {
    render_workers::<false>(input, output, p, extent, workers)
}

/// Checked byte-buffer entry for hosts that already provide native ARGB rows.
/// Only active row bytes are copied; padding and origins retain View semantics.
pub fn render_bytes(
    input: &[u8],
    l: Layout,
    output: &mut [u8],
    o: Layout,
    p: Params,
    extent: Rect,
) -> Result<()> {
    if input.len() < l.span()? || output.len() < o.span()? {
        return Err(Error::Bounds);
    }
    render_owned::<false>(
        l,
        o,
        p,
        extent,
        usize::MAX,
        |src| unsafe {
            let row = l.width * l.depth.pixel_bytes();
            let target =
                std::slice::from_raw_parts_mut(src.as_mut_ptr().cast::<u8>(), src.len() * 8);
            for y in 0..l.height {
                target[y * row..(y + 1) * row]
                    .copy_from_slice(&input[y * l.stride..y * l.stride + row]);
            }
            if p.use_key {
                let key16 = p.key.map(|v| ((v as u32 * 32768 + 128) / 255) as u16);
                for y in extent.top()..extent.bottom() {
                    for x in extent.left()..extent.right() {
                        let at = y as usize * l.width + x as usize;
                        if l.depth == Depth::U8 {
                            let pixel = &mut *src.as_mut_ptr().cast::<[u8; 4]>().add(at);
                            if *pixel == p.key {
                                pixel[0] = 0;
                            }
                        } else {
                            let pixel = &mut *src.as_mut_ptr().cast::<[u16; 4]>().add(at);
                            if *pixel == key16 {
                                pixel[0] = 0;
                            }
                        }
                    }
                }
            }
            Ok(())
        },
        |dst| unsafe {
            let row = o.width * o.depth.pixel_bytes();
            let source = std::slice::from_raw_parts(dst.as_ptr().cast::<u8>(), dst.len() * 8);
            for y in 0..o.height {
                output[y * o.stride..y * o.stride + row]
                    .copy_from_slice(&source[y * row..(y + 1) * row]);
            }
            Ok(())
        },
    )
}

fn render_workers<const REFERENCE: bool>(
    input: &View<'_>,
    output: &mut ViewMut<'_>,
    p: Params,
    extent: Rect,
    workers: usize,
) -> Result<()> {
    let l = input.layout();
    let o = output.layout();
    render_owned::<REFERENCE>(
        l,
        o,
        p,
        extent,
        workers,
        |src| unsafe {
            for y in 0..l.height {
                for x in 0..l.width {
                    let i = y * l.width + x;
                    match input.get(x, y)? {
                        Pixel::U8(mut v) => {
                            if p.use_key
                                && extent.left() <= x as i32
                                && (x as i32) < extent.right()
                                && extent.top() <= y as i32
                                && (y as i32) < extent.bottom()
                                && v == p.key
                            {
                                v[0] = 0;
                            }
                            src.as_mut_ptr().cast::<[u8; 4]>().add(i).write(v);
                        }
                        Pixel::U16(mut v) => {
                            let key = p.key.map(|v| ((v as u32 * 32768 + 128) / 255) as u16);
                            if p.use_key
                                && extent.left() <= x as i32
                                && (x as i32) < extent.right()
                                && extent.top() <= y as i32
                                && (y as i32) < extent.bottom()
                                && v == key
                            {
                                v[0] = 0;
                            }
                            src.as_mut_ptr().cast::<[u16; 4]>().add(i).write(v);
                        }
                        _ => return Err(Error::Unsupported),
                    }
                }
            }
            Ok(())
        },
        |dst| unsafe {
            for y in 0..l.height {
                for x in 0..l.width {
                    let i = y * l.width + x;
                    let px = if l.depth == Depth::U8 {
                        Pixel::U8(dst.as_ptr().cast::<[u8; 4]>().add(i).read())
                    } else {
                        Pixel::U16(dst.as_ptr().cast::<[u16; 4]>().add(i).read())
                    };
                    output.set(x, y, px)?;
                }
            }
            Ok(())
        },
    )
}

#[allow(clippy::too_many_arguments)] // Layouts and closures describe two independently strided worlds.
fn render_owned<const REFERENCE: bool>(
    l: Layout,
    o: Layout,
    p: Params,
    extent: Rect,
    workers: usize,
    stage: impl FnOnce(&mut [u64]) -> Result<()>,
    publish: impl FnOnce(&[u64]) -> Result<()>,
) -> Result<()> {
    if l.depth != o.depth || l.width != o.width || l.height != o.height || l.depth == Depth::F32 {
        return Err(Error::Unsupported);
    }
    if !(0..=255).contains(&p.tolerance)
        || l.width > 4096
        || l.height > 4096
        || l.width.checked_mul(l.height).ok_or(Error::Overflow)? > 4096 * 2160
    {
        return Err(Error::Geometry);
    }
    let frame = Rect::from_size(0, 0, l.width, l.height)?;
    if !frame.contains(extent) {
        return Err(Error::Bounds);
    }
    let n = l.width * l.height;
    let mut budget = Budget::new(4096 * 2160 * 40);
    // u64 storage keeps all pointer-reinterpreted samples and curve buffers aligned.
    let bytes = n * l.depth.pixel_bytes();
    let count = bytes.div_ceil(8);
    let mut src = allocate(count, 0u64, &mut budget)?;
    let mut dst = allocate(count, 0u64, &mut budget)?;
    #[cfg(feature = "profile")]
    let started = std::time::Instant::now();
    unsafe {
        stage(&mut src)?;
        dst.copy_from_slice(&src);
        let mut sw = World {
            data: src.as_mut_ptr().cast(),
            width: l.width as i32,
            height: l.height as i32,
            rowbytes: (l.width * l.depth.pixel_bytes()) as i32,
            ..Default::default()
        };
        let mut dw = World {
            data: dst.as_mut_ptr().cast(),
            ..sw
        };
        let mut state = RenderState {
            src_world: &mut sw,
            dst_world: &mut dw,
            tolerance: p.tolerance,
            tolerance_lo: p.tolerance,
            tolerance_hi: p.tolerance,
            threshold: p.tolerance,
            ..Default::default()
        };
        #[cfg(feature = "profile")]
        let staged = std::time::Instant::now();
        // Classification only reads the immutable source. Each worker owns its
        // descriptors, register/stack carriers and disjoint result rows. Dispatch
        // reads/writes destination pixels and must retain the original order.
        let mut classes = if REFERENCE {
            Vec::new()
        } else {
            allocate(n, Classified::default(), &mut budget)?
        };
        if !REFERENCE {
            classify(
                &src,
                &mut classes,
                l.width,
                l.height,
                l.depth,
                p.tolerance,
                extent,
                workers,
            )?;
        }
        #[cfg(feature = "profile")]
        let classified = std::time::Instant::now();
        for y in extent.top()..extent.bottom() {
            for x in extent.left()..extent.right() {
                #[cfg(all(test, feature = "generated-reference"))]
                if REFERENCE {
                    if l.depth == Depth::U8 {
                        crate::generated::ScanlinePixel8_Main(
                            (&mut state as *mut RenderState).cast(),
                            x,
                            y,
                            std::ptr::null_mut(),
                            std::ptr::null_mut(),
                        );
                    } else {
                        crate::generated::ScanlinePixel16_Main(
                            (&mut state as *mut RenderState).cast(),
                            x,
                            y,
                            std::ptr::null_mut(),
                            std::ptr::null_mut(),
                        );
                    }
                    continue;
                }
                let classified = classes[y as usize * l.width + x as usize];
                let kinds = classified.kinds;
                if kinds == [0; 4] {
                    continue;
                }
                let mut neighbors = [0u64; 10];
                if l.depth == Depth::U8 {
                    NeighborExtract8(x, y, &mut state, neighbors.as_mut_ptr());
                } else {
                    NeighborExtract16(x, y, &mut state, neighbors.as_mut_ptr());
                }
                for (d, kind) in [5, 3, 1, 7].into_iter().zip(kinds) {
                    if kind == 0 {
                        continue;
                    }
                    if kind == 4 {
                        let i = y as usize * l.width + x as usize;
                        if l.depth == Depth::U8 {
                            dst.as_mut_ptr()
                                .cast::<[u8; 4]>()
                                .add(i)
                                .write(classified.blend.map(|v| v as u8));
                        } else {
                            dst.as_mut_ptr()
                                .cast::<[u16; 4]>()
                                .add(i)
                                .write(classified.blend);
                        }
                        continue;
                    }
                    if l.depth == Depth::U8 {
                        crate::kernels::DispatchDirection8(
                            &mut state,
                            neighbors.as_mut_ptr(),
                            x as u32,
                            y as u32,
                            d,
                            kind,
                        );
                    } else {
                        crate::kernels::DispatchDirection16(
                            &mut state,
                            neighbors.as_mut_ptr(),
                            x as u32,
                            y as u32,
                            d,
                            kind,
                        );
                    }
                }
            }
        }
        #[cfg(feature = "profile")]
        let filtered = std::time::Instant::now();
        publish(&dst)?;
        #[cfg(feature = "profile")]
        eprintln!(
            "staging={:?} classification={:?} dispatch={:?} packing={:?}",
            staged - started,
            classified - staged,
            filtered - classified,
            filtered.elapsed()
        );
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn classify(
    src: &[u64],
    classes: &mut [Classified],
    width: usize,
    height: usize,
    depth: Depth,
    tolerance: i32,
    extent: Rect,
    requested: usize,
) -> Result<()> {
    if requested == 0 {
        return Err(Error::Geometry);
    }
    let workers = requested
        .min(std::thread::available_parallelism().map_or(1, usize::from))
        .min((classes.len() / 16384).max(1));
    let row = |y: usize, output: &mut [Classified]| {
        if (y as i32) < extent.top() || y as i32 >= extent.bottom() {
            return;
        }
        let mut world = World {
            data: src.as_ptr().cast_mut().cast(),
            width: width as i32,
            height: height as i32,
            rowbytes: (width * depth.pixel_bytes()) as i32,
            ..Default::default()
        };
        let mut state = RenderState {
            src_world: &mut world,
            tolerance,
            tolerance_lo: tolerance,
            tolerance_hi: tolerance,
            threshold: tolerance,
            ..Default::default()
        };
        for x in extent.left()..extent.right() {
            let mut neighbors = [0u64; 10];
            unsafe {
                if depth == Depth::U8 {
                    NeighborExtract8(x, y as i32, &mut state, neighbors.as_mut_ptr());
                } else {
                    NeighborExtract16(x, y as i32, &mut state, neighbors.as_mut_ptr());
                }
                for (slot, d) in output[x as usize].kinds.iter_mut().zip([5, 3, 1, 7]) {
                    *slot = if depth == Depth::U8 {
                        Classifier8(&mut state, x as u32, y as u32, neighbors.as_mut_ptr(), d)
                    } else {
                        Classifier16Exact(&mut state, x as u32, y as u32, neighbors.as_mut_ptr(), d)
                    };
                }
                if output[x as usize].kinds.contains(&4) {
                    output[x as usize].blend = if depth == Depth::U8 {
                        color_blend5::<false>(neighbors.as_ptr())
                    } else {
                        color_blend5::<true>(neighbors.as_ptr())
                    };
                }
            }
        }
    };
    if workers == 1 {
        for (y, output) in classes.chunks_mut(width).enumerate() {
            row(y, output);
        }
        Ok(())
    } else {
        olm_core::parallel_rows(classes, width, workers, row)
    }
}

#[derive(Clone, Copy, Default)]
struct Classified {
    kinds: [i32; 4],
    blend: [u16; 4],
}

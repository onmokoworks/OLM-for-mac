//! Host-independent ColorKey kernel, translated from the current Mac sources.
use olm_core::{allocate, Budget, Depth, Error, Pixel, View, ViewMut};
use olm_math::{x86, Mode};
/// 2026-11-12 upstream palette capacity (200 colors, eight controls each).
pub const MAX_COLORS: usize = 200;
#[derive(Clone, Debug)]
pub struct Key {
    pub enabled: bool,
    pub replace: bool,
    pub color: [f32; 3],
    pub replacement: [f32; 3],
    pub threshold: f32,
    pub components: [f32; 3],
}
#[derive(Clone, Debug)]
pub struct Params {
    pub keep: bool,
    pub threshold: f32,
    pub premultiplied: bool,
    pub space: i32,
    pub precision: i32,
    pub per_color: bool,
    pub per_component: bool,
    pub components: [f32; 3],
    pub thin: i32,
    pub thin_distance: i32,
    pub blur: f32,
    pub blur_distance: i32,
    pub direction: i32,
    pub replace: bool,
    pub keys: Vec<Key>,
    pub step_x: f32,
    pub step_y: f32,
}
impl Default for Params {
    fn default() -> Self {
        Self {
            keep: false,
            threshold: 0.0,
            premultiplied: false,
            space: 1,
            precision: 1,
            per_color: false,
            per_component: false,
            components: [0.0; 3],
            thin: 0,
            thin_distance: 1,
            blur: 0.0,
            blur_distance: 1,
            direction: 2,
            replace: false,
            keys: vec![],
            step_x: 1.0,
            step_y: 1.0,
        }
    }
}
fn replacement(p: Pixel, c: [f32; 3]) -> Pixel {
    match p {
        Pixel::U8(mut a) => {
            for j in 0..3 {
                a[j + 1] = x86::cvttss2si(c[j] * 255.0).clamp(0, 255) as u8;
            }
            Pixel::U8(a)
        }
        Pixel::U16(mut a) => {
            for j in 0..3 {
                a[j + 1] = x86::cvttss2si(c[j] * 32768.0).clamp(0, 32768) as u16;
            }
            Pixel::U16(a)
        }
        Pixel::F32(mut a) => {
            a[1..].copy_from_slice(&c);
            Pixel::F32(a)
        }
    }
}
fn scale_alpha(p: Pixel, weight: f32) -> Pixel {
    match p {
        Pixel::U8(mut a) => {
            a[0] = x86::cvttss2si(a[0] as f32 * weight) as u8;
            Pixel::U8(a)
        }
        Pixel::U16(mut a) => {
            a[0] = x86::cvttss2si(a[0] as f32 * weight) as u16;
            Pixel::U16(a)
        }
        Pixel::F32(mut a) => {
            a[0] = x86::mul(a[0], weight);
            Pixel::F32(a)
        }
    }
}
/// Full-frame neighborhood rendering; point-only renders also accept cropped output.
pub fn render(input: &View<'_>, out: &mut ViewMut<'_>, p: &Params) -> olm_core::Result<()> {
    let l = out.layout();
    render_impl(input, out, p, (l.width, l.height))
}
/// Original Smart workers classify the delivered extent in an input-sized matte,
/// use local coordinates (world origins do not participate), then commit its crop.
pub fn render_smart(input: &View<'_>, out: &mut ViewMut<'_>, p: &Params) -> olm_core::Result<()> {
    let a = input.layout();
    let b = out.layout();
    if b.depth != a.depth {
        return Err(Error::Unsupported);
    }
    if b.width > a.width || b.height > a.height {
        return Err(Error::Geometry);
    }
    let l = olm_core::Layout {
        origin: (0, 0),
        ..a
    };
    let mut budget = Budget::new(1024 * 1024 * 1024);
    let mut bytes = allocate(l.span()?, 0u8, &mut budget)?;
    render_impl(
        &input.rebased((0, 0))?,
        &mut ViewMut::new(&mut bytes, l)?,
        p,
        (b.width, b.height),
    )?;
    let stage = View::new(&bytes, l)?;
    for y in 0..b.height {
        out.row_mut(y)?
            .copy_from_slice(&stage.row(y)?[..b.width * b.depth.pixel_bytes()]);
    }
    Ok(())
}
fn render_impl(
    input: &View<'_>,
    out: &mut ViewMut<'_>,
    p: &Params,
    classify: (usize, usize),
) -> olm_core::Result<()> {
    let l = out.layout();
    let w = l.width;
    let h = l.height;
    let n = olm_core::image_len(w, h)?;
    if p.keys.len() > MAX_COLORS
        || !(1..=6).contains(&p.space)
        || !(1..=3).contains(&p.direction)
        || !p.blur.is_finite()
        || !(0.0..=4000.0).contains(&p.blur)
        || !(-4000..=4000).contains(&p.thin)
    {
        return Err(Error::Unsupported);
    }
    if (p.thin != 0 || p.blur != 0.0)
        && (input.layout().width != w
            || input.layout().height != h
            || input.layout().origin != l.origin)
    {
        return Err(Error::Unsupported);
    }
    if input.layout().depth != l.depth {
        return Err(Error::Unsupported);
    }
    // Worst-case live planes including distance/envelope scratch, bounded before allocations.
    let mut budget = Budget::new(1024 * 1024 * 1024);
    budget.reserve(n.checked_mul(128).ok_or(Error::Overflow)?)?;
    let mut epsilon = match l.depth {
        Depth::U8 => 0.5 / 255.0,
        Depth::U16 => 1.0 / 65536.0,
        Depth::F32 => 1.0e-6f32,
    };
    if p.precision == 3 {
        epsilon = 0.5 / 255.0
    } else if p.precision == 2 && epsilon < 1.0 / 65536.0 {
        epsilon = 1.0 / 65536.0
    }
    // Conversion depends only on the key and selected color space. Preserve key
    // order because hit() may mutate cmp and the first matching index is retained.
    let converted: Vec<_> = p
        .keys
        .iter()
        .map(|k| crate::color::convert(k.color, p.space))
        .collect();
    if p.thin == 0 && p.blur == 0.0 {
        let il = input.layout();
        if !il.rect()?.contains(l.rect()?) {
            return Err(Error::Bounds);
        }
        let dx = (i64::from(l.origin.0) - i64::from(il.origin.0)) as usize;
        let dy = (i64::from(l.origin.1) - i64::from(il.origin.1)) as usize;
        let bytes = l.depth.pixel_bytes();
        out.for_each_row(|y, row| {
            let source = input.row(y + dy).expect("validated coverage");
            for (x, target) in row.chunks_exact_mut(bytes).enumerate() {
                let src = olm_core::read_pixel(&source[(x + dx) * bytes..], l.depth);
                let index = if x < classify.0 && y < classify.1 {
                    classify_pixel(src, p, &converted, epsilon)
                } else {
                    None
                };
                let mut dst = if index.is_some() {
                    src
                } else {
                    src.with_alpha(0.0)
                };
                if p.keep && p.replace {
                    if let Some(j) = index {
                        if p.keys[j].replace {
                            dst = replacement(dst, p.keys[j].replacement);
                        }
                    }
                }
                if !p.keep {
                    dst = dst.with_alpha(x86::sub(src.alpha(), dst.alpha()));
                }
                olm_core::write_pixel(target, l.depth, dst).expect("same depth");
            }
        });
        return Ok(());
    }
    let mut source = allocate(n, Pixel::U8([0; 4]), &mut budget)?;
    let mut matched = allocate(n, 0u8, &mut budget)?;
    let mut indices = allocate(n, None, &mut budget)?;
    let mut expanded = allocate(n, false, &mut budget)?;
    // The neighborhood path has already required identical input/output geometry.
    // Decode and classify disjoint rows; retain every key comparison within a pixel.
    olm_core::parallel_rows_auto(&mut source, w, |y, row| {
        for (dst, src) in row.iter_mut().zip(input.pixels(y).expect("validated row")) {
            *dst = src;
        }
    })?;
    olm_core::parallel_rows_auto(&mut indices, w, |y, row| {
        if y >= classify.1 {
            return;
        }
        for (x, index) in row.iter_mut().take(classify.0).enumerate() {
            *index = classify_pixel(source[y * w + x], p, &converted, epsilon);
        }
    })?;
    for (value, index) in matched.iter_mut().zip(&indices) {
        *value = index.is_some() as u8;
    }
    let edge = p.thin != 0 || p.blur > 0.0;
    if edge {
        for i in 0..n {
            if source[i].alpha() == 0.0 {
                matched[i] = 0
            }
        }
    }
    let mask = |m: &[u8]| -> Vec<u8> {
        m.iter()
            .enumerate()
            .map(|(i, &v)| if source[i].alpha().is_nan() { 0 } else { v })
            .collect()
    };
    let dx = if p.step_x > 0.0 { p.step_x } else { 1.0 };
    let dy = if p.step_y > 0.0 { p.step_y } else { 1.0 };
    let mut thin_workspace = None;
    if p.thin < 0 {
        let b = crate::distance::boundary(&mask(&matched), w, h);
        let d = crate::distance::distance(&b, w, h, p.thin_distance, dx, dy, None);
        for i in 0..n {
            if !source[i].alpha().is_nan() {
                matched[i] = (matched[i] != 0 && d[i] >= p.thin.unsigned_abs() as f32) as u8
            }
        }
        if w == 1 && p.blur > 0.0 && p.blur_distance == 1 {
            thin_workspace = Some(d)
        }
    } else if p.thin > 0 {
        let m = mask(&matched);
        let d = crate::distance::distance(&m, w, h, p.thin_distance, dx, dy, None);
        if w == 1 && p.blur > 0.0 && p.blur_distance == 1 {
            thin_workspace = Some(crate::distance::distance(
                &crate::distance::boundary(&m, w, h),
                w,
                h,
                p.thin_distance,
                dx,
                dy,
                None,
            ));
        }
        for i in 0..n {
            expanded[i] = m[i] == 0 && d[i] <= p.thin as f32;
            matched[i] = (matched[i] != 0 || expanded[i]) as u8;
        }
    }
    if edge {
        for i in 0..n {
            if source[i].alpha() == 0.0 {
                matched[i] = 0
            }
        }
    }
    let distances = if p.blur > 0.0 {
        Some(crate::distance::distance(
            &crate::distance::boundary(&mask(&matched), w, h),
            w,
            h,
            p.blur_distance,
            dx,
            dy,
            thin_workspace.as_deref(),
        ))
    } else {
        None
    };
    out.for_each_row(|y, row| {
        for x in 0..w {
            let i = y * w + x;
            let src = source[i];
            let keep = matched[i] != 0;
            let mut dst = if keep { src } else { src.with_alpha(0.0) };
            if !keep
                && l.depth == Depth::F32
                && edge
                && src.alpha() == 0.0
                && (indices[i].is_some() || expanded[i])
            {
                dst = dst.with_alpha(src.alpha());
            }
            if p.keep && p.replace && !expanded[i] {
                if let Some(j) = indices[i] {
                    if p.keys[j].replace {
                        dst = replacement(dst, p.keys[j].replacement)
                    }
                }
            }
            if let Some(d) = &distances {
                let dist = d[i];
                let keep = keep && !src.alpha().is_nan();
                let mut weight = if keep { 1.0 } else { 0.0 };
                if p.direction == 2 {
                    weight = if dist == 0.0 {
                        0.5
                    } else if dist >= p.blur {
                        if keep {
                            1.0
                        } else {
                            0.0
                        }
                    } else {
                        let mut phase = dist * (1.5707963705062866f32 / p.blur);
                        if !keep {
                            phase = -phase
                        }
                        (olm_math::sinf(phase, Mode::Fma) + 1.0) * 0.5
                    };
                } else if (p.direction == 1 && keep || p.direction == 3 && !keep) && dist < p.blur {
                    let product = x86::mul(dist, 3.1415927410125732f32 / p.blur) as f64;
                    let phase = if p.direction == 1 {
                        product - 1.57079632679485
                    } else {
                        1.57079632679485 - product
                    };
                    weight = (olm_math::sin(phase, Mode::Fma) + 1.0) as f32 * 0.5;
                }
                if !keep && weight != 0.0 {
                    dst = dst.with_alpha(src.alpha())
                }
                dst = scale_alpha(dst, weight);
            }
            if !p.keep {
                dst = dst.with_alpha(x86::sub(src.alpha(), dst.alpha()));
            }
            let bytes = l.depth.pixel_bytes();
            olm_core::write_pixel(&mut row[x * bytes..(x + 1) * bytes], l.depth, dst)
                .expect("matching output depth");
        }
    });
    Ok(())
}

fn classify_pixel(src: Pixel, p: &Params, converted: &[[f32; 3]], epsilon: f32) -> Option<usize> {
    let norm = src.normalized();
    let mut cmp = [norm[1], norm[2], norm[3]];
    if p.premultiplied {
        for c in &mut cmp {
            *c *= norm[0];
        }
    }
    cmp = crate::color::convert(cmp, p.space);
    let mut index = None;
    for (j, k) in p.keys.iter().enumerate() {
        if !k.enabled {
            continue;
        }
        let t = if p.per_component {
            if p.per_color {
                k.components
            } else {
                p.components
            }
        } else {
            [if p.per_color {
                k.threshold
            } else {
                p.threshold
            }; 3]
        };
        if crate::color::hit(&mut cmp, converted[j], p.space, p.per_component, t, epsilon)
            && index.is_none()
        {
            index = Some(j);
        }
    }
    index
}

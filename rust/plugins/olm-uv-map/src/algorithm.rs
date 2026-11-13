//! UV sampling and mipmaps translated from OLMUVMap 2025 CPU kernels.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Layout {
    pub width: usize,
    pub height: usize,
    pub row_bytes: usize,
    pub bytes_per_pixel: usize,
    pub origin: (i32, i32),
}
impl Layout {
    pub fn span(self) -> Option<usize> {
        if ![4, 8, 16].contains(&self.bytes_per_pixel) {
            return None;
        }
        let row = self.width.checked_mul(self.bytes_per_pixel)?;
        if self.row_bytes < row {
            return None;
        }
        if self.height == 0 {
            return Some(0);
        }
        self.row_bytes
            .checked_mul(self.height - 1)?
            .checked_add(row)
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Params {
    pub method: i32,
    pub smoothness: f32,
}
impl Default for Params {
    fn default() -> Self {
        Self {
            method: 3,
            smoothness: 0.5,
        }
    }
}
type Pixel = [f32; 4]; // ARGB, native range until mipmap conversion.
#[cfg(feature = "witness")]
#[path = "witness_hooks.rs"]
mod witness_hooks;
struct Image {
    width: usize,
    height: usize,
    pixels: Vec<Pixel>,
}
impl Image {
    fn get(&self, x: i32, y: i32) -> Pixel {
        let x = x.clamp(0, self.width as i32 - 1) as usize;
        let y = y.clamp(0, self.height as i32 - 1) as usize;
        self.pixels[y * self.width + x]
    }
    fn decode(data: &[u8], layout: Layout) -> Result<Self, &'static str> {
        if layout.width == 0 || layout.height == 0 || layout.span().ok_or("layout")? > data.len() {
            return Err("invalid image");
        }
        let count = layout
            .width
            .checked_mul(layout.height)
            .ok_or("image overflow")?;
        let mut pixels = Vec::new();
        pixels.try_reserve_exact(count).map_err(|_| "allocation")?;
        let bytes = layout.bytes_per_pixel / 4;
        for y in 0..layout.height {
            for x in 0..layout.width {
                let mut p = [0.0; 4];
                for (c, channel) in p.iter_mut().enumerate() {
                    let at = y * layout.row_bytes + x * layout.bytes_per_pixel + c * bytes;
                    *channel = match bytes {
                        1 => data[at] as f32,
                        2 => u16::from_ne_bytes(data[at..at + 2].try_into().unwrap()) as f32,
                        _ => f32::from_ne_bytes(data[at..at + 4].try_into().unwrap()),
                    };
                }
                pixels.push(p);
            }
        }
        Ok(Self {
            width: layout.width,
            height: layout.height,
            pixels,
        })
    }
}
fn norm(x: f32, bytes: usize) -> f32 {
    match bytes {
        4 => x / 255.0,
        8 => x * (1.0 / 32768.0),
        _ => x,
    }
}
// The original comparisons canonicalize -0 to +0; f32::clamp would preserve -0.
#[allow(clippy::manual_clamp)]
fn unit(mut x: f32) -> f32 {
    if x <= 0.0 {
        x = 0.0;
    }
    if 1.0 <= x {
        x = 1.0;
    }
    x
}
fn coord(mut x: f32, max: f32) -> f32 {
    if x <= 0.0 {
        x = 0.0;
    }
    if max <= x {
        x = max;
    }
    x
}
fn quant(x: f32, bytes: usize) -> f32 {
    match bytes {
        4 => (olm_math::x86::cvttss2si(x) as u8) as f32,
        8 => (olm_math::x86::cvttss2si(x) as u16) as f32,
        _ => x,
    }
}

// 1800011c0 / 14a0 / 1770. Integer bilinear truncates before alpha modulation.
fn bilinear(image: &Image, x: f32, y: f32, bytes: usize) -> Pixel {
    let ix = x.floor() as i32;
    let iy = y.floor() as i32;
    let dx = x - x.floor();
    let dy = y - y.floor();
    let a = image.get(ix, iy);
    let b = image.get(ix + 1, iy);
    let c = image.get(ix, iy + 1);
    let d = image.get(ix + 1, iy + 1);
    let rx = 1.0 - dx;
    let ry = 1.0 - dy;
    let mut p = [0.0; 4];
    for ch in 1..4 {
        p[ch] = quant(
            (a[ch] * rx + b[ch] * dx) * ry + (c[ch] * rx + d[ch] * dx) * dy,
            bytes,
        );
    }
    p[0] = if bytes == 16 {
        (dx * d[0] + rx * c[0]) * dy + (rx * a[0] + dx * b[0]) * ry
    } else {
        quant(
            (a[0] * rx + b[0] * dx) * ry + (d[0] * dx + c[0] * rx) * dy,
            bytes,
        )
    };
    p
}
fn position(image: &Image, u: f32, v: f32) -> (f32, f32) {
    let w = (image.width - 1) as f32;
    let h = (image.height - 1) as f32;
    (coord(w * u, w), coord(h * (1.0 - v), h))
}

// 180004ab0: non-power-of-two 3x3 weighted reduction, scalar order retained.
fn mipmaps(texture: &Image, bytes: usize) -> Result<Vec<Image>, &'static str> {
    let max = texture.width.max(texture.height);
    let count = ((crate::numerics::logf(max as f32, olm_math::Mode::Fma) as f64
        / f64::from_bits(0x3fe62e42fefa39ef)) as f32)
        .floor() as usize;
    let mut levels = Vec::new();
    let mut base = Vec::new();
    base.try_reserve_exact(texture.pixels.len())
        .map_err(|_| "allocation")?;
    base.extend(texture.pixels.iter().map(|p| p.map(|x| norm(x, bytes))));
    levels.push(Image {
        width: texture.width,
        height: texture.height,
        pixels: base,
    });
    for level in 1..=count {
        let prev = &levels[level - 1];
        let w = (texture.width >> level).max(1);
        let h = (texture.height >> level).max(1);
        let mut pixels = Vec::new();
        pixels.try_reserve_exact(w * h).map_err(|_| "allocation")?;
        for y in 0..h {
            let wy = if prev.height & 1 != 0 {
                let d = (h * 2 + 1) as f32;
                [(h - y) as f32 / d, h as f32 / d, (y + 1) as f32 / d]
            } else {
                [0.5, 0.5, 0.0]
            };
            for x in 0..w {
                let wx = if prev.width & 1 != 0 {
                    let d = (w * 2 + 1) as f32;
                    [(w - x) as f32 / d, w as f32 / d, (x + 1) as f32 / d]
                } else {
                    [0.5, 0.5, 0.0]
                };
                let mut out = [0.0; 4];
                for (row, weight) in wy.iter().enumerate() {
                    let a = prev.get((x * 2) as i32, (y * 2 + row) as i32);
                    let b = prev.get((x * 2 + 1) as i32, (y * 2 + row) as i32);
                    let c = prev.get((x * 2 + 2) as i32, (y * 2 + row) as i32);
                    let aa = weight * wx[0];
                    let bb = weight * wx[1];
                    let cc = weight * wx[2];
                    for ch in 0..4 {
                        out[ch] = ((aa * a[ch] + out[ch]) + bb * b[ch]) + cc * c[ch];
                    }
                }
                pixels.push(out);
            }
        }
        levels.push(Image {
            width: w,
            height: h,
            pixels,
        });
    }
    Ok(levels)
}

fn lod(input: &Image, texture: &Image, x: i32, y: i32, bytes: usize, smooth: f32) -> f32 {
    let mut neighbors = [0.0; 20];
    for (k, (dx, dy)) in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        .into_iter()
        .enumerate()
    {
        let p = input.get(x + dx, y + dy);
        neighbors[k * 4] = unit(norm(p[1], bytes));
        neighbors[k * 4 + 1] = unit(norm(p[2], bytes));
        neighbors[k * 4 + 3] = p[0];
    }
    let (mut umin, mut umax, mut vmin, mut vmax) = (0.0, 0.0, 0.0, 0.0);
    unsafe {
        crate::derivative::autoport_180004780(
            neighbors.as_ptr(),
            &mut umin,
            &mut umax,
            &mut vmin,
            &mut vmax,
        );
    }
    let h = (texture.height - 1) as f32;
    let w = (texture.width - 1) as f32;
    let mut v = h * vmin;
    let vhigh = h * vmax;
    if vhigh <= v {
        v = vhigh;
    }
    let uhigh = w * umax;
    let ulow = w * umin;
    let mut low = v;
    if uhigh < v {
        low = uhigh;
    }
    let mut small = ulow;
    if low <= ulow {
        small = v;
        if uhigh < v {
            small = uhigh;
        }
    }
    let mut high = v;
    if v < uhigh {
        high = uhigh;
    }
    let mut large = ulow;
    if ulow <= high {
        large = v;
        if v < uhigh {
            large = uhigh;
        }
    }
    let mut rho = (1.0 - smooth) * small + smooth * large;
    if rho <= 0.0 {
        rho = 0.0001;
    }
    crate::numerics::logf(rho, olm_math::Mode::Fma)
        / crate::numerics::logf(2.0, olm_math::Mode::Fma)
}

/// Checked ARGB worlds; texture dimensions are independent of the UV map.
/// Output padding is preserved. Preview worlds are already downsampled by AE.
pub fn render(
    input: &[u8],
    a: Layout,
    texture: Option<(&[u8], Layout)>,
    output: &mut [u8],
    b: Layout,
    params: Params,
) -> Result<(), &'static str> {
    if a.bytes_per_pixel != b.bytes_per_pixel
        || b.span().ok_or("output")? > output.len()
        || !(1..=3).contains(&params.method)
    {
        return Err("layout/parameters");
    }
    let uv = Image::decode(input, a)?;
    let texture = match texture {
        Some((data, l)) => {
            if l.bytes_per_pixel != a.bytes_per_pixel {
                return Err("texture depth");
            }
            Some(Image::decode(data, l)?)
        }
        None => None,
    };
    let bytes = a.bytes_per_pixel;
    let levels = if params.method == 3 {
        match &texture {
            Some(t) => mipmaps(t, bytes)?,
            None => Vec::new(),
        }
    } else {
        Vec::new()
    };
    if b.width == 0 || b.height == 0 {
        return Ok(());
    }
    let layout = olm_core::Layout {
        width: b.width,
        height: b.height,
        stride: b.row_bytes,
        origin: b.origin,
        depth: match b.bytes_per_pixel {
            4 => olm_core::Depth::U8,
            8 => olm_core::Depth::U16,
            _ => olm_core::Depth::F32,
        },
    };
    let mut destination = olm_core::ViewMut::new(output, layout).map_err(|_| "output layout")?;
    destination.for_each_row(|y, row| {
        for x in 0..b.width {
            let sx = x as i64 + b.origin.0 as i64 - a.origin.0 as i64;
            let sy = y as i64 + b.origin.1 as i64 - a.origin.1 as i64;
            let mut out = [0.0; 4];
            if sx >= 0 && sy >= 0 && sx < a.width as i64 && sy < a.height as i64 {
                let src = uv.get(sx as i32, sy as i32);
                if let Some(t) = &texture {
                    if src[0] > 0.0 {
                        let alpha = unit(norm(src[0], bytes));
                        let u = unit(norm(src[1], bytes));
                        let v = unit(norm(src[2], bytes));
                        if params.method < 3 {
                            let (tx, ty) = position(t, u, v);
                            out = if params.method == 1 {
                                t.get(tx as i32, ty as i32)
                            } else {
                                bilinear(t, tx, ty, bytes)
                            };
                            out[0] = quant(alpha * out[0], bytes);
                        } else {
                            let l = lod(&uv, t, sx as i32, sy as i32, bytes, params.smoothness);
                            let max = (levels.len() - 1) as f32;
                            let lo = l.floor().clamp(0.0, max) as usize;
                            let hi = (l.floor() + 1.0).clamp(0.0, max) as usize;
                            let f = l.clamp(0.0, max);
                            let f = f - f.floor();
                            let p = &levels[lo];
                            let q = &levels[hi];
                            let (px, py) = position(p, u, v);
                            let (qx, qy) = position(q, u, v);
                            let p = bilinear(p, px, py, 16);
                            let q = bilinear(q, qx, qy, 16);
                            let inv = 1.0 - f;
                            let scale = match bytes {
                                4 => 255.0,
                                8 => 32768.0,
                                _ => 1.0,
                            };
                            for ch in 0..4 {
                                let value = if bytes == 16 {
                                    q[ch] * f + inv * p[ch]
                                } else {
                                    p[ch] * inv + q[ch] * f
                                };
                                out[ch] = quant(
                                    if ch == 0 {
                                        (value * alpha) * scale
                                    } else {
                                        value * scale
                                    },
                                    bytes,
                                );
                            }
                        }
                    }
                }
            }
            for (ch, channel) in out.iter().enumerate() {
                let at = x * bytes + ch * (bytes / 4);
                match bytes {
                    4 => row[at] = *channel as u8,
                    8 => row[at..at + 2].copy_from_slice(&(*channel as u16).to_ne_bytes()),
                    _ => row[at..at + 4].copy_from_slice(&channel.to_ne_bytes()),
                }
            }
        }
    });
    Ok(())
}

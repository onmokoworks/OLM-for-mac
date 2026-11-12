//! Bounded vertex storage and the four elementary corner emitters.
//! Cardinal families and full polygon dispatch live in geometry.rs.
use crate::types::{Pixel, Vertex};
use olm_core::{Error, Result};

pub struct Plane<'a> {
    pixels: &'a [Pixel],
    width: usize,
    height: usize,
    stride: usize,
}
impl<'a> Plane<'a> {
    /// Stride in pixels, not bytes. AE byte strides are decoded before scratch setup.
    pub fn new(pixels: &'a [Pixel], width: usize, height: usize, stride: usize) -> Result<Self> {
        if width == 0 || height == 0 || width >= i32::MAX as usize || height >= i32::MAX as usize {
            return Err(Error::Geometry);
        }
        let len = (height - 1)
            .checked_mul(stride)
            .and_then(|v| v.checked_add(width))
            .ok_or(Error::Overflow)?;
        if stride < width || pixels.len() < len {
            return Err(Error::Bounds);
        }
        Ok(Self {
            pixels,
            width,
            height,
            stride,
        })
    }
    fn get(&self, x: i32, y: i32) -> Result<Pixel> {
        if x < 0 || y < 0 || x as usize >= self.width || y as usize >= self.height {
            return Err(Error::Bounds);
        }
        Ok(self.pixels[y as usize * self.stride + x as usize])
    }
}
#[derive(Clone, Copy, Debug)]
#[repr(i32)]
pub enum Corner {
    Nw,
    Ne,
    Sw,
    Se,
}

pub struct Polygon<'a> {
    plane: Plane<'a>,
    x: i32,
    y: i32,
    smoothness: f32,
    samples: [Vertex; 12],
    count: usize,
}
impl<'a> Polygon<'a> {
    pub fn new(plane: Plane<'a>, x: i32, y: i32, smoothness: f32) -> Result<Self> {
        plane.get(x, y)?;
        Ok(Self {
            plane,
            x,
            y,
            smoothness,
            samples: [Vertex::default(); 12],
            count: 0,
        })
    }
    pub fn samples(&self) -> &[Vertex] {
        &self.samples[..self.count]
    }
    pub fn append(&mut self, x: i32, y: i32, weight: f32) -> Result<()> {
        if self.count >= 12 {
            return Ok(());
        }
        let pixel = self.plane.get(x, y)?;
        self.samples[self.count] = Vertex { pixel, weight };
        self.count += 1;
        Ok(())
    }
    pub fn normalize(&mut self) {
        if self.count == 0 {
            return;
        }
        let inverse = 1.0 / self.count as f32;
        for s in &mut self.samples[..self.count] {
            s.weight *= inverse;
        }
    }
    pub fn corner(&mut self, corner: Corner, step: f32) -> Result<()> {
        let x = self.x;
        let y = self.y;
        let right = self.plane.width as i32 - 1;
        let bottom = self.plane.height as i32 - 1;
        let offsets = match corner {
            Corner::Nw => {
                if x == 0 || y == 0 {
                    return Ok(());
                }
                [(-1, 0), (-1, -1), (0, -1)]
            }
            Corner::Ne => {
                if x == right || y == 0 {
                    return Ok(());
                }
                [(0, -1), (1, -1), (1, 0)]
            }
            Corner::Sw => {
                if x == 0 || y == bottom {
                    return Ok(());
                }
                [(-1, 0), (-1, 1), (0, 1)]
            }
            Corner::Se => {
                if x == right || y == bottom {
                    return Ok(());
                }
                [(0, 1), (1, 1), (1, 0)]
            }
        };
        let outer = step * self.smoothness * 0.4;
        let inner = step * self.smoothness * 0.2;
        for ((dx, dy), weight) in offsets.into_iter().zip([outer, inner, outer]) {
            self.append(x + dx, y + dy, weight)?;
        }
        Ok(())
    }
}

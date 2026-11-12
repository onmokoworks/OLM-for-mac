//! Literal class-plane walkers from classification.inc and polygon_scan.inc.
//! Scans require an in-image start. Reads outside the plane return zero.
use olm_core::{Error, Result};

pub struct Grid<'a> {
    bytes: &'a [u8],
    width: i32,
    height: i32,
    stride: usize,
}
impl<'a> Grid<'a> {
    pub fn new(bytes: &'a [u8], width: i32, height: i32, stride: usize) -> Result<Self> {
        if width <= 0 || height <= 0 || width == i32::MAX || height == i32::MAX {
            return Err(Error::Geometry);
        }
        let row = (width as usize).checked_mul(4).ok_or(Error::Overflow)?;
        let len = (height as usize - 1)
            .checked_mul(stride)
            .and_then(|v| v.checked_add(row))
            .ok_or(Error::Overflow)?;
        if stride < row || bytes.len() < len {
            return Err(Error::Bounds);
        }
        Ok(Self {
            bytes,
            width,
            height,
            stride,
        })
    }
    fn contains(&self, x: i32, y: i32) -> bool {
        x >= 0 && x < self.width && y >= 0 && y < self.height
    }
    pub fn byte(&self, x: i32, y: i32, channel: usize) -> u8 {
        if !self.contains(x, y) || channel >= 4 {
            0
        } else {
            self.bytes[y as usize * self.stride + x as usize * 4 + channel]
        }
    }
    fn b(&self, x: i32, y: i32, c: usize) -> bool {
        self.byte(x, y, c) != 0
    }
    pub fn axial(&self, kind: Axial, x: i32, y: i32) -> Result<[i32; 3]> {
        if !self.contains(x, y) {
            return Err(Error::Bounds);
        }
        Ok(match kind {
            Axial::D0d0 => self.up(x, y, false),
            Axial::D3b0 => self.up(x, y, true),
            Axial::D6a0 => self.down(x, y, false),
            Axial::Da50 => self.down(x, y, true),
            Axial::D520 => self.left(x, y, false),
            Axial::D230 => self.left(x, y, true),
            Axial::Dbd0 => self.right(x, y, false),
            Axial::D800 => self.right(x, y, true),
        })
    }
    fn up(&self, x: i32, y0: i32, shifted: bool) -> [i32; 3] {
        let xp = x + shifted as i32;
        if !self.contains(xp, y0) {
            return [xp, y0, 0];
        }
        let mut y = y0;
        if y0 > 0 {
            let mut exited_a0 = false;
            loop {
                if !self.b(xp, y, 0) {
                    exited_a0 = true;
                    break;
                }
                if self.b(xp, y, 1) || self.b(xp - 1, y, 1) {
                    break;
                }
                y -= 1;
                if y < 1 {
                    break;
                }
            }
            if exited_a0 {
                y += 1;
            }
        }
        [
            x,
            y,
            classify(
                self.b(xp, y - 1, 0),
                self.b(xp, y, 1),
                self.b(xp - 1, y, 1),
                self.b(xp - 1, y, 3),
                self.b(xp, y, 2),
            ),
        ]
    }
    fn down(&self, x: i32, y0: i32, shifted: bool) -> [i32; 3] {
        let xp = x + shifted as i32;
        if !self.contains(xp, y0) {
            return [xp, y0, 0];
        }
        let mut y = y0 + 1;
        while y < self.height - 1 {
            if !self.b(xp, y, 0) || self.b(xp, y, 1) || self.b(xp - 1, y, 1) {
                break;
            }
            y += 1;
        }
        let class = if y - 1 < self.height - 1 {
            classify(
                self.b(xp, y, 0),
                self.b(xp - 1, y, 1),
                self.b(xp, y, 1),
                self.b(xp - 1, y, 3),
                self.b(xp, y, 2),
            )
        } else {
            0
        };
        [x, y - 1, class]
    }
    fn left(&self, x0: i32, y: i32, shifted: bool) -> [i32; 3] {
        let yp = y + shifted as i32;
        if !self.contains(x0, yp) {
            return [x0, yp, 0];
        }
        let mut x = x0;
        if x0 > 0 {
            let mut exited_r0 = false;
            loop {
                if !self.b(x, yp, 1) {
                    exited_r0 = true;
                    break;
                }
                if self.b(x, yp, 0) || self.b(x, yp - 1, 0) {
                    break;
                }
                x -= 1;
                if x < 1 {
                    break;
                }
            }
            if exited_r0 {
                x += 1;
            }
        }
        [
            x,
            y,
            classify(
                self.b(x - 1, yp, 1),
                self.b(x, yp - 1, 0),
                self.b(x, yp, 0),
                self.b(x, yp, 2),
                self.b(x - 1, yp, 3),
            ),
        ]
    }
    fn right(&self, x0: i32, y: i32, shifted: bool) -> [i32; 3] {
        let yp = y + shifted as i32;
        if !self.contains(x0, yp) {
            return [x0, yp, 0];
        }
        let mut x = x0 + 1;
        while x < self.width - 1 {
            if !self.b(x, yp, 1) || self.b(x, yp, 0) || self.b(x, yp - 1, 0) {
                break;
            }
            x += 1;
        }
        // d800 always classifies the one-past-end probe; dbd0 gates it.
        let class = if shifted || x - 1 < self.width - 1 {
            classify(
                self.b(x, yp, 1),
                self.b(x, yp, 0),
                self.b(x, yp - 1, 0),
                self.b(x, yp, 2),
                self.b(x - 1, yp, 3),
            )
        } else {
            0
        };
        [x - 1, y, class]
    }
    pub fn diagonal(&self, kind: Diagonal, x: i32, y: i32) -> Result<[i32; 2]> {
        if !self.contains(x, y) {
            return Err(Error::Bounds);
        }
        Ok(match kind {
            Diagonal::D108d0 => self.d108d0(x, y),
            Diagonal::D109d0 => self.down_right(x, y, true),
            Diagonal::D10ad0 => self.down_right(x, y, false),
            Diagonal::D10bd0 => self.step_up(x, y, false),
            Diagonal::D10d20 => self.d10d20(x, y),
            Diagonal::D10e40 => self.step_up(x, y, true),
        })
    }
    fn d108d0(&self, x: i32, y: i32) -> [i32; 2] {
        let y1 = y + 1;
        if y1 < self.height {
            let steps = ((self.height - y1) - 1).min(x);
            if steps != 0 && self.b(x, y1, 0) {
                let (mut cx, mut cy) = (x, y1);
                for _ in 0..steps {
                    let (nx, ny) = (cx - 1, cy + 1);
                    if !self.b(nx, ny, 1) || self.b(nx, ny, 3) || self.b(nx, ny - 1, 3) {
                        break;
                    }
                    cx = nx;
                    cy = ny;
                    if !self.b(nx, ny, 0) {
                        break;
                    }
                }
                return [cx, cy - 1];
            }
        }
        [x, y]
    }
    fn down_right(&self, x: i32, y: i32, shifted: bool) -> [i32; 2] {
        let y1 = y + shifted as i32;
        if shifted && y1 >= self.height {
            return [x, y];
        }
        let lim_h = self.height - y1;
        let lim_w = self.width - x;
        let steps = if lim_h <= lim_w - 1 { lim_h } else { lim_w };
        if steps != 1 && self.b(x + 1, y1, 0) {
            let (mut cx, mut cy) = (x, y1);
            for _ in 0..steps - 1 {
                let (nx, ny) = (cx + 1, cy + 1);
                if !self.b(nx, ny, 1) || self.b(nx, ny, 2) || self.b(nx, ny - 1, 2) {
                    break;
                }
                cx = nx;
                cy = ny;
                if !self.b(nx + 1, ny, 0) {
                    break;
                }
            }
            return [cx, cy - shifted as i32];
        }
        [x, y]
    }
    fn step_up(&self, x: i32, y: i32, right: bool) -> [i32; 2] {
        let y1 = y + 1;
        if y1 >= self.height {
            return [x, y];
        }
        let steps = y1.min(if right { self.width - x - 1 } else { x });
        let channel = if right { 3 } else { 2 };
        if steps == 0 || self.b(x, y1, channel) || self.b(x, y, channel) {
            return [x, y];
        }
        let (mut cx, mut py) = (x, y);
        for _ in 0..steps {
            let nx = cx + if right { 1 } else { -1 };
            let a_col = if right { nx } else { cx };
            if !self.b(nx, py, 1) || !self.b(a_col, py, 0) {
                return [cx, py];
            }
            if self.b(nx, py, channel) || self.b(nx, py - 1, channel) {
                return [nx, py - 1];
            }
            cx = nx;
            py -= 1;
        }
        [cx, py]
    }
    fn d10d20(&self, x: i32, y: i32) -> [i32; 2] {
        let steps = y.min(x);
        if steps == 0 || self.b(x, y, 2) || self.b(x, y - 1, 2) {
            return [x, y];
        }
        let (mut pre_x, mut row) = (x, y - 1);
        for i in 0..steps {
            let nx = pre_x - 1;
            if !self.b(nx, row, 1) || !self.b(pre_x, row, 0) {
                return [pre_x, row + 1];
            }
            if self.b(nx, row, 2) || self.b(nx, row - 1, 2) || i + 1 >= steps {
                return [nx, row];
            }
            pre_x = nx;
            row -= 1;
        }
        [x, y]
    }
}

#[derive(Clone, Copy, Debug)]
#[repr(i32)]
pub enum Axial {
    D0d0,
    D230,
    D3b0,
    D520,
    D6a0,
    D800,
    Da50,
    Dbd0,
}
#[derive(Clone, Copy, Debug)]
#[repr(i32)]
pub enum Diagonal {
    D108d0,
    D109d0,
    D10ad0,
    D10bd0,
    D10d20,
    D10e40,
}

pub fn classify(p1: bool, p2: bool, p3: bool, p4: bool, p5: bool) -> i32 {
    let idx = p1 as usize | (p3 as usize) << 1 | (p2 as usize) << 2;
    if idx == 7 {
        6 + p4 as i32 + 2 * p5 as i32
    } else {
        [0, 0, 1, 4, 2, 3, 5][idx]
    }
}
pub fn trapezoid(width: f32, position: i32, edge: f32) -> f32 {
    if width == 0.0 || edge == 0.0 {
        return 0.0;
    }
    let pos = position as f32;
    if !(pos < width) {
        return 0.0;
    }
    let f2 = (1.0 - pos / width) * edge;
    if width < pos + 1.0 {
        return (width - pos) * f2 * 0.5;
    }
    let next = (pos + 1.0) / width;
    ((1.0 - next) * edge + f2) * 0.5
}

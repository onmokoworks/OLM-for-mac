//! Local translation of shared core/dblur_noise.h; hoisting candidate.
use olm_math::{powf, Mode};
pub struct Mt {
    state: [u32; 624],
    index: usize,
}
impl Mt {
    pub fn new(seed: u32) -> Self {
        let mut s = Self {
            state: [0; 624],
            index: 624,
        };
        s.state[0] = seed;
        for i in 1..624 {
            s.state[i] = 1812433253u32
                .wrapping_mul(s.state[i - 1] ^ (s.state[i - 1] >> 30))
                .wrapping_add(i as u32);
        }
        s
    }
    pub fn next(&mut self) -> u32 {
        if self.index == 624 {
            for i in 0..624 {
                let y = (self.state[i] & 0x80000000) | (self.state[(i + 1) % 624] & 0x7fffffff);
                self.state[i] = self.state[(i + 397) % 624]
                    ^ (y >> 1)
                    ^ if y & 1 != 0 { 0x9908b0df } else { 0 };
            }
            self.index = 0;
        }
        let mut y = self.state[self.index];
        self.index += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c5680;
        y ^= (y << 15) & 0xefc60000;
        y ^= y >> 18;
        y
    }
    fn unit(&mut self) -> f64 {
        self.next() as f64 * (1.0 / 4294967296.0)
    }
}
pub struct Plane {
    pub samples: Vec<f32>,
    pub width: usize,
    pub cell: f32,
}
impl Plane {
    pub fn demanded(
        source: &[[f32; 4]],
        w: usize,
        h: usize,
        rows: usize,
        cell: f32,
        offset: f32,
        seed: u32,
        interpolate: bool,
    ) -> Result<Self, crate::algorithm::Error> {
        let nw = (w as f32 / cell + 3.0) as usize;
        let nh = (h as f32 / cell + 3.0) as usize;
        let mut samples =
            crate::algorithm::zeros(nw.checked_mul(nh).ok_or(crate::algorithm::Error::Size)?)?;
        for y in 0..rows {
            for x in 0..w {
                if source[y * w + x][3] == 0.0 {
                    continue;
                }
                let ix = (x as f32 / cell) as usize;
                let iy = (y as f32 / cell) as usize;
                let k = iy * nw + ix;
                samples[k] = 1.0;
                if interpolate {
                    samples[k + 1] = 1.0;
                    samples[k + nw] = 1.0;
                    samples[k + nw + 1] = 1.0;
                }
            }
        }
        let mut mt = Mt::new(seed);
        let mut table = [0.0; 101];
        for v in &mut table {
            *v = (mt.unit() * 2.0 - 1.0) as f32;
        }
        let read = |i: i32| {
            if (0..101).contains(&i) {
                table[i as usize]
            } else {
                0.0
            }
        };
        for v in &mut samples {
            let base = mt.unit() as f32;
            let mut pos = (mt.unit() * 100.0 + offset as f64) as f32;
            if *v == 0.0 {
                continue;
            }
            while pos >= 100.0 {
                pos -= 100.0;
            }
            let i = pos as i32;
            let f = pos - i as f32;
            let mut smooth = powf(f, 2.0, Mode::Fma);
            smooth *= 3.0 - (f + f);
            let interp = (1.0 - smooth) * read(i) + smooth * read(i + 1);
            let value = (interp as f64 * 0.5 + base as f64) as f32;
            *v = if value < 0.0 {
                0.0
            } else if value > 1.0 {
                1.0
            } else {
                value
            };
        }
        Ok(Self {
            samples,
            width: nw,
            cell,
        })
    }
    pub fn sample(&self, x: usize, y: usize, interpolate: bool) -> f32 {
        let sx = x as f32 / self.cell;
        let sy = y as f32 / self.cell;
        let ix = sx as usize;
        let iy = sy as usize;
        let k = iy * self.width + ix;
        if !interpolate {
            return self.samples[k];
        }
        let fx = sx - ix as f32;
        let fy = sy - iy as f32;
        let xx = fx * fx;
        let yy = fy * fy;
        let ax = (3.0 - (fx + fx)) * xx;
        let ay = (3.0 - (fy + fy)) * yy;
        let bx = 1.0 - ax as f64;
        let by = 1.0 - ay as f64;
        (by * ax as f64) as f32 * self.samples[k + 1]
            + (bx * by) as f32 * self.samples[k]
            + (bx * ay as f64) as f32 * self.samples[k + self.width]
            + ay * ax * self.samples[k + self.width + 1]
    }
}

//! MT19937 and RadialBlur's float canonical conversion (core/dblur_noise.h).
use crate::math::*;
// Test-only counterfactual reads; absent from the plug-in build. Default zero.
#[cfg(test)]
pub(crate) mod probe {
    use std::cell::{Cell, RefCell};
    thread_local! {
        pub static FILL: Cell<f32> = const { Cell::new(0.0) };
        pub static TRACE: RefCell<Option<Vec<i32>>> = const { RefCell::new(None) };
    }
}
struct Mt {
    state: [u32; 624],
    index: usize,
}
impl Mt {
    fn new(seed: u32) -> Self {
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
    fn unit(&mut self) -> f32 {
        if self.index == 624 {
            for i in 0..624 {
                let x = (self.state[i] & 0x80000000) | (self.state[(i + 1) % 624] & 0x7fffffff);
                self.state[i] = self.state[(i + 397) % 624]
                    ^ (x >> 1)
                    ^ if x & 1 != 0 { 0x9908b0df } else { 0 };
            }
            self.index = 0;
        }
        let mut y = self.state[self.index];
        self.index += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c5680;
        y ^= (y << 15) & 0xefc60000;
        y ^= y >> 18;
        y as f32 / 4294967296.0
    }
}
pub fn generate(w: usize, h: usize, size: f32, offset: f32, seed: u32) -> (Vec<f32>, usize) {
    let inv = div(1.0, size);
    let nw = int(add(mul(w as f32, inv), 3.0)) as usize;
    let nh = int(add(mul(h as f32, inv), 3.0)) as usize;
    let mut mt = Mt::new(seed);
    let mut table = [0.0; 101];
    for v in &mut table {
        let u = mt.unit();
        *v = sub(add(u, u), 1.0);
    }
    let at = |i: i32| {
        #[cfg(test)]
        probe::TRACE.with(|v| {
            if let Some(v) = v.borrow_mut().as_mut() {
                v.push(i);
            }
        });
        if (0..101).contains(&i) {
            table[i as usize]
        } else {
            #[cfg(test)]
            {
                probe::FILL.with(|v| v.get())
            }
            #[cfg(not(test))]
            0.0
        }
    };
    let mut values = vec![0.0; nw * nh];
    for v in &mut values {
        let base = mt.unit();
        let mut pos = add(mul(mt.unit(), 100.0), offset);
        while pos >= 100.0 {
            pos = sub(pos, 100.0);
        }
        let i = int(pos);
        let f = sub(pos, i as f32);
        let smooth = mul(sub(3.0, add(f, f)), mul(f, f));
        let left = mul(mul(sub(1.0, smooth), at(i)), 0.5);
        let right = mul(mul(smooth, at(i + 1)), 0.5);
        *v = add(base, add(left, right)).clamp(0.0, 1.0);
    }
    (values, nw)
}
pub fn sample(p: &[f32], stride: usize, size: f32, x: usize, y: usize, smooth: bool) -> f32 {
    let inv = div(1.0, size);
    let sx = mul(x as f32, inv);
    let sy = mul(y as f32, inv);
    let ix = int(sx) as usize;
    let iy = int(sy) as usize;
    let first = iy * stride + ix;
    if !smooth {
        return p[first];
    }
    let fx = sub(sx, ix as f32);
    let fy = sub(sy, iy as f32);
    let x = mul(sub(3.0, add(fx, fx)), mul(fx, fx));
    let y = mul(sub(3.0, add(fy, fy)), mul(fy, fy));
    let ix = sub(1.0, x);
    let iy = sub(1.0, y);
    add(
        add(mul(mul(iy, x), p[first + 1]), mul(mul(ix, iy), p[first])),
        add(
            mul(mul(y, x), p[first + stride + 1]),
            mul(mul(ix, y), p[first + stride]),
        ),
    )
}

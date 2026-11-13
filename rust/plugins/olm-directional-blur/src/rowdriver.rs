use crate::{algorithm::Params, noise::Plane};
use olm_math::{
    powf,
    x86::{add, cvttss2si, div, max, mul},
    Mode,
};
pub struct Driver<'a> {
    pub params: &'a Params,
    pub comp: &'a [[f32; 4]],
    pub divisor: f32,
    pub weights: [Vec<f32>; 4],
    pub noise: Option<Plane>,
    pub field: Option<Vec<f32>>,
    pub width: usize,
}
impl Driver<'_> {
    fn weight(t: &[f32], i: i32, scale: f32) -> f32 {
        t[cvttss2si(i as f32 * scale) as usize]
    }
    fn prepass(
        &self,
        x: usize,
        src: &[[f32; 4]],
        dst: &mut [[f32; 4]],
        den: &mut [f32],
        valid: &mut [f32],
        coeff: f32,
    ) {
        let a = src[x][3];
        if a == 0.0 {
            dst[x] = [0.0; 4];
            den[x] = 0.0;
            valid[x] = 0.0;
            return;
        }
        let scale = if coeff > 0.0 { div(1.0, coeff) } else { 1.0 };
        let n = cvttss2si(self.params.front_fade as f32 * coeff);
        let forward = if (x as i32).wrapping_add(n) < self.width as i32 {
            n
        } else {
            (self.width - x) as i32
        };
        let mut sum = a;
        let mut weight = 1.0;
        for i in 1..forward {
            let v = Self::weight(&self.weights[2], i, scale);
            weight = add(weight, v);
            sum = add(sum, mul(v, src[x + i as usize][3]));
        }
        let mut backward = cvttss2si(self.params.back_fade as f32 * coeff);
        if (x as i32).wrapping_sub(backward) < 0 {
            backward = x as i32;
        }
        for i in 1..backward {
            let v = Self::weight(&self.weights[3], i, scale);
            weight = add(weight, v);
            sum = add(sum, mul(v, src[x - i as usize][3]));
        }
        let n = div(sum, weight);
        den[x] = n;
        dst[x] = [mul(n, src[x][0]), mul(n, src[x][1]), mul(n, src[x][2]), n];
        valid[x] = n;
    }
    fn scatter(
        &self,
        x: usize,
        backward: bool,
        src: &[[f32; 4]],
        dst: &mut [[f32; 4]],
        den: &mut [f32],
        valid: &[f32],
        side: usize,
        coeff: f32,
    ) {
        let count = if side == 0 {
            self.params.front
        } else {
            self.params.back
        };
        let mut len = cvttss2si(count as f32 * coeff);
        let scale = if coeff > 0.0 { div(1.0, coeff) } else { 1.0 };
        if len <= 0 {
            return;
        }
        if !backward && self.width as i32 <= (x as i32).wrapping_add(len) {
            len = (self.width - x) as i32;
        } else if backward && (x as i32).wrapping_sub(len) < 0 {
            len = x as i32;
        }
        for i in 1..len {
            let c = mul(valid[x], Self::weight(&self.weights[side], i, scale));
            let target = if backward {
                x - i as usize
            } else {
                x + i as usize
            };
            for k in 0..3 {
                dst[target][k] = add(mul(c, src[x][k]), dst[target][k]);
            }
            den[target] = add(c, den[target]);
            dst[target][3] = max(dst[target][3], c);
        }
    }
    pub fn rows(
        &self,
        start: usize,
        src: &[[f32; 4]],
        dst: &mut [[f32; 4]],
        den: &mut [f32],
        valid: &mut [f32],
    ) {
        let w = self.width;
        for (local, (((s, d), de), va)) in src
            .chunks_exact(w)
            .zip(dst.chunks_exact_mut(w))
            .zip(den.chunks_exact_mut(w))
            .zip(valid.chunks_exact_mut(w))
            .enumerate()
        {
            let row = start + local;
            let comp = &self.comp[row * w..(row + 1) * w];
            for x in 0..w {
                let c = powf(
                    div(comp[x][0], self.divisor),
                    self.params.size / 100.0,
                    Mode::Fma,
                );
                self.prepass(x, s, d, de, va, c);
            }
            for x in 0..w {
                if s[x][3] == 0.0 {
                    continue;
                }
                let mut c = powf(
                    div(comp[x][0], self.divisor),
                    self.params.size / 100.0,
                    Mode::Fma,
                );
                let opacity = self.params.noise / 100.0;
                if let Some(n) = &self.noise {
                    c = mul(
                        c,
                        add(
                            mul(n.sample(x, row, self.params.noise_type == 1), opacity),
                            1.0 - opacity,
                        ),
                    );
                } else if let Some(f) = &self.field {
                    c = mul(c, add(mul(f[row * w + x], opacity), 1.0 - opacity));
                }
                if c == 0.0 {
                    continue;
                }
                for side in 0..2 {
                    let tail = if side == 0 {
                        self.params.front_tail
                    } else {
                        self.params.back_tail
                    } / 100.0;
                    let dist = f32::from_bits((row as f32 - comp[x][2]).to_bits() & 0x7fffffff);
                    let mut edge = 1.0 - div(mul(dist, tail), comp[x][3]);
                    if edge < 0.0 {
                        edge = 0.0;
                    }
                    self.scatter(x, side == 0, s, d, de, va, side, mul(edge, c));
                }
            }
        }
    }
}

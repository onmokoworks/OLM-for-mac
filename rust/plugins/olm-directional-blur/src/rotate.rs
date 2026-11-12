//! Exact scalar SSE operation and channel accumulation order from dblur_rotate.cpp.
use olm_math::{
    cosf, sinf,
    x86::{add, cvttss2si, div, mul, sub},
    Mode,
};
pub fn rgba(src: &[[f32; 4]], dst: &mut [[f32; 4]], w: usize, h: usize, angle: f32) {
    let co = cosf(angle, Mode::Fma);
    let si = sinf(angle, Mode::Fma);
    for y in 0..h {
        for x in 0..w {
            let cx = (x as i32 - (w / 2) as i32) as f32;
            let cy = (y as i32 - (h / 2) as i32) as f32;
            let sy = add(add(mul(cx, si), mul(cy, co)), (h / 2) as f32);
            let sx = add(sub(mul(cx, co), mul(cy, si)), (w / 2) as f32);
            let iy = cvttss2si(sy);
            let ix = cvttss2si(sx);
            if !(iy > 0 && iy < h as i32 - 1 && ix > 0 && ix < w as i32 - 1) {
                continue;
            }
            let fy = sub(sy, iy as f32);
            let fx = sub(sx, ix as f32);
            let by = sub(1.0, fy);
            let bx = sub(1.0, fx);
            let t = iy as usize * w + ix as usize;
            let b = t + w;
            let mut tl = mul(mul(by, bx), src[t][3]);
            let mut tr = mul(mul(by, fx), src[t + 1][3]);
            let mut bl = mul(mul(bx, fy), src[b][3]);
            let mut br = mul(mul(fy, fx), src[b + 1][3]);
            let a = add(add(add(tr, tl), bl), br);
            if a != 0.0 {
                tl = div(tl, a);
                bl = div(bl, a);
                tr = div(tr, a);
                br = div(br, a);
            }
            let r = add(
                add(
                    add(mul(src[t][0], tl), mul(tr, src[t + 1][0])),
                    mul(bl, src[b][0]),
                ),
                mul(src[b + 1][0], br),
            );
            let g = add(
                add(
                    add(mul(src[t + 1][1], tr), mul(src[t][1], tl)),
                    mul(src[b][1], bl),
                ),
                mul(src[b + 1][1], br),
            );
            let blue = add(
                add(
                    add(mul(src[t + 1][2], tr), mul(src[t][2], tl)),
                    mul(src[b][2], bl),
                ),
                mul(src[b + 1][2], br),
            );
            dst[y * w + x] = [r, g, blue, a];
        }
    }
}
pub fn scalar(src: &[f32], dst: &mut [f32], w: usize, h: usize, angle: f32) {
    let co = cosf(angle, Mode::Fma);
    let si = sinf(angle, Mode::Fma);
    for y in 0..h {
        for x in 0..w {
            let cx = (x as i32 - (w / 2) as i32) as f32;
            let cy = (y as i32 - (h / 2) as i32) as f32;
            let sy = add(add(mul(cx, si), mul(cy, co)), (h / 2) as f32);
            let sx = add(sub(mul(cx, co), mul(cy, si)), (w / 2) as f32);
            let iy = cvttss2si(sy);
            let ix = cvttss2si(sx);
            if !(iy > 0 && iy < h as i32 - 1 && ix > 0 && ix < w as i32 - 1) {
                continue;
            }
            let fy = sub(sy, iy as f32);
            let fx = sub(sx, ix as f32);
            let by = sub(1.0, fy);
            let bx = sub(1.0, fx);
            let t = iy as usize * w + ix as usize;
            let b = t + w;
            dst[y * w + x] = add(
                add(
                    add(mul(mul(by, fx), src[t + 1]), mul(mul(bx, by), src[t])),
                    mul(mul(bx, fy), src[b]),
                ),
                mul(mul(fy, fx), src[b + 1]),
            );
        }
    }
}

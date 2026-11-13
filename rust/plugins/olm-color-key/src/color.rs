//! Operation ordering from ColorMath.inc. Constants retain the reference f32 bits.
use olm_math::{atan2f, powf, x86, Mode};
fn lab_f(t: f32) -> f32 {
    if t <= 0.008856000378727913 {
        t * 7.7870001792907715 + 0.13793103396892548
    } else {
        powf(t, 0.3333300054073334, Mode::Fma)
    }
}
pub fn convert(c: [f32; 3], space: i32) -> [f32; 3] {
    let [r, g, b] = c;
    match space {
        2 => {
            let mx = x86::max(if !(b > g) { g } else { b }, r);
            let mn = x86::min(if !(g > b) { g } else { b }, r);
            let equal = |a: f32, b: f32| !(a < b) && !(a > b);
            let d = x86::sub(mx, mn);
            let mut h = if equal(mx, mn) {
                0.0
            } else if equal(r, mx) {
                (g - b) * 60.0 / d
            } else if equal(g, mx) {
                (b - r) * 60.0 * (1.0 / d) + 120.0
            } else {
                (r - g) * 60.0 * (1.0 / d) + 240.0
            };
            h %= 360.0;
            if !(h >= 0.0) {
                h += 360.0
            }
            [
                h * 0.0027777778450399637,
                if equal(mx, 0.0) { 0.0 } else { d / mx },
                mx,
            ]
        }
        3 | 4 => {
            let x = g * 2.1455016136169434 + r * 0.6380193829536438 + b * 0.2165091633796692;
            let fx = lab_f(x);
            let l = if x <= 0.008856000378727913 {
                g * 1938.031494140625 + r * 576.3229370117188 + b * 195.57272338867188
            } else {
                powf(x, 0.3333300054073334, Mode::Fma) * 116.0 - 16.0
            };
            let a = r * 1.2373713254928589 + g * 1.0727508068084717 + b * 0.5412744283676147;
            let bb = g * 0.35758259892463684 + r * 0.05800257995724678 + b * 2.8507096767425537;
            [l, (lab_f(a) - fx) * 500.0, (fx - lab_f(bb)) * 200.0]
        }
        5 => [
            g * 0.5870000123977661 + r * 0.29899999499320984 + b * 0.11400000005960464,
            b * 0.4359999895095825 - (g * 0.2888599932193756 + r * 0.14712999761104584),
            r * 0.6150000095367432 - g * 0.514989972114563 - b * 0.10001000016927719,
        ],
        6 => [
            r * 0.298909991979599 + g * 0.5866100192070007 + b * 0.11448000371456146,
            b * 0.5 - (r * 0.16874000430107117 + g * 0.33125999569892883),
            r * 0.5 - g * 0.4186899960041046 - b * 0.08130999654531479,
        ],
        _ => c,
    }
}
pub fn mutate(c: &mut [f32; 3]) {
    c[1] += 133.03700256347656;
    c[2] += 163.48800659179688;
}
fn distance(a: [f32; 3], b: [f32; 3]) -> f32 {
    let d0 = a[0] - b[0];
    let d1 = a[1] - b[1];
    let d2 = a[2] - b[2];
    let mut sq = d0 * d0;
    sq += d1 * d1;
    sq += d2 * d2;
    sq.sqrt()
}
fn lab94(a: [f32; 3], b: [f32; 3]) -> f32 {
    let c1 = (a[1] * a[1] + a[2] * a[2]).sqrt();
    let c2 = (b[1] * b[1] + b[2] * b[2]).sqrt();
    let cm = (c2 * c1).sqrt();
    let hue = |aa, bb| {
        let mut h = atan2f(bb, aa, Mode::Fma) * 57.2957763671875 + 180.0;
        if h != 0.0 {
            if h < 0.0 {
                h += 540.0
            }
            h %= 360.0;
        }
        h
    };
    let dl = b[0] - a[0];
    let dc = (c2 - c1) / (cm * 0.04500000178813934 + 1.0);
    let dh = (hue(b[1], b[2]) - hue(a[1], a[2])) / (cm * 0.014999999664723873 + 1.0);
    (dl * dl + dc * dc + dh * dh).sqrt()
}
/// cmp is mutable because Lab comparisons carry offsets across palette entries.
pub fn hit(
    cmp: &mut [f32; 3],
    mut key: [f32; 3],
    space: i32,
    per_component: bool,
    t: [f32; 3],
    epsilon: f32,
) -> bool {
    if space == 3 || (space == 4 && per_component) {
        mutate(cmp);
        mutate(&mut key);
    }
    match space {
        5 | 6 => {
            let un = |u: f32| {
                if space == 5 {
                    (u as f64 * 1.146788990825688 + 0.5) as f32
                } else {
                    u
                }
            };
            !((cmp[0] - key[0]).abs() > t[0] + epsilon)
                && !((un(cmp[1]) - un(key[1])).abs() > t[1] + epsilon)
                && t[2] + epsilon >= 0.0
        }
        3 if per_component => {
            let s = [151.30099487304688, 264.36700439453125, 295.572998046875];
            let e = [2709.929931640625, 578.7139892578125, 414.6759948730469];
            (0..3).all(|j| !((cmp[j] - key[j]).abs() > t[j] * s[j] + epsilon * e[j]))
        }
        3 => distance(key, *cmp) <= epsilon * 424.4352722167969 + t[0] * 424.4352722167969,
        4 if per_component => {
            let s = [151.30099487304688, 264.36700439453125, 295.572998046875];
            (0..3).all(|j| !((cmp[j] - key[j]).abs() > (epsilon + t[j]) * s[j]))
        }
        4 => lab94(key, *cmp) <= ((epsilon + t[0]) as f64 * 352.978) as f32,
        2 if per_component => {
            let mut sh = cmp[0];
            if sh < key[0] {
                sh += 1.0
            }
            !(sh - key[0] > epsilon + t[0])
                && !((cmp[1] - key[1]).abs() > epsilon + t[1])
                && !((cmp[2] - key[2]).abs() > epsilon + t[2])
        }
        _ if per_component => (0..3).all(|j| !((cmp[j] - key[j]).abs() > epsilon + t[j])),
        2 => distance(*cmp, key) <= 3.0f32.sqrt() * (epsilon + t[0]),
        _ => distance(key, *cmp) <= 3.0f32.sqrt() * (epsilon + t[0]),
    }
}

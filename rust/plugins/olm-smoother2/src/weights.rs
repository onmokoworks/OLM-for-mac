//! Coverage rasterizers 13700/13bc0 and the 12850 endpoint switch.
//! Every multiply and add remains separate, including the PF16/PF32 lane.
use olm_core::{Error, Result};

fn floor_int(x: f32) -> Result<i32> {
    if !x.is_finite() || x as f64 >= 2147483648.0 || (x as f64) < -2147483648.0 {
        return Err(Error::Geometry);
    }
    let t = x as i32;
    if x < 0.0 {
        let ax = f32::from_bits(x.to_bits() ^ 0x80000000);
        // Positive magnitude may be 2^31 only at the exact INT_MIN endpoint.
        let ai = ax as i64;
        Ok(t - ((ai as f32) < ax) as i32)
    } else {
        Ok(t)
    }
}

pub fn line(p2: [f32; 2], p3: [f32; 2], scan_y: i32) -> Result<[f32; 2]> {
    let y0 = p2[1];
    let dy = p3[1] - y0;
    let x0 = p2[0];
    let dx = p3[0] - x0;
    if dy == 0.0 || dx == 0.0 {
        return Ok([0.0; 2]);
    }
    let lo = scan_y as f32 + 1.0;
    let hi = lo + 1.0;
    let f10 = ((lo - y0) * dx) / dy + x0;
    let y_x_lo = ((lo - x0) * dy) / dx + y0;
    let f13 = ((hi - y0) * dx) / dy + x0;
    let y_x_hi = ((hi - x0) * dy) / dx + y0;
    let f9 = (((lo - 1.0) - y0) * dx) / dy + x0;
    let it = floor_int(y_x_lo - lo)?;
    let c4 = if it < -1 {
        3
    } else if it == -1 {
        2
    } else if it == 0 {
        1
    } else {
        0
    };
    let it2 = floor_int(y_x_hi - lo)?;
    let c5 = if it2 <= -2 {
        3
    } else if it2 == -1 {
        2
    } else if it2 == 0 {
        1
    } else {
        0
    };
    let frac_l = y_x_lo - floor_int(y_x_lo)? as f32;
    let frac_h = y_x_hi - floor_int(y_x_hi)? as f32;
    let (mut a, mut b) = match (c4, c5) {
        (3, 2) => {
            let product = (hi - f9) * frac_h;
            (1.0 - product * 0.5, 0.0)
        }
        (3, 1) => ((f9 + f10) * 0.5 - lo, (hi - f10) * frac_h * 0.5),
        (3, 0) => ((f9 + f10) * 0.5 - lo, hi - (f10 + f13) * 0.5),
        (3, _) => (1.0, 0.0),
        (2, 2) => (1.0 - (frac_h + frac_l) * 0.5, 0.0),
        (2, 1) => ((f10 - lo) * (1.0 - frac_l) * 0.5, (hi - f10) * frac_h * 0.5),
        (2, 0) => ((f10 - lo) * (1.0 - frac_l) * 0.5, hi - (f10 + f13) * 0.5),
        (2, _) => {
            let product = (f9 - lo) * frac_l;
            (1.0 - product * 0.5, 0.0)
        }
        (1, 2) => ((hi - f10) * (1.0 - frac_h) * 0.5, (f10 - lo) * frac_l * 0.5),
        (1, 1) => (0.0, (frac_h + frac_l) * 0.5),
        (1, 0) => {
            let product = (f13 - lo) * (1.0 - frac_l);
            (0.0, 1.0 - product * 0.5)
        }
        (1, _) => (hi - (f9 + f10) * 0.5, (f10 - lo) * frac_l * 0.5),
        (0, 2) => ((hi - f13) * (1.0 - frac_h) * 0.5, (f10 + f13) * 0.5 - lo),
        (0, 1) => {
            let product = (lo - f13) * (1.0 - frac_h);
            (0.0, 1.0 - product * 0.5)
        }
        (0, 0) => (0.0, 1.0),
        _ => (hi - (f9 + f10) * 0.5, (f10 + f13) * 0.5 - lo),
    };
    if lo < x0 {
        a = 0.0;
    }
    if p3[0] < hi {
        b = 0.0;
    }
    Ok([a, b])
}

pub fn trapezoid(
    a0: [f32; 2],
    a1: [f32; 2],
    b0: [f32; 2],
    b1: [f32; 2],
    scan_y: i32,
) -> Result<[f32; 2]> {
    let [ax, ay] = a0;
    let [bx, by] = b0;
    let adx = a1[0] - ax;
    let ady = a1[1] - ay;
    let bdx = b1[0] - bx;
    let bdy = b1[1] - by;
    let lo = scan_y as f32 + 1.0;
    let hi = lo + 1.0;
    let a_term = (ax / adx) * ady - ay;
    let b_term = (bx / bdx) * bdy - by;
    let cross_y = (a_term - b_term) / (ady / adx - bdy / bdx);
    let y_lo = if cross_y <= lo {
        ((lo - bx) / bdx) * bdy + by
    } else {
        ((lo - ax) / adx) * ady + ay
    };
    let y_hi = if cross_y <= hi {
        ((hi - bx) / bdx) * bdy + by
    } else {
        ((hi - ax) / adx) * ady + ay
    };
    let mut p2 = [lo, y_lo];
    let mut p3 = [hi, y_hi];
    if ax > lo {
        p2 = [ax, ay];
    } else if hi > b1[0] {
        p3 = b1;
    }
    line(p2, p3, scan_y)
}

/// Same key masking as win_weight_pair. Intended caller spans are >=4.
pub fn pair(span_total: i32, offset: i32, key: i32) -> Result<[f32; 2]> {
    let f = span_total as f32;
    let mut l = [0.0; 8];
    let mut trap = false;
    match key & 15 {
        0 => {
            l[6] = f + 0.5;
            l[7] = f + 0.0;
            l[5] = 1.0;
            l[4] = 1.5;
        }
        1 => {
            l[6] = f + 1.0;
            l[5] = 1.0;
            l[4] = 1.5;
            l[7] = f + 0.0;
        }
        2 => {
            l[7] = f + 0.5;
            l[0] = 1.5;
            l[6] = f + 1.0;
            l[4] = 1.0;
            l[5] = 0.0;
            l[1] = 1.0;
            l[3] = l[6];
            l[2] = f + 2.0;
            trap = true;
        }
        3 => {
            l[7] = f + 1.0;
            l[0] = 1.5;
            l[6] = f + 1.0;
            l[4] = 1.0;
            l[5] = 0.0;
            l[1] = 1.0;
            l[3] = l[6];
            l[2] = f + 2.0;
            trap = true;
        }
        4 => {
            l[6] = f + 0.5;
            l[7] = f + 0.0;
            l[5] = 1.0;
            l[4] = 1.0;
        }
        5 => {
            l[6] = f + 1.0;
            l[7] = f + 0.0;
            l[5] = 1.0;
            l[4] = 1.0;
        }
        6 => {
            l[0] = 1.0;
            l[7] = f + 0.5;
            l[6] = f + 1.0;
            l[4] = 1.0;
            l[5] = 0.0;
            l[1] = 1.0;
            l[3] = l[6];
            l[2] = f + 2.0;
            trap = true;
        }
        7 => {
            l[0] = 1.0;
            l[7] = f + 1.0;
            l[6] = f + 1.0;
            l[4] = 1.0;
            l[5] = 0.0;
            l[1] = 1.0;
            l[3] = l[6];
            l[2] = f + 2.0;
            trap = true;
        }
        8 => {
            l[2] = 0.0;
            l[3] = 0.0;
            l[6] = 1.0;
            l[7] = 0.5;
            l[5] = f + 1.0;
            l[4] = f + 1.0;
            l[1] = f + 0.0;
            l[0] = f + 0.5;
            return trapezoid(
                [l[6], l[7]],
                [l[4], l[5]],
                [l[2], l[3]],
                [l[0], l[1]],
                offset,
            );
        }
        9 => {
            l[1] = 0.5;
            l[0] = 1.0;
            l[6] = f + 1.0;
            l[3] = l[6];
            l[2] = l[6];
            l[7] = f + 0.0;
            l[4] = 0.0;
            l[5] = 0.0;
            trap = true;
        }
        10 => {
            l[5] = 0.5;
            l[6] = f + 1.0;
            l[7] = f + 0.5;
            l[4] = 1.0;
        }
        11 => {
            l[7] = f + 1.0;
            l[5] = 0.5;
            l[6] = l[7];
            l[4] = 1.0;
        }
        12 => {
            l[0] = 1.0;
            l[1] = 0.0;
            l[6] = f + 0.5;
            l[3] = f + 1.0;
            l[2] = f + 1.0;
            l[7] = f + 0.0;
            l[4] = 0.0;
            l[5] = 0.0;
            trap = true;
        }
        13 => {
            l[0] = 1.0;
            l[1] = 0.0;
            l[6] = f + 1.0;
            l[3] = l[6];
            l[2] = l[6];
            l[7] = f + 0.0;
            l[4] = 0.0;
            l[5] = 0.0;
            trap = true;
        }
        14 => {
            l[5] = 0.0;
            l[6] = f + 1.0;
            l[7] = f + 0.5;
            l[4] = 1.0;
        }
        _ => {
            l[7] = f + 1.0;
            l[5] = 0.0;
            l[6] = l[7];
            l[4] = 1.0;
        }
    }
    if trap {
        trapezoid(
            [l[0], l[1]],
            [l[2], l[3]],
            [l[4], l[5]],
            [l[6], l[7]],
            offset,
        )
    } else {
        line([l[4], l[5]], [l[6], l[7]], offset)
    }
}

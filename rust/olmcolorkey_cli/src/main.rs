use image::{ImageBuffer, Rgba};
use serde_json::Value;
use std::collections::BTreeMap;
use std::env;
use std::error::Error;
use std::f32::consts::PI;
use std::fs;
use std::path::PathBuf;

#[derive(Clone, Copy, Debug, Default)]
struct Rgb {
    r: f32,
    g: f32,
    b: f32,
}

#[derive(Clone, Debug)]
struct KeyColor {
    rgb: Rgb,
    comp: [f32; 3],
    use_replace: bool,
    replace_rgb: Rgb,
}

#[derive(Clone, Debug)]
struct Params {
    color_keep: bool,
    threshold: f32,
    premultiplied: bool,
    color_space: i32,
    per_component: bool,
    enable_replace: bool,
    edge_thin_amount: f32,
    edge_thin_distance_type: i32,
    edge_blur_amount: f32,
    edge_blur_distance_type: i32,
    edge_blur_direction: i32,
    colors: Vec<KeyColor>,
}

fn number(value: Option<&Value>, fallback: f32) -> f32 {
    match value {
        Some(Value::Number(n)) => n.as_f64().unwrap_or(fallback as f64) as f32,
        Some(Value::Bool(b)) => {
            if *b {
                1.0
            } else {
                0.0
            }
        }
        Some(Value::String(s)) => s.parse().unwrap_or(fallback),
        _ => fallback,
    }
}

fn rgb(value: Option<&Value>) -> Rgb {
    let Some(Value::Array(items)) = value else {
        return Rgb::default();
    };
    let mut c = Rgb {
        r: number(items.get(0), 0.0),
        g: number(items.get(1), 0.0),
        b: number(items.get(2), 0.0),
    };
    if c.r.max(c.g).max(c.b) > 1.0 {
        c.r /= 255.0;
        c.g /= 255.0;
        c.b /= 255.0;
    }
    c.r = c.r.clamp(0.0, 1.0);
    c.g = c.g.clamp(0.0, 1.0);
    c.b = c.b.clamp(0.0, 1.0);
    c
}

fn effect_param_items(root: &Value) -> Vec<(String, Value)> {
    let scope = root.get("params").unwrap_or(root);
    if let Some(effects) = scope.get("effects").and_then(Value::as_array) {
        for effect in effects {
            let name = effect.get("name").and_then(Value::as_str).unwrap_or("");
            let match_name = effect.get("match_name").and_then(Value::as_str).unwrap_or("");
            if name == "OLM Color Key" || match_name == "OLM Color Key" {
                if let Some(params) = effect.get("params").and_then(Value::as_array) {
                    return params
                        .iter()
                        .filter_map(|p| {
                            let name = p.get("name")?.as_str()?.to_string();
                            Some((name, p.get("value").cloned().unwrap_or(Value::Null)))
                        })
                        .collect();
                }
            }
        }
    }
    if let Some(obj) = scope.as_object() {
        return obj.iter().map(|(k, v)| (k.clone(), v.clone())).collect();
    }
    Vec::new()
}

fn read_params(path: &str) -> Result<Params, Box<dyn Error>> {
    let root: Value = serde_json::from_str(&fs::read_to_string(path)?)?;
    let items = effect_param_items(&root);
    let mut map = BTreeMap::<String, Value>::new();
    for (name, value) in &items {
        map.insert(name.clone(), value.clone());
    }
    let get = |name: &str| map.get(name);

    let mut cfg = Params {
        color_keep: number(get("Color Keep"), 0.0) != 0.0,
        threshold: number(get("Threshold"), 0.0),
        premultiplied: number(get("Premultiplied Color"), 0.0) != 0.0,
        color_space: number(get("Color Space"), 1.0).round() as i32,
        per_component: number(get("Per Component"), 0.0) != 0.0,
        enable_replace: number(get("Enable Replace"), 0.0) != 0.0,
        edge_thin_amount: 0.0,
        edge_thin_distance_type: 1,
        edge_blur_amount: 0.0,
        edge_blur_distance_type: 1,
        edge_blur_direction: 2,
        colors: Vec::new(),
    };

    for (i, (name, _)) in items.iter().enumerate() {
        if name == "Edge Thin" {
            cfg.edge_thin_amount = items.get(i + 1).map(|(_, v)| number(Some(v), 0.0)).unwrap_or(0.0);
            cfg.edge_thin_distance_type = items.get(i + 2).map(|(_, v)| number(Some(v), 1.0).round() as i32).unwrap_or(1);
        } else if name == "Edge Blur" {
            cfg.edge_blur_amount = items.get(i + 1).map(|(_, v)| number(Some(v), 0.0)).unwrap_or(0.0);
            cfg.edge_blur_distance_type = items.get(i + 2).map(|(_, v)| number(Some(v), 1.0).round() as i32).unwrap_or(1);
            cfg.edge_blur_direction = items.get(i + 3).map(|(_, v)| number(Some(v), 2.0).round() as i32).unwrap_or(2);
        }
    }

    let ncolors = (number(get("Number of Colors"), 1.0).round() as usize).clamp(1, 25);
    for i in 1..=ncolors {
        let suffix = i.to_string();
        if number(get(&format!("Use Color {suffix}")), 1.0) == 0.0 {
            continue;
        }
        cfg.colors.push(KeyColor {
            rgb: rgb(get(&format!("Color {suffix}"))),
            comp: [
                number(get(&format!("Threshold(R,H,L,Y,Y) {suffix}")), 0.0),
                number(get(&format!("Threshold(G,S,a,U,Cr) {suffix}")), 0.0),
                number(get(&format!("Threshold(B,V,b,V,Cb) {suffix}")), 0.0),
            ],
            use_replace: number(get(&format!("Use Replace Color {suffix}")), 0.0) != 0.0,
            replace_rgb: rgb(get(&format!("Replace Color {suffix}"))),
        });
    }
    if cfg.colors.is_empty() {
        cfg.colors.push(KeyColor {
            rgb: rgb(get("Color 1")),
            comp: [0.0, 0.0, 0.0],
            use_replace: number(get("Use Replace Color 1"), 0.0) != 0.0,
            replace_rgb: rgb(get("Replace Color 1")),
        });
    }
    Ok(cfg)
}

fn l1_distance(mask: &[u8], w: usize, h: usize) -> Vec<f32> {
    let mut d = vec![1.0e9_f32; w * h];
    for i in 0..w * h {
        if mask[i] != 0 {
            d[i] = 0.0;
        }
    }
    for x in 1..w {
        for y in 0..h {
            let i = y * w + x;
            d[i] = d[i].min(d[i - 1] + 1.0);
        }
    }
    for x in (0..w - 1).rev() {
        for y in 0..h {
            let i = y * w + x;
            d[i] = d[i].min(d[i + 1] + 1.0);
        }
    }
    for y in 1..h {
        for x in 0..w {
            let i = y * w + x;
            d[i] = d[i].min(d[i - w] + 1.0);
        }
    }
    for y in (0..h - 1).rev() {
        for x in 0..w {
            let i = y * w + x;
            d[i] = d[i].min(d[i + w] + 1.0);
        }
    }
    d
}

fn chessboard_distance(mask: &[u8], w: usize, h: usize) -> Vec<f32> {
    let mut d = vec![1.0e9_f32; w * h];
    for i in 0..w * h {
        if mask[i] != 0 {
            d[i] = 0.0;
        }
    }
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            if x > 0 {
                d[i] = d[i].min(d[i - 1] + 1.0);
            }
            if y > 0 {
                d[i] = d[i].min(d[i - w] + 1.0);
            }
            if x > 0 && y > 0 {
                d[i] = d[i].min(d[i - w - 1] + 1.0);
            }
            if x + 1 < w && y > 0 {
                d[i] = d[i].min(d[i - w + 1] + 1.0);
            }
        }
    }
    for y in (0..h).rev() {
        for x in (0..w).rev() {
            let i = y * w + x;
            if x + 1 < w {
                d[i] = d[i].min(d[i + 1] + 1.0);
            }
            if y + 1 < h {
                d[i] = d[i].min(d[i + w] + 1.0);
            }
            if x + 1 < w && y + 1 < h {
                d[i] = d[i].min(d[i + w + 1] + 1.0);
            }
            if x > 0 && y + 1 < h {
                d[i] = d[i].min(d[i + w - 1] + 1.0);
            }
        }
    }
    d
}

fn edt_1d(f: &[f32], n: usize) -> Vec<f32> {
    let inf = 1.0e9_f32;
    let sites = (0..n).filter(|&i| f[i] < inf * 0.5).collect::<Vec<_>>();
    let mut d = vec![inf; n];
    if sites.is_empty() {
        return d;
    }

    let mut v = vec![0_usize; sites.len()];
    let mut z = vec![0.0_f32; sites.len() + 1];
    let mut k = 0_usize;
    v[0] = sites[0];
    z[0] = -1.0e20;
    z[1] = 1.0e20;
    for &q in sites.iter().skip(1) {
        let mut s;
        loop {
            let vk = v[k];
            s = ((f[q] + (q as f32).powi(2)) - (f[vk] + (vk as f32).powi(2))) / (2.0 * (q as f32 - vk as f32));
            if s > z[k] {
                break;
            }
            if k == 0 {
                break;
            }
            k -= 1;
        }
        if s <= z[k] {
            k = 0;
        } else {
            k += 1;
        }
        v[k] = q;
        z[k] = s;
        z[k + 1] = 1.0e20;
    }
    k = 0;
    for q in 0..n {
        while z[k + 1] < q as f32 {
            k += 1;
        }
        let vk = v[k];
        d[q] = (q as f32 - vk as f32).powi(2) + f[vk];
    }
    d
}

fn euclidean_distance(mask: &[u8], w: usize, h: usize) -> Vec<f32> {
    let inf = 1.0e9_f32;
    let mut tmp = vec![0.0_f32; w * h];
    let mut f = vec![0.0_f32; w.max(h)];
    for x in 0..w {
        for y in 0..h {
            f[y] = if mask[y * w + x] != 0 { 0.0 } else { inf };
        }
        let col = edt_1d(&f, h);
        for y in 0..h {
            tmp[y * w + x] = col[y];
        }
    }
    let mut out = vec![0.0_f32; w * h];
    for y in 0..h {
        for x in 0..w {
            f[x] = tmp[y * w + x];
        }
        let row = edt_1d(&f, w);
        for x in 0..w {
            out[y * w + x] = row[x].sqrt();
        }
    }
    out
}

fn matte_distance(mask: &[u8], w: usize, h: usize, distance_type: i32) -> Vec<f32> {
    match distance_type {
        1 => chessboard_distance(mask, w, h),
        3 => euclidean_distance(mask, w, h),
        _ => l1_distance(mask, w, h),
    }
}

fn edge_blur_distance(mask: &[u8], w: usize, h: usize, distance_type: i32) -> Vec<f32> {
    matte_distance(mask, w, h, distance_type)
}

fn boundary8(mask: &[u8], w: usize, h: usize) -> Vec<u8> {
    let mut out = vec![0_u8; w * h];
    for y in 0..h {
        for x in 0..w {
            let i = y * w + x;
            if mask[i] == 0 {
                continue;
            }
            let mut all_inside = true;
            for dy in -1_i32..=1 {
                for dx in -1_i32..=1 {
                    if dx == 0 && dy == 0 {
                        continue;
                    }
                    let nx = (x as i32 + dx).clamp(0, w as i32 - 1) as usize;
                    let ny = (y as i32 + dy).clamp(0, h as i32 - 1) as usize;
                    all_inside &= mask[ny * w + nx] != 0;
                }
            }
            out[i] = if all_inside { 0 } else { 1 };
        }
    }
    out
}

fn lab_f(t: f32) -> f32 {
    if t <= 0.008856000378727913 {
        t * 7.7870001792907715 + 0.13793103396892548
    } else {
        t.powf(0.3333300054073334)
    }
}

fn rgb_to_plugin_lab76(c: [f32; 3]) -> [f32; 3] {
    let r = c[0];
    let g = c[1];
    let b = c[2];
    let x = g * 2.1455016136169434 + r * 0.6380193829536438 + b * 0.2165091633796692;
    let fx = lab_f(x);
    let l = if x <= 0.008856000378727913 {
        g * 1938.031494140625 + r * 576.3229370117188 + b * 195.57272338867188
    } else {
        x.powf(0.3333300054073334) * 116.0 - 16.0
    };
    let a_source = r * 1.2373713254928589 + g * 1.0727508068084717 + b * 0.5412744283676147;
    let b_source = g * 0.35758259892463684 + r * 0.05800257995724678 + b * 2.8507096767425537;
    [l, (lab_f(a_source) - fx) * 500.0, (fx - lab_f(b_source)) * 200.0]
}

fn rgb_to_plugin_hsv(c: [f32; 3]) -> [f32; 3] {
    let r = c[0];
    let g = c[1];
    let b = c[2];
    let mx = r.max(g).max(b);
    let mn = r.min(g).min(b);
    let delta = mx - mn;
    let mut h = if delta == 0.0 {
        0.0
    } else if mx == r {
        (g - b) * 60.0 / delta
    } else if mx == g {
        (b - r) * 60.0 / delta + 120.0
    } else {
        (r - g) * 60.0 / delta + 240.0
    };
    h %= 360.0;
    if h < 0.0 {
        h += 360.0;
    }
    [h / 360.0, if mx == 0.0 { 0.0 } else { delta / mx }, mx]
}

fn rgb_to_plugin_yuv(c: [f32; 3]) -> [f32; 3] {
    let r = c[0];
    let g = c[1];
    let b = c[2];
    [
        g * 0.5870000123977661 + r * 0.29899999499320984 + b * 0.11400000005960464,
        b * 0.4359999895095825 - (g * 0.2888599932193756 + r * 0.14712999761104584),
        r * 0.6150000095367432 - g * 0.514989972114563 - b * 0.10001000016927719,
    ]
}

fn rgb_to_plugin_ycrcb(c: [f32; 3]) -> [f32; 3] {
    let r = c[0];
    let g = c[1];
    let b = c[2];
    [
        r * 0.298909991979599 + g * 0.5866100192070007 + b * 0.11448000371456146,
        b * 0.5 - (r * 0.16874000430107117 + g * 0.33125999569892883),
        r * 0.5 - g * 0.4186899960041046 - b * 0.08130999654531479,
    ]
}

fn lab94_distance(a: [f32; 3], b: [f32; 3]) -> f32 {
    let c1 = (a[1] * a[1] + a[2] * a[2]).sqrt();
    let c2 = (b[1] * b[1] + b[2] * b[2]).sqrt();
    let cmean = (c2 * c1).sqrt();
    let hue = |aa: f32, bb: f32| {
        let mut h = bb.atan2(aa) * 57.2957763671875 + 180.0;
        if h != 0.0 {
            if h < 0.0 {
                h += 540.0;
            }
            h %= 360.0;
        }
        h
    };
    let h1 = hue(a[1], a[2]);
    let h2 = hue(b[1], b[2]);
    let dl = b[0] - a[0];
    let dc = (c2 - c1) / (cmean * 0.04500000178813934 + 1.0);
    let dh = (h2 - h1) / (cmean * 0.014999999664723873 + 1.0);
    (dl * dl + dc * dc + dh * dh).sqrt()
}

fn edge_blur_weight(inside: bool, dist: f32, amount: f32, direction: i32) -> f32 {
    if amount <= 0.0 {
        return if inside { 1.0 } else { 0.0 };
    }
    match direction {
        1 => {
            if !inside {
                0.0
            } else if dist >= amount {
                1.0
            } else {
                ((dist * (PI / amount) - PI * 0.5).sin() + 1.0) * 0.5
            }
        }
        2 => {
            if inside {
                1.0
            } else if dist >= amount {
                0.0
            } else {
                ((PI * 0.5 - dist * (PI / amount)).sin() + 1.0) * 0.5
            }
        }
        3 => {
            if !inside {
                0.0
            } else if dist >= amount {
                1.0
            } else {
                ((dist * (PI / amount) - PI * 0.5).sin() + 1.0) * 0.5
            }
        }
        _ => {
            if inside {
                1.0
            } else {
                0.0
            }
        }
    }
}

fn render(input: &ImageBuffer<Rgba<u8>, Vec<u8>>, cfg: &Params) -> Result<ImageBuffer<Rgba<u8>, Vec<u8>>, Box<dyn Error>> {
    let (w_u32, h_u32) = input.dimensions();
    let w = w_u32 as usize;
    let h = h_u32 as usize;
    let n = w * h;
    let raw = input.as_raw();
    let mut out = raw.clone();
    let mut matched = vec![0_u8; n];
    let mut matched_idx = vec![-1_i32; n];
    let eps8 = 0.5_f32 / 255.0;

    for i in 0..n {
        let p = i * 4;
        let alpha = raw[p + 3] as f32 / 255.0;
        let rgb = [
            raw[p] as f32 / 255.0,
            raw[p + 1] as f32 / 255.0,
            raw[p + 2] as f32 / 255.0,
        ];
        let mut cmp = if cfg.premultiplied {
            [rgb[0] * alpha, rgb[1] * alpha, rgb[2] * alpha]
        } else {
            rgb
        };
        if cfg.color_space == 3 || cfg.color_space == 4 {
            cmp = rgb_to_plugin_lab76(cmp);
        } else if cfg.color_space == 2 {
            cmp = rgb_to_plugin_hsv(cmp);
        } else if cfg.color_space == 5 {
            cmp = rgb_to_plugin_yuv(cmp);
        } else if cfg.color_space == 6 {
            cmp = rgb_to_plugin_ycrcb(cmp);
        }
        let mut hit_any = false;
        let mut hit_idx = -1_i32;
        for (ci, kc) in cfg.colors.iter().enumerate() {
            let mut key = [kc.rgb.r, kc.rgb.g, kc.rgb.b];
            let mut comp_scale = [1.0_f32, 1.0, 1.0];
            if cfg.color_space == 3 || cfg.color_space == 4 {
                key = rgb_to_plugin_lab76(key);
                comp_scale = [151.30099487304688, 264.36700439453125, 295.572998046875];
            } else if cfg.color_space == 2 {
                key = rgb_to_plugin_hsv(key);
            } else if cfg.color_space == 5 {
                key = rgb_to_plugin_yuv(key);
            } else if cfg.color_space == 6 {
                key = rgb_to_plugin_ycrcb(key);
            }
            let hit = if cfg.color_space == 5 {
                let t0 = if cfg.per_component { kc.comp[0] } else { cfg.threshold };
                let t1 = if cfg.per_component { kc.comp[1] } else { cfg.threshold };
                let un = |u: f32| (u as f64 * 1.146788990825688 + 0.5) as f32;
                (cmp[0] - key[0]).abs() <= t0 + eps8
                    && (un(cmp[1]) - un(key[1])).abs() <= t1 + eps8
            } else if cfg.color_space == 6 {
                let t0 = if cfg.per_component { kc.comp[0] } else { cfg.threshold };
                let t1 = if cfg.per_component { kc.comp[1] } else { cfg.threshold };
                (cmp[0] - key[0]).abs() <= t0 + eps8
                    && (cmp[1] - key[1]).abs() <= t1 + eps8
            } else if cfg.color_space == 4 {
                if cfg.per_component {
                    (cmp[0] - key[0]).abs() <= (eps8 + kc.comp[0]) * comp_scale[0]
                        && (cmp[1] - key[1]).abs() <= (eps8 + kc.comp[1]) * comp_scale[1]
                        && (cmp[2] - key[2]).abs() <= (eps8 + kc.comp[2]) * comp_scale[2]
                } else {
                    lab94_distance(key, cmp) <= ((eps8 + cfg.threshold) as f64 * 352.978) as f32
                }
            } else if cfg.color_space == 2 {
                if cfg.per_component {
                    let mut sh = cmp[0];
                    if sh < key[0] {
                        sh += 1.0;
                    }
                    (sh - key[0]) <= eps8 + kc.comp[0]
                        && (cmp[1] - key[1]).abs() <= eps8 + kc.comp[1]
                        && (cmp[2] - key[2]).abs() <= eps8 + kc.comp[2]
                } else {
                    let d0 = cmp[0] - key[0];
                    let d1 = cmp[1] - key[1];
                    let d2 = cmp[2] - key[2];
                    (d0 * d0 + d1 * d1 + d2 * d2).sqrt() <= 3.0_f32.sqrt() * (eps8 + cfg.threshold)
                }
            } else if cfg.per_component {
                (cmp[0] - key[0]).abs() <= eps8 + kc.comp[0] * comp_scale[0]
                    && (cmp[1] - key[1]).abs() <= eps8 + kc.comp[1] * comp_scale[1]
                    && (cmp[2] - key[2]).abs() <= eps8 + kc.comp[2] * comp_scale[2]
            } else {
                ((cmp[0] - key[0]).abs() / comp_scale[0]
                    + (cmp[1] - key[1]).abs() / comp_scale[1]
                    + (cmp[2] - key[2]).abs() / comp_scale[2])
                    / 3.0
                    <= cfg.threshold
            };
            if hit && hit_idx == -1 {
                hit_idx = ci as i32;
            }
            hit_any |= hit;
        }
        matched[i] = if hit_any { 1 } else { 0 };
        matched_idx[i] = hit_idx;
    }

    if cfg.edge_thin_amount < 0.0 {
        let nonmatch = matched.iter().map(|&m| if m == 0 { 1 } else { 0 }).collect::<Vec<_>>();
        let dist = matte_distance(&nonmatch, w, h, cfg.edge_thin_distance_type);
        let extra = if cfg.edge_thin_distance_type == 0 || cfg.edge_thin_distance_type == 2 { 1.0 } else { 0.0 };
        let limit = cfg.edge_thin_amount.abs() + extra;
        for i in 0..n {
            matched[i] = if matched[i] != 0 && dist[i] > limit { 1 } else { 0 };
        }
    } else if cfg.edge_thin_amount > 0.0 {
        let dist = matte_distance(&matched, w, h, cfg.edge_thin_distance_type);
        for i in 0..n {
            matched[i] = if matched[i] != 0 || dist[i] <= cfg.edge_thin_amount { 1 } else { 0 };
        }
    }

    let mut keep_mask = vec![0_u8; n];
    for i in 0..n {
        let keep = if cfg.color_keep { matched[i] != 0 } else { matched[i] == 0 };
        keep_mask[i] = if keep { 1 } else { 0 };
        if !keep {
            let p = i * 4;
            out[p] = 0;
            out[p + 1] = 0;
            out[p + 2] = 0;
            out[p + 3] = 0;
        } else if cfg.color_keep && cfg.enable_replace && matched_idx[i] >= 0 {
            let key = &cfg.colors[matched_idx[i] as usize];
            if key.use_replace {
                let p = i * 4;
                out[p] = ((255.0 * key.replace_rgb.r) as i32).clamp(0, 255) as u8;
                out[p + 1] = ((255.0 * key.replace_rgb.g) as i32).clamp(0, 255) as u8;
                out[p + 2] = ((255.0 * key.replace_rgb.b) as i32).clamp(0, 255) as u8;
            }
        }
    }

    if cfg.edge_blur_amount != 0.0 {
        let boundary = boundary8(&keep_mask, w, h);
        let dist = edge_blur_distance(&boundary, w, h, cfg.edge_blur_distance_type);
        for i in 0..n {
            let keep = keep_mask[i] != 0;
            let weight = edge_blur_weight(keep, dist[i], cfg.edge_blur_amount, cfg.edge_blur_direction);
            let p = i * 4;
            let source = if !keep && weight != 0.0 { raw } else { &out };
            let r = source[p];
            let g = source[p + 1];
            let b = source[p + 2];
            let a = source[p + 3];
            out[p] = ((r as f32 * weight) as i32).clamp(0, 255) as u8;
            out[p + 1] = ((g as f32 * weight) as i32).clamp(0, 255) as u8;
            out[p + 2] = ((b as f32 * weight) as i32).clamp(0, 255) as u8;
            out[p + 3] = ((a as f32 * weight) as i32).clamp(0, 255) as u8;
        }
    }

    ImageBuffer::from_raw(w_u32, h_u32, out).ok_or_else(|| "failed to build output image".into())
}

fn parse_args() -> Result<(PathBuf, String, PathBuf), Box<dyn Error>> {
    let mut input = None;
    let mut params = None;
    let mut output = None;
    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--input" => input = args.next().map(PathBuf::from),
            "--params" => params = args.next(),
            "--output" => output = args.next().map(PathBuf::from),
            _ => return Err(format!("unknown argument: {arg}").into()),
        }
    }
    Ok((
        input.ok_or("missing --input")?,
        params.ok_or("missing --params")?,
        output.ok_or("missing --output")?,
    ))
}

fn main() -> Result<(), Box<dyn Error>> {
    let (input_path, params_path, output_path) = parse_args()?;
    let cfg = read_params(&params_path)?;
    let image = image::open(&input_path)?.to_rgba8();
    let output = render(&image, &cfg)?;
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent)?;
    }
    output.save(&output_path)?;
    println!("wrote: {}", output_path.display());
    Ok(())
}

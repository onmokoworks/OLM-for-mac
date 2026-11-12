//! Faithful local-coordinate state machine and draw commands from RampEditor.h.
pub use crate::presets::preset;
use crate::ramp::Ramp;
#[derive(Clone, Copy)]
pub struct Rect(pub i32, pub i32, pub i32, pub i32);
impl Rect {
    fn contains(self, x: i32, y: i32) -> bool {
        self.0 <= x && x <= self.2 && self.1 <= y && y <= self.3
    }
}
const STRIP: Rect = Rect(10, 5, 202, 55);
const BUTTONS: [Rect; 4] = [
    Rect(225, 35, 295, 55),
    Rect(225, 60, 295, 80),
    Rect(5, 80, 135, 100),
    Rect(140, 80, 205, 100),
];
const HEADER: Rect = Rect(220, 5, 300, 25);
fn row(r: i32) -> Rect {
    Rect(228, 30 + 23 * r, 292, 48 + 23 * r)
}
fn preset_hit(x: i32, y: i32) -> i32 {
    (0..34).find(|&r| row(r).contains(x, y)).unwrap_or(-1)
}
#[derive(Clone, Copy, Debug)]
pub struct State {
    pub selected: i32,
    pub armed: i32,
    pub hover_x: i32,
    pub hover_y: i32,
    pub anchor_y: i32,
    pub menu_open: bool,
    pub preset_row: i32,
    pub scroll: i32,
}
impl Default for State {
    fn default() -> Self {
        Self {
            selected: -1,
            armed: -1,
            hover_x: 0,
            hover_y: 0,
            anchor_y: 0,
            menu_open: false,
            preset_row: -1,
            scroll: 0,
        }
    }
}
#[derive(Clone, Copy, PartialEq)]
pub enum Event {
    Hover,
    Single,
    Multiple,
    Drag,
    Release,
}
#[derive(Clone, Copy, Default)]
pub struct Clipboard {
    pub available: bool,
    pub data: Ramp,
}
#[derive(Clone, Copy, Debug)]
pub struct Color {
    pub rgba: [f32; 4],
    pub role: i32,
    pub factor: f32,
}
impl Default for Color {
    fn default() -> Self {
        Self {
            rgba: [0.0; 4],
            role: 0,
            factor: 1.0,
        }
    }
}
fn color(s: [f32; 5]) -> Color {
    Color {
        rgba: [s[2], s[3], s[4], s[1]],
        ..Default::default()
    }
}
fn set_color(s: &mut [f32; 5], c: Color) {
    s[1] = c.rgba[3];
    s[2..5].copy_from_slice(&c.rgba[..3]);
}
fn marker(r: &Ramp, i: usize) -> Rect {
    let x = (10.0 + 192.0 * r.stops[i][0]) as i32;
    Rect(x - 5, 60, x + 5, 70)
}
fn hit(r: &Ramp, x: i32, y: i32) -> i32 {
    (0..r.count as usize)
        .rev()
        .find(|&i| marker(r, i).contains(x, y))
        .map(|i| i as i32)
        .unwrap_or(-1)
}
fn sort(r: &mut Ramp) {
    for i in 0..r.count as usize {
        for j in i + 1..r.count as usize {
            if r.stops[j][0] < r.stops[i][0] {
                r.stops.swap(i, j);
            }
        }
    }
}
pub fn sample(r: &Ramp, p: f32) -> Color {
    if r.count == 0 {
        return Color {
            rgba: [0.0, 0.0, 0.0, 1.0],
            ..Default::default()
        };
    }
    let mut lo: Option<usize> = None;
    let mut hi: Option<usize> = None;
    for i in 0..r.count as usize {
        let q = r.stops[i][0];
        if q - p <= 0.0 {
            if lo.is_none_or(|l| r.stops[l][0] <= q && q != r.stops[l][0]) {
                lo = Some(i);
            }
        } else if hi.is_none_or(|h| q < r.stops[h][0]) {
            hi = Some(i);
        }
    }
    let (l, h) = match (lo, hi) {
        (None, Some(h)) => return color(r.stops[h]),
        (Some(l), None) => return color(r.stops[l]),
        (Some(l), Some(h)) => (l, h),
        _ => return Color::default(),
    };
    let a = color(r.stops[l]);
    let b = color(r.stops[h]);
    let d = r.stops[h][0] - r.stops[l][0];
    let t = if d.abs() < 0.0001 {
        0.0
    } else {
        (p - r.stops[l][0]) / d
    };
    Color {
        rgba: std::array::from_fn(|c| (b.rgba[c] - a.rgba[c]) * t + a.rgba[c]),
        ..Default::default()
    }
}
fn random_word(rng: &mut u32) -> u32 {
    *rng ^= *rng << 13;
    *rng ^= *rng >> 17;
    *rng ^= *rng << 5;
    *rng
}
pub fn dispatch(
    r: &mut Ramp,
    s: &mut State,
    clip: &mut Clipboard,
    rng: &mut u32,
    e: Event,
    x: i32,
    y: i32,
) -> i32 {
    if r.count > 16 {
        return -1;
    }
    s.hover_x = x;
    s.hover_y = y;
    if matches!(e, Event::Hover | Event::Single | Event::Multiple) {
        s.anchor_y = y;
    }
    if e == Event::Hover {
        return -1;
    }
    let mut handled = false;
    if e == Event::Single {
        if STRIP.contains(x, y) {
            handled = true;
            if r.count < 16 {
                let p = (x - 10) as f32 / 192.0;
                let c = sample(r, p);
                let stop = &mut r.stops[r.count as usize];
                stop[0] = p;
                set_color(stop, c);
                r.count += 1;
                s.selected = -1;
                sort(r);
            }
        } else {
            s.selected = hit(r, x, y);
            handled = s.selected >= 0;
        }
    } else if e == Event::Multiple {
        let i = hit(r, x, y);
        if i >= 0 {
            return i;
        }
    } else if s.selected >= 0 && (s.selected as u32) < r.count {
        handled = true;
        if e == Event::Drag {
            let stop = &mut r.stops[s.selected as usize];
            stop[0] = ((x - 10) as f32 / 192.0).clamp(0.0, 1.0);
            stop[1] = if y - 55 > 20 { 0.5 } else { 1.0 };
        } else if e == Event::Release {
            if y - 55 > 20 {
                for i in s.selected as usize + 1..r.count as usize {
                    r.stops[i - 1] = r.stops[i];
                }
                r.count -= 1;
            } else {
                sort(r);
            }
            s.selected = -1;
        }
    }
    if handled {
        return -1;
    }
    if s.menu_open {
        if e == Event::Single {
            if !HEADER.contains(x, y) && Rect(220, 5, 300, 25 + 23 * 34 + 5).contains(x, y) {
                s.preset_row = preset_hit(x, y);
                return -1;
            }
            s.menu_open = false;
            if HEADER.contains(x, y) {
                return -1;
            }
        } else if e == Event::Drag {
            s.scroll = (s.scroll + (y - s.anchor_y) / 18).clamp(0, 33);
        } else if e == Event::Release && s.preset_row >= 0 {
            let row = preset_hit(x, y);
            let armed = s.preset_row;
            s.preset_row = -1;
            if row == armed {
                let index = row + s.scroll;
                if (0..34).contains(&index) {
                    *r = preset(index as usize);
                }
                s.menu_open = false;
                return -1;
            }
        }
    } else if e == Event::Single && HEADER.contains(x, y) {
        s.menu_open = true;
        return -1;
    }
    if matches!(e, Event::Single | Event::Multiple) {
        s.armed = -1;
        for (i, b) in BUTTONS.iter().enumerate() {
            if (i != 1 || clip.available) && b.contains(x, y) {
                s.armed = i as i32;
            }
        }
    } else if e == Event::Release {
        let b = s.armed;
        s.armed = -1;
        if b >= 0 && BUTTONS[b as usize].contains(x, y) {
            match b {
                0 => {
                    clip.data = *r;
                    clip.available = true;
                }
                1 => {
                    if clip.available {
                        *r = clip.data;
                    }
                }
                2 => {
                    *rng = (*rng >> 16 ^ *rng ^ 0x3d).wrapping_mul(9);
                    *rng = (*rng >> 4 ^ *rng).wrapping_mul(0x27d4eb2d);
                    *rng ^= *rng >> 15;
                    for i in 0..r.count as usize {
                        for c in 2..5 {
                            r.stops[i][c] = random_word(rng) as f32 * (1.0 / 4294967296.0);
                        }
                    }
                }
                3 => {
                    for i in 0..r.count as usize / 2 {
                        let j = r.count as usize - 1 - i;
                        let c = color(r.stops[i]);
                        let d = color(r.stops[j]);
                        set_color(&mut r.stops[i], d);
                        set_color(&mut r.stops[j], c);
                    }
                }
                _ => {}
            }
        }
    }
    -1
}
pub fn picker(r: &mut Ramp, s: &mut State, i: i32, cancel: bool, c: Color) {
    if cancel {
        s.selected = -1;
    } else if i >= 0 && (i as u32) < r.count {
        set_color(&mut r.stops[i as usize], c);
    }
}
#[derive(Clone, Copy, Debug)]
#[repr(i32)]
pub enum Kind {
    Theme,
    Antialias,
    Fill,
    Frame,
    Line,
    Text,
    Pen,
    ReleasePen,
    Ticks,
}
#[derive(Clone, Debug)]
pub struct Command {
    pub kind: Kind,
    pub rect: [f32; 4],
    pub color: Color,
    pub text: &'static str,
    pub font: f32,
}
fn cmd(k: Kind, r: [f32; 4], c: Color) -> Command {
    Command {
        kind: k,
        rect: r,
        color: c,
        text: "",
        font: 11.0,
    }
}
fn rect(out: &mut Vec<Command>, k: Kind, r: Rect, c: Color) {
    out.push(cmd(
        k,
        [
            r.0 as f32,
            r.1 as f32,
            (r.2 - r.0) as f32,
            (r.3 - r.1) as f32,
        ],
        c,
    ));
}
fn query(out: &mut Vec<Command>, r: i32) {
    out.push(cmd(
        Kind::Theme,
        [r as f32, 0.0, 0.0, 0.0],
        Color::default(),
    ));
}
fn scaled(c: Color, f: f32) -> Color {
    Color {
        rgba: [c.rgba[0] * f, c.rgba[1] * f, c.rgba[2] * f, c.rgba[3]],
        factor: c.factor * f,
        ..c
    }
}
fn text(r: [f32; 4], c: Color, t: &'static str, font: f32) -> Command {
    Command {
        kind: Kind::Text,
        rect: r,
        color: c,
        text: t,
        font,
    }
}
pub fn draw(r: &Ramp, s: &State, can_paste: bool) -> Vec<Command> {
    let theme = |role| Color {
        rgba: [0.0, 0.0, 0.0, 1.0],
        role,
        factor: 1.0,
    };
    let frame = theme(7);
    let fill = theme(8);
    let foreground = theme(2);
    let black = theme(42);
    let empty = Color::default();
    let mut o = vec![];
    for role in [7, 42, 2] {
        query(&mut o, role);
    }
    o.push(cmd(Kind::Antialias, [0.0; 4], empty));
    if r.count == 0 {
        rect(&mut o, Kind::Fill, STRIP, black);
    } else {
        for x in 10..=202 {
            o.push(cmd(
                Kind::Line,
                [x as f32, 5.0, 0.0, 50.0],
                sample(r, (x - 10) as f32 / 192.0),
            ));
        }
    }
    query(&mut o, 7);
    o.push(cmd(Kind::Pen, [0.0; 4], frame));
    rect(&mut o, Kind::Frame, STRIP, frame);
    for i in 1..=3 {
        o.push(cmd(
            Kind::Ticks,
            [(10 + 48 * i) as f32, 5.0, 0.0, 50.0],
            frame,
        ));
    }
    o.push(cmd(Kind::ReleasePen, [0.0; 4], empty));
    o.push(cmd(Kind::Pen, [0.0; 4], frame));
    for i in 0..r.count as usize {
        rect(&mut o, Kind::Fill, marker(r, i), color(r.stops[i]));
        rect(&mut o, Kind::Frame, marker(r, i), frame);
    }
    o.push(cmd(Kind::ReleasePen, [0.0; 4], empty));
    for b in [2, 3, 0, 1] {
        let enabled = b != 1 || can_paste;
        let hover = BUTTONS[b].contains(s.hover_x, s.hover_y);
        let tf = if !enabled {
            0.3
        } else if s.armed == b as i32 {
            1.0
        } else {
            0.7
        };
        let ff = if !enabled {
            0.3
        } else if s.armed == b as i32 || hover {
            1.0
        } else {
            0.7
        };
        o.push(cmd(Kind::Antialias, [0.0; 4], empty));
        for role in [8, 7, 2] {
            query(&mut o, role);
        }
        rect(&mut o, Kind::Fill, BUTTONS[b], scaled(fill, ff));
        rect(&mut o, Kind::Frame, BUTTONS[b], frame);
        let r = BUTTONS[b];
        o.push(text(
            [
                (r.0 + r.2) as f32 * 0.5,
                r.1 as f32 + 2.0 + 16.0 * 0.8,
                (r.2 - r.0) as f32,
                0.0,
            ],
            scaled(foreground, tf),
            ["copy", "paste", "randomize", "flip"][b],
            16.0,
        ));
    }
    o.push(cmd(Kind::Antialias, [0.0; 4], empty));
    for role in [42, 8, 7, 2, 2] {
        query(&mut o, role);
    }
    rect(&mut o, Kind::Fill, HEADER, black);
    let font = 20.0 * (1.0 - 0.15 * 2.0);
    o.push(text(
        [260.0, 5.0 + 20.0 * 0.15 + font * 0.8, 80.0, 0.0],
        foreground,
        "▼  PRESETS",
        font,
    ));
    if s.menu_open {
        rect(
            &mut o,
            Kind::Fill,
            Rect(220, 25, 300, 25 + 23 * 34 + 5),
            black,
        );
        for index in 0..7 {
            if index + s.scroll >= 34 {
                break;
            }
            let p = preset((index + s.scroll) as usize);
            let r = row(index);
            for x in r.0..=r.2 {
                o.push(cmd(
                    Kind::Line,
                    [x as f32, r.1 as f32, 0.0, 18.0],
                    sample(&p, (x - r.0) as f32 / 64.0),
                ));
            }
            rect(
                &mut o,
                Kind::Frame,
                r,
                if r.contains(s.hover_x, s.hover_y) {
                    foreground
                } else {
                    frame
                },
            );
        }
    }
    o
}

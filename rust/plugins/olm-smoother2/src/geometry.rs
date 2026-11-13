//! Checked storage and verified primitive bridge for mechanically translated geometry.
#![allow(non_snake_case, non_upper_case_globals, dead_code)]
use crate::{
    scan::{Axial, Diagonal, Grid},
    types::{Pixel, Vertex},
};
use olm_core::{Error, Result};
// Retain generated control flow, casts and expressions for source comparison.
#[allow(clippy::unnecessary_cast, clippy::double_parens, clippy::needless_return,
    clippy::unused_unit, clippy::identity_op, clippy::collapsible_else_if,
    clippy::assign_op_pattern, unused_parens,unused_mut,unused_assignments,while_true,unused_variables)]
#[path="geometry_generated.rs"]
#[rustfmt::skip]
mod generated;
use generated::*;
const K_HALF: f32 = 0.5;
const K_ONE: f32 = 1.0;
const K_DD8: f32 = 0.2;
const K_W025: f32 = 0.25;
const W_STEP: f32 = 0.125;
const W_OUT_W: f32 = 0.4;
const W_IN_W: f32 = 0.2;
const g_olmsmoother2_leaf_diag_mode: i32 = 0;
const g_olmsmoother2_idx0_diag_mode: i32 = 0;
const g_olmsmoother2_idx18_diag_mode: i32 = 0;

fn win_weight_pair(out: &mut [f32], span: i32, offset: i32, key: i32, _scalar: bool) {
    out[..2].copy_from_slice(
        &crate::weights::pair(span, offset, key).expect("valid coverage geometry"),
    );
}
fn corner(step: f32, c: crate::polygon::Corner, p: &mut State) {
    let plane = crate::polygon::Plane::new(
        p.plane,
        p.cplane_w as usize,
        p.cplane_h as usize,
        p.cplane_w as usize,
    )
    .unwrap();
    let mut q = crate::polygon::Polygon::new(plane, p.cur_x, p.cur_y, p.smoothness_n).unwrap();
    q.corner(c, step).unwrap();
    for v in q.samples() {
        if p.count < 12 {
            p.samples[p.count as usize] = *v;
            p.count += 1;
        }
    }
}
fn win_FUN_1800134c0_NW(step: f32, p: &mut State) {
    corner(step, crate::polygon::Corner::Nw, p)
}
fn win_FUN_180013570_NE(step: f32, p: &mut State) {
    corner(step, crate::polygon::Corner::Ne, p)
}
fn win_FUN_180012c20_SW(step: f32, p: &mut State) {
    corner(step, crate::polygon::Corner::Sw, p)
}
fn win_FUN_180012ce0_SE(step: f32, p: &mut State) {
    corner(step, crate::polygon::Corner::Se, p)
}
fn win_FUN_18000cc70_normalize(p: &mut State) {
    if p.count > 0 {
        let inv = 1.0 / p.count as f32;
        for v in &mut p.samples[..p.count as usize] {
            v.weight *= inv;
        }
    }
}

pub(crate) fn build(p: &mut State) {
    if p.smoothness_n == 0.0 {
        return;
    }
    let g = grid_of(p);
    let x = p.cur_x;
    let y = p.cur_y;
    let east = if x < g.w - 1 {
        (cp_b(&g, x + 1, y, 0) == 0) as i32
    } else {
        1
    };
    let sw = x > 0 && y < g.h - 1 && cp_b(&g, x - 1, y + 1, 3) != 0;
    let south = y < g.h - 1 && cp_b(&g, x, y + 1, 1) != 0;
    let se = if x < g.w - 1 && y < g.h - 1 {
        (cp_b(&g, x + 1, y + 1, 2) == 0) as i32
    } else {
        1
    };
    let idx = ((if sw { 0 } else { 2 }) + east + (((!south) as i32 + se * 2) * 4)) * 16
        + (if cp_b(&g, x, y, 3) == 0 { 4 } else { 0 })
        + (if cp_b(&g, x, y, 2) == 0 { 1 } else { 0 })
        + (if cp_b(&g, x, y, 1) == 0 { 2 } else { 0 })
        + (if cp_b(&g, x, y, 0) == 0 { 8 } else { 0 });
    dispatch(idx, p);
}

pub(crate) struct State<'a> {
    plane: &'a [Pixel],
    cplane_base: &'a [u8],
    cplane_w: i32,
    cplane_h: i32,
    cplane_stride: i32,
    cur_x: i32,
    cur_y: i32,
    smoothness_n: f32,
    extra_n: f32,
    samples: [Vertex; 12],
    count: i32,
    failed: bool,
    preserve_pf32_scalar_rounding: bool,
}
impl<'a> State<'a> {
    #[allow(clippy::too_many_arguments)] // One-to-one parameters of the source geometry context.
    pub(crate) fn new(
        plane: &'a [Pixel],
        classes: &'a [u8],
        w: i32,
        h: i32,
        x: i32,
        y: i32,
        smooth: f32,
        extra: f32,
    ) -> Result<Self> {
        if w <= 0 || h <= 0 || x < 0 || x >= w || y < 0 || y >= h {
            return Err(Error::Geometry);
        }
        let n = (w as usize)
            .checked_mul(h as usize)
            .ok_or(Error::Overflow)?;
        let stride = w.checked_mul(4).ok_or(Error::Overflow)?;
        if n > i32::MAX as usize / 4 || plane.len() != n || classes.len() != n * 4 {
            return Err(Error::Bounds);
        }
        Ok(Self {
            plane,
            cplane_base: classes,
            cplane_w: w,
            cplane_h: h,
            cplane_stride: stride,
            cur_x: x,
            cur_y: y,
            smoothness_n: smooth,
            extra_n: extra,
            samples: [Vertex::default(); 12],
            count: 0,
            failed: false,
            preserve_pf32_scalar_rounding: true,
        })
    }
    pub(crate) fn vertices(&self) -> Result<&[Vertex]> {
        if self.failed {
            Err(Error::Bounds)
        } else {
            Ok(&self.samples[..self.count as usize])
        }
    }
}
#[derive(Clone, Copy)]
struct GridDesc<'a> {
    base: &'a [u8],
    w: i32,
    h: i32,
    stride: i32,
}
fn grid_of<'a>(poly: &State<'a>) -> GridDesc<'a> {
    GridDesc {
        base: poly.cplane_base,
        w: poly.cplane_w,
        h: poly.cplane_h,
        stride: poly.cplane_stride,
    }
}
fn cp_b(g: &GridDesc, x: i32, y: i32, c: i32) -> u8 {
    if x < 0 || y < 0 || x >= g.w || y >= g.h {
        0
    } else {
        g.base[(y * g.stride + x * 4 + c) as usize]
    }
}
fn win_FUN_180013630_trapezoid(w: f32, p: i32, e: f32) -> f32 {
    crate::scan::trapezoid(w, p, e)
}
fn win_FUN_1800104d0_append(x: i32, y: i32, weight: f32, p: &mut State) {
    if p.count >= 12 {
        return;
    }
    if x < 0 || y < 0 || x >= p.cplane_w || y >= p.cplane_h {
        p.failed = true;
        return;
    }
    p.samples[p.count as usize] = Vertex {
        pixel: p.plane[(y * p.cplane_w + x) as usize],
        weight,
    };
    p.count += 1;
}
macro_rules! axial {($($name:ident:$kind:ident),*)=>{$(fn $name(out:&mut[i32],g:&GridDesc,input:&[i32]){
    let grid=Grid::new(g.base,g.w,g.h,g.stride as usize).unwrap();
    let result=grid.axial(Axial::$kind,input[0],input[1]);
    // The translated C++ scanners' initial out-of-bounds return.
    let fallback=match Axial::$kind {Axial::D230|Axial::D800=>[input[0],input[1]+1,0],Axial::D3b0|Axial::Da50=>[input[0]+1,input[1],0],_=>[input[0],input[1],0]};
    out[..3].copy_from_slice(&result.unwrap_or(fallback));
})*};}
axial!(scan_d0d0:D0d0,scan_cee0:D0d0,scan_d230:D230,scan_d3b0:D3b0,scan_d520:D520,scan_d6a0:D6a0,scan_d800:D800,scan_da50:Da50,scan_dbd0:Dbd0);
macro_rules! diagonal {($($name:ident:$kind:ident),*)=>{$(fn $name(out:&mut[i32],g:&GridDesc,input:&[i32]){
    let grid=Grid::new(g.base,g.w,g.h,g.stride as usize).unwrap();
    out[..2].copy_from_slice(&grid.diagonal(Diagonal::$kind,input[0],input[1]).expect("diagonal start within plane"));
})*};}
diagonal!(scan_108d0:D108d0,scan_109d0:D109d0,scan_10ad0:D10ad0,scan_10bd0:D10bd0,scan_10d20:D10d20,scan_10e40:D10e40);

#[cfg(test)]
pub(crate) fn test_leaf(id: usize, desc: &[i32], scale: f32, p: &mut State) -> bool {
    generated::call_leaf(id, desc, scale, p)
}

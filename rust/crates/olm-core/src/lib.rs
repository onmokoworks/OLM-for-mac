//! Host-independent checked geometry, allocation and byte-strided ARGB worlds.
use std::mem::size_of;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error {
    Geometry,
    Overflow,
    Allocation,
    Bounds,
    Unsupported,
}
pub type Result<T> = std::result::Result<T, Error>;

/// Half-open global-coordinate rectangle. Construction rejects inverted bounds.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Rect {
    left: i32,
    top: i32,
    right: i32,
    bottom: i32,
}
impl Rect {
    pub fn left(self) -> i32 {
        self.left
    }
    pub fn top(self) -> i32 {
        self.top
    }
    pub fn right(self) -> i32 {
        self.right
    }
    pub fn bottom(self) -> i32 {
        self.bottom
    }
    pub fn contains(self, b: Self) -> bool {
        self.left <= b.left && self.top <= b.top && self.right >= b.right && self.bottom >= b.bottom
    }
    pub fn inflate_clipped(self, x: i32, y: i32, bounds: Self) -> Result<Self> {
        if x < 0 || y < 0 {
            return Err(Error::Geometry);
        }
        Ok(Self::new(
            self.left.checked_sub(x).ok_or(Error::Overflow)?,
            self.top.checked_sub(y).ok_or(Error::Overflow)?,
            self.right.checked_add(x).ok_or(Error::Overflow)?,
            self.bottom.checked_add(y).ok_or(Error::Overflow)?,
        )?
        .intersection(bounds))
    }
    pub fn new(left: i32, top: i32, right: i32, bottom: i32) -> Result<Self> {
        if left > right || top > bottom {
            return Err(Error::Geometry);
        }
        Ok(Self {
            left,
            top,
            right,
            bottom,
        })
    }
    pub fn from_size(x: i32, y: i32, w: usize, h: usize) -> Result<Self> {
        let r = i64::from(x)
            .checked_add(i64::try_from(w).map_err(|_| Error::Overflow)?)
            .ok_or(Error::Overflow)?;
        let b = i64::from(y)
            .checked_add(i64::try_from(h).map_err(|_| Error::Overflow)?)
            .ok_or(Error::Overflow)?;
        Self::new(
            x,
            y,
            i32::try_from(r).map_err(|_| Error::Overflow)?,
            i32::try_from(b).map_err(|_| Error::Overflow)?,
        )
    }
    pub fn width(self) -> usize {
        (i64::from(self.right) - i64::from(self.left)) as usize
    }
    pub fn height(self) -> usize {
        (i64::from(self.bottom) - i64::from(self.top)) as usize
    }
    pub fn is_empty(self) -> bool {
        self.left == self.right || self.top == self.bottom
    }
    pub fn intersection(self, b: Self) -> Self {
        let l = self.left.max(b.left);
        let t = self.top.max(b.top);
        Self {
            left: l,
            top: t,
            right: self.right.min(b.right).max(l),
            bottom: self.bottom.min(b.bottom).max(t),
        }
    }
    pub fn union(self, b: Self) -> Self {
        if self.is_empty() {
            return b;
        }
        if b.is_empty() {
            return self;
        }
        Self {
            left: self.left.min(b.left),
            top: self.top.min(b.top),
            right: self.right.max(b.right),
            bottom: self.bottom.max(b.bottom),
        }
    }
}

/// Checked caller-owned budget. Reserve every simultaneously live scratch plane.
pub struct Budget {
    limit: usize,
    used: usize,
}
impl Budget {
    pub fn new(limit: usize) -> Self {
        Self { limit, used: 0 }
    }
    pub fn reserve(&mut self, n: usize) -> Result<()> {
        let next = self.used.checked_add(n).ok_or(Error::Overflow)?;
        if next > self.limit {
            return Err(Error::Allocation);
        }
        self.used = next;
        Ok(())
    }
    pub fn used(&self) -> usize {
        self.used
    }
}
pub fn image_len(w: usize, h: usize) -> Result<usize> {
    if w == 0 || h == 0 {
        return Err(Error::Geometry);
    }
    w.checked_mul(h).ok_or(Error::Overflow)
}
pub fn allocate<T: Clone>(n: usize, value: T, budget: &mut Budget) -> Result<Vec<T>> {
    let bytes = n.checked_mul(size_of::<T>()).ok_or(Error::Overflow)?;
    if bytes > isize::MAX as usize {
        return Err(Error::Overflow);
    }
    if bytes > budget.limit - budget.used {
        return Err(Error::Allocation);
    }
    let mut v = Vec::new();
    v.try_reserve_exact(n).map_err(|_| Error::Allocation)?;
    v.resize(n, value);
    budget.reserve(bytes)?;
    Ok(v)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Depth {
    U8,
    U16,
    F32,
}
impl Depth {
    pub fn pixel_bytes(self) -> usize {
        match self {
            Self::U8 => 4,
            Self::U16 => 8,
            Self::F32 => 16,
        }
    }
}
/// Native ARGB storage, preserving float payload bits when copied.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Pixel {
    U8([u8; 4]),
    U16([u16; 4]),
    F32([f32; 4]),
}
impl Pixel {
    pub fn normalized(self) -> [f32; 4] {
        match self {
            Self::U8(p) => p.map(|v| v as f32 * 0.003921568859368563f32),
            Self::U16(p) => p.map(|v| v as f32 / 32768.0),
            Self::F32(p) => p,
        }
    }
    pub fn alpha(self) -> f32 {
        match self {
            Self::U8(p) => p[0] as f32,
            Self::U16(p) => p[0] as f32,
            Self::F32(p) => p[0],
        }
    }
    pub fn with_alpha(mut self, a: f32) -> Self {
        match &mut self {
            Self::U8(p) => p[0] = a as u8,
            Self::U16(p) => p[0] = a as u16,
            Self::F32(p) => p[0] = a,
        }
        self
    }
}

/// Positive byte stride; the final row need not include padding. Odd strides allowed.
#[derive(Clone, Copy, Debug)]
pub struct Layout {
    pub width: usize,
    pub height: usize,
    pub stride: usize,
    pub depth: Depth,
    pub origin: (i32, i32),
}
impl Layout {
    pub fn span(self) -> Result<usize> {
        image_len(self.width, self.height)?;
        Rect::from_size(self.origin.0, self.origin.1, self.width, self.height)?;
        let row = self
            .width
            .checked_mul(self.depth.pixel_bytes())
            .ok_or(Error::Overflow)?;
        if self.stride < row {
            return Err(Error::Geometry);
        }
        let n = (self.height - 1)
            .checked_mul(self.stride)
            .and_then(|n| n.checked_add(row))
            .ok_or(Error::Overflow)?;
        if n > isize::MAX as usize {
            return Err(Error::Overflow);
        }
        Ok(n)
    }
    pub fn rect(self) -> Result<Rect> {
        Rect::from_size(self.origin.0, self.origin.1, self.width, self.height)
    }
    fn offset(self, x: usize, y: usize) -> Result<usize> {
        if x >= self.width || y >= self.height {
            return Err(Error::Bounds);
        }
        Ok(y * self.stride + x * self.depth.pixel_bytes())
    }
}
pub struct View<'a> {
    data: &'a [u8],
    layout: Layout,
}
pub struct ViewMut<'a> {
    data: &'a mut [u8],
    layout: Layout,
}
impl<'a> View<'a> {
    pub fn layout(&self) -> Layout {
        self.layout
    }
    /// Same borrowed storage with an explicitly chosen coordinate origin.
    pub fn rebased(&self, origin: (i32, i32)) -> Result<View<'_>> {
        Self::new(
            self.data,
            Layout {
                origin,
                ..self.layout
            },
        )
    }
    pub fn new(data: &'a [u8], layout: Layout) -> Result<Self> {
        if data.len() < layout.span()? {
            return Err(Error::Bounds);
        }
        Ok(Self { data, layout })
    }
    pub fn get(&self, x: usize, y: usize) -> Result<Pixel> {
        let i = self.layout.offset(x, y)?;
        Ok(read_pixel(&self.data[i..], self.layout.depth))
    }
    pub fn get_global(&self, x: i32, y: i32) -> Result<Pixel> {
        let x = usize::try_from(i64::from(x) - i64::from(self.layout.origin.0))
            .map_err(|_| Error::Bounds)?;
        let y = usize::try_from(i64::from(y) - i64::from(self.layout.origin.1))
            .map_err(|_| Error::Bounds)?;
        self.get(x, y)
    }
}
impl<'a> ViewMut<'a> {
    pub fn layout(&self) -> Layout {
        self.layout
    }
    pub fn new(data: &'a mut [u8], layout: Layout) -> Result<Self> {
        if data.len() < layout.span()? {
            return Err(Error::Bounds);
        }
        Ok(Self { data, layout })
    }
    pub fn set(&mut self, x: usize, y: usize, p: Pixel) -> Result<()> {
        let i = self.layout.offset(x, y)?;
        write_pixel(&mut self.data[i..], self.layout.depth, p)
    }
}

/// Explicit source dependency for ROI planning; global effects reject partial tiles.
#[derive(Clone, Copy, Debug)]
pub enum Footprint {
    Pointwise,
    Radius { x: i32, y: i32 },
    Global,
}
#[derive(Clone, Copy, Debug)]
pub struct CheckoutPlan {
    pub requested: Rect,
    pub output: Rect,
    pub input: Rect,
}
pub fn checkout_plan(footprint: Footprint, request: Rect, frame: Rect) -> Result<CheckoutPlan> {
    if request.is_empty() || frame.is_empty() {
        return Err(Error::Geometry);
    }
    let output = request.intersection(frame);
    if output.is_empty() {
        return Err(Error::Bounds);
    }
    let input = match footprint {
        Footprint::Pointwise => output,
        Footprint::Radius { x, y } => output.inflate_clipped(x, y, frame)?,
        Footprint::Global => {
            if !request.contains(frame) {
                return Err(Error::Unsupported);
            }
            frame
        }
    };
    Ok(CheckoutPlan {
        requested: request,
        output,
        input,
    })
}
fn read_pixel(d: &[u8], depth: Depth) -> Pixel {
    match depth {
        Depth::U8 => Pixel::U8(d[..4].try_into().unwrap()),
        Depth::U16 => Pixel::U16(std::array::from_fn(|i| {
            u16::from_ne_bytes(d[i * 2..i * 2 + 2].try_into().unwrap())
        })),
        Depth::F32 => Pixel::F32(std::array::from_fn(|i| {
            f32::from_ne_bytes(d[i * 4..i * 4 + 4].try_into().unwrap())
        })),
    }
}
fn write_pixel(d: &mut [u8], depth: Depth, p: Pixel) -> Result<()> {
    match (depth, p) {
        (Depth::U8, Pixel::U8(p)) => d[..4].copy_from_slice(&p),
        (Depth::U16, Pixel::U16(p)) => {
            for i in 0..4 {
                d[i * 2..i * 2 + 2].copy_from_slice(&p[i].to_ne_bytes())
            }
        }
        (Depth::F32, Pixel::F32(p)) => {
            for i in 0..4 {
                d[i * 4..i * 4 + 4].copy_from_slice(&p[i].to_ne_bytes())
            }
        }
        _ => return Err(Error::Unsupported),
    }
    Ok(())
}

/// Disjoint row ownership; fixed row indices and no cross-row reductions.
/// The callback must itself be deterministic and independent of invocation order.
pub fn parallel_rows<T: Send, F: Fn(usize, &mut [T]) + Sync>(
    data: &mut [T],
    stride: usize,
    threads: usize,
    f: F,
) -> Result<()> {
    if stride == 0 || data.len() % stride != 0 || threads == 0 {
        return Err(Error::Geometry);
    }
    let rows = data.len() / stride;
    if rows == 0 {
        return Ok(());
    }
    let chunk = rows
        .div_ceil(threads.min(rows))
        .checked_mul(stride)
        .ok_or(Error::Overflow)?;
    std::thread::scope(|s| {
        for (part, d) in data.chunks_mut(chunk).enumerate() {
            let f = &f;
            s.spawn(move || {
                for (j, row) in d.chunks_mut(stride).enumerate() {
                    f(part * (chunk / stride) + j, row)
                }
            });
        }
    });
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn geometry_and_budget() {
        assert!(Rect::from_size(i32::MAX, 0, 1, 1).is_err());
        assert!(image_len(usize::MAX, 2).is_err());
        let mut b = Budget::new(4);
        b.reserve(4).unwrap();
        assert!(b.reserve(1).is_err());
        assert_eq!(b.used(), 4);
    }
    #[test]
    fn odd_stride() {
        let l = Layout {
            width: 1,
            height: 2,
            stride: 17,
            depth: Depth::F32,
            origin: (-2, 3),
        };
        let mut d = [0u8; 33];
        let p = Pixel::F32([f32::from_bits(0x7f800001), -0.0, 2.0, 3.0]);
        ViewMut::new(&mut d, l).unwrap().set(0, 1, p).unwrap();
        let Pixel::F32(q) = View::new(&d, l).unwrap().get_global(-2, 4).unwrap() else {
            panic!()
        };
        assert_eq!(q[0].to_bits(), 0x7f800001);
        assert_eq!(q[1].to_bits(), 0x80000000);
    }
    #[test]
    fn schedule_independent() {
        let mut a = vec![0; 51];
        let mut b = a.clone();
        parallel_rows(&mut a, 3, 1, |y, r| r.fill(y)).unwrap();
        parallel_rows(&mut b, 3, 7, |y, r| r.fill(y)).unwrap();
        assert_eq!(a, b);
    }
}

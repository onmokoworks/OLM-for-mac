/// Internal float scratch order is RGBA, whereas AE worlds are ARGB.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Pixel {
    pub r: f32,
    pub g: f32,
    pub b: f32,
    pub a: f32,
}

impl Pixel {
    pub fn words(self) -> [u32; 4] {
        [
            self.r.to_bits(),
            self.g.to_bits(),
            self.b.to_bits(),
            self.a.to_bits(),
        ]
    }
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct Vertex {
    pub pixel: Pixel,
    pub weight: f32,
}

pub const COLOR_TOL: f32 = f32::from_bits(0x3b008081);

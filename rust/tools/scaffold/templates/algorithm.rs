//! TODO: port the original algorithm. This scaffold only copies input bytes.
//! No AE types, arithmetic on pixels, color conversion, or reference-equivalence claim.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Layout {
    pub width: usize,
    pub height: usize,
    pub row_bytes: usize,
    pub bytes_per_pixel: usize,
    pub origin: (i32, i32),
}
impl Layout {
    pub fn span(self) -> Option<usize> {
        if ![4, 8, 16].contains(&self.bytes_per_pixel) {
            return None;
        }
        let row = self.width.checked_mul(self.bytes_per_pixel)?;
        if self.row_bytes < row {
            return None;
        }
        if self.height == 0 {
            return Some(0);
        }
        self.row_bytes
            .checked_mul(self.height - 1)?
            .checked_add(row)
    }
}
/// TODO: replace with original behavior and add owned parameter values.
/// Copies the intersection in layer coordinates; clears uncovered output pixels.
/// Preserves every bit (including float NaNs) and leaves row padding untouched.
pub fn render(input: &[u8], a: Layout, output: &mut [u8], b: Layout) -> Result<(), &'static str> {
    if a.bytes_per_pixel != b.bytes_per_pixel
        || a.span().ok_or("input layout")? > input.len()
        || b.span().ok_or("output layout")? > output.len()
    {
        return Err("layout mismatch");
    }
    for y in 0..b.height {
        let sy = i64::from(b.origin.1) + y as i64 - i64::from(a.origin.1);
        for x in 0..b.width {
            let sx = i64::from(b.origin.0) + x as i64 - i64::from(a.origin.0);
            let dst = y * b.row_bytes + x * b.bytes_per_pixel;
            if sx >= 0 && sy >= 0 && (sx as usize) < a.width && (sy as usize) < a.height {
                let src = sy as usize * a.row_bytes + sx as usize * a.bytes_per_pixel;
                output[dst..dst + b.bytes_per_pixel]
                    .copy_from_slice(&input[src..src + a.bytes_per_pixel]);
            } else {
                output[dst..dst + b.bytes_per_pixel].fill(0);
            }
        }
    }
    Ok(())
}

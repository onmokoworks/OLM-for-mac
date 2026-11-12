//! Original arbitrary-data ABI: 0x144 in memory, 0x145 flattened.
//! Disk fields are little-endian: version byte, u32 count, sixteen (position,
//! alpha, red, green, blue) binary32 records. Unused flat records are zero.
#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Ramp {
    pub count: u32,
    pub stops: [[f32; 5]; 16],
}
impl Default for Ramp {
    fn default() -> Self {
        let mut r = Self {
            count: 3,
            stops: [[0.0; 5]; 16],
        };
        r.stops[0] = [0.0, 1.0, 1.0, 0.0, 0.0];
        r.stops[1] = [0.78, 1.0, 1.0, 0.651, 0.0];
        r.stops[2] = [1.0; 5];
        r
    }
}
impl Ramp {
    pub fn flatten(&self) -> Option<[u8; 325]> {
        if self.count > 16 {
            return None;
        }
        let mut out = [0; 325];
        out[0] = 1;
        out[1..5].copy_from_slice(&self.count.to_le_bytes());
        for (i, stop) in self.stops[..self.count as usize].iter().enumerate() {
            for (j, v) in stop.iter().enumerate() {
                out[5 + i * 20 + j * 4..9 + i * 20 + j * 4]
                    .copy_from_slice(&v.to_bits().to_le_bytes());
            }
        }
        Some(out)
    }
    pub fn unflatten(bytes: &[u8]) -> Option<Self> {
        if bytes.len() < 5 {
            return None;
        }
        let count = u32::from_le_bytes(bytes[1..5].try_into().ok()?);
        if count > 16 || bytes.len() < 5 + count as usize * 20 {
            return None;
        }
        // Like the original/C++ parser, the version byte is not a rejection gate.
        let mut r = Self {
            count,
            stops: [[0.0; 5]; 16],
        };
        for i in 0..count as usize {
            for j in 0..5 {
                r.stops[i][j] = f32::from_bits(u32::from_le_bytes(
                    bytes[5 + i * 20 + j * 4..9 + i * 20 + j * 4]
                        .try_into()
                        .ok()?,
                ));
            }
        }
        Some(r)
    }
    pub fn equal_active(&self, other: &Self) -> bool {
        self.count <= 16
            && self.count == other.count
            && self.stops[..self.count as usize] == other.stops[..other.count as usize]
    }
    pub fn interpolate(&self, other: &Self, t: f32) -> Self {
        let mut r = Self {
            count: 0,
            stops: [[0.0; 5]; 16],
        };
        if self.count == 0 || other.count == 0 || self.count > 16 || other.count > 16 {
            return r;
        }
        r.count = self.count.max(other.count);
        for i in 0..r.count as usize {
            for j in 0..5 {
                let a = self.stops[i.min(self.count as usize - 1)][j];
                let b = other.stops[i.min(other.count as usize - 1)][j];
                r.stops[i][j] = a + (b - a) * t;
            }
        }
        r
    }
    pub fn sample(&self, amount: f32) -> [f32; 3] {
        let mut lower: Option<&[f32; 5]> = None;
        let mut upper: Option<&[f32; 5]> = None;
        for s in &self.stops[..(self.count as usize).min(16)] {
            if s[0] <= amount {
                if lower.is_none_or(|v| v[0] <= s[0] && v[0] != s[0]) {
                    lower = Some(s);
                }
            } else if upper.is_none_or(|v| s[0] < v[0]) {
                upper = Some(s);
            }
        }
        match (lower, upper) {
            (None, None) => [1.0, 0.0, 0.0],
            (Some(s), None) | (None, Some(s)) => [s[2], s[3], s[4]],
            (Some(a), Some(b)) => {
                let t = (amount - a[0]) / (b[0] - a[0]);
                std::array::from_fn(|c| a[c + 2] + (b[c + 2] - a[c + 2]) * t)
            }
        }
    }
}

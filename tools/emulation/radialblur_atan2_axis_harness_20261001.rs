// Standalone scalar diagnostic for the controlled reference import.
// Dynamic inputs prevent compile-time evaluation of host atan2f.
use std::io::{self, BufRead};

fn main() {
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let words: Vec<&str> = line.split_whitespace().collect();
        assert_eq!(words.len(), 2);
        let y = f32::from_bits(u32::from_str_radix(words[0], 16).unwrap());
        let x = f32::from_bits(u32::from_str_radix(words[1], 16).unwrap());
        let host = y.atan2(x);
        let axis = if y.to_bits() == 0 && x.is_finite() && x < 0.0 {
            std::f32::consts::PI
        } else {
            host
        };
        let double_cast = (f64::from(y).atan2(f64::from(x))) as f32;
        println!("{:08x} {:08x} {:08x}", host.to_bits(), axis.to_bits(), double_cast.to_bits());
    }
}

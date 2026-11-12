use olm_golden::*;
fn main() {
    run("ColorKeep", ALL_DEPTHS, |c, input, out| {
        let n = [0, 1, 2, 5, 9, 100][c.index % 6];
        c.number(1, n as f64);
        let palette: Vec<_> = (0..n)
            .map(|i| c.color(2 + i, if i % 2 == 0 { [255; 4] } else { [255, 0, 0, 0] }))
            .collect();
        color_keep::render(input, out, &palette).unwrap();
    });
}

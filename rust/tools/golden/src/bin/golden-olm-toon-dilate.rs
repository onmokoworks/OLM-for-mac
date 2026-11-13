use olm_golden::*;
use olm_toon_dilate::algorithm;
fn main() {
    run("OLMToonDilate", ALL_DEPTHS, |c, input, out| {
        let radius = [0., 0.5, 1., 2.25, 5., 12.][c.index % 6];
        c.number(1, radius);
        let l = input.layout();
        let mut src = vec![0; l.span().unwrap()];
        let mut dst = vec![0; src.len()];
        {
            let mut world = olm_core::ViewMut::new(&mut src, l).unwrap();
            for y in 0..c.height {
                for x in 0..c.width {
                    world.set(x, y, input.get(x, y).unwrap()).unwrap();
                }
            }
        }
        algorithm::render(
            &src,
            l,
            &mut dst,
            l,
            algorithm::effective_radius(radius, 1, c.denominator).unwrap(),
        )
        .unwrap();
        let world = olm_core::View::new(&dst, l).unwrap();
        for y in 0..c.height {
            for x in 0..c.width {
                out.set(x, y, world.get(x, y).unwrap()).unwrap();
            }
        }
    });
}

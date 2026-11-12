//! Persistent button edits use ordinary color/count streams, not sequence data.
use crate::algorithm::{detect, Color, Layout};
pub fn additions(
    input: &[u8],
    layout: Layout,
    active: &[Color],
    initialize: bool,
) -> Result<(usize, Vec<(usize, Color)>), &'static str> {
    if active.len() > 100 {
        return Err("palette size");
    }
    let mut first_black = false;
    let mut preserved = 0;
    let slots: Vec<_> = (0..100)
        .filter(|&k| {
            if initialize || k >= active.len() {
                return true;
            }
            let black = active[k][1..] == [0.0; 3];
            if black && first_black {
                return true;
            }
            first_black |= black;
            preserved += 1;
            false
        })
        .collect();
    let colors = detect(input, layout, active, slots.len())?;
    Ok((
        active.len().max(preserved + colors.len()),
        slots.into_iter().zip(colors).collect(),
    ))
}

//! Bounded, scoped row chunks; small images and single-worker calls stay inline.
use olm_core::{Error, Result};

pub(crate) fn parallel_rows<T: Send, F: Fn(usize, &mut [T]) + Sync>(
    data: &mut [T],
    width: usize,
    requested: usize,
    f: F,
) -> Result<()> {
    if width == 0 || data.len() % width != 0 || requested == 0 {
        return Err(Error::Geometry);
    }
    let available = std::thread::available_parallelism().map_or(1, usize::from);
    // At least 16K pixels per worker amortizes OS-thread setup across all three
    // pipeline stages. No global state or workers survive the render call.
    let workers = requested.min(available).min((data.len() / 16384).max(1));
    if workers == 1 {
        for (y, row) in data.chunks_mut(width).enumerate() {
            f(y, row);
        }
        Ok(())
    } else {
        olm_core::parallel_rows(data, width, workers, f)
    }
}

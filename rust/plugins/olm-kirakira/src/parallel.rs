//! Local bounded row work; no persistent pool or render-global mutable state.
pub(crate) fn workers(elements: usize) -> usize {
    if elements < 262_144 {
        1
    } else {
        std::thread::available_parallelism()
            .map_or(1, usize::from)
            .min(8)
    }
}

/// `unit` keeps dependent row groups in the same chunk. `start` is an element
/// offset in the complete output, including for the serial execution path.
pub(crate) fn chunks<T: Send>(
    out: &mut [T],
    unit: usize,
    workers: usize,
    run: impl Fn(usize, &mut [T]) + Sync,
) {
    if out.is_empty() {
        return;
    }
    let units = out.len().div_ceil(unit);
    let workers = workers.max(1).min(units);
    if workers == 1 {
        run(0, out);
        return;
    }
    let size = units.div_ceil(workers) * unit;
    std::thread::scope(|scope| {
        let run = &run;
        for (i, chunk) in out.chunks_mut(size).enumerate() {
            scope.spawn(move || run(i * size, chunk));
        }
    });
}

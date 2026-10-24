# R08 full-size read-only snapshots

`python3 tools/emulation/aexcompat_patches/build_R08.py` verifies the retained
C53b source manifest, copies it to `~/.cache/olm-emu/src-R08`, and raises only
the configuration and capture limits from 16 MiB to 64 MiB. Arithmetic, guest
writes, imports, fixture generation and watch selection semantics are unchanged.

The recipe builds offline/locked with one job, requires at least 30% free memory,
installs `~/.cache/olm-emu/worker-R08-trace/aex-guest-worker` and its source/build
manifest, updates INDEX under its lock, and deletes `build-R08`. `--rebuild`
replaces only this recipe's own hash-verified source and binary.

Use the C53b watch schema and require complete snapshot lengths and hashes.
The limit is per snapshot; multiple watches retain multiple before/after buffers.
Run sequentially and check memory pressure. The R08 full-size driver converts
one trace at a time into compressed binary planes plus metadata, then removes
the large hex JSON. A 31,795,200-byte plane now fits without displacement.

Validation and outstanding scope are recorded in
`orchestra/reports/R08-radial-fullsize-trace.md`. No compatibility claim follows
from capacity alone: traced final outputs must equal the untraced F46 worker
on both repeats, and each refreshed plane must also match current production.

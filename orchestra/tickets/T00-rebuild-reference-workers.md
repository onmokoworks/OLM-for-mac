## Goal
Rebuild the emulator reference workers (`aex-guest-worker`) that all RadialBlur
probes depend on, into a **persistent shared cache**, and record their identity.
All previous builds lived in /tmp and are gone.

## Exception to brief rule 6
For this ticket you MAY write to `/Users/onmk/Documents/Projects/Personal/OLM as/.cache/emu/`
(gitignored). Nothing else in MAIN.

## Facts
- Emulator source repos: `/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat*`
  (several issue checkouts; read-only — copy into the cache, never build in place).
- Build recipes (committed, chained parent -> child, each copies parent source,
  applies a patch, `cargo build --release --offline --locked -p aex-guest-worker`,
  and asserts the parent's worker_sha256):
  `tools/emulation/build_radialblur_{readonly_windows,axis,doublecast,noop,offset}_reference_*.py`
  plus their `aexcompat_radial_*.patch` files.
- Codex's last chain used /tmp names: radial_windows_reference_v2_20261001 ->
  radial_doublecast_reference_20261001 -> radial_noop_highdepth_reference_20261002
  -> radial_offset_reference_20261002 -> radial_offset_bound_reference_20261002.
- Expected hashes are in committed reports (grep `worker_sha256`, `source_sha256`
  in `reports/radialblur_*` and `refs/conformance/*radial*`).

## Steps
1. Work out the exact chain order and the root parent (which AEXCompat checkout +
   commit; the root "parent-build" JSON must exist or be reconstructable). Grep,
   don't read whole files.
2. Build each link into `.cache/emu/<link-name>/` with its build JSON next to it.
   Run cargo with output to a log; check the tail only.
3. Compare each resulting worker_sha256 / source sha with the recorded ones.
   Mismatch = report it (toolchain drift is possible); do not patch to force a match.
4. Write `.cache/emu/INDEX.json`: link name -> worker path, sha256, parent, recipe.
   Also commit a copy as `orchestra/reports/emu_index.json`.

## Done when
The final offset_bound-equivalent worker exists, and every link's hash either matches
the recorded one or the mismatch is explained. Report disk used.

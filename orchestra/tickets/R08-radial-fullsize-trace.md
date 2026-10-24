# R08: full-size Radial fixture planes (R06 group 1 remainder)

R06 matched 91 intermediate planes + 17 finals for the Radial legacy fixtures with `worker-C53b-trace`, but full-size
fixture 165 needs 31,795,200-byte RGBA planes, which C53b's watch buffer/offset limits reject.

## Authorization
Build a C53b-derived trace worker with a larger read-only snapshot capacity (stream planes to a file instead of the
in-memory watch buffer, or raise the limit). Copy `~/.cache/olm-emu/src-C53b` → `~/.cache/olm-emu/src-R08/`, build in
`~/.cache/olm-emu/build-R08/` (delete afterwards), install `~/.cache/olm-emu/worker-R08-trace/`, INDEX entry, patch +
build script under `tools/emulation/aexcompat_patches/`. Prove final output == F46 twice. Never edit `04_Tools/AEXCompat*`.

## Do
Capture every plane the 18 Radial legacy commands (records 152–181 in R05) require, compare with current Mac, and refresh
their pins only where twice-identical and Mac-equal. Report any difference as a finding with a witness. Then rerun those
18 commands. Watch memory: planes are ~32 MB each; keep `memory_pressure` >= 30% free.

1-2 processes. No plugin production changes.

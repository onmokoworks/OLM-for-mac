# F30 isolated UCRT math worker

`F30-ucrtmath.patch` applies to the final F29 `reference-guest` snapshot, whose
436-file manifest is pinned in `F30-evidence/parent-source.json`. The F29 builder
and patch remain the reconstruction path for that prerequisite. This patch
leaves F29's vendor Unicorn source unchanged.

The builder copies the repository's `ucrtmath/` into a local dependency crate.
Its build.rs compiles four C translation units into a static archive using
`-O2 -ffp-contract=off -fno-fast-math`; explicit FMA remains in the library.
A safe Rust interface isolates the three unsafe C calls, preserving the main
worker's `forbid(unsafe_code)` policy. `OLM_UCRT_FMA=0|1` is read once on first
math use, defaults to 1, and rejects other values. Both DLL spellings reach the
legacy import callbacks. Native Win64 callbacks use the same wrappers and now
include atan2f. Native carrier execution is not the arm64 Unicorn reference.
Other math dispatch and implementations are untouched.

Build into a **fresh**, space-free destination (the standard final destination
already exists):

```sh
python3 tools/emulation/aexcompat_patches/build_F30.py --cache-root "$HOME/.cache/olm-emu/F30-independent-check"
```

Build logs and temporary files go to this worktree's
`orchestra/state/F30-oracle-worker-ucrtmath`. The build requires at least 30%
free memory and uses one job. Delete the destination's `worker-F30-ucrtmath/build`
after checks, retaining its worker and diagnostic executable. The final worker
is registered additively by `build_F30.py --register` only after shim validation.
Registration never changes the fuzzer default.

Validation of the designated final cache worker:

```sh
python3 tools/emulation/aexcompat_patches/validate_F30.py
python3 tools/emulation/aexcompat_patches/check_mode_F30.py
python3 tools/emulation/aexcompat_patches/replay_F30.py default f29 f30
python3 tools/emulation/aexcompat_patches/summarize_F30.py
python3 tools/emulation/aexcompat_patches/verify_nan_F30.py
```

The shim diagnostic installs the actual Unicorn callbacks, asserts DLL dispatch,
and executes a guest NOP at the hooked import address for each random pair.
It preserves raw input/output bits in a bounded 16 MiB scratch stream. The
comparator executes the pinned F27c PE UCRT loader under Rosetta. SplitMix64
seed `0xf30` generates one million full-width bit patterns per function,
including expf (not just a low positive subnormal sweep). Each DLL and both modes
are independently exercised. The PE DLL remains external, at the existing
cache path. Expect 12 rows with count 1,000,000 and zero mismatches.

Replay runs are serial per invocation; no more than two invocations may run
concurrently. Each uses `--jobs 1`, seed 1, n300, no shrinking, an explicit worker,
and scratch-only generated corpora. Both Classic and Smart are collected by
the existing harness; Smart is the ticket's primary comparison. Each variant has its own scratch subtree, avoiding cross-run disk-usage scans.
Reports are rerun by default; `--resume` reuses existing complete reports. The summary binds all reports
and worker hashes and retains every changed oracle/status and first mismatch.
Execution-status changes are findings, not silently assigned a numerical cause.

All successful import checks are raw-bit equality. No tolerances, port edits,
saved expectation updates, or default-worker changes are part of this ticket.

An additional x86_64 native-carrier `cargo check` fails in both unmodified F29
and F30 with the same three pre-existing Classic UI interface errors. See
`F30-evidence/native-carrier-check.json`. The shipped reference is the validated
arm64 Unicorn binary; no native-carrier executable is supplied.

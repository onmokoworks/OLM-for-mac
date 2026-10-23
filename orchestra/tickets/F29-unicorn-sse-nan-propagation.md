# F29: fix x86 SSE NaN propagation in the reference emulator

## Background (facts, from C24; read `orchestra/reports/C24-olmblur-smart-r6.md`)
- At `0x180002108 ADDSS XMM12,XMM0` with operands `7fc12345` and `ffc12346`:
  - Unicorn returns `ffc12346`, the second operand.
  - Native x86_64 under Rosetta returns `7fc12345`, as does arm64 FADD.
- Intel SDM rule for SSE binary ops on two NaN operands: the result is the first source operand
  (destination), quieted. Unicorn is based on old QEMU, whose i386 softfloat NaN propagation
  rule is wrong here.
- Over 432 OLMBlur scalar conditions, x86_64 matches the original in 420 and differs in 12. The
  disagreements involve Unicorn.

## Goal
Build a new reference worker variant whose x86 SSE/scalar float NaN propagation matches real x86
hardware. Existing workers stay untouched.

## Steps
1. **Characterize first.**
   - Write a small x86_64 Mac test, run under Rosetta, as the native reference. Cover ADDSS,
     SUBSS, MULSS, DIVSS, MINSS, MAXSS, SQRTSS, CVTSS2SD, CVTSD2SS, the packed PS forms, the SD
     forms, and FMA if reachable.
   - Use operand combinations of QNaN, SNaN, ±inf, 0, and normals, with distinct payloads and
     signs.
   - Run the same instruction bytes in Unicorn, using the existing venv's Unicorn 2.1.4 and the
     worker's Unicorn.
   - Record the full disagreement table.
   - Caveat: Rosetta is itself an emulator. Note where its results agree with the Intel SDM
     text; where SDM and Rosetta disagree, report it and do not pick a side silently.
2. **Patch.**
   - Copy the AEXCompat source (`/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat`)
     into `~/.cache/olm-emu/src-F29/` and never edit the original.
   - Patch the bundled Unicorn/QEMU softfloat NaN selection for the x86 target, using the
     smallest general rule that matches the SDM.
   - Build the worker into `~/.cache/olm-emu/worker-F29-ssenan/`. Record sha256 in
     `~/.cache/olm-emu/INDEX.json`, adding an entry and preserving the existing ones. Note the
     space-in-path gotcha: build outside the repo path.
   - Commit the patch file plus a build script into the repo at `tools/emulation/aexcompat_patches/`.
3. **Validate.**
   - The patched worker must match Rosetta/SDM on the step-1 table.
   - It must be byte-identical to the current default worker on all saved fuzz corpora
     (`tests/fuzz_corpus/*`, replay with `--worker <new>`) wherever no NaN is involved. List
     every changed case and show each one involves NaN propagation.
   - Rerun OLMBlur seed 1 n300 with the new worker and report the cases that move.
4. **Do not change the fuzzer default worker.** Propose the switch in `next`.

## Rules
- Use 1-2 processes. A Unicorn/Rust release build is heavy, so check `memory_pressure` first
  and do not build while it reports under 30% free.
- Delete build trees when done; keep only the final worker binary.
- No plugin code changes.

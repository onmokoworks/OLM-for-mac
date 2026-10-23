# C53b: RadialBlur nonfinite PF32 — build a Radial trace worker, then fix (continue C53)

## Facts
Read `orchestra/reports/C53-radial-nonfinite.md`, `F49-dblur-nonfinite-pf32.md` and `C49-radial-smart-r9.md`.
F49 built trace-enabled F46-equivalent workers (`~/.cache/olm-emu/src-F49-v2`, `worker-F49-trace-v2`) whose resident
watches are hard-wired to DirectionalBlur addresses. C53 confirmed all ten C49 Radial nonfinite inputs reproduce the
saved original hashes on those workers, but no Radial stage could be watched.

## Authorization (orchestrator)
- Copy `~/.cache/olm-emu/src-F49-v2` to `~/.cache/olm-emu/src-C53b/` and make the resident watches configurable
  (function/instruction addresses and plane sizes from the command line or a JSON file), so later tickets can reuse it
  for any plugin. Build in a space-free directory `~/.cache/olm-emu/build-C53b/` (delete it afterwards), install to
  `~/.cache/olm-emu/worker-C53b-trace/` and add an INDEX entry. Commit the patch and build script under
  `tools/emulation/aexcompat_patches/`. Never edit `04_Tools/AEXCompat*`. Arithmetic must stay F46-identical:
  prove the ten originals' output hashes are unchanged.

## Do
1. Bind traced outputs to the ten C49 originals (seed1 17/89/238/247 and the six seed 105 cases).
2. Find the first divergence vs paired Mac stages; implement grounded general SSE semantics with the
   `core/x86_float.h` `sse_*` helpers (as F49 did for DirectionalBlur).
3. Lift the finite gate only where proven: seed 1 + seed 105 + fresh seed n300 with 0 admitted mismatches,
   corpus preserved-exact, ASan/UBSan clean.
4. Missing-layer domain: report what the disassembly says; keep it refused unless proven.

## Rules
1-2 processes; `memory_pressure` >= 30% free before the Rust build. No other plugin changes; no gate/ledger changes.

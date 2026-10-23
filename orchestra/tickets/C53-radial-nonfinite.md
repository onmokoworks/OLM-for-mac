depends: F49-dblur-nonfinite-pf32

# C53: RadialBlur — nonfinite PF32 refusals (reuse the F49 trace worker)

## Facts
C49 left RadialBlur Smart refusals for nonfinite PF32 inputs (seed1 indices 17/89/238/247 and six seed 105 cases),
blocked on the same missing trustworthy stage capture as DirectionalBlur. F49 builds a trace-enabled F46-equivalent
worker (`~/.cache/olm-emu/worker-F49-trace/`) and NaN/Inf helpers. Read `orchestra/reports/C49-radial-smart-r9.md`
and `F49-dblur-nonfinite-pf32.md` first.

## Do
Use the F49 trace worker to find the first divergence on each input, implement the x86 NaN/Inf semantics generally,
and lift the finite gate only where proven (seed 1 + seed 105 + one fresh seed n300 with 0 admitted mismatches,
corpus preserved-exact, ASan/UBSan clean). Leave the missing-layer (null noise world) domain refused unless the
original's semantics are established from disassembly; document what you find there.

## Rules
1-2 processes. No other plugin changes; no release gate/ledger changes.

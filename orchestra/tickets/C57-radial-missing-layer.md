# C57: RadialBlur — missing noise-layer domain (last non-oracle Radial refusal)

## Facts
After C53b, RadialBlur Smart refuses AEX-renderable cases only when the noise layer parameter points to a missing/empty
layer (nullable Smart noise world). C49/C53b `next` sections say the original's checkout/allocation/null-branch semantics
are unknown. Read `orchestra/reports/C49-radial-smart-r9.md` and `C53b-radial-trace-worker.md`.

## Do
1. From the original AEX disassembly (Ghidra MCP is available; any disassembly of the original OLM is allowed), establish
   exactly what SmartRender does when the layer checkout returns no world / an empty world: branches, allocations, what
   memory is read, and whether that memory is initialised.
2. Use the configurable trace worker `~/.cache/olm-emu/worker-C53b-trace/` (see INDEX) to capture the original's planes
   for the refused witnesses and bind them to its public output.
3. If behaviour is deterministic, implement it and lift the refusal where proven (seed 1 + seed 105 + fresh seed n300,
   0 admitted mismatches, corpus preserved, ASan/UBSan clean). If it reads uninitialised memory, record it in
   `notes/KNOWN_ORIGINAL_BUGS.md`, propose deterministic semantics, and implement them only if the oracle agrees on
   all observed values.

## Rules
1-2 processes. No other plugin changes; no gate/ledger changes. Never edit `04_Tools/AEXCompat*`.

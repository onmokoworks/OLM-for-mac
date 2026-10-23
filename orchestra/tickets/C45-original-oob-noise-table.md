# C45: original OLM out-of-bounds noise-table reads (DirectionalBlur + RadialBlur): deterministic zero semantics

## Facts
- DirectionalBlur (C18, C25, C36): with negative Offset, the original reads the 404-byte noise
  table at negative indices (RVA 37f3/37f8, first reads at byte offsets -8/-12/-32). Six seed-1
  refusals (4/7/127/246/280/284) depend on this. The values observed under the emulator were
  `00000000`, with no valid-allocation guarantee.
- RadialBlur (C44): seven AEX-rendered noise-plane refusals reach negative table indices as well.
- On native Windows the bytes read there are whatever the heap holds, so the original's output in
  this domain is **not well-defined**. Bit-exactness against "Windows" is meaningless here.

## Orchestrator / user decision
Treat this as a known bug in the original. In the Mac port, an out-of-range noise-table read
returns **0.0f** (the value observed in the emulator), and the cases render instead of being
refused. Rationale: deterministic output, and the user gets no error.

## Do
1. In both plugins, replace the refusal for "sampled index outside the table" with a bounds-checked
   read that yields 0 outside `[0, table_len)`. Implement it at the read site; do not pad the
   allocation. Keep all other guards.
2. Measure against the default oracle, seed 1 plus two fresh seeds, n300 per plugin:
   - These cases should become exact wherever the emulator also read zeros. Report how many
     become exact, and list any that mismatch along with the emulator's non-zero values.
   - Mismatches in this specific domain are allowed *only* when you show the oracle read
     non-zero heap bytes at the out-of-range addresses. Record them in
     `notes/KNOWN_ORIGINAL_BUGS.md` (create it) as non-comparable, giving the plugin,
     parameters, and RVA.
   - All other cases: no exact may be lost, and 0 mismatches.
3. Add the witnesses to the corpora, rebaselining refusal → exact (or `known-original-bug`,
   if the fuzz tooling supports a tag; otherwise note it in the record's provenance).
- Use 1-2 processes. Do not touch the release gate/ledger.

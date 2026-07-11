# OLMRadialBlur Zoom Residual: Remaining Polar/Sampler Audit

Date: 2026-07-10  
Case: `case_0009`, 8bpc Zoom, Windows Software reference  
Scope: independent read-only audit; no source or CLI change

## Conclusion

The remaining `alpha=254` pixels at top-row `x={6,7,12}` are narrowed to the
**final polar cell population/collapse boundary**, with the exact ownership of
the alpha byte now binary-grounded. The evidence does not support a new global
sampler quantizer, a uniform cell offset, or a further trig-only explanation.

The most useful distinction is:

1. **Polar-plane generation:** still a live candidate only in the sense that
   full-size Windows cell IDs/values are missing. The AEX forward loop is known
   to use the exact paired helper and ordered scalar-float operations, and the
   exported exact AEX trig table plus float inverse still misses all three
   targets. This weakens, but does not fully eliminate, a full-size prefill or
   coordinate-state difference.
2. **Cell collapse:** the strongest remaining layer. The caller preserves the
   RGBA sampler return in a separate validity plane, then collapses that plane
   into final polar `+0xe.alpha` after scatter/prepass. A Windows final-plane
   cell set or collapse witness is absent, so the local `x=7` all-one cells do
   not prove Windows used the same cells.
3. **Sampler alpha ownership:** not an unresolved design choice. In the
   repeat-border path used by this case, the RGBA sampler owns RGB
   alpha-weighted normalization, but leaves alpha as the raw accumulated
   alpha; its separate return is a loose-window validity byte. The final
   inverse sampler normalizes RGB and accumulates alpha, but does not replace
   alpha with a new validity value. A global late alpha policy is therefore
   contradicted by the binary data and by the broad false positives in local
   truncation runs.

## FACT

### AEX polar generation

- `FUN_1800056f0+0x3a00` converts the angle index with `CVTDQ2PS`, multiplies
  by the float step, calls `FUN_18001d060`, then performs `MULSS`, `SUBSS`, and
  `ADDSS` in the source-coordinate construction. The direct instruction span
  is `disasm/OLMRadialBlur.aex.asm.txt:4410-4447`; the matching decompilation is
  `decomp/OLMRadialBlur.aex.c.txt:2490-2514`.
- `FUN_18001d060` is a paired sine/cosine helper with a polynomial/range path,
  not two independent platform-libm calls
  (`disasm/OLMRadialBlur.aex.asm.txt:26917-26932`).
- The exact helper table was exported for the actual `1800`-angle case grid and
  consumed by the local Zoom diagnostic. Combined with the recovered float
  inverse order, it produced `(6,0),(7,0),(12,0) = alpha 255` while the Windows
  reference is `254`; controls `(8,0),(24,0)` stayed `255`
  (`refs/conformance/olmradialblur_zoom_exact_aex_trig_table_probe_20260710.md:72-92`).
- The reduced `32x32/q90` direct AEX prefill comparison matched the Python
  prefill at the pre-worker boundary with `max_abs_diff=0.0`, but this is not a
  full-size `case_0009` final-plane witness
  (`refs/conformance/olmradialblur_zoom_direct_core_prefill_probe_20260708.md:163-173`).

### Sampler and caller ownership

- `FUN_180001520` (repeat RGBA sampler) clamps the four taps to image edges,
  accumulates alpha-weighted RGB, divides RGB by accumulated alpha, and returns
  a separate validity byte derived from the original loose integer-coordinate
  window. It does not rewrite the destination alpha to that validity byte. The
  live Ghidra decompile confirms this at the final normalization/return block.
- `FUN_180001270` (non-repeat RGBA sampler) instead writes
  `alpha_sum / geometric_weight_sum`; it also returns a separate success byte.
  This case's repeat-border path is selected by the caller when Repeat Border
  is enabled. The summarized ownership is recorded in
  `notes/OLMRadialBlur_ASM_FACTS.md:10-27`.
- In `FUN_180004640`, the RGBA sampler return is written to the independent
  validity plane at `+0xf252`. After prepass and scatter, the caller reads
  `+0xf252`: zero clears final polar RGB; nonzero normalizes RGB from the
  accumulation plane and writes that preserved value into `+0xe.alpha`.
  Only then does it call the inverse sampler. The decompilation shows this
  sequence in `decomp/OLMRadialBlur.aex.c.txt` around the `+0xf252` final
  normalization loop; the caller plane map and side-channel boundary are also
  recorded in `notes/OLMRadialBlur_ASM_FACTS.md:36-45` and its caller-collapse
  discussion.
- `FUN_180009d80` (final inverse sampler) performs four bilinear accumulations,
  normalizes RGB by accumulated alpha, and leaves accumulated alpha as the
  output alpha. It does not consult `+0xf252` directly; that ownership has
  already been collapsed into `+0xe.alpha` (`decomp/OLMRadialBlur.aex.c.txt:4918-4984`).

### Local residual facts

- Exact AEX trig plus float inverse misses all three target bytes and emits no
  control false positives. Paired platform trig and inverse-order variants also
  miss all three (`refs/conformance/olmradialblur_zoom_paired_trig_float_inverse_probe_20260710.md`).
- The current local final cells for `x=7` are all alpha `1.0`, while Windows is
  `254`. This is the discriminating witness: ordinary bilinear arithmetic on
  the currently selected cells cannot explain it
  (`refs/conformance/olmradialblur_zoom_case0009_prefill_coordinate_probe_20260709.md`).
- A local `polar-alpha` collapse exposes a plausible sub-one value for `x=6`
  (`0.9999999924`) and can produce `254` only with truncation, but global
  truncation changes `567071` pixels. It therefore identifies a possible
  collapse input, not a valid global writer rule
  (`refs/conformance/olmradialblur_zoom_case0009_quantize_boundary_probe_20260709.md:73-103`).
- The best tested uniform cell shift hits all three targets but adds eleven
  false positives, so it is not a credible cell-collapse rule
  (`refs/conformance/olmradialblur_zoom_case0009_cellset_candidate_20260709.md:9-17`).
- The latest Windows final-plane request is partial and contains no same-run
  cell IDs, per-cell floats, bilinear weights, or retained hook failure artifact
  (`refs/conformance/olmradialblur_zoom_case0009_local_candidate_rejection_20260709.md:15-21`).

## INFERENCE

- The exact AEX trig result removes the most obvious forward-grid mismatch, but
  not the possibility that full-size polar allocation, worker population, or
  coordinate state differs before the final four-cell lookup. That possibility
  cannot be ranked against collapse without Windows cell IDs.
- The `x=7` witness makes a pure final-sample arithmetic explanation unlikely:
  local selected cells are all `1.0`, yet the target is `254`. The likely
  binary-level fork is therefore either (a) Windows selected a different cell
  set containing a sub-one `+0xe.alpha`, or (b) Windows's preceding
  `+0xf252 -> +0xe.alpha` collapse produced a sub-one alpha from a different
  validity/accumulation state.
- `x=6` and `x=12` are compatible with the same collapse boundary, but their
  local near-one cells make them weaker discriminators than `x=7`. No evidence
  currently justifies assigning the residual specifically to polar generation
  versus worker/collapse population.
- No Mac implementation change, fixed offset, global truncation, or PNG-visible
  tuning is justified.

## One Next Proof

Run one narrow **Windows typed final-plane witness for `(7,0)`**, with the same
run also recording controls `(8,0)` and `(24,0)`. At each output pixel capture:

`inverse sample (x,y)`, the four final-polar cell IDs, each `+0xe` RGBA float,
the corresponding `+0xf252` value, bilinear weights, and pre-byte alpha.

This single witness separates the remaining layers: a different four-cell set
implicates polar population/coordinate generation; matching IDs with a
sub-one `+0xe.alpha` implicates collapse ownership/state; matching IDs and
all-one alpha would move the issue to the final byte path. The last outcome is
unlikely given the binary final sampler and prior `(6,0)` provenance, but the
witness should decide it rather than another local quantizer variant.

## Commands Run

```sh
rg --files refs/conformance notes decomp | rg 'OLMRadialBlur|olmradialblur|RadialBlur|asm'
sed -n '1,260p' refs/conformance/olmradialblur_zoom_exact_aex_trig_table_probe_20260710.md
sed -n '1,280p' refs/conformance/olmradialblur_zoom_paired_trig_float_inverse_probe_20260710.md
sed -n '1,320p' refs/conformance/olmradialblur_zoom_polar_cell_sequence_audit_20260710.md
sed -n '1,360p' notes/IR_OLMRadialBlur.md
sed -n '1,300p' notes/OLMRadialBlur_ASM_FACTS.md
nl -ba disasm/OLMRadialBlur.aex.asm.txt | sed -n '4410,4447p;26917,26932p'
nl -ba decomp/OLMRadialBlur.aex.c.txt | sed -n '2490,2515p;4918,4987p'
nl -ba refs/conformance/olmradialblur_zoom_case0009_prefill_coordinate_probe_20260709.md
nl -ba refs/conformance/olmradialblur_zoom_case0009_cellset_candidate_20260709.md | sed -n '1,41p'
nl -ba refs/conformance/olmradialblur_zoom_case0009_quantize_boundary_probe_20260709.md | sed -n '73,103p'
nl -ba refs/conformance/olmradialblur_zoom_case0009_local_candidate_rejection_20260709.md | sed -n '15,65p'
```

Additionally, the connected Ghidra MCP was queried read-only for
`0x180001270`, `0x180001520`, `0x180004640`, and `0x180009d80`.

## Changed Files

- Added only:
  `refs/conformance/olmradialblur_zoom_remaining_polar_sampler_audit_20260710.md`
- No code, decompilation, notes, existing reports, or other worktree changes
  were reverted or edited.

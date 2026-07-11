# OLMBlur full-worker case_0006 boundary audit

Date: 2026-07-10

## Scope

This audit covers the shared-core Mac AE residual reported at:

- `(1120,627)`, R expected `253`, actual `252`
- `(601,598)`, R/G remains the old residual

No source, core, ledger, NAS, or existing report was changed. The current
workspace's existing Mac report is treated as the image-level observation;
the binary boundary below is from the actual `plugins_2025/OLMBlur.aex`.

## Binary facts

`FUN_180005f20` (`0x180005f20`) performs these operations in the current AEX:

1. Render scale is `ctx+0x11c / ctx+0x120`. It scales the radius used to size
   the temporary planes and participates in the weight/decay calculation.
2. Input staging reads the world at `world+0x18`, with row stride at `+0x20`,
   width/height at `+0x24/+0x28`, and 16bpc at `+0x2c`. Each pixel is read as
   little-endian ARGB16: RGB words at offsets `+2/+4/+6` become float values
   directly, while alpha at `+0` becomes a byte validity flag.
3. For the mode-1 branch shown in the decompilation, each repeat performs six
   calls labelled `FUN_1800014f0` followed by six calls labelled
   `FUN_180001ea0`. The helper arguments change the source/destination plane
   offsets and pass origins; this is the pass-orchestration boundary, not the
   final writer. The repository's separate typed fixture identifies
   `FUN_180001000`/`FUN_180001980` as the non-Legacy helper pair, so the exact
   alias/branch mapping between those labels must be retained in the next
   witness rather than inferred from names.
4. The same worker obtains four PF Handle allocations. The observed sizes in
   the bounded Unicorn host-layout probe are `192`, `192`, `12`, and `16`
   bytes, followed by lock/unlock/dispose for all four handles.
5. The worker's 16bpc output path is downstream of the helper passes and
   writes short words after its final float result. The AEX instruction path
   uses float-to-integer truncation after the worker's `+0.5` adjustment;
   the Mac implementation's non-Legacy writer currently uses `nearbyintf`.

## Existing executable evidence

`python3 tools/emulation/test_olmblur_fullentry.py` returns successfully on an
8x2 synthetic 16bpc world. It records all four allocations and their complete
lock/unlock/dispose lifecycle and changes the synthetic output buffer. This is
actual AEX execution through `FUN_180005f20`, but it is not case_0006 evidence:
the dimensions, pixels, and host structs are synthetic, and the hook does not
retain per-pass buffers or a target-coordinate write witness.

The existing helper fixture separately compares the actual AEX helper outputs
for six typed fixtures. It establishes helper-scope arithmetic/ABI coverage,
not case-specific helper inputs or outputs at either requested coordinate.

## Classification

| Candidate boundary | Classification | Reason |
| --- | --- | --- |
| Helper arithmetic | not established for these pixels | The helper fixture is exact for typed synthetic inputs, but no case_0006 input/output plane was captured at either coordinate. Do not retune the helper from PNG bytes. |
| Helper input/output staging | still open, highest-value upstream split | The AEX staging contract is known, but the requested pixels lack captured ARGB16 input words, alpha flags, and helper-plane values. A one-word input or validity difference can propagate to a sparse output residual. |
| Pass orchestration | possible but currently unproven | The AEX has repeated offset/origin calls and scale-derived dimensions. A target-coordinate pass map is missing, so the new point cannot be assigned to a particular horizontal/vertical pass. |
| Float scale/weight path | possible but not isolated | The AEX uses `CVTTSS2SI` for radius/dimension conversions and `DIVSS/MULSS` for scale/weight setup. Mac and AEX formulas look structurally comparable, but no target pre-store float exists. |
| 16bpc writer | not supported as the sole explanation | The old `(601,598)` R/G residual is consistent with a one-word boundary, but the new `(1120,627)` R-only residual has no retained pre-store float or 16-bit word witness. The current image-level report is insufficient to distinguish a writer delta from an upstream float delta. |

**Decision:** classify the new residual as `fullworker-boundary-unresolved`,
with the next split ordered `staging/helper-plane -> pass/scale -> pre-store
float -> 16bpc writer`. No PNG tuning or source change is justified.

## Next witness contract

Capture one same-run record for both `(1120,627)` and `(601,598)` on the
Windows current AEX or an equivalent locally emulated full-worker run. The
record must retain:

- AEX SHA-256, entry `FUN_180005f20`, AE/renderer, 16bpc, and exact case
  parameters;
- `ctx+0x11c/+0x120`, `world+0x18/+0x20/+0x24/+0x28/+0x2c`, and the source /
  destination base pointers;
- staged source ARGB16 words and alpha-validity byte for each target and every
  source tap consumed by the target's horizontal and vertical passes;
- for each of the six horizontal and six vertical calls per repeat: source
  plane, destination plane, origin/offset arguments, radius, weight sum,
  sample count, and target-plane RGB float triplet after the call;
- the final RGB float triplet immediately before 16bpc conversion, its raw
  IEEE-754 bits, the `+0.5`/conversion intermediate, and the stored 16-bit RGB
  words at both coordinates;
- final exported PNG RGBA16 words, with an explicit proof that PNG channel
  order is R/G/B/A while the worker world is A/R/G/B.

Interpretation is then mechanical:

- staged words or validity differ: input/staging;
- staging matches but a pass plane first differs: helper input/output or pass
  orchestration;
- all pass outputs match but pre-store float differs: scale/weight or final
  float path;
- pre-store float matches and only stored words differ: 16bpc writer;
- stored words match but PNG differs: export/writeback path.

## Host limitation

A fresh AE debug attempt for these exact coordinates failed before rendering
with `osascript` error `-609` (invalid After Effects connection). No debug file
from that attempt is evidence. Full-frame Unicorn execution remains
impractical under the existing 30-second cap, so a new case-bound executable
fixture cannot currently satisfy this contract without an independently
grounded crop/origin rule.

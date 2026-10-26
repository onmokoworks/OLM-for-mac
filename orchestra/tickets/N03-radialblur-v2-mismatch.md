# N03: RadialBlur realistic-v2 Smart mismatches (nightly 2026-10-25), traced with the F54b worker

## Facts
- `orchestra/reports/N02-radialblur-nightly-20261025.md`: two realistic-v2 (cropped checkout) Smart mismatches reproduce byte-for-byte and are recorded in a labelled "unresolved" corpus set. The C53b trace worker rejects geometry arguments, and geometry-stripped probes crash before the watched stages.
- `~/.cache/olm-emu/worker-F54b/` (AEXCompat upstream: geometry + cropped checkout + 4K + F49 generic watches; equal to F53 on all corpora) can watch the original **with** the cropped geometry.

## Do
- Using F54b watches, dump the original's polar/source-scalar planes, prepass, accumulator and final float plane for both witnesses (stages as in R06/C53b). Compare them with Mac's stages under the same geometry, and find the first differing stage. Fix it in the general path, keeping the P05b/P07e exact SIMD/threading and the R10 reference split.
- Acceptance:
  - both witnesses are exact;
  - realistic-v2 seeds 1/2/3 n200: 0 mismatches and 0 Mac-only refusals;
  - default seed 1 n300: no exact→non-exact;
  - all corpora replay true (move the witnesses from the unresolved set into a normal labelled set, with both routes);
  - `ref_vs_fast` is clean at caps 1/2/8.
- If the original reads undefined memory, document it as P06a/C57 did.

## Rules
- Use 1-2 processes. Change only RadialBlur sources. Do not touch the release gate or ledger. Build workers only as described in BRIEF.md. The stop rule applies.

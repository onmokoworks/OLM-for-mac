status: partial

summary:
- Closed the Smart typed-input alignment cluster: stage active rows into correctly typed aligned storage before admission probes and rendering.
- Seed 1 Smart exact 108→168; fresh seed 3 exact 113→166. All 221 prior exact hashes are preserved; no newly admitted mismatch.
- 600 sanitized Smart campaign replays and 72 independent layout renders are clean; eight existing smoke tests pass.
- Corpus 35/35 is unchanged, so no expectation rebaseline is needed.
- Angle and remaining Zoom/Rotation refusal clusters are still under investigation; this commit closes one general cause.

facts:

Base `ad206f00`, branch `orch/C06-radial-smart`. Read AGENT_GUIDE, the RadialBlur ledger row, compatibility plan, GOTCHAS, T01/T03/T05/F08/F13/F18 and F10/F12 methodology. MAIN, original AEX, SDK, emulator sources and cache were read-only. No release gate, ledger, installation, worker build, push, history rewrite, or `/tmp` writes.

Reference worker: `/Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker`, SHA256 `93622cbc412f31a094f34da4555eb1023231f26f560869924b9faab28ec4f7ed`. Original AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`. Starting source SHA256 `347c9fd41c3ca6fcc9146efd5b60b5985e86c0c34b31d0309ef488847f01e2db`; alignment source `1d7374fc4fc07f5b5e55517cde3b552d5186bcb957f0d5f6b8da295e7084022e`.

All campaigns used MAIN `tools/emulation/.venv/bin/python`, `tools/fuzz/run.py --plugin radialblur --n 300 --seed {1,3} --jobs 2 --case-timeout 30 --budget-minutes 120 --worker <worker>`, with separate `--scratch`, `--corpus`, and `--report` below `orchestra/state/C06-radial-smart`. The first baseline used default shrinking; later diagnostic campaigns used `--shrink-attempts 0 --shrink-seconds 0` because Classic mismatch reduction is unrelated to the target Smart route. Every subprocess log was redirected there.

| Campaign | Smart exact | mismatch | refusal | Original Smart ok/reject/budget |
|---|---:|---:|---:|---|
| Seed 1 before | 108 | 0 | 192 | 279/20/1 |
| Seed 1 alignment | 168 | 0 | 132 | 279/20/1 |
| Seed 3 before | 113 | 1 | 186 | 279/18/3 |
| Seed 3 alignment | 166 | 1 | 133 | 280/18/2 |

The original-renderable baseline refusals were Zoom profile 86, generic world 62, Rotation profile 12, Type3 zero noise 5, two-stage 2, Smart budget 2, Zoom noise/inner 1, and host 1. A six-tag gate-off experiment completed 300 cases: Smart 132 exact / 144 mismatch / 14 refusal / 10 uncompared. No bypass is enabled in production. Of the 60 seed-1 promotions, 26 previously hit Zoom profile, 33 generic world and one Zoom noise/inner. This is one storage/dispatch cause spanning three guard labels, not three independently closed algorithms.

Smart already stages its destination but passed the original byte-strided input directly to typed admission/render code. `IsGenericBaselineWorldPair` rejected odd typed rowbytes; fallback probes also bound misaligned references before refusing. The new source byte-copies active input rows into PF16 or PF32 vectors when the base address or rowbytes needs alignment. No-op byte copies retain their original path. Original overlap/full-frame/format checks and checkins still refer to the checked-out worlds. Publication remains atomic. The generic budget includes the additional input allocation; the existing budget test now checks its exact byte increment.

An initial generic-controls-only staging experiment had 300/300 identical seed-1 outcomes, but sanitizer reported misaligned PF16 reference bindings in refused cases 123, 173 and 235 at the size-factor input probe (line 1726). Applying staging before all Smart typed probes removed these reports. Final separately compiled O2 and ASan/UBSan executables reproduce all 600 campaign outcomes/hashes; all 600 sanitizer replays are clean. The independent matrix is two geometries × PF16/PF32 × Zoom/Rotation × three active strength/offset/fade profiles, with packed, 1/5-byte, and 3/11-byte input/output padding: 24 original Smart references, 72 exact sanitized Mac renders. Input/padding preservation and checkout/checkin checks are enforced by the existing harness.

Seed 3 index 46 is a **pre-existing** Smart mismatch, unchanged in both builds: three words/three bytes, first word 1031 (byte 4124), original `66a7df3e`, Mac `67a7df3e`; Mac SHA256 `66f28d337094f38b0a8096208c20e10d22ae38833192b214070e0e6d1ad388f3`. This is not included among newly admitted cases or called exact.

Corpus replay before/after: 35/35 `matches_saved`, all 35 Smart exact hashes unchanged; Classic results also unchanged. Rebaseline table: 35 exact→exact, zero changed rows. Eight existing RadialBlur generic baseline, sanitizer, budget, Type3, Smart contract, size/noise and typed geometry tests pass. `git diff --check` passes. Machine evidence is `C06-alignment.evidence.json`, including input hashes, complete transitions, source/reference bindings, sanitizer outcomes and smoke results. The final typed-buffer source was independently replayed against both measured campaigns in ordinary and sanitized builds; their intermediate source identities remain explicitly recorded rather than overwritten.

inference:

The refusal reduction comes from restoring the input storage contract before existing general algorithms, not relaxing numerical comparisons or selecting output values. The retained original worker receives packed input; these experiments establish Mac odd-stride equivalence to that original packed render, not native Windows odd-stride support. This is bounded CPU-emulator evidence, not native AE/UCRT conformance or a claim about arbitrary remaining profiles.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `tests/test_olmradialblur_generic_budget_20260821.py`
- `tools/fuzz/verify_radialblur_smart_C06.py`
- `tools/fuzz/summarize_radialblur_smart_C06.py`
- `orchestra/reports/C06-alignment.evidence.json`
- `orchestra/reports/C06-radial-smart.md`

verify:

Run at this commit from the worktree root:

```sh
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
export TMPDIR="$PWD/orchestra/state/C06-radial-smart/recheck-alignment"
mkdir -p "$TMPDIR"
PYTHONDONTWRITEBYTECODE=1 "$py" -u tools/fuzz/verify_radialblur_smart_C06.py \
  --evidence orchestra/reports/C06-alignment.evidence.json --independent --smoke \
  --output "$TMPDIR/verify" > "$TMPDIR/verify.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 "$py" -u tools/fuzz/run.py --plugin radialblur \
  --n 300 --seed 1 --jobs 2 --case-timeout 30 --budget-minutes 120 \
  --worker /Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker \
  --scratch "$TMPDIR/fuzz" --corpus "$TMPDIR/corpus" --report "$TMPDIR/fuzz.json" \
  > "$TMPDIR/fuzz.log" 2>&1
PYTHONDONTWRITEBYTECODE=1 "$py" -u tools/fuzz/run.py --plugin radialblur \
  --replay tests/fuzz_corpus/radialblur --case-timeout 30 --budget-minutes 60 \
  --worker /Users/onmk/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker \
  --scratch "$TMPDIR/replay" --report "$TMPDIR/replay.json" > "$TMPDIR/replay.log" 2>&1
git diff --check
```

Expected: verifier pass, 600 identical/clean Smart outcomes, 72 independent exact renders, 8/8 smoke tests; seed-1 Smart 168 exact / 0 mismatch / 132 refusal (oracle timeouts can vary); corpus 35/35 matching. The fuzz runner's nonzero status for diagnostic Classic mismatches is separate from Smart acceptance.

next:
- Continue the ticket with the largest remaining Zoom refusal subclusters (Angle domain and Repeat Border), preserving this exact set.
- Investigate fresh-seed index 46's retained three-word mismatch separately if it becomes the selected cluster.

status: partial

summary:
- Closed the PF32 finite-SDR, non-Legacy default-schedule small-frame refusal cluster.
- Seed 1 Smart 102/13/185 -> 110/13/177; fresh seed 4 103/8/189 -> 109/8/183 (exact/mismatch/refusal).
- All 205 baseline-exact campaign cases, Classic results and 39 saved corpus results are unchanged; newly admitted cases are exact.
- 192 independent PF32 SDR cases, 1,200 sanitized campaign routes, 78 sanitized corpus routes and 12 retained fixtures pass.
- PF16 and PF8 default-schedule clusters remain for the next separate commits.

facts:

Base: `99aafc300203ca9ee3de7f3c8e4bfdafc497995b`, branch `orch/C10-olmblur-smart-r2`. Read AGENT_GUIDE, plugin ledger restrictions, GOTCHAS, compatibility plan and T09/F15/F17/F18/C05 plus F10/F12 methodology. MAIN, original AEX, external emulator and cached workers remain read-only. No release gate, ledger, other-plugin, installed bundle, history or push changes. All temporary files are under this ticket's scratch.

Machine evidence: `reports/fuzz/olmblur_admission_C10_pf32.json`. The original MAIN AEX SHA256 is `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`; the INDEX worker is `/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker`, SHA256 `9ac2c86cb707e23de7c360c128d61b14d0b4c3b71b417baa3e7e116fe6af42b7`. Source, core and candidate hashes are in the evidence. No numeric core was changed.

Measured commands used `run.py --plugin olmblur --n 300 --seed {1,4} --jobs 2`, scratch corpora, shrinking disabled. Gate-off uses the C05 diagnostic wrapper before editing, with ASan/UBSan. Production sanitizer runs use the C10 wrapper, `-fsanitize=address,undefined -fno-sanitize-recover=all`, abort on error, leak checking disabled.

| Seed / build | Smart exact | mismatch | refusal | sanitizer abort |
|---|---:|---:|---:|---:|
| 1 baseline | 102 | 13 | 185 | 0 |
| 4 baseline | 103 | 8 | 189 | 0 |
| 1 gate-off | 257 | 41 | 0 | 2 |
| 4 gate-off | 275 | 25 | 0 | 0 |
| 1 PF32 ordinary and sanitized | 110 | 13 | 177 | 0 |
| 4 PF32 ordinary and sanitized | 109 | 8 | 183 | 0 |

Classic remains 13/0/287 (seed 1), 20/0/280 (seed 4). All 600 AEX Smart calls succeed. The verifier checks every input hash, original-route result, Classic result, existing exact bytes, every newly admitted output against both the original Smart output and gate-off output, and equality of ordinary/sanitized result objects. It rejects any change other than refusal -> exact.

**General rule, not input matching:** small PF32 frames with Amount exactly 5, Repeat 2, Legacy off, either Bias, any legal raw Smoothness, and all source ARGB samples finite in [0,1]. Signed zero is admitted. Existing geometry, storage, work, full-frame, downsample, callback and exact-fixture precedence rules remain. The source scan runs only after storage validation and uses memcpy for odd byte strides. The normal worker runs unchanged.

Static basis: MAIN `decomp/OLMBlur.aex.c.txt`, `FUN_180004b80` (line 1968), `FUN_180002280` (789), `FUN_180003710` (1379) implement the separate typed non-Legacy workers. Their decay is powf(3/Amount,1/(Repeat-1)); at the default schedule the two iteration powers are 0 and 1. Smoothness does not enter this non-Legacy calculation. `FUN_180009b40` materializes Amount as float and Smoothness as the signed high word, as already repaired by C05. This admission does not assert arbitrary Amount/Repeat libm equivalence.

**Boundary discovered:** `verify_blur_small_C10.py --diagnostic` gives 727 exact / 9 mismatch, sanitizer clean: PF8 240/240, PF16 240/240, finite PF32 240/240, nonfinite PF32 7/16. First nonfinite failure is matrix index 727, PF32 1x23, 39 differing bytes / 10 words, byte 100: AEX `2143c5ff`, Mac `4523c17f`. These are distinct NaN payloads. No paired intermediate stage is claimed and no numerical correction was made. All nonfinite PF32 inputs remain outside the additional admission, including the seven accidental exact cases. Signed/HDR finite inputs also remain outside this bounded rule despite their matrix successes.

The independent matrix uses eight geometries from singleton/rows/columns through 24x24, both Bias values, Smoothness 1/62.5/100, random/edge/opaque/transparent/wide typed sources and odd padding. PF32 production: 192 exact / 64 refusal. Including existing integer singleton admissions, the complete matrix is 252 exact / 484 refusal, all as expected. Separate one-away Amount/Repeat/Legacy and per-channel SDR-domain boundaries: 2 existing integer single-pass exact / 41 refusal, all as expected. These checks validate source/padding preservation, no output writes on refusal and balanced host callbacks.

Corpus before/after table:

| Smart status | Before | After | Action |
|---|---:|---:|---|
| exact | 15 | 15 | byte-identical |
| mismatch | 11 | 11 | unchanged |
| refusal | 13 | 13 | unchanged |

Sanitized strict replay: 39/39 matches_saved, 78 route executions. Retained original 24x24 depth/Legacy fixtures with optional checkin present/absent: 12/12 pass (active bytes, padding, guards, callbacks). Existing Classic/generic unit checks: 7 tests OK. `git diff --check` passes. The one source-text assertion was updated for the expanded admission predicate.

inference:

- These gate-off, fresh-seed, independent typed matrices and unchanged worker branches support the bounded default-schedule admission. They are not all-input equivalence, native Windows UCRT/AE, installed Mac AE, GPU or ROI proofs.
- PF32 nonfinite propagation is an observed output boundary; its first divergent arithmetic operation remains unlocated. This refutes unrestricted PF32 admission and supplies a new boundary, rather than concealing a mismatch.
- PF32/PF16/PF8 are separate typed-worker refusal clusters and will be committed separately as requested. The pre-existing mismatch clusters are not claimed closed.

changed_files:
- `mac/OLMBlur/OLMBlur.cpp` — bounded default-schedule PF32 admission and source-domain guard.
- `tests/test_olmblur_generic_beta_lane_20260820.py` — updated existing admission assertion.
- `tools/fuzz/blur_admission_campaign_C10.py` — revision/sanitizer/gate-off campaigns.
- `tools/fuzz/verify_blur_small_C10.py` — deterministic independent and negative boundary matrices.
- `tools/fuzz/verify_blur_admission_C10.py` — monotonic campaign/corpus verification and retained controls.
- `reports/fuzz/olmblur_admission_C10_pf32.json` — measured per-commit evidence.
- `orchestra/reports/C10-olmblur-smart-r2.md` — this report.

verify:

Run at this commit from the worktree; logs, builds and generated corpora stay in ticket scratch. Before source can be reproduced with `--blur-source-revision 99aafc300203ca9ee3de7f3c8e4bfdafc497995b`. The core is unchanged. Production commands:

```sh
s="$PWD/orchestra/state/C10-olmblur-smart-r2"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_noop_highdepth_reference_20261002/target/release/aex-guest-worker
for seed in 1 4; do
  python3 tools/fuzz/run.py --plugin olmblur --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/pf32-$seed.json" --corpus "$s/pf32-$seed-corpus" > "$s/pf32-$seed.log" 2>&1
  python3 tools/fuzz/blur_admission_campaign_C10.py --blur-sanitize --plugin olmblur --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --worker "$w" --scratch "$s" --report "$s/pf32-san-$seed.json" --corpus "$s/pf32-san-$seed-corpus" > "$s/pf32-san-$seed.log" 2>&1
done
python3 tools/fuzz/verify_blur_small_C10.py --scratch "$s" --report "$s/matrix-pf32.json" --require-exact > "$s/matrix-pf32.log" 2>&1
python3 tools/fuzz/verify_blur_small_C10.py --boundary-only --scratch "$s" --report "$s/boundaries-pf32.json" --require-exact > "$s/boundaries-pf32.log" 2>&1
python3 tools/fuzz/blur_admission_campaign_C10.py --blur-sanitize --plugin olmblur --jobs 2 --replay tests/fuzz_corpus/olmblur --worker "$w" --scratch "$s" --report "$s/pf32-replay.json" --corpus "$s/replay-corpus" > "$s/pf32-replay.log" 2>&1
PYTHONPATH=tests python3 -m unittest test_olmblur_generic_classic_beta_20260822 test_olmblur_generic_beta_lane_20260820 > "$s/tests-pf32.log" 2>&1
git diff --check
```

Expected: campaign table above, matrices 252/484 and 2/41 exact/refusal, strict replay 39/39, seven tests OK. `verify_blur_admission_C10.py --scratch "$s" --report "$s/recheck-pf32.json" --before before --after pf32 --base 99aafc300203ca9ee3de7f3c8e4bfdafc497995b --admitted-depths 32` combines the saved before/gate-off campaigns and these new outputs; expected new exact 8/6, retained 12/12. Reproduce missing before/off reports using the campaign wrapper with the base revision, `--blur-small-off --blur-sanitize` for off, and corresponding `before-{1,4}`, `off-{1,4}`, `before-replay` report names. The nonfinite diagnostic matrix is regenerated with `--diagnostic` and no `--require-exact`; expected 727 exact / 9 mismatch.

next:
- Promote the independently exact PF16 then PF8 default-schedule small-frame branches in separate commits, preserving monotonic corpus expectations and sanitizer cleanliness.
- Keep broad small-frame admission, PF32 nonfinite propagation, Legacy exceptional-value conversion, and nondefault repeated-schedule residuals unresolved.

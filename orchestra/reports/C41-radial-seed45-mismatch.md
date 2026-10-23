status: done

summary:
- Outcome A: restore Rotation's size-only prepass factor when both Edge Fade spans are zero.
- The seed45 case8 witness becomes raw-exact; no admission restriction was added.
- Paired original-AEX planes isolate the first divergence to pre-accumulation, and every captured plane is exact after the fix.
- Seeds1/44/45/46 n300:1054 Smart exact,140 refusals,6 uncompared, zero mismatches; all1053 baseline exact cases retained.

facts:
- Starting commit: `1ff606b05ea8cf1599442ede1d717ddc29425088`, branch `orch/C41-radial-seed45-mismatch`.
- Read `AGENT_GUIDE.md`, emulation GOTCHAS, the compatibility plan, Radial ledger rows, and C39's report. No release gate, ledger, other plugin, MAIN, or emulator-source modification; no worker rebuild, push, stash, history rewrite, or delegation.
- F45 reference worker: `/Users/onmk/.cache/olm-emu/worker-F45-msdouble/aex-guest-worker`, SHA256 `8849565128e4147bb39b145bf392e20da1983c476498ca4448001ea278a38409`. AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Before: PF8 Rotation 12x21 witness differs at one byte, offset1000, reference `e4`, Mac `a8`. Reference SHA256 `9238ffef5cad5f2efe79b29bcf349cc34cc532ac563b2d4289d9729ec5f56049`; Mac `9578c539714e8ef47a83c67acd6806cc674097b7158c5904947c271e0f382ea4`.
- F45 trace attempt exited1: retained stderr establishes `unknown watch field: "offset"`. This is a CLI capability failure, not a tool permission rejection or a refuted numerical hypothesis. The retained `radial_offset_reference_20261002` worker supports the watches; its public output hash equals F45 for this witness. Its provenance/hash is in `C41-evidence/planes-before.json` and `planes-after.json`. No worker rebuild was needed.
- Before trace: 1800x15 polar grid; polar108000 words, scalar27000 words, and source span252 words all exact. Pre-accumulation differs at400 words /100 cells; premax differs at100 words. First differing premax word20115: AEX `cfe3293e` (0.165908083319664), Mac `00000000`. The corresponding scatter scalar is zero on both sides. Normalized plane differs at400 words. See committed paired plane hashes/first differences.
- Static original AEX: RVA `0x287c` loads the size-factor argument through RBP (derived from R9); `0x2892..0x2895` tests it for zero before processing fade spans. This test is unconditional on the fade span values. The Mac used its noise-composed scatter scalar as the factor when both fades were zero.
- After trace: size-only factor27000 words, polar108000, scalar27000, span252, preaccum108000, premax27000, accum108000, max27000, normalized108000: zero differing words in every plane. Smart output SHA256 equals the reference above. The correction is general factor selection, with no output-coordinate or final-byte changes.
- Source editing initially changed the identically spelled Zoom declaration too; that accidental edit was reverted before final verification. The final diff modifies only Rotation. Seed1/44/45 discovery runs include an intermediate source snapshot; their retained original-AEX hashes are reused by `verify_radialblur_C41.py` to render every case again with the final source and starting baseline. Seed46 uses the final source. Evidence preserves discovery provenance rather than relabeling it.
- `probe_radialblur_C41.py` initial run exited1 because its assertion wrongly required Size100 cases to be admitted: actual results were18 exact and9 refusals, zero mismatches. Corrected the probe to compare baseline admission, then reran:12 mismatch→exact,6 exact→exact,9 refusal→refusal across PF8/PF16/PF32, Size0/witness/100 and Noise0/witness/100. No numerical hypothesis was refuted.
- Witness replay/rebaseline: only `seed45_case000008_C39.json` changed, using production-rebaseline history. Smart mismatch→exact; Classic stays mismatch with updated candidate bytes. Full corpus replay:36/36, `replay_matches_saved=true`, exit0. This does not claim Classic conformance.
- All campaigns use `--jobs 1`, F45, n300, max-size256, default10s case timeout, zero shrink attempts. Fresh seed is46. Oracle timeouts and refusals are recorded separately from exact comparisons; finite CPU-emulator results do not establish native Windows/AE or all-input compatibility.

- Final-source per-case comparison exited0 over1200 cases: baseline1053 exact/1 mismatch/140 refusal/6 uncompared; final1054 exact/0 mismatch/140 refusal/6 uncompared. Exact-case cost:0. Per-seed final exact/refusal/uncompared:1=257/40/3,44=264/35/1,45=258/40/2,46=275/25/0. The only campaign transition is seed45/index8 mismatch→exact. Committed campaign files preserve original-AEX hashes for all1200 generated inputs; `comparison.json` preserves every baseline/current result.
- `git diff --check` and AST parsing of all changed Python tools pass. All launched command sessions completed; regenerable build trees removed, scratch remains below5GiB. No tool permission rejection occurred.

inference:
- The size-only factor must remain distinct from the noise-composed scatter factor even without edge fading, because the original prepass also uses it as an eligibility gate. This accounts for the entire observed divergence and the independent boundary improvements.
- Equal final hashes between F45 and the offset-watch worker bind this witness's trace to the public result; they are not proof of general equivalence between workers.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `tools/fuzz/trace_radialblur_rotation_C11.py`: bounded watch batches, retained stderr, worker selection, corpus input, default-zero angle omission, size-factor plane capture.
- `tools/fuzz/probe_radialblur_C41.py`: depth/size/noise boundary comparison against starting baseline.
- `tools/fuzz/verify_radialblur_C41.py`: per-case baseline/final Smart comparison against captured campaign oracle hashes.
- `tests/fuzz_corpus/radialblur/seed45_case000008_C39.json`
- `orchestra/reports/C41-evidence/*` and this report.

verify:
Run from this worktree. Use a fresh scratch subdirectory for each invocation that builds.
```sh
s="$PWD/orchestra/state/C41-radial-seed45-mismatch/recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/fuzz/verify_radialblur_C41.py --reports orchestra/reports/C41-evidence/campaign-{1,44,45,46}.json --scratch "$s/comparison" > "$s/comparison.log" 2>&1
python3 tools/fuzz/probe_radialblur_C41.py --scratch "$s/boundaries" > "$s/boundaries.log" 2>&1
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --jobs 1 --scratch "$s/replay" --report "$s/replay.json" > "$s/replay.log" 2>&1
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/fuzz/trace_radialblur_rotation_C11.py --fixture tests/fuzz_corpus/radialblur/seed45_case000008_C39.json --output "$s/planes" > "$s/planes.log" 2>&1
git diff --check
```
Expected: all commands exit0; no current Smart mismatch or lost exact case; boundary transitions12/6/9 as above; corpus36/36 matches; every captured plane zero differing words and witness exact.

For independent fresh oracle campaigns (serial):
```sh
for seed in 1 44 45 46; do
  python3 tools/fuzz/run.py --plugin radialblur --seed "$seed" --n 300 --jobs 1 --shrink-attempts 0 --scratch "$s/seed-$seed" --corpus "$s/generated-corpus" --report "$s/seed-$seed.json" > "$s/seed-$seed.log" 2>&1
done
python3 tools/fuzz/verify_radialblur_C41.py --reports "$s/seed-1.json" "$s/seed-44.json" "$s/seed-45.json" "$s/seed-46.json" --scratch "$s/fresh-comparison" > "$s/fresh-comparison.log" 2>&1
```
Expected:300 completed per seed, zero Smart mismatches, zero baseline exact losses. Timing-dependent oracle budgets may vary; do not reinterpret uncompared cases as exact. Corpus discovery is redirected to scratch; only the named existing witness was rebaselined.

next:
- No admission fallback needed. Existing Classic mismatches and oracle-budget/uncompared cases remain outside this ticket's closure.

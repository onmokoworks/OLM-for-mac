status: done
summary:
- Closed one Smart cluster: Smoother2 inverted-key palette comparisons rejected unordered NaN channels that the original COMISS branches accept.
- Smoother2 seed 1 stays 300/300 exact; seed 2 improves 299/300 -> 300/300; seeds 3–6 stay 300/300 each.
- ColorKeep and ToonDilate fresh seeds 2–6 each measure 1,500/1,500 Smart exact, with no Smart refusal.
- All 1,807 base-exact Smoother2 cases are byte-identical; corpus 8/8 matches_saved; 1,808 public cases and 2,744 palette boundaries are ASan/UBSan clean.
- The requested fresh campaigns exposed only this one Smart cluster; no further sampled Smart residual remains. No native AE claim.

facts:

Base: `310b543d` on `orch/C23-smoother2-colorkeep-toondilate-fresh`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, relevant ledger rows, T08/T12 and C01/F19/F21 reports. MAIN, original AEX, cache and emulator source remained read-only. No release gate, ledger, other-plugin production code, installed host, stash, push or history rewrite was changed. All runs used jobs 1 and at most two concurrent worker/build processes. Scratch and compiler temporary paths were ticket-local.

Identities:
- Indexed worker: `/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker`, SHA256 `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2`. Used as-is, no rebuild. This differs from C01's historical containment worker; this ticket's before/after comparison uses the same indexed worker throughout.
- Smoother2 original AEX SHA256: `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
- Before source SHA256: `e5ab723f375bd919297cfffa382e242dba0c35d268ff3444de69fa47a9c19a64`.
- After source SHA256: `07ee9d2009bc8e2b8e262dcf88291f06245b1e0af271d80e1af72d1575dbabf1`.
- Acceptance JSON SHA256: `ac5f3e85681aa393185f584e09ab3680585fbb3865a3882967b6fa8ba16a01c6`.

**Commands actually run.** The initial seed-1 campaign used `python3 -B tools/fuzz/run.py --plugin olmsmoother2 --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --worker "$w" --scratch "$s" --report "$s/olmsmoother2-seed1.json" --corpus "$s/olmsmoother2-seed1-corpus"`, with `$s` and `$w` as in verify below, and redirected its log to `$s/olmsmoother2-seed1.log`. Exit 0, 300 Smart exact. `bash tools/fuzz/run_C23_fresh.sh` then ran seeds 2–6 for all three plugins sequentially, all 15 campaigns complete/exit 0. The committed runner now includes the initial Smoother2 seed-1 command too. `python3 -B tools/fuzz/summarize_C23_fresh.py` exited 0 and committed compact provenance, input/output hashes, counters and the full sole Smart residual in `C23-fresh-census.json`.

| Population | Before Smart exact / mismatch / refusal | After Smart exact / mismatch / refusal | Changed cases |
|---|---:|---:|---:|
| Smoother2 seed 1 | 300 / 0 / 0 | 300 / 0 / 0 | 0 |
| Smoother2 seed 2 | 299 / 1 / 0 | 300 / 0 / 0 | 1 |
| Smoother2 seeds 3–6 (each) | 300 / 0 / 0 | 300 / 0 / 0 | 0 |
| Smoother2 retained corpus | 8 / 0 / 0 | 8 / 0 / 0 | 0 |
| ColorKeep seeds 2–6 (each; production unchanged) | 300 / 0 / 0 | same measured code | 0 |
| ToonDilate seeds 2–6 (each; production unchanged) | 300 / 0 / 0 | same measured code | 0 |

ColorKeep's Classic mismatches/refusals remain recorded separately in the census. Smoother2 Classic refuses all sampled cases; ToonDilate Classic is no-write. These do not enter the F18 Smart closure count. No corpus expectation was rewritten or rebaselined: the before/after corpus table is unchanged, and standard replay with explicit indexed worker override reports 8/8 `matches_saved`.

**First divergent stage and general cause.** Seed 2/index 273 is PF32 nonfinite, 19x15, input SHA256 `72d148152aaf61d7a62a43e758a2bbdb06efbc056548b74be7614f1b8419273d`. Final output before: 4 bytes / 1 word differ; first byte 1328, word 332, pixel (7,4), AEX alpha little-endian `ae47413f`, Mac `00000000`. Source RGBA words at that pixel are `ff812346,7fc12345,ff812346,3f800000`.

The paired probe establishes byte-identical PF32 unpack, then executes original `FUN_180002930` with the retained descriptor and palette ABI. First difference is post-key/pre-gamma alpha: AEX `0000803f`, Mac `00000000`, first differing byte 1342, two differing bytes. Class plane then differs at eight bytes; Mac's polygon is empty while AEX has twelve vertices. Original disassembly at `0x1800029fa/0x180002a0c` uses COMISS followed by JNC to reject ordered greater/equal differences, and `0x180002a1e` uses COMISS/JC for the final component. Unordered comparisons set carry and pass each component. Replacing three `< tolerance` expressions with `!(difference >= tolerance)` preserves finite comparisons and restores this NaN behavior. No output-byte correction or case/coordinate specialization is present.

`C23-key-stages-before.json` and `C23-key-stages-after.json` retain all boundaries and hashes. Afterward pre-setup, pre-gamma, class plane, center, polygon, c0d0, ab00 and b120 match. The reconstructed core's **entire typed frame** equals independently rendered public AEX Smart output before and after the port edit. Scope limitation: this join reuses captured candidate RGB decode and substitutes independently executed original key alpha; it is not an independent proof of RGB decode or a native host trace. The original key worker is also checked to leave RGB bytes unchanged.

**Acceptance.** The exact acceptance command in verify below was run against base `310b543d`, seeds 1–6 and all eight retained cases, writing `C23-smoother2-acceptance.json`. Exit 0: 1,808/1,808 current and sanitized Smart renders exact; all 1,807 base-exact cases unchanged; only seed2/index273 changes, from 4/1 differing bytes/words to 0/0. ASan+UBSan run at `-O2 -fno-fast-math -ffp-contract=off`, abort-on-error; zero process/sanitizer errors. Leak detection disabled; no leak-check claim.

`bash tools/fuzz/verify_C23_stages.sh` exited 0. Original palette worker versus optimized and sanitized production: 2,744/2,744 exact in each build. This crosses fourteen raw FLOAT32 values in every RGB component: +/- zero; +/- threshold and adjacent representable values; +/- infinity; both signs of quiet and signaling NaNs. Raw RGB/alpha words are compared, including payloads. Evidence: `C23-palette-boundary.json`. Paired stage commands pass, then standard retained corpus replay completes 8/8 matches_saved. `bash -n` on both runners and `git diff --check` pass.

Instrumentation development failures, not numerical hypotheses: the old paired probe rejected enabled-key inputs by design; key-stage support was added. A missing Mac c0d0 dump represented the skipped empty-polygon branch and is now recorded explicitly. The first standalone boundary run hit a Python ctypes bytearray argument error before executing the AEX worker; converting to bytes fixed the tool. No numerical patch hypothesis was refuted. These failures are not counted as passing tests.

inference:
- The retained seed-2 residual is a palette predicate defect, not a final writer problem. Original instructions, first-stage bytes, full-frame public join and independent component boundaries support the fix.
- The requested samples now contain no unresolved Smart cluster, so there is no second or third sampled cluster to pursue. This does not establish arbitrary-input, native AE/Windows, or all-NaN conformance. C01's independent two-NaN arithmetic payload boundary remains outside this fix.

changed_files:
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`
- `tools/emulation/trace_olmsmoother2_smart_C01.py` (key stage, fresh seed/worker/scratch arguments, absent-stage and unequal-length reporting)
- `tools/emulation/test_olmsmoother2_palette_C23.py`
- `tools/fuzz/verify_olmsmoother2_C01.py` (configurable seeds/worker/scratch/report, serial jobs)
- `tools/fuzz/run_C23_fresh.sh`, `tools/fuzz/summarize_C23_fresh.py`, `tools/fuzz/verify_C23_stages.sh`
- `orchestra/reports/C23-fresh-census.json`, `C23-smoother2-acceptance.json`, `C23-key-stages-before.json`, `C23-key-stages-after.json`, `C23-palette-boundary.json`
- `orchestra/reports/C23-smoother2-colorkeep-toondilate-fresh.md`

verify:

Run from this worktree. Commands use MAIN assets and the prebuilt cache read-only; all generated verification results stay in scratch.
```sh
s="$PWD/orchestra/state/C23-smoother2-colorkeep-toondilate-fresh"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
w=/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker
bash tools/fuzz/run_C23_fresh.sh > "$s/recheck-campaigns.log" 2>&1
python3 -B tools/fuzz/summarize_C23_fresh.py --report "$s/recheck-census.json" > "$s/recheck-summary.log" 2>&1
python3 -B tools/fuzz/verify_olmsmoother2_C01.py --base 310b543d --label acceptance --scratch "$s" --worker "$w" --seeds 1 2 3 4 5 6 --jobs 1 --report "$s/recheck-acceptance.json" > "$s/recheck-acceptance.log" 2>&1
bash tools/fuzz/verify_C23_stages.sh > "$s/recheck-stages.log" 2>&1
git diff --check
```
Expected: all sixteen current campaigns 300 Smart exact each; comparator table above, zero base-exact changes, one mismatch->exact; zero sanitizer errors; 2,744 palette boundaries exact; before trace first difference pre-gamma, after all captured stages exact; both full-frame AEX joins true; corpus 8/8 matches_saved. Committed census is the historical pre-fix measurement, so seed2's current output hash intentionally differs at index273. Logs and campaign JSONs remain in scratch; regenerable harness/corpus trees are removed before commit.

next:
- Review/merge this one closed-cluster commit. No additional Smart cluster was exposed in the requested fresh samples.
- Separate follow-up for C01's two-NaN arithmetic payload selection with native x86/Windows evidence, or independently expanded source/parameter sampling. Do not infer native AE exactness from these CPU emulation results.

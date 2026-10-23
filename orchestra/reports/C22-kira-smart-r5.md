status: done

summary:
- Closed three Smart clusters in separate commits: Alpha approximation, Gaussian Length1, and scalar luminance/max approximation.
- Seed1 n300 Smart exact254→263, mismatch0 throughout, refusal46→37; all254 base-exact records persist.
- Fresh-seed checks, per-cluster ASan/UBSan campaigns and corpus monotonicity pass; strict saved replay8/8.
- One saved refusal is explicitly rebased to exact with its prior result retained; release gates, ledger restrictions, other plugins, MAIN assets and reference workers are unchanged.

facts:

Base `0b95856c`, branch `orch/C22-kira-smart-r5`, with C16 merged. Shared guide, Kira restrictions, compatibility plan, emulator gotchas and previous triage/fix reports were read. All campaigns use jobs1 (the machine limit), no shrinking and ticket-local scratch/corpora. The initial seed1 remeasurement is254 exact/0 mismatch/46 refusal,287 successful original Smart outputs/13 original rejects.

| Cluster | Commit | Seed1 exact/mismatch/refusal | Fresh campaign |
|---|---|---|---|
| ticket base |0b95856c|254/0/46|—|
| Alpha approximation |3dacf4ae|258/0/42|seed10:243/0/57→252/0/48|
| Gaussian Length1 |8207f109|260/0/40|seed11:267/0/33→268/0/32|
| luminance/max approximation + direct ratio |4b864a58 + corpus follow-up|263/0/37|seed12:262/0/38→264/0/36|

Final seed1 preserves every one of the254 ticket-base exact Smart result objects and every Classic result object. Classic remains48 mismatches/252 refusals against its separate original route. Final original Smart output/reject is287/13 (seed1) and289/11 (seed12). Original rejects are not exact cases. Seeds10/11 are per-cluster evidence, not final-source measurements.

Detailed commands, stage boundaries and evidence:

- [Alpha approximation](C22-kira-smart-r5-approximation.md): bound case70 first differs in reduced source; recover IPP separate SUB/MUL/ADD and double fractional coordinates plus full-source composition. Independent odd geometry exposes a second boundary, resolved before promotion. Final240 independent exact conditions and18 refusals.
- [Gaussian Length1](C22-kira-smart-r5-length1.md): first divergence is fourth-ray Gaussian output word132 (`7369c63c` versus `7269c63c`), followed by the retained one-word final difference. Restore the original symmetric scalar tail. Final288 independent conditions exact;66 retained Gaussian cases preserve497250 words;7 negative refusals.
- [Scalar approximation](C22-kira-smart-r5-scalar-approx.md): connect luminance/max recovery; extended31×23 input exposes reciprocal-of-ratio selecting the preceding integer cell. Original horizontal/vertical tables prove76 direct-ratio coefficient/index entries. Correct the common resize operation. Final480 scalar+96 Alpha conditions exact;18 negative refusals.

Each cluster independently rerenders600 campaign Smart conditions under ASan/UBSan (1800 total), audits70 corpus inputs and140 arithmetic route replays, and passes25 fast tests plus the compiled54-row generic sanitizer test includingHD. Final compiled test takes46.022s. No sanitizer error, admitted mismatch or changed base-exact output was observed. Final independent matrix comparisons total1104 exact conditions across the three clusters; this is an execution count, not a unique-input/all-domain claim.

| Corpus audit | Alpha approximation | Length1 | Scalar approximation |
|---|---|---|---|
| Saved production inputs |8 unchanged|8 unchanged|7 unchanged; index7 refusal→exact|
| Historical diagnostic changed samples |3742, all toward exact|0|0|
| Changes away from exact |0|0|0|
| Strict production replay |8/8|8/8|7/8 before explicit rebaseline;8/8 after|

The final integrity audit checked each `matches_saved` flag rather than relying on replay exit status and found one stale refusal expectation. The corpus follow-up preserves its prior result and rebases only Smart refusal→exact. Original oracle/provenance, pixels, parameters and Classic expectation are unchanged; the repeated strict replay passes8/8. This corrects the third implementation commit's premature saved-replay claim without rewriting history.

Identities:
- Final Mac source SHA256 `84e79d8b823789594e7723b55793a6e4c322e7765a5c3132cb4801c1153de732`.
- Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- Retained Kira worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`; used by absolute path without rebuilding. INDEX lists separate Radial workers.
- Complete bindings and measurements: `reports/fuzz/olmkirakira_smart_C22_{approximation,length1,scalar_approx}.json`.

Regenerable build directories were removed; final scratch measurement36,750,820 bytes (under5GiB), retaining logs/source candidates/raw evidence. No ticket Python probe/campaign process remains. Diagnostic patches reconstruct their candidates byte-for-byte; final staged whitespace check passes. No permission rejection, push, stash, history rewrite, installation, MAIN/external-worker modification or release/ledger/other-plugin edit occurred. All three candidate failures supplied new intermediate boundaries; the two-refutations-without-new-boundary stopping condition did not occur.

inference:

The original instruction/table observations, first divergent stages and independent/fresh tests support these bounded CPU-emulation closures. They are not native AE/UCRT, arbitrary-input, custom-ramp, ROI/downsample or whole-plugin AE-exact claims. Three-cluster ticket scope is complete; residual families remain.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `core/kirakira_gaussian.h`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/check_kirakira_resize_coefficients_C22.py`
- `tools/emulation/fixtures/kirakira_resize_{linear,difference}_C22.patch`
- `tools/emulation/fixtures/kirakira_scalar_resize_reciprocal_C22.patch`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000007.json`
- `reports/fuzz/olmkirakira_smart_C22_{approximation,length1,scalar_approx}.json`
- `orchestra/reports/C22-kira-smart-r5{,-approximation,-length1,-scalar-approx}.md`

verify:

The linked per-cluster reports contain complete before/after, sanitized matrix/campaign, paired-trace and corpus commands. Quick final recheck:

```sh
s="$PWD/orchestra/state/C22-kira-smart-r5/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 12; do
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/seed$seed" --report "$s/seed$seed.json" --corpus "$s/seed$seed-corpus" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
python3 - "$s/replay.json" <<'PYCODE'
import json, sys
r=json.load(open(sys.argv[1]))
assert r['completed']==8 and len(r['replays'])==8
assert all(row['matches_saved'] for row in r['replays'])
print('strict saved replay 8/8')
PYCODE
PYTHONPATH=tests python3 -m unittest test_olmkirakira_generic_beta_lane_20260820 test_olmkirakira_merge2_float_oracle_20260728 test_olmkirakira_outer_compose_oracle_20260728 test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.Mode4FullCallerHostlessExactTests.test_mac_production_owns_the_bounded_highlight_and_typed_writer > "$s/fast-tests.log" 2>&1
PYTHONPATH=tests python3 - <<'PY' > "$s/compiled-sanitizer.log" 2>&1
import unittest
from pathlib import Path
import test_olmkirakira_generic_beta_sanitizers_20260820 as t
# Read-only SDK headers/utilities in MAIN; SOURCE/HARNESS retain worktree paths.
t.ROOT=Path('/Users/onmk/Documents/Projects/Personal/OLM as')
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(t))
raise SystemExit(not r.wasSuccessful())
PY
git diff --check
```

Expected seed1=263/0/37, seed12=264/0/36, strict replay8/8,25 fast tests and1 compiled sanitizer test passing, clean diff check.

next:
- Stop at three closed clusters, as requested.
- Remaining seed1 refusal37 =13 original rejects +24 successful-oracle refusals: Gaussian9, approximation7, non-SDR box5, nonfinite3. These are parameter-family groupings, not proved shared root causes; the final machine report includes every residual record.
- Suggested follow-up: Gaussian Highlight/color constructors, four-component active approximation, finite non-SDR/NaN propagation, then native AE/UCRT and ROI/downsample proof.

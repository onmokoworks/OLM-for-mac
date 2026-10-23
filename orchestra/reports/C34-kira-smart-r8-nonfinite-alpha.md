status: done

summary:
- Recover the original NaN clamp and Highlight's direct3/5-tap RowSum; admit nonfinite PF32 Alpha box inputs.
- Seed1 Smart279/0/21 →282/0/18; fresh seed22 282/0/18 →284/0/16.
- Final1312 matrix conditions,600 campaign Smart renders,1200 historical routes and all sanitizer checks pass.
- Rebaseline one saved refusal→exact; preserve the23 inherited T06 expectation discrepancies.

facts:

Base `ecc0c27b`. F32 worker SHA256 `c9d827ffaaf191e099f90ecc2e34ff738598dd93b32729f9d206eb08733206f1`; original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`. All campaigns n300/jobs1/no shrinking. Machine evidence: `reports/fuzz/olmkirakira_smart_C34_nonfinite_alpha.json`.

The initial nonfinite Alpha box gate-off matrix is512/512 exact, and the finite/HDR/extreme matrix is288/288 exact. However, extending lengths, Highlight, rotation, ramps and opacities yields478 exact/34 mismatches. That refutes unrestricted admission of the old arithmetic. All failing inputs and results remain in the machine report.

New boundary1: source opacity zero with infinite Alpha. Independent length-matrix index24 has exact source/seed/glow, a sign-only NaN ray difference, then a composition difference. Final first word0 is original `0000803f`, Mac `00000000`; three final words differ. The old composition clamp passed NaN through, losing a positive glow after `0 * Inf`. Original outer compose `18114e460` clamps both opacity products before combining them. Original clamp `181156740` ends at `18115676a MAXSS xmm0,xmm1`, with XMM1=+0. It maps every tested NaN to+0.

The import-free original clamp probe covers18 input bit patterns. Old C++ matches12/18. A simple inverted floating comparison matches16/18: ARM optimization quiets input `7f812345`/`ff812346` to `7fc12345`/`ffc12346` rather than zero. A same-flags assembly probe emits `fmaxnm`; its assembly is retained in the machine evidence. Explicit operand-bit NaN classification gives18/18 under ASan/UBSan, including signed zero, subnormals, infinities, quiet/signaling NaNs and payloads. This is the clamp operation's unordered branch, not an output-byte correction. The old Python outer-compose model and its zero-denominator test are corrected to the same original MAXSS semantics. The probe initially needed a tooling correction because AexLoader returns XMM0 as bytes; the corrected probe's recorded results are the18-row comparisons above.

New boundary2: clamp-only candidate length-matrix index261 (9×1) still fails. Original and Mac rays0–3 match; Highlight ray4 first differs at word8, original `e2377d3f` versus Mac `4623c1ff`. Final first word32 is original `0ad7233c`, Mac `0afcc73b`, four words differ. Original row-filter trace records `1812d6690/5/9/1`. MAIN decomp `FUN_1812d6690`, lines3830126ff, has explicit direct sums for kernel3 and5, and sliding state only for other sizes. The old Highlight helper always slid, retaining NaN after it left the contributing window. Restoring the3/5 direct sums makes all512 boundary conditions exact. Index261 then matches every paired stage. Each refuted hypothesis supplied a new boundary; the ticket stop condition did not occur.

The final admission applies only to the existing non-approximated PF32 Alpha/Mode1-or2 tuple. Other constructors, Gaussian, approximation, geometry/layout/ramp/angle and work-budget checks retain their prior domains. The obsolete finite-input/infinite-powf guard is removed after the arithmetic fixes; no source-dependent final-value adjustment is introduced.

| Check | Before | After |
|---|---|---|
| seed1 Smart E/M/R |279/0/21|282/0/18; indices63,116,126|
| seed22 Smart E/M/R |282/0/18|284/0/16; indices122,152|
| Guarded corpus70 |baseline|one refusal→exact,69 unchanged|
| Both-route140 sample comparisons |baseline|zero changed samples|
| Production saved replay |8 fixtures|8/8 matches_saved|
| T06 saved matches |39/62|38/62 before migration;39/62 after|

Final production matrices:512 nonfinite controls +512 length/opacity boundaries +288 finite/HDR/extreme conditions =1312 exact; six outside-domain controls refuse. All are ASan/UBSan builds. The final600 Smart campaign replays match their ordinary-build hashes. Every original exact Smart and every Classic result object is preserved at both seeds. A further1200 sanitized routes replay the earlier seed20/21 campaigns: all561 previous exact Smart hashes and all prior rendered Classic hashes persist. Additional Smart admissions match their cached F32 oracle hashes (seed20 indices122/186, seed21 indices195/266/299). These are execution counts, not an exhaustive-domain claim.

Five final public-bound traces (campaign63/116/126 and independent24/261) have exact glow and post-clamp stored RGBA. Raw ray differences are retained as non-exact: respectively209,47,149,1,0 words, all NaN-to-NaN, zero finite/NaN-boundary differences. These differences are classified, never tolerated by the final comparator. The original aggregation clamp removes their sign/payload distinctions before glow; final bytes are compared exactly. Index261 has no divergent stage at all. No first divergence at a still-host math import was observed.

The one corpus migration is `seed1_case000116_9b13c27c2f2e.json`, raw output SHA256 `f4550c426aa33fe7fdb5fcb4ce3ff4fda8de335e7e6ed128024fca0b9fac1396`. Input/reduction fields and prior result/provenance remain in history. The final23 mismatching T06 paths are exactly the initial set; all62 final result objects equal the explicit F32 replay. Full T06 replay exits1 for these inherited discrepancies, so it is not claimed green. Production8 replay passes. Existing fast tests now26/26; compiled54-row sanitizer test passes (44.822s).

Final hashes:
- Mac source: `52adf53f477672536fdee028a2610356efff28903eab52c30b74e9a594032bc0`.
- Highlight helper: `aa5bb0314f1d97c2d28278994db0370be938ab46ba49a6da0d895a26b76f6297`.
- Compose helper: `5aa9d28fd15be9e31be51eb42b9a960b654df9f24cdb4b26a5b79a7aaf6dca52`.

inference:

The original clamp and direct-row branch explain the counterexamples and support this bounded Alpha box admission. Intermediate NaN payload identity remains unimplemented where original downstream clamps erase it; the task's final-output bar is met in every admitted validation case. This does not establish arbitrary native AE/UCRT, custom ramps or ROI/downsample behavior.

changed_files:
- `core/kirakira_{highlight,merge2}.h` and `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`, `probe_kirakira_clamp_C34.py`, `snapshot_kirakira_C34.py`, `verify_kirakira_history_C34.py`
- `tools/emulation/olmkirakira_outer_compose_oracle_20260728.py` and its test
- `tools/emulation/rebaseline_kirakira_C29.py` (optional history-ticket argument; default unchanged)
- One T06 corpus case, machine evidence, this report and ticket summary

verify:

Historical comparisons MUST bind the old numerical headers; the snapshot helper does this without switching branches. All commands run from this worktree. Expected counts are above.

```sh
s="$PWD/orchestra/state/C34-kira-smart-r8/recheck-nonfinite"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/emulation/snapshot_kirakira_C34.py --revision ecc0c27b --scratch "$s/base" > "$s/snapshot.log" 2>&1
for seed in 1 22; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/base/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
for family in nonfinite-alpha-box nonfinite-alpha-lengths finite-alpha; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family nonfinite-alpha-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/base/before.cpp" --campaign-dir "$s" --seeds 1 22 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/base/before.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_clamp_C34.py --aex '/Users/onmk/Documents/Projects/Personal/OLM as/plugins_2025/OLMKiraKira.aex' --scratch "$s/leaf" --report "$s/leaf.json" --require-exact > "$s/leaf.log" 2>&1
for index in 63 116 126; do
 "$py" tools/emulation/probe_kirakira_smart_C07.py --ucrt-math --campaign-seed 1 --trace-index "$index" --require-exact --scratch "$s/trace$index" --report "$s/trace$index.json" > "$s/trace$index.log" 2>&1
done
for index in 24 261; do
 "$py" tools/emulation/probe_kirakira_smart_C07.py --ucrt-math --family nonfinite-alpha-lengths --trace-index "$index" --require-exact --scratch "$s/matrix$index" --report "$s/matrix$index.json" > "$s/matrix$index.log" 2>&1
done
```

To reproduce the rejected old arithmetic, run `nonfinite-alpha-lengths` with `--source "$s/base/before.cpp" --gate-off` and omit `--require-exact`: expected478 exact/34 mismatch. Add the same source/gate flags to matrix-index24's trace for its pre-fix output. The old clamp probe uses `--header "$s/base/kirakira_merge2.h"` without `--require-exact`: expected12/18.

The earlier seed20/21 preservation command actually run was:

```sh
python3 tools/emulation/verify_kirakira_history_C34.py --campaign "$PWD/orchestra/state/C34-kira-smart-r8/after-seed20.json" --campaign "$PWD/orchestra/state/C34-kira-smart-r8/approx/after-seed21.json" --scratch "$s/history" --report "$s/history.json" > "$s/history.log" 2>&1
```

Those two input reports are reproducible by the preceding cluster reports at their commits. Expected1200 sanitized routes pass. Final fast/compiled test commands are in the ticket summary. For T06, compare the path sets of `matches_saved=false`, not exit status alone. Rebaseline command actually run:

```sh
python3 tools/emulation/rebaseline_kirakira_C29.py --before-replay "$PWD/orchestra/state/C34-kira-smart-r8/nonfinite/t06-before.json" --after-replay "$PWD/orchestra/state/C34-kira-smart-r8/nonfinite/t06-after.json" --scratch "$s/migration" --ticket C34-kira-smart-r8 --apply
```

It updates only the identified refusal→exact transition and is idempotent for those recorded replays. The committed case is already updated.

Final T06 recheck (the runner's expected exit1 is due to the23 inherited discrepancies):

```sh
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch "$s/t06" --report "$s/t06.json" --corpus "$s/t06-corpus" > "$s/t06.log" 2>&1
python3 - "$s/t06.json" <<'PYT06'
import json,sys
from pathlib import Path
r=json.load(open(sys.argv[1]))
e=json.load(open('reports/fuzz/olmkirakira_smart_C34_nonfinite_alpha.json'))
assert r['completed']==62 and sum(x['matches_saved'] for x in r['replays'])==39
paths=sorted(str(Path(x['path']).resolve().relative_to(Path.cwd())) for x in r['replays'] if not x['matches_saved'])
assert paths==e['t06']['unchanged_discrepancies']
print('39/62 saved matches; inherited23 discrepancy paths unchanged')
PYT06
```

next:
- Three clusters closed; stop as requested.
- Seed1 remaining18 refusals:13 original AEX rejects and rendered cases39/52/86/179/272. Suggested follow-up: finite-HDR Max and finite/nonfinite Alpha Gaussian/approximation, using fresh first-stage evidence.

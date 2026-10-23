status: done
summary:
- Admit finite PF32 color input through the existing full-resolution Gaussian tuple.
- Seed1 stays287/0/13; seed106 improves284/0/16 to286/0/14 (indices122/123).
- Gate-off918 and production918 independent conditions exact;12 negative refusals.
- Correct trace-wrapper initialization; both campaign traces now public-bound/all-stage exact.

facts:

Base82661ef7. Campaigns n300/jobs1/no shrinking with scratch corpus. Seed1 original successful Smart/reject287/13; seed106286/14. Production changes only finite-source admission, preserving existing tuples and finite component scan. No arithmetic changed.

The initial color gate-off matrix is864 exact under ASan/UBSan. Seed106/index122's gate-off output is exact, but the first diagnostic trace fails public binding, first differing at ray1. Independent matrix145 repeats that trace-only failure at ray0, with exact public output. Inspection found that probe_kirakira_filtered_C50.py omitted OLM_KK_PROCESS_ATTACH_DIAGNOSTIC and OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC, both enabled by the established probe_kirakira_smart_C07.py. Set those switches in the wrapper before original_trace. This changes the diagnostic harness only; no original numerical body or reference worker is patched. With initialization, case122 and123 both bind their final bytes to F46 and match source_full, source, seed, all five rays, glow, glow_full, composition and output. The earlier unbound diffs are retained as failed diagnostic evidence, not port discrepancies.

Gate-off864 ordinary +54 boundary and production864+54 conditions are exact with ASan/UBSan.12 nonfinite negative cases refuse cleanly. All70 corpus results remain unchanged (production8/T06 62), no rebaseline. The audit passes600 sanitized Smart campaign renders, preserves all571 prior exact Smart result objects, and admits122/123 exactly. A separate comparison preserves all600 Classic result objects.26 existing tests pass. Source SHA2560443f91a775ca30fb53663f46720e1af9355b138f3f2b7e7111bd111d1daac58; AEX and F46 worker identities are unchanged from the scalar report. Full compressed reports and uncompressed SHA256 manifest are in C55-kira-smart-r2/color/.

|Seed|Before Smart E/M/R|After|
|---|---|---|
|1|287/0/13|287/0/13|
|106|284/0/16|286/0/14|

inference:

Missing initialization explains the observed color trace discrepancy: enabling the established initializer sequence restores public binding and full-stage equality. This is not an original-OLM memory bug or reason to change port arithmetic. Finite color Gaussian admission is bounded by existing tuple restrictions; no native AE/general input compatibility claim.

changed_files:
- mac/OLMKiraKira/OLMKiraKira.cpp
- tools/emulation/probe_kirakira_filtered_C50.py
- This report, ticket report and color evidence.

verify:

At this cluster commit, repeat the scalar report's campaign/audit commands with before revision82661ef7 and seeds1/106; expected results above. Use domain color-gaussian for ordinary, --boundary and --negative matrices (expected864/54 exact and12 refusal). Gate-off repetition uses the before source and --gate-off. Exact additional trace commands:

```sh
s="$PWD/orchestra/state/C55-kira-smart-r2/recheck-color"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
for index in 122 123; do
 "$py" tools/emulation/probe_kirakira_filtered_C50.py --domain color-gaussian --seed 106 --case-index "$index" --trace-index 0 --gate-off --require-exact --scratch "$s/trace$index" --report "$s/trace$index.json" > "$s/trace$index.log" 2>&1
done
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain color-gaussian --require-exact --scratch "$s/matrix" --report "$s/matrix.json" > "$s/matrix.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain color-gaussian --boundary --require-exact --scratch "$s/boundary" --report "$s/boundary.json" > "$s/boundary.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain color-gaussian --negative --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
git diff --check
```

next:
- Continue scalar approximation, where the gate-off matrix has actual public-output mismatches; keep that domain refused until corrected and independently verified.

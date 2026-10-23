status: done

summary:
- Connect the recovered linear resize/full-resolution compose pipeline to directional Gaussian.
- Seed1 Smart274/0/26 →275/0/25; fresh seed19 275/0/25 →276/0/24.
- Preserve all prior exact outputs;378 independent production conditions and600 sanitized campaign renders pass.
- Rebaseline the four ticket-new saved refusals to exact, preserving inputs and prior result/provenance history.

facts:

Base `2032aa79`; original AEX/F32 identities unchanged. All campaigns use n300/jobs1/no shrinking and ticket-local scratch/corpora. Seed1 admission174; seed19 admission68. Original output/reject287/13 and290/10. Machine evidence: `reports/fuzz/olmkirakira_smart_C29_gaussian_approximation.json`.

Seed1/index174, PF8 43×4, Channel3/Mode3/Approximated Input: first divergence is the reduced source. Original word0 `2bd6803e` versus Mac `a1a0203f`; all168 source words differ. The original four-component seed also differs in shape from the old scalar fallback. Final output differs in352 bytes, first byte2 original `8a`, Mac `ff`.

Extending the recovered approximation selector to Mode3/Highlight0 connects the existing linear reduction, recovered scalar/four-component constructors, directional Gaussian, scaled helper-length normalizers, linear glow enlargement and full-resolution source composition. The diagnostic immediately matches every paired stage and final output. No Gaussian coefficient, aggregation arithmetic or output sample is adjusted in this cluster.

Admission retains finite SDR, full-frame dimensions at least4×4, existing control/angle/ramp limits and Highlight0. It reuses the directional Gaussian budget with full dimensions and unscaled lengths, conservatively bounding the smaller working image and retaining full-resolution source storage. Highlight Gaussian approximation and one-pixel reduced IPP workspaces remain outside this admission.

Independent gate-off270 control/geometry conditions and108 zero/odd/endpoint-length boundaries are exact under ASan/UBSan; final production repeats all378 exact. Six one-away cases refuse. Final public-bound traces index174 and independent PF32 luminance matrix index199 match all source/seed/ray/glow/compose stages. Final-source campaign audit reproduces all600 Smart outputs under ASan/UBSan.25 fast tests and the compiled54-row sanitizer test pass (49.338s). No numerical hypothesis was refuted in this cluster.

| Comparison | Before → after |
|---|---|
| seed1 Smart E/M/R |274/0/26 →275/0/25|
| seed19 Smart E/M/R |275/0/25 →276/0/24|
| All prior exact Smart / all Classic campaign results |unchanged|
| Guarded70-case corpus |all unchanged in this cluster|
| Both-route140-case sample audit |0 changed samples,0 away from exact|
| Production8 saved replay |8/8, no expectation changes|

Ticket-wide saved-corpus migration (explicit acceptance rebaseline):

The existing T06 corpus had23 saved-result discrepancies at ticket start. Two full F32 replays using the original ticket source and final source establish that only indices48,59,89,235 change during C29, each Smart refusal→exact with unchanged Classic and original oracle results. `rebaseline_kirakira_C29.py` selects exactly these changes and invokes the existing migration tool, retaining previous results/provenance. Case inputs, reduction operations and generator identities remain identical.

| T06 saved comparison | Matches /62 |
|---|---|
| Original ticket source, before migration |39|
| Final source, before migration |35|
| Final source, after four updates |39|

All four updated cases match saved results. The remaining23 discrepancy paths are exactly the initial set. All62 complete result objects match between the explicit F32 replay and the final saved-worker replay. No pre-existing discrepancy was hidden or rebaselined. Production8 remains8/8. The helper is idempotent: an already-applied transition is validated and retained.

inference:

These bounded CPU-emulation observations support directional Gaussian approximation. They do not close four-component Highlight, Gaussian Highlight approximation, non-SDR approximation, arbitrary native math/AE or ROI/downsample. The preserved corpus discrepancy set is inherited baseline drift, not a newly failing C29 case.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/rebaseline_kirakira_C29.py`
- Four `tests/fuzz_corpus/olmkirakira_gate_off_T06/seed1_case000{048,059,089,235}_*.json` entries
- `reports/fuzz/olmkirakira_smart_C29_gaussian_approximation.json`
- `orchestra/reports/C29-kira-smart-r7{,-gaussian-approximation}.md`

verify:

Use the scalar report's campaign/audit/sample/replay sequence at this commit with base revision `2032aa79`, seeds1/19 and scratch `orchestra/state/C29-kira-smart-r7/recheck-approximation`. Expected campaigns275/0/25 and276/0/24; zero changed corpus samples. Replace its independent families with `approximation-gaussian` (270) and `approximation-gaussian-boundary` (108), and its negative family with `approximation-gaussian-negative` (6). Trace index174 with `--ucrt-math`.

```sh
s="$PWD/orchestra/state/C29-kira-smart-r7/recheck-approximation"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for family in approximation-gaussian approximation-gaussian-boundary; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family approximation-gaussian-negative --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira_gate_off_T06 --scratch "$s/t06" --report "$s/t06.json" --corpus "$s/t06-corpus" > "$s/t06.log" 2>&1
python3 - "$s/t06.json" <<'PYCHECK'
import json, sys
r=json.load(open(sys.argv[1]))
assert r['completed']==62
assert sum(x['matches_saved'] for x in r['replays'])==39
updated=('case000048_', 'case000059_', 'case000089_', 'case000235_')
rows=[x for x in r['replays'] if any(i in x['path'] for i in updated)]
assert len(rows)==4 and all(x['matches_saved'] for x in rows)
print('ticket updates4/4; inherited baseline discrepancies23')
PYCHECK
git diff --check
```

The T06 runner intentionally exits1 for the23 inherited discrepancies; inspect its complete report and the assertion result. The migration's exact command, after obtaining before/after complete replays, is:

```sh
python3 tools/emulation/rebaseline_kirakira_C29.py --before-replay "$s/t06-before.json" --after-replay "$s/t06-after.json" --scratch "$s/migration" --apply
```

Render the before replay with `verify_kirakira_admission_F10.py --campaign-source` and the original ticket source `395e5d8af90321982f0493bc052f09e671bd8368`; use `run.py` for after. Both use `--plugin olmkirakira --jobs 1 --worker /Users/onmk/.cache/olm-emu/worker-F32-deep/aex-guest-worker --replay tests/fuzz_corpus/olmkirakira_gate_off_T06`. After migration, rerunning the old source naturally disagrees with the four new saved expectations; the original39→35→39 table is preserved in machine evidence and history.

next:
- Three clusters closed; stop as requested.
- Final residual25 =13 original rejects +12 successful-oracle refusals. Consider four-component Highlight and its approximation owner next; keep the F38 sign-only witness separate.

status: done

summary:
- Closed finite signed-Alpha seed admission on Smart; rendering arithmetic is unchanged.
- Seed1 improves207/0/93→215/0/85; fresh seed6 improves220/0/80→227/0/73 (exact/mismatch/refusal).
- Previous exact Smart and all Classic campaign records are identical;600 ASan/UBSan route replays pass.
- Independent167+167 production cases are exact;6 invalid inputs refuse. All70 corpus inputs retain their results; strict replay8/8.
- Fractional-exponent negative Alpha remains excluded with a public-bound first-filter counterexample.

facts:

Base `7d0b64fad8c5e5909404853e0264537352fcb7e0`, branch `orch/C13-kira-smart-r3`.
Read AGENT_GUIDE, compatibility plan, GOTCHAS, the KiraKira ledger restrictions and triage/fix reports. INDEX lists RadialBlur workers; the unchanged retained KiraKira worker is used by absolute path. No MAIN/external worker/source, release gate, ledger or other-plugin change.

Evidence: `reports/fuzz/olmkirakira_smart_C13_signed.json`. Original AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; retained worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Every campaign/matrix binds the Mac source hash in the machine evidence.

| n300/jobs2 | Before E/M/R | After E/M/R | AEX Smart output/reject |
|---|---|---|---|
| seed1 |207/0/93|215/0/85|287/13|
| fresh seed6 |220/0/80|227/0/73|291/9|

Remeasurement uses `tools/fuzz/run.py`; shrinking is disabled as in C07 to avoid the documented shrink-timeout cleanup issue. No framework errors. Initial sanitized gate-off census:235 exact/52 mismatch/13 uncompared. Among80 successful-oracle refusals,28 are diagnostic exact. Alpha/Mode2 signed inputs are a largest tied parameter/profile group (9);8 diagnostic exact and1 mismatch. Parameter grouping is not a claim of a shared numerical cause.

The retained C07 source predicate excluded every negative Alpha, including those whose original scalar powf produces a finite result. The new rule checks finite ARGB input and finite powf(alpha,materialized/clamped exponent), without requiring nonnegative Alpha. No expected output, coordinate or fitted magnitude cutoff is used. All tuple, storage, geometry, default-ramp and workload requirements persist; Classic and nonfinite/overflowing-seed admissions are unchanged.

- Gate-off independent signed finite-seed matrix:167 exact. Production repeats167 exact; varied-length matrix167 exact, lengths{1,2,3,4,5,6,7,15,50,1000}, geometries1×1/1×9/7×11/9×7, box Modes1/2, both merges, HDR/signed/extreme finite bit patterns. The matrix filters the constructor domain using host float powf, matching the retained worker import. It includes unit and even-integer exponents for negative Alpha.
- Production seed1/index15 (PF32 9×19, signed input, Source Opacity88) has exact source, seed, five rays, glow, composed and final output. Every captured helper stage is exact; original full-caller trace binds to public Smart.
- Counterexample seed1/index89 (PF32 17×21, Strength186): exact source/seed, then first ray differs. First captured helper difference is `helper0_op1_out` word227, AEX `0000c07f` versus Mac `aff59c3d`. Final36 words/102 bytes differ, first word12 `0000003f` versus `2e730b3f`. Original public binding passes. Its nonfinite seeds remain refused. This supplies a measured boundary, not a failed hypothesis without new data.
- Six independent invalid cases (negative Alpha with fractional exponent, Alpha Inf/NaN, RGB Inf/NaN, powf overflow) remain refusals with unchanged destination and balanced callbacks.

| Corpus | Before→after | Rebaseline |
|---|---|---|
| production8 + historical T06 inputs62 |70/70 identical status and bytes|none needed|
| diagnostic arithmetic140 route replays |0 changed samples|none|

All600 final Smart campaign cases rerender under ASan/UBSan and agree with ordinary builds. Previous exact Smart and all Classic records are unchanged. Strict production corpus replay8/8. Existing25 fast tests pass; compiled generic sanitizer test passes (54 internal rows including HD),43.315 seconds. Only its read-only SDK root is rebound to MAIN. `git diff --check` passes.

inference:

Finite negative scalar seeds use the already recovered C07 warp, sliding/direct RowSum and aggregation operations. Removing the redundant sign restriction admits this operation domain without changing rendered bytes. NaN propagation is a distinct unresolved filter behavior; exact final output of some NaN cases is insufficient to admit them. These finite CPU emulator/fake-host probes are not exhaustive native AE/UCRT/ROI/downsample proof.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/summarize_kirakira_smart_C13.py`
- `reports/fuzz/olmkirakira_smart_C13_signed.json`
- `orchestra/reports/C13-kira-smart-r3-signed.md`
- `orchestra/reports/C13-kira-smart-r3.md`

verify:

At this cluster commit:

```sh
s="$PWD/orchestra/state/C13-kira-smart-r3/recheck-signed"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
git show 7d0b64fa:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 6; do
  python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/before-seed$seed.json" --corpus "$s/before-seed$seed-corpus" > "$s/before-seed$seed.log" 2>&1
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/after-seed$seed.json" --corpus "$s/after-seed$seed-corpus" > "$s/after-seed$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 6 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
for family in signed-finite-seed signed-finite-lengths; do
  python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family invalid-input --expect-finite-domain --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
for i in 15 89; do
  "$py" tools/emulation/probe_kirakira_smart_C07.py --gate-off --campaign-seed 1 --trace-index "$i" --scratch "$s/trace$i" --report "$s/trace$i.json" > "$s/trace$i.log" 2>&1
done
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/before.cpp" --scratch "$s/arithmetic" --report "$s/arithmetic.json" > "$s/arithmetic.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected: campaign table,600 sanitized routes,70 unchanged corpus cases,167+167 exact,6 refusals, trace15 all exact/public-bound, trace89 excluded first-filter mismatch/public-bound,140 arithmetic routes/0 changed samples,replay8/8.

next:
- Remaining seed1:85 refusals,13 without original output. Investigate approximation, then color constructors/Gaussian residuals. NaN filtering remains excluded.

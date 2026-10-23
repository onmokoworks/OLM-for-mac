status: done

summary:
- Admit nonfinite PF32 Alpha input through the existing full-resolution Smart Gaussian tuple.
- Seed105 Smart exact/mismatch/refusal improves 282/0/18 → 283/0/17 (index179).
- Seed1 stays287/0/13; fresh seed106 stays282/0/18. Preserve851 prior exact Smart and900 Classic result objects.
- Gate-off512 exact; production512 exact;5 negative refusals;900 sanitized campaign renders;70 unchanged corpus results.

facts:

Base `d6cd18daa05d1106718faa2594d4fe7a3b089564`. Shared guide, compatibility plan, Kira ledger restrictions, emulator GOTCHAS, T06/F12/C34/C38/S01 reports were read. Original AEX and retained worker are read-only. No release gate, ledger, other plugin, MAIN, emulator or installed bundle changes.

All campaigns used `tools/fuzz/run.py --plugin olmkirakira --n 300 --seed SEED --jobs 1 --shrink-attempts 0 --shrink-seconds 0`, ticket-local scratch/corpora, and retained F46. Seed106 before used `verify_kirakira_admission_F10.py --campaign-source base.cpp` with the same flags. They all completed300 cases. The original successful Smart/reject counts are287/13,285/15,286/14 at seeds1/105/106. Original rejections are not counted as exact.

| Seed | Before E/M/R | After E/M/R | Improvement |
|---|---|---|---|
|1|287/0/13|287/0/13|none|
|105|282/0/18|283/0/17|179|
|106 (fresh)|282/0/18|282/0/18|none|

Seed105/index179 gate-off ASan/UBSan output equals original SHA256 `f1c602ebde3c090f9d51c895657a6f87cb50aa6fbb0cbfa70d6c11d3e365314e`. Independent matrices extend the C34 nonfinite bit patterns (signed infinities, quiet/signaling NaNs and payloads) through Gaussian:256 ordinary controls and256 length/Highlight/rotation/ramp/opacity boundary conditions. Gate-off and final production each give512 exact,0 mismatches. Five outside-domain conditions refuse. No hypothesis was refuted in this cluster. No intermediate-stage equality is claimed; admission relies on strict public-AEX final bytes and sanitizer evidence.

`verify_kirakira_smart_C04.py` passes900 sanitized Smart campaign renders, matching each ordinary result/hash, and70 before/after corpus comparisons. All851 initial exact Smart result objects and all900 Classic result objects are identical. Both committed corpora are unchanged: production8 unchanged and historical T06 62 unchanged. No expectation migration is needed. Saved production replay is8/8 matches_saved (its recorded worker binding is retained). The historical T06 saved expectations were not rebaselined or claimed current; this check compares newly executed before/after results.

26 existing fast tests pass. The compiled sanitizer test passes54 harness rows (one unittest,47.825s). Matrices and campaign/corpus verifier use ASan/UBSan with fail-fast checks. Source arithmetic is unchanged; only the source admission predicate adds the existing Gaussian Alpha tuple. Approximation, other constructors, layout, geometry, controls, angle, ramp and work limits retain their prior guards.

Final source SHA256 `ff58eb87944a17697a03a64134c9d82783731a1475ea16277fb8141cf2aa7bbf`. AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; worker SHA256 `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`. Full campaign/matrix/audit results, sanitizer logs and uncompressed SHA256 manifest are in `C50-kira-smart-r1/gaussian/` beside this report.

inference:

The existing recovered Gaussian/aggregation/composition path supports this tested Alpha source domain. This is not exhaustive or native-AE proof. The seed1 residual is entirely original rejection; expanding admission there cannot establish exactness without an original rendered output.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/probe_kirakira_smart_C07.py`
- This report, ticket report, and `orchestra/reports/C50-kira-smart-r1/gaussian/` evidence.

verify:

Run at this cluster commit. All paths remain inside the ticket scratch. Expected results are the table and counts above.

```sh
s="$PWD/orchestra/state/C50-kira-smart-r1/recheck-gaussian"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show d6cd18daa05d1106718faa2594d4fe7a3b089564:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/before.cpp"
for seed in 1 105 106; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/before.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
for family in nonfinite-alpha-gaussian-C50 nonfinite-alpha-gaussian-boundary-C50; do
 python3 tools/emulation/probe_kirakira_smart_C07.py --family "$family" --require-exact --scratch "$s/$family" --report "$s/$family.json" > "$s/$family.log" 2>&1
done
python3 tools/emulation/probe_kirakira_smart_C07.py --family nonfinite-alpha-gaussian-negative-C50 --require-refusal --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/before.cpp" --campaign-dir "$s" --seeds 1 105 106 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Gate-off reproduction: repeat each positive matrix with `--source "$s/before.cpp" --gate-off`, separate scratch/report. Expected512 exact. Existing fast/compiled tests use the commands in the C38 ticket report (unchanged test invocation, ticket-local TMPDIR and UCRT compiler wrapper).

next:
- One cluster closed. Continue color approximation and nonfinite Alpha approximation; neither is promoted by this commit.

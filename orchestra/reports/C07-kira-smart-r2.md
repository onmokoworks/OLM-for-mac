status: done

summary:
- Three clusters closed separately: scalar Alpha opacity, non-unit Strength, and finite-HDR directional RowSum/input admission.
- Seed1 Smart improves134→171→197→207 exact; fresh seed5 improves127→172→193→203 exact, with0 admitted mismatches.
- All baseline-exact Smart outputs persist. Each cluster passes600 ASan/UBSan campaign routes; corpus changes only toward exact.
- Strict production replay is8/8; Gaussian Length1's one-word counterexample remains excluded.
- The ticket's three-cluster stop condition is met; remaining refusals are documented for follow-up.

facts:

Base `81a91efdcc5f3cb55003478cae8665ca42ad8916`, branch `orch/C07-kira-smart-r2`.

| Commit / cluster | Seed1 exact/mismatch/refusal | Fresh seed5 |
|---|---|---|
| base |134/0/166|127/0/173|
| `7db468f4`, opacity |171/0/129|172/0/128|
| `7f825746`, Strength |197/0/103|193/0/107|
| this commit, finite HDR/RowSum |207/0/93|203/0/97|

Campaigns ran `python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed <1-or-5> --jobs 2 --shrink-attempts 0 --shrink-seconds 0`, with ticket-local report/corpus/scratch paths. Seed1 has287 original Smart outputs/13 rejects; seed5 has283/17. No framework errors or admissions without original output. All Classic campaign records remain unchanged.

First measured divergences:
- Opacity: seed1/index281 composed word18 `770b4c3f` versus `780b4c3f`; integer→float percentage multiplication restores all stages.
- Strength: seed1/index24 seed word11 `c8d0b03b` versus `c7d0b03b`; independent537% witness separates float powf from double pow. Materialization,0.001 clamp,powf and aggregation close the scalar pipeline.
- Finite HDR: independent155 box helper word111 `00000000` versus `dbb67f3e`; original sliding double RowSum/direct3-or5 kernels restore all captured stages.

Traces bind to original public Smart. AEX SHA256 `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`; retained worker SHA256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`. Final Mac source SHA256 `9395fa6762317b1f17b2aa4155d5ec58c8249b817730002e7da6f7c719e48b25` binds to final campaigns, matrices, trace and sanitizer replay.

Detailed measured commands, hypotheses, counterexamples and corpus before/after tables:
- [Opacity](C07-kira-smart-r2-opacity.md), evidence `reports/fuzz/olmkirakira_smart_C07_opacity.json`.
- [Strength](C07-kira-smart-r2-strength.md), evidence `reports/fuzz/olmkirakira_smart_C07_strength.json`.
- [Finite HDR/RowSum](C07-kira-smart-r2-finite.md), evidence `reports/fuzz/olmkirakira_smart_C07_finite.json`.

Each cluster has600 sanitized campaign routes and70 sanitized corpus comparisons. Separate140-route arithmetic audits change546,264,0 samples respectively, all toward exact. Only production corpus index16 is explicitly rebased refusal→exact with its full previous result retained. Final replay8/8; final25 fast tests and compiled54-row ASan/UBSan test pass. Gaussian Length1 remains a refusal and diagnostic mismatch at word217 (`5cf1563f` versus `5df1563f`). `git diff --check` passes. Removed32 regenerable build directories; final scratch is44,205,401 bytes (42.16MiB), below5GiB. No tool permission rejection occurred.

MAIN, original binaries, external emulator sources/workers, release gates, ledger and other plugins are unchanged. No worker rebuild, push, install, history rewrite or write to `/tmp`.

inference:

Paired stages establish three general operation/admission causes. The emulator/local traces use host math imports; float powf was made explicit after rejecting an unbound double-pow trace. These finite CPU-emulation/fake-host results are not native AE/UCRT or all-input compatibility claims. Negative/nonfinite alpha, powf overflow, approximation, Gaussian residuals and color constructors remain separate boundaries.

changed_files:
- `mac/OLMKiraKira/OLMKiraKira.cpp`
- `tools/emulation/trace_kirakira_numeric_F09.py`
- `tools/emulation/probe_kirakira_smart_C07.py`
- `tools/emulation/summarize_kirakira_smart_C07.py`
- `tests/fuzz_corpus/olmkirakira/refusal_seed1_case000016.json`
- `reports/fuzz/olmkirakira_smart_C07_{opacity,strength,finite}.json`
- `orchestra/reports/C07-kira-smart-r2{,-opacity,-strength,-finite}.md`

verify:

The finite-cluster report gives the full final sanitizer/corpus/trace audit commands. Quick final check:

```sh
s="$PWD/orchestra/state/C07-kira-smart-r2/final-recheck"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
for seed in 1 5; do
  python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 2 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s" --report "$s/seed$seed.json" --corpus "$s/seed$seed-corpus" > "$s/seed$seed.log" 2>&1
done
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 2 --replay tests/fuzz_corpus/olmkirakira --scratch "$s" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
git diff --check
```

Expected seed1=207/0/93, seed5=203/0/97; strict replay8/8; clean diff check. Historical sources are reproduced with `git show` at revisions listed in each report; MAIN need not be modified.

next:
- Seed1 remaining93 refusals comprise13 without AEX output and80 with output. This ticket stops at three closed clusters.
- Follow-up: approximation, negative-alpha/nonfinite filter propagation, Mode3 Highlight/Length1, scalar/four-channel color constructors. Keep native AE/UCRT claims separate.

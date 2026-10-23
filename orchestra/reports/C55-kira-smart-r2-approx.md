status: done
summary:
- Restore original unordered fade/max constructor branches; admit finite scalar approximation sources.
- Initial independent matrix788 exact/76 mismatch; fade-only854/10; complete comparison fix864/0.
- Additional108 gate-off boundaries exact; corrected focused traces bind to the public oracle.
- Final972 production conditions,900 sanitized campaign renders,2400 before/after history renders and corpus/tests pass.

facts:

Base44f3b1b6. All source experiments are general operation changes; no coordinate or expected-value patches. The matrix uses PF32 finite HDR/signed/extreme components, luminance/max constructors, both merges and Modes1/2/3 with approximated input. The retained source admission bounds include dimensions>=4 and Fade Out<=0.2. All matrix builds use ASan/UBSan.

Initial gate-off matrix:788 exact/76 mismatch. First matrix15, source index2149, PF32 7x11 extreme luminance/Mode1/Strength1:49 differing output words/194 bytes, first word184 AEX047b473e versus Mac00000000. Public-bound trace first differs at reduced-source word40 only by NaN sign (AEX0000c0ff/Mac0000c07f). Seed word10 is the first non-sign divergence: AEX00000000/Mac0000c07f. Source_full is exact. Glow differs in8 words and final output differs.

Original FUN_1811501b0 at1811501c5 executes UCOMISS, then JNE at1811501cf. Unordered comparison sets ZF, so it takes the same zero-return path as zero input. The C++ value==0 condition omitted that behavior. The first candidate restores this branch for recovered scalar seeds, yielding854 exact/10 mismatch. It is reconstructible via tools/emulation/fixtures/kirakira_unordered_fade_C55.patch.

The remaining first mismatch is matrix528:81 differing output words/312 bytes, first word0 AEX0000803f/Mac01000000. Its fade-only public-bound trace first has reduced-source NaN-sign difference at word6, then seed word1 AEX00000000/Mac0000c07f, with two seed-word differences. Static constructor FUN_18114ec60 at18114ed18/18114ed30 and18114ed38/18114ed3b performs COMISS/CMOVB twice: compare G against B first, then R against the chosen value; select the second operand for unordered or less-than, and retain the first for equality. The former std::max initializer-list scan used different order and unordered selection. The final recovered branch uses G>=B?G:B, then R>=selected?R:selected, preserving the original equal/zero behavior.

The complete operation patch (kirakira_unordered_scalar_C55.patch, applied to base44f3b1b6) yields864/864 exact, plus108 independent boundary conditions exact. Corrected traces15/528 are public-bound and output-exact. Trace15 seed is exact; trace528 retains a one-word NaN-sign seed difference. Both retain source/ray NaN signs, while glow/glow_full/composition/output are exact. These raw differences are reported, not tolerated or called equal. Historical seed102/index20 Gaussian and index55 box approximation traces are public-bound and exact at every paired stage.

Disassembly with AEX hash and instruction bytes is retained in approx/constructor-disassembly.txt. The AEX and F46 worker identities match the prior cluster reports. Both refuted hypotheses yielded new boundary values; the stop condition of two refutations without a new boundary did not occur.

The both-route corpus sample audit has140 comparisons, zero changed samples and zero changes away from exact. No expectations were modified.

Final production repeats864 ordinary+108 boundary conditions, all exact;8 nonfinite-source negatives refuse. Seed1 remains287/0/13 and seed106286/0/14; fresh seed107 improves288/0/12 to289/0/11 (index10). The campaign verifier passes900 sanitized Smart renders, preserves all861 prior exact Smart result objects, and a separate comparison preserves all900 Classic result objects. Public Fade Out is scaled before tuple validation; seed107 case10's public slider1 becomes0.1, within the existing bound. No Fade Out limit was widened.

Historical S01 before/after replay uses each revision with ASan/UBSan and archived F46 hashes:1159 exact/41 refusal becomes1162 exact/38 refusal. All1159 former exact hashes are preserved; new exact rows are102/20,102/55,103/26. This is2400 candidate renders against cached original hashes, not2400 new AEX renders. The verifier now accepts --source to reproduce both sides explicitly.

Corpus before/after: production8 unchanged, T06 62 unchanged. Both-route sample audit140 unchanged. Saved production replay8/8 passes with its retained worker provenance (distinct from campaign F46); no rebaseline.26 existing fast tests and the compiled54-row ASan/UBSan test pass (one unittest,46.042s). Python syntax, fixture reconstruction and git diff --check pass. Final source SHA256ac0f133785090baf85bca2b2df78979e2a268b7c43f676857822d77ea20be40d. Compressed reports, uncompressed hashes, test logs and disassembly are in C55-kira-smart-r2/approx/.

inference:

Finite extreme resize can create NaNs; reproducing their original comparison flow is necessary even when every input component is finite. The two original instruction sequences explain the measured seed/output discrepancies, and the corrected independent matrices support the general fix. This does not establish arbitrary nonfinite source admission, Fade Out above existing limits, native AE or unrestricted host layouts.

changed_files:
- mac/OLMKiraKira/OLMKiraKira.cpp
- tools/emulation/verify_kirakira_history_C50.py
- tools/emulation/fixtures/kirakira_unordered_fade_C55.patch
- tools/emulation/fixtures/kirakira_unordered_scalar_C55.patch
- This report, final ticket report, and approximation evidence.

verify:

Run at the final cluster commit from the worktree. Exact reproduction of experiments and matrices:

```sh
s="$PWD/orchestra/state/C55-kira-smart-r2/recheck-approx"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
git show 44f3b1b6:mac/OLMKiraKira/OLMKiraKira.cpp > "$s/base.cpp"
patch -o "$s/fade.cpp" "$s/base.cpp" < tools/emulation/fixtures/kirakira_unordered_fade_C55.patch
patch -o "$s/fixed.cpp" "$s/base.cpp" < tools/emulation/fixtures/kirakira_unordered_scalar_C55.patch
for revision in base fade fixed; do
 python3 tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-approx --source "$s/$revision.cpp" --gate-off --scratch "$s/$revision-matrix" --report "$s/$revision-matrix.json" > "$s/$revision-matrix.log" 2>&1
done
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-approx --require-exact --scratch "$s/production" --report "$s/production.json" > "$s/production.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-approx --boundary --require-exact --scratch "$s/boundary" --report "$s/boundary.json" > "$s/boundary.log" 2>&1
python3 tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-approx --negative --scratch "$s/negative" --report "$s/negative.json" > "$s/negative.log" 2>&1
py='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
"$py" tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-approx --source "$s/base.cpp" --trace-index 15 --gate-off --scratch "$s/trace15-before" --report "$s/trace15-before.json" > "$s/trace15-before.log" 2>&1
"$py" tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-approx --source "$s/fade.cpp" --trace-index 528 --gate-off --scratch "$s/trace528-fade" --report "$s/trace528-fade.json" > "$s/trace528-fade.log" 2>&1
for index in 15 528; do
 "$py" tools/emulation/probe_kirakira_filtered_C50.py --domain scalar-approx --trace-index "$index" --require-exact --scratch "$s/trace$index" --report "$s/trace$index.json" > "$s/trace$index.log" 2>&1
done
python3 tools/emulation/audit_kirakira_numeric_corpus_F09.py --both-routes --before-source "$s/base.cpp" --scratch "$s/samples" --report "$s/samples.json" > "$s/samples.log" 2>&1
git diff --check
```

Expected experiment counts:base788/76, fade854/10, fixed864/0. These initial failing matrices intentionally omit --require-exact; failed outputs remain refused in the base production policy. Corrected focused traces must be public_bound=true and final exact, with internal differences as recorded above.

Additional final verification, following the scratch setup above:

```sh
for seed in 1 106 107; do
 python3 tools/emulation/verify_kirakira_admission_F10.py --campaign-source "$s/base.cpp" --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/before-$seed" --report "$s/before-seed$seed.json" --corpus "$s/before-corpus$seed" > "$s/before-$seed.log" 2>&1
 python3 tools/fuzz/run.py --plugin olmkirakira --n 300 --seed "$seed" --jobs 1 --shrink-attempts 0 --shrink-seconds 0 --scratch "$s/after-$seed" --report "$s/after-seed$seed.json" --corpus "$s/after-corpus$seed" > "$s/after-$seed.log" 2>&1
done
python3 tools/emulation/verify_kirakira_smart_C04.py --before-source "$s/base.cpp" --campaign-dir "$s" --seeds 1 106 107 --scratch "$s/audit" --report "$s/audit.json" > "$s/audit.log" 2>&1
python3 tools/emulation/verify_kirakira_history_C50.py --source "$s/base.cpp" --scratch "$s/before-history" --report "$s/before-history.json" > "$s/before-history.log" 2>&1
python3 tools/emulation/verify_kirakira_history_C50.py --scratch "$s/history" --report "$s/history.json" > "$s/history.log" 2>&1
python3 tools/fuzz/run.py --plugin olmkirakira --jobs 1 --replay tests/fuzz_corpus/olmkirakira --scratch "$s/replay" --report "$s/replay.json" --corpus "$s/replay-corpus" > "$s/replay.log" 2>&1
```

Expected campaign/history/corpus counts are above. The final ticket report includes the exact fast/compiled test commands.

next:
- Three clusters closed; stop as requested.
- Follow-up: successful-oracle nonfinite scalar/color box-source refusals, beginning fresh seed107/index12 and20. Preserve the other nine original rejections as reference boundaries.


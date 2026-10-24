status: blocked
summary:
- Reduced the cropped/downsampled PF32 mismatch to one negative-alpha pixel, zero origin/angle/strength/noise, Size Variation 40, and Back Alpha Fade 6 at 1/3 scale.
- Located two interacting differences: a clamped zero component maximum and missing x86 wrapping-sign semantics in the alpha prepass.
- A rejected candidate fixes the witness and passes 600/600 PF32-focused comparisons, but exposes heap-buffer-overflow in six small-fade ASan cases.
- Original prepass reads beyond generated fade weights; the original backing-storage initialization/lifetime is not yet proven. No zero-fill assumption was shipped.
- Production sources are restored byte-for-byte to the starting commit. Five labelled baseline witnesses and all investigation evidence are committed; acceptance remains blocked.

facts:
- Starting commit: `a3b3b263f7cea3a92013f935bd9879762c1d4e28`. Read AGENT_GUIDE, GOTCHAS, compatibility plan, DirectionalBlur ledger row, P02j and P05a evidence. Memory free observed 62% initially and 57% later; scratch observed below 9 MiB. At most two task-owned build/emulator runs were active. No oracle rebuild, MAIN/oracle source write, release gate/ledger edit, push, or stash.
- Original AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`; F52c SHA256 `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`. Reference paths/provenance are retained in the case and campaign JSONs.
- `python3 orchestra/reports/P06a-evidence/reduce.py`: 65 bounded greedy attempts, 16 accepted reductions. Original 7x5 witness reproduces six differing float words: expected first bytes `2ba6b6bd`, actual `8c9cd9be`; original SHA256 `cad415cde5b57805cf2cccfc4a01282c0105868619f51016984a6d7b8d015ed2`, Mac `526ce74f6cb8e1bbfe6ec36c9c7a524557f423ef943a85573c2151d9bd99ef60`.
- Reduced case: 1x1 input, full layer 3x3, request `[0,0,1,1]`, scale 1/3, first source pixel retained. Three float words differ: expected first bytes `b34397bf`, actual `9b5fc8bf`; original SHA256 `b26979abe7da488ab8538cf1d806bb28c94d7ad87f55b9b67a011d51738555ae`, Mac `fc4e38b8bed90940640770ce5d69aeebd44d7460d11e5b2a26c26e05c37615fb`. This is a bounded reduction, not a minimality proof.
- `python3 orchestra/reports/P06a-evidence/probe.py`: baseline and zero-divisor-only candidates each retain four mismatches among six focused cases. Zero/positive-alpha controls are exact. The combined zero-divisor/wrapping candidate is exact in all six, including the original and an unscaled reduced case. The old candidate experiment is retained separately in `wrapped-probe.json`.
- `stages.py` (MAIN emulation venv, commands below): original Python Unicorn fixture output is byte-identical to F52c for the reduced signed input. This is an independent instrumented fixture, **not an F52c intermediate dump**. The retained F52c session emits final typed pixels; its watch CLI decodes PNG through RGBA8 and cannot carry this signed input. Neither oracle was rebuilt or modified.
- Paired stages: 5x5 work plane, source offset `(2,2)`, angle `1.5707963705062866`; Back Alpha Fade 6 becomes count 2. Original component divisor is zero. Populated plane, rotated plane, component map and generated weights match. Before correction, row-output differs in four words, denominator and alpha-max in one word each, writer-plane in four words. Combined candidate matches every captured stage. Per-stage SHA256 and first differing word are in `stages-before.json` / `stages-after.json`.
- `static_evidence.py`: AEX `0x61f6` stores the component maximum without a nonzero floor. `0x10a8` converts the NaN-scaled backward count with CVTTSS2SI, producing INT32_MIN. `0x1234 CMP` / `0x1237 CMOVS` clips using the sign bit of the 32-bit subtraction, not an overflow-aware signed less-than comparison. With start 2 and backward INT32_MIN, the wrapping result is negative and the original selects start 2. Ordinary C++ signed subtraction has undefined overflow. See `disassembly.txt`.
- **Blocking new boundary:** `edge.py --sanitize` builds the rejected candidate in scratch with ASan+UBSan. Six of 12 cases abort with `AddressSanitizer: heap-buffer-overflow` in `accumulate_prepass`; six are exact. First failing case: PF32 1x1 `ARGB=(-1,.25,.5,1)`, scale 1, Size Variation 40, Back Alpha Fade 1. Its backward prepass reads weight index 1 from a one-float Mac allocation. Normal unsanitized runs are 12/12 exact, and eight larger 101x1/201x1 controls also happen to be exact; those outcomes do not validate the invalid reads. Sanitizer diagnostics are in `edge-sanitized.json`.
- The original Back Alpha Fade table starts at context+`0x7ee8`; the next field starts at `0x8078` (100 float slots later). `FUN_180001830` writes only the requested number of weights. The inspected Smart caller initializes selected fields rather than clearing the entire large context; `storage-excerpts.txt` retains both functions. The independent fresh Python fixture observes the remaining 98 slots as zero for the reduced count-2 case (`fade_back_storage_hex`), but this does not establish their value/lifetime in F52c sessions or reused host stacks. The original NaN path can walk farther than the generated count, and sufficiently wide rows can cross the table's physical boundary.

The following measurements concern the **rejected candidate**, not the final restored production sources:

| Campaign | Seed(s) | Cases | Smart exact | Smart mismatch | Mac-only refusal | Oracle unavailable |
|---|---|---:|---:|---:|---:|---:|
| default | 1 | 300 | 298 | 0 | 0 | 2 |
| realistic-v1 | 1, 2053, 2069 | 300 | 300 | 0 | 0 | 0 |
| realistic-v2 | 1, 2053, 2069 | 300 | 300 | 0 | 0 | 0 |
| odd-even-v1 + realistic-v1 | 2026 | 150 | 149 | 0 | 0 | 1 |
| odd-even-v1 + realistic-v1 | 2027 | 150 | 147 | 0 | 0 | 3 |
| PF32-only downsample + cropped request, v1/v2 | 1, 2053, 2069 each | 600 | 600 | 0 | 0 | 0 |

- `acceptance.py` uses the standard CLI, `--jobs 1`, and recorded T15b max-size/height flags. Default output hashes all match P05a's default baseline, with zero exact-to-nonexact changes. Default unavailable indices remain 274/289; odd-even 2027 indices remain 5/50/54. Odd-even 2026 index 92 also timed out in this shared-load run; it was not retried or counted exact. Thus the full requested acceptance is not achieved even aside from ASan. Noncontract Classic mismatches/refusals remain visible in JSON; they are not presented as Smart failures or conformance.
- `sweep.py` filters the unchanged versioned generator for depth 32, downsample-X denominator >1, and request area smaller than input area. It collects n100 for each of three seeds on both v1 and v2 (600 total); case indices, profiles, geometry and provenance are committed. It does not silently replace failed samples.
- `unit_tests.py --label before` / `--label after`: 39 files, 7 pass / 32 fail before, 9 pass / 30 fail with the candidate; no pass-to-fail changes. The two improvements were baseline build failures from absent worktree `Util/AEGP_SuiteHandler.cpp` / `MissingSuiteError.cpp`; the bundle builder subsequently created the SDK links. These are environment changes, not claimed numerical fixes. Historical test failures remain retained with diagnostic tails.
- `measure.py --label before --build` and `--label candidate --build`: unchanged P00b driver, one job, default/corpus09, 1080p/4K, all depths. Corpus09 times below; each is one SDK-host render on the shared machine, not native AE timing. Maximum observed increase is 6.81%, below 10%.

| Depth | Baseline 1080p s | Candidate 1080p s | Baseline 4K s | Candidate 4K s |
|---|---:|---:|---:|---:|
| 8 | 1.265772 | 1.338264 | 5.415644 | 5.630684 |
| 16 | 1.312209 | 1.362559 | 5.299933 | 5.561034 |
| 32 | 1.244549 | 1.329195 | 5.528759 | 5.614311 |

- Candidate patch was saved as `rejected-candidate.patch`, then both production files restored from the starting commit. The original mismatch therefore remains. No existing corpus expectation was changed. `corpus.py` saves five labelled **baseline** cases, including negative/zero/positive-alpha controls.
- Final `acceptance.py --replay-only`, after restoring production: all 303 standard saved outcomes replay true on both routes: root 83, P02j 200, T15b 4, P04b2 4, P05a 7, P06a 5. Replay true deliberately includes retained mismatches; it is not a zero-mismatch assertion.

inference:
- Crop origin and downsample are not necessary triggers. The smaller boundary is an empty positive-alpha component mask with nonzero negative-alpha samples and Size Variation/Alpha Fade enabled.
- The observed correction needs both zero-divisor propagation and x86 sign-flag behavior. Neither should be patched at final output bytes.
- Restoring just those arithmetic rules activates invalid Mac table reads that ordinary tests can accidentally pass because adjacent memory happens to look like negligible float weights. Shipping that patch would be unsound.
- Zero-padding the original table tail might match a fresh emulator stack, but is not established as the AEX's initialization rule. Extending zeros past the original 100-slot region would be an invented memory model. Stopped at this newly measured backing-storage boundary rather than silently choosing one. The two-hypothesis stop threshold was not reached without new evidence; the blocker is the unproven original backing storage and unsafe candidate.

changed_files:
- `orchestra/reports/P06a-directionalblur-pf32-cropped-mismatch.md`
- `orchestra/reports/P06a-evidence/` (reproduction scripts, static excerpts, candidate patch, paired stages, campaign/unit/performance evidence)
- `tests/fuzz_corpus/olmdirectionalblur/P06a-investigation/` (five baseline witnesses)
- No production source, existing corpus, ledger or release gate changes remain.

verify:
From this worktree, sequentially:
```sh
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/orchestra/state/P06a-directionalblur-pf32-cropped-mismatch"
export TMP="$TMPDIR" TEMP="$TMPDIR"
mkdir -p "$TMPDIR"
python3 orchestra/reports/P06a-evidence/reduce.py
python3 orchestra/reports/P06a-evidence/probe.py
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/P06a-evidence/static_evidence.py
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/P06a-evidence/stages.py
P06_VARIANT=candidate '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/P06a-evidence/stages.py
python3 orchestra/reports/P06a-evidence/edge.py
python3 orchestra/reports/P06a-evidence/edge.py --sanitize
python3 orchestra/reports/P06a-evidence/acceptance.py --replay-only
git diff --check
```
Expected: reduction preserves the mismatch; focused baseline/zero-only 2/6 exact each versus combined 6/6; both instrumented fixture runs match F52c raw, candidate stages all match; edge normal 12/12 exact but sanitized 6 exact / 6 ASan errors; all 303 saved replay outcomes true. Scripts freeze the baseline cores and build candidate experiments only in scratch. The sanitizer driver intentionally records failures rather than hiding them behind its process exit code.

To reproduce the archived candidate campaigns/performance, apply `rejected-candidate.patch` **only in a disposable review worktree**, then run `acceptance.py`, `sweep.py`, `unit_tests.py --label review`, and `measure.py --label review --build`. Standard campaign CLI exit 0 is not proof of acceptance; inspect per-route summaries. Do not merge the rejected patch.

next:
- Follow-up: obtain typed Smart F52c observations of the full fade-table backing region before generation and at prepass, including repeated renders/stack reuse and reads crossing context+0x8078. This needs an approved reference tracing capability; no oracle rebuild is authorized in this ticket.
- Determine the intended contract for original uninitialized/out-of-table reads before implementing storage semantics. Then restore zero-divisor and CMP/CMOVS behavior together with safe, evidence-backed weight access, rerun ASan boundary matrix and the full acceptance suite, and promote the retained witnesses only after exact results.
- Odd-even 2026 index 92 needs an isolated timeout recheck; inherited unavailable originals and historical unit fixture failures remain separate from this numerical cause.

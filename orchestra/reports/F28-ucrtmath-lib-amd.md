status: partial

summary:
- Added an isolated, AMD-derived arm64 candidate library with explicit FMA modes and contraction disabled.
- Built native arm64 producer and x86_64 Rosetta oracle comparator; tested targeted inputs.
- expf: 4,129 inputs, zero mismatches in both modes. atan2f: 9,178 inputs, 650 mismatches in each mode.
- Stopped at the first failing comparison as required; powf validation, full sweeps, and remaining-import survey were not run.
- Candidate is not qualified for integration; the first failure has an unsigned-negation cause candidate.

facts:
- Branch: `orch/F28-ucrtmath-lib-amd`. Read AGENT_GUIDE.md, F27c report, emulation GOTCHAS and compatibility plan. No plugin code was in scope.
- `memory_pressure | tail -5`: system-wide memory free 54% before building/testing.
- `clang --version`: Apple clang 17.0.0 (clang-1700.6.4.2), target arm64-apple-darwin24.6.0.
- Cloned AMD into ticket scratch and checked out `29fd054f383e6c5e2dec2fce781d5220059f1836`. Original source hashes are committed in `ucrtmath/upstream.json`; copyright/license headers retained, NOTICE added. Only three scalar implementations, their expf data declaration and referenced tables are vendored.
- `sh ucrtmath/tests/build.sh orchestra/state/F28-ucrtmath-lib-amd/build`: exit 0, empty compiler log. `file` identifies producer as Mach-O arm64 and comparator as Mach-O x86_64.
- `python3 ucrtmath/tests/targeted.py orchestra/state/F28-ucrtmath-lib-amd/targeted`: exit 0; generated expf 4129, atan2f 9178, powf 75095 input pairs. Includes the 26 retained paper rows (deduplicated in sets), selected F27c witnesses, sign/NaN combinations, near-one and normal/subnormal boundaries, exp cutoffs, integer/half-integer powers, and atan exponent-gap cases. This does not import every F27c capped witness.
- Exact numerical commands run, sequentially, for `fn=expf` then `fn=atan2f`:
  `orchestra/state/F28-ucrtmath-lib-amd/build/native "$fn" file 0 < "orchestra/state/F28-ucrtmath-lib-amd/targeted/$fn.txt" | orchestra/state/F28-ucrtmath-lib-amd/build/compare /Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll "$fn" > "orchestra/state/F28-ucrtmath-lib-amd/targeted-$fn.json"`
  The surrounding shell printed the JSON afterwards; its final exit 0 is not a numerical pass. The retained comparator counts are the evidence.
- expf: 4129 inputs / 8258 mode comparisons; mismatches 0/0; no first mismatch.
- atan2f: 9178 inputs / 18356 mode comparisons; mismatches 650/650. First input `00000001 00000001`: both oracle modes `3f490fdb`; both candidate modes `e12aaaab`. Results retained verbatim in `ucrtmath/tests/results/`.
- UCRT loader checks DLL SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`. Both images explicitly set and check FMA masks, MXCSR 0x1f80. No DLL or oracle edits.
- Executable/artifact SHA256 at testing: native `47dfc5035136b0906663b87bc43a5c5b584f06604292a7ddf54e0be2c8f3e1cb`; compare `a43f3c0300a09033a9cf5d4e341b3175d607cec30b0e96c658b3cbb1743d3e27`; library `0211048615897b16798a05ccaaf34baff9a909d0ee5aa3777452cae913ffbd1b`. Build artifacts are regenerable and not committed.
- Read-only PE inspection confirmed fused-operation boundaries recorded in `ucrtmath/README.md`. The source changes use AMD expressions/coefficient tables with explicit fma calls; no Microsoft code or binary data is committed.
- Implementation changes include sNaN quieting, rounded pow log index, double underflow cutoff comparison, excluding NaNs from odd-power sign adjustment, explicit negative domain NaN bits on arm64, atan NaN priority and widened exponent classification. Their general correctness is not established by this partial test.
- Per the step-2 mismatch stop, no fixes or additional numerical runs were made after the atan failure. The two-refuted-hypotheses stop was not reached. No tolerance or per-input output correction was used.
- Cleanup: removed the regenerable AMD checkout and all local object/archive/executable outputs. Scratch remaining: 1,596,305 bytes; library/test deliverables approximately 71 KB, below the 5 MB committed-results limit. No started background process remains. Final edits after the stop were documentation, replay instructions, and whitespace only.
- Full expf 2^32 × 2 modes: NOT RUN. atan2f/powf 10^8 × 2 modes: NOT RUN. powf targeted run: NOT RUN. log2f/double sin/cos/exp/pow survey: NOT RUN.

inference:
- The candidate table-reduction expression `madd(mode, 256, v, -index*u)` negates an unsigned index before conversion to double. C unsigned wraparound is a concrete source-level defect and plausibly explains the severe first atan mismatch. This hypothesis has not been repaired/retested under this ticket, in obedience to the mismatch stop. It is not a claim that all 650 failures share that cause.
- F27c's subnormal exponent-gap diagnosis is supported by widened exponent classification observed in the oracle, but this candidate's subnormal compatibility is not qualified while atan2f fails.
- Expf's targeted pass is not an exhaustive-equivalence claim. Powf is a built, untested candidate.
- Sinf/cosf still warrant separate disassembly-guided work based on F27c. No recommendation that AMD matches log2f or any double import is possible without the deferred survey.

changed_files:
- `ucrtmath/include/ucrtmath.h`: explicit-mode API.
- `ucrtmath/src/{expf.c,powf.c,atan2f.c,expf_data.h,tables.c,internal.h}`: standalone candidate and portable helpers.
- `ucrtmath/{build.sh,NOTICE,upstream.json,README.md}`: build, provenance and limitations.
- `ucrtmath/tests/{native.c,compare.c,build.sh,targeted.py,reproduce.sh}`: bounded producer/comparator and deterministic targeted inputs.
- `ucrtmath/tests/results/{targeted-expf.json,targeted-atan2f.json}`: actual failure/pass counts.
- `orchestra/reports/F28-ucrtmath-lib-amd.md`.

verify:
```sh
sh ucrtmath/tests/reproduce.sh
```
Expected: **exit 1**, stopping at atan2f; expf 4129 inputs with 0/0 mismatches, atan2f 9178 inputs with 650/650 mismatches and first witness above. The script builds with scratch TMPDIR and serializes the small target stream so producer failures cannot be hidden by a pipeline. It was added after stopping and was not rerun; its component build/generator/comparison commands were run as described above.

```sh
cmp ucrtmath/tests/results/targeted-expf.json orchestra/state/F28-ucrtmath-lib-amd/targeted-expf.json
cmp ucrtmath/tests/results/targeted-atan2f.json orchestra/state/F28-ucrtmath-lib-amd/targeted-atan2f.json
```
Expected: both exit 0 after reproduction.

next:
- Fix the unsigned-negation cause in a follow-up, rerun targeted validation, then investigate any remaining mismatch without per-input patches.
- Validate all F27c witnesses, powf special/near-one/boundary behavior and paper cases. Harden the full harness with expected stream counts, truncated-record rejection and resumable hash-bound checkpoints.
- Only after targeted success, run requested exhaustive expf and 10^8 binary campaigns in both modes; report zero or stop on actual mismatches.
- Run the untouched remaining-import survey separately: exhaustive log2f and 10^8 double sin/cos/exp/pow plus documented plugin ranges, comparing UCRT, AMD and native arm64 Apple.

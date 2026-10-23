status: done

summary:
- Implemented OLM-internal binary64 `ucrt_sin`, `ucrt_cos`, and `ucrt_exp` in independent C derived from pinned UCRT algorithm observations.
- All three functions pass 1,000,000,000 random bit patterns and 100,000,000 requested-range inputs per function, in both FMA modes, with zero mismatches.
- Expanded reduction/special/subnormal/overflow/underflow boundary corpora also pass in both modes; exact counts below.
- Native arm64 uses contraction-off compilation and explicit FMA; constants have RVA provenance and retained source/build/result identities.
- No worker, plugin, release gate, ledger, MAIN, AMD implementation, or Microsoft binary was modified or committed.

facts:
- Read AGENT_GUIDE.md, tools/emulation/GOTCHAS.md, compatibility plan, scoped ledger UCRT references, F42 policy/how-to-derive, F42 implementation/report, F43 report, and existing qualified Rosetta/F28 harness code. Branch: `orch/F43b-ucrtmath-ms-double-trig-exp`; initial working tree was clean.
- `memory_pressure` reported 48% system-wide memory free before implementation/build. Scratch stayed below 5 GiB (111 MiB observed after qualification). Campaigns were serial with at most two mathematical processes, bounded 4096-record streams, no retained full output arrays, and no worker rebuild.
- Read-only Capstone/pefile inspection used MAIN's existing Python environment and `/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll` in place. DLL SHA256: `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`. The loader remains unchanged and checks the DLL hash and FMA mode masks 0/3; comparator sets MXCSR 0x1f80.
- `python3 ucrtmath/ms/check_double.py` exited 0: the initial pilot passed 1,000,000 random and 1,000,000 range inputs per function in both modes, plus initial boundary corpora (sin/cos 2,628,102 each; exp 7,216). No numerical implementation change was needed after this pilot.
- `python3 ucrtmath/ms/check_double.py --full --no-build` exited 0. It ran all requested random/range comparisons, with the initial boundary generator. `python3 ucrtmath/ms/check_double.py --kind boundary --no-build` then exited 0 with expanded boundary coverage. The current generator produces those expanded corpora in ordinary `--full` runs.

| Function | Random inputs | Range inputs | Expanded boundary inputs | Non-FMA mismatches | FMA mismatches | Random / range seconds |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| sin | 1000000000 | 100000000 | 2651476 | 0 | 0 | 65.872 / 4.587 |
| cos | 1000000000 | 100000000 | 2651476 | 0 | 0 | 65.382 / 10.591 |
| exp | 1000000000 | 100000000 | 1316570 | 0 | 0 | 85.209 / 2.861 |

- First mismatch: none in any numerical campaign. Counts are inputs per function; every input is checked in both modes. No tolerance, expected-result substitution, host sin/cos/exp call, or per-case fix is used.
- Random generator: SplitMix64(index XOR 0xf43b), all 64 bits. Range generator maps the top 53 bits to [-64,64) for trig and [-745,710) for exp. Upper endpoints are included separately in boundary windows.
- Boundary inputs include both signs; ±128 raw-word windows around pi/2 multiples 1..4096 and pi/2*2^e for e=13..1023; mode/branch thresholds; dense windows around powers 2^-1074 through 2^-1022; zeros, infinities and selected NaN payloads; ±4 words around every exp integer-reduction boundary n*ln(2)/64 for n=-68800..65536; and ±4096 words around all three exp saturation cutoffs. Integer intervals are merged and streamed without a corpus-sized output array.
- `python3 ucrtmath/ms/check_double_harness.py` exited 0: all 15 valid/mismatch/short/truncated/empty stream tests had the expected exits (0/1/2/2/2). Deliberately corrupting one native result is detected only in the corresponding mode. Existing float regressions all passed, both modes: sinf/cosf/log2f 106167 each, expf 8128, atan2f 13779, powf 79201 inputs.
- `python3 ucrtmath/ms/retain_double.py` and `python3 ucrtmath/ms/retain_double.py --check` both exited 0: nine double campaigns, 15 stream tests, six float regressions, and source identities matched retained evidence. Numerical evidence and source/build/DLL hashes are committed under `ucrtmath/ms/results-double/`.
- Compiler: Apple clang 17.0.0 (clang-1700.6.4.2). `file` identified double_native as arm64 and double_compare as x86_64. Library flags are `-arch arm64 -std=c11 -O2 -ffp-contract=off -fno-fast-math`. `nm -u .../ms-double.o` listed only stack-check symbols, no host transcendental dependency.
- Read-only table audit matched all three 64-double exp tables byte-for-byte at their recorded RVAs; all 149 retained 2/pi bytes matched both the SSE and FMA reference windows. Minimal constant/threshold provenance and algorithm descriptions are in `ucrtmath/ms/README-double.md`; `inspect_double.py` reproduces local read-only inspection without committing instruction listings.
- No numerical hypotheses were refuted, no stop condition was reached, and no tool permission was rejected. All started processes exited. Regenerable build directory was removed after recording identities; logs and reproducible small corpora remain in ticket scratch. `git diff --check` passed.

inference:
- These results qualify the requested sampled raw-binary64-return contract against this pinned, qualified Rosetta UCRT oracle in both modes. They do not prove exhaustive equality across all 2^64 binary64 patterns or qualify another DLL, floating-point environment, errno, or exception flags.
- Compensated argument reduction, mode-specific evaluation order, and explicit FMA are sufficient for every measured input here. The successful measurements justify retaining the required functional constants, without implying that a host-libm substitution is equivalent.
- This is library qualification only. It is not a new native Windows/AE or actual-plugin equality claim; import reachability and operand widths still need integration witnesses.

changed_files:
- `ucrtmath/ms/double.c`: independent sin/cos/exp algorithms, reductions, special-value behavior and mode-specific evaluation.
- `ucrtmath/ms/double_tables.h`: minimal exp and fixed-point reduction constants.
- `ucrtmath/ms/README-double.md`, `ucrtmath/ms/README.md`, `ucrtmath/README.md`: internal-only policy, provenance, algorithms, validation and limitations.
- `ucrtmath/include/ucrtmath.h`, `ucrtmath/build.sh`: binary64 API declarations and native library object.
- `ucrtmath/ms/{double_native.c,double_compare.c,check_double.py,check_double_harness.py,inspect_double.py,retain_double.py}`: bounded comparison, deterministic corpora, rejection/regression tests, inspection and evidence retention.
- `ucrtmath/ms/results-double/*`: nine double results, six float results, harness results and identity manifest.
- `orchestra/reports/F43b-ucrtmath-ms-double-trig-exp.md`: this report.

verify:
Run serially from this worktree; the driver uses at most two mathematical processes:
```sh
state="$PWD/orchestra/state/F43b-ucrtmath-ms-double-trig-exp"
mkdir -p "$state"
export TMPDIR="$state" PYTHONDONTWRITEBYTECODE=1
python3 ucrtmath/ms/check_double.py --full > "$state/recheck-full.log" 2>&1
python3 ucrtmath/ms/check_double_harness.py > "$state/recheck-harness.log" 2>&1
python3 ucrtmath/ms/retain_double.py --check > "$state/recheck-evidence.log" 2>&1
git diff --check
```
Expected: exit 0 throughout; exact input counts and zero mismatches in both modes as in the table; all 15 stream cases and six float regressions pass. Evidence checker compares numerical results and source identities; timing and rebuilt binary hashes are observational, not acceptance criteria. Remove the regenerable `$state/build` directory after recording any desired local identities.

For read-only derivation inspection (no build required):
```sh
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' \
  ucrtmath/ms/inspect_double.py reduce > "$state/recheck-reduction.txt"
```
Expected: exit 0 after validating the pinned DLL hash; local instruction/constant evidence for both large reductions and moderate FMA reduction. Do not commit the generated listing.

next:
- No implementation or requested library qualification remains for F43b. Double pow remains a separate F43c task.
- A follow-up integration ticket should add the worker import shim and verify the selected UCRT mode, DLL/library/worker hashes, and actual-AEX call boundaries before changing Mac plugin call sites.
- Keep the combined library OLM-internal; do not publish it standalone.

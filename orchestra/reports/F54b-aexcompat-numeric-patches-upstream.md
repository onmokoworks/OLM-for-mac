status: done
summary:
- Ported F29/F30/F32/F44/F45/F46, generic F49 watches and opt-in F50 budgets on stacked AEXCompat branch olm/F54b-numeric.
- All 23 corpus sets / 2,976 saved inputs / 5,649 route comparisons completed: 5,542 successful byte-exact outputs, 107 matching rejections, zero byte/status differences.
- Release tests: 727 passed, 3 ignored; 320,000 retained math-probe rows and eight real-AEX trace runs match.
- Registered immutable worker-F54b with source archive and diagnostic probe; measured all ten plugins at 4K in three depths.
- OLM default oracle, MAIN, plugin code, release gate and ledger unchanged; no claim, push or PR.

facts:

Final AEXCompat HEAD and independent-review boundary:
e96d6ed9b0a8170e1d3d427ac6cf65e07dc3144e.
Branch: olm/F54b-numeric, dedicated sibling worktree AEXCompat-olm-F54b.
Stacked base: 5a9bd8f7f7dd128f2d5c6c037ce3a71a14b7504c.
OLM input baseline: af8cedfa2ba5f9451f0599f6dac05dccfab9ef44.
The source worktree is clean; local commits only.

Final worker:
~/.cache/olm-emu/worker-F54b/aex-guest-worker
SHA256 e9d99f8af2dc5582e4f2faa71211b5ec2af405d26598f483768e3406034deb10.
F53 baseline SHA256:
d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9.
The registered directory also contains source.tar, build.json, f30_import_probe
and probe.json. Its INDEX entry was added under .index.lock. An identical
reinstallation returned reused:true without rewriting its artifacts.
Source/file/archive hashes are retained in F54b-evidence/build.json and probe.json.

Port commits (one initial commit per requested patch):
- 4b4cfc23 F29 SSE first-NaN order, isolated from x87.
- 2ca6c0ef F30 UCRT float imports and retained raw-bit tests.
- 254eea2f F32 legacy DEEP_PIXELS world allocation/clear/disposal.
- 354f52b9 F44 sinf/cosf/log2f.
- 0af40e81 F45 double sin/cos/exp.
- f87245dc F46 double pow.
- d7c03cd7 F50 instruction-budget capability.
- 8cc50590 F49 resident Smart watches with caller-selected RVA.
- Subsequent reviewed commits address portability, production import tests,
  preserved execution defaults/diagnostics, and documentation.

F54 inventory disposition:
F47/F47b/c/d and F51 are OLM native-plugin bridges/standalone hosts, not guest
AEX patches, and were not copied into the guest worker. F52/F52c/F53 are inherited
from F54. C53b and R08 are later, separate experiments outside this inventory.

F50 boundary discovered during replay:
The cached F53 source has MAX_INSTRUCTIONS=0 and TIMEOUT_MICROSECONDS=20000000;
it does not inherit F50. An exploratory always-counting build produced identical
Blur 255x257 PF16 Smart bytes but took 78.135 seconds versus F53's 0.822 seconds.
Its binary hash was not captured; this limited exploratory observation is
separately labeled in F50-counting-observation.json.
Final defaults preserve F53. AEXCOMPAT_INSTRUCTION_BUDGET=1..2000000000 explicitly
selects finite per-slice counting without a wall timeout, at most 257 slices.
Default premature-stop diagnostics also preserve F53 status classification.
A ten-instruction infinite-loop test verifies actual bounded execution.

F49 uses AEXCOMPAT_SMART_TRACE and
AEXCOMPAT_SMART_TRACE_WATCH=hex-rva,decimal-bytes,first|all.
No OLM address is embedded in general code. All eight original-AEX observations
(four retained F49 inputs, first/all occurrence) have exact F53 final outputs;
each pointer has one/two captures as requested, at 1,296–61,504 bytes per capture.
Raw traces remain scratch-only; shareable evidence contains counts and hashes.

Commands and actual results:
- cargo build --manifest-path <AEXCompat-olm-F54b>/guest/Cargo.toml --release -p aex-guest-worker --bin aex-guest-worker --example f30_import_probe -j 1:
  final build succeeded in 51.91 seconds.
- cargo test --manifest-path <AEXCompat-olm-F54b>/guest/Cargo.toml --release -p aex-guest-worker -p olm-ucrtmath -j 1:
  709 worker library + 10 CLI + 8 math tests passed, 3 ignored, zero failures;
  both doc-test groups had zero tests.
- clang -std=c11 -O2 -I<source>/guest/crates/olm-ucrtmath/ucrtmath/include
  <source>/guest/crates/olm-ucrtmath/tests/wide_integer.c -o <scratch>/wide-integer-test,
  then executing it: exit 0, 512 boundary and 100,000 deterministic random cases.
- python3 tools/emulation/aexcompat_patches/validate_F54b.py:
  320,000 raw probe rows match retained F46 in both math modes, both DLL aliases,
  and raw/plugin domains; eight real-AEX trace runs exact.
- python3 tools/emulation/aexcompat_patches/test_install_F54b.py --scratch <ticket-scratch>:
  fresh install, immutable identical rerun including mtimes, changed-HEAD rejection,
  and INDEX-conflict rejection all passed without touching the actual cache.
- Independent local review identified and resolved MSVC-incompatible integer
  extensions, installer provenance overwrites, and default diagnostic drift.
  Final reviewed boundary e96d6ed9 has no accepted outstanding findings.
- Earlier test attempts exposed a stale DEEP_PIXELS rejection expectation,
  a missing RET in the new import test, an overbroad negative-DLL assertion,
  and an ambiguous float test literal. Those test defects were corrected;
  final counts above are measured after all corrections.
- Memory-pressure observations before Rust builds were 44–55% free, above 30%.
  One build job; no more than two task-owned build/emulator processes.
  Rust/Cargo 1.95.0 and Apple clang identities are in toolchain.json.
  The repository's pinned toolchain file was not changed.
- Worker/probe/archive hashes and the unique INDEX binding were rechecked; all passed.
  No task-owned worker processes remained. Regenerable build-F54b and the scratch
  integer-test executable were removed; logs/reports and durable cache artifacts remain.
- git diff --check passed. Native Windows/MSVC, native carrier, Adobe-host,
  whole Rust workspace and CI gates were not executed.

Full saved-corpus equivalence (original AEX through each worker; no Mac candidate):

| Plugin | Comparisons | Successful exact | Matching rejection | Byte differences | Status differences |
|---|---:|---:|---:|---:|---:|
| olmblur | 278 | 249 | 29 | 0 | 0 |
| colorkeep | 842 | 842 | 0 | 0 | 0 |
| olmcolorkey | 88 | 88 | 0 | 0 | 0 |
| olmdirectionalblur | 606 | 606 | 0 | 0 | 0 |
| olmdistancegradation | 908 | 908 | 0 | 0 | 0 |
| olmkirakira | 774 | 773 | 1 | 0 | 0 |
| olmsmoother2 | 224 | 224 | 0 | 0 | 0 |
| olmtoondilate | 1124 | 1124 | 0 | 0 | 0 |
| radialblur | 502 | 501 | 1 | 0 | 0 |
| olmsmoother | 303 | 227 | 76 | 0 | 0 |
| Total | 5649 | 5542 | 107 | 0 | 0 |

Every saved corpus in tests/fuzz_corpus/* was replayed, including realistic,
downsample, gate-off and nested sets, using its stored/reconstructed parameters,
typed pixels and geometry flags. Original Classic and Smart routes were both
compared; Smoother uses its original Classic route only. The retainer checked
the complete expected path/route set for omissions and duplicates, input hashes
were checked by load_corpus, and all worker/AEX identities were bound.
First successful-output mismatch: none. Matching rejections are not successful
numerical equivalence, and diagnostic text itself is not claimed identical.
See corpus-summary.json and corpus-results.jsonl.gz.

4K measurements (3840x2160, deterministic finite constant ARGB, declared default
controls; Smart for nine plugins, Classic for Smoother). Each cell is
status / adapter wall seconds; the final column is maximum worker RSS across
the three depths, measured by /usr/bin/time -l.

| Plugin | PF8 | PF16 | PF32 | Max RSS bytes |
|---|---|---|---|---:|
| olmblur | reject / 20.407 | reject / 20.099 | reject / 20.130 | 748,699,648 |
| colorkeep | ok / 0.789 | ok / 1.407 | ok / 1.232 | 841,678,848 |
| olmcolorkey | ok / 3.974 | ok / 2.925 | ok / 1.951 | 845,070,336 |
| olmdirectionalblur | ok / 0.323 | ok / 0.329 | ok / 0.583 | 840,368,128 |
| olmdistancegradation | ok / 2.660 | ok / 4.343 | ok / 3.113 | 1,170,800,640 |
| olmkirakira | reject / 20.442 | reject / 20.319 | reject / 20.385 | 1,264,304,128 |
| olmsmoother2 | reject / 0.196 | reject / 0.085 | reject / 0.132 | 675,774,464 |
| olmtoondilate | ok / 1.848 | ok / 1.243 | ok / 0.935 | 860,979,200 |
| radialblur | ok / 0.310 | ok / 0.378 | ok / 0.478 | 841,236,480 |
| olmsmoother | ok / 3.711 | ok / 3.148 | reject / 0.064 | 442,187,776 |

Twenty successful measurements and ten rejections:
- Blur and KiraKira: six early guest stops near the 20-second bound.
- Smoother2: three guest C++ exception rejections.
- Smoother PF32: original AEX does not advertise that depth.
An additional existing-F54 Blur control run also stopped near 20 seconds at
all three depths; see 4k-F54-control.json. Previous F54 timings are not reused.
These are single-worker measurements, not 4K byte comparisons. The inherited
driver's equal:false/different placeholders in these rows are inapplicable,
not numerical mismatches; actual render acceptance is results[].status.status.
Measurement-command exit 0 means all measurements were recorded, not all rendered.
All measurements are in 4k-results.json. Timings depend on shared-machine load.

inference:
- F54's observed Blur/RadialBlur numerical and Smoother DEEP_PIXELS gaps are
  closed on every saved corpus here. This is finite original-AEX emulator
  equivalence, not a proof over all possible inputs or native Windows/AE.
- The six near-20-second 4K stops are consistent with the configured wall bound.
  The F54 control demonstrates that Blur's observed 4K failure is not unique to
  this numeric port. No numerical or timeout policy was tuned to hide it.
- The 107 shared rejections and 10 4K rejections remain compatibility/performance
  boundaries. They do not justify an unconditional oracle switch.

changed_files:
- AEXCompat: guest/vendor/unicorn-engine-sys SSE/softfloat policy;
  guest/crates/olm-ucrtmath; worker math imports/callbacks, world allocation,
  execution limits, resident tracing and behavioral tests; Cargo manifests/lock;
  docs/OLM_NUMERIC_COMPATIBILITY.md.
- OLM: tools/emulation/aexcompat_patches/verify_F54b.py, install_F54b.py,
  test_install_F54b.py, validate_F54b.py, retain_F54b.py;
  this report and orchestra/reports/F54b-evidence/*.
- Authorized cache: worker-F54b and its INDEX registration. Default unchanged.

verify:

From this OLM worktree, using the durable workers (no rebuild required):

    export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
    WORKER="$HOME/.cache/olm-emu/worker-F54b/aex-guest-worker"
    for plugin in olmblur colorkeep olmcolorkey olmdirectionalblur olmdistancegradation olmkirakira olmsmoother2 olmtoondilate radialblur olmsmoother; do
      python3 tools/emulation/aexcompat_patches/verify_F54b.py --worker "$WORKER" --plugin "$plugin" --tag=-recheck --jobs 1 || exit 1
    done
    python3 tools/emulation/aexcompat_patches/validate_F54b.py
    python3 tools/emulation/aexcompat_patches/test_install_F54b.py --scratch orchestra/state/F54b-aexcompat-numeric-patches-upstream
    git diff --check

Expected corpus totals: 5649 comparisons, 5542 exact successes, 107 shared
rejections, zero differences. Math/trace: 320000 exact rows / eight exact traces.
Use a fresh --tag when preserving a prior replay. Changing runtime load may
change deadline outcomes; record any such differences rather than accepting them.

To repeat the 4K measurements:

    for plugin in olmblur colorkeep olmcolorkey olmdirectionalblur olmdistancegradation olmkirakira olmsmoother2 olmtoondilate radialblur olmsmoother; do
      python3 tools/emulation/aexcompat_patches/verify_F54b.py --worker "$WORKER" --plugin "$plugin" --mode 4k --route smart --tag=-recheck --jobs 1
    done

Expected: 30 recorded measurements; the measured statuses above are the
reference observation, not a promise of identical runtime-dependent timings.

To rebuild/test, first inspect memory_pressure for >=30% free, set TMPDIR to
this ticket's scratch and CARGO_TARGET_DIR=$HOME/.cache/olm-emu/build-F54b,
then run the build/test commands above with cargo +1.95.0 and one job.
The source archive is durable under worker-F54b. Do not overwrite the registered
binary with a rebuild; installer refuses different artifacts/provenance.

next:
- Orchestrator reviews/merges the local stacked AEXCompat branch and decides
  whether to switch OLM's oracle. This ticket makes no switch.
- Follow up the retained 4K early-stop/exception boundaries and native
  Windows/MSVC/Adobe-host qualification separately.
- ms/ math sources retain their OLM-internal/no-standalone-publication notices;
  Cargo publishing is disabled. This local draft is not publication authorization.

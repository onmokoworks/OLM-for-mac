# OLM Color Key — integrated 2026-11-12 release

## Current direct qualification (2026-11-13)

The final twelve-plug-in workspace candidate passes the **ordinary direct oracle**
using AEXCompat `032a187621353bac7b92a76ae394ac387ddedf51`. No bridge or sparse
fixture is used. Smart8/16/32, downsample 1, 1/2 and 1/4, fresh per-process
renders, at most three concurrent renders. Counts below are **per depth**.

| Reference | Smart8 | Smart16 | Smart32 |
| --- | ---: | ---: | ---: |
| New 64/2025 | 226 exact | 226 exact | 226 exact |
| New 64/2026 sample | 12 exact | 12 exact | 12 exact |
| New original-verified golden | 18 exact | 18 exact | 18 exact |

Zero pixel mismatches, reference/candidate failures or timeouts remain in these
campaigns. Inventory matches the 2025 original. Seeds 20261121/20261122 each supply 110
random plus default/min/max plans: **220 random plans per depth**, and scale totals
76/76/74. Random assignments cover all 1,617 value-bearing controls, including all 599
slots 1025–1623. The old transport/sparse-fixture gates are closed for this corpus.

[Integration report](../../INTEGRATION.md),
[hash-bound qualification](../../evidence/integration-20261112/qualification.json),
[staged identity](../../evidence/integration-20261112/staged-identities.json) and
[golden verification](../../tools/golden/verification.json) are the current
authority. Native AE UI/project acceptance remains unverified. Prior job reports
below retain their original hashes and diagnostic observations as **history**;
their old bridge, harness-limit, pending-golden or local-only hoisting statements
are superseded by the direct evidence above.

---

# OLMColorKey validation — 2026-11-12 upstream update

Measured on Windows x64 on 2026-11-13. **Implementation updated; full upstream
qualification incomplete.** These are headless AEXCompat CPU observations,
native internal-function witnesses and mock-host UI tests, not native AE or
macOS acceptance. [upstream-validation.json](upstream-validation.json) binds
hashes, counts, source files, local evidence and cleanup.

## Declarations and implementation

- All **1,623** public parameters and supplementary raw declarations match
  both new upstream builds; runtime version is 1153024 (2.3.3).
- The entire **294-byte PiPL** matches the new AE 2025 binary. Upstream AE 2026
  uses SDK minor 29 instead of 28; the port intentionally targets 2025 metadata.
- Number of Colors valid maximum changes 25 → 200; slider maximum remains 30.
  All 200 Use Color initial/default values are 1. Existing 223 slots retain
  their IDs/types; eight controls per color are appended. Colors 101–200 have
  separate ID bases (color 101: 824, Use Color 101: 1324). Group ID 16 remains
  intentionally duplicated.
- `ae.rs`, `algorithm.rs` and `build.rs` implement the expanded bounds and
  version. Crate-local `host.rs` preserves checkbox labels and dispatches UI
  updates; `ui.rs` implements the observed enabled/hidden rules for 200 colors.
  Shared crates/tools are unchanged. Numerical arithmetic is unchanged.
- Saved-project compatibility is structural evidence only. Explicitly stored
  old values retain their IDs/types. Default substitution and new instances
  change because Use Color now defaults on; native migration is untested.

## Static and function evidence

The retained U-triage old/new comparison reports 329 unchanged, 52 changed
matches (38 instruction and 14 referenced-data changes), 57 added candidates,
and 56 removed candidates. These are matching results, not semantic edit
counts. No new PE imports were found. Its generic behavioral and sensitivity
runs failed at the harness limit; those are **not equivalence evidence**.

This job's private Ghidra analysis decompiled the new setup `0x1000`, UI
`0x1d90`, parameter reader `0xa940`, Smart dispatch `0x1c20`, render drivers,
pixel callbacks `0x2360`/`0x2f30`/`0x3b30`, and UI helpers. The setup has two
100-color ID loops; the reader has 200-entry arrays and a split at color 101.
The pixel callbacks retain the first matching color for replacement. A fresh
funcdb lookup yields **365 exact, 70 fuzzy, 3 unknown** fingerprints; these do
not establish Rust qualification by themselves.

Native witness results: **48/48 per depth**, 144 total, compare output bytes
and return bits for palette sizes 26/101/126/200, all six spaces, and last-key
versus duplicate-first-key replacement. This directly reaches slots beyond
the broker limit. Separately, the record debugger captured four actual pixel
calls per depth from sparse full renders at the global maxima. All **12/12**
recorded outputs replay exactly with the original and Rust adapters. This is
bounded pixel-callback evidence, not every numerical function or host route.

## Full-render comparisons

The unmodified harness can render sparse declarative fixtures. Unlike the
ordinary oracle, these carry only the supplied parameter records. They compare
packed native output buffers exactly (including float bit patterns).

| Corpus | Smart8 | Smart16 | Smart32 CPU |
| --- | ---: | ---: | ---: |
| New 2025, seed 20261113, 103 cases | 102 exact + 1 candidate session-open failure | 103 exact | 103 exact |
| New 2025, seed 20261114, 103 cases | 103 exact | 103 exact | 103 exact |
| Separate replay of failed 8-bit case | 1 exact | — | — |
| New 2026, seed 20261115, 9 cases | 9 exact | 9 exact | 9 exact |
| Final production rebuild, seed 20261116, 9 cases vs new 2025 | 9 exact | 9 exact | 9 exact |

The two main seeds contain **200 random cases per depth**, plus six
default/global-minimum/global-maximum cases. Their source sizes cycle 1x1,
3x7, 11x7 and 31x19; **downsample is 1 only**. Global controls sample their
declared ranges, including color count 0–200. Eight palette entries are edited:
1, 2, 25, 26, 99, 100, 101 and 125. Other entries retain upstream defaults;
this is not a full 200-color assignment sweep or a per-parameter sensitivity
qualification. Palette assignments in the global extrema cases are seeded,
not themselves all minima/maxima. The 8-bit failure is retained as a failure:
the harness reported session-open OS error 80 (already exists); its separate
exact replay does not rewrite the baseline.

The main corpus candidate is `0577b759…62c7`; the final production rebuild is
`8f54e7fb…dec3`. Their `.text`, `.data`, `.pdata` and `.reloc` bytes match.
Remaining differences are eight source-line fields after formatting, debug
metadata, and ordering of equal Windows version strings. The final build's
declarations/PiPL were recaptured and its separate 27-render smoke is exact.
Diagnostic witness binaries are identified separately in the JSON report.

Four Rust test functions pass: 24,576 existing C++ color vectors, 648 distance
scans/216 boundary masks; last-color/first-match/201-color rejection across
depths and spaces; and 40 UI configurations covering all 200 entries plus an
injected late callback failure. The UI test checks 601 enabled-state and
1,603 visibility updates per configuration, unchanged host parameter structs,
and balanced suites/effect/stream references on success and failure. It is a
mock-host test, not observed native AE UI behavior.

## Remaining gates and tool changes

1. The ordinary oracle was attempted at downsample 1, 1/2 and 1/4: all **three
   cases per depth fail on both sides** before pixels can be compared. The
   broker encoder rejects slots above `MAX_PARAMETERS = 1024` and also caps
   payloads at 16,384 bytes. Raise and qualify the broker/worker transport
   limits consistently (or support sparse default transport), then rerun the
   prescribed unrestricted two-seed oracle and per-control sensitivity sweep.
2. Sparse fixtures expose no general downsample host context. Full renders at
   1/2 and 1/4 remain unverified for this release. Internal pixel calls cannot
   substitute for downsample-dependent edge processing.
3. No residual pixel mismatch was observed, so divergence/minimization and UB
   classification were not invoked. Transport failures are not labeled UB.
4. Golden regeneration is **pending**: the owner tool publishes only successful
   all-ten runs; `--only` is diagnostic and cannot update the manifest. Its
   owner must regenerate the existing **54 ColorKey cases** (18 tuples × three
   depths) against the new original, and should add expanded-palette/default
   witnesses. Shared golden files were not edited.
5. Native AE projects/UI, macOS builds, HDR/nonfinite sources, cropped extents,
   exhaustive interactions and performance on production frame sizes remain
   outside this qualification. Classic is not a declared AE route.

The private hub used port 65292, PID 22620; graceful shutdown verified all six
owned PIDs exited, none forced, none remaining. The initial occupied-port
attempt also exited. No GUI, AE, installation, commits or shared tool edits.

Reproduce from the repository root with a staged candidate (all `--out`
directories must be new):

```powershell
$env:CARGO_TARGET_DIR = 'D:/olm-rs-target/Up-colorkey'
cargo test --manifest-path rust/Cargo.toml --release --offline -p olm-color-key -j 2
python rust/plugins/olm-color-key/verify_update.py inventory --candidate '<candidate.aex>' --out '<new-dir>'
python rust/plugins/olm-color-key/verify_update.py sparse --candidate '<candidate.aex>' --seed 20261113 --cases 103 --out '<new-dir>'
python rust/plugins/olm-color-key/verify_update.py sparse --candidate '<candidate.aex>' --seed 20261114 --cases 103 --out '<new-dir>'
python rust/plugins/olm-color-key/verify_update.py sparse --candidate '<candidate.aex>' --year 2026 --seed 20261115 --cases 9 --out '<new-dir>'
cargo build --manifest-path rust/Cargo.toml --release --offline -p olm-color-key --features upstream-witness -j 2
python rust/plugins/olm-color-key/witness_pixels.py --candidate '<diagnostic.aex>' --out '<new-dir>'
python rust/plugins/olm-color-key/capture_pixels.py --candidate '<diagnostic.aex>' --fixtures '<sparse-corpus-dir>' --out '<new-dir>'
```

All raw binaries, Ghidra output, images, process logs and absolute evidence
paths are local-only under ignored `validation/`. The following pilot record
is historical and refers to the **old** original; it is not new-build evidence.

## Historical F-core pilot

Windows x64 AEXCompat CPU evidence, 2026-11-12; not native AE acceptance.
The original pilot record was in the workspace README. This per-crate index
preserves its claims without attributing the old campaigns to a new build.

| Corpus | Smart8 | Smart16 | Smart32 CPU |
| --- | ---: | ---: | ---: |
| Main, seed 20261113 | 203 exact | 203 exact | 203 exact |
| Palette hits | 48 exact | 48 exact | 48 exact |

Main counts are per depth: default/min/max plus 200 random cases. Sizes cycle
1x1, 3x7, 11x7, 31x19, 97x61; downsample cycles 1, 1/2, 1/4. PNG-promoted
deep inputs include partial alpha and hidden RGB; deep output compares raw words.

[validation-report.json](validation-report.json) binds binary identities, counts,
failures and local artifact paths. [pipl-comparison.json](pipl-comparison.json)
records complete 294-byte Windows resource equality; exposed inventories match
(223 parameters excluding input).
[build-equivalence.json](build-equivalence.json) distinguishes the frozen campaign
binary from later metadata-only rebuilds. Both declare 8/16/32-bit SmartFX.

Cropped demand [1,1,6,5] within 11x7 gave one exact and 11 original-unrenderable
cases per depth (worker invariant failure, fatal session error -43). These 11
are not passes. Forced Classic 8/16 diagnostics returned no valid original
frame (classic_finalize/output validation -6), and are not normal AE dispatch.
Palette-hit aggregation recovered from a Windows sharing error by checking all
144 completed raw comparisons and hashes; no extra renders were counted.

Reproduce from `rust/` after staging with `tools/stage_windows.ps1`:

```powershell
cargo build --release -p olm-color-key
cargo test --release -p olm-color-key
python tools/oracle/olm_oracle.py inventory --reference '<original absolute path>/OLMColorKey.aex' --candidate '<staged absolute path>/OLMColorKey.aex' --out local/olm-color-key-inventory-new
python tools/oracle/olm_oracle.py render --reference '<original absolute path>/OLMColorKey.aex' --candidate '<staged absolute path>/OLMColorKey.aex' --cases 203 --seed 20261113 --jobs 3 --sizes 1x1,3x7,11x7,31x19,97x61 --downsample 1,1/2,1/4 --routes smart8,smart16,smart32 --out local/olm-color-key-render-new
```

The shared supplemental runner is
[validate_pilots.py](../olm-color-key/validate_pilots.py); select `--plugin OLMColorKey`.
Shared foundation/pilot tests included 24,576 color vectors, 648 distance scans,
216 boundary masks, 131,072 numeric probes and 82,080 native UCRT comparisons.
The original two-pilot workspace had 12 passing test functions. Current full
workspace results are recorded separately in [integration](../../INTEGRATION.md).

Native AE, macOS, arbitrary HDR/nonfinite worlds and exhaustive UI/project
compatibility remain unverified. Original UCRT FMA3 was enabled. The historical
worker reported source_newer_than_worker; hashes qualify the installed binaries.
No additional hoisting candidate was recorded for this pilot: common geometry,
world, checkout and parameter helpers already live in the shared crates.

Evidence policy: all `validation/` paths, absolute machine paths, candidate-path
files, rendered images, logs and DLL/AEX paths in this document or its JSON
reports are **local-only evidence**, ignored and not included in Git. The linked
compact JSON files and rerun script are versioned candidates. No original
plug-in binary is included.

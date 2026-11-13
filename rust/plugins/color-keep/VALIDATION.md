# ColorKeep — integrated 2026-11-12 release

## Performance (S-misc, 2026-11-13)

Checked active-row slices and scoped row workers replace per-pixel global-coordinate lookups. RGB matching, unordered comparisons, and alpha-only writes are unchanged. Tests cover cropped/padded worlds, float payloads, palette counts 0/1/200, and empty Smart extents.

Final frozen DLL oracle: 106/106/106 exact at 8/16/32 bpc, out of 106 attempts per depth across seeds 20261130 and 20261201. Downsample 1, 1/2, 1/4; resident batches with per-process authority for every non-exact result; at most two render jobs. No pixel mismatches, failures, or timeouts. Default/min/max plans plus at least 100 random plans per depth; sizes 1x1/3x7/11x7/31x19/97x61.

Workspace release tests: **123 passed, 2 existing opt-in tests ignored**; all **616 original-verified golden hashes** pass, retaining the 14 historical RadialBlur exclusions. Owned-crate fmt and release Clippy pass (existing Clippy warnings retained). Workspace-wide fmt still reports 25 unchanged files outside this job's ownership. Shared row tests preserve padding/short final rows and compare serial/parallel results; the SIMD column test checks 53,592 scalar/vector lane results bit-for-bit.

1080p median selector-time ratio (Rust/original; lower is faster), measured serially against the same originals with the previous Rust build and this build in one session. Each cell has one warm-up and five timed frames; all benchmark output pairs are exact. Shared-machine timings are not native AE measurements.

| bpc | Before default | After default | Before heavy | After heavy |
|---:|---:|---:|---:|---:|
| 8 | 3.895 | 0.483 | 1.616 | 0.202 |
| 16 | 3.761 | 0.401 | 1.651 | 0.150 |
| 32 | 2.782 | 0.506 | 1.469 | 0.189 |

Local-only identities, requests, outputs, logs, fixed replays, and before/after timing samples are retained under `D:/olm-rs-target/misc-evidence/`; `qualification.json` indexes the final evidence and frozen DLL hashes. Rust 1.88.0, Windows x64, ordinary headless AEXCompat; no original binary or run output is committed, and no AE installation is changed.


## Current direct qualification (2026-11-13)

The final twelve-plug-in workspace candidate passes the **ordinary direct oracle**
using AEXCompat `032a187621353bac7b92a76ae394ac387ddedf51`. No bridge or sparse
fixture is used. Smart8/16/32, downsample 1, 1/2 and 1/4, fresh per-process
renders, at most three concurrent renders. Counts below are **per depth**.

| Reference | Smart8 | Smart16 | Smart32 |
| --- | ---: | ---: | ---: |
| New 64/2025 | 30 exact | 30 exact | 30 exact |
| New 64/2026 sample | 12 exact | 12 exact | 12 exact |
| New original-verified golden | 18 exact | 18 exact | 18 exact |

Zero pixel mismatches, reference/candidate failures or timeouts remain in these
campaigns. Inventory matches the 2025 original.

[Integration report](../../INTEGRATION.md),
[hash-bound qualification](../../evidence/integration-20261112/qualification.json),
[staged identity](../../evidence/integration-20261112/staged-identities.json) and
[golden verification](../../tools/golden/verification.json) are the current
authority. Native AE UI/project acceptance remains unverified. Prior job reports
below retain their original hashes and diagnostic observations as **history**;
their old bridge, harness-limit, pending-golden or local-only hoisting statements
are superseded by the direct evidence above.

---

# ColorKeep 1.1.0 — upstream 2026-11-12

Job **Up-colorkeep**, measured 2026-11-13 on Windows x64. These are AEXCompat
CPU observations, **not native AE acceptance**. The historical F-core record
below belongs to the old original and is not evidence for this update.

The primary original is `OLMColorKeep/OLMColorKeep/Plugins/64/2025/ColorKeep.aex`.
The new original, 2026 sample, old original, frozen candidate, source and tool
identities are bound in [upstream-validation.json](upstream-validation.json).
All large artifacts are under ignored `validation/upstream-20261112/`.

## Measured rendering

| New-original comparison | Smart8 | Smart16 | Smart32 CPU |
| --- | ---: | ---: | ---: |
| 2025, seed 20261112, resident | 203 exact | 203 exact | 203 exact |
| 2025, seed 20261113, resident | 203 exact | 203 exact | 203 exact |
| 2025, fresh-process general sample | 12 exact | 12 exact | 12 exact |
| 2025, fresh-process matched palettes | 36 exact | 36 exact | 36 exact |
| 2025, every color control actively matched, resident | 200 exact | 200 exact | 200 exact |
| **2025 plugin comparisons total** | **654 exact** | **654 exact** | **654 exact** |
| 2026, fresh-process general + matched palettes | 48 exact | 48 exact | 48 exact |
| 2025, shared golden pure-render diagnostic | 18 exact | 18 exact | 18 exact |

Zero candidate mismatches, render failures or timeouts in these campaigns.
Each random campaign contains three default/min/max plans and 200 random plans:
**400 random cases per depth over two seeds**. Sizes cycle 1x1, 3x7, 11x7,
31x19 and 97x61; downsample cycles **1, 1/2, 1/4**. Fresh general samples use
3x7, 11x7 and 31x19. Matched palettes use 11x7, both palette-alpha endpoints,
translucent nonblack source colors, and counts 0/1/100/101/199/200 at all three
downsample factors. The active sensitivity campaign separately places a matching
color at **every slot 2–201**, with all 200 colors enabled and the other colors
left at their black defaults.

8-bit comparisons decode PNG samples; 16-bit comparisons use native AE-range
words; 32-bit comparisons use raw binary32 bits. Render sources are PNG-promoted
SDR, including partial alpha and hidden RGB. Resident runs preserve module
state; the 48 fresh-process comparisons per depth/year are separately reported
authority checks, not a claim that the entire random population was rerun in
fresh processes. No resident retries were needed.

## Declaration and function evidence

- Independently inspected and captured old, 2025, 2026 and Rust declarations.
  The primary PiPL resource is byte-identical to Rust; public inventories and
  complete supplemental declarations also match. There are **201 controls**
  excluding input (`num_params=202`). The 2026 SDK minor is 29, versus 28 in the
  primary PiPL; the Rust resource deliberately matches 2025.
- The first 100 palette definitions retain IDs, types, flags and defaults.
  The count retains disk ID 1 and default 1; only its valid/display maxima
  increase. Added colors occupy IDs/slots 102–201. Name/entry/version become
  `OLM Color Keep` / `entry_point` / 1.1.0; match name stays unchanged.
- Reused the completed, hash-bound U-triage old/new report: 36 general and 912
  one-parameter route-cases were exact. Those mostly inactive/no-match probes
  do not establish unchanged matching behavior. Its function matcher reports
  63 unchanged, four changed candidates, 314 added/unmatched and 16 removed/
  unmatched functions; these are compiler-dependent matching results.
- Independently imported both originals into a private Ghidra hub and
  decompiled the old callbacks and ten relevant new functions. Funcdb lookup
  against the existing catalog found **312 exact, 62 fuzzy and seven unknown**
  new functions. No automated reuse classification was treated as proof.

| New 2025 RVA | Role / translated behavior |
| --- | --- |
| `0x1000` | Declare count maximum 200 and append 200 color controls |
| `0x10d0`, `0x1540` | Read active float palette; Smart driver copies the source world before changing alpha |
| `0x1460` | Original dynamic visibility loop extends to 200; existing Rust glue does not implement this UI handler |
| `0x15c0`, `0x1690`, `0x1780` | 8/16/32 callbacks: normalized RGB comparison only; preserve/clear alpha |
| `0x7080`, `0x70f0`, `0x7160` | Binary32 normalization by `0x3b808081` / `0x38000000`, or float-channel copy |

The decompiler prints `<= 0.0001`, but inspected COMISS/JA/JBE instructions
accept unordered comparisons. `pixel` deliberately preserves `!(difference >
threshold)` semantics. It does not replace this with Rust `<=`. Integer
matching no longer quantizes the palette, and alpha no longer participates.

`witness` plus `diverge` compare **320 callback invocations per depth**, including
threshold neighbors, counts through 200, mismatches, alpha differences, PF16
values above nominal white, and bounded float HDR/NaN/infinity/signed-zero
inputs. All 960 mapped outputs and returns are exact. These exercise the three
normalization helpers through their callers. The adapters call production
`color_keep::pixel`; there is no duplicate numerical implementation.

`record` captured six actual Smart-render callback calls per depth. All **18/18**
replayed exactly into both the original witness and the Rust adapter, including
input/context immutability, alpha-only output writes and return values. Capture,
witness and adapter cleanup checks passed. The three full recorded renders are
not added to the paired-render totals above.

The source-matched old/new comparison has **12 intentional differences per
depth**, demonstrating the release's translucent matching change. Minimize
reduced the first Smart8 witness from 11x7 to **1x1** (local minimum under its
documented moves): old alpha **0**, new alpha **1**, with matching RGB. Ubdetect
reported `stable_mismatch / stable_in_tested_trials` across three fresh renders
per side, with cleanup verified and no poisoning profile applied. The reports
are linked in the compact record. These release differences are not Rust
failures or exclusions from exact totals.

## Build, compatibility and remaining limits

`validate_upstream.py build` passed release compilation and all **four unit
tests**. The initial ordinary workspace `--locked` build refused a required
Cargo.lock update. The crate-local private manifest builds the actual production
source and build script, leaving shared files untouched. All builds use
`D:/olm-rs-target/Up-colorkeep`; render concurrency never exceeds two.

The frozen render candidate predates rustfmt-only changes. The later rebuild
has identical `.text`, `.data`, `.pdata`, `.reloc` and PiPL bytes. `.rdata`
differences are debug timestamps/PDB age; other resource metadata and whole-PE
hashes differ. Both identities and section hashes are retained rather than
claiming whole-file equality. Later record/golden adapters compile the formatted
production source.

Old project declaration compatibility is structural evidence only. New
rendering intentionally follows upstream and can change the appearance of old
projects. Native AE project load/save, conditional UI, macOS builds, cropped
demand, custom row padding, temporal behavior, and arbitrary full-render
HDR/nonfinite inputs remain unverified for this update. The original color
visibility handler remains an existing shared-glue gap.

The golden owner tool allows `--only color-keep` **diagnostics**, but publishes
manifests only after an all-plugin run. The 54 existing cases passed against
the new original and their output hashes are unchanged. Shared files were not
edited. The owner must refresh the ColorKeep upstream identity and 54-entry
verification provenance during supported regeneration; the shared corpus also
needs translucent matches and counts 101/199/200. Those cases are already covered
by this crate's supplemental suite. A per-plugin publish mode and a configurable
Ghidra data-directory option would remove the current crate-local workarounds.

The owned hub on port 8791, PID **60092**, stopped gracefully; its retained
shutdown report has `exited=true`, `forced=[]`, `remaining=[]`. No AE/GUI was
launched, no originals were modified or copied, and no shared tool sources,
commits or installations were made.

## Historical F-core pilot (old original)

Windows x64 AEXCompat CPU evidence, 2026-11-12; not native AE acceptance.
The original pilot record was in the workspace README. This per-crate index
preserves its claims without attributing the old campaigns to a new build.

| Corpus | Smart8 | Smart16 | Smart32 CPU |
| --- | ---: | ---: | ---: |
| Main, seed 20261112 | 203 exact | 203 exact | 203 exact |
| Palette hits | 24 exact | 24 exact | 24 exact |

Main counts are per depth: default/min/max plus 200 random cases. Sizes cycle
1x1, 3x7, 11x7, 31x19, 97x61; downsample cycles 1, 1/2, 1/4. PNG-promoted
deep inputs include partial alpha and hidden RGB; deep output compares raw words.

[validation-report.json](validation-report.json) binds binary identities, counts,
failures and local artifact paths. [pipl-comparison.json](pipl-comparison.json)
records complete 294-byte Windows resource equality; exposed inventories match
(101 parameters excluding input).
[build-equivalence.json](build-equivalence.json) distinguishes the frozen campaign
binary from later metadata-only rebuilds. Both declare 8/16/32-bit SmartFX.

The main Smart8 case 168 initially failed to create a resident session (Windows
error 80). Its unchanged saved input/request replay was exact; 203 counts unique
cases, not the extra attempt. Twelve cropped-demand requests per depth were
exact. Forced Classic 8/16 diagnostics had 12 exact each; these are not normal
AE dispatch or part of the main totals.

Reproduce from `rust/` after staging with `tools/stage_windows.ps1`:

```powershell
cargo build --release -p color-keep
cargo test --release -p color-keep
python tools/oracle/olm_oracle.py inventory --reference '<original absolute path>/ColorKeep.aex' --candidate '<staged absolute path>/ColorKeep.aex' --out local/color-keep-inventory-new
python tools/oracle/olm_oracle.py render --reference '<original absolute path>/ColorKeep.aex' --candidate '<staged absolute path>/ColorKeep.aex' --cases 203 --seed 20261112 --jobs 3 --sizes 1x1,3x7,11x7,31x19,97x61 --downsample 1,1/2,1/4 --routes smart8,smart16,smart32 --out local/color-keep-render-new
```

The shared supplemental runner is
[validate_pilots.py](../olm-color-key/validate_pilots.py); select `--plugin ColorKeep`.
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

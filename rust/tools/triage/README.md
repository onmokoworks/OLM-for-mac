# OLM plug-in triage

`olm_triage.py` compares Windows AEX versions and profiles unfamiliar plug-ins.
It imports the adjacent `oracle/olm_oracle.py` for inventory, host flags, seeded
case generation, request construction, exact pixel comparisons and private
Windows Job Object process cleanup. Oracle files and production plug-in sources
are not edited. No AE, GUI, installation, server or external service is used.

## Run

Python 3.11+, `pefile`, NumPy, Pillow, the AEXCompat harness, and Ghidra 12 with
its supported JDK are required. Install Python dependencies from
`requirements.txt` if needed. Ghidra is discovered only at `C:/ghidra_12` and
`C:/ghidra_11`; use `--ghidra` elsewhere. The Java exporter is qualified on
Ghidra 12.0.3; Ghidra 11 API compatibility is not established.

From the repository root (PowerShell):

```powershell
$originals = 'D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex'
python rust/tools/triage/olm_triage.py diff --old "$originals/OLMBlur.aex" --new D:/build/OLMBlur.aex --out rust/tools/triage/runs/update --jobs 2 --cases 12
python rust/tools/triage/olm_triage.py profile --aex "$originals/OLMBlur.aex" --out rust/tools/triage/runs/profile-blur
```

Every output directory must be new. `profile --aex X.aex` also works without
`--out`, choosing a unique directory under `runs/`. Both commands produce
`triage.json` and `triage.md`. Exit 0 means a complete triage report **even when
differences were found**; exit 2 means incomplete evidence or a setup failure;
Ctrl+C returns 130. An unsupported route is not counted as an exact comparison.
Setup failures preserve the diagnostics produced before failure.

Useful options:

| Option | Default / meaning |
|---|---|
| `--harness PATH` | Shared AEXCompat release harness from the common kit |
| `--ghidra PATH` | Ghidra installation or `analyzeHeadless.bat` |
| `--cache DIR` | Optional binary/exporter/installation keyed function-export cache; incomplete analyses are not reused |
| `--cases 12` | Diff only: defaults, minima, maxima, then seeded oracle random cases |
| `--seed 20261112` | Deterministic plans and source images |
| `--size 31x19` | Image dimensions for both sides and all one-control probes |
| `--routes smart8,smart16,smart32` | Default includes all six oracle routes, filtered by each side's advertised host flags |
| `--jobs 2` | Concurrent paired render cases; accepts 1, 2 or 3 only |
| `--timeout 120` | Seconds per inspection/render; also sets the harness frame deadline |
| `--analysis-timeout 300` | Ghidra analysis seconds per image; outer process bound adds 180 seconds for import/export |

Ghidra runs with at most two analysis CPUs, uses read-only temporary projects
under the output directory, and deletes its own projects on normal completion. Failed
project artifacts remain inspectable there. Child process trees belong to
private Windows jobs; normal completion, timeout and cancellation close those
jobs and wait for termination. No executable-name process killing is used.
Ghidra stdout/stderr go directly to files, with the launcher PID recorded before
analysis, so timeout cleanup does not wait for inherited pipe handles to close.
Completed exports from unsuccessful processes remain marked incomplete and are
not cached. Java scripts are snapshotted per invocation; PDB loading is disabled so function
results depend on the supplied image rather than external symbol files.

## What the reports contain

- **Inventory:** every oracle compatibility field, including host flags and
  parameter metadata, plus both original inspections.
- **PiPL:** all `PIPL` resource IDs/languages, raw `.bin` files and SHA-256s,
  every property and its raw bytes, Pascal strings including match name,
  effect/PiPL/SDK versions, flags and declared depths. Unknown properties stay
  visible. Malformed resources are marked incomplete, not silently accepted.
- **Behaviour:** identical seeded images and oracle-generated values on both
  sides. Matching prefers slot + name + kind, then a unique name + kind when a
  control moves. Renamed, ambiguous or retyped controls remain unmatched.
  Explicit values outside the new range are recorded as incomplete rather than
  clamped. Untouched defaults stay omitted, preserving each version's effective
  defaults. New/removed unmatched controls remain at defaults and are listed.
- **Sensitivity:** a common default image with empty assignments, then at most
  three distinct non-default edits per matched control (endpoints and seeded
  alternatives). All other controls remain untouched. The report distinguishes
  mismatches, exact cases, unavailable payload types and failed renders. A
  mismatch exposed from equal defaults narrows the change to a control; it does
  not prove which function implements that control.
- **Binary:** Ghidra-discovered function names, RVAs, byte sizes, normalized
  hashes, instruction-shape hashes, direct calls and callers. Matching uses
  unique symbols, normalized hashes, duplicate-hash multiplicities, then unique
  instruction shapes. Shape matches and ambiguous duplicate identity are
  explicitly labelled. Unmatched functions are added/removed candidates, not
  proof of added/deleted functionality across compilers.
  Changed normalized instructions are distinguished from changed referenced
  data. Function bytes are the sum of discovered function-body sizes, not the
  PE file size or a deduplicated code-coverage measure.
- **Imports:** ordinary and delay PE imports with UCRT/CRT, IPP, OpenCV or other
  categories. SDK suites are dynamically acquired; suite strings are listed
  separately as static presence evidence, not claimed PE imports or observed
  acquisitions. Statically linked IPP/OpenCV code can have no corresponding
  DLL import.
- **Effort hints:** number and bytes of changed/added/removed functions, new
  imports and new/unmatched parameters. These suggest review scope, not hours.
- **Profile:** all of the per-side inventory, PiPL, routes, imports, function
  counts/sizes, largest functions, and one default render at each selected,
  declared depth. Timing is cold process wall time including host startup,
  not an isolated kernel benchmark.

8-bit comparisons decode PNG samples; 16-bit comparisons read the raw LE word
sidecars; 32-bit comparisons compare raw float **bits**, including NaN payloads
and signed zero. Images, per-side requests, logs and comparisons remain under
`behaviour/` and `sensitivity/` so reported differences can be inspected.

## Validation on this machine

Windows runs on **2026-11-12**, Ghidra **12.0.3**, shared AEXCompat harness:

- **21 unittest tests pass**, including named/shape/hash matching, moved and
  ambiguous parameters, range rejection, PiPL alignment/truncation, unchanged
  defaults, owned-process output capture and timeout cleanup.
- **Original versus Rust OLMBlur:** zero inventory/PiPL differences; **57/57
  exact** comparisons: 8 behavioural cases and 11 default/sensitivity cases at
  each of Smart8, Smart16 and Smart32. Seed 20261112, 31×19, downsample 1,
  jobs 2. Binary comparison: 54 normalized matches, 3 changed match candidates,
  570 added/unmatched Rust functions and 40 removed/unmatched original
  functions. Those cross-compiler matches are not semantic-equivalence claims.
- **Synthetic pair:** 634 functions matched, no added/removed functions;
  `triage_legacy_amount` is the **only instruction-changing function**
  (25 → 30 bytes), with caller `180004840`. One other function has only a
  changed referenced-data fingerprint. The 12-case behavioural campaign has
  **11 exact + 1 mismatched per depth**. Sensitivity has **10 exact + 1
  mismatched per depth**; only slot 5, **Legacy**, exposes the change. Defaults,
  inventory and PiPL remain equal. No failed renders are counted in these totals.
- **Relocation regression:** all **634/634 normalized function hashes** remain
  equal after moving the synthetic image base from `0x180000000` to
  `0x190000000` and applying its PE relocation fixups.

The worked original/Rust run was:

```powershell
python rust/tools/triage/olm_triage.py diff --old "$originals/OLMBlur.aex" --new rust/tools/triage/local/OLMBlur-rust.aex --out rust/tools/triage/runs/blur-verified --cache rust/tools/triage/local/ghidra-cache --cases 8 --jobs 2 --size 31x19
```

This command's destination already exists; choose a fresh `--out` to repeat it.
Its `triage.md`/`triage.json` are under `runs/blur-verified/`. Synthetic evidence
is under `runs/synthetic-12/`; relocation evidence is under
`runs/relocation-verified/`. The staged Rust input was copied from
`rust/target/release/olm_blur.dll`; the original remained in its external directory.

### Profiles of all ten originals

The profile images are **17×9 at untouched defaults**. Seconds include cold host
startup and are single observations, not kernel benchmarks. Parameter counts
include hidden/UI controls exposed by the harness. A dash means an undeclared
depth, not a failed render. Function counts are Ghidra discoveries, not a proof
that every machine-code function was recovered.

| Original | Params | Depths | Functions | Function bytes | Largest function | Default seconds (8 / 16 / 32) |
|---|---:|---|---:|---:|---:|---|
| ColorKeep | 101 | 8/16/32 | 83 | 14,963 | 3,980 | 0.422 / 0.438 / 0.421 |
| DistanceGradation | 12 | 8/16/32 | 16,569 | 21,463,896 | 31,998 | 0.609 / 0.594 / 0.593 |
| OLMBlur | 5 | 8/16/32 | 97 | 48,215 | 5,255 | 0.437 / 0.438 / 0.422 |
| OLMColorKey | 223 | 8/16/32 | 437 | 109,554 | 3,019 | 0.453 / 0.469 / 0.453 |
| OLMDirectionalBlur | 21 | 8/16/32 | 120 | 37,369 | 3,980 | 0.375 / 0.485 / 0.453 |
| OLMKiraKira | 40 | 8/16/32 | 16,323 | 20,950,007 | 31,998 | 0.969 / 0.953 / 0.969 |
| OLMRadialBlur | 30 | 8/16/32 | 469 | 116,677 | 4,250 | 0.453 / 0.438 / 0.453 |
| OLMSmoother | 3 | 8/16 | 114 | 45,740 | 5,579 | 0.453 / 0.453 / - |
| OLMSmoother2 | 15 | 8/16/32 | 559 | 120,519 | 2,063 | 0.422 / 0.531 / 0.422 |
| OLMToonDilate | 1 | 8/16/32 | 6,109 | 3,067,163 | 11,757 | 0.454 / 0.453 / 0.438 |

Local full artifacts are under ignored `runs/` and `local/`; compact retained
evidence is under ignored `evidence/`. The table above remains in the README.
The hash-bound [validation record](evidence/verified/validation.json) retains
the source report paths, binary/harness/tool/exporter identities and route totals.

The table combines completed reports in `runs/originals/` (first five) and
`runs/originals-retry/` (last five). The initial KiraKira attempt reached its
process bound after exporting functions; it is preserved but not counted.
The successful retry used read-only projects and a **900-second** analysis
budget. The all-original runner now defaults to 900 seconds; smaller plug-ins
finish well before that limit. Diff/relocation tests use the final normalizer;
the final process launcher was additionally verified by
`runs/launcher-verified/` (97 functions, three default renders, verified exit of
the owned launcher and remaining descendant). No global processes were killed.

```powershell
python -m unittest discover -s rust/tools/triage -v
python rust/tools/triage/validate_synthetic.py --out rust/tools/triage/local/synthetic-new
python rust/tools/triage/olm_triage.py diff --old rust/tools/triage/local/synthetic-new/old/OLMBlur.aex --new rust/tools/triage/local/synthetic-new/new/OLMBlur.aex --out rust/tools/triage/runs/synthetic-new --cases 12 --jobs 2
python rust/tools/triage/validate_synthetic.py --verify rust/tools/triage/runs/synthetic-new/triage.json
python rust/tools/triage/validate_relocation.py --aex rust/tools/triage/local/synthetic-new/old/OLMBlur.aex --out rust/tools/triage/runs/relocation-new
python rust/tools/triage/profile_originals.py --originals "$originals" --out rust/tools/triage/runs/originals-new --analysis-timeout 900
```

The synthetic builder uses an isolated source copy and Cargo target directory,
builds offline, and never copies original AEX files. Its common fixture branch
applies a multiplier only when Legacy is enabled and Blur Amount is at most
100, keeping the generated maxima in the kernel's accepted range. The sole
old/new source difference is `2.0f32` → `3.0f32` in the exported, non-inlined
`triage_legacy_amount` function. It builds from one shared source path to avoid
embedding different file paths in the two binaries.

## Limits

This is bounded AEXCompat CPU evidence, not native After Effects acceptance.
The fixed image/downsample-1 corpus does not establish HDR, arbitrary custom
payloads, temporal dependencies, GPU behaviour, exhaustive parameter
interactions or nondeterminism. Original/harness failures remain incomplete;
they are never counted as exact or automatically blamed on the new plug-in.

Function boundaries and static callers depend on Ghidra analysis. Indirect
calls may be absent. Normalized hashes remove address operand bits and PE
relocations, represent local branch targets by instruction index, and retain
referenced literal bytes. Function-target addresses are intentionally removed;
a hash match alone cannot prove semantic equivalence. Compiler changes,
mutable/static data and untyped tables can affect matching. Consult retained
call graphs, imported symbols and render observations together.

The small Cargo manifest/stub exists only because the parent workspace includes
`tools/*`; the actual tool and tests are Python. All authored files remain
inside this directory. No repository commits or remote actions are performed.

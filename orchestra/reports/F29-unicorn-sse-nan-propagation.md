status: done

summary:
- Built and registered an isolated SSE NaN reference worker; existing workers and fuzzer defaults are unchanged.
- Fixed destination-first NaN selection for x86 SSE, including default CPU initialization/reset, while retaining x87 semantics.
- Instruction matrix: 3,200/3,200 patched results match Rosetta; 188 prior differences removed; 2,368 NaN lanes agree with Intel SDM.
- Actual-default comparison: 707/708 saved corpus results unchanged; all 687 cases without input NaNs unchanged; changed words are exclusively NaNs.
- OLMBlur seed 1 n300 retains 281 exact / 2 mismatch / 17 refusal; reference outputs move in cases 99, 116, 290, 299.

facts:

Base worktree branch: `orch/F29-unicorn-sse-nan-propagation`. Read AGENT_GUIDE,
C24 report, GOTCHAS, compatibility plan, and the OLMBlur ledger row. No plugin,
release gate, forbidden-action list, saved corpus expectation, MAIN checkout,
original AEXCompat source, or existing worker was changed. No push, stash,
history rewrite, or permission rejection occurred.

**Source and build identity.** Copied current original AEXCompat revision
`0d3e74732e64dacba4d4508744951f28db538b88` into
`~/.cache/olm-emu/src-F29/` (excluding git metadata/build outputs). The final
build input is `src-F29/reference-guest`, copied from the **actual fuzzer
default** source at
`/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest`,
revision `7113ebfeccfccfc29c1ba009a06c1cfff6a56c56`. Its source checkout has an
unrelated broker edit and untracked build directory; neither was changed or
included in the guest snapshot.

Initially built against C24's cached `radial_noop_highdepth_reference_20261002`
source. Final auditing found that `run.default_worker()` actually selects the
containment worker, SHA `3cb4855b...84261`. All 708 corpora were replayed with
that worker too: **29 RadialBlur results already differ from C24**, including
finite PF8/PF16 inputs. First example `radialblur/seed1_case000006_253d4390d90b.json`
has Smart first differing byte 61: actual default `ff`, C24/candidate `fe`.
The full 29-case baseline difference is committed in
`F29-evidence/parent-selection.json`. Therefore the C24-based candidate was
superseded, and the final build was reconstructed from the actual default's
source with only the same SSE patch. No unrelated host/math changes are
introduced relative to the actual default. Current upstream AEXCompat and the
C24 snapshot are not claimed to be the final worker's parent.

Only these bundled Unicorn files differ from the parent: `qemu/fpu/softfloat.c`,
`qemu/fpu/softfloat-specialize.inc.c`, `qemu/include/fpu/softfloat-types.h`,
`qemu/target/i386/cpu.c`, `qemu/target/i386/unicorn.c`, and
`qemu/target/i386/fpu_helper.c`. Applying the committed patch to a fresh parent
vendor copy reconstructs all **346 files identically** to the compiled vendor
source. The x86-target selector consults an SSE-specific float-status flag;
x87 retains the existing larger-significand/quiet-NaN preference. Existing
quieting and invalid exception logic are reused. FMA's separate selector,
MIN/MAX implementation, conversions, and finite arithmetic are not changed.

| Artifact | SHA-256 |
|---|---|
| Actual default parent worker | `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261` |
| Final `~/.cache/olm-emu/worker-F29-ssenan/aex-guest-worker` | `1c8fb695596e5cf9be21b7c644a3680011ea5b88f4be6e092d93383e3ed4f369` |
| Parent worker's Unicorn dylib | `d4c0324ad23183e1edce5ecfbb15f4e9da1a9f2f11eea3e985b594faf2b8fa91` |
| Patched worker build's Unicorn dylib | `80cea710092f053506fc48035bdeda9942fd3c9f64d9d948aa714717c089a38d` |

Build command (environment: `CARGO_BUILD_JOBS=1`,
`CMAKE_BUILD_PARALLEL_LEVEL=1`, `AEXCOMPAT_BUILD_REVISION=F29-ssenan`,
`CARGO_TARGET_DIR=~/.cache/olm-emu/worker-F29-ssenan/build`, all temporary
variables set to this worktree's `orchestra/state/F29-unicorn-sse-nan-propagation`):

```sh
cargo build --manifest-path /Users/onmk/.cache/olm-emu/src-F29/reference-guest/Cargo.toml --release --offline --locked -j 1 -p aex-guest-worker
```

`memory_pressure` reported **51% free** before the preliminary builds and **55% free**
before the final actual-default rebuild. Cargo 1.95.0;
Apple clang 17.0.0. Initial build completed in 3m13s; initialization correction
rebuilt in 1m15s. Final actual-default build completed in **1m27s**, with one
existing dead-code warning. Logs are `build.log`, `build-reset.log`, and
`build-default.log` in scratch. Build-script preparation/build
steps were executed as constituent commands; its registration mode and the
complete characterization/replay drivers were run. The committed fresh-cache
builder has not itself been invoked end-to-end on another fresh destination.

`python3 tools/emulation/aexcompat_patches/build_F29.py --register` initially added
`worker-F29-ssenan` to `~/.cache/olm-emu/INDEX.json`, preserving the nine existing
entries. After resolving the parent identity, only our new F29 entry and its
metadata were updated to the final hash; the nine pre-existing entries were
again verified unchanged. Durable build metadata is `~/.cache/olm-emu/F29-ssenan-build.json`;
the same source manifest is committed in `F29-evidence/build-manifest.json`.
No fuzzer default setting was changed.

**Instruction characterization.** Executed
`bash tools/emulation/aexcompat_patches/characterize_F29.sh`. C compiled with
`clang -arch x86_64 -O2`, executed with `/usr/bin/arch -x86_64`. Identical raw
instruction bytes execute under Rosetta, MAIN's Python Unicorn 2.1.4, and the
worker's bundled Unicorn (Cargo package 2.1.5), then the patched library. Library
paths and hashes are asserted: the Python binding cannot silently fall back.
The libraries report the same `uc_version()` value; version labels alone do
not distinguish them.

Each of 32 instructions has 100 input conditions. Inputs contain both signed
zeros, ±1, ±infinity, two distinct signed QNaNs and two distinct signed SNaNs.
Packed lanes rotate the inputs and are checked independently; scalar upper
lanes are also compared. Instructions cover ADD/SUB/MUL/DIV/MIN/MAX/SQRT in
SS, PS, SD and PD forms, plus CVTSS2SD, CVTSD2SS, CVTPS2PD, CVTPD2PS. MXCSR is
0x1f80, exceptions masked; output bits, not exception delivery, are the target.

| Instruction family | Old differences per SS / PS / SD / PD | Patched differences |
|---|---|---:|
| ADD, SUB, MUL, DIV (each) | 6 / 23 / 6 / 12 | 0 |
| MIN, MAX, SQRT (each) | 0 / 0 / 0 / 0 | 0 |
| Four conversions | 0 each | 0 |
| Total | 188 / 3,200 | 0 / 3,200 |

Both old libraries produce identical full matrices. First mismatch:
`f3 0f 58 c1` (`ADDSS XMM0,XMM1`), low operands `7fc12345`, `ffc12346`;
old result `ffc12346`, Rosetta/patched result `7fc12345`. The complete 188-row
disagreement table, including full vector inputs/results, is committed in
`F29-evidence/instructions.json`. Source specification:
[Intel SDM volume 1 revision 090](https://cdrdv2-public.intel.com/874241/253665-090-sdm-vol-1.pdf),
section 4.8.3.5 / Table 4-8. Integer-bit checks of 2,368 NaN arithmetic lanes
find **zero SDM/Rosetta disagreements**. MIN/MAX are excluded from that general
NaN rule check and compared separately. Rosetta CPUID.1:ECX=`0298220f`,
FMA=0, AVX=0: FMA is not reachable in this native reference and was not run.

A further default-initialization probe exposed an incomplete first patch:
without an MXCSR write, ADDSS still returned `ffc12346`; after a write it
returned `7fc12345`. Added initialization/reset assignments. The final worker
library returns `7fc12345` without any MXCSR setup. x87 negative control uses
raw 80-bit loads and ADD/SUB/MUL/DIV, 6×6×4 conditions: **144/144 unchanged**, all
matching Rosetta. This is an observed new initialization boundary, not a second
refuted numerical hypothesis. No two-hypothesis stop condition was reached.

**Saved corpora and seed 1.** Executed the complete serial replay driver for the
actual default (`replay_F29.sh default`) and final patched worker. The default
reports were retained under the verifier's `baseline-*` names; the older C24
comparison reports remain separately in scratch `c24-lineage/`. The `baseline`
mode now pins the same actual-default path for future reproduction. Every replay uses `--jobs 1 --worker <absolute worker>`; all generated
reports/corpora remain in scratch. All 11 nonempty saved directories complete.
The first baseline wrapper incorrectly treated two corpus directory suffixes
as adapter names and was corrected to read the saved `plugin` field; both
missing directories were rerun. Editing that running wrapper interrupted its
final seed command, which was rerun explicitly. An early patched run was
terminated before rebuilding the initialization correction; the complete final
patched driver was then rerun. Bash 3's empty-array nounset issue in the initial
characterization wrapper was corrected before the successful complete run.

| Saved directory | Cases | Results changed vs actual default |
|---|---:|---:|
| olmblur | 39 | 1 |
| olmcolorkey | 3 | 0 |
| olmdirectionalblur | 56 | 0 |
| olmdistancegradation | 145 | 0 |
| olmkirakira | 8 | 0 |
| olmkirakira_gate_off_T06 | 62 | 0 |
| olmsmoother | 29 | 0 |
| olmsmoother2 | 8 | 0 |
| olmtoondilate | 300 | 0 |
| olmtoondilate_T13 | 23 | 0 |
| radialblur | 35 | 0 |
| Total | 708 | 1 |

All **687 cases without input NaNs** have identical full result objects,
including successful oracle raw SHA-256 values. Of the remaining 21 cases,
20 are unchanged. Both workers disagree with 16 historical KiraKira gate-off and 29 RadialBlur
saved expectations; those are pre-existing differences, with identical results
between workers. The final worker preserves the actual default even where the
saved corpora were established using another worker. OLMBlur saved `seed1_case000099_9b13c27c2f2e.json` is the sole
new saved-expectation difference. Its Smart reference changes 26 bytes / 9 words,
first word 29: `ffc12346` → `7fc12345`. Its 16 input NaNs and every changed output
word are recorded. All changed output words are NaN before and after.

`python3 tools/emulation/aexcompat_patches/verify_replays_F29.py --scratch
orchestra/state/F29-unicorn-sse-nan-propagation --output
orchestra/state/F29-unicorn-sse-nan-propagation/replays.json` completed without
assertion failures. It independently recaptures both workers' raw output for
every changed route, binds those bytes to the campaign hashes, and records all
changed words. No numeric tolerance is used.

For OLMBlur `--n 300 --seed 1 --jobs 1 --shrink-attempts 0`, both runs complete
with **281 Smart exact / 2 mismatch / 17 refusal**, Classic 13 exact / 287
refusal. All candidate raw hashes and statuses are unchanged. Changed reference
cases, exclusively Smart output NaN words:

| Case | Input NaN words | Changed bytes / words | First word (zero-based) | Before → after |
|---|---:|---:|---:|---|
| 99 | 56 | 30 / 11 | 29 | `ffc12346` → `7fc12345` |
| 116 | 20 | 115 / 56 | 1 | `ffc12346` → `7fc12345` |
| 290 | 45 | 406 / 174 | 2 | `ffc12346` → `7fc12345` |
| 299 | 72 | 372 / 125 | 26 | `ffc12346` → `7fc12345` |

Case 99's Mac-vs-reference residual moves from 32 bytes / 17 words to 10 bytes /
10 words; first remaining word 54 is reference `ffc00000`, Mac `7fc00000`.
Cases 116, 290, 299 remain refused. Complete before/after hashes and every
changed raw word are in `F29-evidence/replays.json`.

inference:
- The measured mismatch is an x87 selection policy reused for SSE; selecting
  according to SSE operand order fixes all characterized differences without
  changing finite arithmetic or x87 behavior.
- NaN payload changes in saved/seed cases are consistent with this general
  cause. Changed raw words alone do not constitute a complete internal trace;
  C24 supplies the original ADDSS instruction boundary for OLMBlur.
- The remaining Mac NaN-sign difference is a separate port issue. No plugin
  admission, rebaseline, or AE-exact claim is made.
- Rosetta is another emulator. Agreement with SDM provides stronger evidence
  than Rosetta alone, but native Windows hardware and FMA remain separate
  validation work.

changed_files:
- `tools/emulation/aexcompat_patches/F29-sse-nan-order.patch`
- `tools/emulation/aexcompat_patches/build_F29.py`
- `tools/emulation/aexcompat_patches/probe_sse_nan_F29.py`
- `tools/emulation/aexcompat_patches/probe_controls_F29.py`
- `tools/emulation/aexcompat_patches/verify_instruction_F29.py`
- `tools/emulation/aexcompat_patches/verify_replays_F29.py`
- `tools/emulation/aexcompat_patches/characterize_F29.sh`
- `tools/emulation/aexcompat_patches/replay_F29.sh`
- `tools/emulation/aexcompat_patches/README.md`
- `tools/emulation/aexcompat_patches/F29-evidence/*.json` — complete disagreement,
  changed-case, x87, library, and source-build evidence.
- `orchestra/reports/F29-unicorn-sse-nan-propagation.md`
- Outside git, authorized new cache source/binary/metadata and additive INDEX
  entry only; existing workers and original source are untouched.

verify:

```sh
bash tools/emulation/aexcompat_patches/replay_F29.sh baseline
bash tools/emulation/aexcompat_patches/replay_F29.sh patched
python3 tools/emulation/aexcompat_patches/verify_replays_F29.py --scratch orchestra/state/F29-unicorn-sse-nan-propagation --output orchestra/state/F29-unicorn-sse-nan-propagation/replays.json
bash -n tools/emulation/aexcompat_patches/characterize_F29.sh
bash -n tools/emulation/aexcompat_patches/replay_F29.sh
git diff --check
```

Expected: the exact corpus/seed counts and five changed-case identities above;
all changed output words NaNs, no changed candidate hashes/statuses. Patched
OLMBlur replay and both historical KiraKira gate-off / RadialBlur replays
intentionally return 1 for saved expectation differences; verifier succeeds.

For an independent fresh-cache rebuild and instruction test:

```sh
python3 tools/emulation/aexcompat_patches/build_F29.py --cache-root "$HOME/.cache/olm-emu/F29-independent-check" --scratch orchestra/state/F29-unicorn-sse-nan-propagation/rebuild
bash tools/emulation/aexcompat_patches/characterize_F29.sh "$HOME/.cache/olm-emu/F29-independent-check"
```

Expected: 3,200/3,200 patched matrix match, 2,368 SDM lane checks, 144 unchanged
x87 results, and fixed default-initialized ADDSS. New paths may change binary
hashes. Delete that independent build tree after verification. The README
explains scratch artifacts and all reproduction entry points.

next:
- Propose explicitly switching the reference worker to the recorded F29 SHA
  after orchestrator review; do not silently change the fuzzer default.
- Rebaseline only the demonstrated OLMBlur corpus oracle change after approval
  of the reference contract. Keep its remaining NaN-sign mismatch visible.
- Follow up the invalid-operation NaN-sign port boundary and remeasure gated
  nonfinite cases against this worker. Native Windows and FMA validation remain
  distinct work; do not infer them from the Rosetta table.

Final hygiene and checks: all five Python scripts parse; both shell drivers pass
`bash -n`; `git diff --check` passes. Final worker, cache index, and committed
manifest hashes agree. The exact final-parent patch reconstructs 346 vendor
files and changes only the six listed source files. Regenerable Rust/CMake and
native-probe build trees were deleted; the worker directory contains only the
7.3 MiB final executable. Scratch retains 14 MiB of logs/evidence, source
snapshot 32 MiB, all below the 5 GiB limit. No task emulator/build process
remains. Preliminary C24 artifacts are retained only as clearly separate
scratch diagnostics; committed main evidence binds the final actual-default
parent and final worker hashes.

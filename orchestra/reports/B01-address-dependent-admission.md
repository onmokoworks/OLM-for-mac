status: partial
summary:
- Proved false overlap rejection with adjacent padded worlds; retained rejection of real overlap.
- Changed span/admission helpers in ColorKey, DirectionalBlur, ColorKeep, KiraKira, RadialBlur and ToonDilate.
- ColorKey staging now copies active source rows instead of reading past a cropped final row.
- Resumed on integration base `1f5a731d31ef0a5d17cb374803fe3e3ec2b326cd`; validation is in progress.

facts:
- Resume validation: ColorKey native differential completed 12,012/12,012 exact comparisons (3,000 small + 3 full-4K cases × two architectures × two builds); zero differences, refusals or execution errors.
- Shared corpus replay with `MallocScribble=1`: 746/746 cases matched saved results: ColorKey 51, DirectionalBlur 106, ColorKeep 203, KiraKira 12, RadialBlur 71, ToonDilate 303. Initial large-frame groups required correcting the runner max-size argument; all remaining cases then replayed with recorded sizes. No corpus changed.
- Resume: merged `refs/keep/B01a`, resolving source-split conflicts by moving each original diff hunk into its matching include file. `git merge codex/public-beta-roi` returned Already up to date. No other worktree was edited.
- Baseline: `56672f7819352ef35c83574101ea8a7c6c301789`, branch `orch/B01-address-dependent-admission`; initial worktree clean.
- Read AGENT_GUIDE, emulator GOTCHAS, Q02 report, compatibility plan and current decision-matrix forbidden-action rows. No release-gate/ledger/kernel arithmetic changes.
- `git diff --stat b5e4c865 HEAD -- mac/OLMColorKey` produced no output: this ticket baseline ColorKey source equals the retained Q02 split. The original historical executable was not reused.
- Original Q02 seed 909 / generator index 4935 / sequence 1932 regenerated: PF8, input 3×1, full 9×4, downsample 1/4×1/4, padding 1. Input SHA256 `352bee204602201794b673362fc72b034b5ca3683aa58624425b78908a817866` matches Q02.
- Initial natural replay: 1,000/1,000 rendered, zero refusals, arm64 reference, `MallocScribble=1`. This did not reproduce the intermittent refusal under ordinary allocation.
- Sanitized extracted-production-helper probe: each of ColorKey, DirectionalBlur and RadialBlur baseline rejected 9,000/9,000 adjacent placements; head rejected 0/9,000. Both baseline/head rejected all 9,000 real one-byte overlaps. Matrix: 1,000 repetitions × PF8/PF16/PF32 × heights 1/2/7; width 2, parent width 3, one byte padding. ASan/UBSan reported no failures.

- `python3 tools/refactor/reproduce_B01.py --forced --revision 56672f7819352ef35c83574101ea8a7c6c301789 --scratch orchestra/state/B01-address-dependent-admission/forced-base` exited 0: 1,000/1,000 refused with error 516, trace `PrepareSmartRenderWorld:smart-public-admission@217`. This is a synthetic zero-source/default-info cropped-world fixture, not a claim that every Q02 parameter was used in the forced fixture. A custom test allocator places the Smart storage vector at arena+16 and the input at arena+4, width 2 / height 1 / rowbytes 13.
- The same forced command without `--revision`, scratch `forced-head`, exited 0: 1,000 rendered / 0 refusals. No production allocator changes.
- `python3 tools/refactor/reproduce_B01.py --scratch orchestra/state/B01-address-dependent-admission/natural-head` exited 0: exact Q02 input binding, 1,000 renders / 0 refusals, rect `[1,0,3,1]`, eight output bytes, SHA256 `af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc` every time. The bytes and rectangle also matched the original AEX under the default realistic-v2 worker F53 (`~/.cache/olm-emu/worker-F53-geom/aex-guest-worker`), with intact guards and clean session.
- Oracle worker SHA256 `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`; original ColorKey AEX SHA256 `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- One superseded ColorKeep differential was deliberately interrupted after 6,128 exact comparisons when the second Smart staging span was found; its results are not counted as final validation. The complete corrected rerun replaced it.

inference:
- A cropped input keeps the parent rowbytes while moving its data pointer. Therefore `rowbytes*height` can extend beyond the parent's allocation even when that allocation originally had full last-row padding. An unrelated allocation in that extension causes the observed class of false overlap refusal. Ordinary replay alone cannot prove the historical Q02 allocation ordering.
- The checked bounding span is `(height-1)*rowbytes + width*pixel_bytes`. Its interior still includes row gaps, as required by the ticket's span rule. Actual intersecting spans remain rejected.
- Pointer validity, real aliasing, arithmetic overflow, necessary typed alignment, host errors and allocation failures remain safety preconditions. This does not claim successful rendering under arbitrary invalid pointers or exhausted memory.

Audit (source facts; interpretation explicitly noted):

| Component / location | Finding and disposition |
| --- | --- |
| `mac/OLMColorKey/Render.inc:17` CheckedPayloadBytes, `:33` DisjointPayloads; PrepareRenderWorld / PrepareSmartRenderWorld | Fixed full-stride bounding span and caller-input copies. Explicit pixel size comes from validated depth/template, not DEEP flags. Internal padding stays zero initialized. |
| `mac/OLMDirectionalBlur/OLMDirectionalBlur_admission.inc:171` PayloadSpan / `:197` DisjointPayloads | Fixed span for input/output/noise and Smart staging/budget accounting. All callers supply actual pixel size. |
| `mac/ColorKeep/ColorKeep.cpp:205` ColorKeepValidateWorldPair / `:343` ColorKeepRenderMapped | Fixed bounds, mapped staging span and Smart output staging span (`:561`). Classic alignment check `:210` retained: guards typed Iterate path; Smart already permits odd-byte cropped origins. |
| `mac/OLMKiraKira/OLMKiraKira.cpp:394` WorldLayoutIsSafe / `:2733` WorldStorageRangesDoNotOverlap | Existing layout validator already used last pixel; overlap helper now agrees and receives explicit format-derived size. |
| `mac/OLMRadialBlur/RadialWorldStorage.inc:2` RadialPayloadSpan / `:23` RadialPayloadsDisjoint | Fixed full-stride range. Alignment guards at `RadialAdmission.inc:144`, `:348`, `RadialZoomAdmission.inc:412` retained for typed paths; Smart at `OLMRadialBlur.cpp:807` stages unaligned source before typed access. Its budget accounts for that staging. These are actual layout requirements, not a false adjacent-allocation overlap. |
| `mac/OLMToonDilate/OLMToonDilate.cpp:371` ValidateToonBetaAdmission | Fixed production input/output spans, including returned staging size. |
| `mac/OLMToonDilate/OLMToonDilate.cpp:249` ToonPublicSourceMatches, `:269` padding sentinel; `:290` ValidateToonPublicAdmission, `:315` span | Not changed: legacy template has no production caller (`rg` finds definition only). It deliberately reads each padding byte, including final tail, so its full span describes actual accesses. Re-enabling it would require replacing the fixture-padding contract; not silently done here. |
| `mac/OLMBlur/OLMBlur.cpp:369` PublicWorldsDisjoint, callers `:713`, `:762` | Not shortened: retained exact fixture path explicitly copies every row's padding at `:789`, including final tail. Shortening this check alone would admit real read/write overlap. Generic paths use TightStaging / checked touched spans (`OLMBlur.cpp:303`, `:719`). Legacy padding-copy removal needs a separate owner-contract change outside admission/span helpers. |
| `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2074`, `:2085`, `:2301`, `:2490`, `:2542` | PF32 typed alignment and core touched-span checks already correct; no change. Parallel eligibility also requires real disjoint spans; no time limit. |
| `mac/OLMSmoother/Mac/OLMSmoother_port.cpp:4133`, `:4157` | Core require_disjoint / TightStaging already use touched spans. Virtual-address memory adapters (`:1358`, `:2433`) map initialized virtual stack storage and real pointers; not allocator-based admission. No change. |
| `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp:5273` | Already computes last-row offset plus active row bytes; kept. |
| `core/olm_world_safety.h:56`, `:87`, `:101`, `:106`, `:118` | Correct checked touched-span layout, address overflow, real overlap and active-row staging. Kept. |
| `core/olm_parallel.h:25`, `:45`; `core/olmblur_parallel_parts.h:19`; `core/kirakira_warp.h:103`; `mac/OLMColorKey/Kernel.inc:60`; `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2293`; `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp:4680`; `mac/OLMRadialBlur/RadialRotationRows.h:22` | Static inspection: row/part ownership and join, with per-row reduction order retained. Debug paths choose serial execution. No observed scheduling-dependent refusal; no change. This is not a full race proof. |
| `mac/OLMRadialBlur/RadialZoomKernels.inc:121`, `RadialTestWorkers.inc:35`, `:125` | std::thread/hardware_concurrency and atomic next-row scheduling; per-row writes, join before consumption. No admission timer. Allocation/thread-creation failure remains a runtime failure; no numerical/scheduling rewrite. |
| `core/dblur_generic_budget.h:205`, `:268`; `core/olm_checked_allocation.h` | Work/live-memory estimates use dimensions, controls, depth and staging bytes rather than elapsed time. No wall-clock deadline found by source search in mac/core. |
| `mac/OLMColorKey/Diagnostics.inc:48`, `:96`, `:103` | Optional PF32 capture claims a file with O_EXCL and dumps full padded rows. I/O failure can return an error; concurrent capture order selects the claimant. Disabled by default, not changed: instrumentation/persistence semantics are outside admission/span helpers. Cropped capture should be a separate diagnostics follow-up. |
| `mac/OLMColorKey/Kernel.inc:65`, `mac/OLMColorKey/Pixels.inc:166` | Uninitialized Lab cache storage is protected by zero-initialized ready bits; each entry is initialized before reuse. No speculative initialization change. |
| `mac/OLMSmoother/Mac/OLMSmoother_port.cpp:2978`, `:3203` | NeighbourExtract16/8 (`:851`, `:884`) writes slots 0–8 before ColorBlend16/8 consumes the neighbourhood (`:3173`, `:3392`). Declaration alone is not an uninitialized-read finding. No arithmetic/code-flow change. |

| `mac/OLMRadialBlur/RadialWorldStorage.inc:58`, `:91` | Optional PF32 diagnostics reject existing capture files, then write full padded rows. Disabled by default. Kept outside admission/span scope; file races and cropped capture safety need a diagnostics follow-up. |

Audit method: searched all ten plugin source trees and core for overlap/ranges/uintptr casts, pointer alignment, malloc/new, chrono/clock/time/random, thread/atomic/parallel_rows, padding comparisons and uninitialized-storage candidates; inspected the sites above. Runtime probes use ASan/UBSan and corpus replay uses MallocScribble. Neither ASan/UBSan nor MallocScribble is a proof against all uninitialized reads; no full MemorySanitizer or ThreadSanitizer coverage is claimed.

changed_files:
- mac/OLMColorKey/Render.inc
- mac/OLMDirectionalBlur/OLMDirectionalBlur_{admission,kernels,dispatch,host}.inc
- mac/ColorKeep/ColorKeep.cpp
- mac/OLMKiraKira/OLMKiraKira.cpp
- mac/OLMRadialBlur/OLMRadialBlur.cpp
- mac/OLMRadialBlur/RadialLayerCompose.inc
- mac/OLMRadialBlur/RadialWorldStorage.inc
- mac/OLMToonDilate/OLMToonDilate.cpp
- tools/refactor/test_address_dependent_admission.py
- tools/refactor/reproduce_B01.py
- orchestra/reports/B01-address-dependent-admission.md

verify:
Run from this worktree, using fresh scratch directories:
```sh
B=1f5a731d31ef0a5d17cb374803fe3e3ec2b326cd
S="$PWD/orchestra/state/B01-address-dependent-admission/recheck"
mkdir -p "$S/tmp"
export TMPDIR="$S/tmp"
python3 tools/refactor/test_address_dependent_admission.py --revision "$B" --scratch "$S/spans-base"
python3 tools/refactor/test_address_dependent_admission.py --scratch "$S/spans-head"
python3 tools/refactor/reproduce_B01.py --forced --revision "$B" --scratch "$S/forced-base"
python3 tools/refactor/reproduce_B01.py --forced --scratch "$S/forced-head"
python3 tools/refactor/reproduce_B01.py --scratch "$S/natural-head"
for plugin in olmcolorkey olmdirectionalblur colorkeep olmkirakira radialblur olmtoondilate; do
  python3 tools/refactor/native_diff.py --plugin "$plugin" --base "$B" --head WORKTREE --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch "$S/native" > "$S/diff-$plugin.log" 2>&1
  python3 tools/refactor/reproduce_B01.py --plugin "$plugin" --differences "$S/native/$plugin" --scratch "$S/oracle-$plugin" > "$S/oracle-$plugin.log" 2>&1
done
git diff --check "$B" HEAD
```
Corpus replay (group all nested cases by recorded max-size; symlink inputs, no oracle copies):
```sh
python3 - <<'PY'
from pathlib import Path
import collections, json, os, subprocess
root = Path.cwd()
s = root/"orchestra/state/B01-address-dependent-admission/recheck-corpus"
s.mkdir(parents=True)
for plugin in ["olmcolorkey", "olmdirectionalblur", "colorkeep", "olmkirakira", "radialblur", "olmtoondilate"]:
    groups = collections.defaultdict(list)
    for path in (root/"tests/fuzz_corpus"/plugin).rglob("*.json"):
        groups[json.loads(path.read_text())["max_size"]].append(path)
    for size, paths in sorted(groups.items()):
        name = f"{plugin}-{size}"
        inputs = s/(name+"-inputs"); inputs.mkdir()
        for i, path in enumerate(sorted(paths)):
            (inputs/f"{i:04d}.json").symlink_to(path)
        with (s/(name+".log")).open("w") as log:
            subprocess.run(["python3", "tools/fuzz/run.py", "--plugin", plugin,
                "--replay", str(inputs), "--max-size", str(size), "--size-sampler", "odd-even-v1",
                "--jobs", "1", "--budget-minutes", "30", "--scratch", str(s/name),
                "--report", str(s/(name+".json"))],
                env=dict(os.environ, MallocScribble="1", TMPDIR=str(s)),
                stdout=log, stderr=subprocess.STDOUT, check=True)
PY
```
Measured again after resume: helper base adjacent refusals 9,000/9,000 per plugin, head 0/9,000; missed real overlaps 0 for both. Forced base 1,000/1,000 error 516, head 0/1,000; natural head 0/1,000 and oracle exact. Differential and corpus expectations await completed runs.

next:
- Finish differential/corpus validation and oracle checks for each changed admission; preserve real overlap guards.

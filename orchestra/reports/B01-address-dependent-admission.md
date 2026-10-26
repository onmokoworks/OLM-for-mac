status: done
summary:

- Corrected touched-span arithmetic in six plugins, including their staging spans.
- ColorKey copies active source rows instead of reading a cropped final-row tail.
- Forced adjacent allocation no longer causes a false refusal; real overlap remains rejected.
- Completed both-architecture/both-build differentials and all six nested corpora.

facts:

- Merged `refs/keep/B01a` and moved its DirectionalBlur/RadialBlur changes into the split files. `git merge codex/public-beta-roi` returned Already up to date. Pre-fix comparison base: `1f5a731d31ef0a5d17cb374803fe3e3ec2b326cd`.
- `tools/refactor/native_diff.py --plugin NAME --base BASE --head WORKTREE --cases 3000 --seed 909 --arch both --build both --jobs 1 --scratch orchestra/state/B01-address-dependent-admission/native` completed for each of the six plugins. Each matrix contains 3,000 small cases plus three 4K cases, across arm64/x86_64 and reference/fast builds. The shared differential runner pins `OLM_PARALLEL_MAX=1`; threading findings below are static inspection, not a race-detector result.
- All 72,072 comparisons matched: 71,772 rendered pairs and 300 matching refusals. Differences, new refusals and execution errors: all zero. First mismatch: none. The difference-oracle checker found no newly admitted differential cases to check.
- Shared `tools/fuzz/run.py --replay` with `--jobs 1` and `MallocScribble=1` matched all 746 saved cases / 1,492 Classic/Smart route executions. All nested directories were included. Initial default-size invocations rejected large-frame groups at setup; the remaining files were replayed with their recorded max-size values. No corpus data was changed.

| Plugin | Native rendered matches | Native matching refusals | Corpus cases matched | Corpus routes |
| --- | ---: | ---: | ---: | ---: |
| olmcolorkey | 12012 | 0 | 51 | 102 |
| olmdirectionalblur | 12012 | 0 | 106 | 212 |
| colorkeep | 12012 | 0 | 203 | 406 |
| olmkirakira | 11712 | 300 | 12 | 24 |
| radialblur | 12012 | 0 | 71 | 142 |
| olmtoondilate | 12012 | 0 | 303 | 606 |

- ASan/UBSan extracted-production-helper tests (`test_address_dependent_admission.py`) checked ColorKey, DirectionalBlur and RadialBlur: 1,000 repetitions × PF8/PF16/PF32 × heights 1/2/7. Each base helper falsely refused 9,000/9,000 adjacent spans; each head helper refused 0/9,000. Both rejected all 9,000 real one-byte overlaps per helper. No sanitizer failure was reported.
- `reproduce_B01.py --forced --revision BASE` refused 1,000/1,000 Smart preparations with error 516, tag `PrepareSmartRenderWorld:smart-public-admission`; head admitted 1,000/1,000. These are preparation calls, not full renders. The synthetic zero-source/default-info fixture has width 2, height 1 and rowbytes 13, input at arena+4 and Smart storage at arena+16. It forces the span error without claiming the exact historical Q02 heap layout.
- `reproduce_B01.py` natural replay, with and without `--revision BASE`, rendered 1,000/1,000 times on each revision under MallocScribble. The natural historical refusal was not observed. This is the Q02 seed 909 / generator index 4935 / sequence 1932 case: PF8, input 3×1, full 9×4, quarter downsample, request `[1,0,3,1]`, one byte padding. Input SHA256: `352bee204602201794b673362fc72b034b5ca3683aa58624425b78908a817866`.
- Natural output was eight bytes, rectangle `[1,0,3,1]`, SHA256 `af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc` in every run. Both revisions matched the original AEX under the default realistic-v2 F53 worker, with intact guards and clean session. Worker SHA256: `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`; ColorKey AEX SHA256: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- Exact build hashes, source hashes, corpus result hashes and probe results are in [the validation manifest](B01-address-dependent-admission.json). Regenerable build outputs were removed; no worker rebuild, release-gate edit or MAIN modification was performed.

inference:

- A cropped world keeps its parent's rowbytes while advancing its data pointer. Counting `rowbytes * height` can include bytes beyond its allocation. The forced placement proves that an unrelated allocation in that excess range can cause a false refusal. It does not establish the allocation ordering of the historical Q02 run.
- The corrected bounding span is `(height - 1) * rowbytes + width * pixel_bytes`; interior row gaps remain inside the checked span. Real overlap, pointer overflow, required typed alignment, host errors and allocation failure remain safety preconditions.

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
| `mac/OLMBlur/OLMBlur.cpp:369` PublicWorldsDisjoint, callers `:713`, `:762` | Not shortened: retained exact fixture path explicitly copies every row's padding at `:789`, including final tail. Shortening this check alone would admit real read/write overlap. Generic paths use TightStaging / checked touched spans (`OLMBlur.cpp:294`, `:719`). Legacy padding-copy removal needs a separate owner-contract change outside admission/span helpers. |
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
| `core/olm_parallel.h:50`, `:51`, `:59` | Static failure-path candidate: the worker ignores the result of saving its previous FP environment before restoring it. Inference: if that call fails without writing the object, restoration could read uninitialized state. No such failure was observed or forced. Kept under the ticket’s admission/span-only constraint; a separate parallel-driver failure-path test is needed. |

Audit method: searched all ten plugin source trees and core for overlap/ranges/uintptr casts, pointer alignment, malloc/new, chrono/clock/time/random, thread/atomic/parallel_rows, padding comparisons and uninitialized-storage candidates; inspected the sites above. Runtime probes use ASan/UBSan and corpus replay uses MallocScribble. Neither ASan/UBSan nor MallocScribble is a proof against all uninitialized reads; no full MemorySanitizer or ThreadSanitizer coverage is claimed.

changed_files:

- mac/ColorKeep/ColorKeep.cpp
- mac/OLMColorKey/Render.inc
- mac/OLMDirectionalBlur/OLMDirectionalBlur_admission.inc
- mac/OLMDirectionalBlur/OLMDirectionalBlur_dispatch.inc
- mac/OLMDirectionalBlur/OLMDirectionalBlur_host.inc
- mac/OLMDirectionalBlur/OLMDirectionalBlur_kernels.inc
- mac/OLMKiraKira/OLMKiraKira.cpp
- mac/OLMRadialBlur/OLMRadialBlur.cpp
- mac/OLMRadialBlur/RadialLayerCompose.inc
- mac/OLMRadialBlur/RadialWorldStorage.inc
- mac/OLMToonDilate/OLMToonDilate.cpp
- tools/refactor/reproduce_B01.py
- tools/refactor/test_address_dependent_admission.py
- orchestra/reports/B01-address-dependent-admission.md
- orchestra/reports/B01-address-dependent-admission.json

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
python3 tools/refactor/reproduce_B01.py --revision "$B" --scratch "$S/natural-base"
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
Expected: each native differential completes 12,012 comparisons with zero differences, new refusals or execution errors. KiraKira has 300 matching refusals; all other comparisons render successfully. Corpus replay matches all 746 saved cases. Helper probes reject every real overlap; base rejects 9,000 adjacent spans per helper and head rejects zero. Forced preparation rejects 1,000/1,000 on base and 0/1,000 on head. Natural replay measured 0/1,000 refusals on both revisions; head must remain at zero. No byte tolerance is used. These counts describe the measured run; a base-only false refusal on a rerun is acceptable only if the difference checker verifies the head output against the default oracle. Any other difference fails.

next:

- No remaining B01 admission validation work.
- Separate follow-ups: diagnostic captures that read padded final tails / race on capture filenames; the legacy OLMBlur padding-copy contract; and a failure-injection test for the shared parallel driver's unchecked FP-environment save. These were not changed under this ticket's admission/span-only rule.

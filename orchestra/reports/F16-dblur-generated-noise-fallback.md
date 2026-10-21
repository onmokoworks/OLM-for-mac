status: blocked

summary:
- Original AEX full-render traces prove out-of-allocation noise-table reads in seed-1 indices 167/183/222/246.
- Changing only host allocator padding changes their generated noise fields; it does **not** change their final pixels in the measured counterfactuals.
- Stopped at this native memory-safety boundary under the ticket's outside-port exception; no production code, admission guard, or corpus was changed.
- Both routes remain 235/300 exact; all 300 before/after result dictionaries are identical, corpus replay is 56/56 matches_saved, and five fast tests pass.
- Full acceptance is not achieved: index145 still refuses; index102 and the other unshrunk refused cases remain unresolved.

facts:

Starting commit: `0696cc7b436a5c4a76b776aa276ea14c5e53eacd`, branch `orch/F16-dblur-generated-noise-fallback`. Read `AGENT_GUIDE.md`, the DirectionalBlur ledger rows including forbidden actions, the compatibility plan, emulation gotchas and F06. MAIN, AEX assets, emulator sources, cached workers, release gates, ledger and other plugins were not modified. No worker rebuild, push, history rewrite, copy exception or numeric correction was made. Scratch and compiler temporary files were confined to `orchestra/state/F16-dblur-generated-noise-fallback`; regenerable build directories were removed by their temporary-directory contexts.

**Scope correction from the actual F06 transition data.** The 25 new refusals plus index145 are **unshrunk campaign cases**. Of these 26, 16 have generated Noise and 10 have Noise disabled with Size × Fade. The ten are indices `73,78,88,152,160,168,169,175,200,241`. The corresponding 25 saved reduced corpus cases already replay exact on both routes; reducing them removed the problematic feature combinations. This ticket does not newly solve those reduced inputs. Index145 is not one of those 25 saved corpus cases.

**Original AEX boundary, reproduced on the assigned inputs.** The new probe generates the six inputs with the unchanged fuzz generator (seed 1), drives the original AEX builder/PF8 worker, and traces `FUN_1800034e0`. The original populate/output callbacks, rotate and rowdriver execute without detours. A transparent prepass leaf first verifies Win64 stack arguments 5/6 using sentinel-filled buffers. The fixture's two diagnostic component-map coordinates are made in-bounds; rendering is not changed. Fixed controls are passed as their signed whole-word getter values; the double Gain and Thickness values retain their fractions. The six unmodified-fixture outputs, including indices102/145, match the independently run cached AEX session worker byte-for-byte.

The generator requests 404 bytes for its 101-float table. At `0x1800037f3` and `0x1800037f8`, the trace compares the actual indexed pointer against the recorded PF Handle allocation. The binary only subtracts the table size while the position is >=100, truncates to a signed index, then reads `[table+index*4]` and `[table+index*4+4]`. There is no lower-bound fold. MAIN's decompilation of `FUN_1800034e0` agrees. The report retains decoded instructions and their byte hash directly from the original AEX.

| Seed-1 index | Work dimensions | Noise dimensions | First signed index | First byte offset relative to 404-byte table | Total outside reads |
|---|---|---|---:|---:|---:|
| 167 | 28×29 | 3×3 | -6 | -24 | 2 |
| 183 | 28×29 | 3×3 | -3 | -12 | 2 |
| 222 | 28×28 | 4×4 | -1 | -4 | 1 |
| 246 | 13×13 | 16×16 | -11 | -44 | 50 |

Indices102 and145 each have zero outside reads. All six finish in the original fixture and match the cached session output. F06 already recorded core failure for the four negative-Offset cases under its blanket bypass. The current core's `generate_noise_plane` rejects the same negative-index condition at `core/dblur_noise.h:83`, before accessing the vector. The public PF8 guard currently refuses all six before this fallback is admitted. This report does not mislabel the public refusal site as the native read instruction.

**Controlled host-padding experiment.** For each input, run the original fixture and two additional fixtures that put a 256-byte prefix/suffix around only the noise table allocation. The prefixes contain repeated float32 0 or 1. The AEX sees the same requested 404-byte allocation size and creates all in-allocation table entries itself; all three table hashes agree per case. No generated value or output byte is patched. These are counterfactual host allocations, not substitute reference outputs.

| Index | Changed field float32 words, padding 0 → 1 | First changed field byte offset | First float32 words, little-endian hex | Changed final ARGB8 bytes |
|---|---:|---:|---|---:|
| 102 | 0 | — | — | 0 |
| 145 | 0 | — | — | 0 |
| 167 | 1 | 28 | `ba37663f` → `0000803f` | 0 |
| 183 | 1 | 32 | `bdec1a3f` → `0000803f` | 0 |
| 222 | 1 | 48 | `0000803f` → `c544f43e` | 0 |
| 246 | 26 | 56 | `ddfd8a3e` → `ee7e453f` | 0 |

The first actual invalid-read values in the unmodified fixture are respectively `480f6a3e`, `1336203f`, `00000000`, `00000000` (little-endian float32 bits). Their bytes lie outside the requested allocation. The zero output deltas are retained explicitly: this experiment proves allocator-dependent **intermediate fields**, not allocator-dependent final pixels for these four inputs. No Windows AE allocator/UCRT behavior or native AE result is claimed.

**Campaign before/after.** Ran the required `tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2` twice, with ticket scratch corpora, the cached worker, and `--shrink-attempts 0`; both exited 0. Each reports 298 completed AEX renders and two instruction-budget cases (274/289). Comparing every `case.result` dictionary gives 300 unchanged, zero changed on either route. Production sources did not change between the runs.

| Route | Exact before → after | Mismatch before → after | Refusal before → after | Uncompared before → after |
|---|---:|---:|---:|---:|
| Classic | 235 → 235 | 23 → 23 | 40 → 40 | 2 → 2 |
| Smart | 235 → 235 | 23 → 23 | 40 → 40 | 2 → 2 |

**Corpus before/after table.** Replay exited 0 with 56/56 `matches_saved`. No corpus update was made.

| Corpus group | Files | Before → after, each route | Changed files |
|---|---:|---|---:|
| Reduced cases corresponding to the 25 F06 new refusals | 25 | exact → exact | 0 |
| Other saved exact cases | 12 | exact → exact | 0 |
| Remaining saved mismatches | 19 | mismatch → identical mismatch | 0 |

**Existing fast tests.** The command below ran five tests and exited 0 (`Ran 5 tests`, `OK`): the checked general-feature budget test plus Type-3 public-owner generator identity, exact rows, row-tamper rejection and claim-tamper rejection. These are the selected fast subset, not the entire historical suite. No guard was relaxed, so a gate-off admission/sanitizer promotion was neither performed nor claimed.

**Artifact bindings.** Full campaign results, corpus results, allocation traces, constructor arguments, field/output hashes and static instructions are committed under `reports/fuzz/f16_dblur_generated_noise/`.

| Artifact | SHA-256 |
|---|---|
| Original `OLMDirectionalBlur.aex` | `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e` |
| Cached worker | `16ab2412c00b6ce5d61cadbf9d1cd3aa3c991f36bc66c6af8c2595c32d075e3c` |
| Unchanged `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp` | `e02a2973a032a77c861a0c86bb8043da6a72f2820141b7a950460c436f9c9156` |
| Unchanged `core/dblur_noise.h` | `5098f0acafc9d7a76136d306bd15193ca0c987fd3610e9340b311e6646001bee` |
| `allocator.json` | `f154478f96074bc3a4f420b89053359e700ce5a3d7beec3da19099c81567ecd5` |
| `before.json` | `96bbfa67a161b16154bcbf34ec82bc9f21e8c2464b1f24b815e2e408314b53aa` |
| `after.json` | `2d8f0bf1373e22dd91611ced7cf5b533fb60ea5e8a88f2f3ca5eb9768bfc51eb` |
| `replay.json` | `c90d2ce65355291018c8f6f4693c83852e9d519a0ed34beb5cc31ebd0ee762f9` |

inference:

- The four negative-Offset generator failures are a native AEX/host allocation boundary, not evidence that a negative-index wrap or clamp belongs in the port. The AEX reads storage outside its requested table; reproducing one emulator allocator's bytes would not establish general Windows compatibility.
- The unchanged final pixels suggest the affected field cells are unused or their differences are masked for these inputs. This is an inference, not a sampled-cell dependency proof. A safe demand-driven generator could be investigated separately, but this ticket did not prove one.
- This boundary does **not** explain index102's F06 one-byte discrepancy, justify restoring index145's copy exception, or establish an outside-port cause for the other refused inputs. No blanket generated-Noise admission is supported.
- Stopping follows the ticket's explicit instruction to document an outside-port cause and stop. The two-refuted-hypotheses/no-new-boundary rule was not triggered; the allocator experiment obtained concrete new read and field-word boundaries. The report remains `blocked`, rather than claiming the whole target cluster is solved.

changed_files:

- `tools/emulation/probe_directionalblur_f16_allocator.py`
- `reports/fuzz/f16_dblur_generated_noise/allocator.json`
- `reports/fuzz/f16_dblur_generated_noise/before.json`
- `reports/fuzz/f16_dblur_generated_noise/after.json`
- `reports/fuzz/f16_dblur_generated_noise/replay.json`
- `orchestra/reports/F16-dblur-generated-noise-fallback.md`

verify:

Run from this worktree. These are the commands used, with recheck destinations so retained evidence is not overwritten:

```sh
S="$PWD/orchestra/state/F16-dblur-generated-noise-fallback"
W=/Users/onmk/.cache/olm-emu/radial_windows_reference_v2_20261001/target/release/aex-guest-worker
P='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S" PYTHONDONTWRITEBYTECODE=1
"$P" tools/emulation/probe_directionalblur_f16_allocator.py --worker "$W" --report "$S/allocator-recheck.json" > "$S/allocator-recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2 --scratch "$S" --worker "$W" --report "$S/before-recheck.json" --corpus "$S/before-recheck-corpus" --shrink-attempts 0 > "$S/before-recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2 --scratch "$S" --worker "$W" --report "$S/after-recheck.json" --corpus "$S/after-recheck-corpus" --shrink-attempts 0 > "$S/after-recheck.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdirectionalblur --jobs 2 --replay tests/fuzz_corpus/olmdirectionalblur --scratch "$S" --worker "$W" --report "$S/replay-recheck.json" --corpus "$S/replay-unused" > "$S/replay-recheck.log" 2>&1
export PYTHONPATH=tests
"$P" -m unittest test_directionalblur_general_feature_budget_20261001 test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_generator_is_externally_pinned test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_exact_rows test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_recanonicalized_row_tamper_rejected test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_claim_tamper_rejected > "$S/tests-fast-recheck.log" 2>&1
git diff --check
```

Expected: every command exits 0; trace assertions establish six fixture/session exact matches, outside-read case membership `{167,183,222,246}`, padding-dependent field membership identical to that set, unchanged in-allocation tables, and zero final-byte deltas for the padding experiments. Campaigns report 235 exact/23 mismatch/40 refusal/2 uncompared per route, corpus 56/56 matches_saved, tests 5/5. Wall-time budgets may vary with machine load and must not be counted as exact.

Check the committed before/after result equality directly:

```sh
python3 - <<'PY'
import json
from pathlib import Path
d = Path('reports/fuzz/f16_dblur_generated_noise')
b, a = [json.loads((d / (n + '.json')).read_text()) for n in ('before', 'after')]
assert len(b['cases']) == len(a['cases']) == 300
assert all(x['index'] == y['index'] and x['result'] == y['result']
           for x, y in zip(b['cases'], a['cases']))
r = json.loads((d / 'replay.json').read_text())
assert r['completed'] == 56 and r['replay_matches_saved']
print('300 unchanged campaign results; 56 saved corpus results reproduced')
PY
```

next:

- Keep the current negative-table-index safety refusal. A separate ticket can trace which generated cells the sampler actually consumes and prove whether safe lazy generation can avoid irrelevant invalid reads; do not invent allocator contents or silently clamp negative indices.
- Continue the valid generated-Noise fallback separately with index102's first differing intermediate and index145 as a regression witness; this report's zero out-of-bounds controls do not solve their admission/arithmetic.
- Route the ten Noise-disabled Size × Fade campaign cases to their dedicated work. Preserve F06's distinction between the already-exact reduced corpus and unresolved full campaign cases.
- Acceptance remains incomplete. No production fix or admission expansion is submitted for merge.

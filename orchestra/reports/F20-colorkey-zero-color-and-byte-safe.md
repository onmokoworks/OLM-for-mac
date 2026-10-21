status: done

summary:
- Admit count zero through both ColorKey parameter checkout paths after 41/41 gate-off exact results and clean sanitizers.
- Replace typed world-pointer dereferences with byte copies through aligned pixel values, including every edge-path write/continue.
- Restore pixel-local source-minus-matte composition and RGB component unordered comparisons from original instructions and intermediate witnesses.
- Seed-1 Smart exact improves 255→299/300; Classic exact remains 0→0. All three retained cases become Smart exact; no prior exact case changes.
- Final 600 campaign route executions and 1,152 independent boundary checks are sanitizer-clean; six selected existing tests pass.

facts:

Base commit: `9bdbc01e437f2367c21b3a2a9621f4585802c553`, branch `orch/F20-colorkey-zero-color-and-byte-safe`.
Read `AGENT_GUIDE.md`, `tools/emulation/GOTCHAS.md`, the ColorKey decision-matrix/forbidden-action row in the ledger, the plan's classification/ColorKey entries, and T12's evidence. No other plugin, release gate, ledger, historical corpus, MAIN file, or emulator source was changed. No worker was rebuilt.

Committed machine evidence: `reports/fuzz/colorkey_F20.json`. It contains all 300 before/after result dictionaries and input hashes, corpus comparison dictionaries, live-builder intermediate comparisons, instruction traces, boundary input/oracle hashes, and build/source provenance. Larger logs and regenerable binaries remain under the ticket scratch directory.

Identities (SHA256):

- Original AEX: `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- Cached worker: `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2`, used at `/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker`.
- Baseline ColorKey source: `8d2b94bfd1fae7264c075414965f5461e6c5a5653a7ba71db7217884e405dabf`.
- Final ColorKey source: `a7a177101066c8939a9716b079af22aed51430578856fe14b7474b544b2794ed`.

Campaigns actually run, each with `--plugin olmcolorkey --n 300 --seed 1 --jobs 2 --shrink-attempts 0`, the cached `--worker`, and separate ticket-local `--scratch`, `--report`, and `--corpus` paths:

| Build / route | Exact | Mismatch | Refusal | Uncompared | Sanitizer-affected cases |
|---|---:|---:|---:|---:|---:|
| Before optimized / Classic | 0 | 259 | 41 | 0 | not enabled |
| Before optimized / Smart | 255 | 3 | 41 | 1 | not enabled |
| Before ASan+UBSan / Classic | 0 | 259 | 41 | 0 | 88 |
| Before ASan+UBSan / Smart | 255 | 3 | 41 | 1 | 88 |
| Final optimized / Classic | 0 | 300 | 0 | 0 | not enabled |
| Final optimized / Smart | 299 | 0 | 0 | 1 | not enabled |
| Final ASan+UBSan / Classic | 0 | 300 | 0 | 0 | 0 |
| Final ASan+UBSan / Smart | 299 | 0 | 0 | 1 | 0 |

`tools/fuzz/run.py` ran the initial/final optimized campaigns directly. `run_colorkey_revision_F20.py --source-ref 9bdbc01e437f2367c21b3a2a9621f4585802c553` reran the original source with sanitizers, without changing the checkout. Both sanitizer campaigns reproduce their optimized comparison dictionaries exactly after removing diagnostics. Before used recoverable UBSan; final used `UBSAN_OPTIONS=halt_on_error=1`. Leak checking was disabled. Every pre-existing Smart exact result dictionary is unchanged. The only previously rendered cases whose output hashes changed are indices 20, 99, and 126, all toward exact.

The 300 original Classic outputs are all zero bytes, from the worker's zero-initialized destination. This ticket does **not** call that a numerical Classic image or claim Classic closure. The Mac Classic and Smart output hashes agree for every final campaign case. The like-named route comparison is retained transparently: Classic exact does not decrease, but its 41 prior refusals now render and are reported as mismatches against that zero output. Original Smart index 96 still rejects `api-ms-win-crt-math-l1-1-0.dll!atan2f`; its oracle result is unchanged. No comparator or route mapping was modified.

**Gate-off prerequisite.** With the count-zero guard still active by default, the byte-safe/subtraction candidate compiled with `OLM_COLOR_TRIAGE_BYPASS=1 OLM_COLOR_TRIAGE_SANITIZE=1` produced 298 Smart exact, one remaining signed-zero mismatch, and the same oracle rejection. All 41 zero-count cases were exact, and all 600 route executions were sanitizer-clean. After the comparator recovery, a second gate-off sanitizer campaign produced 299 Smart exact, all 41 zero-count exact, and zero sanitizer reports. Only then were the default count guards changed from `<1` to `<0` and the obsolete experimental macro removed. Negative and over-maximum counts remain rejected. T12's 16 newly reachable odd-stride UB cases are included in this now-clean gate-off population; the independently rerun baseline reproduces its 88 default UB cases per route.

**First divergence and causes.** `probe_colorkey_stages_F20.py` captures the original parameter record through the direct PF32 worker call (`--watch function=0x9960,arg=stack5,size=1432,occurrence=1`). It then feeds exact raw corpus words to original `0x1800035d0` and `0x180004170`. Native leaf output equals the cached worker's public Smart output for all three retained cases and generated index 116. PNG is used solely to invoke the parameter builder; PNG pixels are never numerical references. The initially attempted indirect pixel-callback watch was explicitly unhookable in this cached worker; the direct owner watch resolves that instrumentation limitation without a worker change.

- **sNaN:** original initial matte and port matte agree. Original `0x180004175` loads source alpha, `0x18000417a` executes `SUBSS` against matte alpha, and `0x18000417e` writes the result. The port formerly copied source alpha when Thin/Blur were zero. Native `462381ff - 00000000` yields `4623c1ff` (little-endian words); the arithmetic operation quiets sNaN. Restoring the existing matched-matte subtraction to the zero-Blur lane fixes this without inspecting or editing NaN bits.
- **signed zero:** after subtraction alone, retained case 20 still differs first in the initial matte: original alpha `00000080`, port `00000000`. Its source RGB contains sNaN and +infinity and uses premultiplication and RGB per-component thresholds. At `0x1800041da/41f0/4202`, original `COMISS` followed by `JA` rejects only ordered-greater differences. The port's `<=` rejects unordered differences. Replacing those three component comparisons with `!(difference > limit)` recovers the matched matte. Native final `-0 - -0` becomes +0. Both matte and final output then agree for all four witnesses. This is an operation/branch fix, not a signed-zero special case.
- **Alignment:** typed pointers created from arbitrary byte-stride row addresses caused the measured UB. `ReadPixel` and `WritePixel` use `memcpy` and aligned local values; all RenderTyped branches, including early returns and continues, use these helpers. Source/padding/atomic-output checks in the existing SDK host remain active.

`trace_colorkey_alpha_F20.py` additionally ran 24 original bounded Smart-worker boundary traces with signed zeros, finite alpha, two sNaN payloads, qNaN, matching/nonmatching RGB, and count 0/1. It first verifies the five-argument Win64 leaf ABI with `1-.25=.75`, captures matte and both sides of SUBSS, and asserts leaf/final worker agreement. Its fixture record is explicitly bounded; the retained-case probe above uses live original-builder records.

**Retained corpus replay (no corpus files updated):** baseline replay is 3/3 `matches_saved`. Final replay intentionally exits 1 because historical mismatch records have become exact. The committed summarizer verifies that every changed case moves toward exact and that Classic differing-word counts also never increase.

| Retained case | Smart first mismatch before (byte; original→port word) | Smart differing words before→after | Classic differing words before→after | Final output SHA256 (both Mac routes) |
|---|---|---:|---:|---|
| `seed1_case000020_32358eb88430` | 3; `00000000`→`00000080` | 1→0 | 4→3 | `5acad5ae07164031d1b7dda4ef816b83df950e40d014976545734909f6fcbfb7` |
| `seed1_case000099_9b13c27c2f2e` | 274; `4623c1ff`→`462381ff` | 1→0 | 120→120 | `e28708d6a20e69602f72bf9181c731566e16082a594de7d389dbf5ec36d3bbbf` |
| `seed1_case000126_9b13c27c2f2e` | 210; `4623c1ff`→`462381ff` | 1→0 | 67→67 | `e8da6f751871100eb2a2c21e195cf3c85a667186fa61d3beb82f7fc59c773d75` |

Generated zero-count index 116 is also exact after restoration (the prior T12 mismatch first occurred at byte 258). The complete gate-off population remains 41/41 exact, not a finite-only subset.

**Independent regression:** `check_colorkey_boundaries_F20.py` ran 192 zero-count cases (three depths; Keep, Premultiplied, Replace, per-component toggles; zero edges, Thin −1/+1, Blur 1) plus 96 RGB unordered boundary cases (all three component positions, both zero signs, ±infinity and two sNaN payloads, scalar/component and Keep toggles). Odd strides are 1 or 3 extra bytes. Original public Smart compared against both Mac routes under O2 and ASan+UBSan: **288 cases, 1,152/1,152 exact, zero sanitizer reports**. Nonfinite source words and payloads remain in the inputs.

**Existing tests:** `python3 tools/fuzz/test_colorkey_existing_F20.py` passed six tests in 15.631 seconds:

- All three functions in `tests/test_olmcolorkey_parameter_ui_parity_20260806.py`.
- `tests/test_olmcolorkey_generic_pixel_local_beta.py::test_generic_pixel_local_beta_worlds`.
- `tests/test_olmcolorkey_generic_pixel_local_pairwise.py::test_generic_pixel_local_pairwise_matrix`.
- The same module's `test_generic_edge_thin_under_asan_ubsan`.

The wrapper only resolves external SDK compiler paths into read-only MAIN and places temporaries in ticket scratch; test assertions and production-source selection are unchanged. Two initially selected historical tests fail before exercising this fix, and the same failures were reproduced with baseline source: the 20260728 parameter-order test searches for an obsolete `ParamsSetup` body; the generic ROI fixture lacks `PF_OutFlag2_SUPPORTS_THREADED_RENDERING`. They were not weakened or repaired in this ticket. The first baseline ROI reproduction needed its source's header include resolved into the worktree; after resolving that path it reproduced the same missing-flag error.

inference:

- The observed sNaN cluster is caused by the omitted source-minus-matte operation. The signed-zero witness additionally exposes the RGB unordered classifier branch; subtraction alone is insufficient.
- Odd-stride UB is eliminated for the measured fake-host contract by byte-safe access. Native AE's ability to supply such strides is not established here.
- Count zero follows the existing general keying/edge/composition pipeline; the measured cases require neither a synthetic passthrough nor final-bit corrections.
- These CPU-emulation/fake-host results do not establish native Windows UCRT, native AE, arbitrary nonfinite/color-space combinations, or general Classic numerical ownership.

changed_files:

- `mac/OLMColorKey/OLMColorKey.cpp`
- `tools/fuzz/run_colorkey_revision_F20.py`
- `tools/fuzz/probe_colorkey_stages_F20.py`
- `tools/fuzz/trace_colorkey_alpha_F20.py`
- `tools/fuzz/check_colorkey_boundaries_F20.py`
- `tools/fuzz/test_colorkey_existing_F20.py`
- `tools/fuzz/summarize_colorkey_F20.py`
- `tools/fuzz/verify_colorkey_F20.sh`
- `reports/fuzz/colorkey_F20.json`
- `orchestra/reports/F20-colorkey-zero-color-and-byte-safe.md`

verify:

From this worktree:

```sh
bash tools/fuzz/verify_colorkey_F20.sh
git diff --check
```

The shell script spells out and reruns the required `tools/fuzz/run.py --plugin olmcolorkey --n 300 --seed 1 --jobs 2` campaign with scratch corpus, baseline source replay, both sanitizer campaigns, both corpus replays, strict intermediate checks, original instruction traces, the independent matrix, and the six existing tests. Expected final line:

```text
F20: 255 -> 299 Smart exact; Classic 0 -> 0; 41 zero-count exact; 3 corpus improvements; sanitizer clean
```

The corresponding component commands were executed individually for this report; the combined shell passed `bash -n`. It writes only ticket scratch, including a fresh evidence JSON, and intentionally handles the improved corpus replay's exit 1. Baseline uses `git show` into scratch, never a checkout/reset. All tests and probes use the committed final source except the explicitly historical baseline. Scratch remained below 100 MiB; regenerable build outputs were removed before commit.

next:

- No F20 target remains open in the measured clusters.
- Separate follow-up: determine original Classic command ownership/no-write behavior and represent it in the route comparator; retain current Classic zero-output results until then.
- Separate follow-ups: cached worker `atan2f` rejection, broader nonfinite/color-space intersections, and the two stale historical test harnesses. Do not infer native Windows/AE coverage from this ticket.

status: done
summary:
- Built/registered F52c oracle and Universal standalone bundle geometry host; default worker unchanged.
- Qualified eight source adapters and eight A01 bundles; realistic-v1 now carries all geometry and negotiated output bounds.
- Seed 1/n100: 800 inputs, 1,500 route comparisons; E/M/R/U = 288/212/892/108 (100 E are no-write owner checks).
- Default oracle qualification 121/121; source/bundle delivery 45/45 + 24/24; independent expanded-allocation tests pass.
- Default corpus batch 810/812 matched; C49 isolated old/current replay matches, C46 retains the prior oracle failure. No plugin code changed.

facts:

## Host contract and durable builds

The oracle patch applies to hash-bound `~/.cache/olm-emu/src-F52/reference-guest`.
Sources are retained at `~/.cache/olm-emu/src-F52c/reference-guest`, and both new
hosts are registered in INDEX. Build memory free was **62%**
(oracle) and **65%** (bundle); builds were serial. SDK rationale
and executable commands are in [README-F52c](../../tools/emulation/aexcompat_patches/README-F52c.md).

- Oracle SHA-256: `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`.
- Universal bundle host SHA-256: `28f6fc3fa5d644be05997c8c1e1b39ba71fcccf67d532e4725f440d8d7c1a51f`; arm64 executed here.
- `build_F52c.py --verify-source` reconstructed the committed patch and matched
  **every source file** and the registered build manifest/binary. The initial
  staged whitespace check flagged blank unified-patch context lines; the patch
  was reformatted with zero context and reverified byte-for-byte. Both patch
  hashes are retained in `F52c-evidence/patch-format.json`; source/binary unchanged.
- `--negotiate-output 1` allocates from PreRender result_rect, checks max_result_rect
  as a bound, sets world/input-relative origins, handles empty results, and returns
  packed output plus `frame_done.output.rect`. Default allocation stays unchanged.
- Source and bundle hosts share `geometry.hpp`. The legacy shims are extended only
  in scratch copies. Padding is bytes, including odd strides; dimensions, extent,
  request, aspect and output bounds are forwarded. Rectangles are compared before
  admitting sample equality. Classic has no Smart request; it receives all other
  geometry, and Smoother's realistic route is Classic only.
- Eight source adapters are qualified. Bundle qualification is independent, using
  cached A01 `.plugin` files without rebuilding them. These bundles predate P01a;
  their hashes are in [bundle-qualification.json](F52c-evidence/bundle-qualification.json).
- MAIN remained at `ef2b582f`; P01b/P01c had not merged, so no new ColorKey or
  DirectionalBlur realistic campaign was run. Their default oracle checks remain.
- No release gate, ledger, plugin implementation, MAIN source or default worker
  was modified. Source/bundle qualification is fake-host evidence, not native AE.

## Commands actually run

All commands were run in this worktree. Long output went to this ticket's scratch.

1. `python3 tools/emulation/aexcompat_patches/build_F52c.py`, `--register`, and
   `--verify-source`; `python3 tools/emulation/aexcompat_patches/build_F52c_bundle.py`.
   Both durable builds succeeded; source binding passed. The bundle was refreshed
   once to handle empty stream output, retaining its previous binary/manifest in
   cache history; default workers were never replaced. Build manifests are
   [worker-build.json](F52c-evidence/worker-build.json) and
   [bundle-build.json](F52c-evidence/bundle-build.json).
2. `python3 tools/fuzz/validate_F52c.py`: **121 checks pass**, covering all ten
   adapters' available default routes/depths against F52, odd padding, and the
   retained Blur/DirectionalBlur scaled-control tests. This is sample-byte
   identity; the new optional JSON rectangle field is not claimed protocol-identical.
3. `python3 tools/fuzz/verify_F52c_host.py` and `verify_F52c_guest.py`: independent
   native synthetic EffectMain and cross-built synthetic Windows PE both produce
   **816 exact packed bytes**, expanded **17x12**, layer origin **(-3,-2)**,
   input-relative origin **(3,2)**, **71-byte stride**; guards intact. These are
   allocation/transport tests, not synthetic replacements for the OLM oracle.
   `verify_F52c_bundle_empty.py` also passes: success code, empty pixels, no
   SmartRender invocation; bundle delivery checks were rerun after that fix.
4. `python3 tools/fuzz/qualify_F52c.py`: **45/45** per-source-adapter delivery
   checks. `python3 tools/fuzz/qualify_F52c_bundle.py`: **24/24** bundle delivery
   checks. Expected metadata and actual observations are retained. Early fixture
   issues (scratch directory reuse, shim aggregate field placement, hex-host stderr
   parsing, and implicit input-parameter slot in bundle declarations) were fixed
   before qualification; they are not plugin failures.
5. `python3 tools/fuzz/probe_F52c_oracle.py`: **29** rectangle probes, **28** normal
   outputs and one Smoother2 partial-ROI guest exception. Covers full, expanded
   request, subset and empty result; expanded *allocation* is tested separately by
   the synthetic PE. [Results](F52c-evidence/oracle-rectangles.json).
6. `python3 tools/fuzz/measure_F52c.py --plugin NAME --n 100` for each of the eight
   names below, serially. The driver always uses seed 1 and `sample(...,'realistic')`;
   explicit equivalents are `--geometry realistic --jobs 1`. **800 inputs / 1,500
   comparisons**, **zero candidate transport/host errors**. Original guest errors
   and timeouts remain U. Raw cases, parameters, input/output hashes and named
   refusals are in `F52c-evidence/*-results.jsonl`; candidate/AEX/worker identities
   are in the corresponding provenance files. The early provenance `world` prose
   is inherited/stale; the committed per-case geometry fields are authoritative.
   Future provenance now names realistic-v1 explicitly.
7. `python3 tools/fuzz/run.py --plugin olmblur --geometry realistic --seed 1 --n 1
   --jobs 1 --shrink-attempts 0 ...`, for source and `--candidate plugin-bundle`
   with cached A01 OLMBlur: both CLI runs **complete** and correctly record refusal.
   [Source](F52c-evidence/cli-source.json), [bundle](F52c-evidence/cli-bundle.json).
8. `python3 tools/fuzz/replay_F52c.py`: **812** saved cases attempted; **810** match
   the saved comparison object. RadialBlur C46_seed1_case000280 retains the prior
   F52 oracle stop at **0x180002860**. C49_seed1_case000117 had a batch guest unmapped
   read at **0x18000287c**. `verify_F52c_replay_failure.py` and `--current` each
   reran C49 once, using the original recorded F46 worker and 60-second timeout:
   **both succeeded**, output hash
   `6958423267181cc23ab6aed257b5007841f3a39d3532abb0ea2a9e616947593d`, matching its
   saved oracle. The batch is not relabeled all-green. No expectations changed.
9. `python3 -m unittest discover -s tools/fuzz -p 'test_*.py'` with ticket-local
   `OLM_FUZZ_TEST_SCRATCH`/`TMPDIR`: **42 tests, OK, 2 skipped**. The added tests
   cover geometry-only mismatch, Classic request mapping and route restoration.
   `git diff --check` passes.

## Campaign E/M/R/U

U takes precedence whenever the oracle is unavailable. R means Mac refusal while
the original returned normally. E includes exact no-write owner checks (ToonDilate
Classic's 100); these do not establish rendered-pixel functionality. All other E
require matching bounds and every raw sample byte.

| Plugin | Route | E | M | R | U |
|---|---|---:|---:|---:|---:|
| ColorKeep | classic | 5 | 4 | 91 | 0 |
| ColorKeep | smart | 11 | 0 | 89 | 0 |
| DistanceGradation | classic | 2 | 98 | 0 | 0 |
| DistanceGradation | smart | 10 | 3 | 83 | 4 |
| KiraKira | classic | 0 | 6 | 94 | 0 |
| KiraKira | smart | 11 | 0 | 89 | 0 |
| RadialBlur | classic | 0 | 59 | 41 | 0 |
| RadialBlur | smart | 11 | 5 | 71 | 13 |
| ToonDilate | classic | 100 | 0 | 0 | 0 |
| ToonDilate | smart | 63 | 37 | 0 | 0 |
| Smoother2 | classic | 0 | 0 | 100 | 0 |
| Smoother2 | smart | 11 | 0 | 50 | 39 |
| Smoother | classic | 31 | 0 | 34 | 35 |
| Blur | classic | 3 | 0 | 80 | 17 |
| Blur | smart | 30 | 0 | 70 | 0 |

## Refusal attribution and first witnesses

Every R below is **Mac-only** in its observed witness: the original returned
successfully. No faithful original PF-error refusal class was established. A
refusal overlapping U cannot honestly be labeled faithful or Mac-only for that
individual case: those entries are explicitly **unresolved**. In particular,
Smoother PF32 is rejected by the oracle's advertised-depth check, and original
OpenCV/guest exceptions and allocation caps are not proven native-AE PF errors.
The raw evidence preserves these distinctions rather than inventing binary labels.

| Plugin/route | Tag | Class | Count | First seed-1 index |
|---|---|---|---:|---:|
| ColorKeep/classic | `Render:classic-bitdepth@399` | Mac-only | 35 | 2 |
| ColorKeep/classic | `Render:render-mapping@403` | Mac-only | 56 | 0 |
| ColorKeep/smart | `SmartRender:smartrender-mapping@469` | Mac-only | 89 | 0 |
| DistanceGradation/smart | `RenderBits:pf32-smart-profile@2149` | unresolved-oracle-unavailable | 1 | 53 |
| DistanceGradation/smart | `SmartPreRender:prerender-size-downsample@2264` | Mac-only | 83 | 0 |
| DistanceGradation/smart | `SmartPreRender:prerender-size-downsample@2264` | unresolved-oracle-unavailable | 3 | 10 |
| KiraKira/classic | `Render:tuple-layout-source@2591` | Mac-only | 94 | 0 |
| KiraKira/smart | `SmartPreRender:checkout-geometry@2849` | Mac-only | 1 | 37 |
| KiraKira/smart | `SmartPreRender:request-not-admitted@2793` | Mac-only | 88 | 0 |
| RadialBlur/classic | `RenderWorld:generic-budget@5528` | Mac-only | 3 | 48 |
| RadialBlur/classic | `RenderWorld:generic-world-not-admitted@5512` | Mac-only | 20 | 1 |
| RadialBlur/classic | `RenderZoomTyped:unadmitted-zoom-profile@2992` | Mac-only | 11 | 21 |
| RadialBlur/classic | `ValidateNoiseLayerWorld:noise-world-invalid@5323` | Mac-only | 7 | 12 |
| RadialBlur/smart | `SmartRender:smartrender-partial-checkout@6277` | Mac-only | 71 | 0 |
| RadialBlur/smart | `SmartRender:smartrender-partial-checkout@6277` | unresolved-oracle-unavailable | 11 | 7 |
| Smoother2/classic | `Render:classic-entry-unowned@5289` | Mac-only | 100 | 0 |
| Smoother2/smart | `SmartPreRender:prerender-frame-contract@5321` | Mac-only | 50 | 1 |
| Smoother2/smart | `SmartPreRender:prerender-frame-contract@5321` | unresolved-oracle-unavailable | 36 | 0 |
| Smoother/classic | `ValidatePublicWorlds:world-depth-32-unsupported@4044` | unresolved-oracle-unavailable | 14 | 15 |
| Smoother/classic | `ValidatePublicWorlds:world-extent-not-full-frame@4025` | Mac-only | 34 | 0 |
| Smoother/classic | `ValidatePublicWorlds:world-extent-not-full-frame@4025` | unresolved-oracle-unavailable | 21 | 2 |
| Blur/classic | `Render:classic-nondefault-tuple@1447` | Mac-only | 48 | 3 |
| Blur/classic | `Render:classic-nondefault-tuple@1447` | unresolved-oracle-unavailable | 14 | 0 |
| Blur/classic | `Render:classic-pf32-unowned@1429` | Mac-only | 32 | 2 |
| Blur/classic | `Render:classic-pf32-unowned@1429` | unresolved-oracle-unavailable | 3 | 25 |
| Blur/smart | `SmartRender:generic-input-world@2088` | Mac-only | 55 | 0 |
| Blur/smart | `SmartRender:generic-output-world@2089` | Mac-only | 15 | 5 |

[summary.json](F52c-evidence/summary.json) stores each first refusal/mismatch/U
witness in full (parameters, exact geometry, hashes, errors and tags). Inputs
regenerate from the committed seed/index sampler; no expected-value patch is used.
First mismatches:

| Plugin/route | Index | First difference |
|---|---:|---|
| ColorKeep/classic | 4 | word 0: original `00`, Mac `ff`; 13682 differing words |
| DistanceGradation/classic | 0 | word 0: original `00`, Mac `b4`; 205 differing words |
| DistanceGradation/smart | 12 | rect [1, 0, 2, 1] vs [0, 0, 2, 18] |
| KiraKira/classic | 3 | word 0: original `0000`, Mac `996a`; 480 differing words |
| RadialBlur/classic | 0 | word 4: original `00`, Mac `1e`; 303 differing words |
| RadialBlur/smart | 1 | word 2: original `9334`, Mac `9434`; 1 differing words |
| ToonDilate/smart | 0 | rect [5, 4, 6, 5] vs [0, 0, 11, 7] |

## Original disassembly pointers (facts versus interpretation)

`python3 tools/fuzz/static_F52c.py` streams read-only MAIN disassemblies. Their
hashes, exact instruction excerpts, and non-stack `+0x11c` operand sites are in
[disassembly.json](F52c-evidence/disassembly.json). SDK offsets identify X/Y scales
at +0x11c/+0x120 and +0x124/+0x128; world dimensions at +0x24/+0x28, extent at
+0x2c and world origins at +0x68/+0x6c. Offset matches alone are not caller proof.

- **ColorKeep:** `0x180001033..0x180001106` derives a row count from output extent
  bottom-top and passes the extent pointer (world+0x2c) into the iterate suite.
  No direct non-stack +0x11c load was found in its disassembly. This does not prove
  that all indirect suite/helper geometry behavior is absent.
- **DistanceGradation:** `0x18117176d..0x1811717bb` multiplies world width/height
  by X/Y denominators, converts to float32, divides by the numerator, then truncates
  to integers. `0x181171bb0` also multiplies by X numerator. Interpretation: an
  inverse-size reconstruction path, not evidence that threshold should be scaled.
- **KiraKira:** `0x18114cc88..0x18114cd32` captures source world dimensions, forms
  float32 X num/den, conditionally changes working dimensions using the constant
  at `0x181486c1c`, then scales integer context fields. Context-field names and
  that constant's numerical meaning are not newly claimed here.
- **RadialBlur:** `0x180006dc8..0x180006e40` subtracts source-world origins from
  double coordinates, forms float32 X num/den, scales a float context field and
  converts the ratio to double to scale those coordinates. This is direct origin
  and downsample arithmetic, not a final-byte correction.
- **ToonDilate:** `0x1801a5ad4..0x1801a5b26` forms float32 X num/den and multiplies
  the scalar supplied by the caller; its truncation/positive-fraction increment
  implements ceiling for nonnegative products. It then reads world height.
- **Smoother2:** helpers `0x180016870..0x1800168be` and `0x1800168d0` compute
  inverse X/Y ratios in double and scale pointed-to coordinates. Their presence
  is fact; active caller coverage is unconfirmed. The ROI probe above independently
  records the original's exception on a smaller output allocation.
- **Smoother Classic:** `0x18000122c..0x18000128b` uses output extent bottom-top,
  invokes host copy, and reads source world dimensions for allocation. No direct
  non-stack +0x11c load was found; do not infer every host-mediated scale is unused.
- **Blur:** `0x1800022ee..0x180002315` forms float32 X num/den, multiplies Amount
  and truncates the radius, consistent with P01a. The current failures are named
  input/output-world guards; the plugin implementation was not changed here.

Pixel-aspect-specific **plugin arithmetic** is not newly established by these
excerpts. Host delivery of aspect is verified; ROI/aspect behavior still needs
per-plugin follow-up. Do not interpret absence of an excerpt as proof of no use.

inference:

- The repeated named admission guards account for most measured failures; simply
  loosening them would be unjustified without the retained exact original witnesses.
- DistanceGradation/ToonDilate Smart have explicit negotiated-rectangle differences.
  RadialBlur also has a same-rectangle PF16 numerical witness (index 1, `9334` vs
  `9434`); those need different investigations.
- C49's isolated success with both adapter versions suggests a transient oracle
  failure; its underlying cause is unproved. C46 remains the known boundary.
- No two-hypothesis numerical tuning loop was undertaken; this ticket changes host
  plumbing and records failures. U cannot establish faithful native refusal.

changed_files:

- `tools/emulation/aexcompat_patches/F52c-geometry.patch`, `build_F52c.py`,
  `README-F52c.md`, `F52c-plugin-host.cpp`, `build_F52c_bundle.py`.
- `tools/emulation/aexcompat_patches/F47d-native-bridge.cpp` (opt-in compile branch).
- `tools/fuzz/adapters/`: common geometry transport, scratch shim augmentation,
  per-adapter qualification, bundle transport and independent bundle admission.
- `tools/fuzz/harnesses/geometry.hpp`, `geometry_contract.cpp`, `geometry_guest.c`.
- `tools/fuzz/core.py`, `geometry.py`, `run.py`, `test_geometry.py`.
- `tools/fuzz/{validate,verify,qualify,measure,summarize,probe,static,replay}_F52c*`:
  reproducible qualification, measurements, static extraction and replay tools.
- This report and `orchestra/reports/F52c-evidence/`.

verify:

```sh
export TMPDIR="$PWD/orchestra/state/F52c-geometry-hosts-and-campaigns"
export OLM_FUZZ_TEST_SCRATCH="$TMPDIR/tests"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OLM_FUZZ_TEST_SCRATCH"
python3 tools/emulation/aexcompat_patches/build_F52c.py --verify-source
python3 tools/fuzz/validate_F52c.py
python3 tools/fuzz/verify_F52c_host.py
python3 tools/fuzz/verify_F52c_guest.py
python3 tools/fuzz/verify_F52c_bundle_empty.py
python3 tools/fuzz/qualify_F52c.py
python3 tools/fuzz/qualify_F52c_bundle.py
python3 -m unittest discover -s tools/fuzz -p 'test_*.py'
for plugin in colorkeep olmdistancegradation olmkirakira radialblur olmtoondilate olmsmoother2 olmsmoother olmblur; do
  python3 tools/fuzz/measure_F52c.py --plugin "$plugin" --geometry realistic --jobs 1 --n 100
done
python3 tools/fuzz/summarize_F52c.py
python3 tools/fuzz/replay_F52c.py
python3 tools/fuzz/verify_F52c_replay_failure.py
python3 tools/fuzz/verify_F52c_replay_failure.py --current
```

Expected bounded qualification counts are above. Campaign counts are the observed
run, not a promise against timeout/guest nondeterminism; retain and report any new
U. Do not overwrite corpus expectations to make replay green. Build commands on
an already installed cache intentionally refuse overwrite; use `--verify-source`.
The existing bundle executable is durable in the cache, with its exact source
manifest committed in the evidence. Source changes do not install/rebuild plugins.

next:

1. **F52d-oracle-ROI-errors:** resolve Smoother2/DG/Radial guest exceptions, allocator
   caps and C46/C49 instability; determine native PF-error versus host limitation
   before assigning faithful/refusal labels to U. Broaden native-AE/empty/origin
   and x86_64 bundle qualification separately.
2. **ColorKeep geometry:** `render-mapping` / `smartrender-mapping`, then Classic
   bitdepth behavior; preserve index 0 refusal and index 4 Classic mismatch.
3. **DistanceGradation geometry:** PreRender scale admission, then index 12 output
   rectangle mismatch and independent Classic output ownership; retain inverse-size
   arithmetic rather than reintroducing threshold scaling.
4. **KiraKira geometry:** requested/checkout geometry guards and context scale/
   working-size branch; keep Classic tuple coverage separate (first mismatch 3).
5. **RadialBlur geometry:** partial checkout/origin mapping; separate PF16 index 1
   `9334`/`9434` numerical boundary, Classic ownership and resource-budget guards.
6. **ToonDilate geometry:** match requested result rectangle (first index 0), then
   quantify float32 scale/ceil radius semantics; keep Classic no-write unchanged.
7. **Smoother2 geometry:** frame-contract guards and smaller-output ROI exception;
   separately decide Classic owner (original returns, Mac refuses all 100).
8. **Smoother Classic geometry:** extent restriction on supported PF8/PF16; keep
   PF32 advertised-depth limitation separate and do not invent float support.
9. **Blur geometry (P01a continuation):** input extent/output mapping guards, first
   seed-1 index 0; preserve the now-exact downsample arithmetic and Legacy radius-0
   behavior. Classic tuple/depth limitations remain independent.

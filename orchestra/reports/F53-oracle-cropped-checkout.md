status: done
summary:
- Added and registered F53 cropped-checkout oracle, plus source and Universal bundle host support; no plugin code changes.
- Opt-in realistic-v2 uses actual PreRender request intersection; explicit packed cropped payloads are also supported.
- P04b 40x30-layer / 20x15-input DirectionalBlur original now renders successfully; Smoother2 original PreRender rectangle is captured.
- Seed 1, n100 for all ten source candidates: E880 / M39 / R66 / U15; 29 refusals are Mac-only.
- Legacy generation/replay and original-worker comparisons pass within the tested scope; bundle smoke retains one pre-existing host limitation.

facts:
- Branch `orch/F53-oracle-cropped-checkout`; checkpoint commit `502d1364` preceded final measurement completion.
- `python3 tools/emulation/aexcompat_patches/build_F53.py`: memory_pressure 61% free, cargo release/offline/locked, one job, 2m51s. Build tree under `~/.cache/olm-emu/build-F53/` was removed. `--register` and `--verify-source` passed.
- Patch representation was normalized to a zero-context unified diff for whitespace checks; applying it to F52c reproduced the identical built source manifest. Cached metadata retains the original patch hash, updated equivalent patch hash, and unchanged binary hash.
- Oracle: `~/.cache/olm-emu/worker-F53-geom/aex-guest-worker`, SHA256 `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`. Parent is F52c. Committed patch and build recipe reproduce/bind the cached source, and the INDEX entry is installed.
- `python3 tools/emulation/aexcompat_patches/build_F53_bundle.py --refresh`: final Universal bundle host SHA256 `218f3a3e702dd509b99997aa4c98259c7264036ba2cad48e3dc7853ee7952c6b`, memory free 60%; registered separately. Final cache records are in `F53-evidence/cache-bindings.json`.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_F53_geometry.py`: PASS, 300 unchanged default/v1 generations, 100 v2 payload checks, 100 full and 100 reduced corpus replays.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_F53_legacy.py`: all 60 F52c/F53 pairs matched without the new option; 57 successful outputs were byte-identical, three were matching non-success outcomes. This is bounded regression evidence, not an exhaustive all-options proof.
- SDK facts are quoted with line numbers and file hash in `F53-evidence/sdk-checkout-excerpts.txt`; rationale is in `tools/emulation/aexcompat_patches/README-F53.md`. Checkout result is actual availability, max is full-request availability, world origin is in layer coordinates, and reference dimensions exclude downsample.
- The new path is used with `--negotiate-output 1`. Explicit `--checkout-rect l,t,r,b` takes a packed sub-rectangle; `--checkout-rect auto` takes full sampled storage and returns cropped Smart worlds. In realistic-v2, absent case-level `checkout_rect` selects auto. Entire option absence preserves F52c behavior. Default/v1 RNG draws and replay are retained.

Measured source survey, seed=1, n=100 each, max_size=256, timeout=10s, strictly serial (`verify_F53.py --survey --n 100 --label survey-auto`; the script now also accepts only `--jobs 1`). Smart route for nine plugins; OLMSmoother uses its supported Classic route. E=raw bytes AND output rectangle exact; M=mismatch; R=candidate refusal; U=not compared. Refusals are not counted as matches.

| Plugin | E | M | R | U | Mac-only R |
|---|---:|---:|---:|---:|---:|
| OLMBlur | 100 | 0 | 0 | 0 | 0 |
| ColorKeep | 97 | 0 | 3 | 0 | 3 |
| OLMColorKey | 100 | 0 | 0 | 0 | 0 |
| OLMDirectionalBlur | 74 | 0 | 26 | 0 | 26 |
| OLMDistanceGradation | 97 | 0 | 1 | 2 | 0 |
| OLMKiraKira | 99 | 0 | 1 | 0 | 0 |
| OLMSmoother2 | 61 | 39 | 0 | 0 | 0 |
| OLMToonDilate | 100 | 0 | 0 | 0 | 0 |
| OLMRadialBlur | 87 | 0 | 0 | 13 | 0 |
| OLMSmoother | 65 | 0 | 35 | 0 | 0 |
| Total | 880 | 39 | 66 | 15 | 29 |

- Original-side non-successes: 35 OLMSmoother PF32 cases rejected from the original's advertised depth capability before rendering; three DistanceGradation and one KiraKira original OpenCV exceptions outside the host's unwind contract; eleven RadialBlur oracle execution faults and two wall-time budgets. No nonzero returned original render PF_Err was established. The exceptions/faults/budgets are not reclassified as original-plugin refusals. The other 37 candidate refusals coincide with unavailable/unsupported originals, so are not asserted Mac-only.
- Refusal tags: ColorKeep `ColorKeepValidateWorldPair:world-alignment@219` ×3; DirectionalBlur `SmartRender:smart-generic-world-or-budget@2710` ×26; DistanceGradation `RenderBits:pf32-smart-profile@2205` ×1; KiraKira `SmartRender:tuple-or-source@2936` ×1; Smoother `ValidatePublicWorlds:world-depth-32-unsupported@4062` ×35.
- Original cropped checkouts: 39/100 each for ColorKeep, ColorKey, DirectionalBlur, DistanceGradation, KiraKira, Smoother2, ToonDilate and RadialBlur; OLMBlur requested the entire input (0/100 cropped), OLMSmoother is Classic. These are actual callback observations, not assumed payload sizes.
- First mismatch: Smoother2 index 0, original output rect `[5,4,6,5]`, Mac `[0,0,11,7]`; 4 versus 308 bytes; first byte 0, expected `af`, actual `00`, 308 differing bytes including length difference. All per-case hashes, parameters, callbacks and first mismatches are committed in `F53-evidence/survey-auto-*.jsonl` with provenance; `classification.json` separates original outcomes.

Fixed witnesses (`verify_F53.py`, plus `--bundle --label bundle-witness`):
- DirectionalBlur PF8, Front Strength 5, 40x30 layer, explicit `[0,0,20,15]`, 1,200 input bytes: original output `[0,0,20,15]`, SHA256 `0a21ff72492dcdd55e430eb9607534bfa730a2b4340415c461fa1e6104129597`, identical to P04b's 20x15-layer baseline. Source Mac error 516, tag `SmartRender:smart-generic-world-or-budget@2710`; cached P00b bundle has the equivalent tag at line 2707. This is a confirmed Mac-only refusal, not a byte mismatch.
- Smoother2 same explicit crop: original PreRender result `[0,0,20,15]`, max `[0,0,40,30]`, output SHA256 `3b82d61392ce504baf7bf23c3ce753f16d6c31fe8bddca9e24c1843824c4685f`. Mac PreRender returns `[0,0,40,30]`, then refuses `ValidatePublicWorlds:validate-world-shape@5240`.
- Both plugins' original explicit/auto, zero/nonzero-origin variants all render: eight original successes. Each candidate route has four DirectionalBlur refusals, two Smoother2 refusals and two Smoother2 mismatches. Original PreRender results and max rectangles are recorded verbatim.
- Candidate host corrections were driven by concrete callback failures: legacy PreRender validation must see payload dimensions, and WorldSuite identifies the original world pointer. The final host preserves pointer identity and restores descriptors after SmartRender. An exploratory explicit-random sampler was replaced with automatic PreRender intersection so required halos are not arbitrarily omitted; final reported survey is only `survey-auto`.

Additional validation:
- `verify_F53.py --bundle --survey --n 10 --label bundle-smoke`: 100 cases across all ten retained P00b bundles. ColorKeep has 10 harness errors from unsupported `iterate`; `verify_F53_bundle_baseline.py` confirms the same case fails on BOTH F52c and F53 bundle hosts. This pre-existing limitation is neither numeric mismatch nor plugin refusal. Other bundle smoke statuses and hashes are retained; no bundle algorithm was rebuilt or modified.
- `run.py --plugin olmcolorkey --geometry realistic-v2 --seed 1 --n 3 --jobs 1 --max-size 16 --budget-minutes 2 --shrink-attempts 0 ...`: CLI completed, Smart 3 exact, Classic 3 mismatch. Both-route results are retained in `cli.json`, with its three generated corpora committed under `cli-corpus/`; no Classic conformance claim is made.
- Scratch is about 5 MiB (including exploratory logs); no Rust build tree remains and no task-owned background workers remain. No MAIN, 04_Tools source, plugin production code, release gate, ledger or default worker was modified. `git diff --check` passed.

inference:
- The original cropped DirectionalBlur witness removes P04b's reference-transport blocker. It supports investigating Mac admission/workspace logic in a separate plugin ticket.
- Smoother2's output negotiation differs from the original under crop; this ticket records the difference rather than patching the plugin.
- Dense rectangular availability and automatic request/layer intersection are host policies grounded in SDK coordinates. These runs do not prove all native AE scheduling, sparse-layer, multi-layer, GPU or arbitrary multi-checkout semantics.
- Timing-sensitive budget counts may differ on replay. Execution faults and unsupported exception handling require separate oracle investigation, not pixel tuning.

changed_files:
- tools/emulation/aexcompat_patches/{F53-checkout.patch,build_F53.py,build_F53_bundle.py,README-F53.md}
- tools/fuzz/{geometry.py,run.py,harnesses/geometry.hpp}
- tools/fuzz/adapters/{public,bundle_geometry,plugin_bundle,colorkeep,olmblur,olmcolorkey,olmdirectionalblur,olmdistancegradation,olmkirakira,olmsmoother,olmsmoother2,olmtoondilate,radialblur}.py
- tools/fuzz/{verify_F53.py,verify_F53_legacy.py,verify_F53_bundle_baseline.py,test_F53_geometry.py,summarize_F53.py}
- orchestra/reports/F53-evidence/* and this report

verify:
```sh
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/emulation/aexcompat_patches/build_F53.py --verify-source
python3 tools/fuzz/test_F53_geometry.py
python3 tools/fuzz/verify_F53_legacy.py
python3 tools/fuzz/verify_F53.py --jobs 1 --label verify-witness
python3 tools/fuzz/verify_F53.py --survey --n 100 --jobs 1 --label survey-auto
python3 tools/fuzz/summarize_F53.py
python3 tools/fuzz/verify_F53.py --bundle --jobs 1 --label verify-bundle-witness
python3 tools/fuzz/verify_F53.py --bundle --survey --n 10 --jobs 1 --label verify-bundle-smoke
python3 tools/fuzz/verify_F53_bundle_baseline.py
git diff --check
```
Expected: binding and generator/replay PASS; legacy 60 matched pairs / 57 successful byte comparisons; eight original witness successes with candidate outcomes above; survey table above (wall-time budgets may vary); ColorKeep bundle baseline limitation confirmed on both hosts. All loops are serial. Read `README-F53.md` for first-install build commands; do not overwrite a registered binary merely to verify it.

next:
- Resume P04b using the durable F53 oracle and the committed 40x30/20x15 witness.
- Separate Smoother2 ticket: correct PreRender output negotiation based on this original evidence.
- Separate ColorKeep alignment-admission and bundle iterate-host tickets; separate original OpenCV exception/RadialBlur oracle-fault investigations.
- No plugin numerical fixes or release promotion are part of F53.

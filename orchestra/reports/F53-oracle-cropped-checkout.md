status: partial
summary:
- F53 oracle built, registered and source/patch/binary binding verified.
- Explicit and automatic cropped checkout render in the original DirectionalBlur and Smoother2 AEX.
- Source and bundle candidate hosts support the new checkout option; realistic-v2 is opt-in.
- Seed-1 n100 all-plugin survey is in progress; this is a checkpoint commit.

facts:
- `python3 tools/emulation/aexcompat_patches/build_F53.py`: memory free 61%, release build completed in 2m51s, build tree deleted.
- `python3 tools/emulation/aexcompat_patches/build_F53.py --register` and `--verify-source`: PASS; worker SHA256 `d88c22f67d06c419608d007619df42eac863a35e317ab7cb380617eff2051fb9`.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_F53_geometry.py`: PASS, 300 unchanged default/v1 generations, 100 v2 payload lengths and corpus replays.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_F53.py`: original accepts all eight explicit/auto/offset witnesses. DirectionalBlur 40x30 layer, 20x15 packed input: output SHA256 `0a21ff72492dcdd55e430eb9607534bfa730a2b4340415c461fa1e6104129597`; Mac refuses with `SmartRender:smart-generic-world-or-budget@2710`. No numeric comparison exists for that refusal.
- Smoother2 explicit checkout [0,0,20,15]: original PreRender output [0,0,20,15], max [0,0,40,30], output SHA256 `3b82d61392ce504baf7bf23c3ce753f16d6c31fe8bddca9e24c1843824c4685f`. Candidate PreRender output [0,0,40,30] and shape refusal; no plugin source changes.
- Initial Smoother2 candidate fake callback rejected full-layer forwarding against cropped payload. Host forwarding was corrected before retained measurements; the final refusal is `ValidatePublicWorlds:validate-world-shape@5240`.

inference:
- The required P04b transport blocker is removed. The original witnesses support follow-up plugin investigation; they do not establish complete AE equivalence.
- Automatic cropping is the default inside the new opt-in path (`auto`); option absence deliberately retains legacy F52c behavior. SDK rationale and limitations are in README-F53.md.

changed_files:
- tools/emulation/aexcompat_patches/F53-checkout.patch, build_F53.py, build_F53_bundle.py, README-F53.md
- tools/fuzz/harnesses/geometry.hpp; tools/fuzz/geometry.py; tools/fuzz/run.py
- tools/fuzz/adapters/{public,bundle_geometry,plugin_bundle,colorkeep,olmblur,olmcolorkey,olmdirectionalblur,olmdistancegradation,olmkirakira,olmsmoother,olmsmoother2,olmtoondilate,radialblur}.py
- tools/fuzz/verify_F53.py; tools/fuzz/test_F53_geometry.py
- orchestra/reports/F53-evidence/*; this report

verify:
```sh
python3 tools/emulation/aexcompat_patches/build_F53.py --verify-source
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_F53_geometry.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_F53.py --label verify-witness
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/verify_F53.py --survey --n 100 --label verify-survey
git diff --check
```
Expected: binding and generator tests PASS; witness original successes, with candidate refusals/mismatches as above. Survey counts pending.

next:
- Finish all-plugin survey, distinguish original plugin refusal from host/emulator failures, and qualify bundle transport and legacy worker output equivalence.

# DirectionalBlur 8bpc full-render host fixture

- Current status: superseded by complete full-entry and Mac AE exact evidence
- Latest closeout: `refs/conformance/dblur_frontonly_mac_ae_exact_20260711.md`
- Historical status below: `blocked-rowdriver-instruction-budget`
- Case: `case_0001`, `960x540`
- AEX: `plugins_2025/OLMDirectionalBlur.aex`
- Cap: `200000000` instructions

## ABI Evidence

The real AEX entered PF Iterate8 at `0x1800067c5`. The suite callback read its
own stack using the confirmed Windows x64 layout:

```text
+0x28 area, +0x30 refcon, +0x38 pixel_fn, +0x40 dst
```

Observed first populate call:

```text
area      = 0x4000041c -> [0, 0, 960, 540]
refcon    = 0x0f0f6e60
pixel_fn  = 0x180006980
dst       = 0x400003f0
start/end = 0/540
work dims = 1104x1104
```

The depth descriptor is separate from the PF worlds. `param_6[0]+0x2c` holds
8bpc depth; source and destination worlds own `[left,top,right,bottom]` extent
metadata at their own `+0x2c`.

## Import Evidence

The fixture registers `powf`, `sqrtf`, `cosf`, `sinf`, `ceilf`, `ceil`, and
`omp_get_max_threads=1`. The authoritative run recorded no unimplemented
imports. Counts, including zero-call tracked imports, are in the JSON artifact.

## Result

The first populate callback completed and the callback model check passed.
The PNG is decoded as RGBA and explicitly repacked to PF_Pixel8 `A/R/G/B`
before the input world is built. The JSON pins the PNG, decoded-RGBA, and
host-ARGB hashes separately. An earlier RGBA-as-ARGB probe was invalidated and
is not used as pixel evidence.

`FUN_180001ec0` rotate-in was replaced only for this fixture by
`core/dblur_rotate.cpp`, whose six bounded actual-AEX fixtures are byte-exact.
The observed full-frame call was `1104x1104`, angle bits `0x3fc90fdb`; complete
source, destination-before, and destination-after hashes are recorded in the
JSON.

The corrected-input run then entered the real AEX rowdriver at `0x1800038d0`
and exhausted exactly `200000000` instructions at `0x18000168c`, inside the
scatter leaf `FUN_1800013e0`. No normalization, rotate-back, final PF Iterate8,
or complete ARGB8 output occurred, so no final hash is claimed.

This historical blocker is closed for the declared front-only slice. The
corrected PF Iterate8 area/world model, byte-exact rotate and rowdriver detours,
and actual AEX full-entry now complete. Feature families outside front-only
remain separate lanes; do not reuse this old instruction-budget statement as
their current next action.

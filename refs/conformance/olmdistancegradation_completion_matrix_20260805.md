# OLMDistanceGradation completion matrix

`Exact` means an actual-AEX field/owner/callback output is compared with Mac
production. Axis coverage does not imply every Cartesian parameter combination
is proven.

| Surface | PF8 | PF16 | PF32 |
|---|---|---|---|
| Classic render | Exact | Exact | Exact |
| Smart pre-render | Exact natural chain | Exact natural chain | Exact natural public chain, bounded |
| Smart render | Exact, `FUN_181170380` | Exact, `FUN_181170280` | Actual public owner: command `0x18` → `FUN_181173d20` → `FUN_181172a10` → iterateFloat/`FUN_181170c90`; fixed17x11 non-Power 24/24 raw exact, Power 8/8 fail-closed; Mode 5 non-Power 6/6 |

| Public axis | Exact witnesses |
|---|---|
| Render Mode RGB | PF8/PF16 Outside; PF32 Inside and Outside owners |
| Render Mode Layer | PF8 Inside/Outside/Both; PF32 Both owner |
| Interpolation Constant | PF8 Inside/Layer/use-bg |
| Constant + Blur | PF32 Inside/RGB/no-bg through actual `cvSmooth` and owner writer |
| Blur Mode 5 | Fixed17x11 PF32 Constant/Linear/Sphere × background off/on, direct-`expf` IPP order and noncontracting Universal codegen, 6/6 raw exact; Power pair fail-closed pending native UCRT |
| Interpolation Linear | PF8 Both/Layer/no-bg; PF16 Inside baseline; PF32 Both owner |
| Interpolation Sphere | PF8/PF16 Outside; PF32 Outside owner |
| Interpolation Power | PF8 Outside/RGB/no-bg, PF16 Both/Layer/no-bg, and PF32 Both/Layer/no-bg |
| Ownership Inside | PF8/PF16/PF32 |
| Ownership Outside | PF8/PF16/PF32 |
| Ownership Both | PF8, PF16, and PF32 |
| Invert off/on | PF8/PF16/PF32 bounded pairs |
| Row padding | Distinct rowbytes with unchanged sentinels at all depths |

PF16 also has a bounded Cartesian family for
Outside/RGB/no-background/no-blur: Constant, Linear, Sphere, and Power 2.5,
each with Invert off/on. A 9x7 transparent island retains intermediate
distance values, so all eight actual-AEX outputs are distinct and match
production including row padding. See the 2026-08-06 interpolation-family
evidence for hashes and exclusions.

PF32 Layer mode is exact for Both/Layer/Linear/no-bg and
Both/Layer/Power-2.5/no-bg through the actual classic whole-render owner:

- Geometry 17x11; input/output rowbytes 280/288.
- Internal field SHA-256:
  `8ac06eb6a3a4329f511a3496e33b13c51ec01c6fb03624f238e545c7536e30ca`.
- Active output SHA-256:
  `6a0c57df59d4ccf2a170d851fec2b236d3600a46a8521b8029101f1f952ebd25`.
- Padded output SHA-256:
  `a155960e97efca905be85c9640b5cbc30c890735811c6b63e4c5f31a922cb1ae`.
- Production comparison: 3,168/3,168 bytes, zero mismatches.

The PF32 owner exports the Both ownership scalar to RGBA rather than source
Layer color. Production implements this only for PF32 Both/Layer/no-bg. The
Power witness is byte-identical to Linear for this scalar field, while retaining
the actual Power 2.5 parameter contract. Constant-with-blur is now connected
entry-to-writer for PF32 Inside/RGB/no-bg with a byte-exact bounded witness.
The earlier PF32-Smart-unsupported conclusion inspected classic command `0x0b`
instead of the actual public Smart command and is superseded. Production admits
only the fixed 17x11 PF32 Smart matrix: Blur Modes 2/3/4 contribute 18 admitted
non-Power cells and Mode 5 contributes six Constant/Linear/Sphere × background
off/on cells. All eight Power cells and every unlisted tuple, geometry, or layout fail
closed. See `olmdistancegradation_public_smart_owner_contract_20260812.{json,md}`
and `olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.{json,md}`.
The current installed arm64 executable `231421e4…` has also been replayed
AE-free through the real-SDK Smart entry: the same six Mode 5 cells are
source/installed byte-identical with padding and lifecycle exact, while all
eight Power cells fail closed with untouched output. This does not replace the
missing native Windows UCRT `powf` capture or constitute a native-AE claim.

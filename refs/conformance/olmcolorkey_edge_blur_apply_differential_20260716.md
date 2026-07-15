# OLMColorKey Edge Blur Apply Differential 20260716

Status: implemented binary-grounded local exact at the equivalent typed apply
boundary. This is not AE-host execution and does not promote an AE-exact claim.

## Boundary

The original broad full-RGBA mismatch was an adapter-scope and callback-contract
mismatch:

- `FUN_1800113c0` addresses `rowbytes + x*4`; the original 4x2 fixture supplied
  8 matte bytes instead of 32 typed PF_Pixel8 bytes.
- `FUN_1800085b0` writes byte offset 0 only. Offsets 1/2/3 remain `0xCC`.
- The default `AexLoader` shim did not return `sin`/`sinf` results in `XMM0`.
- The actual callsite at `0x1800098a4..0x1800098cc` passes keyed matte
  `local_208`; `local_108` is used only by the distance helper.

The corrected AEX side packs matte as PF_Pixel8, keeps distance as float4,
implements only the two math callbacks, and compares all 32 destination bytes
with zero tolerance.

The production side is no longer duplicated Python math. Each differential run
builds a temporary C++ executable whose translation unit source-includes
`cli/OLMColorKey/main.cpp`, renames the CLI program entrypoint, and calls the
real `edge_blur_weight` and `edge_blur_apply_channel` functions. The latter is
also used by `render_olmcolorkey`, so both weight and scalar channel application
are compiled current production code. The temporary product is local evidence,
not a checked-in or released binary.

## Enum Evidence

The direction mapping remains independently established by setup/decomp/disasm:

1. The popup is `Direction: Inside | Around | Outside`, with one-based values
   `1`, `2`, and `3`.
2. `FUN_18000a3d0` reads property index `0x13` through `FUN_18000e050` and
   stores it at context offset `0x48`.
3. The apply callsite loads `*(uint32_t *)(context+0x48)` into `r8d` and calls
   `FUN_1800085b0` without transforming it.
4. `FUN_1800085b0` dispatches `1` to `FUN_1800049a0` (Inside), `2` to
   `FUN_180004b50` (Around), and `3` to `FUN_180004cf0` (Outside).

## Implementation

Direction 1 is preserved unchanged in all three implementations.

- Direction 2 starts at `0.5`, uses
  `sin(+/-distance*((pi/2)/amount))` below the amount, and resolves to `1`
  inside or `0` outside at and above the amount.
- Direction 3 keeps inside at `1` and uses
  `sin(pi/2-distance*(pi/amount))` outside below the amount.

Implemented locations:

| Source | Direction 1 | Direction 2 | Direction 3 |
| --- | --- | --- | --- |
| `cli/OLMColorKey/main.cpp` | `718-722` | `723-729` | `730-734` |
| `mac/OLMColorKey/OLMColorKey.cpp` | `715-719` | `720-726` | `727-731` |
| `rust/olmcolorkey_cli/src/main.rs` | `448-456` | `457-470` | `471-479` |

The CLI callable apply helper is at lines `738-746` and is used by the renderer
at lines `950-953`. The Rust grounded endpoint unit test is at lines `490-518`.

## Exact Matrix

The matrix covers mixed integer thresholds, separate inside/outside endpoint
sweeps, and alternating fractional ramps for all directions.

| AEX direction | Compiled CLI arm | Result |
| --- | --- | --- |
| 1 Inside | 1 | Exact in all 3 patterns |
| 2 Around | 2 | Exact in all 3 patterns |
| 3 Outside | 3 | Exact in all 3 patterns |

Result: 9/9 cases and 288/288 destination bytes are exact at zero tolerance.
All 72 scalar production apply requests execute through the temporary compiled
source-include seam. The independent decomp model is also exact in 9/9 cases.

## Validation

- Direct report run: exit `0`, `status=pass`, 9 cases.
- Strict `--enforce`: exit `0`, `status=pass`, 9 cases.
- Python test assertion: pass.
- C++ CLI: built to
  `/tmp/olmcolorkey_edge_blur_apply_20260716/cpp/olmcolorkey_cli`; `--help`
  exits `0`.
- C++ reference controls: RGB cases `0001-0004` exact; Edge Thin case `0007`
  exact.
- Mac plugin: arm64 Debug build succeeded under
  `/tmp/olmcolorkey_edge_blur_apply_20260716/xcode`; product is an arm64 Mach-O
  bundle. The old project emits SDK packing and legacy Rez warnings.
- Rust: `cargo test` passes 1 grounded test; `cargo check` passes, both with a
  `/tmp` target directory.

The legacy exploratory full-frame Edge Blur checks `case_0008/0009` no longer
meet their old loose thresholds (`mean=51.6708` and `40.1137`). Those checks
encode the superseded direction behavior and a broader full-RGBA path, so they
are recorded as residual evidence rather than used to override the typed AEX
apply result. No legacy fixture or threshold was edited.

`cargo fmt --check` remains non-clean across pre-existing unrelated formatting
in `rust/olmcolorkey_cli/src/main.rs`; only the newly changed branch was put in
rustfmt shape.

The machine-readable byte report is
`refs/conformance/olmcolorkey_edge_blur_apply_differential_20260716.json`.

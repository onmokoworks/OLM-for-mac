# OLMKiraKira Mode Dispatch Static Audit

Date: 2026-07-10  
Scope: static mapping only. Sources are the decomp/disasm notes, parameter
manifests, and the current Mac port. No source, PNG, hotspot-compose, or
Windows-request changes are implied by this audit.

## Evidence boundary

The Windows binary facts below are from `notes/PORTING_BOARD.md` and
`notes/OLMKiraKira_ASM_FACTS.md`. Parameter ids and runtime-block offsets are
the Ghidra reconstruction recorded at `notes/PORTING_BOARD.md:1656-1669`.
The current Mac behavior is checked against
`mac/OLMKiraKira/OLMKiraKira.cpp` and `mac/OLMKiraKira/OLMKiraKira.h`.
The Windows UI/range facts are from the fresh manifests named in
`refs/conformance/olmkirakira_endgame_control_coverage_audit_20260710.md:13-17`.

Confidence labels:

- **PROVEN**: direct static call/branch, parameter read, or current-source
  consumer is identified.
- **PARTIAL**: a relevant object/branch exists, but the requested control's
  exact semantic link or selected target is not established.
- **UNKNOWN**: no static consumer/target has been recovered.

## Parameter-to-runtime map

| Control | Registration / manifest identity | Runtime block | Static status |
| --- | --- | --- | --- |
| `Blur Mode` | AEX parameter id `9`, match suffix `-0009`; four-choice popup, default `2` | `+0x4c` | **PROVEN read; dispatch only partial** |
| `Merge mode` | id `0x11` / suffix `-0017`; two-choice popup, default `1` | `+0x44` | **PROVEN read and dispatch split** |
| `Approximated Input` | id `10` / suffix `-0010`; checkbox, default off | `+0x50` | **PROVEN read into block; consumer unknown** |
| `Fade Out` | id `0x1b` / suffix `-0027`; range `0..1`, default `0` | `+0x0c` | **PROVEN binary read; downstream consumer unknown** |
| `Highlight Radius` | id `6` / suffix `-0006`; range `0..500` in fresh Windows capture | `+0x30` | **PROVEN binary read; highlight use unknown** |
| `Highlight Color` | id `0x10` / suffix `-0016` | color/ramp metadata passed to aggregation | **PROVEN parameter exists; highlight-path use partial** |

The source-side parameter enum and disk ids are explicit at
`mac/OLMKiraKira/OLMKiraKira.h:41-96`. The Windows registration/read map is
the `FUN_18114c1a0` / `FUN_18114e860` reconstruction at
`notes/PORTING_BOARD.md:1656-1669`; it is the authoritative static mapping
for the binary, not the Mac enum ordering.

## Blur Mode 1/2/3/4

### Proven

- `FUN_18114f4a0` is the core and calls the directional helper
  `FUN_181150790`; the helper receives Blur Mode from the caller stack slot
  `[rsp+0x38]`, populated from the runtime block's `+0x4c` field. This is the
  exact caller/argument evidence recorded in
  `notes/OLMKiraKira_ASM_FACTS.md` under “FUN_181150790: Ray Helper Overview”.
- The helper's mode-sensitive region is `0x18115095e..0x18115110a`.
  The recovered Blur Mode 2 path calls `FUN_181280bc0` three times at the
  first-pass range `0x18115110a..0x18115116f`, second-pass range
  `0x181151174..0x1811511c2`, and third-pass range
  `0x1811511c7..0x181151215`.
- `FUN_181280bc0` is the OpenCV `boxFilter` wrapper. For this path the static
  arguments are `ksize=(length,1)`, `anchor=(-1,-1)`, `normalize=param_9`
  (the current Channel 2 vtable returns `1`), and `borderType=4`
  (`BORDER_REFLECT_101`). This is the direct call audit in
  `notes/OLMKiraKira_ASM_FACTS.md` under “Blur Mode 2: cv::boxFilter Calls”.
- Therefore **Blur Mode 2 is proven** as the three-pass horizontal box-filter
  path inside the rotate/blur/rotate-back helper. The current Mac source does
  not implement a mode dispatch: `RenderTyped` hard-codes `passes = 3` and
  calls `RotatedAxisBoxBlur` at `mac/OLMKiraKira/OLMKiraKira.cpp:415-427`.

- **Blur Mode 1 is proven** by the `JZ` at `0x181150958` to block
  `0x18115122e`, which calls `FUN_181280bc0` once at `0x181151290`. This is a
  single box-filter call, distinct from the three calls in Mode 2.
- **Blur Mode 3 is proven** by the `JZ` at `0x18115096a` to block
  `0x1811510a9`, which calls `FUN_181272ec0` at `0x181151100`. Existing binary
  identification grounds that target as the GaussianBlur wrapper.
- **Blur Mode 4 dispatch and body are proven**: after the compare at
  `0x181150970`, value `4` falls through to the inline body
  `0x181150979..0x181150f3a` and rejoins at `0x181150f3d`. It makes no
  subordinate filter call and uses recursive/separable accumulation factors
  derived from `length/(length+1)` and `length/(length+1)^2`. Calling this
  product mode "exponential" remains an interpretation of the UI label, not a
  binary fact.
- Other/default values branch at `0x181150973` directly to `0x181150f3d`,
  bypassing these mode-specific filter bodies.

### Remaining implementation gap

- The binary dispatch is now closed for values `1..4`; no additional runtime
  witness is required merely to identify their targets. A runtime witness is
  still useful later for exact intermediate values and border/quantization
  conformance.
- The Mac `info->blur_mode` is read at
  `mac/OLMKiraKira/OLMKiraKira.cpp:501-503` and then unused by the render
  path. Its four-choice declaration is at lines `599-603`; that is schema
  parity, not behavior parity.

### Next useful witness

For implementation validation, use one Windows Software case per value
`1..4`, otherwise identical to the existing single-ray length-50 case, and
record one post-mode float. The dispatch address itself no longer needs to be
rediscovered.

## Merge Mode 1/2

### Proven

- `FUN_18114f4a0` dispatches after ray generation through the vtable selected
  by the channel implementation. The exact branch is
  `param_15 == 1 -> vtable + 0x08` and `param_15 == 2 -> vtable + 0x10`, with
  call setup at `0x18114fc2d..0x18114fc86`.
- For the current luminance vtable, `+0x08` is `FUN_18114fd90` and `+0x10`
  is `FUN_18114ffd0` (`notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md:12-35`).
  `FUN_18114fd90` is the premultiplied RGB plus alpha-union aggregator and
  normalizes RGB by final alpha. `FUN_18114ffd0` is the additive/clamp
  aggregator and does not show the same trailing Brightness/Gain use.
- The current Mac render always performs the screen-over-style final compose
  at `mac/OLMKiraKira/OLMKiraKira.cpp:448-461`; it does not read
  `OLMKIRAKIRA_MERGE_MODE` in `ReadRenderInfo` or `CheckoutSmartInfo`.
  The popup is declared at `mac/OLMKiraKira/OLMKiraKira.cpp:617`.

### Interpretation limit

The binary proves a mode-1/2 aggregation dispatch and the two function
targets. It does **not** by itself prove that the Windows UI labels
“Premultiply Add” and “Add” are exact names for those two vtable functions,
nor does it prove the later source/glow compose formula for mode 2. The
existing grounded IR identifies the current 8bpc Software path as Merge Mode 1
and the screen-over compose, but the mode-2 output/compose contract remains
unwitnessed.

### Smallest missing runtime witness

Two otherwise identical Windows Software renders using one short nonzero ray
and opaque source, Merge Mode 1 versus 2. At the post-ray dispatch, record the
selected target (`FUN_18114fd90` or `FUN_18114ffd0`) and one output RGBA float
before final writeback. This separates dispatch from later compose behavior;
do not use the frozen hotspot as the witness.

## Approximated Input

### Proven

- The Windows binary registers parameter id `10` and copies it into the
  runtime block at `+0x50` (`notes/PORTING_BOARD.md:1658-1669`).
- The current Mac source declares and renders the checkbox, and
  `ReadRenderInfo` reads the control at `mac/OLMKiraKira/OLMKiraKira.cpp:502-504`
  only for the neighboring fields; there is no `info.approximated_input`
  member or read. The render seed is built directly by `MakeSeed` at
  `:370-399`, followed by the fixed ray helper at `:415-427`.

### Unknown

No static consumer or branch target for the binary's `+0x50` value has been
identified. It is unknown whether Approximate Input changes seed generation,
source preprocessing, the blur input, or only a later path. The manifest
checkbox/default is not semantic proof.

### Smallest missing runtime witness

One paired Windows Software render with the same source and one nonzero ray,
Approximate Input off/on. Trace the first branch or stage that reads the
`+0x50` field and capture one changed seed/blur-input float (or prove no stage
changes and record it as a Windows no-op).

## Fade Out

### Proven

- The binary registration/read map places Fade Out at parameter id `0x1b`
  and runtime offset `+0x0c` (`notes/PORTING_BOARD.md:1661-1669`).
- The current Mac UI declaration is `0..1`, default `0`, at
  `mac/OLMKiraKira/OLMKiraKira.cpp:627-630`, but `OLMKiraKiraInfo` has no
  Fade Out field (`mac/OLMKiraKira/OLMKiraKira.h:99-122`) and neither render
  reader consumes it.

### Unknown

The downstream Fade Out branch, affected buffer, and whether it is spatial
edge attenuation, ray-length attenuation, or a no-op are unknown. No static
mapping to `FUN_181150790`, `FUN_18114fd90`, or final compose is established.

### Smallest missing runtime witness

Paired Windows renders at Fade Out `0` and `1`, with one nonzero ray and a
finite image edge. Trace the first changed value after the `+0x0c` read. If
there is no changed stage or output, record the Windows no-op instead of
assigning a formula.

## Highlight path

### Proven

- `FUN_18114f4a0` builds five ray-buffer slots. The four ordinary directions
  use `FUN_181150790`; layer index `4` has a distinct special branch that
  expands a length as `length * 2 + 1` and stores its squared area. In Blur
  Mode 2 that scalar is squared twice more. This is direct static evidence
  recorded in `notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md:10-17`.
- The parameter map places Highlight Radius at `+0x30`, Highlight Color at
  parameter id `0x10`, and Highlight Use Ramp at id `0x24`; the Mac source
  reads the color and toggle at `mac/OLMKiraKira/OLMKiraKira.cpp:508-514`.
- The current Mac render aggregates only `vertical`, `horizontal`,
  `diagonal`, and `diagonal2` at `mac/OLMKiraKira/OLMKiraKira.cpp:434-438`.
  There is no highlight buffer, radius read, highlight color application, or
  highlight-ramp branch in that render path.

### Unknown / partial

The special fifth buffer is strong proof that a highlight-related path exists
in the Windows core, but static evidence does not yet connect its length input
to `Highlight Radius`, establish its trigger condition, or prove whether its
color/ramp metadata comes from `Highlight Color`. The exact branch and buffer
consumer are therefore **PARTIAL**, not a complete Highlight Radius/Color
mapping. The Mac source's read of `Highlight Color` is source-backed only; it
does not prove execution.

### Smallest missing runtime witness

One Windows Software case with all four ordinary ray lengths zero, a positive
Highlight Radius, and a non-default Highlight Color. Trace the fifth buffer
creation/use around `FUN_18114f4a0`, capture the radius-derived size and one
nonzero buffer/aggregation sample. If the isolated case is silent, use the
smallest documented trigger that activates the special branch and record that
trigger.

## Frozen boundaries

- Keep the hotspot compose lane frozen. This document does not reopen
  BT.709 seed, boxFilter arguments, ray-helper choreography,
  `FUN_18114fd90`, Merge Mode 1 compose, gain scaling, or final quantization.
- No source changes, PNG tuning, or Windows request staging are part of this
  audit. The only artifact created by this task is this markdown file.

status: done
summary: |
  Surveyed all ten original 2025 AEX files; all ten GLOBAL_SETUP/PARAMS_SETUP runs succeeded under cached Unicorn.
  Only KiraKira registers drawable ECW controls: five 310×170 ramp editors. RadialBlur advertises CUSTOM_UI but registers no drawable parameter.
  Active drawing already uses AE Drawbot, not GDI. Eight plugins have meaningful UPDATE logic; no runtime parameter renaming was found.
  The current Mac checkout already has partial KiraKira UI and six UPDATE handlers; the brief's blanket “none” premise is stale.
  Remaining priorities are KiraKira's full editor, exact dynamic visibility, and a UI-capable original-AEX oracle.

## facts: provenance and commands actually run

Scope: read-only originals, SDK headers, decomp/disasm, emulator source and Mac sources. No plugin, release-gate, ledger, MAIN, or emulator source was changed. Worktree baseline `6e140f16`; first checkpoint commit `2bc4e98b`.

`MAIN` below means `/Users/onmk/Documents/Projects/Personal/OLM as`.
`AEXCompat` means `/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat` (read-only source HEAD `0d3e74732e64dacba4d4508744951f28db538b88`; source inspection, not a claim that the cached worker was built from this revision).

Executed:

```sh
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/U01-ui-inventory.py
python3 orchestra/reports/U01-ui-setup.py orchestra/state/U01-custom-ui-survey/setup
```

- PE inventory: **10** original binaries, SHA256 and raw PiPL resource bytes retained in [U01-ui-inventory.json](U01-ui-inventory.json). All ten PiPL flag pairs agree with executed GlobalSetup results. No `gdi32.dll` or `user32.dll` imports in any of ten originals; the reachable drawing implementation below calls Drawbot directly.
- Setup: **10/10** subprocess exit codes 0; **10/10** `global_setup_error=0`, **10/10** `params_setup_error=0`; **451** registered non-input parameter definitions; zero unsupported suite calls in these setup runs. Complete names, slot numbers, types, dimensions and defaults are retained in [U01-ui-setup.json](U01-ui-setup.json).
- Worker: `/Users/onmk/.cache/olm-emu/radial_frozen_reference_bd878da/target/release/aex-guest-worker`, SHA256 `544ff209d11b11071c9665aba9927c2d5f31157e0f80bf408470925fc080b8d2`, selected from `~/.cache/olm-emu/INDEX.json`. No rebuild.
- `worker --help`: exposes `inspect`, `setup`, `render`, `session`, and `trace-selector <GLOBAL_SETUP|PARAMS_SETUP>`; no UI-event replay command.
- Static inspection used streaming function reads and `rg` over original decomp/disasm and local SDK. Reproducible reader: [U01-read-function.py](U01-read-function.py). Addresses below are original preferred **VA**, image base `0x180000000`, not runtime ASLR addresses.
- Re-ran both capture commands into `orchestra/state/U01-custom-ui-survey/recheck/`: both inventory and setup-summary `cmp` returned 0. Independent assertions confirmed 10/10 PiPL/setup flag pairs and all 451 parameter records. Static-reader checks produced 953 lines for the four cited KiraKira handlers and 16 lines for ramp-registration asm. `git diff --check` passed. Scratch is 3.1 MiB; no builds or background processes remain.
- No EVENT/UPDATE execution, drawing capture, native AE visual check, or render differential was performed. There is **no measured UI/pixel mismatch count or first mismatch** in this survey. Static Mac differences are listed explicitly as such.

## Capabilities: PiPL and executed GlobalSetup

Both columns are identical between PiPL and GlobalSetup. `C` = `PF_OutFlag_CUSTOM_UI` bit 15; `U` = `PF_OutFlag_SEND_UPDATE_PARAMS_UI` bit 26. A missing U bit does **not** mean the binary has no UPDATE handler.

| Original | out_flags | out_flags2 | C / U | GlobalSetup address | Registered non-input params |
|---|---:|---:|---|---|---:|
| ColorKeep | `0x02000040` | `0x08001400` | no / no | entry `1800025c0`, case 1 | 101 |
| DistanceGradation | `0x06000040` | `0x08001400` | no / yes | entry `181174bd0`, case 1 | 12 |
| OLMBlur | `0x06000040` | `0x08001400` | no / yes | entry `18000a970`, case 1 | 5 |
| OLMColorKey | `0x02000440` | `0x08001400` | no / no | `18000b340` | 223 |
| OLMDirectionalBlur | `0x06000040` | `0x08001408` | no / yes | entry `1800083f0`, case 1 | 21 |
| OLMKiraKira | `0x02008040` | `0x08001400` | yes / no | `1811514c0` | 40 |
| OLMRadialBlur | `0x06008040` | `0x08001408` | yes / yes | `18000b8e0` | 30 |
| OLMSmoother | `0x02000040` | `0x08000000` | no / no | entry `18000a2c0`, case 1 | 3 |
| OLMSmoother2 | `0x02000440` | `0x08001400` | no / no | `1800053d0` | 15 |
| OLMToonDilate | `0x02000044` | `0x08021400` | no / no | `1801a6fe0` | 1 |

`out_flags2`: all set `SUPPORTS_THREADED_RENDERING` (bit 27); all except Smoother v1 set `SUPPORTS_SMART_RENDER` (10) and `FLOAT_COLOR_AWARE` (12). DirectionalBlur/RadialBlur additionally set `PARAM_GROUP_START_COLLAPSED_FLAG` (3); ToonDilate additionally sets `AUTOMATIC_WIDE_TIME_INPUT` (17). No other bits, including `CUSTOM_UI_ASYNC_MANAGER`, camera/light, or GPU flags, are set in these setup snapshots. Definitions: MAIN `Headers/AE_Effect.h:915` onward.

**Actual custom registration:**

- KiraKira `18114c1a0` calls registration helper `181153550` with events `4 = PF_CustomEFlag_EFFECT`; comp/layer/preview dimensions and alignments are all zero. Five arbitrary (`PF_Param_ARBITRARY_DATA=11`) parameters: **slots 14,20,26,32,38**, persistent IDs **0x13,0x15,0x17,0x24,0x19**, all named **`Ramp`**, all **310×170**, `ui_flags=0x82` (`CONTROL | DONT_ERASE_CONTROL`), parameter flags `0x60`. Wrapper `181153210` supplies these dimensions/flags to `181153330`. Groups are Vertical, Horizontal, Diagonal, Diagonal 2, Highlight.
- ToonDilate `1801a58b0 → 1801a9010` also registers events `4` with zero dimensions, but has only a standard Search Radius slider, no CONTROL and no CUSTOM_UI flag. Registration alone is not an active drawing surface.
- Remaining eight: no custom registration recorded. RadialBlur's slots 4/6/7/10/12/13/27 have `ui_flags=0x40` (`DONT_ERASE_TOPIC`), **not** CONTROL; dimensions are zero. Every other standard parameter has zero UI flags at setup.
- Across all **451** definitions: only KiraKira's five have CONTROL/nonzero dimensions; **zero** have `PF_PUI_ECW_SEPARATOR`. SDK `AE_Effect.h:2259` also says that separator flag is not used by AE. None warrants inventing a new separator or preview in the port.

## Per-plugin survey and estimated remaining effort

Effort is **inference**, engineering days including focused hostless checks but excluding waiting for native AE. “No draw” means no reachable drawable control on the registered 2025 surface, not absence of shared UI library code in the PE.

| Plugin | Active custom UI / events | Draws / click semantics | UPDATE / labels | Mac mapping; estimated work |
|---|---|---|---|---|
| ColorKeep | No; no EVENT switch case | No draw/custom click | Hide Color slots above Number of Colors; USER_CHANGED and UPDATE share handler. No renaming. | DynamicStream hidden flag; existing Mac disables instead: audit/fix, 0.5–1 day |
| DistanceGradation | No; no EVENT case | No draw/custom click | Six conditional disabled states, detailed below. No renaming. | ParamUtils UpdateParamUI; existing handler, verify 0.5–1 day |
| OLMBlur | No; no EVENT case | No draw/custom click | Unconditionally hides Blur Smoothness. No renaming. | DynamicStream; existing handler, verify 0.25–0.5 day |
| OLMColorKey | No active custom control; dormant shared EVENT code | No reachable custom draw/click | Palette/replace/component visibility and enable states. Labels generated at setup, not renamed on Color Space change. | ParamUtils + DynamicStream; existing handler, audit 1–2 days |
| OLMDirectionalBlur | No; no EVENT case | No draw/custom click | Noise Type toggles Noise Layer versus Seed/Offset/Thickness visibility. No renaming. | DynamicStream; existing handler, verify 0.5–1 day |
| OLMKiraKira | **Yes**, ECW CONTROL: DRAW, DO_CLICK, DRAG, ADJUST_CURSOR | Gradient and coloured stops, preset menu, copy/paste/randomize/flip; edit the clicked arbitrary ramp | Use Ramp disables solid colour/enables ramp, and conversely. No parameter renaming; literal button captions below. | EffectCustomUI + Drawbot + AppSuite + ParamUtils; complete current partial editor, 4–7 days |
| OLMRadialBlur | Advertised, **dormant**; shared EVENT requires an arbitrary control absent from setup | No reachable custom draw/click | Noise visibility, Rotation/Zoom Offset and Strength enabling. No renaming. | ParamUtils + DynamicStream; existing handler, verify 0.5–1 day |
| OLMSmoother | No; no EVENT/UPDATE case | No draw/custom click | None | No feature implementation; negative regression 0.25 day |
| OLMSmoother2 | No active custom control; dormant shared EVENT code | No reachable custom draw/click | Color Key/Invert and Gamma controls enabled/hidden conditionally. No renaming. | ParamUtils + DynamicStream; add missing dispatch/logic after oracle, 1–2 days |
| OLMToonDilate | ECW registration only; dormant shared EVENT code | No drawable Search Radius control | UPDATE is empty `1801a7310` | No custom feature implementation; negative regression 0.25 day |

## Event dispatch and KiraKira drawing/interaction

**FACT, static:** The C++ active effect vtables were resolved from the exported entry constructor's disassembly, then read from the PE (recorded in inventory). EVENT is vtable byte offset `0x38`, UPDATE `0x30`, ParamsSetup `0x18`. This avoids treating shared Ramp/Curve classes as a registered feature.

| Plugin | Active effect vtable | EVENT target | UPDATE target |
|---|---|---|---|
| ColorKey | `18001fd80` | `18000b680` | `180001a50` |
| KiraKira | `18148db50` | `181151800` | `18114ca70` |
| RadialBlur | `180021e98` | `18000bc20` | `180003ca0` |
| Smoother2 | `180022d48` | `180005710` | `1800023a0` |
| ToonDilate | `180311e18` | `1801a7320` | `1801a7310` (empty) |

The shared EVENT pattern requires non-null params, `extra+0x54 == 2` (**PF_EA_CONTROL**, not a window-type field), and `params[extra.index].param_type == 11`. Only KiraKira meets this on actual registered parameters. ECW registration, not the area check alone, supplies the context boundary. No active comp/layer overlay or separate preview window is registered. No graph/curve editor or image-effect preview is instantiated by these ten parameter setups.

KiraKira `181151800`:

- DO_CLICK (`2`): set `send_drag` byte `extra+0x48=1`, translate coordinates and invoke arbitrary object's interaction method.
- DRAG (`3`): same method with `last_time` distinguished. After click/drag, call `PF_InvalidateRect`, set event flags `0x9 = HANDLED_EVENT | UPDATE_NOW`, set clicked parameter `PF_ChangeFlag_CHANGED_VALUE`.
- DRAW (`4`): translate into control-local coordinates, acquire drawing suites, invoke arbitrary draw method. Unlike the click path, this wrapper does not explicitly set event-out flags.
- ADJUST_CURSOR (`9`): update stored hover coordinates, set event flags `0x9` and parameter changed flag; it does **not** assign a different cursor enum or directly invoke the ramp interaction method. Preserve this observed peculiarity until native evidence says otherwise.
- NEW_CONTEXT, ACTIVATE, DEACTIVATE, CLOSE_CONTEXT, IDLE, KEYDOWN and MOUSE_EXITED have no event-specific implementation here. State is allocated by arbitrary-data construction/handler initialization, not NEW_CONTEXT.
- `181155700` converts events to internal operations: single click 2, non-single click 3, ongoing drag 4, final drag 5, hover 1; subtracts current-frame left/top. This is distinct from AE event enum numbering.

**Draw call chain:** handler vtable `18148d818` → draw `181232940` / interact `181232a30` → RampContainer vtable `1814d6f88` → draw `181236520` / interact `1812366b0`. Ramp child vtable `1814d6f70` has draw `181235950` and interaction `181235bb0`. Preset and Button vtables are `1814d6f50` and `1814d6f38`.

**What is drawn (FACT, static):**

- `181236260` constructs the layout. Ramp strip is local rectangle **(10,5)–(202,55)**; each stop appears below it in a **10×10** coloured rectangle at `x = trunc(10 + 192*position)`, spanning x±5, y60–70. The strip has a frame. This is a gradient editor, not a rendered KiraKira image preview.
- `1812392b0` samples the ramp at `(x-left)/width`, stepping x by **1.0** through **both endpoints**, and draws vertical lines using `181233ce0`. Each line creates a pen/path, MoveTo/LineTo and Surface StrokePath; this differs from the current Mac's PaintRect strip and endpoint sampling.
- `181235950` paints each stop with its ramp colour (`181234300` converts the pixel to Drawbot RGBA), frames it with a theme pen, and uses a black background for an empty ramp. Rectangle helper `181233a30` calls Surface `PaintRect`; `181233860` uses Path `MoveTo`/`AddRect` and Surface `StrokePath`.
- Theme colours come from `PF_AppGetColor` through `1812341a0`: roles **7 BUTTON_FRAME**, **8 BUTTON_FILL**, **2 TEXT**, **42 BLACK**; 16-bit components are multiplied by float32 `1/65535`. No fixed Windows GDI palette. Button states scale RGB using float constants approximately 0.3 and 0.7 (`1812355e0`, constants `1814d9bec`, `1814d9bf8`); alpha is not a substitute for these RGB factors.
- Buttons: `copy` at (225,35)–(295,55), `paste` at (225,60)–(295,80), `randomize` at (5,80)–(135,100), `flip` at (140,80)–(205,100). `paste` reflects whether the shared copy buffer has data (`181236520`). Captions are lowercase UTF-16 at pointers `181824970/978/988/980`.
- Preset header: **`▼  PRESETS`** (`181824960 → 1814d6940`), rectangle (220,5)–(300,25). `181235000` draws an expanded list of **seven** preview rows, with hover frames; constructor sets total preset count **64**, row height 18, spacing 5, scroll offset 0. Preset payload table begins `1814d7030`, stride `0x144`. Rows are gradient previews, not dynamically generated text names.
- Text helper `181233ed0` calls Supplier `NewDefaultFont` (slot 4), `NewBrush`, Surface `DrawString` (slot 9), releases font/brush. Button font-size field is float **11.0**. `181234230` sets Surface antialias policy to enum 0. Do not replace literal captions with invented parameter-name changes.
- Drawing acquisition `181233510`: PF AE App Suite v1; PF Effect Custom UI Suite v1 `PF_GetDrawingReference`; DRAWBOT Draw v1 `GetSupplier/GetSurface`; Supplier v1, Surface v2, Path v1. No Win32 GDI calls in this reachable chain.

**Interaction semantics (FACT, static; not yet executed):**

- In `181235bb0`, single click inside the strip inserts a stop if count < **16** at `(x-left)/(right-left)`. New colour is the sampled existing ramp; the empty-ramp branch initializes opaque black. It then sorts via `181239220`. Clicking a marker selects it via hit-test `181236130`; selection is not arbitrary nearest-stop snapping.
- Non-single click on a marker opens AE `PF_AppColorPickerDialog("Color select", …, TRUE, …)`, via AppSuite offset `0x38`. Cancel `0x205` clears selection without copying the temporary colour back. Accepted colour is copied back to that ramp.
- Ongoing drag sets selected stop position to the normalized x clamped to [0,1]. Dragging more than **20** pixels below strip bottom sets that stop's alpha to **0.5** as a deletion preview; otherwise alpha becomes **1.0**. Final release below that boundary deletes the selected stop and shifts later records; otherwise sorts and clears selection. Probe y offsets 20/21 separately.
- Buttons use `181235760`: arm on click when inside, retain state through drag, activate on final release inside. `1812366b0`: copy writes the ramp's `0x144` bytes to handler-shared copy storage and marks it available; paste copies it back when available. All five ramp params share the same RampDataHandler instance (`181153330`), so copy/paste is shared within the effect instance, not proven to be the system clipboard or cross-effect storage.
- `randomize` changes **RGB only** for each existing stop using the original global RNG state at `181824968`; preserves count, positions and alpha. It uses the integer hash pre-step and xorshift 13/17/5 shown at `1812366b0`. Record/restore that state for repeatable tests; no OS RNG substitution.
- `flip` reverses the colour quadruples between first/last stops, retaining their positions. It does **not** implement `position = 1-position`.
- Preset interactions `181235250`: click toggles the menu, drag adjusts the visible starting index with clamping, final selection chooses `row+scroll_offset`; container copies table entry `1814d7030 + index*0x144` to the clicked ramp. Button/preset interactions change that arbitrary parameter, not the solid colour or Use Ramp checkbox.

## UPDATE_PARAMS_UI rules and labels

All following are **static facts** from the cited handlers. IDs below mean persistent disk IDs unless explicitly called **slots**. Modern wrappers translate IDs to slots; never send a disk ID directly to `PF_UpdateParamUI`. `PF_PUI_DISABLED=0x20`; DynamicStream `HIDDEN=2`. Helpers that accept “visible” invert it before SetDynamicStreamFlag.

- **ColorKeep:** `180002210`, invoked by entry `1800025c0` commands 13 and 14. Reads Number of Colors (slot 1) through Stream Suite at current layer time, loops i=0…99; `180001ff0` hides slot `i+2` iff `count <= i`. All swatches are standard `Color` controls. No rename, custom picker or swatch rendering by plugin code.
- **Blur:** entry `18000a970`, command 14, calls `18000a750(..., slot=2, hidden=true, ...)`. Always hides **Blur Smoothness**; independent of Legacy/Repeat/Bias. No changed caption.
- **DirectionalBlur:** `180007eb0` checks out **slot 16 Noise Type**. If value ==3, show **slot17 Noise Layer**, hide **18 Seed / 19 Offset / 20 Thickness**; otherwise reverse. `1800081d0` sets DynamicStream HIDDEN. Slot21 is a group end despite its captured `Thickness` name; do not treat it as a second thickness value. The popup's publicly selectable count versus label-string count is a separate existing boundary; test raw value 3 but do not claim native reachability from the static comparison alone.
- **DistanceGradation:** `1811741a0 → 1811743b0`; helper `181174060` replaces UI flags with `0x20` or zero, then UpdateParamUI. Disable **Power slot10** iff Interpolation Mode slot9 !=4; disable **Outside Threshold slot4** iff In/Out slot2 ==1, and **Inside Threshold slot3** iff ==2; disable **Gradation Color slot7** iff Render Mode slot5 !=1; disable **BG Color [trailing space] slot8** iff Use Background Color slot6 ==0; disable **Blur Size slot12** iff Blur Mode slot11 ==1. These are six target controls/six condition comparisons, not a custom gradient preview. No renaming.
- **ColorKey:** UPDATE `180001a50`; disabled helper `18000bd30`, visibility helper `18000bee0`. Let `P=Per Color (ID6)`, `C=Per Component (ID7)`, `N=Number of Colors (ID0x15)`, `R=Enable Replace (ID0x20b)`. Disable global **Threshold ID2** when P or C. Show global component thresholds IDs8/9/10 only when C and not P. For each i=0…24: show **Use Color i+1** and **Color i+1** iff i<N; disable Color if Use Color is off. Show per-colour scalar threshold iff i<N and P and not C; show its three component thresholds iff i<N and P and C. Show **Use Replace Color i+1** iff i<N and R; show **Replace Color i+1** iff additionally Use Replace Color is on; disable both replacement controls if Use Color is off. Scalar thresholds are visibility-controlled, not additionally disabled by Use Color in this handler. Colour-space ID5 and global Threshold are read but no renaming branch follows. Exact component labels are **`Threshold(R,H,L,Y,Y)`**, **`Threshold(G,S,a,U,Cr)`**, **`Threshold(B,V,b,V,Cb)`**. Per-row suffixes ` 1`…` 25`, `Color n`, `Use Color n`, `Use Replace Color n`, `Replace Color n` are generated by `%s %d` in **ParamsSetup `180001000`**, not UPDATE.
- **KiraKira:** `18114ca70 → 181151eb0` uses ParamUtils UpdateParamUI, not hiding. For each pair (Use Ramp ID, solid-colour ID, Ramp ID): `(0x12,0x0d,0x13)`, `(0x14,0x0e,0x15)`, `(0x16,0x0f,0x17)`, `(0x23,0x1c,0x24)`, `(0x18,0x10,0x19)`. If checkbox is true, disable solid colour and enable Ramp; if false, enable solid colour and disable Ramp. No changes to group names or literal `Ramp` caption. U flag is absent: actual AE update scheduling must be witnessed, not inferred from existence of the method.
- **RadialBlur:** `180003ca0`. Noise Type ID0x14 ==3: show Noise Layer ID0x15; hide Seed/Offset/Thickness IDs0x16/17/18; otherwise reverse (`18000c480`). If Blur Type ID1 !=2 (Zoom), disable outer/inner Offset Mode IDs0x1c/1e and Offset IDs0x1d/1f. In Rotation (=2), enable these; disable each Strength ID4 or ID8 **only** when its corresponding Offset Mode equals3 (Override). `18000c2d0` changes disabled bits via ParamUtils. No renamed Outer/Inner/Strength labels and no center overlay.
- **Smoother2:** `1800023a0`. Disable **Color Key ID2 (slot2)** and **Invert Color Key ID15 (slot3)** iff Enable Color Key ID1 is off. Gamma Correction ID7 (slot8): disable **Gamma Value ID8 (slot9)** iff mode==1 (None); disable **Number of Gamma Colors ID9 (slot10)** iff mode!=2. Show Gamma Color IDs10…14 (slots11…15) only when mode==2 and index<count, through hidden helper `180005f70`; disable helper is `180005dc0`. Gamma choices are exactly **`None|Gamma Colors|All Colors`**; Smoother Version is **`v1|v2`**. No renaming. Again U is absent despite handler presence.
- **Smoother v1:** entry `18000a2c0` has no UPDATE or EVENT case. **ToonDilate:** UPDATE `1801a7310` returns immediately; Search Radius remains standard. No dynamic labels in either.

**Result:** no conditional parameter-name replacement was found in any reachable UPDATE handler. The requested “dynamic label strings” are therefore **none** for this binary set. KiraKira's literal custom text and ColorKey's setup-generated numbered names above are the relevant strings; names of all 451 definitions are in the setup artifact. Native host localization/default control labels remain host-owned.

## Mac feasibility and current-source boundary

**FACT:** baseline already has `PF_Cmd_UPDATE_PARAMS_UI` branches in ColorKeep, Blur, ColorKey, DirectionalBlur, DistanceGradation, RadialBlur; KiraKira has `PF_Cmd_EVENT`/ARBITRARY_CALLBACK plus `RampEvent` at `mac/OLMKiraKira/OLMKiraKira.cpp:2296`, and sets flags `0x02008040` at line1359. RadialBlur's EVENT no-op explicitly documents absent arbitrary params. These are source observations, not installed/native-host parity.

**FACT, static differences to prioritize:** KiraKira draws strips using PaintRect, white 5×10 markers and Flush; the original uses sampled stroked lines, coloured 10×10 markers and theme frames. Current RampEvent lacks original preset/copy/paste/randomize/flip surface and ADJUST_CURSOR handling. Its fallback selects a nearest stop rather than the original marker hit-test. ColorKeep's `SetColorsEnabled` uses disabled flags whereas the original hides unused swatches. KiraKira and Smoother2 lack UPDATE dispatch in this baseline. Other existing handlers require differential audit; their mere presence does not prove equality.

**INFERENCE / API mapping:**

- KiraKira can use the same cross-platform suites: `PF_EffectCustomUISuite` drawing reference; Drawbot Draw/Supplier/Surface/Path for pens, paths, rectangles, fonts and UTF-16 text. Use `PFAppSuite` theme colours, picker and invalidation. Preserve arbitrary NEW/COPY/DISPOSE/FLATTEN/UNFLATTEN/COMPARE/INTERP and saved-project payload contracts; an editable picture without persistent data is incomplete.
- All disabled states map to a copied `PF_ParamDef` + `PF_ParamUtilsSuite3::PF_UpdateParamUI`; all hidden states map to `AEGP_DynamicStreamSuite::AEGP_SetDynamicStreamFlag(...HIDDEN...)` using PF Interface/Stream suites to obtain the actual stream. This applies separately to each row above, including ColorKeep's hidden-versus-disabled distinction. No new custom drawing is needed for those controls.
- `PF_REGISTER_UI`/`PF_CustomUIInfo` with EFFECT only, parameter CONTROL and dimensions, and appropriate out flags are supported on Mac. Do not add comp/layer events, UI-only parameter types, curve editors or async-frame requests absent from the original.
- There is no discovered Windows-only drawing primitive to replace. Mac cannot literally reproduce Windows-native picker chrome/font rasterization through AE's host API; UI theme, screen scale and default font are host inputs. Compare semantic drawing calls with injected identical colours/fonts/scale, then perform a native visual check. Do not silently weaken render bit-exactness or declare cross-OS screen pixels exact based on call parity.
- SDK references are the supplied primary headers: MAIN `Headers/AE_EffectUI.h` (events, registration, areas), `AE_Effect.h` (flags/param data), `AE_EffectSuites.h` (App/ParamUtils/CustomUI), `AE_GeneralPlug.h` (DynamicStream) and `adobesdk/DrawbotSuite.h` (slot signatures). Preserve suite version versus C type-name differences (e.g. Dynamic Stream version constant 5 names C struct Suite4).

## Verification plan: what AEXCompat needs

**FACT, source and CLI inspection:** the cached **Unicorn Rust guest** and the newer **Windows native minihost** are different executors. Do not call the native minihost an emulator or assume its new support exists in the pinned guest.

- Cached guest setup runs above prove registration only. Current Rust `guest/crates/aex-guest-worker/src/classic.rs`, `resident.rs`, `x64/callbacks.rs` and `x64/tests_register_ui.rs` support recording custom registration. EVENT/UPDATE numeric constants in `aex-abi/src/generated.rs` are declarations, not a CLI dispatch implementation. The inspected guest has no Drawbot UI suite implementation or public event/update runner.
- Native minihost `minihost/src/worker_ui_event_execution.cpp:75` does dispatch selector15 with draw/click/drag/hover/lifecycle variants, initializes arbitrary values, and preserves context through a drag. However ECW `extra.index` at byte80 is hardcoded **1**, changed-value reporting also reads definition1, click-count is fixed1, and the test frame is synthetic. This cannot target the five KiraKira ramps unchanged.
- `worker_host_suite_catalog.cpp:105–107` registers Supplier slots0/1/6/12, Surface slots2/3/4, and Path slots0/1/3. Original KiraKira also needs Supplier **NewDefaultFont slot4**, Surface **DrawString slot9**, **SetAntiAliasPolicy slot13**. Missing slots are filled with unsupported callbacks. `worker_drawbot_runtime.cpp` records counters/colours and validates objects; it does not produce a complete ordered semantic drawing trace.
- `l2_main_support.inc:3264` `dispatch_conditional_ui_selectors` deliberately **does not dispatch UPDATE_PARAMS_UI** during headless rendering (issue1156). Do not re-enable it globally for rendering. `worker_pf_param_suites.cpp:116` restricts UpdateParamUI to an active UPDATE/USER_CHANGED scope.

**INFERENCE / bounded harness ticket:** add an explicit UI-session mode to the Unicorn guest (or a ticket-scoped AexLoader driver using its plugin-agnostic Win64 call ABI). Keep render mode unchanged. Required pieces:

1. Run original GlobalSetup/ParamsSetup and arbitrary initialization; construct real default values via original callbacks, preserving each effect/handler's handle ownership. Accept exact slot, CONTROL area, current frame, x/y, click count, drag sequence/final flag and context. Keep state across events, including shared copy buffer and RNG seed. Include negative context/ordinary-param tests; do not hand-fill guessed ramp payloads.
2. Dispatch command14 explicitly even when U is absent for **handler logic** tests; separately test native AE's actual scheduling. Capture ParamUtils changes, DynamicStream hidden flags and any label writes with ID→slot mapping. Implement PF Interface/Layer/Effect/Stream handle lifetimes and current time used by the older plugins. Fail closed on unsupported suite calls.
3. Marshal the Win64 208-byte EventExtra according to the ABI probe, including PF_Point ordering (y at20, x at24 in click union), 5th/6th stack arguments and coordinate frames. Don't reuse platform-native Mac struct memory as guest ABI bytes.
4. Provide recording Drawbot/CustomUI/App suites with object IDs and retain/release, theme GetColor, fonts, text, antialias policy, picker accept/cancel, invalidation. Record **ordered** calls, exact float bits, strings, rect/path coordinates and resources. Never rasterize through an approximate substitute as an exact oracle.
5. Serialize canonical arbitrary payload values and all param/UI mutations before/after each event; strip only pointer identity/allocator metadata, not numeric fields. Compare the equivalent Mac adapter under the same injected inputs byte-exactly. A draw-call mismatch is data even if a screenshot looks similar.

**Test matrix, to execute in implementation tickets:**

- Setup negative controls: all ten flags match PiPL; only five KiraKira CONTROL params; no separator/comp/layer overlay. This survey supplies the baseline.
- KiraKira: five slots; zero/one/16 stops; strip endpoints and outside; marker hit boundary ±5; single versus non-single click; accepted/cancelled picker; clamped x; release y offsets20/21; repeated/sorted/coincident positions; menu open/close/scroll/first/last preset; button press-drag-out/release-in; copy in one ramp/paste into another and separate effect instances; RNG seeds and two consecutive randomizations; flip with asymmetric positions/alphas; save/load and undo/redo. Compare disabled-ramp interaction only as host delivers it, not by inventing a new guard.
- UPDATE: ColorKeep count1/2/99/100; ColorKey P×C×R plus per-row toggles and N0/1/24/25; Smoother2 key on/off × all Gamma modes × counts0/1/5; Directional/Radial Noise values1/2/3, Radial Blur Type1/2 × each Offset Mode1/2/3; Distance all predicate branches above; Blur unconditional hide; Smoother/Toon no-op cases. Verify hidden versus disabled separately and label bytes unchanged.
- Drawing trace: original and Mac run identical frame origin, scale, theme colours, parameter values and hover/pressed/menu state. Verify line endpoints, fill colours, marker sizes, default-font size, text and release balance, not just counters. Stable object IDs permit comparison without pointer addresses.
- Final **real Windows AE + Mac AE** check: same AE major version/project/UI language/theme, collapsed/expanded ECW, HiDPI scale, each menu/button/drag/picker state, keyboard focus, undo/redo, save/reopen. Record loaded binary hashes and screenshots/video. Verify actual UPDATE scheduling for U-absent plugins and disabled custom controls. Keep native acceptance separate from hostless logic/draw-call exactness.

## inference

The urgent visible gap is chiefly **completion and verification of KiraKira's existing ramp UI**, not ten new preview implementations. The other meaningful gaps are dynamic-control parity and scheduling. Setup execution and static reachability establish what to implement; they do not establish native look, event-result exactness, or whole-plugin compatibility. No two-refuted-hypotheses loop occurred; the capability scope was narrowed by new binary setup boundaries.

## changed_files

- `orchestra/reports/U01-custom-ui-survey.md` — this survey.
- `orchestra/reports/U01-ui-inventory.py`, `U01-ui-inventory.json` — read-only PE hashes/PiPL/import/active-vtable extraction and result.
- `orchestra/reports/U01-ui-setup.py`, `U01-ui-setup.json` — sequential cached-worker setup capture and original parameter metadata.
- `orchestra/reports/U01-read-function.py` — bounded streaming static-evidence reader.

## verify

From the ticket worktree (scratch stays here; no `/tmp`):

```sh
mkdir -p orchestra/state/U01-custom-ui-survey/recheck
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' orchestra/reports/U01-ui-inventory.py > orchestra/state/U01-custom-ui-survey/recheck/inventory.json
cmp orchestra/reports/U01-ui-inventory.json orchestra/state/U01-custom-ui-survey/recheck/inventory.json
python3 orchestra/reports/U01-ui-setup.py orchestra/state/U01-custom-ui-survey/recheck/setup > orchestra/state/U01-custom-ui-survey/recheck/setup.log 2>&1
cmp orchestra/reports/U01-ui-setup.json orchestra/state/U01-custom-ui-survey/recheck/setup/summary.json
python3 orchestra/reports/U01-read-function.py OLMKiraKira 181151800 18114ca70 181235bb0 1812366b0 > orchestra/state/U01-custom-ui-survey/recheck/kira.txt
python3 orchestra/reports/U01-read-function.py OLMKiraKira 181153210 --asm > orchestra/state/U01-custom-ui-survey/recheck/ramp-registration.asm
```

Expected: both `cmp` exit0; setup log has ten exit-zero rows with counts **101,12,5,223,21,40,30,3,15,1** in filename order. Static files contain the cited functions; registration asm supplies `0x136×0xaa` and ORs `0x82` into UI flags. No plugin build or render regression is needed for this documentation-only diff.

## next: implementation tickets ordered by user value

1. **U02 — Complete KiraKira ECW ramp editor (4–7 days).** Extend current Mac implementation with exact original strip/markers/theme/text, preset menu, copy/paste/randomize/flip, hit testing, drag preview/deletion and hover flags. Preserve payload/render contracts. Acceptance: original-AEX event state and ordered drawing parity plus native visual/undo/save checks. Depends on U03 oracle evidence; no screenshot-tuned approximations.
2. **U03 — Explicit original-AEX UI oracle (2–4 days; prerequisite work for U02).** Unicorn UI-session dispatch and recording suites described above; never rebuild the frozen render worker in place. If a new worker is authorized, install it in a distinct `~/.cache/olm-emu/<name>/` entry and register its hash. Deliver reusable event/update traces before implementation claims exactness.
3. **U04 — Dynamic controls across ColorKeep/ColorKey/Smoother2/KiraKira (2–4 days).** Restore hide-versus-disable and missing UPDATE dispatch after original scheduling witnesses; include all exact labels/slots, state transitions and saved-project reload. Reuse existing handlers; don't change pixel kernels.
4. **U05 — Audit existing Blur/DirectionalBlur/DistanceGradation/RadialBlur UPDATE paths (1–2 days).** Execute the predicate matrix against original and Mac; retain no-op/dormant EVENT semantics. Include negative Smoother/Toon capability tests. No new preview surfaces.
5. **U06 — Native AE UI acceptance (1–2 days, host access dependent).** Aggregated Windows/Mac check after U02/U04/U05; record theme/scale/font/picker differences and actual update scheduling separately from deterministic UI logic. Update user-facing limitations only from accepted evidence, under a separately authorized ticket.

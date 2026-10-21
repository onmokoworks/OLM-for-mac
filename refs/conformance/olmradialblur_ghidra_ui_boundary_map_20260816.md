# OLMRadialBlur legacy UI / arbitrary-data boundary map

## Decision

For the pinned OLMRadialBlur.aex, the Ramp / Curve / String / Widget framework is linked and its three data-handler objects are constructed, but no Ramp, Curve, or String arbitrary parameter is registered by RadialBlur_ParamsSetup. Therefore:

- none of the legacy widget drawing, interaction, arbitrary serialization, interpolation, or UTF conversion functions is required for numerical pixel parity;
- none of those legacy functions is required for the currently exposed parameter surface;
- public command parity still requires:
  1. the exact standard parameter definitions and num_params;
  2. PF_Cmd_UPDATE_PARAMS_UI enable/disable behavior;
  3. successful no-op behavior for PF_Cmd_USER_CHANGED_PARAM;
  4. PF_Cmd_EVENT to remain a no-op for all registered parameters.

The current Mac implementation has exactly this boundary. No recommendation in this map authorizes adding a legacy arbitrary parameter or exposing its UI.

## Reachability map

    EffectBase_Construct
      ├─ constructs RampDataHandler object  ─┐
      ├─ constructs CurveDataHandler object ├─ linked/passive only
      └─ constructs StringDataHandler object┘

    RadialBlur_ParamsSetup
      ├─ popup / point / topic / slider / checkbox / angle / layer only
      ├─ no EffectBase_AddRampArbitraryParam
      ├─ no EffectBase_AddCurveArbitraryParam
      ├─ no EffectBase_AddStringArbitraryParam
      └─ no EffectBase_RegisterCustomUI
              ↓
    No PF_Param_ARBITRARY_DATA (type 0x0b) is registered
              ↓
    EffectBase_HandleCustomParamEvent exits before Drawbot/widget dispatch
              ↓
    Ramp / Curve / String widgets and their data callbacks are not publicly reachable

## Primary Ghidra evidence

### MyEffect and command boundary

- MyEffect vtable begins at 0x180021e98:
  - +0x18 / 0x180021eb0 → RadialBlur_ParamsSetup (0x1800034c0)
  - +0x30 / 0x180021ec8 → RadialBlur_UpdateParamsUI (0x180003ca0)
  - +0x38 / 0x180021ed0 → inherited EffectBase_HandleCustomParamEvent (0x18000bc20)
- entry_point (0x180010540) routes the AE command cases through these virtual slots.
- EffectBase_HandleCustomParamEvent rejects the event unless:
  - event payload kind at extra+0x54 is 2; and
  - the selected parameter's type at param_def+0x0c is 0x0b (PF_Param_ARBITRARY_DATA).
- RadialBlur_ParamsSetup contains no arbitrary-data helper call. Its direct setup calls are only popup, point, topic/end-topic, slider, float-slider, checkbox, angle, and layer helpers, ending with out_data->num_params = 0x1f.
- EffectBase_AddRampArbitraryParam (0x18000d630), EffectBase_AddCurveArbitraryParam (0x18000d6f0), EffectBase_AddStringArbitraryParam (0x18000d690), and EffectBase_RegisterCustomUI (0x18000d970) have only data/vtable references (the three Add helpers call the generic helper internally); none is called from plugin command code.

This proves the early exit is structural, not merely an untested assumption.

### Mac source evidence

- mac/OLMRadialBlur/OLMRadialBlur.cpp:612–783 defines the same standard surface and sets OLMRADIALBLUR_NUM_PARAMS; it contains no arbitrary parameter or custom-UI registration.
- mac/OLMRadialBlur/OLMRadialBlur.cpp:787–~830 implements the public UpdateParamsUI dependencies (noise-layer controls and rotation/offset controls).
- mac/OLMRadialBlur/OLMRadialBlur.cpp:5623–5628 treats PF_Cmd_USER_CHANGED_PARAM and PF_Cmd_EVENT as no-ops, explicitly because none of the 30 non-input definitions uses the legacy custom type.

## Class/vtable inventory and boundary classification

### Arbitrary-data handler classes

EffectBase_Construct (0x18000b7c0) constructs one instance of each derived handler at object offsets 0x198, 0x1a8, and 0x1b8. Construction alone does not register them with AE.

| Class / vtable | Slots and functions | Meaning | Boundary |
|---|---|---|---|
| ArbitraryDataHandler base | common disposal 0x18001a3e0, 0x18001a490; common no-op slots 0x18001a540/550/560; dispatch bridges 0x18001a570, 0x18001a660; default allocation 0x18001a740 | Owns PF handles and routes AE arbitrary callbacks to virtual operations. | Linked framework support; not needed for current public behavior or numerical parity. |
| RampDataHandler, vtable 0x180021980–0x1800219f0 | default 0x18001a740; New 0x18001a8c0; Copy 0x18001a9b0; Flatten 0x18001ab40; Unflatten 0x18001af40; FlatSize 0x18001b130; Compare 0x18001b140; Interpolate 0x18001b330; common tail slots 0x18001a540/550/560/570/660 | Serializes/interpolates ramp stop data and constructs a RampContainer. | Not needed. Would become required only if a Ramp arbitrary parameter were publicly registered or old projects actually contained one under the same effect identity. Neither is true in current ParamsSetup. |
| CurveDataHandler, vtable 0x180021a00–0x180021a70 | default/state 0x18001b820; New 0x18001b9a0; Copy 0x18001ba90; Flatten 0x18001bc20; Unflatten 0x18001bdd0; FlatSize 0x18001bf90; Compare 0x18001bfa0; Interpolate 0x18001c0f0; common tail slots | Serializes a fixed curve/control-point state and linearly interpolates its float fields. | Not needed for current surface and pixels. |
| StringDataHandler, vtable 0x180021a80–0x180021af0 | state/default 0x18001c3c0; New 0x18001c540; Copy 0x18001c630; Flatten 0x18001c790; Unflatten 0x18001c8d0; FlatSize 0x18001ca10 (67 bytes); Compare 0x18001ca20; Interpolate/select endpoint 0x18001cc80; common tail slots | Stores a bounded 32-code-unit Windows UTF-16 string in a PF handle and provides AE arbitrary callbacks. | Not needed for current surface and pixels. |

Notes:

- CurveDataHandler_ArbInterpolate is still auto-named FUN_18001c0f0 in Ghidra, but its vtable slot and behavior are unambiguous: it allocates the destination and lerps the fixed float region.
- String interpolation at 0x18001cc80 is discrete: it selects the first or second endpoint around the midpoint and copies the bounded UTF-16 string.
- These callbacks could matter to project serialization/keyframing only after parameter registration. No such registration exists here.

### Widget hierarchy and Drawbot dispatch

RTTI lists Widget, Dropdown, Button, RampPreset, Ramp, RampContainer, CurvePreset, Curve, CurveContainer, Label, StringField, and StringContainer. Their method tables form this bounded UI layer:

| Class / vtable region | Draw / event / helper functions | Boundary |
|---|---|---|
| Widget base | abstract/shared destructor entries near 0x1800224f8–0x180022508; Draw/Event contract inherited by concrete widgets | Framework only; not reached by registered RadialBlur params. |
| Dropdown, 0x180022518–0x180022528 | Draw 0x180011060; HandleEvent 0x1800112b0; pure virtual item draw; geometry/hit helpers 0x180011450, 0x1800114c0, 0x180011590 | Not needed. |
| Button, 0x180022538–0x180022540 | Draw 0x180011640; HandleEvent 0x1800117c0 | Not needed. |
| RampPreset, 0x180022550–0x180022560 | inherited Dropdown Draw/Event; DrawItem 0x1800118b0 | Not needed. |
| Ramp, 0x180022570–0x180022578 | Draw 0x1800119b0; HandleEvent 0x180011c10; hit test 0x180012190; stop sort 0x180015280; gradient draw 0x180015310; curve-overlay helper 0x1800154c0 | Not needed. It edits/paints legacy ramp state; it does not feed any current render parameter. |
| RampContainer, 0x180022588–0x180022590 | Construct 0x1800122c0; Draw 0x180012580; HandleEvent 0x180012710 | Not needed. Constructed only by unreachable RampDataHandler_ArbNew. |
| CurvePreset, 0x1800225a0–0x1800225b0 | inherited Dropdown Draw/Event; DrawItem 0x180012e30 | Not needed. |
| Curve, 0x1800225c0–0x1800225c8 | Draw 0x180013000; HandleEvent 0x180013370 | Not needed. |
| CurveContainer, 0x1800225d8–0x1800225e0 | Construct 0x180013770; Draw 0x180013a10; HandleEvent 0x180013bb0 | Not needed. Constructed only by unreachable CurveDataHandler_ArbNew. |
| Label, 0x1800225f0–0x1800225f8 | Construct 0x180014240; Draw 0x180014290; HandleEvent/no-op 0x180014440 | Not independently needed; embedded by StringField. |
| StringField, 0x180022608–0x180022610 | Construct 0x180014450; Draw 0x180014500; HandleEvent 0x180014570 | Not needed. Handler opens an ExtendScript dialog to edit a legacy string value. |
| StringContainer, 0x180022620–0x180022628 | Construct 0x180014c50; Draw wrapper 0x180014d20; HandleEvent wrapper 0x180014e10 | Not needed. Constructed only by unreachable StringDataHandler New. |

The concrete vtable pointers above come from Ghidra data xrefs, not name inference. For example, 0x180022570 points to ae_ui_Ramp_Draw, 0x180022578 to ae_ui_Ramp_HandleEvent, and the corresponding RTTI Complete Object Locator precedes the table at 0x180022568.

### String conversion and light-name dialog subtree

ae_ui_StringField_HandleEvent (0x180014570) acquires AEGP Memory/Utility suites, converts the existing Windows UTF-16 value to UTF-8, builds and evaluates an ExtendScript dialog, converts the result back, and bounds the result to 32 UTF-16 code units.

Its private support subtree is:

- wstring_convert_utf8_utf16_construct 0x180015d10
- wstring_convert_utf8_utf16_to_bytes 0x180016e80
- wstring_convert_utf8_utf16_from_bytes 0x180016890
- codecvt virtuals 0x180015610, 0x180016400, 0x180016410, 0x180016420, 0x1800166a0, 0x1800166b0, 0x180016880
- conversion exception and destructor helpers 0x180015e50–0x180016180
- MSVC string/wstring helpers in 0x180015890–0x180016280

This entire subtree is not required unless StringField becomes reachable. It has no numerical/render dependency.

## What must be ported or retained

| Behavior | Required? | Reason / acceptance condition |
|---|---:|---|
| Standard ParamsSetup identity, order, disk IDs, defaults, bounds, flags, topics, and count | Yes | Public project/UI contract and render parameter binding. Mac implementation already contains it. |
| UpdateParamsUI noise-type and rotation/offset enable/disable rules | Yes | Observable public command behavior. Must match AEX state transitions. |
| PF_Cmd_USER_CHANGED_PARAM no-op | Yes | The AEX has no plugin-specific reachable handler for current standard controls; returning success/no mutation is the contract. |
| PF_Cmd_EVENT success/no-op for current params | Yes | AEX's inherited handler exits when the selected param is not arbitrary type 0x0b. Mac's explicit no-op is equivalent. |
| Ramp/Curve/String arbitrary-data serialization and interpolation | No | No corresponding parameter is registered. |
| Drawbot Widget/Dropdown/Button/Ramp/Curve/StringField rendering and mouse handling | No | No custom UI registration and no arbitrary parameter dispatch reaches them. |
| ExtendScript light-name dialog and UTF-8/UTF-16 bridge | No | Private StringField subtree; StringField is unreachable. |
| Generic handler construction/destruction internals | No as source parity | Compiler/framework implementation detail. Mac need only avoid exposing or depending on those objects. |

## Re-evaluation triggers

This boundary must be reopened only if one of the following happens:

1. a future ParamsSetup adds PF_Param_ARBITRARY_DATA;
2. an old-project compatibility witness shows the pinned effect identity loading a hidden Ramp/Curve/String disk ID absent from current ParamsSetup;
3. custom UI is registered through PF_REGISTER_UI/equivalent;
4. a runtime trace shows EffectBase_HandleCustomParamEvent passing its param type == 0x0b gate for this pinned AEX.

Without one of those concrete triggers, porting this legacy hierarchy would expand scope without improving numerical parity or current public command parity.

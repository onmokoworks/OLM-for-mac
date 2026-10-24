Refusal interpretation (FACT and INFERENCE kept separate):

- **DirectionalBlur / `SmartRender:smart-generic-world-or-budget@2707`**.
  FACT: the cropped-expand probe has full layer 1920×1080 but checked-out
  input 960×540. For this plugin PreRender returns 960×540 too: the situation
  name does **not** mean output actually expanded. The Mac guard at
  `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:2707` compares the worlds
  against sampled full-layer dimensions through
  `DirectionalGenericWorldIsFullFrame` at line 2378. Default zero blur passes;
  nondefault blur triggers the guard. P02j's retained original excerpts
  (`P02j-evidence/original-geometry-excerpts.txt`, worker `0x180004a20`)
  establish that working planes derive from input-world dimensions and
  PreRender forwards the request; output extent controls Iterate.
  T15b's 295/300 exact Smart rows include downsample and ROI but do not prove
  this exact cropped-checkout case.
  INFERENCE: this is a remaining Mac-only full-layer admission restriction,
  likely to make such a valid cropped checkout black in AE. Original acceptance
  at these exact sizes/parameters is unmeasured; get a small original witness
  and native checkout trace before changing the guard. Unlike Smoother2 below,
  these input/output worlds are equal-sized.

- **DistanceGradation / `RenderBits:pf32-smart-profile@2201`**.
  FACT: all default PF32 probes fail the explicit union of retained admission
  profiles at `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2180–2201`.
  T15b default original calibration completed PF32 at 1080×1080 in 0.9041 s
  (`T15b-odd-even-random-comp-sweep.md`, calibration table and
  `T15b-evidence/olmdistancegradation-calibration.json`). Its original full-HD
  PF32 limitation is the oracle arena, not a measured AEX profile rejection.
  INFERENCE: the Mac-only default PF32 admission gap remains, and would return
  an error/black frame when AE supplies that supported float path. A smaller
  successful original default plus the Mac profile guard supports the group;
  it does not establish original 4K acceptance or pixel equality.

- **Smoother2 / `ValidatePublicWorlds:validate-world-shape@5240`**.
  FACT: cropped-expand supplies 960×540 input and allocates 1920×1080 output
  from Mac PreRender. The check is in
  `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp:5240`. P02f retained disassembly
  (`P02f-evidence/static.json`) identifies original worker `0x180003eb0`,
  dimension comparisons `0x180003f16..0x180003f4e`, and the mismatch branch
  `0x180004244` constructing invalid_argument from `0x180022410`.
  F52c's 7×5-to-2×2 probe reached that original check; T15b also retained
  exception-transport failures. These do not establish a native AE PF code.
  INFERENCE: original plausibly fails the same unequal-world contract too;
  do not remove the guard. Whether Mac PreRender unnecessarily creates this
  unequal layout in native AE remains a negotiation question.

- **Smoother v1 / `world-depth-32-unsupported`** (if observed).
  FACT: Smoother does not advertise FLOAT_COLOR_AWARE. T15b original calibration
  rejects PF32 even at 1×1, and its sweep has 112 unsupported-PF32 rows.
  INFERENCE: a deliberate direct PF32 host call is unsupported on both sides;
  this is not evidence that an AE 32bpc composition renders black, because AE
  can convert to the plugin's supported depth.

These are host-return observations and bounded prior evidence, not a new
original-AEX run or native-AE numerical validation. No pixel mismatch count or
first differing byte exists for this oracle-free audit.

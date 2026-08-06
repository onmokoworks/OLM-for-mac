# OLMDistanceGradation GLOBAL/PARAMS_SETUP parity

Status: `exact` for the bounded hostless registration stream.

The public Windows AEX entry point `0x181174bd0` was executed for
`PF_Cmd_GLOBAL_SETUP` and `PF_Cmd_PARAMS_SETUP`. The AEX emitted 12 raw
176-byte `PF_ParamDef` records through the real add-param callback. The test
normalizes the old Windows layout and compares it with the source-included Mac
production entry point.

All compared fields now match: parameter order, disk IDs, names (including
trailing spaces), types, flags, UI dimensions, current/default values, valid
and slider ranges, popup counts/defaults/choice strings, colors, and complete
float-slider metadata. `num_params` is 13 including the input layer.

Production differences corrected from the raw AEX records:

- `In/Out` default: 3 -> 0.
- Inside/Outside Threshold visual slider maximum: 1000 -> 512; valid maximum
  remains 1000.
- `BG Color` -> `BG Color ` (one trailing ASCII space).
- Power flags: 0 -> `0x20` (`PF_ParamFlag_START_COLLAPSED`).
- Blur Mode declared choices: 3 -> 5; the AEX choice string remains the three
  visible entries `No Blur|Blur No Scale|Blur`.
- Blur Size flags: 0 -> `0x20`; visual slider maximum: 4096 -> 500; valid
  maximum remains 4096.

The raw record hashes and every normalized row are retained in the JSON
report. The AEX SHA-256 is
`a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.

Verification:

- focused actual-AEX/production test: PASS, 12/12 rows exact;
- existing PF8/PF16 Smart natural chain and 16 classic regressions: PASS;
- Debug Universal build: PASS, `x86_64 arm64`;
- installed signed executable SHA-256:
  `0f492ec20d7f90c9c7e59e8569d8b8598e881bdd9bc18d5398a5eb68d712c8c6`;
- strict deep code-sign verification after installation: PASS;
- previous installed executable backed up with SHA-256
  `656537d052f67a9e7eb4d4ba2c6f5c890fe34e3d2c47069bcfba01854d96055e`.

Installed bundle:

`~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin`

Recoverable backup:

`handoff/mac_plugin_backups/20260806T171300_ui_parity/OLMDistanceGradation.plugin`

After Effects 26.3 was already running from 16:57:09 JST. It had no
OLMDistanceGradation mapping at the post-install check, but changing the
current project solely to force a lazy load was not considered safe. The
installed binary therefore requires a subsequent ordinary effect use or AE
restart for host-load attestation.

Excluded: native control geometry/appearance, rendering parameter consumption,
localized non-ASCII resources, and AE project migration behavior for the
changed defaults/ranges.

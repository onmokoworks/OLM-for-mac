# Mac AE 32bpc Float Candidate Path Design

Date: 2026-07-10

Status: `host-path-selected; output-module-template-probe-blocked-by-cold-r-crash`

## Decision

Use the AE Render Queue and an OpenEXR Output Module for Mac host-final 32bpc
candidates. Keep the existing PNG runners unchanged for 8/16bpc. A plug-in
internal raw-float dump remains a diagnostic witness only because it does not
include AE's final color, alpha, compositing, and output-module path.

Do not claim 32bpc `AE exact` until both Windows and Mac artifacts pass
`scripts/verify_32bpc_float_return.py` and the semantic RGBA float comparison
is bit-exact under the declared NaN/Inf and alpha rules.

## FACT

- `scripts/ae_pixel_validation_render.jsx` and
  `scripts/ae_render_single_case.jsx` currently call only
  `CompItem.saveFrameToPng`; they cannot preserve 32bpc float samples.
- `scripts/verify_ae_pixel_validation_result.py` searches and copies PNG
  candidates only. It cannot accept an EXR Mac candidate today.
- `scripts/verify_32bpc_float_return.py` now fail-closes PNG-only returns,
  validates SHA-256, 32bpc/SOFTWARE/case/parameter metadata, parses the real EXR
  scanline offset table, rejects HALF channels, verifies exactly the RGBA
  channel set and declared physical order, and records finite/NaN/+Inf/-Inf
  counts. Compressed EXR remains fail-closed until a real EXR decoder is
  available.
- `scripts/ae_probe_output_module_templates.jsx` was created to enumerate
  `OutputModule.templates` and settability settings without rendering.
- Direct cold launches with both `-r` and `-noui -r` crashed AE 2026 before the
  probe JSON was written. The same crash reproduced after temporarily removing
  every OLM/ColorKeep plug-in; those plug-ins were restored afterward.
- A normal GUI launch with no `-r` remained alive for at least 20 seconds with
  the OLM plug-ins installed. Therefore the observed crash is specific to the
  cold command-line script path, not proof of an OLM host crash.
- The current machine has no OpenEXR Python module, `oiiotool`, `exrheader`, or
  ImageMagick EXR delegate. The verifier intentionally rejects compressed EXR
  until one independent decoder is installed or bundled.
- A live-GUI probe completed on AE `26.3x87` and enumerated 18 registered
  Output Module templates. None is an OpenEXR template. The built-in
  `_HIDDEN X-Factor 32` templates resolve to PSD, not EXR.
- The installed `OpenEXR.plugin` contains `32-bit float` and `floatNotHalf`
  implementation strings, so OpenEXR export is installed but not registered as
  an Output Module template in this user profile.
- `OutputModule.setSettings({"Format": "OpenEXR"})` is rejected as
  read-only by AE. A user-created Output Module template is therefore required
  before the Render Queue runner can select OpenEXR without UI scripting.
- The user-created `OLM EXR 32 Float` template was rendered through AE's live
  Render Queue on 2026-07-10. The resulting 4x4 EXR has `A/B/G/R` channels,
  each with OpenEXR sample type `2` (FLOAT), compression `0` (none), and 64
  finite float samples. This establishes the Mac host output-module path; it
  is only a template probe, not plugin conformance evidence.
- `OLMColorKey` case_0001 then rendered successfully through the same path
  from the materialized 32bpc bridge: 1920x1080, `A/B/G/R` FLOAT channels,
  no compression, and `8,294,400` finite float samples. Artifact SHA-256:
  `1f9b4cc40d8a7223a1507b9c56cec36712fb900f8b866e6ce4fbcf80d0a34c84`.
  This proves the Mac host-final candidate path, not Windows/Mac equivalence.
- All nine declared `OLMColorKey` and all three declared `OLMToonDilate`
  32bpc probe cases have since been rendered through that path locally. Every
  artifact has four FLOAT channels and no compression. The candidate files are
  deliberately transient under `/tmp`: they are reproducible candidates, not
  versioned reference evidence, until the matching Windows EXR return arrives.
- `scripts/run_ae_32bpc_candidate_batch.py` now writes a fail-closed candidate
  index with case ID, canonical parameter hash, artifact hash, and declared
  32bpc depth. `scripts/verify_32bpc_float_return.py --mac-candidate-index`
  accepts only uncompressed scanline FLOAT RGBA EXRs with matching hashes and
  an explicit `ae_exact_claim: false`. Non-Mac and dry-run execution emits
  `MAC_32BPC_READINESS.json` rather than pretending AE ran.
- `scripts/materialize_32bpc_mac_request.py` now creates a one-case bridge
  directory from a 32bpc reference spec: it preserves the original spec,
  materializes the runner-style request/reference manifests and input PNG, and
  writes an EXR result template. Its smoke covers ColorKey case_0001.

## INFERENCE

- The smallest faithful export path is:
  add the target comp to `app.project.renderQueue`, set
  `RenderQueueItem.timeSpanStart` and `timeSpanDuration` to one frame, apply a
  verified OpenEXR Output Module template, set `OutputModule.file`, call the
  synchronous `render()`, then verify both `RenderQueueItem.status` and the
  fresh output file.
- Project `bitsPerChannel=32` is necessary but not sufficient. The selected
  Output Module must be independently proven to emit 32-bit FLOAT RGBA rather
  than HALF.
- Template names are localized and user-dependent. The implementation must
  select from the live `OutputModule.templates` list and fail closed if no
  candidate produces a verified FLOAT EXR. A name containing `EXR` is only a
  candidate, not proof.
- AE standard EXR output is not assumed to write custom `color_space` or
  `alpha_mode` header attributes. These values must come from the actual
  project/output-module settings and the applied effect manifest, be recorded
  in the sidecar return manifest, and be checked against the EXR header where
  the header exposes them. Do not invent `CompItem.alphaMode` or
  `CompItem.colorProfile`; those are not established API facts.

## Minimal Implementation

1. Run `scripts/ae_probe_output_module_templates.jsx` from an already-stable AE
   GUI session, not through a cold `After Effects -r` launch. Record the exact
   template names and `getSettings(GetSettingsFormat.STRING_SETTABLE)` output.
   The reusable launcher is `scripts/run_ae_output_module_probe.py`.
   The current profile needs a manually saved OpenEXR/32-bit-float template;
   use the stable name `OLM EXR 32 Float`.
2. Add a separate 32bpc JSX runner that reuses the existing request parsing,
   layer/effect setup, and parameter application, but renders one frame through
   Render Queue/OpenEXR. Do not replace the PNG path.
3. Write a Mac candidate manifest containing the exact request/case IDs,
   project bits, renderer, AE version, project working-space settings, selected
   Output Module template/settings, effect parameters, alpha convention,
   physical EXR channel order, dimensions, and SHA-256.
4. Extend `scripts/verify_ae_pixel_validation_result.py` to dispatch 32bpc
   candidates to `scripts/verify_32bpc_float_return.py` rather than copying a
   PNG into the integer comparator.
5. Compare semantic RGBA float32 planes. Finite values require bit identity;
   infinities require equal sign; NaNs require the explicitly documented
   canonicalization rule. Epsilon results are diagnostic, not `AE exact`.

## Acceptance Tests

- Template probe succeeds in a stable AE GUI session and records at least one
  candidate without changing project content after cleanup.
- A 2x2 32bpc synthetic comp with finite, NaN, +Inf, and -Inf values produces a
  FLOAT RGBA EXR whose header and counts pass the verifier.
- A HALF EXR, PNG-only output, missing metadata/hash, wrong renderer, mismatched
  channel declaration, or compressed EXR without a decoder fails closed.
- One normalized ColorKey and one ToonDilate case render from Mac AE and pass
  the same artifact gate before the full 9+3 case batch is attempted.
- Only full declared-case `max_diff=0` / bit identity may update the ledger to
  `AE exact`.

## Independent Review

`agy` and Claude Sonnet 5 medium independently selected Render Queue/OpenEXR
as the minimum host-final path and warned against treating plug-in dumps as AE
output. Sonnet additionally identified the localized template name,
`RenderQueueItem.status`, one-frame duration, Output Module depth, and truthful
metadata constraints. Their advice is incorporated only where it agrees with
the inspected repository and local AE observations above.

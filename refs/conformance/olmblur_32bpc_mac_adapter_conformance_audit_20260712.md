# OLMBlur 32bpc Mac adapter conformance audit

Date: 2026-07-12
Scope: `mac/OLMBlur` 32bpc adapter and focused OLMBlur worker evidence.

## Verdict

No binary-grounded integration bug was found. The existing Mac adapter routes
32bpc Non-Legacy and Legacy renders to the exact portable worker boundaries.
No source change was justified.

This is an adapter/build and worker-contract audit, not an AE-host exactness
claim for 32bpc output.

## FACT

- `mac/OLMBlur/OLMBlur.cpp:1087-1094` dispatches `bpc == 32` to
  `render_32bpc_nonlegacy_adapter` when Legacy is false and to
  `render_32bpc_legacy_adapter` when Legacy is true.
- Both adapters read each input row from
  `input->data + y * input->rowbytes` as `PF_PixelFloat`, and write each output
  row from `output->data + y * output->rowbytes` as `PF_PixelFloat`.
- The adapters pack and unpack the fields in `alpha, red, green, blue` order.
  This matches the portable worker contract of little-endian float32 A/R/G/B.
- The Non-Legacy adapter calls `olm::blur::worker32::render_nonlegacy` with the
  full width, height, and parameter tuple.
- The Legacy adapter calls `olm::blur::worker32_legacy::render` with the full
  width, height, parameter tuple, and `render_scale = 1.0f`.
- Both workers initialize the destination from the source and replace only
  R/G/B. The adapter therefore preserves source alpha, including zero and
  negative float alpha values, instead of converting it to a byte validity
  mask at the host boundary.
- Both adapters guard width/height and pixel-count multiplication and map
  `std::bad_alloc` to `PF_Err_OUT_OF_MEMORY`. The enclosing `EffectMain`
  catches `PF_Err` as required by the existing plug-in entry pattern.
- The Mac target builds successfully with:

  `xcodebuild -project mac/OLMBlur/Mac/OLMBlur.xcodeproj -scheme OLMBlur -configuration Debug -derivedDataPath /tmp/olmblur-xcodebuild build CODE_SIGNING_ALLOWED=NO`

- The Non-Legacy worker smoke passes 7/7 complete AEX fixtures. The Legacy
  worker smoke passes 5/5 complete AEX fixtures. These compare complete raw
  float A/R/G/B buffers byte-for-byte against actual AEX CPU fixtures, not PNG
  tuning or EXR output.

## INFERENCE

- Given the exact worker-boundary fixtures and the compiled Mac target, the
  32bpc adapter’s routing, channel order, row addressing, alpha ownership, and
  worker selection are internally consistent.
- The retained Mac/Windows 32bpc EXR comparison remains insufficient for an
  AE-exact verdict because the Windows effect artifact does not carry a loaded
  OLMBlur AEX hash and cases 0005-0007 also have an input-conversion control
  difference. That evidence must not drive adapter or worker changes.
- The adapter’s `std::bad_alloc` handling is covered; no separate evidence
  currently requires broadening exception policy beyond the established
  `PF_Err` entry boundary.

## Focused verification

- `python3 refs/scripts/smoke_olmblur_worker32_nonlegacy.py` -> PASS, 7/7.
- `python3 refs/scripts/smoke_olmblur_worker32_legacy.py` -> PASS, 5/5.
- `python3 refs/scripts/smoke_olmblur_32bpc_focus.py` -> PASS.
- `python3 refs/scripts/smoke_audit_olmblur_32bpc_mac_candidates.py` -> PASS.
- Mac `xcodebuild` -> `BUILD SUCCEEDED`.

No ledger, Windows request, PNG tuning, or unrelated plug-in file was changed.

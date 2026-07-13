# Mac 32bpc paired batch host abort and OutFlags2 repair (2026-07-12)

## FACT

- The paired ColorKey/ToonDilate Mac AE batch was stopped immediately after a
  user-observed PiPL version dialog.
- `olmcolorkey__case_0001` completed both effect-on and no-effect FLOAT EXR
  renders before the dialog appeared on the next AE launch.
- `olmcolorkey__case_0002` stopped after `try add effect OLM Color Key`; no
  completed result was accepted.
- The batch process exited via interruption (`130`), so no complete candidate
  index or conformance promotion exists.
- AE `Plugin Loading.log` says all MediaCore OLM bundles were taken from its
  registry/cache and the scanned files were marked `Ignore` on that launch.
- Source declarations agree internally for the two rebuilt plug-ins:
  ColorKey `2.3.1/develop` in code and PiPL; ToonDilate `1.1.1/develop` in code
  and PiPL.
- A nine-plug-in audit found zero Code/PiPL declaration mismatches. The
  installed `.rsrc` payloads contain the expected values, and ColorKey's arm64
  `GlobalSetup` writes immediate `0x118800` to `out_data->my_version`.
- The AE plist registry entry timestamp matches the newly installed ColorKey
  bundle. Therefore a stale registry is no longer strong enough to classify
  as the cause without the dialog's exact text.
- A direct one-case rerun of ColorKey case 0002 subsequently completed once,
  but a fresh multi-case batch later stalled again at `try add effect OLM
  Color Key`. The behavior is intermittent and host-state dependent.
- The batch was then hardened to require complete AE process exit before and
  after every artifact. A one-case paired rerun still stopped on its first AE
  launch before creating any JSX log, so asynchronous shutdown is not a
  sufficient explanation.
- The batch now has an independent 180-second per-artifact runner timeout and
  exact `--case-id` filtering. Future host stalls fail closed without spending
  the full AE timeout or producing a partial candidate index.
- The previously unclassified effect-add dialog was captured directly from the
  Window Server. It reports a **Global OutFlags2 mismatch**, not a version
  mismatch: code `0x00801400`, PiPL `0x08001400`. The screenshot is
  `olmcolorkey_global_outflags2_mismatch_20260712.png`.
- The SDK constants used by current ColorKey code evaluate to `0x00801400`:
  smart render (`1 << 10`), float-color aware (`1 << 12`), and flattened
  sequence data (`1 << 23`). The stale PiPL value additionally advertised
  threaded rendering (`1 << 27`) and omitted flattened sequence data.
- ColorKey and ToonDilate PiPL resources were changed to `0x00801400`, matching
  their `GlobalSetup` code. Both universal builds succeeded and
  `smoke_olmcolorkey_toondilate_32bpc_host_paths.py` passed.
- With the rebuilt ColorKey installed, the same case advanced past effect add
  into the 32bpc project-settings stage without the OutFlags2 dialog. The run
  still failed closed because crash-recovery/safe-mode host state prevented the
  JSX runner from writing its result JSON and AE did not exit cleanly. This is
  not pixel-conformance evidence.

## Classification

The original effect-add blocker is classified `host-fix-confirmed-outflags2`.
The production version constants remain unchanged. The current batch failure is
separately `host-runner-state-failed-closed`; rerun only after a normal clean AE
session, and do not promote the partial artifacts.

The partial EXRs remain diagnostic only and are not AE-exact evidence.

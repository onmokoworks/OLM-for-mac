status: blocked
summary: Production runner now uses A03e’s workspace-gated single DoScriptFile dispatch.
  First live JSX exposed read-only output Color/Depth; opt-in builder now retains template readback.
  Second JSX saved all 3 priority projects / 132 queue items, then wrote complete.
  Watcher rejected the script-progress Cancel window as unknown; stopped without rendering.
  Both scripting preferences restored byte-exactly; no AE/aerender/watcher remains.

facts:
- Initial HEAD eab59fdc, clean worktree, empty ticket scratch. Read shared guide,
  compatibility plan, ledger decision rows, emulator GOTCHAS, A01c/A02d/A03e
  reports and smoke runner/watcher sources. No plugin, installed bundle, MAIN,
  emulator, ledger or gate changes; no push, stash, signals or delegated agents.
- Exact live build commands (each once, fresh IDs; stdout/stderr retained):
```sh
TMPDIR="$PWD/orchestra/state/A02e-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02e-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-priority --stage build --run-id priority-e1 --scratch orchestra/state/A02e-real-ae-retest-downsample > orchestra/state/A02e-real-ae-retest-downsample/build-run.log 2>&1
TMPDIR="$PWD/orchestra/state/A02e-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02e-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-priority --stage build --run-id priority-e2 --scratch orchestra/state/A02e-real-ae-retest-downsample > orchestra/state/A02e-real-ae-retest-downsample/build-e2.log 2>&1
```
- Both builds exited 1. Preflight saw unlocked sessions and no AE; memory free
  was 47% / 41%. Prevention backed up preferences and read both crash flags 0.
  Owned AE 2026 PIDs 73027 / 73338 each received exactly one full-path event after
  workspace detection. No -r dispatch. Watcher clicks 0 for both; therefore no
  click entries were appended to A02b-evidence/dialogs.jsonl.
- priority-e1 build.json: phase=error, projects=0. AE 26.3x87 explicitly rejected
  Depth and Color as read-only. Script exited AE normally. This new measured
  host boundary justified removing those writes only in the opt-in JSX.
- priority-e2 build.json: phase=complete, three saved projects at 1920x1080,
  1279x719 and 3840x2160, 44 items each (10 defaults + control × 4 resolutions).
  All are 8 bpc. Queue settings/property readbacks are in the committed manifest.
  Output template reads RGB + Alpha, Millions of Colors+, Premultiplied (Matted).
  No alpha conversion fidelity is inferred from those settings.
- Watcher observed window 1825, title “スクリプト launch.jsx を実行中...”, text
  “Script execution time 0 minutes 4 seconds.”, button “キャンセル”. It emitted
  unknown then blocked, with no click. Screenshot unknown-1825.png is 22,898 bytes;
  both subsequent inspect crops also remain below 400 KB. Screenshot inspected.
  Runner captured owned windows and sent one normal full-path quit; osascript
  returned -128 (user canceled). AE subsequently absent. Although the JSX
  completed during cleanup, the watcher failure is not accepted as a successful
  build lifecycle and no aerender launch followed. No retry after unknown dialog.
- Both scripting-pref records restored=true, original/restored SHA-256
  bb437dbab0b979e92fb55e33051d9331d12f1fc86bb64e33aee8dd16dad77f03.
  Backups, logs, input hashes, manifests, screenshots and installed binary hashes
  are in A02e-evidence/. Ten installed executables were hashed, not modified;
  this is on-disk identity, not loaded-module proof.
- Offline pipeline 7/7 and comparator 4/4 pass. New pipeline regression checks
  single post-workspace dispatch without -r and unknown-dialog capture/one quit.
  git diff --check passes. No render, oracle or native-bundle comparison occurred.
  Mismatch counts / first mismatch / actual InData downsample / refusals /
  seconds per rendered frame: unavailable, not zero. No plugin bug established.

NT = not rendered, for all requested sizes/defaults/corpus cases.

| Plugin | Full 8/16/32 | Half 8/16/32 | Third 8/16/32 | Quarter 8/16/32 |
| --- | --- | --- | --- | --- |
| OLMBlur | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| ColorKeep | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMColorKey | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMDirectionalBlur | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMDistanceGradation | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMKiraKira | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMSmoother2 | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMToonDilate | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMRadialBlur | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |
| OLMSmoother | NT/NT/NT | NT/NT/NT | NT/NT/NT | NT/NT/NT |

| Timing scope | 1080p seconds/frame | 4K seconds/frame |
| --- | --- | --- |
| All ten plugins, four resolutions | unavailable | unavailable |

inference:
- A03e’s dispatch recipe works for the real builder. The new stop is a watcher
  classification boundary: a script-progress window offers only Cancel, which
  is outside the click allowlist. It plausibly needs an explicit wait-only rule,
  not a button action. This does not justify broad unknown-dialog bypass.
- The complete second manifest is useful scaffolding evidence, not render proof.
  Premultiplied TIFF may affect transparent effect comparisons; controls and
  pixel-preserving output setup must resolve this before attributing differences.

changed_files:
- tools/ae_smoke/run_ae_smoke.py
- tools/ae_smoke/prepare_downsample.jsx
- tools/ae_smoke/test_pipeline.py
- tools/ae_smoke/README.md
- orchestra/reports/A02e-real-ae-retest-downsample.md
- orchestra/reports/A02-real-ae-retest-downsample.md (latest-attempt pointer)
- orchestra/reports/A02e-evidence/

verify:
```sh
mkdir -p orchestra/state/A02e-real-ae-retest-downsample
python3 -m venv orchestra/state/A02e-real-ae-retest-downsample/venv
TMPDIR="$PWD/orchestra/state/A02e-real-ae-retest-downsample" orchestra/state/A02e-real-ae-retest-downsample/venv/bin/pip install numpy tifffile OpenEXR
TMPDIR="$PWD/orchestra/state/A02e-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02e-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_pipeline.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py
git diff --check
```
Expected 7 + 4 passing tests and clean whitespace. No AE launch. Live commands
above document attempted runs; do not reuse their IDs or retry the unknown
window before the watcher boundary is resolved.

next:
- A03f proposed: narrowly recognize AE script-execution progress windows as
  wait-only, retain unknown-dialog fail-closed and deadlines, add screenshot/
  metadata regression from window 1825. Do not click Cancel. Then use a fresh
  priority run ID and repeat all unlocked/busy/memory checks.
- Add prevention + scripting-pref restore to each aerender launch, calibrate
  template depth/alpha and controls, render priority defaults, then actual
  InData/downsample-bound F53 comparisons. Complete 16/32 bpc including untouched
  DistanceGradation defaults and two exact corpus cases per plugin. Corpus/oracle
  integration remains unimplemented. No black/plugin fix ticket is justified.

cleanup:
- No owned background process remains. Regenerable watcher binaries/module
  caches and ticket venv removed after verification. Evidence/inputs retained
  within the 5 GiB limit; no generated bundle was created or installed.
- Third-party AE extension logs mention their own /tmp socket; worker scratch
  and all commands’ temporary directories were under this worktree.

# AE 2026's built-in NExpression MCP bridge

AE 2026 (both platforms) ships an AEGP plugin, NExpression, that runs a local
MCP server at `http://127.0.0.1:9224/mcp` whenever AE is running. It gives
structured scripting access (comp/layer/property enumeration, expression
read/write, frame-snapshot PNG rendering, undo-grouped writes) plus raw
ExtendScript execution (`execute_script` / `execute_script_async` /
`get_script_job` / `get_bridge_status`), without driving the real screen.

`client.py` here is a minimal stdlib client for it (same protocol the
Windows-side T18 fixture's `tools/ae_mcp.py` uses, so scripts written against
one run against the other). It was discovered and used live during the T16/T17
investigations (2026-10-28/29) to open the real T18 project, render frames
through the actual installed plugins, and compare them byte-for-byte against
Windows AE's reference exports — much faster and more reliable than this
project's existing AX/Vision dialog-watcher (`tools/ae_smoke/`), because most
scripted operations never surface a dialog at all.

## Usage

```python
import sys; sys.path.insert(0, 'tools/ae_mcp')
from client import Client

c = Client()
result = c.execute('JSON.stringify({numItems: app.project.numItems});')
print(result['result'])

# Structured tools (see initialize's `instructions` field, or tools/list, for
# the full catalog): get_comp_structure, list_layer_properties,
# get_property_value, set_property_value, apply_expression, get_frame_snapshot,
# create_comp, set_comp_settings, duplicate_comp, delete_item, get_comp_layers,
# copy_layers_to_comp, get_selected_layers, get_project_info, undo, redo,
# check_properties_exist, get_expression_error, poll_events.
info = c.call('get_project_info')
```

## Things learned the hard way

- **Opening/closing projects**: always `app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES)`
  before `app.open(...)` to a different file in the same session — otherwise a
  dirty project (e.g. one with render-queue items you added) can prompt to
  save, which this bridge cannot dismiss.
- **Quitting**: use `app.quit()` via `execute`/`execute_script_async`, not an
  AppleEvent (`osascript -e 'tell application ... to quit'`). The AppleEvent
  route repeatedly failed with `-128`/`-1708` in this project's testing,
  apparently whenever AE's main thread is even slightly busy; the in-process
  `app.quit()` call always worked cleanly. If AE's main thread is genuinely
  hung (see below), nothing can quit it — `get_bridge_status` will show
  `mainThreadLastTickMsAgo` climbing without bound; at that point only a
  manual/force quit recovers it.
- **A render that looks instant can still be an error, not a success.**
  `RenderQueueItem.status` after `renderQueue.render()` is an enum; look it up
  once per session (`for (var k in RQItemStatus) ...`) rather than assuming a
  number. `3019` is `DONE`; `3018` is `ERR_STOPPED` — a render that returns in
  under a second with status `3018` and no output file failed, it did not
  succeed quickly. There is no scripted way found so far to read the actual
  error text; AE's own logs/Console.app showed nothing even with
  `rq.logType = LogType.ERRORS_AND_SETTINGS` set. A plugin's own
  `OLM_REFUSAL_TRACE`-style env-gated tracing (grep the plugin's `.cpp` for
  `getenv`) only takes effect if it was present in AE's environment at launch —
  set it before `open -a`/launching the binary, not after.
- **Crash-recovery dialogs are not solely gated by the `CrashOccurred`/
  `ForceQuitOccured` preference flags** that `tools/ae_smoke/ae_dialog_watch`
  resets. Even with both confirmed `0` before launch, a "クラッシュ修復オプション"
  dialog appeared once in testing after an earlier force-quit; the actual
  trigger (a leftover autosave/recovery artifact?) was not identified. If one
  appears, this bridge cannot see or dismiss it — closing/dismissing it is a
  real-screen action outside this bridge's scope.
- A render-queue item added with `om.applyTemplate("_HIDDEN X-Factor N[ Premul]")`
  immediately after adding it to the queue picked up this machine's existing
  output-module templates (set up previously for `tools/ae_smoke`'s own work)
  without needing to create them.
- PSD output files AE writes are **not byte-stable across machines/runs even
  for pixel-identical content** (observed non-pixel metadata differences on a
  32bpc PSD export). Decode and compare actual pixel data (see
  `compare_images.py`'s `read_psd`/`ae_decode.compare`), never raw file hashes,
  for anything AE writes as PSD. PNG and the derived EXR did not show this
  problem.

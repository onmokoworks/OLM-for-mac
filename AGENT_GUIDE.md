# AGENT_GUIDE — read this first (any model: Fable, Opus, Sonnet, Gemini, Codex)

This repo ports Windows AE `.aex` plugins to Apple Silicon/macOS. Multiple models
work on it in turns. This is the shared contract. It is short on purpose.

## The bar
- **Correctness = exact sample match** against the Windows **CPU Software**
  render for the declared 8/16/32bpc cell. 8bpc may use PNG, 16bpc requires a
  typed high-depth reference, and 32bpc requires a float-preserving reference.
  Tolerance bands and "guarded green" are never completion.
- The only completion state is `AE exact`. Everything else is an evidence/work
  state. `notes/CONFORMANCE_LEDGER.md` is the single source of truth for status,
  priority order, and the per-plugin **forbidden actions** — obey those.
- `notes/PORTING_ROADMAP.md` defines the target set and critical path.
  `refs/conformance/olm_release_scope.json` is the whole-release gate; a slice
  can be `AE exact` while the plug-in and release remain incomplete.

## How we find truth (in order — cheapest, most reliable first)
1. **Local emulation of the CPU `.aex`** (`tools/emulation/`). This is the default.
   Before asking for a Windows debugger trace, ask whether driving the CPU `.aex`
   locally can answer it. On OLM it repeatedly beat Windows round-trips (which
   failed 3× on DistanceGradation while emulation closed it in minutes).
   - Read `tools/emulation/GOTCHAS.md` and use `tools/emulation/aex_witness.py`.
   - The loader (`aex_loader.py`) is plugin-agnostic; it loads any PE64 `.aex`.
2. **Static disasm/decomp** (`disasm/`, `decomp/`) for branch logic and operators.
3. **Windows reference/trace requests** — reserve for what emulation genuinely
   can't answer: GPU-path references (see below) and true AE-host behavior.

## Reference-path-split (important)
Packaged reference PNGs may have been rendered with AE **GPU** acceleration. The
CPU `.aex` cannot produce a GPU shader's output, so a faithful CPU emulation that
still disagrees with a PNG usually means the *reference* is GPU/stale, not that
the port is wrong. When you hit this, request a **SOFTWARE (GPU=0) recapture**
rather than tuning the port to match the PNG. Record each reference's provenance
(GPU vs SOFTWARE) as a first-class fact.

## Discipline (non-negotiable)
- **Fact vs inference**: label every claim. Never fabricate a value or "correct"
  a number to look right — a mismatch is data.
- **No PNG look-matching / no global rewrites / no final-byte-only tweaks** unless
  the ledger's row for that plugin explicitly allows it.
- **Do the work, don't just plan it.** If you're a subagent asked to run/verify,
  actually run it and report real command output — a plan-only reply is a failure.
- Mac source edits on a frozen lane stay frozen until a witness demands the change
  (see the ledger's per-lane notes).

## Windows handoff workflow
- Share root: `/Volumes/onmk/olm_pr` (`new/` = active exchange, `old/` = archive).
- Requests: package with `refs/scripts/package_reference_requests.py`, stage the
  zip into `new/`. Windows renders, drops a return zip in `new/`.
- Intake returns with `scripts/intake_latest_windows_return_from_share.py` (or
  `scripts/intake_olm_return.py`). A return only counts if it delivers the exact
  requested witness; otherwise classify it `failed_partial` etc., don't promote it.

## Porting a NEW (non-OLM) plugin — the playbook
The OLM-specific ledger/notes don't transfer, but the method does:
1. Get the plugin binary; produce Ghidra `disasm/` + `decomp/`.
2. Load it in `tools/emulation/aex_loader.py` (generic) and binary-ground the
   algorithm with `aex_witness.py` — leaf-check ABI first, then drive the worker.
3. Build the CLI/port from the grounded algorithm.
4. Build a conformance check against **SOFTWARE** references.
Keep the emulation harness and this guide; leave the OLM ledger behind.

## Pointers
- Release scope and orchestration: `notes/PORTING_ROADMAP.md`
- Status/priority/forbidden actions: `notes/CONFORMANCE_LEDGER.md`
- Machine release gate: `refs/conformance/olm_release_scope.json`,
  `scripts/check_olm_release_scope.py`
- Emulation how-to + perf: `tools/emulation/README.md`, `GOTCHAS.md`
- Per-plugin IR: `notes/IR_*.md`

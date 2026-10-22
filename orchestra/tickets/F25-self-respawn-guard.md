## Goal
Eliminate the fork-bomb class found during I02: scripts that re-execute themselves
(`[sys.executable, __file__, "--mode", ...]`) and dispatch child modes by `len(sys.argv)`.

## Root cause (fact, orchestrator analysis)
`tools/emulation/test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.py`: when the `--zoom-actual` child
fails, `expected` is None, the `--zoom-production` child is spawned with one argument fewer, matches no
dispatch branch and falls through to `main()`, which re-launches the whole 3-thread campaign -> exponential
self-spawning (procguard caught ~440 Python processes; earlier ~1,500 and 15.6 GB swap).
That file is already patched (child env `OLM_SELF_SPAWN_CHILD=1`, any `--` action or child env refuses main(),
subprocess timeout 1800 s). Use it as the reference fix.

## Steps
1. Find every self-respawning script: `grep -rlE 'sys\.executable,\s*(str\()?(Path\()?__file__' tools tests scripts refs/scripts handoffs`
   (exclude .venv). Also helpers that spawn `sys.argv[0]`.
2. Apply the same guard to each: children get `OLM_SELF_SPAWN_CHILD=1`; in `__main__`, after the child-mode
   branches, a child env or any unmatched `--` action exits 2 and never calls main(); add a subprocess timeout;
   do not change measurement logic, arguments, or outputs.
3. Add one test `tests/test_self_respawn_guard.py` that statically checks every self-respawning script has the guard,
   and dynamically runs 2-3 representative scripts with a malformed child argv under `OLM_SELF_SPAWN_CHILD=1`
   expecting exit 2 within seconds.
4. Do NOT run full campaigns. Keep `--jobs`/pools as they are. Commit.

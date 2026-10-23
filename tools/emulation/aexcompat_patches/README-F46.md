# F46 double pow import worker

F45 plus F43c `ucrt_pow`, default FMA mode, through the Unicorn binary import
hook and native Win64 callback. Both CRT DLL names remain supported. No other
math implementation changes. The source snapshot and hash manifest are retained.

Run serially from the worktree:

```sh
python3 tools/emulation/aexcompat_patches/build_F46.py
python3 tools/emulation/aexcompat_patches/validate_F46.py
python3 tools/emulation/aexcompat_patches/check_mode_F46.py
python3 tools/emulation/aexcompat_patches/validate_native_F46.py
python3 tools/emulation/aexcompat_patches/build_F46.py --register
bash tools/fuzz/build_F46.sh
python3 tools/emulation/aexcompat_patches/validate_mac_F46.py
python3 tools/fuzz/measure_F46.py --before
python3 tools/fuzz/measure_F46.py
python3 tools/fuzz/summarize_F46.py
python3 tools/fuzz/rebaseline_F46.py
```

For an independent rebuild, pass a fresh `--cache-root` outside existing worker
paths. Do not register over an existing entry. Validators target the retained
cache paths; copy the new build manifest to F46-evidence before native validation.
Worker builds use memory_pressure >=30%, cargo/CMake jobs=1 and clean their
regenerable build tree. Replays use jobs=1. No corpus changes are automatic.

The shim checks one million full-width random pairs and one million plugin-range
pairs for each DLL against the pinned Rosetta UCRT. Plugin ranges include sRGB
2.4/1÷2.4, repeat integer exponents 0..99, positive gamma 0..10, normalized bases
and HDR bases up to 16. Mac-object qualification additionally exercises both
modes in full-width and signed-exponent ranges on arm64 and x86_64.

Keep F45 selectable using `--worker` or `OLM_AEX_WORKER` set to
`~/.cache/olm-emu/worker-F45-msdouble/aex-guest-worker`.
See `orchestra/reports/F46-evidence/boundaries.md` for boundary exclusions.

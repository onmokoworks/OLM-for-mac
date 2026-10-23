# F45 double import worker

F44 plus double `sin`, `cos`, `exp`, in the existing default FMA mode. `pow`
remains host because the dependency F43c reports blocked, as the ticket requires.
Both CRT DLL names use the same production Unicorn hooks; native Win64 export
callbacks use the same ucrtmath module. The ABI probe emits four uint64 words
(input, reserved, result, duplicate result). No float implementation is changed.

Build (one cargo/CMake job, memory >=30%, no existing cache path overwritten):

```sh
python3 tools/emulation/aexcompat_patches/build_F45.py
python3 tools/emulation/aexcompat_patches/validate_F45.py
python3 tools/emulation/aexcompat_patches/check_mode_F45.py
python3 tools/emulation/aexcompat_patches/validate_native_F45.py
python3 tools/emulation/aexcompat_patches/build_F45.py --register
```

The registered worker exists already. For an optional independent rebuild use
`--cache-root "$HOME/.cache/olm-emu/recheck-F45"` on the build command; do not
register it over the existing worker. Validation tools target the registered
cache paths. The build's source snapshot and manifest are retained; its Rust
build tree is removed. All test streams/logs go under this ticket's worktree
scratch. The Rosetta oracle is the pinned UCRT DLL used by F43b/F44.

The old worker remains selectable with `--worker` or `OLM_AEX_WORKER` pointing to
`~/.cache/olm-emu/worker-F44-msfloat/aex-guest-worker`.

See `orchestra/reports/F45-evidence/boundaries.md` for Mac boundary selection,
including why embedded OpenCV exp and Mac FFT twiddle math remain unchanged.
The Mac translation unit `core/ucrt_ms_double_mac.c` avoids Carbon prefix-header
name pollution without editing the qualified standalone math implementation.

After `bash tools/fuzz/build_F45.sh`, run `python3 tools/emulation/aexcompat_patches/validate_mac_F45.py` to qualify both architectures of the actual Xcode objects against Rosetta (three functions, both modes, one million inputs each).

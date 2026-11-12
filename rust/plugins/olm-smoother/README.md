# OLMSmoother v1 Rust port

This crate implements the independent **v1** effect, with the original Classic
8/16 bpc entry points. It does not declare SmartFX or 32 bpc. Production rendering
uses Rust; the existing C++ kernels are compiled into a reference archive used
only by unit tests.

From `rust/`, with the job's isolated build directory:

```powershell
$env:CARGO_TARGET_DIR = 'D:\olm-rs-target\P-smoother'
cargo build --release -p olm-smoother -j 2
cargo test --release -p olm-smoother -j 2
```

The Windows output is `D:\olm-rs-target\P-smoother\release\olm_smoother.dll`.
Stage it as `.aex` for AEXCompat; do not install a validation build in MediaCore.
See [VALIDATION.md](VALIDATION.md) for the actual binary identities and results.

`src/algorithm.rs` owns parameter validation, fallible aligned scratch buffers,
color-key preparation, ordered traversal, and final output. It preserves the
C++ 4096-side / 4096×2160-pixel envelope. Classic output extent selects callback
centers; source reads and neighboring writes remain frame-wide. Downsample
does not scale v1's integer tolerance. Input extent and world origins do not
change the original local-coordinate traversal.

`src/generated.rs` translates the existing C++ classifier, contour walk,
dispatch, and interpolation bodies. Its state machines preserve the source's
goto control flow, integer promotions, wrapping arithmetic, binary32 operations,
and x86 truncation. `src/support.rs` supplies local register/stack carriers,
direction tables, and the five curve evaluators. These carriers use owned
memory and contain no emulator, original executable, or platform API.

Generation is a development operation, not part of a normal Cargo build:

```powershell
python rust/plugins/olm-smoother/tools/translate.py
```

The generator uses the installed `C:/Program Files/LLVM/bin/clang++.exe` to
obtain a typed AST of the repository's C++ source. Unknown AST constructs fail
generation. It keeps the AST and temporary translation unit in ignored
`tools/work/`; only generated Rust is needed to compile the algorithm. The
test-only C++ wrapper reads the original include bodies directly. No new
third-party dependency was introduced beyond the pilots' existing `cc`, PiPL,
and `winres` build approach.

`src/ae.rs` retains `EffectMain` and the original `entryPointFunc` alias. A local
ParamsSetup adapter is necessary because the shared `Kind::Color` currently
initializes black, whereas v1 declares white. Native inspection also establishes
that the original tolerance UI maximum is **255**, despite the C++ source's
slider maximum of 6. Default tolerance remains 6. The complete Windows PiPL is
298 bytes and is checked independently against the original resource.

Traversal within each render is serial because callbacks write neighboring
pixels. Separate renders have no shared mutable state. Tests compare 1/2/4-worker
schedules as well as C++ numerical helpers, complete frames, each direction's
classification/dispatch, and contour walkers. This does not certify native AE
threading or macOS packaging; neither was exercised in this Windows job.

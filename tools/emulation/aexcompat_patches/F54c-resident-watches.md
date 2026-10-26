# F54c resident watches

AEXCompat branch `olm/F54c-resident-watches` is stacked on F54b
`e96d6ed9b0a8170e1d3d427ac6cf65e07dc3144e`. The adjacent patch reproduces its
source changes. The worker documentation is `docs/RESIDENT_WATCHES.md` in that
patch and the installed source archive.

Build from the space-free AEXCompat worktree, with one job:

```sh
export CARGO_TARGET_DIR="$HOME/.cache/olm-emu/build-F54c/target"
export TMPDIR="$HOME/.cache/olm-emu/build-F54c/tmp"
mkdir -p "$TMPDIR"
cargo build --manifest-path guest/Cargo.toml --release -p aex-guest-worker --bin aex-guest-worker -j 1
RUST_TEST_THREADS=1 cargo test --manifest-path guest/Cargo.toml --release -p aex-guest-worker -p olm-ucrtmath -j 1
```

From the OLM worktree, install committed source with `install_F54c.py --source
<space-free-worktree> --binary <target>/release/aex-guest-worker`. This registers an
immutable `worker-F54c` directory under the shared INDEX lock, retaining source
archive and hashes. It never changes the default oracle.

`verify_F54c.py --worker <worker-F54c>/aex-guest-worker` compares all 17 retained
R06 first-witness cases against their archived C53b stage bytes and final outputs,
then checks a displaced cropped checkout against untraced output. Raw dumps are
checked against JSON and retired after each retained case. Summary hashes remain
in this ticket's scratch. Original AEX/source assets are read from MAIN.

`run_F54c_corpus.py --worker <worker-F54c>/aex-guest-worker` reuses the F54b driver
and F53 baseline on every saved corpus, with tracing unset, one worker process at
a time. The only change to the F54b driver is an optional scratch destination.
The wrapper verifies every expected case/route was seen and retains compressed
per-case observations and totals. Neither verifier builds or runs an OLM plugin.

Final evidence belongs in `orchestra/reports/F54c-evidence/`; raw captured planes
remain private scratch and must not be committed. Delete regenerable cache build
trees after installation and successful verification.

`verify_F54c_4k.py --worker <worker-F54c>/aex-guest-worker` separately compares
original-AEX 3840×2160 no-op renders in all three depths to F54b and captures the
128-byte InData context at direct call RVA 0x10974. F53 rejects these dimensions.
The full 132710400-byte snapshot is covered by the synthetic worker unit test;
this is not a claim of capturing a real-AEX 4K intermediate plane.

Known inherited boundary: `probe_F54c_entry.py` records zero captures at selector
entry RVA 0x10540 on both F54b and F54c, despite exact no-op output and no
unhookable diagnostic. Use the measured direct-call sites for the present ticket;
selector-entry/warmed-session hook behavior needs a separate investigation.

Qualification is **blocked**: the final 5687-route inventory contains two
RadialBlur status differences (F53 completes; F54c reaches the existing 20-second
limit). See the ticket report and installed `qualification.json`. Initial and
isolated observations are retained, including baseline status variability. Do
not interpret successful stage captures as full-corpus qualification.

`run_F54c_corpus.py --resume` can validate and reaggregate completed records from
the same frozen corpus. It checks worker identities, route coverage and category
counts; it does not establish that edited corpus contents match old observations.
A new non-resumed run removes stale summaries before launching workers. Comparison
failures still produce retained evidence and a nonzero final exit status.

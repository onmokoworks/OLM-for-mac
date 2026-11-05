# T24 host fixture data arena

`build_t24.py` builds `~/.cache/olm-emu/worker-T24-arena/aex-guest-worker`
from the hash-bound retained F53 source, without changing the default worker.
It applies `T24-arena.patch` and the previously validated S02 float-color
transport in `T24-S02-transport.patch`. The latter is required by the T22
DistanceGradation/KiraKira captures; its callback SHA-256 must match the
retained S02-F53 build manifest.

The original failure is a host fixture allocation, not a guest suite call:
`classic.rs:3325` allocates the negotiated output after SMART_PRE_RENDER
returns. Both T23 PF32 captures request 33,177,728 bytes (1920 × 1080 × 16
plus two 64-byte guards). At failure the low data cursor is `0x43f49e70`,
aligned start `0x43f49e80`, requested end `0x45eedf00`, and limit
`0x44000000`. Guest RIP is the return sentinel `0x600ff000`.

Although DATA_SIZE is 256 MiB, the host bump allocator stops at
HANDLE_DATA_BASE, only 64 MiB from DATA_BASE. The arena patch leaves all
existing region addresses and successful low allocations unchanged. On
overflow it maps a separate 256 MiB host bump arena at `0xe00000000`,
beyond the existing world, stream, popup, and handle/token reservations. It does not change guest
arithmetic, suite semantics, handles, or plugin sources.

Run from this worktree (the builder runs Cargo from its space-free cache
source and puts all build temporary files under `src-T24`):

```sh
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 tools/live_capture/build_t24.py
python3 tools/live_capture/build_t24.py --register
python3 tools/live_capture/build_t24.py --verify
python3 -m unittest discover -s tools/live_capture -p test_compare.py
python3 tools/live_capture/regression.py --t23 \
  --worker "$HOME/.cache/olm-emu/worker-T24-arena/aex-guest-worker" \
  --scratch orchestra/state/T24-aexcompat-worker-32bpc-arena/regression
python3 tools/live_capture/audit_t24.py
```

Redirect lengthy runs to logs under the ticket scratch directory. The build
runs two allocator boundary tests, installs a source/hash/recipe manifest,
then deletes the regenerable Cargo target directory. Registration retains
other INDEX entries. `--replace-existing` is required to replace an earlier
T24 worker hash. The audit uses F53 for T23 and S02-F53 for T22, compares
against saved logs, and preserves worker commands, stderr, session messages,
RAW outputs and JSON results. Corpus replay checks saved outcomes, which
must not be interpreted as every saved case being exact.

PF32 comparison remains bit-exact. ULP reporting uses monotonic binary32
word keys (signed zeros are distinct, distance 1); nonfinite differences
have no finite ULP distance. Row padding is excluded.

The ignored `orchestra/reports/T24-aexcompat-worker-32bpc-arena.md` contains
the measured results and evidence paths. No plugin or release-gate change
belongs to this ticket.

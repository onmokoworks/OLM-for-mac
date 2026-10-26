#!/bin/sh
set -eu
: "${AEXCOMPAT_SOURCE:?Set AEXCOMPAT_SOURCE to the space-free X01 worktree}"
: "${X03_LOG_DIR:?Set X03_LOG_DIR to ticket scratch}"
cd "$AEXCOMPAT_SOURCE"
export TMPDIR="$HOME/.cache/olm-emu/build-X03/tmp"
export TMP="$TMPDIR" TEMP="$TMPDIR"
export CARGO_TARGET_DIR="$HOME/.cache/olm-emu/build-X03/target"
export CARGO_PROFILE_DEV_DEBUG=0 CARGO_PROFILE_TEST_DEBUG=0 CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_INCREMENTAL=0
export CARGO_BUILD_JOBS=1 CMAKE_BUILD_PARALLEL_LEVEL=1 RUST_TEST_THREADS=1
mkdir -p "$TMPDIR" "$X03_LOG_DIR"
memory_pressure > "$X03_LOG_DIR/memory-pressure.txt"
python3 - "$X03_LOG_DIR/memory-pressure.txt" <<'PY'
import re,sys
text=open(sys.argv[1]).read()
free=int(re.search(r'System-wide memory free percentage: (\d+)%',text)[1])
assert free>=30, f'Build blocked: {free}% free'
print('Memory free:',free)
PY
run() {
  name="$1"
  shift
  printf '%s\n' "START $name"
  if "$@" > "$X03_LOG_DIR/$name.log" 2>&1; then
    printf '%s\n' "PASS $name"
  else
    result=$?
    tail -40 "$X03_LOG_DIR/$name.log"
    printf '%s\n' "FAIL $name ($result)"
    exit "$result"
  fi
}
run guest-tests cargo test --release --manifest-path guest/Cargo.toml -p aex-guest-worker -p olm-ucrtmath --locked --jobs 1 -- --test-threads=1
run guest-build cargo build --release --manifest-path guest/Cargo.toml -p aex-guest-worker --bin aex-guest-worker --locked --jobs 1
run harness-tests cargo test --manifest-path broker/Cargo.toml -p aexcompat-harness --bin aexcompat-harness --locked --jobs 1 -- --test-threads=1
run artifact-tests cargo test --manifest-path broker/Cargo.toml -p aexcompat-broker --lib render_artifacts --locked --jobs 1 -- --test-threads=1
run decoding-tests cargo test --manifest-path broker/Cargo.toml -p aexcompat-broker --lib decoded_rgba --locked --jobs 1 -- --test-threads=1
export AEXCOMPAT_TEST_AEX="$HOME/Documents/Projects/Personal/OLM as/refs/upstream_official/20260619_olm_official_zips/extracted/OLMColorKeep/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
export AEXCOMPAT_GUEST_WORKER="$CARGO_TARGET_DIR/release/aex-guest-worker"
run chain-tests cargo test --manifest-path broker/Cargo.toml -p aexcompat-harness --bin aexcompat-harness chain --locked --jobs 1 -- --include-ignored --test-threads=1
run uhd-tests cargo test --manifest-path broker/Cargo.toml -p aexcompat-harness --bin aexcompat-harness 4k --locked --jobs 1 -- --include-ignored --test-threads=1
run resident-export cargo test --manifest-path broker/Cargo.toml -p aexcompat-harness --bin aexcompat-harness real_resident_argb16_gui_export_matches_worker_world --locked --jobs 1 -- --ignored --test-threads=1
run windows-check cargo check --manifest-path broker/Cargo.toml -p aexcompat-harness --target x86_64-pc-windows-msvc --locked --jobs 1
run harness-build cargo build --release --manifest-path broker/Cargo.toml -p aexcompat-harness --locked --jobs 1
run coordinate-build clang++ -std=c++20 -D__cdecl= -Iminihost/src tests/portable/ui_event_coordinates.cpp minihost/src/worker_ui_event_execution.cpp -o "$HOME/.cache/olm-emu/build-X03/ui-event-coordinates"
run coordinate-test "$HOME/.cache/olm-emu/build-X03/ui-event-coordinates"

#!/usr/bin/env bash
# Run on a Mac. Build and package; never install into an Adobe directory.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
[[ "$(uname -s)" == Darwin ]] || { echo 'macOS with Xcode command-line tools required' >&2; exit 1; }
export MACOSX_DEPLOYMENT_TARGET=11.0
export CC="${CC:-clang}" CXX="${CXX:-clang++}"
dest="${1:-local/macos-universal}"
[[ ! -e "$dest" && ! -e "$dest.zip" ]] || { echo 'Output already exists; choose a new directory' >&2; exit 1; }
for target in aarch64-apple-darwin x86_64-apple-darwin; do
  cargo build --release --workspace --target "$target"
done
target_dir="${CARGO_TARGET_DIR:-$root/target}"
python3 tools/golden/package_macos.py "$target_dir" "$dest"
ditto -c -k --sequesterRsrc --keepParent "$dest" "$dest.zip"
echo "Wrote $dest.zip (ten universal plug-ins; ad-hoc only, not notarized)"

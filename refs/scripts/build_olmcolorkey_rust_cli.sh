#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CRATE_DIR="$ROOT_DIR/rust/olmcolorkey_cli"
OUT="${1:-$ROOT_DIR/cli/OLMColorKey/olmcolorkey_rust_cli}"

cargo build --manifest-path "$CRATE_DIR/Cargo.toml" --release
mkdir -p "$(dirname "$OUT")"
cp "$CRATE_DIR/target/release/olmcolorkey_cli" "$OUT"
echo "$OUT"

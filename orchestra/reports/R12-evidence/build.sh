#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
export TMPDIR="${OLM_PACKAGE_STATE:-$PWD/orchestra/state/R12-release-gate-final/package}"
release_cache="${OLM_RELEASE_CACHE:-$HOME/.cache/olm-emu/release-R12}"
mkdir -p "$TMPDIR"
export OLM_TEST_JOBS=1
# Keep the packager's fixed product paths inside ticket scratch as well.
for plugin in ColorKeep OLMBlur OLMColorKey OLMDirectionalBlur OLMRadialBlur OLMKiraKira OLMToonDilate OLMDistanceGradation OLMSmoother OLMSmoother2; do
  product="$PWD/mac/$plugin/Mac/build/Release"
  mkdir -p "$(dirname "$product")"
  mkdir -p "$TMPDIR/products/$plugin"
  if [[ ! -e "$product" ]]; then
    ln -s "$TMPDIR/products/$plugin" "$product"
  fi
done
mkdir -p "$release_cache"
# Limit the existing serial bundle builder without changing shared build policy.
xcodebuild() {
  if [[ "${1:-}" == -project ]]; then
    command xcodebuild -jobs 1 "$@"
  else
    command xcodebuild "$@"
  fi
}
export -f xcodebuild
scripts/package_mac_plugins.sh --configuration Release --output "$release_cache/OLM_for_Mac.zip"

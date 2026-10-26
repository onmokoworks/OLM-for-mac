#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
export TMPDIR="$PWD/orchestra/state/R12-release-gate-final/package"
mkdir -p "$TMPDIR"
export OLM_TEST_JOBS=1
export OLM_REFERENCE_ROOT="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
# Keep the packager's fixed product paths inside ticket scratch as well.
for plugin in ColorKeep OLMBlur OLMColorKey OLMDirectionalBlur OLMRadialBlur OLMKiraKira OLMToonDilate OLMDistanceGradation OLMSmoother OLMSmoother2; do
  product="$PWD/mac/$plugin/Mac/build"
  mkdir -p "$TMPDIR/products/$plugin"
  if [[ ! -e "$product" ]]; then
    ln -s "$TMPDIR/products/$plugin" "$product"
  fi
done
mkdir -p "$HOME/.cache/olm-emu/release-R12"
# Limit the existing serial bundle builder without changing shared build policy.
xcodebuild() {
  if [[ "${1:-}" == -project ]]; then
    command xcodebuild -jobs 1 "$@"
  else
    command xcodebuild "$@"
  fi
}
export -f xcodebuild
scripts/package_mac_plugins.sh --configuration Release --output "$HOME/.cache/olm-emu/release-R12/OLM_Mac_Plugins_Release_20261026.zip"

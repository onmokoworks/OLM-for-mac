#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
export TMPDIR="$PWD/orchestra/state/R11-release-package-and-notes"
mkdir -p "$TMPDIR"
export OLM_TEST_JOBS=1
export OLM_REFERENCE_ROOT="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
# Limit the existing serial bundle builder without changing shared build policy.
xcodebuild() {
  if [[ "${1:-}" == -project ]]; then
    command xcodebuild -jobs 1 "$@"
  else
    command xcodebuild "$@"
  fi
}
export -f xcodebuild
scripts/package_mac_plugins.sh --configuration Release --output "$TMPDIR/OLM_Mac_Plugins_Release_20261026.zip"

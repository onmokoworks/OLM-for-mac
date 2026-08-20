#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIGURATION="${CONFIGURATION:-Debug}"

case "$CONFIGURATION" in
  Debug)
    PROJECT_CONFIGURATION="Debug"
    # Bash 3.2 treats an empty-array expansion as unbound under `set -u`.
    # Keep the invocation explicit and the array non-empty on stock macOS.
    optimization_flags=(GCC_OPTIMIZATION_LEVEL=0)
    ;;
  Release)
    # The imported legacy projects only define Debug. Keep that project
    # configuration as the source of target settings, but make the release
    # invocation explicit and reproducible here until the projects are
    # migrated to shared xcconfig files.
    PROJECT_CONFIGURATION="Debug"
    optimization_flags=(
      GCC_OPTIMIZATION_LEVEL=3
      DEBUG_INFORMATION_FORMAT=dwarf-with-dsym
      ENABLE_TESTABILITY=NO
      COPY_PHASE_STRIP=YES
    )
    ;;
  *)
    echo "unsupported CONFIGURATION: $CONFIGURATION (expected Debug or Release)" >&2
    exit 2
    ;;
esac

derived_data="$(mktemp -d "${TMPDIR:-/tmp}/olm_mac_build.XXXXXX")"
trap 'rm -rf "$derived_data"' EXIT

"$ROOT/scripts/setup_ae_sdk_links.sh" >/dev/null

plugins=(
  ColorKeep
  OLMBlur
  OLMColorKey
  OLMDirectionalBlur
  OLMRadialBlur
  OLMKiraKira
  OLMToonDilate
  OLMDistanceGradation
  OLMSmoother
  OLMSmoother2
)

for plugin in "${plugins[@]}"; do
  project="$ROOT/mac/$plugin/Mac/$plugin.xcodeproj"
  binary="$ROOT/mac/$plugin/Mac/build/$CONFIGURATION/$plugin.plugin/Contents/MacOS/$plugin"

  if [[ ! -d "$project" ]]; then
    echo "[MISS] $plugin project: $project" >&2
    exit 1
  fi

  echo "=== build $plugin ($CONFIGURATION) ==="
  xcodebuild \
    -project "$project" \
    -configuration "$PROJECT_CONFIGURATION" \
    ARCHS="arm64 x86_64" \
    ONLY_ACTIVE_ARCH=NO \
    MACOSX_DEPLOYMENT_TARGET=11.0 \
    OBJROOT="$derived_data/$plugin/Intermediates" \
    SHARED_PRECOMPS_DIR="$derived_data/$plugin/PrecompiledHeaders" \
    CONFIGURATION_BUILD_DIR="$ROOT/mac/$plugin/Mac/build/$CONFIGURATION" \
    "${optimization_flags[@]}" \
    build

  if [[ ! -f "$binary" ]]; then
    echo "[MISS] $plugin binary: $binary" >&2
    exit 1
  fi

  file "$binary"
  archs="$(lipo -archs "$binary")"
  if [[ " $archs " != *" arm64 "* || " $archs " != *" x86_64 "* || "$(wc -w <<<"$archs" | tr -d ' ')" != 2 ]]; then
    echo "[FAIL] $plugin binary architectures are not exactly arm64+x86_64: $archs" >&2
    exit 1
  fi

  for arch in arm64 x86_64; do
    minos="$(xcrun vtool -show-build -arch "$arch" "$binary" | awk '/minos/ && !found {print $2; found=1}')"
    if [[ "$minos" != "11.0" ]]; then
      echo "[FAIL] $plugin $arch minimum macOS is $minos, expected 11.0" >&2
      exit 1
    fi
  done

  codesign --verify --deep --strict "$ROOT/mac/$plugin/Mac/build/$CONFIGURATION/$plugin.plugin"
done

echo "all mac plugin builds verified ($CONFIGURATION)"

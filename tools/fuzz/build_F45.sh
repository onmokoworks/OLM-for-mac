#!/bin/bash
set -eu
root="$(cd "$(dirname "$0")/../.." && pwd)"
s="$root/orchestra/state/F45-integrate-ms-double/xcode"
mkdir -p "$s"
"$root/scripts/setup_ae_sdk_links.sh" > "$s/sdk-links.log"
export TMPDIR="$s" TMP="$s" TEMP="$s"
for plugin in OLMColorKey OLMKiraKira OLMRadialBlur; do
  xcodebuild -project "$root/mac/$plugin/Mac/$plugin.xcodeproj" -configuration Debug -jobs 1 \
    ARCHS='arm64 x86_64' ONLY_ACTIVE_ARCH=NO MACOSX_DEPLOYMENT_TARGET=11.0 \
    OBJROOT="$s/$plugin/obj" SYMROOT="$s/$plugin/products" \
    SHARED_PRECOMPS_DIR="$s/$plugin/pch" CONFIGURATION_BUILD_DIR="$s/$plugin/products" \
    GCC_OPTIMIZATION_LEVEL=2 CODE_SIGNING_ALLOWED=NO build > "$s/$plugin.log" 2>&1
  lipo -archs "$s/$plugin/products/$plugin.plugin/Contents/MacOS/$plugin"
done

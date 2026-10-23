#!/bin/bash
# Run existing touched-plugin tests with independent UCRT C linkage.
set -eu
root="$(cd "$(dirname "$0")/../.." && pwd)"
s="$root/orchestra/state/F31-port-ucrtmath-switch-oracle/tests"
mkdir -p "$s/bin"
ln -sf "$root/tools/ucrt_cxx.py" "$s/bin/clang++"
export PATH="$s/bin:$PATH" TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
export OLM_SDK_ROOT="${OLM_SDK_ROOT:-/Users/onmk/Documents/Projects/Personal/OLM as}"
cd "$root"
"$root/scripts/setup_ae_sdk_links.sh" > "$s/sdk-links.log"
# Read-only absolute reference to retained originals; never copy AEX assets.
if [[ ! -e "$root/plugins_2025" ]]; then ln -s "$OLM_SDK_ROOT/plugins_2025" "$root/plugins_2025"; fi
if [[ ! -e "$root/refs/win_references" ]]; then ln -s "$OLM_SDK_ROOT/refs/win_references" "$root/refs/win_references"; fi
python="${OLM_TEST_PYTHON:-$OLM_SDK_ROOT/tools/emulation/.venv/bin/python}"
"$python" -m pytest -q \
 tests/test_olmblur_generic_beta_lane_20260820.py \
 tests/test_olmblur_generic_beta_sanitizers_20260820.py \
 tests/test_olmcolorkey_generic_pixel_local_beta.py \
 tests/test_olmdistancegradation_generic_production_beta_20260820.py \
 tests/test_olmkirakira_generic_beta_lane_20260820.py \
 tests/test_olmkirakira_generic_beta_sanitizers_20260820.py \
 tests/test_olmradialblur_generic_baseline_20260820.py \
 tests/test_olmradialblur_generic_baseline_sanitizers_20260820.py \
 tests/test_olmdirectionalblur_remaining6_ucrt_powf_census_20260814.py \
 tests/test_directionalblur_general_features_20261001.py \
 tools/fuzz/test_framework.py tools/fuzz/test_adapters.py tools/fuzz/test_rebaseline_production.py \
 > "$s/targeted.log" 2>&1

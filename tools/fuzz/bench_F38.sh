#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
S="$PWD/orchestra/state/F38-x86-default-nan-sign"
mkdir -p "$S"
export TMPDIR="$S" TMP="$S" TEMP="$S"
# Baseline is the ticket's starting commit. Build artifacts stay ticket-local.
git show 395e5d8a:core/olmblur_fullworker_helper.cpp > "$S/baseline.cpp"
clang++ -std=c++17 -O2 -ffp-contract=off -Icore tools/fuzz/bench_F38.cpp "$S/baseline.cpp" -o "$S/bench-before"
clang++ -std=c++17 -O2 -ffp-contract=off tools/fuzz/bench_F38.cpp core/olmblur_fullworker_helper.cpp -o "$S/bench-after"
clang++ -std=c++17 -O2 -ffp-contract=off tools/fuzz/test_F38.cpp core/olmblur_helper.cpp core/olmblur_fullworker_helper.cpp -o "$S/test-F38"
"$S/test-F38"
for round in 1 2 3; do
    echo "round=$round before"
    "$S/bench-before"
    echo "round=$round after"
    "$S/bench-after"
done
rm "$S/bench-before" "$S/bench-after" "$S/test-F38" "$S/baseline.cpp"

#!/bin/sh
# Run from the worktree root. No Microsoft binaries are copied or downloaded.
set -eu
state="$PWD/orchestra/state/F27b-ucrt-math-rosetta"
source_dir="$PWD/tools/ucrt_math_probe/rosetta"
mkdir -p "$state"
export TMPDIR="$state"
: "${PROBE_PY:=/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python}"
clang -arch x86_64 -O2 -Wall -Wextra -Wno-deprecated-declarations "$source_dir/oracle.c" -o "$state/oracle"
clang -arch x86_64 -O2 -Wall -Wextra "$source_dir/apple.c" -o "$state/apple"
memory_pressure > "$state/memory-pressure.log"
"$PROBE_PY" "$source_dir/qualify.py" --oracle "$state/oracle" --out "$state/qualification"
"$PROBE_PY" "$source_dir/boundaries.py" --oracle "$state/oracle" --out "$state/boundaries.json"
if [ ! -d "$state/mpfr-venv" ]; then python3 -m venv "$state/mpfr-venv"; fi
"$state/mpfr-venv/bin/pip" install gmpy2==2.3.2
"$state/mpfr-venv/bin/python" "$source_dir/sanity.py" --oracle "$state/oracle" --corpus "$state/qualification"
if [ ! -d "$state/aocl" ]; then git clone https://github.com/amd/aocl-libm-ose.git "$state/aocl"; fi
git -C "$state/aocl" checkout --detach 29fd054f383e6c5e2dec2fce781d5220059f1836
python3 "$source_dir/build_amd.py" --source "$state/aocl" --out "$state/amd"
python3 "$source_dir/compare_sample.py" --apple "$state/apple" --amd "$state/amd" --corpus "$state/qualification"
python3 "$source_dir/check_results.py" --actual "$state" --expected "$source_dir/results" --boundaries "$source_dir/results-f27c/boundaries.json"

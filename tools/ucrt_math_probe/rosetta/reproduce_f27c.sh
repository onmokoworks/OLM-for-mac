#!/bin/sh
# Run from the worktree root. All scratch stays in this worktree.
set -eu
state="$PWD/orchestra/state/F27c-ucrt-math-exhaustive"
src="$PWD/tools/ucrt_math_probe/rosetta"
mkdir -p "$state"
export TMPDIR="$state"
: "${PROBE_PY:=/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python}"
memory_pressure > "$state/memory-pressure.log"
for binary in oracle sweep error_state; do
 clang -arch x86_64 -O2 -Wall -Wextra -Wno-deprecated-declarations "$src/$binary.c" -o "$state/$binary"
done
clang -arch x86_64 -O2 -Wall -Wextra "$src/apple.c" -o "$state/apple"
if [ ! -d "$state/aocl" ]; then git clone https://github.com/amd/aocl-libm-ose.git "$state/aocl"; fi
git -C "$state/aocl" checkout --detach 29fd054f383e6c5e2dec2fce781d5220059f1836
python3 "$src/build_amd.py" --source "$state/aocl" --out "$state/amd"
if [ ! -d "$state/mpfr-venv" ]; then python3 -m venv "$state/mpfr-venv"; fi
"$state/mpfr-venv/bin/pip" install gmpy2==2.3.2
"$PROBE_PY" "$src/qualify.py" --oracle "$state/oracle" --out "$state/qualification"
"$PROBE_PY" "$src/boundaries.py" --oracle "$state/oracle" --out "$state/boundaries.json"
"$state/mpfr-venv/bin/python" "$src/qualify_errors.py" --oracle "$state/oracle" --out "$state/error-qualification.json"
"$state/mpfr-venv/bin/python" "$src/sanity.py" --oracle "$state/oracle" --corpus "$state/qualification"
python3 "$src/compare_sample.py" --apple "$state/apple" --amd "$state/amd" --corpus "$state/qualification"
python3 "$src/check_results.py" --actual "$state" --expected "$src/results" --boundaries "$src/results-f27c/boundaries.json"
python3 "$src/check_sweep.py" --state "$state"
"$state/error_state" /Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll
cmp "$state/paper-results.json" "$src/results-f27c/paper-results.json"
"$state/mpfr-venv/bin/python" "$src/check_finite_witnesses.py" --state "$state" --out "$state/finite-witnesses.json"
cmp "$state/finite-witnesses.json" "$src/results-f27c/finite-witnesses.json"
"$state/mpfr-venv/bin/python" "$src/diagnose_sin.py" --state "$state" --out "$state/sin-diagnosis.json"
cmp "$state/sin-diagnosis.json" "$src/results-f27c/sin-diagnosis.json"
"$state/mpfr-venv/bin/python" "$src/diagnose_cos.py" --state "$state" --out "$state/cos-diagnosis.json"
cmp "$state/cos-diagnosis.json" "$src/results-f27c/cos-diagnosis.json"
clang -arch x86_64 -O2 -ffp-contract=off -Wall -Wextra -Wno-deprecated-declarations -I"$state/aocl/src/optimized" "$src/reduction_probe.c" -o "$state/reduction_probe"
"$state/reduction_probe" /Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll > "$state/reduction.csv"
cmp "$state/reduction.csv" "$src/results-f27c/reduction.csv"
# --full opts into the measured exhaustive run. Default validates small evidence.
if [ "${1:-}" = --full ]; then
 for fn in expf sinf cosf atan2f powf; do
  mkdir -p "$state/pilot-$fn"
  "$state/sweep" /Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll "$fn" "$state/amd/amd-off.dylib" "$state/amd/amd-fma.dylib" "$state/pilot-$fn" 16777216 16777216 >> "$state/pilot-$fn.log" 2>&1
 done
 sh "$src/run_sweep.sh" "$state"
 python3 "$src/check_full.py" --actual "$state/full" --expected "$src/results-f27c"
 "$PROBE_PY" "$src/diagnose_pow.py" --state "$state" --out "$state/pow-diagnosis.json"
 cmp "$state/pow-diagnosis.json" "$src/results-f27c/pow-diagnosis.json"
 "$state/mpfr-venv/bin/python" "$src/check_underflow.py" --state "$state" --out "$state/underflow-mpfr.json"
 cmp "$state/underflow-mpfr.json" "$src/results-f27c/underflow-mpfr.json"
fi

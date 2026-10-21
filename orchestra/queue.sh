#!/bin/zsh
# Run tickets sequentially on one engine: orchestra/queue.sh <engine> <model|-> T.. T..
MAIN="/Users/onmk/Documents/Projects/Personal/OLM as"
engine=$1; model=$2; shift 2; [[ $model == - ]] && model=""
for t in "$@"; do
  [[ -f "$MAIN/orchestra/state/$t.meta" ]] && grep -q '^exit' "$MAIN/orchestra/state/$t.meta" && continue
  "$MAIN/orchestra/run.sh" "$t" "$engine" $model
done

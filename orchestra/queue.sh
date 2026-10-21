#!/bin/zsh
# Dynamic queue: orchestra/queue.sh <engine> <model|-> <queue-file> [max-concurrent]
# Runs the first ticket id in the file that has not finished; append lines to add work.
MAIN="/Users/onmk/Documents/Projects/Personal/OLM as"
engine=$1; model=$2; q=$3; limit=${4:-1}; [[ $model == - ]] && model=""
running(){ local n=0; for m in "$MAIN"/orchestra/state/*.meta(N); do read e _ < "$m"; [[ $e == $engine ]] && ! grep -q "^exit" "$m" && ((n++)); done; echo $n; }
while true; do
  (( $(running) >= limit )) && { sleep 60; continue; }
  next=""
  while read -r t; do
    [[ -z $t || $t == \#* ]] && continue
    [[ -f "$MAIN/orchestra/state/$t.meta" ]] && continue  # started or done; delete meta to re-run
    next=$t; break
  done < "$q"
  [[ -z $next ]] && { sleep 120; continue; }
  "$MAIN/orchestra/run.sh" "$next" "$engine" $model &
  sleep 20
done

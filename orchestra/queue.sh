#!/bin/zsh
# Dynamic queue: orchestra/queue.sh <engine> <model|-> <queue-file> [max-concurrent]
# Runs the first ticket id in the file that has not finished; append lines to add work.
MAIN="/Users/onmk/Documents/Projects/Personal/OLM as"
engine=$1; model=$2; q=$3; limit=${4:-1}; [[ $model == - ]] && model=""
running(){ local n=0; for m in "$MAIN"/orchestra/state/*.meta(N); do read e _ < "$m"; [[ $e == $engine ]] && ! grep -q "^exit" "$m" && ((n++)); done; echo $n; }
while true; do
  (( $(running) >= limit )) && { sleep 60; continue; }
  # while an integration ticket runs, start nothing else
  excl=0; for m in "$MAIN"/orchestra/state/I*.meta(N); do grep -q "^exit" "$m" || excl=1; done
  (( excl )) && { sleep 60; continue; }
  # resource gate: keep memory and disk headroom
  memfree=$(memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{gsub("%","",$2);print $2}')
  diskfree=$(df -g "$MAIN" | awk 'NR==2{print $4}')
  if (( ${memfree:-100} < ${MIN_MEM_PCT:-25} || ${diskfree:-999} < ${MIN_DISK_GB:-20} )); then
    echo "$(date +%T) hold: mem ${memfree}% disk ${diskfree}G" >> "$MAIN/orchestra/state/queue-$engine.hold"; sleep 120; continue
  fi
  next=""
  while read -r t; do
    [[ -z $t || $t == \#* ]] && continue
    [[ -f "$MAIN/orchestra/state/$t.meta" ]] && continue  # started or done; delete meta to re-run
    next=$t; break
  done < "$q"
  [[ -z $next ]] && { sleep 120; continue; }
  # integration tickets (I*) run alone: wait until nothing else of any engine runs
  if [[ $next == I* ]]; then
    others=0; for m in "$MAIN"/orchestra/state/*.meta(N); do grep -q "^exit" "$m" || ((others++)); done
    (( others > 0 )) && { sleep 60; continue; }
  fi
  echo "$engine ${model:-default} $(date +%s)" > "$MAIN/orchestra/state/$next.meta"  # claim before launch (avoid double start)
  # own process group per worker so procguard/run.sh can kill the whole subtree; cap user processes
  python3 -c 'import os,sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' "$MAIN/orchestra/run.sh" "$next" "$engine" $model &
  sleep ${LAUNCH_GAP:-240}  # let the new worker ramp up before the memory gate is read again
done

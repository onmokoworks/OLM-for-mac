#!/bin/zsh
# Block until a new drift flag / worker exit / error appears, print it, exit.
cd "/Users/onmk/Documents/Projects/Personal/OLM as"
snap(){ { orchestra/drift.sh; grep -H '^exit' orchestra/state/*.meta 2>/dev/null; grep -lE 'UnknownError|Model not found|^ERROR: \{|auto-rejecting' orchestra/logs/*.log 2>/dev/null | sed 's/^/errors-in /'; } | sort; }
prev=$(snap)
while true; do
  sleep 60; cur=$(snap)
  new=$(comm -13 <(echo "$prev") <(echo "$cur"))
  [[ -n $new ]] && { echo "$new"; exit 0; }
  prev=$cur
done

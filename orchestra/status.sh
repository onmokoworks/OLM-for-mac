#!/bin/zsh
# One compact line per ticket, for the orchestrator. Keep output small.
MAIN="/Users/onmk/Documents/Projects/Personal/OLM as"
now=$(date +%s)
printf "disk_free=%s\n" "$(df -h "$MAIN" | awk 'NR==2{print $4}')"
for meta in "$MAIN"/orchestra/state/*.meta(N); do
  id=${meta:t:r}; wt="$MAIN/worktrees/$id"
  read engine model start < "$meta"
  fin=$(grep '^exit' "$meta" | tail -1)
  state=${fin:-running}
  mins=$(( (now - start) / 60 ))
  rep=$wt/orchestra/reports/$id.md
  st=$( [[ -f $rep ]] && grep -m1 '^status:' "$rep" | cut -c9- || echo "-")
  commits=$(git -C "$wt" rev-list --count HEAD ^codex/public-beta-roi 2>/dev/null || echo 0)
  dirty=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  logsz=$(stat -f %z "$MAIN/orchestra/logs/$id.log" 2>/dev/null || echo 0)
  printf "%-28s %-8s %-28s %4sm %-10s report=%-8s commits=%s dirty=%s log=%sB\n" \
    "$id" "$engine" "${model:-default}" "$mins" "$state" "$st" "$commits" "$dirty" "$logsz"
done

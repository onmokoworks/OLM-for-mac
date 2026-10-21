#!/bin/zsh
# Cheap drift detector: prints only rule violations / red flags per running worker.
MAIN="/Users/onmk/Documents/Projects/Personal/OLM as"
for meta in "$MAIN"/orchestra/state/*.meta(N); do
  id=${meta:t:r}; wt="$MAIN/worktrees/$id"; log="$MAIN/orchestra/logs/$id.log"
  [[ -f $log ]] || continue
  hits=()
  grep -qE '(>|cp |mv |mkdir[^\n]*|write_text\(|open\()[^\n]*/tmp/' "$log" && hits+=("writes-/tmp")
  grep -qE 'git (push|reset --hard|rebase|commit --amend)' "$log" && hits+=("git-history/push")
  git -C "$MAIN" status --porcelain | grep -vqE '^\?\? (orchestra/(logs|state)|worktrees)/' && hits+=("MAIN-dirty")
  changed=$(git -C "$wt" diff --name-only codex/public-beta-roi 2>/dev/null; git -C "$wt" status --porcelain 2>/dev/null | cut -c4-)
  echo "$changed" | grep -qE 'run_olm_release_gate|olm_release_gate_|CONFORMANCE_LEDGER' && hits+=("touches-gate/ledger")
  echo "$changed" | grep -qE '(expected|golden)[^/]*\.(json|bin)$' && hits+=("touches-expected")
  scratch=$(du -sk "$wt/orchestra/state" 2>/dev/null | cut -f1); (( ${scratch:-0} > 5242880 )) && hits+=("scratch>5GiB")
  # repetition: same tool command issued many times recently
  rep=$(tail -c 200000 "$log" | grep -E '^\s*(\$ |bash -lc)' | sort | uniq -c | sort -rn | awk '$1>=8{print $1}' | head -1)
  [[ -n $rep ]] && hits+=("repeating-cmd x$rep")
  (( ${#hits} )) && echo "$id: ${hits[*]}"
done
exit 0

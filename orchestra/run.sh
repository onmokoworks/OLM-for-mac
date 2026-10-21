#!/bin/zsh
# Launch one worker on one ticket in its own worktree.
#   orchestra/run.sh <ticket-id> <opencode|codex> [model]
# Ticket text: orchestra/tickets/<ticket-id>.md
set -u
MAIN="/Users/onmk/Documents/Projects/Personal/OLM as"
id=$1; engine=$2; model=${3:-}
ticket="$MAIN/orchestra/tickets/$id.md"
[[ -f $ticket ]] || { echo "no ticket $ticket"; exit 1; }
wt="$MAIN/worktrees/$id"
mkdir -p "$MAIN/orchestra/logs" "$MAIN/orchestra/state"
if [[ ! -d $wt ]]; then
  git -C "$MAIN" worktree add -q -b "orch/$id" "$wt" HEAD
fi
mkdir -p "$wt/orchestra/state/$id" "$wt/orchestra/reports"
prompt="$(cat "$MAIN/orchestra/BRIEF.md")

# Your ticket: $id
Worktree: $wt

$(cat "$ticket")"
log="$MAIN/orchestra/logs/$id.log"
echo "$engine ${model:-default} $(date +%s)" > "$MAIN/orchestra/state/$id.meta"
cd "$wt"
marg=(); [[ -n $model ]] && marg=(-m "$model")
case $engine in
  opencode)
    # Run one opencode turn with a stall watchdog: kill if the log stops growing for STALL_MIN minutes.
    oc(){ # $1 = extra flags, $2 = prompt
      opencode run --dir "$wt" ${=1} "${marg[@]}" "$2" < /dev/null >> "$log" 2>&1 &
      local pid=$! last=$(stat -f %z "$log") idle=0
      while kill -0 $pid 2>/dev/null; do
        sleep 60; local now=$(stat -f %z "$log")
        if (( now == last )); then (( idle++ )); else idle=0; last=$now; fi
        if (( idle >= ${STALL_MIN:-20} )); then
          echo "[run.sh] stall ${idle}m, killing $pid" >> "$log"; pkill -P $pid; kill $pid; wait $pid; return 124
        fi
      done
      wait $pid
    }
    oc "" "$prompt"; rc=$?
    for attempt in 1 2 3; do
      if [[ $rc -ne 0 ]] && grep -q 'UnknownError\|Model not found' "$log" && (( attempt == 1 )); then
        echo "[run.sh] transient failure, retry" >> "$log"; sleep 30; oc "" "$prompt"; rc=$?; continue
      fi
      [[ -f "$wt/orchestra/reports/$id.md" ]] && break
      echo "[run.sh] no report (rc=$rc), continue $attempt" >> "$log"
      oc "--continue" "You stopped without the required report (or the session stalled). If work remains and you are not blocked, continue the ticket now. In any case, finish by writing and committing orchestra/reports/$id.md in the exact format from the brief."; rc=$?
    done ;;
  codex)    codex exec --dangerously-bypass-approvals-and-sandbox -C "$wt" -c model_reasoning_effort=${EFFORT:-high} "${marg[@]}" "$prompt" < /dev/null > "$log" 2>&1; rc=$? ;;
  *) echo "unknown engine $engine"; exit 1 ;;
esac
echo "exit $rc $(date +%s)" >> "$MAIN/orchestra/state/$id.meta"

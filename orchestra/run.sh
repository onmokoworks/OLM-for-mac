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
# limit runaway process creation: allow ~400 more processes than the user has now
ulimit -u $(( $(ps -axo user= | grep -c "^$(whoami)") + 400 )) 2>/dev/null
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
      if [[ $rc -eq 124 && -n ${FALLBACK_MODELS:-} ]]; then  # stalled: rotate to the next free model
        fb=(${=FALLBACK_MODELS}); nm=${fb[$attempt]:-}; [[ -n $nm ]] && { marg=(-m "$nm"); echo "[run.sh] switching model to $nm" >> "$log"; }
      fi
      echo "[run.sh] no report (rc=$rc), continue $attempt" >> "$log"
      oc "--continue" "You stopped without the required report (or the session stalled). If work remains and you are not blocked, continue the ticket now. In any case, finish by writing and committing orchestra/reports/$id.md in the exact format from the brief."; rc=$?
    done ;;
  codex)
    codex exec --dangerously-bypass-approvals-and-sandbox -C "$wt" -c model_reasoning_effort=${EFFORT:-medium} "${marg[@]}" "$prompt" < /dev/null > "$log" 2>&1; rc=$?
    for attempt in 1 2 3; do
      [[ -f "$wt/orchestra/reports/$id.md" ]] && break
      grep -qE 'routing discovery timed out|Reconnecting\.\.\. 5/5|at capacity|stream disconnected|request timed out' "$log" || break
      echo "[run.sh] codex transient failure, retry $attempt after 120s" >> "$log"; sleep 120
      codex exec --dangerously-bypass-approvals-and-sandbox -C "$wt" -c model_reasoning_effort=${EFFORT:-medium} "${marg[@]}" "$prompt

## Resume
A previous attempt of this ticket was cut off by a network/capacity error. Inspect git status/diff and
orchestra/state/$id/ in this worktree, keep what you can verify, and continue." < /dev/null >> "$log" 2>&1; rc=$?
    done ;;
  *) echo "unknown engine $engine"; exit 1 ;;
esac
echo "exit $rc $(date +%s)" >> "$MAIN/orchestra/state/$id.meta"
# reap anything left in this worker's process group (MCP helpers, timed-out test descendants)
pg=$(ps -o pgid= -p $$ | tr -d " "); [[ -n $pg && $pg -gt 1 ]] && { for p in $(pgrep -g $pg); do [[ $p != $$ ]] && kill -TERM $p 2>/dev/null; done; }

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
case $engine in
  opencode)
    for try in 1 2 3; do
      opencode run --dir "$wt" ${model:+-m $model} "$prompt" < /dev/null >> "$log" 2>&1 && break
      grep -q 'UnknownError\|Model not found' "$log" || break
      echo "[run.sh] transient failure, retry $try" >> "$log"; sleep 30
    done ;;
  codex)    codex exec --dangerously-bypass-approvals-and-sandbox -C "$wt" -c model_reasoning_effort=${EFFORT:-high} ${model:+-m $model} "$prompt" < /dev/null > "$log" 2>&1 ;;
  *) echo "unknown engine $engine"; exit 1 ;;
esac
rc=$?
echo "exit $rc $(date +%s)" >> "$MAIN/orchestra/state/$id.meta"

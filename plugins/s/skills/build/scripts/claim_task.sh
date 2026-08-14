#!/usr/bin/env bash
# claim_task.sh — task coordination for /s:build execution sub-agents.
#
# Improves on a naive grep+sed claimer in three ways:
#   1. Parallel-safe: `claim` takes a mkdir-based lock, so two sub-agents can
#      never grab the same task.
#   2. In-progress state: a claimed task becomes `- [~]` until done, so `next`
#      skips work already owned by another sub-agent.
#   3. Targeted completion: `complete`/`release` act on a specific task ID,
#      not "the first unchecked box", so nobody closes the wrong task.
#
# Task IDs are stable **ordinals**: counting only checkbox lines
# (`- [ ]`, `- [~]`, `- [x]`) top-to-bottom, the Nth such line is task ID N.
# IDs stay stable within a run because tasks are not added/removed mid-run.
#
# Task line conventions (.shipd/planned tasks.md checklists):
#   - [ ] pending      - [~] in progress      - [x] done
# A task's text may carry a parallel group tag `[P<n>]` (see first_ready_line).
#
# Usage (run from the project root, where ./.am lives):
#   claim_task.sh next     <change-name>            # peek: print "ID\tTEXT" of next pending, or nothing
#   claim_task.sh claim    <change-name>            # atomically take next pending -> [~], print "ID\tTEXT"
#   claim_task.sh complete <change-name> [id]       # mark task ID done -> [x]; ID optional if exactly one is in progress
#   claim_task.sh release  <change-name> [id]       # give task ID back -> [ ]; ID optional if exactly one is in progress
#   claim_task.sh status   <change-name>            # print counts: pending/in-progress/done
set -euo pipefail

ACTION="${1:-}"
CHANGE="${2:-}"
ID_ARG="${3:-}"

TASKS=".shipd/planned/${CHANGE}/tasks.md"
LOCK=".shipd/planned/${CHANGE}/.tasks.lock"

die() { echo "Error: $*" >&2; exit 1; }
usage() { echo "Usage: $0 {next|claim|status} <change-name>  |  $0 {complete|release} <change-name> [id]" >&2; exit 2; }

[ -n "$ACTION" ] && [ -n "$CHANGE" ] || usage
[ -f "$TASKS" ] || die "tasks file not found: $TASKS"

# All checkbox lines, in order, one per line as "LINE:REST".
all_checkboxes() { grep -n -- '- \[[ ~x]\]' "$TASKS" || true; }

# First pending line as "LINE:REST" or empty.
first_pending() { grep -nm1 -- '- \[ \]' "$TASKS" || true; }

# Parallel group tags: a task's text may carry an optional `[P<n>]` tag (e.g.
# `- [ ] 2.1 [P2] Add CLI flag`). Tasks sharing a `P` number are mutually
# independent; groups become ready in ascending numeric order. An untagged task
# is a sequential *barrier*: it is ready only when everything before it is done,
# and nothing after it is ready until it is done.
#
# Readiness (per checkbox ordinal T, using current on-disk box states):
#   barrier T : ready iff every task before T (file order) is done.
#   grouped T : ready iff every barrier before T is done AND every task in a
#               strictly-lower group is done.
# A file with no tags is therefore fully sequential — every task is a barrier —
# reproducing the original first-pending behavior.
#
# Print the file line number of the first *ready* pending task, or nothing.
first_ready_line() {
  awk '
    /- \[[ ~x]\]/ {
      ord++
      match($0, /- \[[ ~x]\]/)
      state[ord] = substr($0, RSTART + 3, 1)   # box char: " ", "~", or "x"
      line[ord] = NR
      if (match($0, /\[P[0-9]+\]/)) {
        tag = substr($0, RSTART, RLENGTH)       # e.g. "[P2]"
        grp[ord] = substr(tag, 3, length(tag) - 3) + 0
        isbar[ord] = 0
      } else {
        grp[ord] = 0
        isbar[ord] = 1
      }
    }
    function ready(t,   j) {
      if (isbar[t]) {
        for (j = 1; j < t; j++) if (state[j] != "x") return 0
        return 1
      }
      for (j = 1; j < t; j++) if (isbar[j] && state[j] != "x") return 0
      for (j = 1; j <= n; j++)
        if (!isbar[j] && grp[j] < grp[t] && state[j] != "x") return 0
      return 1
    }
    END {
      n = ord
      for (t = 1; t <= n; t++) {
        if (state[t] != " ") continue
        if (ready(t)) { print line[t]; exit }
      }
    }
  ' "$TASKS"
}

# First *ready* pending line as "LINE:REST" (mirrors first_pending), or empty.
first_ready_pending() {
  local ln rest
  ln="$(first_ready_line)"
  [ -n "$ln" ] || return 0
  rest="$(sed -n "${ln}p" "$TASKS")"
  printf '%s:%s\n' "$ln" "$rest"
}

# Line number for ordinal task ID N (1-based), or empty if out of range.
line_for_id() { # <id>
  all_checkboxes | awk -F: -v n="$1" 'NR==n {print $1}'
}

# Ordinal task ID for a given line number.
id_for_line() { # <line>
  all_checkboxes | awk -F: -v ln="$1" '$1==ln {print NR}'
}

# Bare task text: strip the leading "- [ ] " / "- [~] " / "- [x] " marker.
strip_marker() { sed 's/^- \[[ ~x]\] *//'; }

# Portable checkbox rewrite: set LINE's bracket to TO ('x', '~', or ' ').
set_box() { # <line> <to-char>
  local ln="$1" to="$2"
  sed "${ln}s/- \[[ ~x]\]/- [${to}]/" "$TASKS" > "$TASKS.tmp" && mv "$TASKS.tmp" "$TASKS"
}

# Refuse a mutating verb run from the wrong checkout. If this repo has a branch
# named `change/<change>` and the current checkout is not on it — a different
# branch, or a detached HEAD (empty branch name) — print a refusal naming both
# branches and exit 3. Outside a git checkout, or when no such branch exists, or
# when already on the change branch, this is a no-op, so onboarding sandboxes,
# eval scratch repos, and non-git fixture dirs are unaffected. Read-only verbs
# (`status`, `next`) never call this.
require_change_branch() {
  local want="change/${CHANGE}"
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 0
  git rev-parse --verify --quiet "refs/heads/${want}" >/dev/null 2>&1 || return 0
  local cur
  cur="$(git branch --show-current 2>/dev/null || true)"
  if [ "$cur" != "$want" ]; then
    echo "refusing: current branch '${cur}' is not '${want}' — run from the change's worktree" >&2
    exit 3
  fi
}

acquire_lock() {
  local tries=0
  until mkdir "$LOCK" 2>/dev/null; do
    tries=$((tries + 1))
    [ "$tries" -gt 100 ] && die "could not acquire lock on $TASKS (stale $LOCK?)"
    sleep 0.1
  done
  trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT
}

# Resolve the target line for complete/release when the ID may be omitted:
# an explicit ID wins; otherwise there must be exactly one in-progress task.
resolve_line() { # <id-or-empty>
  local id="$1"
  if [ -n "$id" ]; then
    local ln
    ln="$(line_for_id "$id")"
    [ -n "$ln" ] || die "no task with id $id"
    echo "$ln"
    return
  fi
  local hits count
  hits="$(grep -n -- '- \[~\]' "$TASKS" || true)"
  count="$(printf '%s\n' "$hits" | grep -c . || true)"
  if [ "$count" -eq 1 ]; then
    printf '%s\n' "$hits" | head -1 | cut -d: -f1
  else
    die "$count tasks in progress; pass an explicit id: $0 $ACTION $CHANGE <id>"
  fi
}

case "$ACTION" in
  next)
    hit="$(first_ready_pending)"
    [ -n "$hit" ] || exit 0
    ln="${hit%%:*}"
    printf '%s\t%s\n' "$(id_for_line "$ln")" "$(echo "${hit#*:}" | strip_marker)"
    ;;
  claim)
    require_change_branch
    acquire_lock
    hit="$(first_ready_pending)"
    if [ -z "$hit" ]; then
      # Distinguish "all done" from "pending, but nothing ready yet" (an earlier
      # group or barrier is still in flight). Either way: nothing on stdout.
      if [ -n "$(first_pending)" ]; then
        echo "No ready tasks (waiting on the current group/barrier)." >&2
      else
        echo "No pending tasks." >&2
      fi
      exit 0
    fi
    ln="${hit%%:*}"
    set_box "$ln" "~"
    printf '%s\t%s\n' "$(id_for_line "$ln")" "$(echo "${hit#*:}" | strip_marker)"
    ;;
  complete)
    require_change_branch
    ln="$(resolve_line "$ID_ARG")"
    set_box "$ln" "x"
    echo "Task $(id_for_line "$ln") marked complete."
    ;;
  release)
    require_change_branch
    ln="$(resolve_line "$ID_ARG")"
    set_box "$ln" " "
    echo "Task $(id_for_line "$ln") released."
    ;;
  status)
    p="$(grep -c -- '- \[ \]' "$TASKS" || true)"
    w="$(grep -c -- '- \[~\]' "$TASKS" || true)"
    d="$(grep -c -- '- \[x\]' "$TASKS" || true)"
    echo "pending=$p in_progress=$w done=$d"
    ;;
  *)
    usage
    ;;
esac

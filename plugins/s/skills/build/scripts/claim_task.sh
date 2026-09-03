#!/usr/bin/env bash
# claim_task.sh — task coordination for /s:build execution sub-agents.
#
# Improves on a naive grep+sed claimer in four ways:
#   1. Parallel-safe: `claim` takes a mkdir-based lock, so two sub-agents can
#      never grab the same task.
#   2. In-progress state: a claimed task becomes `- [~]` until done, so `next`
#      skips work already owned by another sub-agent.
#   3. Targeted completion: `complete`/`release` act on a specific task ID,
#      not "the first unchecked box", so nobody closes the wrong task.
#   4. Claim liveness: every claim is stamped with a holder and a timestamp in
#      a sidecar record, `claim --wait` blocks in-shell instead of forcing an
#      agent to poll, `complete`/`release` refuse a task that is not in
#      progress, and `release --stale` reclaims abandoned claims.
#
# Task IDs are stable **ordinals**: counting only checkbox lines
# (`- [ ]`, `- [~]`, `- [x]`) top-to-bottom, the Nth such line is task ID N.
# IDs stay stable within a run because tasks are not added/removed mid-run.
#
# Task line conventions (.shipd/planned tasks.md checklists):
#   - [ ] pending      - [~] in progress      - [x] done
# A task's text may carry a parallel group tag `[P<n>]` (see first_ready_line).
#
# Claim records live beside the tasks file in `.tasks.claims`, one TSV line per
# in-progress task: `id<TAB>holder<TAB>epoch-seconds`. The file is read and
# rewritten only under the same lock that flips the checkbox, and it is deleted
# when its last record goes. `tasks.md`'s own grammar never carries a holder.
#
# Usage (run from the project root, where ./.shipd lives):
#   claim_task.sh next     <change-name>
#       peek: print "ID\tTEXT" of the next ready pending task, or nothing
#   claim_task.sh claim    <change-name> [--as <label>] [--wait [--timeout <secs>]]
#       atomically take the next ready pending task -> [~], print "ID\tTEXT".
#       --as names the claim's holder (default: $CLAUDE_CODE_SESSION_ID, else
#       `anon`). --wait blocks *inside this invocation*, retrying every few
#       seconds until a task is won, nothing is pending, or --timeout seconds
#       (default 600) pass; a timeout prints to stderr and exits 0 with empty
#       stdout, the established "nothing claimed" contract.
#   claim_task.sh complete <change-name> [id] [--as <label>]
#       mark task ID done -> [x]; ID optional if exactly one is in progress
#   claim_task.sh release  <change-name> [id] [--as <label>]
#       give task ID back -> [ ]; ID optional if exactly one is in progress
#   claim_task.sh release  <change-name> --stale <mins>
#       return every claim older than <mins> (and every record-less [~]) to [ ]
#   claim_task.sh status   <change-name> [--stale-after <mins>]
#       print counts, then one `claimed:` line per in-progress task
#
# complete/release refuse a task whose box is not `- [~]`, naming its state, so
# a finished task can never be flipped back to pending. Holder verification is
# soft: they refuse only when the record names a holder AND the caller passed a
# *different* --as label; a bare call acts regardless of the recorded holder.
set -euo pipefail

TAB="$(printf '\t')"

die() { echo "Error: $*" >&2; exit 1; }
usage() {
  cat >&2 <<'EOF'
Usage:
  claim_task.sh next     <change-name>
  claim_task.sh claim    <change-name> [--as <label>] [--wait [--timeout <secs>]]
  claim_task.sh complete <change-name> [id] [--as <label>]
  claim_task.sh release  <change-name> [id] [--as <label>]
  claim_task.sh release  <change-name> --stale <mins>
  claim_task.sh status   <change-name> [--stale-after <mins>]
EOF
  exit 2
}

is_number() { case "${1:-}" in '' | *[!0-9]*) return 1 ;; *) return 0 ;; esac; }

# ---------------------------------------------------------------------------
# Argument parsing: verb first, then the positionals (<change> [id]) and flags
# in any order, so `release <change> 3 --stale 30` and `release --stale 30
# <change>` are both understood (the former as the refused combination).
# ---------------------------------------------------------------------------
ACTION="${1:-}"
[ -n "$ACTION" ] || usage
shift

CHANGE=""
ID_ARG=""
HOLDER_ARG=""
WAIT=0
TIMEOUT=600
STALE_MINS=""
STALE_AFTER=30

while [ $# -gt 0 ]; do
  case "$1" in
    --as)
      [ $# -ge 2 ] || usage
      HOLDER_ARG="$2"; shift 2 ;;
    --wait)
      WAIT=1; shift ;;
    --timeout)
      [ $# -ge 2 ] || usage
      TIMEOUT="$2"; shift 2 ;;
    --stale)
      [ $# -ge 2 ] || usage
      STALE_MINS="$2"; shift 2 ;;
    --stale-after)
      [ $# -ge 2 ] || usage
      STALE_AFTER="$2"; shift 2 ;;
    --)
      shift ;;
    -*)
      echo "unknown flag: $1" >&2; usage ;;
    *)
      if [ -z "$CHANGE" ]; then
        CHANGE="$1"
      elif [ -z "$ID_ARG" ]; then
        ID_ARG="$1"
      else
        echo "unexpected argument: $1" >&2; usage
      fi
      shift ;;
  esac
done

[ -n "$CHANGE" ] || usage
is_number "$TIMEOUT" || die "--timeout expects whole seconds"
is_number "$STALE_AFTER" || die "--stale-after expects whole minutes"
if [ -n "$STALE_MINS" ]; then
  is_number "$STALE_MINS" || die "--stale expects whole minutes"
  if [ "$ACTION" != "release" ]; then
    echo "--stale is only valid for release" >&2; usage
  fi
fi

TASKS=".shipd/planned/${CHANGE}/tasks.md"
LOCK=".shipd/planned/${CHANGE}/.tasks.lock"
CLAIMS=".shipd/planned/${CHANGE}/.tasks.claims"

[ -f "$TASKS" ] || die "tasks file not found: $TASKS"

# The claim holder: an explicit --as label, else the session id, else `anon`.
# Tabs and newlines would corrupt the TSV sidecar, so they are folded to spaces.
HOLDER="${HOLDER_ARG:-${CLAUDE_CODE_SESSION_ID:-anon}}"
HOLDER="$(printf '%s' "$HOLDER" | tr '\t\n' '  ')"

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

# The checkbox character (" ", "~" or "x") on a given file line.
box_at_line() { # <line>
  awk -v ln="$1" 'NR==ln && match($0, /- \[[ ~x]\]/) {
    print substr($0, RSTART + 3, 1); exit
  }' "$TASKS"
}

# Human name for a checkbox character, for refusal messages.
state_name() { # <box-char>
  case "$1" in
    ' ') echo "pending" ;;
    '~') echo "in progress" ;;
    'x') echo "done" ;;
    *) echo "unknown" ;;
  esac
}

# In-progress tasks as "ID<TAB>LINE", in ordinal order.
in_progress_pairs() {
  all_checkboxes | awk -F: -v tab="$TAB" '/- \[~\]/ { print NR tab $1 }'
}

# Bare task text: strip the leading "- [ ] " / "- [~] " / "- [x] " marker.
strip_marker() { sed 's/^- \[[ ~x]\] *//'; }

# Portable checkbox rewrite: set LINE's bracket to TO ('x', '~', or ' ').
set_box() { # <line> <to-char>
  local ln="$1" to="$2"
  sed "${ln}s/- \[[ ~x]\]/- [${to}]/" "$TASKS" > "$TASKS.tmp" && mv "$TASKS.tmp" "$TASKS"
}

# ---------------------------------------------------------------------------
# Claim records (`.tasks.claims`, TSV `id<TAB>holder<TAB>epoch`). Every reader
# and writer below runs under the lock.
# ---------------------------------------------------------------------------
now_epoch() { date +%s; }

claim_field() { # <id> <field-number>
  [ -f "$CLAIMS" ] || return 0
  awk -F'\t' -v id="$1" -v f="$2" '$1 == id { print $f; exit }' "$CLAIMS"
}

claim_holder() { claim_field "$1" 2; }
claim_epoch() { claim_field "$1" 3; }

claim_record_put() { # <id> <holder> <epoch>
  local tmp="$CLAIMS.tmp"
  if [ -f "$CLAIMS" ]; then
    awk -F'\t' -v id="$1" '$1 != id' "$CLAIMS" > "$tmp"
  else
    : > "$tmp"
  fi
  printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$tmp"
  mv "$tmp" "$CLAIMS"
}

claim_record_del() { # <id>
  [ -f "$CLAIMS" ] || return 0
  local tmp="$CLAIMS.tmp"
  awk -F'\t' -v id="$1" '$1 != id' "$CLAIMS" > "$tmp"
  if [ -s "$tmp" ]; then
    mv "$tmp" "$CLAIMS"
  else
    rm -f "$tmp" "$CLAIMS"
  fi
}

# Coarse, human-readable age: "42s", "7m", "2h 5m".
fmt_age() { # <seconds>
  local s="$1"
  if [ "$s" -lt 60 ]; then
    printf '%ds' "$s"
  elif [ "$s" -lt 3600 ]; then
    printf '%dm' "$((s / 60))"
  else
    printf '%dh %dm' "$((s / 3600))" "$(((s % 3600) / 60))"
  fi
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

# Drop the lock explicitly, so a retrying `claim --wait` never sleeps while
# holding it and never double-releases via the EXIT trap.
release_lock() {
  trap - EXIT
  rmdir "$LOCK" 2>/dev/null || true
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

# Soft holder verification: refuse only when the record names a holder AND the
# caller passed a *different* --as label. A bare call acts regardless.
verify_holder() { # <id>
  [ -n "$HOLDER_ARG" ] || return 0
  local recorded
  recorded="$(claim_holder "$1")"
  [ -n "$recorded" ] || return 0
  if [ "$recorded" != "$HOLDER" ]; then
    die "task $1 is held by '$recorded', not '$HOLDER'; refusing to $ACTION"
  fi
}

# One atomic claim attempt: takes and drops the lock itself, so `--wait` can
# call it repeatedly without deadlocking on the EXIT trap.
#   0 = a task was claimed (printed on stdout)
#   2 = pending tasks exist, but none is ready yet (group/barrier in flight)
#   3 = no pending task remains at all
claim_once() {
  local hit ln id
  acquire_lock
  hit="$(first_ready_pending)"
  if [ -z "$hit" ]; then
    local pending
    pending="$(first_pending)"
    release_lock
    [ -n "$pending" ] && return 2
    return 3
  fi
  ln="${hit%%:*}"
  set_box "$ln" "~"
  id="$(id_for_line "$ln")"
  claim_record_put "$id" "$HOLDER" "$(now_epoch)"
  release_lock
  printf '%s\t%s\n' "$id" "$(echo "${hit#*:}" | strip_marker)"
  return 0
}

# Flip one in-progress task to <to-char>, clearing its claim record. Callers
# hold the lock. Refuses any task that is not `- [~]`, naming its state.
finish_task() { # <line> <to-char> <verb>
  local ln="$1" to="$2" verb="$3" id box
  id="$(id_for_line "$ln")"
  box="$(box_at_line "$ln")"
  if [ "$box" != "~" ]; then
    die "task $id is $(state_name "$box"), not in progress; refusing to $verb it"
  fi
  verify_holder "$id"
  set_box "$ln" "$to"
  claim_record_del "$id"
  echo "$id"
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
    if [ "$WAIT" -eq 0 ]; then
      rc=0
      claim_once || rc=$?
      # Distinguish "all done" from "pending, but nothing ready yet" (an earlier
      # group or barrier is still in flight). Either way: nothing on stdout.
      case "$rc" in
        2) echo "No ready tasks (waiting on the current group/barrier)." >&2 ;;
        3) echo "No pending tasks." >&2 ;;
      esac
      exit 0
    fi
    deadline=$(( $(now_epoch) + TIMEOUT ))
    while :; do
      rc=0
      claim_once || rc=$?
      [ "$rc" -eq 0 ] && exit 0
      if [ "$rc" -eq 3 ]; then
        echo "No pending tasks." >&2
        exit 0
      fi
      remaining=$(( deadline - $(now_epoch) ))
      if [ "$remaining" -le 0 ]; then
        echo "wait timed out after ${TIMEOUT}s (waiting on the current group/barrier)." >&2
        exit 0
      fi
      step=5
      [ "$remaining" -lt "$step" ] && step="$remaining"
      sleep "$step"
    done
    ;;
  complete)
    require_change_branch
    acquire_lock
    ln="$(resolve_line "$ID_ARG")"
    id="$(finish_task "$ln" "x" "complete")"
    release_lock
    echo "Task $id marked complete."
    ;;
  release)
    require_change_branch
    if [ -n "$STALE_MINS" ]; then
      if [ -n "$ID_ARG" ]; then
        echo "release: --stale and an explicit task id are mutually exclusive" >&2
        usage
      fi
      acquire_lock
      now="$(now_epoch)"
      threshold=$((STALE_MINS * 60))
      released=0
      pairs="$(in_progress_pairs)"
      if [ -n "$pairs" ]; then
        while IFS="$TAB" read -r id ln; do
          [ -n "$id" ] || continue
          epoch="$(claim_epoch "$id")"
          if [ -n "$epoch" ]; then
            age=$((now - epoch))
            [ "$age" -lt 0 ] && age=0
            if [ "$age" -lt "$threshold" ]; then
              continue
            fi
            who="$(claim_holder "$id")"
            [ -n "$who" ] || who="unknown"
            age_label="$(fmt_age "$age")"
          else
            # A `- [~]` with no record is abandoned by definition.
            who="unknown"
            age_label="unknown"
          fi
          set_box "$ln" " "
          claim_record_del "$id"
          echo "Task $id released (held by $who for $age_label)."
          released=$((released + 1))
        done <<EOF
$pairs
EOF
      fi
      release_lock
      [ "$released" -eq 0 ] && echo "No stale claims."
      exit 0
    fi
    acquire_lock
    ln="$(resolve_line "$ID_ARG")"
    id="$(finish_task "$ln" " " "release")"
    release_lock
    echo "Task $id released."
    ;;
  status)
    p="$(grep -c -- '- \[ \]' "$TASKS" || true)"
    w="$(grep -c -- '- \[~\]' "$TASKS" || true)"
    d="$(grep -c -- '- \[x\]' "$TASKS" || true)"
    echo "pending=$p in_progress=$w done=$d"
    now="$(now_epoch)"
    threshold=$((STALE_AFTER * 60))
    pairs="$(in_progress_pairs)"
    if [ -n "$pairs" ]; then
      while IFS="$TAB" read -r id ln; do
        [ -n "$id" ] || continue
        epoch="$(claim_epoch "$id")"
        if [ -z "$epoch" ]; then
          # Visible, never fatal: a pre-change file or a hand-edited checkbox.
          echo "claimed: $id by unknown age unknown [stale]"
          continue
        fi
        who="$(claim_holder "$id")"
        [ -n "$who" ] || who="unknown"
        age=$((now - epoch))
        [ "$age" -lt 0 ] && age=0
        line="claimed: $id by $who age $(fmt_age "$age")"
        [ "$age" -ge "$threshold" ] && line="$line [stale]"
        echo "$line"
      done <<EOF
$pairs
EOF
    fi
    ;;
  *)
    usage
    ;;
esac

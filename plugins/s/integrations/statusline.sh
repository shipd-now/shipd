#!/usr/bin/env bash
# shipd status line for Claude Code.
# Shows a live spec: name, lifecycle status, and task progress. Scans the
# workspace root's .shipd/planned/ plus one level of .worktrees/*/.shipd/planned/,
# so a change developed inside a worktree still surfaces here.
#
# Input: Claude Code session JSON on stdin (uses workspace.current_dir).
# Output: single line "☕ <name> · <status> · <done>/<total>", with position
#         "(1 of X)" and aggregate "(<total> of <Y>)" brackets when more than
#         one change is live; "☕ no active specs" for an am project with no
#         live change; nothing at all when the workspace has no .shipd/ directory.
#
# Note: macOS ships bash 3.2, so we avoid `mapfile`, `set -u`, associative
# arrays, and `$'\uXXXX'` throughout this script. No Python/Node is spawned.
#
# The default content directory `.shipd` is assumed literally: this script does
# NOT resolve `.shipd-config.json`, so a repo (or worktree) that renames its
# content directory is not scanned (a documented statusline limitation).

# ANSI colors (segment-colored; the " · " separator stays uncolored).
NAME_COLOR=$'\033[94m'   # light blue
RESET=$'\033[0m'

# ☕ = U+2615 HOT BEVERAGE — emoji presentation by default, no variation
# selector needed. Emit the raw UTF-8 bytes ($'\uXXXX' is bash 4.2+ only).
COFFEE=$(printf '\xe2\x98\x95')

# ● = U+25CF BLACK CIRCLE — the breathing live-run dot. Emit raw UTF-8 bytes
# ($'\uXXXX' is bash 4.2+ only). Colored from an 8-step ping-pong ramp of
# xterm-256 greens (light→dark→light) indexed by epoch seconds modulo 8, so
# the dot fades one step per statusline re-render (once per second).
DOT=$(printf '\xe2\x97\x8f')
DOT_RAMP=(46 40 34 28 22 28 34 40)

# Color for a status value (empty string for the default/counts color).
status_color() {
  case "$1" in
    draft)    printf '\033[90m' ;;
    ready)    printf '\033[94m' ;;
    active)   printf '\033[33m' ;;
    complete) printf '\033[32m' ;;
    verified) printf '\033[92m' ;;
    rejected) printf '\033[31m' ;;
    *)        printf '\033[90m' ;;
  esac
}

# Modification time of a file in epoch seconds, or 0 when it cannot be read
# (missing file, or neither stat variant available -> degrade to 0 so the
# pick falls back to candidate order rather than erroring).
#
# Probe GNU `stat -c %Y` first: on BSD/macOS `-c` is an illegal option and
# stdout stays empty, so we fall back to BSD `stat -f %m`. The reverse order
# is unsafe — GNU's `-f` means "filesystem status" (not "format") and prints
# a multi-line block on stdout with exit 0, which would poison the result.
# A final numeric guard forces any non-numeric output to 0.
mtime_of() {
  [ -f "$1" ] || { printf '0'; return; }
  m=$(stat -c %Y "$1" 2>/dev/null)
  if [ -z "$m" ]; then
    m=$(stat -f %m "$1" 2>/dev/null)
  fi
  case "$m" in
    ''|*[!0-9]*) m=0 ;;
  esac
  printf '%s' "$m"
}

# Status header from a change's plan.md ("?" when missing or invalid).
status_of() {
  s="?"
  if [ -f "$1" ]; then
    raw=$(sed -n 's/^Status:[[:space:]]*\([A-Za-z][A-Za-z]*\).*/\1/p' "$1" \
      | head -n 1)
    case "$raw" in
      draft|ready|active|complete|verified|rejected) s="$raw" ;;
      *) s="?" ;;
    esac
  fi
  printf '%s' "$s"
}

# Epic slug from a change's plan.md header (empty when there is no `Epic:`
# line). Same sed idiom as status_of; the slug value itself is not rendered
# (only its presence gates the literal `(EPIC)` marker).
epic_of() {
  e=""
  if [ -f "$1" ]; then
    e=$(sed -n 's/^Epic:[[:space:]]*\([^[:space:]][^[:space:]]*\).*/\1/p' "$1" \
      | head -n 1)
  fi
  printf '%s' "$e"
}

# 1-based position and member count of a change in an epic file's members
# table. Args: epic file path, change name. Filters `^|` table rows, drops
# the `---` separator rows and the header row whose first cell is `Change`,
# then numbers the remaining member rows and, on a first-cell match, prints
# `pos total` (space-separated). Prints nothing on any miss (file absent or
# no matching row). Pure sed/grep/while-read — bash 3.2, no runtimes.
epic_position() {
  ef="$1"; cn="$2"
  [ -f "$ef" ] || return 0
  n=0; hit=0
  while IFS= read -r cell; do
    [ -n "$cell" ] || continue
    n=$((n + 1))
    if [ "$hit" -eq 0 ] && [ "$cell" = "$cn" ]; then
      hit=$n
    fi
  done <<EOF
$(grep '^|' "$ef" | grep -v '^|[[:space:]]*---' \
    | sed -n 's/^|[[:space:]]*//; s/[[:space:]]*|.*//; p' \
    | grep -v '^Change$')
EOF
  [ "$hit" -gt 0 ] || return 0
  printf '%s %s' "$hit" "$n"
}

# True when an autopilot run is live: some heartbeat file under the workspace
# root's `.shipd/autopilot/*-heartbeat.json` has a modification time within 3600 s
# of now (2× the default session budget, so a long silent stage keeps the dot
# while a crashed run's stale file loses it) and records a `running` run state.
# The heartbeat delta pins the value vocabulary (`running`) but not the key
# name, so both `state` and `run_state` are tolerated.
run_is_live() {
  now=$(date +%s)
  for f in "$workspace"/.shipd/autopilot/*-heartbeat.json; do
    [ -f "$f" ] || continue
    age=$((now - $(mtime_of "$f")))
    [ "$age" -le 3600 ] || continue
    if grep -Eq '"(run_)?state"[[:space:]]*:[[:space:]]*"running"' "$f"; then
      return 0
    fi
  done
  return 1
}

# Read stdin JSON and extract workspace.current_dir.
input=$(cat)
workspace=$(printf '%s' "$input" | sed -n 's/.*"current_dir"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)

# Fallback to current working directory if stdin didn't provide one.
if [ -z "$workspace" ]; then
  workspace="$PWD"
fi

# An am project is any workspace carrying a `.shipd/` directory. Without one the
# statusline stays silent (non-am repo); with one it always reports.
if [ ! -d "$workspace/.shipd" ]; then
  exit 0
fi

# --- Collect candidate changes -------------------------------------------
# Parallel arrays (bash 3.2: no associative arrays). Candidates come from the
# root's .shipd/planned/ plus one level of .worktrees/*/.shipd/planned/.
cand_dir=()
cand_name=()
cand_status=()
cand_epic=()
cand_is_root=()
cand_has_tasks=()
cand_done=()
cand_total=()
cand_mtime=()

add_candidate() {
  d="$1"; is_root="$2"
  [ -d "$d" ] || return
  name=$(basename "$d")
  st=$(status_of "$d/plan.md")
  ep=$(epic_of "$d/plan.md")
  tasks="$d/tasks.md"
  have=0; dn=0; tot=0; mt=0
  if [ -f "$tasks" ]; then
    have=1
    dn=$(grep -cE '^[[:space:]]*- \[x\]' "$tasks" 2>/dev/null)
    tot=$(grep -cE '^[[:space:]]*- \[( |x|~)\]' "$tasks" 2>/dev/null)
    [ -z "$dn" ] && dn=0
    [ -z "$tot" ] && tot=0
    mt=$(mtime_of "$tasks")
  fi
  i=${#cand_dir[@]}
  cand_dir[$i]="$d"
  cand_name[$i]="$name"
  cand_status[$i]="$st"
  cand_epic[$i]="$ep"
  cand_is_root[$i]="$is_root"
  cand_has_tasks[$i]="$have"
  cand_done[$i]="$dn"
  cand_total[$i]="$tot"
  cand_mtime[$i]="$mt"
}

for d in "$workspace"/.shipd/planned/*/; do
  add_candidate "$d" 1
done
for d in "$workspace"/.worktrees/*/.shipd/planned/*/; do
  add_candidate "$d" 0
done

X=${#cand_dir[@]}

# An am project with no live change reports rather than vanishing.
if [ "$X" -eq 0 ]; then
  printf '%s no active specs\n' "$COFFEE"
  exit 0
fi

# --- Pick the change that owns the line ----------------------------------
pick=-1

# (1)/(2) prefer an active change anywhere, newest tasks.md mtime wins ties.
best_mt=-1
i=0
while [ "$i" -lt "$X" ]; do
  if [ "${cand_status[$i]}" = "active" ]; then
    if [ "${cand_mtime[$i]}" -gt "$best_mt" ]; then
      best_mt=${cand_mtime[$i]}
      pick=$i
    fi
  fi
  i=$((i + 1))
done

# (3) no active: fall back to the root's recorded selection when it resolves
# to a root candidate.
if [ "$pick" -lt 0 ]; then
  state_file="$workspace/.shipd/state.json"
  if [ -f "$state_file" ]; then
    selected=$(sed -n 's/.*"current_spec"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$state_file" | head -n 1)
    if [ -n "$selected" ]; then
      i=0
      while [ "$i" -lt "$X" ]; do
        if [ "${cand_is_root[$i]}" = "1" ] \
          && [ "${cand_name[$i]}" = "$selected" ]; then
          pick=$i
          break
        fi
        i=$((i + 1))
      done
    fi
  fi
fi

# (4) a sole candidate overall.
if [ "$pick" -lt 0 ] && [ "$X" -eq 1 ]; then
  pick=0
fi

# (5) several candidates, none pickable.
if [ "$pick" -lt 0 ]; then
  printf '%s %s specs %s none selected\n' "$COFFEE" "$X" "·"
  exit 0
fi

# --- Aggregate task total across all task-bearing candidates -------------
Y=0
i=0
while [ "$i" -lt "$X" ]; do
  if [ "${cand_has_tasks[$i]}" -eq 1 ]; then
    Y=$((Y + ${cand_total[$i]}))
  fi
  i=$((i + 1))
done

# --- Render ---------------------------------------------------------------
name="${cand_name[$pick]}"
status="${cand_status[$pick]}"
epic="${cand_epic[$pick]}"
have_tasks="${cand_has_tasks[$pick]}"
done_count="${cand_done[$pick]}"
total_count="${cand_total[$pick]}"

sep=" · "
# The epic marker sits between the name and any `(1 of X)` position bracket.
# On an Epic header, resolve the epic file relative to the picked candidate's
# own content dir (its dir always ends `/planned/<name>/`) and render the
# change's table position `(EPIC: <slug>, spec <pos>/<total>)`; a missing epic
# file or a change absent from the table degrades to the bare `(EPIC)`.
name_seg="$name"
if [ -n "$epic" ]; then
  d="${cand_dir[$pick]}"
  base="${d%/planned/"$name"/}"
  epic_file="$base/epics/$epic/epic.md"
  pos_total=$(epic_position "$epic_file" "$name")
  if [ -n "$pos_total" ]; then
    pos="${pos_total% *}"
    total="${pos_total#* }"
    name_seg="$name_seg (EPIC: $epic, spec $pos/$total)"
  else
    name_seg="$name_seg (EPIC)"
  fi
fi
if [ "$X" -gt 1 ]; then
  name_seg="$name_seg (1 of $X)"
fi
out="${NAME_COLOR}${name_seg}${RESET}"
scolor=$(status_color "$status")
# The dot lives inside the status segment (after the uncolored " · ") so the
# separators stay uncolored; its green is independent of the status color.
if [ "$status" = "active" ] && run_is_live; then
  n=$(( $(date +%s) % 8 ))
  dcolor=$(printf '\033[38;5;%sm' "${DOT_RAMP[$n]}")
  out="${out}${sep}${dcolor}${DOT}${RESET} ${scolor}${status}${RESET}"
else
  out="${out}${sep}${scolor}${status}${RESET}"
fi
if [ "$have_tasks" -eq 1 ]; then
  tasks_seg="${done_count}/${total_count}"
  if [ "$X" -gt 1 ]; then
    tasks_seg="${tasks_seg} (${total_count} of ${Y})"
  fi
  out="${out}${sep}${tasks_seg}"
fi

printf '%s %s\n' "$COFFEE" "$out"

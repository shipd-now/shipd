#!/usr/bin/env bash
# shipd status line for Claude Code.
# Shows a live spec: name, lifecycle status, and task progress. Scans the
# resolved content directory's planned/ plus, with no store, one level of
# .worktrees/*/<dir>/planned/, so a change developed inside a worktree still surfaces here.
#
# Input: Claude Code session JSON on stdin (uses workspace.current_dir).
# Arguments (all optional, any order):
#   --line <seg>[,<seg>...]  declare one output line (repeatable); segments are
#                            spec, directory, context, joined by " · ". The
#                            first printed line carries the "☕ " prefix. With
#                            no --line the layout is one line "spec,context".
#   --then <command>         after shipd's own output (on every exit path,
#                            including the no-content-directory one) run
#                            <command> through `bash -c` with the same session
#                            JSON on stdin, so the user's own statusline
#                            follows ours.
#   --print-content-dir      print only the resolved content directory (or
#                            nothing) and exit 0; used by `shipd doctor` to
#                            compare against the engine's folder.
#
# Segments:
#   spec       "<name> · <status> · <done>/<total>", with position "(1 of X)"
#              and aggregate "(<total> of <Y>)" brackets when more than one
#              change is live; "no active specs" for a shipd project with no
#              live change; "<n> specs · none selected" when none is pickable;
#              "no specs" when no content directory resolves.
#   directory  workspace relative to ~ (uncolored).
#   context    "<bar> <pct>%" from context_window.used_percentage, a four-cell
#              █/░ bar (uncolored); empty when the session JSON has none.
# Empty segments are skipped; a line with no segments is not printed.
#
# Content directory: resolved from the session directory W the way the engine
# does, with local file reads only. `.shipd-config.json` is read in W and each
# ancestor (nearest declaring file wins per key) then ~/.shipd-config.json:
# `store_root` (a leading ~ expands; a relative value joins the declaring
# file's directory) and `dir` (default .shipd). The main checkout comes from
# the nearest `.git` (a linked worktree's `.git` file names it). With a store
# the content directory is the first existing of <store>/<main checkout
# relative to the registry root> and <store>/<main checkout basename>; without
# one it is W/<dir>. Nothing resolving prints "no specs".
#
# Note: macOS ships bash 3.2, so we avoid `mapfile`, `set -u`, associative
# arrays, and `$'\uXXXX'` throughout this script. No Python/Node is spawned.
#
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
# resolved content directory's `autopilot/*-heartbeat.json` has a modification time within 3600 s
# of now (2× the default session budget, so a long silent stage keeps the dot
# while a crashed run's stale file loses it) and records a `running` run state.
# The heartbeat delta pins the value vocabulary (`running`) but not the key
# name, so both `state` and `run_state` are tolerated.
run_is_live() {
  now=$(date +%s)
  for f in "$C"/autopilot/*-heartbeat.json; do
    [ -f "$f" ] || continue
    age=$((now - $(mtime_of "$f")))
    [ "$age" -le 3600 ] || continue
    if grep -Eq '"(run_)?state"[[:space:]]*:[[:space:]]*"running"' "$f"; then
      return 0
    fi
  done
  return 1
}

# Arguments: repeatable --line <segs> and --then <command>. Anything else is
# shifted past. No --line means the default single line "spec,context".
lines=()
chain=""
print_cd=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --line)
      if [ "$#" -ge 2 ]; then lines[${#lines[@]}]="$2"; shift; fi ;;
    --then)
      if [ "$#" -ge 2 ]; then chain="$2"; shift; fi ;;
    --print-content-dir)
      print_cd=1 ;;
  esac
  shift
done
if [ "${#lines[@]}" -eq 0 ]; then
  lines[0]="spec,context"
fi

# Read stdin JSON and extract workspace.current_dir.
input=$(cat)

# Run the chained command (the user's own statusline) after shipd's output,
# with the same session JSON on stdin. Installed as an EXIT trap so every
# `exit` path runs it, including the silent non-shipd one.
run_chain() {
  if [ -n "$chain" ]; then
    printf '%s' "$input" | bash -c "$chain"
  fi
}
trap run_chain EXIT
workspace=$(printf '%s' "$input" | sed -n 's/.*"current_dir"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)

# Fallback to current working directory if stdin didn't provide one.
if [ -z "$workspace" ]; then
  workspace="$PWD"
fi

# --- Content-directory resolution ------------------------------------------
# Value of a top-level-looking JSON string key in a file (first match).
read_key() {
  sed -n 's/.*"'"$2"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$1" 2>/dev/null \
    | head -n 1
}

# Fold one config file (args: file, its directory) into the nearest-wins
# settings: store_root (with its declaring directory), dir, registry root.
scan_config() {
  cf="$1"; cfd="$2"
  if [ -z "$cfg_store" ]; then
    v=$(read_key "$cf" store_root)
    if [ -n "$v" ]; then cfg_store="$v"; cfg_store_base="$cfd"; fi
  fi
  if [ -z "$cfg_dir" ]; then
    cfg_dir=$(read_key "$cf" dir)
  fi
  if [ -z "$cfg_reg" ] \
    && grep -Eq '"workspace"[[:space:]]*:[[:space:]]*\{' "$cf" 2>/dev/null; then
    cfg_reg="$cfd"
  fi
}

# Set C to the resolved content directory (empty when none resolves).
resolve_content_dir() {
  C=""
  cfg_store=""; cfg_store_base=""; cfg_dir=""; cfg_reg=""
  home_seen=0
  wd="${workspace%/}"
  [ -n "$wd" ] || wd="/"
  d="$wd"
  while :; do
    [ "$d" = "$HOME" ] && home_seen=1
    if [ "$d" = "/" ]; then cf="/.shipd-config.json"; else cf="$d/.shipd-config.json"; fi
    [ -f "$cf" ] && scan_config "$cf" "$d"
    [ "$d" = "/" ] && break
    nd="${d%/*}"
    [ -n "$nd" ] || nd="/"
    [ "$nd" = "$d" ] && break
    d="$nd"
  done
  if [ "$home_seen" -eq 0 ] && [ -n "$HOME" ] && [ -f "$HOME/.shipd-config.json" ]; then
    scan_config "$HOME/.shipd-config.json" "$HOME"
  fi

  if [ -z "$cfg_store" ]; then
    cd_name="${cfg_dir:-.shipd}"
    if [ -d "$wd/$cd_name" ]; then C="$wd/$cd_name"; fi
    return 0
  fi

  # Store path: expand a leading ~, join a relative value onto its file's dir.
  store="$cfg_store"
  case "$store" in
    "~")   store="$HOME" ;;
    "~/"*) store="$HOME/${store#"~/"}" ;;
  esac
  case "$store" in
    /*) ;;
    *)  store="$cfg_store_base/$store" ;;
  esac
  while [ "${#store}" -gt 1 ] && [ "${store%/}" != "$store" ]; do
    store="${store%/}"
  done

  # Main checkout: nearest .git directory, or the .git file's main checkout.
  main=""
  d="$wd"
  while :; do
    if [ -d "$d/.git" ]; then
      main="$d"; break
    elif [ -f "$d/.git" ]; then
      gl=""
      IFS= read -r gl < "$d/.git" 2>/dev/null
      gl="${gl#gitdir: }"
      case "$gl" in
        */.git/worktrees/*) main="${gl%/.git/worktrees/*}" ;;
        *) main="$d" ;;
      esac
      break
    fi
    [ "$d" = "/" ] && break
    nd="${d%/*}"
    [ -n "$nd" ] || nd="/"
    [ "$nd" = "$d" ] && break
    d="$nd"
  done
  [ -n "$main" ] || main="$wd"

  if [ -n "$cfg_reg" ]; then
    case "$main" in
      "$cfg_reg"/*)
        rel="${main#"$cfg_reg"/}"
        if [ -d "$store/$rel" ]; then C="$store/$rel"; return 0; fi ;;
    esac
  fi
  if [ -d "$store/${main##*/}" ]; then C="$store/${main##*/}"; fi
  return 0
}

if [ "$print_cd" -eq 1 ]; then
  chain=""
  resolve_content_dir
  [ -n "$C" ] && printf '%s\n' "$C"
  exit 0
fi
resolve_content_dir

# --- Trailing segments: directory relative to ~, and context-usage bar -----
dir_seg="$workspace"
if [ -n "$HOME" ]; then
  if [ "$workspace" = "$HOME" ]; then
    dir_seg="~"
  elif [ "${workspace#"$HOME"/}" != "$workspace" ]; then
    dir_seg="~/${workspace#"$HOME"/}"
  fi
fi
ctx_seg=""

# used_percentage: integer part only (a fractional value truncates, null never
# matches), clamped to 100. The bar fills round(pct * 4 / 100) cells; glyphs
# are raw UTF-8 bytes ($'\uXXXX' is bash 4.2+ only).
ctx_pct=$(printf '%s' "$input" | sed -n 's/.*"used_percentage"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' | head -n 1)
if [ -n "$ctx_pct" ]; then
  ctx_pct=$((10#$ctx_pct))
  [ "$ctx_pct" -gt 100 ] && ctx_pct=100
  filled=$(( (ctx_pct * 4 + 50) / 100 ))
  bar=""
  c=0
  while [ "$c" -lt 4 ]; do
    if [ "$c" -lt "$filled" ]; then
      bar="${bar}$(printf '\xe2\x96\x88')"
    else
      bar="${bar}$(printf '\xe2\x96\x91')"
    fi
    c=$((c + 1))
  done
  if [ "$ctx_pct" -gt 95 ]; then
    ctx_color=$'\033[38;5;124m'
  elif [ "$ctx_pct" -gt 90 ]; then
    ctx_color=$'\033[38;5;160m'
  elif [ "$ctx_pct" -gt 75 ]; then
    ctx_color=$'\033[38;5;196m'
  elif [ "$ctx_pct" -gt 50 ]; then
    ctx_color=$'\033[38;5;208m'
  else
    ctx_color="$NAME_COLOR"
  fi
  ctx_seg="${ctx_color}${bar} ${ctx_pct}%${RESET}"
fi

# Print the layout: per --line, map segment names to their text, skip empty
# and unknown ones, join with " · ", skip an empty line, and prefix the first
# printed line with the coffee cup.
render_lines() {
  printed=0
  for spec_line in "${lines[@]}"; do
    joined=""
    IFS=',' read -r -a segs <<EOF
$spec_line
EOF
    for seg in "${segs[@]}"; do
      case "$seg" in
        spec)      text="$spec_seg" ;;
        directory) text="$dir_seg" ;;
        context)   text="$ctx_seg" ;;
        *)         text="" ;;
      esac
      [ -n "$text" ] || continue
      if [ -n "$joined" ]; then
        joined="${joined} · ${text}"
      else
        joined="$text"
      fi
    done
    [ -n "$joined" ] || continue
    if [ "$printed" -eq 0 ]; then
      printf '%s %s\n' "$COFFEE" "$joined"
      printed=1
    else
      printf '%s\n' "$joined"
    fi
  done
}

# No content directory resolves: report rather than vanishing.
if [ -z "$C" ]; then
  spec_seg="no specs"
  render_lines
  exit 0
fi

# --- Collect candidate changes -------------------------------------------
# Parallel arrays (bash 3.2: no associative arrays). Candidates come from the
# resolved content directory's planned/ plus, with no store, one level of
# .worktrees/*/<dir>/planned/.
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

for d in "$C"/planned/*/; do
  add_candidate "$d" 1
done
if [ -z "$cfg_store" ]; then
  for d in "${workspace%/}"/.worktrees/*/"${cfg_dir:-.shipd}"/planned/*/; do
    add_candidate "$d" 0
  done
fi

X=${#cand_dir[@]}

# A shipd project with no live change reports rather than vanishing.
if [ "$X" -eq 0 ]; then
  spec_seg="no active specs"
  render_lines
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
  state_file="$C/state.json"
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
  spec_seg="$X specs · none selected"
  render_lines
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

spec_seg="$out"
render_lines
exit 0

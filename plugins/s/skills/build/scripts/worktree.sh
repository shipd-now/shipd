#!/usr/bin/env bash
# worktree.sh — create/remove an isolated git worktree + branch for one change.
#
# The workflow is: one change = one worktree = one branch = one PR. This script
# creates `.worktrees/<change>` on branch `change/<change>`; the whole am
# lifecycle (plan -> build -> merge/archive) runs there so artifacts,
# implementation, and spec promotion travel in a single PR.
#
# It also provides `remove <change>`, a *guarded* teardown: removal refuses
# (exit 2, listing every reason) while the worktree shows work in progress —
# uncommitted/untracked files, an unshipped change under `.shipd/planned/`, a
# `[~]` task claim or `.tasks.lock` in a planned checklist, or any file
# modified within the idle window (default 30 minutes,
# `SHIPD_WORKTREE_IDLE_MINUTES` overrides; `0` disables the activity guard). This
# stops a parallel session from pruning a worktree out from under a live one.
# `--force` performs the removal anyway, printing each guard it overrode.
#
# Shipped as a plugin engine script — invocable by plugin path from any git
# repository. It assumes nothing about the repository beyond git itself: no am
# layout, content directory, or host-repo convention is required.
#
# Usage (run from the repository root):
#   <plugin>/skills/build/scripts/worktree.sh <change-name>
#   <plugin>/skills/build/scripts/worktree.sh remove <change-name> [--force]
#
# Bash 3.2-safe (macOS system bash): no mapfile, no associative arrays.
set -e

usage() {
  echo "usage: worktree.sh <change-name>              # create .worktrees/<change-name>" >&2
  echo "       worktree.sh remove <change> [--force]  # guarded removal + prune" >&2
  echo "  <change-name> must be kebab-case (lowercase letters, digits, hyphens)" >&2
}

# --- remove verb ------------------------------------------------------------
#
# Guards run in order dirty -> unshipped -> claims/lock -> recent activity,
# accumulating every failing reason into one refusal report (never
# first-failure-only — the human should see the whole picture). Exit codes
# mirror the gate engine: 0 removed, 2 refused, 1 usage/error.
cmd_remove() {
  CHANGE="${1:-}"
  [ $# -gt 0 ] && shift
  FORCE=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --force) FORCE=1 ;;
      *) echo "error: unknown argument '$1'" >&2; usage; return 1 ;;
    esac
    shift
  done

  if [ -z "$CHANGE" ]; then
    usage
    return 1
  fi

  # Same kebab-case rule as the create path: names never contain slashes, so
  # `remove ../foo` cannot resolve a path outside `.worktrees/`.
  if ! printf '%s' "$CHANGE" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$'; then
    echo "error: '$CHANGE' is not kebab-case (lowercase letters, digits, hyphens)" >&2
    return 1
  fi

  # Must run from the repository root: it has a real `.git` directory.
  if [ ! -d ".git" ]; then
    echo "error: run this from the repo root (no .git directory here)" >&2
    return 1
  fi

  WORKTREE=".worktrees/$CHANGE"
  if [ ! -d "$WORKTREE" ]; then
    echo "error: no worktree at $WORKTREE" >&2
    return 1
  fi

  IDLE="${SHIPD_WORKTREE_IDLE_MINUTES:-30}"
  case "$IDLE" in
    ''|*[!0-9]*)
      echo "error: SHIPD_WORKTREE_IDLE_MINUTES must be a non-negative integer" >&2
      return 1 ;;
  esac

  reasons=()

  # 1. Dirty tree: any uncommitted or untracked path.
  if [ -n "$(git -C "$WORKTREE" status --porcelain 2>/dev/null)" ]; then
    reasons+=("dirty worktree: uncommitted or untracked files")
  fi

  planned="$WORKTREE/.shipd/planned"

  # 2. Unshipped changes still parked under .shipd/planned/.
  if [ -d "$planned" ]; then
    for d in "$planned"/*/; do
      [ -d "$d" ] || continue
      reasons+=("unshipped change under .shipd/planned: ${d%/}")
    done
  fi

  # 3. Coordination in progress: a `[~]` task claim or a `.tasks.lock`.
  if [ -d "$planned" ]; then
    for t in "$planned"/*/tasks.md; do
      [ -f "$t" ] || continue
      if grep -q -- '- \[~\]' "$t" 2>/dev/null; then
        reasons+=("in-progress task claim ([~]) in $t")
      fi
    done
    for l in "$planned"/*/.tasks.lock; do
      [ -e "$l" ] || continue
      reasons+=("coordination lock present: $l")
    done
  fi

  # 4. Recent activity inside the idle window (skipped when IDLE=0). The probe
  # is `find -mmin`, which both GNU and BSD (macOS) find implement — unlike
  # `-newermt`/`-quit`, whose grammar/availability differs across find flavors.
  # `| head -n1` stops the walk at the first hit without the GNU-only `-quit`.
  if [ "$IDLE" -gt 0 ]; then
    hit=$(find "$WORKTREE" -mmin "-$IDLE" -print 2>/dev/null | head -n 1 || true)
    if [ -n "$hit" ]; then
      reasons+=("file modified within the idle window (last $IDLE minutes): $hit")
    fi
  fi

  if [ "${#reasons[@]}" -gt 0 ]; then
    if [ "$FORCE" -eq 1 ]; then
      echo "worktree remove --force $WORKTREE: overriding guard(s):" >&2
      for r in "${reasons[@]}"; do
        echo "  - overriding: $r" >&2
      done
    else
      echo "refusing to remove $WORKTREE — work in progress:" >&2
      for r in "${reasons[@]}"; do
        echo "  - $r" >&2
      done
      echo "Resolve the above and retry, or pass --force to override." >&2
      return 2
    fi
  fi

  if [ "$FORCE" -eq 1 ]; then
    git worktree remove --force "$WORKTREE"
  else
    git worktree remove "$WORKTREE"
  fi
  git worktree prune
  echo "Removed worktree $WORKTREE."
}

# Subcommand dispatch: `remove` is the only verb; any other first argument is a
# change name for the create path (backward compatible).
if [ "${1:-}" = "remove" ]; then
  shift
  cmd_remove "$@"
  exit $?
fi

# --- create path ------------------------------------------------------------
NAME="${1:-}"

if [ -z "$NAME" ]; then
  usage
  exit 1
fi

# Must run from the repository root: it has a real `.git` directory.
if [ ! -d ".git" ]; then
  echo "error: run this from the repo root (no .git directory here)" >&2
  exit 1
fi

# Enforce kebab-case: lowercase letters/digits in hyphen-separated segments.
case "$NAME" in
  -*|*-) echo "error: '$NAME' is not kebab-case (no leading/trailing hyphen)" >&2; exit 1 ;;
esac
if ! printf '%s' "$NAME" | grep -Eq '^[a-z0-9]+(-[a-z0-9]+)*$'; then
  echo "error: '$NAME' is not kebab-case (lowercase letters, digits, hyphens)" >&2
  exit 1
fi

WORKTREE=".worktrees/$NAME"
BRANCH="change/$NAME"

# Idempotent by default (no opt-in flag): a caller should never need to test
# for an existing worktree before invoking this script. Resolution, in order:
#   worktree exists on $BRANCH        -> reuse, unchanged, exit 0
#   worktree exists on another branch -> refuse, change nothing, exit non-zero
#   worktree absent, branch exists    -> attach a worktree to that branch
#   worktree absent, branch absent    -> create both (today's original behavior)
REUSED=0

if [ -e "$WORKTREE" ]; then
  CURRENT_BRANCH=$(git -C "$WORKTREE" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  if [ "$CURRENT_BRANCH" = "$BRANCH" ]; then
    REUSED=1
  else
    echo "error: $WORKTREE already exists on branch '$CURRENT_BRANCH', not $BRANCH" >&2
    exit 1
  fi
elif git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git worktree add "$WORKTREE" "$BRANCH"
else
  git worktree add "$WORKTREE" -b "$BRANCH"
fi

if [ "$REUSED" -eq 1 ]; then
  echo
  echo "(reusing existing worktree)"
fi

cat <<EOF

Created worktree $WORKTREE on branch $BRANCH.

Next steps:
  cd $WORKTREE
  # run the am lifecycle here (/s:plan -> /s:build, including merge/archive)
  # then ship it as a PR:
  git push -u origin $BRANCH
  gh pr create --fill
  gh pr merge --auto --squash --delete-branch
EOF

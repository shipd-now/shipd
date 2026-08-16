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
# The create path is idempotent and says so out loud: reusing a worktree or
# re-attaching an existing branch prints an explicit notice with the branch's
# ahead/behind counts against the base branch (the root checkout's checked-out
# branch), so a stale branch is never mistaken for a fresh one. `--fresh` opts
# out of that reuse entirely — it refuses an existing worktree or an unmerged
# branch, and recreates a branch whose content already reached the base.
#
# `prune-branches` reclaims the other side of the workflow: local `change/*`
# branches whose content already landed on the base branch, which a
# squash-merged PR leaves behind because it deletes only the remote branch.
#
# Usage (run from the repository root):
#   <plugin>/skills/build/scripts/worktree.sh <change-name> [--fresh]
#   <plugin>/skills/build/scripts/worktree.sh remove <change-name> [--force]
#   <plugin>/skills/build/scripts/worktree.sh prune-branches
#
# Bash 3.2-safe (macOS system bash): no mapfile, no associative arrays.
set -e

usage() {
  echo "usage: worktree.sh <change-name> [--fresh]    # create .worktrees/<change-name>" >&2
  echo "       worktree.sh remove <change> [--force]  # guarded removal + prune" >&2
  echo "       worktree.sh prune-branches             # delete merged local change/* branches" >&2
  echo "  <change-name> must be kebab-case (lowercase letters, digits, hyphens)" >&2
  echo "  --fresh: never adopt an existing worktree or unmerged branch" >&2
}

# --- base branch helpers ----------------------------------------------------
#
# The base branch is the root checkout's currently checked-out branch, resolved
# once. `origin/HEAD` is deliberately not consulted: the helper assumes nothing
# about the repository beyond git itself, so there may be no remote at all. A
# detached root HEAD resolves to the empty string — the reuse notice then omits
# its counts, and any verb that must judge merged-ness errors out.
resolve_base_branch() {
  git symbolic-ref -q --short HEAD 2>/dev/null || true
}

# Ahead/behind of a branch against the base, printed as `ahead N, behind M`.
# `git rev-list --left-right --count <base>...<branch>` prints "<behind>\t<ahead>".
# Prints nothing when no base is known or either ref is missing.
branch_counts() {
  local base="$1" branch="$2" counts
  [ -n "$base" ] || return 0
  counts=$(git rev-list --left-right --count "$base...$branch" 2>/dev/null) || return 0
  [ -n "$counts" ] || return 0
  set -- $counts
  [ $# -eq 2 ] || return 0
  printf 'ahead %s, behind %s' "$2" "$1"
}

# Is a branch's *content* already in the base? True (exit 0) when the branch is
# an ancestor of the base, or when the base already carries an equivalent
# patch. That second probe is what `git branch --merged` cannot do: a squash
# merge — how every PR here lands — leaves no ancestry, so ancestry alone would
# call a fully shipped branch unmerged. It replays the branch's tree as a
# throwaway commit on the merge base and asks `git cherry` whether the base
# already has that patch (a leading `-`). The probe commit is unreferenced and
# is garbage-collected; no ref is touched. No base or no merge base at all
# means not merged.
branch_is_merged() {
  local base="$1" branch="$2" ancestor tree probe cherry
  [ -n "$base" ] || return 1
  if git merge-base --is-ancestor "$branch" "$base" 2>/dev/null; then
    return 0
  fi
  ancestor=$(git merge-base "$base" "$branch" 2>/dev/null) || return 1
  [ -n "$ancestor" ] || return 1
  tree=$(git rev-parse "$branch^{tree}" 2>/dev/null) || return 1
  probe=$(git commit-tree "$tree" -p "$ancestor" -m probe 2>/dev/null) || return 1
  cherry=$(git cherry "$base" "$probe" 2>/dev/null) || return 1
  case "$cherry" in
    -*) return 0 ;;
  esac
  return 1
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

# --- prune-branches verb ----------------------------------------------------
#
# A squash-merged PR deletes only the *remote* branch, so merged `change/*`
# branches pile up in the local checkout with nothing to reclaim them. This
# verb deletes exactly those: content already in the base (the same
# content-based probe `--fresh` uses), never a branch checked out in any
# worktree, never anything outside `change/*`. `git branch -d` is deliberately
# not used — it judges by ancestry alone and so cannot see the squash merges
# that are the whole problem. Every candidate is reported, pruned or kept, and
# the verb exits 0 whether or not anything was deleted.
cmd_prune_branches() {
  if [ $# -gt 0 ]; then
    echo "error: unknown argument '$1'" >&2
    usage
    return 1
  fi

  # Must run from the repository root: it has a real `.git` directory.
  if [ ! -d ".git" ]; then
    echo "error: run this from the repo root (no .git directory here)" >&2
    return 1
  fi

  local base checked_out branch pruned kept
  base=$(resolve_base_branch)
  if [ -z "$base" ]; then
    echo "error: prune-branches needs a base branch, but the root checkout's HEAD is detached" >&2
    return 1
  fi

  # Branches checked out anywhere — the root checkout included — are off
  # limits. `git worktree list --porcelain` names each on a
  # `branch refs/heads/<name>` line.
  checked_out=$(git worktree list --porcelain | sed -n 's|^branch refs/heads/||p')

  pruned=0
  kept=0
  while read -r branch; do
    [ -n "$branch" ] || continue
    if [ "$branch" = "$base" ] || printf '%s\n' "$checked_out" | grep -qxF "$branch"; then
      echo "kept: $branch (checked out)"
      kept=$((kept + 1))
      continue
    fi
    if branch_is_merged "$base" "$branch"; then
      git branch -D "$branch" >/dev/null
      echo "pruned: $branch"
      pruned=$((pruned + 1))
    else
      echo "kept: $branch (not merged into $base)"
      kept=$((kept + 1))
    fi
  done < <(git for-each-ref --format='%(refname:short)' refs/heads/change)

  echo "prune-branches: $pruned pruned, $kept kept (base $base)."
}

# Subcommand dispatch: `remove` and `prune-branches` are the verbs; any other
# first argument is a change name for the create path (backward compatible).
if [ "${1:-}" = "remove" ]; then
  shift
  cmd_remove "$@"
  exit $?
fi

if [ "${1:-}" = "prune-branches" ]; then
  shift
  cmd_prune_branches "$@"
  exit $?
fi

# --- create path ------------------------------------------------------------
NAME="${1:-}"
if [ $# -gt 0 ]; then
  shift
fi

# Trailing flags, mirroring `remove`'s loop.
FRESH=0
while [ $# -gt 0 ]; do
  case "$1" in
    --fresh) FRESH=1 ;;
    *) echo "error: unknown argument '$1'" >&2; usage; exit 1 ;;
  esac
  shift
done

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

BASE_BRANCH=$(resolve_base_branch)

# `--fresh` opts out of idempotence: the caller wants a branch starting at the
# base, never an adopted one. Anything that would mean reuse is an error, and
# only a branch whose content already reached the base is deleted — unmerged
# work is never thrown away.
if [ "$FRESH" -eq 1 ]; then
  if [ -e "$WORKTREE" ]; then
    echo "error: --fresh refuses to reuse the existing worktree at $WORKTREE" >&2
    exit 1
  fi
  if [ -z "$BASE_BRANCH" ]; then
    echo "error: --fresh needs a base branch, but the root checkout's HEAD is detached" >&2
    exit 1
  fi
  if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    if branch_is_merged "$BASE_BRANCH" "$BRANCH"; then
      OLD_TIP=$(git rev-parse --short "$BRANCH")
      git branch -D "$BRANCH" >/dev/null
      echo "Deleted merged branch $BRANCH (was $OLD_TIP) — recreating it from $BASE_BRANCH."
    else
      echo "error: --fresh will not delete $BRANCH — its content is not merged into $BASE_BRANCH" >&2
      exit 1
    fi
  fi
fi

# Idempotent by default (no opt-in flag): a caller should never need to test
# for an existing worktree before invoking this script. Resolution, in order:
#   worktree exists on $BRANCH        -> reuse, unchanged, exit 0
#   worktree exists on another branch -> refuse, change nothing, exit non-zero
#   worktree absent, branch exists    -> attach a worktree to that branch
#   worktree absent, branch absent    -> create both (today's original behavior)
# Reuse is never silent: the two reuse arms say so explicitly and report how
# far the adopted branch has drifted from the base, so a stale branch cannot be
# mistaken for a fresh one. Only the arm that creates both says "Created".
MODE=create

if [ -e "$WORKTREE" ]; then
  CURRENT_BRANCH=$(git -C "$WORKTREE" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  if [ "$CURRENT_BRANCH" = "$BRANCH" ]; then
    MODE=reuse
  else
    echo "error: $WORKTREE already exists on branch '$CURRENT_BRANCH', not $BRANCH" >&2
    exit 1
  fi
elif git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git worktree add "$WORKTREE" "$BRANCH"
  MODE=attach
else
  git worktree add "$WORKTREE" -b "$BRANCH"
fi

COUNTS=$(branch_counts "$BASE_BRANCH" "$BRANCH")
DRIFT=""
if [ -n "$COUNTS" ]; then
  DRIFT=" ($COUNTS vs $BASE_BRANCH)"
fi

echo
case "$MODE" in
  reuse)
    echo "Reusing existing worktree $WORKTREE on branch $BRANCH$DRIFT." ;;
  attach)
    echo "Attached worktree $WORKTREE to existing branch $BRANCH$DRIFT." ;;
  *)
    echo "Created worktree $WORKTREE on branch $BRANCH." ;;
esac

cat <<EOF

Next steps:
  cd $WORKTREE
  # run the am lifecycle here (/s:plan -> /s:build, including merge/archive)
  # then ship it as a PR:
  git push -u origin $BRANCH
  gh pr create --fill
  gh pr merge --auto --squash --delete-branch
EOF

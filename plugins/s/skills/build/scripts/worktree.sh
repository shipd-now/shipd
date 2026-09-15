#!/usr/bin/env bash
# worktree.sh — create/remove an isolated git worktree + branch for one change.
#
# The workflow is: one change = one worktree = one branch = one PR. This script
# creates `.worktrees/<change>` on branch `change/<change>`; the whole shipd
# lifecycle (plan -> build -> merge/archive) runs there so artifacts,
# implementation, and spec promotion travel in a single PR.
#
# It also provides `remove <change>`, a *guarded* teardown: removal refuses
# (exit 2, listing every reason) while the worktree shows work in progress —
# uncommitted/untracked files, an unshipped change under the worktree's
# configured content directory (`<content-dir>/planned/`, resolved through the
# engine and falling back to the literal `.shipd`), a
# `[~]` task claim or `.tasks.lock` in a planned checklist, or — only while the
# tree is already dirty — any file modified within the idle window (default 30
# minutes, `SHIPD_WORKTREE_IDLE_MINUTES` overrides; `0` disables the activity
# guard). A clean tree never triggers the idle guard on its own: a worktree
# whose work is fully committed removes however recently its files were
# written. This stops a parallel session from pruning a worktree out from
# under a live one.
# `--force` performs the removal anyway, printing each guard it overrode. The
# unshipped-change guard skips a planned change that is base content — tracked,
# locally clean, and identical to the base branch — since that is not the
# worktree's own work; the claim/lock guard still scans every planned checklist.
# Where the configuration relocates the content directory into an external
# store (`store_root`), both guards additionally check the store's
# `planned/<change>` — the change under removal and only that one, since the
# store is shared by every worktree of the repository — with no base-content
# carve-out there.
#
# Shipped as a plugin engine script — invocable by plugin path from any git
# repository. It assumes nothing about the repository beyond git itself: no shipd
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
# `sweep [--dry-run]` combines the two: it reclaims every worktree whose
# branch is merged and guard-clean, reports the rest (`kept:`/`stale:`), then
# runs `prune-branches`'s own branch reclamation. Never forces past a guard,
# and always exits 0.
#
# Usage (run from the repository root):
#   <plugin>/skills/build/scripts/worktree.sh <change-name> [--fresh]
#   <plugin>/skills/build/scripts/worktree.sh remove <change-name> [--force]
#   <plugin>/skills/build/scripts/worktree.sh prune-branches
#   <plugin>/skills/build/scripts/worktree.sh sweep [--dry-run]
#
# Bash 3.2-safe (macOS system bash): no mapfile, no associative arrays.
set -e

# This script's own directory, so `remove` can reach the engine beside it to
# resolve the worktree's configured content directory. Resolved without
# `readlink -f`, which BSD/macOS lacks.
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() {
  echo "usage: worktree.sh <change-name> [--fresh]    # create .worktrees/<change-name>" >&2
  echo "       worktree.sh remove <change> [--force]  # guarded removal + prune" >&2
  echo "       worktree.sh prune-branches [--dry-run]  # delete merged local change/* branches" >&2
  echo "       worktree.sh sweep [--dry-run]           # reclaim merged worktrees + branches" >&2
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

# Is a branch's remote-tracking ref gone after once having existed? True
# (exit 0) only when the branch carries recorded upstream config
# (`branch.<branch>.remote`, set by `git push -u`, the workflow in
# AGENTS.md) and that remote's tracking ref for it is now absent — the state
# a squash merge that deletes its remote branch leaves, even when the base
# moved and the content probe can no longer match the patch. False (exit 1)
# both when the tracking ref still exists and when the branch was never
# pushed at all (no `branch.<branch>.remote` recorded): an unpushed local
# branch has no tracking ref either, so this probe must decline rather than
# read that as "gone" and delete it. The remote name is read from that config
# rather than assumed, so a remote not named `origin` is honored too. This is
# the second merged-ness probe `prune-branches` consults when the content
# probe reports not-merged. Silent on stdout either way.
branch_remote_ref_gone() {
  local branch="$1" remote
  remote=$(git config --get "branch.$branch.remote" 2>/dev/null) || return 1
  [ -n "$remote" ] || return 1
  if git rev-parse --verify --quiet "refs/remotes/$remote/$branch" >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

# Is a planned change directory *base content* rather than the worktree's own
# work? True (exit 0) only when all three probes hold against the resolved
# base: the path is tracked (an untracked-only directory is never base
# content), it has no local modifications or untracked files, and it is
# byte-identical to the same path on the base branch. Any probe failing — or no
# base at all — returns false, and the unshipped-change guard fires as before.
# `<rel>` is the directory's path relative to the worktree root.
planned_is_base_content() {
  local worktree="$1" base="$2" rel="$3"
  [ -n "$base" ] || return 1
  [ -n "$(git -C "$worktree" ls-files -- "$rel" 2>/dev/null)" ] || return 1
  [ -z "$(git -C "$worktree" status --porcelain -- "$rel" 2>/dev/null)" ] || return 1
  git -C "$worktree" diff --quiet "$base" -- "$rel" 2>/dev/null || return 1
  return 0
}

# resolve_worktree_settings <root>
#
# Reads the three layered worktree-housekeeping settings (shipd-config
# worktree-sweep-keys) through `spec_status.py config-show` at `<root>`, the
# same seam and `sed -n 's/^<key>: //p'` idiom the guard chain already uses to
# resolve `content-dir:` and `store:`. Sets the globals `WORKTREE_SWEEP`
# (`true` or `false`), `IDLE` (minutes), and `STALE_DAYS` (days). Any
# resolution failure — python3 absent, malformed config, no matching line —
# falls back to the built-in defaults `true`, `30`, and `7`, mirroring the
# layered loader's own tolerance, so this helper never depends on anything
# beyond git. `config-show` itself already resolves `SHIPD_WORKTREE_IDLE_MINUTES`
# and `SHIPD_WORKTREE_STALE_DAYS` ahead of the config layer, so those
# environment overrides keep working with no separate handling here.
resolve_worktree_settings() {
  local root="$1" config_show

  config_show=$(python3 "$SCRIPT_DIR/spec_status.py" --root "$root" \
    config-show 2>/dev/null || true)

  WORKTREE_SWEEP=$(printf '%s\n' "$config_show" \
    | sed -n 's/^worktree-sweep: //p' | head -n 1)
  case "$WORKTREE_SWEEP" in
    true|false) ;;
    *) WORKTREE_SWEEP="true" ;;
  esac

  IDLE=$(printf '%s\n' "$config_show" \
    | sed -n 's/^worktree-idle-minutes: //p' | head -n 1)
  case "$IDLE" in
    ''|*[!0-9]*) IDLE=30 ;;
  esac

  STALE_DAYS=$(printf '%s\n' "$config_show" \
    | sed -n 's/^worktree-stale-days: //p' | head -n 1)
  case "$STALE_DAYS" in
    ''|*[!0-9]*) STALE_DAYS=7 ;;
  esac
}

# --- remove verb ------------------------------------------------------------
#
# Guards run in order dirty -> unshipped -> claims/lock -> recent activity,
# accumulating every failing reason into one refusal report (never
# first-failure-only — the human should see the whole picture). Exit codes
# mirror the gate engine: 0 removed, 2 refused, 1 usage/error.

# collect_remove_reasons <worktree> <change>
#
# Populates the global `reasons` array with every guard reason firing against
# `<worktree>` (a `.worktrees/<change>`-style path) and prints nothing. Reset
# at the top of every call, so a caller iterating several worktrees — the
# `sweep` verb — gets a fresh array each time rather than an accumulating one.
# `cmd_remove` and `cmd_sweep` both call this; a guard added here applies to
# both, and `cmd_sweep` never forces past what it finds. Guard 4 reads the
# idle window from the global `$IDLE`, which the caller resolves once before
# looping.
collect_remove_reasons() {
  local worktree="$1" change="$2"
  local base wt_branch porcelain config_show content_dir store_dir
  local planned store_planned d dir t l hit

  reasons=()

  # The base for guard #2's carve-out, resolved once per worktree. Fail
  # closed: a detached root HEAD resolves empty, and a base that *is* the
  # worktree's own branch would carve out the worktree's own work — both
  # leave `base` empty, so every planned change guards exactly as it did
  # before the carve-out.
  base=$(resolve_base_branch)
  wt_branch=$(git -C "$worktree" symbolic-ref -q --short HEAD 2>/dev/null || true)
  if [ "$base" = "$wt_branch" ]; then
    base=""
  fi

  # 1. Dirty tree: any uncommitted or untracked path. Computed once and reused
  # by guard 4 below, which only runs while this is non-empty.
  porcelain=$(git -C "$worktree" status --porcelain 2>/dev/null)
  if [ -n "$porcelain" ]; then
    reasons+=("dirty worktree: uncommitted or untracked files")
  fi

  # The worktree's content directory, resolved through the engine rather than
  # hardcoded, so a repo that configures `dir` to a renamed or nested path is
  # guarded where its artifacts actually live (build-spec-lifecycle
  # worktree-guard-content-dir). Any failure — python3 absent, malformed
  # config, no `content-dir:` line — falls back to the literal `.shipd`, so the
  # guard never scans less than it does under the default configuration and the
  # helper still runs in repositories with nothing but git.
  #
  # The same output additionally carries a `store:` line when the layered
  # configuration relocates the content directory into an external store
  # (`store_root`); guards 2 and 3 then also check the store, scoped to the
  # change under removal.
  config_show=$(python3 "$SCRIPT_DIR/spec_status.py" --root "$worktree" \
    config-show 2>/dev/null || true)
  content_dir=$(printf '%s\n' "$config_show" \
    | sed -n 's/^content-dir: //p' | head -n 1)
  if [ -z "$content_dir" ]; then
    content_dir=".shipd"
  fi
  store_dir=$(printf '%s\n' "$config_show" | sed -n 's/^store: //p' | head -n 1)

  planned="$worktree/$content_dir/planned"
  # Only this change's directory in the store: the store is shared by every
  # worktree of the repository, so scanning the whole `planned/` would block
  # removing any worktree while any change is in flight.
  store_planned=""
  if [ -n "$store_dir" ]; then
    store_planned="$store_dir/planned/$change"
  fi

  # 2. Unshipped changes still parked under <content-dir>/planned/ — except the
  # ones that are base content rather than this worktree's own work (a planned
  # change committed on the base branch and checked out here unmodified). The
  # worktree's *own* change never qualifies: `planned/<change>/` is absent from
  # the base, so the identical-to-base probe fails and the guard fires.
  if [ -d "$planned" ]; then
    for d in "$planned"/*/; do
      [ -d "$d" ] || continue
      dir="${d%/}"
      if planned_is_base_content "$worktree" "$base" "${dir#$worktree/}"; then
        continue
      fi
      reasons+=("unshipped change under $content_dir/planned: $dir")
    done
  fi
  # The store's copy of *this* change. The base-content carve-out does not
  # apply: a change present in the store's `planned/` is in flight by
  # definition — the store carries no branch to have shipped it on.
  if [ -n "$store_planned" ] && [ -d "$store_planned" ]; then
    reasons+=("unshipped change in the store: $store_planned")
  fi

  # 3. Coordination in progress: a `[~]` task claim or a `.tasks.lock`. This
  # guard scans every planned checklist, base-tracked or not — a `[~]` mark is
  # live coordination wherever it sits, so guard #2's carve-out does not apply.
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
  if [ -n "$store_planned" ]; then
    if [ -f "$store_planned/tasks.md" ] \
       && grep -q -- '- \[~\]' "$store_planned/tasks.md" 2>/dev/null; then
      reasons+=("in-progress task claim ([~]) in $store_planned/tasks.md")
    fi
    if [ -e "$store_planned/.tasks.lock" ]; then
      reasons+=("coordination lock present: $store_planned/.tasks.lock")
    fi
  fi

  # 4. Recent activity inside the idle window (skipped when IDLE=0), and only
  # while the tree is dirty (guard 1's $porcelain, reused rather than
  # recomputed). This makes the probe non-decisive: a dirty tree already
  # refuses through guard 1, so this can only add a second reason line beside
  # it — a clean tree is indistinguishable from a finished close-out, so there
  # is nothing left here for the probe to protect. The probe itself is
  # `find -mmin`, which both GNU and BSD (macOS) find implement — unlike
  # `-newermt`/`-quit`, whose grammar/availability differs across find flavors.
  # `| head -n1` stops the walk at the first hit without the GNU-only `-quit`.
  if [ "$IDLE" -gt 0 ] && [ -n "$porcelain" ]; then
    hit=$(find "$worktree" -mmin "-$IDLE" -print 2>/dev/null | head -n 1 || true)
    if [ -n "$hit" ]; then
      reasons+=("file modified within the idle window (last $IDLE minutes): $hit")
    fi
  fi
}

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

  # Resolves `IDLE` (guard 4's window) through the layered config, with
  # `SHIPD_WORKTREE_IDLE_MINUTES` as the higher-precedence override —
  # `config-show` itself applies that precedence (shipd-config
  # worktree-sweep-keys).
  resolve_worktree_settings "$WORKTREE"

  collect_remove_reasons "$WORKTREE" "$CHANGE"

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
# the verb exits 0 whether or not anything was deleted. `--dry-run` reports
# the same candidates without deleting anything — used internally by `sweep`,
# which reuses this verb wholesale for its own branch pass.
cmd_prune_branches() {
  local dry_run=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --dry-run) dry_run=1 ;;
      *) echo "error: unknown argument '$1'" >&2; usage; return 1 ;;
    esac
    shift
  done

  # Must run from the repository root: it has a real `.git` directory.
  if [ ! -d ".git" ]; then
    echo "error: run this from the repo root (no .git directory here)" >&2
    return 1
  fi

  local base checked_out branch pruned kept remote_probe_available
  base=$(resolve_base_branch)
  if [ -z "$base" ]; then
    echo "error: prune-branches needs a base branch, but the root checkout's HEAD is detached" >&2
    return 1
  fi

  # Branches checked out anywhere — the root checkout included — are off
  # limits. `git worktree list --porcelain` names each on a
  # `branch refs/heads/<name>` line.
  checked_out=$(git worktree list --porcelain | sed -n 's|^branch refs/heads/||p')

  # Refresh remote-tracking refs once, before judging merged-ness. `--all`
  # refreshes every configured remote, not just one hardcoded name — the
  # second probe reads each branch's own recorded remote (below), which need
  # not be "origin". `fetch.prune` is unset by default and `git pull` never
  # prunes, so a remote branch deleted by a squash merge leaves its local
  # tracking ref behind unless this runs. Where no remote is configured, or
  # the fetch fails (offline, unreachable host), the remote probe below is
  # unavailable and the loop falls back to the content probe alone — the same
  # outcome as before this refresh existed, never a wrongly deleted branch.
  # The verb never depends on the network.
  remote_probe_available=0
  if [ -n "$(git remote 2>/dev/null)" ]; then
    if git fetch --prune --all --quiet 2>/dev/null; then
      remote_probe_available=1
    else
      echo "note: could not refresh remote-tracking refs; falling back to the content probe" >&2
    fi
  fi

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
      [ "$dry_run" -eq 1 ] || git branch -D "$branch" >/dev/null
      echo "pruned: $branch"
      pruned=$((pruned + 1))
    elif [ "$remote_probe_available" -eq 1 ] && branch_remote_ref_gone "$branch"; then
      [ "$dry_run" -eq 1 ] || git branch -D "$branch" >/dev/null
      echo "pruned: $branch"
      pruned=$((pruned + 1))
    else
      echo "kept: $branch (not merged into $base)"
      kept=$((kept + 1))
    fi
  done < <(git for-each-ref --format='%(refname:short)' refs/heads/change)

  echo "prune-branches: $pruned pruned, $kept kept (base $base)."
}

# --- sweep verb --------------------------------------------------------------
#
# Opportunistic housekeeping: reclaims the worktrees under `.worktrees/`
# whose work has already shipped, then runs `prune-branches`'s own branch
# reclamation. Judges each worktree's merged-ness with the same two probes
# `prune-branches` consults, in the same order, and reuses the `remove`
# guard chain (`collect_remove_reasons`) on merged candidates so a sweep
# never forces past a guard `remove` itself would refuse on. Always exits 0,
# whether or not anything was reclaimed, so a caller's own outcome never
# depends on it (worktree-sweep worktree-sweep-verb).
cmd_sweep() {
  local dry_run=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --dry-run) dry_run=1 ;;
      *) echo "error: unknown argument '$1'" >&2; usage; return 1 ;;
    esac
    shift
  done

  # Must run from the repository root: it has a real `.git` directory.
  if [ ! -d ".git" ]; then
    echo "error: run this from the repo root (no .git directory here)" >&2
    return 1
  fi

  local base
  base=$(resolve_base_branch)
  if [ -z "$base" ]; then
    echo "sweep: no base branch resolves — the root checkout's HEAD is detached; skipping the worktree pass and the branch prune" >&2
    return 0
  fi

  resolve_worktree_settings "."

  # Refresh remote-tracking refs once, before judging any worktree's
  # merged-ness — the same refresh `prune-branches` does for its own branch
  # pass below, run here too so this pass's `branch_remote_ref_gone` calls see
  # current state. Never depends on the network: no remote, or a failed
  # fetch, just leaves the remote probe unavailable and the loop falls back
  # to the content probe alone.
  local remote_probe_available=0
  if [ -n "$(git remote 2>/dev/null)" ]; then
    if git fetch --prune --all --quiet 2>/dev/null; then
      remote_probe_available=1
    fi
  fi

  local now stale_seconds wt name branch counts merged tip age_seconds age_days joined r

  now=$(date +%s)
  stale_seconds=$((STALE_DAYS * 86400))

  if [ -d ".worktrees" ]; then
    for wt in .worktrees/*/; do
      [ -d "$wt" ] || continue
      wt="${wt%/}"
      name="${wt#.worktrees/}"

      branch=$(git -C "$wt" symbolic-ref -q --short HEAD 2>/dev/null || true)
      [ -n "$branch" ] || continue

      # A branch with no commits ahead of the base is never a sweep
      # candidate — otherwise the create-path sweep would delete the
      # worktree it just created.
      counts=$(branch_counts "$base" "$branch")
      case "$counts" in
        "ahead 0,"*) continue ;;
      esac

      merged=0
      if branch_is_merged "$base" "$branch"; then
        merged=1
      elif [ "$remote_probe_available" -eq 1 ] && branch_remote_ref_gone "$branch"; then
        merged=1
      fi

      if [ "$merged" -eq 1 ]; then
        collect_remove_reasons "$wt" "$name"
        if [ "${#reasons[@]}" -gt 0 ]; then
          joined=""
          for r in "${reasons[@]}"; do
            if [ -z "$joined" ]; then
              joined="$r"
            else
              joined="$joined; $r"
            fi
          done
          echo "kept: $wt ($joined)"
        else
          # The removal runs as an `if` condition so the script's global
          # `set -e` does not abort the sweep when it fails (a locked
          # worktree, a permission error). Housekeeping must never take the
          # whole pass — or the caller's exit code — down with one worktree
          # it cannot reclaim, so a failure is reported and the loop and the
          # branch prune below carry on.
          if [ "$dry_run" -eq 1 ]; then
            echo "swept: $wt"
          elif git worktree remove "$wt"; then
            git worktree prune
            echo "swept: $wt"
          else
            echo "kept: $wt (removal failed)"
          fi
        fi
      else
        tip=$(git -C "$wt" log -1 --format=%ct 2>/dev/null || true)
        if [ -n "$tip" ]; then
          age_seconds=$((now - tip))
          if [ "$age_seconds" -gt "$stale_seconds" ]; then
            age_days=$((age_seconds / 86400))
            echo "stale: $wt (unmerged; branch tip ${age_days}d old)"
          else
            echo "kept: $wt (unmerged; branch tip recent)"
          fi
        else
          echo "kept: $wt (unmerged)"
        fi
      fi
    done
  fi

  if [ "$dry_run" -eq 1 ]; then
    cmd_prune_branches --dry-run
  else
    cmd_prune_branches
  fi

  return 0
}

# Subcommand dispatch: `remove`, `prune-branches`, and `sweep` are the verbs;
# any other first argument is a change name for the create path (backward
# compatible).
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

if [ "${1:-}" = "sweep" ]; then
  shift
  cmd_sweep "$@"
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
  # run the shipd lifecycle here (/s:plan -> /s:build, including merge/archive)
  # then ship it as a PR:
  git push -u origin $BRANCH
  gh pr create --fill
  gh pr merge --auto --squash --delete-branch
EOF

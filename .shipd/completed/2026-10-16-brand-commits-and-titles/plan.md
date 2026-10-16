# brand-commits-and-titles
Status: verified
Planned-at: d8e018df10926725ee27b8ca05c9516203ecad34
Gated-hash: fdd0d9f4f0de

## Idea

Every commit subject and pull request title shipd writes starts with the fixed
brand prefix `☕ Shipd: `.

### Motivation

A reader scanning a GitHub commit list or PR list (e.g. the commits on
https://github.com/shipd-now/shipd/pull/331) cannot tell which commits and
PRs shipd wrote, because their subjects are bare. Branding them makes shipd's
work recognisable at a glance, and a squash merge carries the branded PR title
into main's history.

### Details

- One engine constant and one helper brand a subject, never doubling it.
- `/s:pr` titles pass through the helper after the `pr.title` template.
- A shipd-managed `commit-msg` git hook, installed by the worktree create
  path, brands every commit made inside a shipd worktree, by any agent.
- Engine auto-commits (`wiki_autocommit`, which every store and wiki commit
  rides) brand their subject through the helper.
- The literal commit lines outside worktrees (`/s:gate` install and refresh,
  `/s:epic` store amend) render their subject through the helper.

Affected capabilities: `shipd-brand` (new), `shipd-pr` (modified title
render). Impact: `spec_common.py`, a new `brand.py`, `worktree.py`,
`pr_title.py`, two skills, the content README, tests, and the plugin version.

### Non-goals

- No configuration: the brand cannot be changed or turned off.
- No rewriting of existing commits or existing PR titles.
- No change to `pr-mode` or to the `pr` key.
- No chaining with, or editing of, a repository's own `commit-msg` hook or a
  `core.hooksPath` directory.
- No branding of commits a person makes in the root checkout.

## Implementation

- **Constant** `BRAND_PREFIX = "☕ Shipd: "` in `spec_common`, the single owner
  of the prefix. Every site below uses it; no site spells the prefix itself.
  No config key is added (the user's answer, Q2).
- **Helper** `brand_subject(subject)` in `spec_common`: returns the subject
  unchanged when it is empty or whitespace, already starts with
  `BRAND_PREFIX` or with `BRAND_PREFIX.rstrip()`, or starts with `fixup!`,
  `squash!`, or `amend!` (so autosquash keeps working). Otherwise returns
  `BRAND_PREFIX + subject`. Existing subjects keep their own lead:
  `shipd-wiki: queue-add q-x` becomes `☕ Shipd: shipd-wiki: queue-add q-x`
  (Q3).
- **New script** `plugins/s/skills/build/scripts/brand.py`, stdlib only, verbs:
  - `subject <text>` prints `brand_subject(text)`.
  - `commit-msg <file>` is the hook entry. It reads `git rev-parse
    --show-toplevel` from the cwd; when that directory's parent is not named
    `.worktrees`, it changes nothing. Otherwise it rewrites the first line
    that is not a `#` comment through `brand_subject`. It always exits 0.
  - `install-hook [--root DIR]` installs the hook (below) and prints one line:
    `installed:`, `refreshed:`, or `note: commit branding skipped — <reason>`.
    It always exits 0.
- **The hook file** is a POSIX `sh` script whose second line is the marker
  `# shipd-managed commit-msg hook`. It names `brand.py` by the absolute path
  of the installing plugin, exits 0 when that file or `python3` is missing,
  and otherwise runs `python3 <brand.py> commit-msg "$1"` and exits 0. A
  commit is never blocked.
- **Install rules**: when `git config core.hooksPath` is non-empty, skip with
  a note. The hooks dir is `<git-common-dir>/hooks` (created if absent; linked
  worktrees read hooks from it, observed below). A `commit-msg` file without
  the marker is foreign: skip with a note. A marked one is overwritten, so a
  plugin update repoints it. The file is chmod 0755. Rejected: chaining or
  writing into `core.hooksPath` (Q4).
- **Worktree create**: `worktree.py`'s `cmd_create` calls the install
  in-process after `worktree.sh` succeeds, on fresh, attached, and reused
  worktrees alike, before the post-worktree scripts. Its outcome never changes
  the exit code.
- **Mechanism choice**: a git hook plus the engine helper (Q1). Rejected: a
  skill rule at each commit site, which every new agent must remember; a
  Claude Code `PreToolUse` Bash rewriter, which misses heredoc, `-F`, and
  engine commits.
- **Engine commits**: `wiki_autocommit` commits with `brand_subject(subject)`.
- **PR titles**: `pr_title.py` applies `brand_subject` to the rendered title.
- **Skill commit lines** (in place, same line count): `/s:gate`'s two
  `git commit -m` lines and `/s:epic`'s store amend line wrap their subject in
  `$(python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/brand.py" subject
  "<subject>")`.
- **Docs**: the content README's `pr` key section gains one paragraph saying
  every title, and every commit shipd writes, starts with `☕ Shipd: `.
  `AGENTS.md`'s store-amend sentence names the branded subject.
- **Version**: bump the patch in `plugins/s/.claude-plugin/plugin.json` to one
  above `main`'s at build time.

Risk: a stale hook path after a plugin cache purge leaves commits unbranded,
never blocked. The next worktree create refreshes it.

## Questions and answers

### Q1: How do agent-written commits get the brand?
- **Question:** A `commit-msg` hook installed by the worktree create path,
  scoped to shipd worktrees, plus an engine helper for engine and literal skill
  commits (1); a skill rule plus a helper at every commit site (2); or a
  Claude Code `PreToolUse` Bash rewriter (3). Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1, the `commit-msg` hook plus the engine helper.
- **Queued:** q-brand-commit-agent-mechanism

### Q2: What config key shape controls the brand?
- **Question:** A new top-level `brand` key (string replaces, `false` turns
  off, undeclared is the default) (1); a `pr.brand` member (2); or separate
  commit and title keys (3). Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Not configurable; the brand is always on.
- **Queued:** q-brand-config-key-shape

### Q3: Do engine subjects keep their own lead?
- **Question:** Prepend the brand and keep subjects like `shipd-wiki: ...` as
  they are (1), or drop their own `shipd:` lead (2). Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. Add the brand only, giving
  `☕ Shipd: shipd-wiki: ...`.
- **Queued:** q-brand-prefix-on-existing-commit-subjects

### Q4: What happens beside a foreign hook or `core.hooksPath`?
- **Question:** Skip the install with one note and never clobber (1); chain
  the foreign hook (2); or write into the `core.hooksPath` directory (3).
  Recommendation: (1).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option 1. Skip and print one note when the repository already
  has its own `commit-msg` hook or sets `core.hooksPath`.
- **Queued:** q-commit-msg-hook-foreign-hook-policy

## Readiness attestation

### Problem and motivation

Commits and PRs shipd writes carry bare subjects, so nobody can tell them apart
from a person's work on GitHub.

Evidence:

- `git log -3` on main shows bare subjects such as `room: resolve repo from
  URL or --repo; ...` (22ecf9b).
- Capability `shipd-pr`, requirement `pr-title-render`, adds no brand.

### Scope and non-goals

Subjects and titles written from now on are branded; history, config,
`pr-mode`, and user-owned hooks are left alone.

Evidence:

- `spec_common.py:1152` (`resolve_pr`) and `pr-mode` stay as they are.
- `worktree.sh` is not edited; the install lives in `worktree.py`.

### Affected capabilities and files

Two capabilities and about a dozen files, because every commit and title path
has to reach the one helper.

Evidence:

- Capabilities: `shipd-brand` (new), `shipd-pr` (`pr-title-render`, base
  9da11755275f from `base-hash`).
- Commit sites: `spec_common.py:1617` (`wiki_autocommit`, which
  `store_autocommit`, `spec_merge.py:246`, `spec_gate.py:480`, and
  `spec_emit.py:143` ride), `gate/SKILL.md:138` and `:344`,
  `epic/SKILL.md:175`.
- Title site: `pr_title.py` `main`. Create site: `worktree.py:359`
  (`cmd_create`).
- Runnable premise: a probe repo with a `commit-msg` hook in `.git/hooks`
  and a linked worktree under its worktrees folder; `git commit -m hello`
  there gave the subject `BR: hello`, so linked worktrees run the common-dir
  hook, and `git rev-parse --show-toplevel` printed the worktree's path.
- Tests that assert exact engine subjects: `test_spec_status.py:4644`,
  `:4652`, `:4657`, `:4790`, `:5138`, `test_spec_emit.py:798`,
  `test_wiki_remove.py:173`, `test_spec_common.py:4759`; and the CLI titles
  in `test_pr_title.py:80-100`.

### No open task-shaping decision

Every task-shaping decision is settled.

Evidence:

- Mechanism (Q1), configurability (Q2), subject lead (Q3), and hook conflicts
  (Q4): settled by the user.
- Hook scope (shipd worktrees only), fixup handling, and fail-open behavior:
  investigation of `worktree.py` and the probe above.

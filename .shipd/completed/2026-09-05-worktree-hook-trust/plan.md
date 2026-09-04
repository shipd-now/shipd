# worktree-hook-trust
Status: verified

## Idea

Add first-run consent gating for `post-worktree-scripts`: a machine-local
trust ledger keyed by the hooks list's content hash, so hooks from a freshly
cloned or edited config never execute without the user's explicit consent.

### Motivation

`post-worktree-scripts` resolve nearest-wins through the layered config, so a
cloned workspace or member repo's tracked `.shipd-config.json` supplies shell
commands that execute unannounced on the first `shipd worktree` — and with
team-shared workspace repos now documented (`docs/portable-workspaces.md` §8),
that is an unstated code-execution grant from whoever last pushed the shared
repo.

### Details

- A trust ledger at `~/.shipd-trust.json` holds the SHA-256 fingerprints of
  consented hooks lists, so consent is to the exact command list and travels
  across checkouts and worktree copies of it.
- The create path and `hooks run` gate on it: trusted lists run as today;
  untrusted lists prompt for consent on a TTY, and without a TTY refuse with
  exit 3, worktree left in place, naming `hooks trust` then `hooks run` from
  the created worktree as the resume path.
- `hooks add`/`hooks remove` auto-trust the list they just produced only when
  the prior effective list was trusted or empty; a new `hooks trust` verb
  records trust for the resolved list explicitly.
- `docs/portable-workspaces.md` §8 gains the hook-inheritance trust warning
  and a paragraph on concurrent answers to the same queue question.

Affected capabilities: `worktree-hooks` (modified), `shipd-workspace`
(modified). Impact: `plugins/s/skills/build/scripts/worktree.py`,
`plugins/s/skills/build/tests/test_worktree_engine.py`,
`docs/portable-workspaces.md`, `plugins/s/.claude-plugin/plugin.json`
(version bump).

### Non-goals

- No change to hook *resolution* — nearest-wins inheritance from enclosing
  configs stays exactly as `shipd-config/post-worktree-scripts-key` specifies.
- No change to execution semantics once trusted: env vars, ordering, announce
  lines, and exit-3-on-failure are untouched.
- No per-item trust, signatures, or content inspection beyond the exact-list
  fingerprint.
- No workspace-side switch to stop supplying hooks — consent on the receiving
  machine is the control.

## Implementation

- **Ledger file `~/.shipd-trust.json`**, resolved with `os.path.expanduser`;
  a JSON object `{<sha256 hex>: <declaring config path>}`. Tests point `HOME` at a
  temp dir, the same isolation the layered-config tests use. Rejected: a key
  in `~/.shipd-config.json` — config is user-authored intent, the ledger is
  engine state, and mixing them races the user's own edits. Rejected: any
  in-repo or git-dir marker — tracked files are attacker-controlled and
  git-dir state is lost per-clone.
- **Fingerprint** = `hashlib.sha256(json.dumps(items,
  separators=(",", ":")).encode()).hexdigest()`; the ledger is keyed by the
  fingerprint itself (the value records the declaring config path,
  informationally). Consent is to the exact command list, not the file that
  declared it, so trust granted against a tracked config carries into every
  checkout and worktree copy of the same list. Rejected: keying by the
  declaring config's realpath — a worktree's checked-out copy of the tracked
  config is a different path, so consent granted at the parked root never
  carried into the worktree (validator-refuted). Any list edit re-prompts. A
  missing/malformed ledger reads as empty; a failed ledger write warns on
  stderr and never fails a verb that already obtained consent.
- **Gate function** `ensure_hooks_trusted(items, source)` in `worktree.py`,
  called before each `run_hooks` call site (`cmd_create` and `hooks run`);
  `run_hooks` itself stays pure. Empty list bypasses. Consent prompt only
  when `sys.stdin.isatty()`: print the source path and every item, accept
  `y`/`yes`. Refusal and non-TTY both exit `HOOK_FAILURE_EXIT` (3) with the
  worktree kept — the oracle-cited convention (completed/worktree-hooks
  rejected git's native hooks *because* they fail silently;
  epic/autonomous-delivery forbids silently dropping a gate), and the code
  autopilot already parks a member on.
- **`hooks add` / `hooks remove`** re-resolve after their successful write
  and record trust for the resulting list **only when the prior effective
  list was already trusted or empty** — the user just typed the registration,
  so the solo path never prompts, but an untrusted pre-existing item is never
  blanket-trusted by an unrelated registration (a hostile tracked list must
  always reach the consent gate where the user sees it). **`hooks trust`** resolves
  the effective list, prints the source and items, records the entry, exits 0;
  with nothing configured it reports that and exits non-zero without writing.
  Runnable premise: `worktree.py hooks list --json` on this repo prints
  `{"root": …, "source": null, "items": []}` and exits 0 (observed), so the
  no-hooks shape the new verbs branch on is confirmed.
- **Docs**: §8 of `docs/portable-workspaces.md` documents that a shared
  workspace's tracked config supplies hooks to member repos, the consent
  gate, and `hooks trust`; plus the concurrent-answer conflict (two clones
  answering the same pending `q-` block conflict on its `Answer:` line — keep
  exactly one answer, never both).
- **Risk**: existing users with configured hooks hit one prompt (or one
  parked exit 3 in unattended runs) after upgrading — a deliberate, one-time
  cost, resumable via `hooks trust`, and called out in the doc.

## Questions and answers

### Q1: Which hook sources require first-run consent?
- **Question:** Which hook sources should require first-run consent before
  `post-worktree-scripts` execute? Options: (a) every source config not yet in
  the machine-local trust ledger, with `hooks add` auto-trusting its own
  entry; (b) only source configs outside the invocation root.
  Recommendation: (a).
- **Verdict:** INSUFFICIENT
- **Answered by:** USER
- **Answer:** Option (a) — a uniform ledger over every source. Self-registered
  hooks never prompt because the registration verbs record trust themselves,
  and the rule also covers a freshly cloned member repo's own tracked hooks,
  not just workspace-inherited ones.
- **Queued:** none (no workspace discoverable from the asking root)

### Q2: What happens non-interactively when hooks are untrusted?
- **Question:** When the create path resolves untrusted hooks and stdin is not
  a TTY, what should happen? Options: (a) do not run the hooks, leave the
  worktree in place, report, and exit 3 — resumable like a failing hook;
  (b) skip with a warning and exit 0. Recommendation: (a).
- **Verdict:** ANSWER
- **Answered by:** ORACLE
- **Answer:** Option (a). The repo's spec record already took this position:
  the worktree-hooks change rejected git's native `post-checkout` hook because
  its silence was disqualifying, and the delivery epic forbids silently
  dropping a gate in unattended runs — a parked member is the designed
  outcome for an unattended run that needs a human.
- **Cited:** completed/worktree-hooks, epic/autonomous-delivery

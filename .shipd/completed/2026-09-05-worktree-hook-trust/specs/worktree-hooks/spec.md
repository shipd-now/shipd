## ADDED Requirements

### Requirement: Hook trust ledger
id: hook-trust-ledger

The engine SHALL maintain a machine-local trust ledger at
`~/.shipd-trust.json` — a JSON object whose keys are SHA-256 fingerprints of
consented `post-worktree-scripts` lists, each value recording informationally
the declaring config path the consent was granted against — and SHALL treat a
resolved hooks list as trusted exactly when the list's fingerprint is a key
of the ledger, wherever the declaring config file lives, so consent granted
against a tracked config carries into every checkout and worktree copy of
the same list. When `hooks add` or `hooks remove` completes a registration
write, the engine SHALL record trust for the resulting resolved list only
when the effective list before the write was itself trusted or empty; if the
prior list was untrusted, then the engine SHALL record nothing, leaving the
consent gate to present the full list. If the ledger file is missing or
unreadable, then the engine SHALL treat it as holding no entries; if
recording a trust entry fails, then the engine SHALL print one stderr
warning and SHALL NOT fail the verb that obtained the consent.

#### Scenario: Registration through the verb auto-trusts
- **GIVEN** a repo with no configured hooks
- **WHEN** `worktree.py hooks add "cp .env.example .env"` runs and then a
  fresh worktree is created
- **THEN** the hook runs without any consent prompt and the ledger holds the
  one-item list's fingerprint as a key

#### Scenario: Trust carries into the worktree's copy of a tracked config
- **GIVEN** a repo whose tracked `.shipd-config.json` declares hooks
- **WHEN** `hooks trust` runs at the repo root and `hooks run` then runs from
  inside a created worktree, whose checkout carries its own copy of that
  config
- **THEN** the hooks execute without a prompt

#### Scenario: Adding onto an untrusted list does not trust it
- **GIVEN** a tracked config already declaring an untrusted item
- **WHEN** `worktree.py hooks add "echo mine"` registers a second item
- **THEN** no ledger entry is recorded and the next create still refuses (or
  prompts with) both items

#### Scenario: Out-of-band list edit invalidates trust
- **GIVEN** a trusted one-item list
- **WHEN** the declaring config file's list gains a second item by hand-edit
- **THEN** the resolved list is no longer trusted

#### Scenario: Malformed ledger reads as empty
- **GIVEN** a `~/.shipd-trust.json` holding invalid JSON
- **WHEN** the create path resolves configured hooks
- **THEN** the list is treated as untrusted and the verb proceeds through the
  consent gate without crashing

### Requirement: Hook consent gate
id: hook-consent-gate

When the worktree create path or `hooks run` would execute a resolved
non-empty `post-worktree-scripts` list that is not trusted, the engine SHALL
NOT run the hooks unconsented. While stdin is a TTY, the engine SHALL print
the declaring config file's path and every item and prompt for consent: an
affirmative reply SHALL record the trust entry and run the hooks, and any
other reply SHALL report the refusal and exit `3` with a created worktree
left in place. While stdin is not a TTY, the engine SHALL report the
untrusted source and items and exit `3` with a created worktree left in
place, naming as the resume path `hooks trust` followed by `hooks run` run
from the created worktree — never from the parked root, whose own directory
the scripts would otherwise set up. A trusted or empty list SHALL run
exactly as it did before the gate existed.

#### Scenario: Untrusted hooks refuse non-interactively
- **GIVEN** hooks inherited from an enclosing workspace config with no ledger
  entry
- **WHEN** `worktree.py my-change` runs with stdin not a TTY
- **THEN** the worktree exists, no hook ran, the output names the declaring
  config, each item, and the resume path — `hooks trust`, then `hooks run`
  from the created worktree — and the exit code is `3`

#### Scenario: Consent records and runs
- **GIVEN** the same untrusted hooks and an interactive terminal
- **WHEN** the user answers the prompt affirmatively
- **THEN** the ledger gains the entry, the hooks run in order, and the exit
  code is `0`

#### Scenario: Declined consent keeps the worktree
- **GIVEN** the same untrusted hooks and an interactive terminal
- **WHEN** the user declines the prompt
- **THEN** no hook runs, the worktree remains on disk, and the exit code is
  `3`

### Requirement: Hooks trust verb
id: worktree-hooks-trust-verb

The engine SHALL provide `worktree.py hooks trust`, which resolves the
effective `post-worktree-scripts`, prints the declaring config file's path
and every item, records the trust-ledger entry for that resolved list, and
exits `0`. If no hooks are configured, then the verb SHALL report that and
exit non-zero without writing to the ledger.

#### Scenario: Trust verb unblocks a parked create
- **GIVEN** a create that exited `3` on untrusted hooks
- **WHEN** `worktree.py hooks trust` runs and then `hooks run` runs from the
  worktree
- **THEN** the hooks execute without a prompt

#### Scenario: Nothing to trust is an error
- **GIVEN** a repo resolving no `post-worktree-scripts`
- **WHEN** `worktree.py hooks trust` runs
- **THEN** it reports nothing configured, exits non-zero, and the ledger is
  unchanged

## MODIFIED Requirements

### Requirement: Engine worktree create path
id: engine-worktree-create
base: 4125a3fec7b1

The engine SHALL provide a stdlib-only `worktree.py` script whose first
argument dispatches: `remove`, `prune-branches`, and `hooks` select those
verbs, and any other first argument is a change name for the create path with
an optional `--fresh` flag. The `remove` and `prune-branches` verbs SHALL
re-execute `worktree.sh` with the arguments passed through verbatim,
preserving its output and exit code. When the create path runs, the engine
SHALL invoke `worktree.sh`'s create path for the git mechanics from the repo
root with output inherited, and, when `worktree.sh` succeeds and
`.worktrees/<name>` did not exist before the invocation, SHALL execute the
resolved `post-worktree-scripts` through the hook consent gate; while the
worktree already existed (a reuse), the engine SHALL skip the scripts.

#### Scenario: Fresh create runs the configured scripts
- **GIVEN** a repo config declaring two trusted `post-worktree-scripts`
- **WHEN** `worktree.py my-change` runs and `.worktrees/my-change` does not
  yet exist
- **THEN** the worktree is created and both scripts run in declaration order
  with the new worktree as working directory

#### Scenario: Reused worktree skips the scripts
- **GIVEN** an existing `.worktrees/my-change` on branch `change/my-change`
- **WHEN** `worktree.py my-change` runs
- **THEN** the reuse notice is printed and no post-worktree script runs

#### Scenario: Remove passes through to the guarded helper
- **WHEN** `worktree.py remove my-change` runs against a dirty worktree
- **THEN** `worktree.sh`'s refusal report is printed and the exit code is `2`,
  exactly as invoking `worktree.sh remove my-change` directly

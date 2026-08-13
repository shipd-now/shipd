# shipd-port-tool
Status: verified
Epic: shipd-port
Theme: spec-engine

## Idea

Build `tools/port.py` in the shipd repo — the tested, ordered, boundary-aware
rename engine every later member of the shipd port runs.

### Motivation

The `shipd-port` epic decided the port is driven by a checked-in tested tool
rather than by hand or `sed`, because `am` is a substring of ordinary English and
a loose substitution would corrupt unrelated text across hundreds of files
(`.shipd/epics/shipd-port/epic.md`, Decisions). Nothing can be ported until that
tool exists.

### Details

- Add `tools/port.py` to the shipd repo: a stdlib-only Python 3 CLI with `plan`,
  `apply`, and `verify` verbs.
- Encode the epic's token map and path map as ordered, anchored rules — longest
  token first, never a bare `am`.
- Derive capability renames (`am-<name>` → `shipd-<name>`) by enumerating the
  source's `.shipd/verified/` rather than by a blind `am-*` regex.
- Read the source as tracked files at a git ref, so a run is reproducible and
  ignores dirty working state.
- Scan the result for residual unanchored matches and report them.
- Add `tools/tests/test_port.py` covering the map against synthetic fixtures.

Affected capabilities: `shipd-port` (added). Impact: the shipd repo only
(`tools/port.py`, `tools/tests/`); no file in shipd changes.

### Non-goals

- No git-history replay. The tool transforms a tree, not a commit sequence;
  shipd's history begins with the port commits and shipd keeps the lineage.
- No actual porting of shipd's tree — this member delivers the tool and its
  tests only. Members 2–3 run it.
- No two-way sync, no watch mode, no reverse (shipd → shipd) direction.
- No handling of `openspec/` or `.shipd/`; they are dropped, which the path
  map expresses as an exclusion, not a transformation.

## Implementation

- **Home and language.** `tools/port.py` in the shipd repo, stdlib-only Python 3.
  The constitution binds `plugins/s/skills/build/scripts/` to stdlib-only; this
  file sits outside that path but a rename tool has no honest need for a
  dependency, so the same rule applies. Rejected: `git filter-repo` — a
  third-party dependency, and it solves history rewriting, which is a non-goal.

- **Verbs and exit codes, matching the engine's existing grammar.**
  ```
  port.py plan   --source <shipd> --ref <ref> --dest <shipd>
  port.py apply  --source <shipd> --ref <ref> --dest <shipd>
  port.py verify --dest <shipd>
  ```
  Exit `0` clean, `1` a general error printed as `Error: …` on stderr, `2` a
  findings verdict. This mirrors `spec_gate.py` (0/2/1) and `worktree.sh remove`
  rather than inventing a new convention.

- **Source is a git ref, not the working tree.** `plan`/`apply` enumerate with
  `git -C <source> ls-files --with-tree=<ref>` and read content with
  `git -C <source> show <ref>:<path>`. A re-run at the same ref is byte-identical
  regardless of dirty state. Rejected: walking the working tree — a mid-edit
  re-run silently produces a different port.

- **Substitution is ordered and anchored; longest token first.** The rule list is
  applied in this order, and no rule ever matches a bare `am`:
  1. `s@shipd` → `s@shipd`
  2. `.shipd-config.json` → `.shipd-config.json`
  3. `SHIPD_WORKTREE_IDLE_MINUTES` → `SHIPD_WORKTREE_IDLE_MINUTES`
  4. `~/.shipd-memory` → `~/.shipd-memory`
  5. `~/.shipd/builds` → `~/.shipd/builds`
  6. `.cache/shipd` → `.cache/shipd`
  7. `plugins/s/` → `plugins/s/`
  8. `s:oracle` / `s:sub-agent` / `s:validator` → `s:…`
  9. `/s:` → `/s:`
  10. each enumerated capability slug `am-<name>` → `shipd-<name>` (word-bounded)
  11. a complete quoted `".shipd"` or `'.shipd'` → `".shipd"` / `'.shipd'`
  12. `.shipd/` → `.shipd/`
  13. `shipd` → `shipd`, then `Shipd` → `Shipd`

  Ordering is load-bearing, not cosmetic: `.shipd-config.json` contains the
  capability slug `shipd-config`, so rule 2 must consume it before rule 10 would
  rewrite it to `.shipd-config.json`'s corrupted sibling. The test suite pins
  this case explicitly.

  Rule 11 exists because the content directory appears in Python as a bare
  path *segment*, not a path — `DEFAULT_DIR = ".shipd"`, and
  `os.path.join(root, ".shipd", "planned", slug)` throughout the engine, the
  textual suite, and the evals runner. Rule 12 is anchored on the trailing
  slash and would miss every one of them, leaving the ported engine resolving
  a `.am` directory that does not exist. The match is the *complete* quoted
  string, so `".shipd-config.json"` and `".among"` are untouched.

- **Capability renames are enumerated, never regex-guessed.** The tool lists
  `<source>/.shipd/verified/` at the ref and takes the directories literally
  matching `am-<name>`; that set becomes rule 10. Rejected: a blind `am-\w+`
  regex — `shipd-plan` also occurs in running prose about the skill, and a regex
  cannot tell a capability slug from a sentence.

- **Path map, applied to destinations only.** `plugins/s/…` → `plugins/s/…`;
  `.shipd/…` → `.shipd/…`; `.shipd-config.json` → `.shipd-config.json`;
  `.shipd/verified/am-<n>/` → `.shipd/verified/shipd-<n>/`;
  `.shipd/completed/*/specs/am-<n>/` → `.shipd/completed/*/specs/shipd-<n>/`. Paths
  under `openspec/` and `.shipd/` are **excluded** — the epic drops them.

- **`apply` writes only mapped destinations.** It creates and overwrites exactly
  the paths the map produced and touches nothing else, so `LICENSE`, `.git`, and
  anything else already in the destination survive by construction rather than by
  a rule someone must remember. Rejected: wiping the destination first — it would
  destroy the repo's own history and license.

- **A repeatable `--include <prefix>` stages the port.** Without it the first
  `apply` would land the engine, the whole spec library, and the root infra in one
  unreviewable commit — the opposite of the epic's "reviewers read the map" goal.
  With it, member 2 ports `plugins/s/` and the root infra, member 3 ports `.shipd/`,
  and each lands as its own PR. Absent the flag the whole tree ports, so the
  staging is opt-in.

- **Residual scan is part of the run, not a separate discipline.** After writing,
  `apply` (and `verify` standalone) scans every written text file for a residual
  `shipd` or an anchored `am` form the map should have caught, and reports each
  as `<path>:<line>: <match>`. Findings exit `2` — the port is not silently
  declared clean.

- **Binary and non-UTF-8 files are copied byte-for-byte**, never substituted, and
  are excluded from the residual scan.

Risk: the map is correct on today's tree but a future shipd file could
introduce a new anchored form (say a `~/.am-designs` path). The residual scan is
the guard — an unmapped anchored form surfaces as a finding rather than passing
through silently.

# shipd-brand
Status: verified
Epic: shipd-port
Theme: developer-experience

## Idea

Give shipd its human-facing layer: a README under the new name and domain,
working docs restated for shipd's own discipline, and the repo hygiene files the
throwaway clone shipped with.

### Motivation

The token map rewrites strings, not meaning: it cannot redraw an ASCII banner
spelling `au.mikk`, cannot state the `shipd.now` domain that appears nowhere in
shipd, and cannot rewrite `AGENTS.md` to describe shipd's own plugin-cache and
worktree discipline. Those are the parts a reader meets first.

### Details

- Replace the throwaway README with shipd's own: a new banner, the `shipd.now`
  domain, and the skill table under `/s:`.
- Restate `AGENTS.md` (and its `CLAUDE.md` include) for shipd — its marketplace,
  its cache-snapshot rule, its content directory.
- Replace the clone's Node-template `.gitignore` with shipd's real one.
- Confirm the brand strings the tool *did* rewrite are correct rather than
  rewriting them again — the board header and the statusline banner.
- Port the three tracked files under `docs/`.

Affected capabilities: `shipd-port` (added). Impact: the shipd repo (`README.md`,
`AGENTS.md`, `CLAUDE.md`, `.gitignore`, `docs/`, and confirmation of
`plugins/s/skills/build/scripts/dashboard.py` and
`plugins/s/integrations/statusline.sh`).

### Non-goals

- No website, landing page, or docs deployment. `shipd.now` is recorded as a
  brand string; building anything at that domain is out of scope for this epic.
- No rewriting of `.shipd/README.md` or `.shipd/constitution.md` beyond what the
  token map already did — they are library artifacts ported in member 3 and their
  substance is unchanged.
- No untracked content. `docs/research/` is untracked in shipd and does not
  cross over; nothing here depends on it.
- No change to skill descriptions or trigger phrases; those ported with the
  plugin and are member 2's surface.

## Implementation

- **The banner is redrawn, not translated.** shipd's README opens with figlet
  ASCII art spelling `au.mikk` — slashes and underscores, containing no literal
  `shipd` string for the map to catch. It ports through untouched and wrong.
  A new banner spelling `shipd` replaces it wholesale.

- **`shipd.now` goes in the README and the manifest descriptions only.** It is
  the one genuinely new fact in this epic — it exists in no shipd file — so it
  is stated where a reader looks for it and nowhere else. Rejected: threading it
  through skill descriptions and the constitution, which would couple unrelated
  artifacts to a domain that hosts nothing yet.

- **`AGENTS.md` is rewritten, not ported.** Its whole subject is *this repo's*
  workflow: which marketplace, which cache path, which content directory, which
  plugin update command. The token map produces a document that is textually
  correct and substantively confused — it would describe shipd as "both the
  source and a consumer of the `s` plugin" while still narrating shipd's
  history. It is rewritten from the ported version, keeping the structure and the
  hard-won rules (worktree-per-change, PR-only, the review gate, snapshot
  refresh) and restating them for `s@shipd`.

- **Tool-rewritten brand strings are confirmed, not re-edited.** The board's brand
  block and the statusline's header comment both contain the literal `shipd`,
  so the map already produced `shipd`. This member asserts that rather than
  touching the files again — an unnecessary edit to a ported file is a diff a
  reviewer has to read for no reason.

- **The clone's `.gitignore` is replaced wholesale.** It is a stock Node template
  matching nothing in a Python repo, and keeping it would leave `__pycache__/`,
  `.venv/`, `.worktrees/`, and the runtime state paths untracked-but-noisy.
  shipd's ignores the content directory's `state.json` and `autopilot/`, so
  the ported equivalent names the `.shipd` paths.

Risk: `AGENTS.md` is the file every future shipd session reads as binding
instruction, so an error here propagates into every later change. It is
proofread against the ported reality — every path, command, and marketplace name
in it is checked to resolve — rather than trusted as prose.

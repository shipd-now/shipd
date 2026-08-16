# plugin-auto-update
Status: verified

## Idea

Wire shipd into Claude Code's native per-marketplace auto-update: the
installer and docs surface the one-time enable step, the doctor's
stale-snapshot hint names it, and the repo's own settings advertise it —
no custom updater is built.

### Motivation

A consumer's plugin snapshot goes stale until they hand-run
`claude plugin update s@shipd`, because Claude Code's built-in auto-update
is disabled by default for third-party marketplaces like `shipd` — while
the shipped launcher already applies any fetched snapshot automatically,
so enabling the fetch side completes the whole update chain.

### Details

- `install.sh` prints, after a successful install, an enable-auto-update
  notice: the `/plugin` → Marketplaces → `shipd` toggle, the
  `"autoUpdate": true` settings alternative, and the apply semantics
  (updates land after session start; a new session — or `/reload-plugins` —
  activates them; the launcher needs no change).
- README install mode and `docs/quickstart.md` document the same enable
  step; the quickstart gains it as part of the install step.
- `plugins/s/bin/shipd`'s stale-`snapshot` warn detail additionally names
  enabling marketplace auto-update as the durable fix alongside
  `claude plugin update s@shipd`.
- `.claude/settings.json`'s `extraKnownMarketplaces.shipd` entry gains
  `"autoUpdate": true`, so other checkouts self-advertise the default
  (trust-gated; inert on a machine where the user-scope install wins).

Affected capabilities: `shipd-install` (modified). Impact: `install.sh`,
`README.md`, `docs/quickstart.md`, `plugins/s/bin/shipd` (hint text only),
`plugins/s/skills/build/tests/test_shipd_cli.py` (hint assertion),
`.claude/settings.json`, plugin version bump. No new dependencies.

### Non-goals

- No custom update mechanism — no cron, no SessionStart hook, no updater in
  the launcher; Claude Code's native marketplace auto-update is the engine.
- No mutation of the user's `~/.claude/settings.json` from `install.sh` —
  the script stays deterministic and consent-clean; it instructs, never
  flips the toggle itself.
- No change to the doctor check semantics or exit contract — only the
  stale-snapshot warn's hint text grows, within the spec'd "names the newer
  version" contract.
- No change to the launcher (its newest-snapshot resolution already applies
  updates) and none to the in-flight `doctor-skill` change's files.

## Implementation

- **Native auto-update is the mechanism** (Claude Code docs,
  code.claude.com/docs/en/discover-plugins): per-marketplace toggle,
  default-off for third-party marketplaces; when enabled it refreshes the
  marketplace catalog and updates installed plugin snapshots shortly after
  session start, applying at the next launch or `/reload-plugins`.
  Rejected: a shipd-side updater (launcher-triggered `claude plugin update`
  or a SessionStart hook) — it duplicates a platform feature, adds
  unprompted network/process activity to every invocation, and the
  platform's randomized post-startup update already has the right shape.
- **Enablement is instructed, never performed.** There is no CLI flag to
  enable it (`claude plugin marketplace add --help` carries only
  `--scope`, verified), so the two real surfaces — the `/plugin` UI toggle
  and a `"autoUpdate": true` settings entry — are printed by `install.sh`
  and documented. The installer editing `~/.claude/settings.json` is
  rejected on the deterministic-script requirement and the repo's consent
  precedents (read-only doctor, consent-gated skill remedies).
- **The notice is stdout text after the success path**, exercised by the
  existing stub-claude test harness (`test_install.py` asserts its
  presence on success and its absence on the abort paths).
- **Doctor hint stays inside its spec:** the `doctor-verb` requirement pins
  that the stale-snapshot warn "names the newer version"; the hint text
  gains "enable auto-update for the shipd marketplace (see /plugin) or run
  claude plugin update s@shipd" — no `shipd-cli` delta needed, the pinned
  test string in `test_shipd_cli.py` is updated with it.
- **Verified premises:** `claude plugin update --help` states restart
  required to apply; the launcher's newest-version resolution shipped in
  `public-install` and was validator-confirmed; `claude plugin update
  s@shipd` refreshed snapshots repeatedly this session (0.6.103 → 0.6.104,
  → 0.6.107); the settings entry `extraKnownMarketplaces.shipd` exists at
  `.claude/settings.json:9`.
- Risk: the platform's auto-update behavior or toggle location changes;
  guard: the docs cite the toggle by its `/plugin` → Marketplaces path and
  keep `claude plugin update s@shipd` documented as the always-works manual
  path.

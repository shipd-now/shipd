# plan-version-stamp
Status: verified

## Idea

Debugging the plan-skill behavior is currently blind to versioning: when a
session misbehaves there is no way to tell whether it is running a stale
plugin snapshot or genuinely ignoring the current skill text. The snapshot
version lives only in `plugin.json` and the cache directory name — invisible
in a session. Three iterations on the `/s:plan` UX have already been
diagnosed by screenshot, and each time "is this even the new version?" was
unanswerable.

Fix: `/s:plan` announces the running skill version in its first user-visible
sentence, read at runtime from the running snapshot's own manifest
(`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`), so the version on
screen always names the snapshot actually loaded — a stale session becomes
instantly recognizable.

### Non-goals

- No version stamps in the other skills yet — the plan skill is the one under
  active iteration; the convention can spread later if it earns its keep.
- No baked-in version string in SKILL.md prose (it would drift from
  `plugin.json`); the version is read at runtime from the manifest.
- No statusline or engine changes.

Affected capabilities: `shipd-plan` (added — `version-announcement`). Impact:
`plugins/s/skills/plan/SKILL.md`,
`plugins/s/.claude-plugin/plugin.json`.

## Implementation

- **Runtime read, not a baked string.** The skill's first action reads
  `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`; `${CLAUDE_PLUGIN_ROOT}`
  resolves to the cache snapshot the session actually loaded, so the version
  shown is by construction the running one. Rejected: writing the version
  into SKILL.md at release time — one forgotten sync and the stamp lies.
- **Placement: the opening sentence.** SKILL.md instructs the Planner to
  include `am:plan v<version>` in its first user-visible status sentence
  (e.g. "am:plan v0.2.11 — investigating the repo first"), before or with
  the start of investigation. One line in the flow preamble, no new flow
  step.
- **Version bump to 0.2.11** in `plugins/s/.claude-plugin/plugin.json`, same
  PR, per the cache-snapshot rule in AGENTS.md — which is also what makes the
  stamp immediately testable: a session showing v0.2.11 provably runs this
  change.

Risks: none beyond prompt adherence itself; if the model skips even the
version stamp, that too is a diagnostic (the session is provably not
following the current skill, or not running it).

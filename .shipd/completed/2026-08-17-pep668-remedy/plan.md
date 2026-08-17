# pep668-remedy
Status: verified

## Idea

Make the doctor preflight's pip hints — and the `/s:doctor` remedies built on
them — runnable on PEP 668 externally-managed interpreters.

### Motivation

On a Homebrew (externally-managed) Python, `/s:doctor`'s consented
`python3 -m pip install …` remedies fail unconditionally with PEP 668's
`externally-managed-environment` error, so the user consents to a repair that
was doomed before it ran. The remedy the skill offers must be one the
interpreter that prints the finding can actually execute.

### Details

- `shipd doctor`'s `textual`/`pydantic` hints gain a PEP 668 probe: when the
  running interpreter's stdlib carries the `EXTERNALLY-MANAGED` marker, the
  hint prepends `--user --break-system-packages` to its existing form
  (`-r requirements.txt` or the pinned specifier).
- `/s:doctor`'s textual/pydantic remedy rows relay the command the finding's
  own detail names instead of hardcoding one, and the consent dialog states
  the `--break-system-packages` flag explicitly when it is present.

Affected capabilities: `shipd-cli` (modified `doctor-verb`), `shipd-doctor`
(modified `doctor-remedy-boundaries`). Impact: `plugins/s/bin/shipd`,
`plugins/s/skills/doctor/SKILL.md`,
`plugins/s/skills/build/tests/test_shipd_cli.py`,
`plugins/s/.claude-plugin/plugin.json` (version bump). No new dependencies.

### Non-goals

- No venv or pipx machinery: pipx installs applications, not importable
  libraries, and a shipd-owned venv could not be imported by the `python3`
  running the engine without `sys.path` surgery the constitution's
  stdlib-only rule forbids.
- No change to the one-remedy-round contract: the skill still never retries a
  failed remedy with a different approach — the fix is proposing a runnable
  command in the first place.
- No silent override: `--break-system-packages` is only ever run after a
  consent dialog that names the flag.
- No change to the difft, gh, git, snapshot, or statusline remedies.

## Implementation

- **Detection lives in the binary; the skill relays.** `_install_hint`
  (`bin/shipd:381-388`) composes the full runnable command; the skill's
  remedy becomes `python3 -m ` + the hint the finding's detail carries.
  One source of truth — the environment logic is testable Python, not prose.
  Rejected: probing PEP 668 in SKILL.md prose — unverifiable by the engine's
  test suite and duplicated logic.
- **The probe**: `os.path.isfile(os.path.join(sysconfig.get_path("stdlib"),
  "EXTERNALLY-MANAGED"))`, stdlib-only and read-only, wrapped in a helper
  with an injectable parameter (the `check_pydantic(root, find_spec=…)`
  pattern beside it) so tests exercise both branches without a real Homebrew
  interpreter. Verified premise: the marker is present at that path on the
  machine that hit the failure (Homebrew Python 3.14.6), and
  `python3 -m pip install --user --break-system-packages --dry-run
  "pydantic>=2.12,<3"` exits 0 there ("Would install pydantic-2.13.4 …")
  while the unflagged form fails with the PEP 668 error.
- **Flag choice**: `--user --break-system-packages` — installs into the user
  site (importable by the same interpreter, Homebrew's own site-packages
  untouched), and is the pair PEP 668's error text itself sanctions for
  consenting users. The flags prepend to both existing hint forms
  (`-r requirements.txt` and the pinned specifier); the unmanaged-interpreter
  forms stay byte-identical to today's.
- **Consent stays informed**: the remedy-boundaries contract gains the rule
  that a relayed command carrying `--break-system-packages` is stated with
  the flag visible in the dialog option — overriding a distro guard is part
  of what the user consents to.
- **Version bump** `plugins/s/.claude-plugin/plugin.json` to the next free
  patch version in the same PR (0.6.129 at planning time), per the
  cache-snapshot rule.
- Risk: pip changes its PEP 668 interface someday — mitigated by pinning
  nothing new: the flags are additive to hints that already exist, and an
  unmanaged interpreter's behavior is unchanged.

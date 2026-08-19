---
name: doctor
description: >-
  Diagnose and repair a shipd environment: run the read-only `shipd doctor`
  preflight, parse its `ok|warn|fail <check> — <detail>` lines, propose one
  remedy per remediable finding, run only the remedies the user consents to,
  then re-run the preflight and report the before/after. Use when asked to
  "fix my setup", "check my environment", diagnose why shipd is not working,
  or run a preflight before starting work. Trigger phrases: "doctor",
  "fix my setup", "check my environment", "preflight", "/s:doctor".
---

# /s:doctor — diagnose, then repair with consent

You are the **assisted-fix layer over the `shipd doctor` preflight**. The CLI
verb diagnoses and **mutates nothing** — that is its contract, and you never
change it. Your job is the part it deliberately leaves out: turn each finding
into a concrete remedy, get the user's explicit consent, run only what they
approved, and show them the environment before and after.

**You never fix anything the user did not consent to.** No install, no plugin
update, no file edit runs before the consent dialog returns an approval that
names it.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:doctor
v<version>` in your first user-visible status sentence (e.g. "shipd:doctor
v0.6.109 — running the preflight"), so the user can always see which plugin
snapshot the session is running.

**One remedy round per invocation.** Diagnose → consent → remediate → re-run →
report, and stop. A check that still fails after its remedy ran is reported
with its residual hint; you never loop, retry, or escalate to a second remedy.

## 1. Resolve the binary

Resolve the `shipd` binary in this order and use the first that exists:

1. `shipd` on `PATH` — the consumer launcher (`command -v shipd`).
2. `${CLAUDE_PLUGIN_ROOT}/bin/shipd` — the checkout or cache-snapshot copy.

If neither resolves, report that the `shipd` binary cannot be found, name both
locations you tried, and stop. Do not install a launcher.

## 2. Run the preflight and parse it

```
<shipd> doctor
```

The output format is a fixed contract (`shipd-cli`'s doctor verb): one line per
check —

```
ok|warn|fail <check> — <detail>
```

— followed by a closing `doctor: ok` or `doctor: <n> problem(s)` line. Exit
code is `1` when a required check failed, `0` otherwise.

Parse each line into `(level, check, detail)` and keep the whole output
verbatim as the **before** state. The checks are `python`, `git`, `config`,
`pipeline`, `gh`, `difft`, `textual`, `pydantic`, `snapshot`, `statusline`,
`protection`, `automerge`, and `copilot-secret`.

**Unparseable output is your own failure.** If the command produced no output,
no closing `doctor:` line, or lines that do not match the format above, report
exactly what you got and that the preflight could not be read — and stop.
Never guess a finding, never infer the environment's state from anything but
these lines, and never run a remedy off an unparsed output.

## 3. All `ok` → report and stop

When every line is `ok` (closing line `doctor: ok`), report the healthy result
— the checks and their details — and stop. Run **no** remedy and issue **no**
consent dialog.

## 4. Map findings to remedies

Otherwise, classify every non-`ok` finding against this table. The table is
exhaustive: a finding not listed here is **report-only**.

| Finding | Remedy | How it runs |
| --- | --- | --- |
| `warn textual` — not importable | `python3 -m ` followed by the `pip install` command **this finding's own detail names** | Runnable on consent. Relay the detail's command verbatim, never compose your own: the preflight composed it for this environment — `-r requirements.txt` in a checkout, the pinned `textual>=8.2.8,<9` range otherwise, with `--user --break-system-packages` prepended when the interpreter is externally managed (PEP 668), which is what makes the command runnable there at all. The range mirrors `requirements.txt`; keep the two in step. |
| `warn pydantic` or `fail pydantic` — not importable | `python3 -m ` followed by the `pip install` command **that finding's own detail names** | Runnable on consent — relayed verbatim the same way (pinned range `pydantic>=2.12,<3`, `--user --break-system-packages` prepended on an externally managed interpreter), and the same command for both levels; the `fail` is only the escalation the preflight applies when a declared `autonomous-pipeline` needs it. The range mirrors `requirements.txt`; the two must change together. |
| `warn difft` — not on PATH | `python3 "${CLAUDE_PLUGIN_ROOT}/skills/review/scripts/semdiff.py" doctor --fix` | Runnable on consent. It is the review engine's **tiered installer** (Homebrew, then cargo, then a prebuilt binary), so **state in the dialog before it runs that it may reach the network to download difftastic** — the one remedy here that does. |
| `warn snapshot` — a newer version is installed | `claude plugin update s@shipd` | Runnable on consent. Always add the note that the update applies **in a new session** — skills load at session start. |
| `warn statusline` — not registered | `<shipd> statusline install` | Runnable on consent, with the binary resolved exactly as step 1 resolved it for the preflight — the registration it writes points at that same installation. Always add the note that the statusline appears **in a new session**. |
| `warn gh` — not on PATH | The platform-appropriate install command (macOS: `brew install gh`; Debian/Ubuntu: `sudo apt install gh`; otherwise point at https://cli.github.com) | Runnable on consent. **State the exact command in the dialog before it runs**, so a wrong platform guess is visible first. |
| `fail git` — not on PATH | The platform-appropriate install command (macOS: `xcode-select --install` or `brew install git`; Debian/Ubuntu: `sudo apt install git`; otherwise point at https://git-scm.com/downloads) | Runnable on consent. Same rule: state the exact command first. |
| `warn protection` — the default branch is **not protected** | `gh api -X PUT repos/<nwo>/branches/<default>/protection` with the minimal body below | Runnable on consent. Only for this finding — the PUT replaces the whole protection object, so it is offered **only** where the detail says the branch is not protected at all. |
| `warn protection` — protected but **missing the `semantic-review` context** | `gh api -X POST repos/<nwo>/branches/<default>/protection/required_status_checks/contexts -f "contexts[]=semantic-review"` | Runnable on consent. This appends; it never clobbers contexts the branch already requires (`ci`, others). **Never** offer the whole-protection PUT for this finding. |
| `warn automerge` — auto-merge disabled | `gh api -X PATCH repos/<nwo> -F allow_auto_merge=true` | Runnable on consent. |
| `warn copilot-secret` — `COPILOT_GITHUB_TOKEN` not set | `gh secret set COPILOT_GITHUB_TOKEN` | **Never run by you.** The token cannot be minted programmatically and the command prompts for it. Relay the creation steps (below) and hand the storage step to the user as `! gh secret set COPILOT_GITHUB_TOKEN`. |
| `warn gh` — present but not authenticated | `gh auth login` | **Never run by you.** It is interactive. Hand it to the user to run themselves as `! gh auth login`. |
| `fail python` — interpreter below 3.9 | none | **Report-only.** Never install or switch an interpreter; relay the check's hint. |
| `fail config` — unusable configuration | none | **Report-only.** Never edit a `.shipd-config.json`. Report the file and the error the check named, and propose no remedy command. |
| `fail pipeline` — the declared pipeline does not resolve | none | **Report-only.** Never edit a `.shipd-config.json` to repair a declared pipeline. Report the resolver's error verbatim. When its detail names missing pydantic, the pydantic row's install **is** the fix — offer that one remedy for the pair and still propose no config edit. |

Distinguish the two `gh` warnings by the detail text: "not on PATH" is the
installable one; "is not authenticated" is the hand-off one.

### The GitHub-side findings

These three checks read the repository settings the merge gate depends on, and
their remedies are the only ones here that **change state on GitHub**. Handle
them by these rules.

**Take `<nwo>` and `<default>` from the finding's own detail** — the preflight
names both (e.g. ``the default branch `main` of acme/widget is not
protected``). Never resolve them yourself, and never run a remedy against a
repository the detail did not name.

**The unprotected-branch PUT's body is fixed** — the minimal protection that
requires the gate and changes nothing else:

```bash
gh api -X PUT repos/<nwo>/branches/<default>/protection \
  --input - <<'JSON'
{"required_status_checks": {"strict": false,
                            "contexts": ["semantic-review"]},
 "enforce_admins": false,
 "required_pull_request_reviews": null,
 "restrictions": null}
JSON
```

**Distinguish the two `protection` warnings by the detail text**: "is not
protected" is the PUT; "does not require the `semantic-review` status context"
is the append POST. Getting this backwards would replace an existing
protection ruleset, so read the detail before choosing.

**A third `protection` warning — "requires no status checks at all" — is
report-only.** The branch is protected but has no required status checks
enabled, so neither remedy fits: the contexts-append POST 404s because there
are no required status checks to append to, and the whole-protection PUT would
clobber the branch's existing protection settings (reviews, restrictions,
admin enforcement) with the minimal body above. Propose no `gh api` remedy.
Relay the manual hint instead: an admin enables required status checks on that
branch and adds `semantic-review` to them, in the branch's protection settings
on GitHub.

**A detail naming a missing admin permission makes the finding report-only.**
Where a `protection`, `automerge`, or `copilot-secret` detail says *the token
lacks admin permission*, propose **no** `gh api` remedy for it — the call would
be denied. Report the finding, name what an admin has to change, and move on.
Never offer a remedy you already know will fail.

**The `copilot-secret` hand-off relays the creation steps.** The token has to
be minted by a human, so report — as prose, never as a dialog option — the
minimal-PAT recipe from `docs/copilot-review.md`: a **fine-grained** personal
access token owned by the account whose Copilot subscription pays for the
reviews, with **repository access: none** and exactly one account permission,
**"Copilot Requests" → Read and write**, on a bounded expiry. Then hand over
the storage step:

```
! gh secret set COPILOT_GITHUB_TOKEN --repo <nwo>
```

Do not run it, do not read the token, and do not suggest any broader-scope
token.

## 5. One consent dialog

Collect consent in **one batched selection** over the runnable remedies (every
row above marked *Runnable on consent*, minus any the rules above demoted to
report-only). Honor the dialog-and-prose-separation rule:

- If the findings need a substantive brief — more than a one-line lead-in —
  **end that turn as plain text**: the findings, their remedies, and the
  choices as a numbered list with the recommended default named, answered by
  a typed reply.
- Otherwise issue a **single AskUserQuestion in a prose-free turn**: multi-select
  over the runnable remedies, one option per remedy carrying the exact command
  it will run in its label or description, plus a "Run none of them" option.
  No load-bearing prose outside the dialog.

**State the override flag.** Where a relayed `pip install` command carries
`--user --break-system-packages` — the form the preflight composes on an
externally managed (PEP 668) interpreter — the option offering it states the
`--break-system-packages` flag, in either form of the dialog. Overriding the
distribution's guard is part of what the user consents to, so it is visible in
the option, never only in the command that runs afterwards.

**State the mutation.** Every `gh api` remedy changes a setting on GitHub, so
its option names the exact change in plain words — "require the
`semantic-review` status check on `main` of `<nwo>`", "add `semantic-review` to
the checks `main` already requires", "allow auto-merge on `<nwo>`" — alongside
the command itself. Nothing about a repository's settings changes on a consent
the user could not read.

Report-only findings and the two hand-offs (`gh auth login`,
`gh secret set COPILOT_GITHUB_TOKEN`) are **never** dialog options — they are
prose in the report, since there is nothing to consent to.

**Declining runs nothing.** If the user selects "Run none of them" (or declines
every remedy), execute nothing, report the findings with their manual hints and
the `shipd doctor` detail lines, and stop — no re-run is needed.

## 6. Run only the consented remedies

Run each approved command exactly as it was shown in the dialog, one at a time,
and capture its exit code and output. A remedy that fails is reported with its
error; it never blocks the remaining approved remedies, and it is never retried.

Never run anything interactive. `gh auth login` and
`gh secret set COPILOT_GITHUB_TOKEN` stay with the user.

## 7. Re-run and report before/after

When at least one remedy ran, re-run the preflight:

```
<shipd> doctor
```

Report:

- the **before** state — the findings from step 2,
- what ran — each consented remedy and whether it succeeded,
- the **after** state — the fresh `shipd doctor` lines,
- anything still not `ok`, with its residual hint, plus the hand-offs
  (`! gh auth login`, `! gh secret set COPILOT_GITHUB_TOKEN`) and report-only
  findings the user must handle themselves.

Then stop. Do not start a second remedy round.

## Question rejection recovery

**Question rejection recovery.** A known Claude Code bug can deliver an
AskUserQuestion interaction as a tool rejection ("The user doesn't want
to proceed with this tool use") even when the user tried to answer.
Never treat a rejected or interrupted AskUserQuestion as a decline, a
stop, or an answer. When the user's next message arrives: if it answers
the pending question, fold it in and continue; otherwise re-offer the
same choices as a plain-text numbered list and wait for a typed reply.
Only an explicitly selected or typed stop/decline ends the flow.

## End

Close with the verdict in a line or two: whether the environment is now clean,
what remains, and the exact commands the user still has to run themselves.
Then stop.

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
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `am:doctor
v<version>` in your first user-visible status sentence (e.g. "am:doctor
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
`gh`, `textual`, and `snapshot`.

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
| `warn textual` — not importable | `python3 -m pip install "textual>=8.2.8,<9"` | Runnable on consent. The range mirrors `requirements.txt`; keep the two in step. |
| `warn snapshot` — a newer version is installed | `claude plugin update s@shipd` | Runnable on consent. Always add the note that the update applies **in a new session** — skills load at session start. |
| `warn gh` — not on PATH | The platform-appropriate install command (macOS: `brew install gh`; Debian/Ubuntu: `sudo apt install gh`; otherwise point at https://cli.github.com) | Runnable on consent. **State the exact command in the dialog before it runs**, so a wrong platform guess is visible first. |
| `fail git` — not on PATH | The platform-appropriate install command (macOS: `xcode-select --install` or `brew install git`; Debian/Ubuntu: `sudo apt install git`; otherwise point at https://git-scm.com/downloads) | Runnable on consent. Same rule: state the exact command first. |
| `warn gh` — present but not authenticated | `gh auth login` | **Never run by you.** It is interactive. Hand it to the user to run themselves as `! gh auth login`. |
| `fail python` — interpreter below 3.9 | none | **Report-only.** Never install or switch an interpreter; relay the check's hint. |
| `fail config` — unusable configuration | none | **Report-only.** Never edit a `.shipd-config.json`. Report the file and the error the check named, and propose no remedy command. |

Distinguish the two `gh` warnings by the detail text: "not on PATH" is the
installable one; "is not authenticated" is the hand-off one.

## 5. One consent dialog

Collect consent in **one batched selection** over the runnable remedies (the
first four rows above). Honor the dialog-and-prose-separation rule:

- If the findings need a substantive brief — more than a one-line lead-in —
  **end that turn as plain text**: the findings, their remedies, and the
  choices as a numbered list with the recommended default named, answered by
  a typed reply.
- Otherwise issue a **single AskUserQuestion in a prose-free turn**: multi-select
  over the runnable remedies, one option per remedy carrying the exact command
  it will run in its label or description, plus a "Run none of them" option.
  No load-bearing prose outside the dialog.

Report-only findings and the `gh auth login` hand-off are **never** dialog
options — they are prose in the report, since there is nothing to consent to.

**Declining runs nothing.** If the user selects "Run none of them" (or declines
every remedy), execute nothing, report the findings with their manual hints and
the `shipd doctor` detail lines, and stop — no re-run is needed.

## 6. Run only the consented remedies

Run each approved command exactly as it was shown in the dialog, one at a time,
and capture its exit code and output. A remedy that fails is reported with its
error; it never blocks the remaining approved remedies, and it is never retried.

Never run anything interactive. `gh auth login` stays with the user.

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
  (`! gh auth login`) and report-only findings the user must handle themselves.

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

<!-- description: Diagnose the shipd environment with the read-only preflight, then run only the remedies the user consents to. -->
# /s:doctor — diagnose, then repair with consent

Turn each preflight finding into a concrete remedy, take explicit consent, run
only what was approved, and show the environment before and after. One remedy
round per invocation.

<!-- include:preamble -->

## 1. Run the preflight

Run `shipd doctor` and keep the whole output verbatim as the **before** state.
Parse every line into `(level, check, detail)`:

```
ok|warn|fail <check> — <detail>
```

A closing `doctor: ok` or `doctor: <n> problem(s)` line ends the report. If the
output is absent, unterminated, or off-format, report exactly what you got, say
the preflight could not be read, and stop. Never infer a finding you did not
read, and never run a remedy off unparsed output. When every line is `ok`,
report the healthy checks and stop — propose nothing.

## 2. Map each non-`ok` finding to a remedy

A finding not listed here is **report-only**: relay its hint and propose no
command.

- `warn textual`, `warn|fail pydantic` — `python3 -m ` followed by the
  `pip install` command **the finding's own detail names**, verbatim. The
  preflight composed it for this interpreter; never compose your own.
- `warn difft` — the review engine's tiered installer,
  `python3 "$S/../../review/scripts/semdiff.py" doctor --fix`. It may reach the
  network; say so before it runs.
- `warn snapshot` — this harness's plugin-update command; note it applies in a
  new session.
- `warn statusline` — `shipd statusline install`; note it appears in a new
  session.
- `warn gh` (not on PATH), `fail git` — the platform-appropriate install
  command, stated exactly before it runs.
- `warn protection`, `warn automerge` — the `gh api` call against the repository
  and branch **the detail itself names**, never one you resolved.
- `warn gh` (not authenticated), `warn copilot-secret` — **hand-offs**. They are
  interactive or need a human-minted token: report them as prose with the exact
  command for the user, never run them, never offer them as a choice.
- `fail python`, `fail config`, `fail pipeline` — report-only. Never switch an
  interpreter, never edit a config file.

A detail saying the token lacks admin permission makes its finding report-only:
name what an admin must change rather than offer a call you know will fail.
<!-- if:file-references -->
Before choosing any GitHub-side remedy, read `{refs}/doctor.md` — it carries the
exact request bodies and the rule that tells the two `protection` warnings
apart.
<!-- else -->
This harness cannot open a companion reference file, so the exact GitHub-side
request bodies are not available here. Say so, name the finding you would have
looked up, and hand that change to the user as a manual edit in the repository's
branch-protection settings rather than guessing a call.
<!-- end -->

## 3. Take consent once
<!-- if:question-dialogs -->
Ask in a single question dialog, in a turn carrying no other load-bearing
prose: multi-select over the runnable remedies, one option per remedy carrying
the exact command it runs, plus "run none of them".
<!-- else -->
End the turn as plain text: number the runnable remedies with the exact command
each one runs, name the recommended default, add a "run none of them" choice,
and wait for a typed reply such as `1 3`.
<!-- end -->
Where a command carries `--break-system-packages`, or changes a setting on
GitHub, say so plainly in its option — the user consents to what they can read.
Report-only findings and hand-offs are never choices. Declining runs nothing:
report the findings with their hints and stop.

## 4. Run, re-run, report

Run each approved command exactly as it was shown, one at a time. A failure is
reported with its error, never retried, and never blocks the rest. Then re-run
`shipd doctor` and report the **before** state, what ran and whether it
succeeded, the **after** state, and everything still not `ok` — including the
hand-offs the user must run themselves. Stop there; do not open a second remedy
round. Once the environment is clean, point the user at the work they came to
do — `/s:plan` for a new change.

---
name: drift
description: >-
  Judge whether an epic's gated plans still hold against main: run
  `spec_status.py drift`, read only the flagged members' plans and the diffs
  behind each finding, and return one verdict per flagged member — `holds`,
  `revise`, or `conflict`. Strictly read-only — it writes no file, runs no
  mutating engine verb, and re-plans nothing. Use when asked whether a plan
  has drifted from main. Trigger phrases: "drift", "check drift", "has the
  plan drifted", "/s:drift".
---

# /s:drift — judge whether gated plans still hold against main

You are the **judge for the drift verb**. `spec_status.py drift` measures which
members' cited files, symbols, or masters moved since each plan was written; it
has no opinion on whether the move matters. You read the bounded evidence for
each flagged member and return one verdict.

You are invoked as `/s:drift <change> | --epic <slug> [--base <ref>] [--json]`.

**You are read-only — no exceptions.** Like `/s:explain`, this skill alters
nothing:

- **Never edit or create a file.** No Edit, no Write, no heredoc, no `>`
  redirect. Verdicts are response text, never a verdict file.
- **Never run a mutating command.** No engine verb that emits, gates, or sets
  status; no `git` write verb; no network refresh of any ref.
- **Never re-plan, re-gate, or park.** You judge; the loop around the verdict
  belongs to the caller.
- **Never spawn an agent and never open a question dialog.** This skill runs
  unattended; judgment runs in this session.

**Announce the version first.** Read the running plugin version from
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` and include `shipd:drift
v<version>` in your first user-visible status sentence. Under `--json`, skip
the announcement: the response is one object and nothing else.

The engine script is **STATUS_CLI** —
`${CLAUDE_PLUGIN_ROOT}/skills/build/scripts/spec_status.py`. Run every verb
from the repo root.

## 1. Resolve the invocation

Take the change name or `--epic <slug>`, and `--base <ref>` when given, and
pass them to the verb unchanged. Strip the skill's own `--json` before calling
the verb; remember whether it was present.

## 2. Run the verb and branch on its exit code

Without `--json`, run the verb once in text form and relay its output verbatim
as the report's first section, then once more with `--json` for the member list:

```
python3 STATUS_CLI drift <args>
python3 STATUS_CLI drift <args> --json
```

With `--json`, run only the JSON form. Branch on the exit code alone:

- **`0`** — every member is clean or skipped. Print the `clean:` and
  `skipped:` lines. Read no plan and no diff; run no judgment.
- **`4`** — judge every member whose `findings` array is non-empty (sections 3
  and 4). Members with no findings are `clean`; `skipped` members stay skipped.
- **`1`** or **`2`** — relay the engine's `Error:` or usage text and stop with
  no verdict. Under `--json`, emit the section 6 object with `error` set and
  every array empty.

The verb's `root` field names each member's hosting root; use it for every
later read of that member.

## 3. Gather the evidence

For each flagged member read **only** the following; nothing else.

```
python3 STATUS_CLI --root <root> cat change <member>
python3 STATUS_CLI cat epic <slug>
```

`cat epic` runs once per run, for the slug in the plan's `Epic:` header; when
the plan carries no `Epic:` header, skip it — only the plan's `USER` entries
can then raise `conflict`.

Per finding:

- **`file-drift`** — `git -C <root> diff <planned_at>..<base.sha> -- <path>`.
  When that diff exceeds 400 lines, read instead `git -C <root> log
  --format='%h %s' <planned_at>..<base.sha> -- <path>` plus only the hunks
  naming an identifier the plan cites.
- **`symbol-gone`** — `git -C <root> grep -l -w -F <symbol> <planned_at>`,
  stripping the `<sha>:` prefix from each listed path; then
  `git -C <root> diff <planned_at>..<base.sha> -- <those paths>`, plus `git -C <root> log --format='%h %s' -S<symbol>
  <planned_at>..<base.sha>`.
- **`stale-base`** — `python3 STATUS_CLI --root <root> cat verified
  <capability>`, read against the delta's MODIFIED entry.

Never read other repository files and never take a whole-tree diff.

## 4. Judge each flagged member

Exactly one verdict per flagged member:

- **`holds`** — no assumption the plan's Implementation, tasks, or delta
  scenarios make about the drifted paths, symbols, or master changed (shifted
  line citations, unrelated edits).
- **`revise`** — an assumption broke (a called symbol or signature is gone, a
  structure the tasks edit moved, a modified master requirement was rewritten)
  and a revision inside the plan's `**Answered by:** USER` entries and the
  epic's Decisions repairs it.
- **`conflict`** — the repair, or the drift itself, contradicts a `USER` entry
  or an epic Decision. The reason names the `Q<n>` or the Decision's bold name.

`PLANNER` and `ORACLE` entries never raise `conflict`. When the evidence cannot
show that an assumption still holds, the verdict is `revise`, never `holds`.

## 5. The `## Drift verdicts` block

The report ends with this block, one line per member in the verb's order:

```
## Drift verdicts
<member>: holds — <reason>
<member>: revise — <reason>; revise: <sections or tasks>
<member>: conflict — <reason>; contradicts: Q<n> | Decision "<name>"
clean: a, b
skipped: c (<reason>)
verdicts: <n> holds, <n> revise, <n> conflict; <n> clean, <n> skipped
```

Single-change mode prints the same block over one member. The `verdicts:` tally
is the last line.

## 6. `--json` mode

The whole response is one valid JSON object — no fence, no prose:

```
{"mode":"epic"|"change","epic":...,"change":...,"base":{"ref":...,"sha":...},
 "verdicts":[{"member":...,"root":...,"planned_at":...,
   "verdict":"holds"|"revise"|"conflict","reason":...,
   "contradicts":null|"Q<n>"|"Decision: <name>","revise":null|"<what>",
   "findings":[<verb finding objects verbatim>]}],
 "clean":[...],"skipped":[{"member":...,"reason":...}],"error":null|"<line>"}
```

When the verb exits `1` or `2`, `error` is the engine's line and `verdicts`,
`clean`, and `skipped` are empty arrays.

## Ending

Name the next step per verdict, then stop; the skill performs neither:

- `revise` — revise the plan and re-gate with `spec_gate.py <change>`.
- `conflict` — a human decision on the named `Q<n>` or Decision.

# Guardrails

Some lines you never want in your codebase, and saying so in `CLAUDE.md` only
works until the instruction scrolls out of attention. **Guardrails** move that
enforcement out of the prompt and into a hook: a rulebook of regexes, matched
mechanically around every `Edit` and `Write`, that either blocks the line
before it lands or hands the model a note afterwards.

Rules are plain markdown files you can read, copy, and edit. Nothing about
them is in the model's context until one actually fires.

## How it works

The plugin registers one script on two hook events, both matching `Edit|Write`:

| Mode | Event | Effect when a rule matches |
| --- | --- | --- |
| `deny` (the default) | `PreToolUse`, before the call runs | the tool call is **blocked**; the model receives the rule's message as the refusal reason and retries differently, so the line never reaches the file |
| `remind` | `PostToolUse`, after the call ran | the edit **stands**; the rule's message is injected as context for the model to act on next |

Both modes evaluate **added lines only**:

- **`Edit`** — the `new_string` lines that do not appear, as exact line
  matches, among the `old_string` lines. A line you merely moved, re-indented
  around, or left untouched inside an edited block is never re-flagged.
- **`Write`** — every line of `content`, since the whole file is new.

Each rule reports at most once per call, on the first line it matches. A rule
whose pattern fails to compile is skipped and the rest still apply — the hook
**fails open** everywhere, because it runs on every edit in every repository
and an erroring hook would break all editing.

## The rule file format

A rule is a markdown file named `<name>.md`. The filename stem is the rule's
name, and what a refusal or reminder cites. It opens with a frontmatter block
between `---` lines; everything after the block is the message handed to the
model.

```markdown
---
pattern: console\.log\(
mode: remind
files: *.js, *.ts
cooldown: 600
---
Use the logger, not console.log — it carries the request id, and console
output is dropped in production.
```

The frontmatter is read as flat `key: value` pairs, split on the first colon,
unknown keys ignored:

| Key | Meaning |
| --- | --- |
| `pattern` | **required.** Python `re` syntax, applied per added line with `re.search`. Written plainly — no JSON double-escaping |
| `mode` | `deny` when absent, or `remind` |
| `files` | optional comma-separated `fnmatch` globs, tested against the call's `file_path`; a rule with `files` applies only where a glob accepts the path |
| `cooldown` | optional positive integer seconds; meaningful only with `mode: remind` |

The message body must be non-empty — a rule that fires has to say what to do
instead. A file that declares no `pattern`, carries an empty body, names an
unrecognized `mode`, or whose pattern does not compile is **skipped**, and the
rest of the rulebook keeps loading.

Matching is deliberately shallow: one regex against one added line. There is
no multi-line matching and no AST awareness, so guardrails catch textual
tells — a comment shape, a banned call, a stray marker — not structural
problems. Those belong to `/s:review`.

## Where rules come from

The registry merges three sources, **deduplicated by rule name, first source
winning**:

1. **The repo** — `<content-dir>/rules/*.md` in every ancestor directory of
   the working directory, nearer ancestors first. That is `.shipd/rules/` by
   default, or whatever the config's `dir` key names. Checked in, so the whole
   team gets them.
2. **You** — `~/.shipd/rules/*.md`, applying in every repository on your
   machine. Your own habits, not the team's.
3. **The plugin** — its own `hooks/rules/*.md` built-ins.

Three built-in rules are active everywhere unless overridden or disabled:

| Rule | Denies |
| --- | --- |
| `changelog-comment` | comments narrating the edit rather than the code |
| `narrating-comment` | step narration restating the line below it |
| `filler-placeholder` | elisions standing in for content that must be written |

They are ordinary rule files. Read them for the exact patterns, and copy one
as the template for your own.

## Adding, editing, and overriding rules

**Add a rule** by dropping a file into the source you want it to cover:

```
mkdir -p .shipd/rules
$EDITOR .shipd/rules/no-bare-except.md
```

**Edit a rule** by editing its file. The hook re-reads the rulebook on every
invocation, so a saved change applies to the very next tool call — no restart,
no session reload.

**Override a built-in** by writing a file of the same name in a
higher-precedence source. Precedence is by **rule name**, which is the
filename stem, and the winner replaces the loser wholesale — pattern and
message together:

```
.shipd/rules/changelog-comment.md   ← this one wins
~/.shipd/rules/changelog-comment.md ← over this
<plugin>/hooks/rules/…              ← over the built-in
```

So a repo that wants a narrower `changelog-comment` writes its own; the
built-in's pattern is gone with it, not merged. To remove a rule rather than
replace it, disable it instead (below) — an override still needs a valid
pattern and message.

## Cooldown: keeping reminders quiet

A `deny` rule can fire as often as it likes; each firing blocks something you
did not want. A `remind` rule is different — it costs context every time and
blocks nothing — so reminders are rate-limited:

- **By default, once per session per rule.** The note lands the first time,
  and stays quiet after that.
- **`cooldown: <seconds>` re-arms it** that many seconds after its last fire,
  for guidance worth repeating during a long session.

The record is kept per session under `~/.shipd/guardrails/`, keyed by the
session id the hook payload carries. If a payload arrives without one, the
rule fires without recording — guidance delivered is better than guidance
lost. State that cannot be read or written never suppresses a reminder.

## Turning it off

Rules are authored as files; the `guardrails` key in `.shipd-config.json`
holds only the kill-switches.

Drop a single rule by name, wherever it came from:

```json
{ "guardrails": { "disable": ["narrating-comment"] } }
```

Or turn the hook off wholesale — no source consulted, every call allowed:

```json
{ "guardrails": false }
```

Like every top-level config key, `guardrails` merges nearest-wins-wholesale,
so declaring it at a workspace root governs every member repo beneath it.

For the emergency case — a rule misfiring while you are trying to get
something done — set the environment variable and the hook exits immediately,
for that session only:

```
export SHIPD_GUARDRAILS=off
```

An earlier version of the config key also accepted a `rules` member holding
rule objects. The rulebook supersedes it: that member is now **ignored**
without erroring, and any rule still living there should be moved to a file
under `<content-dir>/rules/` or `~/.shipd/rules/`.

## Token cost

Guardrails are unusually cheap, and it is worth knowing exactly why.

**A rule that does not fire costs nothing.** The rulebook is never part of the
prompt. Rules are read from disk by a Python subprocess and matched outside
the model entirely, so a repo carrying fifty rules costs the same context as a
repo carrying none: zero. This is the whole argument for a hook over a
`CLAUDE.md` section — instructions in the prompt are paid for on every single
turn whether or not they are ever relevant, and they still degrade as the
context fills.

**A firing `deny` costs the retried edit.** The model receives the refusal
reason — the rule's message and the offending line, a few dozen tokens — and
issues the tool call again. That retry is the real expense, and it is the one
you are buying deliberately: catching the line here is far cheaper than a
review round-trip, a follow-up commit, or the line surviving into `main`.

**A firing `remind` costs one injected message**, once per session by default.
No retry, no blocked call.

That asymmetry is the authoring rule:

- **`deny` for the certain.** If you would flag the line in review every time,
  without needing to look at the surrounding code, make it a deny. A false
  positive costs a wasted retry and a confused model.
- **`remind` for the fuzzy.** If it depends — a preference that usually holds,
  a convention with real exceptions — make it a remind. A false positive costs
  one sentence the model is free to disregard, which is exactly the right
  price for advice that might be wrong.

The failure mode to avoid is a chatty rulebook: reminders that fire constantly
train the model to ignore them, and they are the only part of the system that
spends context. Keep the deny rules sharp and the remind rules few.

## See also

- [What is shipd?](what-is-shipd.md) — where guardrails sit in the workflow.
- [The shipd review inside GitHub Copilot code review](copilot-review.md) —
  the semantic review that catches what a regex cannot.
- The content directory's `README.md` (`.shipd/README.md`) — the format
  authority for the rule file format and the `guardrails` config key.

# plan-video-entry
Status: verified
Epic: video-ingest
Theme: developer-experience

## Idea

Let `/s:plan` take a recording directly: ingest it, plan from the resulting
brief, and say so plainly when the brief is too broad for one change.

### Motivation

`/s:video-ingest` and `/s:plan` are separate invocations with no link between
them, so turning a recording into a spec means running two commands and carrying
the brief across by hand.

### Details

- Accept a video path or an existing bundle slug as the `/s:plan` argument, and
  delegate ingestion to `/s:video-ingest` by reference.
- Use the installed brief as investigation input ahead of the codebase-first
  read, never as a replacement for it.
- Where the brief's intents are too broad for one change, report that and stop
  without emitting, naming the intents that drove the read.
- Add a binary-free eval case exercising planning from a pre-installed brief.

Affected capabilities: `shipd-plan` (modified). Impact:
`plugins/s/skills/plan/SKILL.md`, a new `evals/cases/plan-video-brief/`, and
the plugin version in `plugins/s/.claude-plugin/plugin.json`. No engine script
changes.

### Non-goals

- No reimplementation of ingest — `/s:video-ingest` is invoked by reference,
  the way `/s:build` already invokes the plan flow.
- No mechanical epic threshold; routing is advisory and the human decides.
- No automatic `/s:epic` invocation — plan never starts an epic on its own.
- No change to `/s:epic` itself; consuming a brief there is
  `epic-video-brief`'s job.
- No video fixture committed to `evals/cases/`.
- No change to the brief grammar, the bundle contract, or any engine script.

## Implementation

**Delegation by reference, not reimplementation.** `/s:build` already invokes
the plan flow "by reference — do not copy its prompt"
(`plugins/s/skills/build/SKILL.md:124`). The video pre-step follows that exact
precedent: `/s:plan` names the `/s:video-ingest` skill and lets it run its own
staged pipeline, so ingest logic lives in one place and this member adds no
duplicate instructions about doctor, bundles, or frames.

**The brief informs investigation; it does not replace it.** `shipd-plan`'s
`codebase-first-investigation` is unchanged and still binding — the brief says
what the speaker wants, the repository still says which capability owns it and
how it is currently built. The pre-step therefore runs *ahead* of investigation
and feeds it, rather than short-circuiting it. Neither
`convergent-plan-flow` nor `codebase-first-investigation` is contradicted, so
both are left unmodified and this change is purely additive.

**Epic routing is advisory, because no mechanical criterion exists to reuse.**
The epic's D14 says routing "reuses the existing epic criteria", but
`shipd-epic`'s spec defines no threshold — epic-versus-change is judgment
everywhere else in this repo. Rather than invent a rule that would then be the
only mechanical scope trigger in the system, plan reports that the brief reads
as epic-sized, names the intents that drove that read, and stops without
emitting. The human decides. Rejected: a "more than one verified capability"
trigger, which would invent a threshold nothing else honours; and no routing at
all, which would silently emit one overstuffed change from a broad recording.

**Stopping without emitting is a deliberate exception to the auto-proceed
flow.** The plan skill otherwise proceeds to emission without asking. An
epic-sized brief is a genuine scope decision that only the user can take, so it
joins the skill's short list of conditions that end a turn — reported as such
rather than smuggled in as a question.

**The eval case ships a brief, not a recording.** `skill-evals/eval-case-layout`
defines a case as `prompt.md` plus a `fixture/` repo and discovers cases
automatically, so a new case needs no spec change. The fixture carries a
pre-installed `brief.md` under its content directory and the prompt points plan
at that bundle slug, exercising the half of the flow that reasons — brief in,
lint-clean change out — without a multi-megabyte binary in `evals/cases/` and
without depending on the MLX toolchain being installed on the machine running
evals.

**This change edits a skill the existing eval cases already exercise**, unlike
`video-ingest-skill`, which only added one. `AGENTS.md`'s local-eval rule
therefore applies for real here: the task list runs `evals/run.py` over the
existing cases to confirm the pre-step has not disturbed the ordinary
no-video path, and that run costs real model spend.

Risk: the pre-step fires on an argument that merely looks like a path and
derails an ordinary text-prompt plan. Guarded by keying the branch on an
explicit video file extension or a slug whose bundle directory actually
exists and holds a `transcript.json` — `video_ingest.py path` itself performs
no existence check and always exits 0, so the guard verifies the printed
directory on disk rather than trusting the command's exit status; anything
failing that check falls through to the unchanged flow.
